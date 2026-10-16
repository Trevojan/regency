#!/usr/bin/env python3
"""hook-resume.py - SessionStart: one resume slice line, so work resumes from traces (conventions §10).

Decision record R4.2. On startup, resume, clear and compact, for a project that has guidelines:

  regency resume · ledger 1 ongoing / 1 review / 1 blocked / 2 backlog · STALE 1 · latest Order ORD-0001
  · last checkpoint 2026-10-09T20:10-03:00 Edit src/Page.razor (M01.D01.T01) · first peek: vp.py ongoing, vp.py trace

A project without guidelines gets nothing (the plugin is silent outside the Regent's projects).
SessionStart plain output becomes context; this script answers with additionalContext JSON instead,
so the line is wrapped as a system reminder and stays under the 10 000-character cap.

Market pattern: resuming a thread from its last checkpoint (LangGraph checkpointer + thread_id),
read as state, never as an instruction.

Modes:  (no args) hook · --selftest · --print (the line for the current directory)
Pure standard library, Python 3.8+.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

_spec = importlib.util.spec_from_file_location("hook_journal", HERE / "hook-journal.py")
journal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(journal)

STATES = ("ongoing", "review", "blocked", "backlog")
MAX_SCAN = 2000  # guideline files scanned for STALE lines


def ledger_part(vdir):
    led = vdir / "ongoing.json" if vdir else None
    if not led or not led.is_file():
        return "ledger absent" if vdir else "no .shortcuts/.virtual (lineage and ledger not adopted)"
    try:
        items = json.loads(led.read_text(encoding="utf-8-sig")).get("items", [])
    except ValueError:
        return "ledger UNREADABLE (vp.py ongoing)"
    counts = {s: sum(1 for it in items if it.get("state") == s) for s in STATES}
    return "ledger " + " / ".join(f"{counts[s]} {s}" for s in STATES)


def stale_count(g):
    n = 0
    for i, p in enumerate(g.rglob("*.md")):
        if i >= MAX_SCAN:
            break
        if not wire.SKIP_PARTS.intersection(p.relative_to(g).parts):
            n += p.read_text(encoding="utf-8-sig", errors="replace").count(wire.STALE_MARK)
    return n


def latest_order(g):
    od = g / ".orders"
    nums = sorted(p.name for p in od.glob("ORD-*") if re.match(r"^ORD-\d{4,}$", p.name)) if od.is_dir() else []
    return f"latest Order {nums[-1]}" if nums else None


def checkpoint_part(vdir):
    c = journal.last(vdir)
    if not c:
        return None
    what = c.get("gen_ai.tool.name") or c.get("regency.event")
    unit = f" ({c['regency.unit']})" if c.get("regency.unit") else ""
    return f"last checkpoint {c.get('ts', '?')} {what} {c.get('regency.target', '')}{unit}".rstrip()


def line_for(repo, source=None):
    g = wire.guidelines_root(repo)
    if not g:
        return None
    vdir = wire.virtual_dir(repo)
    stale = stale_count(g)
    return wire.one_line(f"regency resume{' after ' + source if source in ('compact', 'clear') else ''}",
                         ledger_part(vdir), f"STALE {stale}" if stale else None, latest_order(g),
                         checkpoint_part(vdir), "first peek: vp.py ongoing, vp.py trace")


def respond(event):
    line = line_for(wire.event_repo(event), event.get("source"))
    return wire.context("SessionStart", line) if line else None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        plain = Path(tmp) / "plain"
        (plain / ".git").mkdir(parents=True)
        arch = root / ".guidelines/.decisions/ARCHITECTURE.md"
        arch.write_text(arch.read_text(encoding="utf-8") + "\n[warn'STALE' on='2026-10-09' changed='x']\n", encoding="utf-8")
        journal.respond({"hook_event_name": "PostToolUse", "tool_name": "Edit", "session_id": "s", "cwd": str(root),
                         "tool_input": {"file_path": str(root / "src/Page.razor")}})

        def text(answer):
            return (answer or {}).get("hookSpecificOutput", {}).get("additionalContext", "")

        out = text(respond({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(root)}))
        cases = [
            ("ledger 1 ongoing / 1 review / 1 blocked / 2 backlog" in out, "ledger counted by state"),
            ("STALE 1" in out, "STALE lines counted"),
            ("latest Order ORD-0001" in out, "latest Order named"),
            ("Edit src/Page.razor" in out, "last checkpoint read back"),
            ("\n" not in out and len(out) <= wire.MAX_LINE, "one slice line, capped"),
            ("after compact" in text(respond({"hook_event_name": "SessionStart", "source": "compact", "cwd": str(root)})),
             "compaction is named"),
            ("not adopted" in text(respond({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(bare)})),
             "guidelines without .virtual: says so"),
            (respond({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(plain)}) is None,
             "no guidelines: silent"),
        ]
        return wire.check([(ok, label) for ok, label in cases])


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if "--print" in a:
        print(line_for(wire.repo_root(Path(os.getcwd()))) or "no guidelines here")
        sys.exit(0)
    sys.exit(wire.serve(respond))
