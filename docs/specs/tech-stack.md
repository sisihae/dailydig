# 3. Tech Stack & Configuration

## Backend

- Python 3.11+
- Poetry (package manager)
- FastAPI + Uvicorn
- LangGraph (agent orchestration)
- SQLAlchemy (async) + asyncpg (PostgreSQL driver)
- Redis (caching + scheduler job locking)
- pydantic-settings (config management)

## LLM

- Anthropic Claude (via `anthropic` SDK)

## External APIs

- Spotify Web API (via `spotipy`)

## Infrastructure

- Docker Compose (PostgreSQL 16, Redis 7, app)

## Notification

- Telegram Bot API (via `python-telegram-bot`, polling mode)

## Optional (post-MVP)

- Neo4j (knowledge graph)
- D3.js (discovery path visualization)

---

## Key Dependencies

| Library                           | Purpose                              |
| --------------------------------- | ------------------------------------ |
| `fastapi` + `uvicorn`             | Web framework                        |
| `sqlalchemy[asyncio]` + `asyncpg` | Async Postgres ORM                   |
| `redis[hiredis]`                  | Caching + job locking                |
| `spotipy`                         | Spotify Web API client               |
| `anthropic`                       | Claude LLM for explanations          |
| `langgraph`                       | Agent orchestration                  |
| `python-telegram-bot`             | Telegram delivery + feedback buttons |
| `apscheduler`                     | Daily cron scheduler                 |
| `pydantic-settings`               | Config from `.env`                   |
| `pytest` + `pytest-asyncio`       | Testing                              |

---

## Configuration

Environment variables (`.env.example`):

```
# Spotify
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback
SPOTIFY_REFRESH_TOKEN=        # Set after first OAuth flow

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

Config class: `pydantic BaseSettings` loading from `.env` file.
