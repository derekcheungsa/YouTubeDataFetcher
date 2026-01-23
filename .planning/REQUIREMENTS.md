# Requirements: YouTube Data API

**Defined:** 2026-01-22
**Core Value:** Get YouTube video data into AI workflows with minimal friction — REST for flexibility, MCP for seamless n8n integration

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Validated

Existing functionality already delivered:

- ✓ **TRAN-01**: Fetch video transcripts with optional timestamps — existing
- ✓ **COMM-01**: Fetch video comments with configurable limit — existing
- ✓ **RATE-01**: Rate limiting (100/day, 10/min per IP) — existing
- ✓ **CACHE-01**: LRU caching for API responses — existing
- ✓ **VALID-01**: Video ID validation (11-char format) — existing
- ✓ **ERR-01**: Comprehensive error handling with proper HTTP status codes — existing
- ✓ **UI-01**: Web UI for testing endpoints — existing

### Active

Current scope — building toward MCP-enabled API with metadata endpoints:

#### Video Metadata (META)

- [ ] **META-01**: Fetch video metadata (title, description, tags, category, thumbnails)
- [ ] **META-02**: Fetch video statistics (views, likes, comment count, duration)
- [ ] **META-03**: Unified video data endpoint combining transcript + metadata + stats

#### Channel Data (CHAN)

- [ ] **CHAN-01**: Fetch channel information (name, subscriber count, description, branding)
- [ ] **CHAN-02**: Fetch channel upload feed (recent videos from channel)

#### Discovery (DISC)

- [ ] **DISC-01**: Fetch related/suggested videos for a video
- [ ] **DISC-02**: Fetch playlist video enumeration with pagination

#### MCP Server (MCP)

- [ ] **MCP-01**: MCP server interface exposing all endpoints as tools
- [ ] **MCP-02**: Single process serving both REST and MCP interfaces
- [ ] **MCP-03**: MCP tool: analyze_video (unified data bundle)
- [ ] **MCP-04**: MCP tool: search_youtube_content (keyword/topic search)
- [ ] **MCP-05**: MCP tool: get_channel_overview (channel + recent uploads)

#### Service Layer (SRVC)

- [ ] **SRVC-01**: Extract service layer from Flask monolith
- [ ] **SRVC-02**: Shared business logic between REST and MCP interfaces
- [ ] **SRVC-03**: Service layer returns plain Python objects (no HTTP/MCP coupling)

### Out of Scope

Explicitly excluded from v1:

| Feature | Reason |
|---------|--------|
| Playlist management (create/update/delete) | Not needed for content creation workflows |
| Video upload/modification | Read-only API simplifies auth and scope |
| User authentication/OAuth | API key sufficient for data access |
| Real-time subscriptions/webhooks | Polling sufficient for automation |
| Mobile app | Server-only deployment |
| Batch operations (multi-video requests) | Nice-to-have, can add post-MVP when users hit quota |
| Transcript chunking/segmentation | AI enhancement, can be done client-side |
| Comment sentiment analysis | Requires additional AI model, let users analyze with their own LLMs |
| Smart caching with TTL | Adds state management complexity, LRU cache sufficient for v1 |
| Search by topic/keyword (advanced) | Search API costs 100 units/call, burns through quota fast |

## v2 Requirements

Deferred to future release. Not in current roadmap.

### Advanced Features (ADV)

- **ADV-01**: Batch operations (process multiple videos in one request)
- **ADV-02**: Smart caching with TTL based on video age/popularity
- **ADV-03**: Transcript chunking for RAG applications
- **ADV-04**: Comment sentiment pre-processing
- **ADV-05**: Search by topic/keyword (YouTube Search API integration)

### Scalability (SCALE)

- **SCALE-01**: Redis-based distributed caching
- **SCALE-02**: Rate limiting with Redis backend
- **SCALE-03**: Horizontal scaling support (multiple instances)

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| META-01 | Phase 1 | Pending |
| META-02 | Phase 1 | Pending |
| META-03 | Phase 1 | Pending |
| CHAN-01 | Phase 2 | Pending |
| CHAN-02 | Phase 2 | Pending |
| DISC-01 | Phase 2 | Pending |
| DISC-02 | Phase 2 | Pending |
| SRVC-01 | Phase 3 | Pending |
| SRVC-02 | Phase 3 | Pending |
| SRVC-03 | Phase 3 | Pending |
| MCP-01 | Phase 4 | Pending |
| MCP-02 | Phase 4 | Pending |
| MCP-03 | Phase 4 | Pending |
| MCP-04 | Phase 4 | Pending |
| MCP-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 13 total (7 Validated, 13 Active)
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-22 after initial definition*
