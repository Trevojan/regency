#!/usr/bin/env python3
"""judge.py - the Judge (JD): the Regent's grants, where and how a hazardous act may run without asking.

hook-hazard.py asks the Regent before the hazardous local acts (conventions §5). A grant answers that ask
ahead of time, for named places and one or more kinds of act:

  how      delete, discard, history, layout             the kinds hook-hazard.py asks about and a grant may cover
  where    globs relative to the repository root        `Herança/**` (the folder itself too), `build/*.log`;
           or absolute                                   `**` is the whole repository; `*` crosses folders
  scope    session   this session only                  <state>/sessions/<sid>.grants.json
           repo      travels with the repository        <guidelines>/JD.md, else <repo>/JD.md
           machine   this repository, every session     ~/.claude/regency/JD.md
           <path>    a .md file the Regent names        listed in ~/.claude/regency/judge.json "sources"
  why      required: a grant without a reason grants nothing

An act is covered when every path it names matches a glob of one grant of its kind. An act that names no
path (git reset --hard, git rebase, git branch -D) or a path no script can resolve ("$d", a glob, a 'cd'
to an unknown place) needs `**`. Never grantable, so they keep asking or denying: installing system
software, destructive SQL, docker prunes and disk tools, cloud writes (conventions §6), pack consent (T5)
and a push to main (guard-push.py).

Only the Regent grants (conventions §1): a 'grant:' line in a message of theirs (hook-verbs.py) or their
answer to the Judge's pop-up (hook-judge.py). This script has no command that adds a grant. A file store is
fingerprinted in ~/.claude/regency/judge.json whenever a hook writes the Regent's grant into it; a store that
changed any other way (a pull, a hand edit, an agent's shell) reads STALE and grants nothing until the Regent
says 'ratify grants' (conventions §9) or approves `judge.py ratify --yes`, which hook-hazard.py asks for.

Modes:
  list   [--repo DIR]                     the file grants that reach this repository; STALE stores named
  check  <kind> <path>... [--repo DIR]    the grant that covers the act, or the grant line the Judge proposes
  revoke <id> [--repo DIR]                remove one grant (narrowing needs nobody)
  ratify [--yes] [--repo DIR]             without --yes: the review of each STALE store; with it: record them
  --selftest
Pure standard library, Python 3.8+.
"""
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402

KINDS = ("delete", "discard", "history", "layout")
NOT_ASKED = {"edit", "write", "move", "rename", "create"}
NEVER = {"install": "installing system software always asks (conventions §5)",
         "cloud": "a cloud write runs only on the exact command the Regent quotes (conventions §6)",
         "consent": "consent to run a pack's hooks is the Regent's alone, each time (T5)",
         "push": "a push to main is the Regent's (guard-push.py)"}
SCOPE_WORDS = {"session": "session", "this session": "session", "repo": "repo", "repository": "repo",
               "this repo": "repo", "machine": "machine", "this machine": "machine", "permanent": "machine"}
LETTER = {"session": "S", "repo": "R", "machine": "M", "path": "P"}
STORE_NAME = "JD.md"
BEGIN, END = "<!-- jd:grants -->", "<!-- /jd:grants -->"
COLUMNS = ("id", "how", "where", "repo", "why", "by", "at")
GRANT_LINE = re.compile(r"(?im)^[ \t>*`-]*grant:[ \t]*(.+?)[ \t`]*$")
SKELETON = f"""# JD — the Regent's grants

Where and how a hazardous act may run without asking (`library/judge.md`). regency's hooks write these rows
from the Regent's own words; an agent never does. A hand edit is the Regent's to make: say `ratify grants`
after it, or this table grants nothing.

{BEGIN}
| {' | '.join(COLUMNS)} |
|{'---|' * len(COLUMNS)}
{END}
"""


# ---------- paths ------------------------------------------------------------------------------

def norm(s):
    """One spelling per path: composed accents (NFC), forward slashes, case folded where the file system folds."""
    s = unicodedata.normalize("NFC", str(s)).replace("\\", "/")
    return s.casefold() if os.name == "nt" else s


def is_absolute_path(s):
    return s.startswith("/") or bool(re.match(r"^[A-Za-z]:/", s))


def matches(path, glob):
    """path: relative to the repository root (posix) or absolute; glob likewise. '**' is the whole repository."""
    p, g = norm(path).rstrip("/"), norm(glob).rstrip("/")
    if is_absolute_path(g) != is_absolute_path(p):
        return False
    if g == "**":
        return True  # p is relative here: the line above kept absolute paths out of reach
    return fnmatch.fnmatchcase(p, g) or (g.endswith("/**") and p == g[:-3])


def relative(path, repo):
    """The act's path as a grant reads it: relative posix inside the repository ('' = its root), else absolute."""
    try:
        return Path(os.path.normpath(str(path))).relative_to(Path(os.path.normpath(str(repo)))).as_posix().strip(".")
    except ValueError:
        return Path(os.path.normpath(str(path))).as_posix()


# ---------- the Regent's grant lines -----------------------------------------------------------

def parse_spec(text):
    """{'how', 'where', 'scope', 'path', 'why'} for '<how>[,<how>] <where>... [for <scope>] -- <why>';
    raises ValueError naming what is missing."""
    m = re.match(r"^(.*?)\s+(?:--|—)\s+(\S.*)$", (text or "").strip())
    if not m:
        raise ValueError("no reason: a grant ends with '-- <why>'")
    head, why = m.group(1).strip(), m.group(2).strip().strip("`").strip()
    scope, path = "session", None
    body, sep, target = head.rpartition(" for ")
    if sep:
        head, raw = body.strip(), target.strip().strip("`").strip()
        word = SCOPE_WORDS.get(raw.lower())
        if word:
            scope = word
        elif "/" in raw or "\\" in raw or raw.lower().endswith(".md"):
            if not raw.lower().endswith(".md"):
                raise ValueError(f"'{raw}': a grant file the Regent names is a .md file")
            scope, path = "path", raw
        else:
            raise ValueError(f"'{raw}': the scope is session, repo, machine or a .md path")
    tokens = [t for t in re.split(r"[\s,]+", head) if t]
    how = []
    while tokens and tokens[0].strip("`").lower() in set(KINDS) | NOT_ASKED | set(NEVER):
        how.append(tokens.pop(0).strip("`").lower())
    for k in how:
        if k in NOT_ASKED:
            raise ValueError(f"'{k}': regency asks before no {k}, so there is nothing to grant")
        if k in NEVER:
            raise ValueError(f"'{k}' is never granted: {NEVER[k]}")
    if not how:
        raise ValueError(f"no kind: start with one of {', '.join(KINDS)}")
    where = [t.strip("`") for t in tokens if t.strip("`")]
    if not where:
        raise ValueError("no place: name the globs the grant covers ('**' is the whole repository)")
    for g in where:
        if "|" in g:
            raise ValueError(f"'{g}': a glob holds no '|'")
        if not is_absolute_path(norm(g)) and ".." in norm(g).split("/"):
            raise ValueError(f"'{g}': a relative glob stays inside the repository (no '..'); write it absolute")
    return {"how": sorted(set(how), key=KINDS.index), "where": where, "scope": scope, "path": path, "why": why}


def grant_lines(prompt):
    """The specs of every line of the Regent's message that opens with 'grant:'."""
    return [m.group(1) for m in GRANT_LINE.finditer(wire.regent_text(prompt))]


# ---------- stores -----------------------------------------------------------------------------

def judge_home():
    return Path(os.environ.get("REGENCY_JUDGE_HOME") or Path.home() / ".claude" / "regency")


def record_file():
    return judge_home() / "judge.json"


def load_record():
    try:
        data = json.loads(record_file().read_text(encoding="utf-8"))
        return {"stores": dict(data.get("stores", {})), "sources": list(data.get("sources", []))}
    except (OSError, ValueError, AttributeError):
        return {"stores": {}, "sources": []}


def save_record(rec):
    record_file().parent.mkdir(parents=True, exist_ok=True)
    wire.atomic_write(record_file(), json.dumps(rec, indent=2, ensure_ascii=False) + "\n")


def key(path):
    return norm(os.path.normpath(str(Path(path).expanduser().absolute())))


def repo_store(repo):
    return (wire.guidelines_root(repo) or Path(repo)) / STORE_NAME


def machine_store():
    return judge_home() / STORE_NAME


def sources():
    extra = [p for p in os.environ.get("REGENCY_JD", "").split(os.pathsep) if p.strip()]
    return [Path(p).expanduser() for p in load_record()["sources"] + extra]


def file_stores(repo):
    out = [("repo", repo_store(repo)), ("machine", machine_store())] + [("path", p) for p in sources()]
    seen, unique = set(), []
    for scope, p in out:
        if key(p) not in seen:
            seen.add(key(p))
            unique.append((scope, p))
    return unique


def block(text):
    m = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), text or "", re.S)
    return m.group(1).replace("\r\n", "\n").strip() if m else None


def fingerprint(text):
    return hashlib.sha256((block(text) or "").encode("utf-8")).hexdigest()


def rows(text):
    out = []
    for line in (block(text) or "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != len(COLUMNS) or cells[0] == "id" or set(cells[0]) <= set("-: "):
            continue
        r = dict(zip(COLUMNS, cells))
        r["how"] = [k.strip().lower() for k in r["how"].split(",") if k.strip()]
        r["where"] = [g.strip().strip("`") for g in r["where"].split(",") if g.strip().strip("`")]
        out.append(r)
    return out


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def state(path):
    """'absent' (no file or no rows), 'ok' (as the hooks or the Regent's ratification left it) or 'STALE'."""
    text = read(path)
    if text is None or not rows(text):
        return "absent"
    return "ok" if load_record()["stores"].get(key(path)) == fingerprint(text) else "STALE"


def applies(cell, scope, repo):
    c = (cell or "").strip()
    return (c == "." and scope == "repo") or c == "*" or (c != "." and norm(c) == key(repo))


def render(text, new_rows):
    lines = "\n".join(f"| {' | '.join(cells)} |" for cells in new_rows)
    table = f"| {' | '.join(COLUMNS)} |\n|{'---|' * len(COLUMNS)}" + (f"\n{lines}" if lines else "")
    base = text if text and BEGIN in text and END in text else (text.rstrip() + "\n\n" + SKELETON.split("\n\n", 2)[2]
                                                                if text else SKELETON)
    return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: f"{BEGIN}\n{table}\n{END}", base, flags=re.S)


def cells(r):
    return [r["id"], ", ".join(r["how"]), ", ".join(f"`{g}`" for g in r["where"]), r["repo"], r["why"], r["by"], r["at"]]


def next_id(letter, taken):
    nums = [int(m.group(1)) for t in taken for m in [re.match(rf"^JD-{letter}(\d+)$", t)] if m]
    return f"JD-{letter}{max(nums, default=0) + 1:02d}"


def store_path(spec, repo):
    if spec["scope"] == "repo":
        return repo_store(repo)
    if spec["scope"] == "machine":
        return machine_store()
    p = Path(spec["path"]).expanduser()
    return p if p.is_absolute() else Path(repo) / p


def record(event, repo, spec, by):
    """Write the Regent's grant where the spec says; returns (id, where it went). ValueError when it cannot."""
    if isinstance(spec, str):
        spec = parse_spec(spec)
    row = {"how": spec["how"], "where": spec["where"], "why": spec["why"].replace("|", "/"), "by": by,
           "at": wire.today()}
    letter = LETTER[spec["scope"]]
    if spec["scope"] == "session":
        st = wire.load_state(event, "grants") or {"grants": []}
        row.update(id=next_id(letter, [g["id"] for g in st["grants"]]), repo=key(repo))
        st["grants"].append(row)
        wire.save_state(event, "grants", st)
        return row["id"], "this session"
    path = store_path(spec, repo)
    if state(path) == "STALE":
        raise ValueError(f"{path} changed since the Regent last ratified it: say 'ratify grants' first "
                         "(review: judge.py ratify)")
    text = read(path)
    current = rows(text) if text else []
    row.update(id=next_id(letter, [r["id"] for r in current]), repo="." if spec["scope"] == "repo" else key(repo))
    new = render(text, [cells(r) for r in current] + [cells(row)])
    path.parent.mkdir(parents=True, exist_ok=True)
    wire.atomic_write(path, new)
    rec = load_record()
    rec["stores"][key(path)] = fingerprint(new)
    if spec["scope"] == "path" and key(path) not in {key(s) for s in rec["sources"]}:
        rec["sources"].append(str(path))
    save_record(rec)
    return row["id"], f"{spec['scope']} {path}"


def grants(event, repo):
    """Every grant in force for this repository: session ones and the rows of each store that reads ok."""
    out = [dict(g, store="session") for g in (wire.load_state(event, "grants") or {}).get("grants", [])
           if g.get("repo") in (key(repo), "*")]
    for scope, path in file_stores(repo):
        if state(path) == "ok":
            out += [dict(r, store=f"{scope} {path}") for r in rows(read(path)) if applies(r["repo"], scope, repo)]
    return out


def stale(repo):
    return [p for _, p in file_stores(repo) if state(p) == "STALE"]


def covers(event, repo, kind, paths):
    """The grant that lets this act run without asking, or None. paths: absolute paths, None for one no script
    could resolve; an empty list means the act names no path."""
    if kind not in KINDS or paths is None:
        return None
    want = ["**" if p is None else relative(p, repo) for p in paths] or ["**"]
    for g in grants(event, repo):
        if kind not in g.get("how", []) or not g.get("why"):
            continue
        if all(any((w == "**" and gl == "**") or (w != "**" and (matches(w, gl) or (w == "" and gl == "**")))
                   for gl in g["where"]) for w in want):
            return g
    return None


def propose(kind, paths, repo):
    """The grant line the Judge puts before the Regent for an act no grant covers."""
    globs = []
    for p in paths or [None]:
        r = "**" if p is None else relative(p, repo)
        g = "**" if r in ("", "**") else (r.rstrip("/") + "/**" if Path(p).is_dir() else r)
        if g not in globs:
            globs.append(g)
    return f"grant: {kind} {' '.join(globs)} for session -- <why>"


def revoke(event, repo, gid):
    """Remove one grant; returns where it was, or None. A STALE store is the Regent's to ratify first."""
    st = wire.load_state(event, "grants") or {"grants": []}
    if any(g["id"] == gid for g in st["grants"]):
        st["grants"] = [g for g in st["grants"] if g["id"] != gid]
        wire.save_state(event, "grants", st)
        return "this session"
    for scope, path in file_stores(repo):
        text = read(path)
        current = rows(text) if text else []
        if not any(r["id"] == gid for r in current):
            continue
        if state(path) == "STALE":
            raise ValueError(f"{path} is STALE: the Regent ratifies it or edits it by hand")
        new = render(text, [cells(r) for r in current if r["id"] != gid])
        wire.atomic_write(path, new)
        rec = load_record()
        rec["stores"][key(path)] = fingerprint(new)
        save_record(rec)
        return f"{scope} {path}"
    return None


def ratify(repo, yes=False):
    """One line per STALE store: its rows as they stand; with yes, they are recorded as the Regent's."""
    out = []
    rec = load_record()
    for scope, path in file_stores(repo):
        if state(path) != "STALE":
            continue
        rs = rows(read(path))
        out.append(f"{'ratified' if yes else 'STALE'} {scope} {path}: " +
                   "; ".join(f"{r['id']} {', '.join(r['how'])} {', '.join(r['where'])} ({r['repo']}) -- {r['why']}"
                             for r in rs))
        if yes:
            rec["stores"][key(path)] = fingerprint(read(path))
    if yes and out:
        save_record(rec)
    return out


def is_store(path):
    """True for a file only the Regent's words may change: a JD.md, the fingerprint record, a named source."""
    p = Path(path)
    if p.name == STORE_NAME or p.name.endswith(".grants.json"):
        return True
    k = key(p)
    return k == key(record_file()) or k in {key(s) for s in sources()}


STORE_NAMES = (STORE_NAME, "judge.json", ".grants.json")


# ---------- command line -----------------------------------------------------------------------

def line(g):
    return f"{g['id']} · {', '.join(g['how'])} · {', '.join(g['where'])} · {g['store']} · {g['why']}"


def main(argv):
    repo_arg = argv[argv.index("--repo") + 1] if "--repo" in argv else None
    repo = wire.repo_root(Path(repo_arg) if repo_arg else Path.cwd())
    args = [a for i, a in enumerate(argv) if a != "--repo" and (i == 0 or argv[i - 1] != "--repo")]
    mode = args[0] if args else "list"
    if mode == "list":
        found = grants({}, repo)
        for g in found:
            print(line(g))
        for p in stale(repo):
            print(f"STALE {p}: grants nothing until the Regent says 'ratify grants'")
        print(f"judge: {len(found)} file grant(s) for {repo}; session grants live with the session's hooks")
        return 0
    if mode == "check" and len(args) >= 3:
        kind = args[1]
        paths = [Path(os.path.normpath(str(Path.cwd() / a))) for a in args[2:]]
        g = covers({}, repo, kind, paths)
        print(f"covered by {line(g)}" if g else f"no file grant covers it; the Judge proposes: {propose(kind, paths, repo)}")
        return 0 if g else 1
    if mode == "revoke" and len(args) == 2:
        try:
            where = revoke({}, repo, args[1])
        except ValueError as e:
            print(f"not revoked: {e}")
            return 1
        print(f"revoked {args[1]} from {where}" if where else f"{args[1]}: no file grant has this id")
        return 0 if where else 1
    if mode == "ratify":
        out = ratify(repo, yes="--yes" in args)
        for o in out:
            print(o)
        print(f"judge: {len(out)} store(s) {'ratified' if '--yes' in args else 'STALE; ratify with --yes'}" if out
              else "judge: no STALE store")
        return 0
    print(__doc__)
    return 2


# ---------- self-test --------------------------------------------------------------------------

def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        os.environ["REGENCY_JUDGE_HOME"] = str(Path(tmp) / "home" / ".claude" / "regency")
        os.environ.pop("REGENCY_JD", None)
        root = wire.build_fixture(Path(tmp) / "proj")
        other = wire.build_fixture(Path(tmp) / "other")
        folder = root / unicodedata.normalize("NFC", "Herança")
        (folder / "old").mkdir(parents=True)
        ev, ev2 = {"session_id": "s1"}, {"session_id": "s2"}
        cases = []

        def err(text):
            try:
                parse_spec(text)
                return ""
            except ValueError as e:
                return str(e)

        s = parse_spec("delete, discard `Herança/**` build/** for repo -- cleanup of the old layout")
        cases.append((s["how"] == ["delete", "discard"] and s["where"] == ["Herança/**", "build/**"] and s["scope"] == "repo"
                      and s["why"] == "cleanup of the old layout", f"spec parsed: {s}"))
        cases.append((parse_spec("delete x/** -- y")["scope"] == "session", "no scope: the narrowest, this session"))
        cases.append(("no reason" in err("delete x/**"), "no reason, no grant"))
        cases.append(("nothing to grant" in err("edit x/** -- y"), "edit: regency asks nothing, so nothing to grant"))
        cases.append(("never granted" in err("install ** -- y"), "install is never granted"))
        cases.append(("scope" in err("delete x/** for everyone -- y"), "an unknown scope is refused"))
        cases.append(("'..'" in err("delete ../x -- y"), "a relative glob cannot leave the repository"))
        cases.append(("no place" in err("delete -- y"), "a grant names its place"))
        cases.append((parse_spec("delete x/** for notes/GRANTS.md -- y")["scope"] == "path", "a .md path the Regent names"))
        cases.append((grant_lines("<system-reminder>\ngrant: delete ** -- x\n</system-reminder>ok\n> grant: delete a/** -- b\n"
                                  "please grant: nothing") == ["delete a/** -- b"],
                      "grant lines: the Regent's own lines only, never inside a harness reminder"))

        rm = [folder / "old"]
        cases.append((covers(ev, root, "delete", rm) is None, "no grant: the act is not covered"))
        gid, where = record(ev, root, "delete Herança/** -- the old layout", "Regent: message")
        cases.append((gid == "JD-S01" and where == "this session", f"session grant recorded: {gid}"))
        cases.append((covers(ev, root, "delete", rm) is not None, "covered inside the glob"))
        cases.append((covers(ev, root, "delete", [folder]) is not None, "'X/**' covers the folder X itself"))
        decomposed = root / unicodedata.normalize("NFD", "Herança") / "old"
        cases.append((covers(ev, root, "delete", [decomposed]) is not None, "an accent spelled decomposed still matches"))
        cases.append((covers(ev, root, "delete", [root / "src" / "Page.razor"]) is None, "a path outside every glob asks"))
        cases.append((covers(ev, root, "delete", [folder / "old", root / "src"]) is None, "every path must be covered"))
        cases.append((covers(ev, root, "discard", rm) is None, "another kind is not covered"))
        cases.append((covers(ev, root, "delete", []) is None and covers(ev, root, "delete", [None]) is None,
                      "no path, or an unresolvable one, needs '**'"))
        cases.append((covers(ev2, root, "delete", rm) is None, "a session grant stays in its session"))
        cases.append((covers(ev, other, "delete", [other / "Herança"]) is None, "a session grant stays in its repository"))
        cases.append((covers(ev, root, "delete", None) is None, "an act no grant may cover (SQL, disk) is never covered"))

        gid, where = record(ev, root, "history ** for repo -- rebase the plumbing branch freely", "Regent: pop-up")
        store = root / ".guidelines" / "JD.md"
        cases.append((gid == "JD-R01" and store.is_file() and state(store) == "ok", f"repo grant in {where}"))
        cases.append((covers(ev2, root, "history", []) is not None, "a repo grant reaches every session"))
        cases.append((covers(ev2, other, "history", []) is None, "a repo grant stays in its repository"))
        store.write_text(store.read_text(encoding="utf-8").replace(
            END, "| JD-R09 | delete | `**` | . | planted | agent | 2026-10-29 |\n" + END), encoding="utf-8")
        cases.append((state(store) == "STALE" and covers(ev2, root, "history", []) is None
                      and covers(ev2, root, "delete", [root / "db"]) is None,
                      "a store changed outside the hooks is STALE and grants nothing"))
        cases.append(("ratify" in str(_raises(record, ev, root, "delete x/** for repo -- y", "R")),
                      "no new grant lands on a STALE store"))
        review = ratify(root)
        cases.append((len(review) == 1 and "JD-R09" in review[0] and state(store) == "STALE", "ratify without yes: review only"))
        ratify(root, yes=True)
        cases.append((state(store) == "ok" and covers(ev2, root, "delete", [root / "db"]) is not None,
                      "the Regent's ratification makes the store grant again"))

        gid, where = record(ev, root, "layout ** for machine -- worktrees for the speed modes", "Regent: message")
        cases.append((gid == "JD-M01" and covers(ev2, root, "layout", []) is not None
                      and covers(ev2, other, "layout", []) is None, "machine grant: this repository, every session"))
        gid, where = record(ev, root, f"discard src/** for {Path(tmp) / 'notes' / 'GRANTS.md'} -- scratch edits",
                            "Regent: message")
        cases.append((gid == "JD-P01" and covers(ev2, root, "discard", [root / "src" / "Page.razor"]) is not None
                      and any(key(p) == key(Path(tmp) / "notes" / "GRANTS.md") for p in sources()),
                      "a grant file the Regent names is listed and read"))
        outside = Path(tmp) / "scratch" / "x"
        record(ev, root, f"delete {Path(tmp).as_posix()}/scratch/** -- scratch", "Regent: message")
        cases.append((covers(ev, root, "delete", [outside]) is not None, "an absolute glob covers a path outside"))
        cases.append((covers(ev, root, "delete", [Path(tmp) / "elsewhere"]) is None
                      and not matches("/abs/x", "**"), "'**' never reaches outside the repository"))
        cases.append((revoke(ev, root, "JD-S01") == "this session" and "JD-S01" not in {g["id"] for g in grants(ev, root)}
                      and revoke(ev, root, "JD-S99") is None, "revoke removes one grant; an unknown id removes nothing"))
        cases.append((revoke(ev, root, "JD-M01").startswith("machine") and state(machine_store()) == "absent"
                      and covers(ev2, root, "layout", []) is None, "revoking from a store keeps it ratified"))
        cases.append((is_store(store) and is_store(record_file()) and is_store(Path(tmp) / "notes" / "GRANTS.md")
                      and not is_store(root / "README.md"), "the stores only the Regent's words change"))
        cases.append((propose("delete", [folder, root / "a.txt"], root) == "grant: delete Herança/** a.txt for session -- <why>"
                      and propose("history", [], root).startswith("grant: history ** "), "the Judge's proposal line"))
        if os.name != "nt":
            cases.append((matches("Herança/old", "Herança\\**".replace("\\", "/")) and norm("a\\b") == "a/b",
                          "backslashes read as slashes"))
        return wire.check(cases)


def _raises(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return e
    return ""


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else main(a))
