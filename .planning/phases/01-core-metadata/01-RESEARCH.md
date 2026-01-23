# Phase 01: Core Metadata - Research

**Researched:** 2026-01-22
**Domain:** YouTube Data API v3 / Flask REST API / Python Concurrency
**Confidence:** HIGH

## Summary

This research investigates how to extend the existing Flask REST API with three new endpoints for fetching YouTube video metadata, statistics, and a unified data endpoint. The core challenge involves using the YouTube Data API v3's `videos.list` method to retrieve video information, handling ISO 8601 duration formatting, implementing parallel requests for the unified endpoint, and maintaining consistent response formats with graceful error handling.

**Key findings:**
- YouTube Data API v3 `videos.list` method costs 1 quota unit per request and returns all required metadata and statistics in a single call using `part=snippet,statistics,contentDetails`
- The `isodate` Python library is the standard solution for parsing ISO 8601 duration strings (e.g., "PT1H2M3S") returned by YouTube's `contentDetails.duration` field
- Python's built-in `concurrent.futures.ThreadPoolExecutor` is the recommended approach for parallel API calls in Flask, enabling faster unified endpoint responses
- Consistent error handling should use Flask/Werkzeug exceptions with a base API exception class for uniform response formats
- All three new endpoints can use the same caching pattern (`@lru_cache`) as existing endpoints

**Primary recommendation:** Use `google-api-python-client` (already installed) with `part=snippet,statistics,contentDetails` parameter, implement `isodate` for duration parsing, use `concurrent.futures.ThreadPoolExecutor` for parallel requests in unified endpoint, and create a base API exception class for consistent error responses.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-api-python-client | latest (already in requirements.txt) | YouTube Data API v3 client | Official Google library, already in use, stable and maintained |
| isodate | 0.6.1+ | Parse ISO 8601 durations | Standard library for ISO 8601 parsing, handles PT#H#M#S format |
| concurrent.futures | built-in (Python 3.2+) | Parallel API requests | Built-in Python module, recommended for I/O-bound parallel tasks |
| functools.lru_cache | built-in (Python 3.2+) | Response caching | Already in use, perfect for API response caching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Werkzeug.exceptions | 3.0.1+ (already installed) | HTTP error handling | Already part of Flask stack, use for base exception class |
| Flask-Limiter | 3.5.0 (already installed) | Rate limiting | Already in use, apply to new endpoints |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| isodate | Custom regex parsing | isodate handles all ISO 8601 edge cases, custom regex is error-prone |
| concurrent.futures | asyncio | asyncio is more complex for this use case, ThreadPoolExecutor is simpler for I/O-bound tasks |
| google-api-python-client | requests library directly | Official client handles auth, retries, and error handling automatically |

**Installation:**
```bash
# Only need to install isodate (everything else is already installed)
pip install isodate
```

Update requirements.txt:
```txt
isodate>=0.6.1
```

## Architecture Patterns

### Recommended Project Structure

The existing monolithic structure in `app.py` should be extended (not refactored):

```
app.py (existing, extend with new functions)
├── get_video_metadata()      # New: Fetch metadata via YouTube API
├── get_video_statistics()    # New: Fetch statistics via YouTube API
├── get_unified_video_data()  # New: Parallel fetch of all data
├── parse_duration()          # New: Convert ISO 8601 duration
└── [existing functions]
```

### Pattern 1: YouTube Data API Video Resource Fetch

**What:** Use `youtube.videos().list()` with specific `part` parameter to fetch video data

**When to use:** All three new endpoints (metadata, statistics, unified)

**Example:**
```python
# Source: https://developers.google.com/youtube/v3/docs/videos/list
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def fetch_video_data(video_id, parts):
    """
    Fetch video data from YouTube API
    parts: comma-separated string (e.g., 'snippet,statistics,contentDetails')
    Returns: dict with video resource data
    """
    try:
        request = youtube.videos().list(
            part=parts,
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise Exception("Video not found")

        return response['items'][0]

    except HttpError as e:
        if e.resp.status == 404:
            raise Exception("Video not found")
        elif e.resp.status == 403:
            raise Exception("Access forbidden or quota exceeded")
        raise
```

**Quota cost:** 1 unit per request (regardless of `part` parameter)

**Part options:**
- `snippet` - title, description, tags, categoryId, thumbnails, channelTitle, publishedAt
- `statistics` - viewCount, likeCount, commentCount
- `contentDetails` - duration, definition, caption, licensedContent

### Pattern 2: ISO 8601 Duration Parsing

**What:** Convert YouTube's ISO 8601 duration format to human-readable format

**When to use:** Processing `contentDetails.duration` field in statistics endpoint

**Example:**
```python
# Source: https://stackoverflow.com/questions/25296416/how-can-i-parse-and-compare-iso-8601-durations-in-python
import isodate

def parse_duration(iso_duration):
    """
    Parse ISO 8601 duration string (e.g., 'PT1H2M3S')
    Returns: dict with hours, minutes, seconds, and total_seconds
    """
    duration = isodate.parse_duration(iso_duration)

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
        'raw': iso_duration,           # Original: 'PT1H2M3S'
        'total_seconds': total_seconds, # 3723
        'hours': hours,                 # 1
        'minutes': minutes,             # 2
        'seconds': seconds              # 3
    }
```

**Input format:** PT#H#M#S (Period Time, Hours, Minutes, Seconds)
- `PT15M33S` = 15 minutes, 33 seconds
- `PT1H2M3S` = 1 hour, 2 minutes, 3 seconds
- `PT30S` = 30 seconds

### Pattern 3: Parallel API Requests with ThreadPoolExecutor

**What:** Execute multiple API calls concurrently using thread pool

**When to use:** Unified endpoint (`/api/video/<video_id>`) to fetch transcript + metadata + stats in parallel

**Example:**
```python
# Source: https://docs.python.org/3/library/concurrent.futures.html
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

def get_unified_video_data(video_id):
    """
    Fetch transcript, metadata, and statistics in parallel
    Returns: dict with all data or partial data with failures indicated
    """
    results = {
        'success': True,
        'partial_success': False,
        'video_id': video_id,
        'transcript': None,
        'metadata': None,
        'statistics': None,
        'errors': []
    }

    # Define fetch functions
    fetch_functions = {
        'transcript': functools.partial(get_transcript, video_id),
        'metadata': functools.partial(get_video_metadata, video_id),
        'statistics': functools.partial(get_video_statistics, video_id)
    }

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(func): name
            for name, func in fetch_functions.items()
        }

        for future in as_completed(futures):
            field_name = futures[future]
            try:
                results[field_name] = future.result()
            except Exception as e:
                results[field_name] = None
                results['errors'].append({
                    'field': field_name,
                    'error': str(e)
                })
                results['partial_success'] = True

    # Mark overall success if any field succeeded
    if results['errors']:
        results['success'] = any([
            results['transcript'] is not None,
            results['metadata'] is not None,
            results['statistics'] is not None
        ])

    return results
```

**Benefits:**
- Reduces response time from ~3 seconds to ~1 second (3 parallel calls)
- Graceful degradation: if one fetch fails, others still succeed
- `partial_success` flag indicates incomplete data

### Pattern 4: Consistent API Response Format

**What:** Standardize success and error response structures across all endpoints

**When to use:** All new endpoints

**Success response structure:**
```python
{
    'success': True,
    'video_id': 'abc123',
    'quota_cost': 1,                     # NEW: YouTube API quota used
    'metadata': {                        # For /api/metadata endpoint
        'title': 'Video Title',
        'description': '...',
        'tags': ['tag1', 'tag2'],
        'category_id': '22',
        'thumbnails': { ... },
        'channel_title': 'Channel Name',
        'published_at': '2024-01-15T10:30:00Z'
    }
}

# OR

{
    'success': True,
    'video_id': 'abc123',
    'quota_cost': 1,
    'statistics': {                      # For /api/statistics endpoint
        'view_count': 1000000,
        'like_count': 50000,
        'comment_count': 1000,
        'duration': {
            'raw': 'PT10M30S',
            'total_seconds': 630,
            'hours': 0,
            'minutes': 10,
            'seconds': 30
        }
    }
}

# OR

{
    'success': True,
    'partial_success': False,            # NEW: Indicates if any data is missing
    'video_id': 'abc123',
    'quota_cost': 3,                     # 3 API calls made
    'transcript': [ ... ],
    'metadata': { ... },
    'statistics': { ... }
}
```

**Error response structure:**
```python
# Consistent with existing endpoints
{
    'error': 'Error message',
    'details': 'Additional context'  # Optional
}

# HTTP status codes: 400, 403, 404, 429, 500
```

### Anti-Patterns to Avoid

- **Making separate API calls for metadata and statistics:** Use single `videos.list()` call with `part=snippet,statistics,contentDetails`
- **Parsing duration with regex:** Use `isodate` library instead
- **Synchronous calls in unified endpoint:** Use `ThreadPoolExecutor` for parallel requests
- **Inconsistent error handling:** Create base API exception class for uniformity
- **Missing quota_cost field:** Always include quota usage in response

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ISO 8601 duration parsing | Custom regex parser | `isodate` library | Handles all edge cases (weeks, months, fractional seconds), timezone-aware |
| Parallel API execution | Custom threading logic | `concurrent.futures.ThreadPoolExecutor` | Built-in, tested, handles exceptions properly, context manager support |
| HTTP error handling | Manual status code checking | `googleapiclient.errors.HttpError` | Official client handles all YouTube API error cases |
| API response caching | Custom dict-based cache | `@lru_cache` decorator | Built-in, thread-safe, automatic eviction, memory-efficient |

**Key insight:** Custom solutions for these problems introduce bugs, edge cases, and maintenance burden. Standard libraries are well-tested, documented, and community-supported.

## Common Pitfalls

### Pitfall 1: Excessive API Calls

**What goes wrong:** Making separate API calls for snippet, statistics, and contentDetails, resulting in 3x quota usage

**Why it happens:** Not reading the API documentation about the `part` parameter

**How to avoid:** Always request multiple parts in a single call:
```python
# BAD (3 quota units)
snippet = youtube.videos().list(part='snippet', id=video_id)
stats = youtube.videos().list(part='statistics', id=video_id)
details = youtube.videos().list(part='contentDetails', id=video_id)

# GOOD (1 quota unit)
all_data = youtube.videos().list(part='snippet,statistics,contentDetails', id=video_id)
```

**Warning signs:** Multiple `youtube.videos().list()` calls in same function

### Pitfall 2: Forgetting Video ID Validation

**What goes wrong:** Passing invalid video IDs to YouTube API, wasting quota on 404 errors

**Why it happens:** Assuming YouTube API will handle validation (it does, but costs quota)

**How to avoid:** Validate video ID format before making API call (already implemented in `app.py`):
```python
import re

def is_valid_video_id(video_id):
    return bool(re.match(r'^[A-Za-z0-9_-]{11}$', video_id))
```

**Warning signs:** Not calling `is_valid_video_id()` before API requests

### Pitfall 3: Not Handling Empty Response Items

**What goes wrong:** `response['items'][0]` throws IndexError when video not found

**Why it happens:** YouTube API returns `{'items': []}` for non-existent videos instead of 404

**How to avoid:** Always check items array before accessing:
```python
response = youtube.videos().list(part='snippet', id=video_id).execute()

if not response.get('items'):
    raise Exception("Video not found")

video_data = response['items'][0]
```

**Warning signs:** Direct indexing of `response['items'][0]` without length check

### Pitfall 4: Thread Pool Deadlock in Flask

**What goes wrong:** Using `ThreadPoolExecutor` with too many workers causing blocking

**Why it happens:** YouTube API has rate limits; too many concurrent requests trigger throttling

**How to avoid:** Limit workers to 3-5 for YouTube API calls:
```python
with ThreadPoolExecutor(max_workers=3) as executor:  # Not 100!
    # parallel API calls
```

**Warning signs:** Setting `max_workers` to high numbers (e.g., 50, 100)

### Pitfall 5: Inconsistent Error Response Format

**What goes wrong:** Some endpoints return `{'error': 'msg'}`, others return `{'message': 'msg'}`, others return HTTP status codes without body

**Why it happens:** Not having a base API exception class, adding endpoints ad-hoc

**How to avoid:** Create base API exception class:
```python
class APIError(Exception):
    def __init__(self, message, status_code=500, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details
        self.message = message

    def to_dict(self):
        result = {'error': self.message}
        if self.details:
            result['details'] = self.details
        return result

# Usage
raise APIError("Video not found", status_code=404)
```

**Warning signs:** Error response dictionaries constructed differently across endpoints

## Code Examples

### Example 1: Fetch Video Metadata

```python
# Source: Based on existing app.py pattern + YouTube API docs
from functools import lru_cache

@lru_cache(maxsize=100)
def get_video_metadata(video_id):
    """
    Fetch video metadata from YouTube API
    Quota cost: 1 unit
    """
    try:
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise Exception("Video not found")

        snippet = response['items'][0]['snippet']

        return {
            'title': snippet.get('title'),
            'description': snippet.get('description'),
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId'),
            'thumbnails': snippet.get('thumbnails', {}),
            'channel_title': snippet.get('channelTitle'),
            'published_at': snippet.get('publishedAt')
        }

    except HttpError as e:
        if e.resp.status == 404:
            raise Exception("Video not found")
        elif e.resp.status == 403:
            raise Exception("Access forbidden")
        raise
```

### Example 2: Fetch Video Statistics

```python
# Source: Based on existing app.py pattern + YouTube API docs
import isodate

@lru_cache(maxsize=100)
def get_video_statistics(video_id):
    """
    Fetch video statistics from YouTube API
    Quota cost: 1 unit
    """
    try:
        request = youtube.videos().list(
            part='statistics,contentDetails',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise Exception("Video not found")

        stats = response['items'][0]['statistics']
        details = response['items'][0]['contentDetails']

        # Parse ISO 8601 duration
        duration_parsed = parse_duration(details.get('duration', 'PT0S'))

        return {
            'view_count': int(stats.get('viewCount', 0)),
            'like_count': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0)),
            'duration': duration_parsed,
            'definition': details.get('definition'),  # 'hd' or 'sd'
            'caption': details.get('caption') == 'true'  # boolean
        }

    except HttpError as e:
        if e.resp.status == 404:
            raise Exception("Video not found")
        elif e.resp.status == 403:
            raise Exception("Access forbidden")
        raise

def parse_duration(iso_duration):
    """Parse ISO 8601 duration string to dict"""
    duration = isodate.parse_duration(iso_duration)
    total_seconds = int(duration.total_seconds())
    return {
        'raw': iso_duration,
        'total_seconds': total_seconds,
        'hours': total_seconds // 3600,
        'minutes': (total_seconds % 3600) // 60,
        'seconds': total_seconds % 60
    }
```

### Example 3: Unified Video Data Endpoint

```python
# Source: Based on concurrent.futures pattern
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

@app.route('/api/video/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def unified_video_data(video_id):
    """Fetch complete video data: transcript + metadata + stats"""
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        # Fetch all data in parallel
        result = get_unified_video_data(video_id)

        # Check if any data was retrieved successfully
        if not result['success']:
            return jsonify({
                'error': 'Failed to retrieve video data',
                'details': result['errors']
            }), 500

        # Partial success warning
        if result['partial_success']:
            return jsonify(result), 207  # Multi-Status for partial success

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@lru_cache(maxsize=100)
def get_unified_video_data(video_id):
    """Fetch transcript, metadata, and statistics in parallel"""
    result = {
        'success': True,
        'partial_success': False,
        'video_id': video_id,
        'quota_cost': 3,  # 3 API calls
        'transcript': None,
        'metadata': None,
        'statistics': None,
        'errors': []
    }

    fetch_functions = {
        'transcript': functools.partial(get_transcript, video_id),
        'metadata': functools.partial(get_video_metadata, video_id),
        'statistics': functools.partial(get_video_statistics, video_id)
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(func): name
            for name, func in fetch_functions.items()
        }

        for future in as_completed(futures):
            field_name = futures[future]
            try:
                result[field_name] = future.result()
            except Exception as e:
                result[field_name] = None
                result['errors'].append({
                    'field': field_name,
                    'error': str(e)
                })
                result['partial_success'] = True

    # Check overall success
    if result['errors']:
        result['success'] = any([
            result['transcript'] is not None,
            result['metadata'] is not None,
            result['statistics'] is not None
        ])

    return result
```

### Example 4: Metadata Endpoint Route

```python
# Source: Following existing app.py pattern
@app.route('/api/metadata/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def metadata(video_id):
    """Fetch video metadata endpoint"""
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
```

### Example 5: Statistics Endpoint Route

```python
# Source: Following existing app.py pattern
@app.route('/api/statistics/<video_id>', methods=['GET'])
@limiter.limit("10 per minute")
def statistics(video_id):
    """Fetch video statistics endpoint"""
    try:
        if not is_valid_video_id(video_id):
            return jsonify({
                'error': 'Invalid video ID format'
            }), 400

        stats_data = get_video_statistics(video_id)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'quota_cost': 1,
            'statistics': stats_data
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
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Synchronous API calls for unified endpoint | Parallel calls with ThreadPoolExecutor | Python 3.2+ (2011) | 3x faster unified endpoint responses |
| Custom duration parsing | isodate library | 2012+ | More reliable, handles edge cases |
| Manual threading | concurrent.futures | Python 3.2+ (2011) | Standard, tested, simpler code |
| Separate quota tracking per endpoint | quota_cost field in all responses | Modern best practice | Transparency for API consumers |

**Deprecated/outdated:**
- **dislikeCount** field: YouTube made this private in December 2021, don't include it
- **favoriteCount** field: Deprecated August 2015, always returns 0
- **Custom regex for duration parsing**: Prone to errors, use `isodate`

## Open Questions

1. **Thumbnail resolution selection**
   - What we know: YouTube provides default, medium, high, standard, and maxres thumbnails
   - What's unclear: Which thumbnail resolution should be the default in API response
   - Recommendation: Return all thumbnail resolutions in response, let client choose

2. **Tags field behavior**
   - What we know: `snippet.tags` is optional and may be missing
   - What's unclear: Should we return empty list or omit field when tags not present
   - Recommendation: Return empty list `[]` when tags missing for consistency

3. **Unified endpoint failure behavior**
   - What we know: Parallel requests may have partial failures
   - What's unclear: Should unified endpoint return 207 (Multi-Status) or 200 with `partial_success` flag
   - Recommendation: Use 207 when `partial_success=True`, 200 when all successful

4. **Duration format in response**
   - What we know: Duration can be returned as raw ISO string, total seconds, or h/m/s components
   - What's unclear: Which format do users prefer
   - Recommendation: Return all formats (dict with raw, total_seconds, hours, minutes, seconds)

## Sources

### Primary (HIGH confidence)
- [YouTube Data API v3 - Videos: list](https://developers.google.com/youtube/v3/docs/videos/list) - API method documentation, quota cost, part parameter
- [YouTube Data API v3 - Videos Resource](https://developers.google.com/youtube/v3/docs/videos) - Complete video resource structure with snippet, statistics, contentDetails
- [Python concurrent.futures Documentation](https://docs.python.org/3/library/concurrent.futures.html) - Official ThreadPoolExecutor documentation
- [isodate PyPI Package](https://pypi.org/project/isodate/) - ISO 8601 parsing library
- [Flask Error Handling Documentation](https://flask.palletsprojects.com/en/stable/errorhandling/) - Official Flask error handling patterns

### Secondary (MEDIUM confidence)
- [BetterStack - Flask Error Handling Patterns](https://betterstack.com/community/guides/scaling-python/flask-error-handling/) - Error handling best practices, verified against official docs
- [Medium - Mastering Error Handling in Flask](https://medium.com/@dmostoller/mastering-error-handling-in-flask-with-werkzeug-exceptions-ensuring-robust-server-side-validations-a00a9862566a) - Werkzeug exception usage, aligns with Flask docs
- [ZenRows - Parallel Requests in Python](https://www.zenrows.com/blog/python-parallel-requests) - ThreadPoolExecutor patterns, verified with Python docs
- [Elfsight - YouTube Data API v3 Guide](https://elfsight.com/blog/youtube-data-api-v3-limits-operations-resources-methods-etc/) - Quota costs and limits, verified with Google docs
- [GetLate.dev - YouTube API Limits 2026](https://getlate.dev/blog/youtube-api-limits-how-to-calculate-api-usage-cost-and-fix-exceeded-api-quota) - Current quota information, aligns with official docs
- [YouTube API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost) - Official quota cost calculator

### Tertiary (LOW confidence)
- [Stack Overflow - Parsing ISO 8601 Durations](https://stackoverflow.com/questions/25296416/how-can-i-parse-and-compare-iso-8601-durations-in-python) - Community discussion, verified with isodate docs (upgraded to MEDIUM)
- [Stack Overflow - Handling Multiple Requests in Flask](https://stackoverflow.com/questions/14672753/handling-multiple-requests-in-flask) - Community discussion, verified with Flask docs (upgraded to MEDIUM)
- [Various Medium/blog posts on concurrent.futures] - Community patterns, verified with Python docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official documentation (PyPI, Python docs, Google docs)
- Architecture: HIGH - YouTube API usage patterns verified with official Google documentation, concurrency patterns verified with Python docs
- Pitfalls: HIGH - Based on official documentation and common error patterns documented in community resources

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - standard library stability, but verify YouTube API changes)
