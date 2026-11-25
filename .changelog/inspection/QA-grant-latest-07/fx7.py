"""fx7.py <scripts dir> <dir>: proj (git init, one commit) under <dir> with src/f, build/, .gitignore, .gitmodules, .github/w,
.cache/x, g -> .git (a link inside to the own .git), self -> . (a link to the root), link -> <dir>/a/b/c/outside; no repository
nested below. Session grants: a 'delete **', e 'discard **', d 'history **', l 'layout **', r 'delete .git/**', c 'delete .cache/**'.
State and judge home under <dir>. Prints the repo path."""
import os, sys, subprocess
from pathlib import Path
S, D = Path(sys.argv[1]), Path(sys.argv[2]).resolve(); sys.path.insert(0, str(S))
os.environ.update(REGENCY_HOOK_STATE=str(D / "state"), REGENCY_JUDGE_HOME=str(D / "home"))
import judge
root = D / "proj"; root.mkdir(parents=True, exist_ok=True)
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
G = ["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
subprocess.run(G + ["init", "-q", str(root)], check=True, env=env)
for rel in ("src/f", ".github/w", ".cache/x", "build/o"):
    (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x\n")
(root / ".gitignore").write_text("build/\n"); (root / ".gitmodules").write_text("")
subprocess.run(G + ["-C", str(root), "add", "-A"], check=True, env=env); subprocess.run(G + ["-C", str(root), "commit", "-qm", "t"], check=True, env=env)
(D / "a" / "b" / "c" / "outside" / "x").mkdir(parents=True, exist_ok=True)
for name, target in (("g", root / ".git"), ("self", root), ("link", D / "a" / "b" / "c" / "outside")):
    if not (root / name).is_symlink():
        (root / name).symlink_to(target, target_is_directory=True)
for sid, spec in (("a", "delete **"), ("e", "discard **"), ("d", "history **"), ("l", "layout **"), ("r", "delete .git/**"), ("c", "delete .cache/**")):
    judge.record({"session_id": sid}, root, f"{spec} -- probe", "Regent: message")
print(root)
