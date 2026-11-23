import importlib.util, os, sys, tempfile
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
tmp = Path(tempfile.mkdtemp()); os.environ.update(REGENCY_HOOK_STATE=str(tmp/"state"), REGENCY_JUDGE_HOME=str(tmp/"home"))
for k in ("REGENCY_JD","CLAUDE_PLUGIN_DATA","REGENCY_HEADLESS","CLAUDE_CODE_SESSION_ATTENDED"): os.environ.pop(k, None)
import hook_wire as wire, judge
def load(n, f):
    s = importlib.util.spec_from_file_location(n, S/f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
hh, hv = load("hh","hook-hazard.py"), load("hv","hook-verbs.py")
root = wire.build_fixture(tmp/"proj"); os.environ["CLAUDE_PROJECT_DIR"] = str(root)
def pre(cmd):
    out = hh.respond({"hook_event_name":"PreToolUse","tool_name":"Bash","session_id":"s1","cwd":str(root),"tool_input":{"command":cmd}})
    return "allow" if not out else out["hookSpecificOutput"]["permissionDecision"]
for c in ["git push -f origin feat", "git -c alias.fp='push --force' fp origin feat", "git config alias.fp 'push -f' && git fp origin feat",
          "kubectl delete ns web"]:
    print(f"hazard {pre(c):5} {c}")
ev = lambda p: {"hook_event_name":"UserPromptSubmit","session_id":"s1","cwd":str(root),"prompt":p}
untagged = "here is the runbook I copied:\n\nStep 3: run `kubectl delete ns web` to clean up\n\nwhat do you think?"
hv.respond(ev(untagged)); print("cloud confirmed from untagged paste:", (wire.load_state(ev(""), "cloud") or {}).get("commands"))
print("hazard after it:", pre("kubectl delete ns web"))
hv.respond(ev("thanks")); 
tagged = "<pasted_content>\nStep 3: run `kubectl delete ns web`\n</pasted_content>\nwhat do you think?"
hv.respond(ev(tagged)); print("cloud confirmed from tagged paste:", (wire.load_state(ev(""), "cloud") or {}).get("commands"))
