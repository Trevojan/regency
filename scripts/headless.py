#!/usr/bin/env python3
"""headless.py - the Regent's headless runner: one route from library/headless.json, plain text out.

Every route lives in library/headless.json; this script is its only consumer. A new route is a new entry
there, never a new script.

  script route    runs a regency script with no model (the cheapest rung: the answer is already code)
  command route   runs one /regency command through `claude -p` under a profile (read or work)
  prompt route    runs the Regent's own text through `claude -p` under a profile

Usage (from the project's directory; the regency root is found relative to this file)
  python scripts/headless.py                          list the routes, one line each
  python scripts/headless.py <route> [args...]        run it: text on stdout, the run's exit code
  python scripts/headless.py <route> ... --dry-run    print what would run; run nothing
  python scripts/headless.py <route> ... --no-plugin  do not pass --plugin-dir (regency already installed)
  python scripts/headless.py <route> ... -- <flags>   extra flags for claude -p, e.g. -- --max-budget-usd 2
  python scripts/headless.py --check                  the table resolves: scripts, commands, profiles, settings
  python scripts/headless.py --selftest               prove --check and the composer catch each planted defect

Material piped on stdin is appended to a model route's prompt. The prompt always travels on stdin and
the preamble in a temp file, so no free text passes through a shell or a .cmd shim.

Exit codes: the route's own; 2 usage, unknown route or broken table; 3 refused route.
Pure standard library, Python 3.8+. Writes nothing but one temp file per model run.
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "library" / "headless.json"
REGISTRY = ROOT / "library" / "registry.json"
MODES = {"default", "acceptEdits", "plan", "auto", "dontAsk"}
PLACEHOLDERS = {"root", "route", "profile", "profile_summary"}
ROUTE_ID = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SHIM_UNSAFE = re.compile(r'[%^&|<>!"\r\n]')  # cmd.exe would read these inside a .cmd shim's arguments
KINDS = ("script", "command", "prompt")


def load(path=TABLE):
    return json.loads(path.read_text(encoding="utf-8"))


def commands_in_registry(path=REGISTRY):
    reg = json.loads(path.read_text(encoding="utf-8"))
    out = set()
    for c in reg["commands"]:
        out.add(c["id"])
        out.update(f"{c['id']}:{s['id']}" for s in c.get("subs", []))
    return out


def kind(route):
    found = [k for k in KINDS if route.get(k)]
    return found[0] if len(found) == 1 else None


def problems(table, root=ROOT, known=None):
    """One line per defect in the table; empty when it resolves."""
    known = commands_in_registry() if known is None else known
    out = []
    profiles = table.get("profiles", {})
    for name, p in profiles.items():
        if p.get("mode") not in MODES:
            out.append(f"profile '{name}': mode {p.get('mode')!r} is not a permission mode")
        if p.get("settings"):
            s = root / p["settings"]
            try:
                if "autoMode" not in json.loads(s.read_text(encoding="utf-8")):
                    out.append(f"profile '{name}': {p['settings']} has no autoMode block")
            except (OSError, ValueError) as e:
                out.append(f"profile '{name}': settings {p['settings']} unreadable: {type(e).__name__}")
        for s in p.get("scripts", []):
            if not (root / "scripts" / s.split()[0]).is_file():
                out.append(f"profile '{name}': script {s.split()[0]} is not in scripts/")
    for line in table.get("preamble", []):
        for ph in re.findall(r"\{([a-z_]+)\}", line):
            if ph not in PLACEHOLDERS:
                out.append(f"preamble: unknown placeholder {{{ph}}}")
    seen = set()
    for r in table.get("routes", []) + table.get("refused", []):
        rid = r.get("id", "")
        if not ROUTE_ID.match(rid):
            out.append(f"route {rid!r}: id is not kebab-case")
        if rid in seen:
            out.append(f"route '{rid}': duplicate id")
        seen.add(rid)
    for r in table.get("routes", []):
        rid, k = r.get("id", "?"), kind(r)
        if k is None:
            out.append(f"route '{rid}': needs exactly one of script, command, prompt")
            continue
        if k == "script":
            if not (root / "scripts" / r["script"]).is_file():
                out.append(f"route '{rid}': scripts/{r['script']} does not exist")
            if r.get("profile"):
                out.append(f"route '{rid}': a script route runs no model and takes no profile")
            continue
        if k == "command" and r["command"] not in known:
            out.append(f"route '{rid}': /regency:{r['command']} is not in library/registry.json")
        if r.get("profile") not in profiles:
            out.append(f"route '{rid}': profile {r.get('profile')!r} is not declared")
    for r in table.get("refused", []):
        if r.get("command") and r["command"] not in known:
            out.append(f"refused '{r.get('id')}': /regency:{r['command']} is not in library/registry.json")
        if not str(r.get("reason", "")).strip():
            out.append(f"refused '{r.get('id')}': no reason (a silent refusal is worth nothing)")
    return out


def find(table, rid):
    for r in table["routes"]:
        if r["id"] == rid:
            return r, None
    for r in table.get("refused", []):
        if r["id"] == rid:
            return None, r
    return None, None


def allowed_tools(profile, root):
    rules = list(profile.get("tools", []))
    for c in profile.get("commands", []):
        rules += [f"Bash({c})", f"Bash({c} *)", f"PowerShell({c})", f"PowerShell({c} *)"]
    for s in profile.get("scripts", []):
        cmd = f"python {root.as_posix()}/scripts/{s}"
        rules += [f"Bash({cmd})", f"Bash({cmd} *)", f"PowerShell({cmd})", f"PowerShell({cmd} *)"]
    return rules


def compose(table, route, args, piped="", root=ROOT, claude="claude", plugin=True, extra=()):
    """(argv, stdin text, preamble text) for a route. Pure: no I/O."""
    args = list(args) or list(route.get("default", []))
    if kind(route) == "script":
        return [sys.executable, str(root / "scripts" / route["script"])] + route.get("args", []) + args, None, None
    name = route["profile"]
    profile = table["profiles"][name]
    text = " ".join(args)
    prompt = f"/regency:{route['command']} {text}".strip() if route.get("command") else text
    if piped.strip():
        prompt = f"{prompt}\n\n{piped.strip()}" if prompt else piped.strip()
    preamble = "\n".join(table.get("preamble", [])).format(
        root=root.as_posix(), route=route["id"], profile=name, profile_summary=profile.get("summary", ""))
    argv = [claude, "-p", "--output-format", "text", "--permission-mode", profile["mode"], "--add-dir", str(root)]
    if plugin:
        argv += ["--plugin-dir", str(root)]
    if profile.get("tools") or profile.get("commands") or profile.get("scripts"):
        argv += ["--allowedTools", ",".join(allowed_tools(profile, root))]
    if profile.get("prompts"):
        argv += ["--permission-prompts", profile["prompts"]]
    if profile.get("settings"):
        argv += ["--settings", str(root / profile["settings"])]
    return argv + list(extra), prompt, preamble


def shim_risk(argv):
    """Arguments a .cmd/.bat launcher would hand to cmd.exe's parser."""
    if not argv[0].lower().endswith((".cmd", ".bat")):
        return []
    return [a for a in argv[1:] if SHIM_UNSAFE.search(a)]


def listing(table):
    lines = []
    for r in table["routes"]:
        k = kind(r)
        how = "script, no model" if k == "script" else f"{k}, {r['profile']}"
        lines.append(f"{r['id']:<12} {how:<18} {r['summary']}" + (f"  {r['hint']}" if r.get("hint") else ""))
    for r in table.get("refused", []):
        lines.append(f"{r['id']:<12} {'refused':<18} {r['reason']}")
    return lines


def run(argv):
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    dry, plugin = "--dry-run" in argv, "--no-plugin" not in argv
    argv = [a for a in argv if a not in ("--dry-run", "--no-plugin")]
    table = load()
    bad = problems(table)
    if bad:
        print("headless table is broken (library/headless.json):", *(f"\n  - {b}" for b in bad))
        return 2
    if not argv:
        print("\n".join(listing(table)))
        return 0
    route, refused = find(table, argv[0])
    if refused:
        print(f"{refused['id']} · refused · {refused['reason']}")
        return 3
    if route is None:
        print(f"unknown route '{argv[0]}'; python scripts/headless.py lists them")
        return 2
    piped = "" if kind(route) == "script" or sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
    claude = shutil.which("claude") or "claude"
    cmd, prompt, preamble = compose(table, route, argv[1:], piped, ROOT, claude, plugin, extra)
    if kind(route) == "prompt" and not prompt:
        print(f"route '{route['id']}' needs text: {route.get('hint', '<text>')}")
        return 2
    env = dict(os.environ, PYTHONUTF8="1", MSYS_NO_PATHCONV="1")
    if prompt is None:
        if dry:
            print(subprocess.list2cmdline(cmd))
            return 0
        return subprocess.run(cmd, env=env).returncode
    risky = shim_risk(cmd)
    if risky:
        print(f"refused: {Path(cmd[0]).name} is a cmd.exe shim and these arguments would be reparsed by cmd.exe: "
              + " | ".join(risky))
        return 2
    with tempfile.NamedTemporaryFile("w", suffix=".md", prefix="regency-headless-", delete=False,
                                     encoding="utf-8") as f:
        f.write(preamble)
    cmd += ["--append-system-prompt-file", f.name]
    try:
        if dry:
            print(subprocess.list2cmdline(cmd))
            print(f"--- stdin ---\n{prompt}\n--- preamble ---\n{preamble}")
            return 0
        return subprocess.run(cmd, input=prompt, text=True, encoding="utf-8", env=env).returncode
    finally:
        os.unlink(f.name)


# ---------- self-test ------------------------------------------------------------------------

def selftest():
    table = load()
    known = commands_in_registry()
    misses, n = [], 0

    def expect(label, mutate):
        nonlocal n
        n += 1
        t = copy.deepcopy(table)
        mutate(t)
        if not problems(t, ROOT, known):
            misses.append(label)

    def route(t, rid):
        return next(r for r in t["routes"] if r["id"] == rid)

    if problems(table, ROOT, known):
        misses.append("the shipped table must be clean: " + " | ".join(problems(table, ROOT, known)))
    expect("missing script", lambda t: route(t, "doctor").update(script="nope.py"))
    expect("unknown command", lambda t: route(t, "measure").update(command="nope"))
    expect("unknown sub", lambda t: route(t, "status").update(command="team:nope"))
    expect("two kinds", lambda t: route(t, "doctor").update(command="proceed"))
    expect("no kind", lambda t: route(t, "doctor").pop("script"))
    expect("undeclared profile", lambda t: route(t, "proceed").update(profile="nope"))
    expect("profile on a script", lambda t: route(t, "doctor").update(profile="read"))
    expect("duplicate id", lambda t: t["routes"].append(dict(route(t, "doctor"))))
    expect("refused id reused", lambda t: t["refused"].append({"id": "doctor", "command": None, "reason": "x"}))
    expect("bad id", lambda t: route(t, "doctor").update(id="Doctor_1"))
    expect("bad mode", lambda t: t["profiles"]["read"].update(mode="yolo"))
    expect("missing settings", lambda t: t["profiles"]["work"].update(settings="library/nope.json"))
    expect("missing profile script", lambda t: t["profiles"]["read"]["scripts"].append("nope.py"))
    expect("silent refusal", lambda t: t["refused"][0].update(reason=" "))
    expect("unknown placeholder", lambda t: t["preamble"].append("{secret}"))

    def check(label, ok):
        nonlocal n
        n += 1
        if not ok:
            misses.append(label)

    root = Path("/r")
    argv, stdin, pre = compose(table, route(table, "measure"), [], "", root, "claude")
    check("read: dontAsk", argv[argv.index("--permission-mode") + 1] == "dontAsk")
    check("read: default argument", stdin == "/regency:measure-changes tree")
    check("read: script allowed", "Bash(python /r/scripts/vp.py *)" in argv[argv.index("--allowedTools") + 1])
    check("read: no settings", "--settings" not in argv)
    check("preamble filled", "/r/library/conventions.md" in pre and "Route: measure" in pre)
    argv, stdin, _ = compose(table, route(table, "do"), ["fix", "it"], "log line", root, "claude", False, ["--x"])
    check("work: auto + prompts none", argv[argv.index("--permission-mode") + 1] == "auto"
          and argv[argv.index("--permission-prompts") + 1] == "none")
    check("work: settings file", argv[argv.index("--settings") + 1] == str(root / "library" / "automode.json"))
    check("work: no plugin when asked", "--plugin-dir" not in argv and argv[-1] == "--x")
    check("piped material appended", stdin == "fix it\n\nlog line")
    argv, stdin, _ = compose(table, route(table, "ongoing"), [], "", root)
    check("script route: no model", stdin is None and argv[-1] == "ongoing" and "claude" not in argv)
    check("shim guard", shim_risk(["c.CMD", "a&b"]) == ["a&b"] and not shim_risk(["c.exe", "a&b"]))
    for m in misses:
        print("MISS", m)
    print(f"selftest: {n - len(misses)}/{n} planted defects detected")
    return 1 if misses else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--check" in argv:
        table = load()
        bad = problems(table)
        for b in bad:
            print("FAIL", b)
        refused = len(table.get("refused", []))
        print(f"headless: {len(table['routes'])} route(s), {refused} refused -> {'ok' if not bad else 'BROKEN'}")
        return 1 if bad else 0
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    return run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
