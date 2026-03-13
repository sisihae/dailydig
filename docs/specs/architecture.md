# 2. Core System Architecture

## Two Modes of Operation

The system has two delivery modes, selected automatically:

### Mode A: Queue Delivery (feed-first)

When the dig queue has pending tracks:

```
Daily Scheduler (09:00 KST)
   ↓
Queue Check → has pending tracks
   ↓
Pick random track from queue
   ↓
Music Analysis Agent (Claude LLM)
   ↓
Delivery Agent (Telegram)
   ↓
User Feedback (👍/👎/⏭)
   ↓
Feedback Agent → Taste Modeling Agent
```

### Mode B: Auto-Discovery (queue empty)

When the dig queue is empty:

```
Daily Scheduler (09:00 KST)
   ↓
Queue Check → empty
   ↓
Notify user ("Switching to auto-discovery")
   ↓
Planner Agent (uses feedback-learned taste)
   ↓
Discovery Agent (Spotify recommendations)
   ↓
Ranking Agent (score + select best)
   ↓
Add remaining candidates to queue
   ↓
Music Analysis Agent (Claude LLM)
   ↓
Delivery Agent (Telegram)
   ↓
User Feedback → Feedback Agent → Taste Modeling Agent
```

---

## Playlist Import Flow (user-initiated)

```
User sends Spotify playlist URL
   ↓
POST /import-playlist
   ↓
Spotify Service: fetch all tracks from playlist
   ↓
Filter out already-delivered tracks (dedup)
   ↓
Add to dig_queue (status: pending, source: playlist_import)
```

---

## LangGraph Workflow

### AgentState

```python
class AgentState(TypedDict):
    taste_profile: TasteProfile | None   # None during cold start
    queue_mode: bool                      # True = queue delivery, False = auto-discovery
    planner_strategy: dict | None
    candidate_tracks: list[Track]
    selected_track: Track | None
    score_breakdown: dict | None
    explanation: str | None
    delivery_status: str | None
    error: str | None
```

### StateGraph

```python
graph = StateGraph(AgentState)

# Queue mode: skip planner/discovery/ranking
graph.add_node("check_queue", check_queue_node)
graph.add_node("pick_from_queue", pick_from_queue_node)
graph.add_node("planner", planner_agent)        # auto-discovery only
graph.add_node("discovery", discovery_agent)      # auto-discovery only
graph.add_node("ranking", ranking_agent)          # auto-discovery only
graph.add_node("analysis", analysis_agent)
graph.add_node("delivery", delivery_agent)

graph.set_entry_point("check_queue")

# Conditional routing based on queue state
graph.add_conditional_edges("check_queue", route_by_queue, {
    "queue": "pick_from_queue",
    "auto_discovery": "planner"
})
graph.add_edge("pick_from_queue", "analysis")
graph.add_edge("planner", "discovery")
graph.add_edge("discovery", "ranking")
graph.add_edge("ranking", "analysis")
graph.add_edge("analysis", "delivery")
graph.add_edge("delivery", END)
```

Feedback and taste update are NOT part of this graph — they run asynchronously when the user presses a Telegram button.
