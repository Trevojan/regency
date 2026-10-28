#!/usr/bin/env python3
"""hook-lineage.py - PostToolUse after every file write: fingerprint the file, mark governing norms STALE.

Decision records R4.3 and R7. For a file written inside an adopted project (one with .shortcuts/.virtual/):

  1. fingerprint   shortcuts.record(): the file's row in <virtual>/shortcuts.db (sha256, size, mtime,
                   the hash it replaced, when, which session) and, for a guideline doc, its nodes
  2. lineage       for each manifest slice whose refers_to cites the file:
                     mark_stale  write one STALE line right under the anchor (once per changed file);
                                 only a human removes it (virtualpath §2); the norm doc is recorded
                                 too, so the hook's own write never reads as drift
                     ledger_row  never written inside a table: reported in the context line instead
                     lock        cannot happen here (hook-acts-guard.py refused the write)
  3. one context line telling the agent which slices are now out of date (virtualpath §5)

Files inside .shortcuts/.virtual/ and outside the repository are ignored. A project without
.shortcuts/.virtual/ is never touched (adoption gate, hook_wire).

Market pattern: content-addressed state (fingerprints) + dependency invalidation, the build-system
and data-lineage answer to "which derived facts did this change make stale?".

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
import shortcuts  # noqa: E402  (record(): the one fingerprint store)
import vp  # noqa: E402  (resolve(): the one slice resolver)


def stale_line(rel):
    return (f"[warn'STALE' on='{wire.today()}' changed='{rel}' by='hook-lineage'] "
            "check this slice against the code; only a human removes this line")


def mark(guidelines, entry, rel):
    """Return 'written', 'already', 'unresolved' or 'reported' for one mark_stale slice."""
    ok, start, end, lines = vp.resolve(guidelines, entry)
    if not ok:
        return "unresolved"
    if entry.get("selector_type") == "ledger_row":
        return "reported"
    needle = f"changed='{rel}'"
    if any(wire.STALE_MARK in l and needle in l for l in lines[start:end]):
        return "already"
    lines.insert(start + 1, stale_line(rel))
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
    session = wire.session_key(event)
    shortcuts.record(place, path, session=session, source="hook")
    guidelines = vdir.parent.parent
    notes = []
    for e in wire.governing(wire.manifest_entries(vdir), rel):
        if e.get("on_mutation") != "mark_stale":
            continue
        result = mark(guidelines, e, rel)
        if result == "written":
            shortcuts.record(place, guidelines / vp.split_vpath(e["virtual_path"])[0], session=session, source="lineage")
        notes.append({"written": f"{e['virtual_path']} (STALE written)",
                      "already": f"{e['virtual_path']} (already STALE for this file)",
                      "reported": f"{e['virtual_path']} (ledger row: check it by hand)",
                      "unresolved": f"{e['virtual_path']} (slice DOES NOT RESOLVE: vp.py check)"}[result])
    if not notes:
        return None
    return wire.context("PostToolUse", wire.one_line(f"lineage: {rel} changed", "out of date: " + "; ".join(notes),
                                                     "a human clears STALE; never edit the norm to match the code"))


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

        def files():
            con = sqlite3.connect(str(vdir / shortcuts.DB_NAME))
            try:
                return {r[0]: r[1:] for r in con.execute("SELECT path, sha256, source FROM files")}
            finally:
                con.close()

        cases = []
        out = respond(ev(root, "src/Page.razor"))
        text = arch.read_text(encoding="utf-8").split("\n")
        i = text.index("## §layout-stable — layout")
        cases.append((wire.STALE_MARK in text[i + 1] and "changed='src/Page.razor'" in text[i + 1],
                      "STALE line written right under the anchor"))
        cases.append((bool(out) and "STALE written" in json.dumps(out), "context line names the slice"))
        cases.append((files().get("src/Page.razor", (None,))[0] == wire.sha256(root / "src/Page.razor"),
                      "fingerprint in the store matches the file"))
        cases.append((files().get(".guidelines/.decisions/ARCHITECTURE.md", (None, None))[1] == "lineage"
                      and not [d for d in shortcuts.drift(shortcuts.locate(root)) if d[0] in ("drift", "gone")],
                      "the hook's own STALE write is recorded: no drift"))
        respond(ev(root, "src/Page.razor"))
        cases.append((arch.read_text(encoding="utf-8").count(wire.STALE_MARK) == 1, "second edit: no duplicate STALE"))
        vp_check = vp.resolve(root / ".guidelines", {"virtual_path": ".decisions/ARCHITECTURE.md#layout-stable"})
        cases.append((vp_check[0], "slice still resolves after the insert"))
        before = (root / ".guidelines/.plan/BACKLOG.md").read_text(encoding="utf-8")
        out = respond(ev(root, "src/Ledger.cs"))
        cases.append((before == (root / ".guidelines/.plan/BACKLOG.md").read_text(encoding="utf-8")
                      and "ledger row" in json.dumps(out), "ledger_row: table untouched, reported"))
        (root / "src/Other.cs").write_text("class Other {}\n", encoding="utf-8")
        cases.append((respond(ev(root, "src/Other.cs", tool="Write")) is None and "src/Other.cs" in files(),
                      "ungoverned file: fingerprinted, silent"))
        cases.append((respond(ev(root, ".guidelines/.shortcuts/.virtual/ongoing.json")) is None
                      and ".guidelines/.shortcuts/.virtual/ongoing.json" not in files(),
                      "the virtual folder itself is ignored"))
        cases.append((not (vdir / "fingerprints.json").exists(), "no fingerprints.json is written any more"))
        cases.append((respond(ev(bare, "src/Page.razor")) is None
                      and not (bare / ".guidelines/.shortcuts/.virtual").exists(),
                      "adoption gate: no .virtual -> nothing written"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond))
