# External Integrations

**Analysis Date:** 2026-01-22

## APIs & External Services

**YouTube Transcript Fetching:**
- YouTube (via youtube-transcript-api scraping) - Retrieves video transcripts by scraping YouTube pages
  - SDK/Client: `youtube-transcript-api` v1.2.3
  - Auth: No authentication required for transcript API (scraping-based)
  - Implementation: `app.py` lines 32-39
  - Instance: `ytt_api = YouTubeTranscriptApi()`
  - Method: `ytt_api.fetch(video_id)` returns `FetchedTranscript` object
  - Cached: LRU cache with maxsize=100 on `get_transcript()` function
  - Error handling includes: NoTranscriptFound, VideoUnavailable, RequestBlocked, AgeRestricted, VideoUnplayable, ParseError

**YouTube Data API v3:**
- YouTube Data API v3 - Official Google API for fetching video metadata and comments
  - SDK/Client: `google-api-python-client` (version not pinned)
  - Auth: API key via `YOUTUBE_API_KEY` environment variable (required)
  - Implementation: `app.py` lines 29-30, 42-67
  - Endpoint: `youtube.commentThreads().list()` to fetch video comments
  - Parameters used: part="snippet", videoId, maxResults (capped at 100), order="relevance", textFormat="plainText"
  - Cached: LRU cache with maxsize=100 on `get_video_comments()` function
  - Error handling: Catches `HttpError` - returns 403 if comments disabled (line 65-66)
  - Quota management: Handles quota exceeded errors (line 173 in `app.py`)

## Data Storage

**Databases:**
- None - Not applicable. Application is stateless API with no persistent database.

**File Storage:**
- Local filesystem only - Templates in `templates/` directory, static assets in `static/` directory
  - No cloud storage integration detected

**Caching:**
- Python LRU Cache (built-in `functools.lru_cache`)
  - Location: `app.py` lines 36-39, 41-67
  - Transcript cache: maxsize=100 on `get_transcript(video_id)`
  - Comments cache: maxsize=100 on `get_video_comments(video_id, max_results)`
  - Scope: In-memory, per-process
  - Persistence: Lost on server restart

## Authentication & Identity

**Auth Provider:**
- Custom (API key-based)
  - Implementation: YouTube API key authentication via `YOUTUBE_API_KEY` environment variable
  - Method: Passed to `googleapiclient.discovery.build()` as `developerKey` parameter (line 30)
  - Scope: Only YouTube Data API v3 requires authentication
  - No user authentication system - public API endpoints

## Rate Limiting

**Rate Limiter:**
- Flask-Limiter with in-memory storage
  - Configuration: `app.py` lines 22-26
  - Default limits: 100 per day, 10 per minute per IP address
  - Per-endpoint limits: Both `/api/transcript/` and `/api/comments/` use 10 per minute (lines 85, 147)
  - Key function: `get_remote_address()` - limits by client IP address
  - Error response: 429 status code with rate limit exceeded message (lines 184-188)
  - Production warning: In-memory storage only (README.md line 173) - not suitable for distributed systems

## Monitoring & Observability

**Error Tracking:**
- None detected - No third-party error tracking service (Sentry, Rollbar, etc.)

**Logs:**
- Flask default logging - Errors returned to client via JSON response
  - Error responses include HTTP status codes and descriptive messages
  - No centralized logging system detected

## CI/CD & Deployment

**Hosting:**
- Flexible - Runs anywhere with Python 3.11 and dependencies
- Optimized for Replit (see `.replit` and `replit.nix` files)
- Docker-ready: Includes `Dockerfile` for containerized deployment
- Cloud deployment warning: YouTube blocks most cloud provider IPs (AWS, GCP, Railway, etc.) - documented in CLAUDE.md

**CI Pipeline:**
- None detected - No GitHub Actions, GitLab CI, or other CI service configuration files

## Environment Configuration

**Required env vars:**
- `YOUTUBE_API_KEY` - Google YouTube Data API v3 key (required for comments endpoint)
  - Location in code: `app.py` line 29
  - Missing this var causes application startup failure (KeyError)

**Optional env vars:**
- `FLASK_ENV` - Set to 'production' in Dockerfile (optional for development)

**Secrets location:**
- Environment variables only - No `.env` file in codebase
- Developer must set `YOUTUBE_API_KEY` before running application
- Production: Should use cloud platform secret management (AWS Secrets Manager, Google Secret Manager, etc.)

## Webhooks & Callbacks

**Incoming:**
- None detected - API is request-response only, no webhook receiver endpoints

**Outgoing:**
- None detected - Application does not make outbound callbacks or webhooks to external services

## Request/Response Integration Points

**External Request Headers:**
- User-Agent: Handled by youtube-transcript-api (HTTP requests to YouTube)
- Authorization: YouTube API key sent in API requests (handled by google-api-python-client)

**Rate Limiting Integration:**
- Flask-Limiter inspects X-Forwarded-For header for IP identification (if behind proxy)
- Default: Uses REMOTE_ADDR for direct connections

**CORS:**
- Not configured - No CORS headers set in `app.py`
- Accessible from any origin (suitable for public API)

## Known Integration Limitations

**YouTube Transcript API:**
- Cloud provider IP blocking: "YouTube blocks most cloud provider IPs (AWS, GCP, Railway, etc.)" - see CLAUDE.md
- Workarounds: Proxy services or third-party transcript API (Supadata mentioned)

**YouTube Data API v3:**
- Requires valid API key with YouTube Data API v3 quota enabled
- Comments disabled on some videos returns 403 error
- Age-restricted videos cannot be accessed

---

*Integration audit: 2026-01-22*
