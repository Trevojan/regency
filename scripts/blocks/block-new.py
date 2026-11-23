"""block-new - add a block to the catalogue: scripts/blocks/<id>.py with its card, a run() and a selftest that
fails until it is written, so no block ships untested. Always the Regent's yes: it creates a file (AR9).
"""
import re
from pathlib import Path

CARD = {
    "id": "block-new",
    "intent": "add a new block to the catalogue: scaffold scripts/blocks/<id>.py with its card, run() and a "
              "selftest that fails until written",
    "when": ["new block", "add block", "create block", "repeated code", "same code again", "turn code into block",
             "catalogue", "no block"],
    "args": {
        "id": {"help": "hyphen-case block id, named by role: ledger-move, not do-it"},
        "intent": {"help": "one line: what the block does, as find should match it"},
        "confirm": {"default": "agent", "choices": ["read", "agent", "regent"], "help": "who confirms its writes"},
    },
    "confirm": "regent",
    "returns": "{path}",
}
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
BANNED = {"base", "abs", "mgr", "helper", "common", "utils"}  # conventions section 14
REGENCY = Path(__file__).resolve().parent
TEMPLATE = '''"""{id} - {intent}"""
from pathlib import Path

CARD = {{
    "id": "{id}",
    "intent": {intent_repr},
    "when": [],  # the phrases an intent is asked in; find matches these words
    "args": {{
        # "name": {{"type": "str|int|bool|path|list|paths", "default": ..., "choices": [...], "help": "..."}},
    }},
    "confirm": "{confirm}",
    "returns": "{{...}}",
}}


def run(a, root):
    """Pure: read what it needs under root, return what it would write. Refuse with ValueError("one line")."""
    raise ValueError("{id} is not written yet")
    return {{"summary": "...", "result": {{}}, "writes": [{{"path": "...", "text": "...", "detail": "..."}}]}}


def selftest(tmp):
    """Plant inputs under tmp, call run(args, str(tmp)), assert on the result and on every refusal."""
    raise AssertionError("write the selftest of {id}: a block ships tested or not at all")
'''


def run(a, root):
    bid = a["id"]
    if not KEBAB.match(bid):
        raise ValueError(f"id {bid!r} is not hyphen-case")
    bad = BANNED.intersection(bid.split("-"))
    if bad:
        raise ValueError(f"id {bid!r} carries a banned name: {', '.join(sorted(bad))}")
    if not a["intent"].strip():
        raise ValueError("intent is empty")
    rel = f"scripts/blocks/{bid}.py"
    if (Path(root) / rel).exists():
        raise ValueError(f"{rel} exists")
    if Path(root).resolve() != REGENCY.parent.parent and (REGENCY / f"{bid}.py").exists():
        raise ValueError(f"regency has a block {bid!r}; to replace it here, copy its file on purpose")
    text = TEMPLATE.format(id=bid, intent=a["intent"].strip(), intent_repr=repr(a["intent"].strip()),
                           confirm=a["confirm"])
    return {"summary": f"new block {bid} ({a['confirm']}) at {rel}, selftest failing until written",
            "result": {"path": rel}, "writes": [{"path": rel, "text": text, "detail": "scaffold"}]}


def selftest(tmp):
    import importlib.util

    def refuses(args):
        try:
            run(args, str(tmp))
        except ValueError:
            return True
        return False

    out = run({"id": "ledger-move", "intent": "move a ledger item to a state", "confirm": "agent"}, str(tmp))
    w = out["writes"][0]
    assert w["path"] == "scripts/blocks/ledger-move.py", w["path"]
    target = tmp / w["path"]
    target.parent.mkdir(parents=True)
    target.write_text(w["text"], encoding="utf-8")
    spec = importlib.util.spec_from_file_location("probe_ledger_move", str(target))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CARD["id"] == "ledger-move" and mod.CARD["confirm"] == "agent"
    for fn, err in ((lambda: mod.run({}, str(tmp)), ValueError), (lambda: mod.selftest(tmp), AssertionError)):
        try:
            fn()
        except err:
            continue
        raise AssertionError("the scaffold must refuse and fail until written")
    assert refuses({"id": "ledger-move", "intent": "again", "confirm": "agent"}), "an existing block is refused"
    assert refuses({"id": "Bad_Id", "intent": "x", "confirm": "agent"}), "not hyphen-case"
    assert refuses({"id": "string-utils", "intent": "x", "confirm": "agent"}), "a banned name"
    assert refuses({"id": "next-id", "intent": "x", "confirm": "agent"}), "shadowing regency's block"
    assert refuses({"id": "fine-one", "intent": " ", "confirm": "agent"}), "an empty intent"
