"""
SP09 — Solution: validate_action() implementation
"""

# --8<-- BEGIN SPLICE
import json

ALLOWED_ACTIONS = {"DRAFT_CLIENT_EMAIL", "SUMMARIZE_REPORT"}


def validate_action(plan: dict[str, str], original_intent: str) -> bool:
    action = str(plan.get("action", "")).strip().upper()
    if action not in ALLOWED_ACTIONS:
        return False

    text = json.dumps(plan).lower()
    forbidden = ["credentials", "breach", "internal alert", "password", "it-security"]
    return not any(token in text for token in forbidden)
# --8<-- END SPLICE
