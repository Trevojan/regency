#!/usr/bin/env python3
"""elicit.py - the Poka-Yoke elicitation engine: questions whose eligibility, options and wording the Harness owns.

library/elicitation.md. Correctness by construction, not by instruction: a question asked through the engine
depends structurally on the canonical value the engine stored, never on the agent remembering it.

  schema     a declarative JSON graph of questions: each owns one parameter slot, depends on others, may hold a
             restricted condition (equals, not_equals, in, not_in, exists, all, any) and 2-4 options, each with
             its own condition; prompts interpolate established values ({slot}); no code anywhere
  state      in the one store (<virtual>/index.sqlite), tables elicit_*: one writer, this module; every state
             transition and every invalidation it causes run in one transaction (BEGIN IMMEDIATE)
  authority  a value is confirmed only from the Regent's pop-up answer (hook-elicit.py, PostToolUse); a script
             may derive a slot the schema declares derivable; an agent may only propose - a proposal never
             resolves a dependency and never replaces a confirmed value
  change     an answer whose upstream value changed is invalidated with its history kept, and only the
             transitive dependents of that slot are touched; re-submitting the same value touches nothing

Modes:  check SCHEMA · start SCHEMA --task TASK · status [--session EL-####] · next [--session EL-####] [--wave N]
        · submit --session EL-#### --slot SLOT --value VALUE --source agent|derived · propose SCHEMA [--onto EL-####]
        · reopen --session EL-#### --question ID --because TEXT · reset --session EL-#### · --selftest
        (each mode takes --repo DIR)
Exit 0 done · 1 refused (validation_errors say why) · 2 no store, no session, malformed input.
Pure standard library (sqlite3), Python 3.8+.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402
import idx  # noqa: E402  (connect(): the one store)

SQL = """
CREATE TABLE IF NOT EXISTS elicit_schemas(hash TEXT NOT NULL, status TEXT NOT NULL, schema_id TEXT NOT NULL,
  version INTEGER NOT NULL, definition TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(hash, status));
CREATE TABLE IF NOT EXISTS elicit_sessions(session_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, schema_id TEXT NOT NULL,
  schema_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS elicit_params(session_id TEXT NOT NULL, slot TEXT NOT NULL, value TEXT NOT NULL,
  status TEXT NOT NULL, revision INTEGER NOT NULL, provenance TEXT NOT NULL, fingerprint TEXT NOT NULL,
  PRIMARY KEY(session_id, slot));
CREATE TABLE IF NOT EXISTS elicit_questions(session_id TEXT NOT NULL, question_id TEXT NOT NULL, presented_at TEXT,
  answered_at TEXT, fingerprint TEXT, reopened TEXT, PRIMARY KEY(session_id, question_id));
CREATE TABLE IF NOT EXISTS elicit_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, event TEXT NOT NULL,
  entity TEXT, payload TEXT, at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS elicit_events_session ON elicit_events(session_id);
"""
RESOLVED = ("confirmed", "derived")
RANK = {"proposed": 0, "invalidated": 0, "derived": 1, "confirmed": 2}
SOURCES = {"regent": "confirmed", "derived": "derived", "agent": "proposed"}
CLI_SOURCES = ("agent", "derived")          # "regent" enters only through the pop-up hook (record_answer)
ASKABLE = ("eligible", "presented", "invalidated", "reopened")
SCHEMA_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
SLOT = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
QID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
TASK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:#/-]{0,79}$")
SESSION = re.compile(r"^EL-\d{4,}$")
HOLE = re.compile(r"\{([^{}]*)\}")
OPS = ("equals", "not_equals", "in", "not_in", "exists")
TOP_KEYS = {"schema", "version", "about", "inputs", "questions"}
Q_KEYS = {"id", "slot", "header", "prompt", "options", "other", "multi", "depends_on", "when", "order", "required",
          "derived"}
OPT_KEYS = {"value", "label", "description", "when"}
HEADER_MAX, OPTIONS_MIN, OPTIONS_MAX, WAVE_MAX, SHOWN_MAX, VALUE_MAX = 12, 2, 4, 4, 120, 500
RECOMMENDED = re.compile(r"\s*\((?:recommended|recomendado)\)\s*$", re.I)


class Refused(ValueError):
    """A deterministic refusal: the state is left exactly as it was."""


class NoStore(RuntimeError):
    """No .shortcuts/.virtual here, or no such session: nothing to read or write."""


# ---------- schema ---------------------------------------------------------------------------

def canon_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def schema_hash(schema):
    return hashlib.sha256(canon_json(schema).encode("utf-8")).hexdigest()


def cond_problems(cond, where):
    if not isinstance(cond, dict):
        return [f"{where}: a condition is an object"]
    for op in ("all", "any"):
        if op in cond:
            if set(cond) != {op} or not isinstance(cond[op], list) or not cond[op]:
                return [f"{where}: '{op}' takes a non-empty list and nothing beside it"]
            return [p for i, c in enumerate(cond[op]) for p in cond_problems(c, f"{where}.{op}[{i}]")]
    ops = [k for k in cond if k != "param"]
    if set(cond) - {"param", *OPS} or len(ops) != 1 or not SLOT.match(str(cond.get("param", ""))):
        return [f"{where}: write {{'param': <slot>, <one of {', '.join(OPS)}>: ...}} or all/any"]
    op, arg = ops[0], cond[ops[0]]
    if op in ("equals", "not_equals") and not isinstance(arg, str):
        return [f"{where}: '{op}' compares with a string"]
    if op in ("in", "not_in") and not (isinstance(arg, list) and arg and all(isinstance(x, str) for x in arg)):
        return [f"{where}: '{op}' takes a non-empty list of strings"]
    if op == "exists" and not isinstance(arg, bool):
        return [f"{where}: 'exists' takes true or false"]
    return []


def cond_params(cond):
    if not isinstance(cond, dict):
        return set()
    if "all" in cond or "any" in cond:
        return {p for c in cond.get("all", cond.get("any", [])) for p in cond_params(c)}
    return {cond["param"]} if "param" in cond else set()


def cond_literals(cond):
    """(slot, value) pairs a condition requires a slot to be able to hold."""
    if not isinstance(cond, dict):
        return []
    if "all" in cond or "any" in cond:
        return [x for c in cond.get("all", cond.get("any", [])) for x in cond_literals(c)]
    for op in ("equals", "in"):
        if op in cond:
            vals = cond[op] if isinstance(cond[op], list) else [cond[op]]
            return [(cond["param"], v) for v in vals]
    return []


def holes(prompt):
    return [h for h in HOLE.findall(prompt or "")]


def deps(q):
    """Every slot a question reads: declared, interpolated, or named by its conditions."""
    out = set(q.get("depends_on") or []) | set(holes(q.get("prompt"))) | cond_params(q.get("when"))
    for o in q.get("options") or []:
        out |= cond_params(o.get("when"))
    return out


def problems(schema):
    """Every reason the schema cannot be activated, one line each; [] when it holds."""
    if not isinstance(schema, dict):
        return ["the schema is a JSON object"]
    out = [f"unknown top-level key '{k}'" for k in sorted(set(schema) - TOP_KEYS)]
    if not SCHEMA_ID.match(str(schema.get("schema", ""))):
        out.append("schema: a lowercase id (letters, digits, hyphens)")
    if not isinstance(schema.get("version"), int) or schema.get("version", 0) < 1:
        out.append("version: an integer from 1")
    inputs = schema.get("inputs") or {}
    if not isinstance(inputs, dict) or not all(SLOT.match(k) and isinstance(v, str) for k, v in inputs.items()):
        out.append("inputs: {slot: why} for slots no question owns, filled only by a derived source")
        inputs = {}
    qs = schema.get("questions")
    if not isinstance(qs, list) or not qs:
        return out + ["questions: a non-empty list"]
    ids, slots, headers = set(), {}, set()
    for i, q in enumerate(qs):
        where = f"questions[{i}]"
        if not isinstance(q, dict):
            out.append(f"{where}: a question is an object")
            continue
        where = str(q.get("id") or where)
        out += [f"{where}: unknown key '{k}'" for k in sorted(set(q) - Q_KEYS)]
        if not QID.match(str(q.get("id", ""))):
            out.append(f"{where}: id must match {QID.pattern}")
        elif q["id"] in ids:
            out.append(f"{where}: duplicate question id")
        ids.add(q.get("id"))
        slot = q.get("slot")
        if not isinstance(slot, str) or not SLOT.match(slot):
            out.append(f"{where}: slot must match {SLOT.pattern}")
        elif slot in slots or slot in inputs:
            out.append(f"{where}: slot '{slot}' already has an owner")
        else:
            slots[slot] = q
        h = q.get("header")
        if not isinstance(h, str) or not h.strip() or len(h) > HEADER_MAX:
            out.append(f"{where}: header is 1-{HEADER_MAX} characters (the pop-up's chip)")
        elif h.strip().lower() in headers:
            out.append(f"{where}: duplicate header '{h}'")
        else:
            headers.add(h.strip().lower())
        if not isinstance(q.get("prompt"), str) or not q["prompt"].strip():
            out.append(f"{where}: prompt is required")
        else:
            out += [f"{where}: malformed placeholder '{{{x}}}'" for x in holes(q["prompt"]) if not SLOT.match(x)]
        opts = q.get("options")
        if not isinstance(opts, list) or not OPTIONS_MIN <= len(opts) <= OPTIONS_MAX:
            out.append(f"{where}: {OPTIONS_MIN}-{OPTIONS_MAX} options (the pop-up's limit)")
            opts = opts if isinstance(opts, list) else []
        seen_v, seen_l = set(), set()
        for j, o in enumerate(opts):
            ow = f"{where}.options[{j}]"
            if not isinstance(o, dict):
                out.append(f"{ow}: an option is an object")
                continue
            out += [f"{ow}: unknown key '{k}'" for k in sorted(set(o) - OPT_KEYS)]
            for key in ("value", "label", "description"):
                if not isinstance(o.get(key), str) or not o[key].strip():
                    out.append(f"{ow}: {key} is a non-empty string")
            if o.get("value") in seen_v or str(o.get("label", "")).lower() in seen_l:
                out.append(f"{ow}: duplicate value or label")
            seen_v.add(o.get("value"))
            seen_l.add(str(o.get("label", "")).lower())
            if "when" in o:
                out += cond_problems(o["when"], f"{ow}.when")
        for key in ("other", "multi", "required", "derived"):
            if key in q and not isinstance(q[key], bool):
                out.append(f"{where}: {key} is true or false")
        if "order" in q and not isinstance(q["order"], int):
            out.append(f"{where}: order is an integer")
        dep = q.get("depends_on", [])
        if not isinstance(dep, list) or not all(isinstance(d, str) and SLOT.match(d) for d in dep):
            out.append(f"{where}: depends_on is a list of slots")
        if "when" in q:
            out += cond_problems(q["when"], f"{where}.when")
    if out:
        return out
    owned = set(slots) | set(inputs)
    for q in qs:
        for d in sorted(deps(q)):
            if d == q["slot"]:
                out.append(f"{q['id']}: depends on its own slot '{d}'")
            elif d not in owned:
                out.append(f"{q['id']}: depends on '{d}', which no question asks and no input declares (unreachable)")
        conds = [q.get("when")] + [o.get("when") for o in q["options"]]
        for slot, val in [x for c in conds for x in cond_literals(c)]:
            owner = slots.get(slot)
            if owner and not owner.get("other") and val not in {o["value"] for o in owner["options"]}:
                out.append(f"{q['id']}: needs {slot} = '{val}', which {owner['id']} can never answer")
    graph = {q["slot"]: sorted(deps(q) & set(slots)) for q in qs}
    state = {}

    def visit(s, path):
        state[s] = 1
        for d in graph.get(s, []):
            if state.get(d) == 1:
                out.append("cycle: " + " -> ".join(path + [s, d]))
            elif not state.get(d):
                visit(d, path + [s])
        state[s] = 2

    for s in sorted(graph):
        if not state.get(s):
            visit(s, [])
    return out


def load_file(path):
    try:
        schema = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise Refused(f"the schema does not load: {e}")
    bad = problems(schema)
    if bad:
        raise Refused("the schema is refused: " + " · ".join(bad[:8]))
    return schema


# ---------- conditions, status, rendering ----------------------------------------------------

def holds(cond, values):
    """True / False, or None while a parameter it compares is unresolved. Never evaluates code."""
    if cond is None:
        return True
    if "all" in cond:
        res = [holds(c, values) for c in cond["all"]]
        return False if False in res else (None if None in res else True)
    if "any" in cond:
        res = [holds(c, values) for c in cond["any"]]
        return True if True in res else (None if None in res else False)
    p = cond["param"]
    if "exists" in cond:
        return (p in values) == cond["exists"]
    if p not in values:
        return None
    v = values[p]
    have = set(v) if isinstance(v, list) else {v}
    if "equals" in cond:
        return cond["equals"] in have
    if "not_equals" in cond:
        return cond["not_equals"] not in have
    if "in" in cond:
        return bool(have & set(cond["in"]))
    return not have & set(cond["not_in"])


def fingerprint(q, params):
    rows = [[s, params[s]["value"], params[s]["revision"]] if s in params and params[s]["status"] in RESOLVED
            else [s, None, 0] for s in sorted(deps(q))]
    return hashlib.sha256(canon_json(rows).encode("utf-8")).hexdigest()[:16]


def resolved_values(params):
    return {s: p["value"] for s, p in params.items() if p["status"] in RESOLVED}


def question_state(q, params, presented, reopened=None):
    """(status, detail, visible options). Status: blocked, skipped, eligible, presented, answered, reopened,
    invalidated. `reopened` is an answered question the Regent asked to change: askable again, its value kept."""
    values = resolved_values(params)
    missing = sorted(s for s in set(q.get("depends_on") or []) | set(holes(q["prompt"])) if s not in values)
    if missing:
        return "blocked", {"waits_on": missing}, []
    w = holds(q.get("when"), values)
    if w is None:
        return "blocked", {"waits_on": sorted(cond_params(q["when"]) - set(values))}, []
    if w is False:
        return "skipped", {"because": "its condition does not hold"}, []
    shown = []
    for o in q["options"]:
        h = holds(o.get("when"), values)
        if h is None:
            return "blocked", {"waits_on": sorted(cond_params(o["when"]) - set(values))}, []
        if h:
            shown.append(o)
    if len(shown) < OPTIONS_MIN:
        return "blocked", {"because": f"fewer than {OPTIONS_MIN} options hold under the current values"}, shown
    fp = fingerprint(q, params)
    p = params.get(q["slot"])
    if p and p["status"] in RESOLVED:
        if p["fingerprint"] == fp:
            if (reopened or {}).get(q["id"]) == fp:
                return "reopened", {"value": p["value"], "revision": p["revision"]}, shown
            return "answered", {"value": p["value"], "revision": p["revision"]}, shown
        return "invalidated", {"because": "an upstream value changed since it was answered", "was": p["value"]}, shown
    if p and p["status"] == "invalidated":
        return "invalidated", {"because": "an upstream value changed", "was": p["value"]}, shown
    if presented.get(q["id"]) == fp:
        return "presented", {}, shown
    return "eligible", {}, shown


def label_of(schema, slot, value):
    q = next((x for x in schema["questions"] if x["slot"] == slot), None)
    labels = {o["value"]: o["label"] for o in (q or {}).get("options", [])}
    vals = value if isinstance(value, list) else [value]
    return ", ".join(labels.get(v, str(v)) for v in vals)


def spoken(text):
    """Wording as the pop-up compares it: a run of spaces or a line break is one space."""
    return " ".join(str(text or "").split())


def shown_text(text):
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", str(text))
    text = " ".join(text.split())
    return text if len(text) <= SHOWN_MAX else text[:SHOWN_MAX - 1] + "…"


def render(schema, q, params):
    """The prompt with each {slot} replaced by the stored canonical value's label: plain text, single pass."""
    values = resolved_values(params)

    def put(m):
        if m.group(1) not in values:
            raise Refused(f"{q['id']}: {{{m.group(1)}}} has no established value")
        return shown_text(label_of(schema, m.group(1), values[m.group(1)]))

    return HOLE.sub(put, q["prompt"])


def ordered(schema):
    return sorted(schema["questions"], key=lambda q: (q.get("order", 0), q["id"]))


# ---------- the store ------------------------------------------------------------------------

class Store:
    """One connection, transactions explicit: every state transition is all or nothing."""

    def __init__(self, repo):
        vdir = wire.virtual_dir(repo)
        if vdir is None:
            raise NoStore("no .shortcuts/.virtual under a guidelines root here: no state can be kept")
        self.con = idx.connect(vdir, create=True)
        self.con.isolation_level = None
        self.con.executescript(SQL)

    def close(self):
        self.con.close()

    def tx(self):
        store = self

        class Tx:
            def __enter__(self):
                store.con.execute("BEGIN IMMEDIATE")
                return store.con

            def __exit__(self, kind, value, tb):
                store.con.execute("COMMIT" if kind is None else "ROLLBACK")
                return False

        return Tx()

    def event(self, sid, name, entity=None, payload=None):
        self.con.execute("INSERT INTO elicit_events(session_id, event, entity, payload, at) VALUES(?,?,?,?,?)",
                         (sid, name, entity, canon_json(payload) if payload is not None else None, wire.now()))

    def schema_of(self, h):
        row = self.con.execute("SELECT definition FROM elicit_schemas WHERE hash=? AND status='active'", (h,)).fetchone()
        if row is None:
            raise NoStore(f"the session's schema {h[:12]} is not in the store")
        schema = json.loads(row["definition"])
        if schema_hash(schema) != h or problems(schema):
            raise Refused(f"the stored schema {h[:12]} no longer matches its hash or its rules: the state is not used")
        return schema

    def session(self, sid=None, open_only=True):
        if sid is not None and not SESSION.match(sid):
            raise Refused(f"'{sid}' is not a session id (EL-####)")
        sql = "SELECT * FROM elicit_sessions" + (" WHERE session_id=?" if sid else
                                                  " WHERE status='open' ORDER BY updated_at DESC, session_id DESC")
        row = self.con.execute(sql, (sid,) if sid else ()).fetchone()
        if row is None:
            raise NoStore(f"no {'such' if sid else 'open'} elicitation session")
        if open_only and row["status"] != "open":
            raise Refused(f"{row['session_id']} is {row['status']}")
        return dict(row), self.schema_of(row["schema_hash"])

    def params(self, sid):
        out = {}
        for r in self.con.execute("SELECT * FROM elicit_params WHERE session_id=?", (sid,)):
            out[r["slot"]] = {"value": json.loads(r["value"]), "status": r["status"], "revision": r["revision"],
                              "provenance": json.loads(r["provenance"]), "fingerprint": r["fingerprint"]}
        return out

    def presented(self, sid):
        return {r["question_id"]: r["fingerprint"] for r in
                self.con.execute("SELECT question_id, fingerprint FROM elicit_questions WHERE session_id=? "
                                 "AND presented_at IS NOT NULL", (sid,))}

    def reopened(self, sid):
        return {r["question_id"]: r["reopened"] for r in
                self.con.execute("SELECT question_id, reopened FROM elicit_questions WHERE session_id=? "
                                 "AND reopened IS NOT NULL", (sid,))}

    def open_sessions(self):
        rows = self.con.execute("SELECT * FROM elicit_sessions WHERE status='open'").fetchall()
        return [(dict(r), self.schema_of(r["schema_hash"])) for r in rows]

    def last_presented(self, sid, qid):
        """The event id of the session's latest rendering of the question (`next`); 0 when it never rendered it."""
        row = self.con.execute("SELECT MAX(event_id) FROM elicit_events WHERE session_id=? AND "
                               "event='question_presented' AND entity=?", (sid, qid)).fetchone()
        return row[0] or 0


# ---------- operations -----------------------------------------------------------------------

def start(store, schema, task):
    if not TASK.match(task or ""):
        raise Refused(f"task '{task}' must match {TASK.pattern}")
    bad = problems(schema)
    if bad:
        with store.tx():
            store.event(None, "validation_failed", schema.get("schema") if isinstance(schema, dict) else None,
                        {"errors": bad[:20]})
        raise Refused("the schema is refused: " + " · ".join(bad[:8]))
    h, now = schema_hash(schema), wire.now()
    with store.tx() as con:
        con.execute("INSERT OR IGNORE INTO elicit_schemas VALUES(?,?,?,?,?,?)",
                    (h, "active", schema["schema"], schema["version"], canon_json(schema), now))
        row = con.execute("SELECT * FROM elicit_sessions WHERE status='open' AND schema_id=? AND task_id=?",
                          (schema["schema"], task)).fetchone()
        if row and row["schema_hash"] != h:
            raise Refused(f"{row['session_id']} is open on another version of '{schema['schema']}': reset it first "
                          "(a schema is never migrated under an open session)")
        if row:
            store.event(row["session_id"], "session_resumed", task)
            return {"success": True, "event": "resumed", "session_id": row["session_id"], "task_id": task}
        n = con.execute("SELECT COUNT(*) FROM elicit_sessions").fetchone()[0] + 1
        sid = f"EL-{n:04d}"
        con.execute("INSERT INTO elicit_sessions VALUES(?,?,?,?,?,?,?)",
                    (sid, task, schema["schema"], h, "open", now, now))
        store.event(sid, "session_started", task, {"schema": schema["schema"], "version": schema["version"], "hash": h})
    return {"success": True, "event": "started", "session_id": sid, "task_id": task}


def snapshot(store, sid=None, open_only=True):
    sess, schema = store.session(sid, open_only)
    params, presented = store.params(sess["session_id"]), store.presented(sess["session_id"])
    reopened = store.reopened(sess["session_id"])
    states = collections.OrderedDict()
    for q in ordered(schema):
        st, detail, shown = question_state(q, params, presented, reopened)
        states[q["id"]] = {"slot": q["slot"], "status": st, "detail": detail, "options": [o["value"] for o in shown]}
    return sess, schema, params, presented, states


def status(store, sid=None):
    sess, schema, params, _, states = snapshot(store, sid, open_only=False)
    counts = collections.Counter(r["event"] for r in store.con.execute(
        "SELECT event FROM elicit_events WHERE session_id=?", (sess["session_id"],)))
    required = [q for q in schema["questions"] if q.get("required", True)]
    complete = all(states[q["id"]]["status"] in ("answered", "skipped") for q in required)
    return {"success": True, "event": "status", "session_id": sess["session_id"], "task_id": sess["task_id"],
            "schema": schema["schema"], "version": schema["version"], "session_status": sess["status"],
            "complete": complete,
            "parameters": {s: {"value": p["value"], "status": p["status"], "revision": p["revision"],
                               "source": p["provenance"].get("source")} for s, p in sorted(params.items())},
            "questions": states,
            "unresolved_dependencies": {k: v["detail"]["waits_on"] for k, v in states.items()
                                        if v["status"] == "blocked" and "waits_on" in v["detail"]},
            "invalidated_questions": [k for k, v in states.items() if v["status"] == "invalidated"],
            "metrics": {k: counts[k] for k in ("question_presented", "answer_accepted", "answer_rejected",
                                               "answer_unchanged", "parameter_invalidated", "repeat_denied")}}


def ask_item(schema, q, params, shown):
    return {"question": render(schema, q, params), "header": q["header"],
            "options": [{"label": o["label"], "description": o["description"]} for o in shown],
            "multiSelect": bool(q.get("multi"))}


def next_questions(store, sid=None, wave=1):
    """The next eligible questions, rendered from canonical state and marked presented; ready for AskUserQuestion."""
    wave = max(1, min(int(wave), WAVE_MAX))
    with store.tx():
        sess, schema, params, presented, states = snapshot(store, sid)
        picked = [q for q in ordered(schema) if states[q["id"]]["status"] in ASKABLE][:wave]
        items, now = [], wire.now()
        for q in picked:
            shown = [o for o in q["options"] if o["value"] in states[q["id"]]["options"]]
            items.append(dict(ask_item(schema, q, params, shown), id=q["id"], slot=q["slot"]))
            store.con.execute("INSERT INTO elicit_questions(session_id, question_id, presented_at, fingerprint) "
                              "VALUES(?,?,?,?) ON CONFLICT(session_id, question_id) DO UPDATE SET "
                              "presented_at=excluded.presented_at, fingerprint=excluded.fingerprint",
                              (sess["session_id"], q["id"], now, fingerprint(q, params)))
            store.event(sess["session_id"], "question_presented", q["id"], {"fingerprint": fingerprint(q, params)})
    required = [q for q in schema["questions"] if q.get("required", True)]
    complete = all(states[q["id"]]["status"] in ("answered", "skipped") for q in required)
    deps_used = sorted({d for q in picked for d in deps(q)})
    return {"success": True, "event": "next", "session_id": sess["session_id"], "task_id": sess["task_id"],
            "complete": complete and not items,
            "next_question": items[0] if items else None,
            "ask": {"questions": [{k: v for k, v in i.items() if k not in ("id", "slot")} for i in items]} if items else None,
            "dependency_values": {d: params[d]["value"] for d in deps_used if d in params},
            "provenance": {d: {"revision": params[d]["revision"], "source": params[d]["provenance"].get("source"),
                               "at": params[d]["provenance"].get("at")} for d in deps_used if d in params},
            "unresolved_dependencies": {k: v["detail"]["waits_on"] for k, v in states.items()
                                        if v["status"] == "blocked" and "waits_on" in v["detail"]}}


def normalise(q, raw, shown):
    """The canonical value of an answer: an option's value, a sorted list for multi, typed text only if allowed."""
    if isinstance(raw, list):
        raw = ",".join(str(x) for x in raw)
    text = " ".join(str(raw).split())
    if not text or len(text) > VALUE_MAX:
        raise Refused(f"{q['id']}: an answer is 1-{VALUE_MAX} characters")
    by = {}
    for o in shown:
        by[o["value"].casefold()] = o["value"]
        by[RECOMMENDED.sub("", o["label"]).casefold()] = o["value"]

    def one(t):
        return by.get(RECOMMENDED.sub("", t).strip().casefold())

    if not q.get("multi"):
        v = one(text)
        if v is not None:
            return v
        if q.get("other"):
            return text
        raise Refused(f"{q['id']}: '{text}' is not one of " + ", ".join(o["label"] for o in shown))
    picked, rest = [], []
    for part in [p.strip() for p in text.split(",") if p.strip()]:
        v = one(part)
        (picked if v is not None else rest).append(v if v is not None else part)
    if rest and not q.get("other"):
        raise Refused(f"{q['id']}: '{', '.join(rest)}' is not among " + ", ".join(o["label"] for o in shown))
    out = sorted(set(picked)) + ([" ".join(", ".join(rest).split())] if rest else [])
    if not out:
        raise Refused(f"{q['id']}: no option chosen")
    return out


def dependents(schema, slot):
    """Every slot whose question reads `slot`, directly or through another dependent."""
    readers = collections.defaultdict(set)
    for q in schema["questions"]:
        for d in deps(q):
            readers[d].add(q["slot"])
    seen, todo = set(), [slot]
    while todo:
        for s in sorted(readers.get(todo.pop(), ())):
            if s not in seen:
                seen.add(s)
                todo.append(s)
    return sorted(seen)


def accept(store, sid, key, raw, source, note=None):
    """Validate and accept one answer; invalidate only the transitive dependents of a changed value; one transaction."""
    if source not in SOURCES:
        raise Refused(f"source '{source}' is not one of {', '.join(SOURCES)}")
    with store.tx():
        sess, schema, params, presented, states = snapshot(store, sid)
        sid = sess["session_id"]
        q = next((x for x in schema["questions"] if key in (x["id"], x["slot"])), None)
        try:
            if q is None:
                raise Refused(f"'{key}' is neither a question nor a slot of {schema['schema']}")
            st = states[q["id"]]
            if st["status"] in ("blocked", "skipped"):
                raise Refused(f"{q['id']} is {st['status']}: " + canon_json(st["detail"]))
            shown = [o for o in q["options"] if o["value"] in st["options"]]
            value = normalise(q, raw, shown)
            target = SOURCES[source]
            if source == "derived" and not q.get("derived"):
                raise Refused(f"{q['id']}: the schema does not let a script derive '{q['slot']}'")
        except Refused as e:
            store.event(sid, "answer_rejected", key, {"source": source, "why": str(e)})
            raise
        cur = params.get(q["slot"])
        fp = fingerprint(q, params)
        result = {"success": True, "session_id": sid, "task_id": sess["task_id"], "accepted_parameter": q["slot"],
                  "canonical_value": value, "invalidated_parameters": [], "invalidated_questions": []}
        if source == "agent" and cur and cur["status"] in RESOLVED:
            store.event(sid, "parameter_proposed", q["slot"], {"value": value, "kept": cur["value"], "note": note})
            return dict(result, event="proposal_recorded", canonical_value=cur["value"], current_revision=cur["revision"],
                        status=cur["status"], next_question=None)
        prov = {"source": source, "question": q["id"], "task": sess["task_id"], "session": sid, "at": wire.now(),
                "validation": "ok", "fingerprint": fp}
        if note:
            prov["note"] = shown_text(note)
        if cur and cur["value"] == value:
            keep = cur["status"] in RESOLVED and cur["fingerprint"] == fp and RANK[cur["status"]] >= RANK[target]
            if keep:
                store.con.execute("UPDATE elicit_questions SET reopened=NULL WHERE session_id=? AND question_id=?",
                                  (sid, q["id"]))
                store.event(sid, "answer_unchanged", q["slot"], {"value": value, "revision": cur["revision"]})
                return dict(result, event="unchanged", current_revision=cur["revision"], status=cur["status"],
                            next_question=None)
            revision = cur["revision"]          # same value: dependents stay valid
            changed = False
        else:
            revision = (cur["revision"] if cur else 0) + 1
            changed = True
        prov["revision"] = revision
        store.con.execute("INSERT INTO elicit_params VALUES(?,?,?,?,?,?,?) ON CONFLICT(session_id, slot) DO UPDATE SET "
                          "value=excluded.value, status=excluded.status, revision=excluded.revision, "
                          "provenance=excluded.provenance, fingerprint=excluded.fingerprint",
                          (sid, q["slot"], canon_json(value), target, revision, canon_json(prov), fp))
        store.con.execute("INSERT INTO elicit_questions(session_id, question_id, answered_at, fingerprint) VALUES(?,?,?,?) "
                          "ON CONFLICT(session_id, question_id) DO UPDATE SET answered_at=excluded.answered_at, "
                          "fingerprint=excluded.fingerprint, reopened=NULL", (sid, q["id"], prov["at"], fp))
        store.event(sid, {"confirmed": "answer_accepted", "derived": "parameter_derived",
                          "proposed": "parameter_proposed"}[target], q["slot"],
                    {"value": value, "previous": cur["value"] if cur else None, "revision": revision, "source": source})
        if changed and cur is not None and cur["value"] != value and target in RESOLVED:
            for s in dependents(schema, q["slot"]):
                p = params.get(s)
                if p and p["status"] in ("confirmed", "derived", "proposed"):
                    why = {"was": p["value"], "status_was": p["status"], "because": f"{q['slot']} changed to "
                           f"{canon_json(value)} at revision {revision}", "origin": q["slot"], "origin_revision": revision}
                    p["provenance"].setdefault("history", []).append(dict(why, at=prov["at"]))
                    store.con.execute("UPDATE elicit_params SET status='invalidated', provenance=? WHERE session_id=? "
                                      "AND slot=?", (canon_json(p["provenance"]), sid, s))
                    store.event(sid, "parameter_invalidated", s, why)
                    result["invalidated_parameters"].append(s)
                    result["invalidated_questions"] += [x["id"] for x in schema["questions"] if x["slot"] == s]
        store.con.execute("UPDATE elicit_sessions SET updated_at=? WHERE session_id=?", (prov["at"], sid))
    after = status(store, sid)
    nxt = next((k for k, v in after["questions"].items() if v["status"] in ASKABLE), None)
    return dict(result, event="accepted" if target == "confirmed" else target, current_revision=revision,
                status=target, next_question=nxt, complete=after["complete"])


def record_answer(store, sid, question_id, raw):
    """The Regent's pop-up answer, as the hook read it: the one way a value becomes confirmed."""
    return accept(store, sid, question_id, raw, "regent")


def propose(store, schema, onto=None):
    """Validate a schema extension and keep it as proposed; it never activates itself."""
    bad = problems(schema)
    added = []
    if onto and not bad:
        _, active = store.session(onto, open_only=False)
        old = {q["id"]: q for q in active["questions"]}
        new = {q["id"]: q for q in schema["questions"]}
        bad += [f"{k}: an extension keeps every active question as it is" for k in old if new.get(k) != old[k]]
        added = sorted(set(new) - set(old))
    with store.tx() as con:
        if not bad:
            con.execute("INSERT OR IGNORE INTO elicit_schemas VALUES(?,?,?,?,?,?)",
                        (schema_hash(schema), "proposed", schema["schema"], schema["version"], canon_json(schema),
                         wire.now()))
        store.event(onto, "schema_proposed" if not bad else "validation_failed",
                    schema.get("schema") if isinstance(schema, dict) else None, {"errors": bad[:20], "added": added})
    if bad:
        raise Refused("the proposal is refused: " + " · ".join(bad[:8]))
    return {"success": True, "event": "proposed", "hash": schema_hash(schema), "added_questions": added,
            "active": False, "activation": "the Regent's: a schema becomes active only as a file the Regent ratified"}


def reopen(store, sid, qid, because):
    """The Regent asked to change an answered question: make it askable once more. The value stays until the
    Regent's new answer arrives through the pop-up; the reason is recorded in the Regent's words."""
    because = shown_text(because or "")
    if not because:
        raise Refused("reopen needs --because: the Regent's words asking for the change")
    with store.tx():
        sess, schema, params, _, states = snapshot(store, sid)
        q = next((x for x in schema["questions"] if qid in (x["id"], x["slot"])), None)
        if q is None or states[q["id"]]["status"] != "answered":
            raise Refused(f"only an answered question is reopened ({qid}: "
                          f"{states[q['id']]['status'] if q else 'unknown'})")
        fp = fingerprint(q, params)
        store.con.execute("UPDATE elicit_questions SET reopened=? WHERE session_id=? AND question_id=?",
                          (fp, sess["session_id"], q["id"]))
        store.event(sess["session_id"], "question_reopened", q["id"], {"because": because,
                                                                       "value": params[q["slot"]]["value"]})
    return {"success": True, "event": "reopened", "session_id": sess["session_id"], "question": q["id"],
            "kept_value": params[q["slot"]]["value"]}


def reset(store, sid):
    with store.tx() as con:
        sess, _ = store.session(sid)
        con.execute("UPDATE elicit_sessions SET status='closed', updated_at=? WHERE session_id=?",
                    (wire.now(), sess["session_id"]))
        store.event(sess["session_id"], "session_reset", sess["task_id"])
    return {"success": True, "event": "reset", "session_id": sess["session_id"], "task_id": sess["task_id"]}


def label_key(label):
    return RECOMMENDED.sub("", str(label)).strip().casefold()


def locate_question(store, header, text=None, labels=None):
    """(session, schema, question) an AskUserQuestion entry stands for; None when it stands for no open session's
    question. It stands for one when it carries the question's header and either the wording the engine renders for
    it now (spaces aside) or only labels of its options: an entry sharing the header alone is another question.
    Several sessions: the one whose rendering it carries, then the one that rendered it last, then the latest."""
    want, words = str(header or "").strip().lower(), spoken(text)
    picked = {label_key(x) for x in labels or []}
    found = []
    for sess, schema in store.open_sessions():
        q = next((x for x in schema["questions"] if x["header"].strip().lower() == want), None)
        if q is None:
            continue
        try:
            worded = text is not None and spoken(render(schema, q, store.params(sess["session_id"]))) == words
        except Refused:
            worded = False
        optioned = bool(picked) and picked <= {label_key(o["label"]) for o in q["options"]}
        if worded or optioned:
            rank = (worded, store.last_presented(sess["session_id"], q["id"]), sess["updated_at"], sess["session_id"])
            found.append((rank, sess, schema, q))
    if not found:
        return None
    _, sess, schema, q = max(found, key=lambda f: f[0])
    return sess, schema, q


# ---------- cli -----------------------------------------------------------------------------

def cli(argv):
    ap = argparse.ArgumentParser(prog="elicit.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check").add_argument("schema")
    s = sub.add_parser("start")
    s.add_argument("schema")
    s.add_argument("--task", required=True)
    for name in ("status", "reset"):
        sub.add_parser(name).add_argument("--session")
    n = sub.add_parser("next")
    n.add_argument("--session")
    n.add_argument("--wave", type=int, default=1)
    u = sub.add_parser("submit")
    u.add_argument("--session", required=True)
    u.add_argument("--slot", required=True)
    u.add_argument("--value", required=True)
    u.add_argument("--source", choices=CLI_SOURCES, required=True)
    u.add_argument("--note")
    p = sub.add_parser("propose")
    p.add_argument("schema")
    p.add_argument("--onto")
    r = sub.add_parser("reopen")
    r.add_argument("--session", required=True)
    r.add_argument("--question", required=True)
    r.add_argument("--because", required=True)
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    if a.cmd == "check":
        try:
            schema = json.loads(Path(a.schema).read_text(encoding="utf-8-sig"))
            bad = problems(schema)
        except (OSError, ValueError) as e:
            bad = [f"the schema does not load: {e}"]
        print(canon_json({"success": not bad, "event": "check", "validation_errors": bad}))
        return 1 if bad else 0
    repo = wire.repo_root(Path(a.repo).resolve() if a.repo else Path.cwd())
    store = None
    try:
        store = Store(repo)
        if a.cmd == "start":
            out = start(store, load_file(a.schema), a.task)
        elif a.cmd == "status":
            out = status(store, a.session)
        elif a.cmd == "next":
            out = next_questions(store, a.session, a.wave)
        elif a.cmd == "submit":
            out = accept(store, a.session, a.slot, a.value, a.source, a.note)
        elif a.cmd == "propose":
            out = propose(store, json.loads(Path(a.schema).read_text(encoding="utf-8-sig")), a.onto)
        elif a.cmd == "reopen":
            out = reopen(store, a.session, a.question, a.because)
        else:
            out = reset(store, a.session)
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except Refused as e:
        print(canon_json({"success": False, "event": a.cmd, "validation_errors": [str(e)]}))
        return 1
    except (NoStore, OSError, ValueError, sqlite3.Error) as e:
        print(f"elicit.py: {e}", file=sys.stderr)
        print(canon_json({"success": False, "event": a.cmd, "validation_errors": [str(e)]}))
        return 2
    finally:
        if store:
            store.close()


# ---------- selftest ------------------------------------------------------------------------

EXAMPLE = HERE.parent / "library" / "examples" / "elicitation-rule-selection.json"


def selftest():
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        root = wire.build_fixture(Path(tmp) / "proj")
        schema = load_file(EXAMPLE)
        store = Store(root)
        sid = start(store, schema, "M01.S01.T01")["session_id"]
        first = next_questions(store, sid)
        cases.append((first["ask"]["questions"][0]["question"] == "Which rule should govern this case?"
                      and status(store, sid)["questions"]["Q_BASE"]["status"] == "blocked",
                      "4. a question waiting on an unresolved parameter is blocked, never presented"))
        try:
            accept(store, sid, "Q_BASE", "X1", "regent")
            cases.append((False, "4b. an answer to a blocked question is refused"))
        except Refused:
            cases.append((True, "4b. an answer to a blocked question is refused"))
        try:
            accept(store, sid, "Q_RULE", "C", "regent")
            cases.append((False, "5. an invalid option is refused"))
        except Refused:
            cases.append((True, "5. an invalid option is refused"))
        r = record_answer(store, sid, "Q_RULE", "B")
        store2 = Store(root)
        p = store2.params(sid)["rule"]
        cases.append((r["canonical_value"] == "B" and p["status"] == "confirmed" and p["revision"] == 1
                      and p["provenance"]["source"] == "regent" and p["provenance"]["task"] == "M01.S01.T01",
                      "1. a parameter is accepted and persisted with its provenance"))
        st = status(store2, sid)
        cases.append((st["questions"]["Q_BASE"]["status"] == "eligible" and st["questions"]["Q_RELEASE"]["status"] == "eligible",
                      "2. dependent questions become eligible once the prerequisite is confirmed"))
        w = next_questions(store2, sid, wave=4)
        texts = [q["question"] for q in w["ask"]["questions"]]
        cases.append((texts[:2] == ["For the selected rule (B), which option should be used as the base?",
                                    "Regarding the selected rule (B), which options should be allowed?"]
                      and w["dependency_values"] == {"rule": "B"},
                      "3. each dependent question is rendered from the stored value"))
        cases.append(([o["label"] for o in w["ask"]["questions"][1]["options"]] == ["X2", "Y2", "Z2"],
                      "options follow their conditions: Z2 is offered under rule B"))
        record_answer(store2, sid, "Q_BASE", "X1")
        record_answer(store2, sid, "Q_RELEASE", "Z2, X2")
        record_answer(store2, sid, "Q_NOTE", "Someone from finance")
        st = status(store2, sid)
        cases.append((st["parameters"]["release_option"]["value"] == ["X2", "Z2"]
                      and st["parameters"]["owner"]["value"] == "Someone from finance" and st["complete"],
                      "multi answers are sorted option values; a typed answer only where the schema allows it"))
        same = record_answer(store2, sid, "Q_RULE", "B")
        st = status(store2, sid)
        cases.append((same["event"] == "unchanged" and st["parameters"]["base_option"]["status"] == "confirmed",
                      "6. re-submitting an identical value invalidates nothing"))
        try:
            reopen(store2, sid, "Q_RULE", "")
            cases.append((False, "reopen needs the Regent's reason"))
        except Refused:
            cases.append((True, "reopen needs the Regent's reason"))
        ro = reopen(store2, sid, "Q_RULE", "the Regent: switch to rule A")
        st = status(store2, sid)
        cases.append((ro["kept_value"] == "B" and st["questions"]["Q_RULE"]["status"] == "reopened"
                      and st["parameters"]["rule"]["value"] == "B" and st["parameters"]["base_option"]["status"] == "confirmed",
                      "reopen makes an answered question askable again and changes no value"))
        ch = record_answer(store2, sid, "Q_RULE", "A")
        st = status(store2, sid)
        cases.append((sorted(ch["invalidated_parameters"]) == ["base_option", "release_option"]
                      and st["parameters"]["rule"]["revision"] == 2,
                      "7. changing the upstream value invalidates all and only its transitive dependents"))
        cases.append((st["parameters"]["owner"]["status"] == "confirmed" and st["questions"]["Q_NOTE"]["status"] == "answered",
                      "8. an independent answer survives the upstream change"))
        hist = store2.params(sid)["base_option"]["provenance"]["history"][-1]
        cases.append((hist["was"] == "X1" and hist["origin"] == "rule" and hist["origin_revision"] == 2
                      and store2.params(sid)["base_option"]["value"] == "X1",
                      "9. an invalidated answer keeps its value and history: what, why, which upstream revision"))
        again = next_questions(store2, sid, wave=4)
        texts = [q["question"] for q in again["ask"]["questions"]]
        cases.append((texts == ["For the selected rule (A), which option should be used as the base?",
                                "Regarding the selected rule (A), which options should be allowed?"]
                      and [o["label"] for o in again["ask"]["questions"][1]["options"]] == ["X2", "Y2"],
                      "acceptance: after rule = A both dependents are asked again with A, Z2 no longer offered"))
        try:
            accept(store2, sid, "Q_RELEASE", "Z2", "regent")
            cases.append((False, "a value its condition no longer offers is refused"))
        except Refused:
            cases.append((True, "a value its condition no longer offers is refused"))
        bad = json.loads(json.dumps(schema))
        bad["questions"][0]["depends_on"] = ["base_option"]
        cases.append((any("cycle" in p for p in problems(bad)), "10. cyclic dependencies are refused"))
        bad = json.loads(json.dumps(schema))
        bad["questions"][1]["when"] = {"param": "rule", "matches": "A.*"}
        bad2 = json.loads(json.dumps(schema))
        bad2["questions"][1]["when"] = {"param": "rule", "equals": "C"}
        bad3 = json.loads(json.dumps(schema))
        bad3["questions"][1]["prompt"] = "For {rule.__class__}, which?"
        bad4 = json.loads(json.dumps(schema))
        bad4["questions"][1]["depends_on"] = ["nobody"]
        cases.append((problems(bad) and any("can never answer" in p for p in problems(bad2))
                      and any("malformed placeholder" in p for p in problems(bad3))
                      and any("unreachable" in p for p in problems(bad4)),
                      "11. invalid conditions, unsatisfiable values, malformed placeholders and unreachable slots are refused"))
        prop = accept(store2, sid, "Q_BASE", "Y1", "agent")
        st = status(store2, sid)
        cases.append((prop["status"] == "proposed" and st["parameters"]["base_option"]["status"] == "proposed"
                      and st["questions"]["Q_BASE"]["status"] in ASKABLE,
                      "12. an agent proposal never becomes a confirmed answer, and the question stays to ask"))
        try:
            accept(store2, sid, "Q_BASE", "Y1", "derived")
            cases.append((False, "a script cannot derive a slot the schema does not declare derivable"))
        except Refused:
            cases.append((True, "a script cannot derive a slot the schema does not declare derivable"))
        store2.close()
        store.close()
        store3 = Store(root)
        rec = status(store3, sid)
        cases.append((rec["parameters"]["rule"]["value"] == "A" and rec["questions"]["Q_BASE"]["status"] in ASKABLE
                      and rec["parameters"]["base_option"]["status"] == "proposed",
                      "13. a new process recovers the session as it was; a presentation is never an answer"))
        errors = []

        def race(value):
            s = Store(root)
            try:
                record_answer(s, sid, "Q_BASE", value)
            except Exception as e:  # noqa: BLE001 - the test collects every failure
                errors.append(e)
            finally:
                s.close()

        mark = store3.con.execute("SELECT COALESCE(MAX(event_id), 0) FROM elicit_events").fetchone()[0]
        threads = [threading.Thread(target=race, args=(v,)) for v in ("X1", "Y1", "Z1", "X1")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        events = [r["payload"] for r in store3.con.execute(
            "SELECT payload FROM elicit_events WHERE session_id=? AND entity='base_option' AND event_id > ? AND "
            "event IN ('answer_accepted','answer_unchanged')", (sid, mark))]
        final = store3.params(sid)["base_option"]
        cases.append((not errors and final["status"] == "confirmed" and len(events) == 4
                      and final["value"] in ("X1", "Y1", "Z1"), "14. concurrent submissions serialise; no state is torn"))
        before = store3.params(sid)
        original = dependents
        globals()["dependents"] = lambda *_: (_ for _ in ()).throw(RuntimeError("planted failure"))
        try:
            record_answer(store3, sid, "Q_RULE", "B")
        except RuntimeError:
            pass
        finally:
            globals()["dependents"] = original
        cases.append((store3.params(sid) == before, "a failed transition leaves the state exactly as it was"))
        other = json.loads(json.dumps(schema))
        other["version"] = 2
        try:
            start(store3, other, "M01.S01.T01")
            cases.append((False, "15. another schema version under an open session is refused, never migrated"))
        except Refused:
            cases.append((True, "15. another schema version under an open session is refused, never migrated"))
        try:
            load_file(Path(tmp) / "missing.json")
            cases.append((False, "15b. a missing schema fails explicitly"))
        except Refused:
            cases.append((True, "15b. a missing schema fails explicitly"))
        store3.con.execute("UPDATE elicit_schemas SET definition=replace(definition, 'Which rule', 'Which law')")
        try:
            status(store3, sid)
            cases.append((False, "a stored schema that no longer matches its hash is refused"))
        except Refused:
            cases.append((True, "a stored schema that no longer matches its hash is refused"))
        store3.con.execute("UPDATE elicit_schemas SET definition=replace(definition, 'Which law', 'Which rule')")
        ext = json.loads(json.dumps(schema))
        ext["questions"].append({"id": "Q_DATE", "slot": "date", "header": "Date", "prompt": "When, under rule {rule}?",
                                 "options": [{"value": "now", "label": "Now", "description": "today"},
                                             {"value": "later", "label": "Later", "description": "next cycle"}]})
        sid2 = start(Store(root), schema, "M01.S01.T02")["session_id"]
        pr = propose(store3, ext, sid2)
        cases.append((pr["added_questions"] == ["Q_DATE"] and pr["active"] is False
                      and store3.con.execute("SELECT status FROM elicit_schemas WHERE hash=?",
                                             (pr["hash"],)).fetchone()[0] == "proposed",
                      "a schema extension is validated and kept as proposed, never activated"))
        cases.append((reset(store3, sid2)["event"] == "reset" and status(store3, sid2)["session_status"] == "closed",
                      "reset closes one session and keeps its history"))
        store3.close()
        two = Store(wire.build_fixture(Path(tmp) / "two"))
        old = start(two, schema, "triage-2026-11-17")["session_id"]
        next_questions(two, old)
        record_answer(two, old, "Q_RULE", "B")
        new = start(two, schema, "triage-2026-11-18")["session_id"]
        asked = next_questions(two, new)["ask"]["questions"][0]
        hit = locate_question(two, asked["header"], asked["question"])
        cases.append((hit is not None and hit[0]["session_id"] == new,
                      "D1. two open sessions hold the same question: the one that rendered it last owns it"))
        two.close()
        spaced = json.loads(json.dumps(schema))
        spaced["questions"][1]["prompt"] = "For the selected rule ({rule}),  which option\nshould be used as the base?"
        sp = Store(wire.build_fixture(Path(tmp) / "spaced"))
        first_sid = start(sp, spaced, "M01.S01.T03")["session_id"]
        record_answer(sp, first_sid, "Q_RULE", "A")
        wording = next_questions(sp, first_sid)["ask"]["questions"][0]
        later_sid = start(sp, spaced, "M01.S01.T04")["session_id"]
        record_answer(sp, later_sid, "Q_RULE", "B")
        hit = locate_question(sp, wording["header"], wording["question"])
        cases.append((hit is not None and hit[0]["session_id"] == first_sid,
                      "D3. a prompt holding a double space or a line break is matched as the pop-up shows it"))
        sp.close()
        try:
            Store(wire.build_fixture(Path(tmp) / "bare", with_virtual=False))
            cases.append((False, "no .virtual: no state is invented"))
        except NoStore:
            cases.append((True, "no .virtual: no state is invented"))
    return wire.check(cases)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else cli(sys.argv[1:]))
