# 8. API Endpoints

| Method | Path                         | Purpose                                          |
| ------ | ---------------------------- | ------------------------------------------------ |
| `POST` | `/import-playlist`           | Import Spotify playlist into dig queue           |
| `GET`  | `/queue`                     | View dig queue (pending tracks + count)          |
| `GET`  | `/recommendation/today`      | Today's recommendation + explanation             |
| `POST` | `/feedback`                  | Manual feedback submission (backup for Telegram) |
| `GET`  | `/taste-profile`             | Current taste profile (learned from feedback)    |
| `GET`  | `/discovery-path/{track_id}` | Track metadata + score breakdown                 |
| `POST` | `/trigger-recommendation`    | Manually trigger daily pipeline (dev/testing)    |
| `GET`  | `/evaluation/metrics`        | Evaluation dashboard data                        |
| `GET`  | `/auth/spotify`              | Start Spotify OAuth flow                         |
| `GET`  | `/auth/callback`             | Spotify OAuth callback                           |

---

## Import Playlist Payload

```json
{
  "playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
}
```

Response:

```json
{
  "imported": 42,
  "duplicates_skipped": 3,
  "queue_total": 58
}
```

---

## Feedback Payload

```json
{
  "track_id": 1,
  "feedback_type": "like"
}
```
