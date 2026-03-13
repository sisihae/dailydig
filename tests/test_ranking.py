from backend.agents.ranking_agent import RankingAgent


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
