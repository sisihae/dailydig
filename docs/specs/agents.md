# 6. Agents

## 6.1 Planner Agent

**Active only in auto-discovery mode** (when dig queue is empty).

Purpose: Define discovery strategy using feedback-learned taste.

Inputs:

- TasteProfile (built from feedback)
- Recent recommendation history (last 30 days)

Logic:

- If recent dislike rate > 40%: increase `exploration_ratio` to explore new genres
- Pick `candidate_genres`: weighted random sample from `genre_preferences` (top 3–5)
- Pick `seed_artists`: random sample from `favorite_artists` (top 2–3)
- Set `novelty_weight` based on exploration_ratio
- If taste profile is too sparse (< 5 feedback entries): fallback to genres from recently delivered tracks

Output:

```json
{
  "exploration_ratio": 0.3,
  "candidate_genres": ["neo soul", "alt rnb", "jazz"],
  "seed_artists": ["spotify_artist_id_1", "spotify_artist_id_2"],
  "novelty_weight": 0.2,
  "taste_similarity_weight": 0.5,
  "diversity_weight": 0.3
}
```

Note: Spotify Recommendations API allows max 5 seeds total (artists + genres combined). Planner must pick top 2–3 artists + 2–3 genres to stay within this limit.

---

## 6.2 Discovery Agent

**Active only in auto-discovery mode** (when dig queue is empty).

Purpose: Fetch candidate tracks from Spotify.

Inputs:

- PlannerStrategy

Steps:

1. Extract seed genres and seed artists from strategy
2. Call `spotify_service.get_recommendations(seed_artists, seed_genres, limit=50)`
3. Fetch audio features for all candidates via `get_track_audio_features()`
4. Filter out tracks already in `recommendation_history` or `dig_queue` (dedup)
5. Return 30–50 candidate tracks

Output:

```python
candidate_tracks: list[Track]  # 30–50 tracks with audio features populated
```

Redis caching: Cache Spotify recommendation responses (TTL: 1 hour) and audio features (TTL: 24 hours) to avoid rate limits.

---

## 6.3 Ranking Agent

**Active only in auto-discovery mode** (when dig queue is empty).

Purpose: Select the best track for today + queue the remaining candidates.

Inputs:

- Candidate tracks (from Discovery Agent)
- TasteProfile
- PlannerStrategy (contains weights)

Scoring formula:

```
score =
    taste_similarity_weight * taste_score
  + novelty_weight * novelty_score
  + diversity_weight * artist_diversity
```

Default weights: `taste_similarity=0.5`, `novelty=0.3`, `diversity=0.2`

Score components:

- **taste_score**: Cosine similarity between track audio features (energy, valence, tempo normalized) and user's preference vector. Also factor in genre overlap with `genre_preferences`.
- **novelty_score**: 1.0 if artist has never been recommended before, 0.5 if recommended >30 days ago, 0.0 if recommended in last 30 days. Bonus if genre is underexplored.
- **artist_diversity**: 1.0 if artist not in last 7 recommendations, linearly decreasing otherwise.

Output:

```python
selected_track: Track         # best scored → delivered today
remaining_tracks: list[Track]  # added to dig_queue with source="auto_fetch"
score: float
score_breakdown: {"taste": float, "novelty": float, "diversity": float}
```

---

## 6.4 Music Analysis Agent

**Active in both modes.**

Purpose: Generate a human-readable description of today's track.

Uses: Anthropic Claude API.

Prompt (for queue mode — no taste context available early on):

```
You are a music discovery assistant helping someone explore unfamiliar music.
Write a concise, intriguing description (2–4 sentences) of this track that makes
someone want to listen to it.

Track:
- Artist: {artist}
- Track: {track_name}
- Genre: {genre}
- Energy: {energy}, Valence: {valence}, Tempo: {tempo}

Write in a warm, music-enthusiast tone. Focus on what makes this track interesting.
```

Prompt (for auto-discovery mode — taste context available):

```
You are a music discovery assistant. Based on the user's listening feedback
and the recommended track's metadata, write a concise explanation (2–4 sentences)
for why this track is a good discovery today.

User taste learned from feedback:
{taste_profile_summary}

Recommended track:
- Artist: {artist}
- Track: {track_name}
- Genre: {genre}
- Energy: {energy}, Valence: {valence}, Tempo: {tempo}

Write in a warm, music-enthusiast tone.
```

Output:

```json
{
  "explanation": "Hiatus Kaiyote blends jazz-fusion energy with warm, melodic grooves. The track's mid-tempo feel and rich harmonics make it a compelling listen if you're exploring neo-soul territory."
}
```

---

## 6.5 Delivery Agent

**Active in both modes.**

Purpose: Send today's track to the user via Telegram.

Message format (Markdown):

```
🎵 *Today's Music Discovery*

*Artist:* Hiatus Kaiyote
*Track:* Nakamarra
*Album:* Tawk Tomahawk

_About this track:_
Hiatus Kaiyote blends jazz-fusion energy with warm grooves...

🔗 [Listen on Spotify](https://open.spotify.com/track/xxx)
```

Telegram inline keyboard buttons:

```
[👍 Like] [👎 Dislike] [⏭ Skip]
```

Additional notifications:

- When switching to auto-discovery: "🔄 Your dig queue is empty. Switching to auto-discovery based on your feedback!"

Actions:

1. Format message with track info + explanation + Spotify link
2. Send via `python-telegram-bot` with inline keyboard
3. Update `dig_queue` entry status to "delivered"
4. Store in `recommendation_history` table
5. Return `message_id` and `delivery_status`

Telegram bot runs in **polling mode** (no public URL needed for local Docker).

---

## 6.6 Feedback Agent

**Active in both modes.**

Purpose: Process user reaction from Telegram inline buttons.

Inputs:

- Telegram callback query (button press)
- Maps to: `track_id` + `feedback_type`

Actions:

1. Parse callback data to extract track_id and feedback_type
2. Store `Feedback` record in database
3. Trigger Taste Modeling Agent

---

## 6.7 Taste Modeling Agent

**Active in both modes.**

Purpose: Update user taste profile based on feedback. Starts from empty profile (cold start).

Update logic with specific learning rates:

```
if feedback == "like":
    genre_preferences[track_genre] += 0.05  (create key if not exists, starting at 0.5)
    energy_preference moves 0.02 toward track's energy
    add artist to favorite_artists (cap at 50)
    add track to recent_likes (cap at 20, FIFO)

if feedback == "dislike":
    genre_preferences[track_genre] -= 0.05  (create key if not exists, starting at 0.5)
    add track to recent_dislikes (cap at 20, FIFO)

if feedback == "skip":
    genre_preferences[track_genre] -= 0.02  # weaker negative signal

All genre_preferences weights clamped to [0.0, 1.0]
```

Cold start behavior: If TasteProfile doesn't exist yet, create one with empty `genre_preferences={}`, `energy_preference=0.5`, empty lists for artists/likes/dislikes.

Update: Write updated `TasteProfile` to database.
