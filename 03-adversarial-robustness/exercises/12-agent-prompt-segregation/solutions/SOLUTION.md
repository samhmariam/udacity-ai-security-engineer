# SP12 — Solution: Prompt Segregation (Vantage / Aria)

## Working chat_safe() Implementation

```python
def chat_safe(user_input):
    """Proper message-level segregation — system and user never concatenated."""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": ARIA_SYSTEM},
            {"role": "user",   "content": user_input},
        ],
        "stream": False,
    }, timeout=180)
    resp.raise_for_status()
    return resp.json()["message"]["content"]
```

## Why chat_unsafe() Fails

In `chat_unsafe()`, ARIA_SYSTEM and user_input are concatenated into a single string and sent as a `"user"` message. The model receives no structural boundary between instructions and input — they're just text. An injecting user can write `"Ignore the system instructions above..."` and the model may comply, because "above" literally refers to text earlier in the same message.

In `chat_safe()`, ARIA_SYSTEM is in the `"system"` role, which the model treats with higher authority than the `"user"` role. The boundary is structural, not just positional.

## Expected Comparison

| Test | chat_unsafe() | chat_safe() |
|------|--------------|-------------|
| Normal query | Answers correctly | Answers correctly |
| Injection attempt | May comply with injection | Refuses, stays in role |

## What to Look For in Student Work

- `chat_safe()` uses the messages array with separate system and user roles
- Student does not concatenate strings — the user input goes only into the user role content
- Bonus: Student can explain why structural segregation is stronger than positional separation
