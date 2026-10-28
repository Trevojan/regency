#!/usr/bin/env python3
"""migrate.py - fit a project to the installed regency (library/migrations/README.md).

The engine behind /regency:update (skills/update/SKILL.md); /regency:normalise will share it. It touches only
what regency owns in a project: the scaffold files it wrote (library/migrations/scaffolds.json), the explicit
steps a version declares (steps.json) and the stamp. The project's own prose, its acts and .scope/ are input:
never rewritten.

  migrate.py gate   [--from DIR]          does the project's stamp agree with the installed regency? one line;
                                          exit 0 agree (or no guidelines), 1 behind or unstamped (run
                                          /regency:update), 2 ahead (update the plugin first)
  migrate.py plan   [--from DIR]          the numbered operations an update would run, and the plan id
  migrate.py apply  --yes PLAN [--from DIR]
                                          run that plan: the id must match a fresh plan, the tree must be a
                                          clean git repository (every step revertible); then stamp
  migrate.py check  [--from DIR]          the project fits: stamp agrees and no operation is pending
  migrate.py stamp  [--from DIR]          record the installed version and the files regency just wrote
                                          (run by /regency:init and /regency:ux-init right after scaffolding)
  migrate.py record [--check]             maintainers: file the current templates' fingerprints under the
                                          current version in history.json; --check fails when one is missing
  migrate.py --selftest                   plant a defect per rule; exit 1 if one goes unseen

The stamp is <guidelines>/.shortcuts/regency.json. Pure standard library, Python 3.8+.
"""
import datetime
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDELINE_PROBES = (".guidelines", "Docs/.guidelines", "docs/.guidelines")  # library/layouts.md §1
STAMP = ".shortcuts/regency.json"
KINDS = ("mkdir", "rename", "move", "delete", "rewrite", "create", "replace", "beside", "stamp")
UPDATE_PLUGIN = "claude plugin marketplace update regency, then claude plugin update regency@regency"


# ---------- versions, fingerprints, places ---------------------------------------------------------

def version_key(v):
    """'2.10' > '2.9': a.b compared as numbers (conventions §13)."""
    return tuple(int(x) for x in str(v).split("."))


def installed(root=ROOT):
    return json.loads((Path(root) / "library" / "registry.json").read_text(encoding="utf-8"))["version"]


def fingerprint(data):
    """First 12 hex of sha256 with line endings normalised: a CRLF checkout is the same file."""
    if isinstance(data, Path):
        data = data.read_bytes()
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:12]


def repo_root(start):
    start = Path(start).resolve()
    for p in [start] + list(start.parents):
        if (p / ".git").exists():
            return p
    return start


def guidelines_root(repo):
    for probe in GUIDELINE_PROBES:
        if (repo / probe).is_dir():
            return repo / probe
    return None


def load(root, name):
    return json.loads((Path(root) / "library" / "migrations" / name).read_text(encoding="utf-8"))


def read_stamp(g):
    p = g / STAMP
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except ValueError:
        return {"regency": None, "unreadable": True}


_acts = None


def act_kind(name):
    """The acts guard's own table (hook-acts-guard.py): an Order, a gate sheet, a ladder plan, an opinion or a
    dated handoff is never rewritten, so no operation may touch one."""
    global _acts
    if _acts is None:
        spec = importlib.util.spec_from_file_location("hook_acts_guard", Path(__file__).resolve().parent / "hook-acts-guard.py")
        _acts = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        spec.loader.exec_module(_acts)
    return _acts.act_kind(name)


def forbidden(rel):
    """Why an operation may not touch this guidelines-relative path, or None."""
    parts = Path(rel).parts
    if not parts or ".." in parts or Path(rel).is_absolute():
        return "outside the guidelines root"
    if ".scope" in parts:
        return ".scope/ is the Regent's raw material (read-only)"
    kind = act_kind(Path(rel).name)
    if kind:
        return f"an act ({kind[0] if isinstance(kind, tuple) else kind}) is never rewritten"
    return None


# ---------- the gate --------------------------------------------------------------------------------

def gate(start, root=ROOT):
    """(code, line): 0 agree or nothing to gate, 1 behind or unstamped, 2 ahead."""
    repo = repo_root(start)
    g = guidelines_root(repo)
    want = installed(root)
    if g is None:
        return 0, "no guidelines here: nothing to gate"
    stamp = read_stamp(g)
    if stamp is None:
        return 1, f"this project carries no regency stamp; regency {want} is installed: run /regency:update before going on"
    have = stamp.get("regency")
    if not have or stamp.get("unreadable") or not re.match(r"^\d+\.\d+$", str(have)):
        return 1, f"the regency stamp ({STAMP}) is unreadable: run /regency:update before going on"
    if version_key(have) < version_key(want):
        return 1, f"this project is on regency {have}; regency {want} is installed: run /regency:update before going on"
    if version_key(have) > version_key(want):
        return 2, (f"this project is on regency {have}, newer than the installed {want}: update the plugin before "
                   f"going on ({UPDATE_PLUGIN})")
    return 0, f"project and regency agree: {want}"


# ---------- the plan --------------------------------------------------------------------------------

def scaffold_files(root):
    """{scaffold: {template rel: (guidelines rel or None, policy, bytes)}} from scaffolds.json."""
    spec = load(root, "scaffolds.json")["scaffolds"]
    out = {}
    for name, s in spec.items():
        src = Path(root) / s["source"]
        files = {}
        for p in sorted(src.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            rel = p.relative_to(src).as_posix()
            mapped = s["prefix"] + rel[len(s["strip"]):] if rel.startswith(s["strip"]) else None
            files[rel] = (mapped, "seed" if rel in s["seed"] else "refresh", p.read_bytes())
        out[name] = {"present_if": s["present_if"], "files": files}
    return out


def known_prints(root):
    """{'<scaffold>/<template rel>': {fingerprint: [versions]}} from history.json: every template a version shipped."""
    out = {}
    for version, table in load(root, "history.json").get("versions", {}).items():
        for key, fp in table.items():
            out.setdefault(key, {}).setdefault(fp, []).append(version)
    return out


def guess_version(g, root):
    """For an unstamped project: the newest version whose templates match the most untouched files."""
    votes = {}
    for scaffold, s in scaffold_files(root).items():
        for rel, (mapped, policy, _) in s["files"].items():
            p = g / mapped if mapped else None
            if p and p.is_file():
                for version in known_prints(root).get(f"{scaffold}/{rel}", {}).get(fingerprint(p), []):
                    votes[version] = votes.get(version, 0) + 1
    return max(votes, key=lambda v: (votes[v], version_key(v))) if votes else None


def plan(start, root=ROOT):
    """{'id', 'from', 'to', 'guidelines', 'ops': [...], 'refused': [...], 'note'} for the project at start."""
    repo = repo_root(start)
    g = guidelines_root(repo)
    to = installed(root)
    out = {"id": None, "from": None, "to": to, "guidelines": None, "ops": [], "refused": [], "note": None}
    if g is None:
        out["note"] = "no guidelines here: /regency:init first"
        return out
    out["guidelines"] = g.relative_to(repo).as_posix()
    stamp = read_stamp(g) or {}
    have = stamp.get("regency") if re.match(r"^\d+\.\d+$", str(stamp.get("regency"))) else None
    out["from"] = have
    if have and version_key(have) > version_key(to):
        out["note"] = f"the project is on {have}, newer than {to}: update the plugin ({UPDATE_PLUGIN})"
        return out
    if not have:
        out["guess"] = guess_version(g, root)
    ops, refused = [], []

    def add(op):
        why = forbidden(op["path"]) or (forbidden(op["to"]) if op.get("to") else None)
        (refused if why else ops).append(dict(op, refused=why) if why else op)

    # 1. the explicit steps of every version after the stamp (all of them for an unstamped project)
    for step in load(root, "steps.json").get("steps", []):
        if have and version_key(step["to"]) <= version_key(have):
            continue
        if version_key(step["to"]) > version_key(to):
            continue
        for raw in step.get("ops", []):
            op = dict(raw, step=step["to"])
            kind = "rename" if op["op"] == "move" else op["op"]
            p = g / op["path"]
            if kind == "mkdir" and not p.exists():
                add(dict(op, op="mkdir", why=op.get("why", "")))
            elif kind == "rename" and p.exists() and not (g / op["to"]).exists():
                add(dict(op, op="rename", why=op.get("why", "")))
            elif kind == "delete" and p.is_file():
                add(dict(op, op="delete", why=op.get("why", "")))
            elif kind == "rewrite" and p.is_file():
                text = p.read_text(encoding="utf-8-sig")
                if any(old in text for old, _ in op["replace"]):
                    add(dict(op, op="rewrite", why=op.get("why", "")))
    # 2. the scaffold files regency owns
    prints = known_prints(root)
    stamped = stamp.get("files", {})
    for scaffold, s in scaffold_files(root).items():
        if not (g / s["present_if"]).is_dir():
            continue
        for rel, (mapped, policy, body) in s["files"].items():
            if mapped is None or policy == "seed":
                continue
            p, want = g / mapped, fingerprint(body)
            if not p.exists():
                if p.parent.is_dir():
                    add({"op": "create", "path": mapped, "source": f"{scaffold}/{rel}", "why": "new in this version"})
                continue
            have_fp = fingerprint(p)
            if have_fp == want:
                continue
            if have_fp == stamped.get(mapped) or have_fp in prints.get(f"{scaffold}/{rel}", {}):
                shipped = prints.get(f"{scaffold}/{rel}", {}).get(have_fp) or [stamp.get("regency") or "?"]
                was = max(shipped, key=lambda v: version_key(v) if v != "?" else (0,))
                add({"op": "replace", "path": mapped, "source": f"{scaffold}/{rel}", "why": f"untouched: regency's text up to {was}"})
            else:
                side = p.with_name(p.name + ".template")
                if side.is_file() and fingerprint(side) == want:
                    continue
                add({"op": "beside", "path": mapped + ".template", "source": f"{scaffold}/{rel}",
                     "why": "edited by the project: the new version goes beside it to merge by hand"})
    # 3. the stamp, last
    if ops or have != to:
        ops.append({"op": "stamp", "path": STAMP, "why": f"{have or 'unstamped'} -> {to}"})
    for i, op in enumerate(ops, 1):
        op["n"] = i
    out["ops"], out["refused"] = ops, refused
    body = json.dumps([{k: v for k, v in op.items() if k != "n"} for op in ops], sort_keys=True)
    out["id"] = "UPD-" + hashlib.sha256((to + body).encode("utf-8")).hexdigest()[:8] if ops else None
    return out


# ---------- apply, stamp, check ---------------------------------------------------------------------

def git_clean(repo):
    """(clean, why) — an update runs only where every step can be reverted."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True)
    except OSError:
        return False, "git is not available"
    if r.returncode != 0:
        return False, "not a git repository: an update must be revertible, so commit the project to git first"
    if r.stdout.strip():
        return False, f"the tree has uncommitted changes ({len(r.stdout.strip().splitlines())}): commit or stash them first"
    return True, None


def write_stamp(g, root, history=None):
    """Record the installed version and the fingerprints of the files regency owns that hold its current text."""
    old = read_stamp(g) or {}
    files = {}
    for scaffold, s in scaffold_files(root).items():
        if not (g / s["present_if"]).is_dir():
            continue
        for rel, (mapped, policy, body) in s["files"].items():
            p = g / mapped if mapped else None
            if p and p.is_file() and fingerprint(p) == fingerprint(body):
                files[mapped] = fingerprint(body)
    stamp = {"schema": 1, "regency": installed(root), "updated": datetime.date.today().isoformat(),
             "files": dict(sorted(files.items())), "history": list(old.get("history", []))}
    if history:
        stamp["history"].append(history)
    (g / STAMP).parent.mkdir(parents=True, exist_ok=True)
    (g / STAMP).write_text(json.dumps(stamp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return stamp


def apply(start, plan_id, root=ROOT):
    """(code, lines). Recomputes the plan; runs it only when the id matches and the tree is clean."""
    pl = plan(start, root)
    if pl["note"]:
        return 2, [pl["note"]]
    if not pl["ops"]:
        return 0, ["nothing to apply: the project already fits regency " + pl["to"]]
    if plan_id != pl["id"]:
        return 2, [f"plan {plan_id} is not the current plan ({pl['id']}): run plan again and approve that one"]
    repo = repo_root(start)
    clean, why = git_clean(repo)
    if not clean:
        return 2, [f"refused: {why}"]
    g = repo / pl["guidelines"]
    files = {f"{sc}/{rel}": body for sc, s in scaffold_files(root).items() for rel, (_, _, body) in s["files"].items()}
    lines = []
    for op in pl["ops"]:
        p = g / op["path"]
        if op["op"] == "mkdir":
            p.mkdir(parents=True, exist_ok=True)
        elif op["op"] == "rename":
            (g / op["to"]).parent.mkdir(parents=True, exist_ok=True)
            p.replace(g / op["to"])
        elif op["op"] == "delete":
            p.unlink()
        elif op["op"] == "rewrite":
            text = p.read_text(encoding="utf-8-sig")
            for old, new in op["replace"]:
                text = text.replace(old, new)
            p.write_text(text, encoding="utf-8")
        elif op["op"] in ("create", "replace", "beside"):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(files[op["source"]])
        elif op["op"] == "stamp":
            write_stamp(g, root, {"from": pl["from"], "to": pl["to"], "on": datetime.date.today().isoformat(),
                                  "plan": pl["id"], "ops": len(pl["ops"]) - 1})
        lines.append(f"done  {op['n']:>3}  {op['op']:<8} {op['path']}" + (f" -> {op['to']}" if op.get("to") else ""))
    return 0, lines


def check(start, root=ROOT):
    code, line = gate(start, root)
    pending = [op for op in plan(start, root)["ops"] if op["op"] != "stamp"]
    if code == 0 and not pending:
        return 0, line
    return 1, line + (f"; {len(pending)} operation(s) pending: run /regency:update" if pending else "")


# ---------- maintainers: the template history -------------------------------------------------------

def current_prints(root=ROOT):
    return {f"{sc}/{rel}": fingerprint(body)
            for sc, s in scaffold_files(root).items() for rel, (_, _, body) in s["files"].items()}


def record(root=ROOT, check_only=False):
    """(code, line). history.json keeps every template fingerprint a version shipped; nothing is ever removed."""
    path = Path(root) / "library" / "migrations" / "history.json"
    hist = json.loads(path.read_text(encoding="utf-8"))
    version, now = installed(root), current_prints(root)
    have = hist.setdefault("versions", {}).get(version, {})
    missing = sorted(k for k, fp in now.items() if have.get(k) != fp)
    if check_only:
        if missing:
            return 1, (f"history.json lacks {len(missing)} template fingerprint(s) of {version} ({missing[0]} ...): "
                       "run python scripts/migrate.py record")
        return 0, f"history.json holds the {len(now)} templates of {version}"
    hist["versions"][version] = dict(sorted(now.items()))
    hist["versions"] = dict(sorted(hist["versions"].items(), key=lambda kv: version_key(kv[0])))
    path.write_text(json.dumps(hist, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0, f"recorded {len(now)} template fingerprints under {version}"


# ---------- selftest --------------------------------------------------------------------------------

def selftest():
    cases = []

    def ok(cond, name):
        cases.append((bool(cond), name))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        reg = tmp / "regency"
        (reg / "library" / "migrations").mkdir(parents=True)
        tpl = reg / "library" / "templates" / "guidelines"
        for rel, text in {"README.md": "root readme\n", ".guidelines/.plan/README.md": "plan v2\n",
                          ".guidelines/.decisions/README.md": "decisions v2\n",
                          ".guidelines/.history/README.md": "attic v2\n",
                          ".guidelines/.shortcuts/README.md": "index\n"}.items():
            (tpl / rel).parent.mkdir(parents=True, exist_ok=True)
            (tpl / rel).write_text(text, encoding="utf-8")
        (reg / "library" / "migrations" / "scaffolds.json").write_text(json.dumps({"schema": 1, "scaffolds": {
            "guidelines": {"source": "library/templates/guidelines", "strip": ".guidelines/", "prefix": "",
                           "present_if": "", "seed": ["README.md", ".guidelines/.shortcuts/README.md"]}}}), encoding="utf-8")
        old_plan = fingerprint(b"plan v1\n")
        (reg / "library" / "migrations" / "history.json").write_text(json.dumps({"schema": 1, "versions": {
            "2.1": {"guidelines/.guidelines/.plan/README.md": old_plan}}}), encoding="utf-8")
        (reg / "library" / "migrations" / "steps.json").write_text(json.dumps({"schema": 1, "steps": [
            {"to": "2.5", "ops": [{"op": "rename", "path": ".plan/OLD_NAME.md", "to": ".plan/NEW_NAME.md", "why": "renamed"},
                                  {"op": "delete", "path": ".shortcuts/.virtual/fingerprints.json", "why": "moved to a cache"},
                                  {"op": "rewrite", "path": ".shortcuts/.virtual/ongoing.json",
                                   "replace": [["\"schema\": 1", "\"schema\": 2"]], "why": "ledger schema 2"},
                                  {"op": "delete", "path": ".orders/ORD-0001/ORD-0001.xml", "why": "planted: an act"},
                                  {"op": "delete", "path": ".scope/raw.md", "why": "planted: the Regent's material"}]},
            {"to": "3.0", "ops": [{"op": "mkdir", "path": ".future", "why": "beyond the installed version"}]}]}),
            encoding="utf-8")
        (reg / "library" / "registry.json").write_text('{"version": "2.10"}', encoding="utf-8")

        ok(version_key("2.10") > version_key("2.9"), "2.10 is newer than 2.9")

        proj = tmp / "proj"
        g = proj / ".guidelines"
        for rel, text in {".plan/README.md": "plan v1\n", ".plan/OLD_NAME.md": "x\n",
                          ".decisions/README.md": "our own decisions\n", ".shortcuts/README.md": "our index\n",
                          ".shortcuts/.virtual/fingerprints.json": "{}\n", ".shortcuts/.virtual/ongoing.json": "{\"schema\": 1}\n",
                          ".orders/ORD-0001/ORD-0001.xml": "<o/>\n", ".scope/raw.md": "raw\n"}.items():
            (g / rel).parent.mkdir(parents=True, exist_ok=True)
            (g / rel).write_text(text, encoding="utf-8")
        ok(gate(tmp / "nowhere", reg)[0] == 0, "no guidelines: nothing to gate")
        code, line = gate(proj, reg)
        ok(code == 1 and "no regency stamp" in line, f"unstamped: update first ({line})")

        pl = plan(proj, reg)
        kinds = [(op["op"], op["path"]) for op in pl["ops"]]
        ok(("rename", ".plan/OLD_NAME.md") in kinds, "a step renames")
        ok(("delete", ".shortcuts/.virtual/fingerprints.json") in kinds, "a step deletes")
        ok(("rewrite", ".shortcuts/.virtual/ongoing.json") in kinds, "a step rewrites")
        ok(("replace", ".plan/README.md") in kinds, "an untouched old template is replaced")
        ok(("beside", ".decisions/README.md.template") in kinds, "an edited file gets .template beside it")
        ok(not any(p.startswith(".shortcuts/README.md") for _, p in kinds), "a seed is never touched, nor given a .template")
        ok(not any(p == ".history/README.md" for _, p in kinds), "no file is created where its folder is absent")
        ok(not any(k == "mkdir" for k, _ in kinds), "a step beyond the installed version waits")
        ok(kinds[-1] == ("stamp", STAMP), "the stamp comes last")
        refused = {op["path"]: op["refused"] for op in pl["refused"]}
        ok("act" in (refused.get(".orders/ORD-0001/ORD-0001.xml") or ""), "an act is refused")
        ok(".scope" in (refused.get(".scope/raw.md") or ""), ".scope/ is refused")
        ok(pl["id"] and pl["id"] == plan(proj, reg)["id"], "the plan id is stable")

        code, lines = apply(proj, pl["id"], reg)
        ok(code == 2 and "not a git repository" in lines[0], f"no git, no apply ({lines[0][:60]})")
        if shutil.which("git"):
            def git(*a):
                return subprocess.run(["git", "-C", str(proj), "-c", "user.name=t", "-c", "user.email=t@t",
                                       "-c", "commit.gpgsign=false", *a], capture_output=True, text=True)
            git("init", "-q")
            git("add", "-A")
            git("commit", "-qm", "base")
            (g / ".plan" / "scratch.md").write_text("dirty\n", encoding="utf-8")
            code, lines = apply(proj, plan(proj, reg)["id"], reg)
            ok(code == 2 and "uncommitted" in lines[0], "a dirty tree is refused")
            (g / ".plan" / "scratch.md").unlink()
            ok(apply(proj, "UPD-00000000", reg)[0] == 2, "a stale plan id is refused")
            code, lines = apply(proj, pl["id"], reg)
            ok(code == 0 and len(lines) == len(pl["ops"]), f"the plan runs ({len(lines)} ops)")
            ok((g / ".plan" / "NEW_NAME.md").is_file() and not (g / ".plan" / "OLD_NAME.md").exists(), "renamed on disk")
            ok(not (g / ".shortcuts/.virtual/fingerprints.json").exists(), "deleted on disk")
            ok("\"schema\": 2" in (g / ".shortcuts/.virtual/ongoing.json").read_text(), "rewritten on disk")
            ok((g / ".plan/README.md").read_text() == "plan v2\n", "replaced with the new template")
            ok((g / ".decisions/README.md").read_text() == "our own decisions\n", "the project's text is untouched")
            ok((g / ".decisions/README.md.template").read_text() == "decisions v2\n", "the new text waits beside it")
            ok((g / ".orders/ORD-0001/ORD-0001.xml").is_file() and (g / ".scope/raw.md").is_file(), "acts and .scope/ survive")
            st = read_stamp(g)
            ok(st["regency"] == "2.10" and st["files"].get(".plan/README.md") == fingerprint(b"plan v2\n")
               and st["history"][-1]["plan"] == pl["id"], "stamped with the version, the files and the plan")
            ok(gate(proj, reg)[0] == 0, "after the update the gate agrees")
            ok(check(proj, reg)[0] == 0 and not [o for o in plan(proj, reg)["ops"]], "a second plan is empty")
            (g / ".plan/README.md").write_text("plan v2, then ours\n", encoding="utf-8")
            (reg / "library" / "templates" / "guidelines" / ".guidelines/.plan/README.md").write_text("plan v3\n", encoding="utf-8")
            (reg / "library" / "registry.json").write_text('{"version": "2.11"}', encoding="utf-8")
            kinds = [(op["op"], op["path"]) for op in plan(proj, reg)["ops"]]
            ok(("beside", ".plan/README.md.template") in kinds, "edited after its stamp: beside, not replace")
            (reg / "library" / "registry.json").write_text('{"version": "2.9"}', encoding="utf-8")
            code, line = gate(proj, reg)
            ok(code == 2 and "update the plugin" in line, f"a newer project stops the older plugin ({line[:50]})")
            ok(plan(proj, reg)["note"] and not plan(proj, reg)["ops"], "and plans nothing")
        else:
            ok(True, "git unavailable: apply cases skipped")
        code, line = record(reg, check_only=True)
        ok(code == 1 and "lacks" in line, "a template missing from history fails record --check")
        ok(record(reg)[0] == 0 and record(reg, check_only=True)[0] == 0, "record files it, and --check passes")
    bad = [n for good, n in cases if not good]
    for n in bad:
        print("MISS", n)
    print(f"migrate selftest: {len(cases) - len(bad)}/{len(cases)} ok")
    return 1 if bad else 0


# ---------- command line ----------------------------------------------------------------------------

def show(pl):
    if pl["note"]:
        return [pl["note"]]
    head = f"regency update {pl['from'] or 'unstamped'} -> {pl['to']}   guidelines: {pl['guidelines']}"
    if pl.get("guess"):
        head += f"   (its files look like {pl['guess']})"
    lines = [head]
    if not pl["ops"]:
        return lines + ["nothing to do: the project fits"]
    for op in pl["ops"]:
        target = f" -> {op['to']}" if op.get("to") else ""
        lines.append(f"{op['n']:>3}  {op['op']:<8} {op['path']}{target}   ({op.get('why', '')})")
    for op in pl["refused"]:
        lines.append(f"  -  refused  {op['op']} {op['path']}   ({op['refused']})")
    lines.append(f"plan {pl['id']}: {len(pl['ops'])} operation(s); apply with: migrate.py apply --yes {pl['id']}")
    return lines


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--selftest":
        return selftest()
    cmd, rest = argv[0], argv[1:]
    start = rest[rest.index("--from") + 1] if "--from" in rest else "."
    if cmd == "gate":
        code, line = gate(start)
        print(line)
        return code
    if cmd == "plan":
        pl = plan(start)
        print("\n".join(show(pl)))
        return 2 if pl["note"] and "newer" in pl["note"] else 0
    if cmd == "apply":
        if "--yes" not in rest:
            print("apply needs --yes <plan id>: the Regent's one yes to the plan shown by migrate.py plan")
            return 2
        code, lines = apply(start, rest[rest.index("--yes") + 1])
        print("\n".join(lines))
        return code
    if cmd == "check":
        code, line = check(start)
        print(line)
        return code
    if cmd == "stamp":
        repo = repo_root(start)
        g = guidelines_root(repo)
        if g is None:
            print("no guidelines here: nothing to stamp")
            return 2
        st = write_stamp(g, ROOT)
        print(f"stamped {g.relative_to(repo).as_posix()}/{STAMP}: regency {st['regency']}, {len(st['files'])} file(s)")
        return 0
    if cmd == "record":
        code, line = record(check_only="--check" in rest)
        print(line)
        return code
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
