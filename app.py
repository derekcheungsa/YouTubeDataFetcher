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
import os
import re
import isodate

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

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'details': str(e.description)
    }), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
