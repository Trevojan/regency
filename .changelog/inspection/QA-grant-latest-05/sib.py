"""sib.py <scripts dir> <fixture dir>: a git act after a logical cd that leaves for a sibling repository."""
import importlib.util, os, sys
from pathlib import Path
S, F = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(F / "state"), REGENCY_JUDGE_HOME=str(F / "home"))
import hook_wire as wire, judge
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
root = F / "proj"; os.environ["CLAUDE_PROJECT_DIR"] = str(root)
def v(cmd, sid):
    out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "cwd": str(root), "tool_input": {"command": cmd}})
    return "allow" if not out else out["hookSpecificOutput"]["permissionDecision"] + " | " + out["hookSpecificOutput"]["permissionDecisionReason"][:60]
for sid, how in (("d", "history"), ("e", "discard"), ("a", "delete")):
    judge.record({"session_id": sid}, root, f"{how} ** -- whole repo", "Regent: message")
for sid, cmd in (("e", "cd current && cd ../../sibling && git reset --hard"), ("d", "cd current && cd ../../sibling && git push -f origin main"),
                 ("a", "cd current && cd ../../sibling && git clean -fdx"), ("a", "cd current && cd ../../sibling && git branch -D side"),
                 ("e", "cd ../sibling && git reset --hard"), ("e", "cd current/../../sibling && git reset --hard"),
                 ("a", "cd current && cd ../../sibling && rm -rf work"), ("e", "git -C current/../../sibling reset --hard")):
    print(f"{sid} {v(cmd, sid):70}  {cmd}")
