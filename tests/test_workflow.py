from contextlib import asynccontextmanager
from unittest.mock import patch, AsyncMock, MagicMock

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
                {
                    "spotify_id": "new_sp_001", "name": "New Track", "artist": "New Artist",
                    "album": "New Album", "genre": "jazz", "energy": 0.6, "valence": 0.5, "tempo": 120,
                },
            ])
            mock_discovery.return_value = discovery_inst

            ranking_inst = MagicMock()
            ranking_inst.rank_and_select = AsyncMock(return_value={
                "selected": {
                    "spotify_id": "new_sp_001", "name": "New Track", "artist": "New Artist",
                    "album": "New Album", "genre": "jazz", "energy": 0.6, "valence": 0.5, "tempo": 120,
                },
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
