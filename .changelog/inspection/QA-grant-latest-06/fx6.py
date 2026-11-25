"""fx6.py <scripts dir> <dir> <kind>...: proj (git init) under <dir> with link -> <dir>/a/b/c/outside and <dir>/a/b/c/x;
record session grant '<kind> **' as sid '<kind>'; print the repo path. State and judge home under <dir>."""
import os, sys, subprocess
from pathlib import Path
S, D = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(D / "state"), REGENCY_JUDGE_HOME=str(D / "home"))
import judge
root = D / "proj"; root.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(root)], check=True)
(D / "a" / "b" / "c" / "outside").mkdir(parents=True, exist_ok=True); (D / "a" / "b" / "c" / "x").mkdir(exist_ok=True)
(root / "x").mkdir(exist_ok=True)
if not (root / "link").exists():
    (root / "link").symlink_to(D / "a" / "b" / "c" / "outside", target_is_directory=True)
for k in sys.argv[3:]:
    judge.record({"session_id": k}, root, f"{k} ** -- whole repo", "Regent: message")
print(root)
