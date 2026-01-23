# Architecture

**Analysis Date:** 2026-01-22

## Pattern Overview

**Overall:** Monolithic REST API with single-entry-point server

**Key Characteristics:**
- Single Flask application file (`app.py`) containing all server logic, routes, and business logic
- RESTful API design with two main endpoints
- Synchronous request/response handling
- LRU caching layer for function-level memoization
- Rate limiting applied at route decorator level

## Layers

**Presentation Layer:**
- Purpose: Serve HTML UI and handle HTTP requests
- Location: `templates/index.html`, `static/js/script.js`, `static/css/style.css`
- Contains: Bootstrap UI components, client-side fetch handlers, form validation
- Depends on: Flask route `/` rendering templates
- Used by: End users via web browser

**API Route Layer:**
- Purpose: Define HTTP endpoints and validate requests
- Location: `app.py` routes (lines 80-189)
- Contains: Route decorators (`@app.route`), request parameter parsing, rate limiter application
- Depends on: Business logic functions, Flask framework
- Used by: Client-side JavaScript, external API consumers

**Business Logic Layer:**
- Purpose: Fetch and process YouTube data from external APIs
- Location: `app.py` functions (lines 36-78): `get_transcript()`, `get_video_comments()`, `process_transcript()`, `is_valid_video_id()`
- Contains: Core application logic, data transformation, validation rules
- Depends on: YouTube external APIs, LRU cache decorator
- Used by: API route handlers

**External API Integration Layer:**
- Purpose: Interface with external services
- Location: `app.py` initialization (lines 28-33)
- Contains: SDK/client instantiation for `YouTubeTranscriptApi` and Google API client
- Depends on: Environment variables for configuration
- Used by: Business logic functions

**Error Handling Layer:**
- Purpose: Catch and transform exceptions into JSON responses
- Location: `app.py` route try/catch blocks (lines 86-144, 149-181) and error handler (lines 183-188)
- Contains: Exception type matching, error message formatting, HTTP status code mapping
- Depends on: SDK exception types
- Used by: All routes

**Caching Layer:**
- Purpose: Reduce API calls and improve response time
- Location: `app.py` decorator usage (lines 36, 41): `@lru_cache(maxsize=100)`
- Contains: In-memory LRU cache with 100-item limit
- Depends on: Python functools module
- Used by: `get_transcript()` and `get_video_comments()` functions

**Rate Limiting Layer:**
- Purpose: Enforce request quotas per IP address
- Location: `app.py` limiter setup (lines 22-26) and route decorators (lines 85, 147)
- Contains: Flask-Limiter configuration with default limits
- Depends on: Flask-Limiter, client IP detection
- Used by: All API endpoints

## Data Flow

**Transcript Fetch Flow:**

1. User enters video ID in UI (`templates/index.html`)
2. Client JavaScript posts fetch request to `GET /api/transcript/<video_id>`
3. Rate limiter checks request quota (10/minute limit)
4. Route handler validates video ID using `is_valid_video_id()` regex
5. Route handler calls cached function `get_transcript(video_id)`
6. Cache checks for existing result; if miss, calls `YouTubeTranscriptApi().fetch(video_id)`
7. External API returns transcript object; `to_raw_data()` converts to dictionary
8. `process_transcript()` formats output based on timestamps parameter
9. Route handler returns JSON response with metadata
10. JavaScript displays response in UI

**Comments Fetch Flow:**

1. User enters video ID and max results in UI
2. Client JavaScript posts fetch request to `GET /api/comments/<video_id>?max_results=N`
3. Rate limiter checks request quota
4. Route handler validates video ID format
5. Route handler calls cached function `get_video_comments(video_id, max_results)`
6. Cache checks for existing result; if miss, calls Google API
7. Google API returns comment threads in paginated format
8. Business logic extracts relevant fields (author, text, likes, published_at)
9. Returns comments list as JSON
10. Error handler catches HTTP 403 (comments disabled) or quota exceeded scenarios
11. JavaScript displays response or error in UI

**State Management:**

- **Request State:** Stateless per-request; no session management
- **Cache State:** In-memory LRU cache shared across all concurrent requests (thread-safe via GIL)
- **Configuration State:** Environment variables loaded at startup (immutable during runtime)

## Key Abstractions

**Validation Abstraction:**
- Purpose: Ensure video IDs conform to YouTube format
- Examples: `is_valid_video_id()` function (line 76)
- Pattern: Regex matching against 11-character alphanumeric with `-` and `_`

**Processing Abstraction:**
- Purpose: Transform transcript data based on user preference
- Examples: `process_transcript()` function (line 69)
- Pattern: Conditional formatting (with/without timestamps)

**Comment Extraction Abstraction:**
- Purpose: Extract relevant fields from verbose Google API response
- Examples: Nested loop in `get_video_comments()` (lines 54-61)
- Pattern: Destructure nested response objects, map to simplified schema

**Caching Abstraction:**
- Purpose: Transparent memoization of expensive API calls
- Examples: `@lru_cache(maxsize=100)` on functions
- Pattern: Python decorator, automatic cache invalidation not implemented (TTL-less)

**Rate Limiting Abstraction:**
- Purpose: Prevent abuse via request quotas
- Examples: `@limiter.limit("10 per minute")` on routes
- Pattern: Declarative decorator with IP-based tracking

## Entry Points

**Server Entry Point:**
- Location: `main.py`
- Triggers: `python main.py` command
- Responsibilities: Import Flask app from `app.py` and run development server on 0.0.0.0:5000

**Web Entry Point:**
- Location: `GET /` route in `app.py` (line 80)
- Triggers: Browser navigation to root URL
- Responsibilities: Render `index.html` template with embedded documentation and testing UI

**API Entry Point - Transcripts:**
- Location: `GET /api/transcript/<video_id>` route in `app.py` (line 84)
- Triggers: HTTP GET request with video ID in path
- Responsibilities: Validate input, fetch transcript, format output, handle errors

**API Entry Point - Comments:**
- Location: `GET /api/comments/<video_id>` route in `app.py` (line 146)
- Triggers: HTTP GET request with video ID in path and optional max_results parameter
- Responsibilities: Validate input, fetch comments, format output, handle YouTube API errors

## Error Handling

**Strategy:** Exception type matching with HTTP status code mapping; clients receive standardized JSON error objects

**Patterns:**

**Transcript Errors:**
- `NoTranscriptFound`: Return 404 with "No transcript found for this video"
- `VideoUnavailable`: Return 404 with "Video is unavailable"
- `RequestBlocked`: Return 503 with IP restriction details
- `AgeRestricted`: Return 403 with age verification message
- `VideoUnplayable`: Return 403 with specific error details
- `ParseError`: Return 503 with invalid response note
- Generic `Exception`: Return 500 with details

**Comments Errors:**
- HTTP 403 from Google API: Transformed to "Comments are disabled"
- "quota" in error message: Return 429 for quota exceeded
- Generic exception: Return 500 with error details

**Rate Limiting Errors:**
- Rate limit exceeded: Flask-Limiter returns 429 with description

## Cross-Cutting Concerns

**Logging:** Not detected; uses print/console debugging only (no structured logging framework)

**Validation:**
- Video ID format: Regex pattern validates 11-character alphanumeric with `-` and `_`
- Max results: Integer validation with 100-item cap applied in comments route

**Authentication:** None; API is public/unauthenticated. Comments endpoint requires `YOUTUBE_API_KEY` environment variable for OAuth token, but no user authentication at HTTP layer.

**CORS:** Not configured; Flask defaults prevent cross-origin requests from browsers. Single-origin assumption (served from same domain).

**Configuration Management:** Environment variable loading at module level (`os.environ['YOUTUBE_API_KEY']`); will fail fast if missing.

---

*Architecture analysis: 2026-01-22*
