#!/usr/bin/env python3
"""issues.py - the repository's issues against the project's own records (library/issues.md).

One function per verb; one finding or one issue per line.

  issues.py check                      every issue against its verdict; exit 1 while one is untriaged or broken
  issues.py status [N]                 one line per issue, or one issue whole: state, age, checklist, verdict
  issues.py measure N                  the issue as a slice for /regency:measure-changes; applies nothing

  issues.py adopt N --to LEDGER_ID --why TEXT       verdict: the issue is work here, held by that ledger item
  issues.py flatten N --to PATH[#anchor] --why TEXT verdict: the issue is lesser, noted at that place
  issues.py ignore N --why TEXT                     verdict: nothing is owed here

  issues.py close N [--reason completed|not-planned] [--yes]
  issues.py publish --title T --body-file F [--label L]... [--yes]
  issues.py question N --body-file F [--yes]        adds one comment, changes nothing else
  issues.py revise N --body-file F [--yes]          replaces the description
  issues.py revise N --fold --why TEXT [--yes]      folds the description under one line (what flatten leaves)

Verdicts are the Regent's: record one only from the Regent's answer. They live in issues.json beside the
work ledger (<guidelines>/.shortcuts/.virtual/). The four tracker writes print their plan and change
nothing; --yes runs it through gh, and is passed only after the Regent's yes.

The issues are read with gh (gh issue list), or from --json FILE ('-' is stdin): gh's own JSON or the
GitHub tool's {"issues": [...]}. --repo DIR names the repository when the current folder is not inside it.

Exit codes: 0 fine, 1 a finding that needs the Regent, 2 usage or no data.  --selftest plants a defect per rule.
Pure standard library, Python 3.8+.
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402

VERDICTS = ("adopt", "flatten", "ignore")
PAST = {"adopt": "adopted", "flatten": "flattened", "ignore": "ignored"}
FIELDS = "number,title,state,labels,createdAt,updatedAt,comments,body"
BOX = re.compile(r"(?m)^\s*[-*] \[( |x|X)\]")
CITED = re.compile(r"`([\w.\-/]+\.[A-Za-z0-9]{1,5}|[\w.\-]+(?:/[\w.\-]+)+/?)`")
FOLD_OPEN = "<details><summary>The description as filed</summary>"


# ---------- stores -----------------------------------------------------------------------------

def virtual_dir(repo):
    v = wire.virtual_dir(repo)
    if v:
        return v
    v = Path(repo) / ".shortcuts" / ".virtual"
    return v if v.is_dir() else None


def load_store(vdir):
    p = vdir / "issues.json" if vdir else None
    if not p or not p.is_file():
        return {"schema": 1, "issues": []}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_store(vdir, store):
    store["updated"] = wire.today()
    store["issues"].sort(key=lambda r: r["n"])
    rows = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in store["issues"])
    head = {k: v for k, v in store.items() if k != "issues"}
    text = json.dumps(head, ensure_ascii=False)[:-1] + ',\n  "issues": [\n' + rows + "\n  ]\n}\n"
    wire.atomic_write(vdir / "issues.json", text)


def ledger_items(vdir):
    p = vdir / "ongoing.json" if vdir else None
    if not p or not p.is_file():
        return {}
    return {it.get("id"): it for it in json.loads(p.read_text(encoding="utf-8-sig")).get("items", [])}


def verdict_of(store, n):
    return next((r for r in store["issues"] if r["n"] == n), None)


# ---------- the tracker ------------------------------------------------------------------------

def normal(raw):
    """One shape for gh's JSON and the GitHub tool's."""
    rows = raw.get("issues", []) if isinstance(raw, dict) else raw
    out = []
    for r in rows:
        comments = r.get("comments", 0)
        out.append({
            "n": int(r["number"]), "title": r.get("title", ""), "open": str(r.get("state", "")).upper() == "OPEN",
            "labels": [l.get("name", "") if isinstance(l, dict) else str(l) for l in r.get("labels", [])],
            "created": (r.get("createdAt") or r.get("created_at") or "")[:10],
            "updated": (r.get("updatedAt") or r.get("updated_at") or "")[:10],
            "comments": len(comments) if isinstance(comments, list) else int(comments or 0),
            "body": r.get("body") or "",
        })
    return sorted(out, key=lambda i: i["n"])


def gh(repo, *args, body=None):
    try:
        r = subprocess.run(["gh", *args], cwd=str(repo), input=body, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return None, "gh is not installed"
    return (r.stdout, None) if r.returncode == 0 else (None, (r.stderr or r.stdout).strip().splitlines()[-1:] or ["gh failed"])


def fetch(repo, opts):
    src = opts.get("json")
    if src:
        text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8-sig")
        return normal(json.loads(text))
    out, err = gh(repo, "issue", "list", "--state", "all", "--limit", "500", "--json", FIELDS)
    if out is None:
        print(f"issues: no data ({err if isinstance(err, str) else err[0]}). Log in to gh, or pass --json FILE "
              "with the issues as the session's GitHub tool lists them.")
        return None
    return normal(json.loads(out))


def write(repo, opts, label, args, body=None):
    """A tracker write: the plan always, the act only with --yes."""
    print(f"PLAN  {label}: gh {shlex.join(args)}")
    for line in (body or "").splitlines():
        print(f"  | {line}")
    if not opts.get("yes"):
        print("not run: the Regent's yes first, then the same line with --yes "
              "(without gh, the session's GitHub tool does this act with this text)")
        return 0
    out, err = gh(repo, *args, body=body)
    if out is None:
        print(f"FAIL  {label}: {err if isinstance(err, str) else err[0]}")
        return 1
    print(f"DONE  {label} {out.strip()}".rstrip())
    return 0


# ---------- read-only verbs --------------------------------------------------------------------

def findings(issues, store, items):
    """(level, line) per finding. FAIL levels: UNTRIAGED, BROKEN, ORPHAN."""
    out, by_n = [], {i["n"]: i for i in issues}
    for i in issues:
        v = verdict_of(store, i["n"])
        tag = f'#{i["n"]} "{i["title"]}"'
        if not v:
            if i["open"]:
                out.append(("UNTRIAGED", f"{tag} open since {i['created']}: adopt, flatten or ignore"))
            continue
        if v["verdict"] == "adopt":
            it = items.get(v.get("to"))
            if not it:
                out.append(("BROKEN", f"{tag} adopted as '{v.get('to')}', which the ledger does not hold"))
            elif not i["open"]:
                out.append(("CLOSED", f"{tag} is closed and ledger item '{v['to']}' ({it.get('state')}) still stands"))
        elif i["open"]:
            out.append(("OPEN", f"{tag} {PAST[v['verdict']]} {v['on']} and still open: close it, or leave it on purpose"))
        if i["open"] and i["updated"] > v["on"]:
            out.append(("MOVED", f"{tag} changed {i['updated']}, after its verdict of {v['on']}: read it again"))
    for v in store["issues"]:
        if v["n"] not in by_n:
            out.append(("ORPHAN", f"#{v['n']} has a verdict ({v['verdict']}) and the tracker has no such issue"))
    return out


def cmd_check(repo, vdir, opts):
    issues = fetch(repo, opts)
    if issues is None:
        return 2
    store = load_store(vdir)
    found = findings(issues, store, ledger_items(vdir))
    for level, line in found:
        print(f"{level:<9} {line}")
    count = {v: sum(1 for r in store["issues"] if r["verdict"] == v) for v in VERDICTS}
    bad = sum(1 for level, _ in found if level in ("UNTRIAGED", "BROKEN", "ORPHAN"))
    untriaged = sum(1 for level, _ in found if level == "UNTRIAGED")
    print(f"issues: {len(issues)} ({sum(1 for i in issues if i['open'])} open) · adopted {count['adopt']} · "
          f"flattened {count['flatten']} · ignored {count['ignore']} · untriaged {untriaged} -> "
          f"{'TRIAGE' if bad else 'ok'}")
    return 1 if bad else 0


def boxes(body):
    marks = BOX.findall(body)
    return sum(1 for m in marks if m.strip()), len(marks)


def verdict_text(v, items):
    if not v:
        return "untriaged"
    if v["verdict"] == "adopt":
        it = items.get(v.get("to"))
        return f"adopted {v['on']} -> {v.get('to')} ({it.get('state') if it else 'missing from the ledger'})"
    return f"{PAST[v['verdict']]} {v['on']}" + (f" -> {v['to']}" if v.get("to") else "")


def find(issues, n):
    i = next((i for i in issues if i["n"] == n), None)
    if not i:
        print(f"issues: the tracker has no #{n}")
    return i


def cmd_status(repo, vdir, opts, n=None):
    issues = fetch(repo, opts)
    if issues is None:
        return 2
    store, items = load_store(vdir), ledger_items(vdir)
    if n is None:
        for i in issues:
            done, total = boxes(i["body"])
            box = f" · {done}/{total}" if total else ""
            print(f"#{i['n']:<4} {'open' if i['open'] else 'closed':<6} {i['updated']} · {i['comments']} comment(s){box} · "
                  f"{verdict_text(verdict_of(store, i['n']), items)} · {i['title']}")
        return 0
    i = find(issues, n)
    if not i:
        return 2
    done, total = boxes(i["body"])
    v = verdict_of(store, n)
    print(f"Issue     #{n} {i['title']}")
    print(f"State     {'open' if i['open'] else 'closed'} · labels: {', '.join(i['labels']) or 'none'}")
    print(f"Dates     created {i['created']} · updated {i['updated']} · {i['comments']} comment(s)")
    print(f"Checklist {f'{round(100 * done / total)}% - {done}/{total}' if total else 'none'}")
    print(f"Verdict   {verdict_text(v, items)}" + (f" · {v['why']}" if v else ""))
    return 0


def cmd_measure(repo, vdir, opts, n):
    issues = fetch(repo, opts)
    if issues is None:
        return 2
    i = find(issues, n)
    if not i:
        return 2
    cited = sorted(set(CITED.findall(i["body"])))
    here = [c for c in cited if (Path(repo) / c).exists()]
    done, total = boxes(i["body"])
    print(f"Change    issue #{n}: {i['title']} (intended)")
    print(f"Cited     {len(here)} path(s) here: {', '.join(here) or 'none'}")
    print(f"Absent    {len(cited) - len(here)} cited and not in this tree: {', '.join(c for c in cited if c not in here) or 'none'}")
    print(f"Checklist {f'{done}/{total} done' if total else 'none'}")
    print(f"Verdict   {verdict_text(verdict_of(load_store(vdir), n), ledger_items(vdir))}")
    print("Next      /regency:measure-changes with this issue as the intended change; "
          "the cited paths are where the reading starts, not the footprint")
    return 0


# ---------- verdicts ---------------------------------------------------------------------------

def cmd_record(repo, vdir, verdict, n, opts):
    why, to = (opts.get("why") or "").strip(), (opts.get("to") or "").strip()
    if not vdir:
        print("issues: no .shortcuts/.virtual folder here, so no place for a verdict (/regency:init)")
        return 2
    if not why:
        print(f"issues: {verdict} needs --why (a verdict without its reason is not a record)")
        return 2
    if verdict == "adopt" and to not in ledger_items(vdir):
        print(f"issues: adopt needs --to <ledger id>; the ledger holds no '{to}'. Add the item first.")
        return 2
    if verdict == "flatten" and not (to and (Path(repo) / to.split("#")[0]).is_file()):
        print(f"issues: flatten needs --to <path[#anchor]> of the note that holds it; '{to}' is not a file here")
        return 2
    store = load_store(vdir)
    row = {"n": n, "verdict": verdict, "on": opts.get("on") or wire.today(), "why": why}
    if to and verdict != "ignore":
        row["to"] = to
    store["issues"] = [r for r in store["issues"] if r["n"] != n] + [row]
    save_store(vdir, store)
    print(f"#{n} {PAST[verdict]}" + (f" -> {to}" if row.get("to") else "") + f" · {why}")
    if verdict == "flatten":
        print(f"next: issues.py revise {n} --fold --why \"...\"  then  issues.py close {n} --reason not-planned")
    return 0


# ---------- tracker writes ---------------------------------------------------------------------

def body_of(opts):
    f = opts.get("body-file")
    if not f:
        return None
    text = sys.stdin.read() if f == "-" else Path(f).read_text(encoding="utf-8-sig")
    return text.strip() + "\n" if text.strip() else None


def folded(body, why):
    if FOLD_OPEN in body:
        return None
    return f"**Closed: lesser.** {why}\n\n{FOLD_OPEN}\n\n{body.strip()}\n\n</details>\n"


def cmd_close(repo, opts, n):
    reason = opts.get("reason") or "completed"
    if reason not in ("completed", "not-planned"):
        print("issues: --reason is completed or not-planned")
        return 2
    return write(repo, opts, f"close #{n}", ["issue", "close", str(n), "--reason", reason.replace("-", " ")])


def cmd_publish(repo, opts):
    body, title = body_of(opts), (opts.get("title") or "").strip()
    if not title or not body:
        print("issues: publish needs --title and a --body-file that holds text")
        return 2
    args = ["issue", "create", "--title", title, "--body-file", "-"]
    for label in opts.get("label", []):
        args += ["--label", label]
    return write(repo, opts, f"publish \"{title}\"", args, body)


def cmd_question(repo, opts, n):
    body = body_of(opts)
    if not body:
        print("issues: question needs a --body-file that holds text")
        return 2
    return write(repo, opts, f"comment on #{n}", ["issue", "comment", str(n), "--body-file", "-"], body)


def cmd_revise(repo, opts, n):
    body = body_of(opts)
    if opts.get("fold"):
        why = (opts.get("why") or "").strip()
        issues = fetch(repo, opts) if why else None
        i = find(issues, n) if issues else None
        if not i:
            print("issues: revise --fold needs --why and the issue's current description")
            return 2
        body = folded(i["body"], why)
        if body is None:
            print(f"issues: #{n} is folded already")
            return 0
    if not body:
        print("issues: revise needs a --body-file that holds text, or --fold --why TEXT")
        return 2
    return write(repo, opts, f"new description of #{n}", ["issue", "edit", str(n), "--body-file", "-"], body)


# ---------- self-test --------------------------------------------------------------------------

def selftest():
    """A throwaway project and a planted tracker: every rule must be seen."""
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

    tmp = Path(tempfile.mkdtemp(prefix="issues-selftest-"))
    try:
        vdir = tmp / ".guidelines" / ".shortcuts" / ".virtual"
        vdir.mkdir(parents=True)
        (tmp / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
        (vdir / "ongoing.json").write_text(json.dumps({"schema": 1, "items": [
            {"id": "slow-pass", "title": "t", "state": "backlog"}]}), encoding="utf-8")
        feed = tmp / "feed.json"

        def tracker(*rows):
            feed.write_text(json.dumps({"issues": [
                {"number": n, "title": f"t{n}", "state": state, "created_at": "2026-11-01T00:00:00Z",
                 "updated_at": updated + "T00:00:00Z", "comments": 1, "labels": [{"name": "bug"}], "body": body}
                for n, state, updated, body in rows]}), encoding="utf-8")

        opts = {"json": str(feed)}
        body = "See `NOTES.md` and `gone/file.py`.\n- [x] a\n- [ ] b\n"
        tracker((1, "OPEN", "2026-11-02", body), (2, "OPEN", "2026-11-02", ""), (3, "CLOSED", "2026-11-02", ""))
        cases.append((virtual_dir(tmp) == vdir, "the verdicts sit beside the ledger"))
        code, out = run(cmd_check, tmp, vdir, opts)
        cases.append((code == 1 and out.count("UNTRIAGED") == 2 and "#3" not in out, "open issues without a verdict fail; closed ones are quiet"))
        rec = lambda verdict, n, **o: run(cmd_record, tmp, vdir, verdict, n, dict({"on": "2026-11-03"}, **o))
        cases.append((rec("ignore", 1)[0] == 2, "a verdict without --why is refused"))
        cases.append((rec("adopt", 1, why="w", to="nowhere")[0] == 2, "adopt refuses a ledger id the ledger lacks"))
        cases.append((rec("flatten", 2, why="w", to="MISSING.md")[0] == 2, "flatten refuses a note that is not a file"))
        cases.append((rec("adopt", 1, why="w", to="slow-pass")[0] == 0, "adopt records against a ledger item"))
        code, out = rec("flatten", 2, why="lesser", to="NOTES.md#notes")
        cases.append((code == 0 and "revise 2 --fold" in out, "flatten records and names the two acts that finish it"))
        code, out = run(cmd_check, tmp, vdir, opts)
        cases.append((code == 0 and "OPEN" in out and "untriaged 0 -> ok" in out, "triaged: ok, and a flattened issue still open is named"))
        cases.append((rec("ignore", 2, why="again")[0] == 0 and len(load_store(vdir)["issues"]) == 2
                      and "to" not in verdict_of(load_store(vdir), 2), "a new verdict replaces the old one"))
        tracker((1, "CLOSED", "2026-11-02", body), (2, "OPEN", "2026-11-09", ""))
        code, out = run(cmd_check, tmp, vdir, opts)
        cases.append(("CLOSED" in out and "slow-pass" in out, "an adopted issue closed while its ledger item stands"))
        cases.append(("MOVED" in out, "an issue that changed after its verdict"))
        (vdir / "ongoing.json").write_text('{"schema": 1, "items": []}', encoding="utf-8")
        tracker((1, "OPEN", "2026-11-02", body))
        code, out = run(cmd_check, tmp, vdir, opts)
        cases.append((code == 1 and "BROKEN" in out, "an adoption whose ledger item is gone fails"))
        cases.append((code == 1 and "ORPHAN" in out, "a verdict for an issue the tracker lacks fails"))
        code, out = run(cmd_status, tmp, vdir, opts, 1)
        cases.append((code == 0 and "50% - 1/2" in out and "labels: bug" in out, "status reads the checklist as a fraction"))
        cases.append((run(cmd_status, tmp, vdir, opts, 9)[0] == 2, "status of an unknown issue is refused"))
        code, out = run(cmd_measure, tmp, vdir, opts, 1)
        cases.append(("1 path(s) here: NOTES.md" in out and "gone/file.py" in out, "measure splits cited paths: here, absent"))
        gh_feed = tmp / "gh.json"
        gh_feed.write_text(json.dumps([{"number": 4, "title": "g", "state": "OPEN", "createdAt": "2026-11-01T00:00:00Z",
                                        "updatedAt": "2026-11-01T00:00:00Z", "comments": [{}, {}], "labels": []}]), encoding="utf-8")
        got = fetch(tmp, {"json": str(gh_feed)})
        cases.append((got[0]["comments"] == 2 and got[0]["open"], "gh's own JSON reads the same"))
        text = tmp / "body.md"
        text.write_text("Why here?\n", encoding="utf-8")
        code, out = run(cmd_question, tmp, {"body-file": str(text)}, 1)
        cases.append((code == 0 and "PLAN" in out and "| Why here?" in out and "not run" in out, "a tracker write without --yes is a plan"))
        cases.append((run(cmd_question, tmp, {}, 1)[0] == 2, "a comment without text is refused"))
        cases.append((run(cmd_publish, tmp, {"body-file": str(text)})[0] == 2, "publish without a title is refused"))
        cases.append((run(cmd_close, tmp, {"reason": "bored"}, 1)[0] == 2, "close takes two reasons only"))
        code, out = run(cmd_revise, tmp, dict(opts, fold=True, why="noted in NOTES.md"), 1)
        cases.append((code == 0 and "**Closed: lesser.** noted in NOTES.md" in out and FOLD_OPEN in out and "- [x] a" in out,
                      "revise --fold keeps the description under one line"))
        cases.append((folded(folded("x", "w"), "w") is None, "a folded description is not folded twice"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [name for ok, name in cases if not ok]
    for name in bad:
        print("MISS", name)
    print(f"issues selftest: {len(cases) - len(bad)}/{len(cases)} ok")
    return 1 if bad else 0


# ---------- entry ------------------------------------------------------------------------------

def main(argv):
    opts, pos, i = {"label": []}, [], 0
    while i < len(argv):
        a = argv[i]
        if a in ("--json", "--repo", "--to", "--why", "--on", "--reason", "--title", "--body-file") and i + 1 < len(argv):
            opts[a[2:]] = argv[i + 1]
            i += 2
        elif a == "--label" and i + 1 < len(argv):
            opts["label"].append(argv[i + 1])
            i += 2
        elif a in ("--yes", "--fold"):
            opts[a[2:]] = True
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a == "--selftest":
            return selftest()
        elif a.startswith("--"):
            print(f"issues: unknown option {a}")
            return 2
        else:
            pos.append(a)
            i += 1
    cmd = pos[0] if pos else "check"
    n = None
    if len(pos) > 1:
        if not pos[1].lstrip("#").isdigit():
            print(f"issues: '{pos[1]}' is not an issue number")
            return 2
        n = int(pos[1].lstrip("#"))
    repo = wire.repo_root(Path(opts["repo"]).resolve() if opts.get("repo") else None)
    vdir = virtual_dir(repo)
    if cmd == "check":
        return cmd_check(repo, vdir, opts)
    if cmd == "status":
        return cmd_status(repo, vdir, opts, n)
    if cmd == "publish":
        return cmd_publish(repo, opts)
    if cmd not in VERDICTS + ("measure", "close", "question", "revise"):
        print(f"issues: unknown verb '{cmd}'")
        return 2
    if n is None:
        print(f"issues: {cmd} needs an issue number")
        return 2
    if cmd in VERDICTS:
        return cmd_record(repo, vdir, cmd, n, opts)
    if cmd == "measure":
        return cmd_measure(repo, vdir, opts, n)
    return {"close": cmd_close, "question": cmd_question, "revise": cmd_revise}[cmd](repo, opts, n)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
