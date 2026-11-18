import sys, os, json, tempfile, subprocess
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
st = elicit.Store(root)
sid = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "A")["session_id"]
st.con.execute("UPDATE elicit_schemas SET definition=replace(definition, 'Which rule', 'Which law')")
st.close()
plain = {"question": "Delete the build folder?", "header": "Judge", "options": [{"label": "Yes", "description": "y"}, {"label": "No", "description": "n"}]}
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
for phase in ("PreToolUse", "PostToolUse"):
    ev = {"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(root), "session_id": "s",
          "tool_input": {"questions": [plain]}, "tool_response": "x"}
    p = subprocess.run([sys.executable, S + "/hook-elicit.py"], input=json.dumps(ev), capture_output=True, text=True, env=env, cwd=tmp)
    print(phase, "exit", p.returncode, "stdout:", p.stdout[:300], "| stderr:", p.stderr[:200])
