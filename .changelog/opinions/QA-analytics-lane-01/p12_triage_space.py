import sys, os, json, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit, analytics as an
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
repo = an.fixture_repo(tmp)
(repo / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
pk = an.plan(repo, "baseline")
an.record(repo, an.envelope(pk, [an.sample(title="approve()  offers no reversal")]), create=True)
schema = an.triage_schema(repo)
st = elicit.Store(repo); sid = elicit.start(st, schema, "triage-2026-11-18")["session_id"]
ask = elicit.next_questions(st, sid)["ask"]["questions"]; st.close()
print("asked:", repr(ask[0]["question"]))
out = he.respond({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(repo), "session_id": "x",
                  "tool_input": {"questions": ask}})
print("hook on the engine's own rendering:", (out or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allowed"))
