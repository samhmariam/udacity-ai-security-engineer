"""
SP07 — Solution: log_interaction()

Lesson:  L15, Implement Agent Monitoring and Incident Response with Python
Video:   topher 206706
Feeds:   student_work/reports/ir_playbook.md in the project

This is the one function you implement in starter/aria_sp07.py.
Code is lifted verbatim from SOLUTION.md beside this file, which is the
Aria-generation reference. The markers below let tools/build_demos.py splice
it into the starter to produce demo/aria_fixed.py.
"""

# --8<-- BEGIN SPLICE
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
# --8<-- END SPLICE
