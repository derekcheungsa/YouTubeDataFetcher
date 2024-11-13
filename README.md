# YouTube Transcript API Service

A REST API service for retrieving YouTube video transcripts and comments, built using Flask and the youtube-transcript-api library. The service provides transcript retrieval with configurable timestamp output, comments retrieval, comprehensive error handling, and interactive API documentation.

## Features

- 🎯 RESTful endpoints:
  - Transcript retrieval (`/api/transcript/<video_id>`)
  - Comments retrieval (`/api/comments/<video_id>`)
- ⏱️ Configurable timestamp output support for transcripts
- 🔒 Built-in rate limiting (100 requests/day, 10/minute)
- 📱 Bootstrap-based responsive UI
- 🌙 Dark mode documentation interface with live API testing
- ⚠️ Comprehensive error handling for:
  - Invalid video IDs
  - Missing transcripts
  - Disabled comments
  - Unavailable videos
  - Rate limit exceeded

## Installation

1. Clone the repository to your local machine or Replit workspace
2. Install the required dependencies:
   ```bash
   pip install flask youtube-transcript-api flask-limiter google-api-python-client
   ```
3. Run the application:
   ```bash
   python main.py
   ```
   The server will start on `http://0.0.0.0:5000`

## API Documentation

### Get Video Transcript
```http
GET /api/transcript/<video_id>?timestamps=true|false
```

#### Parameters

| Parameter   | Type    | Description                                     | Required |
|------------|---------|------------------------------------------------|----------|
| video_id   | string  | YouTube video ID (11 characters)                | Yes      |
| timestamps | boolean | Include timing information (default: true)      | No       |

#### Response Format

With Timestamps (`timestamps=true`):
```json
{
    "success": true,
    "video_id": "video_id",
    "timestamps_included": true,
    "transcript": [
        {
            "text": "transcript text",
            "start": 0.0,
            "duration": 1.5
        }
    ]
}
```

Without Timestamps (`timestamps=false`):
```json
{
    "success": true,
    "video_id": "video_id",
    "timestamps_included": false,
    "transcript": {
        "text": "Complete transcript text all combined into one string"
    }
}
```

### Get Video Comments
```http
GET /api/comments/<video_id>?max_results=100
```

#### Parameters

| Parameter   | Type    | Description                                     | Required |
|------------|---------|------------------------------------------------|----------|
| video_id   | string  | YouTube video ID (11 characters)                | Yes      |
| max_results| integer | Maximum number of comments to return (max: 100) | No       |

#### Response Format
```json
{
    "success": true,
    "video_id": "video_id",
    "comment_count": 50,
    "comments": [
        {
            "author": "User Name",
            "text": "Comment text",
            "likes": 42,
            "published_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Error Responses

| Status Code | Description           | Response                                      |
|-------------|--------------------|-----------------------------------------------|
| 400         | Invalid video ID   | `{"error": "Invalid video ID format"}`         |
| 403         | Comments disabled  | `{"error": "Comments are disabled for this video"}` |
| 404         | No transcript      | `{"error": "No transcript found for this video"}` |
| 404         | Video unavailable  | `{"error": "Video is unavailable"}`            |
| 429         | Rate limit exceeded| `{"error": "Rate limit exceeded"}`             |
| 500         | Server error       | `{"error": "An unexpected error occurred"}`    |

## Rate Limits

The API implements the following rate limits:
- 100 requests per day per IP address
- 10 requests per minute per IP address

## Usage Examples

### Using cURL
```bash
# Get transcript with timestamps
curl "http://your-domain.com/api/transcript/VIDEO_ID?timestamps=true"

# Get transcript without timestamps
curl "http://your-domain.com/api/transcript/VIDEO_ID?timestamps=false"

# Get video comments
curl "http://your-domain.com/api/comments/VIDEO_ID?max_results=50"
```

### Using Python Requests
```python
import requests

# Get transcript with timestamps
response = requests.get('http://your-domain.com/api/transcript/VIDEO_ID', 
                       params={'timestamps': 'true'})
print(response.json())

# Get video comments
response = requests.get('http://your-domain.com/api/comments/VIDEO_ID', 
                       params={'max_results': 50})
print(response.json())
```

## Technology Stack

- **Backend Framework**: Flask
- **API Integration**: 
  - youtube-transcript-api
  - google-api-python-client
- **Rate Limiting**: Flask-Limiter
- **Frontend**: 
  - Bootstrap 5.3.0 (Responsive UI)
  - Custom dark mode theme
  - Vanilla JavaScript
- **Caching**: Python's built-in LRU cache
- **Error Handling**: Comprehensive exception handling with proper HTTP status codes

## Development and Deployment

This project is optimized for deployment on Replit. The development server automatically runs on `0.0.0.0:5000` to ensure compatibility with Replit's infrastructure.

## Warning

The current implementation uses in-memory storage for rate limiting. For production use, it's recommended to configure a proper storage backend as described in the [Flask-Limiter documentation](https://flask-limiter.readthedocs.io#configuring-a-storage-backend).
