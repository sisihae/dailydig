# Implementation Plans — Index

Each plan is a self-contained, runnable implementation unit. Execute them in order; each plan lists its dependencies.

---

## Phase 1: Project Scaffolding & Infrastructure

| #   | Plan                                                 | Creates                             | Depends on |
| --- | ---------------------------------------------------- | ----------------------------------- | ---------- |
| 01  | [Poetry Project Init](01-poetry-project-init.md)     | `pyproject.toml`, `poetry.lock`     | —          |
| 02  | [Docker Infrastructure](02-docker-infrastructure.md) | `docker-compose.yml`, `Dockerfile`  | 01         |
| 03  | [Config & Environment](03-config-env.md)             | `backend/config.py`, `.env.example` | 01         |
| 04  | [Database Setup](04-database-setup.md)               | `backend/database/db.py`            | 03         |
| 05  | [SQLAlchemy Models](05-sqlalchemy-models.md)         | `backend/models/*.py` (5 models)    | 04         |
| 06  | [Repositories (CRUD)](06-repositories.md)            | `backend/database/repositories.py`  | 05         |
| 07  | [FastAPI App Entry Point](07-fastapi-app-entry.md)   | `backend/app.py`                    | 04, 03     |

**Milestone**: `docker-compose up` starts all services, tables auto-created, `/docs` loads.

---

## Phase 2: Spotify Integration + Playlist Import

| #   | Plan                                             | Creates                                              | Depends on |
| --- | ------------------------------------------------ | ---------------------------------------------------- | ---------- |
| 08  | [Spotify OAuth](08-spotify-auth.md)              | `backend/services/spotify_auth.py`, `/auth/*` routes | 03         |
| 09  | [Spotify Service](09-spotify-service.md)         | `backend/services/spotify_service.py`                | 08         |
| 10  | [Queue Service](10-queue-service.md)             | `backend/services/queue_service.py`                  | 06, 09     |
| 11  | [Playlist Import API](11-playlist-import-api.md) | `backend/routes/playlist.py`                         | 10, 07     |

**Milestone**: Import a Spotify playlist, see tracks in queue via `GET /queue`.

---

## Phase 3: Queue Delivery + Analysis

| #   | Plan                                                           | Creates                                                       | Depends on |
| --- | -------------------------------------------------------------- | ------------------------------------------------------------- | ---------- |
| 12  | [Music Analysis Agent](12-analysis-agent.md)                   | `backend/agents/analysis_agent.py`                            | 03         |
| 13  | [Delivery Agent (Telegram)](13-delivery-agent.md)              | `backend/agents/delivery_agent.py`, `notification_service.py` | 03         |
| 14  | [Trigger Recommendation API](14-trigger-recommendation-api.md) | `backend/routes/recommendation.py`                            | 12, 13, 10 |

**Milestone**: `POST /trigger-recommendation` picks a queue track and sends a Telegram message.

---

## Phase 4: Feedback System

| #   | Plan                                                      | Creates                                                                      | Depends on |
| --- | --------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------- |
| 15  | [Feedback Agent + Telegram Handler](15-feedback-agent.md) | `backend/agents/feedback_agent.py`, `telegram_handler.py`, `/feedback` route | 13         |
| 16  | [Taste Modeling Agent](16-taste-model-agent.md)           | `backend/agents/taste_model_agent.py`                                        | 06, 05     |
| 17  | [Taste Profile API](17-taste-profile-api.md)              | `backend/routes/taste.py`                                                    | 16, 06     |

**Milestone**: Press 👍 in Telegram → feedback stored → taste profile created/updated.

---

## Phase 5: Auto-Discovery Pipeline

| #   | Plan                                     | Creates                             | Depends on |
| --- | ---------------------------------------- | ----------------------------------- | ---------- |
| 18  | [Planner Agent](18-planner-agent.md)     | `backend/agents/planner_agent.py`   | 06         |
| 19  | [Discovery Agent](19-discovery-agent.md) | `backend/agents/discovery_agent.py` | 18, 09, 06 |
| 20  | [Ranking Agent](20-ranking-agent.md)     | `backend/agents/ranking_agent.py`   | 19, 06     |

**Milestone**: Empty queue triggers Spotify recommendations → best track delivered, rest queued.

---

## Phase 6: LangGraph Orchestration & Scheduler

| #   | Plan                                           | Creates                                 | Depends on |
| --- | ---------------------------------------------- | --------------------------------------- | ---------- |
| 21  | [LangGraph Workflow](21-langgraph-workflow.md) | `backend/graph/state.py`, `workflow.py` | All agents |
| 22  | [Daily Scheduler](22-daily-scheduler.md)       | `backend/scheduler/daily_job.py`        | 21, 03     |

**Milestone**: Scheduler runs full pipeline at 09:00 KST; both modes work end-to-end.

---

## Phase 7: Evaluation & Remaining Endpoints

| #   | Plan                                                     | Creates                                                    | Depends on |
| --- | -------------------------------------------------------- | ---------------------------------------------------------- | ---------- |
| 23  | [Evaluation Metrics](23-evaluation-metrics.md)           | `backend/evaluation/metrics.py`, `EvaluationMetrics` model | 06         |
| 24  | [Remaining API Endpoints](24-remaining-api-endpoints.md) | `/evaluation/metrics`, `/discovery-path/{track_id}`        | 23, 06     |

**Milestone**: `GET /evaluation/metrics` returns valid numbers after 3+ feedback entries.

---

## Phase 8: Testing

| #   | Plan                                                     | Creates                           | Depends on |
| --- | -------------------------------------------------------- | --------------------------------- | ---------- |
| 25  | [Test Infrastructure](25-test-infrastructure.md)         | `tests/conftest.py` with fixtures | 04, 05     |
| 26  | [Unit & Integration Tests](26-unit-integration-tests.md) | 5 test files                      | 25         |

**Milestone**: `pytest -v` passes all tests with mocked externals.

---

## Phase 9: Knowledge Graph & Visualization (Post-MVP)

| #   | Plan                                                                   | Creates                                      | Depends on |
| --- | ---------------------------------------------------------------------- | -------------------------------------------- | ---------- |
| 27  | [Knowledge Graph & Visualization](27-knowledge-graph-visualization.md) | Neo4j service, graph service, D3.js frontend | All MVP    |

**Milestone**: Discovery path rendered as force-directed graph.

---

## Quick Reference: All Files Created

```
backend/
├── app.py                          (07)
├── config.py                       (03)
├── agents/
│   ├── analysis_agent.py           (12)
│   ├── delivery_agent.py           (13)
│   ├── feedback_agent.py           (15)
│   ├── planner_agent.py            (18)
│   ├── discovery_agent.py          (19)
│   ├── ranking_agent.py            (20)
│   └── taste_model_agent.py        (16)
├── database/
│   ├── db.py                       (04)
│   └── repositories.py             (06)
├── evaluation/
│   └── metrics.py                  (23)
├── graph/
│   ├── state.py                    (21)
│   └── workflow.py                 (21)
├── models/
│   ├── track.py                    (05)
│   ├── dig_queue.py                (05)
│   ├── taste_profile.py            (05)
│   ├── feedback.py                 (05)
│   ├── recommendation_history.py   (05)
│   └── evaluation_metrics.py       (23)
├── routes/
│   ├── auth.py                     (08)
│   ├── playlist.py                 (11)
│   ├── recommendation.py           (14)
│   ├── feedback.py                 (15)
│   ├── taste.py                    (17)
│   ├── evaluation.py               (24)
│   └── discovery_path.py           (24)
├── scheduler/
│   └── daily_job.py                (22)
└── services/
    ├── spotify_auth.py             (08)
    ├── spotify_service.py          (09)
    ├── queue_service.py            (10)
    ├── notification_service.py     (13)
    ├── telegram_handler.py         (15)
    └── knowledge_graph_service.py  (27, post-MVP)

tests/
├── conftest.py                     (25)
├── test_queue.py                   (26)
├── test_ranking.py                 (26)
├── test_taste_update.py            (26)
├── test_discovery.py               (26)
└── test_workflow.py                (26)
```
