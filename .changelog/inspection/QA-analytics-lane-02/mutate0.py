"""M0: the head tree with locate_question put back to its eef6edc body (new helpers kept), new self-tests run.
Usage: python3 -B -I mutate0.py <head export> <base export> <work dir>"""
import sys, re, shutil, subprocess, os
from pathlib import Path
HEAD, BASE, WORK = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
d = WORK / "M0"
if d.exists():
    shutil.rmtree(d)
shutil.copytree(HEAD, d)
grab = lambda src: re.search(r"\ndef locate_question\(.*?(?=\n\n\n)", src, re.S).group(0)
new_src = (d / "scripts/elicit.py").read_text(encoding="utf-8")
old_body = grab((BASE / "scripts/elicit.py").read_text(encoding="utf-8"))
old_body = old_body.replace("def locate_question(store, header, text=None):", "def locate_question(store, header, text=None, labels=None):")
(d / "scripts/elicit.py").write_text(new_src.replace(grab(new_src), old_body), encoding="utf-8")
for t in ("elicit", "hook-elicit"):
    p = subprocess.run([sys.executable, "-B", str(d / "scripts" / f"{t}.py"), "--selftest"], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    lines = (p.stdout + p.stderr).strip().splitlines()
    print(f"M0 {t}: exit {p.returncode}")
    for x in lines:
        if not x.startswith("pass"):
            print("   ", x[:160])
