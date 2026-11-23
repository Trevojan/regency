"""eacces.py <scripts dir> <repo>: simulate EACCES on stat of <repo>/data/db/.git; run the hook through wire.serve."""
import errno, importlib.util, io, json, os, sys, pathlib
S, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); sys.path.insert(0, str(S))
real_stat = pathlib.Path.stat
def stat(self, *a, **k):
    if "data/db" in self.as_posix() and self.name in (".git", "HEAD", "objects", "refs"):
        raise PermissionError(errno.EACCES, "Permission denied", str(self))
    return real_stat(self, *a, **k)
pathlib.Path.stat = stat
import hook_wire as wire
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": "a", "cwd": str(root), "tool_input": {"command": "rm -rf data/db/x"}}
sys.stdin = io.StringIO(json.dumps(ev)); out = io.StringIO(); sys.stdout = out
wire.serve(hh.respond, guard=True); sys.stdout = sys.__stdout__
t = out.getvalue().strip(); print(json.loads(t)["hookSpecificOutput"]["permissionDecision"] + " | " + json.loads(t)["hookSpecificOutput"]["permissionDecisionReason"][:150] if t else "allow (empty)")
