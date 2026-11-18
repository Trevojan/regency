import sys, os, json, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"
sys.path.insert(0, S)
import hook_wire as wire, elicit
spec = importlib.util.spec_from_file_location("hook_elicit", S + "/hook-elicit.py")
he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)

tmp = tempfile.mkdtemp()
os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
schema = elicit.load_file(elicit.EXAMPLE)
st = elicit.Store(root)
old = elicit.start(st, schema, "triage-2026-11-17")["session_id"]
elicit.next_questions(st, old)
elicit.record_answer(st, old, "Q_RULE", "B")          # Regent answered in the old session
new = elicit.start(st, schema, "triage-2026-11-18")["session_id"]   # next day, same schema, new task
ask = elicit.next_questions(st, new)["ask"]["questions"]
st.close()
print("old", old, "new", new, "asked in new:", ask[0]["question"], ask[0]["header"])
ev = {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(root), "session_id": "s",
      "tool_input": {"questions": ask}}
out = he.respond(ev)
print("PRE verdict on the NEW session's own rendering:", json.dumps(out)[:400])
# Post: Regent answers A to the new session's question
ev2 = dict(ev, hook_event_name="PostToolUse", tool_input={"questions": ask, "answers": {ask[0]["question"]: "A"}})
out2 = he.respond(ev2)
print("POST:", json.dumps(out2)[:400])
st = elicit.Store(root)
print("old params:", {k:(v["value"],v["status"]) for k,v in st.params(old).items()})
print("new params:", {k:(v["value"],v["status"]) for k,v in st.params(new).items()})
