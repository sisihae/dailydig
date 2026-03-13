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
    '🎶 {artist} — "{track_name}" from the album {album}. '
    "Genre: {genre}. A track worth exploring today."
)


class AnalysisAgent:
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_explanation(
        self,
        track: dict,
        taste_profile_summary: str | None = None,
        queue_mode: bool = True,
    ) -> str:
        """
        Generate a track explanation via Claude.
        Falls back to template if Claude API fails.
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
            message = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception:
            return FALLBACK_TEMPLATE.format(
                artist=track["artist"],
                track_name=track["track_name"],
                album=track.get("album", "Unknown"),
                genre=track.get("genre", "Unknown"),
            )
