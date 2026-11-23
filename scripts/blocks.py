#!/usr/bin/env python3
"""blocks.py - tested code blocks the Agent calls instead of writing code: which block, how to call it, who confirms.

library/blocks.md. A block is one file, scripts/blocks/<id>.py, holding a CARD (what it does, its arguments, who
confirms), a pure run() that returns what it would write (or raises ValueError to refuse), and a selftest(). This runner is the only caller and the
only writer: it checks the arguments against the card, applies the confirmation level, and writes atomically.

  find WORDS...                 the blocks whose card matches an intent, best first, each with its exact call
  show ID                       one card: intent, arguments, confirmation, returns, call
  list                          every block, one line each
  run ID [key=value ...]        run a block; --plan shows the writes without writing; --yes TOKEN applies a
                                regent-level plan the Regent accepted
  test [ID]                     every block's selftest (or one)
  --selftest                    the runner's own checks, then every block's selftest

Confirmation (the card's "confirm", raised by "regent_if"):
  read    writes nothing; runs at once
  agent   writes inside the task (conventions section 5); runs at once and prints every write
  regent  prints the plan, its TOKEN and the pop-up (ASK) to pass as given; writes only with --yes TOKEN

Layers: regency's scripts/blocks/, then the project's own <root>/scripts/blocks/ (a project block of the same id wins).
Every run takes --repo DIR (default: the current directory); every path argument stays inside it.
Exit 0 done · 1 refused (the line says why) · 2 waiting for the Regent's yes (plan printed, nothing written).
Pure standard library, Python 3.8+.
"""
import hashlib
import importlib.util
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BLOCKS = HERE / "blocks"
LEVELS = ("read", "agent", "regent")
TYPES = ("str", "int", "bool", "path", "list", "paths")
STOP = {"the", "and", "for", "with", "from", "into", "this", "that", "what", "which", "how", "file", "files"}


class Refused(Exception):
    """A block or the runner refuses: the message is the one line the caller reads."""


# --- loading -----------------------------------------------------------------------------------------------------

def layers(root):
    seen, out = set(), []
    for label, folder in (("regency", BLOCKS), ("project", Path(root) / "scripts" / "blocks")):
        f = folder.resolve()
        if f.is_dir() and f not in seen:
            seen.add(f)
            out.append((label, f))
    return out


def load(path):
    spec = importlib.util.spec_from_file_location("block_" + path.stem.replace("-", "_"), str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    card = getattr(mod, "CARD", None)
    problem = card_problem(card, path.stem) or (None if callable(getattr(mod, "run", None)) else "no run()") \
        or (None if callable(getattr(mod, "selftest", None)) else "no selftest()")
    if problem:
        raise Refused(f"{path.name}: {problem}")
    return mod


def card_problem(card, stem):
    if not isinstance(card, dict):
        return "no CARD dict"
    if card.get("id") != stem:
        return f"CARD id {card.get('id')!r} must equal the file name {stem!r}"
    for key in ("intent", "when", "args", "confirm", "returns"):
        if key not in card:
            return f"CARD has no {key!r}"
    if card["confirm"] not in LEVELS:
        return f"confirm must be one of {', '.join(LEVELS)}"
    for name, spec in card["args"].items():
        if spec.get("type", "str") not in TYPES:
            return f"argument {name}: type must be one of {', '.join(TYPES)}"
    for name in card.get("regent_if", {}):
        if name not in card["args"]:
            return f"regent_if names an unknown argument {name!r}"
    return None


def catalogue(root):
    """{id: (layer, module)}; a project block replaces regency's block of the same id."""
    out = {}
    for label, folder in layers(root):
        for f in sorted(folder.glob("*.py")):
            out[f.stem] = (label, load(f))
    return out


# --- arguments and confirmation ----------------------------------------------------------------------------------

def parse_args(card, pairs, root):
    given = {}
    for p in pairs:
        if "=" not in p:
            raise Refused(f"argument {p!r} is not key=value; arguments: {', '.join(card['args']) or 'none'}")
        k, v = p.split("=", 1)
        if k not in card["args"]:
            raise Refused(f"unknown argument {k!r}; arguments: {', '.join(card['args']) or 'none'}")
        given[k] = v
    out = {}
    for name, spec in card["args"].items():
        if name not in given:
            if "default" not in spec:
                raise Refused(f"missing argument {name}=<{spec.get('type', 'str')}>: {spec.get('help', '')}")
            out[name] = spec["default"]
            continue
        out[name] = convert(name, spec, given[name], root)
    return out


def convert(name, spec, raw, root):
    kind = spec.get("type", "str")
    try:
        if kind == "int":
            value = int(raw)
        elif kind == "bool":
            if raw.lower() not in ("yes", "no", "true", "false"):
                raise ValueError("yes or no")
            value = raw.lower() in ("yes", "true")
        elif kind == "list":
            value = [x.strip() for x in raw.split(",") if x.strip()]
        elif kind == "path":
            value = inside(root, raw)
        elif kind == "paths":
            value = [inside(root, x.strip()) for x in raw.split(",") if x.strip()]
        else:
            value = raw
    except ValueError as e:
        raise Refused(f"argument {name}: {raw!r} is not a {kind} ({e})")
    choices = spec.get("choices")
    if choices and value not in choices:
        raise Refused(f"argument {name}: {raw!r} is not one of {', '.join(map(str, choices))}")
    return value


def inside(root, raw):
    """A path argument as a posix path relative to root; one that leaves root is refused (a trust boundary)."""
    base = Path(root).resolve()
    p = (base / raw).resolve()
    try:
        return p.relative_to(base).as_posix() or "."
    except ValueError:
        raise ValueError("it leaves the root")


def level(card, args):
    for name, values in card.get("regent_if", {}).items():
        v = args.get(name)
        if v in values or (values == ["*"] and v not in (None, "", [])):
            return "regent"
    return card["confirm"]


def token(block_id, args, writes, root):
    rows = []
    for w in writes:
        cur = Path(root) / w["path"]
        before = hashlib.sha256(cur.read_bytes()).hexdigest() if cur.is_file() else ""
        rows.append([w["path"], before, hashlib.sha256(w["text"].encode("utf-8")).hexdigest()])
    blob = json.dumps({"block": block_id, "args": args, "writes": rows}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:10]


def ask(summary, writes):
    names = ", ".join(w["path"] for w in writes)
    return {"question": f"{summary}. Apply?", "header": "Confirm", "multiSelect": False,
            "options": [{"label": "Apply", "description": f"writes {len(writes)} file(s): {names}"},
                        {"label": "Do not apply", "description": "nothing is written"}]}


def write_all(root, writes):
    for w in writes:
        target = Path(root) / inside(root, w["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=".block-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                fh.write(w["text"])
            os.replace(tmp, target)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


def execute(block_id, pairs, root=".", plan_only=False, yes=None):
    """Run one block. Returns (exit code, lines). The one entry point for the CLI and the selftests."""
    root = str(Path(root).resolve())
    blocks = catalogue(root)
    if block_id not in blocks:
        raise Refused(f"no block {block_id!r}; find one: blocks.py find <intent>")
    layer, mod = blocks[block_id]
    card = mod.CARD
    args = parse_args(card, pairs, root)
    try:
        out = mod.run(args, root)
    except ValueError as e:  # a block refuses by raising ValueError with its one line
        raise Refused(f"{block_id}: {e}")
    if not isinstance(out, dict) or "summary" not in out:
        raise Refused(f"{block_id}: run() must return a dict with 'summary'")
    writes = out.get("writes") or []
    for w in writes:
        try:
            w["path"] = inside(root, w["path"])
        except ValueError:
            raise Refused(f"{block_id}: write to {w['path']!r} leaves the root")
    need = level(card, args)
    if need == "read" and writes:
        raise Refused(f"{block_id}: a read block returned writes")
    lines = [f"BLOCK  {block_id} ({layer}, {need})", f"SUMMARY  {out['summary']}"]
    lines += [f"WRITE  {w['path']}  {w.get('detail', '')}".rstrip() for w in writes]
    if "result" in out:
        lines.append("RESULT  " + json.dumps(out["result"], sort_keys=True, default=str))
    if not writes:
        return 0, lines + ["DONE  nothing to write"]
    if plan_only:
        return 0, lines + ["PLAN  nothing written (--plan)"]
    if need == "regent":
        t = token(block_id, args, writes, root)
        if yes is None:
            call = " ".join(shlex.quote(x) for x in [block_id] + list(pairs))
            return 2, lines + [f"TOKEN  {t}", "ASK  " + json.dumps(ask(out["summary"], writes)),
                               f"ON-APPLY  blocks.py run {call} --repo {shlex.quote(root)} --yes {t}",
                               "WAIT  the Regent's answer; 'Do not apply' or no answer writes nothing"]
        if yes != t:
            raise Refused(f"token {yes} does not match this plan ({t}): the arguments or the files changed since "
                          "the Regent saw it; plan again and ask again")
    write_all(root, writes)
    return 0, lines + [f"DONE  wrote {len(writes)} file(s)"]


# --- orientation -------------------------------------------------------------------------------------------------

def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP}


def call_line(card):
    parts = [f"blocks.py run {card['id']}"]
    for name, spec in card["args"].items():
        hint = f"{name}=<{spec.get('type', 'str')}>"
        parts.append(hint if "default" not in spec else f"[{name}={shown(spec['default'], spec)}]")
    return " ".join(parts)


def shown(value, spec):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value in ("", [], None):
        return f"<{spec.get('type', 'str')}>"
    return ",".join(map(str, value)) if isinstance(value, list) else str(value)


def find(query, root):
    q = words(" ".join(query))
    scored = []
    for bid, (layer, mod) in catalogue(root).items():
        c = mod.CARD
        hay = words(" ".join([bid.replace("-", " "), c["intent"], " ".join(c["when"])]))
        score = len(q & hay)
        if score:
            scored.append((-score, bid, layer, c))
    return [(-s, bid, layer, c) for s, bid, layer, c in sorted(scored)[:3]]


def show(card, layer):
    lines = [f"BLOCK  {card['id']} ({layer}, confirm {card['confirm']})", f"INTENT  {card['intent']}"]
    for name, spec in card["args"].items():
        extra = f" one of {', '.join(str(c) if c != '' else '(empty)' for c in spec['choices'])}" \
            if spec.get("choices") else ""
        dflt = f" default {shown(spec['default'], spec)}" if "default" in spec else " required"
        lines.append(f"ARG  {name}: {spec.get('type', 'str')}{dflt}{extra} - {spec.get('help', '')}")
    for name, values in card.get("regent_if", {}).items():
        lines.append(f"REGENT-IF  {name} " + ("given" if values == ["*"] else "in " + ", ".join(map(str, values))))
    lines += [f"RETURNS  {card['returns']}", f"CALL  {call_line(card)}"]
    return lines


# --- tests -------------------------------------------------------------------------------------------------------

def test_blocks(root, only=None):
    fails, lines = 0, []
    for bid, (layer, mod) in sorted(catalogue(root).items()):
        if only and bid != only:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                mod.selftest(Path(tmp))
                lines.append(f"OK    {bid} ({layer})")
            except Exception as e:  # a block's failing selftest is a finding, reported, never swallowed
                fails += 1
                lines.append(f"FAIL  {bid} ({layer}): {type(e).__name__}: {e}")
    if only and not lines:
        return 1, [f"FAIL  no block {only!r}"]
    return (1 if fails else 0), lines


def selftest():
    misses, ran = [], []

    def check(name, cond):
        ran.append(name)
        if not cond:
            misses.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pb = root / "scripts" / "blocks"
        pb.mkdir(parents=True)
        (pb / "probe-write.py").write_text(
            'CARD = {"id": "probe-write", "intent": "write a probe note", "when": ["probe note"], "confirm": "agent",\n'
            '        "regent_if": {"loud": [True]}, "returns": "the note",\n'
            '        "args": {"to": {"type": "path"}, "text": {"default": "hi"}, "loud": {"type": "bool", "default": False}}}\n'
            'def run(a, root):\n'
            '    return {"summary": "note to " + a["to"], "writes": [{"path": a["to"], "text": a["text"]}]}\n'
            'def selftest(tmp):\n'
            '    assert run({"to": "x", "text": "y", "loud": False}, str(tmp))["writes"][0]["text"] == "y"\n',
            encoding="utf-8")
        (pb / "probe-bad.py").write_text(
            'CARD = {"id": "probe-bad", "intent": "a read block that writes", "when": [], "confirm": "read",\n'
            '        "returns": "", "args": {}}\n'
            'def run(a, root):\n    return {"summary": "x", "writes": [{"path": "y", "text": "z"}]}\n'
            'def selftest(tmp):\n    raise AssertionError("planted")\n', encoding="utf-8")

        def refused(fn):
            try:
                fn()
            except Refused:
                return True
            return False

        code, _ = execute("probe-write", ["to=a.txt"], root)
        check("agent level writes at once", code == 0 and (root / "a.txt").read_text() == "hi")
        code, _ = execute("probe-write", ["to=b.txt", "text=x"], root, plan_only=True)
        check("--plan writes nothing", code == 0 and not (root / "b.txt").exists())
        check("a path leaving the root is refused", refused(lambda: execute("probe-write", ["to=../out.txt"], root)))
        check("an unknown argument is refused", refused(lambda: execute("probe-write", ["to=a", "nope=1"], root)))
        check("a missing argument is refused", refused(lambda: execute("probe-write", [], root)))
        check("a bad bool is refused", refused(lambda: execute("probe-write", ["to=a", "loud=maybe"], root)))
        check("a read block that writes is refused", refused(lambda: execute("probe-bad", [], root)))
        code, lines = execute("probe-write", ["to=c.txt", "loud=yes"], root)
        t = next((l.split()[1] for l in lines if l.startswith("TOKEN")), None)
        asked = next((json.loads(l[5:]) for l in lines if l.startswith("ASK ")), {})
        check("regent_if raises the level and waits", code == 2 and t and not (root / "c.txt").exists())
        check("the pop-up is ready to pass", asked.get("header") == "Confirm" and len(asked.get("options", [])) == 2)
        check("a wrong token is refused", refused(lambda: execute("probe-write", ["to=c.txt", "loud=yes"], root,
                                                                   yes="0000000000")))
        (root / "c.txt").write_text("changed meanwhile", encoding="utf-8")
        check("a file changed after the plan invalidates the token",
              refused(lambda: execute("probe-write", ["to=c.txt", "loud=yes"], root, yes=t)))
        _, lines = execute("probe-write", ["to=c.txt", "loud=yes"], root)
        t2 = next(l.split()[1] for l in lines if l.startswith("TOKEN"))
        code, _ = execute("probe-write", ["to=c.txt", "loud=yes"], root, yes=t2)
        check("the right token applies", code == 0 and (root / "c.txt").read_text() == "hi")
        hits = find(["write", "a", "probe", "note"], root)
        check("find ranks the matching block first", bool(hits) and hits[0][1] == "probe-write")
        check("find returns nothing for an unrelated intent", not find(["zebra", "quasar"], root))
        code, lines = test_blocks(root, "probe-bad")
        check("a failing block selftest is reported", code == 1 and lines[0].startswith("FAIL"))
        (pb / "next-id.py").write_text((BLOCKS / "next-id.py").read_text(encoding="utf-8")
                                       .replace("next free number", "project copy of next free number"),
                                       encoding="utf-8")
        check("a project block replaces regency's of the same id",
              catalogue(root)["next-id"][0] == "project")
        (pb / "probe-x.py").write_text((pb / "probe-write.py").read_text(encoding="utf-8")
                                       .replace('"id": "probe-write"', '"id": "other"'), encoding="utf-8")
        check("a card whose id differs from its file is refused", refused(lambda: catalogue(root)))
    n = len(ran)
    for m in misses:
        print(f"MISS  {m}")
    code, lines = test_blocks(str(HERE.parent))
    for l in lines:
        print(l)
    print(f"blocks: runner {n - len(misses)}/{n}, blocks {sum(l.startswith('OK') for l in lines)}/{len(lines)}")
    return 1 if misses or code else 0


# --- command line ------------------------------------------------------------------------------------------------

def main(argv):
    args, root, plan_only, yes = [], ".", False, None
    it = iter(argv)
    for a in it:
        if a == "--repo":
            root = next(it, ".")
        elif a == "--plan":
            plan_only = True
        elif a == "--yes":
            yes = next(it, "")
        else:
            args.append(a)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] == "--selftest":
        return selftest()
    mode, rest = args[0], args[1:]
    try:
        if mode == "find":
            hits = find(rest, root)
            if not hits:
                print(f"NONE  no block for {' '.join(rest)!r}: write the code inline; when the same intent comes "
                      "back, add a block with: blocks.py run block-new id=<id> intent=<text> (library/blocks.md section 5)")
                return 1
            for score, bid, layer, c in hits:
                print(f"BLOCK  {bid} ({layer}, {c['confirm']}, score {score})  {c['intent']}")
                print(f"  CALL  {call_line(c)}")
            return 0
        if mode == "list":
            for bid, (layer, mod) in sorted(catalogue(root).items()):
                print(f"{bid}  ({layer}, {mod.CARD['confirm']})  {mod.CARD['intent']}")
            return 0
        if mode == "show":
            blocks = catalogue(root)
            if not rest or rest[0] not in blocks:
                raise Refused(f"no block {rest[0] if rest else ''!r}; blocks.py list")
            layer, mod = blocks[rest[0]]
            print("\n".join(show(mod.CARD, layer)))
            return 0
        if mode == "test":
            code, lines = test_blocks(root, rest[0] if rest else None)
            print("\n".join(lines))
            return code
        if mode == "run":
            if not rest:
                raise Refused("run needs a block id; blocks.py find <intent>")
            code, lines = execute(rest[0], rest[1:], root, plan_only, yes)
            print("\n".join(lines))
            return code
        raise Refused(f"unknown mode {mode!r}: find, show, list, run, test, --selftest")
    except Refused as e:
        print(f"REFUSED  {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
