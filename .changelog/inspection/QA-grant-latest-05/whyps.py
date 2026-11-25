"""whyps.py <scripts dir> <repo> <sid> <tool> <cmd>...: verdicts for one tool (Bash or PowerShell)."""
import importlib.util, os, sys
from pathlib import Path
S, root, sid, tool = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]; sys.path.insert(0, str(S))
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
for cmd in sys.argv[5:]:
    out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "cwd": str(root), "tool_input": {"command": cmd}})
    print(f"{(out or {}).get('hookSpecificOutput', {}).get('permissionDecision', 'allow'):5} [{tool}] {cmd}")
