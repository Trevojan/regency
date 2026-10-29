#!/usr/bin/env python3
"""hook-judge.py - the Judge's pop-up: the Regent's answer to a grant question becomes the grant (R15).

The Judge (/regency:judge) puts each proposed grant to the Regent as one AskUserQuestion question:

  header    "JD grant"
  question  the grant, in backticks:   Grant `delete, discard Herança/** -- the old layout goes`?
  options   Session · Repo · This machine · No     (the Regent may type a .md path instead: "Other")

PreToolUse   AskUserQuestion   deny a Judge question that arrives with its answers already filled in:
                               the answers are the Regent's, never the agent's (conventions §1)
PostToolUse  AskUserQuestion   for each Judge question the Regent answered with a scope, record the grant
                               where the answer says (judge.record); "No" records nothing

The grant's text is the agent's proposal and the Regent reads it before answering; the scope is the
Regent's pick. A typed 'grant:' line (hook-verbs.py) is the other way in, and the one every surface honours.

Not yet seen live: where a surface puts the answers in the PostToolUse event. This script reads
tool_input.answers, then tool_response.answers, then a 'question'="answer" text (library/maintaining.md).

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
import judge  # noqa: E402

HEADER = "jd grant"
SPEC = re.compile(r"`([^`]+)`")
SCOPES = {"session": "session", "this session": "session", "repo": "repo", "repository": "repo",
          "this repo": "repo", "machine": "machine", "this machine": "machine", "permanent": "machine"}


def judge_questions(event):
    qs = wire.tool_input(event).get("questions")
    return [q for q in qs if isinstance(q, dict) and str(q.get("header", "")).strip().lower() == HEADER] \
        if isinstance(qs, list) else []


def answers(event):
    """{question text: answer text}, from wherever the surface put them."""
    for holder in (wire.tool_input(event), event.get("tool_response")):
        if isinstance(holder, dict) and isinstance(holder.get("answers"), dict):
            return {str(k): str(v) for k, v in holder["answers"].items()}
    resp = event.get("tool_response")
    text = resp if isinstance(resp, str) else ""
    if isinstance(resp, dict):
        text = " ".join(str(c.get("text", "")) for c in resp.get("content", []) if isinstance(c, dict)) \
            if isinstance(resp.get("content"), list) else str(resp.get("content") or resp.get("result") or "")
    return {m.group(1): m.group(2) for m in re.finditer(r'"([^"]+)"="([^"]*)"', text)}


def scope_of(answer):
    """(scope, path) for the Regent's pick; None for "No" and for anything that names no scope."""
    a = (answer or "").strip().strip("`").strip()
    low = a.lower().rstrip(".!")
    if low in SCOPES:
        return SCOPES[low], None
    if a.lower().endswith(".md"):
        return "path", a
    return None


def respond(event):
    if event.get("tool_name") != "AskUserQuestion":
        return None
    qs = judge_questions(event)
    if not qs:
        return None
    phase = event.get("hook_event_name")
    if phase == "PreToolUse":
        if wire.tool_input(event).get("answers"):
            return wire.permission("deny", "a Judge question arrived with its answers filled in: the answers are the "
                                           "Regent's alone. Ask again without 'answers' (library/judge.md)")
        return None
    if phase != "PostToolUse":
        return None
    got = answers(event)
    repo = wire.repo_root(Path(event.get("cwd") or os.getcwd()))
    parts = []
    for q in qs:
        text = str(q.get("question", ""))
        m = SPEC.search(text)
        pick = scope_of(got.get(text))
        if not m or pick is None:
            continue
        try:
            spec = judge.parse_spec(m.group(1))
            spec["scope"], spec["path"] = pick
            gid, where = judge.record(event, repo, spec, "Regent: pop-up")
            parts.append(f"grant {gid} recorded ({where}): {', '.join(spec['how'])} {' '.join(spec['where'])} -- {spec['why']}")
        except ValueError as e:
            parts.append(f"grant not recorded ({m.group(1)[:60]}): {e}")
    if qs and not got:
        parts.append("no answers reached the hook from this surface: ask the Regent for the 'grant:' line instead")
    return wire.context("PostToolUse", wire.one_line(*parts)) if parts else None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        os.environ["REGENCY_JUDGE_HOME"] = str(Path(tmp) / "home")
        os.environ.pop("REGENCY_JD", None)
        root = wire.build_fixture(Path(tmp) / "proj")
        q1 = "Grant `delete, discard Herança/** -- the old layout goes`?"
        q2 = "Grant `history ** -- rebase freely`?"
        q3 = "Grant `layout ** -- worktrees`?"
        q4 = "Grant `delete build/** -- output`?"
        questions = [{"header": "JD grant", "question": q, "options": [{"label": "Session"}, {"label": "Repo"},
                                                                         {"label": "This machine"}, {"label": "No"}],
                      "multiSelect": False} for q in (q1, q2, q3, q4)]

        def ev(phase, ans=None, resp=None, sid="s1", qs=None):
            ti = {"questions": qs if qs is not None else questions}
            if ans is not None:
                ti["answers"] = ans
            e = {"hook_event_name": phase, "tool_name": "AskUserQuestion", "session_id": sid, "cwd": str(root),
                 "tool_input": ti}
            if resp is not None:
                e["tool_response"] = resp
            return e

        def verdict(a):
            return (a or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allow")

        def ctx(a):
            return (a or {}).get("hookSpecificOutput", {}).get("additionalContext", "")

        cases = [
            (verdict(respond(ev("PreToolUse"))) == "allow", "pre: a Judge question asks freely"),
            (verdict(respond(ev("PreToolUse", ans={q1: "Repo"}))) == "deny", "pre: answers filled in by the agent -> deny"),
            (respond(ev("PreToolUse", ans={"x": "y"}, qs=[{"header": "Scope", "question": "x"}])) is None,
             "pre: other questions are not the Judge's"),
        ]
        out = ctx(respond(ev("PostToolUse", ans={q1: "Repo", q2: "Session", q3: "No", q4: "notes/GRANTS.md"})))
        cases.append(("JD-R01" in out and "JD-S01" in out and "JD-P01" in out and "worktrees" not in out,
                      f"post: each answered scope is recorded, 'No' records nothing ({out[:110]})"))
        cases.append((judge.covers({"session_id": "s9"}, root, "delete", [root / "Herança" / "a"]) is not None
                      and judge.covers({"session_id": "s1"}, root, "history", []) is not None
                      and judge.covers({"session_id": "s1"}, root, "layout", []) is None,
                      "post: the grants hold where the Regent put them"))
        out = ctx(respond(ev("PostToolUse", resp={"answers": {q2: "This machine"}}, sid="s2")))
        cases.append(("JD-M01" in out, "post: answers read from tool_response.answers too"))
        text = f'User has answered your questions: "{q4}"="Session". You can now continue.'
        out = ctx(respond(ev("PostToolUse", resp={"content": [{"type": "text", "text": text}]}, sid="s3")))
        cases.append(("JD-S01" in out and judge.covers({"session_id": "s3"}, root, "delete", [root / "build"]),
                      "post: answers read from the result text"))
        out = ctx(respond(ev("PostToolUse", sid="s4")))
        cases.append(("'grant:' line" in out, "post: no answers reached the hook -> the typed line is named"))
        bad = [{"header": "JD grant", "question": "Grant `edit src/** -- x`?"}]
        out = ctx(respond(ev("PostToolUse", ans={"Grant `edit src/** -- x`?": "Repo"}, qs=bad, sid="s5")))
        cases.append(("not recorded" in out, "post: a grant the Judge may not make is reported, not recorded"))
        cases.append((respond({"hook_event_name": "PostToolUse", "tool_name": "Bash"}) is None, "other tools pass"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond, guard=True))
