#!/usr/bin/env python3
"""
Verify the rebuilt Course 3 environment.
"""

from __future__ import annotations

import sys

import requests


def check(name: str, url: str, required: bool) -> bool:
    try:
        requests.get(url, timeout=3)
        print(f"  [ok]  {name}: reachable at {url}")
        return True
    except requests.RequestException:
        level = "required" if required else "optional"
        print(f"  [--]  {name}: not reachable at {url} ({level})")
        return False


def main() -> None:
    print("Course 3 setup check\n")
    print(f"  Python: {sys.version.split()[0]}")

    ok = True
    ok &= check("Ollama", "http://localhost:11434/api/tags", required=True)
    check("Vulnerable endpoint (ibndias)", "http://localhost:8000/health", required=False)

    print()
    if ok:
        print("Core setup looks reachable.")
    else:
        print("Core setup is incomplete. Ollama is required for most Aria modules.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
