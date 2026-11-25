"""mut4.py <base dir with scripts/ and library/> <work dir>: QA-06 §4's four mutations (H11, H15, H16, H17), each in a fresh copy;
print the hook-hazard self-test tail and every MISS line."""
import os, shutil, subprocess, sys
from pathlib import Path
BASE, WORK = Path(sys.argv[1]), Path(sys.argv[2])
M = {
 "none": None,
 "H11 pushd ignores the mode": ('option = cd_mode(w[1:]) if name(w[0]) == "cd" else None', 'option = cd_mode(w[1:]) if name(w[0]) == "cd" else False'),
 "H15 git clean: --exclude only in full": ('or (len(word) > 2 and "--exclude".startswith(word))', 'or word == "--exclude"'),
 "H16 git clean: one -f per word": ('return cluster.group(1).count("f") if cluster else 0', 'return min(1, cluster.group(1).count("f")) if cluster else 0'),
 "H17 git clean: --force not counted": ('    if len(word) > 2 and "--force".startswith(word):\n        return 1', "    if False:\n        return 1"),
}
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
for k in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "REGENCY_JD", "REGENCY_HOOK_STATE", "REGENCY_JUDGE_HOME"):
    env.pop(k, None)
for label, m in M.items():
    d = WORK / label.split()[0]
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(BASE / "scripts", d / "scripts"); shutil.copytree(BASE / "library", d / "library")
    f = d / "scripts" / "hook-hazard.py"; t = f.read_text(encoding="utf-8")
    if m:
        if t.count(m[0]) != 1:
            print(f"== {label}: PATTERN COUNT {t.count(m[0])}"); continue
        f.write_text(t.replace(m[0], m[1]), encoding="utf-8")
    r = subprocess.run([sys.executable, "scripts/hook-hazard.py", "--selftest"], cwd=d, capture_output=True, text=True, env=env, timeout=900)
    miss = [l[6:] for l in r.stdout.splitlines() if l.startswith("MISS")]
    print(f"== {label}: {(r.stdout.strip().splitlines() or [r.stderr[-200:]])[-1]}")
    for x in miss: print(f"   MISS {x[:170]}")
