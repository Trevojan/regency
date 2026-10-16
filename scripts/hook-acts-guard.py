#!/usr/bin/env python3
"""hook-acts-guard.py - PreToolUse guard for every file write (Edit, Write, MultiEdit, NotebookEdit).

Decision record R4.4. One answer per call, first match wins:

  deny  .scope/          the Regent's raw material is read-only for agents          (ids.md, Terms)
  deny  act rewrite      an existing act is never rewritten: Order ORD-####, gate GT-## / GATE_*,
                         ladder plan LADDER_*, opinion, dated handoff — add a new one   (conventions §7)
  deny  lock slice       the file is governed by a manifest slice with on_mutation=lock (virtualpath §2)
  deny  banned name      a NEW path carries Base/Abs/Mgr/Helper/Common/Utils           (conventions §14)
  ask   hazard watch     a destructive step ran this session; writes wait until the Regent says a
                         release verb (set by hook-hazard.py, released by hook-verbs.py; R5.2)
  (nothing)              the write proceeds

Market pattern: tool guardrail with a tripwire (OpenAI Agents SDK), policy-as-code before the side
effect. A broken guard answers 'ask', never a silent pass (hook_wire.serve, guard=True).

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
from conventions_check import BANNED, tokens  # noqa: E402

ACTS = (  # (kind, filename pattern, what to do instead)
    ("Order", re.compile(r"^ORD-\d{4,}"), "an Order is immutable: write a versioned file or an INTAKE-*.md"),
    ("gate sheet", re.compile(r"^(GT-\d{2,}|GATE_)"), "a gate sheet is an act: open a new GT-##"),
    ("ladder plan", re.compile(r"^LADDER_"), "a ladder plan is an act: write the next one"),
    ("opinion", re.compile(r"(?i)opinion"), "an opinion is an act: write a new one"),
    ("dated handoff", re.compile(r"(?i)(handoff.*\d{4}-\d{2}-\d{2}|\d{4}-\d{2}-\d{2}.*handoff)"),
     "a dated handoff is an act: write today's"),
)


def act_kind(name):
    for kind, pattern, instead in ACTS:
        if pattern.search(name):
            return kind, instead
    return None


def new_parts(path, repo):
    """Names that this write would create: the file and any missing directories inside the repo."""
    rel = wire.rel_posix(path, repo)
    if rel is None:
        return []
    out, cur = [], Path(repo)
    for part in rel.split("/"):
        cur = cur / part
        if not cur.exists():
            out.append(part)
    return out


def respond(event):
    if event.get("tool_name") not in wire.WRITE_TOOLS:
        return None
    path = wire.target_path(event)
    if not path:
        return None
    repo = wire.repo_root(path.parent)
    rel = wire.rel_posix(path, repo) or path.as_posix()
    if ".scope" in Path(rel).parts:
        return wire.permission("deny", f"{rel}: .scope/ is the Regent's raw material, read-only for agents (R4.6)")
    act = act_kind(path.name)
    if act and path.exists():
        kind, instead = act
        return wire.permission("deny", f"{rel} is a closed act ({kind}); acts are never rewritten (conventions §7): {instead}")
    vdir = wire.virtual_dir(repo)
    for e in wire.governing(wire.manifest_entries(vdir), rel):
        if e.get("on_mutation") == "lock":
            return wire.permission("deny", f"{rel} is governed by {e['virtual_path']} (lock): the change is refused; "
                                           "the Regent changes the norm first (virtualpath §2)")
    for part in new_parts(path, repo):
        hit = BANNED.intersection(tokens(Path(part).stem if "." in part else part))
        if hit:
            return wire.permission("deny", f"new name '{part}' uses banned token {sorted(hit)} (conventions §14, S3): "
                                           "name it by role")
    watch = wire.load_state(event, "hazard")
    if watch:
        release = "' or '".join(wire.release_words()) or "a release verb"
        return wire.permission("ask", f"hazard watch: '{watch.get('label')}' ran at {watch.get('at')}; "
                                      f"writes wait for the Regent until the Regent says '{release}' (R4.4, R5.2)")
    return None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        root = wire.build_fixture(Path(tmp) / "proj")
        state = Path(tmp) / "state"
        os.environ["REGENCY_HOOK_STATE"] = str(state)

        def ev(tool, rel, sid="s1"):
            key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            return {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid,
                    "cwd": str(root), "tool_input": {key: str(root / rel)}}

        def verdict(answer):
            return (answer or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allow")

        g = ".guidelines/"
        table = [
            ("Write", ".scope/brief.txt", "deny", ".scope read-only"),
            ("Write", ".scope/new.txt", "deny", ".scope new file too"),
            ("Edit", g + ".orders/ORD-0001/ORD-0001.xml", "deny", "existing Order"),
            ("Write", g + ".orders/ORD-0001/INTAKE-01.md", "allow", "intake beside an Order"),
            ("Write", g + ".orders/ORD-0002/ORD-0002.xml", "allow", "a new Order file"),
            ("Edit", g + ".plan/GATE_M01.md", "deny", "existing gate sheet"),
            ("Write", g + ".plan/GT-04.md", "allow", "a new gate sheet"),
            ("Edit", g + ".plan/LADDER_PLAN_PART_1.md", "deny", "existing ladder plan"),
            ("Edit", g + ".plan/HANDOFF_2026-10-01.md", "deny", "dated handoff"),
            ("Edit", g + ".plan/RESUMING.md", "allow", "state file is updated in place"),
            ("Edit", "db/schema.sql", "deny", "lock slice"),
            ("Edit", "src/Page.razor", "allow", "mark_stale slice does not block"),
            ("Write", "src/StringHelper.cs", "deny", "banned token in new file"),
            ("Write", "src/utils/Parser.cs", "deny", "banned token in new directory"),
            ("Write", "src/Parser.cs", "allow", "role name"),
            ("Edit", "src/Database.cs", "allow", "'database' is not the token 'base'"),
            ("NotebookEdit", "nb/Analysis.ipynb", "allow", "notebook path read"),
        ]
        cases = []
        for tool, rel, want, label in table:
            got = verdict(respond(ev(tool, rel)))
            cases.append((got == want, f"{label}: {tool} {rel} -> {got} (want {want})"))
        old = root / "src" / "CommonThing.cs"
        old.write_text("x", encoding="utf-8")
        cases.append((verdict(respond(ev("Edit", "src/CommonThing.cs"))) == "allow",
                      "an existing banned-name file can still be edited"))
        wire.save_state(ev("Edit", "x"), "hazard", {"label": "git reset --hard", "at": "t"})
        cases.append((verdict(respond(ev("Edit", "src/Page.razor"))) == "ask", "hazard watch -> ask"))
        cases.append((verdict(respond(ev("Edit", "src/Page.razor", sid="s2"))) == "allow",
                      "hazard watch is per session"))
        cases.append((respond({"tool_name": "Bash", "tool_input": {"command": "ls"}}) is None, "other tools pass"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond, guard=True))
