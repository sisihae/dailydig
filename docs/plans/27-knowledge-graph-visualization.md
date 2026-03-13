# Plan 27 — Knowledge Graph & Visualization (Post-MVP)

**Phase**: 9 – Knowledge Graph & Visualization  
**Creates**: `backend/services/knowledge_graph_service.py`, Neo4j docker service, frontend  
**Depends on**: All MVP phases complete

---

## Goal

Add Neo4j-based knowledge graph for deeper music exploration and D3.js discovery
path visualization. Neo4j is **optional** — all existing flows degrade gracefully
when it's unavailable.

## Steps

### 1. Add `neo4j` Python driver to `pyproject.toml`

```toml
neo4j = ">=5.0"
```

### 2. Add Neo4j to `docker-compose.yml`

Append to `services:`:

```yaml
neo4j:
  image: neo4j:5-community
  environment:
    NEO4J_AUTH: neo4j/password
  ports:
    - "7474:7474" # browser
    - "7687:7687" # bolt
  volumes:
    - neo4jdata:/data
  healthcheck:
    test: ["CMD-SHELL", "wget -qO- http://localhost:7474 || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Append to `volumes:`:

```yaml
neo4jdata:
```

Make `app` depend on `neo4j` (soft — app still starts if neo4j is down).

### 3. Add config variables

In `backend/config.py`:

```python
neo4j_uri: str = "bolt://localhost:7687"
neo4j_user: str = "neo4j"
neo4j_password: str = "password"
```

In `.env.example`:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 4. Create `backend/services/knowledge_graph_service.py`

Singleton service with:

- `__init__` — create async driver.
- `close()` — close driver.
- `add_track(track: dict)` — MERGE Track, Artist, Genre nodes + edges.
- `add_influence_edge(artist_from, artist_to)` — MERGE INFLUENCED_BY edge.
- `get_discovery_path(track_spotify_id)` — return {nodes, edges} for D3.js.
- `get_related_artists(artist_name)` — return list of related artist names
  (via genre co-occurrence and influence edges) for Discovery Agent seeding.

All public methods catch exceptions and log warnings (never raise to callers).
This ensures Neo4j failures never break the main pipeline.

### 5. Wire KG service lifecycle in `backend/app.py`

In `lifespan`:

```python
# Startup — try to connect, set app.state.kg_service (None if unavailable)
try:
    kg_service = KnowledgeGraphService()
    app.state.kg_service = kg_service
except Exception:
    logger.warning("Neo4j unavailable — knowledge graph disabled")
    app.state.kg_service = None

# Shutdown
if app.state.kg_service:
    await app.state.kg_service.close()
```

### 6. Populate graph after track delivery (workflow)

In `graph/workflow.py`, add a `populate_graph_node` after `delivery_node`:

```python
async def populate_graph_node(state: AgentState) -> dict:
    """Write delivered track to Neo4j (best-effort)."""
    kg_service = _get_kg_service()  # returns None if unavailable
    if not kg_service:
        return {}
    track = state.get("selected_track")
    if track:
        await kg_service.add_track(track)
    return {}
```

Wire it as `delivery → populate_graph → END` in the graph.

### 7. Enhance `/discovery-path/{track_id}` API

Merge graph data into the existing endpoint response:

```python
@router.get("/discovery-path/{track_id}")
async def get_discovery_path(track_id: int, ...):
    # ... existing relational query ...
    graph_data = None
    if kg_service:
        graph_data = await kg_service.get_discovery_path(track.spotify_id)
    return {
        "track": { ... },
        "recommendation": { ... },
        "graph": graph_data,
    }
```

### 8. Enhance Discovery Agent

Add optional method `expand_seeds_from_graph`:

```python
async def fetch_candidates(self, session, strategy, kg_service=None):
    seed_artists = strategy.get("seed_artists", [])
    # Expand seeds from graph if available
    if kg_service and seed_artists:
        for artist in seed_artists[:3]:
            related = await kg_service.get_related_artists(artist)
            seed_artists.extend(related[:2])
        seed_artists = list(dict.fromkeys(seed_artists))  # dedup, preserve order
    # ... rest unchanged ...
```

Pass `kg_service` from `discovery_node` in the workflow.

### 9. Frontend (`frontend/discovery_visualization/`)

Create `index.html` — standalone HTML + D3.js (CDN). No build tools.

- Input: track ID (URL param or text input).
- Fetch `/discovery-path/{track_id}`.
- Render force-directed graph with D3.js v7.
- Node colors: track (blue), artist (orange), genre (green).
- Edge labels rendered along links.
- Tooltip on hover showing node properties.

## Key Decisions

- Neo4j Community Edition (free, sufficient for single-user).
- Graph populated incrementally as tracks are delivered.
- **Graceful degradation**: all methods catch exceptions, log warnings, return
  empty results. Neo4j being down never breaks queue/auto-discovery flows.
- D3.js frontend is a minimal standalone HTML page (no build tools, no SPA).
- Discovery path API merges relational + graph data; `graph` is `null` when
  Neo4j is unavailable.

## Verification

1. `docker-compose up` — Neo4j starts, health check passes
2. Recommend a track → check Neo4j browser (`localhost:7474`) for nodes
3. `GET /discovery-path/{track_id}` → JSON with relational data + `graph` field
4. Open `frontend/discovery_visualization/index.html` → see force-directed graph
5. Stop Neo4j → re-run recommendation → pipeline completes without error
6. Discovery Agent uses graph seeds when available

## Output

- `neo4j` added to `pyproject.toml`
- Neo4j added to `docker-compose.yml` with healthcheck
- `backend/config.py` — three Neo4j settings
- `backend/services/knowledge_graph_service.py` — graph CRUD + query + graceful degradation
- `backend/app.py` — KG service lifecycle
- `backend/graph/workflow.py` — `populate_graph_node` after delivery
- `backend/routes/discovery_path.py` — merged graph data in response
- `backend/agents/discovery_agent.py` — optional graph-based seed expansion
- `frontend/discovery_visualization/index.html` — D3.js visualization
- `.env.example` — Neo4j vars
