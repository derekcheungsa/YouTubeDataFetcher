# Codebase Structure

**Analysis Date:** 2026-01-22

## Directory Layout

```
YouTubeDataFetcher/
├── main.py                 # Application entry point; imports and runs Flask server
├── app.py                  # Core application logic; all routes, APIs, and business logic
├── requirements.txt        # Python package dependencies
├── pyproject.toml          # Project metadata and alternate dependency specification
├── CLAUDE.md               # Developer instructions for Claude AI
├── README.md               # Project documentation
├── Dockerfile              # Container configuration
├── .replit                 # Replit environment configuration
├── replit.nix              # Nix package manager configuration
├── uv.lock                 # UV package manager lock file
├── generated-icon.png      # Application icon asset
├── templates/              # HTML templates
│   └── index.html          # Single-page documentation and API testing UI
├── static/                 # Frontend static assets
│   ├── css/
│   │   └── style.css       # Custom CSS styles (minimal; mostly Bootstrap)
│   └── js/
│       └── script.js       # Client-side JavaScript for API interaction
└── .git/                   # Git repository metadata
```

## Directory Purposes

**Project Root:**
- Purpose: Top-level configuration and entry points
- Contains: Python entry point, dependency specs, documentation, config files
- Key files: `main.py`, `app.py`, `requirements.txt`

**templates/**
- Purpose: Server-side rendered HTML templates
- Contains: Single Jinja2 HTML file serving documentation and testing interface
- Key files: `index.html` (9.3KB bootstrap-based UI)

**static/css/**
- Purpose: Cascading stylesheets for frontend
- Contains: Custom CSS overrides for Bootstrap theme
- Key files: `style.css`

**static/js/**
- Purpose: Client-side JavaScript for interactive API testing
- Contains: Fetch handlers, DOM event listeners, user input validation
- Key files: `script.js` (114 lines)

## Key File Locations

**Entry Points:**
- `main.py`: Server startup; runs Flask app on 0.0.0.0:5000
- `templates/index.html`: Web UI entry point; serves documentation and test console

**Core Logic:**
- `app.py`: Monolithic file containing all application logic
  - Flask app initialization (lines 19-30)
  - Cache setup (lines 35-39)
  - Business functions (lines 41-78)
  - Route handlers (lines 80-189)

**Configuration:**
- `requirements.txt`: Runtime dependencies (pip-managed)
- `pyproject.toml`: Project metadata and dependency specification
- Environment variables: `YOUTUBE_API_KEY` (required for comments endpoint)

**Testing:**
- No test files present; manual testing via UI or API client tools

**Frontend:**
- `templates/index.html`: All HTML (no template logic beyond `render_template()`)
- `static/js/script.js`: Event handlers and fetch logic
- `static/css/style.css`: Custom styling

## Naming Conventions

**Files:**
- Entry point: `main.py` (lowercase, single word)
- Application: `app.py` (lowercase, single word)
- Assets: lowercase with hyphens (e.g., `style.css`, `script.js`)
- Config: lowercase with dots (e.g., `pyproject.toml`)

**Functions:**
- Snake case: `get_transcript()`, `get_video_comments()`, `process_transcript()`, `is_valid_video_id()`, `getElement()` (in JavaScript)
- Descriptive verbs: start with action (get, process, is, handle)

**Variables:**
- Snake case in Python: `video_id`, `max_results`, `include_timestamps`, `transcript_list`
- Camel case in JavaScript: `videoId`, `fetchTranscriptButton`, `commentsResultDiv`

**Routes:**
- Lowercase path segments: `/api/transcript/<video_id>`, `/api/comments/<video_id>`
- RESTful pattern: Resource name followed by ID path parameter

**Classes/Instances:**
- Flask app: `app` (lowercase module-level instance)
- Limiter: `limiter` (lowercase module-level instance)
- API clients: `youtube` (Google API), `ytt_api` (YouTube Transcript API)

## Where to Add New Code

**New Endpoint:**
- Implementation: `app.py` - add route function after line 189, following existing pattern
- Pattern: Use `@app.route()` decorator, `@limiter.limit()` for rate limiting, try/catch for errors
- Example location: After the `ratelimit_handler` function

**New Business Logic Function:**
- Implementation: `app.py` between lines 36-78
- Pattern: Use `@lru_cache(maxsize=100)` if caching is beneficial; pure functions preferred
- Should call external APIs and return formatted data

**New Frontend Feature:**
- HTML: `templates/index.html` - add new card/section with form controls
- JavaScript: `static/js/script.js` - add event listener and fetch handler following existing pattern
- Styling: `static/css/style.css` - override Bootstrap defaults if needed

**Shared Utilities:**
- No utilities file exists; add new file `utils.py` in project root for shared functions
- Alternative: Keep in `app.py` if only used once or twice

**Dependencies:**
- Add to `requirements.txt` with pinned version
- Also update `pyproject.toml` if using modern Python packaging

## Special Directories

**static/**
- Purpose: Serve unversioned static files to browser
- Generated: No (manually created)
- Committed: Yes

**templates/**
- Purpose: Store Jinja2 templates rendered by Flask
- Generated: No (manually created)
- Committed: Yes

**.git/**
- Purpose: Git repository history and metadata
- Generated: Yes (by git init)
- Committed: No (part of VCS itself)

**.planning/**
- Purpose: GSD phase planning documents
- Generated: Yes (by GSD orchestrator)
- Committed: No (development-only)

**.claude/**
- Purpose: Claude Code IDE configuration
- Generated: Yes (by Claude IDE)
- Committed: No (IDE-specific)

## Module Organization

**app.py Module Exports:**
- `app`: Flask application instance (used by `main.py`)
- Implicit: All route handlers are registered via decorators during import

**main.py Module:**
- Imports: `app` from `app.py`
- Responsibility: Single execution (server startup)

**Frontend Modules:**
- `index.html`: Self-contained HTML; loads Bootstrap CDN and local CSS
- `script.js`: Vanilla JavaScript; no module system (global scope)
- `style.css`: CSS cascade; no organization system

## Import Patterns

**Python:**
- Standard library imports first (os, re, functools)
- Third-party imports next (flask, youtube_transcript_api, google-api-python-client)
- No circular dependencies
- All imports at module top level in `app.py`

**JavaScript:**
- No imports; vanilla JavaScript with inline event listeners
- Globals: `document` object used directly
- Load order: Bootstrap JS before custom script.js

## Configuration Locations

**Environment Configuration:**
- `YOUTUBE_API_KEY`: Required; set before server startup
- Accessed in `app.py` line 29: `os.environ['YOUTUBE_API_KEY']`
- Missing variable causes KeyError at import time (fail-fast)

**Flask Configuration:**
- Server host/port hardcoded in `main.py`: `0.0.0.0:5000`
- Rate limiting defaults hardcoded in `app.py` lines 25-26

**External Service Configuration:**
- YouTube Transcript API: Default endpoint (no custom config)
- Google YouTube Data API: Uses `YOUTUBE_API_KEY` for authentication

---

*Structure analysis: 2026-01-22*
