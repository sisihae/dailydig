# 4. Repository Structure

```
music-discovery-agent/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── app.py                           # FastAPI app with lifespan
│   ├── config.py                        # pydantic BaseSettings from .env
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner_agent.py             # Auto-discovery mode only
│   │   ├── discovery_agent.py           # Auto-discovery mode only
│   │   ├── ranking_agent.py             # Auto-discovery mode only
│   │   ├── analysis_agent.py
│   │   ├── delivery_agent.py
│   │   ├── feedback_agent.py
│   │   └── taste_model_agent.py
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                     # AgentState TypedDict
│   │   └── workflow.py                  # LangGraph StateGraph (dual-mode)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── spotify_service.py           # Spotify Web API client
│   │   ├── spotify_auth.py              # OAuth flow
│   │   ├── queue_service.py             # Dig queue management
│   │   ├── notification_service.py      # Telegram Bot
│   │   └── knowledge_graph_service.py   # Post-MVP
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── track.py
│   │   ├── dig_queue.py                 # Dig queue entries
│   │   ├── taste_profile.py
│   │   ├── feedback.py
│   │   └── recommendation_history.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                        # Async engine + sessionmaker + Base
│   │   └── repositories.py             # CRUD operations
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── metrics.py
│   │
│   └── scheduler/
│       ├── __init__.py
│       └── daily_job.py                 # APScheduler cron job
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_ranking.py
│   ├── test_taste_update.py
│   ├── test_discovery.py
│   ├── test_queue.py
│   └── test_workflow.py
│
└── frontend/                            # Post-MVP
    └── discovery_visualization/
```
