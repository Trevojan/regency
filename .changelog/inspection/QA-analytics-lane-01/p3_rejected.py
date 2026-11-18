import sys, os, json, tempfile
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
st = elicit.Store(root)
sid = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "T")["session_id"]
for key, val in (("Q_RULE", "C"), ("Q_BASE", "X1"), ("nope", "x")):
    try:
        elicit.record_answer(st, sid, key, val)
    except elicit.Refused as e:
        print("refused:", key, e)
print("answer_rejected events persisted:",
      st.con.execute("SELECT COUNT(*) FROM elicit_events WHERE event='answer_rejected'").fetchone()[0])
print("metrics:", elicit.status(st, sid)["metrics"])
