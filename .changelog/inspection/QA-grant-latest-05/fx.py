"""fx.py <scripts dir> <dir> <kind>... : build proj (git init) under <dir>, record session grant '<kind> **' as sid '<kind>'; print the repo path."""
import os, sys, subprocess
from pathlib import Path
S, D = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(D / "state"), REGENCY_JUDGE_HOME=str(D / "home"))
import judge
root = D / "proj"; root.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(root)], check=True)
for k in sys.argv[3:]:
    judge.record({"session_id": k}, root, f"{k} ** -- whole repo", "Regent: message")
print(root)
