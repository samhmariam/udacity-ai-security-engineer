#!/usr/bin/env python3
"""
Course 3 redesign launcher.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SP_MAP = {
    "01": (
        "skill-pair-01-vulnerable-endpoint-basics",
        "Reliable Prompt Injection Basics",
        "starter/endpoint_sp01.py",
    ),
    "02": (
        "skill-pair-02-vulnerable-endpoint-owasp-audit",
        "OWASP Audit of a Vulnerable LLM App",
        "starter/endpoint_sp02.py",
    ),
    "03": ("skill-pair-03-aria-indirect-injection", "Aria Indirect Injection", "starter/aria_sp03.py"),
    "04": ("skill-pair-04-aria-defensive-prompting", "Aria Defensive Prompting", "starter/aria_sp04.py"),
    "05": ("skill-pair-05-aria-rag-poisoning", "Aria RAG Poisoning", "starter/aria_sp05.py"),
    "06": ("skill-pair-06-aria-agent-boundaries", "Aria Agent Boundaries", "starter/aria_sp06.py"),
    "07": ("skill-pair-07-aria-logging-ir", "Aria Logging and IR", "starter/aria_sp07.py"),
    "08": ("skill-pair-08-aria-hitl-gates", "Aria Human Risk Gates", "starter/aria_sp08.py"),
    "09": (
        "skill-pair-09-vulnerable-agent-task-hijacking",
        "Vulnerable Agent Task Hijacking",
        "starter/agent_sp09.py",
    ),
    "10": (
        "skill-pair-10-aria-multimodal-injection",
        "Aria Multimodal Injection",
        "starter/aria_sp10.py",
    ),
    "11": (
        "skill-pair-11-aria-named-guardrails",
        "Aria Named Guardrails",
        "starter/aria_sp11.py",
    ),
    "12": (
        "skill-pair-12-agent-prompt-segregation",
        "Agent Prompt Segregation",
        "starter/aria_sp12.py",
    ),
}


def normalize_sp(value: str) -> str:
    value = value.strip().upper().replace("SP", "")
    if len(value) == 1:
        value = f"0{value}"
    if value not in SP_MAP:
        raise SystemExit(f"Unknown skill pair: {value}")
    return value


def list_sps() -> None:
    for sp, (directory, title, script) in SP_MAP.items():
        print(f"SP{sp}  {title}  ->  {directory}/{script}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sp", nargs="?", help="Skill pair number, e.g. 1, 01, SP01")
    args = parser.parse_args()

    if not args.sp:
        list_sps()
        return

    sp = normalize_sp(args.sp)
    directory, title, script = SP_MAP[sp]
    exercise = ROOT / directory / "EXERCISE.md"
    workdir = ROOT / directory
    cmd = [sys.executable, script]

    print(f"SP{sp} — {title}", flush=True)
    print(f"Exercise: {exercise}", flush=True)
    print(flush=True)
    raise SystemExit(subprocess.call(cmd, cwd=workdir))


if __name__ == "__main__":
    main()
