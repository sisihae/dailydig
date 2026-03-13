# 11. Error Handling

- **Empty queue + no taste profile**: Cannot auto-discover without feedback data. Send Telegram message asking user to import a playlist. Skip daily recommendation.
- **Spotify API failures**: Retry with exponential backoff (max 3 retries). If all fail, skip daily recommendation and log error.
- **Playlist import failures**: Return error to user with details. Don't partially import.
- **Claude API failures**: Fallback to template-based explanation (no LLM).
- **Telegram send failures**: Retry once, then store recommendation in DB as "undelivered" for manual retrieval via API.
- **LangGraph node errors**: Set `error` in AgentState, short-circuit to END. Log full error for debugging.
- **Scheduler duplicate protection**: Redis lock key `daily_rec:YYYY-MM-DD` prevents re-runs.
