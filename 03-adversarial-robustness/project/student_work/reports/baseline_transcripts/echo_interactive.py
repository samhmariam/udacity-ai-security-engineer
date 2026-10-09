# Runs northstar_agent.py --interactive unmodified, echoing piped stdin so the transcript shows user turns.
import builtins, runpy, sys
_orig = builtins.input
def _echo(prompt=""):
    line = _orig(prompt)
    print(line, flush=True)
    return line
builtins.input = _echo
sys.argv = ["northstar_agent.py", "--interactive"]
runpy.run_path("northstar_agent.py", run_name="__main__")
