# YouTube Data API

## What This Is

A comprehensive REST API and MCP server for fetching YouTube video data — transcripts, comments, metadata, channel info, and related videos. Designed for AI automation workflows, particularly n8n-based content creation pipelines. Single process exposes both REST endpoints for direct HTTP access and MCP tools for AI agent integration.

## Core Value

Get YouTube video data into AI workflows with minimal friction — REST for flexibility, MCP for seamless n8n integration.

## Requirements

### Validated

<!-- Shipped and confirmed working. -->

- ✓ Fetch video transcripts with optional timestamps — existing
- ✓ Fetch video comments with configurable limit — existing
- ✓ Rate limiting (100/day, 10/min per IP) — existing
- ✓ LRU caching for API responses — existing
- ✓ Video ID validation (11-char format) — existing
- ✓ Comprehensive error handling with proper HTTP status codes — existing
- ✓ Web UI for testing endpoints — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Fetch video metadata (title, description, duration, publish date, views, likes)
- [ ] Fetch channel info (name, subscriber count, video list)
- [ ] Fetch related/suggested videos
- [ ] MCP server interface exposing all endpoints as tools
- [ ] Single process serving both REST and MCP interfaces

### Out of Scope

- Playlist management — not needed for content creation workflows
- Video upload/modification — read-only API
- User authentication/OAuth — API key sufficient for data access
- Real-time subscriptions/webhooks — polling sufficient for automation
- Mobile app — server-only deployment

## Context

**Existing codebase:**
- Flask 3.0 monolithic REST API in `app.py`
- youtube-transcript-api for transcript scraping
- google-api-python-client for YouTube Data API v3
- Deployed to Railway.com

**Known limitations:**
- YouTube blocks most cloud provider IPs for transcript scraping
- Transcript endpoint may return `RequestBlocked` on Railway
- Comments and metadata endpoints use official API (should work fine)

**Target integration:**
- n8n workflows as MCP client
- Content creation automation pipelines
- AI agents needing YouTube context

## Constraints

- **Tech stack**: Python/Flask — extend existing codebase, don't rewrite
- **API key**: YouTube Data API v3 key required (already in use)
- **Deployment**: Railway.com — must work in containerized cloud environment
- **MCP protocol**: Must follow MCP specification for tool definitions

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Same process for REST + MCP | Shared logic, single deployment, simpler maintenance | — Pending |
| Extend Flask app vs new framework | Preserve working code, minimize risk | — Pending |
| Accept transcript IP blocking for v1 | Not a blocker, can add proxy/third-party later | — Pending |

---
*Last updated: 2026-01-22 after initialization*
