"""rt7.py <scripts dir> <dir> <scope>: for each act, a fresh fx7 fixture; the proposal with no grant, recorded as given but
'for <scope>', then the act again and a neighbour act that the grant must not open."""
import importlib.util, os, re, subprocess, sys
from pathlib import Path
S, D, SCOPE = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), sys.argv[3]
ACTS = [("rm -rf .git", "rm -rf ."), ("rm -f .git/index.lock", "rm -rf .git"), ("rm -rf .", "rm -rf ../"),
        ("find . -name '*.o' -delete", "rm -rf .git"), ("rm -rf .*", "rm -rf ."), ("cd src && rm -rf ..", "rm -rf link/x"),
        ("rm -rf g/objects", "rm -rf .git/refs"), ("rm -rf .git src", "rm -rf .git"), ("Remove-Item -Recurse -Force .git", "rm -f .git/HEAD")]
for n, (act, other) in enumerate(ACTS):
    d = D / f"rt{n}"
    subprocess.run([sys.executable, "-I", str(Path(__file__).parent / "fx7.py"), str(S), str(d)], check=True, capture_output=True)
    os.environ.update(REGENCY_HOOK_STATE=str(d / "state"), REGENCY_JUDGE_HOME=str(d / "home"), CLAUDE_PROJECT_DIR=str(d / "proj"))
    sys.path.insert(0, str(S))
    for m in [k for k in sys.modules if k in ("judge", "hh", "hook_wire", "guard_push")]: del sys.modules[m]
    import judge
    spec = importlib.util.spec_from_file_location("hh", S / "hook-hazard.py"); hh = importlib.util.module_from_spec(spec); spec.loader.exec_module(hh)
    tool = "PowerShell" if act.startswith("Remove-Item") else "Bash"
    def v(cmd, sid):
        out = hh.respond({"hook_event_name": "PreToolUse", "tool_name": tool if cmd == act else "Bash", "session_id": sid, "cwd": str(d / "proj"), "tool_input": {"command": cmd}})
        r = (out or {}).get("hookSpecificOutput", {})
        return r.get("permissionDecision", "allow"), r.get("permissionDecisionReason", "")
    first, why = v(act, "z")
    m = re.search(r"proposes 'grant: (.*) for session -- <why>'", why)
    if not m:
        print(f"{first:5} NO PROPOSAL :: {act} :: {why[-120:]}"); continue
    try:
        gid = judge.record({"session_id": "y"}, d / "proj", f"{m.group(1)} for {SCOPE} -- as proposed", "Regent: message")
    except Exception as e:
        print(f"RECORD FAILED {type(e).__name__}: {e} :: {act}"); continue
    again, why2 = v(act, "y"); other_v, _ = v(other, "y"); fresh, _ = v(act, "x")
    print(f"{first:5} -> granted {str(gid)[:8]:8} -> {again:5} (other session {fresh:5}) | neighbour {other_v:5} {other!r} :: {act}  [{m.group(1).replace(str(D), '<D>')}]")
