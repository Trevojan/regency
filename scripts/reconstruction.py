#!/usr/bin/env python3
"""reconstruction.py - how much of what a session reads was already read, unchanged, by an earlier session.

library/shortcuts.md §8. Reads the `reads` table hook-reads.py fills in the one store (<virtual>/index.sqlite)
and measures, per session:

  read         bytes the Read tool returned in the session
  carried      bytes of only those lines of a read that an EARLIER session had already read at the same path and
               sha256 (line-level, the Regent's definition of 2026-11-18): context rebuilt from scratch because
               nothing carried it over - the reconstruction. Exact: the rows of one content give the byte offset
               of every boundary an overlap can have
  repeated     bytes of reads of the same lines of the same content earlier in the SAME session
  ratio        carried / read, the context-reconstruction ratio

and, over the window, the files most often re-read unchanged across sessions (a session counts when any of the
file's lines was carried): the candidates to transcribe into the entry index, a brief, a slice or a script
(conventions §0). Tokens are bytes / 4: an estimate, said so. A row journalled without its byte offset (b0, before
hook-reads.py kept it) is left out of every number and counted as left out.

Not measured: Bash reads (cat, sed, grep), Grep and Glob output, tool results, the system prompt, the prompt
cache. A Read that failed is not journalled.

Modes:  report [--sessions N] [--top N] [--json] · --selftest          (each mode takes --repo DIR)
Pure standard library (sqlite3), Python 3.8+.
"""
import argparse
import collections
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402
import idx  # noqa: E402  (connect(): the one store)

SESSIONS, TOP = 10, 10
METHOD = ("Read tool calls journalled by hook-reads.py; bytes of the lines each call returned; carried = the bytes of "
          "only those lines an earlier session read at the same path and sha256; tokens ~ bytes / 4 (estimate)")


def load(repo):
    vdir = wire.virtual_dir(repo)
    if vdir is None:
        return None, "no .shortcuts/.virtual under a guidelines root here: nothing is journalled"
    con = idx.connect(vdir)
    if con is None:
        return [], "no store yet (index.sqlite): no read journalled"
    try:
        rows = [dict(r) for r in con.execute("SELECT rowid, * FROM reads ORDER BY rowid")]
    except sqlite3.Error:
        rows = []
    con.close()
    return rows, None if rows else "no read journalled yet: hook-reads.py records from the next session on"


def merged(spans):
    """Line ranges (first, last), sorted and joined where they overlap or touch."""
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
            continue
        out.append([a, b])
    return out


def covered(row, earlier, starts):
    """(lines, bytes) of the row's lines that the earlier ranges already hold. `starts` maps a line of this content
    to the byte offset it starts at; every boundary of an overlap is the first line, or the line after the last, of
    the row or of an earlier read, so the bytes are exact."""
    lines = size = 0
    for a, b in merged(earlier):
        low, high = max(a, row["l0"]), min(b, row["l1"])
        if low <= high:
            lines += high - low + 1
            size += starts[high + 1] - starts[low]
    return lines, size


def measure(rows, sessions=SESSIONS, top=TOP):
    kept = [r for r in rows if r.get("b0") is not None]
    order = []
    for r in kept:
        if r["session"] not in order:
            order.append(r["session"])
    spans = collections.defaultdict(list)    # (path, sha) -> [(session rank, first line, last line)] read so far
    starts = collections.defaultdict(dict)   # (path, sha) -> {line: byte offset it starts at}
    per = collections.OrderedDict((s, {"session": s, "reads": 0, "read": 0, "carried": 0, "repeated": 0,
                                       "agents": set()}) for s in order)
    within = set()
    rebuilt = collections.defaultdict(set)   # path -> sessions that re-read some of its lines unchanged
    rank = {s: i for i, s in enumerate(order)}
    for r in kept:
        s, key = r["session"], (r["path"], r["sha256"])
        st = per[s]
        st["reads"] += 1
        st["read"] += r["bytes"]
        st["agents"].add(r["agent"])
        starts[key][r["l0"]] = r["b0"]
        starts[key][r["l1"] + 1] = r["b0"] + r["bytes"]
        lines_carried, bytes_carried = covered(r, [(a, b) for k, a, b in spans[key] if k < rank[s]], starts[key])
        st["carried"] += bytes_carried
        if lines_carried:
            rebuilt[r["path"]].add(s)
        if r["l1"] >= r["l0"]:
            spans[key].append((rank[s], r["l0"], r["l1"]))
        span = (s, r["path"], r["sha256"], r["l0"], r["l1"])
        if span in within:
            st["repeated"] += r["bytes"]
        within.add(span)
    window = list(per.values())[-sessions:]
    for st in window:
        st["ratio"] = round(st["carried"] / st["read"], 3) if st["read"] else 0.0
        st["agents"] = sorted(st["agents"])
    total = {k: sum(st[k] for st in window) for k in ("reads", "read", "carried", "repeated")}
    total["ratio"] = round(total["carried"] / total["read"], 3) if total["read"] else 0.0
    inside = {st["session"] for st in window}
    files = sorted(((p, len(ss & inside)) for p, ss in rebuilt.items() if ss & inside), key=lambda x: (-x[1], x[0]))
    return {"method": METHOD, "sessions": window, "total": total,
            "rebuilt_files": [{"path": p, "sessions": n} for p, n in files[:top]], "left_out": len(rows) - len(kept)}


def kb(n):
    return f"{n / 1024:.1f} KB (~{n // 4:,} tokens)"


def lines(m):
    t = m["total"]
    out = [f"reconstruction: {len(m['sessions'])} session(s) · read {kb(t['read'])} · carried {kb(t['carried'])} "
           f"· ratio {t['ratio']:.0%} · repeated in-session {kb(t['repeated'])}"]
    for st in m["sessions"]:
        out.append(f"session {st['session'][:12]} · {st['reads']} read(s) · read {kb(st['read'])} · carried "
                   f"{kb(st['carried'])} · ratio {st['ratio']:.0%} · repeated {kb(st['repeated'])} · "
                   f"agents {', '.join(st['agents'])}")
    for f in m["rebuilt_files"]:
        out.append(f"rebuilt {f['path']} · re-read unchanged in {f['sessions']} session(s)")
    if m.get("left_out"):
        out.append(f"left out: {m['left_out']} read(s) journalled before line offsets were kept")
    out.append(f"method: {m['method']}")
    return out


def cli(argv):
    ap = argparse.ArgumentParser(prog="reconstruction.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("report")
    r.add_argument("--sessions", type=int, default=SESSIONS)
    r.add_argument("--top", type=int, default=TOP)
    r.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    repo = wire.repo_root(Path(a.repo).resolve() if a.repo else Path.cwd())
    rows, why = load(repo)
    if not rows:
        print(f"reconstruction: {why}")
        return 0 if rows is not None else 2
    m = measure(rows, a.sessions, a.top)
    print(json.dumps(m, ensure_ascii=False, indent=1) if a.json else "\n".join(lines(m)))
    return 0


def selftest():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hook_reads", HERE / "hook-reads.py")
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        rows, why = load(root)
        cases.append((rows == [] and "no store" in why, "before any read: says so, measures nothing"))
        doc = root / ".guidelines/.decisions/ARCHITECTURE.md"
        code = root / "src/Page.razor"

        def read(sid, target, agent=None, **ti):
            ev = {"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": sid, "cwd": str(root),
                  "tool_input": dict({"file_path": str(target)}, **ti)}
            if agent:
                ev["agent_type"] = agent
            hook.respond(ev)

        read("s1", doc)
        read("s1", code)
        read("s1", doc)                       # the same lines again, same session: repeated
        read("s2", doc)                       # unchanged since s1: carried
        code.write_text("<p>page two</p>\n", encoding="utf-8")
        read("s2", code, agent="qa")          # changed since s1: new reading, not carried
        rows, _ = load(root)
        m = measure(rows)
        s1, s2 = m["sessions"]
        d = len(doc.read_bytes())
        cases.append((s1["carried"] == 0 and s1["repeated"] == d, "first session: nothing carried, the re-read counted as repeated"))
        cases.append((s2["carried"] == d and s2["ratio"] == round(d / (d + len(code.read_bytes())), 3),
                      "next session: the unchanged file is carried, the changed one is not"))
        cases.append((m["rebuilt_files"] == [{"path": ".guidelines/.decisions/ARCHITECTURE.md", "sessions": 1}],
                      "the file re-read unchanged across sessions is named"))
        cases.append((s2["agents"] == ["main", "qa"], "subagents are counted with the session"))
        cases.append((measure(rows, sessions=1)["total"]["reads"] == 2, "--sessions narrows the window to the latest"))
        out = lines(m)
        cases.append((out[0].startswith("reconstruction: 2 session(s)") and out[-1].startswith("method:"),
                      "the report: a total line first, the method last"))
        part = wire.build_fixture(Path(tmp) / "lines")
        big = part / ".guidelines/big.md"
        text = "".join(f"{i}:{'x' * (i % 7)}\n" for i in range(1, 101))
        big.write_text(text, encoding="utf-8")
        span_bytes = [len(x.encode("utf-8")) for x in text.splitlines(keepends=True)]

        def oracle(*spans):
            return sum(sum(span_bytes[a - 1:b]) for a, b in spans)

        for sid, first, count in (("p1", 1, 10), ("p2", 51, 50), ("p3", 5, 56)):
            hook.respond({"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": sid, "cwd": str(part),
                          "tool_input": {"file_path": str(big), "offset": first, "limit": count}})
        p1, p2, p3 = measure(load(part)[0])["sessions"]
        cases.append((p2["carried"] == 0 and p2["ratio"] == 0.0 and p3["carried"] == oracle((5, 10), (51, 60))
                      and p3["read"] == oracle((5, 60)) and p1["carried"] == 0,
                      "D4. carried counts only the lines an earlier session read: disjoint lines carry nothing, "
                      "an overlap carries its own lines' bytes"))
        legacy = [{"session": "old", "agent": "main", "path": "a.md", "sha256": "h", "l0": 1, "l1": 2, "bytes": 9,
                   "b0": None},
                  {"session": "new", "agent": "main", "path": "a.md", "sha256": "h", "l0": 1, "l1": 2, "bytes": 9,
                   "b0": 0}]
        lm = measure(legacy)
        cases.append((lm.get("left_out") == 1 and lm["total"]["reads"] == 1 and lm["total"]["carried"] == 0
                      and any(x.startswith("left out: 1 read(s)") for x in lines(lm)),
                      "a read journalled without its offset is left out of the measure, and the report says so"))
    return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else cli(sys.argv[1:]))
