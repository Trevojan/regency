#!/usr/bin/env python3
"""speed.py - the computable parts of the speed modes (library/team/SPEED_MODES.md).

A playbook step that this script refuses does not run.

  speed.py fuel [ARG ...]          the fuel the Regent declared: prints 'fuel <n>' or 'fuel all';
                                   no or bad fuel prints the one-line refusal and exits 2   (section 4)
  speed.py range FROM [TO]         unit ids checked against library/ids.md, in ladder order, with the
                                   modules they cover; exit 2 when an id or the order is wrong
  speed.py waves CARDS.json        the task cards in waves: every dependency in an earlier wave, at most
                                   one task per module per wave (ORCHESTRATION section 4); JSON lines   (section 5)
  speed.py packet FILE [PREVIOUS]  a fuel packet (PASS-nn.json) or a wave (WAVE-nn.json) against section 7,
                                   and against the packet before it: numbering, fuel, carried returns,
                                   applied fix notes; exit 1 on a miss
  speed.py --selftest              plant a defect per rule; exit 1 if one goes unseen

Pure standard library, Python 3.8+. Reads only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = ROOT / "library" / "ids.md"
MODES = {"extreme-go-horse": "kraken", "just-in-time": "jit"}
RUN = re.compile(r"^(kraken|jit)-\d{4}-\d{2}-\d{2}-\d+$")
VERDICTS = ("pass", "return", "not-reviewed")
PAIRING = {"dv": "sonnet", "qa": "opus"}  # SPEED_MODES section 9, decision 2: per team, set at spawn
REFUSAL = ("Refused: extreme-go-horse burns only the fuel the Regent declares - "
           "add fuel=<n> (passes) or fuel=all.")


def grammar(name):
    """One id grammar from library/ids.md, compiled; the file is the only source."""
    text = IDS.read_text(encoding="utf-8")
    block = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
    return re.compile(block[name]["pattern"])


def unit_key(unit):
    """Ladder order: the numbers of each segment, in position (M03.D02.T04 -> (3, 2, 4))."""
    return tuple(int(n) for n in re.findall(r"\d+", unit.split(" ")[0]))


def module_of(unit):
    return unit.split(".")[0]


# ---------- fuel -----------------------------------------------------------------------------------

def fuel(args):
    """('3' | 'all', None) or (None, refusal line)."""
    found = [a for a in args if a.lower().startswith("fuel=")]
    if not found:
        return None, REFUSAL
    if len(found) > 1:
        return None, f"Refused: fuel declared twice ({', '.join(found)}) - declare it once."
    value = found[0].split("=", 1)[1].strip().lower()
    if value == "all" or (value.isdigit() and int(value) >= 1):
        return value, None
    return None, f"Refused: '{found[0]}' is not fuel - use fuel=<n> with n of 1 or more, or fuel=all."


# ---------- range ----------------------------------------------------------------------------------

def unit_range(first, last=None):
    """(summary, problems) for a range of unit ids."""
    pat = grammar("unit")
    problems = [f"'{u}' is not a unit id (library/ids.md)" for u in (first, last) if u is not None and not pat.match(u)]
    if problems:
        return None, problems
    if last is not None and unit_key(last) < unit_key(first):
        return None, [f"'{last}' comes before '{first}' in the ladder"]
    mods = sorted({module_of(first), module_of(last or first)}, key=unit_key)
    if len(mods) == 2:
        lo, hi = unit_key(mods[0])[0], unit_key(mods[1])[0]
        mods = [f"M{n:02d}" for n in range(lo, hi + 1)]
    return {"from": first, "to": last or first, "modules": mods}, []


# ---------- waves ----------------------------------------------------------------------------------

def waves(cards):
    """([[unit, ...], ...], problems): dependency layers, one task per module per wave, ladder order inside."""
    pat = grammar("unit")
    problems, byunit, files = [], {}, {}
    for c in cards:
        u = c.get("unit", "")
        if not pat.match(u):
            problems.append(f"card '{u}': not a unit id")
            continue
        if u in byunit:
            problems.append(f"card '{u}': twice")
        byunit[u] = c
        f = c.get("file")
        if not f:
            problems.append(f"card '{u}': no file (one task, one file)")
        elif f in files:
            problems.append(f"cards '{files[f]}' and '{u}': the same file {f} (one task, one file)")
        else:
            files[f] = u
    for u, c in byunit.items():
        for d in c.get("depends_on", []):
            if d not in byunit:
                problems.append(f"card '{u}': depends on '{d}', which has no card")
    if problems:
        return [], problems
    done, out = set(), []
    left = sorted(byunit, key=unit_key)
    while left:
        ready = [u for u in left if all(d in done for d in byunit[u].get("depends_on", []))]
        if not ready:
            return out, [f"a dependency cycle among: {', '.join(left)}"]
        wave, mods = [], set()
        for u in ready:
            if module_of(u) not in mods:
                wave.append(u)
                mods.add(module_of(u))
        out.append(wave)
        done.update(wave)
        left = [u for u in left if u not in done]
    return out, []


# ---------- packets --------------------------------------------------------------------------------

def check_packet(pk, prev=None):
    """[miss, ...] for one fuel packet or wave against SPEED_MODES section 7 (and the one before it)."""
    m = []
    unit_pat = grammar("unit")
    fx_pat = grammar("fix-note")
    if pk.get("packet") != 1:
        m.append("packet: must be 1 (the format version)")
    mode = pk.get("mode")
    if mode not in MODES:
        return m + [f"mode: {mode!r} is not a speed mode with packets ({', '.join(MODES)})"]
    run = str(pk.get("run", ""))
    if not RUN.match(run) or run.split("-")[0] != MODES[mode]:
        m.append(f"run: {run!r} is not '{MODES[mode]}-YYYY-MM-DD-n'")
    counter = "pass" if mode == "extreme-go-horse" else "wave"
    n = pk.get(counter)
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        m.append(f"{counter}: a whole number from 1")
        n = None
    if prev is not None:
        if prev.get("run") != run:
            m.append(f"previous packet is from run {prev.get('run')!r}, not {run!r}")
        if n is not None and prev.get(counter) != n - 1:
            m.append(f"{counter}: {n} does not follow the previous {prev.get(counter)}")
    if mode == "extreme-go-horse":
        m += check_kraken(pk, prev, n, unit_pat)
    else:
        m += check_wave(pk, prev, n, unit_pat, fx_pat)
    return m


def check_kraken(pk, prev, n, unit_pat):
    m = []
    fu = pk.get("fuel") or {}
    declared, used = str(fu.get("declared", "")), fu.get("used")
    if declared != "all" and not (declared.isdigit() and int(declared) >= 1):
        m.append(f"fuel.declared: {declared!r} is neither a whole number nor 'all'")
    if n is not None and used != n:
        m.append(f"fuel.used: {used!r} must equal the pass number {n}")
    if declared.isdigit() and isinstance(used, int) and used > int(declared):
        m.append(f"fuel.used: {used} passes exceed the declared fuel {declared}")
    teams = pk.get("teams") or {}
    if not teams or set(teams) - {"A", "B"}:
        m.append("teams: A, or A and B")
    seen = {}
    for name, t in teams.items():
        for s in t.get("span") or []:
            if not unit_pat.match(s):
                m.append(f"teams.{name}.span: '{s}' is not a unit id")
            mod = module_of(s)
            if mod in seen and seen[mod] != name:
                m.append(f"teams: module {mod} in span {seen[mod]} and span {name} (one agent per module)")
            seen[mod] = name
        for role, model in PAIRING.items():
            got = (t.get("models") or {}).get(role)
            if got != model:
                m.append(f"teams.{name}.models.{role}: {got!r}, the pairing is {model} (SPEED_MODES section 9)")
    for i, t in enumerate(pk.get("tasks") or []):
        where = f"tasks[{i}] {t.get('unit', '?')}"
        if not unit_pat.match(t.get("unit", "")):
            m.append(f"{where}: not a unit id")
        if t.get("team") not in teams:
            m.append(f"{where}: team {t.get('team')!r} is not in the packet")
        if t.get("gate") not in ("green", "red"):
            m.append(f"{where}: gate is green or red")
        if t.get("verdict") not in VERDICTS:
            m.append(f"{where}: verdict is one of {', '.join(VERDICTS)}")
        if t.get("gate") == "red" and t.get("verdict") == "pass":
            m.append(f"{where}: a red gate is never a pass")
        if t.get("ledger") == "done":
            m.append(f"{where}: ledger never 'done' (T5)")
    returns = pk.get("returns") or []
    escal = pk.get("escalations") or []
    for i, r in enumerate(returns):
        where = f"returns[{i}] {r.get('unit', '?')}"
        if not unit_pat.match(r.get("unit", "")):
            m.append(f"{where}: not a unit id")
        if r.get("attempts") not in (1, 2):
            m.append(f"{where}: attempts {r.get('attempts')!r}; a third failure is an escalation, never a carried return (T4)")
        if not r.get("artefact"):
            m.append(f"{where}: names no artefact (the bug report or gate log, as written)")
        if not r.get("key"):
            m.append(f"{where}: no key")
    for i, e in enumerate(escal):
        where = f"escalations[{i}] {e.get('unit', '?')}"
        if not isinstance(e.get("attempts"), int) or e.get("attempts") < 3:
            m.append(f"{where}: an escalation follows the third failure (T4)")
        if e.get("to") != "RGN":
            m.append(f"{where}: goes to RGN")
    both = {r.get("unit") for r in returns} & {e.get("unit") for e in escal}
    for u in sorted(x for x in both if x):
        m.append(f"{u}: both carried and escalated")
    if prev is not None:
        fixed = {t.get("unit") for t in pk.get("tasks") or [] if t.get("verdict") == "pass"}
        now = {r.get("unit"): r.get("attempts") for r in returns}
        up = {e.get("unit") for e in escal}
        for r in prev.get("returns") or []:
            u, a = r.get("unit"), r.get("attempts")
            if u in fixed or u in up:
                continue
            if u in now:
                if isinstance(a, int) and now[u] != a + 1:
                    m.append(f"{u}: attempts {now[u]} after {a} (one more per pass)")
                continue
            m.append(f"{u}: the return from pass {prev.get('pass')} was dropped (fix it first, carry it, or escalate it)")
    return m


def check_wave(pk, prev, n, unit_pat, fx_pat):
    m = []
    units = pk.get("units") or []
    if not units:
        m.append("units: a wave drafts at least one unit")
    mods = {}
    for i, u in enumerate(units):
        uid = u.get("unit", "")
        if not unit_pat.match(uid):
            m.append(f"units[{i}]: '{uid}' is not a unit id")
            continue
        if u.get("ledger") != "draft":
            m.append(f"units[{i}] {uid}: ledger is 'draft' (DRAFT/UNVERIFIED until a team pass verifies it)")
        if not u.get("file"):
            m.append(f"units[{i}] {uid}: no file")
        mod = module_of(uid)
        if mod in mods:
            m.append(f"units: {mods[mod]} and {uid} in one wave (one task per module per wave)")
        mods[mod] = uid
    gate = pk.get("gate") or {}
    for k in ("builds", "runs", "contract"):
        if not isinstance(gate.get(k), bool):
            m.append(f"gate.{k}: true or false")
    if gate.get("accepted"):
        m.append("gate: the QA gates and never accepts (T5)")
    for fx in pk.get("fix_notes") or []:
        fid = fx.get("id", "") if isinstance(fx, dict) else str(fx)
        if not fx_pat.match(fid) or (n is not None and fid.split("-")[1] != str(n)):
            m.append(f"fix_notes: '{fid}' is not FX-{n}-<n>")
    if prev is not None:
        owed = [fx.get("id") if isinstance(fx, dict) else fx for fx in prev.get("fix_notes") or []]
        applied = set(pk.get("applied_fix_notes") or [])
        for fid in owed:
            if fid not in applied:
                m.append(f"applied_fix_notes: {fid} from wave {prev.get('wave')} not applied (fix notes go first)")
    return m


# ---------- selftest -------------------------------------------------------------------------------

def selftest():
    cases = []
    ok = lambda cond, name: cases.append((bool(cond), name))  # noqa: E731

    ok(fuel(["M01", "fuel=3"]) == ("3", None), "fuel=3 is three passes")
    ok(fuel(["fuel=ALL"]) == ("all", None), "fuel=all")
    ok(fuel(["M01.D01.T01"])[1] == REFUSAL, "no fuel: the one-line refusal")
    ok(fuel(["fuel=0"])[0] is None, "fuel=0 refused")
    ok(fuel(["fuel=lots"])[0] is None, "fuel=lots refused")
    ok(fuel(["fuel=2", "fuel=3"])[0] is None, "fuel declared twice refused")

    r, p = unit_range("M01.D01.T01", "M03.D06.T09")
    ok(not p and r["modules"] == ["M01", "M02", "M03"], f"a range covers its modules: {r}")
    ok(unit_range("M03.D01.T01", "M01.D01.T01")[1], "a range backwards is refused")
    ok(unit_range("M1.D1.T1")[1], "a malformed id is refused")
    ok(not unit_range("M02")[1], "one module is a range")

    cards = [{"unit": "M01.D01.T01", "file": "a.py"},
             {"unit": "M01.D01.T02", "file": "b.py", "depends_on": ["M01.D01.T01"]},
             {"unit": "M02.D01.T01", "file": "c.py"},
             {"unit": "M02.D01.T02", "file": "d.py", "depends_on": ["M01.D01.T01"]},
             {"unit": "M01.D02.T01", "file": "e.py"}]
    w, p = waves(cards)
    ok(not p and w[0] == ["M01.D01.T01", "M02.D01.T01"], f"wave 1: independent, one per module: {w}")
    ok(all(len({module_of(u) for u in x}) == len(x) for x in w), "never two tasks of one module in a wave")
    pos = {u: i for i, x in enumerate(w) for u in x}
    ok(all(pos[d] < pos[c["unit"]] for c in cards for d in c.get("depends_on", [])), "every dependency in an earlier wave")
    ok(sum(len(x) for x in w) == 5, "every card drafted once")
    ok(waves(cards + [{"unit": "M03.D01.T01", "file": "a.py"}])[1], "two cards on one file refused")
    ok(waves([{"unit": "M01.D01.T01", "file": "a", "depends_on": ["M01.D01.T02"]},
              {"unit": "M01.D01.T02", "file": "b", "depends_on": ["M01.D01.T01"]}])[1], "a cycle is named")
    ok(waves([{"unit": "M01.D01.T01", "file": "a", "depends_on": ["M09.D01.T01"]}])[1], "a dependency with no card")

    p1 = {"packet": 1, "mode": "extreme-go-horse", "run": "kraken-2026-10-28-1", "pass": 1,
          "fuel": {"declared": "3", "used": 1}, "range": {"from": "M01.D01.T01", "to": "M02.D01.T05"},
          "teams": {"A": {"span": ["M01"], "models": {"dv": "sonnet", "qa": "opus"}},
                    "B": {"span": ["M02"], "models": {"dv": "sonnet", "qa": "opus"}}},
          "tasks": [{"unit": "M01.D01.T01", "team": "A", "gate": "green", "verdict": "pass", "ledger": "review"},
                    {"unit": "M02.D01.T01", "team": "B", "gate": "green", "verdict": "return", "ledger": "ongoing"},
                    {"unit": "M02.D01.T02", "team": "B", "gate": "red", "verdict": "not-reviewed", "ledger": "ongoing"}],
          "returns": [{"unit": "M02.D01.T01", "team": "B", "from": "QA", "key": "defect-a", "attempts": 1, "artefact": "r/1.md"},
                      {"unit": "M02.D01.T02", "team": "B", "from": "gate", "key": "gate-red", "attempts": 1, "artefact": "r/2.log"}],
          "escalations": [], "seam": {"findings": []}}
    ok(check_packet(p1) == [], f"a sound first packet holds: {check_packet(p1)}")
    p2 = json.loads(json.dumps(p1))
    p2.update(**{"pass": 2, "fuel": {"declared": "3", "used": 2}})
    p2["tasks"] = [{"unit": "M02.D01.T01", "team": "B", "gate": "green", "verdict": "pass", "ledger": "review"}]
    p2["returns"] = [{"unit": "M02.D01.T02", "team": "B", "from": "gate", "key": "gate-red", "attempts": 2, "artefact": "r/3.log"}]
    ok(check_packet(p2, p1) == [], f"a sound second packet holds: {check_packet(p2, p1)}")

    def miss(fn, text, base=p1, prev=None):
        pk = json.loads(json.dumps(base))
        fn(pk)
        found = check_packet(pk, prev)
        ok(any(text in x for x in found), f"planted: {text} -> {found[:2]}")

    miss(lambda k: k.update(mode="lazy"), "not a speed mode")
    miss(lambda k: k.update(run="jit-2026-10-28-1"), "is not 'kraken-")
    miss(lambda k: k["fuel"].update(declared="lots"), "neither a whole number")
    miss(lambda k: k["fuel"].update(used=2), "must equal the pass number")
    miss(lambda k: (k.update(**{"pass": 4}), k["fuel"].update(used=4)), "exceed the declared fuel")
    miss(lambda k: k["teams"]["B"].update(span=["M01"]), "one agent per module")
    miss(lambda k: k["teams"]["A"]["models"].update(dv="haiku"), "the pairing is sonnet")
    miss(lambda k: k["teams"]["B"]["models"].update(qa="sonnet"), "the pairing is opus")
    miss(lambda k: k["tasks"][2].update(verdict="pass"), "a red gate is never a pass")
    miss(lambda k: k["tasks"][0].update(ledger="done"), "never 'done'")
    miss(lambda k: k["tasks"][0].update(verdict="approved"), "verdict is one of")
    miss(lambda k: k["returns"][0].update(attempts=3), "a third failure is an escalation")
    miss(lambda k: k["returns"][0].update(artefact=""), "names no artefact")
    miss(lambda k: k["escalations"].append({"unit": "M02.D01.T01", "attempts": 3, "to": "RGN"}), "both carried and escalated")
    miss(lambda k: k["escalations"].append({"unit": "M02.D01.T09", "attempts": 2, "to": "RGN"}), "follows the third failure")
    miss(lambda k: k.update(returns=[]), "was dropped", base=p2, prev=p1)
    miss(lambda k: k["returns"][0].update(attempts=1), "one more per pass", base=p2, prev=p1)
    miss(lambda k: k.update(**{"pass": 3}), "does not follow", base=p2, prev=p1)

    w1 = {"packet": 1, "mode": "just-in-time", "run": "jit-2026-10-28-1", "wave": 1,
          "units": [{"unit": "M01.D01.T01", "file": "a.py", "ledger": "draft"},
                    {"unit": "M02.D01.T01", "file": "c.py", "ledger": "draft"}],
          "gate": {"builds": True, "runs": True, "contract": False},
          "fix_notes": [{"id": "FX-1-1", "note": "Money is decimal in the contract"}], "applied_fix_notes": []}
    ok(check_packet(w1) == [], f"a sound wave holds: {check_packet(w1)}")
    w2 = json.loads(json.dumps(w1))
    w2.update(wave=2, units=[{"unit": "M01.D01.T02", "file": "b.py", "ledger": "draft"}], fix_notes=[],
              applied_fix_notes=["FX-1-1"], gate={"builds": True, "runs": True, "contract": True})
    ok(check_packet(w2, w1) == [], f"a sound second wave holds: {check_packet(w2, w1)}")
    miss(lambda k: k["units"][0].update(ledger="review"), "ledger is 'draft'", base=w1)
    miss(lambda k: k["units"].append({"unit": "M01.D01.T02", "file": "b.py", "ledger": "draft"}), "one task per module per wave", base=w1)
    miss(lambda k: k["gate"].update(runs="yes"), "gate.runs", base=w1)
    miss(lambda k: k["gate"].update(accepted=True), "never accepts", base=w1)
    miss(lambda k: k.update(fix_notes=["FX-3-1"]), "is not FX-1-", base=w1)
    miss(lambda k: k.update(applied_fix_notes=[]), "not applied", base=w2, prev=w1)

    sys.path.insert(0, str(ROOT / "scripts"))
    import returns  # the stage shapes live in packets.md section 4; the doctrine names them
    doctrine = (ROOT / "library" / "team" / "SPEED_MODES.md").read_text(encoding="utf-8")
    named = set(re.findall(r"`((?:po|dv|qa|da)\.[a-z]+)`", doctrine.split("## 3.")[0]))
    shapes = set(returns.load_shapes()["stages"])
    ok(named and named <= shapes, f"every stage SPEED_MODES section 2 names has a shape in packets.md: {sorted(named - shapes)}")

    bad = [name for good, name in cases if not good]
    for name in bad:
        print("MISS", name)
    print(f"speed selftest: {len(cases) - len(bad)}/{len(cases)} ok")
    return 1 if bad else 0


# ---------- command line ---------------------------------------------------------------------------

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "--selftest":
        return selftest()
    if cmd == "fuel":
        value, refusal = fuel(rest)
        print(f"fuel {value}" if value else refusal)
        return 0 if value else 2
    if cmd == "range" and 1 <= len(rest) <= 2:
        r, problems = unit_range(*rest)
        for p in problems:
            print("FAIL", p)
        if r:
            print(f"range {r['from']} -> {r['to']}   modules: {' '.join(r['modules'])}")
        return 2 if problems else 0
    if cmd == "waves" and len(rest) == 1:
        data = load(rest[0])
        out, problems = waves(data.get("cards", data) if isinstance(data, dict) else data)
        for p in problems:
            print("FAIL", p)
        for i, w in enumerate(out, 1):
            print(json.dumps({"wave": i, "units": w}))
        return 1 if problems else 0
    if cmd == "packet" and 1 <= len(rest) <= 2:
        pk = load(rest[0])
        found = check_packet(pk, load(rest[1]) if len(rest) == 2 else None)
        for x in found:
            print("MISS", x)
        print(f"packet {rest[0]}: {'holds' if not found else f'{len(found)} miss(es)'}")
        return 1 if found else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
