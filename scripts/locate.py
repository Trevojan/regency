#!/usr/bin/env python3
"""locate.py - where a word lives: a contentless SQLite FTS5 index over the project's structural nodes.

library/shortcuts.md §7. Written for the harness: before a broad grep, ask the index where a term lives and get
locations back - path, the line of the first hit, the node's range and id, its section chain - never the text.
The text stays in the files (the index points, it never copies): the FTS5 table is contentless, so the store
holds the inverted index and the node rows only.

  rows     one per structural node of scripts/idx.py's parser, holding only the node's OWN lines (the lines no
           child node holds), so every line is indexed once and a hit names the deepest node holding it
  store    the one store, <virtual>/index.sqlite: tables search (FTS5), search_rows, search_files; idx.py build
           clears none of them
  fresh    every query first compares each candidate file's size and mtime with what was indexed and re-parses
           only the files that moved; a removed file leaves the index
  fallback no FTS5 in this Python's SQLite, or no .shortcuts/.virtual here -> one JSON line naming the rg command
           to run instead, exit 3

Modes:  index [--guidelines-only] · query TERMS... [--path PREFIX] [--limit N] [--any] [--raw] · --selftest
        (each mode takes --repo DIR)
Pure standard library (sqlite3), Python 3.8+.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402
import idx  # noqa: E402  (parse(): the same nodes and ids as the exact index; connect(): the one store)

SCHEMA_ROWS = """
CREATE TABLE IF NOT EXISTS search_rows(rowid INTEGER PRIMARY KEY, path TEXT NOT NULL, node TEXT NOT NULL,
  l0 INTEGER NOT NULL, l1 INTEGER NOT NULL, chain TEXT);
CREATE INDEX IF NOT EXISTS search_rows_path ON search_rows(path);
CREATE TABLE IF NOT EXISTS search_files(path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL, rows INTEGER NOT NULL, at TEXT NOT NULL);
"""
TOKENIZERS = ("unicode61 remove_diacritics 2", "unicode61")
LIMIT = 20
LABEL = 60
TERM = re.compile(r"[\w*]+", re.U)


class NoIndex(RuntimeError):
    """FTS5 or the store is missing here: the caller falls back to rg."""


def fts5_ok():
    try:
        sqlite3.connect(":memory:").execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        return True
    except sqlite3.Error:
        return False


def open_store(repo):
    vdir = wire.virtual_dir(repo)
    if vdir is None:
        raise NoIndex("no .shortcuts/.virtual under a guidelines root here (library/virtualpath.md §4)")
    if not fts5_ok():
        raise NoIndex(f"this Python's SQLite {sqlite3.sqlite_version} has no FTS5")
    con = idx.connect(vdir, create=True)
    con.executescript(SCHEMA_ROWS)
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='search'").fetchone() is None:
        for tok, extra in [(t, e) for t in TOKENIZERS for e in (", contentless_delete=1", "")]:
            try:
                con.execute(f"CREATE VIRTUAL TABLE search USING fts5(text, content='', tokenize='{tok}'{extra})")
                con.execute("INSERT OR REPLACE INTO meta VALUES('search_delete', ?)", ("rows" if extra else "rebuild",))
                break
            except sqlite3.OperationalError:
                continue
    return con, vdir


def own_rows(rel, raw):
    """[(node id, l0, l1, chain, text)] - each node with the lines no child of it holds (1-based, inclusive)."""
    nodes, _ = idx.parse(rel, raw, light=True)
    lines = raw.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    owner = {}
    for nd in sorted(nodes, key=lambda n: n["depth"]):
        for x in range(nd["l0"], min(nd["l1"], len(lines))):
            owner[x] = nd["id"]
    by_id = {nd["id"]: nd for nd in nodes}

    def name(nd):
        if nd["kind"] == "file":
            return ""
        at = nd["key_line"] if nd.get("key_line") is not None else nd["l0"]
        text = nd.get("label") or (lines[at] if at < len(lines) else "")
        return " ".join(text.split())[:LABEL]

    def chain(nd):
        parts = []
        while nd is not None:
            if name(nd):
                parts.append(name(nd))
            nd = by_id.get(nd["parent_id"])
        return " > ".join(reversed(parts))

    own = {}
    for x, nid in owner.items():
        own.setdefault(nid, []).append(lines[x])
    out = []
    for nid, body in own.items():
        text = "\n".join(body).strip()
        if text:
            nd = by_id[nid]
            out.append((nid, nd["l0"] + 1, max(nd["l1"], nd["l0"] + 1), chain(nd), text))
    return out


def candidates(repo, vdir, guidelines_only):
    return idx.candidates(repo, Path(vdir).parent.parent, wire.manifest_entries(vdir), guidelines_only)


def drop(con, rel):
    ids = [r[0] for r in con.execute("SELECT rowid FROM search_rows WHERE path=?", (rel,))]
    if ids:
        con.executemany("DELETE FROM search WHERE rowid=?", [(i,) for i in ids])
        con.execute("DELETE FROM search_rows WHERE path=?", (rel,))
    con.execute("DELETE FROM search_files WHERE path=?", (rel,))


def put(con, repo, rel, st):
    raw = idx.text_bytes(repo / rel)
    rows = own_rows(rel, raw) if raw is not None else []  # a binary file is recorded with no rows: never re-read
    for nid, l0, l1, chain, text in rows:
        cur = con.execute("INSERT INTO search_rows(path, node, l0, l1, chain) VALUES(?,?,?,?,?)", (rel, nid, l0, l1, chain))
        con.execute("INSERT INTO search(rowid, text) VALUES(?, ?)", (cur.lastrowid, text))
    con.execute("INSERT OR REPLACE INTO search_files VALUES(?,?,?,?,?,?)",
                (rel, hashlib.sha256(raw or b"").hexdigest(), st.st_size, st.st_mtime_ns, len(rows), wire.now()))
    return len(rows)


def refresh(con, repo, vdir, guidelines_only=None):
    """Bring the index level with the files; returns (files indexed, files re-parsed, scope)."""
    scope = guidelines_only
    if scope is None:
        row = con.execute("SELECT v FROM meta WHERE k='search_scope'").fetchone()
        scope = bool(row and row[0] == "guidelines")
    known = {r["path"]: (r["bytes"], r["mtime_ns"]) for r in con.execute("SELECT path, bytes, mtime_ns FROM search_files")}
    want = candidates(repo, vdir, scope)
    moved = []
    for rel in want:
        try:
            st = (repo / rel).stat()
        except OSError:
            continue
        if known.get(rel) != (st.st_size, st.st_mtime_ns):
            moved.append((rel, st))
    gone = sorted(set(known) - set(want))
    mode = (con.execute("SELECT v FROM meta WHERE k='search_delete'").fetchone() or ["rows"])[0]
    with con:
        if mode == "rebuild" and (gone or any(rel in known for rel, _ in moved)):
            con.execute("INSERT INTO search(search) VALUES('delete-all')")
            con.execute("DELETE FROM search_rows")
            con.execute("DELETE FROM search_files")
            moved = [(rel, (repo / rel).stat()) for rel in want if (repo / rel).is_file()]
            gone = []
        for rel in gone:
            drop(con, rel)
        for rel, st in moved:
            if mode != "rebuild":
                drop(con, rel)
            put(con, repo, rel, st)
        con.execute("INSERT OR REPLACE INTO meta VALUES('search_scope', ?)", ("guidelines" if scope else "tracked",))
    n = con.execute("SELECT COUNT(*) FROM search_files").fetchone()[0]
    return n, len(moved) + len(gone), "guidelines" if scope else "tracked"


def match_expr(terms, any_=False, raw=False):
    if raw:
        return " ".join(terms)
    words = [w for t in terms for w in TERM.findall(t)]
    parts = []
    for w in words:
        star = w.endswith("*")
        core = w.rstrip("*").replace('"', '""')
        if core:
            parts.append(f'"{core}"' + ("*" if star else ""))
    return (" OR " if any_ else " ").join(parts)


def first_hit(repo, rel, l0, l1, terms):
    try:
        lines = (repo / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return l0
    words = [w.rstrip("*").casefold() for t in terms for w in TERM.findall(t) if w.rstrip("*")]
    for x in range(l0 - 1, min(l1, len(lines))):
        low = lines[x].casefold()
        if any(w in low for w in words):
            return x + 1
    return l0


def query(repo, terms, path=None, limit=LIMIT, any_=False, raw=False):
    con, vdir = open_store(repo)
    files, moved, scope = refresh(con, repo, vdir)
    expr = match_expr(terms, any_, raw)
    if not expr:
        raise ValueError("no searchable term")
    sql = ("SELECT r.path, r.node, r.l0, r.l1, r.chain, bm25(search) AS score FROM search "
           "JOIN search_rows r ON r.rowid = search.rowid WHERE search MATCH ?")
    args = [expr]
    if path:
        p = path.strip("/")
        sql += " AND (r.path = ? OR r.path LIKE ?)"
        args += [p, p.replace("%", r"\%").replace("_", r"\_") + "/%"]
    sql += " ORDER BY score LIMIT ?"
    args.append(int(limit))
    try:
        rows = con.execute(sql, args).fetchall()
    except sqlite3.OperationalError as e:
        raise ValueError(f"FTS5 refused the query {expr!r}: {e}")
    con.close()
    head = {"index": "fts5", "scope": scope, "files": files, "refreshed": moved, "match": expr, "hits": len(rows)}
    hits = [{"path": r["path"], "line": first_hit(repo, r["path"], r["l0"], r["l1"], terms), "lines": [r["l0"], r["l1"]],
             "node": r["node"], "chain": r["chain"], "score": round(r["score"], 3)} for r in rows]
    return head, hits


def fallback(terms, why):
    return {"index": "none", "why": why, "fallback": "rg -n -i -F -- " + shlex.quote(" ".join(terms)) + " ."}


def cli(argv):
    ap = argparse.ArgumentParser(prog="locate.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo")
    sub = ap.add_subparsers(dest="cmd")
    i = sub.add_parser("index")
    i.add_argument("--guidelines-only", action="store_true")
    q = sub.add_parser("query")
    q.add_argument("terms", nargs="+")
    q.add_argument("--path")
    q.add_argument("--limit", type=int, default=LIMIT)
    q.add_argument("--any", action="store_true")
    q.add_argument("--raw", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    repo = wire.repo_root(Path(a.repo).resolve() if a.repo else Path.cwd())
    try:
        if a.cmd == "index":
            con, vdir = open_store(repo)
            files, moved, scope = refresh(con, repo, vdir, a.guidelines_only)
            print(json.dumps({"index": "fts5", "scope": scope, "files": files, "refreshed": moved}))
            return 0
        head, hits = query(repo, a.terms, a.path, a.limit, a.any, a.raw)
        print(json.dumps(head, ensure_ascii=False))
        for h in hits:
            print(json.dumps(h, ensure_ascii=False))
        return 0
    except NoIndex as e:
        print(json.dumps(fallback(getattr(a, "terms", []) or [], str(e))))
        return 3
    except (ValueError, OSError, sqlite3.Error) as e:
        print(f"locate.py: {e}", file=sys.stderr)
        return 2


def selftest():
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        try:
            open_store(bare)
            cases.append((False, "an unadopted project falls back to rg"))
        except NoIndex:
            cases.append((True, "an unadopted project falls back to rg"))
        root = wire.build_fixture(Path(tmp) / "proj")
        (root / "src").mkdir(exist_ok=True)
        code = root / "src" / "cards.py"
        code.write_text("class Cards:\n    def approve(self, card):\n        card.state = 'approved'\n\n"
                        "    def archive(self, card):\n        card.state = 'archived'\n", encoding="utf-8")
        doc = root / ".guidelines" / "RULES.md"
        doc.write_text("# Rules\n\n## Approval\n\nAn approval can be reversed by the owner.\n", encoding="utf-8")
        head, hits = query(root, ["approved"])
        cases.append((head["hits"] == 1 and hits[0]["path"] == "src/cards.py" and hits[0]["line"] == 3,
                      "query: the hit names the file and the exact line"))
        cases.append((all("text" not in h for h in hits) and "approve" in hits[0]["chain"],
                      "query: locations and the node chain, never the text"))
        con, vdir = open_store(root)
        stored = con.execute("SELECT COUNT(*) FROM search_rows WHERE path='src/cards.py'").fetchone()[0]
        lines = con.execute("SELECT SUM(l1 - l0 + 1) FROM search_rows").fetchone()[0]
        con.close()
        cases.append((stored >= 3 and lines > 0, "rows: one per node holding its own lines"))
        head2, hits2 = query(root, ["reversed", "owner"])
        cases.append((head2["refreshed"] == 0 and hits2 and hits2[0]["path"] == ".guidelines/RULES.md",
                      "query: a second query re-parses nothing and finds the guideline slice"))
        _, none = query(root, ["approved"], path=".guidelines")
        _, some = query(root, ["approval"], path=".guidelines")
        cases.append((none == [] and some and all(h["path"].startswith(".guidelines/") for h in some),
                      "query: --path narrows to a folder"))
        code.write_text(code.read_text(encoding="utf-8").replace("approved", "accepted"), encoding="utf-8")
        os.utime(code, ns=(code.stat().st_atime_ns, code.stat().st_mtime_ns + 10 ** 9))
        head3, hits3 = query(root, ["approved"])
        cases.append((head3["refreshed"] == 1 and hits3 == [], "fresh: an edited file is re-indexed before the query"))
        _, hits4 = query(root, ["accep*"])
        cases.append((len(hits4) == 1 and hits4[0]["line"] == 3, "query: a trailing * is a prefix"))
        code.unlink()
        head5, hits5 = query(root, ["accepted"])
        cases.append((hits5 == [] and head5["refreshed"] == 1, "fresh: a removed file leaves the index"))
        con, _ = open_store(root)
        con.execute("INSERT OR REPLACE INTO meta VALUES('search_delete', 'rebuild')")
        con.commit()
        con.close()
        doc.write_text(doc.read_text(encoding="utf-8").replace("owner", "steward"), encoding="utf-8")
        os.utime(doc, ns=(doc.stat().st_atime_ns, doc.stat().st_mtime_ns + 10 ** 9))
        _, old = query(root, ["owner"])
        _, new = query(root, ["steward"])
        cases.append((old == [] and len(new) == 1, "fresh: an SQLite without contentless delete rebuilds the index whole"))
        cases.append((match_expr(['say "hi"', "x*"]) == '"say" "hi" "x"*', "terms are quoted: no FTS5 syntax error from input"))
        cases.append((fallback(["a b"], "x")["fallback"] == "rg -n -i -F -- 'a b' .", "fallback: the rg line to run instead"))
    return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else cli(sys.argv[1:]))
