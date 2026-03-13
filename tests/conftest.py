import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.db import Base
from backend.models import Track, DigQueue, TasteProfile, Feedback, RecommendationHistory


# --- Database fixtures ---


@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Async session for tests."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


# --- Sample data fixtures ---


@pytest_asyncio.fixture
async def sample_track(db_session):
    """Insert and return a sample track."""
    track = Track(
        name="Nakamarra",
        artist="Hiatus Kaiyote",
        album="Tawk Tomahawk",
        spotify_id="test_spotify_id_001",
        genre="neo soul",
        energy=0.65,
        valence=0.72,
        tempo=110.0,
    )
    db_session.add(track)
    await db_session.flush()
    return track


@pytest_asyncio.fixture
async def sample_queue_entry(db_session, sample_track):
    """Insert a pending queue entry for the sample track."""
    entry = DigQueue(
        track_id=sample_track.id,
        source="playlist_import",
        status="pending",
    )
    db_session.add(entry)
    await db_session.flush()
    return entry


@pytest_asyncio.fixture
async def sample_taste_profile(db_session):
    """Insert a taste profile with some preferences."""
    profile = TasteProfile(
        user_id=1,
        genre_preferences={"neo soul": 0.7, "jazz": 0.6, "electronic": 0.3},
        energy_preference=0.6,
        favorite_artists=["Hiatus Kaiyote", "Erykah Badu"],
        recent_likes=["sp_id_1", "sp_id_2"],
        recent_dislikes=["sp_id_3"],
    )
    db_session.add(profile)
    await db_session.flush()
    return profile


# --- Mock fixtures ---


@pytest.fixture
def mock_spotify():
    """Mock SpotifyService."""
    with patch("backend.services.spotify_service.SpotifyService") as mock:
        service = MagicMock()
        service.get_playlist_tracks = AsyncMock(return_value=[
            {
                "spotify_id": "sp_001", "name": "Track 1",
                "artist": "Artist 1", "artist_id": "art_001", "album": "Album 1",
            },
        ])
        service.get_track_audio_features = AsyncMock(return_value={
            "sp_001": {"energy": 0.7, "valence": 0.5, "tempo": 120.0},
        })
        service.get_recommendations = AsyncMock(return_value=[])
        service.get_artist_genres = AsyncMock(return_value=["neo soul"])
        mock.return_value = service
        yield service


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic AsyncAnthropic client (actual code uses async client)."""
    with patch("backend.agents.analysis_agent.anthropic") as mock:
        client = AsyncMock()
        message = MagicMock()
        message.content = [MagicMock(text="A great track worth discovering.")]
        client.messages.create.return_value = message
        mock.AsyncAnthropic.return_value = client
        yield client


@pytest.fixture
def mock_telegram():
    """Mock Telegram Bot used by NotificationService."""
    with patch("backend.services.notification_service.Bot") as mock:
        bot = AsyncMock()
        message = MagicMock()
        message.message_id = 12345
        bot.send_message = AsyncMock(return_value=message)
        mock.return_value = bot
        yield bot
