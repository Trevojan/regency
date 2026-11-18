#!/usr/bin/env python3
"""hook-elicit.py - the pop-up side of the elicitation engine: an engine question is asked as the engine says, once.

library/elicitation.md §5. A thin adapter: every decision is scripts/elicit.py's. A pop-up question is an engine
question when an open elicitation session's schema has a question with that header and the entry carries either its
current wording (spaces aside) or only labels of its options; every other question passes untouched, and nothing is
recorded for it. Several open sessions holding the question: it belongs to the one whose rendering it carries, then to
the one that rendered it last, and to no other.

PreToolUse   AskUserQuestion   deny an engine question that is already answered under unchanged upstream values
                               and not reopened on the Regent's word (counted as repeat_denied), blocked, not
                               applicable, worded or optioned otherwise
                               than the engine renders it, or that arrives with its answers filled in
PostToolUse  AskUserQuestion   each engine question the Regent answered goes to elicit.record_answer - the one way a
                               value becomes confirmed; one context line says what was accepted, refused or
                               invalidated and what is eligible next

Plain chat questions never reach a hook: an agent that asks in prose bypasses this guard, which is why the
protocol asks through `elicit.py next` and the pop-up. Answers are read from tool_input.answers, then
tool_response.answers, then the `"question"="answer"` result text, split on the known question texts so an answer
holding quotes or commas is read whole.

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
import elicit  # noqa: E402


def open_store(event):
    """The store when it holds elicitation sessions; None otherwise (no file is created for a pop-up)."""
    vdir = wire.virtual_dir(wire.repo_root(Path(event.get("cwd") or os.getcwd())))
    db = vdir / "index.sqlite" if vdir else None
    if not db or not db.is_file():
        return None
    con = sqlite3.connect(str(db), timeout=10)
    try:
        found = con.execute("SELECT 1 FROM sqlite_master WHERE name='elicit_sessions'").fetchone()
    finally:
        con.close()
    return elicit.Store(vdir.parent.parent.parent) if found else None


def questions(event):
    qs = wire.tool_input(event).get("questions")
    return [q for q in qs if isinstance(q, dict)] if isinstance(qs, list) else []


def labels(q_in):
    return [str(o.get("label", "")) for o in q_in.get("options") or [] if isinstance(o, dict)]


def locate(store, q_in):
    """The (session, schema, question) a pop-up entry stands for, or None: elicit.locate_question decides."""
    return elicit.locate_question(store, q_in.get("header"), q_in.get("question"), labels(q_in))


def flat(resp):
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        if isinstance(resp.get("content"), list):
            return " ".join(str(c.get("text", "")) for c in resp["content"] if isinstance(c, dict))
        return str(resp.get("content") or resp.get("result") or "")
    if isinstance(resp, list):
        return " ".join(flat(x) for x in resp)
    return ""


def answers(event, texts):
    """{question text: answer}, wherever the surface put them."""
    for holder in (wire.tool_input(event), event.get("tool_response")):
        if isinstance(holder, dict) and isinstance(holder.get("answers"), dict):
            return {str(k): str(v) for k, v in holder["answers"].items()}
    text = flat(event.get("tool_response"))
    marks = sorted((text.find(f'"{t}"="'), t) for t in texts if f'"{t}"="' in text)
    out = {}
    for i, (pos, t) in enumerate(marks):
        start = pos + len(t) + 4
        chunk = text[start:marks[i + 1][0]] if i + 1 < len(marks) else text[start:]
        if i + 1 < len(marks):
            chunk = chunk.rstrip().rstrip(",").rstrip()
            chunk = chunk[:-1] if chunk.endswith('"') else chunk
        else:
            chunk = chunk[:chunk.rfind('"')] if '"' in chunk else chunk
        out[t] = chunk
    return out


def pre(event, store):
    denials = []
    filled = wire.tool_input(event).get("answers")
    for q_in in questions(event):
        hit = locate(store, q_in)
        if not hit:
            continue
        sess, schema, q = hit
        sid = sess["session_id"]
        if filled:
            denials.append(f"{q['id']} arrived with its answers filled in: the answers are the Regent's alone")
            continue
        _, _, params, _, states = elicit.snapshot(store, sid)
        st = states[q["id"]]
        if st["status"] == "answered":
            p = params[q["slot"]]
            with store.tx():
                store.event(sid, "repeat_denied", q["id"], {"value": p["value"], "revision": p["revision"]})
            denials.append(f"{q['id']} is already answered: {q['slot']} = "
                           f"{elicit.label_of(schema, q['slot'], p['value'])} (revision {p['revision']}, "
                           f"{p['provenance'].get('source')} {str(p['provenance'].get('at', ''))[:10]}); its upstream "
                           f"values have not changed; if the Regent asked to change it: python scripts/elicit.py reopen "
                           f"--session {sid} --question {q['id']} --because \"<their words>\"")
            continue
        if st["status"] == "blocked":
            denials.append(f"{q['id']} is blocked: " + elicit.canon_json(st["detail"]) +
                           f"; python scripts/elicit.py next --session {sid}")
            continue
        if st["status"] == "skipped":
            denials.append(f"{q['id']} does not apply: its condition does not hold")
            continue
        shown = [o for o in q["options"] if o["value"] in st["options"]]
        want = elicit.ask_item(schema, q, params, shown)
        if (elicit.spoken(q_in.get("question")) != elicit.spoken(want["question"])
                or labels(q_in) != [o["label"] for o in want["options"]]
                or bool(q_in.get("multiSelect")) != want["multiSelect"]):
            with store.tx():
                store.event(sid, "presentation_refused", q["id"], {"expected": want["question"]})
            denials.append(f"{q['id']} must be asked as the engine renders it: \"{want['question']}\" with options "
                           + ", ".join(o["label"] for o in want["options"])
                           + f" (python scripts/elicit.py next --session {sid})")
    return wire.permission("deny", "elicitation: " + " | ".join(denials)) if denials else None


def post(event, store):
    engine = []
    for q_in in questions(event):
        hit = locate(store, q_in)
        if hit:
            engine.append((q_in, hit))
    if not engine:
        return None
    got = answers(event, [str(q_in.get("question", "")) for q_in, _ in engine])
    if not got:
        return wire.context("PostToolUse", "elicitation · no answers reached the hook from this surface: nothing was "
                                           "confirmed; the questions stay eligible")
    parts, last = [], None
    for q_in, (sess, schema, q) in engine:
        raw = got.get(str(q_in.get("question", "")))
        if raw is None:
            parts.append(f"{q['id']}: no answer")
            continue
        try:
            r = elicit.record_answer(store, sess["session_id"], q["id"], raw)
            shown = elicit.label_of(schema, q["slot"], r["canonical_value"])
            line = f"{q['slot']} = {shown} {r['event']} (revision {r['current_revision']})"
            if r["invalidated_parameters"]:
                line += " · invalidated: " + ", ".join(r["invalidated_parameters"])
            parts.append(line)
            last = (sess["session_id"], r)
        except elicit.Refused as e:
            parts.append(f"{q['id']} refused: {e}")
    tail = ""
    if last:
        sid, r = last
        tail = "complete" if r.get("complete") else f"next eligible: {r.get('next_question') or 'none'}"
        tail = f"{tail} (python scripts/elicit.py next --session {sid})"
    return wire.context("PostToolUse", wire.one_line("elicitation", *parts, tail))


def respond(event):
    name = event.get("hook_event_name")
    if event.get("tool_name") != "AskUserQuestion" or name not in ("PreToolUse", "PostToolUse") or not questions(event):
        return None
    store = open_store(event)
    if store is None:
        return None
    try:
        return pre(event, store) if name == "PreToolUse" else post(event, store)
    finally:
        store.close()


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        bare = wire.build_fixture(Path(tmp) / "bare", with_virtual=False)
        store = elicit.Store(root)
        sid = elicit.start(store, elicit.load_file(elicit.EXAMPLE), "M01.S01.T01")["session_id"]
        rule_q = elicit.next_questions(store, sid)["ask"]["questions"][0]
        store.close()

        def ev(phase, qs, base=root, **extra):
            e = {"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(base), "session_id": "s1",
                 "tool_input": {"questions": qs}}
            e.update(extra)
            return e

        def verdict(a):
            return ((a or {}).get("hookSpecificOutput") or {}).get("permissionDecision")

        def ctx(a):
            return ((a or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")

        def params():
            s = elicit.Store(root)
            try:
                return s.params(sid)
            finally:
                s.close()

        plain = {"question": "Which colour?", "header": "Colour", "options": [{"label": "Red", "description": "r"},
                                                                            {"label": "Blue", "description": "b"}]}
        cases = []
        cases.append((respond(ev("PreToolUse", [plain])) is None and respond(ev("PreToolUse", [plain], bare)) is None
                      and not (bare / ".guidelines/.shortcuts/.virtual").exists(),
                      "a question no open session asks passes untouched, and no store is created for it"))
        cases.append((respond(ev("PreToolUse", [rule_q])) is None, "pre: the engine's own rendering is allowed"))
        reworded = dict(rule_q, question="Which rule applies, A or B?")
        cases.append((verdict(respond(ev("PreToolUse", [reworded]))) == "deny", "pre: a reworded engine question is denied"))
        filled = ev("PreToolUse", [rule_q])
        filled["tool_input"]["answers"] = {rule_q["question"]: "B"}
        cases.append((verdict(respond(filled)) == "deny", "pre: answers filled in by the agent are denied"))
        base_q = {"question": "For the selected rule (B), which option should be used as the base?", "header": "Base",
                  "options": [{"label": "X1", "description": ""}, {"label": "Y1", "description": ""},
                              {"label": "Z1", "description": ""}]}
        out = respond(ev("PreToolUse", [base_q]))
        cases.append((verdict(out) == "deny" and "blocked" in json.dumps(out), "pre: a question waiting on rule is denied as blocked"))
        out = respond(ev("PostToolUse", [rule_q], tool_response=f'Your questions have been answered: "{rule_q["question"]}"="B". '
                                                                  "You can now continue with these answers in mind."))
        cases.append(("rule = B accepted (revision 1)" in ctx(out) and params()["rule"]["status"] == "confirmed",
                      "post: the Regent's answer, read from the result text, is the confirmed value"))
        out = respond(ev("PreToolUse", [rule_q]))
        s = elicit.Store(root)
        repeats = elicit.status(s, sid)["metrics"]["repeat_denied"]
        s.close()
        cases.append((verdict(out) == "deny" and "already answered" in json.dumps(out) and repeats == 1,
                      "pre: asking an answered question again is denied and counted as a repeat avoided"))
        s = elicit.Store(root)
        wave = elicit.next_questions(s, sid, wave=2)["ask"]["questions"]
        s.close()
        cases.append((respond(ev("PreToolUse", wave)) is None and "(B)" in wave[0]["question"],
                      "pre: the dependent questions, rendered with B, are allowed"))
        text = ("Your questions have been answered: " + f'"{wave[0]["question"]}"="X1", '
                + f'"{wave[1]["question"]}"="X2,Z2". Read the answers carefully.')
        out = respond(ev("PostToolUse", wave, tool_response={"content": [{"type": "text", "text": text}]}))
        p = params()
        cases.append((p["base_option"]["value"] == "X1" and p["release_option"]["value"] == ["X2", "Z2"],
                      "post: several answers in one result, a multi answer split on its labels"))
        s = elicit.Store(root)
        elicit.reopen(s, sid, "Q_RULE", "the Regent: switch to rule A")
        s.close()
        cases.append((respond(ev("PreToolUse", [rule_q])) is None, "pre: a question the Regent reopened may be asked again"))
        out = respond(ev("PostToolUse", [rule_q], tool_input={"questions": [rule_q], "answers": {rule_q["question"]: "A"}}))
        p = params()
        cases.append(("invalidated: base_option, release_option" in ctx(out) and p["base_option"]["status"] == "invalidated",
                      "post: the Regent changes the rule; only its dependents are invalidated, said in one line"))
        out = respond(ev("PostToolUse", [rule_q], tool_response={"answers": {rule_q["question"]: "C"}}))
        cases.append(("refused" in ctx(out) and params()["rule"]["value"] == "A",
                      "post: an answer outside the options is refused and changes nothing"))
        quoted = dict(base_q, question="For the selected rule (A), which option should be used as the base?")
        note_q = {"question": "Who owns the case?", "header": "Owner",
                  "options": [{"label": "The Regent", "description": "The Regent owns it"},
                              {"label": "The product owner", "description": "The product's human owner owns it"}]}
        text = (f'Your questions have been answered: "{quoted["question"]}"="Y1", '
                f'"{note_q["question"]}"="the "finance" team, for now". You can now continue.')
        got = answers({"tool_response": text}, [quoted["question"], note_q["question"]])
        cases.append((got == {quoted["question"]: "Y1", note_q["question"]: 'the "finance" team, for now'},
                      "answers holding quotes and commas are read whole from the result text"))
        out = respond(ev("PostToolUse", [note_q], tool_response="the dialog was dismissed"))
        cases.append(("nothing was confirmed" in ctx(out), "post: no answer reached the hook, so nothing is confirmed"))

        def values(base, session):
            s = elicit.Store(base)
            try:
                return {k: (v["value"], v["status"]) for k, v in s.params(session).items()}
            finally:
                s.close()

        def two_sessions(name, old_answers):
            base = wire.build_fixture(Path(tmp) / name)
            s = elicit.Store(base)
            old = elicit.start(s, elicit.load_file(elicit.EXAMPLE), "triage-2026-11-17")["session_id"]
            elicit.next_questions(s, old)
            if old_answers:
                elicit.record_answer(s, old, "Q_RULE", "B")
            new = elicit.start(s, elicit.load_file(elicit.EXAMPLE), "triage-2026-11-18")["session_id"]
            asked = elicit.next_questions(s, new)["ask"]["questions"]
            s.close()
            return base, old, new, asked

        base, old, new, asked = two_sessions("answered-before", True)
        allowed = respond(ev("PreToolUse", asked, base))
        respond(ev("PostToolUse", asked, base, tool_input={"questions": asked, "answers": {asked[0]["question"]: "A"}}))
        cases.append((allowed is None and values(base, new) == {"rule": ("A", "confirmed")}
                      and values(base, old) == {"rule": ("B", "confirmed")},
                      "D1. an older session that answered the question neither denies nor takes the newer one's"))
        base, old, new, asked = two_sessions("unanswered-before", False)
        respond(ev("PostToolUse", asked, base, tool_input={"questions": asked, "answers": {asked[0]["question"]: "B"}}))
        cases.append((values(base, new) == {"rule": ("B", "confirmed")} and values(base, old) == {},
                      "D1. the answer goes to the session that rendered the question last, never to an older one"))
        base = wire.build_fixture(Path(tmp) / "older-rendered-last")
        s = elicit.Store(base)
        old = elicit.start(s, elicit.load_file(elicit.EXAMPLE), "triage-2026-11-17")["session_id"]
        new = elicit.start(s, elicit.load_file(elicit.EXAMPLE), "triage-2026-11-18")["session_id"]
        elicit.next_questions(s, new)
        asked = elicit.next_questions(s, old)["ask"]["questions"]
        s.close()
        allowed = respond(ev("PreToolUse", asked, base))
        respond(ev("PostToolUse", asked, base, tool_input={"questions": asked, "answers": {asked[0]["question"]: "B"}}))
        cases.append((allowed is None and values(base, old) == {"rule": ("B", "confirmed")} and values(base, new) == {},
                      "D1. the older session rendered the question last: the pop-up and its answer are its own"))

        done = wire.build_fixture(Path(tmp) / "complete")
        s = elicit.Store(done)
        sid_done = elicit.start(s, elicit.load_file(elicit.EXAMPLE), "done-last-week")["session_id"]
        for qid, value in (("Q_RULE", "B"), ("Q_BASE", "X1"), ("Q_RELEASE", "X2"), ("Q_NOTE", "RGN")):
            elicit.record_answer(s, sid_done, qid, value)
        s.close()
        unrelated = {"question": "Who should own the deploy pipeline change?", "header": "Owner",
                     "options": [{"label": "Platform team", "description": "p"}, {"label": "App team", "description": "a"}]}
        pre_out = respond(ev("PreToolUse", [unrelated], done))
        post_out = respond(ev("PostToolUse", [unrelated], done,
                              tool_input={"questions": [unrelated], "answers": {unrelated["question"]: "App team"}}))
        s = elicit.Store(done)
        st_done = elicit.status(s, sid_done)
        s.close()
        cases.append((pre_out is None and post_out is None and st_done["metrics"]["repeat_denied"] == 0
                      and st_done["parameters"]["owner"]["value"] == "RGN",
                      "D2. a pop-up that shares only a header with an engine question passes untouched, nothing recorded"))

        gap = wire.build_fixture(Path(tmp) / "spaced")
        spaced = elicit.load_file(elicit.EXAMPLE)
        spaced["questions"][0]["prompt"] = "AN-01-01 (gap, src/a.py): approve()  has no reversal\npath - which rule?"
        s = elicit.Store(gap)
        sid_gap = elicit.start(s, spaced, "triage-2026-11-18")["session_id"]
        verbatim = elicit.next_questions(s, sid_gap)["ask"]["questions"]
        s.close()
        cases.append((respond(ev("PreToolUse", verbatim, gap)) is None,
                      "D3. the engine's own rendering of a prompt holding a double space or a line break is allowed"))
        return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else wire.serve(respond, guard=True))
