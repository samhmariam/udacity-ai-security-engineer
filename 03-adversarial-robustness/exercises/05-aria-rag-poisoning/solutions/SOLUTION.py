"""
SP05 — Solution: scan_for_injection()

Lesson:  L11, Secure a RAG System with Access Controls and Data Validation
Video:   topher 206704
Feeds:   RAG controls in the project's northstar_agent_hardened.py

This is the one function you implement in starter/aria_sp05.py.

SP03 scanned a document a user uploaded. This scans a document the *system*
retrieved and already trusts. Same technique, higher stakes: a poisoned entry
in the knowledge base attacks every query that retrieves it, not just one.
"""

# --8<-- BEGIN SPLICE
import re

# Retrieved documents are prose. Anything that reads as an instruction aimed at
# the model is out of place in a knowledge base article, which is what makes
# this detectable at all.
KB_INJECTION_PATTERNS = [
    r"system\s*:",
    r"ignore\s+(your|all|previous|prior|the\s+above)",
    r"disregard\s+(your|all|previous|prior|the\s+above)",
    r"previous\s+instructions",
    r"new\s+instructions?\s*:",
    r"admin\s+mode",
    r"developer\s+mode",
    r"you\s+are\s+now\s+",
    r"forget\s+(that\s+)?you",
    r"override\s+(your|all|the)",
    r"when\s+(asked|answering|summarizing)[^.]{0,60}(also|instead|always)",
    r"do\s+not\s+mention\s+(this|these)",   # payloads that ask to stay hidden
]

_KB_COMPILED = [re.compile(p, re.IGNORECASE) for p in KB_INJECTION_PATTERNS]


def scan_for_injection(doc_text):
    """
    Return True if doc_text contains injection patterns, False if clean.

    Runs on every retrieved document before it is placed in the model's
    context. True means the document is quarantined and not used to answer.
    """
    return any(p.search(doc_text) for p in _KB_COMPILED)
# --8<-- END SPLICE


# ---------------------------------------------------------------------------
# WHY IT IS WRITTEN THIS WAY
# ---------------------------------------------------------------------------
#
# Why scan at retrieval instead of at ingestion?
#   Do both. Ingestion scanning is cheaper and catches the bulk. Retrieval
#   scanning is what still protects you when a document was poisoned *after*
#   it was ingested, or ingested before you had a scanner, or edited in place
#   by someone with write access to the source system. The knowledge base is
#   not a trust boundary just because you control it.
#
# Why two patterns SP03 did not have?
#   "when asked ... also/instead/always" and "do not mention this" are
#   conditional payloads -- they lie dormant until a matching query arrives,
#   which is what makes poisoned retrieval different from a poisoned upload.
#   A document that asks not to be mentioned has declared its own intent.
#
# Why quarantine the whole document rather than strip the bad line?
#   At retrieval time you cannot tell whether the rest of the document was
#   also tampered with. Dropping one answer is cheap; serving a half-sanitized
#   poisoned document is not. SP10 takes the other approach, stripping rather
#   than rejecting, and the difference is worth understanding: strip when the
#   content is the user's own and they need it back, reject when it is
#   authoritative content the system vouches for.
#
# ---------------------------------------------------------------------------
# WHAT THIS CONTROL DOES NOT STOP
# ---------------------------------------------------------------------------
#
# Everything in SP03's list -- paraphrase, encoding, splitting across lines --
# applies here too. Two failure modes are specific to RAG:
#
#   - Semantic poisoning with no instruction at all. A document that simply
#     states something false ("expense limits were suspended in October") has
#     no pattern to match. It is not an injection; it is a lie, and the model
#     will repeat it faithfully. No keyword scanner catches this.
#   - Retrieval starvation. An attacker who floods the index with documents
#     that rank highly for a target query can crowd out the true answer without
#     writing a single instruction.
#
# The controls that address those are provenance and access control: who was
# allowed to write this document, when, and does the answer cite a source the
# user is cleared to see. That is the other half of this lesson, and the half
# your project has to implement.
