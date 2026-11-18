import sys, os, json, tempfile, subprocess
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import alpha
tmp = tempfile.mkdtemp()
os.environ.update(GIT_AUTHOR_NAME="qa", GIT_AUTHOR_EMAIL="qa@example.invalid", GIT_COMMITTER_NAME="qa",
                  GIT_COMMITTER_EMAIL="qa@example.invalid", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=tmp + "/gc")
repo = alpha.Path(tmp) / "r"; repo.mkdir()
(repo / "a.txt").write_text("x\n")
for a in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "s"]):
    subprocess.run(["git", "-C", str(repo), *a], check=True)
(repo / ".alpha").write_text("a file where the export folder goes\n")    # export target blocked
m = alpha.plan(repo, "main")
m.update(scope={"included": ["the whole thing"], "excluded": []}, build={"command": "", "artefacts": []},
         check=["open a.txt"], limits=["none"])
try:
    alpha.cut(repo, m)
except Exception as e:
    print("cut failed:", type(e).__name__, e)
print("tags after the failure:", alpha.ids(repo))
try:
    alpha.cut(repo, m)
except Exception as e:
    print("retry:", type(e).__name__, e)
