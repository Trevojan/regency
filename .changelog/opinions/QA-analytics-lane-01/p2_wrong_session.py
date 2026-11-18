import sys, os, json, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
spec = importlib.util.spec_from_file_location("hook_elicit", S + "/hook-elicit.py")
he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
schema = elicit.load_file(elicit.EXAMPLE)
st = elicit.Store(root)
old = elicit.start(st, schema, "triage-2026-11-17")["session_id"]
elicit.next_questions(st, old)                       # presented, never answered (unfinished)
new = elicit.start(st, schema, "triage-2026-11-18")["session_id"]
ask = elicit.next_questions(st, new)["ask"]["questions"]
st.close()
ev = {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(root), "session_id": "s",
      "tool_input": {"questions": ask}}
print("PRE:", he.respond(ev))
he.respond(dict(ev, hook_event_name="PostToolUse", tool_input={"questions": ask, "answers": {ask[0]["question"]: "B"}}))
st = elicit.Store(root)
print("old", old, {k:(v["value"],v["status"]) for k,v in st.params(old).items()})
print("new", new, {k:(v["value"],v["status"]) for k,v in st.params(new).items()})
print("new complete?", elicit.status(st, new)["questions"]["Q_RULE"]["status"])
