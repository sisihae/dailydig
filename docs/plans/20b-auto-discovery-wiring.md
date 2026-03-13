# Plan 20b — Auto-Discovery Wiring

**Phase**: 5 – Auto-Discovery Pipeline  
**Modifies**: `backend/routes/recommendation.py`  
**Creates**: `backend/agents/planner_agent.py::format_taste_summary()` (static method)  
**Depends on**: 18, 19, 20, 12, 13, 14

---

## Goal

Wire the auto-discovery pipeline into `/trigger-recommendation` so that when the queue is empty, the system runs Planner → Discovery → Ranking → Analysis → Delivery end-to-end. Also provide a taste profile summary formatter for the auto-discovery analysis prompt.

---

## Steps

### 1. Add `format_taste_summary` to `PlannerAgent`

A static method that converts a `TasteProfile` into a human-readable summary string for the AnalysisAgent auto-discovery prompt.

```python
# In backend/agents/planner_agent.py

@staticmethod
def format_taste_summary(profile) -> str:
    """Format TasteProfile into a summary string for Claude prompts."""
    if profile is None:
        return "No taste profile yet — first-time discovery."

    parts = []

    genre_prefs = profile.genre_preferences or {}
    if genre_prefs:
        top_genres = sorted(genre_prefs.items(), key=lambda x: x[1], reverse=True)[:5]
        genre_str = ", ".join(f"{g} ({w:.2f})" for g, w in top_genres)
        parts.append(f"Preferred genres: {genre_str}")

    parts.append(f"Energy preference: {profile.energy_preference:.2f}")

    fav = profile.favorite_artists or []
    if fav:
        parts.append(f"Favorite artists: {', '.join(fav[:5])}")

    return "\n".join(parts) if parts else "Minimal taste data available."
```

### 2. Update `/trigger-recommendation` endpoint

Replace the current 404 response when queue is empty with the full auto-discovery pipeline:

```python
@router.post("/trigger-recommendation")
async def trigger_recommendation(session: AsyncSession = Depends(get_session)):
    queue_service = QueueService(SpotifyService())
    queue_entry, track = await queue_service.pick_random_track(session)

    if queue_entry is not None:
        # === Queue mode (existing logic) ===
        analysis_agent = AnalysisAgent()
        explanation = await analysis_agent.generate_explanation(
            track={
                "artist": track.artist,
                "track_name": track.name,
                "genre": track.genre,
                "energy": track.energy,
                "valence": track.valence,
                "tempo": track.tempo,
                "album": track.album,
            },
            queue_mode=True,
        )
        delivery_agent = DeliveryAgent()
        result = await delivery_agent.deliver_track(
            session=session,
            track_id=track.id,
            queue_entry_id=queue_entry.id,
            explanation=explanation,
            source="queue",
        )
        return {
            "mode": "queue",
            "track": {"name": track.name, "artist": track.artist, "album": track.album},
            "explanation": explanation,
            "delivery": result,
        }

    # === Auto-discovery mode ===
    delivery_agent = DeliveryAgent()
    await delivery_agent.send_auto_discovery_notice()

    # 1. Planner
    planner = PlannerAgent()
    strategy = await planner.create_strategy(session)

    # 2. Discovery
    spotify_service = SpotifyService()
    discovery = DiscoveryAgent(spotify_service)
    candidates = await discovery.fetch_candidates(session, strategy)

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="Auto-discovery found no candidates. Try importing a playlist.",
        )

    # 3. Ranking
    ranking = RankingAgent()
    ranking_result = await ranking.rank_and_select(session, candidates, strategy)
    selected = ranking_result["selected"]

    if selected is None:
        raise HTTPException(status_code=404, detail="Ranking produced no selection.")

    # Create selected track in DB
    existing = await repo.get_track_by_spotify_id(session, selected["spotify_id"])
    if existing:
        selected_track = existing
    else:
        selected_track = await repo.create_track(
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

    # 4. Analysis (auto-discovery mode)
    taste_profile = await repo.get_taste_profile(session)
    taste_summary = PlannerAgent.format_taste_summary(taste_profile)

    analysis_agent = AnalysisAgent()
    explanation = await analysis_agent.generate_explanation(
        track={
            "artist": selected["artist"],
            "track_name": selected["name"],
            "genre": selected.get("genre"),
            "energy": selected.get("energy"),
            "valence": selected.get("valence"),
            "tempo": selected.get("tempo"),
            "album": selected.get("album"),
        },
        taste_profile_summary=taste_summary,
        queue_mode=False,
    )

    # 5. Delivery
    result = await delivery_agent.deliver_track(
        session=session,
        track_id=selected_track.id,
        queue_entry_id=None,
        explanation=explanation,
        source="auto_discovery",
        score=ranking_result["score"],
        score_breakdown=ranking_result["score_breakdown"],
    )

    # 6. Queue remaining candidates
    queued_count = await ranking.queue_remaining(session, ranking_result["remaining"])
    await session.commit()

    return {
        "mode": "auto_discovery",
        "track": {
            "name": selected["name"],
            "artist": selected["artist"],
            "album": selected.get("album"),
        },
        "explanation": explanation,
        "score": ranking_result["score"],
        "score_breakdown": ranking_result["score_breakdown"],
        "candidates_queued": queued_count,
        "delivery": result,
    }
```

New imports needed at top of `recommendation.py`:

```python
from backend.agents.planner_agent import PlannerAgent
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.ranking_agent import RankingAgent
from backend.database import repositories as repo
```

---

## Verification

```bash
# 1. Make sure queue is empty (deliver all pending tracks or start fresh)
# 2. Ensure at least some feedback exists so taste profile is non-empty
# 3. Trigger recommendation:
curl -X POST http://localhost:8000/trigger-recommendation

# Expected: response with mode="auto_discovery", track info, score, queued count
# Expected: Telegram gets "switching to auto-discovery" notice + track message
```

---

## Output

- Modified `backend/agents/planner_agent.py` — added `format_taste_summary()` static method
- Modified `backend/routes/recommendation.py` — full auto-discovery pipeline when queue empty
