# SP07 — Solution: Structured Logging & IR (Vantage / Aria)

## Working log_interaction() Implementation

```python
def log_interaction(user_id, query, response):
    """Log one JSON line per interaction."""
    logger = logging.getLogger("aria")
    haystack = f"{query}\n{response}".lower()
    anomalous = any(flag in haystack for flag in RED_FLAGS)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "query": query,
        "response": response[:200],
        "anomalous": anomalous,
    }
    logger.info(json.dumps(entry))
```

## Expected Log Output (aria_sp07.log)

Four JSON lines, one per interaction. The third interaction (user u047 asking about salaries with an injection) should be `"anomalous": true` if the model response contains any RED_FLAG phrase.

## What Good Structured Logs Enable

- **Incident reconstruction**: Every interaction is timestamped and attributed to a user
- **Anomaly alerting**: `anomalous: true` entries can trigger automated alerts
- **Audit trails**: Compliance requires evidence of what the AI said, to whom, and when

## What to Look For in Student Work

- `log_interaction()` writes valid JSON lines to `aria_sp07.log`
- Each entry includes timestamp, user_id, query, and response
- `anomalous` flag is set correctly for the injection attempt
- Bonus: Student adds a second anomaly detection rule beyond the provided RED_FLAGS list
