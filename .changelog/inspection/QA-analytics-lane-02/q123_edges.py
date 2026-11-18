"""D1-D3 edge probes for the elicitation hook. Usage: python3 -B -I q123_edges.py <scripts dir>"""
import sys, os, json, copy, tempfile, importlib.util
sys.dont_write_bytecode = True
S = sys.argv[1]; sys.path.insert(0, S)
import hook_wire as wire, elicit, analytics as an
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
EX = elicit.load_file(elicit.EXAMPLE)
n = [0]


def proj():
    n[0] += 1
    return wire.build_fixture(Path(tmp) / f"p{n[0]}")


from pathlib import Path


def hook(base, phase, qs, answers=None, **extra):
    ti = {"questions": qs}
    if answers is not None:
        ti["answers"] = answers
    e = {"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(base), "session_id": "x", "tool_input": ti}
    e.update(extra)
    return he.respond(e)


def verdict(out):
    return ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecision") or "allowed"


def reason(out):
    h = (out or {}).get("hookSpecificOutput") or {}
    return (h.get("permissionDecisionReason") or h.get("additionalContext") or "")[:150]


def vals(base, sid):
    st = elicit.Store(base)
    try:
        return {k: (v["value"], v["status"]) for k, v in st.params(sid).items()}
    finally:
        st.close()


def metric(base, sid, k):
    st = elicit.Store(base)
    try:
        return elicit.status(st, sid)["metrics"][k]
    finally:
        st.close()


def two(base, schema=EX, t1="task-a", t2="task-b"):
    st = elicit.Store(base)
    a = elicit.start(st, schema, t1)["session_id"]; b = elicit.start(st, schema, t2)["session_id"]
    st.close()
    return a, b


def nxt(base, sid, wave=1):
    st = elicit.Store(base)
    try:
        return elicit.next_questions(st, sid, wave)["ask"]["questions"]
    finally:
        st.close()


def rec(base, sid, q, v):
    st = elicit.Store(base)
    try:
        elicit.record_answer(st, sid, q, v)
    finally:
        st.close()


print("## D1")
# 1a: the OLDER-id session rendered last: it must own the pop-up (a session-id tie-break would pick the newer)
base = proj(); a, b = two(base)
nxt(base, b); ask = nxt(base, a)
print("1a older id rendered last -> Pre", verdict(hook(base, "PreToolUse", ask)))
hook(base, "PostToolUse", ask, {ask[0]["question"]: "B"})
print("   answer went to", {a: vals(base, a), b: vals(base, b)}, "(expected: only", a, ")")
# 1b: renderings differ by an upstream value: the entry carrying A's rendering goes to A even though B rendered later
base = proj(); a, b = two(base)
rec(base, a, "Q_RULE", "A"); rec(base, b, "Q_RULE", "B")
ask_a = nxt(base, a); ask_b = nxt(base, b)
print("1b renderings:", ask_a[0]["question"], "|", ask_b[0]["question"])
print("   Pre on A's rendering", verdict(hook(base, "PreToolUse", ask_a)))
hook(base, "PostToolUse", ask_a, {ask_a[0]["question"]: "X1"})
print("   base_option A", vals(base, a).get("base_option"), "B", vals(base, b).get("base_option"))
# 1c: interleaving: A renders, Pre passes, B renders the same question, then the Regent's answer arrives at Post
base = proj(); a, b = two(base)
ask = nxt(base, a)
pre = hook(base, "PreToolUse", ask)
nxt(base, b)
hook(base, "PostToolUse", ask, {ask[0]["question"]: "A"})
print("1c A asked, B rendered before the answer -> A", vals(base, a), "B", vals(base, b))
# 1d: the older session answered; the newer session never rendered (agent skipped `next`)
base = proj(); a, b = two(base)
nxt(base, a); rec(base, a, "Q_RULE", "B")
out = hook(base, "PreToolUse", [{"question": "Which rule should govern this case?", "header": "Rule", "multiSelect": False,
                                  "options": [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}]}])
print("1d newer never rendered -> Pre", verdict(out), "|", reason(out)[:90])
# 1e: repeat-denied counted in the owning session only
base = proj(); a, b = two(base)
nxt(base, a); rec(base, a, "Q_RULE", "B"); nxt(base, b); rec(base, b, "Q_RULE", "A")
ask = [{"question": "Which rule should govern this case?", "header": "Rule", "multiSelect": False,
        "options": [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}]}]
out = hook(base, "PreToolUse", ask)
print("1e both answered -> Pre", verdict(out), "| repeat_denied A", metric(base, a, "repeat_denied"), "B", metric(base, b, "repeat_denied"), "|", reason(out)[:80])

print("## D1 on the real consumer, completed")
repo = an.fixture_repo(Path(tmp) / "an"); (repo / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
an.record(repo, an.envelope(an.plan(repo, "baseline"), [an.sample(), an.sample("suggestion", "src/other.py", "name it")]), create=True)


def rnd(sid, picks, w=4):
    st = elicit.Store(repo); ask = elicit.next_questions(st, sid, w)["ask"]["questions"]; st.close()
    pre = hook(repo, "PreToolUse", ask)
    if verdict(pre) != "allowed":
        return ask, pre
    hook(repo, "PostToolUse", ask, {q["question"]: picks[q["header"]] for q in ask if q["header"] in picks})
    return ask, None


st = elicit.Store(repo); d1 = elicit.start(st, an.triage_schema(repo), "triage-2026-11-17")["session_id"]; st.close()
rnd(d1, {"AN-01-01": "Recycle", "AN-01-02": "Promote"}); rnd(d1, {"AN-01-02 to": ".plan"})
print("day 1:", an.triage_from_elicit(repo, d1)["triaged"], "(session left open, as p13)")
st = elicit.Store(repo); d2 = elicit.start(st, an.triage_schema(repo), "triage-2026-11-18")["session_id"]; st.close()
a1, p1 = rnd(d2, {"AN-01-01": "Trash"})
a2, p2 = rnd(d2, {"AN-01-01 why": "Duplicate"})
print("day 2 rounds:", [q["header"] for q in a1], verdict(p1), [q["header"] for q in a2], verdict(p2))
r = an.triage_from_elicit(repo, d2)
print("day 2 triage --from-elicit:", r.get("triaged"), "undecided", r.get("undecided"))
st = elicit.Store(repo); print("day 1 params untouched:", {k: v["value"] for k, v in st.params(d1).items()}); st.close()

print("## D2")
base = proj(); st = elicit.Store(base); sid = elicit.start(st, EX, "done")["session_id"]; st.close()
for q, v in (("Q_RULE", "B"), ("Q_BASE", "X1"), ("Q_RELEASE", "X2"), ("Q_NOTE", "RGN")):
    rec(base, sid, q, v)


def one(question, header, labels, multi=False):
    return [{"question": question, "header": header, "multiSelect": multi,
             "options": [{"label": l, "description": "d"} for l in labels]}]


cases = [
    ("2a unrelated, header 'owner' (case), other labels", one("Who signs the release?", "owner", ["Ana", "Bo"])),
    ("2b unrelated, header 'Rule', labels A/B (a subset)", one("Which lint rule set?", "Rule", ["A", "B"])),
    ("2c unrelated, header 'Rule', labels 'A' only", one("Pick a plan", "Rule", ["A", "Other plan"])),
    ("2d engine Q_RULE reworded, same labels", one("What rule governs it?", "Rule", ["A", "B"])),
    ("2e engine Q_RULE verbatim, labels changed", one("Which rule should govern this case?", "Rule", ["A", "C"])),
    ("2f engine Q_RULE reworded and re-optioned", one("What rule governs it?", "Rule", ["A", "C"])),
    ("2g engine Q_NOTE labels with '(Recommended)'", one("Owner?", "Owner", ["The Regent (Recommended)", "The product owner"])),
]
for name, qs in cases:
    out = hook(base, "PreToolUse", qs)
    print(f"{name}: Pre {verdict(out)} | {reason(out)[:70]}")
print("   repeat_denied total", metric(base, sid, "repeat_denied"))
qs = one("Who signs the release?", "Owner", ["Ana", "Bo"])
print("2h Post of an unrelated 'Owner' answer:", hook(base, "PostToolUse", qs, {qs[0]["question"]: "Ana"}), vals(base, sid)["owner"])
qs = one("What rule governs it?", "Rule", ["A", "C"])
base2 = proj(); st = elicit.Store(base2); s2 = elicit.start(st, EX, "fresh")["session_id"]; st.close()
print("2i reworded+re-optioned on an UNANSWERED engine question: Pre", verdict(hook(base2, "PreToolUse", qs)),
      "Post", hook(base2, "PostToolUse", qs, {qs[0]["question"]: "A"}), vals(base2, s2))

print("## D3")
repo3 = an.fixture_repo(Path(tmp) / "an3"); (repo3 / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
an.record(repo3, an.envelope(an.plan(repo3, "baseline"), [an.sample(title="approve()  offers no\treversal")]), create=True)
st = elicit.Store(repo3); s3 = elicit.start(st, an.triage_schema(repo3), "triage-2026-11-18")["session_id"]
ask = elicit.next_questions(st, s3)["ask"]["questions"]; st.close()
print("3a asked:", repr(ask[0]["question"]))
print("   Pre verbatim", verdict(hook(repo3, "PreToolUse", ask)))
norm = [dict(ask[0], question=" ".join(ask[0]["question"].split()))]
print("   Pre single-spaced by the agent", verdict(hook(repo3, "PreToolUse", norm)))
out = hook(repo3, "PostToolUse", ask, {ask[0]["question"]: "Recycle"})
print("   Post verbatim:", reason(out)[:90])
print("   triage --from-elicit:", an.triage_from_elicit(repo3, s3).get("triaged"))
# 3b: the same, answers only in the result text, the question echoed single-spaced by the surface
repo4 = an.fixture_repo(Path(tmp) / "an4"); (repo4 / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
an.record(repo4, an.envelope(an.plan(repo4, "baseline"), [an.sample(title="approve()  offers no reversal")]), create=True)
st = elicit.Store(repo4); s4 = elicit.start(st, an.triage_schema(repo4), "triage-2026-11-18")["session_id"]
ask = elicit.next_questions(st, s4)["ask"]["questions"]; st.close()
q = ask[0]["question"]
for label, shown in (("verbatim", q), ("single-spaced", " ".join(q.split()))):
    out = hook(repo4, "PostToolUse", ask, None, tool_response=f'User has answered your questions: "{shown}"="Recycle". You can now continue.')
    print(f"3b result text, question {label}:", reason(out)[:100])
