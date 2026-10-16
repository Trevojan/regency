#!/usr/bin/env python3
"""hook-gov.py - Kooiman's governance at the two points where a pass changes hands.

SubagentStart            one slice line for a regency role or subagent: who it answers to, its own
                         mode, and the packet header the project reads (gov.py grammar).
PostToolUse Agent|Task   reads the packet the subagent returned, routes it with gov.py
                         (G1 -> ledger, G2/G3 -> Regent; missing or under-declared -> up), appends the
                         decision to <virtual>/gov-queue.jsonl and adds one context line to the main
                         agent, so the Regent's review packet carries only what is second order or meta.

Kind: recorder. Never blocks, never decides a tool call; an error goes to stderr (library/hooks.md §0).
Adoption gate: silent outside a project that has <guidelines>/.shortcuts/.virtual/.

Modes:  (no args) hook · --selftest · --print TEXT (route TEXT as if a subagent had returned it)
Pure standard library, Python 3.8+.
"""
import importlib.util
import os
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

AGENT_TOOLS = ("Agent", "Task")


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
        decision = gov.route(text, sender=agent)
        gov.record(vdir, decision, agent=agent, session=event.get("session_id"))
        return wire.context("PostToolUse", answer_line(decision, agent))
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

        def post(agent, resp, cwd=root, tool="Agent"):
            return respond({"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(cwd), "session_id": "s1",
                            "tool_input": {"subagent_type": agent, "prompt": "x"}, "tool_response": resp})

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
