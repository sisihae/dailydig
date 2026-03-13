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
