"""tree7.py <dir> <folders> <files per folder>: a git repository <dir>/proj with <folders> folders (fan-out 20) of empty files."""
import os, subprocess, sys
from pathlib import Path
D, N, F = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
root = D / "proj"; root.mkdir(parents=True, exist_ok=True)
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(root)], check=True, env=env)
made, level = 0, [root / "t"]
(root / "t").mkdir(exist_ok=True)
while made < N:
    nxt = []
    for p in level:
        for i in range(20):
            if made >= N: break
            q = p / f"d{i}"; q.mkdir(); made += 1; nxt.append(q)
            for j in range(F): open(q / f"f{j}", "w").close()
        if made >= N: break
    level = nxt
print(root, made, made * F)
