"""
rate_limiter_solution.py
------------------------
Reference copy of the rate limiter in starter/rate_limiter.py.

This is the reference solution. It contains the same implementation that
students read and run in Task 1. When main() runs, the ALLOWED/DENIED output
follows this pattern:
  - cust_0001: requests 1-3 ALLOWED, no more submitted
  - cust_0042: requests 1-3 ALLOWED, requests 4-5 DENIED
  - cust_0001 after 11-second sleep: ALLOWED (window expired)
"""

# ---------------------------------------------------------------------------
# USAGE LOG ANALYSIS — Task 2 answers
# ---------------------------------------------------------------------------
# User(s) identified as abusing the system:
#   cust_0042: 75 requests concentrated in two overnight burst sessions.
#   Timing pattern is non-human: most requests arrive 73–74 seconds apart,
#   in bursts between 02:07 and 03:47 UTC, strongly suggesting a script. Zero guardrail triggers —
#   this is a cost/volume attack, not an injection probing attempt.
#
#   cust_0099: 9 requests (within normal count range) but average query length
#   is 5,266 chars vs. overall average of 559 chars — nearly 10× the norm.
#   Each query submits an oversized context to maximize token consumption.
#   This is a token budget attack, not a rate attack — the per-user hourly
#   limit by count won't catch it; a per-user token budget cap would.
#
# Total estimated cost in the log and largest single-user contributor:
#   Total cost: $3.35 (141 invocations at avg $0.024).
#   cust_0042 accounts for $1.78 (53.1% of total) with 75 invocations.
#   cust_0099 accounts for $0.81 (24.3%) with 9 invocations — high cost per
#   query due to extreme input length.
#
# Users with elevated guardrail_triggered rate:
#   cust_0088: 76.9% trigger rate (10 of 13 requests). The pattern fits
#   systematic injection probing; the harmless explanation is an integration
#   passing raw user content through. All other customers: 0%.
#   cust_0042: 0% trigger rate — volume abuse and injection probing are
#   distinct attack patterns; cust_0042 is targeting cost, not controls.
# ---------------------------------------------------------------------------

import time
from collections import defaultdict
from typing import Dict


class RateLimiter:
    """Sliding window rate limiter that tracks per-user request timestamps."""

    def __init__(self, window_seconds: int = 3600, max_requests: int = 20):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._timestamps: Dict[str, list] = defaultdict(list)

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check whether a user is within their rate limit.
        Records the request if allowed; does not record if denied.
        Returns True if allowed, False if denied.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune timestamps older than the window
        self._timestamps[user_id] = [
            ts for ts in self._timestamps[user_id] if ts > cutoff
        ]

        # Check if under the limit
        if len(self._timestamps[user_id]) < self.max_requests:
            self.record_request(user_id)
            return True
        return False

    def record_request(self, user_id: str) -> None:
        """Append the current timestamp for the user."""
        self._timestamps[user_id].append(time.time())

    def get_user_stats(self, user_id: str) -> dict:
        """
        Return current usage statistics for a user.
        Prunes stale timestamps but does NOT record a new request.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune (same logic as check_rate_limit, but no record_request call)
        self._timestamps[user_id] = [
            ts for ts in self._timestamps[user_id] if ts > cutoff
        ]

        requests_in_window = len(self._timestamps[user_id])
        return {
            "requests_in_window": requests_in_window,
            "remaining_requests": max(0, self.max_requests - requests_in_window),
            "window_seconds": self.window_seconds,
            "max_requests": self.max_requests,
        }


def main():
    print("=== Orion API Rate Limiter — Simulation ===\n")

    limiter = RateLimiter(window_seconds=10, max_requests=3)

    print("User: cust_0001 (normal usage — 3 requests within limit)")
    for i in range(1, 4):
        allowed = limiter.check_rate_limit("cust_0001")
        status = "ALLOWED" if allowed else "DENIED"
        print(f"  Request {i}: {status}")
    stats = limiter.get_user_stats("cust_0001")
    print(f"  Stats after 3 requests: {stats}\n")

    print("User: cust_0042 (abusive usage — 5 requests, limit is 3)")
    for i in range(1, 6):
        allowed = limiter.check_rate_limit("cust_0042")
        status = "ALLOWED" if allowed else "DENIED"
        print(f"  Request {i}: {status}")
    stats = limiter.get_user_stats("cust_0042")
    print(f"  Stats after 5 attempts: {stats}\n")

    print("Waiting 11 seconds for cust_0001's window to expire...")
    time.sleep(11)
    allowed = limiter.check_rate_limit("cust_0001")
    status = "ALLOWED" if allowed else "DENIED"
    print(f"  cust_0001 request after window reset: {status}")
    stats = limiter.get_user_stats("cust_0001")
    print(f"  Stats after window reset: {stats}\n")

    print("Simulation complete.")
    print("With a limit of 3, each user's first 3 requests are ALLOWED and the rest are DENIED until the window passes.")


if __name__ == "__main__":
    main()
