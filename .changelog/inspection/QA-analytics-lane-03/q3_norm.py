"""QA attempt 3: the four norm points against behaviour, and scenarios that tell rank mutants apart.
Usage: python3 -B -I q3_norm.py <scripts dir>"""
import sys, os, json, tempfile, importlib.util
from pathlib import Path
sys.dont_write_bytecode = True
S = sys.argv[1]; sys.path.insert(0, S)
import hook_wire as wire, elicit, analytics as an
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
EX = elicit.load_file(elicit.EXAMPLE); n = [0]
def proj():
    n[0] += 1; return wire.build_fixture(Path(tmp) / f"p{n[0]}")
def hook(base, phase, qs, answers=None, **extra):
    ti = {"questions": qs}
    if answers is not None: ti["answers"] = answers
    e = {"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(base), "session_id": "x", "tool_input": ti}
    e.update(extra); return he.respond(e)
def verdict(out): return ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecision") or "allowed"
def ctx(out):
    h = (out or {}).get("hookSpecificOutput") or {}; return h.get("additionalContext") or h.get("permissionDecisionReason") or ""
def with_store(base, f):
    st = elicit.Store(base)
    try: return f(st)
    finally: st.close()
def vals(base, sid): return with_store(base, lambda st: {k: (v["value"], v["status"]) for k, v in st.params(sid).items()})
def nxt(base, sid, w=1): return with_store(base, lambda st: (elicit.next_questions(st, sid, w)["ask"] or {}).get("questions") or [])
def two(base):
    return with_store(base, lambda st: (elicit.start(st, EX, "task-a")["session_id"], elicit.start(st, EX, "task-b")["session_id"]))
def sql(base, q, a=()):
    def f(st):
        with st.tx(): st.con.execute(q, a)
    with_store(base, f)

print("## 1c in full (norm §3 limit)")
base = proj(); a, b = two(base)
ask = nxt(base, a); print("  Pre on A:", verdict(hook(base, "PreToolUse", ask)))
nxt(base, b)
out = hook(base, "PostToolUse", ask, {ask[0]["question"]: "A"})
print("  A", vals(base, a), "| B", vals(base, b))
print("  context line the asking agent gets:", ctx(out))
print("  B's answer provenance:", with_store(base, lambda st: st.params(b)["rule"]["provenance"]), "| B task:",
      with_store(base, lambda st: elicit.status(st, b).get("task_id")))
st_a = with_store(base, lambda st: elicit.status(st, a))
print("  A status keys:", sorted(st_a)[:12])
again = nxt(base, a); print("  next on A returns:", [q["header"] + ": " + q["question"] for q in again])
print("  Pre on A's re-render:", verdict(hook(base, "PreToolUse", again)))
out = hook(base, "PostToolUse", again, {again[0]["question"]: "A"}); print("  Post:", ctx(out)[:120])
print("  A", vals(base, a), "| B", vals(base, b))
print("  same pop-up re-asked WITHOUT a new next on A (stale rendering):")
base = proj(); a, b = two(base); ask = nxt(base, a); hook(base, "PreToolUse", ask); nxt(base, b)
hook(base, "PostToolUse", ask, {ask[0]["question"]: "A"})
out = hook(base, "PreToolUse", ask); print("   Pre:", verdict(out), "|", ctx(out)[:110])

print("## D18 steps (norm §5, Post lookup)")
def d18():
    repo = an.fixture_repo(Path(tmp) / f"an{n[0]}"); n[0] += 1
    (repo / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
    an.record(repo, an.envelope(an.plan(repo, "baseline"), [an.sample(title="approve()  offers no reversal")]), create=True)
    sid = with_store(repo, lambda st: elicit.start(st, an.triage_schema(repo), "triage-2026-11-18")["session_id"])
    return repo, sid, nxt(repo, sid)
repo, sid, ask = d18(); q = ask[0]["question"]; single = " ".join(q.split())
print("  question:", repr(q))
out = hook(repo, "PostToolUse", ask, {single: "Recycle"}); print("  a) answers keyed single-spaced:", ctx(out)[:110])
print("     params", vals(repo, sid), "| next again:", [x["header"] for x in nxt(repo, sid)])
repo, sid, ask = d18(); q = ask[0]["question"]; single = " ".join(q.split())
out = hook(repo, "PostToolUse", ask, None, tool_response=f'User has answered your questions: "{single}"="Recycle". You can now continue.')
print("  b) result text echoed single-spaced:", ctx(out)[:110])
print("     params", vals(repo, sid), "| next again:", [x["header"] for x in nxt(repo, sid)])
repo, sid, ask = d18(); q = ask[0]["question"]
out = hook(repo, "PostToolUse", ask, {q: "Recycle"}); print("  c) control, keyed verbatim:", ctx(out)[:80])
repo, sid, ask = d18(); q = ask[0]["question"]; single = " ".join(q.split()); ent = [dict(ask[0], question=single)]
print("  d) entry single-spaced by the agent: Pre", verdict(hook(repo, "PreToolUse", ent)), end=" ")
out = hook(repo, "PostToolUse", ent, {single: "Recycle"}); print("| Post keyed as the entry:", ctx(out)[:80])
repo, sid, ask = d18(); q = ask[0]["question"]
out = hook(repo, "PostToolUse", ask, {}, tool_response={"answers": {q: "Recycle"}})
print("  e) tool_input.answers = {} and tool_response.answers verbatim:", ctx(out)[:100])

print("## §6: triage --from-elicit leaves the session open")
repo, sid, ask = d18(); q = ask[0]["question"]; hook(repo, "PreToolUse", ask); hook(repo, "PostToolUse", ask, {q: "Recycle"})
r = an.triage_from_elicit(repo, sid)
print("  triaged", r.get("triaged"), "undecided", r.get("undecided"), "| session status after:",
      with_store(repo, lambda st: elicit.status(st, sid).get("session_status")))

print("## rank scenarios (expected per norm §5)")
base = proj(); a, b = two(base)
with_store(base, lambda st: (elicit.record_answer(st, a, "Q_RULE", "A"), elicit.record_answer(st, b, "Q_RULE", "B")))
ask_a = nxt(base, a); nxt(base, b)
hook(base, "PreToolUse", ask_a); hook(base, "PostToolUse", ask_a, {ask_a[0]["question"]: "X1"})
print("  S1 rendering carried beats rendered last (exp A): A", vals(base, a).get("base_option"), "B", vals(base, b).get("base_option"))
base = proj(); a, b = two(base); nxt(base, a); nxt(base, b); ask = nxt(base, a)
hook(base, "PreToolUse", ask); hook(base, "PostToolUse", ask, {ask[0]["question"]: "B"})
print("  S2 A re-rendered last (exp A):", {a: vals(base, a), b: vals(base, b)})
base = proj(); a, b = two(base); nxt(base, b); ask = nxt(base, a)
sql(base, "UPDATE elicit_sessions SET updated_at='2099-01-01T00:00:00+00:00' WHERE session_id=?", (b,))
hook(base, "PreToolUse", ask); hook(base, "PostToolUse", ask, {ask[0]["question"]: "B"})
print("  S3 A rendered last, B updated last (exp A):", {a: vals(base, a), b: vals(base, b)})
base = proj(); a, b = two(base)
sql(base, "UPDATE elicit_sessions SET updated_at='2026-11-18T00:00:00+00:00'")
ask = [{"question": "Which rule should govern this case?", "header": "Rule", "multiSelect": False,
        "options": [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}]}]
print("  S4 neither rendered, same updated_at: Pre", verdict(hook(base, "PreToolUse", ask)), end=" ")
hook(base, "PostToolUse", ask, {ask[0]["question"]: "B"})
print("| answer (exp higher id", b, "):", {a: vals(base, a), b: vals(base, b)})
