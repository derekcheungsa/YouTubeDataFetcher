# Technology Stack

**Analysis Date:** 2026-01-22

## Languages

**Primary:**
- Python 3.11 - Backend API server and application logic

**Secondary:**
- JavaScript (Vanilla) - Frontend client-side interactions
- HTML5 - UI template structure
- CSS3 - Styling and dark mode theme

## Runtime

**Environment:**
- Python 3.11 (specified in `pyproject.toml` requires-python)
- Docker container: `python:3.11-slim` (see `Dockerfile`)

**Package Manager:**
- pip - Python package management
- Lockfile: `uv.lock` present (using uv for dependency management)

## Frameworks

**Core:**
- Flask 3.0.0 - REST API web framework (`app.py` imports and uses Flask)

**Rate Limiting:**
- Flask-Limiter 3.5.0 - Request rate limiting middleware
  - Configured for 100 requests/day, 10 requests/minute per IP address
  - Location: `app.py` lines 22-26

**Frontend:**
- Bootstrap 5.3.0 (CDN) - Responsive UI framework, loaded from `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`
- Vanilla JavaScript - Custom client-side logic in `static/js/script.js`
- Jinja2 3.1.2 - Template engine (indirect dependency via Flask)

**ASGI/WSGI:**
- Werkzeug 3.0.1 - WSGI utility library (Flask dependency)

## Key Dependencies

**Critical:**
- youtube-transcript-api 1.2.3 - Scrapes YouTube transcripts programmatically
  - Used in `app.py` lines 2-8
  - Instance method: `ytt_api.fetch(video_id)` returns `FetchedTranscript` object
  - Call `.to_raw_data()` to convert to dictionary format
  - Error handling for: `NoTranscriptFound`, `VideoUnavailable`, `RequestBlocked`, `AgeRestricted`, `VideoUnplayable`, `ParseError`

- google-api-python-client (version not pinned in `requirements.txt`) - Official YouTube Data API v3 client
  - Used in `app.py` lines 14-15
  - Accesses `youtube.commentThreads().list()` endpoint
  - Requires `YOUTUBE_API_KEY` environment variable

**Infrastructure:**
- Flask-Limiter 3.5.0 - Rate limiting
  - Uses in-memory storage (production warning in README.md line 173)
  - Config location: `app.py` lines 22-26

- limits 3.6.0 - Rate limit specification library (dependency of Flask-Limiter)

**Utility:**
- click 8.1.7 - CLI framework (Flask dependency)
- blinker 1.7.0 - Signal support (Flask dependency)
- itsdangerous 2.1.2 - Secure signing (Flask dependency)
- MarkupSafe 2.1.3 - HTML escaping (Jinja2 dependency)
- typing_extensions 4.8.0 - Type hints backport
- ordered-set 4.1.0 - Ordered set data structure

## Configuration

**Environment:**
- `YOUTUBE_API_KEY` - Required for YouTube Data API v3 access (line 29 in `app.py`)
  - Loaded via `os.environ['YOUTUBE_API_KEY']` - will raise KeyError if missing
  - Used to authenticate YouTube API client

**Build:**
- `pyproject.toml` - Poetry/uv project metadata
  - Project name: `repl-nix-workspace`
  - Python version requirement: >=3.11
  - Contains both build dependencies and runtime dependencies

- `Dockerfile` - Container configuration
  - Base image: `python:3.11-slim`
  - Workdir: `/app`
  - Exposes port 5000
  - Entry: `python main.py`
  - Env vars set: `FLASK_ENV=production`, `FLASK_APP=main.py`

## Platform Requirements

**Development:**
- Python 3.11+
- pip or uv package manager
- YOUTUBE_API_KEY environment variable

**Production:**
- Deployment target: Docker container on cloud platforms or local server
- Platform: 0.0.0.0:5000 (accessible on all interfaces)
- Known limitation: YouTube blocks most cloud provider IPs (AWS, GCP, Railway, etc.) - see CLAUDE.md for workarounds

**Compatibility Note:**
- Project optimized for Replit deployment (see `README.md` line 169)
- Includes `.replit` configuration file for Replit environment
- Uses `replit.nix` for Nix-based environment setup

---

*Stack analysis: 2026-01-22*
