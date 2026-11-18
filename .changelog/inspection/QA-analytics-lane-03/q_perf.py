import sys, os, time, tempfile, importlib.util
from pathlib import Path
sys.dont_write_bytecode = True
S = sys.argv[1]; sys.path.insert(0, S)
import hook_wire as wire, elicit
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
for n in (50, 500):
    base = wire.build_fixture(Path(tmp) / f"n{n}"); st = elicit.Store(base); sch = elicit.load_file(elicit.EXAMPLE)
    for i in range(n):
        sid = elicit.start(st, sch, f"task-{i}")["session_id"]; elicit.next_questions(st, sid, 4)
    ask = elicit.next_questions(st, sid, 4)["ask"]["questions"]; st.close()
    t = time.perf_counter(); out = he.respond({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(base), "session_id": "x", "tool_input": {"questions": ask}})
    print(f"{n} open sessions, {len(ask)} entries: Pre {time.perf_counter() - t:.2f}s ->", ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecision", "allowed"))
