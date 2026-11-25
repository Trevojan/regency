import importlib.util, os, sys, json
from pathlib import Path
S, root = Path(sys.argv[1]), Path(sys.argv[2]); sys.path.insert(0, str(S))
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
for cmd in ("rm -rf data/db/x", "rm -rf src/x"):
    try:
        out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": "a", "cwd": str(root), "tool_input": {"command": cmd}})
        print(cmd, "->", "allow" if not out else out["hookSpecificOutput"]["permissionDecision"])
    except Exception as e:
        print(cmd, "-> RAISES", type(e).__name__, str(e).replace(str(root), "<proj>"))
