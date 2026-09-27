from runpy import run_path
from pathlib import Path


def main() -> None:
    script = Path(__file__).resolve().parents[2] / "01-ai-threat-modeling" / "call_aria.py"
    run_path(str(script), run_name="__main__")
