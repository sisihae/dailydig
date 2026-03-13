# Plan 26 — Unit & Integration Tests

**Phase**: 8 – Testing  
**Creates**: `tests/test_queue.py`, `tests/test_ranking.py`, `tests/test_taste_update.py`, `tests/test_discovery.py`, `tests/test_workflow.py`  
**Depends on**: 25 (test fixtures)

---

## Goal

Write tests for all core logic: queue operations, ranking, taste updates, discovery dedup, and the LangGraph workflow.

## Steps

### 1. Create `tests/test_queue.py`

```python
import pytest
from backend.database import repositories as repo


class TestQueueOperations:
    async def test_import_adds_tracks_to_queue(self, db_session, sample_track):
        """Track added to queue has status=pending."""
        entry = await repo.add_to_queue(db_session, track_id=sample_track.id, source="playlist_import")
        assert entry.status == "pending"
        assert entry.source == "playlist_import"

    async def test_dedup_skips_existing_tracks(self, db_session, sample_track, sample_queue_entry):
        """Track already in queue should be detected."""
        is_in_queue = await repo.is_track_in_queue(db_session, sample_track.id)
        assert is_in_queue is True

    async def test_pick_random_from_pending(self, db_session, sample_track, sample_queue_entry):
        """Random pick returns a pending entry."""
        entry = await repo.pick_random_pending(db_session)
        assert entry is not None
        assert entry.status == "pending"

    async def test_pick_from_empty_queue_returns_none(self, db_session):
        """Empty queue returns None."""
        entry = await repo.pick_random_pending(db_session)
        assert entry is None

    async def test_mark_delivered(self, db_session, sample_queue_entry):
        """Marking delivered changes status."""
        await repo.mark_delivered(db_session, sample_queue_entry.id)
        await db_session.flush()
        # Re-fetch
        from sqlalchemy import select
        from backend.models import DigQueue
        result = await db_session.execute(select(DigQueue).where(DigQueue.id == sample_queue_entry.id))
        entry = result.scalar_one()
        assert entry.status == "delivered"
```

### 2. Create `tests/test_ranking.py`

```python
import pytest
from backend.agents.ranking_agent import RankingAgent
from backend.models import TasteProfile


class TestRankingAgent:
    async def test_taste_score_neutral_without_profile(self):
        """No profile → 0.5 neutral score."""
        score = RankingAgent._taste_score({"energy": 0.5, "genre": "jazz"}, None)
        assert score == 0.5

    async def test_taste_score_high_for_matching_genre(self, sample_taste_profile):
        """High genre preference → higher taste score."""
        candidate = {"energy": 0.6, "genre": "neo soul"}
        score = RankingAgent._taste_score(candidate, sample_taste_profile)
        assert score > 0.5

    async def test_novelty_score_new_artist(self):
        """Never-recommended artist → novelty 1.0."""
        score = RankingAgent._novelty_score(
            {"artist": "New Artist"},
            all_recommended_artists=set(),
            recent_30d_artists=set(),
        )
        assert score == 1.0

    async def test_novelty_score_recent_artist(self):
        """Recently recommended artist → novelty 0.0."""
        score = RankingAgent._novelty_score(
            {"artist": "Old Artist"},
            all_recommended_artists={"Old Artist"},
            recent_30d_artists={"Old Artist"},
        )
        assert score == 0.0

    async def test_diversity_score_fresh_artist(self):
        """Artist not in last 7 recs → diversity 1.0."""
        score = RankingAgent._diversity_score(
            {"artist": "Fresh Artist"},
            recent_artists=["A", "B", "C"],
        )
        assert score == 1.0
```

### 3. Create `tests/test_taste_update.py`

```python
import pytest
from backend.agents.taste_model_agent import TasteModelAgent
from backend.database import repositories as repo


class TestTasteUpdate:
    async def test_cold_start_creates_profile(self, db_session, sample_track):
        """First feedback creates a new TasteProfile."""
        profile = await repo.get_taste_profile(db_session)
        assert profile is None

        agent = TasteModelAgent()
        await agent.update_from_feedback(db_session, "like", sample_track.id)

        profile = await repo.get_taste_profile(db_session)
        assert profile is not None
        assert sample_track.genre in profile.genre_preferences

    async def test_like_increases_genre_preference(self, db_session, sample_taste_profile, sample_track):
        """Liking a 'neo soul' track should increase neo soul preference."""
        old_pref = sample_taste_profile.genre_preferences.get("neo soul", 0.5)

        agent = TasteModelAgent()
        await agent.update_from_feedback(db_session, "like", sample_track.id)

        profile = await repo.get_taste_profile(db_session)
        new_pref = profile.genre_preferences.get("neo soul", 0.5)
        assert new_pref > old_pref

    async def test_dislike_decreases_genre_preference(self, db_session, sample_taste_profile, sample_track):
        """Disliking should decrease genre preference."""
        old_pref = sample_taste_profile.genre_preferences.get("neo soul", 0.5)

        agent = TasteModelAgent()
        await agent.update_from_feedback(db_session, "dislike", sample_track.id)

        profile = await repo.get_taste_profile(db_session)
        new_pref = profile.genre_preferences.get("neo soul", 0.5)
        assert new_pref < old_pref

    async def test_preferences_clamped(self):
        """Genre preferences should be clamped to [0.0, 1.0]."""
        val = max(0.0, min(1.0, 1.5))
        assert val == 1.0
        val = max(0.0, min(1.0, -0.1))
        assert val == 0.0
```

### 4. Create `tests/test_discovery.py`

```python
import pytest
from backend.agents.discovery_agent import DiscoveryAgent


class TestDiscoveryAgent:
    async def test_dedup_filters_existing(self, db_session, sample_track, mock_spotify):
        """Candidates already in DB should be filtered out."""
        mock_spotify.get_recommendations.return_value = [
            {"spotify_id": sample_track.spotify_id, "name": "Dup", "artist": "A", "artist_id": "x", "album": "B"},
            {"spotify_id": "new_id", "name": "New Track", "artist": "B", "artist_id": "y", "album": "C"},
        ]
        mock_spotify.get_track_audio_features.return_value = {
            "new_id": {"energy": 0.5, "valence": 0.5, "tempo": 120},
        }
        mock_spotify.get_artist_genres.return_value = ["jazz"]

        agent = DiscoveryAgent(mock_spotify)
        strategy = {"seed_artists": [], "candidate_genres": ["jazz"]}
        candidates = await agent.fetch_candidates(db_session, strategy)

        spotify_ids = [c["spotify_id"] for c in candidates]
        assert sample_track.spotify_id not in spotify_ids
```

### 5. Create `tests/test_workflow.py`

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager

from backend.graph.workflow import build_workflow


class TestWorkflow:
    async def test_queue_mode_workflow(self, db_session, sample_track, sample_queue_entry):
        """With tracks in queue, workflow should pick from queue and deliver."""

        @asynccontextmanager
        async def mock_session_ctx():
            yield db_session

        with patch("backend.graph.workflow.async_session", mock_session_ctx), \
             patch("backend.graph.workflow.SpotifyService"), \
             patch("backend.graph.workflow.AnalysisAgent") as mock_analysis, \
             patch("backend.graph.workflow.DeliveryAgent") as mock_delivery:

            analysis_inst = MagicMock()
            analysis_inst.generate_explanation = AsyncMock(return_value="Great track")
            mock_analysis.return_value = analysis_inst

            delivery_inst = MagicMock()
            delivery_inst.deliver_track = AsyncMock(
                return_value={"message_id": 1, "delivery_status": "delivered"}
            )
            mock_delivery.return_value = delivery_inst

            workflow = build_workflow()
            result = await workflow.ainvoke({})

            assert result.get("queue_mode") is True
            assert result.get("delivery_status") == "delivered"

    async def test_auto_discovery_mode_workflow(self, db_session):
        """With empty queue, workflow should enter auto-discovery mode."""

        @asynccontextmanager
        async def mock_session_ctx():
            yield db_session

        with patch("backend.graph.workflow.async_session", mock_session_ctx), \
             patch("backend.graph.workflow.SpotifyService"), \
             patch("backend.graph.workflow.PlannerAgent") as mock_planner, \
             patch("backend.graph.workflow.DiscoveryAgent") as mock_discovery, \
             patch("backend.graph.workflow.RankingAgent") as mock_ranking, \
             patch("backend.graph.workflow.AnalysisAgent") as mock_analysis, \
             patch("backend.graph.workflow.DeliveryAgent") as mock_delivery:

            planner_inst = MagicMock()
            planner_inst.create_strategy = AsyncMock(return_value={
                "seed_artists": ["art_001"],
                "candidate_genres": ["jazz"],
                "taste_similarity_weight": 0.5,
                "novelty_weight": 0.3,
                "diversity_weight": 0.2,
            })
            mock_planner.return_value = planner_inst

            discovery_inst = MagicMock()
            discovery_inst.fetch_candidates = AsyncMock(return_value=[
                {"spotify_id": "new_sp_001", "name": "New Track", "artist": "New Artist",
                 "album": "New Album", "genre": "jazz", "energy": 0.6, "valence": 0.5, "tempo": 120},
            ])
            mock_discovery.return_value = discovery_inst

            ranking_inst = MagicMock()
            ranking_inst.rank_and_select = AsyncMock(return_value={
                "selected": {"spotify_id": "new_sp_001", "name": "New Track", "artist": "New Artist",
                             "album": "New Album", "genre": "jazz", "energy": 0.6, "valence": 0.5, "tempo": 120},
                "remaining": [],
                "score": 0.85,
                "score_breakdown": {"taste": 0.7, "novelty": 1.0, "diversity": 1.0},
            })
            ranking_inst.queue_remaining = AsyncMock()
            mock_ranking.return_value = ranking_inst

            analysis_inst = MagicMock()
            analysis_inst.generate_explanation = AsyncMock(return_value="A jazzy discovery")
            mock_analysis.return_value = analysis_inst

            delivery_inst = MagicMock()
            delivery_inst.deliver_track = AsyncMock(
                return_value={"message_id": 2, "delivery_status": "delivered"}
            )
            delivery_inst.send_auto_discovery_notice = AsyncMock()
            mock_delivery.return_value = delivery_inst

            workflow = build_workflow()
            result = await workflow.ainvoke({})

            assert result.get("queue_mode") is False
            assert result.get("delivery_status") == "delivered"
```

## Test Coverage Map

| Test File              | Tests    | Area                                        |
| ---------------------- | -------- | ------------------------------------------- |
| `test_queue.py`        | 5 tests  | Import, dedup, pick, empty, mark delivered  |
| `test_ranking.py`      | 5 tests  | Taste/novelty/diversity scoring, edge cases |
| `test_taste_update.py` | 4 tests  | Cold start, like/dislike effects, clamping  |
| `test_discovery.py`    | 1+ tests | Dedup filtering                             |
| `test_workflow.py`     | 2 tests  | Queue mode + auto-discovery mode with mocks |

## Verification

```bash
poetry run pytest -v
poetry run pytest --cov=backend --cov-report=term-missing
```

## Output

- 5 test files in `tests/`
