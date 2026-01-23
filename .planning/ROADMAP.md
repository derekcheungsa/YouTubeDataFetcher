# Roadmap: YouTube Data API

## Overview

Transform the existing Flask REST API into a dual-interface server (REST + MCP) that provides comprehensive YouTube data extraction for AI workflows. Start by extending the API with video metadata and discovery features, then refactor to a service layer architecture, and finally implement MCP tools using a progressive disclosure pattern optimized for n8n integration.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Metadata** - Extend API with video metadata, statistics, and unified data endpoint
- [ ] **Phase 2: Discovery Features** - Add channel information and video discovery endpoints
- [ ] **Phase 3: Service Layer Refactor** - Extract business logic to enable dual REST/MCP interfaces
- [ ] **Phase 4: MCP Server** - Implement MCP interface with workflow-based tools for AI agents

## Phase Details

### Phase 1: Core Metadata

**Goal**: Users can retrieve comprehensive video data (metadata, statistics, transcripts) through REST endpoints

**Depends on**: Nothing (first phase)

**Requirements**: META-01, META-02, META-03

**Success Criteria** (what must be TRUE):
1. User can fetch video metadata (title, description, tags, category, thumbnails) via `/api/metadata/<video_id>`
2. User can fetch video statistics (views, likes, comment count, duration) via `/api/statistics/<video_id>`
3. User can fetch unified video data (transcript + metadata + stats) via `/api/video/<video_id>`
4. All new endpoints return consistent JSON structure matching existing transcript/comments endpoints
5. Quota cost is visible in API responses (1 unit per metadata/stats call)

**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Implement video metadata endpoint (title, description, tags, category, thumbnails, channel info, publish date)
- [ ] 01-02-PLAN.md — Implement video statistics endpoint (views, likes, comments, duration with ISO 8601 parsing, definition, caption)
- [ ] 01-03-PLAN.md — Implement unified video data endpoint (parallel fetch of transcript + metadata + stats with partial success handling)

### Phase 2: Discovery Features

**Goal**: Users can explore YouTube content through channels, related videos, and playlists

**Depends on**: Phase 1

**Requirements**: CHAN-01, CHAN-02, DISC-01, DISC-02

**Success Criteria** (what must be TRUE):
1. User can fetch channel information (name, subscriber count, description, branding) via `/api/channel/<channel_id>`
2. User can fetch channel upload feed (recent videos from channel) via `/api/channel/<channel_id>/uploads`
3. User can fetch related/suggested videos for a video via `/api/related/<video_id>`
4. User can enumerate playlist videos with pagination via `/api/playlist/<playlist_id>`
5. All discovery endpoints include pagination support for lists > 50 items

**Plans**: TBD

Plans:
- [ ] 02-01: Implement channel information and upload feed endpoints
- [ ] 02-02: Implement related videos discovery endpoint
- [ ] 02-03: Implement playlist enumeration with pagination

### Phase 3: Service Layer Refactor

**Goal**: Business logic is extracted from Flask routes into a shared service layer, enabling both REST and MCP interfaces

**Depends on**: Phase 2

**Requirements**: SRVC-01, SRVC-02, SRVC-03

**Success Criteria** (what must be TRUE):
1. All YouTube data operations (transcript, comments, metadata, stats, channel, discovery) are available through service layer methods
2. Service layer returns plain Python objects (no HTTP/MCP coupling)
3. Flask routes are thin adapters that delegate to service layer
4. Existing REST endpoints continue working with no behavioral changes
5. Service layer is testable without Flask/MCP dependencies

**Plans**: TBD

Plans:
- [ ] 03-01: Extract YouTubeService class with all business logic
- [ ] 03-02: Refactor Flask routes to use service layer
- [ ] 03-03: Add service layer tests

### Phase 4: MCP Server

**Goal**: AI agents can access YouTube data through MCP tools optimized for n8n workflows

**Depends on**: Phase 3

**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04, MCP-05

**Success Criteria** (what must be TRUE):
1. MCP server runs alongside Flask REST API in a single Python process
2. MCP tool `analyze_video` returns unified data bundle (transcript + metadata + stats + comments)
3. MCP tool `search_youtube_content` finds videos by keyword/topic
4. MCP tool `get_channel_overview` returns channel info with recent uploads
5. MCP tools follow progressive disclosure pattern (3 high-level tools, not API mirror)
6. Both REST and MCP interfaces share the same service layer (no duplicate logic)
7. Single process serves both interfaces on Railway deployment (Streamable HTTP transport)

**Plans**: TBD

Plans:
- [ ] 04-01: Create FastMCP server with tool definitions
- [ ] 04-02: Implement analyze_video tool (unified data bundle)
- [ ] 04-03: Implement search_youtube_content tool
- [ ] 04-04: Implement get_channel_overview tool
- [ ] 04-05: Configure dual transport (stdio for local, HTTP for Railway)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Metadata | 0/3 | Not started | - |
| 2. Discovery Features | 0/3 | Not started | - |
| 3. Service Layer Refactor | 0/3 | Not started | - |
| 4. MCP Server | 0/5 | Not started | - |
