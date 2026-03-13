from backend.agents.discovery_agent import DiscoveryAgent


class TestDiscoveryAgent:
    async def test_dedup_filters_existing(self, db_session, sample_track, sample_queue_entry, mock_spotify):
        """Candidates already in DB and in queue should be filtered out."""
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

    async def test_empty_recommendations_returns_empty(self, db_session, mock_spotify):
        """No recommendations from Spotify → empty candidates list."""
        mock_spotify.get_recommendations.return_value = []

        agent = DiscoveryAgent(mock_spotify)
        strategy = {"seed_artists": [], "candidate_genres": ["rock"]}
        candidates = await agent.fetch_candidates(db_session, strategy)

        assert candidates == []
