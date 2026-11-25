"""ex.py <scripts dir>: exploratory cases for D1/D2's class, beyond the named steps. Prints one verdict per line."""
import importlib.util, os, sys, tempfile, subprocess, re
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
tmp = Path(tempfile.mkdtemp()).resolve()
os.environ.update(REGENCY_HOOK_STATE=str(tmp / "state"), REGENCY_JUDGE_HOME=str(tmp / "home"))
for k in ("REGENCY_JD", "CLAUDE_PLUGIN_DATA"): os.environ.pop(k, None)
import hook_wire as wire, judge
spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
root = wire.build_fixture(tmp / "proj"); os.environ["CLAUDE_PROJECT_DIR"] = str(root)
G = ["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "init.defaultBranch=main"]
subprocess.run(G + ["init", "-q", str(root)])
deep = tmp / "a" / "b" / "c" / "outside"; (deep / "precious").mkdir(parents=True); (tmp / "a" / "b" / "keep").mkdir()
(root / "link").symlink_to(deep, target_is_directory=True)
(root / "src").mkdir(exist_ok=True); (root / "src" / "f").write_text("x")
(root / "build2").symlink_to(root / "src", target_is_directory=True)          # a link that stays inside
subprocess.run(G + ["init", "-q", str(root / "nested")])
(root / "vendor" / "lib").mkdir(parents=True); subprocess.run(G + ["init", "-q", str(root / "vendor" / "lib")])
(root / "sub").mkdir(); (root / "sub" / ".git").write_text("gitdir: ../.git/modules/sub\n")   # a submodule's gitfile
(root / ".git" / "modules" / "sub").mkdir(parents=True)
(root / "loop").symlink_to(root / "loop")
(root / "dl").symlink_to(tmp / "nowhere" / "deep", target_is_directory=True)
(root / "lf").symlink_to(deep / "precious" / "file"); (deep / "precious" / "file").write_text("p")
for part in ("objects", "refs"): (root / "data" / part).mkdir(parents=True)
(root / "data" / "HEAD").write_text("not a repo\n")
(tmp / "projlink").symlink_to(root, target_is_directory=True)

def v(cmd, sid, cwd=root, tool="Bash"):
    try:
        out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "cwd": str(cwd), "tool_input": {"command": cmd}})
    except Exception as e:  # noqa
        return f"CRASH {type(e).__name__}: {e}"
    if not out:
        return "allow"
    r = out["hookSpecificOutput"]
    prop = re.search(r"proposes '([^']*)'", r.get("permissionDecisionReason", ""))
    return r["permissionDecision"] + (f"  [proposes {prop.group(1)}]" if prop else "")

def say(sid, cmd, **kw):
    out = v(cmd, sid, **kw)
    print(f"{sid} {out.replace(str(tmp), '<tmp>')[:150]:60}  {cmd.replace(str(tmp), '<tmp>')}" + (f"   (cwd {str(kw['cwd']).replace(str(tmp), '<tmp>')})" if 'cwd' in kw else ""))
    return out

judge.record({"session_id": "a"}, root, "delete ** -- whole repo", "Regent: message")
judge.record({"session_id": "e"}, root, "discard ** -- whole repo", "Regent: message")
judge.record({"session_id": "d"}, root, "history ** -- whole repo", "Regent: message")
judge.record({"session_id": "g"}, root, "delete build2/** -- the build link", "Regent: message")
judge.record({"session_id": "h"}, root, f"delete {(tmp / 'keep').as_posix()}/** -- a folder outside, by its text", "Regent: message")
judge.record({"session_id": "n"}, root, "discard nested/** -- the nested one, relative", "Regent: message")
print("-- A. the Judge's proposal, granted, then the same act")
for sid, cmd in (("a", "rm -rf link/precious"), ("e", "git -C nested reset --hard")):
    out = say(sid, cmd)
    m = re.search(r"proposes grant: (\w+) (\S+) for session", out)
    if m:
        judge.record({"session_id": sid + "2"}, root, f"{m.group(1)} {m.group(2)} -- as proposed", "Regent: message")
        say(sid + "2", cmd)
print("-- B/C. a link reached by an absolute path, after a cd, through a ..")
say("a", f"rm -rf {root}/link/precious"); say("a", "cd src && rm -rf ../link/precious"); say("a", "rm -rf link/../src/f")
say("a", "rm -rf ../proj/src/f")
print("-- D. a '..' that climbs out of the repository's text through a link (grant h names <tmp>/keep by its text)")
say("h", "rm -rf link/../../keep"); say("a", "rm -rf link/../../keep")
print("-- E. a link that stays inside, under a relative glob that names the link (grant g: build2/**)")
say("g", "rm -rf build2/*"); say("g", "find build2/ -delete"); say("g", "rm -rf src/f")
print("-- F. an act in this repository that reaches down into a nested one (delete ** / discard **)")
for cmd in ("rm -rf *", "rm -rf .", "rm -rf vendor", "find . -delete", "find vendor -delete"):
    say("a", cmd)
say("a", "git clean -ffdx"); say("e", "git submodule foreach git reset --hard")
print("-- G. the line itself makes the link or the repository it then acts through")
say("a", f"ln -s {deep} l2 && rm -rf l2/*"); say("e", "git init -q n2 && git -C n2 reset --hard")
print("-- H/I/J/K. a loop, a dangling link, a link to a file, the link itself")
say("a", "rm -rf loop/x"); say("a", "rm -rf dl/"); say("a", "rm lf"); say("a", "rm -rf link"); say("a", "unlink link")
print("-- L. cd read physically where bash reads it logically")
say("a", "cd link/.. && rm -rf build"); say("a", "cd link && cd .. && rm -rf build")
print("-- M. a submodule's gitfile, and its git folder under this .git")
say("e", "git -C sub reset --hard"); say("a", "rm -rf .git/modules/sub"); say("a", "rm -rf sub")
print("-- N/O. the session opened through a link to the repository")
say("a", "rm -rf src/f", cwd=tmp / "projlink"); say("a", f"rm -rf {root}/src/f", cwd=tmp / "projlink"); say("e", "git reset --hard", cwd=tmp / "projlink")
print("-- P. a plain folder shaped like a bare repository (HEAD, objects, refs)")
say("a", "rm -rf data/objects")
print("-- R. PowerShell")
say("a", "Remove-Item -Recurse -Force link/*", tool="PowerShell"); say("a", "Remove-Item -Recurse -Force src/f", tool="PowerShell")
print("-- T. a relative glob that names the nested repository (grant n: discard nested/**)")
say("n", "git -C nested reset --hard")
print("-- the plain inside acts still covered")
for sid, cmd in (("a", "rm -rf src"), ("a", "rm -rf build"), ("e", "git reset --hard"), ("e", "git -C src checkout -- ."), ("d", "git push -f origin feat")):
    say(sid, cmd)
