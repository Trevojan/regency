"""Exploratory mutants for attempt 3 (QA, not a criterion). Usage: python3 -B -I mutate3.py <export> <work dir> [runs]"""
import sys, shutil, subprocess, os
from pathlib import Path
HEAD, WORK = Path(sys.argv[1]), Path(sys.argv[2])
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 1
RANK = 'rank = (worded, store.last_presented(sess["session_id"], q["id"]), sess["updated_at"], sess["session_id"])'
M = [
    ("X1 updated_at ranked before rendered-last", "scripts/elicit.py", RANK,
     'rank = (worded, sess["updated_at"], store.last_presented(sess["session_id"], q["id"]), sess["session_id"])'),
    ("X2 first rendering instead of last (MIN)", "scripts/elicit.py",
     '"SELECT MAX(event_id) FROM elicit_events WHERE session_id=? AND "',
     '"SELECT MIN(event_id) FROM elicit_events WHERE session_id=? AND "'),
    ("X3 fourth tie-break inverted (lower id wins)", "scripts/elicit.py", RANK,
     'rank = (worded, store.last_presented(sess["session_id"], q["id"]), sess["updated_at"], [-ord(c) for c in sess["session_id"]])'),
    ("X4 fourth tie-break dropped", "scripts/elicit.py", RANK,
     'rank = (worded, store.last_presented(sess["session_id"], q["id"]), sess["updated_at"])'),
    ("X5 worded dropped from the rank", "scripts/elicit.py", RANK,
     'rank = (store.last_presented(sess["session_id"], q["id"]), sess["updated_at"], sess["session_id"])'),
]
for name, rel, old, new in M:
    d = WORK / name.split()[0]
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(HEAD, d)
    f = d / rel
    src = f.read_text(encoding="utf-8")
    assert src.count(old) == 1, (name, src.count(old))
    f.write_text(src.replace(old, new), encoding="utf-8")
    print(f"== {name}")
    for t in ("elicit", "hook-elicit"):
        seen = {}
        for _ in range(RUNS):
            p = subprocess.run([sys.executable, "-B", str(d / "scripts" / f"{t}.py"), "--selftest"], capture_output=True,
                               text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            out = (p.stdout + p.stderr).strip().splitlines()
            key = (p.returncode, " || ".join(x[:150] for x in out if not x.startswith("pass")))
            seen[key] = seen.get(key, 0) + 1
        for (rc, msg), k in seen.items():
            print(f"   {t}: exit {rc} x{k}/{RUNS} | {msg}")
