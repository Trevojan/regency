"""one.py <scripts dir> <repo> <sid> <cmd>: the verdict of one (multi-line) command over the stdin wire."""
import json, os, subprocess, sys
S, root, sid, cmd = sys.argv[1:5]
ev = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "cwd": root, "tool_input": {"command": cmd}})
out = subprocess.run([sys.executable, f"{S}/hook-hazard.py"], input=ev, capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": root}).stdout.strip()
print(json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow")
