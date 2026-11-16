#!/usr/bin/env python3
"""alpha.py - the alpha simple release: one pinned commit, one bounded scope, for the Regent to exercise.

library/analytics.md §6. A capsule is an annotated tag `alpha-###` on one commit (normally testing): the tag's
message carries the manifest, so the pin and its description travel together and never move. The files go to
<repo>/.alpha/alpha-###/ - `source/` exported with `git archive`, then the project's build run inside it when the
manifest names one - and `.alpha/` ignores itself, so nothing of it enters a commit.

  plan     the manifest skeleton for the next id: ref, SHA, the live findings of the analytics lane; the
           playbook fills scope, build, check steps and limits from the project's documents and the Regent
  cut      refuse an unfilled or colliding manifest; tag the commit; export; build when asked
  list     every alpha with its commit, date and scope        show ID   one manifest whole

Nothing here pushes: `git push origin alpha-###` publishes the tag, on the Regent's yes.

Modes:  plan [--ref REF] · cut MANIFEST|- [--build] · list · show ID · --selftest      (each mode takes --repo DIR)
Pure standard library, Python 3.8+.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402
import analytics  # noqa: E402  (git helpers; the lane's live findings for the manifest)

ALPHA_ID = re.compile(r"^alpha-(\d{3,})$")
OUT = ".alpha"
PLACEHOLDER = re.compile(r"<[^<>]+>")
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.S)
BUILD_TIMEOUT = 1800
git, rev, LaneError = analytics.git, analytics.rev, analytics.LaneError


def ids(repo):
    out = analytics.try_git(repo, "tag", "--list", "alpha-*") or ""
    return sorted(t for t in out.split() if ALPHA_ID.match(t))


def next_id(repo):
    nums = [int(ALPHA_ID.match(t).group(1)) for t in ids(repo)]
    return f"alpha-{(max(nums) + 1 if nums else 1):03d}"


def plan(repo, ref=None):
    ref = ref or analytics.default_target(repo)
    sha = rev(repo, ref)
    if not sha:
        raise LaneError(f"`{ref}` is not a commit here")
    idx, _, _ = analytics.load(repo)
    findings = [f"{k} {f['kind']} - {f['title']}" for k, f in sorted(analytics.live(idx).items())]
    return {"id": next_id(repo), "ref": ref, "sha": sha,
            "scope": {"included": ["<a feature, module or utility the Regent tests>"],
                      "excluded": ["<what this capsule leaves out on purpose>"]},
            "build": {"command": "<the project's build command, run inside source/; empty for none>",
                      "artefacts": ["<a path the build leaves inside source/, e.g. bin/app>"]},
            "check": ["<one step the Regent takes to try it>"],
            "limits": ["<a known limitation>"],
            "findings": findings}


def unfilled(value, path="manifest"):
    """Paths whose value is still a <placeholder>."""
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in unfilled(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in unfilled(v, f"{path}[{i}]")]
    return [path] if isinstance(value, str) and PLACEHOLDER.fullmatch(value.strip()) else []


def tag_text(m):
    lines = [f"{m['id']} - alpha simple release of {m['ref']} at {m['sha'][:12]}", "",
             "Included: " + "; ".join(m["scope"]["included"]),
             "Excluded: " + ("; ".join(m["scope"].get("excluded") or []) or "nothing named"),
             "Check: " + " / ".join(m.get("check") or []),
             "Limits: " + ("; ".join(m.get("limits") or []) or "none named"),
             "Open findings: " + (str(len(m.get("findings") or [])) if m.get("findings") else "none"), "",
             "```json", json.dumps(m, ensure_ascii=False, indent=1), "```", ""]
    return "\n".join(lines)


def export(repo, sha, dest):
    raw = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha], capture_output=True, timeout=300)
    if raw.returncode != 0:
        raise LaneError("git archive: " + raw.stderr.decode("utf-8", "replace").strip()[:300])
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw.stdout)) as tar:
        root = dest.resolve()
        for member in tar.getmembers():
            target = (dest / member.name).resolve()
            if root != target and root not in target.parents:
                raise LaneError(f"git archive: member {member.name!r} escapes the export folder")
        if hasattr(tarfile, "data_filter"):  # Python 3.12, and the 3.8-3.11 security releases
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)


def run_build(command, cwd):
    with open(cwd.parent / "build.log", "w", encoding="utf-8", newline="") as log:
        try:
            r = subprocess.run(command, shell=True, cwd=str(cwd), stdout=log, stderr=subprocess.STDOUT,
                               timeout=BUILD_TIMEOUT)
            return r.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\nalpha.py: the build passed its {BUILD_TIMEOUT} s limit and was stopped\n")
            return 124


def cut(repo, manifest, build=False):
    m = manifest
    holes = unfilled({k: v for k, v in m.items() if k != "findings"})
    if holes:
        raise LaneError("the manifest still holds placeholders: " + ", ".join(holes[:6]))
    if not ALPHA_ID.match(m.get("id", "")):
        raise LaneError(f"`{m.get('id')}` is not an alpha id (alpha-###)")
    if m["id"] in ids(repo):
        raise LaneError(f"{m['id']} already exists: a capsule never moves; plan the next id")
    if not (m.get("scope") or {}).get("included"):
        raise LaneError("scope.included is empty: name what the Regent tests")
    sha = rev(repo, m.get("sha", ""))
    if not sha:
        raise LaneError(f"`{m.get('sha')}` is not a commit here")
    m = dict(m, sha=sha, at=wire.now())
    git(repo, "tag", "-a", "--cleanup=verbatim", m["id"], sha, "-F", "-", data=tag_text(m).encode("utf-8"))
    out = repo / OUT
    out.mkdir(exist_ok=True)
    ignore = out / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("# regency: alpha exports and builds never enter a commit (library/analytics.md §6)\n*\n",
                          encoding="utf-8")
    home = out / m["id"]
    export(repo, sha, home / "source")
    (home / "MANIFEST.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    result = {"id": m["id"], "tag": m["id"], "sha": sha, "export": wire.rel_posix(home, repo),
              "build": "not run", "push": f"git push origin {m['id']}"}
    command = (m.get("build") or {}).get("command") or ""
    if build and command:
        code = run_build(command, home / "source")
        missing = [a for a in (m["build"].get("artefacts") or []) if not (home / "source" / a).exists()]
        result.update(build="green" if code == 0 and not missing else "red", exit=code, missing=missing,
                      log=wire.rel_posix(home / "build.log", repo))
    return result


def manifest_of(repo, tag):
    text = analytics.try_git(repo, "tag", "--list", "--format=%(contents)", tag) or ""
    m = JSON_BLOCK.search(text)
    return json.loads(m.group(1)) if m else None


def listing(repo):
    rows = []
    for t in ids(repo):
        m = manifest_of(repo, t) or {}
        rows.append(f"{t} {m.get('ref', '?')}@{(m.get('sha') or '?')[:7]} {(m.get('at') or '')[:10]} - "
                    + "; ".join((m.get("scope") or {}).get("included") or ["(no manifest)"]))
    return rows or ["alpha: none yet"]


def cli(argv):
    ap = argparse.ArgumentParser(prog="alpha.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("plan").add_argument("--ref")
    c = sub.add_parser("cut")
    c.add_argument("manifest")
    c.add_argument("--build", action="store_true")
    sub.add_parser("list")
    sub.add_parser("show").add_argument("id")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    repo = wire.repo_root(Path(a.repo).resolve() if a.repo else Path.cwd())
    try:
        if a.cmd == "plan":
            print(json.dumps(plan(repo, a.ref), ensure_ascii=False, indent=1))
        elif a.cmd == "cut":
            text = sys.stdin.read() if a.manifest == "-" else Path(a.manifest).read_text(encoding="utf-8")
            print(json.dumps(cut(repo, json.loads(text), a.build), ensure_ascii=False))
        elif a.cmd == "list":
            print("\n".join(listing(repo)))
        elif a.cmd == "show":
            m = manifest_of(repo, a.id)
            if m is None:
                raise LaneError(f"{a.id}: no such alpha, or its tag carries no manifest")
            print(json.dumps(m, ensure_ascii=False, indent=1))
    except (LaneError, OSError, ValueError, KeyError) as e:
        print(f"alpha.py: {e}", file=sys.stderr)
        return 2
    return 0


def selftest():
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = analytics.fixture_repo(tmp)
        m = plan(repo)
        cases.append((m["id"] == "alpha-001" and m["ref"] == "testing" and m["sha"] == rev(repo, "testing"),
                      "plan: the next id, pinned to testing's commit"))
        try:
            cut(repo, m)
            cases.append((False, "cut: refuses a manifest that still holds placeholders"))
        except LaneError as e:
            cases.append(("placeholders" in str(e), "cut: refuses a manifest that still holds placeholders"))
        script = "import pathlib; pathlib.Path('bin').mkdir(); pathlib.Path('bin/app').write_text('ok')"
        m.update(scope={"included": ["approve a card"], "excluded": ["reversal"]},
                 build={"command": f'"{sys.executable}" -c "{script}"', "artefacts": ["bin/app"]},
                 check=["open bin/app"], limits=["no reversal yet"])
        out = cut(repo, m, build=True)
        home = repo / OUT / "alpha-001"
        cases.append((out["build"] == "green" and (home / "source/src/approve.py").is_file()
                      and (home / "source/bin/app").is_file(), "cut: exported at the pinned commit and built inside it"))
        cases.append((rev(repo, "alpha-001") == m["sha"] and manifest_of(repo, "alpha-001")["scope"]["excluded"] == ["reversal"],
                      "cut: the annotated tag pins the commit and carries the manifest"))
        cases.append((git(repo, "status", "--porcelain") == "", "cut: .alpha/ ignores itself; the work tree stays clean"))
        try:
            cut(repo, m)
            cases.append((False, "cut: an existing id is refused - a capsule never moves"))
        except LaneError:
            cases.append((True, "cut: an existing id is refused - a capsule never moves"))
        failing = dict(m, id="alpha-002", build={"command": f'"{sys.executable}" -c "raise SystemExit(3)"',
                                                 "artefacts": ["bin/none"]})
        out2 = cut(repo, failing, build=True)
        cases.append((out2["build"] == "red" and out2["exit"] == 3 and out2["missing"] == ["bin/none"],
                      "cut: a failing build is reported red with its exit and missing artefacts"))
        rows = listing(repo)
        cases.append((len(rows) == 2 and rows[0].startswith("alpha-001 testing@") and "approve a card" in rows[0],
                      "list: one line per alpha, from its tag"))
        cases.append((plan(repo)["id"] == "alpha-003", "plan: numbering follows the existing tags"))
    return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else cli(sys.argv[1:]))
