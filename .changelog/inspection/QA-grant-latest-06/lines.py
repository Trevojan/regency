"""lines.py <scripts dir> <repo> <sid> <file of commands> [tool]: verdict of each command (one per line), cwd = repo.
Grants already recorded by fx6.py; the state and judge home come from the environment."""
import importlib.util, os, re, sys
from pathlib import Path
S, root, sid, cmds = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]).read_text().splitlines()
tool = sys.argv[5] if len(sys.argv) > 5 else "Bash"
sys.path.insert(0, str(S))
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
os.environ["CLAUDE_PROJECT_DIR"] = str(root)
top = str(root.parent)
for cmd in cmds:
    if not cmd.strip() or cmd.startswith("#"):
        continue
    try:
        out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "cwd": str(root), "tool_input": {"command": cmd}})
    except Exception as e:
        print(f"CRASH {type(e).__name__}: {e} :: {cmd}"); continue
    r = (out or {}).get("hookSpecificOutput", {})
    prop = re.search(r"proposes '([^']*)'", r.get("permissionDecisionReason", ""))
    extra = f" [proposes {prop.group(1)}]" if prop else (" [no script can tell]" if "No script can tell" in r.get("permissionDecisionReason", "") else "")
    print(f"{r.get('permissionDecision', 'allow'):5}{extra.replace(top, '<F>')}  :: {cmd}")
