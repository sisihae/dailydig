# 1. Project Overview

**Daily Music Discovery Agent** is a **single-user multi-agent system** for digging into unfamiliar music. Instead of matching your existing taste, it helps you explore music you haven't heard before.

The system performs the following functions:

1. Accepts Spotify playlist imports as a "dig queue" of unfamiliar music
2. Delivers one track per day from the queue via Telegram
3. Produces explanations for each track (via Claude LLM)
4. Collects feedback to learn your evolving taste (cold start — no initial data)
5. Auto-discovers similar music from Spotify when the queue runs out
6. Operates an evaluation system to measure discovery engagement

The objective of this project is to implement an **agent orchestration architecture with a feed-first queue system, feedback learning loop, and auto-discovery fallback**.

## Key Design Decisions

- **Single-user**: No auth, hardcoded `user_id=1`. No user registration or login.
- **Spotify only**: No Apple Music integration.
- **Feed-first**: User imports Spotify playlists → songs go into a dig queue → delivered randomly.
- **Cold start**: No taste bootstrapping. Taste profile built purely from feedback.
- **Auto-discovery**: When queue is empty, system fetches 30–50 similar tracks from Spotify using feedback-learned taste.
- **Append mode**: New playlist imports merge into the existing queue.
- **Telegram-based feedback**: Inline keyboard buttons (👍/👎/⏭) directly in the notification message.
- **Local deployment**: Docker Compose on local machine.

## Core Workflow

```
1. User imports a Spotify playlist → tracks added to dig queue
2. Daily at 09:00: pick random track from queue → explain → deliver via Telegram
3. User gives feedback (👍/👎/⏭) → taste profile updated
4. When queue is empty:
   → Notify user ("Switching to auto-discovery")
   → Planner builds strategy from learned taste
   → Discovery Agent fetches 30-50 tracks from Spotify
   → New tracks become the queue, cycle repeats
```

---

## Expected Outcome

The system should:

1. Accept Spotify playlist URLs and import tracks into a dig queue
2. Deliver one track daily at 09:00 KST (random from queue)
3. Explain the track using Claude LLM
4. Deliver via Telegram with inline feedback buttons
5. Learn taste purely from feedback (cold start, no bootstrap)
6. Auto-discover similar music when the queue runs out
7. Notify user when switching from queue to auto-discovery mode
8. Track evaluation metrics (like rate, genre diversity, etc.)
9. Never deliver the same track twice
