# 13. MVP Scope & Implementation Phases

## MVP Scope

**Included in MVP:**

- Spotify playlist import into dig queue
- Queue-based daily delivery (random pick)
- Claude-powered track description
- Telegram notification with inline feedback buttons
- Feedback collection → taste profile update (cold start)
- Auto-discovery pipeline when queue is empty (Planner → Discovery → Ranking)
- LangGraph agent orchestration (dual-mode workflow)
- Evaluation metrics
- Track deduplication
- Docker Compose infrastructure
- Basic pytest tests

**Deferred to post-MVP:**

- Knowledge graph (Neo4j)
- Discovery path visualization (D3.js frontend)
- Apple Music integration
- Multi-user support / authentication
- Cloud deployment
- CI/CD pipeline

---

## Implementation Phases

### Phase 1: Project Scaffolding & Infrastructure

1. Initialize project with Poetry (`pyproject.toml`)
2. Create `docker-compose.yml` (PostgreSQL 16, Redis 7, app service)
3. Create `Dockerfile`
4. Create `.env.example` with all env vars
5. Create `backend/config.py` with pydantic BaseSettings
6. Create `backend/database/db.py` (async SQLAlchemy engine, sessionmaker, Base)
7. Create all SQLAlchemy models (Track, DigQueue, TasteProfile, Feedback, RecommendationHistory)
8. Create `backend/database/repositories.py` (CRUD for all models)
9. Create `backend/app.py` (FastAPI with lifespan: db init, scheduler start)

**Verify**: `docker-compose up` starts all services, tables auto-created, `/docs` loads.

### Phase 2: Spotify Integration + Playlist Import

1. Create `spotify_auth.py` — OAuth flow (for private playlists)
2. Create `spotify_service.py` — `get_playlist_tracks()`, `get_recommendations()`, `get_track_audio_features()`
3. Create `queue_service.py` — queue management (add tracks, pick random, check empty)
4. Create `POST /import-playlist` endpoint (parse URL, fetch tracks, dedup, add to queue)
5. Create `GET /queue` endpoint (view pending tracks + count)
6. Add Redis caching layer for Spotify API responses

**Verify**: Import a Spotify playlist URL, see tracks in queue via `GET /queue`.

### Phase 3: Queue Delivery + Analysis Agent

1. **Analysis Agent** — Claude description generation (queue mode prompt)
2. **Delivery Agent** — Telegram message + inline keyboard buttons
3. Queue delivery logic: pick random pending track, analyze, deliver, mark as delivered
4. Create `POST /trigger-recommendation` endpoint for manual testing

**Verify**: `POST /trigger-recommendation` picks a queue track and sends a Telegram message.

### Phase 4: Feedback System

1. Telegram callback handler for inline button presses
2. Feedback Agent: parse callback → store in DB
3. Taste Modeling Agent: feedback → create/update profile with learning rates (cold start)
4. Wire automatic pipeline: button press → feedback stored → taste updated

**Verify**: Press 👍 in Telegram, confirm feedback row in DB + taste_profile created/updated.

### Phase 5: Auto-Discovery Pipeline

1. **Planner Agent** — strategy from feedback-learned taste
2. **Discovery Agent** — Spotify recommendations + dedup filtering
3. **Ranking Agent** — score candidates, pick best, queue the rest
4. Auto-discovery trigger: when queue check finds no pending tracks
5. Notification: send "Switching to auto-discovery" message via Telegram

**Verify**: Empty the queue, trigger recommendation — system fetches from Spotify and delivers.

### Phase 6: LangGraph Orchestration & Scheduler

1. Define `AgentState` TypedDict in `graph/state.py`
2. Build dual-mode StateGraph in `graph/workflow.py` (queue path vs auto-discovery path)
3. Create APScheduler cron job at 09:00 KST in `scheduler/daily_job.py`
4. Redis-based lock to prevent duplicate runs
5. Register scheduler in FastAPI lifespan

**Verify**: Set scheduler to short interval, observe full pipeline execution (both modes).

### Phase 7: Evaluation System & Remaining API Endpoints

1. Implement all metrics calculations (like_rate, skip_rate, genre_diversity, new_artist_rate)
2. Create daily metrics snapshot storage
3. Implement remaining API endpoints (see [api-endpoints.md](api-endpoints.md))

**Verify**: After 3+ feedback entries, `GET /evaluation/metrics` returns valid numbers.

### Phase 8: Testing

1. `tests/conftest.py` — test DB fixtures, mock Spotify/Claude/Telegram
2. `test_queue.py` — import, dedup, random pick, empty detection
3. `test_ranking.py` — scoring formula correctness, edge cases
4. `test_taste_update.py` — cold start + feedback → profile update logic
5. `test_discovery.py` — auto-discovery dedup filtering, candidate generation
6. `test_workflow.py` — LangGraph dual-mode workflow end-to-end with mocks

### Phase 9: Knowledge Graph & Visualization (Post-MVP)

1. Add Neo4j to docker-compose
2. Create `knowledge_graph_service.py`
3. Enhance Discovery Agent to query graph
4. Implement discovery path data
5. Frontend D3.js visualization
