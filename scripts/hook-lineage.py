#!/usr/bin/env python3
"""hook-lineage.py - PostToolUse after every file write: fingerprint the file, mark governing norms STALE.

Decision records R4.3 and R12. For a file written inside an adopted project (one with .shortcuts/.virtual/):

  1. fingerprint   shortcuts.record(): the file's row in the prints table of the one store, idx.py's
                   <virtual>/index.sqlite (sha256, size, mtime, the hash it replaced, when, which session;
                   library/shortcuts.md §3)
  2. index         with an index (idx.py build), re-index the file and diff its nodes: what was modified,
                   added, removed, or only reformatted (virtualpath §6)
  3. lineage       for each manifest slice whose refers_to cites the file, and each slice whose anchor a
                   changed node cites:
                     mark_stale  write one STALE line right under the anchor (once per changed file) when a
                                 governed node changed beyond whitespace - or on any write when there is no
                                 index or the index never saw the file (the conservative rule, virtualpath §2);
                                 only a human removes it; the norm doc is then
                                 re-indexed and recorded too, so the STALE line never reads as drift
                     ledger_row  never written inside a table: reported in the context line instead
                     lock        cannot happen here (hook-acts-guard.py refused the write)
  4. one context line telling the agent which slices are now out of date (virtualpath §5)

Files inside .shortcuts/.virtual/ and outside the repository are ignored. A project without
.shortcuts/.virtual/ is never touched (adoption gate, hook_wire).

Market pattern: content-addressed state (fingerprints) + dependency invalidation, the build-system
and data-lineage answer to "which derived facts did this change make stale?".

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
import idx  # noqa: E402  (the exact index: node diff, touches())
import shortcuts  # noqa: E402  (record(): the one writer of a file's print)
import vp  # noqa: E402  (resolve(): the one slice resolver)


def stale_line(rel, nodes=None):
    at = f" nodes='{','.join(nodes[:6])}'" if nodes else ""
    return (f"[warn'STALE' on='{wire.today()}' changed='{rel}'{at} by='hook-lineage'] "
            "check this slice against the code; only a human removes this line")


def mark(guidelines, entry, rel, nodes=None):
    """Return 'written', 'already', 'unresolved' or 'reported' for one mark_stale slice."""
    ok, start, end, lines = vp.resolve(guidelines, entry)
    if not ok:
        return "unresolved"
    if entry.get("selector_type") == "ledger_row":
        return "reported"
    needle = f"changed='{rel}'"
    if any(wire.STALE_MARK in l and needle in l for l in lines[start:end]):
        return "already"
    lines.insert(start + 1, stale_line(rel, nodes))
    f, _ = vp.split_vpath(entry["virtual_path"])
    wire.atomic_write(guidelines / f, "\n".join(lines))
    return "written"


def respond(event):
    if event.get("tool_name") not in wire.WRITE_TOOLS:
        return None
    path = wire.target_path(event)
    if not path:
        return None
    repo = wire.repo_root(path.parent)
    vdir = wire.virtual_dir(repo)
    rel = wire.rel_posix(path, repo)
    if not vdir or not rel or wire.rel_posix(path, vdir) is not None or rel.startswith(".git/"):
        return None
    place = shortcuts.locate(repo)
    shortcuts.record(place, path, session=wire.session_key(event), source="hook")
    guidelines = vdir.parent.parent
    entries = wire.manifest_entries(vdir)
    diff = idx.update_hook(vdir, repo, rel)
    targets = wire.governing(entries, rel)
    targets += [e for e in idx.cited_entries(entries, diff) if e not in targets]
    notes, unchanged, touched_docs = [], [], set()
    for e in targets:
        if e.get("on_mutation") != "mark_stale":
            continue
        hit, nodes = idx.touches(e, rel, diff) if diff is not None else (True, [])
        if not hit:
            unchanged.append(e["virtual_path"])
            continue
        result = mark(guidelines, e, rel, nodes)
        if result == "written":
            touched_docs.add(vp.split_vpath(e["virtual_path"])[0])
        notes.append({"written": f"{e['virtual_path']} (STALE written)",
                      "already": f"{e['virtual_path']} (already STALE for this file)",
                      "reported": f"{e['virtual_path']} (ledger row: check it by hand)",
                      "unresolved": f"{e['virtual_path']} (slice DOES NOT RESOLVE: vp.py check)"}[result])
    for doc in touched_docs:  # the STALE line moved bytes: keep the index exact, and the print current
        idx.update_hook(vdir, repo, wire.rel_posix(guidelines / doc, repo))
        shortcuts.record(place, guidelines / doc, session=wire.session_key(event), source="lineage")
    if not notes and not unchanged:
        return None
    if diff is None:
        how = "index absent: file-level rule (idx.py build)"
    elif not diff.get("known"):
        how = "new to the index: counted as changed"
    elif diff.get("whitespace_only"):
        how = "whitespace only"
    else:
        how = f"nodes ~{len(diff['modified'])} +{len(diff['added'])} -{len(diff['removed'])}"
    return wire.context("PostToolUse", wire.one_line(
        f"lineage: {rel} changed", how, "out of date: " + "; ".join(notes) if notes else None,
        "governed nodes unchanged: " + ", ".join(unchanged) if unchanged else None,
        "a human clears STALE; never edit the norm to match the code" if notes else None))


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        vdir = root / ".guidelines/.shortcuts/.virtual"
        arch = root / ".guidelines/.decisions/ARCHITECTURE.md"

        def ev(base, rel, tool="Edit"):
            return {"hook_event_name": "PostToolUse", "tool_name": tool, "session_id": "sess-1234567890",
                    "cwd": str(base), "tool_input": {"file_path": str(base / rel)}}

        def prints():
            con = idx.connect(vdir)
            rows = {r["path"]: dict(r) for r in con.execute("SELECT * FROM prints")} if con else {}
            if con:
                con.close()
            return rows

        cases = []
        out = respond(ev(root, "src/Page.razor"))
        text = arch.read_text(encoding="utf-8").split("\n")
        i = text.index("## §layout-stable — layout")
        cases.append((wire.STALE_MARK in text[i + 1] and "changed='src/Page.razor'" in text[i + 1],
                      "STALE line written right under the anchor"))
        cases.append((bool(out) and "STALE written" in json.dumps(out), "context line names the slice"))
        fps = prints()
        cases.append((fps.get("src/Page.razor", {}).get("sha256") == wire.sha256(root / "src/Page.razor")
                      and fps["src/Page.razor"]["source"] == "hook" and fps["src/Page.razor"]["session"] == "sess-123",
                      "fingerprint matches the file, in the prints table, with its session"))
        norm = fps.get(".guidelines/.decisions/ARCHITECTURE.md", {})
        cases.append((norm.get("source") == "lineage" and norm.get("sha256") == wire.sha256(arch),
                      "the norm doc's STALE write is recorded, so it never reads as drift"))
        con = idx.connect(vdir)
        partial = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        con.close()
        cases.append((not (vdir / "fingerprints.json").exists() and not partial,
                      "one store: no fingerprints.json, and no partial index"))
        respond(ev(root, "src/Page.razor"))
        cases.append((arch.read_text(encoding="utf-8").count(wire.STALE_MARK) == 1, "second edit: no duplicate STALE"))
        vp_check = vp.resolve(root / ".guidelines", {"virtual_path": ".decisions/ARCHITECTURE.md#layout-stable"})
        cases.append((vp_check[0], "slice still resolves after the insert"))
        before = (root / ".guidelines/.plan/BACKLOG.md").read_text(encoding="utf-8")
        out = respond(ev(root, "src/Ledger.cs"))
        cases.append((before == (root / ".guidelines/.plan/BACKLOG.md").read_text(encoding="utf-8")
                      and "ledger row" in json.dumps(out), "ledger_row: table untouched, reported"))
        (root / "src/Other.cs").write_text("class Other {}\n", encoding="utf-8")
        cases.append((respond(ev(root, "src/Other.cs", tool="Write")) is None and "src/Other.cs" in prints(),
                      "ungoverned file: fingerprinted, silent"))
        cases.append((respond(ev(root, ".guidelines/.shortcuts/.virtual/ongoing.json")) is None
                      and ".guidelines/.shortcuts/.virtual/ongoing.json" not in prints(),
                      "the virtual folder itself is ignored"))
        cases.append((respond(ev(bare, "src/Page.razor")) is None
                      and not (bare / ".guidelines/.shortcuts/.virtual").exists(),
                      "adoption gate: no .virtual -> nothing written"))

        # node-exact staleness, once an index exists (virtualpath §2, §6)
        ix = wire.build_fixture(Path(tmp) / "indexed")
        ivd = ix / ".guidelines/.shortcuts/.virtual"
        iarch = ix / ".guidelines/.decisions/ARCHITECTURE.md"
        (ix / "src/Board.cs").write_text("public class Board\n{\n    private int _n;\n\n    public int Count()\n"
                                         "    {\n        return _n;\n    }\n}\n", encoding="utf-8")
        (ix / "src/split.py").write_text("# §layout-stable governs this\ndef split(a, b):\n    return a\n\n\n"
                                         "def join(x):\n    return x\n", encoding="utf-8")
        idx.build(ix, ivd)
        con = idx.connect(ivd)
        count_id = con.execute("SELECT id FROM nodes WHERE path='src/Board.cs' AND key='public int Count()'").fetchone()[0]
        con.close()
        man = ivd / "manifest.json"
        data = json.loads(man.read_text(encoding="utf-8"))
        data["virtual_context"].append({"virtual_path": ".decisions/ARCHITECTURE.md#Other",
                                        "refers_to": [f"src/Board.cs#n:{count_id}"],
                                        "selector_type": "markdown_anchor", "on_mutation": "mark_stale"})
        man.write_text(json.dumps(data), encoding="utf-8")

        def stales():
            return iarch.read_text(encoding="utf-8").count(wire.STALE_MARK)

        page = ix / "src/Page.razor"
        page.write_text(page.read_text(encoding="utf-8").replace("<p>", "<p>  "), encoding="utf-8")
        out = json.dumps(respond(ev(ix, "src/Page.razor")))
        cases.append((stales() == 0 and "whitespace only" in out and "unchanged" in out,
                      "index: a whitespace-only write marks nothing and says why"))
        page.write_text("<p>page two</p>\n", encoding="utf-8")
        respond(ev(ix, "src/Page.razor"))
        cases.append((stales() == 1 and "nodes='" in iarch.read_text(encoding="utf-8"),
                      "index: a content change writes STALE with the node ids"))
        board = ix / "src/Board.cs"
        board.write_text(board.read_text(encoding="utf-8").replace("_n;\n\n", "_n = 1;\n\n", 1), encoding="utf-8")
        out = json.dumps(respond(ev(ix, "src/Board.cs")))
        cases.append((stales() == 1 and "#Other" in out and "unchanged" in out,
                      "index: a node selector ignores a change to another member"))
        board.write_text(board.read_text(encoding="utf-8").replace("return _n;", "return _n + 1;"), encoding="utf-8")
        respond(ev(ix, "src/Board.cs"))
        text = iarch.read_text(encoding="utf-8")
        cases.append((stales() == 2 and f"nodes='{count_id}'" in text, "index: the selected member changing marks its slice"))
        sp = ix / "src/split.py"
        sp.write_text(sp.read_text(encoding="utf-8").replace("return a\n", "return a or b\n"), encoding="utf-8")
        respond(ev(ix, "src/split.py"))
        cases.append((stales() == 3 and "changed='src/split.py'" in iarch.read_text(encoding="utf-8"),
                      "index: code that cites §layout-stable governs it without a manifest line"))
        sp.write_text(sp.read_text(encoding="utf-8").replace("return x", "return x * 2"), encoding="utf-8")
        respond(ev(ix, "src/split.py"))
        cases.append((stales() == 3, "index: an uncited sibling in the citing file marks nothing"))
        con = idx.connect(ivd)
        sha = con.execute("SELECT sha FROM files WHERE path='.guidelines/.decisions/ARCHITECTURE.md'").fetchone()[0]
        con.close()
        cases.append((sha == wire.sha256(iarch), "index: the norm file is re-indexed after a STALE line moves its bytes"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond))
