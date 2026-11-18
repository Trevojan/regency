import sys, os, json, tempfile, copy, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
s = copy.deepcopy(elicit.load_file(elicit.EXAMPLE))
s["questions"][0]["prompt"] = "AN-01-01 (gap, src/a.py): approve()  has no reversal\npath - promote, recycle or trash?"
print("schema problems:", elicit.problems(s))
st = elicit.Store(root); sid = elicit.start(st, s, "T")["session_id"]
ask = elicit.next_questions(st, sid)["ask"]["questions"]; st.close()
out = he.respond({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "cwd": str(root), "session_id": "x",
                  "tool_input": {"questions": ask}})
print("engine's own rendering passed verbatim ->", (out or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allowed"))
