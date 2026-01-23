from flask import Flask, jsonify, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    AgeRestricted,
    VideoUnplayable
)
from xml.etree.ElementTree import ParseError
from functools import lru_cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import isodate
import functools

app = Flask(__name__)

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# YouTube API setup
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# YouTube Transcript API instance
ytt_api = YouTubeTranscriptApi()

# Cache configuration using LRU cache
@lru_cache(maxsize=100)
def get_transcript(video_id):
    transcript = ytt_api.fetch(video_id)
    return transcript.to_raw_data()

@lru_cache(maxsize=100)
def get_video_comments(video_id, max_results=100):
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()

        comments = []
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'likes': comment['likeCount'],
                'published_at': comment['publishedAt']
            })

        return comments
    except HttpError as e:
        if e.resp.status == 403:
            raise Exception("Comments are disabled for this video")
        raise e

@lru_cache(maxsize=100)
def get_video_metadata(video_id):
    try:
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise Exception("Video not found")

        video_data = response['items'][0]
        snippet = video_data['snippet']

        return {
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId', ''),
            'thumbnails': snippet.get('thumbnails', {}),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', '')
        }
    except HttpError as e:
        if e.resp.status == 403:
            raise Exception("Access forbidden")
        elif e.resp.status == 404:
            raise Exception("Video not found")
        raise e

@lru_cache(maxsize=100)
def get_video_statistics(video_id):
    """
    Fetch video statistics from YouTube Data API v3.

    Args:
        video_id: YouTube video ID (11 characters)

    Returns:
        Dictionary with view_count, like_count, comment_count, duration (parsed),
        definition, and caption status

    Raises:
        Exception: If video not found or access is forbidden
    """
    try:
        request = youtube.videos().list(
            part='statistics,contentDetails',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise Exception("Video not found")

        video_data = response['items'][0]
        statistics = video_data.get('statistics', {})
        details = video_data.get('contentDetails', {})

        # Extract statistics (convert to int, default to 0 if missing)
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))

        # Extract content details
        duration_raw = details.get('duration', '')
        definition = details.get('definition', '')
        caption = details.get('caption', 'false') == 'true'

        # Parse duration from ISO 8601 format
        duration_parsed = parse_duration(duration_raw) if duration_raw else {
            'raw': '',
            'total_seconds': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0
        }

        return {
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'duration': duration_parsed,
            'definition': definition,
            'caption': caption
        }

    except HttpError as e:
        if e.resp.status == 403:
            raise Exception("Access forbidden")
        elif e.resp.status == 404:
            raise Exception("Video not found")
        raise e

@lru_cache(maxsize=100)
def get_unified_video_data(video_id):
    """
    Fetch complete video data (transcript, metadata, statistics) in parallel.

    Uses ThreadPoolExecutor to fetch all three data types concurrently,
    then aggregates results with error handling for partial failures.

    Args:
        video_id: YouTube video ID (11 characters)

    Returns:
        Dictionary with:
        - success (bool): True if any data fetched successfully
        - partial_success (bool): True if some fetches failed
        - video_id (str): The video ID
        - quota_cost (int): Total API quota cost (3)
        - transcript (dict/list or None): Transcript data
        - metadata (dict or None): Video metadata
        - statistics (dict or None): Video statistics
        - errors (list): List of {field, error} for failed fetches
    """
    # Initialize result structure
    result = {
        'success': True,
        'partial_success': False,
        'video_id': video_id,
        'quota_cost': 3,
        'transcript': None,
        'metadata': None,
        'statistics': None,
        'errors': []
    }

    # Create fetch functions with video_id bound using functools.partial
    fetch_functions = {
        'transcript': functools.partial(get_transcript, video_id),
        'metadata': functools.partial(get_video_metadata, video_id),
        'statistics': functools.partial(get_video_statistics, video_id)
    }

    # Execute fetches in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all fetch functions and store futures
        futures = {
            executor.submit(func): field_name
            for field_name, func in fetch_functions.items()
        }

        # Process completed futures as they finish
        for future in as_completed(futures):
            field_name = futures[future]
            try:
                result[field_name] = future.result()
            except Exception as e:
                # Field failed: store None, log error, mark partial success
                result[field_name] = None
                result['errors'].append({
                    'field': field_name,
                    'error': str(e)
                })
                result['partial_success'] = True

    # If all fetches failed, set success to False
    if result['errors'] and not any([result['transcript'], result['metadata'], result['statistics']]):
        result['success'] = False

    return result

@lru_cache(maxsize=100)
def get_comments_for_video(video_id, max_results=100):
    """
    Fetch comments for a video.

    This is a helper function for the MCP tool to fetch comments
    without dealing with Flask request/response structures.

    Args:
        video_id: YouTube video ID (11 characters)
        max_results: Maximum number of comments to fetch (default: 100)

    Returns:
        List of comment dictionaries with author, text, likes, and published_at

    Raises:
        Exception: If comments are disabled or video not found
    """
    return get_video_comments(video_id, max_results)

@lru_cache(maxsize=50)
def search_youtube_videos(query, max_results=10):
    """
    Search YouTube videos by keyword using YouTube Search API.

    WARNING: This operation costs 100 YouTube API quota units per request.
    The Search API is expensive compared to other endpoints.

    Args:
        query: Search query string (must not be empty)
        max_results: Maximum number of results to return (1-50, default: 10)

    Returns:
        List of video objects with keys:
        - video_id (str): 11-character YouTube video ID
        - title (str): Video title
        - description (str): Video description
        - thumbnail (str): Thumbnail URL
        - channel_title (str): Channel name
        - published_at (str): ISO 8601 publish date

    Raises:
        ValueError: If query is empty/None or max_results out of range
        HttpError: If API quota exceeded or other API errors
        Exception: For other errors
    """
    # Validate query
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    # Validate and clamp max_results to YouTube API limits
    max_results = max(1, min(50, int(max_results)))

    try:
        # Call YouTube Search API
        search_request = youtube.search().list(
            part='snippet',
            q=query,
            type='video',
            maxResults=max_results,
            order='relevance'  # Most relevant results first
        )
        search_response = search_request.execute()

        # Extract video data from response
        videos = []
        for item in search_response.get('items', []):
            # Extract video ID (nested structure for search results)
            video_id = item.get('id', {}).get('videoId')
            if not video_id:
                continue

            snippet = item.get('snippet', {})

            # Extract thumbnail with fallback
            thumbnail_url = None
            thumbnails = snippet.get('thumbnails', {})
            if 'default' in thumbnails:
                thumbnail_url = thumbnails['default'].get('url')
            elif 'medium' in thumbnails:
                thumbnail_url = thumbnails['medium'].get('url')
            elif 'high' in thumbnails:
                thumbnail_url = thumbnails['high'].get('url')

            videos.append({
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'thumbnail': thumbnail_url,
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', '')
            })

        return videos

    except HttpError as e:
        if e.resp.status == 403:
            # Check if it's quota exceeded
            error_content = e.content.decode('utf-8') if hasattr(e, 'content') else ''
            if 'quota' in error_content.lower():
                raise Exception("YouTube API quota exceeded. Search API is expensive (100 units per request).")
            raise Exception("Access forbidden. Quota may be exceeded or API key is invalid.")
        elif e.resp.status == 400:
            raise Exception(f"Invalid search request: {e}")
        raise e
    except Exception as e:
        raise e

@lru_cache(maxsize=100)
def get_channel_info(channel_id):
    """
    Fetch YouTube channel information from YouTube Channels API.

    Args:
        channel_id: YouTube channel ID (starts with 'UC', 24 characters)

    Returns:
        Dictionary with keys:
        - channel_id (str): Channel ID
        - title (str): Channel title
        - description (str): Channel description
        - subscriber_count (int): Number of subscribers
        - video_count (int): Total videos on channel
        - view_count (int): Total lifetime views
        - created_at (str): ISO 8601 date when channel was created
        - thumbnail (str): URL to channel thumbnail

    Raises:
        ValueError: If channel_id is empty
        Exception: If channel not found or API error occurs
    """
    # Validate channel_id
    if not channel_id or not channel_id.strip():
        raise ValueError("Channel ID cannot be empty")

    try:
        request = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        response = request.execute()

        # Check if channel was found
        if not response.get('items'):
            raise Exception(f"Channel not found: {channel_id}")

        channel_data = response['items'][0]
        snippet = channel_data.get('snippet', {})
        statistics = channel_data.get('statistics', {})

        # Extract thumbnail with fallback
        thumbnail_url = None
        thumbnails = snippet.get('thumbnails', {})
        if 'default' in thumbnails:
            thumbnail_url = thumbnails['default'].get('url')
        elif 'medium' in thumbnails:
            thumbnail_url = thumbnails['medium'].get('url')
        elif 'high' in thumbnails:
            thumbnail_url = thumbnails['high'].get('url')

        return {
            'channel_id': channel_data.get('id', channel_id),
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'subscriber_count': int(statistics.get('subscriberCount', 0)),
            'video_count': int(statistics.get('videoCount', 0)),
            'view_count': int(statistics.get('viewCount', 0)),
            'created_at': snippet.get('publishedAt', ''),
            'thumbnail': thumbnail_url
        }

    except HttpError as e:
        if e.resp.status == 404:
            raise Exception(f"Channel not found: {channel_id}")
        elif e.resp.status == 403:
            raise Exception("Access forbidden. Quota may be exceeded or API key is invalid.")
        raise e
    except Exception as e:
        raise e

@lru_cache(maxsize=50)
def get_channel_uploads(channel_id, max_results=10):
    """
    Fetch recent video uploads from a YouTube channel using YouTube Search API.

    Args:
        channel_id: YouTube channel ID (starts with 'UC', 24 characters)
        max_results: Maximum number of videos to return (1-50, default: 10)

    Returns:
        List of video objects with keys:
        - video_id (str): 11-character YouTube video ID
        - title (str): Video title
        - description (str): Video description
        - thumbnail (str): Thumbnail URL
        - published_at (str): ISO 8601 publish date

    Raises:
        ValueError: If max_results out of range
        Exception: If channel not found or API error occurs
    """
    # Validate and clamp max_results
    max_results = max(1, min(50, int(max_results)))

    try:
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            type='video',
            order='date',  # Most recent first
            maxResults=max_results
        )
        response = request.execute()

        # Extract video data from response
        videos = []
        for item in response.get('items', []):
            # Extract video ID (nested structure for search results)
            video_id = item.get('id', {}).get('videoId')
            if not video_id:
                continue

            snippet = item.get('snippet', {})

            # Extract thumbnail with fallback
            thumbnail_url = None
            thumbnails = snippet.get('thumbnails', {})
            if 'default' in thumbnails:
                thumbnail_url = thumbnails['default'].get('url')
            elif 'medium' in thumbnails:
                thumbnail_url = thumbnails['medium'].get('url')
            elif 'high' in thumbnails:
                thumbnail_url = thumbnails['high'].get('url')

            videos.append({
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'thumbnail': thumbnail_url,
                'published_at': snippet.get('publishedAt', '')
            })

        return videos

    except HttpError as e:
        if e.resp.status == 403:
            error_content = e.content.decode('utf-8') if hasattr(e, 'content') else ''
            if 'quota' in error_content.lower():
                raise Exception("YouTube API quota exceeded.")
            raise Exception("Access forbidden. Quota may be exceeded or API key is invalid.")
        raise e
    except Exception as e:
        raise e

def parse_duration(iso_duration):
    """
    Parse ISO 8601 duration string (e.g., PT1H2M3S) into components.

    Args:
        iso_duration: ISO 8601 duration string (e.g., "PT1H2M3S")

    Returns:
        Dictionary with keys: raw, total_seconds, hours, minutes, seconds
    """
    duration = isodate.parse_duration(iso_duration)
    total_seconds = int(duration.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
        'raw': iso_duration,
        'total_seconds': total_seconds,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds
    }

def process_transcript(transcript_list, include_timestamps=True):
    if include_timestamps:
        return transcript_list
    # Combine all text segments into a single string when timestamps=false
    combined_text = " ".join(item['text'] for item in transcript_list)
    return {"text": combined_text}

def is_valid_video_id(video_id):
    # Basic YouTube video ID validation (11 characters, alphanumeric with some special chars)
    return bool(re.match(r'^[A-Za-z0-9_-]{11}$', video_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcript/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def transcript(video_id):
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        # Get timestamps parameter (default to True)
        include_timestamps = request.args.get('timestamps', 'true').lower() == 'true'
        
        transcript_list = get_transcript(video_id)
        processed_transcript = process_transcript(transcript_list, include_timestamps)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'timestamps_included': include_timestamps,
            'transcript': processed_transcript
        })

    except NoTranscriptFound:
        return jsonify({
            'error': 'No transcript found for this video'
        }), 404

    except VideoUnavailable:
        return jsonify({
            'error': 'Video is unavailable'
        }), 404

    except RequestBlocked:
        return jsonify({
            'error': 'Request blocked by YouTube',
            'details': 'YouTube has blocked this request. This may be due to IP restrictions.'
        }), 503

    except AgeRestricted:
        return jsonify({
            'error': 'Video is age-restricted',
            'details': 'This video requires age verification and cannot be accessed.'
        }), 403

    except VideoUnplayable as e:
        return jsonify({
            'error': 'Video is unplayable',
            'details': str(e)
        }), 403

    except ParseError:
        return jsonify({
            'error': 'Transcript unavailable',
            'details': 'YouTube returned an invalid response. The video may have restricted transcripts or be temporarily unavailable.'
        }), 503

    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/comments/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def comments(video_id):
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        # Get max_results parameter (default to 100, max 100)
        max_results = min(int(request.args.get('max_results', 100)), 100)

        comments_list = get_video_comments(video_id, max_results)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'comment_count': len(comments_list),
            'comments': comments_list
        })

    except Exception as e:
        error_message = str(e)
        if "Comments are disabled" in error_message:
            return jsonify({
                'error': 'Comments are disabled for this video'
            }), 403
        elif "quota" in error_message.lower():
            return jsonify({
                'error': 'YouTube API quota exceeded'
            }), 429
        else:
            return jsonify({
                'error': 'An unexpected error occurred',
                'details': error_message
            }), 500

@app.route('/api/metadata/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def metadata(video_id):
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        metadata_data = get_video_metadata(video_id)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'quota_cost': 1,
            'metadata': metadata_data
        })

    except Exception as e:
        error_message = str(e)
        if "Video not found" in error_message:
            return jsonify({
                'error': 'Video not found'
            }), 404
        elif "Access forbidden" in error_message:
            return jsonify({
                'error': 'Access forbidden',
                'details': 'Quota may be exceeded or video is private'
            }), 403
        else:
            return jsonify({
                'error': 'An unexpected error occurred',
                'details': error_message
            }), 500

@app.route('/api/statistics/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def statistics(video_id):
    """
    Endpoint to fetch video statistics.

    Returns:
        JSON with success, video_id, quota_cost (1), and statistics object
        containing view_count, like_count, comment_count, duration, definition,
        and caption status.

    Error responses:
        400: Invalid video ID format
        403: Access forbidden (quota exceeded or private video)
        404: Video not found
        500: Unexpected error
    """
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        statistics_data = get_video_statistics(video_id)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'quota_cost': 1,
            'statistics': statistics_data
        })

    except Exception as e:
        error_message = str(e)
        if "Video not found" in error_message:
            return jsonify({
                'error': 'Video not found'
            }), 404
        elif "Access forbidden" in error_message:
            return jsonify({
                'error': 'Access forbidden',
                'details': 'Quota may be exceeded or video is private'
            }), 403
        else:
            return jsonify({
                'error': 'An unexpected error occurred',
                'details': error_message
            }), 500

@app.route('/api/video/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def unified_video_data(video_id):
    """
    Unified endpoint to fetch complete video data (transcript, metadata, statistics) in parallel.

    Returns:
        JSON with all video data:
        - success (bool): True if any data fetched successfully
        - partial_success (bool): True if some fetches failed
        - video_id (str): The video ID
        - quota_cost (int): Total API quota cost (3)
        - transcript: Video transcript with timestamps
        - metadata: Video metadata (title, description, tags, etc.)
        - statistics: Video statistics (views, likes, comments, duration)
        - errors (list): Any errors from failed fetches

    Status codes:
        200: All data fetched successfully
        207: Partial success (some data available, some failed)
        400: Invalid video ID format
        500: Complete failure (all fetches failed)
    """
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        result = get_unified_video_data(video_id)

        # Check if all fetches failed
        if not result['success']:
            return jsonify({
                'error': 'Failed to retrieve video data',
                'details': result['errors']
            }), 500

        # Check for partial success
        if result['partial_success']:
            return jsonify(result), 207  # Multi-Status

        # All successful
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/health')
def health():
    """
    Health check endpoint for the Flask API.

    Returns:
        JSON with service status and MCP server location.
    """
    return jsonify({
        "status": "ok",
        "service": "YouTube Data Fetcher API",
        "flask": "running",
        "mcp": "http://localhost:8000/mcp"
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'details': str(e.description)
    }), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
