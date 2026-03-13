import logging

from langgraph.graph import StateGraph, START, END

from backend.graph.state import AgentState
from backend.database.db import async_session
from backend.database import repositories as repo
from backend.services.spotify_service import SpotifyService
from backend.services.queue_service import QueueService
from backend.agents.planner_agent import PlannerAgent
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.ranking_agent import RankingAgent
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.delivery_agent import DeliveryAgent

logger = logging.getLogger(__name__)


# --- Node functions ---


async def check_queue_node(state: AgentState) -> dict:
    """Check if queue has pending tracks. Set queue_mode accordingly."""
    async with async_session() as session:
        queue_service = QueueService(SpotifyService())
        is_empty = await queue_service.is_queue_empty(session)

        if is_empty:
            # Load taste profile for auto-discovery (None is OK — planner handles cold start)
            profile = await repo.get_taste_profile(session)
            profile_dict = None
            if profile:
                profile_dict = {
                    "genre_preferences": profile.genre_preferences,
                    "energy_preference": profile.energy_preference,
                    "favorite_artists": profile.favorite_artists,
                }
            return {"queue_mode": False, "taste_profile": profile_dict}
        else:
            return {"queue_mode": True}


async def pick_from_queue_node(state: AgentState) -> dict:
    """Pick a random track from the queue."""
    async with async_session() as session:
        queue_service = QueueService(SpotifyService())
        queue_entry, track = await queue_service.pick_random_track(session)

        if not track:
            return {"error": "Failed to pick track from queue"}

        return {
            "queue_entry_id": queue_entry.id,
            "selected_track_id": track.id,
            "selected_track": {
                "id": track.id,
                "artist": track.artist,
                "track_name": track.name,
                "album": track.album,
                "genre": track.genre,
                "energy": track.energy,
                "valence": track.valence,
                "tempo": track.tempo,
                "spotify_id": track.spotify_id,
            },
        }


async def planner_node(state: AgentState) -> dict:
    """Run planner agent to create discovery strategy."""
    if state.get("error"):
        return {}

    async with async_session() as session:
        agent = PlannerAgent()
        strategy = await agent.create_strategy(session)

    # Send auto-discovery notice
    delivery = DeliveryAgent()
    await delivery.send_auto_discovery_notice()

    return {"planner_strategy": strategy}


async def discovery_node(state: AgentState) -> dict:
    """Fetch candidate tracks from Spotify."""
    strategy = state.get("planner_strategy")
    if not strategy:
        return {"error": "No planner strategy available"}

    async with async_session() as session:
        agent = DiscoveryAgent(SpotifyService())
        candidates = await agent.fetch_candidates(session, strategy)

    if not candidates:
        return {"error": "No candidates found from Spotify"}

    return {"candidate_tracks": candidates}


async def ranking_node(state: AgentState) -> dict:
    """Score candidates and select the best one."""
    candidates = state.get("candidate_tracks", [])
    strategy = state.get("planner_strategy", {})

    if not candidates:
        return {"error": "No candidates to rank"}

    async with async_session() as session:
        agent = RankingAgent()
        result = await agent.rank_and_select(session, candidates, strategy)

        selected = result["selected"]
        if not selected:
            return {"error": "Ranking produced no selection"}

        # Create track in DB if not exists
        existing = await repo.get_track_by_spotify_id(session, selected["spotify_id"])
        if existing:
            track_id = existing.id
        else:
            track = await repo.create_track(
                session,
                name=selected["name"],
                artist=selected["artist"],
                album=selected.get("album"),
                spotify_id=selected["spotify_id"],
                genre=selected.get("genre"),
                energy=selected.get("energy"),
                valence=selected.get("valence"),
                tempo=selected.get("tempo"),
            )
            track_id = track.id

        # Queue remaining candidates
        await agent.queue_remaining(session, result["remaining"])
        await session.commit()

    return {
        "selected_track_id": track_id,
        "selected_track": {
            "id": track_id,
            "artist": selected["artist"],
            "track_name": selected["name"],
            "album": selected.get("album"),
            "genre": selected.get("genre"),
            "energy": selected.get("energy"),
            "valence": selected.get("valence"),
            "tempo": selected.get("tempo"),
            "spotify_id": selected["spotify_id"],
        },
        "score": result["score"],
        "score_breakdown": result["score_breakdown"],
    }


async def analysis_node(state: AgentState) -> dict:
    """Generate track explanation via Claude."""
    if state.get("error"):
        return {}

    track = state.get("selected_track")
    if not track:
        return {"error": "No track selected for analysis"}

    agent = AnalysisAgent()

    # Build taste summary for auto-discovery mode
    taste_summary = None
    if not state.get("queue_mode") and state.get("taste_profile"):
        tp = state["taste_profile"]
        taste_summary = (
            f"Genre preferences: {tp.get('genre_preferences', {})}\n"
            f"Energy preference: {tp.get('energy_preference', 0.5)}\n"
            f"Favorite artists: {', '.join(tp.get('favorite_artists', [])[:5])}"
        )

    explanation = await agent.generate_explanation(
        track=track,
        taste_profile_summary=taste_summary,
        queue_mode=state.get("queue_mode", True),
    )

    return {"explanation": explanation}


async def delivery_node(state: AgentState) -> dict:
    """Deliver track to user via Telegram."""
    if state.get("error"):
        return {}

    agent = DeliveryAgent()

    async with async_session() as session:
        result = await agent.deliver_track(
            session=session,
            track_id=state["selected_track_id"],
            queue_entry_id=state.get("queue_entry_id"),
            explanation=state.get("explanation", ""),
            source="queue" if state.get("queue_mode") else "auto_discovery",
            score=state.get("score"),
            score_breakdown=state.get("score_breakdown"),
        )

    return {"delivery_status": result["delivery_status"]}


# --- Routing ---


def route_by_queue(state: AgentState) -> str:
    """Route based on queue state."""
    if state.get("error"):
        return "end"
    if state.get("queue_mode"):
        return "queue"
    return "auto_discovery"


# --- Build graph ---


def build_workflow():
    """Build and compile the dual-mode workflow graph."""
    graph = StateGraph(AgentState)

    graph.add_node("check_queue", check_queue_node)
    graph.add_node("pick_from_queue", pick_from_queue_node)
    graph.add_node("planner", planner_node)
    graph.add_node("discovery", discovery_node)
    graph.add_node("ranking", ranking_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("delivery", delivery_node)

    graph.add_edge(START, "check_queue")

    graph.add_conditional_edges("check_queue", route_by_queue, {
        "queue": "pick_from_queue",
        "auto_discovery": "planner",
        "end": END,
    })

    graph.add_edge("pick_from_queue", "analysis")
    graph.add_edge("planner", "discovery")
    graph.add_edge("discovery", "ranking")
    graph.add_edge("ranking", "analysis")
    graph.add_edge("analysis", "delivery")
    graph.add_edge("delivery", END)

    return graph.compile()
