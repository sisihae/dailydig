# 12. Knowledge Graph & Visualization (Post-MVP, Phase 8)

## Knowledge Graph

Purpose: Enable deeper music exploration.

Graph nodes:

```
Artist
Genre
Track
```

Edges:

```
artist → genre
artist → influenced_by → artist
track → artist
```

Example:

```
D'Angelo
→ neo soul
→ influenced_by Marvin Gaye
```

Used by Discovery Agent to find related artists beyond Spotify's algorithm.

---

## Discovery Path Visualization

Goal: Show how the recommendation was discovered.

Example path:

```
D'Angelo
↓ genre similarity
Erykah Badu
↓ artist similarity
Hiatus Kaiyote
↓ recommended track
Nakamarra
```

Output format:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

Frontend renders graph using D3.js.
