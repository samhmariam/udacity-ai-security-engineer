"""
SP08 — Solution: risk_gate()

Lesson:  L17, Implement a Human-in-the-Loop Workflow for an LLM Agent with Python
Video:   topher 206707
Feeds:   the HITL gate in northstar_agent_hardened.py

This is the one function you implement in starter/aria_sp08.py.
Code is lifted verbatim from SOLUTION.md beside this file, which is the
Aria-generation reference. The markers below let tools/build_demos.py splice
it into the starter to produce demo/aria_fixed.py.
"""

# --8<-- BEGIN SPLICE
import re


def risk_gate(query):
    """Return True if this query requires human review."""
    q = query.lower()

    # Dollar amounts over $500
    amounts = re.findall(r'\$[\d,]+', query)
    for amt in amounts:
        value = int(amt.replace('$', '').replace(',', ''))
        if value > 500:
            return True

    # Salary and compensation queries
    salary_keywords = {"salary", "compensation", "pay band", "pay range",
                       "wage", "earnings", "how much does", "how much do"}
    if any(k in q for k in salary_keywords):
        return True

    # Destructive actions
    delete_keywords = {"delete", "remove", "purge", "wipe", "erase"}
    if any(k in q for k in delete_keywords):
        return True

    return False
# --8<-- END SPLICE
