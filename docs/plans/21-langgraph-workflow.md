# Plan 21 — LangGraph Workflow (Dual-Mode StateGraph)

**Phase**: 6 – LangGraph Orchestration & Scheduler  
**Creates**: `backend/graph/state.py`, `backend/graph/workflow.py`  
**Depends on**: All agents (12, 13, 18, 19, 20), 10 (queue service)

---

## Goal

Define the LangGraph StateGraph that orchestrates the dual-mode pipeline: queue delivery vs auto-discovery.

## Steps

### 1. Create `backend/graph/__init__.py`

Empty file.

### 2. Create `backend/graph/state.py`

```python
from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Taste & mode
    taste_profile: dict | None          # None during cold start
    queue_mode: bool                     # True = queue delivery, False = auto-discovery

    # Queue mode fields
    queue_entry_id: int | None
    selected_track_id: int | None

    # Auto-discovery fields
    planner_strategy: dict | None
    candidate_tracks: list[dict]

    # Shared fields
    selected_track: dict | None          # Track dict for analysis/delivery
    score: float | None
    score_breakdown: dict | None
    explanation: str | None
    delivery_status: str | None
    error: str | None
```

### 3. Create `backend/graph/workflow.py`

```python
from langgraph.graph import StateGraph, END

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


# --- Node functions ---

async def check_queue_node(state: AgentState) -> AgentState:
    """Check if queue has pending tracks. Set queue_mode accordingly."""
    async with async_session() as session:
        queue_service = QueueService(SpotifyService())
        is_empty = await queue_service.is_queue_empty(session)

        if is_empty:
            # Load taste profile for auto-discovery
            profile = await repo.get_taste_profile(session)
            if profile is None:
                # Can't auto-discover without any feedback
                return {**state, "queue_mode": False, "taste_profile": None,
                        "error": "Queue empty and no taste profile. Import a playlist."}
            profile_dict = {
                "genre_preferences": profile.genre_preferences,
                "energy_preference": profile.energy_preference,
                "favorite_artists": profile.favorite_artists,
            }
            return {**state, "queue_mode": False, "taste_profile": profile_dict}
        else:
            return {**state, "queue_mode": True}


async def pick_from_queue_node(state: AgentState) -> AgentState:
    """Pick a random track from the queue."""
    async with async_session() as session:
        queue_service = QueueService(SpotifyService())
        queue_entry, track = await queue_service.pick_random_track(session)

        if not track:
            return {**state, "error": "Failed to pick track from queue"}

        return {
            **state,
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


async def planner_node(state: AgentState) -> AgentState:
    """Run planner agent to create discovery strategy."""
    if state.get("error"):
        return state

    async with async_session() as session:
        agent = PlannerAgent()
        strategy = await agent.create_strategy(session)

    # Send auto-discovery notice
    delivery = DeliveryAgent()
    await delivery.send_auto_discovery_notice()

    return {**state, "planner_strategy": strategy}


async def discovery_node(state: AgentState) -> AgentState:
    """Fetch candidate tracks from Spotify."""
    strategy = state.get("planner_strategy")
    if not strategy:
        return {**state, "error": "No planner strategy available"}

    async with async_session() as session:
        agent = DiscoveryAgent(SpotifyService())
        candidates = await agent.fetch_candidates(session, strategy)

    if not candidates:
        return {**state, "error": "No candidates found from Spotify"}

    return {**state, "candidate_tracks": candidates}


async def ranking_node(state: AgentState) -> AgentState:
    """Score candidates and select the best one."""
    candidates = state.get("candidate_tracks", [])
    strategy = state.get("planner_strategy", {})

    if not candidates:
        return {**state, "error": "No candidates to rank"}

    async with async_session() as session:
        agent = RankingAgent()
        result = await agent.rank_and_select(session, candidates, strategy)

        selected = result["selected"]
        if not selected:
            return {**state, "error": "Ranking produced no selection"}

        # Create track in DB and queue remaining
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
        **state,
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


async def analysis_node(state: AgentState) -> AgentState:
    """Generate track explanation via Claude."""
    if state.get("error"):
        return state

    track = state.get("selected_track")
    if not track:
        return {**state, "error": "No track selected for analysis"}

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

    return {**state, "explanation": explanation}


async def delivery_node(state: AgentState) -> AgentState:
    """Deliver track to user via Telegram."""
    if state.get("error"):
        return state

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

    return {**state, "delivery_status": result["delivery_status"]}


# --- Routing ---

def route_by_queue(state: AgentState) -> str:
    """Route based on queue state."""
    if state.get("error"):
        return "end"
    if state.get("queue_mode"):
        return "queue"
    return "auto_discovery"


# --- Build graph ---

def build_workflow() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("check_queue", check_queue_node)
    graph.add_node("pick_from_queue", pick_from_queue_node)
    graph.add_node("planner", planner_node)
    graph.add_node("discovery", discovery_node)
    graph.add_node("ranking", ranking_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("delivery", delivery_node)

    graph.set_entry_point("check_queue")

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
```

## Graph Flow

```
check_queue
  ├─ queue_mode=True  → pick_from_queue → analysis → delivery → END
  ├─ queue_mode=False → planner → discovery → ranking → analysis → delivery → END
  └─ error            → END
```

## Key Decisions

- Each node opens its own `async_session()` — keeps transactions short.
- Errors halt the pipeline via `error` key in state.
- Feedback/taste update NOT part of this graph (runs async via Telegram callback).
- `build_workflow()` returns a compiled graph ready to `.ainvoke()`.

## Verification

```python
workflow = build_workflow()
result = await workflow.ainvoke({})
print(result["delivery_status"])  # "delivered"
```

## Output

- `backend/graph/state.py` — `AgentState` TypedDict
- `backend/graph/workflow.py` — full dual-mode StateGraph
