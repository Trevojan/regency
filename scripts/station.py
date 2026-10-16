#!/usr/bin/env python3
"""station.py - mise-en-place for a regency pass: is the station prepped before the first ticket?

Two layers, one script (the essay "Mise-en-place in Regency"):
  discipline  regency's own prep: a ledger entry for the unit, lineage that resolves, no STALE slice
  instrument  mise (mise.jdx.dev): a pinned toolchain, a config the Regent trusted, the gate as tasks

mise is OPTIONAL (convention F5): without it every mise item reports SKIP, the regency items still
run, and the pass declares its gate parts `manual`. regency itself never requires mise.

Commands
  check    [--unit ID] [--json]   the station gate, one slice line per item; exit 1 on a FAIL. Read-only.
  gate     [--task NAME] [--log FILE] [--timeout S]
                                  the mechanical gate through mise: every dependency of the gate task
                                  runs, one verdict per check, failures carry their evidence;
                                  exit 1 red, 2 cannot run, 3 refused (untrusted station)
  scaffold [--write]              propose a mise.toml from the repository's stack; --write only when
                                  no mise config exists (never overwrites)
  line                            the station as one slice line (for a resume slice)
  --selftest                      planted defects against a stub mise; needs no real mise

Options for every command: --repo DIR (default: nearest .git above the current directory).

Rules it enforces
  - Trust is the Regent's ratification. An agent never runs `mise trust`. `mise run` trusts a config by
    itself, so `gate` reads `mise trust --show` first and refuses an untrusted station.
  - An agent never installs a toolchain (library/conventions.md §5). Every call runs with
    MISE_TASK_RUN_AUTO_INSTALL=false and without MISE_YES; a missing tool is a FAIL for the Regent.
  - A floating pin (latest, stable, lts, nightly, system) is a WARN: QA evidence must be reproducible.

Environment: REGENCY_MISE = the mise executable to use (a path, a .py stub, or `none` for absent).
Pure standard library, Python 3.8+.
"""
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

CONFIG_NAMES = ("mise.toml", ".mise.toml", "mise/config.toml", ".mise/config.toml",
                ".config/mise.toml", ".config/mise/config.toml")
LOCK_NAMES = ("mise.lock", ".mise.lock", ".config/mise.lock", "mise/mise.lock", ".mise/mise.lock")
FLOATING = ("latest", "stable", "lts", "nightly", "beta", "system")
GATE_TASK = "gate"
WALK_SKIP = wire.SKIP_PARTS | {"bin", "obj", "target", "dist", "build", ".venv", "venv"}
TAIL = 12        # evidence lines kept per failed check
LEVELS = ("FAIL", "WARN", "MANUAL", "SKIP", "OK")


# ---------- mise, read through one door -------------------------------------------------------

def mise_cmd():
    """The command prefix that runs mise, or None when mise is absent (an optional layer)."""
    raw = os.environ.get("REGENCY_MISE", "").strip()
    if raw.lower() == "none":
        return None
    if raw:
        return [sys.executable, raw] if raw.endswith(".py") else [raw]
    found = shutil.which("mise")
    return [found] if found else None


def mise_env():
    """The environment every mise call gets: no auto-install, no blanket yes."""
    env = dict(os.environ)
    env["MISE_TASK_RUN_AUTO_INSTALL"] = "false"
    env.pop("MISE_YES", None)
    return env


def call(mise, args, repo, timeout=60):
    """(exit code, stdout, stderr) of one mise call in the repository; never raises."""
    try:
        r = subprocess.run([*mise, *args], cwd=str(repo), env=mise_env(), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except OSError as e:
        return 127, "", f"{type(e).__name__}: {e}"


def first_line(*texts):
    for t in texts:
        for line in (t or "").splitlines():
            if line.strip():
                return line.strip()[:200]
    return ""


UNTRUSTED = "not trusted"  # mise refuses to parse an untrusted config that uses templates or [env]


def blocked(text):
    return UNTRUSTED in (text or "")


def norm(path):
    return os.path.normcase(os.path.realpath(str(path)))


def inside(path, repo):
    if not path:
        return False
    p, r = norm(path), norm(repo)
    return p == r or p.startswith(r + os.sep)


def config_file(repo):
    return next((repo / n for n in CONFIG_NAMES if (repo / n).is_file()), None)


def lock_file(repo):
    return next((repo / n for n in LOCK_NAMES if (repo / n).is_file()), None)


def mise_version(mise, repo):
    code, out, err = call(mise, ["--version"], repo)
    return first_line(out).split(" ")[0] if code == 0 else None


def trust_state(mise, repo):
    """'trusted', 'untrusted', 'ignored' or None (unknown) for the repository's config, plus evidence."""
    code, out, err = call(mise, ["trust", "--show"], repo)
    if code != 0:
        return None, first_line(err, out)
    wanted = {norm(repo)} | {norm(repo / n) for n in CONFIG_NAMES} | {norm(repo / d) for d in (".config", ".mise", "mise")}
    states = []
    for line in out.splitlines():
        path, sep, state = line.rpartition(": ")
        if sep and norm(path.strip()) in wanted:
            states.append(state.strip().lower())
    if not states:
        return None, first_line(out) or "no line for this repository"
    worst = next((s for s in ("untrusted", "ignored") if s in states), states[0])
    return worst, f"{len(states)} config line(s)"


def tool_rows(mise, repo):
    """[(tool, requested, installed)] for the tools this repository's config requests; None on error."""
    code, out, err = call(mise, ["ls", "--current", "--json"], repo)
    if code != 0:
        return None, err or out
    try:
        data = json.loads(out or "{}")
    except ValueError:
        return None, "mise ls --json did not parse"
    rows = []
    for tool, entries in (data.items() if isinstance(data, dict) else []):
        for e in entries if isinstance(entries, list) else [entries]:
            if isinstance(e, dict) and inside((e.get("source") or {}).get("path"), repo):
                rows.append((tool, str(e.get("requested_version") or e.get("version") or "?"), bool(e.get("installed"))))
    return rows, ""


def floating(requested):
    r = requested.lower()
    return r in FLOATING or r.startswith("lts") or r.startswith("ref:")


def task_table(mise, repo):
    """{name: task dict} from `mise tasks ls --json --hidden`; None on error."""
    code, out, err = call(mise, ["tasks", "ls", "--json", "--hidden"], repo)
    if code != 0:
        return None, err or out
    try:
        return {t["name"]: t for t in json.loads(out or "[]") if isinstance(t, dict) and t.get("name")}, ""
    except ValueError:
        return None, "mise tasks ls --json did not parse"


def dep_spec(dep):
    """A depends entry (string, list or table) as the argv after `mise run`."""
    if isinstance(dep, dict):
        return [str(dep.get("task", "?")), *[str(a) for a in dep.get("args", [])]]
    if isinstance(dep, list):
        return [str(a) for a in dep]
    return shlex.split(str(dep))


# ---------- check: the station gate (read-only) -----------------------------------------------

def check_station(repo, unit=None):
    """[(level, item, message)] for every station item, in reading order."""
    out = []
    add = lambda lvl, item, msg: out.append((lvl, item, msg))  # noqa: E731
    mise = mise_cmd()
    cfg = config_file(repo)

    # the instrument
    if not mise:
        add("SKIP", "mise", "mise not on PATH: optional layer; gate parts run by hand and are declared manual")
    else:
        add("OK", "mise", f"mise {mise_version(mise, repo) or '?'}")
    if mise and not cfg:
        add("WARN", "config", "no mise config: the station is undeclared (station.py scaffold proposes one)")
    elif mise:
        add("OK", "config", cfg.relative_to(repo).as_posix())
    if mise and cfg:
        state, why = trust_state(mise, repo)
        if state == "trusted":
            add("OK", "trust", "trusted")
        elif state is None:
            add("WARN", "trust", f"trust unknown ({why}); the Regent checks `mise trust --show`")
        else:
            add("FAIL", "trust", f"{state}: the Regent reviews {cfg.name} and runs `mise trust`; an agent never does")
        wait = "unreadable until the Regent trusts the config"
        rows, why = tool_rows(mise, repo)
        if rows is None and blocked(why):
            add("SKIP", "tools", wait)
        elif rows is None:
            add("FAIL", "tools", f"mise ls failed: {first_line(why)}")
        elif not rows:
            add("WARN", "tools", "no [tools] pinned: the toolchain is whatever the machine has")
        else:
            missing = [f"{t}@{v}" for t, v, ok in rows if not ok]
            loose = [f"{t}@{v}" for t, v, ok in rows if floating(v)]
            listed = ", ".join(f"{t}@{v}" for t, v, _ in rows)
            if missing:
                add("FAIL", "tools", f"not installed: {', '.join(missing)}; the Regent runs `mise install`")
            elif loose:
                add("WARN", "tools", f"floating pin: {', '.join(loose)}; pin a version so evidence reproduces")
            else:
                add("OK", "tools", listed)
            lock = lock_file(repo)
            add("OK" if lock else "WARN", "lock", lock.relative_to(repo).as_posix() if lock
                else "no mise.lock: versions resolve at install time (`mise lock` fixes them)")
        tasks, why = task_table(mise, repo)
        code, vout, verr = call(mise, ["tasks", "validate"], repo)
        if code == 0:
            add("OK", "tasks", "mise tasks validate")
        elif blocked(verr + vout):
            add("SKIP", "tasks", wait)
        else:
            add("FAIL", "tasks", f"mise tasks validate: {first_line(verr, vout)}")
        if tasks is None and blocked(why):
            add("SKIP", "gate-task", wait)
        elif tasks is None:
            add("FAIL", "gate-task", f"mise tasks ls failed: {first_line(why)}")
        elif GATE_TASK not in tasks:
            add("WARN", "gate-task", f"no '{GATE_TASK}' task: the gate runs by hand and the pass declares it manual")
        else:
            deps = [" ".join(dep_spec(d)) for d in tasks[GATE_TASK].get("depends") or []]
            add("OK", "gate-task", f"{GATE_TASK} -> {', '.join(deps) or 'its own run'}")
    elif not mise:
        for item in ("config", "trust", "tools", "gate-task"):
            add("SKIP", item, "mise absent")
    else:
        for item in ("trust", "tools", "gate-task"):
            add("SKIP", item, "no mise config")

    # the discipline
    vdir = wire.virtual_dir(repo)
    led = vdir / "ongoing.json" if vdir else None
    if not unit:
        add("SKIP", "ledger", "no --unit given")
    elif not led or not led.is_file():
        add("WARN", "ledger", "no work ledger in this project (.shortcuts/.virtual/ongoing.json)")
    else:
        try:
            items = json.loads(led.read_text(encoding="utf-8-sig")).get("items", [])
        except ValueError:
            items = None
        hit = None if items is None else (
            next((it for it in items if it.get("id") == unit), None)
            or next((it for it in items if unit.startswith(str(it.get("id")) + ".")), None))
        if items is None:
            add("FAIL", "ledger", "ongoing.json does not parse (vp.py ongoing)")
        elif hit and hit.get("state") == "blocked":
            add("WARN", "ledger", f"{hit['id']} is blocked by {hit.get('blocked_by', '?')}: team check 2 decides")
        elif hit:
            add("OK", "ledger", f"{hit['id']} is {hit.get('state', '?')}")
        else:
            add("FAIL", "ledger", f"{unit} has no ledger entry: prep lists it before the first ticket")
    lineage = HERE / "vp.py"
    if not lineage.is_file():
        add("SKIP", "lineage", "scripts/vp.py not beside station.py")
    else:
        r = subprocess.run([sys.executable, str(lineage), "check", "--from", str(repo)], cwd=str(repo),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if "no manifest found" in (r.stderr + r.stdout):
            add("SKIP", "lineage", "no virtual-path manifest (lineage not adopted)")
        elif r.returncode == 0:
            add("OK", "lineage", (r.stdout.strip().splitlines() or ["resolves"])[-1])
        else:
            add("FAIL", "lineage", f"{first_line(r.stdout)} (vp.py check)")
    g = wire.guidelines_root(repo)
    stale = 0
    if g:
        for p in g.rglob("*.md"):
            if not wire.SKIP_PARTS.intersection(p.relative_to(g).parts):
                stale += p.read_text(encoding="utf-8-sig", errors="replace").count(wire.STALE_MARK)
    if stale:
        add("WARN", "stale", f"{stale} STALE line(s): the Regent clears those inside the span before build (vp.py stale)")
    elif g:
        add("OK", "stale", "no STALE line")
    else:
        add("SKIP", "stale", "no guidelines root")
    add("MANUAL", "f0", "norm ratified, criteria challenged, oracle supplied: read them from the Pass Declaration "
                        "(team check 4, stages 2-3)")
    return out


def verdict(items):
    levels = {lvl for lvl, _, _ in items}
    return "red" if "FAIL" in levels else "amber" if "WARN" in levels else "green"


def cmd_check(repo, unit, as_json):
    items = check_station(repo, unit)
    v = verdict(items)
    if as_json:
        print(json.dumps({"repo": str(repo), "unit": unit, "verdict": v,
                          "items": [{"level": l, "item": i, "message": m} for l, i, m in items]}, ensure_ascii=False))
    else:
        for lvl, item, msg in items:
            print(f"{lvl:<6}  station.{item:<10} {msg}")
        counts = {l: sum(1 for x, _, _ in items if x == l) for l in ("FAIL", "WARN", "MANUAL")}
        print(f"\nstation: {v} ({counts['FAIL']} fail, {counts['WARN']} warn, {counts['MANUAL']} manual)")
    return 1 if v == "red" else 0


# ---------- gate: the mechanical gate through mise --------------------------------------------

def run_check(mise, repo, argv, timeout):
    """(label, exit code, seconds, evidence tail) for one `mise run`."""
    started = time.monotonic()
    code, out, err = call(mise, ["run", *argv], repo, timeout=timeout)
    tail = [l for l in (out + "\n" + err).splitlines() if l.strip()][-TAIL:]
    label = next((a for a in argv if not a.startswith("-")), "?")
    return label, code, time.monotonic() - started, tail


def cmd_gate(repo, task, log, timeout):
    mise = mise_cmd()
    if not mise:
        print("gate: mise not on PATH: run Rule A, Rule B, the tests and the manifest diff by hand; declare them manual")
        return 2
    if not config_file(repo):
        print("gate: no mise config in this repository: the gate runs by hand and is declared manual")
        return 2
    if log and Path(log).exists():
        print(f"gate: {log} exists; a gate log is an act and is never rewritten: name a new file")
        return 2
    state, why = trust_state(mise, repo)
    if state != "trusted":
        print(f"REFUSED  station.trust  {state or 'unknown'} ({why}): the Regent reviews the config and runs "
              "`mise trust`; `mise run` would trust it silently, so the gate does not start")
        return 3
    tasks, why = task_table(mise, repo)
    if tasks is None or task not in tasks:
        print(f"gate: no '{task}' task ({first_line(why) or 'not declared'}): the gate runs by hand and is declared manual")
        return 2
    spec = tasks[task]
    plan = [dep_spec(d) for d in spec.get("depends") or []]
    if spec.get("run") or spec.get("file"):
        plan.append(["--skip-deps", task])
    if not plan:
        print(f"gate: '{task}' has no depends and no run: nothing to check")
        return 2
    rows, _ = tool_rows(mise, repo)
    tools = ", ".join(f"{t}@{v}{'' if ok else ' (NOT INSTALLED)'}" for t, v, ok in rows or []) or "none pinned"
    lines = [f"gate log · task '{task}' · {repo.name} · {wire.now()}", f"mise {mise_version(mise, repo) or '?'} · toolchain {tools}", ""]
    failed = 0
    for argv in plan:
        label, code, secs, tail = run_check(mise, repo, argv, timeout)
        if code == 0:
            lines.append(f"PASS  gate.{label}  {secs:.1f}s")
        else:
            failed += 1
            lines.append(f"FAIL  gate.{label}  exit {code} · {secs:.1f}s")
            lines.extend(f"      | {l}" for l in tail)
    v = "red" if failed else "green"
    lines.append("")
    lines.append(f"gate: {v} ({len(plan) - failed}/{len(plan)} pass)"
                 + (" -> return this log to DV; QA and the human are not consumed" if failed else ""))
    text = "\n".join(lines)
    print(text)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(text + "\n", encoding="utf-8")
    return 1 if failed else 0


# ---------- scaffold: a proposed mise.toml from the stack -------------------------------------

def shallow_files(repo, depth=3):
    for base, dirs, files in os.walk(repo):
        rel = Path(base).relative_to(repo)
        dirs[:] = [d for d in dirs if d not in WALK_SKIP] if len(rel.parts) < depth else []
        for f in files:
            yield rel / f


def read(repo, rel):
    try:
        return (repo / rel).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def detect_stack(repo):
    """(tools, tests): {tool: pin} and [(task name, command, description)] read from the repository."""
    files = list(shallow_files(repo))
    names = {f.name for f in files}
    tools, tests = {}, []
    projects = [f for f in files if f.suffix in (".csproj", ".fsproj", ".sln", ".slnx")]
    if projects or "global.json" in names:
        pin = None
        if (repo / "global.json").is_file():
            try:
                pin = json.loads(read(repo, "global.json")).get("sdk", {}).get("version")
            except ValueError:
                pin = None
        majors = [int(m) for f in projects for m in re.findall(r"<TargetFrameworks?>[^<]*?net(\d+)\.", read(repo, f))]
        tools["dotnet"] = pin or (str(max(majors)) if majors else "latest")
        tests.append(("dotnet", "dotnet test", "Tests: the .NET suite passes"))
    if "Cargo.toml" in names:
        chan = re.search(r'channel\s*=\s*"([^"]+)"', read(repo, "rust-toolchain.toml"))
        plain = first_line(read(repo, "rust-toolchain"))
        tools["rust"] = chan.group(1) if chan else plain or "stable"
        tests.append(("rust", "cargo test", "Tests: the Rust suite passes"))
    py = [f for f in files if f.suffix == ".py" and len(f.parts) <= 2]
    if py or names & {"pyproject.toml", "setup.py", "requirements.txt"}:
        tools["python"] = first_line(read(repo, ".python-version")) or f"{sys.version_info[0]}.{sys.version_info[1]}"
        if (repo / "scripts" / "doctor.py").is_file() and (repo / ".claude-plugin" / "plugin.json").is_file():
            tests.append(("python", "python scripts/doctor.py", "Health: regency doctor, every self-test included"))
        elif names & {"pytest.ini", "conftest.py"} or (repo / "tests").is_dir() or "[tool.pytest" in read(repo, "pyproject.toml"):
            tests.append(("python", "python -m pytest", "Tests: the Python suite passes"))
    if "package.json" in names and (repo / "package.json").is_file():
        pin = first_line(read(repo, ".nvmrc"), read(repo, ".node-version")).lstrip("v")
        tools["node"] = pin or "lts"
        try:
            if json.loads(read(repo, "package.json")).get("scripts", {}).get("test"):
                tests.append(("node", "npm test", "Tests: the Node suite passes"))
        except ValueError:
            pass
    return tools, tests


def render_toml(repo, tools, tests):
    lines = [f"# The station for {repo.name}, proposed by regency scripts/station.py scaffold.",
             "# The Regent reviews it, then runs: mise trust, mise install, mise lock. An agent runs none of them.", ""]
    if tools:
        lines.append("[tools]")
        lines += [f'{t} = "{v}"' for t, v in tools.items()]
        lines.append("")
    gate = []
    for stack, command, description in tests:
        name = "test" if len(tests) == 1 else f"test-{stack}"
        gate.append(name)
        lines += [f"[tasks.{name}]", f'description = "{description}"', f'run = "{command}"', ""]
    if wire.virtual_dir(repo) and any(wire.virtual_dir(repo).glob("manifest*.json")):
        gate.append("lineage")
        lines += ["[tasks.lineage]", 'description = "Lineage: every norm slice resolves (vp.py check)"',
                  "run = 'python \"{{env.REGENCY_ROOT}}/scripts/vp.py\" check'", ""]
    lines += ["# Rule A, Rule B and the F3 manifest diff are this project's own checks",
              "# (library/team/references/vocabulary-map.md section 3). Wire each one, then add it to the gate:",
              '# [tasks.rule-a]        run = "..."', '# [tasks.rule-b]        run = "..."',
              '# [tasks.manifest-diff] run = "..."', "",
              f"[tasks.{GATE_TASK}]", 'description = "The mechanical gate: runs before the human (ORCHESTRATION section 13)"',
              "depends = [" + ", ".join(f'"{g}"' for g in gate) + "]", ""]
    return "\n".join(lines)


def cmd_scaffold(repo, write):
    tools, tests = detect_stack(repo)
    text = render_toml(repo, tools, tests)
    existing = config_file(repo)
    if not write:
        print(text)
        if existing:
            print(f"# note: {existing.relative_to(repo).as_posix()} already exists; compare, never overwrite")
        return 0
    if existing:
        print(f"scaffold: {existing.relative_to(repo).as_posix()} exists; scaffold never overwrites")
        return 1
    (repo / "mise.toml").write_text(text, encoding="utf-8")
    print(f"scaffold: wrote mise.toml ({len(tools)} tool(s), {len(tests)} test task(s)); "
          "next: the Regent reviews it and runs mise trust, mise install, mise lock")
    return 0


# ---------- line: the station as one slice ----------------------------------------------------

def station_line(repo):
    mise = mise_cmd()
    if not mise:
        return "station: mise absent (optional layer)"
    if not config_file(repo):
        return wire.one_line("station", f"mise {mise_version(mise, repo) or '?'}", "no mise config")
    state, _ = trust_state(mise, repo)
    rows, _ = tool_rows(mise, repo)
    rows = rows or []
    tasks, _ = task_table(mise, repo)
    gate = (tasks or {}).get(GATE_TASK)
    return wire.one_line("station", f"mise {mise_version(mise, repo) or '?'}", state or "trust unknown",
                         f"{len(rows)} tool(s), {sum(1 for _, _, ok in rows if not ok)} missing, "
                         f"{sum(1 for _, v, _ in rows if floating(v))} floating",
                         f"gate -> {len(gate.get('depends') or [])} check(s)" if gate else "no gate task")


# ---------- self-test ------------------------------------------------------------------------

STUB = r'''
import json, os, sys
args = sys.argv[1:]
with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"args": args, "auto": os.environ.get("MISE_TASK_RUN_AUTO_INSTALL"),
                        "yes": os.environ.get("MISE_YES")}) + "\n")
if args[:1] == ["--version"]:
    print("2026.10.9 linux-x64 (2026-10-13)"); sys.exit(0)
if args[:2] == ["trust", "--show"]:
    print(os.getcwd() + ": " + os.environ.get("STUB_TRUST", "trusted")); sys.exit(0)
if args[:1] == ["trust"]:
    sys.exit(0)
if os.environ.get("STUB_BLOCKED") and args[:1] in (["ls"], ["tasks"]):
    print("mise ERROR error parsing config file: mise.toml", file=sys.stderr)
    print("mise ERROR Config files in mise.toml are not trusted.", file=sys.stderr)
    sys.exit(1)
if args[:2] == ["ls", "--current"]:
    print(open(os.environ["STUB_TOOLS"], encoding="utf-8").read()); sys.exit(0)
if args[:2] == ["tasks", "ls"]:
    print(open(os.environ["STUB_TASKS"], encoding="utf-8").read()); sys.exit(0)
if args[:2] == ["tasks", "validate"]:
    sys.exit(int(os.environ.get("STUB_VALIDATE", "0")))
if args[:1] == ["run"]:
    name = [a for a in args[1:] if not a.startswith("-")][0]
    code = int(os.environ.get("STUB_RUN_" + name.replace("-", "_").upper(), "0"))
    print("[" + name + "] ran")
    if code:
        print("[" + name + "] ERROR task failed", file=sys.stderr)
    sys.exit(code)
sys.exit(9)
'''


def captured(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*a)
    return code, buf.getvalue()


def selftest():
    keep = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            root = wire.build_fixture(tmp / "proj")
            stub, log = tmp / "stub_mise.py", tmp / "calls.jsonl"
            stub.write_text(STUB, encoding="utf-8")
            tools_ok, tools_bad, tasks_f = tmp / "tools_ok.json", tmp / "tools_bad.json", tmp / "tasks.json"
            src = {"type": "mise.toml", "path": str(root / "mise.toml")}
            tools_ok.write_text(json.dumps({"python": [{"version": "3.13.8", "requested_version": "3.13",
                                                        "installed": True, "source": src}]}), encoding="utf-8")
            tools_bad.write_text(json.dumps({"python": [{"version": "3.13", "requested_version": "3.13", "installed": False, "source": src}],
                                             "node": [{"version": "24", "requested_version": "latest", "installed": True, "source": src}],
                                             "jq": [{"version": "1.7", "requested_version": "1.7", "installed": False,
                                                     "source": {"type": "mise.toml", "path": str(tmp / "global.toml")}}]}),
                                 encoding="utf-8")
            tasks_f.write_text(json.dumps([{"name": "rule-a", "depends": [], "run": ["x"]},
                                           {"name": "test", "depends": [], "run": ["y"]},
                                           {"name": "gate", "depends": ["rule-a", "test"], "run": []}]), encoding="utf-8")
            os.environ.update({"STUB_LOG": str(log), "STUB_TOOLS": str(tools_ok), "STUB_TASKS": str(tasks_f),
                               "STUB_TRUST": "trusted", "MISE_YES": "1"})

            def levels(items):
                return {i: l for l, i, _ in items}

            def calls():
                return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []

            unit = "M01.D01.T01"
            os.environ["REGENCY_MISE"] = "none"
            absent = check_station(root, unit)
            cases = [(levels(absent).get("mise") == "SKIP" and verdict(absent) == "green", "mise absent: SKIP, regency items still run, green")]
            cases.append((captured(cmd_gate, root, GATE_TASK, None, 30)[0] == 2,
                          "mise absent: gate cannot run (exit 2), declared manual"))

            os.environ["REGENCY_MISE"] = str(stub)
            nocfg = check_station(root, unit)
            cases.append((levels(nocfg).get("config") == "WARN" and levels(nocfg).get("trust") == "SKIP", "no mise config: WARN, mise items SKIP"))

            (root / "mise.toml").write_text('[tools]\npython = "3.13"\n', encoding="utf-8")
            (root / "mise.lock").write_text("", encoding="utf-8")
            green = check_station(root, unit)
            cases.append((verdict(green) == "green" and captured(cmd_check, root, unit, False)[0] == 0,
                          "prepped station: green, exit 0"))
            cases.append((levels(green).get("gate-task") == "OK" and levels(green).get("lineage") == "OK", "gate task and lineage read"))
            cases.append((levels(check_station(root, "M02.D01.T03")).get("ledger") == "OK", "unit covered by its module's ledger item"))
            cases.append((levels(check_station(root, "M09.D01.T01")).get("ledger") == "FAIL", "unit with no ledger entry: FAIL"))
            cases.append((levels(check_station(root, "M01.D02.T01")).get("ledger") == "WARN", "blocked unit: WARN, team check 2 decides"))
            cases.append((not any(c["args"][:1] == ["run"] or c["args"] == ["trust"] for c in calls()),
                          "check is read-only: no run, no trust"))

            os.environ["STUB_TRUST"] = "untrusted"
            cases.append((levels(check_station(root, unit)).get("trust") == "FAIL", "untrusted config: FAIL"))
            os.environ["STUB_BLOCKED"] = "1"
            held = check_station(root, unit)
            cases.append(([l for l, _, _ in held].count("FAIL") == 1 and levels(held).get("tools") == "SKIP"
                          and levels(held).get("gate-task") == "SKIP" and levels(held).get("tasks") == "SKIP",
                          "untrusted config mise cannot read: one FAIL (trust), the rest wait"))
            os.environ.pop("STUB_BLOCKED")
            log.write_text("", encoding="utf-8")
            code, text = captured(cmd_gate, root, GATE_TASK, None, 30)
            cases.append((code == 3 and "REFUSED" in text and not any(c["args"][:1] == ["run"] for c in calls()),
                          "gate refuses an untrusted station before any run (exit 3)"))
            os.environ["STUB_TRUST"] = "trusted"

            os.environ["STUB_TOOLS"] = str(tools_bad)
            bad = check_station(root, unit)
            msg = next(m for l, i, m in bad if i == "tools")
            cases.append((levels(bad).get("tools") == "FAIL" and "python@3.13" in msg and "jq" not in msg,
                          "missing tool: FAIL; tools from other configs ignored"))
            (root / "mise.toml").write_text('[tools]\nnode = "latest"\n', encoding="utf-8")
            tools_bad.write_text(json.dumps({"node": [{"version": "24", "requested_version": "latest", "installed": True, "source": src}]}),
                                 encoding="utf-8")
            cases.append((levels(check_station(root, unit)).get("tools") == "WARN", "floating pin: WARN"))
            os.environ["STUB_TOOLS"] = str(tools_ok)

            os.environ["STUB_VALIDATE"] = "1"
            cases.append((levels(check_station(root, unit)).get("tasks") == "FAIL", "invalid tasks: FAIL"))
            os.environ["STUB_VALIDATE"] = "0"

            log.write_text("", encoding="utf-8")
            os.environ["STUB_RUN_RULE_A"] = "1"
            code, text = captured(cmd_gate, root, GATE_TASK, None, 30)
            runs = [c for c in calls() if c["args"][:1] == ["run"]]
            cases.append((code == 1 and "FAIL  gate.rule-a" in text and "PASS  gate.test" in text and "| [rule-a] ERROR" in text,
                          "gate: one verdict per check, failure carries its evidence"))
            cases.append((len(runs) == 2 and all(c["auto"] == "false" and c["yes"] is None for c in runs),
                          "gate runs without auto-install and without MISE_YES"))
            os.environ.pop("STUB_RUN_RULE_A")
            glog = tmp / "GT-01.log"
            code, _ = captured(cmd_gate, root, GATE_TASK, str(glog), 30)
            cases.append((code == 0 and glog.is_file() and "gate: green (2/2 pass)" in glog.read_text(encoding="utf-8"),
                          "green gate writes its log"))
            cases.append((captured(cmd_gate, root, GATE_TASK, str(glog), 30)[0] == 2, "an existing gate log is never rewritten"))

            arch = root / ".guidelines/.decisions/ARCHITECTURE.md"
            arch.write_text(arch.read_text(encoding="utf-8") + "\n[warn'STALE' on='2026-10-13']\n", encoding="utf-8")
            cases.append((levels(check_station(root, unit)).get("stale") == "WARN", "STALE line: WARN"))
            (root / "src/Ledger.cs").unlink()
            cases.append((levels(check_station(root, unit)).get("lineage") == "FAIL", "broken lineage: FAIL"))

            line = station_line(root)
            cases.append(("\n" not in line and "trusted" in line and "gate -> 2 check(s)" in line, "station line: one slice"))

            (root / "App").mkdir()
            (root / "App/App.csproj").write_text("<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework>"
                                                 "</PropertyGroup></Project>", encoding="utf-8")
            (root / ".python-version").write_text("3.13\n", encoding="utf-8")
            (root / "tool.py").write_text("print(1)\n", encoding="utf-8")
            (root / "tests").mkdir()
            code, text = captured(cmd_scaffold, root, False)
            cases.append(('dotnet = "10"' in text and 'python = "3.13"' in text and '"test-dotnet"' in text and '"lineage"' in text,
                          "scaffold reads the stack: dotnet 10, python 3.13, tests, lineage"))
            cases.append((captured(cmd_scaffold, root, True)[0] == 1, "scaffold --write never overwrites"))
            (root / "mise.toml").unlink()
            code, _ = captured(cmd_scaffold, root, True)
            cases.append((code == 0 and "[tasks.gate]" in read(root, "mise.toml"), "scaffold --write creates mise.toml when absent"))
            return wire.check(cases)
    finally:
        os.environ.clear()
        os.environ.update(keep)


# ---------- entry ----------------------------------------------------------------------------

def main(argv):
    if "--selftest" in argv:
        return selftest()
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in ("check", "gate", "scaffold", "line"):
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    cmd, rest = argv[0], argv[1:]
    opts, flags, i = {}, set(), 0
    while i < len(rest):
        a = rest[i]
        if a in ("--repo", "--unit", "--task", "--log", "--timeout") and i + 1 < len(rest):
            opts[a[2:]] = rest[i + 1]
            i += 2
        else:
            flags.add(a)
            i += 1
    repo = Path(opts["repo"]).resolve() if opts.get("repo") else wire.repo_root(Path(os.getcwd()))
    if cmd == "check":
        return cmd_check(repo, opts.get("unit"), "--json" in flags)
    if cmd == "gate":
        return cmd_gate(repo, opts.get("task", GATE_TASK), opts.get("log"), int(opts.get("timeout", "1800")))
    if cmd == "scaffold":
        return cmd_scaffold(repo, "--write" in flags)
    print(station_line(repo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
