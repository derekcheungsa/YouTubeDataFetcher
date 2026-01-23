# Phase 1: Core Metadata - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

## Phase Boundary

Extend the existing Flask REST API with three new endpoints for YouTube video data:
- Video metadata endpoint (title, description, tags, category, thumbnails)
- Video statistics endpoint (views, likes, comment count, duration)
- Unified video data endpoint (transcript + metadata + stats combined)

All endpoints must return consistent JSON structure matching existing transcript/comments endpoints, expose quota costs, and handle errors gracefully. This is backend API work — no UI/UX considerations.

## Implementation Decisions

### API Response Structure
- **Flat structure** — minimal nesting in response objects
- **Wrapped response** — success field + data object + metadata wrapper (not direct data)
- **Include metadata in wrapper** — request_id, timestamp, quota_cost
- **snake_case naming** — video_id, view_count, etc. (Python/Flask convention)
- **ISO 8601 timestamps** — '2025-01-22T10:30:00Z' format
- **Best quality thumbnail only** — single URL field, not all quality variants

### Error Handling
- **Graceful degradation** — partial data returned with error indicator
- **Explicit partial_success flag** — set to true when some data fetches fail
- **Include error_details array** — lists what failed and why
- **Zero retries** — respect YouTube API response immediately, no retry logic
- **Friendly error messages** — user-readable text, not technical codes
- **No quota cost on errors** — only count successful API calls

### Quota Tracking
- **Response body** — include quota_cost field in response body (not headers)
- **Top-level field** — quota_cost at same level as data/success
- **Per-request cost** — cost for the specific API call(s) made

### Unified Endpoint Design
- **Full bundle always** — /api/video/<id> returns transcript + metadata + stats
- **No filtering params** — single endpoint, no ?include= or ?fields= options
- **Parallel requests** — fetch transcript, metadata, stats concurrently for speed
- **All-or-nothing fallback** — if parallel fetch fails, degrade gracefully with partial_success flag

### Caching Strategy
- **Independent caching** — separate LRU caches for each endpoint type
- **Cache keys** — based on video_id + endpoint type
- **Shared cache size** — maintain 100-entry limit across all caches (existing pattern)

### Claude's Discretion
- Exact field names within the flat structure
- Response metadata fields beyond request_id/timestamp/quota_cost
- Cache TTL and eviction policy
- HTTP status codes for specific error scenarios
- Logging verbosity for debugging API calls

## Specific Ideas

- "Follow the existing pattern from transcript/comments endpoints" — maintain consistency
- Graceful degradation is important because YouTube API has intermittent failures
- Parallel fetching for unified endpoint balances speed vs quota cost
- Independent caching keeps each endpoint's cache behavior predictable

## Deferred Ideas

- Add batch operations (multiple videos in one request) — defer to post-MVP
- Add field filtering parameters (?fields=) — defer if users request it
- Add response compression (gzip) — defer to performance optimization phase
- Add rate limiting per API key — current IP-based limiting is sufficient

---

*Phase: 01-core-metadata*
*Context gathered: 2026-01-22*
