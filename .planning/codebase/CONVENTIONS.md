# Coding Conventions

**Analysis Date:** 2026-01-22

## Naming Patterns

**Files:**
- Lowercase with underscores for Python modules: `app.py`, `main.py`
- camelCase for JavaScript files: `script.js`, `style.css`
- Consistent, descriptive names reflecting module purpose

**Functions:**
- snake_case for Python functions: `get_transcript()`, `get_video_comments()`, `is_valid_video_id()`
- camelCase for JavaScript functions: `getElement()`, `fetchTranscriptButton.addEventListener()`
- Private/helper functions use same convention without leading underscore

**Variables:**
- snake_case in Python: `video_id`, `include_timestamps`, `max_results`, `error_message`
- camelCase in JavaScript: `videoId`, `includeTimestamps`, `maxResults`
- Descriptive names that indicate purpose: `fetchTranscriptButton`, `transcriptResponseData`

**Constants:**
- UPPERCASE_WITH_UNDERSCORES for Python constants: `YOUTUBE_API_KEY`

**Classes:**
- PascalCase for Flask application: `Flask`, `YouTubeTranscriptApi`

## Code Style

**Formatting:**
- No explicit formatter configured (not detected in codebase)
- Consistent indentation: 4 spaces in Python, 2-4 spaces in JavaScript
- Blank lines separate logical sections within functions
- Line breaks after imports with blank line before code (Python PEP 8 style)

**Linting:**
- No linter configuration detected
- Code follows implicit PEP 8 conventions for Python
- JavaScript lacks explicit linting rules

## Import Organization

**Python Order (in `app.py`):**
1. Standard library imports (`os`, `re`, `functools.lru_cache`)
2. Third-party Flask imports (`flask`, `flask_limiter`)
3. Third-party YouTube/Google API imports (`youtube_transcript_api`, `googleapiclient`)
4. Exception imports from third-party libraries
5. XML parsing utilities (`xml.etree.ElementTree`)

Example from `app.py`:
```python
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
```

**Path Aliases:**
- Not used in this codebase

## Error Handling

**Patterns:**
- Explicit exception catching in Flask route handlers (`try/except` blocks)
- Specific exception types caught first, then generic `Exception` as fallback
- Each exception returns appropriate HTTP status code with JSON error response
- Broad exception handling in `comments()` endpoint uses string matching for error categorization

Example from `transcript()` endpoint in `app.py` (lines 86-144):
```python
try:
    if not is_valid_video_id(video_id):
        return jsonify({'error': 'Invalid video ID format'}), 400
    # ...
except NoTranscriptFound:
    return jsonify({'error': 'No transcript found for this video'}), 404
except VideoUnavailable:
    return jsonify({'error': 'Video is unavailable'}), 404
except RequestBlocked:
    return jsonify({'error': 'Request blocked by YouTube', ...}), 503
# ... more specific exceptions
except Exception as e:
    return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
```

**Error Response Format:**
- JSON with `error` key (string)
- Optional `details` key for additional context
- Corresponding HTTP status codes (400, 403, 404, 429, 500, 503)

## Logging

**Framework:** console-based (not explicitly configured)

**Patterns:**
- JavaScript uses `console.warn()` for non-critical issues: `console.warn(`Element with id '${id}' not found`);`
- Python does not include logging framework (uses exception raising instead)
- No centralized logging layer; logging would be added to Flask if needed

## Comments

**When to Comment:**
- Explain non-obvious logic or constraints
- Document regex patterns and validation rules
- Flag known issues and workarounds

Examples from codebase:
- Line 77-78 in `app.py`: Comment explains YouTube video ID format: `# Basic YouTube video ID validation (11 characters, alphanumeric with some special chars)`
- Line 72-73: Comment explains parameter behavior: `# Combine all text segments into a single string when timestamps=false`
- JavaScript line 2-10: Helper function with clear purpose documented

**JSDoc/TSDoc:**
- Not used in this JavaScript codebase
- Python lacks docstrings in current code

## Function Design

**Size:**
- Small, focused functions handling single responsibility
- Helper functions like `is_valid_video_id()` (3 lines), `getElement()` (6 lines)
- Route handlers up to ~50 lines with comprehensive error handling

**Parameters:**
- Positional parameters for required values: `process_transcript(transcript_list, include_timestamps)`
- Query parameters via `request.args.get()` with defaults: `request.args.get('timestamps', 'true')`
- Type coercion handled at parameter level: `int(request.args.get('max_results', 100))`

**Return Values:**
- Flask routes return tuple of (JSON response, HTTP status code)
- Helper functions return data structures (list, dict, boolean)
- Error cases raise exceptions which are caught by route handlers

## Module Design

**Exports:**
- `app.py` exports single `Flask` app instance imported by `main.py`
- All business logic in `app.py` module (not separated into modules)
- Global instances at module level: `app`, `limiter`, `youtube`, `ytt_api`

**Barrel Files:**
- Not used (single entry point via `main.py`)

## Rate Limiting & Caching

**Patterns:**
- LRU caching on expensive operations using `@lru_cache(maxsize=100)` decorator
- Applied to `get_transcript()` and `get_video_comments()` functions
- Rate limiting via Flask-Limiter: `@limiter.limit("10 per minute")` on routes
- Default limits configured: "100 per day", "10 per minute" per IP

## Validation

**Pattern:** Validation at route level before processing

Example from `app.py` lines 88-91:
```python
if not is_valid_video_id(video_id):
    return jsonify({'error': 'Invalid video ID format'}), 400
```

Video ID validation regex: `^[A-Za-z0-9_-]{11}$` (exactly 11 alphanumeric characters, hyphens, underscores)

---

*Convention analysis: 2026-01-22*
