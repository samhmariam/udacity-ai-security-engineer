# SP08 — Solution: Human-in-the-Loop Risk Gates (Vantage / Aria)

## Working risk_gate() Implementation

```python
import re

def risk_gate(query):
    """Return True if this query requires human review."""
    q = query.lower()

    # Check for dollar amounts over $500
    amounts = re.findall(r'\$[\d,]+', query)
    for amt in amounts:
        value = int(amt.replace('$', '').replace(',', ''))
        if value > 500:
            return True

    # Check for salary/compensation queries
    salary_keywords = {"salary", "compensation", "pay band", "pay range",
                       "wage", "earnings", "how much does", "how much do"}
    if any(k in q for k in salary_keywords):
        return True

    # Check for delete/remove/purge requests
    delete_keywords = {"delete", "remove", "purge", "wipe", "erase"}
    if any(k in q for k in delete_keywords):
        return True

    return False
```

## Expected Results

| Request | risk_gate() | Outcome |
|---------|-------------|---------|
| Remote work guidelines | False | Aria responds |
| $6,400 expense | **True** | Escalated |
| Salary range query | **True** | Escalated |
| Delete contractor records | **True** | Escalated |

## What to Look For in Student Work

- `risk_gate()` correctly escalates the last 3 requests and not the first
- Student uses regex for dollar amount detection (not just keyword matching)
- Bonus: Student considers edge cases — what about "$499" written as "four hundred ninety-nine dollars"?
