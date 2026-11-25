"""why.py <scripts dir> <repo> <sid> <cmd>...: the full verdict and reason of each command, cwd = repo (grants already recorded by the caller's fixture)."""
import importlib.util, os, sys
from pathlib import Path
S, root, sid = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]; sys.path.insert(0, str(S))
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
os.environ["CLAUDE_PROJECT_DIR"] = str(root)
for cmd in sys.argv[4:]:
    out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "cwd": str(root), "tool_input": {"command": cmd}})
    r = (out or {}).get("hookSpecificOutput", {})
    print(f"{r.get('permissionDecision', 'allow'):5} {cmd}\n      {r.get('permissionDecisionReason', '').replace(str(root), '<proj>')}")
