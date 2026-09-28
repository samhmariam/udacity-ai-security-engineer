"""
rate_limiter.py
---------------
Sliding window rate limiter for the Orion API.

This module enforces per-customer request limits on Bedrock API calls. It is
designed to be imported into the Orion API application and called
before any bedrock-agentcore InvokeHarness request is made.

Usage (in the Streamlit app):
    from rate_limiter import RateLimiter

    limiter = RateLimiter(window_seconds=3600, max_requests=20)

    if not limiter.check_rate_limit(user_id):
        st.error("You've reached the hourly request limit. Please wait before submitting another query.")
        st.stop()

Exercise instructions
---------------------
The implementation is complete. Don't modify it. Read the code, then answer the
Task 1 questions in my_answers/task1_rate_limiter_analysis.md. Run this file
and paste the output into the same answer file:

    python starter/rate_limiter.py

Answer Task 2 (usage log analysis) in my_answers/task2_usage_analysis.md.
"""

import time
from collections import defaultdict
from typing import Dict


class RateLimiter:
    """
    Sliding window rate limiter that tracks per-user request timestamps.

    The sliding window algorithm works as follows:
      - Each user has a list of timestamps recording when their requests occurred.
      - When a new request arrives, timestamps older than `window_seconds` are
        pruned from the list first.
      - The count of remaining timestamps is the number of requests the user has
        made within the current rolling window.
      - If that count is below `max_requests`, the request is allowed and the
        new timestamp is appended. If the count equals or exceeds `max_requests`,
        the request is denied and no timestamp is recorded.

    This is a rolling (sliding) window, not a fixed clock window. A fixed window
    resets at a clock boundary (e.g., the top of every hour), which can be gamed
    by submitting requests just before and just after the reset. The sliding window
    measures the most recent `window_seconds` of activity at all times, which
    cannot be gamed this way.

    Attributes:
        window_seconds (int): Length of the rolling time window in seconds.
        max_requests (int): Maximum number of requests allowed within the window.
        _timestamps (dict): Maps user_id -> list of float timestamps (from time.time()).
    """

    def __init__(self, window_seconds: int = 3600, max_requests: int = 20):
        """
        Initialize the rate limiter.

        Args:
            window_seconds: Rolling window duration in seconds. Default is 3600 (1 hour).
            max_requests: Maximum requests allowed per user within the window. Default is 20.
        """
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        # Keys are user_id strings. Values are lists of float timestamps.
        # defaultdict means a missing key automatically gets an empty list.
        self._timestamps: Dict[str, list] = defaultdict(list)

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check whether a user is within their rate limit and, if so, record the request.

        This method must:
          1. Prune timestamps older than self.window_seconds from the user's list.
          2. Count the remaining timestamps.
          3. If the count is less than self.max_requests:
               - Call self.record_request(user_id) to log the new timestamp.
               - Return True (request is allowed).
          4. If the count equals or exceeds self.max_requests:
               - Do NOT call record_request.
               - Return False (request is denied).

        Args:
            user_id: A string identifying the requesting user (e.g., "cust_0042").

        Returns:
            True if the request is allowed, False if the user has hit their limit.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune timestamps outside the current window
        self._timestamps[user_id] = [
            ts for ts in self._timestamps[user_id] if ts > cutoff
        ]

        if len(self._timestamps[user_id]) < self.max_requests:
            self.record_request(user_id)
            return True
        return False

    def record_request(self, user_id: str) -> None:
        """
        Record a new request for a user by appending the current timestamp.

        This method must:
          - Append time.time() to self._timestamps[user_id].

        Note: This method is called by check_rate_limit when a request is allowed.
        You should not call it directly from application code — use check_rate_limit
        instead, which enforces the limit before recording.

        Args:
            user_id: A string identifying the requesting user.

        Returns:
            None
        """
        self._timestamps[user_id].append(time.time())

    def get_user_stats(self, user_id: str) -> dict:
        """
        Return current usage statistics for a user within the active window.

        This method must:
          1. Prune timestamps older than self.window_seconds (same pruning logic
             as check_rate_limit — do NOT record a new timestamp here).
          2. Count the remaining timestamps.
          3. Return a dict with at minimum these four keys:
               {
                   "requests_in_window": <int>,   # how many requests in the current window
                   "remaining_requests": <int>,   # how many more requests are allowed
                   "window_seconds": <int>,       # the configured window length
                   "max_requests": <int>,         # the configured maximum
               }

        Args:
            user_id: A string identifying the requesting user.

        Returns:
            A dict with usage stats as described above.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune (same logic as check_rate_limit, but do NOT record a new request)
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


# ---------------------------------------------------------------------------
# main() runs a short simulation that shows the limiter allowing and denying requests.
# ---------------------------------------------------------------------------

def main():
    """
    Demonstrate and verify the RateLimiter with a small simulation.

    This function creates a limiter with a short window (10 seconds) and a low
    limit (3 requests) so the behavior is easy to observe quickly. It then
    simulates requests from two users and prints results.
    """
    print("=== Orion API Rate Limiter — Simulation ===\n")

    # Short window and low limit to make the demo observable without sleeping long.
    limiter = RateLimiter(window_seconds=10, max_requests=3)

    # --- Simulate cust_0001: normal user, 3 requests (should all be allowed) ---
    print("User: cust_0001 (normal usage — 3 requests within limit)")
    for i in range(1, 4):
        allowed = limiter.check_rate_limit("cust_0001")
        status = "ALLOWED" if allowed else "DENIED"
        print(f"  Request {i}: {status}")

    stats = limiter.get_user_stats("cust_0001")
    print(f"  Stats after 3 requests: {stats}\n")

    # --- Simulate cust_0042: abusive user, 5 requests (2 should be denied) ---
    print("User: cust_0042 (abusive usage — 5 requests, limit is 3)")
    for i in range(1, 6):
        allowed = limiter.check_rate_limit("cust_0042")
        status = "ALLOWED" if allowed else "DENIED"
        print(f"  Request {i}: {status}")

    stats = limiter.get_user_stats("cust_0042")
    print(f"  Stats after 5 attempts: {stats}\n")

    # --- Demonstrate window expiry ---
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
