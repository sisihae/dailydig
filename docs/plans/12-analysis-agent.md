# Plan 12 — Music Analysis Agent

**Phase**: 3 – Queue Delivery + Analysis Agent  
**Creates**: `backend/agents/analysis_agent.py`  
**Depends on**: 03 (config with Anthropic key), 05 (Track model)

---

## Goal

Generate human-readable track descriptions using Claude LLM, with a template fallback.

## Steps

### 1. Create `backend/agents/__init__.py`

Empty file.

### 2. Create `backend/agents/analysis_agent.py`

```python
import anthropic

from backend.config import settings

QUEUE_MODE_PROMPT = """You are a music discovery assistant helping someone explore unfamiliar music.
Write a concise, intriguing description (2–4 sentences) of this track that makes
someone want to listen to it.

Track:
- Artist: {artist}
- Track: {track_name}
- Genre: {genre}
- Energy: {energy}, Valence: {valence}, Tempo: {tempo}

Write in a warm, music-enthusiast tone. Focus on what makes this track interesting."""

AUTO_DISCOVERY_PROMPT = """You are a music discovery assistant. Based on the user's listening feedback
and the recommended track's metadata, write a concise explanation (2–4 sentences)
for why this track is a good discovery today.

User taste learned from feedback:
{taste_profile_summary}

Recommended track:
- Artist: {artist}
- Track: {track_name}
- Genre: {genre}
- Energy: {energy}, Valence: {valence}, Tempo: {tempo}

Write in a warm, music-enthusiast tone."""


FALLBACK_TEMPLATE = (
    "🎶 {artist} — \"{track_name}\" from the album {album}. "
    "Genre: {genre}. A track worth exploring today."
)


class AnalysisAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def generate_explanation(
        self,
        track: dict,
        taste_profile_summary: str | None = None,
        queue_mode: bool = True,
    ) -> str:
        """
        Generate a track explanation via Claude.
        Falls back to template if Claude API fails.

        Args:
            track: dict with keys: artist, track_name, genre, energy, valence, tempo, album
            taste_profile_summary: stringified taste profile (auto-discovery mode only)
            queue_mode: True for queue delivery, False for auto-discovery
        """
        if queue_mode:
            prompt = QUEUE_MODE_PROMPT.format(
                artist=track["artist"],
                track_name=track["track_name"],
                genre=track.get("genre", "Unknown"),
                energy=track.get("energy", "N/A"),
                valence=track.get("valence", "N/A"),
                tempo=track.get("tempo", "N/A"),
            )
        else:
            prompt = AUTO_DISCOVERY_PROMPT.format(
                taste_profile_summary=taste_profile_summary or "No profile yet",
                artist=track["artist"],
                track_name=track["track_name"],
                genre=track.get("genre", "Unknown"),
                energy=track.get("energy", "N/A"),
                valence=track.get("valence", "N/A"),
                tempo=track.get("tempo", "N/A"),
            )

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception:
            # Fallback to template
            return FALLBACK_TEMPLATE.format(
                artist=track["artist"],
                track_name=track["track_name"],
                album=track.get("album", "Unknown"),
                genre=track.get("genre", "Unknown"),
            )
```

## Key Decisions

- Two prompt templates: queue mode (no taste context) vs auto-discovery (with taste).
- `claude-sonnet-4-20250514` for cost efficiency; easy to swap model.
- Template fallback on any Claude failure (per error-handling spec).
- Async interface but uses sync Anthropic client (sufficient for single-user).

## Verification

```python
agent = AnalysisAgent()
explanation = await agent.generate_explanation({
    "artist": "Hiatus Kaiyote",
    "track_name": "Nakamarra",
    "genre": "neo soul",
    "energy": 0.65, "valence": 0.72, "tempo": 110.0,
    "album": "Tawk Tomahawk"
})
print(explanation)
```

## Output

- `backend/agents/analysis_agent.py` — Claude-powered explanation generator with fallback
