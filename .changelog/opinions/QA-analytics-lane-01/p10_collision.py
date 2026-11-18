import sys, os, json, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
st = elicit.Store(root); sid = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "done-last-week")["session_id"]
for q, v in (("Q_RULE", "B"), ("Q_BASE", "X1"), ("Q_RELEASE", "X2"), ("Q_NOTE", "RGN")):
    elicit.record_answer(st, sid, q, v)
print("session complete:", elicit.status(st, sid)["complete"], "| session status:", elicit.status(st, sid)["session_status"])
st.close()
unrelated = {"question": "Who should own the deploy pipeline change?", "header": "Owner",
             "options": [{"label": "Platform team", "description": "p"}, {"label": "App team", "description": "a"}]}
out = he.respond({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(root), "session_id": "x",
                  "tool_input": {"questions": [unrelated]}})
print("unrelated pop-up, header 'Owner':", json.dumps(out)[:330])
