#!/usr/bin/env python3
"""hook-reads.py - PostToolUse Read: one row per file read, so a re-read of unchanged content can be counted.

library/shortcuts.md §8 and library/hooks.md §3. In an adopted project (one with .shortcuts/.virtual/), every
Read of a file inside the repository adds a row to the `reads` table of the one store (<virtual>/index.sqlite):
the session, the agent, the path, the file's sha256, which lines the call returned and their size in bytes.
scripts/reconstruction.py turns the rows into the context-reconstruction ratio: how much of what a session reads
was read, unchanged, by an earlier session (/regency:measure-context-reconstruction).

The row holds no text: a hash and counts. The table keeps the latest KEEP rows.

A recorder: never blocks, never answers, errors go to stderr only (hook_wire.serve). Wired async.

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
import idx  # noqa: E402  (connect(): the one store)

SQL = """
CREATE TABLE IF NOT EXISTS reads(session TEXT NOT NULL, agent TEXT NOT NULL, path TEXT NOT NULL,
  sha256 TEXT NOT NULL, l0 INTEGER NOT NULL, l1 INTEGER NOT NULL, bytes INTEGER NOT NULL, at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS reads_print ON reads(path, sha256);
CREATE INDEX IF NOT EXISTS reads_session ON reads(session);
"""
KEEP = 50000
READ_LIMIT = 2000  # the Read tool's default line count


def part(raw, ti):
    """(first line, last line, bytes) of what one Read returned: offset and limit as the tool takes them."""
    pieces = raw.split(b"\n")  # lines as the Read tool counts them: on LF only, each with its end
    lines = [x + b"\n" for x in pieces[:-1]] + ([pieces[-1]] if pieces[-1] else [])
    try:
        start = max(int(ti.get("offset") or 1), 1)
        count = max(int(ti.get("limit") or READ_LIMIT), 1)
    except (TypeError, ValueError):
        start, count = 1, READ_LIMIT
    chunk = lines[start - 1:start - 1 + count]
    return start, start - 1 + len(chunk), sum(len(c) for c in chunk)


def respond(event):
    if event.get("hook_event_name") not in (None, "PostToolUse") or event.get("tool_name") != "Read":
        return None
    path = wire.target_path(event)
    if path is None or not path.is_file():
        return None
    repo = wire.repo_root(path.parent)
    vdir = wire.virtual_dir(repo)
    rel = wire.rel_posix(path, repo)
    if vdir is None or rel is None or "/.shortcuts/.virtual/" in "/" + rel:
        return None
    raw = path.read_bytes()
    l0, l1, size = part(raw, wire.tool_input(event))
    con = idx.connect(vdir, create=True)
    with con:
        con.executescript(SQL)
        con.execute("INSERT INTO reads VALUES(?,?,?,?,?,?,?,?)",
                    (wire.session_key(event), event.get("agent_type") or "main", rel,
                     hashlib.sha256(raw).hexdigest(), l0, l1, size, wire.now()))
        con.execute("DELETE FROM reads WHERE rowid <= (SELECT MAX(rowid) FROM reads) - ?", (KEEP,))
    con.close()
    return None


def rows(root):
    con = idx.connect(wire.virtual_dir(root))
    if con is None:
        return []
    try:
        return [tuple(r) for r in con.execute("SELECT session, agent, path, l0, l1, bytes FROM reads ORDER BY rowid")]
    except Exception:  # noqa: BLE001 - no table yet reads as no rows
        return []
    finally:
        con.close()


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        doc = root / ".guidelines/.decisions/ARCHITECTURE.md"

        def read(base, target, sid="s1", **ti):
            return respond({"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": sid,
                            "cwd": str(base), "tool_input": dict({"file_path": str(target)}, **ti)})

        cases = []
        out = read(root, doc)
        got = rows(root)
        size = len(doc.read_bytes())
        cases.append((out is None and got == [("s1", "main", ".guidelines/.decisions/ARCHITECTURE.md", 1, 9, size)],
                      "a whole read: one row, the lines and bytes it returned, no answer"))
        read(root, doc, "s1", offset=3, limit=2)
        cases.append((rows(root)[-1][3:] == (3, 4, len("## §layout-stable — layout\n\n".encode("utf-8"))),
                      "offset and limit: only the lines the call returned are counted"))
        respond({"hook_event_name": "PostToolUse", "tool_name": "Edit", "cwd": str(root),
                 "tool_input": {"file_path": str(doc)}})
        cases.append((len(rows(root)) == 2, "other tools: ignored"))
        read(root, root / ".guidelines/.shortcuts/.virtual/ongoing.json")
        cases.append((len(rows(root)) == 2, "the store's own folder: not recorded"))
        read(bare, bare / "src/Page.razor")
        cases.append((not (bare / ".guidelines/.shortcuts").exists(), "adoption gate: nothing written without .virtual"))
        read(root, root / "nowhere.txt")
        cases.append((len(rows(root)) == 2, "a missing file: nothing recorded"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond))
