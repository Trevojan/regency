import importlib.util, os, sys
from pathlib import Path
S, F = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(F / "state2"), REGENCY_JUDGE_HOME=str(F / "home2"))
import judge
def load(n, f):
    s = importlib.util.spec_from_file_location(n, S / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
hh, gp = load("hh", "hook-hazard.py"), load("gp", "guard-push.py")
root = F / "proj"; os.environ["CLAUDE_PROJECT_DIR"] = str(root)
judge.record({"session_id": "d"}, root, "history ** -- whole repo", "Regent: message")
for cmd in ("cd current && cd ../../sibling && git push -f origin side", "cd current && cd ../../sibling && git push -f origin main"):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": "d", "cwd": str(root), "tool_input": {"command": cmd}}
    a = hh.respond(ev); b = gp.decide(cmd, str(root))
    f = lambda o: "allow" if not o else o.get("hookSpecificOutput", {}).get("permissionDecision", str(o)[:40])
    print(f"hook-hazard {f(a):5} guard-push {str(b)[:60]} :: {cmd}")
