import sys, os, json, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit, analytics as an
spec = importlib.util.spec_from_file_location("he", S + "/hook-elicit.py"); he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
repo = an.fixture_repo(tmp); (repo / ".guidelines/.shortcuts/.virtual").mkdir(parents=True)
an.record(repo, an.envelope(an.plan(repo, "baseline"), [an.sample(), an.sample("suggestion", "src/other.py", "name it")]), create=True)
def hook(phase, qs, answers=None):
    ti = {"questions": qs}
    if answers: ti["answers"] = answers
    return he.respond({"hook_event_name": phase, "tool_name": "AskUserQuestion", "cwd": str(repo), "session_id": "x", "tool_input": ti})
def ask_round(sid, picks):
    st = elicit.Store(repo); ask = elicit.next_questions(st, sid, 4)["ask"]["questions"]; st.close()
    pre = hook("PreToolUse", ask)
    if pre: return ask, pre
    hook("PostToolUse", ask, {q["question"]: picks[q["header"]] for q in ask if q["header"] in picks})
    return ask, None
# day 1
st = elicit.Store(repo); d1 = elicit.start(st, an.triage_schema(repo), "triage-2026-11-17")["session_id"]; st.close()
ask_round(d1, {"AN-01-01": "Recycle", "AN-01-02": "Promote"})
ask_round(d1, {"AN-01-02 to": ".plan"})
print("day 1 recorded:", an.triage_from_elicit(repo, d1)["triaged"])
# day 2: the recycled finding again
st = elicit.Store(repo); d2 = elicit.start(st, an.triage_schema(repo), "triage-2026-11-18")["session_id"]; st.close()
ask, pre = ask_round(d2, {"AN-01-01": "Trash"})
print("day 2 asks:", [q["header"] for q in ask], "->", (pre or {}).get("hookSpecificOutput", {}).get("permissionDecisionReason", "allowed")[:200])
try:
    print(an.triage_from_elicit(repo, d2))
except an.LaneError as e:
    print("day 2 triage --from-elicit:", e)
