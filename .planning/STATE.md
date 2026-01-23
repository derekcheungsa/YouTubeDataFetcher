# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Get YouTube video data into AI workflows with minimal friction — REST for flexibility, MCP for seamless n8n integration

**Current focus:** Phase 4: MCP Server (COMPLETE)

## Current Position

Phase: 4 of 4 (MCP Server)
Plan: 5 of 5 in current phase
Status: Phase complete
Last activity: 2026-01-23 — Completed 04-05-PLAN.md (Dual-Server Production Architecture)

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 5 min
- Total execution time: 0.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-metadata | 3 | 3 | 6 min |
| 04-mcp-server | 5 | 5 | 5 min |

**Recent Trend:**
- Last 5 plans: 5 min (04-01), 3 min (04-02), 4 min (04-03), 4 min (04-04), 8 min (04-05)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

**From 01-01 (Video Metadata Endpoint):**
- Used flat dictionary structure with snake_case keys for metadata response to match existing API patterns
- Set quota_cost=1 for metadata endpoint (1 YouTube Data API v3 unit per request)
- Applied 10/minute rate limit to align with existing endpoints and prevent quota exhaustion
- Included full thumbnails dictionary from API response for client flexibility

**From 01-02 (Video Statistics Endpoint):**
- Parsed ISO 8601 duration to components (total_seconds, hours, minutes, seconds) for easier client consumption
- Returned duration as object with raw ISO string plus parsed components for flexibility
- Set quota_cost=1 for statistics endpoint (1 YouTube Data API v3 unit per request)
- Applied 10/minute rate limit to align with existing endpoints and prevent quota exhaustion

**From 01-03 (Unified Video Data Endpoint):**
- Used ThreadPoolExecutor with max_workers=3 to fetch all three data types concurrently for reduced latency
- Returned 207 Multi-Status for partial success (some data available, some failed) to enable graceful degradation
- Aggregated errors with field name and error message in errors array for detailed error tracking
- Set quota_cost=3 for unified endpoint (1 for each data type: transcript, metadata, statistics)
- Applied 10/minute rate limit to align with existing endpoints and prevent quota exhaustion

**From 04-01 (FastMCP Server Infrastructure):**
- Used FastMCP 2.14.4 (latest stable) instead of 3.0.0 (not yet released) for HTTP transport support
- Configured HTTP transport on port 8000 with Server-Sent Events (SSE) for n8n integration
- Added health check endpoint at /health for server monitoring
- Updated typing_extensions from ==4.8.0 to >=4.9.0 to resolve FastMCP dependency conflict
- Established tool registration pattern using @mcp.tool() decorator

**From 04-02 (analyze_video MCP Tool):**
- Used regex pattern for video ID extraction supporting all YouTube URL formats (watch, youtu.be, embed, etc.)
- Set quota_cost=4 (transcript=0, metadata=1, stats=1, comments=1) to track API usage
- Implemented partial success pattern: tool returns available data even if some fetches fail
- Created get_comments_for_video helper in app.py to provide clean interface for MCP tool
- Leveraged existing get_unified_video_data for parallel fetching via ThreadPoolExecutor

**From 04-03 (YouTube Search MCP Tool):**
- Used @lru_cache(maxsize=50) for search function (lower than data fetch due to query variability)
- Set quota_cost=100 to explicitly track and warn about expensive Search API usage (vs 1 unit for metadata/statistics)
- Included workflow_hint in response guiding users to analyze_video for complete data retrieval
- Clamped max_results parameter to 1-50 range to match YouTube API limits and prevent errors
- Ordered search results by 'relevance' to return most relevant videos first for general queries
- Extracted thumbnail with fallback chain (default -> medium -> high) to handle missing sizes gracefully

**From 04-04 (Channel Overview MCP Tool):**
- Used YouTube Channels API (snippet,statistics parts) for channel metadata - costs 1 quota unit
- Used YouTube Search API with order='date' for recent uploads - costs 1 quota unit
- Channel ID extraction regex: ^UC[A-Za-z0-9_-]{22}$ for bare IDs, youtube\.com\/channel\/(UC[A-Za-z0-9_-]{22}) for URLs
- Custom URLs (/c/username) and handles (/@username) not supported in MVP - returns helpful error message
- Set quota_cost=2 for channel overview (1 for channel info, 1 for uploads search)
- Included workflow_hint to guide users from channel overview to analyze_video() for full data
- Implemented partial success: returns channel data even if uploads fail

**From 04-05 (Dual-Server Production Architecture):**
- Used threading (daemon=True) to run MCP server in background while Flask runs in main thread
- MCP server on port 8000 via uvicorn, Flask on port 5000 in main thread
- Single `python main.py` command starts both servers simultaneously
- Added health check endpoints for both services (Flask: /health, MCP: /health)
- Updated Dockerfile to expose both ports 5000 and 8000 with health check command
- Configured for Railway deployment with HTTP transport MCP (not stdio)
- Flask health check returns MCP server location for service discovery

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

None yet.

## Session Continuity

Last session: 2026-01-23
Stopped at: Completed Phase 4 (MCP Server) - all five plans finished
Resume file: None

**Phase 1 Complete:**
- 01-01: Video Metadata Endpoint (GET /api/metadata/<video_id>)
- 01-02: Video Statistics Endpoint (GET /api/statistics/<video_id>)
- 01-03: Unified Video Data Endpoint (GET /api/video/<video_id>)

**Phase 4 Complete:**
- 04-01: FastMCP Server Infrastructure ✓
- 04-02: analyze_video MCP Tool ✓
- 04-03: YouTube Search MCP Tool ✓
- 04-04: Channel Overview MCP Tool ✓
- 04-05: Dual-Server Production Architecture ✓

**MCP Tools Implemented (3 total):**
1. analyze_video - Fetch complete YouTube video data (transcript, metadata, statistics, comments)
2. search_youtube_content - Search YouTube videos by keyword (100 quota cost)
3. get_channel_overview - Fetch channel info and recent uploads
