# Plan 01 — Poetry Project Initialization

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `pyproject.toml`  
**Depends on**: Nothing (first step)

---

## Goal

Initialize the Python project with Poetry, declaring all MVP dependencies.

## Steps

### 1. Initialize Poetry project

```bash
poetry init --name dailydig --python "^3.11"
```

### 2. Add production dependencies

```bash
poetry add fastapi uvicorn[standard] \
  "sqlalchemy[asyncio]" asyncpg alembic \
  "redis[hiredis]" \
  spotipy \
  anthropic \
  langgraph \
  python-telegram-bot \
  apscheduler \
  pydantic-settings \
  httpx
```

### 3. Add dev dependencies

```bash
poetry add --group dev pytest pytest-asyncio pytest-cov \
  ruff mypy \
  aiosqlite   # for test DB (in-memory SQLite)
```

### 4. Configure `pyproject.toml` extras

Add the following sections to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
strict = true
```

## Verification

```bash
poetry install
poetry run python -c "import fastapi, sqlalchemy, langgraph; print('OK')"
```

## Output

- `pyproject.toml` with all dependencies declared
- `poetry.lock` generated
