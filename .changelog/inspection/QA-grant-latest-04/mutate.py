"""mutate.py <src scripts dir> <work dir>: remove each piece of the fix in a fresh copy; report which cases go red."""
import shutil, subprocess, sys, os
from pathlib import Path
SRC, WORK = Path(sys.argv[1]), Path(sys.argv[2])
M = {
 "M1 relative ignores lands_in (textual, as before)": ("judge.py",
   'return inside.as_posix().strip(".") if lands_in(path, repo) else Path(os.path.realpath(str(path))).as_posix()',
   'return inside.as_posix().strip(".")'),
 "M2 git where: textual .git walk, as before": ("hook-hazard.py",
   'return [] if root is None or judge.lands_in(where, root) else [where]',
   'top = next((p for p in [where] + list(where.parents) if (p / ".git").exists()), None)\n    return [] if root is None or top == root else [where]'),
 "M3 resolve normalises again": ("hook-hazard.py",
   'return p if p.is_absolute() else Path(here) / p',
   'return Path(os.path.normpath(str(p if p.is_absolute() else Path(here) / p)))'),
 "M4 lands_in without the nested check": ("judge.py",
   'return not any(holds_repository(folder) for folder in way[:way.index(top)])', 'return True'),
 "M5 holds_repository without the bare check": ("judge.py",
   'return (folder / ".git").exists() or all((folder / part).exists() for part in ("HEAD", "objects", "refs"))',
   'return (folder / ".git").exists()'),
 "M6 lands_in without the own-.git exception": ("judge.py",
   '    if top / ".git" in way:\n        return True\n', ''),
 "M7 judge check normalises again": ("judge.py",
   'paths = args[2:] if kind == "push" else [Path.cwd() / a for a in args[2:]]',
   'paths = args[2:] if kind == "push" else [Path(os.path.normpath(str(Path.cwd() / a))) for a in args[2:]]'),
 "M8 outside reads as written, not where it lands": ("judge.py",
   'else Path(os.path.realpath(str(path))).as_posix()', 'else written.as_posix()'),
 "M9 lands_in ignores links (textual top check)": ("judge.py",
   'real, top = Path(os.path.realpath(str(path))), Path(os.path.realpath(str(repo)))',
   'real, top = Path(os.path.normpath(str(path))), Path(os.path.normpath(str(repo)))'),
}
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
for label, (f, old, new) in M.items():
    d = WORK / label.split()[0]
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(SRC, d / "scripts"); shutil.copytree(SRC.parent / "library", d / "library")
    t = (d / "scripts" / f).read_text(encoding="utf-8")
    assert t.count(old) == 1, (label, t.count(old))
    (d / "scripts" / f).write_text(t.replace(old, new), encoding="utf-8")
    print(f"== {label}")
    for s in ("hook-hazard", "judge", "hook-judge", "hook-verbs", "guard-push", "hook-refs"):
        r = subprocess.run([sys.executable, f"scripts/{s}.py", "--selftest"], cwd=d, capture_output=True, text=True, env=env)
        miss = [l[6:] for l in r.stdout.splitlines() if l.startswith("MISS")]
        tail = (r.stdout.strip().splitlines() or [r.stderr.strip()[-150:]])[-1]
        print(f"   {s}: {tail[:90]}")
        for m in miss: print(f"      MISS {m[:150]}")
