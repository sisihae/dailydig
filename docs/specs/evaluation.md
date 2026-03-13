# 10. Evaluation System

Metrics tracked (rolling 30-day window):

## User Engagement

```
like_rate = likes / total_recommendations
dislike_rate = dislikes / total_recommendations
skip_rate = skips / total_recommendations
```

## Discovery Quality

```
new_artist_rate = first_time_artists / total_recommendations
genre_diversity = unique_genres_recommended / total_recommendations
```

## Storage

`evaluation_metrics` table with daily snapshots.
