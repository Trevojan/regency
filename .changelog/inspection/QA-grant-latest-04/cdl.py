"""cdl.py <scripts dir> <fixture dir>: bash's logical cd against the physical reading; and -C through an outside link."""
import importlib.util, os, sys, subprocess
from pathlib import Path
S, F = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(F / "state"), REGENCY_JUDGE_HOME=str(F / "home"))
import hook_wire as wire, judge
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
root = F / "proj"; os.environ["CLAUDE_PROJECT_DIR"] = str(root)
def v(cmd, sid, cwd=root):
    out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "cwd": str(cwd), "tool_input": {"command": cmd}})
    return "allow" if not out else out["hookSpecificOutput"]["permissionDecision"]
judge.record({"session_id": "a"}, root, "delete ** -- whole repo", "Regent: message")
judge.record({"session_id": "e"}, root, "discard ** -- whole repo", "Regent: message")
for sid, cmd in (("a", "cd current && cd .. && rm -rf cache/*"), ("a", "cd current/.. && rm -rf cache/precious"),
                 ("a", "rm -rf cache/*"), ("e", "cd current && cd ../cache && git reset --hard"),
                 ("e", "git -C cache reset --hard"), ("e", "git -C ../alias reset --hard"), ("a", "cd ../alias && rm -rf src")):
    print(f"{sid} {v(cmd, sid):5}  {cmd}")
