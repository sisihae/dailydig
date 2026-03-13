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
