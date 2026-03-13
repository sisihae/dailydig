# Plan 03 — Configuration & Environment Variables

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `backend/config.py`, `.env.example`  
**Depends on**: 01 (pydantic-settings installed)

---

## Goal

Centralized configuration via pydantic `BaseSettings`, loading from `.env`.

## Steps

### 1. Create `.env.example`

```env
# Spotify
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback
SPOTIFY_REFRESH_TOKEN=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Anthropic
ANTHROPIC_API_KEY=

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/musicdiscovery

# Redis
REDIS_URL=redis://localhost:6379/0

# Scheduler
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=0
SCHEDULE_TIMEZONE=Asia/Seoul
```

### 2. Create `backend/__init__.py`

Empty file.

### 3. Create `backend/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Spotify
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8000/auth/callback"
    spotify_refresh_token: str = ""

    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str

    # Anthropic
    anthropic_api_key: str

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/musicdiscovery"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Scheduler
    schedule_hour: int = 9
    schedule_minute: int = 0
    schedule_timezone: str = "Asia/Seoul"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

## Key Decisions

- Single `settings` instance imported throughout the project.
- All secrets loaded from environment; no hardcoded values.
- Defaults only for non-sensitive values (URLs, schedule).

## Verification

```python
from backend.config import settings
print(settings.database_url)  # should read from .env
```

## Output

- `backend/config.py` — `Settings` class + singleton `settings`
- `.env.example` — template for all env vars
- `backend/__init__.py` — package init
