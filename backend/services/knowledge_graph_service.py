import logging

from neo4j import AsyncGraphDatabase

from backend.config import settings

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Neo4j-backed knowledge graph for music discovery.

    All public methods are best-effort: they catch exceptions and log warnings
    so that Neo4j failures never break the main pipeline.
    """

    def __init__(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self.driver.close()

    async def add_track(self, track: dict) -> None:
        """Add Track node + edges to Artist and Genre."""
        try:
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
                    name=track.get("name") or track.get("track_name"),
                    artist=track["artist"],
                    genre=track.get("genre"),
                    energy=track.get("energy"),
                    valence=track.get("valence"),
                )
        except Exception:
            logger.warning("Failed to add track to knowledge graph", exc_info=True)

    async def add_influence_edge(self, artist_from: str, artist_to: str) -> None:
        """Add INFLUENCED_BY edge between artists."""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MERGE (a1:Artist {name: $from_artist})
                    MERGE (a2:Artist {name: $to_artist})
                    MERGE (a1)-[:INFLUENCED_BY]->(a2)
                    """,
                    from_artist=artist_from,
                    to_artist=artist_to,
                )
        except Exception:
            logger.warning("Failed to add influence edge to knowledge graph", exc_info=True)

    async def get_discovery_path(self, track_spotify_id: str) -> dict | None:
        """Return the graph neighborhood around a track for D3.js visualization.

        Returns {"nodes": [...], "edges": [...]} or None on failure.
        """
        try:
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

                nodes: list[dict] = []
                edges: list[dict] = []

                # Track node
                track_node = dict(record["t"])
                nodes.append({
                    "id": track_node["spotify_id"],
                    "type": "track",
                    "name": track_node.get("name"),
                })

                # Artist node
                artist_node = dict(record["a"])
                artist_id = artist_node["name"]
                nodes.append({"id": artist_id, "type": "artist", "name": artist_id})
                edges.append({
                    "source": track_node["spotify_id"],
                    "target": artist_id,
                    "type": "performed_by",
                })

                # Genre nodes
                for g in record["genres"]:
                    if g:
                        gd = dict(g)
                        nodes.append({"id": gd["name"], "type": "genre", "name": gd["name"]})
                        edges.append({
                            "source": artist_id,
                            "target": gd["name"],
                            "type": "plays",
                        })

                # Influence edges
                for inf in record["influences"]:
                    if inf:
                        ind = dict(inf)
                        nodes.append({"id": ind["name"], "type": "artist", "name": ind["name"]})
                        edges.append({
                            "source": artist_id,
                            "target": ind["name"],
                            "type": "influenced_by",
                        })

                return {"nodes": nodes, "edges": edges}
        except Exception:
            logger.warning("Failed to query knowledge graph", exc_info=True)
            return None

    async def get_related_artists(self, artist_name: str) -> list[str]:
        """Find related artists via genre co-occurrence and influence edges.

        Returns a list of artist names, or empty list on failure.
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (a:Artist {name: $name})-[:PLAYS]->(g:Genre)<-[:PLAYS]-(related:Artist)
                    WHERE related.name <> $name
                    RETURN DISTINCT related.name AS name
                    LIMIT 5
                    UNION
                    MATCH (a:Artist {name: $name})-[:INFLUENCED_BY]->(inf:Artist)
                    RETURN DISTINCT inf.name AS name
                    LIMIT 5
                    """,
                    name=artist_name,
                )
                records = [r["name"] async for r in result]
                return records
        except Exception:
            logger.warning("Failed to get related artists from knowledge graph", exc_info=True)
            return []
