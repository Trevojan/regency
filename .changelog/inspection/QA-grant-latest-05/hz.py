import importlib.util, json, os, sys, tempfile, subprocess
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
tmp = Path(tempfile.mkdtemp())
os.environ.update(REGENCY_HOOK_STATE=str(tmp/"state"), REGENCY_JUDGE_HOME=str(tmp/"home"))
for k in ("REGENCY_JD", "CLAUDE_PLUGIN_DATA"): os.environ.pop(k, None)
import hook_wire as wire, judge
spec = importlib.util.spec_from_file_location("hh", S/"hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
root = wire.build_fixture(tmp/"proj"); os.environ["CLAUDE_PROJECT_DIR"] = str(root)
subprocess.run(["git","init","-q",str(root)])
outside = tmp/"outside"; (outside/"precious").mkdir(parents=True)
(root/"link").symlink_to(outside, target_is_directory=True)
(root/"nested").mkdir(); subprocess.run(["git","init","-q",str(root/"nested")])
(root/".env").write_text("x"); (root/"env").mkdir(exist_ok=True)
def v(cmd, sid):
    out = hh.respond({"hook_event_name":"PreToolUse","tool_name":"Bash","session_id":sid,"cwd":str(root),"tool_input":{"command":cmd}})
    return "allow" if not out else out["hookSpecificOutput"]["permissionDecision"]
judge.record({"session_id":"a"}, root, "delete ** -- whole repo", "Regent: message")
judge.record({"session_id":"b"}, root, "delete .env -- the dotfile", "Regent: message")
judge.record({"session_id":"c"}, root, "delete env/** -- the env folder", "Regent: message")
judge.record({"session_id":"d"}, root, "history ** -- whole repo", "Regent: message")
judge.record({"session_id":"e"}, root, "discard ** -- whole repo", "Regent: message")
for sid, cmd in [("a","rm -rf link/*"),("a","rm -rf link/"),("a","find link/ -delete"),("a","rm -rf link/precious"),
                 ("a","rm -rf .git"),("a",'rm -rf "$d"'),("a","rm -rf a\\ b"),("a","rm -rf build && echo $(date)"),
                 ("b","rm .env"),("c","rm .env"),("c","rm -rf .env/x"),("c","rm -rf env/x"),
                 ("d","git -C nested push -f origin side"),("e","git -C nested reset --hard"),("e","cd nested && git reset --hard"),
                 ("a","rm -rf ../outside")]:
    print(f"{sid} {v(cmd, sid):5}  {cmd}")
