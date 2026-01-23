# Phase 4: MCP Server - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

## Phase Boundary

Implement MCP (Model Context Protocol) server interface that exposes YouTube data fetching through AI-optimized tools. Single Python process runs both Flask REST API and FastMCP server using streamable HTTP transport. Three high-level tools provide workflow-based access: analyze_video (unified data bundle), search_youtube_content (keyword search via YouTube Search API), and get_channel_overview (channel info + recent uploads).

## Implementation Decisions

### MCP Tool Design
- **3 workflow tools** — Progressive disclosure pattern, not API mirror
  - `analyze_video(video_url_or_id)` — Returns transcript + metadata + statistics + comments in one call
  - `search_youtube_content(query)` — Finds videos by keyword using YouTube Search API
  - `get_channel_overview(channel_id_or_url)` — Returns channel info with recent uploads
- **Accept both URLs and IDs** — Tools extract video ID from full YouTube URLs automatically
- **Full bundle for analyze_video** — Always fetch all data types (transcript, metadata, statistics, comments)
- **Structured JSON responses** — All tools return structured JSON for LLM consumption
- **Graceful degradation** — If some data fails (e.g., transcript blocked), return available data with errors array

### Transport Architecture
- **Streamable HTTP transport** — MCP server uses HTTP/SSE for communication
- **Single Python process** — Flask and FastMCP mounted together in ASGI application
- **Deployment target** — Railway.com (must work in containerized cloud environment)
- **No stdio support initially** — Focus on HTTP transport for n8n integration (can add stdio later if needed)

### Data Bundling
- **analyze_video always returns full bundle** — All 4 data types: transcript, metadata, statistics, comments
- **Parallel fetching** — Use ThreadPoolExecutor like unified endpoint to fetch data concurrently
- **quota_cost=4** — One unit per data type (transcript=0 via scraping, metadata=1, stats=1, comments=1)
- **Response format matches unified endpoint** — Reuse get_unified_video_data() logic where possible

### Tool Discovery Pattern
- **Resource listing** — Expose tools via MCP tool list capability
- **Clear tool descriptions** — Each tool has description explaining what it does and what it returns
- **Structured schemas** — Tool parameters defined with JSON schemas for validation
- **No categories** — Keep it simple with just 3 tools for Phase 4

### Search Implementation
- **YouTube Search API** — Use official YouTube Data API v3 search endpoint
- **100 quota units per call** — Search is expensive, make this clear in tool description
- **Returns video list** — Array of video IDs, titles, thumbnails, descriptions
- **User can then analyze_video** — Search results feed into analyze_video tool

### Error Handling
- **Graceful degradation** — If transcript fails (IP block), return other data with error details
- **User-friendly error messages** — "Transcript unavailable (video may be restricted)" instead of technical codes
- **Partial success flag** — Indicate which data succeeded/failed
- **HTTP status codes** — 200 for success, 207 for partial, 500 for complete failure

### Claude's Discretion
- Exact tool parameter names and JSON schema structures
- Tool descriptions and help text
- Error message wording
- Whether to include debug/logging information
- Search result limit (default to 10 results)

## Specific Ideas

- "I want to use this from n8n workflows" — HTTP transport is critical
- Full bundle approach means analyze_video might be slow but comprehensive
- Graceful degradation is important because YouTube transcript scraping gets blocked on cloud IPs
- Search API is expensive (100 units) so limit results by default

## Deferred Ideas

- Discovery features (channels, playlists, related videos) — Phase 2, not yet implemented
- Service layer refactoring — Phase 3, not yet done
- stdio transport for local development — Can add later if needed
- Batch operations — Not in v1 scope
- Configurable data fetching (include/exclude parameters) — Full bundle simplifies MVP

---

*Phase: 04-mcp-server*
*Context gathered: 2026-01-23*
