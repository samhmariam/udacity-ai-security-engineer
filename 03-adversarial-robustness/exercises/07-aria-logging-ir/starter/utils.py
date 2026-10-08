"""
utils.py — Shared helpers for the AI Security Lab SP exercises.

This file is imported automatically by each exercise script.
You do not need to read or modify it.
"""

import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen2.5:7b-instruct"


def check_ollama():
    """
    Verify Ollama is reachable before starting an exercise.
    Exits with a clear, actionable message if it is not.
    """
    try:
        requests.get("http://localhost:11434/api/tags", timeout=4)
    except requests.exceptions.ConnectionError:
        print()
        print("  ✗  Cannot reach Ollama on localhost:11434.")
        print()
        print("  Fix: open a second terminal and run:")
        print("         ollama serve")
        print()
        print("  Then come back here and re-run this script.")
        print()
        sys.exit(1)
    except requests.exceptions.Timeout:
        print()
        print("  ✗  Ollama is not responding (timed out).")
        print("  Try restarting it:  ollama serve")
        print()
        sys.exit(1)
