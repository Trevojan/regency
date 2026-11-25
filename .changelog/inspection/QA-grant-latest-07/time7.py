"""time7.py <scripts dir> <repo> <sid> <runs> <cmd>...: wall time of hook-hazard.py fed each PreToolUse event on stdin."""
import json, os, subprocess, sys, time
S, R, sid, runs = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
for cmd in sys.argv[5:]:
    ev = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "cwd": R, "tool_input": {"command": cmd}})
    ts, dec = [], ""
    for _ in range(runs):
        t0 = time.monotonic()
        p = subprocess.run([sys.executable, f"{S}/hook-hazard.py"], input=ev, capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": R})
        ts.append(time.monotonic() - t0)
        out = p.stdout.strip(); dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"
    print(f"{min(ts):5.2f}-{max(ts):5.2f}s rc={p.returncode} {dec:5} :: {cmd}")
