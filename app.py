from flask import Flask, jsonify, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
from functools import lru_cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

app = Flask(__name__)

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# Cache configuration using LRU cache
@lru_cache(maxsize=100)
def get_transcript(video_id):
    return YouTubeTranscriptApi.get_transcript(video_id)

def process_transcript(transcript_list, include_timestamps=True):
    if include_timestamps:
        return transcript_list
    return [{'text': item['text']} for item in transcript_list]

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
        
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'details': str(e.description)
    }), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
