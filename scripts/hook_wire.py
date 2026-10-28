#!/usr/bin/env python3
"""hook_wire.py - the wire contract between Claude Code hook events and regency's hook scripts.

Every hook script imports this module and none of them parses stdin, walks for the project or prints
JSON by itself. One place owns:

  event      read the hook JSON from stdin (an unreadable event is an empty dict, never a crash)
  location   repository root, guidelines root (library/layouts.md §1), the .shortcuts/.virtual folder
  lineage    the virtual-path manifest and the slices that govern a file (library/virtualpath.md §2)
  state      session-scoped flags kept outside the repository (hazard watch)
  verbs      the Regent's verb table, read from library/conventions.md §9 (the only copy)
  answers    PreToolUse permission decisions and additionalContext lines, one slice line each (R4.1)
  failure    guards fail toward the Regent (ask); recorders fail silent (stderr only)
  fixture    the throw-away project every hook self-test runs against

Adoption gate: hooks that WRITE (lineage, journal) act only when the project already has
<guidelines>/.shortcuts/.virtual/. They never create guideline folders (library/layouts.md §1).

Pure standard library, Python 3.8+. Importing it writes nothing.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # an installed plugin runs from a cache that may be read-only

GUIDELINE_ROOTS = (".guidelines", "Docs/.guidelines", "docs/.guidelines")
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
STALE_MARK = "warn'STALE"
MAX_LINE = 600            # one slice line; Claude Code caps any hook string at 10 000 characters
UNIT = re.compile(r"\bM\d{2}(?:\.D\d{2}(?:\.T\d{2})?)?\b")
SKIP_PARTS = {".git", "node_modules", ".venv", "__pycache__", ".history", "discard", ".obsidian"}


# ---------- event ------------------------------------------------------------------------------

def read_event(stream=None):
    """The hook input as a dict; {} when stdin is empty or not JSON."""
    try:
        data = json.load(stream or sys.stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def tool_input(event):
    ti = event.get("tool_input")
    return ti if isinstance(ti, dict) else {}


def target_path(event):
    """The file a write tool is about to touch (or touched), absolute; None for other tools."""
    ti = tool_input(event)
    raw = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = Path(event.get("cwd") or os.getcwd()) / p
    return Path(os.path.normpath(str(p)))


def session_key(event):
    sid = str(event.get("session_id") or "nosession")
    return re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:64]


# ---------- location ---------------------------------------------------------------------------

def repo_root(start):
    """Nearest ancestor holding .git; else CLAUDE_PROJECT_DIR; else the start itself."""
    start = Path(start) if start else Path(os.getcwd())
    start = start if start.is_dir() else start.parent
    for p in [start] + list(start.parents):
        if (p / ".git").exists():
            return p
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else start


def event_repo(event):
    p = target_path(event)
    return repo_root(p.parent if p else Path(event.get("cwd") or os.getcwd()))


def guidelines_root(repo):
    for rel in GUIDELINE_ROOTS:
        g = Path(repo) / rel
        if g.is_dir():
            return g
    return None


def virtual_dir(repo):
    g = guidelines_root(repo)
    v = g / ".shortcuts" / ".virtual" if g else None
    return v if v and v.is_dir() else None


def rel_posix(path, repo):
    try:
        return Path(path).resolve().relative_to(Path(repo).resolve()).as_posix()
    except (ValueError, OSError):
        return None


# ---------- lineage ----------------------------------------------------------------------------

def manifest_entries(vdir):
    if not vdir:
        return []
    for p in sorted(vdir.glob("manifest*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            return [e for e in data.get("virtual_context", []) if isinstance(e, dict)]
        except (ValueError, OSError):
            return []
    return []


def governing(entries, rel):
    return [e for e in entries if rel in (e.get("refers_to") or [])]


# ---------- files ------------------------------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path, text):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def today():
    return datetime.date.today().isoformat()


def units_in(*texts):
    for t in texts:
        m = UNIT.search(t or "")
        if m:
            return m.group(0)
    return None


# ---------- session state (outside the repository) --------------------------------------------

def state_dir():
    base = os.environ.get("REGENCY_HOOK_STATE") or os.environ.get("CLAUDE_PLUGIN_DATA") \
        or os.path.join(tempfile.gettempdir(), "regency-hooks")
    d = Path(base) / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_file(event, name):
    return state_dir() / f"{session_key(event)}.{name}.json"


def load_state(event, name):
    p = state_file(event, name)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (ValueError, OSError):
        return None


def save_state(event, name, value):
    atomic_write(state_file(event, name), json.dumps(value))


def clear_state(event, name):
    p = state_file(event, name)
    if p.is_file():
        p.unlink()
        return True
    return False


# ---------- the Regent's verbs (library/conventions.md §9 is the only copy) ---------------------

CONVENTIONS = Path(__file__).resolve().parent.parent / "library" / "conventions.md"
RELEASE_COMMAND = "hook-hazard.py --clear"
MAX_ROUTED = 80  # characters: a longer message is prose, not an order


def verb_table(text):
    """[(phrase, meaning, command)] from the '## 9.' table, longest phrase first."""
    m = re.search(r"^## 9\..*?$(.*?)(?=^## \d+\.|\Z)", text, re.S | re.M)
    rows = []
    for line in (m.group(1) if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.lstrip().startswith("|") or len(cells) != 3 or cells[0] == "Says" or set(cells[0]) <= set("-: "):
            continue
        cmd = re.search(r"`([^`]+)`", cells[2])
        if not cmd:
            continue
        for phrase in cells[0].split(","):
            p = phrase.strip().lower()
            if p:
                rows.append((p, cells[1], cmd.group(1)))
    return sorted(rows, key=lambda r: -len(r[0]))


def regent_verbs():
    try:
        return verb_table(CONVENTIONS.read_text(encoding="utf-8"))
    except OSError:
        return []


HARNESS_BLOCK = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def regent_text(prompt):
    """The Regent's own words: some surfaces prepend <system-reminder> blocks (a timezone line, context) to
    the prompt a hook receives. They are the harness's, never the Regent's, so a verb can open the message
    behind them and a command quoted inside them confirms nothing."""
    return HARNESS_BLOCK.sub("", prompt or "").strip()


def opening_verb(prompt, table):
    """The (phrase, meaning, command) a short message opens with, or None. Slash commands never match."""
    p = re.sub(r"\s+", " ", (prompt or "").strip().lower())
    if not p or p.startswith("/") or len(p) > MAX_ROUTED:
        return None
    for row in table:
        if p == row[0] or re.match(rf"^{re.escape(row[0])}(?=$|[\s,.!:;?])", p):
            return row
    return None


def release_words(table=None):
    return [phrase for phrase, _, cmd in (regent_verbs() if table is None else table) if RELEASE_COMMAND in cmd]


# ---------- answers ----------------------------------------------------------------------------

def one_line(*parts):
    line = " · ".join(str(p) for p in parts if p)
    return line if len(line) <= MAX_LINE else line[: MAX_LINE - 1] + "…"


def permission(verdict, reason):
    """PreToolUse answer: verdict is 'deny' or 'ask' (allow = print nothing)."""
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": verdict,
                                   "permissionDecisionReason": one_line(reason)}}


def context(event_name, line):
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": one_line(line)}}


def emit(answer):
    if answer:
        sys.stdout.write(json.dumps(answer, ensure_ascii=False))
        sys.stdout.flush()


def serve(respond, guard=False):
    """Run one hook: read, respond, emit. Exit code is always 0 so the JSON decides.

    guard=True  (policy hooks): an internal error becomes an 'ask' carrying the error, so a broken
                guard hands the call to the Regent instead of letting it pass silently.
    guard=False (recorders): an internal error goes to stderr only; the session is never disturbed.
    """
    event = read_event()
    try:
        emit(respond(event))
    except Exception as e:  # noqa: BLE001 - a hook must never crash the session
        if guard and event.get("hook_event_name") == "PreToolUse":
            emit(permission("ask", f"regency guard error ({type(e).__name__}: {e}); the Regent decides this call"))
        else:
            sys.stderr.write(f"regency hook error: {type(e).__name__}: {e}\n")
    return 0


# ---------- self-test fixture ------------------------------------------------------------------

FIXTURE = {
    ".guidelines/.shortcuts/.virtual/manifest.json": json.dumps({"virtual_context": [
        {"virtual_path": ".decisions/ARCHITECTURE.md#layout-stable", "refers_to": ["src/Page.razor"],
         "selector_type": "markdown_anchor", "on_mutation": "mark_stale"},
        {"virtual_path": ".constraints/README.md#frozen-schema", "refers_to": ["db/schema.sql"],
         "selector_type": "markdown_anchor", "on_mutation": "lock"},
        {"virtual_path": ".plan/BACKLOG.md#ledger-x", "refers_to": ["src/Ledger.cs"],
         "selector_type": "ledger_row", "on_mutation": "mark_stale"}]}),
    ".guidelines/.shortcuts/.virtual/ongoing.json": json.dumps({"schema": 1, "updated": "2026-10-09", "items": [
        {"id": "M01.D01.T01", "title": "a", "state": "ongoing", "where": ["src/Page.razor"]},
        {"id": "M01.D01.T02", "title": "b", "state": "review"},
        {"id": "M01.D02.T01", "title": "c", "state": "blocked", "blocked_by": "RGN"},
        {"id": "M02", "title": "d", "state": "backlog"},
        {"id": "M03", "title": "e", "state": "backlog"}]}),
    ".guidelines/.decisions/ARCHITECTURE.md": "# Architecture\n\n## §layout-stable — layout\n\nRule text.\n\n## Other\n\nx\n",
    ".guidelines/.constraints/README.md": "# Constraints\n\n## frozen-schema\n\nNo change.\n",
    ".guidelines/.plan/BACKLOG.md": "| item | state |\n|---|---|\n| **ledger-x** | open |\n",
    ".guidelines/.plan/GATE_M01.md": "gate\n",
    ".guidelines/.plan/LADDER_PLAN_PART_1.md": "ladder\n",
    ".guidelines/.plan/HANDOFF_2026-10-01.md": "handoff\n",
    ".guidelines/.plan/RESUMING.md": "state\n",
    ".guidelines/.orders/ORD-0001/ORD-0001.xml": "<order/>\n",
    ".scope/brief.txt": "raw\n",
    "src/Page.razor": "<p>page</p>\n",
    "src/Ledger.cs": "class Ledger {}\n",
    "db/schema.sql": "create table t (id int);\n",
}


def build_fixture(root, with_virtual=True):
    """A minimal adopted project at root: .git, guidelines, manifest, ledger, acts, .scope."""
    root = Path(root)
    (root / ".git").mkdir(parents=True, exist_ok=True)
    for rel, text in FIXTURE.items():
        if not with_virtual and "/.virtual/" in rel:
            continue
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def check(cases):
    """Print one line per case and return the exit code: cases are (ok, label)."""
    bad = 0
    for ok, label in cases:
        if not ok:
            bad += 1
        print(f"{'pass' if ok else 'MISS'}  {label}")
    name = Path(sys.argv[0]).stem
    print(f"{name} selftest: {len(cases) - bad}/{len(cases)} ok")
    return 1 if bad else 0


if __name__ == "__main__":
    print(__doc__)
