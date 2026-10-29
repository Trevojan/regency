#!/usr/bin/env python3
"""hook-shortcuts.py - SessionEnd: rewrite the generated state block of the entry index.

Decision records R7.3 and R12 (library/shortcuts.md §5). At the end of a session in an adopted project (one
with .shortcuts/.virtual/), runs shortcuts.refresh(): the block between the shortcuts:state markers in
.shortcuts/README.md is rewritten when the state moved, and left alone when it did not. Without markers nothing
is written (shortcuts.py refresh --init appends them once). No scan here: SessionEnd hooks share a 1.5 s budget,
so only the index file itself is hashed, and only when the block was rewritten.

A recorder: never blocks, never answers, errors go to stderr only (hook_wire.serve).

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
import shortcuts  # noqa: E402  (refresh(): the one writer of the state block)


def respond(event):
    if event.get("hook_event_name") not in (None, "SessionEnd"):
        return None
    place = shortcuts.locate(event.get("cwd") or os.getcwd())
    if place.vdir:
        shortcuts.refresh(place)
    return None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        idx = root / ".guidelines/.shortcuts/README.md"
        idx.write_text("# Shortcuts\n", encoding="utf-8")

        def end(base):
            return respond({"hook_event_name": "SessionEnd", "reason": "other", "cwd": str(base)})

        cases = []
        end(root)
        cases.append((idx.read_text(encoding="utf-8") == "# Shortcuts\n", "no markers: the index is left alone"))
        shortcuts.refresh(shortcuts.locate(root), init=True)
        led = root / ".guidelines/.shortcuts/.virtual/ongoing.json"
        led.write_text(led.read_text(encoding="utf-8").replace('"state": "backlog"', '"state": "ongoing"', 1),
                       encoding="utf-8")
        out = end(root)
        cases.append((out is None and "2 ongoing" in idx.read_text(encoding="utf-8"), "state moved: block rewritten, silent"))
        before = idx.stat().st_mtime_ns
        end(root)
        cases.append((idx.stat().st_mtime_ns == before, "state unchanged: nothing written"))
        cases.append((respond({"hook_event_name": "PreCompact", "cwd": str(root)}) is None, "other events: ignored"))
        end(bare)
        cases.append((not (bare / ".guidelines/.shortcuts").exists(), "adoption gate: nothing written without .virtual"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond))
