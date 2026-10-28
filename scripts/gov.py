#!/usr/bin/env python3
"""gov.py - governance grammar for regency packets, after Jan Kooiman.

Kooiman reads governing as interaction among actors with partial authority (Modern Governance, 1993,
ed.) and structures it in Governing as Governance (2003). Regency takes four of his ideas and makes
each one checkable:

  orders     G1 first order   solving problems: dispatch, delivery, the QA -> DV loop
             G2 second order  the institutions that frame G1: SPEC vN+1, gates, ladder, Orders, classes
             G3 meta          the norms behind G2: conventions, maxims, F0 norms
  modes      hier             command down the tree: Regent -> managers -> operators
             co               managers together, or a manager with the Regent (the PO/QA co-signature)
             self             a role or subagent inside its declared span
  elements   image            shared understanding broke: spec, criterion, intent
             instrument       a tool broke: hook, gate, lint, script, template
             action           the work broke: test, build, defect
  fit        governability: the Regent's review capacity measured against what reaches it
  recur      the flywheel's sensor: findings that keep coming back, by key

The packet contract (tags G1/G2/G3, never O#, which regency already uses for its levels):

    gov: order=G2 · mode=co · element=image · from=QA · to=RGN · unit=M03.D02.T04 · key=criterion-untestable
    ask: approve SPEC v3 (criterion C-04 untestable)

Routing: G1 stays in the ledger; G2 and G3 reach the Regent. A missing, malformed or under-declared
header routes UP, never down (conventions E2: surplus parts over missing parts).

key= (optional) names the finding's class as a lower-case slug, so two findings can be known to be the
same finding. record() keeps a per-key aggregate beside the queue (gov-keys.json) that is NOT trimmed
with the queue, so a slow recurrence is not forgotten. `recur` reads it and prints candidates: keys seen
at least THRESHOLD times across at least UNITS distinct units within the last WINDOW passes. It proposes;
it ratifies nothing (conventions 1). The three numbers are proposals awaiting the Regent.

Modes:  header ... · check FILE|- · queue · fit · recur · --selftest
Pure standard library, Python 3.8+.
"""
import argparse
import collections
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

ORDERS = ("G1", "G2", "G3")
MODES = ("hier", "co", "self")
ELEMENTS = ("image", "instrument", "action")
ROLES = ("RGN", "PO", "QA", "DA", "DV")
MANAGERS, OPERATORS = {"PO", "QA"}, {"DA", "DV"}
RANK = {"RGN": 0, "PO": 1, "QA": 1, "DA": 2, "DV": 2}
OWNER = {  # subagent -> role that owns it (TEAM-ORCHESTRATION, 13 subagents)
    "suba-requirements-analyst": "PO", "suba-strategy": "PO", "suba-research": "PO", "suba-design": "PO",
    "suba-recon": "QA", "suba-tester": "QA", "suba-validator": "QA",
    "suba-acquisition": "DA", "suba-analysis": "DA", "suba-modeling": "DA",
    "suba-scribe": "DV", "suba-architect": "DV", "suba-implementer": "DV",
}
QUEUE, KEEP = "gov-queue.jsonl", 200
DEFAULT_CAPACITY = 3  # Regent packets per pass before the fit is called strained

# The flywheel's sensor. Proposals awaiting the Regent; override per call with --threshold/--units/--window.
KEYS = "gov-keys.json"
RECUR_THRESHOLD = 3   # occurrences of one key inside the window
RECUR_UNITS = 2       # ... spread over at least this many distinct units (one unit repeating is one problem)
RECUR_WINDOW = 10     # the latest N passes (conversation ids) count
KEEP_PASSES = 100     # pass order remembered by the aggregate
KEEP_PER_KEY = 50     # occurrences remembered per key
KEY = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUNG = {  # the conventions 15.1 ladder, read from the element: a suggestion for the drafter, never a decision
    "image": "F0 norm text (a gate cannot settle meaning)",
    "instrument": "fix the tool, then a gate check",
    "action": "gate check or template",
}

HEADER = re.compile(r"^[ \t>*_`]*gov:[ \t]*(.+?)[ \t`*_]*$", re.M | re.I)
ASK = re.compile(r"^[ \t>*_`]*ask:[ \t]*(.+?)[ \t`*_]*$", re.M | re.I)
PAIR = re.compile(r"([a-z]+)\s*=\s*([^\s·;,|]+)", re.I)

# What the text says, whatever the header claims. Order is read from the most structural signal found.
META = re.compile(r"(?i)\b(conventions?|CODE-CONVENTIONS|maxims?|F0|meta-?governance|principles?|norms? (change|amend))")
INSTITUTION = re.compile(r"(?i)(SPEC v\d+|vN\+1|\bgates?\b|\bladder\b|orchestration|\bprotocol\b|\btemplates?\b|\bclass C\d"
                         r"|third (failure|loop)|loop 3|\bT4\b|escalat\w*|Quality Expectations Brief|\bQEB\b)")
ELEMENT_SIGNS = {
    "image": re.compile(r"(?i)(ambigu\w*|unclear|untestable|criteri\w*|\bspecs?\b|expectations?|scenarios?|misread"
                        r"|interpret\w*|intent|out[- ]of[- ]scope|meaning)"),
    "instrument": re.compile(r"(?i)(\bhooks?\b|\blint\w*|\bscripts?\b|\bgates?\b|\btool(s|ing)?\b|doctor|manifest"
                             r"|\bCI\b|pipeline|selftest|template|matcher)"),
    "action": re.compile(r"(?i)(tests? fail\w*|failed|failing|\bbugs?\b|exception|regression|build (broke|fail\w*)"
                         r"|crash\w*|wrong output|defect)"),
}


# ---------- reading ------------------------------------------------------------------------------

def role_of(name):
    """RGN/PO/QA/DA/DV for a role name, a subagent name or a plugin-scoped name; None if unknown."""
    n = (name or "").strip().split(":")[-1].strip()
    up = n.upper()
    if up in ROLES:
        return up
    if up in ("REGENT", "REGENTE"):
        return "RGN"
    return OWNER.get(n.lower())


def parse(text):
    """The first gov: header in a packet as a dict (keys lower-case, values as written); None if absent."""
    m = HEADER.search(text or "")
    if not m:
        return None
    h = {k.lower(): v for k, v in PAIR.findall(m.group(1))}
    a = ASK.search(text or "")
    if a:
        h["ask"] = a.group(1).strip()
    for k in ("order", "from", "to"):
        if k in h:
            h[k] = h[k].upper()
    for k in ("mode", "element", "key"):
        if k in h:
            h[k] = h[k].lower()
    for k in ("from", "to"):
        if k in h and h[k] not in ROLES:
            h[k] = role_of(h[k]) or h[k]
    return h


def problems(h):
    """Why a header is malformed or breaks the topology; [] when it is sound."""
    if h is None:
        return ["no gov: header"]
    out = []
    for key, allowed in (("order", ORDERS), ("mode", MODES), ("element", ELEMENTS)):
        if h.get(key) not in allowed:
            out.append(f"{key}={h.get(key, '?')} is not one of {'/'.join(allowed)}")
    src, dst = h.get("from"), h.get("to")
    for key, val in (("from", src), ("to", dst)):
        if val is None:
            out.append(f"{key}= is missing")
        elif val not in ROLES:
            out.append(f"{key}={val} is not a role (RGN/PO/QA/DA/DV or a suba-)")
    if "key" in h and not KEY.match(h["key"]):
        out.append(f"key={h['key']} is not a lower-case slug (contract-nullable)")
    if out:
        return out
    mode, order = h["mode"], h["order"]
    if {src, dst} == OPERATORS:
        out.append("DA and DV never talk directly; route through a manager")
    if src == dst:
        out.append("a role does not address itself (T5)")
    if mode == "hier" and not (RANK[src] < RANK[dst] or (src, dst) == ("PO", "QA")):
        out.append(f"hier runs down the tree; {src} -> {dst} does not")
    if mode == "co" and not (src in MANAGERS and dst in MANAGERS | {"RGN"}):
        out.append(f"co-governance is the managers' mode; {src} -> {dst} is not")
    if mode == "self" and src == "RGN":
        out.append("the Regent governs by hier, never self")
    if order == "G3" and dst != "RGN":
        out.append("G3 (meta) is addressed only to the Regent")
    if order == "G2" and dst in OPERATORS:
        out.append("G2 (institutions) is never addressed to an operator")
    return out


def infer(text):
    """(order, element, reasons) read from the packet's words alone."""
    reasons = []
    if META.search(text or ""):
        order = "G3"
        reasons.append("names a norm or convention")
    elif INSTITUTION.search(text or ""):
        order = "G2"
        reasons.append("names an institution (spec version, gate, ladder, escalation)")
    else:
        order = "G1"
    scores = {e: len(rx.findall(text or "")) for e, rx in ELEMENT_SIGNS.items()}
    best = max(scores.values())
    element = next((e for e in ELEMENTS if scores[e] == best), "action") if best else "action"
    return order, element, reasons


def higher(a, b):
    return a if ORDERS.index(a) >= ORDERS.index(b) else b


def route(text, sender=None):
    """The routing decision for one packet. sender fills from= when the header lacks it."""
    h = parse(text)
    if h is not None and sender and "from" not in h:
        h["from"] = role_of(sender) or sender
    found = problems(h)
    inferred, element, reasons = infer(text)
    flags = []
    if h is None:
        order = higher("G2", inferred)
        flags.append("undeclared")
    else:
        order = h.get("order") if h.get("order") in ORDERS else "G2"
        if ORDERS.index(inferred) > ORDERS.index(order):
            order = inferred
            flags.append(f"under-declared ({h.get('order')} -> {inferred})")
        if found:
            order = higher(order, "G2")
            flags.append("invalid")
    return {
        "order": order,
        "mode": (h or {}).get("mode"),
        "element": (h or {}).get("element") if (h or {}).get("element") in ELEMENTS else element,
        "from": (h or {}).get("from") or role_of(sender) or sender,
        "to": (h or {}).get("to"),
        "unit": (h or {}).get("unit") or wire.units_in(text),
        "key": (h or {}).get("key") if KEY.match((h or {}).get("key") or "") else None,
        "ask": (h or {}).get("ask"),
        "route": "ledger" if order == "G1" else "regent",
        "flags": flags,
        "problems": found if h is not None else [],
        "reasons": reasons,
    }


def build(order, mode, element, src, dst, ask, unit=None, key=None):
    """Two lines an agent pastes at the top of a packet; raises ValueError when they break the grammar."""
    h = {"order": order.upper(), "mode": mode.lower(), "element": element.lower(),
         "from": role_of(src) or src.upper(), "to": role_of(dst) or dst.upper()}
    if key:
        h["key"] = key.lower()
    bad = problems(h)
    if bad:
        raise ValueError("; ".join(bad))
    head = f"gov: order={h['order']} · mode={h['mode']} · element={h['element']} · from={h['from']} · to={h['to']}"
    return head + (f" · unit={unit}" if unit else "") + (f" · key={h['key']}" if key else "") + f"\nask: {ask}"


# ---------- queue --------------------------------------------------------------------------------

def record(vdir, decision, agent=None, session=None):
    """Append one routing decision to <virtual>/gov-queue.jsonl, trimmed to the latest KEEP lines."""
    entry = {"ts": wire.now(), "gen_ai.agent.name": agent or "main", "gen_ai.conversation.id": session,
             **{f"gov.{k}": v for k, v in decision.items() if k not in ("problems", "reasons") and v}}
    p = Path(vdir) / QUEUE
    lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
    lines.append(json.dumps(entry, ensure_ascii=False))
    wire.atomic_write(p, "\n".join(lines[-KEEP:]) + "\n")
    remember(vdir, entry)
    return entry


# ---------- keys: the flywheel's sensor ----------------------------------------------------------

def read_keys(vdir):
    """The per-key aggregate; an empty one when absent. None when present but unreadable (never overwritten)."""
    p = Path(vdir) / KEYS if vdir else None
    if not p or not p.is_file():
        return {"schema": 1, "passes": [], "keys": {}}
    try:
        agg = json.loads(p.read_text(encoding="utf-8"))
        return agg if isinstance(agg.get("passes"), list) and isinstance(agg.get("keys"), dict) else None
    except ValueError:
        return None


def remember(vdir, entry, count=True):
    """Fold one recorded packet into gov-keys.json; count=False adds the occurrence without counting a packet."""
    agg = read_keys(vdir)
    if agg is None:
        print(f"gov.py: {KEYS} is unreadable; left untouched, this packet not counted", file=sys.stderr)
        return
    pid = entry.get("gen_ai.conversation.id") or "?"
    key = entry.get("gov.key")
    passes = agg["passes"]
    if not passes or passes[-1]["id"] != pid:
        known = next((x for x in passes if x["id"] == pid), None)
        if known:
            passes.remove(known)
        passes.append(known or {"id": pid, "packets": 0, "keyed": 0})
    current = passes[-1]
    if count:
        current["packets"] += 1
        current["keyed"] += 1 if key else 0
    if key:
        occ = agg["keys"].setdefault(key, [])
        occ.append({"ts": entry.get("ts"), "pass": pid, "unit": entry.get("gov.unit"),
                    "element": entry.get("gov.element"), "route": entry.get("gov.route")})
        agg["keys"][key] = occ[-KEEP_PER_KEY:]
    agg["passes"] = passes[-KEEP_PASSES:]
    wire.atomic_write(Path(vdir) / KEYS, json.dumps(agg, ensure_ascii=False, indent=1) + "\n")


def note(vdir, key, unit=None, element="action", session=None):
    """Count a keyed finding that is not a packet - a return that missed its shape (returns.py). The key
    aggregate gains an occurrence; packet and coverage counts stay as they are, so fit is not inflated."""
    if vdir and KEY.match(key or ""):
        remember(vdir, {"ts": wire.now(), "gen_ai.conversation.id": session, "gov.key": key, "gov.unit": unit,
                        "gov.element": element, "gov.route": "ledger"}, count=False)


def recur(agg, threshold=RECUR_THRESHOLD, units=RECUR_UNITS, window=RECUR_WINDOW):
    """Keys that came back often enough, across enough units, inside the window. Proposes; decides nothing."""
    span = (agg or {}).get("passes", [])[-window:]
    inside = {x["id"] for x in span}
    packets, keyed = sum(x["packets"] for x in span), sum(x["keyed"] for x in span)
    rows = []
    for key, occ in (agg or {}).get("keys", {}).items():
        hits = [o for o in occ if o.get("pass") in inside]
        if not hits:
            continue
        distinct = {o["unit"] for o in hits if o.get("unit")}
        element = collections.Counter(o.get("element") for o in hits).most_common(1)[0][0]
        rows.append({"key": key, "hits": len(hits), "units": len(distinct), "element": element,
                     "to_regent": sum(1 for o in hits if o.get("route") == "regent"),
                     "rung": RUNG.get(element, RUNG["action"]), "last": max(o.get("ts") or "" for o in hits),
                     "candidate": len(hits) >= threshold and len(distinct) >= units})
    rows.sort(key=lambda r: (not r["candidate"], -r["hits"], -r["units"], r["key"]))
    return {"window_passes": len(span), "packets": packets, "keyed": keyed,
            "coverage": round(keyed / packets, 2) if packets else 0.0,
            "rule": f"{threshold}x across {units} units within {window} passes (proposal)",
            "candidates": [r for r in rows if r["candidate"]],
            "watching": [r for r in rows if not r["candidate"]]}


def read_queue(vdir):
    p = Path(vdir) / QUEUE if vdir else None
    out = []
    for line in (p.read_text(encoding="utf-8").splitlines() if p and p.is_file() else []):
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def fit(entries, capacity=DEFAULT_CAPACITY):
    """Governability, after Kooiman: what the governing system must absorb versus what it can."""
    if not entries:
        return {"packets": 0, "verdict": "no packets recorded yet"}
    passes = collections.Counter(e.get("gen_ai.conversation.id") or "?" for e in entries if e.get("gov.route") == "regent")
    flags = collections.Counter(f.split(" ")[0] for e in entries for f in e.get("gov.flags", []))
    regent = sum(passes.values())
    load = regent / max(1, len(passes)) if passes else 0.0
    report = {
        "packets": len(entries),
        "to_regent": regent,
        "to_ledger": len(entries) - regent,
        "regent_load_per_pass": round(load, 2),
        "capacity_per_pass": capacity,
        "diversity_agents": len({e.get("gov.from") for e in entries if e.get("gov.from")}),
        "dynamics_flags": dict(flags),
        "complexity_units": len({e.get("gov.unit") for e in entries if e.get("gov.unit")}),
        "by_element": dict(collections.Counter(e.get("gov.element") for e in entries if e.get("gov.route") == "regent")),
    }
    undeclared = flags.get("undeclared", 0) + flags.get("under-declared", 0) + flags.get("invalid", 0)
    if load > capacity:
        report["verdict"] = f"strained: {load:.1f} Regent packets per pass against {capacity}"
    elif undeclared * 2 > len(entries):
        report["verdict"] = "noisy: more than half the packets needed their header corrected"
    else:
        report["verdict"] = "fit"
    return report


# ---------- CLI ----------------------------------------------------------------------------------

def here_vdir(repo):
    return wire.virtual_dir(wire.repo_root(Path(repo).resolve()))


def cli(argv):
    ap = argparse.ArgumentParser(prog="gov.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    h = sub.add_parser("header", help="build a valid gov: header")
    for k in ("order", "mode", "element", "from", "to", "ask"):
        h.add_argument(f"--{k}", required=True)
    h.add_argument("--unit")
    h.add_argument("--key")
    c = sub.add_parser("check", help="route one packet (file or - for stdin)")
    c.add_argument("path")
    c.add_argument("--sender")
    q = sub.add_parser("queue", help="packets routed to the Regent")
    q.add_argument("--repo", default=".")
    q.add_argument("--all", action="store_true")
    q.add_argument("-n", type=int, default=20)
    f = sub.add_parser("fit", help="governability report")
    f.add_argument("--repo", default=".")
    f.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY)
    k = sub.add_parser("recur", help="findings that keep coming back: promotion candidates (read-only)")
    k.add_argument("--repo", default=".")
    k.add_argument("--threshold", type=int, default=RECUR_THRESHOLD)
    k.add_argument("--units", type=int, default=RECUR_UNITS)
    k.add_argument("--window", type=int, default=RECUR_WINDOW)
    k.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "recur":
        agg = read_keys(here_vdir(a.repo))
        if agg is None:
            print(f"gov.py: {KEYS} is unreadable", file=sys.stderr)
            return 2
        rep = recur(agg, a.threshold, a.units, a.window)
        if a.json:
            print(json.dumps(rep, ensure_ascii=False, indent=2))
            return 0
        for r in rep["candidates"] + rep["watching"]:
            print(wire.one_line("candidate" if r["candidate"] else "watching", r["key"], f"{r['hits']}x",
                                f"{r['units']} units", r["element"], f"{r['to_regent']} reached RGN",
                                f"-> {r['rung']}" if r["candidate"] else None))
        print(wire.one_line(f"{len(rep['candidates'])} candidate(s)",
                            f"coverage {rep['coverage']:.0%} ({rep['keyed']}/{rep['packets']} packets keyed)",
                            f"{rep['window_passes']} pass(es) in window", rep["rule"]))
        return 0
    if a.cmd == "header":
        try:
            print(build(a.order, a.mode, a.element, getattr(a, "from"), a.to, a.ask, a.unit, a.key))
            return 0
        except ValueError as e:
            print(f"gov.py: {e}", file=sys.stderr)
            return 1
    if a.cmd == "check":
        text = sys.stdin.read() if a.path == "-" else Path(a.path).read_text(encoding="utf-8")
        d = route(text, a.sender)
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return 1 if "invalid" in d["flags"] or "undeclared" in d["flags"] else 0
    if a.cmd == "queue":
        rows = [e for e in read_queue(here_vdir(a.repo)) if a.all or e.get("gov.route") == "regent"][-a.n:]
        for e in rows:
            print(wire.one_line(e.get("ts"), e.get("gov.order"), e.get("gov.element"), e.get("gov.from"), e.get("gov.unit"),
                                e.get("gov.ask"), ",".join(e.get("gov.flags", []))))
        print(f"{len(rows)} packet(s)")
        return 0
    if a.cmd == "fit":
        print(json.dumps(fit(read_queue(here_vdir(a.repo)), a.capacity), ensure_ascii=False, indent=2))
        return 0
    ap.print_help()
    return 0


# ---------- self-test ----------------------------------------------------------------------------

def selftest():
    G1 = "gov: order=G1 · mode=self · element=action · from=DV · to=QA · unit=M03.D02.T04\nask: re-run the named test"
    cases = []

    def r(text, sender=None):
        return route(text, sender)

    d = r(G1)
    cases.append((d["route"] == "ledger" and not d["flags"], f"sound G1 stays in the ledger: {d['route']} {d['flags']}"))
    cases.append((d["unit"] == "M03.D02.T04" and d["ask"] == "re-run the named test", "unit and ask are read"))
    d = r("**gov: order=g2 · mode=co · element=image · from=qa · to=regent**\nask: approve SPEC v3")
    cases.append((d["order"] == "G2" and d["route"] == "regent" and d["to"] == "RGN" and not d["flags"],
                  "markdown-wrapped, lower-case header parses; Regent alias resolves"))
    d = r("Done. Tests pass.")
    cases.append((d["route"] == "regent" and "undeclared" in d["flags"], "no header routes up (E2)"))
    d = r(G1.replace("re-run the named test", "propose SPEC v4: criterion C-04 is untestable"))
    cases.append((d["order"] == "G2" and any(f.startswith("under-declared") for f in d["flags"]),
                  "a G1 that names a spec version is under-declared and climbs to G2"))
    d = r(G1.replace("re-run the named test", "amend CODE-CONVENTIONS S3"))
    cases.append((d["order"] == "G3", "a G1 that names a convention climbs to G3"))
    d = r("gov: order=G1 · mode=self · element=action · from=DA · to=DV\nask: take this data")
    cases.append(("invalid" in d["flags"] and d["route"] == "regent" and any("DA and DV" in p for p in d["problems"]),
                  "DA -> DV is refused and routed up"))
    d = r("gov: order=G1 · mode=hier · element=action · from=DV · to=QA\nask: fix your test")
    cases.append((any("hier runs down" in p for p in d["problems"]), "an operator cannot command a manager"))
    d = r("gov: order=G1 · mode=hier · element=action · from=PO · to=QA\nask: verify")
    cases.append((not d["problems"], "PO -> QA dispatch is a legitimate hier edge (Development topology)"))
    d = r("gov: order=G2 · mode=co · element=image · from=DV · to=RGN\nask: x")
    cases.append((any("co-governance" in p for p in d["problems"]), "co is the managers' mode"))
    d = r("gov: order=G3 · mode=co · element=image · from=PO · to=QA\nask: change the maxim")
    cases.append((any("G3 (meta)" in p for p in d["problems"]), "G3 is addressed only to the Regent"))
    d = r("gov: order=G2 · mode=hier · element=instrument · from=QA · to=DV\nask: change the gate")
    cases.append((any("never addressed to an operator" in p for p in d["problems"]), "G2 never goes to an operator"))
    d = r("gov: order=G1 · mode=self · element=action · to=QA\nask: done", sender="regency:suba-implementer")
    cases.append((d["from"] == "DV" and not d["problems"], "from= fills from the subagent's owner"))
    d = r("gov: order=G4 · mode=solo · element=vibe · from=DV · to=QA\nask: x")
    cases.append((len(d["problems"]) == 3 and d["order"] == "G2", "unknown values are three problems, routed up"))
    _, el, _ = infer("the hook matcher misfired and the lint script crashed")
    cases.append((el == "instrument", f"element read as instrument: {el}"))
    _, el, _ = infer("criterion C-02 is ambiguous; the spec scenario can be read two ways")
    cases.append((el == "image", f"element read as image: {el}"))
    _, el, _ = infer("the named test failed with an exception")
    cases.append((el == "action", f"element read as action: {el}"))
    cases.append((build("G2", "co", "image", "QA", "Regent", "approve SPEC v3", "M03")
                  .startswith("gov: order=G2 · mode=co · element=image · from=QA · to=RGN · unit=M03"), "header builder"))
    try:
        build("G1", "self", "action", "DA", "DV", "x")
        cases.append((False, "builder refuses DA -> DV"))
    except ValueError:
        cases.append((True, "builder refuses DA -> DV"))
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(KEEP + 5):
            record(tmp, route(G1), session="p1")
        cases.append((len(read_queue(tmp)) == KEEP, f"queue trimmed to {KEEP}"))
        for s in ("p2", "p2", "p2", "p2", "p3"):
            record(tmp, route("no header at all"), session=s)
        rep = fit(read_queue(tmp), capacity=3)
        cases.append((rep["to_regent"] == 5 and rep["regent_load_per_pass"] == 2.5 and rep["verdict"] == "fit",
                      f"fit: {rep['regent_load_per_pass']} per pass -> {rep['verdict']}"))
        rep = fit(read_queue(tmp), capacity=2)
        cases.append((rep["verdict"].startswith("strained"), f"fit under lower capacity: {rep['verdict']}"))
    cases.append((fit([])["packets"] == 0, "fit with no packets"))

    # ---- keys: the flywheel's sensor
    d = r(G1.replace("unit=M03.D02.T04", "unit=M03.D02.T04 · key=contract-nullable"))
    cases.append((d["key"] == "contract-nullable" and not d["problems"], "key= is read and is no problem"))
    d = r(G1.replace("unit=M03.D02.T04", "unit=M03.D02.T04 · key=Contract-Nullable"))
    cases.append((d["key"] == "contract-nullable", "key= is lower-cased"))
    d = r(G1.replace("unit=M03.D02.T04", "unit=M03.D02.T04 · key=null_check!"))
    cases.append((d["key"] is None and "invalid" in d["flags"] and d["route"] == "regent",
                  "a key that is not a slug is a problem, routed up, and never counted"))
    cases.append((r(G1)["key"] is None and not r(G1)["problems"], "key= stays optional"))
    cases.append((build("G1", "self", "action", "DV", "QA", "x", "M03", "Contract-Nullable")
                  .endswith("unit=M03 · key=contract-nullable\nask: x"), "header builder writes key="))

    def pkt(unit, key, order="G1"):
        to = "QA" if order == "G1" else "RGN"
        mode = "self" if order == "G1" else "co"
        src = "DV" if order == "G1" else "QA"
        return f"gov: order={order} · mode={mode} · element=action · from={src} · to={to} · unit={unit} · key={key}\nask: x"

    with tempfile.TemporaryDirectory() as tmp:
        # one unit repeating is one problem, not a recurrence
        for _ in range(4):
            record(tmp, route(pkt("M01.D01.T01", "same-unit")), session="p1")
        rep = recur(read_keys(tmp))
        cases.append((not rep["candidates"] and [w["key"] for w in rep["watching"]] == ["same-unit"],
                      "4 hits in ONE unit stay watching, not a candidate"))
        # three hits across two units: a candidate
        record(tmp, route(pkt("M01.D01.T02", "contract-nullable")), session="p2")
        record(tmp, route(pkt("M02.D01.T01", "contract-nullable", "G2")), session="p2")
        record(tmp, route(pkt("M02.D01.T03", "contract-nullable")), session="p3")
        rep = recur(read_keys(tmp))
        c = rep["candidates"][0] if rep["candidates"] else {}
        cases.append((c.get("key") == "contract-nullable" and c.get("hits") == 3 and c.get("units") == 3
                      and c.get("to_regent") == 1 and c.get("rung") == RUNG["action"],
                      f"3 hits across 3 units become a candidate with its rung: {c.get('key')} {c.get('hits')}x {c.get('units')} units"))
        cases.append((rep["packets"] == 7 and rep["keyed"] == 7 and rep["coverage"] == 1.0, "coverage counts keyed packets"))
        record(tmp, route(G1), session="p3")
        cases.append((recur(read_keys(tmp))["coverage"] == round(7 / 8, 2), "an unkeyed packet lowers coverage"))
        # the aggregate survives the queue's trim
        for i in range(KEEP + 5):
            record(tmp, route(G1), session="p3")
        cases.append((len(read_queue(tmp)) == KEEP and "contract-nullable" in read_keys(tmp)["keys"],
                      "the queue trims to KEEP; the key aggregate does not forget"))
        # the window slides: old passes stop counting
        for i in range(RECUR_WINDOW):
            record(tmp, route(G1), session=f"later-{i}")
        cases.append((not recur(read_keys(tmp))["candidates"], "after WINDOW newer passes, old hits leave the window"))
        cases.append(([c["key"] for c in recur(read_keys(tmp), window=RECUR_WINDOW + 3)["candidates"]] == ["contract-nullable"],
                      "a wider window brings them back (thresholds are parameters, not law)"))
        # an unreadable aggregate is never overwritten
        (Path(tmp) / KEYS).write_text("{not json", encoding="utf-8")
        record(tmp, route(pkt("M09.D01.T01", "contract-nullable")), session="p9")
        cases.append(((Path(tmp) / KEYS).read_text(encoding="utf-8") == "{not json" and read_keys(tmp) is None,
                      "an unreadable gov-keys.json is left untouched (no data loss)"))
    cases.append((recur(None)["candidates"] == [] and recur({"passes": [], "keys": {}})["packets"] == 0,
                  "recur on an empty or missing aggregate"))
    with tempfile.TemporaryDirectory() as tmp:
        record(tmp, route(G1), session="n1")
        for unit in ("M01.D01.T01", "M02.D01.T01", "M03.D01.T01"):
            note(tmp, "return-build-change-notes-rollback", unit=unit, session="n1")
        note(tmp, "Not A Slug", session="n1")
        rep = recur(read_keys(tmp))
        cases.append((rep["packets"] == 1 and rep["keyed"] == 0 and [c["key"] for c in rep["candidates"]]
                      == ["return-build-change-notes-rollback"] and "Not A Slug" not in read_keys(tmp)["keys"],
                      "note() counts a shape miss as a finding, never as a packet; a bad key is dropped"))
    return wire.check(cases)


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in args else cli(args))
