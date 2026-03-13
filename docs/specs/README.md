# Daily Music Discovery Agent — Spec Index

| File                                               | Description                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [overview.md](overview.md)                         | Project overview, design decisions, expected outcome                                 |
| [architecture.md](architecture.md)                 | System architecture (dual-mode: queue + auto-discovery) + LangGraph workflow         |
| [tech-stack.md](tech-stack.md)                     | Tech stack, dependencies, configuration                                              |
| [repository-structure.md](repository-structure.md) | Repository file/folder layout                                                        |
| [data-models.md](data-models.md)                   | Track, DigQueue, TasteProfile, Feedback, RecommendationHistory                       |
| [agents.md](agents.md)                             | All 7 agents: Planner, Discovery, Ranking, Analysis, Delivery, Feedback, Taste Model |
| [spotify-integration.md](spotify-integration.md)   | Spotify OAuth, playlist import, service methods                                      |
| [api-endpoints.md](api-endpoints.md)               | FastAPI endpoints                                                                    |
| [scheduler.md](scheduler.md)                       | APScheduler daily job (dual-mode)                                                    |
| [evaluation.md](evaluation.md)                     | Evaluation metrics system                                                            |
| [error-handling.md](error-handling.md)             | Error handling strategy                                                              |
| [knowledge-graph.md](knowledge-graph.md)           | Knowledge graph + visualization (post-MVP)                                           |
| [mvp-and-phases.md](mvp-and-phases.md)             | MVP scope + implementation phases (9 phases)                                         |
