import sys, os, json, tempfile, copy
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
st = elicit.Store(root)
base = elicit.load_file(elicit.EXAMPLE)

print("--- (a) history after re-answer of an invalidated slot")
sid = elicit.start(st, base, "A")["session_id"]
elicit.record_answer(st, sid, "Q_RULE", "B"); elicit.record_answer(st, sid, "Q_BASE", "X1")
elicit.record_answer(st, sid, "Q_RULE", "A")
print(" after invalidation, history in row:", "history" in st.params(sid)["base_option"]["provenance"])
elicit.record_answer(st, sid, "Q_BASE", "Y1")
p = st.params(sid)["base_option"]
print(" after re-answer: value", p["value"], "status", p["status"], "history in row:", "history" in p["provenance"])
ev = [r[0] for r in st.con.execute("SELECT event FROM elicit_events WHERE session_id=? AND entity='base_option'", (sid,))]
print(" events for base_option:", ev)

print("--- (b) inputs slot: declared 'filled only by a derived source'")
s2 = copy.deepcopy(base); s2["schema"] = "with-input"; s2["inputs"] = {"env": "set by a script"}
s2["questions"][3]["depends_on"] = ["env"]
print(" problems:", elicit.problems(s2))
sid2 = elicit.start(st, s2, "B")["session_id"]
try:
    print(elicit.accept(st, sid2, "env", "prod", "derived"))
except elicit.Refused as e:
    print(" derived submit on input refused:", e)
print(" Q_NOTE status:", elicit.status(st, sid2)["questions"]["Q_NOTE"])

print("--- (c) derived overwrites the Regent's confirmed answer")
s3 = copy.deepcopy(base); s3["schema"] = "derivable"; s3["questions"][3]["derived"] = True
sid3 = elicit.start(st, s3, "C")["session_id"]
elicit.record_answer(st, sid3, "Q_NOTE", "RGN")
r = elicit.accept(st, sid3, "Q_NOTE", "RGN-PO", "derived")
print(" event", r["event"], "->", {k:(v["value"],v["status"],v["provenance"]["source"]) for k,v in st.params(sid3).items()})

print("--- (d) multi option whose label holds a comma")
s4 = copy.deepcopy(base); s4["schema"] = "commas"
s4["questions"][2]["options"][0]["label"] = "X2, now"
print(" problems:", elicit.problems(s4))
sid4 = elicit.start(st, s4, "D")["session_id"]
elicit.record_answer(st, sid4, "Q_RULE", "B")
for raw in ("X2, now", ["X2, now", "Y2"]):
    try:
        r = elicit.record_answer(st, sid4, "Q_RELEASE", raw); print(" ", raw, "->", r["canonical_value"])
    except elicit.Refused as e:
        print(" ", raw, "refused:", e)
