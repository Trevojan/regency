#!/usr/bin/env python3
"""hook-journal.py - the checkpoint journal: the latest actions, one JSON line each.

Writes <virtual>/checkpoints.jsonl in an adopted project (one with .shortcuts/.virtual/), keeping only
the latest KEEP lines ("latest actions only", method step generate-shortcuts). hook-resume.py reads the
last line back at SessionStart, so a fresh or compacted context resumes from a trace, not from memory.

Events recorded (all async except SessionEnd, none can block anything; R4.5: no Stop gate):
  PostToolUse        file writes; shell commands only when they change git state or are hazardous
  SubagentStart/Stop role agents entering and leaving
  TaskCreated/Completed  the task list moving
  PreCompact         the context is about to be compacted
  SessionEnd         the session closed

Line shape follows the OpenTelemetry GenAI semantic conventions (Development status), so the journal
can be shipped to any OTel backend unchanged:
  gen_ai.operation.name  execute_tool | invoke_agent
  gen_ai.conversation.id session id      gen_ai.agent.name  agent type, or "main"
  gen_ai.tool.name / gen_ai.tool.call.id
plus regency.event, regency.target (file or command head), regency.unit (M##.S##.T## when present).

Modes:  (no args) hook · --selftest · --tail [N] (print the last N lines of this project's journal)
Pure standard library, Python 3.8+.
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

_spec = importlib.util.spec_from_file_location("hook_hazard", HERE / "hook-hazard.py")
hazard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hazard)

JOURNAL = "checkpoints.jsonl"
KEEP = 200
GIT_STATE = {"commit", "merge", "checkout", "switch", "branch", "tag", "stash", "reset", "rebase", "revert",
             "cherry-pick", "push", "pull", "am", "apply", "restore", "clean", "worktree"}


def git_verb(command):
    for seg in hazard.guard_push.segments(command or ""):
        w = hazard.words(seg)
        if w and hazard.name(w[0]) == "git":
            j = 1
            while j < len(w) and w[j].startswith("-"):
                j += 2 if w[j] in hazard.guard_push.GIT_VALUE_OPTS else 1
            if j < len(w) and w[j] in GIT_STATE:
                return f"git {w[j]}"
    return None


def record(event, repo):
    """The journal line for this event, or None when the event is not worth a checkpoint."""
    name = event.get("hook_event_name")
    line = {"ts": wire.now(), "regency.event": name, "gen_ai.conversation.id": wire.session_key(event),
            "gen_ai.agent.name": event.get("agent_type") or "main"}
    if name == "PostToolUse":
        tool = event.get("tool_name")
        line.update({"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": tool,
                     "gen_ai.tool.call.id": event.get("tool_use_id")})
        if tool in wire.WRITE_TOOLS:
            p = wire.target_path(event)
            line["regency.target"] = (wire.rel_posix(p, repo) or str(p)) if p else None
        elif tool in wire.SHELL_TOOLS:
            cmd = wire.tool_input(event).get("command", "")
            found = hazard.classify(cmd)
            verb = git_verb(cmd)
            if not (found or verb):
                return None
            line["regency.target"] = cmd.strip().splitlines()[0][:160] if cmd.strip() else None
            if found:
                line["regency.hazard"] = found[0]
        else:
            return None
    elif name in ("SubagentStart", "SubagentStop"):
        line.update({"gen_ai.operation.name": "invoke_agent", "regency.phase": name[8:].lower(),
                     "gen_ai.agent.id": event.get("agent_id")})
    elif name in ("TaskCreated", "TaskCompleted"):
        task = event.get("task") if isinstance(event.get("task"), dict) else event
        line["regency.target"] = str(task.get("subject") or task.get("task_subject") or task.get("title") or "")[:160]
    elif name == "PreCompact":
        line["regency.target"] = event.get("trigger") or "auto"
    elif name == "SessionEnd":
        line["regency.target"] = event.get("reason") or "other"
    else:
        return None
    unit = wire.units_in(line.get("regency.target"), json.dumps(wire.tool_input(event))[:2000])
    if unit:
        line["regency.unit"] = unit
    return {k: v for k, v in line.items() if v not in (None, "")}


def append(vdir, line):
    j = vdir / JOURNAL
    with open(j, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    lines = j.read_text(encoding="utf-8").splitlines()
    if len(lines) > KEEP + KEEP // 4:  # trim in batches, not on every write
        wire.atomic_write(j, "\n".join(lines[-KEEP:]) + "\n")


def last(vdir):
    j = vdir / JOURNAL if vdir else None
    if not j or not j.is_file():
        return None
    for raw in reversed(j.read_text(encoding="utf-8").splitlines()):
        try:
            return json.loads(raw)
        except ValueError:
            continue
    return None


def respond(event):
    repo = wire.event_repo(event)
    vdir = wire.virtual_dir(repo)
    if not vdir:
        return None
    line = record(event, repo)
    if line:
        append(vdir, line)
    return None


def tail(n):
    vdir = wire.virtual_dir(wire.repo_root(Path(os.getcwd())))
    j = vdir / JOURNAL if vdir else None
    if not j or not j.is_file():
        print("no checkpoint journal in this project")
        return 0
    for raw in j.read_text(encoding="utf-8").splitlines()[-n:]:
        print(raw)
    return 0


def selftest():
    global KEEP
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        vdir = root / ".guidelines/.shortcuts/.virtual"
        base = {"session_id": "s1", "cwd": str(root)}

        def post(tool, **ti):
            return dict(base, hook_event_name="PostToolUse", tool_name=tool, tool_use_id="toolu_1", tool_input=ti)

        cases = []
        respond(post("Edit", file_path=str(root / "src/Page.razor")))
        got = last(vdir)
        cases.append((got and got.get("regency.target") == "src/Page.razor"
                      and got.get("gen_ai.operation.name") == "execute_tool", "file write recorded, OTel keys"))
        n = len((vdir / JOURNAL).read_text(encoding="utf-8").splitlines())
        respond(post("Bash", command="ls -la"))
        respond(post("Read", file_path=str(root / "src/Page.razor")))
        cases.append((len((vdir / JOURNAL).read_text(encoding="utf-8").splitlines()) == n,
                      "harmless shell and reads are not recorded"))
        respond(post("Bash", command="git commit -m 'feat: M03.S02.T04 layout'"))
        got = last(vdir)
        cases.append((got.get("regency.unit") == "M03.S02.T04", "git commit recorded with its unit"))
        respond(post("Bash", command="rm -rf build"))
        cases.append((last(vdir).get("regency.hazard") == "delete", "hazardous command tagged"))
        respond(dict(base, hook_event_name="SubagentStart", agent_type="qa", agent_id="a1"))
        cases.append((last(vdir).get("gen_ai.operation.name") == "invoke_agent"
                      and last(vdir).get("gen_ai.agent.name") == "qa", "subagent start recorded"))
        respond(dict(base, hook_event_name="TaskCompleted", task_subject="M01.S01.T02 parser"))
        cases.append((last(vdir).get("regency.unit") == "M01.S01.T02", "task completion recorded"))
        respond(dict(base, hook_event_name="PreCompact", trigger="auto"))
        cases.append((last(vdir).get("regency.event") == "PreCompact", "compaction checkpoint"))
        KEEP = 10
        for i in range(30):
            respond(post("Write", file_path=str(root / f"src/F{i}.cs")))
        size = len((vdir / JOURNAL).read_text(encoding="utf-8").splitlines())
        cases.append((size <= KEEP + KEEP // 4 and last(vdir).get("regency.target") == "src/F29.cs",
                      f"journal trimmed to the latest actions ({size} lines)"))
        respond(dict(base, cwd=str(bare), hook_event_name="SessionEnd", reason="other"))
        cases.append((not (bare / ".guidelines/.shortcuts/.virtual").exists(), "adoption gate holds"))
        return wire.check(cases)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if "--tail" in a:
        i = a.index("--tail")
        sys.exit(tail(int(a[i + 1]) if i + 1 < len(a) and a[i + 1].isdigit() else 10))
    sys.exit(wire.serve(respond))
