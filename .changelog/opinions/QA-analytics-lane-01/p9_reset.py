import sys, os, json, tempfile, subprocess
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
st = elicit.Store(root)
a = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "task-A")["session_id"]
b = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "task-B")["session_id"]
elicit.record_answer(st, a, "Q_RULE", "B")          # task-A touched last
st.close()
r = subprocess.run([sys.executable, S + "/elicit.py", "--repo", str(root), "reset"], capture_output=True, text=True,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
print("reset with no --session: exit", r.returncode, r.stdout.strip())
r = subprocess.run([sys.executable, S + "/elicit.py", "--repo", str(root), "next"], capture_output=True, text=True,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
print("next with no --session ->", json.loads(r.stdout)["session_id"])
