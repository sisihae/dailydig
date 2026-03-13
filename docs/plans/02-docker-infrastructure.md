# Plan 02 — Docker Infrastructure

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `docker-compose.yml`, `Dockerfile`  
**Depends on**: 01 (pyproject.toml must exist)

---

## Goal

Set up Docker Compose with PostgreSQL 16, Redis 7, and the app service.

## Steps

### 1. Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-dev

COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create `docker-compose.yml`

Three services:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: musicdiscovery
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis

volumes:
  pgdata:
```

### 3. Create `.dockerignore`

```
__pycache__
*.pyc
.env
.git
.mypy_cache
.pytest_cache
tests/
```

## Verification

```bash
docker-compose up -d db redis
docker-compose ps  # both services healthy
```

## Output

- `docker-compose.yml` — PostgreSQL 16, Redis 7, app service
- `Dockerfile` — Python 3.11 slim image with Poetry install
- `.dockerignore`
