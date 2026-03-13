# Plan 27 — Knowledge Graph & Visualization (Post-MVP)

**Phase**: 9 – Knowledge Graph & Visualization  
**Creates**: `backend/services/knowledge_graph_service.py`, Neo4j docker service, frontend stubs  
**Depends on**: All MVP phases complete

---

## Goal

Add Neo4j-based knowledge graph for deeper music exploration and D3.js discovery path visualization. **Post-MVP** — implement only after all MVP phases are stable.

## Steps

### 1. Add Neo4j to `docker-compose.yml`

```yaml
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7474:7474"  # browser
      - "7687:7687"  # bolt
    volumes:
      - neo4jdata:/data

volumes:
  neo4jdata:
```

### 2. Add config variables

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 3. Create `backend/services/knowledge_graph_service.py`

```python
from neo4j import AsyncGraphDatabase
from backend.config import settings


class KnowledgeGraphService:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self):
        await self.driver.close()

    async def add_track(self, track: dict) -> None:
        """Add Track node + edges to Artist and Genre."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (t:Track {spotify_id: $spotify_id})
                SET t.name = $name, t.energy = $energy, t.valence = $valence

                MERGE (a:Artist {name: $artist})
                MERGE (t)-[:PERFORMED_BY]->(a)

                FOREACH (g IN CASE WHEN $genre IS NOT NULL THEN [$genre] ELSE [] END |
                    MERGE (genre:Genre {name: g})
                    MERGE (a)-[:PLAYS]->(genre)
                )
                """,
                spotify_id=track["spotify_id"],
                name=track["name"],
                artist=track["artist"],
                genre=track.get("genre"),
                energy=track.get("energy"),
                valence=track.get("valence"),
            )

    async def add_influence_edge(self, artist_from: str, artist_to: str) -> None:
        """Add INFLUENCED_BY edge between artists."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (a1:Artist {name: $from})
                MERGE (a2:Artist {name: $to})
                MERGE (a1)-[:INFLUENCED_BY]->(a2)
                """,
                **{"from": artist_from, "to": artist_to},
            )

    async def get_discovery_path(self, track_spotify_id: str) -> dict:
        """
        Get the graph neighborhood around a track for visualization.
        Returns nodes + edges in D3.js-compatible format.
        """
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Track {spotify_id: $sid})-[:PERFORMED_BY]->(a:Artist)
                OPTIONAL MATCH (a)-[:PLAYS]->(g:Genre)
                OPTIONAL MATCH (a)-[:INFLUENCED_BY]->(a2:Artist)
                RETURN t, a, collect(DISTINCT g) as genres,
                       collect(DISTINCT a2) as influences
                """,
                sid=track_spotify_id,
            )
            record = await result.single()
            if not record:
                return {"nodes": [], "edges": []}

            nodes = []
            edges = []

            # Track node
            track_node = dict(record["t"])
            nodes.append({"id": track_node["spotify_id"], "type": "track", **track_node})

            # Artist node
            artist_node = dict(record["a"])
            artist_id = artist_node["name"]
            nodes.append({"id": artist_id, "type": "artist", **artist_node})
            edges.append({"source": track_node["spotify_id"], "target": artist_id, "type": "performed_by"})

            # Genre nodes
            for g in record["genres"]:
                if g:
                    gd = dict(g)
                    nodes.append({"id": gd["name"], "type": "genre", **gd})
                    edges.append({"source": artist_id, "target": gd["name"], "type": "plays"})

            # Influence edges
            for inf in record["influences"]:
                if inf:
                    ind = dict(inf)
                    nodes.append({"id": ind["name"], "type": "artist", **ind})
                    edges.append({"source": artist_id, "target": ind["name"], "type": "influenced_by"})

            return {"nodes": nodes, "edges": edges}
```

### 4. Frontend stub (`frontend/discovery_visualization/`)

Create minimal HTML + D3.js to render the graph. This is a thin post-MVP layer:

- `index.html` — single-page with D3 force-directed graph
- Fetches from `/discovery-path/{track_id}` API
- Renders nodes (Track, Artist, Genre) with different colors
- Renders edges with labels

### 5. Enhance Discovery Agent

Optionally query the knowledge graph for related artists/genres to expand seed recommendations.

## Key Decisions

- Neo4j Community Edition (free, sufficient for single-user).
- Graph populated incrementally as tracks are recommended.
- D3.js frontend is a minimal HTML page, not a full SPA.
- Discovery path API already exists (Plan 24); this enhances it with graph data.

## Verification

1. Start Neo4j via docker-compose
2. Recommend a track → check Neo4j browser (`localhost:7474`)
3. Query `/discovery-path/{track_id}` → JSON with `nodes` + `edges`
4. Open frontend HTML → see force-directed graph

## Output

- Neo4j added to `docker-compose.yml`
- `backend/services/knowledge_graph_service.py` — graph CRUD + query
- `frontend/discovery_visualization/` — D3.js visualization stub
