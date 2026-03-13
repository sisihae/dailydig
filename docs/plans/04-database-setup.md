# Plan 04 — Database Setup (Async SQLAlchemy)

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `backend/database/__init__.py`, `backend/database/db.py`  
**Depends on**: 03 (config with DATABASE_URL)

---

## Goal

Set up async SQLAlchemy engine, session factory, and declarative Base.

## Steps

### 1. Create `backend/database/__init__.py`

Empty file.

### 2. Create `backend/database/db.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

engine = create_async_engine(settings.database_url, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables. Called once at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for FastAPI route injection."""
    async with async_session() as session:
        yield session
```

## Key Decisions

- `expire_on_commit=False` — prevents lazy-load issues with async sessions.
- `init_db()` uses `create_all` for MVP simplicity. Alembic migrations can be layered later.
- `get_session()` is an async generator for FastAPI `Depends()`.

## Verification

```python
# After models are defined (Plan 05), run:
import asyncio
from backend.database.db import init_db
asyncio.run(init_db())  # tables created in PostgreSQL
```

## Output

- `backend/database/db.py` — engine, session factory, Base, `init_db()`, `get_session()`
