"""Mutation run: each mutant removes one behaviour in a fresh copy of the head export and runs the self-tests.
Usage: python3 -B -I mutate.py <head export dir> <work dir>"""
import sys, shutil, subprocess, os
from pathlib import Path
HEAD, WORK = Path(sys.argv[1]), Path(sys.argv[2])
M = [
    ("M1 rank without last_presented", "scripts/elicit.py",
     'rank = (worded, store.last_presented(sess["session_id"], q["id"]), sess["updated_at"], sess["session_id"])',
     'rank = (worded, sess["updated_at"], sess["session_id"])', ["elicit", "hook-elicit"]),
    ("M2 header alone recognises", "scripts/elicit.py", "if worded or optioned:", "if True:", ["elicit", "hook-elicit"]),
    ("M3 locate: render not spoken", "scripts/elicit.py",
     'spoken(render(schema, q, store.params(sess["session_id"]))) == words',
     'render(schema, q, store.params(sess["session_id"])) == words', ["elicit", "hook-elicit"]),
    ("M4 pre: want not spoken", "scripts/hook-elicit.py", 'elicit.spoken(want["question"])', 'want["question"]', ["hook-elicit"]),
    ("M5 carried = whole row on any overlap", "scripts/reconstruction.py",
     "        st[\"carried\"] += bytes_carried\n", "        st[\"carried\"] += r[\"bytes\"] if lines_carried else 0\n",
     ["reconstruction"]),
    ("M6 no legacy filter", "scripts/reconstruction.py", 'kept = [r for r in rows if r.get("b0") is not None]',
     'kept = [dict(r, b0=r.get("b0") or 0) for r in rows]', ["reconstruction"]),
    ("M7 b0 always 0", "scripts/hook-reads.py", "sum(len(c) for c in lines[:start - 1])", "0", ["hook-reads"]),
    ("M8 no ALTER on an old store", "scripts/hook-reads.py", '        con.execute("ALTER TABLE reads ADD COLUMN b0 INTEGER")',
     "        pass", ["hook-reads"]),
]
for name, rel, old, new, tests in M:
    d = WORK / name.split()[0]
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(HEAD, d)
    f = d / rel
    src = f.read_text(encoding="utf-8")
    assert src.count(old) == 1, (name, src.count(old))
    f.write_text(src.replace(old, new), encoding="utf-8")
    print(f"== {name}")
    for t in tests:
        p = subprocess.run([sys.executable, "-B", str(d / "scripts" / f"{t}.py"), "--selftest"], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        out = (p.stdout + p.stderr).strip().splitlines()
        fails = [x for x in out if not x.startswith("pass")]
        print(f"   {t}: exit {p.returncode} | " + " || ".join(x[:150] for x in fails[-4:]))
