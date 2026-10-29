#!/usr/bin/env python3
"""idx.py - the exact index under .shortcuts/.virtual: nodes, fingerprints, edges, recovery, raw shortcuts.

library/virtualpath.md section 6. Written for the harness, not for a reader: every answer is a JSON line,
every position exact.

  nodes     the file itself; in Markdown each heading's section, paragraph, list, table, table row, code
            fence and front matter; in any other file, blocks by one language-agnostic rule (indentation and
            blank lines, with attached comments, attributes and closing lines), down to three levels
  id        12 hex from the node's structural key (a section-sign anchor or the heading text, a block's first
            line that is not a comment or attribute, a glyph block's name) and its parent's key chain - never
            its position: an insertion elsewhere changes no id, and a rebuild from nothing gives the same ids
  ranges    bytes [b0, b1) and lines l0..l1 (1-based, inclusive) over the file as stored
  hashes    exact: sha256 of the node (CRLF read as LF, STALE lines left out)
            shape: whitespace collapsed, spaces beside punctuation dropped, indentation as relative ranks -
                   a reformat keeps it; a re-indent that moves a line into or out of a block does not
            body:  the shape without the key line (a renamed key with the same body is a rename)
  edges     manifest slice -> governed nodes (a bare file: all of it; path#n:<id>: that node); node -> the
            anchors and ids it cites (library/ids.md), on the deepest node holding the citing line
  recovery  a removed node leaves a tombstone; a node that reappears with the same shape (moved), the same
            body under a new key (renamed) or a close trigram sketch (similar) is recorded as a move, and
            `check` proposes the relink - nothing is relinked silently

Storage: <virtual>/index.sqlite, a cache gitignored by <virtual>/.gitignore and rebuilt by `build`. Its prints
table (every recorded file's fingerprint: sha256, size, mtime, the hash it replaced, when, which session) is
written by scripts/shortcuts.py and hook-lineage.py, and a rebuild keeps it (library/shortcuts.md §2).

Modes:  build [--guidelines-only] · update PATH · node PATH[:LINE] · get ID · governs PATH[:LINE] · cites REF
        · check · shortcuts [--write] · --selftest             (each mode takes --repo DIR)
Pure standard library (sqlite3), Python 3.8+.
"""
import argparse
import collections
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

DB, SCHEMA = "index.sqlite", "1"
MAX_BYTES, MAX_FILES, MAX_NODES, MAX_DEPTH = 512 * 1024, 20000, 4000, 3
TOMBSTONES, SKETCH, SIMILAR = 500, 32, 0.6
MD_EXT = {".md", ".markdown", ".txt"}
FLAT_EXT = {".csv", ".tsv", ".lock", ".svg", ".map", ".sum", ".snap", ".ipynb"}
SKIP = set(wire.SKIP_PARTS) | {"bin", "obj", "dist", "build", "target", "venv"}
CITE_KINDS = ("gate", "ui-rule", "order", "conflict")

HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
ANCHOR = re.compile(r"§([^\s—:,;()\[\]]+)")
GLYPH_OPEN = re.compile(r"^\s*\[block'([^']+)'")
GLYPH_CLOSE = re.compile(r"^\s*\[/block")
ROW_LABEL = re.compile(r"^\|\s*~{0,2}\s*\*\*(.+?)\*\*")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
LEAD = re.compile(r"^(?://|/\*|\*|--|;|<!--|@\*|#(?![\w{])|#\[|@[\w.]|\[[A-Za-z_][\w.]*(?:\(.*\))?\]$)")
CLOSER = re.compile(r"^(?:[\]\)\}]+[;,)]*|end\b.*|fi|done|esac|</[\w.:-]+>)$")
CONTINUES = re.compile(r"^(?:[\]\)\}{]|else\b|elif\b|except\b|finally\b|catch\b|\.)")

SQL = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, sha TEXT, bytes INTEGER, nodes INTEGER, at TEXT);
CREATE TABLE IF NOT EXISTS nodes(path TEXT, id TEXT, kind TEXT, depth INTEGER, parent TEXT, ord INTEGER,
  b0 INTEGER, b1 INTEGER, l0 INTEGER, l1 INTEGER, key TEXT, label TEXT, exact TEXT, shape TEXT, body TEXT,
  sketch TEXT, PRIMARY KEY(path, id));
CREATE INDEX IF NOT EXISTS nodes_id ON nodes(id);
CREATE INDEX IF NOT EXISTS nodes_label ON nodes(path, label);
CREATE TABLE IF NOT EXISTS cites(path TEXT, id TEXT, ref TEXT, kind TEXT);
CREATE INDEX IF NOT EXISTS cites_ref ON cites(ref);
CREATE INDEX IF NOT EXISTS cites_path ON cites(path);
CREATE TABLE IF NOT EXISTS tombs(path TEXT, id TEXT, kind TEXT, label TEXT, shape TEXT, body TEXT, sketch TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS moves(old_path TEXT, old_id TEXT, old_label TEXT, new_path TEXT, new_id TEXT,
  new_label TEXT, how TEXT, score REAL, at TEXT);
CREATE TABLE IF NOT EXISTS shortcuts(name TEXT, src TEXT, path TEXT, anchor TEXT, node TEXT, l0 INTEGER,
  l1 INTEGER, b0 INTEGER, b1 INTEGER, exact TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS prints(path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL, prev_sha256 TEXT, at TEXT NOT NULL, session TEXT, source TEXT NOT NULL);
"""
NODE_COLS = ("path", "id", "kind", "depth", "parent", "ord", "b0", "b1", "l0", "l1", "key", "label",
             "exact", "shape", "body", "sketch")


# ---------- normal forms ------------------------------------------------------------------------

def h16(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def indent(line):
    s = line.expandtabs(4)
    return len(s) - len(s.lstrip(" "))


def shape_line(line):
    s = re.sub(r"[ \t]+", " ", line.strip())
    return re.sub(r" ?([^\w ]) ?", r"\1", s)


def hashes(body, key_text=None):
    """(exact, shape, body) of a node's lines."""
    exact = h16("\n".join(body))
    lines = [l for l in body if l.strip()]
    rank = {w: r for r, w in enumerate(sorted({indent(l) for l in lines}))}
    shaped = [f"{rank[indent(l)]}|{shape_line(l)}" for l in lines]
    rest = list(shaped)
    if key_text is not None:
        ks = shape_line(key_text)
        for i, s in enumerate(rest):
            if s.split("|", 1)[1] == ks:
                del rest[i]
                break
    elif rest:
        rest = rest[1:]
    return exact, h16("\n".join(shaped)), h16("\n".join(rest))


def sketch(body):
    text = " ".join(shape_line(l) for l in body if l.strip())[:800]
    grams = {text[i:i + 3] for i in range(max(0, len(text) - 2))}
    vals = sorted(int.from_bytes(hashlib.blake2b(g.encode("utf-8"), digest_size=4).digest(), "big") for g in grams)
    return " ".join(f"{v:08x}" for v in vals[:SKETCH])


def similarity(a, b):
    sa, sb = set((a or "").split()), set((b or "").split())
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def cite_patterns():
    """(kind, regex) for the anchors and the ids of library/ids.md a node may cite."""
    pats = [("anchor", ANCHOR), ("unit", wire.UNIT)]
    try:
        text = (HERE.parent / "library" / "ids.md").read_text(encoding="utf-8")
        grammar = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
        for kind in CITE_KINDS:
            core = grammar[kind]["pattern"].lstrip("^").rstrip("$")
            pats.append((kind, re.compile(r"(?<![\w-])" + core + r"(?![\w-])")))
    except (OSError, AttributeError, KeyError, ValueError):
        pass
    return pats


# ---------- parsing -----------------------------------------------------------------------------

def split(raw):
    """Lines (a final newline ends the last line; it does not open an empty one) and their byte offsets."""
    parts = raw.split(b"\n")
    offs, pos = [], 0
    for p in parts:
        offs.append(pos)
        pos += len(p) + 1
    if len(parts) > 1 and parts[-1] == b"":
        parts = parts[:-1]
    return [p.rstrip(b"\r").decode("utf-8", "replace") for p in parts], offs


def mk(kind, l0, l1, key, parent, depth, label=None, key_line=None):
    return {"kind": kind, "l0": l0, "l1": l1, "key": key, "parent": parent, "depth": depth,
            "label": label, "key_line": key_line}


def parse_md(lines):
    n = len(lines)
    nodes = [mk("file", 0, n, "", None, 0)]
    front = 0
    if n and lines[0].strip() == "---":
        front = next((k + 1 for k in range(1, n) if lines[k].strip() == "---"), 0)
        if front:
            nodes.append(mk("front", 0, front, "front", 0, 1))
    heads, fence = [], None
    for i in range(front, n):
        m = FENCE.match(lines[i])
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        hm = HEADING.match(lines[i])
        if hm:
            heads.append((i, len(hm.group(1)), hm.group(2).strip()))
    stack, owner_of = [], {}
    for k, (i, lvl, text) in enumerate(heads):
        end = next((hh[0] for hh in heads[k + 1:] if hh[1] <= lvl), n)
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        parent = stack[-1][1] if stack else 0
        sec = ANCHOR.search(text)
        key = "§" + sec.group(1) if sec else re.sub(r"\s+", " ", text)
        nodes.append(mk("section", i, end, key, parent, nodes[parent]["depth"] + 1,
                        label=sec.group(1) if sec else text, key_line=i))
        stack.append((lvl, len(nodes) - 1))
        owner_of[i] = len(nodes) - 1
    marks = [front] + [hh[0] for hh in heads] + [n]
    for r in range(len(marks) - 1):
        a, b = marks[r], marks[r + 1]
        owner = owner_of.get(a, 0)
        md_blocks(lines, a + 1 if a in owner_of else a, b, owner, nodes)
    return nodes


def md_blocks(lines, a, b, owner, nodes):
    depth = nodes[owner]["depth"] + 1

    def add(kind, l0, l1, key, label=None, parent=owner, d=depth):
        nodes.append(mk(kind, l0, l1, key, parent, d, label=label, key_line=l0))
        return len(nodes) - 1

    i = a
    while i < b:
        line = lines[i]
        if not line.strip() or wire.STALE_MARK in line:
            i += 1
            continue
        fm, gm = FENCE.match(line), GLYPH_OPEN.match(line)
        if fm:
            j = i + 1
            while j < b:
                m = FENCE.match(lines[j])
                if m and m.group(1)[0] == fm.group(1)[0] and not m.group(2).strip():
                    break
                j += 1
            j = min(j + 1, b)
            first = next((lines[k] for k in range(i + 1, j) if lines[k].strip() and not FENCE.match(lines[k])), "")
            add("fence", i, j, f"fence:{fm.group(2).strip()}:{shape_line(first)[:60]}")
            i = j
        elif gm:
            j = next((k + 1 for k in range(i + 1, b) if GLYPH_CLOSE.match(lines[k])), b)
            add("glyph", i, j, "glyph:" + gm.group(1), label=gm.group(1))
            i = j
        elif line.lstrip().startswith("|"):
            j = i
            while j < b and lines[j].lstrip().startswith("|"):
                j += 1
            t = add("table", i, j, "table:" + shape_line(line)[:60])
            for k in range(i, j):
                rm = ROW_LABEL.match(lines[k].lstrip())
                if rm:
                    add("row", k, k + 1, "row:" + rm.group(1).strip(), label=rm.group(1).strip(), parent=t, d=depth + 1)
            i = j
        else:
            kind = "list" if LIST_ITEM.match(line) else "para"
            j = i + 1
            while j < b and lines[j].strip() and wire.STALE_MARK not in lines[j] and not FENCE.match(lines[j]) \
                    and not lines[j].lstrip().startswith("|") and not GLYPH_OPEN.match(lines[j]) \
                    and (kind == "list" or not LIST_ITEM.match(lines[j])):
                j += 1
            add(kind, i, j, f"{kind}:{shape_line(line)[:60]}")
            i = j


def continued(lines):
    """Lines inside a multi-line string or block comment opened on an earlier line: they continue that line."""
    inside, state = [False] * len(lines), None
    for i, line in enumerate(lines):
        if state:
            inside[i] = True
            if (state == "/*" and "*/" in line) or (state != "/*" and line.count(state) % 2 == 1):
                state = None
            continue
        state = next((q for q in ('"""', "'''") if line.count(q) % 2 == 1), None)
        if state is None and "/*" in line and "*/" not in line[line.index("/*"):]:
            state = "/*"
    return inside


def parse_code(lines):
    n = len(lines)
    inner = continued(lines)
    info = [((not l.strip()) or wire.STALE_MARK in l, 10 ** 6 if inner[k] else indent(l), l.strip())
            for k, l in enumerate(lines)]
    nodes = [mk("file", 0, n, "", None, 0)]

    def walk(start, end, floor, parent, depth):
        ws = [info[k][1] for k in range(start, end) if not info[k][0] and info[k][1] > floor]
        if not ws:
            return
        level = min(ws)
        i = start
        while i < end and len(nodes) <= MAX_NODES:
            blank, w, _ = info[i]
            if blank or w != level:
                i += 1
                continue
            s = i
            while i < end and not info[i][0] and info[i][1] == level and LEAD.match(info[i][2]):
                i += 1
            if i < end and not info[i][0] and info[i][1] == level:
                key_i, j = i, i + 1
            else:
                key_i, j = s, max(i, s + 1)
            while j < end:
                bj, wj, tj = info[j]
                if bj:
                    k = j
                    while k < end and info[k][0]:
                        k += 1
                    if k < end and (info[k][1] > level or (info[k][1] == level and CLOSER.match(info[k][2]))):
                        j = k
                        continue
                    break
                if wj > level or (wj == level and (CLOSER.match(tj) or CONTINUES.match(tj))):
                    j += 1
                    continue
                break
            e = j
            while e > s and info[e - 1][0]:
                e -= 1
            nodes.append(mk("block", s, e, shape_line(info[key_i][2])[:120], parent, depth, key_line=key_i))
            me = len(nodes) - 1
            if depth < MAX_DEPTH and e - key_i > 2:
                walk(key_i + 1, e, level, me, depth + 1)
            i = max(j, s + 1)

    walk(0, n, -1, 0, 1)
    for i, line in enumerate(lines):
        gm = GLYPH_OPEN.match(line)
        if gm:
            j = next((k + 1 for k in range(i + 1, n) if GLYPH_CLOSE.match(lines[k])), n)
            nodes.append(mk("glyph", i, j, "glyph:" + gm.group(1), 0, 1, label=gm.group(1), key_line=i))
    return nodes


def parse(rel, raw):
    """(nodes, cites) of one file, with ids, ranges, order and hashes resolved."""
    lines, offs = split(raw)
    name = rel.lower()
    flat = len(raw) > MAX_BYTES or Path(name).suffix in FLAT_EXT or name.endswith((".min.js", ".min.css"))
    if flat:
        nodes = [mk("file", 0, len(lines), "", None, 0)]
    elif Path(name).suffix in MD_EXT:
        nodes = parse_md(lines)
    else:
        nodes = parse_code(lines)
    if len(nodes) > MAX_NODES:
        nodes = [mk("file", 0, len(lines), "", None, 0)]
    order = sorted(range(len(nodes)), key=lambda k: (nodes[k]["l0"], -(nodes[k]["l1"] - nodes[k]["l0"]), nodes[k]["depth"]))
    seen = collections.Counter()

    def chain(k):
        parts = []
        while k is not None:
            parts.append(nodes[k]["kind"][0] + ":" + nodes[k]["key"])
            k = nodes[k]["parent"]
        return "\x1f".join(reversed(parts))

    for rank, k in enumerate(order):
        nd = nodes[k]
        slot = (nd["parent"], nd["kind"], nd["key"])
        nd["id"] = hashlib.sha256(f"{rel}\0{chain(k)}\0{seen[slot]}".encode("utf-8")).hexdigest()[:12]
        seen[slot] += 1
        nd["ord"] = rank
        body = [lines[x] for x in range(nd["l0"], nd["l1"]) if wire.STALE_MARK not in lines[x]]
        key_text = lines[nd["key_line"]] if nd["key_line"] is not None else None
        nd["exact"], nd["shape"], nd["body"] = hashes(body, key_text)
        nd["sketch"] = sketch(body)
        nd["b0"] = offs[nd["l0"]] if nd["l0"] < len(offs) else len(raw)
        nd["b1"] = offs[nd["l1"]] if nd["l1"] < len(offs) else len(raw)
    for nd in nodes:
        nd["parent_id"] = nodes[nd["parent"]]["id"] if nd["parent"] is not None else None
    cites = []
    pats = cite_patterns()
    by_depth = sorted(nodes, key=lambda nd: -nd["depth"])
    for x, line in enumerate(lines):
        for kind, pat in pats:
            for m in pat.finditer(line):
                ref = m.group(1) if kind == "anchor" else m.group(0)
                holder = next((nd for nd in by_depth if nd["l0"] <= x < nd["l1"]), nodes[0])
                cites.append((holder["id"], ref, kind))
    return nodes, sorted(set(cites))


# ---------- storage -----------------------------------------------------------------------------

def connect(vdir, create=False):
    p = Path(vdir) / DB
    if not create and not p.is_file():
        return None
    ign = Path(vdir) / ".gitignore"
    if create and not ign.is_file():
        ign.write_text("# regency: the index is a cache, rebuilt by scripts/idx.py build\nindex.sqlite*\n", encoding="utf-8")
    con = sqlite3.connect(str(p), timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SQL)
    con.execute("INSERT OR REPLACE INTO meta VALUES('schema', ?)", (SCHEMA,))
    return con


def built(con):
    """True once `build` ran: a store that holds only prints (shortcuts.py) is not an index yet."""
    return con.execute("SELECT 1 FROM meta WHERE k='built'").fetchone() is not None


def row_of(rel, nd):
    l0 = nd["l0"] + 1
    return (rel, nd["id"], nd["kind"], nd["depth"], nd["parent_id"], nd["ord"], nd["b0"], nd["b1"], l0,
            max(nd["l1"], l0 - 1), nd["key"], nd["label"], nd["exact"], nd["shape"], nd["body"], nd["sketch"])


def store(con, rel, raw, nodes, cites):
    con.execute("DELETE FROM nodes WHERE path=?", (rel,))
    con.execute("DELETE FROM cites WHERE path=?", (rel,))
    con.executemany(f"INSERT OR REPLACE INTO nodes VALUES({','.join('?' * len(NODE_COLS))})",
                    [row_of(rel, nd) for nd in nodes])
    con.executemany("INSERT INTO cites VALUES(?,?,?,?)", [(rel, i, r, k) for i, r, k in cites])
    con.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)",
                (rel, hashlib.sha256(raw).hexdigest(), len(raw), len(nodes), wire.now()))


def text_bytes(path):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return None
    return None if b"\0" in raw[:8192] else raw


def wanted(rel):
    return not SKIP.intersection(Path(rel).parts) and "/.shortcuts/.virtual/" not in "/" + rel


def candidates(repo, guidelines, entries, guidelines_only):
    out = set()
    if guidelines and guidelines.is_dir():
        for p in guidelines.rglob("*"):
            r = wire.rel_posix(p, repo)
            if p.is_file() and r and wanted(r):
                out.add(r)
    for e in entries:
        for ref in e.get("refers_to") or []:
            if (repo / wire.ref_path(ref)).is_file():
                out.add(wire.ref_path(ref))
    if not guidelines_only:
        try:
            r = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, timeout=60)
            names = r.stdout.decode("utf-8", "replace").split("\0") if r.returncode == 0 else []
        except (OSError, subprocess.SubprocessError):
            names = []
        if not names:
            names = [wire.rel_posix(p, repo) for p in repo.rglob("*") if p.is_file()]
        out.update(n for n in names if n and wanted(n) and (repo / n).is_file())
    return sorted(out)[:MAX_FILES]


def build(repo, vdir, guidelines_only=False):
    con = connect(vdir, create=True)
    entries = wire.manifest_entries(vdir)
    files = candidates(repo, Path(vdir).parent.parent, entries, guidelines_only)
    nodes_total = 0
    with con:
        for table in ("files", "nodes", "cites", "shortcuts"):
            con.execute(f"DELETE FROM {table}")
        for rel in files:
            raw = text_bytes(repo / rel)
            if raw is None:
                continue
            nodes, cites = parse(rel, raw)
            store(con, rel, raw, nodes, cites)
            nodes_total += len(nodes)
        con.execute("INSERT OR REPLACE INTO meta VALUES('built', ?)", (wire.now(),))
    n_files = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    con.close()
    return {"built": True, "files": n_files, "nodes": nodes_total, "truncated": len(files) >= MAX_FILES}


# ---------- diff, recovery ----------------------------------------------------------------------

def outside(rel, guidelines_rel):
    return not (guidelines_rel and (rel == guidelines_rel or rel.startswith(guidelines_rel + "/")))


def update(con, repo, rel, guidelines_rel=""):
    """Re-index one file; the node diff against the index's last record of it."""
    old = {r["id"]: dict(r) for r in con.execute("SELECT * FROM nodes WHERE path=?", (rel,))}
    known = con.execute("SELECT 1 FROM files WHERE path=?", (rel,)).fetchone() is not None
    old_cites = list(con.execute("SELECT id, ref FROM cites WHERE path=?", (rel,)))
    raw = text_bytes(repo / rel) if (repo / rel).is_file() else None
    if raw is None:
        nodes, cites = [], []
        con.execute("DELETE FROM nodes WHERE path=?", (rel,))
        con.execute("DELETE FROM cites WHERE path=?", (rel,))
        con.execute("DELETE FROM files WHERE path=?", (rel,))
    else:
        nodes, cites = parse(rel, raw)
        store(con, rel, raw, nodes, cites)
    new = {nd["id"]: nd for nd in nodes}
    both = old.keys() & new.keys()
    modified = sorted(i for i in both if old[i]["shape"] != new[i]["shape"])
    reformatted = sorted(i for i in both if old[i]["shape"] == new[i]["shape"] and old[i]["exact"] != new[i]["exact"])
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())

    def siblings(table, parent_of):
        groups = collections.defaultdict(list)
        for i in sorted(both, key=lambda x: table[x]["ord"]):
            groups[parent_of(table[i])].append(i)
        return {i: (p, g.index(i)) for p, g in groups.items() for i in g}

    so, sn = siblings(old, lambda r: r["parent"]), siblings(new, lambda r: r["parent_id"])
    moved = sorted(i for i in both if i not in modified and so.get(i) != sn.get(i))
    file_old = next((r for r in old.values() if r["kind"] == "file"), None)
    file_new = next((nd for nd in nodes if nd["kind"] == "file"), None)
    file_changed = (not known or raw is None or file_old is None or file_new is None
                    or file_old["shape"] != file_new["shape"])
    cite_nodes = collections.defaultdict(set)
    if outside(rel, guidelines_rel):
        touched_old, touched_new = set(modified) | set(removed), set(modified) | set(added)
        for i, ref in old_cites:
            if i in touched_old:
                cite_nodes[ref].add(i)
        for i, ref, _ in cites:
            if i in touched_new or not known:
                cite_nodes[ref].add(i)
    moves = recover(con, rel, old, new, removed, added)
    return {"path": rel, "known": known, "deleted": raw is None, "file_changed": file_changed,
            "whitespace_only": known and raw is not None and not file_changed,
            "modified": modified, "added": added, "removed": removed, "reformatted": reformatted,
            "moved": moved, "cites_changed": sorted(cite_nodes), "cite_nodes": {k: sorted(v) for k, v in cite_nodes.items()},
            "moves": moves}


def recover(con, rel, old, new, removed, added):
    at = wire.now()
    con.executemany("INSERT INTO tombs VALUES(?,?,?,?,?,?,?,?)",
                    [(rel, i, old[i]["kind"], old[i]["label"] or old[i]["key"], old[i]["shape"], old[i]["body"],
                      old[i]["sketch"], at) for i in removed if old[i]["kind"] != "file"])
    tombs = [dict(r) for r in con.execute("SELECT rowid AS rid, * FROM tombs ORDER BY rowid DESC LIMIT ?", (TOMBSTONES,))]
    found = []
    for i in added:
        nd = new[i]
        if nd["kind"] == "file" or len(nd["sketch"].split()) < 8:
            continue
        best = None
        for t in tombs:
            if t["kind"] != nd["kind"] or (t["path"] == rel and t["id"] == i):
                continue
            if t["shape"] == nd["shape"]:
                cand = ("moved", 1.0)
            elif t["body"] == nd["body"]:
                cand = ("renamed", 0.95)
            else:
                s = similarity(t["sketch"], nd["sketch"])
                cand = ("similar", round(s, 2)) if s >= SIMILAR else None
            if cand and (best is None or cand[1] > best[1][1]):
                best = (t, cand)
        if best:
            t, (how, score) = best
            con.execute("INSERT INTO moves VALUES(?,?,?,?,?,?,?,?,?)",
                        (t["path"], t["id"], t["label"], rel, i, nd["label"] or nd["key"], how, score, at))
            con.execute("DELETE FROM tombs WHERE rowid=?", (t["rid"],))
            found.append({"old_path": t["path"], "old_id": t["id"], "new_id": i, "how": how, "score": score})
    con.execute("DELETE FROM tombs WHERE rowid NOT IN (SELECT rowid FROM tombs ORDER BY rowid DESC LIMIT ?)", (TOMBSTONES,))
    return found


# ---------- the hook's questions ----------------------------------------------------------------

def update_hook(vdir, repo, rel):
    """The node diff for a file just written, or None when there is no index (the caller stays conservative)."""
    try:
        con = connect(vdir)
        if con is None:
            return None
        if not built(con):
            con.close()
            return None
        with con:
            diff = update(con, Path(repo), rel, wire.rel_posix(Path(vdir).parent.parent, repo) or "")
        con.close()
        return diff
    except (sqlite3.Error, OSError) as e:
        print(f"idx.py: index not used ({e})", file=sys.stderr)
        return None


def anchor_of(entry):
    return entry.get("virtual_path", "").partition("#")[2]


def touches(entry, rel, diff):
    """(hit, node ids): did this write change what the entry governs in rel? Unknown history counts as a change."""
    if not diff.get("known"):
        return True, []
    hit = []
    changed = set(diff["modified"]) | set(diff["removed"])
    for ref in entry.get("refers_to") or []:
        path, _, sel = ref.partition("#")
        if path != rel:
            continue
        if not sel and diff["file_changed"]:
            hit.extend(diff["modified"] + diff["added"] + diff["removed"] or ["file"])
        elif sel.startswith("n:") and sel[2:] in changed:
            hit.append(sel[2:])
    hit.extend(diff.get("cite_nodes", {}).get(anchor_of(entry), []))
    return bool(hit), sorted(set(hit))


def cited_entries(entries, diff):
    refs = set((diff or {}).get("cites_changed", []))
    return [e for e in entries if anchor_of(e) in refs]


def summary(vdir):
    try:
        con = connect(vdir)
        if con is None or not built(con):
            if con:
                con.close()
            return "index absent (idx.py build)"
        n = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        s = con.execute("SELECT COUNT(*) FROM shortcuts").fetchone()[0]
        con.close()
        return f"index {n} nodes" + (f" · shortcuts {s}" if s else "")
    except sqlite3.Error:
        return "index unreadable (idx.py build)"


# ---------- queries -----------------------------------------------------------------------------

def out_node(r):
    return {k: r[k] for k in ("path", "id", "kind", "depth", "parent", "ord", "l0", "l1", "b0", "b1", "label", "exact", "shape")}


def chain_at(con, rel, line):
    rows = con.execute("SELECT * FROM nodes WHERE path=? AND l0<=? AND l1>=? ORDER BY depth", (rel, line, line))
    return [dict(r) for r in rows]


def governs(con, entries, rel, line=None):
    ids = {r["id"] for r in (chain_at(con, rel, line) if line else con.execute("SELECT id FROM nodes WHERE path=?", (rel,)))}
    out = []
    for e in entries:
        for ref in e.get("refers_to") or []:
            path, _, sel = ref.partition("#")
            if path == rel and (not sel or sel[2:] in ids):
                out.append({"slice": e["virtual_path"], "how": "node" if sel else "file", "ref": ref,
                            "on_mutation": e.get("on_mutation")})
    for r in con.execute("SELECT id, ref FROM cites WHERE path=?", (rel,)):
        if r["id"] in ids:
            for e in entries:
                if anchor_of(e) == r["ref"]:
                    out.append({"slice": e["virtual_path"], "how": "cite", "node": r["id"], "on_mutation": e.get("on_mutation")})
    return out


def resolve(con, rel, anchor):
    if anchor:
        r = con.execute("SELECT * FROM nodes WHERE path=? AND label=? ORDER BY depth LIMIT 1", (rel, anchor)).fetchone()
        if r is None:
            r = con.execute("SELECT * FROM nodes WHERE path=? AND kind='section' AND key=? LIMIT 1", (rel, anchor)).fetchone()
        return r
    return con.execute("SELECT * FROM nodes WHERE path=? AND kind='file'", (rel,)).fetchone()


def check(con, repo, entries, guidelines_rel):
    out, bad = [], 0
    drifted, deleted = [], []
    for r in con.execute("SELECT path, sha FROM files"):
        p = repo / r["path"]
        if not p.is_file():
            deleted.append(r["path"])
        elif hashlib.sha256(p.read_bytes()).hexdigest() != r["sha"]:
            drifted.append(r["path"])
    out.append({"check": "cache", "files": con.execute("SELECT COUNT(*) FROM files").fetchone()[0],
                "drifted": len(drifted), "deleted": len(deleted), "sample": (drifted + deleted)[:10]})

    def proposals(where, args):
        return [dict(r) for r in con.execute(f"SELECT new_path, new_id, new_label, how, score FROM moves WHERE {where}"
                                             " ORDER BY score DESC, rowid DESC LIMIT 3", args)]

    anchors = set()
    for e in entries:
        vp = e["virtual_path"]
        f, _, anchor = vp.partition("#")
        anchors.add(anchor)
        gpath = f"{guidelines_rel}/{f}" if guidelines_rel else f
        if resolve(con, gpath, anchor) is None:
            bad += 1
            out.append({"check": "slice", "slice": vp, "status": "unresolved",
                        "proposals": proposals("old_path=? AND old_label=?", (gpath, anchor))})
        for ref in e.get("refers_to") or []:
            path, _, sel = ref.partition("#")
            if not (repo / path).is_file():
                bad += 1
                out.append({"check": "ref", "slice": vp, "ref": ref, "status": "missing-file",
                            "proposals": proposals("old_path=? AND new_path<>?", (path, path))})
                continue
            if sel.startswith("n:") and con.execute("SELECT 1 FROM nodes WHERE path=? AND id=?", (path, sel[2:])).fetchone() is None:
                bad += 1
                out.append({"check": "ref", "slice": vp, "ref": ref, "status": "missing-node",
                            "proposals": proposals("old_id=?", (sel[2:],))})
                continue
            cited = con.execute("SELECT 1 FROM cites WHERE path=? AND ref=?", (path, anchor)).fetchone() is not None
            out.append({"check": "ref", "slice": vp, "ref": ref, "status": "cited" if cited else "uncited"})
    for r in con.execute("SELECT path, id, ref FROM cites WHERE kind='anchor'"):
        if outside(r["path"], guidelines_rel) and r["ref"] not in anchors:
            out.append({"check": "cite", "path": r["path"], "node": r["id"], "ref": r["ref"], "status": "no-slice"})
    return out, bad


def shortcuts(con, repo, vdir):
    """Exact rows for the prose index's links, the ledger's evidence, every STALE slice and the latest Order."""
    g = Path(vdir).parent.parent
    rows = []

    def row(name, src, rel, anchor=""):
        r = resolve(con, rel, anchor) if rel else None
        base = {"name": name, "src": src, "path": rel, "anchor": anchor}
        if r is None:
            return dict(base, node=None, l0=None, l1=None, b0=None, b1=None, exact=None, status="dead")
        return dict(base, node=r["id"], l0=r["l0"], l1=r["l1"], b0=r["b0"], b1=r["b1"], exact=r["exact"], status="ok")

    readme = g / ".shortcuts" / "README.md"
    if readme.is_file():
        for m in LINK.finditer(readme.read_text(encoding="utf-8-sig", errors="replace")):
            target = m.group(2)
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path, _, anchor = target.partition("#")
            rel = wire.rel_posix((readme.parent / path).resolve(), repo)
            rows.append(row(m.group(1).strip() or path, "readme", rel, anchor))
    led = Path(vdir) / "ongoing.json"
    try:
        items = json.loads(led.read_text(encoding="utf-8-sig")).get("items", []) if led.is_file() else []
    except ValueError:
        items = []
    for it in items:
        for where in it.get("where") or []:
            path, _, sel = where.partition("#")
            if ":" in path:
                continue
            r = con.execute("SELECT * FROM nodes WHERE path=? AND id=?", (path, sel[2:])).fetchone() if sel.startswith("n:") else None
            rows.append(row(it.get("id", "?"), "ledger", path) if r is None else
                        {"name": it.get("id", "?"), "src": "ledger", "path": path, "anchor": "", "node": r["id"],
                         "l0": r["l0"], "l1": r["l1"], "b0": r["b0"], "b1": r["b1"], "exact": r["exact"], "status": "ok"})
    for r in con.execute("SELECT path FROM files"):
        p = repo / r["path"]
        if not r["path"].endswith(".md") or not p.is_file():
            continue
        lines = p.read_text(encoding="utf-8-sig", errors="replace").split("\n")
        for x, line in enumerate(lines):
            if wire.STALE_MARK in line:
                sec = con.execute("SELECT * FROM nodes WHERE path=? AND kind='section' AND l0<=? AND l1>=? "
                                  "ORDER BY depth DESC LIMIT 1", (r["path"], x + 1, x + 1)).fetchone()
                if sec:
                    rows.append({"name": sec["label"], "src": "stale", "path": r["path"], "anchor": sec["label"],
                                 "node": sec["id"], "l0": sec["l0"], "l1": sec["l1"], "b0": sec["b0"], "b1": sec["b1"],
                                 "exact": sec["exact"], "status": "ok"})
    od = g / ".orders"
    nums = sorted(p.name for p in od.glob("ORD-*") if re.match(r"^ORD-\d{4,}$", p.name)) if od.is_dir() else []
    if nums:
        for f in sorted((od / nums[-1]).glob("*")):
            rows.append(row(nums[-1], "order", wire.rel_posix(f, repo)))
    return rows


# ---------- CLI ---------------------------------------------------------------------------------

def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def place(repo_arg):
    repo = wire.repo_root(Path(repo_arg).resolve()) if repo_arg else wire.repo_root(Path.cwd())
    return repo, wire.virtual_dir(repo)


def rel_and_line(repo, spec):
    m = re.match(r"^(.*?)(?::(\d+))?$", spec)
    p = Path(m.group(1))
    rel = wire.rel_posix(p if p.is_absolute() else repo / p, repo) or m.group(1)
    return rel, int(m.group(2)) if m.group(2) else None


def cli(argv):
    ap = argparse.ArgumentParser(prog="idx.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("--guidelines-only", action="store_true")
    for name in ("update", "node", "governs"):
        sub.add_parser(name).add_argument("spec")
    sub.add_parser("get").add_argument("id")
    sub.add_parser("cites").add_argument("ref")
    sub.add_parser("check")
    s = sub.add_parser("shortcuts")
    s.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    repo, vdir = place(a.repo)
    if not vdir:
        emit({"error": "no .shortcuts/.virtual under a guidelines root here", "repo": str(repo)})
        return 2
    if a.cmd == "build":
        emit(build(repo, vdir, a.guidelines_only))
        return 0
    con = connect(vdir)
    if con is None or not built(con):
        emit({"error": "no index: run idx.py build"})
        return 2
    entries = wire.manifest_entries(vdir)
    g_rel = wire.rel_posix(Path(vdir).parent.parent, repo) or ""
    code = 0
    with con:
        if a.cmd == "update":
            emit(update(con, repo, rel_and_line(repo, a.spec)[0], g_rel))
        elif a.cmd == "node":
            rel, line = rel_and_line(repo, a.spec)
            rows = chain_at(con, rel, line) if line else [dict(r) for r in con.execute(
                "SELECT * FROM nodes WHERE path=? ORDER BY ord", (rel,))]
            for r in rows:
                emit(out_node(r))
            code = 0 if rows else 1
        elif a.cmd == "get":
            r = con.execute("SELECT * FROM nodes WHERE id=?", (a.id,)).fetchone()
            if r is None:
                emit({"error": "no such node", "id": a.id})
                return 1
            f = con.execute("SELECT sha FROM files WHERE path=?", (r["path"],)).fetchone()
            raw = (repo / r["path"]).read_bytes() if (repo / r["path"]).is_file() else b""
            if f is None or hashlib.sha256(raw).hexdigest() != f["sha"]:
                update(con, repo, r["path"], g_rel)
                r = con.execute("SELECT * FROM nodes WHERE id=?", (a.id,)).fetchone()
                if r is None:
                    emit({"error": "node gone after re-index", "id": a.id})
                    return 1
            emit(dict(out_node(r), text=raw[r["b0"]:r["b1"]].decode("utf-8", "replace")))
        elif a.cmd == "governs":
            rel, line = rel_and_line(repo, a.spec)
            for row in governs(con, entries, rel, line):
                emit(row)
        elif a.cmd == "cites":
            for r in con.execute("SELECT path, id, ref, kind FROM cites WHERE ref=? ORDER BY path", (a.ref.lstrip("§"),)):
                emit(dict(r))
        elif a.cmd == "check":
            rows, bad = check(con, repo, entries, g_rel)
            for row in rows:
                emit(row)
            code = 1 if bad else 0
        elif a.cmd == "shortcuts":
            rows = shortcuts(con, repo, vdir)
            if a.write:
                con.execute("DELETE FROM shortcuts")
                con.executemany("INSERT INTO shortcuts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                [(r["name"], r["src"], r["path"], r["anchor"], r["node"], r["l0"], r["l1"], r["b0"],
                                  r["b1"], r["exact"], r["status"]) for r in rows])
            for row in rows:
                emit(row)
            code = 1 if any(r["status"] == "dead" for r in rows) else 0
    con.close()
    return code


# ---------- self-test ---------------------------------------------------------------------------

PY = """import os

# §layout-stable governs the splitter
@cached
def split(a, b):
    if a:
        return a
    else:
        return b


def join(x):
    return x
"""
CS = """namespace Board;

public class Board
{
    private int _n;

    [Obsolete]
    public int Count()
    {
        return _n;
    }
}
"""
MD = """# Architecture

## §layout-stable — layout

Rule text.

| key | value |
|---|---|
| **ledger-x** | open |

## Other

x
"""


def selftest():
    cases = []

    def labels(nodes):
        return [(nd["kind"], nd["key"]) for nd in nodes]

    py, _ = parse("src/split.py", PY.encode())
    keys = [nd["key"] for nd in py if nd["kind"] == "block" and nd["depth"] == 1]
    cases.append((keys == ["import os", "def split(a,b):", "def join(x):"], f"Python blocks by indentation: {keys}"))
    doc = '"""Title line.\n\nSecond paragraph\nstill the docstring.\n"""\nimport os\n'
    dk = [nd["key"] for nd in parse("d.py", doc.encode())[0] if nd["depth"] == 1]
    cases.append((dk == ['"""Title line.', "import os"], f"a docstring at column 0 is one block: {dk}"))
    split_node = next((nd for nd in py if nd["key"] == "def split(a,b):"), py[0])
    cases.append((PY.split("\n")[split_node["l0"]].startswith("# §layout"), "comment and decorator attach to the def"))
    cases.append((any(nd["key"] == "if a:" and nd["l1"] - nd["l0"] == 4 for nd in py), "else stays with its if"))
    cs, _ = parse("src/Board.cs", CS.encode())
    members = [nd["key"] for nd in cs if nd["depth"] == 2]
    cases.append((members == ["private int _n;", "public int Count()"], f"C# members under the class: {members}"))
    count = next((nd for nd in cs if nd["key"] == "public int Count()"), cs[0])
    cases.append((CS.split("\n")[count["l0"]].strip() == "[Obsolete]" and CS.split("\n")[count["l1"] - 1].strip() == "}",
                  "attribute and Allman braces belong to the member"))
    md, md_cites = parse(".guidelines/A.md", MD.encode())
    sec = next(nd for nd in md if nd["kind"] == "section" and nd["label"] == "layout-stable")
    cases.append((sec["key"] == "§layout-stable" and MD.split("\n")[sec["l1"] - 1] == "", "section by anchor, to the next heading"))
    cases.append((any(nd["kind"] == "row" and nd["label"] == "ledger-x" for nd in md), "ledger rows are nodes"))
    raw = MD.encode()
    cases.append((raw[sec["b0"]:sec["b1"]].decode().startswith("## §layout-stable"), "byte range is exact"))
    f3 = parse("f.py", b"a = 1\nb = 2\nc = 3\n")[0][0]
    cases.append((f3["l1"] == 3 and f3["b1"] == 18, "a final newline does not add a phantom line"))
    _, py_cites = parse("src/split.py", PY.encode())
    holder = next(i for i, r, k in py_cites if r == "layout-stable")
    cases.append((holder == split_node["id"], "a citation belongs to the deepest node holding it"))

    # ids: deterministic, positional-free; hashes: whitespace-blind, indentation-aware
    again, _ = parse("src/split.py", PY.encode())
    cases.append(([nd["id"] for nd in py] == [nd["id"] for nd in again], "a rebuild gives the same ids"))
    shifted, _ = parse("src/split.py", ("import sys\n\n" + PY).encode())
    cases.append((split_node["id"] in {nd["id"] for nd in shifted}, "an insertion above changes no id"))
    reformatted, _ = parse("src/split.py", PY.replace("(a, b)", "( a,b )").replace("    return x", "        return x").encode())
    rs = next(nd for nd in reformatted if nd["id"] == split_node["id"])
    cases.append((rs["shape"] == split_node["shape"] and rs["exact"] != split_node["exact"], "a reformat keeps the shape"))
    two = "\n".join(l.replace("    ", "  ") for l in PY.split("\n"))
    t2 = next(nd for nd in parse("src/split.py", two.encode())[0] if nd["id"] == split_node["id"])
    cases.append((t2["shape"] == split_node["shape"], "re-indenting the whole file 4 -> 2 keeps the shape"))
    stale = MD.replace("## §layout-stable — layout\n", "## §layout-stable — layout\n[warn'STALE' on='x' changed='y']\n")
    st = next(nd for nd in parse(".guidelines/A.md", stale.encode())[0] if nd["id"] == sec["id"])
    cases.append((st["exact"] == sec["exact"] and st["shape"] == sec["shape"], "a STALE line changes no hash"))
    loop = "def f(x):\n    for i in x:\n        total(i)\n        log(i)\n"
    out_of_loop = loop.replace("        log(i)", "    log(i)")
    a1, a2 = (next(nd for nd in parse("f.py", t.encode())[0] if nd["key"] == "def f(x):") for t in (loop, out_of_loop))
    cases.append((a1["id"] == a2["id"] and a1["shape"] != a2["shape"],
                  "the same tokens moved out of a block change the shape, not the id"))

    with tempfile.TemporaryDirectory() as tmp:
        root = wire.build_fixture(Path(tmp) / "proj")
        vdir = root / ".guidelines/.shortcuts/.virtual"
        (root / "src/split.py").write_text(PY, encoding="utf-8")
        (root / "src/Board.cs").write_text(CS, encoding="utf-8")
        (root / ".guidelines/.shortcuts/README.md").write_text(
            "- [layout](../.decisions/ARCHITECTURE.md#layout-stable)\n- [gone](../.decisions/NOPE.md)\n", encoding="utf-8")
        summary_ = build(root, vdir, guidelines_only=False)
        cases.append((summary_["files"] >= 8 and (vdir / ".gitignore").read_text().strip().endswith("index.sqlite*"),
                      f"build indexes the tree and gitignores the cache: {summary_}"))
        con = connect(vdir)
        g_rel = ".guidelines"
        with con:
            d = update(con, root, "src/split.py", g_rel)
        cases.append((d["known"] and not (d["modified"] or d["added"] or d["removed"]), "an unchanged file diffs empty"))
        (root / "src/split.py").write_text(PY.replace("(a, b)", "(a,  b)"), encoding="utf-8")
        with con:
            d = update(con, root, "src/split.py", g_rel)
        cases.append((d["whitespace_only"] and not d["modified"] and d["reformatted"], "whitespace only: nothing modified"))
        (root / "src/split.py").write_text(PY.replace("return a\n", "return a + 1\n"), encoding="utf-8")
        with con:
            d = update(con, root, "src/split.py", g_rel)
        cases.append((split_node["id"] in d["modified"] and "layout-stable" in d["cites_changed"],
                      "an edit inside the cited function: modified, and its citation changed"))
        cases.append((con.execute("SELECT id FROM nodes WHERE path='src/split.py' AND key='def join(x):'").fetchone()["id"]
                      not in d["modified"], "a sibling function is not modified"))
        entry = {"virtual_path": ".decisions/ARCHITECTURE.md#layout-stable", "refers_to": ["src/Page.razor"]}
        cases.append((touches(entry, "src/split.py", d)[0] and touches(entry, "src/split.py", d)[1] == [split_node["id"]],
                      "a slice cited by the changed node is touched, through the citation"))
        join_id = con.execute("SELECT id FROM nodes WHERE path='src/split.py' AND key='def join(x):'").fetchone()["id"]
        sel = {"virtual_path": ".decisions/ARCHITECTURE.md#Other", "refers_to": [f"src/split.py#n:{join_id}"]}
        cases.append((not touches(sel, "src/split.py", d)[0], "a node selector ignores a change elsewhere in the file"))
        cases.append((touches(dict(sel, refers_to=["src/split.py"]), "src/split.py", d)[0], "a bare file sees any change"))
        cases.append((touches(sel, "src/split.py", {"known": False})[0], "unknown history counts as a change"))

        # recovery: a renamed function and a function moved to another file
        (root / "src/split.py").write_text(PY.replace("def join(x):", "def merge(x):").replace("return a\n", "return a + 1\n"),
                                           encoding="utf-8")
        with con:
            d = update(con, root, "src/split.py", g_rel)
        cases.append((any(m["old_id"] == join_id and m["how"] == "renamed" for m in d["moves"]), f"a rename is recorded: {d['moves']}"))
        body = "def relocated(q):\n    total = q * 2\n    total += 3\n    return total\n"
        (root / "src/one.py").write_text("import os\n\n\n" + body, encoding="utf-8")
        (root / "src/two.py").write_text("import sys\n", encoding="utf-8")
        with con:
            update(con, root, "src/one.py", g_rel)
            update(con, root, "src/two.py", g_rel)
            rel_id = con.execute("SELECT id FROM nodes WHERE path='src/one.py' AND key='def relocated(q):'").fetchone()["id"]
            (root / "src/one.py").write_text("import os\n", encoding="utf-8")
            update(con, root, "src/one.py", g_rel)
            (root / "src/two.py").write_text("import sys\n\n\n" + body, encoding="utf-8")
            d = update(con, root, "src/two.py", g_rel)
        cases.append((any(m["old_id"] == rel_id and m["old_path"] == "src/one.py" and m["how"] == "moved" for m in d["moves"]),
                      "a block moved to another file is recorded, exactly"))
        entries = [{"virtual_path": ".decisions/ARCHITECTURE.md#layout-stable", "refers_to": [f"src/one.py#n:{rel_id}"]},
                   {"virtual_path": ".decisions/ARCHITECTURE.md#gone-anchor", "refers_to": ["src/Page.razor"]}]
        with con:
            rows, bad = check(con, root, entries, g_rel)
        miss = next((r for r in rows if r.get("status") == "missing-node"), {})
        cases.append((miss.get("proposals") and miss["proposals"][0]["new_path"] == "src/two.py",
                      "check proposes the relink, never applies it"))
        cases.append((any(r.get("status") == "unresolved" and r["slice"].endswith("#gone-anchor") for r in rows) and bad >= 2,
                      "an anchor that resolves to no node is reported"))
        with con:
            sc = shortcuts(con, root, vdir)
        ok = next((r for r in sc if r["name"] == "layout"), {})
        cases.append((ok.get("status") == "ok" and ok.get("node") and ok.get("b1", 0) > ok.get("b0", 0),
                      "a prose link resolves to an exact node and byte range"))
        cases.append((any(r["name"] == "gone" and r["status"] == "dead" for r in sc), "a dead prose link is reported"))
        cases.append((any(r["src"] == "ledger" and r["path"] == "src/Page.razor" and r["status"] == "ok" for r in sc),
                      "ledger evidence resolves to its file node"))
        cases.append((any(r["src"] == "order" for r in sc), "the latest Order is a shortcut"))
        con.close()
        cases.append((update_hook(Path(tmp) / "nowhere", root, "src/split.py") is None, "no index: the hook gets None"))
    return wire.check(cases)


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in args else cli(args))
