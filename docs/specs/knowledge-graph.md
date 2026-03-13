# 12. Knowledge Graph & Visualization (Post-MVP, Phase 9)

## Knowledge Graph

Purpose: Enable deeper music exploration by building a persistent graph of
tracks, artists, genres, and their relationships.

### Graph Nodes

| Label    | Key Properties                            |
| -------- | ----------------------------------------- |
| `Track`  | `spotify_id`, `name`, `energy`, `valence` |
| `Artist` | `name`                                    |
| `Genre`  | `name`                                    |

### Edges

| Relationship    | From   | To     | Meaning                       |
| --------------- | ------ | ------ | ----------------------------- |
| `PERFORMED_BY`  | Track  | Artist | Track performed by artist     |
| `PLAYS`         | Artist | Genre  | Artist associated with genre  |
| `INFLUENCED_BY` | Artist | Artist | Artist influence relationship |

Example:

```
D'Angelo
→ neo soul
→ influenced_by Marvin Gaye
```

### Graph Population

- **When**: After every track delivery in the LangGraph workflow (both queue and
  auto-discovery modes).
- **What**: The delivered track + its artist + genre are added as nodes/edges.
- **Idempotent**: Uses `MERGE` (not `CREATE`) so duplicate deliveries are safe.

### Graceful Degradation

Neo4j is **optional**. When unavailable:

- Graph writes silently fail with a warning log.
- Discovery Agent skips graph-based seed expansion.
- Discovery path API returns relational data only (no graph neighborhood).
- Existing queue/auto-discovery flows are **never** blocked.

Used by Discovery Agent to find related artists beyond Spotify's algorithm.

---

## Discovery Path Visualization

Goal: Show how the recommendation was discovered, combining relational
recommendation data with the graph neighborhood.

### API Response

The `/discovery-path/{track_id}` endpoint merges two data sources:

1. **Relational** (PostgreSQL): recommendation source, score, score_breakdown,
   explanation — already exists.
2. **Graph** (Neo4j): artist → genre edges, influence edges, nearby tracks —
   added by this phase.

```json
{
  "track": { "id": 1, "name": "...", "artist": "...", ... },
  "recommendation": { "source": "auto_discovery", "score": 0.82, ... },
  "graph": {
    "nodes": [
      { "id": "spotify:abc", "type": "track", "name": "..." },
      { "id": "D'Angelo", "type": "artist", "name": "D'Angelo" },
      { "id": "neo soul", "type": "genre", "name": "neo soul" }
    ],
    "edges": [
      { "source": "spotify:abc", "target": "D'Angelo", "type": "performed_by" },
      { "source": "D'Angelo", "target": "neo soul", "type": "plays" }
    ]
  }
}
```

When Neo4j is unavailable, `graph` is `null`.

### Frontend

Minimal standalone HTML + D3.js force-directed graph (no build tools, no SPA).

- Different node colors per type (track, artist, genre).
- Edge labels for relationship type.
- Fetches from `/discovery-path/{track_id}`.
- Lives in `frontend/discovery_visualization/`.
