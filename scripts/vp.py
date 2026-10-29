#!/usr/bin/env python3
"""vp.py - read-only queries over a project's virtual-path manifest.

The manifest links NORM SLICES (anchors inside guidelines documents) to the CODE they govern:

  {"virtual_context": [
     {"virtual_path": ".decisions/ARCHITECTURE.md#layout-estavel",
      "refers_to": ["src/Page.razor", "src/Other.razor"],
      "selector_type": "markdown_anchor | glyph_block | ledger_row",
      "on_mutation": "mark_stale | lock"}]}

Commands (all read-only):
  vp.py code  <code path>        slices that govern this code file (read them BEFORE editing it);
                                 a refers_to entry may name one node: path#n:<id> (idx.py)
  vp.py slice <virtual_path>     code governed by this slice;  add --show to print the slice text
  vp.py stale                    slices carrying a STALE warning line (waiting for the Regent's check)
  vp.py check                    every slice resolves to an anchor; every refers_to file exists
  vp.py ongoing                  the work ledger (.virtual/ongoing.json): ongoing / draft / review / blocked / backlog
  vp.py trace                    every trace of agent work in the repo (git, guidelines, orders), to reconcile the ledger
  vp.py drafts                   unverified drafts from a speed mode: ledger items in 'draft' and 'Draft: UNVERIFIED'
                                 commits with no 'Verified-Draft:' commit for their unit; exit 1 while any remain
                                 (library/team/SPEED_MODES.md section 6: nothing merges past plumbing until it is 0)
  vp.py --selftest               plant a defect per ledger rule and per draft rule; exit 1 if one goes unseen

Options:
  --manifest FILE   explicit manifest (default: found by searching .shortcuts/.virtual/manifest*.json)
  --repo DIR        repository root that refers_to is relative to (default: nearest .git, else guessed)
  --from DIR        where to start searching for the manifest (default: current directory)

Pure standard library, Python 3.8+. Never writes anything (the self-test writes to a temp folder).
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SKIP = {".git", "node_modules", ".venv", "bin", "obj", "dist", "build", "discard", ".obsidian"}


def find_manifest(start):
    start = Path(start).resolve()
    hits = []
    for base in [start] + list(start.parents):
        for pat in ("**/.shortcuts/.virtual/manifest*.json", ".shortcuts/.virtual/manifest*.json"):
            for p in base.glob(pat):
                if not any(part in SKIP for part in p.relative_to(base).parts):
                    hits.append(p)
        if hits:
            return sorted(hits, key=lambda p: len(p.parts))[0]
        if base.name == "" or (base / ".git").exists():
            break
    return None


def repo_root(guidelines, explicit):
    if explicit:
        return Path(explicit).resolve()
    for p in [guidelines] + list(guidelines.parents):
        if (p / ".git").exists():
            return p
    g = guidelines.parent
    return g.parent if g.name.lower() == "docs" else g


def load(args):
    manifest = Path(args["manifest"]).resolve() if args.get("manifest") else find_manifest(args.get("from") or ".")
    if not manifest or not manifest.is_file():
        sys.exit("vp: no manifest found (looked for .shortcuts/.virtual/manifest*.json). Use --manifest FILE.")
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    entries = data.get("virtual_context", [])
    guidelines = manifest.parent.parent.parent  # <guidelines>/.shortcuts/.virtual/<manifest>
    return manifest, entries, guidelines, repo_root(guidelines, args.get("repo"))


def split_vpath(vp):
    if "#" in vp:
        f, a = vp.split("#", 1)
        return f, a
    return vp, ""


def headings(lines):
    for i, l in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", l)
        if m:
            yield i, len(m.group(1)), m.group(2)


def resolve(guidelines, entry):
    """Return (ok, start_line, end_line, lines) of the slice; ok False when it does not resolve."""
    f, anchor = split_vpath(entry["virtual_path"])
    path = guidelines / f
    if not path.is_file():
        return False, 0, 0, []
    lines = path.read_text(encoding="utf-8-sig", errors="replace").split("\n")
    kind = entry.get("selector_type", "markdown_anchor")
    if kind == "markdown_anchor":
        for i, lvl, text in headings(lines):
            sec = re.search(r"§([^\s—:]+)", text)
            name = sec.group(1) if text.lstrip().startswith("§") and sec else text
            if name == anchor or (sec and sec.group(1) == anchor):
                end = len(lines)
                for j, lv2, _ in headings(lines):
                    if j > i and lv2 <= lvl:
                        end = j
                        break
                return True, i, end, lines
        return False, 0, 0, lines
    if kind == "glyph_block":
        for i, l in enumerate(lines):
            if f"[block'{anchor}'" in l:
                end = next((j for j in range(i + 1, len(lines)) if lines[j].strip().startswith("[/block")), i + 1)
                return True, i, end + 1, lines
        return False, 0, 0, lines
    if kind == "ledger_row":
        for i, l in enumerate(lines):
            m = re.match(r"^\|\s*~{0,2}\s*\*\*(.+?)\*\*", l)  # a paid row is struck through: ~~**label**~~
            if m and m.group(1).strip() == anchor:
                return True, i, i + 1, lines
        return False, 0, 0, lines
    return False, 0, 0, lines


def cmd_code(entries, target, repo):
    t = Path(target)
    rel = str(t.resolve().relative_to(repo)).replace("\\", "/") if t.is_absolute() else target.replace("\\", "/")
    hits = [e for e in entries if any(r.partition("#")[0] == rel for r in e.get("refers_to", []))]
    if not hits:
        print(f"no slice cites {rel} (code that cites an anchor: idx.py governs {rel})")
        return 0
    for e in hits:
        nodes = [r.partition("#")[2] for r in e.get("refers_to", []) if r.partition("#")[0] == rel and "#" in r]
        scope = f"  nodes {', '.join(nodes)}" if nodes else ""
        print(f"{e['virtual_path']}   [{e.get('selector_type', '?')}, {e.get('on_mutation', '?')}]{scope}")
    return 0


def cmd_slice(entries, vp, guidelines, show):
    hit = next((e for e in entries if e["virtual_path"] == vp), None)
    if not hit:
        print(f"no such slice: {vp}")
        return 1
    print("\n".join(hit.get("refers_to", [])))
    if show:
        ok, s, e, lines = resolve(guidelines, hit)
        print("\n--- slice text ---" if ok else "\n--- slice DOES NOT RESOLVE ---")
        if ok:
            print("\n".join(lines[s:e]))
    return 0


def cmd_stale(entries, guidelines):
    n = 0
    for p in sorted(guidelines.rglob("*.md")):
        if any(part in SKIP for part in p.relative_to(guidelines).parts):
            continue
        for i, l in enumerate(p.read_text(encoding="utf-8-sig", errors="replace").split("\n"), 1):
            if "warn'STALE" in l:
                print(f"{p.relative_to(guidelines).as_posix()}:{i}: {l.strip()[:200]}")
                n += 1
    print(f"{n} STALE line(s)")
    return 0


def cmd_check(entries, guidelines, repo):
    bad = 0
    for e in entries:
        ok, *_ = resolve(guidelines, e)
        if not ok:
            print(f"UNRESOLVED  {e['virtual_path']}  ({e.get('selector_type', 'markdown_anchor')})")
            bad += 1
        for r in e.get("refers_to", []):
            if not (repo / r.partition("#")[0]).exists():
                print(f"MISSING     {r}  <- {e['virtual_path']}")
                bad += 1
    refs = sum(len(e.get("refers_to", [])) for e in entries)
    print(f"{len(entries)} slices, {refs} references, {bad} problem(s)")
    return 1 if bad else 0


LEDGER_STATES = ("ongoing", "draft", "review", "blocked", "backlog", "done")
DRAFT_FORBIDDEN = ("main", "master", "testing")  # a draft lives on plumbing; it never reaches these (SPEED_MODES §6)
TRAILER_DRAFT = re.compile(r"(?m)^Draft:[ \t]*UNVERIFIED[ \t]*$")
TRAILER_UNIT = re.compile(r"(?m)^Unit:[ \t]*(\S+)[ \t]*$")
TRAILER_VERIFIED = re.compile(r"(?m)^Verified-Draft:[ \t]*(\S+)[ \t]*$")


def virtual_dir(args):
    """The .shortcuts/.virtual directory: next to the manifest if there is one, else searched."""
    m = Path(args["manifest"]).resolve() if args.get("manifest") else find_manifest(args.get("from") or ".")
    if m and m.is_file():
        return m.parent
    start = Path(args.get("from") or ".").resolve()
    for base in [start] + list(start.parents):
        for p in sorted(base.glob("**/.shortcuts/.virtual"), key=lambda p: len(p.parts)):
            if p.is_dir() and not any(part in SKIP for part in p.relative_to(base).parts):
                return p
        if (base / ".git").exists():
            break
    return None


def git(repo, *a):
    try:
        r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.stdout.strip() if r.returncode == 0 else None
    except OSError:
        return None


def lines_of(text):
    return [l for l in (text or "").split("\n") if l.strip()]


def cmd_trace(vdir, repo):
    """Everything agents leave behind, so a returning agent can reconcile the ledger with reality."""
    g = vdir.parent.parent if vdir else None  # guidelines root = <g>/.shortcuts/.virtual
    print(f"repo: {repo}")
    branch = git(repo, "branch", "--show-current")
    if branch is None:
        print("git: not a repository (or git unavailable)")
    else:
        print(f"git branch: {branch or '(detached)'}")
        dirty = lines_of(git(repo, "status", "--short"))
        print(f"uncommitted: {len(dirty)}")
        for l in dirty[:20]:
            print("   ", l)
        if len(dirty) > 20:
            print(f"    ... {len(dirty) - 20} more")
        default = next((b for b in ("main", "master") if git(repo, "rev-parse", "--verify", "--quiet", b) is not None), None)
        if default:
            unmerged = [b.strip().lstrip("* ").strip() for b in lines_of(git(repo, "branch", "--no-merged", default))]
            print(f"local branches not merged into {default}: {len(unmerged)}" + ("  " + ", ".join(unmerged[:12]) if unmerged else ""))
            ahead = git(repo, "rev-list", "--count", f"{default}..HEAD")
            if ahead not in (None, "0") and branch != default:
                print(f"commits on this branch not in {default}: {ahead}")
        print(f"stashes: {len(lines_of(git(repo, 'stash', 'list')))}")
        dc = draft_commits(repo)
        if dc and dc[0]:
            print(f"unverified draft commits: {len(dc[0])} unit(s)  {', '.join(sorted(dc[0])[:8])}  (vp.py drafts)")
        print("last commits:")
        for l in lines_of(git(repo, "log", "-8", "--date=short", "--pretty=%h %ad %s")):
            print("   ", l[:150])
    if g and g.is_dir():
        now = time.time()
        recent = []
        for p in g.rglob("*"):
            if p.is_file() and not any(part in SKIP for part in p.relative_to(g).parts):
                age = now - p.stat().st_mtime
                if age <= 14 * 86400:
                    recent.append((age, p))
        recent.sort()
        print(f"guidelines touched in the last 14 days: {len(recent)}")
        for age, p in recent[:15]:
            print(f"    {age / 86400:4.1f}d  {p.relative_to(g).as_posix()}")
        stale = 0
        for p in g.rglob("*.md"):
            if not any(x in SKIP for x in p.relative_to(g).parts):
                stale += p.read_text(encoding="utf-8-sig", errors="replace").count("warn'STALE")
        print(f"STALE lines: {stale}")
        od = g / ".orders"
        orders = sorted(p.name for p in od.glob("ORD-*")) if od.is_dir() else []
        print(f"orders: {', '.join(orders) if orders else 'none'}")
    if vdir:
        led = vdir / "ongoing.json"
        print(f"ledger: {'present' if led.is_file() else 'ABSENT'} ({led.as_posix()})")
    else:
        print("ledger: no .shortcuts/.virtual directory found")
    return 0


def draft_problems(it):
    """What a 'draft' ledger item lacks: a branch and files as evidence, never a branch past plumbing."""
    where = it.get("where") or []
    branches = [w.split(":", 1)[1] for w in where if w.startswith("branch:")]
    out = []
    if not branches:
        out.append(f"{it['id']}: draft with no 'branch:' evidence in 'where'")
    for b in branches:
        if b in DRAFT_FORBIDDEN:
            out.append(f"{it['id']}: draft on branch {b}: a draft never leaves plumbing until a team pass verifies it")
    return out


def default_branch(repo):
    return next((b for b in ("main", "master") if git(repo, "rev-parse", "--verify", "--quiet", b) is not None), None)


def draft_commits(repo):
    """(unverified, verified): units with a 'Draft: UNVERIFIED' commit on HEAD and not on the default branch,
    minus those a later 'Verified-Draft: <unit>' commit closed; None when git cannot answer."""
    default = default_branch(repo)
    rng = [f"{default}..HEAD"] if default and git(repo, "rev-parse", "--abbrev-ref", "HEAD") != default else ["HEAD"]
    log = git(repo, "log", "--format=%h%x00%B%x01", *rng)
    if log is None:
        return None
    drafted, verified = {}, set()
    for rec in log.split("\x01"):
        sha, _, body = rec.strip().partition("\x00")
        if not sha:
            continue
        verified.update(TRAILER_VERIFIED.findall(body))
        if TRAILER_DRAFT.search(body):
            for unit in TRAILER_UNIT.findall(body) or ["(no Unit: trailer)"]:
                drafted.setdefault(unit, []).append(sha)
    return {u: c for u, c in drafted.items() if u not in verified}, verified


def cmd_drafts(vdir, repo):
    """Every unverified draft: ledger items in 'draft' and draft commits no verifying commit has closed."""
    items = []
    led = vdir / "ongoing.json" if vdir else None
    if led and led.is_file():
        items = [it for it in json.loads(led.read_text(encoding="utf-8-sig")).get("items", []) if it.get("state") == "draft"]
    commits = draft_commits(repo)
    print(f"ledger drafts: {len(items)}")
    for it in items:
        print(f"  {it.get('id', '?')}  {it.get('title', '')}  where: {', '.join(it.get('where') or []) or '-'}")
        for p in draft_problems(it) if it.get("id") else []:
            print(f"      problem: {p}")
    if commits is None:
        print("draft commits: git unavailable or not a repository")
        unverified = {}
    else:
        unverified, verified = commits
        print(f"draft commits not yet verified: {len(unverified)} unit(s)" + (f"   (verified: {len(verified)})" if verified else ""))
        for unit, shas in sorted(unverified.items()):
            print(f"  {unit}  {' '.join(shas[:6])}{f' and {len(shas) - 6} more' if len(shas) > 6 else ''}")
    n = len(items) + len(unverified)
    print(f"{n} unverified draft(s)" + (": nothing merges past plumbing until a /regency:team pass verifies each" if n else ""))
    return 1 if n else 0


def cmd_ongoing(vdir, repo):
    if not vdir:
        print("no .shortcuts/.virtual directory: this project keeps no work ledger yet.")
        print("create it only with the Regent's yes (see library/virtualpath.md, 'The work ledger').")
        return 0
    led = vdir / "ongoing.json"
    if not led.is_file():
        print(f"no ledger at {led.as_posix()}; template: library/templates/guidelines/.guidelines/.shortcuts/.virtual/ongoing.json")
        return 0
    data = json.loads(led.read_text(encoding="utf-8-sig"))
    items = data.get("items", [])
    problems, by, ids = [], {s: [] for s in LEDGER_STATES}, set()
    for it in items:
        miss = [k for k in ("id", "title", "state") if not it.get(k)]
        if miss:
            problems.append(f"item {it.get('id', '?')}: missing {', '.join(miss)}")
            continue
        if it["id"] in ids:
            problems.append(f"duplicate id {it['id']}")
        ids.add(it["id"])
        if it["state"] not in LEDGER_STATES:
            problems.append(f"{it['id']}: unknown state {it['state']!r}")
            continue
        if it["state"] == "ongoing" and not it.get("where"):
            problems.append(f"{it['id']}: ongoing with no evidence in 'where'")
        if it["state"] == "draft":
            problems += draft_problems(it)
        if it["state"] == "blocked" and not it.get("blocked_by"):
            problems.append(f"{it['id']}: blocked with no 'blocked_by'")
        by[it["state"]].append(it)
        for w in it.get("where", []):
            if not w.startswith(("branch:", "pass:", "order:")) and "#" not in w and not (repo / w).exists():
                problems.append(f"{it['id']}: evidence path missing: {w}")
    print(f"ledger updated: {data.get('updated', '?')}   items: {len(items)}")
    for s in LEDGER_STATES:
        if s in ("draft", "done") and not by[s]:
            continue
        print(f"\n{s.upper()} ({len(by[s])})")
        for it in by[s]:
            extra = f" <- {it['blocked_by']}" if s == "blocked" else ""
            print(f"  {it['id']}  {it['title']}  [{it.get('who', '?')}, since {it.get('since', '?')}]{extra}")
            if it.get("next"):
                print(f"      next: {it['next']}")
    if by["done"]:
        problems.append(f"{len(by['done'])} 'done' item(s) still listed: remove them at the next handoff (version control is the record)")
    print(f"\n{len(problems)} problem(s)")
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


def selftest():
    """Plant a defect per ledger and draft rule in a throwaway project; every one must be seen."""
    import contextlib
    import io
    import shutil
    import tempfile
    cases = []

    def run(fn, *a):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fn(*a)
        return code, buf.getvalue()

    tmp = Path(tempfile.mkdtemp(prefix="vp-selftest-"))
    try:
        repo = tmp / "p"
        vdir = repo / ".guidelines" / ".shortcuts" / ".virtual"
        vdir.mkdir(parents=True)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")

        def ledger(*items):
            (vdir / "ongoing.json").write_text(json.dumps({"schema": 1, "updated": "2026-10-28", "items": list(items)}),
                                               encoding="utf-8")
            return run(cmd_ongoing, vdir, repo)

        good = {"id": "M01.D01.T01", "title": "a", "state": "draft", "who": "DV",
                "where": ["branch:plumbing", "src/a.py"], "next": "verify: /regency:team M01.D01.T01"}
        code, out = ledger(good)
        cases.append((code == 0 and "DRAFT (1)" in out, "a draft with branch and files holds"))
        code, out = ledger(dict(good, where=["src/a.py"]))
        cases.append((code == 1 and "no 'branch:' evidence" in out, "a draft with no branch is named"))
        code, out = ledger(dict(good, where=["branch:main", "src/a.py"]))
        cases.append((code == 1 and "draft on branch main" in out, "a draft on main is named"))
        code, out = ledger(dict(good, where=["branch:testing", "src/a.py"]))
        cases.append((code == 1 and "draft on branch testing" in out, "a draft on testing is named"))
        code, out = ledger(dict(good, state="ongoing", where=[]))
        cases.append((code == 1 and "ongoing with no evidence" in out, "ongoing still needs evidence"))
        code, out = ledger(dict(good, state="drafted"))
        cases.append((code == 1 and "unknown state" in out, "an unknown state is named"))
        code, out = ledger(dict(good, state="review"))
        cases.append((code == 0 and "DRAFT" not in out, "no draft, no DRAFT section"))

        if shutil.which("git"):
            def g(*a):
                return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                                       "-c", "commit.gpgsign=false", *a], capture_output=True, text=True)
            g("init", "-q", "-b", "main")
            g("add", "-A")
            g("commit", "-qm", "base")
            g("checkout", "-qb", "plumbing")
            (repo / "src" / "b.py").write_text("y = 2\n", encoding="utf-8")
            g("add", "-A")
            g("commit", "-qm", "draft(M01.D01.T02): b\n\nDraft: UNVERIFIED\nUnit: M01.D01.T02\nSpeed-Mode: just-in-time")
            ledger(dict(good, id="M01.D01.T02"))
            code, out = run(cmd_drafts, vdir, repo)
            cases.append((code == 1 and "M01.D01.T02" in out and "1 unit(s)" in out, f"an unverified draft commit is listed: {out[-90:]!r}"))
            ledger(dict(good, id="M01.D01.T02", state="review"))
            code, out = run(cmd_drafts, vdir, repo)
            cases.append((code == 1 and "not yet verified: 1" in out, "a ledger moved by hand does not verify the commit"))
            (repo / "src" / "b.py").write_text("y = 2  # verified\n", encoding="utf-8")
            g("add", "-A")
            g("commit", "-qm", "feat(M01.D01.T02): b, verified\n\nVerified-Draft: M01.D01.T02")
            code, out = run(cmd_drafts, vdir, repo)
            cases.append((code == 0 and "0 unverified" in out, f"a Verified-Draft commit closes it: {out[-60:]!r}"))
            g("commit", "-q", "--allow-empty", "-m", "draft: no unit\n\nDraft: UNVERIFIED")
            code, out = run(cmd_drafts, vdir, repo)
            cases.append((code == 1 and "(no Unit: trailer)" in out, "a draft commit without Unit: is named"))
            code, out = run(cmd_trace, vdir, repo)
            cases.append(("unverified draft commits: 1" in out, "trace names unverified draft commits"))
        else:
            cases.append((True, "git unavailable: draft-commit cases skipped"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [name for ok, name in cases if not ok]
    for name in bad:
        print("MISS", name)
    print(f"vp selftest: {len(cases) - len(bad)}/{len(cases)} ok")
    return 1 if bad else 0


def main(argv):
    opts, pos, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a in ("--manifest", "--repo", "--from") and i + 1 < len(argv):
            opts[a[2:]] = argv[i + 1]
            i += 2
        elif a == "--show":
            opts["show"] = True
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a == "--selftest":
            return selftest()
        else:
            pos.append(a)
            i += 1
    if not pos:
        print(__doc__)
        return 2
    cmd, rest = pos[0], pos[1:]
    if cmd in ("trace", "ongoing", "drafts"):
        vdir = virtual_dir(opts)
        repo = repo_root(vdir.parent.parent if vdir else Path(opts.get("from") or ".").resolve(), opts.get("repo"))
        return {"trace": cmd_trace, "ongoing": cmd_ongoing, "drafts": cmd_drafts}[cmd](vdir, repo)
    manifest, entries, guidelines, repo = load(opts)
    if cmd == "code" and rest:
        return cmd_code(entries, rest[0], repo)
    if cmd == "slice" and rest:
        return cmd_slice(entries, rest[0], guidelines, opts.get("show"))
    if cmd == "stale":
        return cmd_stale(entries, guidelines)
    if cmd == "check":
        return cmd_check(entries, guidelines, repo)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
