"""mutate5.py <src scripts dir> <work dir>: remove each part of attempt 5's fix in a fresh copy; report which cases go red."""
import shutil, subprocess, sys, os
from pathlib import Path
SRC, WORK = Path(sys.argv[1]), Path(sys.argv[2])
M = {
 "H1 moved: always physical (as before)": ("hook-hazard.py", "logical = None if physical else canonical(t)", "logical = None"),
 "H2 canonical: no folder check before '..'": ("hook-hazard.py", 'if part == ".." and kept and not os.path.isdir(Path(t.anchor, *kept)):', "if False:"),
 "H3 physical_cd: never physical": ("hook-hazard.py", 'return flags[-1:] == ["P"]', "return False"),
 "H4 reached: finds nothing": ("hook-hazard.py", "out += [None] if found is None else found", "out += []"),
 "H5 recursive: rm never recursive": ("hook-hazard.py", 'flags = args[:args.index("--")] if "--" in args else args\n    return cmd == "find" or any(', 'flags = []\n    return cmd == "find" or any('),
 "H6 forced_twice: never": ("hook-hazard.py", "for a in flags if a.startswith(\"-\")) >= 2", "for a in flags if a.startswith(\"-\")) >= 99"),
 "H7 a glob's wildcard part ignored": ("hook-hazard.py", "pick = None if part is None else (", "pick = None if True else ("),
 "H8 a glob's dot rule ignored": ("hook-hazard.py", ' and (g[:1] == "." or n[:1] != "."))', ")"),
 "H9 no '**' beside what it reaches": ("hook-hazard.py", "return (named or ([judge.ALL] if below else [])) + below", "return named + below"),
 "H10 respond passes no deadline": ("hook-hazard.py", "deadline=time.monotonic() + judge.WALK_SECONDS)", "deadline=None)"),
 "H11 find reaches nothing below": ("hook-hazard.py", ' + reached(args[:stop] or ["."], here, root, deadline)', ""),
 "J1 search goes on below a found repository": ("judge.py", "found.append(folder)\n            continue", "found.append(folder)"),
 "J2 search follows links": ("judge.py", "e.is_dir(follow_symlinks=False)", "e.is_dir(follow_symlinks=True)"),
 "J3 search enters .git": ("judge.py", "down = e.name != GIT and e.is_dir", "down = e.is_dir"),
 "J4 search ignores the deadline": ("judge.py", "if deadline is not None and time.monotonic() > deadline:", "if False:"),
 "J5 search enters the own .git when named": ("judge.py", "if top / GIT in [real] + list(real.parents):\n        return []", "if False:\n        return []"),
 "J6 search runs for a path outside too": ("judge.py", "    if not lands_in(path, repo):\n        return []\n    real, top", "    real, top"),
 "J7 check: no search below": ("judge.py", 'if kind == "delete":  # removing a folder', 'if False:  # removing a folder'),
 "J8 check: a timed-out search not refused": ("judge.py", '        if None in paths:\n            print("no grant covers it: no script could tell', '        if False:\n            print("no grant covers it: no script could tell'),
 "J9 scandir error not passed": ("judge.py", "        except OSError:\n            continue  # what this user", "        except ZeroDivisionError:\n            continue  # what this user"),
}
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
for label, (f, old, new) in M.items():
    d = WORK / label.split()[0]
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(SRC, d / "scripts"); shutil.copytree(SRC.parent / "library", d / "library")
    t = (d / "scripts" / f).read_text(encoding="utf-8")
    if t.count(old) != 1:
        print(f"== {label}: PATTERN COUNT {t.count(old)}"); continue
    (d / "scripts" / f).write_text(t.replace(old, new), encoding="utf-8")
    print(f"== {label}")
    for s in ("hook-hazard", "judge", "hook-judge"):
        r = subprocess.run([sys.executable, f"scripts/{s}.py", "--selftest"], cwd=d, capture_output=True, text=True, env=env, timeout=600)
        miss = [l[6:] for l in r.stdout.splitlines() if l.startswith("MISS")]
        tail = (r.stdout.strip().splitlines() or [r.stderr.strip()[-150:]])[-1]
        print(f"   {s}: {tail[:90]}")
        for m in miss: print(f"      MISS {m[:140]}")
