"""Store checks for hook-reads b0. Usage: python3 -B -I q_store.py <head scripts> <base scripts> <procs>"""
import sys, os, sqlite3, tempfile, importlib.util, subprocess, json
from pathlib import Path
sys.dont_write_bytecode = True
HEAD, BASE, PROCS = sys.argv[1], sys.argv[2], int(sys.argv[3])


def load(S, name):
    spec = importlib.util.spec_from_file_location(name, S + "/hook-reads.py"); m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, S); spec.loader.exec_module(m); sys.path.pop(0); return m


tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
sys.path.insert(0, HEAD); import hook_wire as wire
print("sqlite", sqlite3.sqlite_version)
# 1. rollback: the eef6edc hook on a store the head hook migrated, then the DROP COLUMN the change notes name
root = wire.build_fixture(Path(tmp) / "rb"); doc = root / ".guidelines/.decisions/ARCHITECTURE.md"
ev = {"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": "s", "cwd": str(root), "tool_input": {"file_path": str(doc)}}
new, old = load(HEAD, "hr_new"), load(BASE, "hr_old")
new.respond(ev)
try:
    old.respond(ev); print("1 old hook on a b0 store: recorded")
except Exception as e:
    print("1 old hook on a b0 store:", type(e).__name__, str(e)[:90])
db = wire.virtual_dir(root) / "index.sqlite"
con = sqlite3.connect(str(db)); con.execute("ALTER TABLE reads DROP COLUMN b0"); con.commit(); con.close()
old.respond(ev)
con = sqlite3.connect(str(db)); print("  after DROP COLUMN, old hook rows:", con.execute("SELECT COUNT(*) FROM reads").fetchone()[0]); con.close()
# 2. a pre-b0 store, first writes from PROCS parallel processes (async hooks)
root = wire.build_fixture(Path(tmp) / "race"); doc = root / ".guidelines/.decisions/ARCHITECTURE.md"
db = wire.virtual_dir(root) / "index.sqlite"
old.respond(dict(ev, cwd=str(root), tool_input={"file_path": str(doc)}))
runner = Path(tmp) / "one.py"
runner.write_text(f"""import sys, os, importlib.util
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('hr', {HEAD!r} + '/hook-reads.py'); m = importlib.util.module_from_spec(spec)
sys.path.insert(0, {HEAD!r}); spec.loader.exec_module(m)
m.respond({{'hook_event_name': 'PostToolUse', 'tool_name': 'Read', 'session_id': 'p' + sys.argv[1], 'cwd': {str(root)!r},
           'tool_input': {{'file_path': {str(doc)!r}, 'offset': 2, 'limit': 3}}}})
""", encoding="utf-8")
ps = [subprocess.Popen([sys.executable, "-B", str(runner), str(i)], stderr=subprocess.PIPE, text=True) for i in range(PROCS)]
errs = [p.communicate()[1].strip().splitlines()[-1:] for p in ps]
con = sqlite3.connect(str(db))
print(f"2 {PROCS} parallel first writes on a pre-b0 store: rows {con.execute('SELECT COUNT(*) FROM reads').fetchone()[0] - 1}/{PROCS}, "
      f"b0 column {'b0' in [r[1] for r in con.execute('PRAGMA table_info(reads)')]}, failures {sum(1 for e in errs if e)}: "
      f"{sorted(set(e[0][:80] for e in errs if e))}")
con.close()
