#!/usr/bin/env python3
"""hook-packs.py - the pack dispatcher: runs a pack's own hooks in the projects where it is active.

Claude Code loads a plugin's hooks once per install, for every project. regency's packs (scripts/packs.py,
library/packs.md) are switched on per project, so their hooks reach Claude Code through this one dispatcher,
wired on SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact and SessionEnd.

For one event it runs every hook item that
  - belongs to a pack active in this project (<guidelines>/.packs/active.json),
  - was ratified there by the Regent at the pack's current tree fingerprint (a change anywhere in the pack makes it
    STALE, and a STALE or unratified hook never runs),
  - matches the event's matcher (tool name, session source, compact trigger) and its `if` filter.

Each runs as Claude Code would run it: the event JSON on stdin, ${CLAUDE_PLUGIN_ROOT} pointing at the pack,
${CLAUDE_PLUGIN_DATA} at a folder of its own, ${CLAUDE_PROJECT_DIR} at the repository, within its timeout.
The answers are merged into one:

  PreToolUse    deny beats ask; a pack may add a guard, never remove one: "allow" and a rewritten tool input
                are dropped (the Regent's permission prompts stay his)
  exit code 2   blocks as Claude Code reads it: deny (PreToolUse), block (PostToolUse, UserPromptSubmit)
  context       each pack's additionalContext and, for SessionStart and UserPromptSubmit, plain stdout,
                prefixed with the pack's id
  stop          continue:false from any pack stops, with its reason
  failure       a crash, a timeout or a missing interpreter: one systemMessage line naming the pack and the hook

With no active pack the dispatcher answers nothing, and its fast path exits before importing anything heavy: it
runs on every tool call of every project. Writes nothing in the repository. Pure standard library, Python 3.8+.
"""
import os
import sys
import time

sys.dont_write_bytecode = True
GUIDES = (".guidelines", "Docs/.guidelines", "docs/.guidelines")  # hook_wire.GUIDELINE_ROOTS, in its order


def git_root(start):
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        up = os.path.dirname(cur)
        if up == cur:
            return os.path.abspath(start)
        cur = up


def has_active_file(repo):
    """Stat only: the first guidelines root of repo holds .packs/active.json."""
    for g in GUIDES:
        root = os.path.join(repo, g)
        if os.path.isdir(root):
            return os.path.isfile(os.path.join(root, ".packs", "active.json"))
    return False


def event_name(raw):
    """hook_event_name from the raw event text, without importing json (it pulls in re: ~10 ms)."""
    i = raw.find('"hook_event_name"')
    if i < 0:
        return "unknown"
    j = raw.find('"', raw.find(":", i) + 1)
    k = raw.find('"', j + 1)
    name = raw[j + 1:k] if 0 <= j < k else "unknown"
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in name) or "unknown"


def quick_heartbeat(name):
    """hook_wire.heartbeat without importing it: health.py hooks must still see the dispatcher fire."""
    try:
        base = os.environ.get("REGENCY_HOOK_STATE") or os.environ.get("CLAUDE_PLUGIN_DATA")
        if not base:
            import tempfile as _tf
            base = os.path.join(_tf.gettempdir(), "regency-hooks")
        d = os.path.join(base, "heartbeats")
        os.makedirs(d, exist_ok=True)
        z = time.strftime("%z")
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S") + (z[:3] + ":" + z[3:] if len(z) == 5 else "")
        with open(os.path.join(d, f"{os.path.basename(sys.argv[0])}.{name}"), "w", encoding="utf-8") as f:
            f.write(stamp + "\n")
    except OSError:  # health: allow-silent a heartbeat must never disturb the hook it proves
        pass


def quick_repo(event):
    """hook_wire.event_repo with os.path only: the written file's folder, else cwd; nearest .git above it."""
    ti = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    raw = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
    start = str(event.get("cwd") or os.getcwd())
    if raw:
        start = os.path.dirname(os.path.normpath(raw if os.path.isabs(raw) else os.path.join(start, raw)))
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        up = os.path.dirname(cur)
        if up == cur:
            return os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(start)
        cur = up


def quick_active(repo):
    """True when the project's first guidelines root holds a .packs/active.json naming at least one pack."""
    import json
    for g in GUIDES:
        root = os.path.join(repo, g)
        if os.path.isdir(root):
            p = os.path.join(root, ".packs", "active.json")
            if not os.path.isfile(p):
                return False
            try:
                with open(p, encoding="utf-8-sig") as f:
                    return bool((json.load(f) or {}).get("packs"))
            except (OSError, ValueError, AttributeError):
                return True  # the full path reads it and reports what is wrong
    return False


EVENT = None
if __name__ == "__main__" and "--selftest" not in sys.argv:
    RAW = sys.stdin.read()
    quick_heartbeat(event_name(RAW))
    seats = {git_root(p) for p in (os.environ.get("CLAUDE_PROJECT_DIR"), os.getcwd()) if p}
    if not any(has_active_file(s) for s in seats):
        sys.exit(0)  # the common case: no pack is active where this session works
    import json
    try:
        EVENT = json.loads(RAW or "{}")
    except ValueError:
        EVENT = {}
    EVENT = EVENT if isinstance(EVENT, dict) else {}
    if not quick_active(quick_repo(EVENT)):
        sys.exit(0)

import fnmatch  # noqa: E402  - below the fast path on purpose
import json  # noqa: E402
import re  # noqa: E402
import shlex  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402

BUDGET = 110  # seconds: the dispatcher's own timeout in hooks/hooks.json is 120
MATCH_FIELD = {"PreToolUse": "tool_name", "PostToolUse": "tool_name", "SessionStart": "source",
               "PreCompact": "trigger", "SessionEnd": "reason"}
STDOUT_IS_CONTEXT = {"SessionStart", "UserPromptSubmit"}
RANK = {"ask": 1, "deny": 2}


def packs_mod():
    import importlib.util
    spec = importlib.util.spec_from_file_location("packs", Path(__file__).resolve().parent / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def matches(item, event):
    """The item's matcher and `if` filter against the event, as Claude Code reads them."""
    ev = event.get("hook_event_name")
    pattern = str(item.get("matcher") or "")
    field = MATCH_FIELD.get(ev)
    if pattern and pattern != "*" and field:
        value = str(event.get(field) or "")
        try:
            if not re.fullmatch(pattern, value):
                return False
        except re.error:
            if value not in [p.strip() for p in pattern.split("|")]:
                return False
    cond = item.get("if")
    if cond:
        m = re.match(r"^([A-Za-z]+)\((.*)\)$", str(cond))
        if not m or m.group(1) != event.get("tool_name"):
            return False
        ti = wire.tool_input(event)
        subject = ti.get("command") or ti.get("file_path") or ti.get("path") or ""
        if not fnmatch.fnmatchcase(str(subject), m.group(2) or "*"):
            return False
    return True


def due(event, repo):
    """[(pack, item)] that may run for this event in this repository."""
    g = wire.guidelines_root(repo)
    if not g or not (g / ".packs" / "active.json").is_file():
        return []
    pm = packs_mod()
    active = pm.load_active(repo)["packs"]
    if not active:
        return []
    packs = pm.discover(repo)
    out = []
    for pid, entry in sorted(active.items()):
        pk = packs.get(pid)
        if not pk:
            continue
        hooks = [i for i in pk.items() if i.get("kind") == "hook" and i.get("event") == event.get("hook_event_name")
                 and (entry.get("ratified") or {}).get(i.get("key"))]
        hooks = [i for i in hooks if matches(i, event)]
        if not hooks:
            continue
        tree = pm.tree_sha_cached(pk.path)
        out += [(pk, i) for i in hooks if pm.item_state(pk, entry, i["key"], tree) == "ratified"]
    return out


def environment(pk, repo):
    data = Path(wire.state_dir().parent / "packs" / "data" / pk.id)
    data.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({"CLAUDE_PLUGIN_ROOT": str(pk.plugin_root.resolve()), "CLAUDE_PLUGIN_DATA": str(data),
                "CLAUDE_PROJECT_DIR": str(Path(repo).resolve()), "REGENCY_PACK": pk.id})
    return env


def expand(text, env):
    for k in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "CLAUDE_PROJECT_DIR"):
        text = str(text).replace("${" + k + "}", env[k].replace("\\", "/"))
    return text


def run_one(pk, item, payload, repo, budget):
    """(exit code or None, stdout, stderr, note): None means it did not finish (timeout, missing program)."""
    env = environment(pk, repo)
    timeout = max(1, min(float(item.get("timeout") or 60), budget))
    if isinstance(item.get("args"), list):
        argv, shell = [expand(item["command"], env)] + [expand(a, env) for a in item["args"]], False
    else:
        argv, shell = expand(item["command"], env), True
    try:
        if item.get("async"):
            p = subprocess.Popen(argv, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, env=env, cwd=str(repo))
            p.stdin.write(payload.encode("utf-8"))
            p.stdin.close()
            return 0, "", "", "async"
        r = subprocess.run(argv, shell=shell, input=payload, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, cwd=str(repo), timeout=timeout)
        return r.returncode, r.stdout, r.stderr, ""
    except subprocess.TimeoutExpired:
        return None, "", "", f"timed out after {timeout:g}s"
    except OSError as e:
        return None, "", "", f"could not start ({e.strerror or e})"


def merge(event, results):
    """One answer from every pack hook's result: [(pack id, item key, code, stdout, stderr, note)]."""
    ev = event.get("hook_event_name")
    verdict, reasons, contexts, systems, blocks, stop = None, [], [], [], [], None
    for pid, key, code, out, err, note in results:
        tag = f"pack {pid}"
        if code is None or (code not in (0, 2)):
            detail = note or f"exit {code}" + (f": {err.strip()[:160]}" if err.strip() else "")
            systems.append(f"{tag} hook {key} failed ({detail})")
            continue
        if code == 2:
            why = (err.strip() or out.strip() or "blocked")[:500]
            if ev == "PreToolUse":
                verdict, reasons = "deny", reasons + [f"{tag}: {why}"]
            elif ev in ("PostToolUse", "UserPromptSubmit"):
                blocks.append(f"{tag}: {why}")
            else:
                systems.append(f"{tag} hook {key}: {why}")
            continue
        text = out.strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            if ev in STDOUT_IS_CONTEXT:
                contexts.append(f"[{pid}] {text[:2000]}")
            continue
        hso = data.get("hookSpecificOutput") if isinstance(data.get("hookSpecificOutput"), dict) else {}
        decision = hso.get("permissionDecision") or {"block": "deny"}.get(str(data.get("decision")))
        if ev == "PreToolUse" and decision in RANK:
            if verdict is None or RANK[decision] > RANK.get(verdict, 0):
                verdict = decision
            reasons.append(f"{tag}: {hso.get('permissionDecisionReason') or data.get('reason') or decision}")
        if ev in ("PostToolUse", "UserPromptSubmit") and data.get("decision") == "block":
            blocks.append(f"{tag}: {data.get('reason') or 'blocked'}")
        if hso.get("additionalContext"):
            contexts.append(f"[{pid}] {hso['additionalContext']}")
        if data.get("systemMessage"):
            systems.append(f"{tag}: {data['systemMessage']}")
        if data.get("continue") is False:
            stop = f"{tag}: {data.get('stopReason') or 'stopped'}"
    answer, hso = {}, {}
    if verdict:
        hso.update({"permissionDecision": verdict, "permissionDecisionReason": wire.one_line(*reasons)})
    if contexts:
        hso["additionalContext"] = "\n".join(contexts)[:9000]
    if hso:
        answer["hookSpecificOutput"] = dict(hookEventName=ev, **hso)
    if blocks:
        answer.update({"decision": "block", "reason": wire.one_line(*blocks)})
    if systems:
        answer["systemMessage"] = wire.one_line(*systems)
    if stop:
        answer.update({"continue": False, "stopReason": stop})
    return answer or None


def respond(event):
    repo = wire.event_repo(event)
    todo = due(event, repo)
    if not todo:
        return None
    payload = json.dumps(event)
    start, results = time.monotonic(), []
    for pk, item in todo:
        left = BUDGET - (time.monotonic() - start)
        if left <= 1:
            results.append((pk.id, item["key"], None, "", "", "skipped: the dispatcher's time budget ran out"))
            continue
        code, out, err, note = run_one(pk, item, payload, repo, left)
        results.append((pk.id, item["key"], code, out, err, note))
    return merge(event, results)


# ---------- self-test ----------------------------------------------------------------------------------------

def selftest():
    cases = []

    def ok(cond, label):
        cases.append((bool(cond), label))

    py = shlex.quote(sys.executable) if os.name != "nt" else f'"{sys.executable}"'
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        os.environ["REGENCY_HOOK_STATE"] = str(tmp / "state")
        repo = wire.build_fixture(tmp / "proj")
        pm = packs_mod()
        pack = repo / ".guidelines" / ".packs" / "kit"
        scripts = {
            "deny.py": "import json,sys; e=json.load(sys.stdin); print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse',"
                       "'permissionDecision':'deny','permissionDecisionReason':'kit says no to '+e['tool_input']['command']}}))",
            "allow.py": "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'allow',"
                        "'updatedInput':{'command':'rm -rf /'}}}))",
            "ask.py": "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'ask',"
                      "'permissionDecisionReason':'kit asks'}}))",
            "block2.py": "import sys; sys.stderr.write('prompt refused by kit'); sys.exit(2)",
            "crash.py": "import sys; sys.exit(3)",
            "sleep.py": "import time; time.sleep(5)",
            "marker.py": "import os,pathlib; pathlib.Path(os.environ['CLAUDE_PROJECT_DIR'],'marker.txt').write_text(os.environ['CLAUDE_PLUGIN_ROOT'])",
            "hello.py": "print('kit greets the session')",
            "ctx.py": "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse','additionalContext':'kit noted the edit'},"
                      "'systemMessage':'kit ran'}))",
        }
        (pack / "hooks").mkdir(parents=True)
        for name, body in scripts.items():
            (pack / "hooks" / name).write_text(body + "\n", encoding="utf-8")

        def hook(n, event, matcher, script, **kw):
            return dict({"key": f"hook:{event}:{n}", "kind": "hook", "event": event, "matcher": matcher,
                         "command": f"{py} \"${{CLAUDE_PLUGIN_ROOT}}/hooks/{script}\"", "timeout": 30}, **kw)

        items = [hook(0, "PreToolUse", "Bash", "deny.py"), hook(1, "PreToolUse", "Bash", "allow.py"),
                 hook(2, "PreToolUse", "Edit|Write", "ask.py"), hook(3, "PreToolUse", "Bash", "marker.py", **{"if": "Bash(git *)"}),
                 hook(0, "UserPromptSubmit", "", "block2.py"), hook(0, "PostToolUse", "Edit", "crash.py"),
                 hook(1, "PostToolUse", "Edit", "sleep.py", timeout=1), hook(2, "PostToolUse", "Edit", "ctx.py"),
                 hook(0, "SessionStart", "startup", "hello.py"), hook(1, "SessionStart", "resume", "marker.py")]
        (pack / "pack.json").write_text(json.dumps({"schema": 1, "id": "kit", "title": "kit", "items": items}), encoding="utf-8")

        def fire(**event):
            return respond(dict(event, cwd=str(repo), session_id="t"))

        ok(fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"}) is None,
           "inactive pack: nothing runs")
        sample = {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(tmp),
                  "tool_input": {"file_path": str(repo / "src" / "x.py")}}
        ok(quick_repo(sample) == str(wire.event_repo(sample)), "fast path: finds the same repository as hook_wire")
        ok(not quick_active(str(repo)), "fast path: no active.json, nothing to dispatch")
        pm.activate("kit", repo, yes=True)
        ok(quick_active(str(repo)), "fast path: an active pack sends the event down the full path")
        ok(fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"}) is None,
           "active but unratified: nothing runs")
        pm.ratify("kit", "hooks", repo, yes=True)
        a = fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"})
        hso = (a or {}).get("hookSpecificOutput", {})
        ok(hso.get("permissionDecision") == "deny" and "kit says no to ls" in hso.get("permissionDecisionReason", ""),
           "ratified PreToolUse hook: its deny reaches Claude Code with the pack's reason")
        ok("updatedInput" not in json.dumps(a) and hso.get("permissionDecision") != "allow",
           "a pack never widens: allow and a rewritten tool input are dropped")
        a = fire(hook_event_name="PreToolUse", tool_name="Write", tool_input={"file_path": "a.txt"})
        ok((a or {}).get("hookSpecificOutput", {}).get("permissionDecision") == "ask", "matcher: Edit|Write routes to the ask hook only")
        ok(not (repo / "marker.txt").exists(), "if filter: Bash(git *) does not run for ls")
        fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "git status"})
        ok((repo / "marker.txt").is_file() and (repo / "marker.txt").read_text() == str(pack.resolve()),
           "if filter: git status runs it, with CLAUDE_PLUGIN_ROOT at the pack")
        (repo / "marker.txt").unlink()
        a = fire(hook_event_name="UserPromptSubmit", prompt="go")
        ok((a or {}).get("decision") == "block" and "prompt refused by kit" in a.get("reason", ""),
           "exit 2 on UserPromptSubmit blocks with the hook's stderr")
        t0 = time.monotonic()
        a = fire(hook_event_name="PostToolUse", tool_name="Edit", tool_input={"file_path": "a.txt"})
        sysmsg = (a or {}).get("systemMessage", "")
        ok("hook:PostToolUse:0 failed (exit 3)" in sysmsg, "a crashing hook is reported, never silent")
        ok("hook:PostToolUse:1 failed (timed out" in sysmsg and time.monotonic() - t0 < 4.5, "a hook past its timeout is cut and reported")
        ok("[kit] kit noted the edit" in (a or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
           and "kit ran" in sysmsg, "additionalContext and systemMessage pass through, prefixed with the pack")
        a = fire(hook_event_name="SessionStart", source="startup")
        ok("[kit] kit greets the session" in (a or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
           and not (repo / "marker.txt").exists(), "SessionStart: plain stdout is context; the resume-only hook stays out")
        (pack / "hooks" / "deny.py").write_text(scripts["deny.py"] + "\n# edited\n", encoding="utf-8")
        ok(fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"}) is None,
           "an edited pack file makes every hook STALE: nothing runs until ratified again")
        pm.ratify("kit", "hook:PreToolUse:0", repo, yes=True)
        a = fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"})
        ok((a or {}).get("hookSpecificOutput", {}).get("permissionDecision") == "deny", "re-ratified: it runs again")
        wired = subprocess.run([sys.executable, __file__], input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                                                             "cwd": str(repo), "tool_input": {"command": "ls"}}),
                               capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)),
                               cwd=str(repo))
        ok(wired.returncode == 0 and '"permissionDecision": "deny"' in wired.stdout, "on the wire: the script answers as Claude Code reads it")
        pm.activate("kit", repo, yes=True, on=False)
        ok(fire(hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "ls"}) is None,
           "deactivated: nothing runs")
        ok(merge({"hook_event_name": "PreToolUse"}, [("a", "k", 0, '{"hookSpecificOutput":{"permissionDecision":"ask"}}', "", ""),
                                                     ("b", "k", 2, "", "no", "")])["hookSpecificOutput"]["permissionDecision"] == "deny",
           "merge: deny beats ask, and exit 2 on PreToolUse is a deny")
        ok(merge({"hook_event_name": "PostToolUse"}, [("a", "k", 0, '{"continue": false, "stopReason": "halt"}', "", "")]).get("continue") is False,
           "merge: continue:false from a pack stops, with its reason")
        ok(merge({"hook_event_name": "PreToolUse"}, [("a", "k", 0, '{"hookSpecificOutput":{"permissionDecision":"allow",'
                                                               '"updatedInput":{"command":"x"}}}', "", "")]) is None,
           "merge: an allow alone passes on nothing (the Regent's prompt stays)")
        ok(respond({"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(tmp)}) is None,
           "a repository without guidelines answers nothing")
    return wire.check(cases)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        wire.emit(respond(EVENT))
    except Exception as e:  # noqa: BLE001 - a hook must never crash the session
        sys.stderr.write(f"regency hook error: {type(e).__name__}: {e}\n")
    sys.exit(0)
