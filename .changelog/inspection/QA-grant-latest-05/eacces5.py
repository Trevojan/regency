"""eacces5.py <scripts dir> <repo> <cmd>: simulate EACCES on stat of entries under <repo>/data/db, and on scandir of <repo>/data/db; run hook-hazard through wire.serve."""
import errno, importlib.util, io, json, os, sys, pathlib
S, root, cmd = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]; sys.path.insert(0, str(S))
real_stat, real_scandir = pathlib.Path.stat, os.scandir
def stat(self, *a, **k):
    if "data/db" in self.as_posix() and self.name in (".git", "HEAD", "objects", "refs"):
        raise PermissionError(errno.EACCES, "Permission denied", str(self))
    return real_stat(self, *a, **k)
def scandir(p="."):
    if str(p).endswith("data/db"):
        raise PermissionError(errno.EACCES, "Permission denied", str(p))
    return real_scandir(p)
pathlib.Path.stat = stat; os.scandir = scandir
import hook_wire as wire
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": "delete", "cwd": str(root), "tool_input": {"command": cmd}}
sys.stdin = io.StringIO(json.dumps(ev)); out = io.StringIO(); sys.stdout = out
wire.serve(hh.respond, guard=True); sys.stdout = sys.__stdout__
t = out.getvalue().strip(); print((json.loads(t)["hookSpecificOutput"]["permissionDecision"] + " | " + json.loads(t)["hookSpecificOutput"]["permissionDecisionReason"][:120]) if t else "allow (empty)", " ::", cmd)
