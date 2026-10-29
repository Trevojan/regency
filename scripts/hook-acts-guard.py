#!/usr/bin/env python3
"""hook-acts-guard.py - PreToolUse guard for every file write (Edit, Write, MultiEdit, NotebookEdit).

Decision record R4.4. One answer per call, first match wins:

  deny  .scope/          the Regent's raw material is read-only for agents          (ids.md, Terms)
  deny  grant store      a JD.md, the grant fingerprints, a grant file the Regent named: only the Regent's
                         words change them, through regency's hooks                  (library/judge.md, R15)
  deny  act rewrite      an existing act is never rewritten: Order ORD-####, gate GT-## / GATE_*,
                         ladder plan LADDER_*, opinion, dated handoff — add a new one   (conventions §7)
  deny  generated block  a hand edit inside the shortcuts:state block of .shortcuts/README.md (F4, R7)
  deny  lock slice       the file is governed by a manifest slice with on_mutation=lock (virtualpath §2)
  deny  banned name      a NEW path carries Base/Abs/Mgr/Helper/Common/Utils           (conventions §14)
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
import shortcuts  # noqa: E402  (guard_generated(): the state block is generated, R7)
import judge  # noqa: E402  (is_store(): the Regent's grants, R15)

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
    if judge.is_store(path):
        return wire.permission("deny", f"{rel} holds the Regent's grants: only the Regent's own words change it, through "
                                       "a 'grant:' line or the Judge's pop-up (/regency:judge, library/judge.md)")
    act = act_kind(path.name)
    if act and path.exists():
        kind, instead = act
        return wire.permission("deny", f"{rel} is a closed act ({kind}); acts are never rewritten (conventions §7): {instead}")
    generated = shortcuts.guard_generated(event)
    if generated:
        return wire.permission("deny", generated)
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
    return None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        root = wire.build_fixture(Path(tmp) / "proj")
        state = Path(tmp) / "state"
        os.environ["REGENCY_HOOK_STATE"] = str(state)
        os.environ["REGENCY_JUDGE_HOME"] = str(Path(tmp) / "home")
        os.environ.pop("REGENCY_JD", None)

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
        cases.append((verdict(respond(ev("Edit", "src/Page.razor"))) == "allow",
                      "no hazard watch: a destructive step earlier locks nothing (R15)"))
        for rel, label in ((g + "JD.md", "the repository's grants"), ("JD.md", "a JD.md at the root"),
                           ("docs/JD.md", "any JD.md")):
            cases.append((verdict(respond(ev("Write", rel))) == "deny", f"grant store: {label} -> deny"))
        rec = judge.record_file()
        rec.parent.mkdir(parents=True, exist_ok=True)
        outside = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": "s1", "cwd": str(root),
                   "tool_input": {"file_path": str(rec)}}
        cases.append((verdict(respond(outside)) == "deny", "grant store: the fingerprint record -> deny"))
        cases.append((verdict(respond(ev("Write", g + "JD-notes.md"))) == "allow", "a name that only starts with JD passes"))
        cases.append((respond({"tool_name": "Bash", "tool_input": {"command": "ls"}}) is None, "other tools pass"))
        index = root / ".guidelines/.shortcuts/README.md"
        index.write_text("# Shortcuts\n\nRead the state block first.\n", encoding="utf-8")
        shortcuts.refresh(shortcuts.locate(root), init=True)
        inside = dict(ev("Edit", ".guidelines/.shortcuts/README.md", sid="s3"))
        inside["tool_input"] = dict(inside["tool_input"], old_string="| latest Order | ORD-0001 |",
                                    new_string="| latest Order | ORD-0009 |")
        outside = dict(inside, tool_input=dict(inside["tool_input"], old_string="Read the state block first.",
                                               new_string="Read it first."))
        cases.append((verdict(respond(inside)) == "deny", "shortcuts state block: hand edit inside -> deny (R7)"))
        cases.append((verdict(respond(outside)) == "allow", "shortcuts index: edit outside the block -> allow"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond, guard=True))
