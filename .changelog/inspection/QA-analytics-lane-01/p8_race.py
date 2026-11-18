import sys, os, json, tempfile, random, multiprocessing as mp
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, elicit

def worker(root, sid, seed, out):
    random.seed(seed); errs = []
    for _ in range(25):
        st = elicit.Store(root)
        try:
            k = random.choice(["rule", "base", "rel"])
            if k == "rule": elicit.record_answer(st, sid, "Q_RULE", random.choice("AB"))
            elif k == "base": elicit.record_answer(st, sid, "Q_BASE", random.choice(["X1", "Y1", "Z1"]))
            else: elicit.record_answer(st, sid, "Q_RELEASE", random.choice(["X2", "Y2"]))
        except elicit.Refused:
            pass
        except Exception as e:
            errs.append(repr(e))
        finally:
            st.close()
    out.put(errs)

if __name__ == "__main__":
    tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
    root = wire.build_fixture(tmp + "/proj")
    st = elicit.Store(root); sid = elicit.start(st, elicit.load_file(elicit.EXAMPLE), "T")["session_id"]
    elicit.record_answer(st, sid, "Q_RULE", "B"); st.close()
    q = mp.Queue(); ps = [mp.Process(target=worker, args=(root, sid, i, q)) for i in range(8)]
    [p.start() for p in ps]; errs = [e for _ in ps for e in q.get()]; [p.join() for p in ps]
    print("worker errors:", errs[:5], len(errs))
    st = elicit.Store(root)
    params = st.params(sid); schema = st.session(sid)[1]
    rule = params["rule"]
    bad = []
    for qid, slot in (("Q_BASE", "base_option"), ("Q_RELEASE", "release_option")):
        p = params.get(slot)
        q_ = next(x for x in schema["questions"] if x["id"] == qid)
        if p and p["status"] == "confirmed" and p["fingerprint"] != elicit.fingerprint(q_, params):
            bad.append(f"{slot} confirmed under a stale fingerprint")
    revs = [json.loads(r[0])["revision"] for r in st.con.execute(
        "SELECT payload FROM elicit_events WHERE entity='rule' AND event='answer_accepted' ORDER BY event_id")]
    print("rule revisions in order:", revs[:12], "... final", rule["revision"], rule["value"])
    print("monotonic +1:", all(b == a + 1 for a, b in zip(revs, revs[1:])), "| invariant breaks:", bad)
    print("status:", {k: v["status"] for k, v in elicit.status(st, sid)["questions"].items()})
