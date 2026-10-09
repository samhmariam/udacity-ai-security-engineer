"""
SP12 — Solution: chat_safe()

Lesson:  L25, Implement External Content Segregation in Prompts with Python
Video:   topher 206715
Feeds:   prompt segregation in northstar_agent_hardened.py

This is the one function you implement in starter/aria_sp12.py.
Code is lifted verbatim from SOLUTION.md beside this file, which is the
Aria-generation reference. The markers below let tools/build_demos.py splice
it into the starter to produce demo/aria_fixed.py.
"""

# --8<-- BEGIN SPLICE
def chat_safe(user_input):
    """
    Proper message-level segregation — system and user are never concatenated.

    ARIA_SYSTEM stays in its own system message; untrusted user_input stays in
    its own user message. The model receives a structural boundary the text
    cannot cross.
    """
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
# --8<-- END SPLICE
