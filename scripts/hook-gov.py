#!/usr/bin/env python3
"""hook-gov.py - Kooiman's governance at the two points where a pass changes hands.

SubagentStart            one slice line for a regency role or subagent: who it answers to, its own
                         mode, and the packet header the project reads (gov.py grammar).
PostToolUse Agent|Task   reads the packet the subagent returned, routes it with gov.py
                         (G1 -> ledger, G2/G3 -> Regent; missing or under-declared -> up), appends the
                         decision to <virtual>/gov-queue.jsonl and adds one context line to the main
                         agent, so the Regent's review packet carries only what is second order or meta.
                         A role agent dispatched with a 'Stage:' line (packets.md section 1) is also checked
                         against its return shape (returns.py); each miss is counted as
                         key=return-<stage>-<field> (gov.note, never a packet) and the line says RETURN.
                         Every suba envelope in the message (one per suba the role wore) is checked against
                         its contract, logged to <virtual>/returns.jsonl (metadata, never the body), its keys
                         counted for recur, its misses counted as return-<suba>-<field>; a suba returned by a
                         role that does not own it is a miss; a ledger line that disagrees with ongoing.json is
                         named. Envelopes never raise the role's own order: routing reads the message without them.

Kind: recorder. Never blocks, never decides a tool call; an error goes to stderr (library/hooks.md §0).
Adoption gate: silent outside a project that has <guidelines>/.shortcuts/.virtual/.

Modes:  (no args) hook · --selftest · --print TEXT (route TEXT as if a subagent had returned it)
Pure standard library, Python 3.8+.
"""
import importlib.util
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

_spec = importlib.util.spec_from_file_location("gov", HERE / "gov.py")
gov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gov)
_rspec = importlib.util.spec_from_file_location("returns", HERE / "returns.py")
returns = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(returns)

AGENT_TOOLS = ("Agent", "Task")
STAGE = re.compile(r"(?m)^[ \t]*Stage:[ \t]*([a-z]+)")


def slice_line(agent_type):
    """The governance slice for one subagent, stated as facts (prompt-injection-safe), or None."""
    role = gov.role_of(agent_type)
    if not role or role == "RGN":
        return None
    is_role_agent = (agent_type or "").split(":")[-1].strip().upper() == role
    owner = "RGN" if is_role_agent else role
    mode = "co with the other manager, hier toward operators" if role in gov.MANAGERS else "self inside the declared span"
    return wire.one_line(
        f"regency governance · {agent_type} belongs to {role} and answers to {owner}",
        f"own mode: {mode}",
        f"returned packets in this project open with 'gov: order=G1|G2|G3 · mode=hier|co|self · "
        f"element=image|instrument|action · from={role} · to=<role>' and a second line 'ask: <one decision>'",
        "G1 stays in the ledger; G2 (spec version, gate, ladder, escalation) and G3 (conventions) reach the Regent",
        "DA and DV never address each other")


def returned_text(event):
    """The subagent's final text from the Agent/Task tool response, whatever its shape."""
    resp = event.get("tool_response")
    if isinstance(resp, str):
        return resp
    parts = []

    def walk(x):
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, dict):
            if x.get("type") == "text" and isinstance(x.get("text"), str):
                parts.append(x["text"])
            else:
                for k in ("content", "result", "output", "text", "message"):
                    if k in x:
                        walk(x[k])
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(resp)
    return "\n".join(p for p in parts if p.strip())


def answer_line(decision, agent):
    d = decision
    head = f"gov · {agent} · {d['order']} {d['element']} · route {d['route']}"
    if d["route"] == "ledger":
        return wire.one_line(head, "first order: kept out of the Regent's packet")
    return wire.one_line(head, f"ask: {d['ask']}" if d.get("ask") else "no ask line",
                         f"flags: {', '.join(d['flags'])}" if d["flags"] else None,
                         f"problems: {'; '.join(d['problems'])}" if d["problems"] else None)


def shape_line(event, agent, text, decision, vdir):
    """The return gate for a role packet dispatched with a Stage: line; None when there is nothing to check.
    The stage shape applies to role agents; suba envelopes are checked by envelope_line."""
    role = gov.role_of(agent)
    stage = STAGE.search(wire.tool_input(event).get("prompt") or "")
    if not stage or (agent or "").split(":")[-1].strip().upper() != role:
        return None
    try:
        found = returns.stage_findings(text, role, stage.group(1))
    except (OSError, ValueError) as e:
        return f"shape not checked ({e})"
    if found is None:
        return None
    name = f"{role.lower()}.{stage.group(1)}"
    if not found:
        return f"shape {name} holds"
    for field, _ in found:
        gov.note(vdir, f"return-{stage.group(1)}-{field}", unit=decision.get("unit"), session=event.get("session_id"))
    return f"shape {name}: {len(found)} miss(es) - " + "; ".join(m for _, m in found[:3]) + f" -> RETURN to {role}"


def ledger_note(vdir, info):
    """A ledger line that disagrees with ongoing.json, or None. Reconciliation is named, never written (virtualpath §3)."""
    state, unit = (info.get("ledger") or {}).get("state"), info.get("unit")
    if not state or not unit:
        return None
    unit_id = unit.split(" [")[0]
    try:
        items = json.loads((Path(vdir) / "ongoing.json").read_text(encoding="utf-8-sig")).get("items", [])
    except (OSError, ValueError):
        return None
    item = next((i for i in items if i.get("id") == unit_id), None)
    if item is None:
        return f"ledger has no {unit_id}"
    return None if item.get("state") == state else f"ledger says {unit_id} {item.get('state')}, the return says {state}"


def envelope_line(event, agent, text, vdir):
    """Every suba envelope in a role's message: checked, logged, keyed for recur. None when there is none."""
    try:
        results = returns.check_message(text)
    except (OSError, ValueError) as e:
        return f"envelopes not checked ({e})"
    if not results:
        return None
    role, sid = gov.role_of(agent), event.get("session_id")
    rows, parts = [], []
    for name, misses, info in results:
        if info.get("owner") and role and info["owner"] != role:
            misses = [("suba", f"{name} belongs to {info['owner']}, returned by {role}")] + misses
        for key in info.get("keys") or []:
            gov.note(vdir, key, unit=info.get("unit"), element=info.get("element") or "action", session=sid)
        for path, _ in misses:
            key = returns.field_key(name, path) if info else "return-envelope-json"
            gov.note(vdir, key, unit=info.get("unit"), session=sid)
        rows.append(returns.row(dict(info, suba=info.get("suba") or name), misses, agent, sid))
        if misses:
            parts.append(f"{name} {len(misses)} miss(es) - {misses[0][0]}: {misses[0][1]} -> RETURN to {role or info.get('owner')}")
        else:
            parts.append(f"{name} ok")
        note = ledger_note(vdir, info) if info else None
        if note:
            parts.append(note)
    returns.record(vdir, rows)
    return "subas: " + "; ".join(parts)


def respond(event):
    vdir = wire.virtual_dir(wire.repo_root(Path(event.get("cwd") or os.getcwd())))
    if not vdir:
        return None  # adoption gate
    phase = event.get("hook_event_name")
    if phase == "SubagentStart":
        line = slice_line(event.get("agent_type"))
        return wire.context("SubagentStart", line) if line else None
    if phase == "PostToolUse" and event.get("tool_name") in AGENT_TOOLS:
        agent = wire.tool_input(event).get("subagent_type") or "general-purpose"
        if gov.role_of(agent) is None:
            return None  # not a regency role: Explore, Plan, general-purpose stay ungoverned
        text = returned_text(event)
        if not text.strip():
            return None
        decision = gov.route(returns.strip_envelopes(text), sender=agent)
        gov.record(vdir, decision, agent=agent, session=event.get("session_id"))
        parts = [answer_line(decision, agent), shape_line(event, agent, text, decision, vdir),
                 envelope_line(event, agent, text, vdir)]
        return wire.context("PostToolUse", " · ".join(p for p in parts if p))
    return None


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        (root / ".git").mkdir(parents=True)
        vdir = root / ".guidelines" / ".shortcuts" / ".virtual"
        vdir.mkdir(parents=True)
        bare = Path(tmp) / "bare"
        (bare / ".git").mkdir(parents=True)

        def start(agent, cwd=root):
            return respond({"hook_event_name": "SubagentStart", "agent_type": agent, "cwd": str(cwd), "session_id": "s1"})

        def post(agent, resp, cwd=root, tool="Agent", prompt="x"):
            return respond({"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(cwd), "session_id": "s1",
                            "tool_input": {"subagent_type": agent, "prompt": prompt}, "tool_response": resp})

        def ctx(a):
            return (a or {}).get("hookSpecificOutput", {}).get("additionalContext", "")

        cases = []
        line = ctx(start("regency:suba-implementer"))
        cases.append(("belongs to DV" in line and "self inside the declared span" in line, "slice for a DV subagent"))
        line = ctx(start("qa"))
        cases.append(("answers to RGN" in line and "co with the other manager" in line, "slice for the QA role agent"))
        cases.append((start("Explore") is None, "non-regency agents get no slice"))
        cases.append((start("suba-validator", cwd=bare) is None, "adoption gate: silent without .virtual/"))
        cases.append((len(line) <= wire.MAX_LINE, f"slice fits one line ({len(line)} chars)"))

        g1 = "gov: order=G1 · mode=self · element=action · from=DV · to=QA\nask: re-run the named test"
        a = ctx(post("suba-implementer", {"content": [{"type": "text", "text": g1}]}))
        cases.append(("route ledger" in a, f"G1 packet -> ledger: {a}"))
        a = ctx(post("suba-validator", "Verdict: criterion C-04 is untestable; propose SPEC v3."))
        cases.append(("route regent" in a and "undeclared" in a, f"headerless packet -> Regent: {a}"))
        a = ctx(post("suba-validator", [{"type": "text", "text": "gov: order=G2 · mode=co · element=image · to=RGN\n"
                                                                 "ask: approve SPEC v3"}], tool="Task"))
        cases.append(("G2 image" in a and "ask: approve SPEC v3" in a and "problems" not in a,
                      "list response, Task tool, from= filled from the owner"))
        cases.append((post("general-purpose", g1) is None, "ungoverned agent is not recorded"))
        cases.append((post("suba-implementer", "") is None, "empty response is ignored"))
        cases.append((post("suba-implementer", g1, cwd=bare) is None, "adoption gate on PostToolUse"))
        q = gov.read_queue(vdir)
        cases.append((len(q) == 3 and [e["gov.route"] for e in q] == ["ledger", "regent", "regent"],
                      f"queue holds 3 decisions: {[e['gov.route'] for e in q]}"))
        build = "You are acting as DV on the project team.\nUnit:       M03.S02.T04\nStage:      build\n"
        dv_ok = ("gov: order=G1 · mode=self · element=action · from=DV · to=QA · unit=M03.S02.T04\nask: verify\n"
                 "change_notes:\n  touched_paths: [src/a.py]\n  touched_phases: [F2]\n  surface_changed: false\n"
                 "  rollback: revert 1a2b\n  new_tests: [test_split]\nSUCCESS built and handed to QA")
        a = ctx(post("dv", dv_ok, prompt=build))
        cases.append(("shape dv.build holds" in a, f"a sound DV build passes the return gate: {a}"))
        packets_before = gov.recur(gov.read_keys(vdir), window=50)["packets"]
        a = ctx(post("regency:dv", dv_ok.replace("revert 1a2b", "<how to revert>"), prompt=build))
        keys = gov.read_keys(vdir)["keys"]
        cases.append(("RETURN to DV" in a and "return-build-change-notes-rollback" in keys,
                      f"an unfilled rollback is a RETURN and a counted key: {a}"))
        cases.append((gov.recur(gov.read_keys(vdir), window=50)["packets"] == packets_before + 1,
                      "the miss is counted as a key, never as an extra packet"))
        cases.append(("shape" not in ctx(post("dv", dv_ok)), "no Stage: line, no return gate"))
        cases.append(("shape" not in ctx(post("suba-implementer", dv_ok, prompt=build)),
                      "the stage gate applies to role agents only"))
        cases.append(("shape" not in ctx(post("dv", dv_ok, prompt=build.replace("build", "close"))),
                      "a stage with no fixed shape is not gated"))

        # suba envelopes at the boundary
        (vdir / "ongoing.json").write_text(json.dumps({"schema": 1, "items": [
            {"id": "M01.S01.T01", "title": "a", "state": "ongoing", "where": ["src/a.py"]}]}), encoding="utf-8")
        imp = returns.template("suba-implementer", mode="filled")
        imp.update(unit="M01.S01.T01")
        imp["ledger"].update(state="review")
        imp["body"]["for_dv"]["limitations"] = ["the gate log escalates nothing, by convention"]
        head = "gov: order=G1 · mode=self · element=action · from=DV · to=QA · unit=M01.S01.T01\nask: verify\n"

        def wrapped(env):
            return head + "```json\n" + json.dumps(env) + "\n```\nSUCCESS built and handed to QA"

        a = ctx(post("dv", wrapped(imp)))
        log = returns.read_log(vdir)
        cases.append(("subas: suba-implementer ok" in a and log and log[-1]["regency.valid"],
                      f"a sound envelope: checked and logged ({a[-120:]})"))
        cases.append(("ledger says M01.S01.T01 ongoing, the return says review" in a, "a ledger disagreement is named"))
        cases.append(("route ledger" in a, "words inside an envelope never raise the role's order"))
        keys = gov.read_keys(vdir)["keys"]
        cases.append(("contract-nullable" in keys, "envelope keys reach recur"))
        bad = json.loads(json.dumps(imp))
        bad["body"]["change_notes"]["rollback"] = "<how to revert>"
        a = ctx(post("dv", wrapped(bad)))
        cases.append(("suba-implementer 1 miss(es)" in a and "RETURN to DV" in a
                      and "return-implementer-change-notes-rollback" in gov.read_keys(vdir)["keys"],
                      "a miss is a RETURN and a counted key"))
        recon = returns.template("suba-recon", mode="filled")
        a = ctx(post("dv", wrapped(recon)))
        cases.append(("belongs to QA, returned by DV" in a, "a role returning another role's suba is a miss"))
        a = ctx(post("dv", head + "```json\n{\"envelope\": 1, \"suba\": \n```\nSUCCESS built and handed to QA"))
        cases.append(("not valid JSON" in a and "return-envelope-json" in gov.read_keys(vdir)["keys"],
                      "an unreadable envelope is reported and counted"))
        cases.append(("escalates nothing" not in (vdir / "returns.jsonl").read_text(encoding="utf-8"),
                      "the log never holds the body's content"))
        return wire.check(cases)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if "--print" in a:
        text = " ".join(a[a.index("--print") + 1:]) or sys.stdin.read()
        print(answer_line(gov.route(text, sender="cli"), "cli"))
        sys.exit(0)
    sys.exit(wire.serve(respond))
