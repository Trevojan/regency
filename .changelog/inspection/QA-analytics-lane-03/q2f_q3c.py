"""2b/2f at any tree; 3c: Post with tool_input.answers keyed by the single-spaced question. Usage: <scripts dir>"""
import sys, os, tempfile, importlib.util
from pathlib import Path
sys.dont_write_bytecode = True
S = sys.argv[1]; sys.path.insert(0, S)
import hook_wire as wire, elicit, analytics as an
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"


def hook(base, phase, qs, answers=None):
    ti = {"questions": qs}
    if answers is not None:
        ti["answers"] = answers
    out = he.respond({"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(base), "session_id": "x", "tool_input": ti})
    h = (out or {}).get("hookSpecificOutput") or {}
    return h.get("permissionDecision") or ("ctx: " + h.get("additionalContext", "")[:90] if h else "allowed/none")


base = wire.build_fixture(Path(tmp) / "p")
st = elicit.Store(base); sid = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "done")["session_id"]
elicit.record_answer(st, sid, "Q_RULE", "B"); st.close()
one = lambda q, h, ls: [{"question": q, "header": h, "multiSelect": False, "options": [{"label": l, "description": "d"} for l in ls]}]
print("2b unrelated 'Rule' A/B:", hook(base, "PreToolUse", one("Which lint rule set?", "Rule", ["A", "B"])))
print("2f engine Q_RULE reworded+re-optioned:", hook(base, "PreToolUse", one("What rule governs it?", "Rule", ["A", "C"])))
repo = an.fixture_repo(Path(tmp) / "an"); (repo / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
an.record(repo, an.envelope(an.plan(repo, "baseline"), [an.sample(title="approve()  offers no reversal")]), create=True)
st = elicit.Store(repo); s = elicit.start(st, an.triage_schema(repo), "triage-2026-11-18")["session_id"]
ask = elicit.next_questions(st, s)["ask"]["questions"]; st.close()
print("3c Post, answers keyed single-spaced:", hook(repo, "PostToolUse", ask, {" ".join(ask[0]["question"].split()): "Recycle"}))
