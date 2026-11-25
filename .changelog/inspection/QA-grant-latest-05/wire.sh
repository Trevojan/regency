#!/bin/bash
# wire.sh <scripts dir> <repo> <sid> <cmd>: feed one PreToolUse Bash event to hook-hazard.py on stdin; print wall time, exit code, decision
S=$1; R=$2; SID=$3; CMD=$4
EV=$(python3 -c 'import json,sys; print(json.dumps({"hook_event_name":"PreToolUse","tool_name":"Bash","session_id":sys.argv[1],"cwd":sys.argv[2],"tool_input":{"command":sys.argv[3]}}))' "$SID" "$R" "$CMD")
t0=$(date +%s.%N); OUT=$(printf '%s' "$EV" | CLAUDE_PROJECT_DIR=$R python3 $S/hook-hazard.py 2>/dev/null); rc=$?; t1=$(date +%s.%N)
DEC=$(printf '%s' "$OUT" | python3 -c 'import json,sys; t=sys.stdin.read().strip(); d=json.loads(t)["hookSpecificOutput"] if t else {}; print(d.get("permissionDecision","allow"), "|", d.get("permissionDecisionReason","")[:110])' 2>/dev/null || echo "RAW $OUT")
printf '%6.2fs rc=%s %s  :: %s\n' "$(echo "$t1 - $t0" | bc)" "$rc" "$DEC" "$CMD"
