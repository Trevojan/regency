#!/usr/bin/env python3
"""returns.py - the return gate: does a return have the shape its contract requires?

It checks presence and shape, never truth (conventions 15.2): it can say the rollback line exists,
not that the rollback works. Two kinds of return:

  stage   a role's packet leaving the role. Shapes: the machine block of
          library/team/references/packets.md section 4. Edit the shapes there, never here.
  suba    one JSON envelope per return, in a ```json fence (library/subagents/envelope.schema.json). Its
          body follows the suba's own contract, library/subagents/<name>/contract.json: `returns` to the
          owner and, for a suba with a direct mode, `returns_direct` to its caller.

Schemas use a JSON Schema subset, validated here with the standard library: type, enum, const, pattern,
minLength, maxLength, minimum, maximum, items, minItems, maxItems, properties, required,
additionalProperties, minProperties, anyOf, $ref, $defs, description, examples. A fact that lives
elsewhere is referenced, never copied:
  ids:<kind>         a grammar of library/ids.md (unit, phase, gate, ui-rule, order, conflict, version, person)
  gov:<name>         scripts/gov.py: key (the slug grammar), role, order, mode, element
  packets:terminal   the terminal states of packets.md section 4
Rules beyond the subset (library/subagents/ALIGNMENT.md section 10): a value that is wholly <...> is an
unfilled placeholder; to its owner an envelope carries a gov block running from and to the owner (gov.py
OWNER), in direct mode none; every artefact the body names is listed in the envelope and, with the message
at hand, delivered as an ARTEFACT block; a ledger line carries what its state needs (ongoing and draft:
where, review: next, blocked: blocked_by) and is never 'done'. Every value of type gov:key is a finding class,
collected for gov.py recur. Validated envelopes are logged to <virtual>/returns.jsonl - metadata only,
never the body.

One finding per line; exit 1 when any finding means RETURN, 2 when a shape or contract cannot be loaded.

Modes:  check --stage ROLE.STAGE FILE|-  ·  check --suba NAME [--direct] FILE|-  ·  envelopes FILE|-
        template NAME [--direct]  ·  show [--unit ID] [-n N]  ·  contracts  ·  stages  ·  --selftest
Pure standard library, Python 3.8+.
"""
import argparse
import functools
import json
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import gov  # noqa: E402
import hook_wire as wire  # noqa: E402

PACKETS = Path("library") / "team" / "references" / "packets.md"
SUBAGENTS = Path("library") / "subagents"
ENVELOPE = SUBAGENTS / "envelope.schema.json"
IDS = Path("library") / "ids.md"
LOG, KEEP = "returns.jsonl", 500
SHAPES_HEAD = re.compile(r"^## 4\. Return shapes", re.M)
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.S)
FENCE = re.compile(r"^\s*```")
TOP = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$")
CHILD = re.compile(r"^([ \t]+)([A-Za-z_][\w-]*):[ \t]*(.*)$")
PLACEHOLDER = re.compile(r"^<[^<>]+>$")
CHECKS = {"labels", "match", "one_of", "yaml", "filled", "absent", "approved_needs"}
SUBSET = {"type", "enum", "const", "pattern", "minLength", "maxLength", "minimum", "maximum", "items", "minItems",
          "maxItems", "properties", "required", "additionalProperties", "minProperties", "anyOf", "$ref", "$defs",
          "description", "examples", "$id"}
ARTEFACT_BLOCK = re.compile(r"(?ms)^<<<ARTEFACT[ \t]+(\S+)[ \t]*\n.*?^ARTEFACT>>>[ \t]*$")
JSON_FENCE = re.compile(r"(?ms)^[ \t]*```json[ \t]*\n(.*?)\n[ \t]*```[ \t]*$")
ARTEFACT_REF = "envelope#/$defs/artefact"


# ---------- loading ------------------------------------------------------------------------------

def load_shapes(root=ROOT):
    """The machine block of packets.md section 4; ValueError when it is missing or malformed."""
    text = (Path(root) / PACKETS).read_text(encoding="utf-8")
    head = SHAPES_HEAD.search(text)
    m = JSON_BLOCK.search(text, head.end()) if head else None
    if not m:
        raise ValueError(f"{PACKETS.as_posix()}: no machine block under '## 4. Return shapes'")
    data = json.loads(m.group(1))
    for name, shape in data.get("stages", {}).items():
        unknown = set(shape) - CHECKS
        if unknown:
            raise ValueError(f"stage {name}: unknown check(s) {sorted(unknown)}")
    return data


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "field"


@functools.lru_cache(maxsize=None)
def _json_file(path, mtime):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_json(path):
    p = Path(path)
    return _json_file(str(p.resolve()), p.stat().st_mtime_ns)


def envelope_schema(root=ROOT):
    return load_json(Path(root) / ENVELOPE)


def contract(name, root=ROOT):
    """A suba's contract.json, or None when the suba has none."""
    p = Path(root) / SUBAGENTS / str(name) / "contract.json"
    return load_json(p) if re.match(r"^suba-[a-z0-9-]+$", str(name)) and p.is_file() else None


@functools.lru_cache(maxsize=None)
def _ids(path, mtime):
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))


def external(ref, root=ROOT):
    """The schema a reference names outside the schema files; None when it names nothing."""
    kind, _, name = ref.partition(":")
    if kind == "ids":
        p = Path(root) / IDS
        g = _ids(str(p.resolve()), p.stat().st_mtime_ns).get(name)
        return None if g is None else {"type": "string", "pattern": g["pattern"], "examples": [g["example"]],
                                       "description": name}
    if kind == "gov":
        if name == "key":
            return {"type": "string", "pattern": gov.KEY.pattern, "examples": ["contract-nullable"], "description": "key"}
        values = {"role": gov.ROLES, "order": gov.ORDERS, "mode": gov.MODES, "element": gov.ELEMENTS}.get(name)
        return None if values is None else {"enum": list(values), "description": name}
    if kind == "packets" and name == "terminal":
        return {"enum": list(load_shapes(root)["terminal_states"]), "description": "terminal state"}
    return None


# ---------- role packets (stage shapes) -----------------------------------------------------------

def norm_line(line):
    """Lower-case, markdown decoration and numbering stripped, - and _ read as spaces."""
    s = line.replace("*", "").replace("`", "").lower()
    s = re.sub(r"^[\s>#|\-]+", "", s)
    s = re.sub(r"^\d+[.)]\s+", "", s)
    s = re.sub(r"[_\-]", " ", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def has_label(norm_lines, alternatives):
    for alt in alternatives.split("|"):
        pat = re.compile(r"^" + re.escape(norm_line(alt)) + r"\s*(?::|\||$)")
        if any(pat.match(line) for line in norm_lines):
            return True
    return False


def has_word(text, word):
    return re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text, re.I) is not None


def yaml_blocks(text):
    """Top-level keys and their first-level children, read tolerantly (fenced or not): {top: {"value", "children"}}."""
    out, top, indent = {}, None, None
    for raw in text.splitlines():
        if FENCE.match(raw) or not raw.strip():
            continue
        line = re.sub(r"\s+#.*$", "", raw) if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        t = TOP.match(line)
        if t:
            top, indent = t.group(1), None
            out[top] = {"value": t.group(2).strip(), "children": {}}
            continue
        c = CHILD.match(line)
        if c and top is not None:
            width = len(c.group(1).expandtabs(2))
            indent = width if indent is None else indent
            if width == indent:
                out[top]["children"][c.group(2)] = c.group(3).strip()
            continue
        if not line[:1].isspace():
            top = None
    return out


def filled(value):
    v = (value or "").strip().strip("'\"")
    return bool(v) and v.lower() not in ("~", "null") and not PLACEHOLDER.match(v)


def terminal(text, states):
    """(field, message) when the terminal state or its reason is missing; [] when both are there."""
    lines = text.splitlines()
    pat = re.compile(r"\b(" + "|".join(map(re.escape, states)) + r")\b")
    hits = [i for i, line in enumerate(lines) if pat.search(line)]
    if not hits:
        return [("terminal-state", f"no terminal state ({', '.join(states)})")]
    i = hits[-1]
    rest = pat.sub("", lines[i])
    words = re.findall(r"[A-Za-z]{2,}", rest)
    if len(words) < 3:
        after = next((line for line in lines[i + 1:] if line.strip()), "")
        words = re.findall(r"[A-Za-z]{2,}", after)
    if len(words) < 3:
        return [("terminal-reason", f"terminal state {pat.search(lines[i]).group(1)} has no reason line")]
    return []


def check_stage(text, shape, states):
    """[(field, message)] for one role's packet against its stage shape."""
    found = []
    norm = [norm_line(line) for line in text.splitlines()]
    for label in shape.get("labels", []):
        if not has_label(norm, label):
            found.append((slug(label.split("|")[0]), f"missing '{label.split('|')[0]}'"))
    for name, pattern in shape.get("match", {}).items():
        if not re.search(pattern, text):
            found.append((slug(name), f"'{name}' does not match {pattern}"))
    for name, words in shape.get("one_of", {}).items():
        if not any(has_word(text, w) for w in words):
            found.append((slug(name), f"'{name}' must be one of: {' / '.join(words)}"))
    blocks = yaml_blocks(text)
    for block, keys in shape.get("yaml", {}).items():
        if block not in blocks:
            found.append((slug(block), f"missing block '{block}:'"))
            continue
        got = blocks[block]["children"]
        for k in keys:
            if k not in got:
                found.append((slug(f"{block}-{k}"), f"{block}.{k} is missing"))
        for k in got:
            if k not in keys:
                found.append((slug(f"{block}-{k}"), f"{block}.{k} is not in the shape (no field for reasoning)"))
    for dotted in shape.get("filled", []):
        block, _, key = dotted.partition(".")
        value = blocks.get(block, {}).get("children", {}).get(key)
        if value is not None and not filled(value):
            found.append((slug(dotted), f"{dotted} is empty or an unfilled placeholder"))
    for block in shape.get("absent", []):
        if block in blocks:
            found.append((slug(block), f"'{block}:' must not leave the role"))
    needs = shape.get("approved_needs")
    if needs and has_word(text, "approved") and needs.lower() not in text.lower():
        found.append(("approved", f"'approved' without '{needs}'"))
    return found + terminal(text, states)


def stage_findings(text, role, stage, root=ROOT):
    """For hook-gov: [(field, message)] for a role's packet, or None when the stage has no fixed shape."""
    data = load_shapes(root)
    shape = data["stages"].get(f"{role.lower()}.{stage.lower()}")
    return None if shape is None else check_stage(text, shape, data["terminal_states"])


# ---------- the schema subset -------------------------------------------------------------------

TYPES = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
         "string": lambda v: isinstance(v, str), "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None,
         "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
         "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)}


def jtype(value):
    return next((t for t in ("null", "boolean", "integer", "number", "string", "array", "object") if TYPES[t](value)), "?")


def join(path, key):
    return f"{path}.{key}" if path else str(key)


class Check:
    """One validation run: misses as (path, message); finding keys and artefact names collected on the way."""

    def __init__(self, envelope, root=ROOT):
        self.envelope, self.root = envelope, root
        self.misses, self.keys, self.named = [], [], []

    def miss(self, path, message):
        self.misses.append((path or "(envelope)", message))

    def resolve(self, ref, doc):
        if ref.startswith("#/$defs/"):
            return doc.get("$defs", {}).get(ref[8:]), doc
        if ref.startswith("envelope#/$defs/"):
            return self.envelope.get("$defs", {}).get(ref[16:]), self.envelope
        return external(ref, self.root), doc

    def run(self, value, schema, doc, path=""):
        if "$ref" in schema:
            target, tdoc = self.resolve(schema["$ref"], doc)
            if target is None:
                return self.miss(path, f"schema reference {schema['$ref']} resolves to nothing")
            before = len(self.misses)
            self.run(value, target, tdoc, path)
            if len(self.misses) == before and isinstance(value, str):
                if schema["$ref"] == "gov:key":
                    self.keys.append(value)
                elif schema["$ref"] == ARTEFACT_REF:
                    self.named.append((path, value))
            return None
        if isinstance(value, str) and PLACEHOLDER.match(value.strip()):
            return self.miss(path, f"unfilled placeholder {value!r}")
        if "anyOf" in schema:
            first = None
            for alt in schema["anyOf"]:
                sub = Check(self.envelope, self.root)
                sub.run(value, alt, doc, path)
                if not sub.misses:
                    self.keys += sub.keys
                    self.named += sub.named
                    return None
                first = first or sub
            return self.miss(path, "matches none of its forms: " + "; ".join(m for _, m in first.misses[:2]))
        if "const" in schema and value != schema["const"]:
            return self.miss(path, f"must be {json.dumps(schema['const'])}")
        if "enum" in schema and value not in schema["enum"]:
            return self.miss(path, f"{json.dumps(value)} is not one of {' | '.join(map(str, schema['enum']))}")
        t = schema.get("type")
        if t and not any(TYPES[x](value) for x in ([t] if isinstance(t, str) else t)):
            return self.miss(path, f"must be {t if isinstance(t, str) else ' or '.join(t)}, got {jtype(value)}")
        if isinstance(value, str):
            if len(value.strip()) < schema.get("minLength", 0):
                self.miss(path, f"is shorter than {schema['minLength']}")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                self.miss(path, f"is longer than {schema['maxLength']}")
            if "pattern" in schema and not re.search(schema["pattern"], value):
                self.miss(path, f"{value!r} does not match {schema['pattern']}")
        elif TYPES["number"](value):
            if "minimum" in schema and value < schema["minimum"]:
                self.miss(path, f"is below {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                self.miss(path, f"is above {schema['maximum']}")
        elif isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                self.miss(path, f"needs at least {schema['minItems']} item(s)")
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                self.miss(path, f"takes at most {schema['maxItems']} item(s)")
            for i, item in enumerate(value):
                if "items" in schema:
                    self.run(item, schema["items"], doc, f"{path}[{i}]")
        elif isinstance(value, dict):
            props = schema.get("properties", {})
            for k in schema.get("required", []):
                if k not in value:
                    self.miss(join(path, k), "is missing")
            for k, v in value.items():
                if k in props:
                    self.run(v, props[k], doc, join(path, k))
                elif schema.get("additionalProperties", True) is False:
                    self.miss(join(path, k), "is not in the contract (no field for reasoning)")
                elif isinstance(schema.get("additionalProperties"), dict):
                    self.run(v, schema["additionalProperties"], doc, join(path, k))
            if len(value) < schema.get("minProperties", 0):
                self.miss(path, f"needs at least {schema['minProperties']} field(s)")
        return None


# ---------- envelopes ---------------------------------------------------------------------------

def check_envelope(env, delivered=None, root=ROOT):
    """(misses, info) for one envelope. delivered: the ARTEFACT names in its message, or None when unknown."""
    envelope = envelope_schema(root)
    c = Check(envelope, root)
    c.run(env, envelope, envelope)
    info = {"suba": None, "via": None, "unit": None, "owner": None, "keys": [], "terminal": None, "ask": None,
            "element": None, "ledger": None}
    if not isinstance(env, dict):
        return c.misses, info
    name, via = env.get("suba"), env.get("via")
    owner = gov.OWNER.get(name) if isinstance(name, str) else None
    con = contract(name, root)
    if con is None:
        c.miss("suba", f"{name!r} has no contract.json in {SUBAGENTS.as_posix()}")
    elif via in ("owner", "direct"):
        key = "returns_direct" if via == "direct" else "returns"
        if key not in con:
            c.miss("via", f"{name} has no direct mode")
        elif "body" in env:
            c.run(env["body"], con[key], con, "body")
    g = env.get("gov")
    if via == "owner":
        if not isinstance(g, dict):
            c.miss("gov", "a return to the owner carries a gov block")
        elif owner and (g.get("from") != owner or g.get("to") != owner):
            c.miss("gov", f"must run from={owner} to={owner}, got from={g.get('from')} to={g.get('to')}")
    elif via == "direct" and "gov" in env:
        c.miss("gov", "a direct-mode return carries no gov block")
    led = env.get("ledger")
    if isinstance(led, dict):
        need = {"ongoing": "where", "draft": "where", "review": "next", "blocked": "blocked_by"}.get(led.get("state"))
        if need and not led.get(need):
            c.miss(f"ledger.{need}", f"a {led['state']} ledger line needs {need}")
    listed = [a for a in env.get("artefacts") or [] if isinstance(a, str)]
    for path, n in c.named:
        if n not in listed:
            c.miss(path, f"names artefact {n!r}, which the envelope does not list")
    if delivered is not None:
        for n in listed:
            if n not in delivered:
                c.miss("artefacts", f"{n!r} has no ARTEFACT block in the message")
    info.update(suba=name, via=via, unit=env.get("unit"), owner=owner, keys=sorted(set(c.keys)),
                terminal=(env.get("terminal") or {}).get("state") if isinstance(env.get("terminal"), dict) else None,
                ask=g.get("ask") if isinstance(g, dict) else None, element=g.get("element") if isinstance(g, dict) else None,
                ledger=led if isinstance(led, dict) else None)
    return c.misses, info


def extract(text):
    """([(envelope, None) | (None, error)], [ARTEFACT names]) found in one message."""
    text = text or ""
    names = [m.group(1) for m in ARTEFACT_BLOCK.finditer(text)]
    bare = ARTEFACT_BLOCK.sub("", text)
    raws = [m.group(1) for m in JSON_FENCE.finditer(bare)]
    if not raws and bare.strip().startswith("{"):
        raws = [bare.strip()]
    found = []
    for raw in raws:
        try:
            obj = json.loads(raw)
        except ValueError as e:
            if '"envelope"' in raw:
                found.append((None, f"an envelope is not valid JSON ({e})"))
            continue
        if isinstance(obj, dict) and "envelope" in obj:
            found.append((obj, None))
    return found, names


def strip_envelopes(text):
    """The message without its envelope fences: a suba's hand-up is internal and never raises the role's order."""
    def keep(m):
        try:
            obj = json.loads(m.group(1))
        except ValueError:
            return m.group(0)
        return "" if isinstance(obj, dict) and "envelope" in obj else m.group(0)
    return JSON_FENCE.sub(keep, text or "")


def field_key(name, path):
    """The finding key a miss is counted under: return-<suba>-<field>, indices dropped."""
    field = re.sub(r"\[\d+\]", "", path)
    field = field[5:] if field.startswith("body.") else field
    return f"return-{str(name or 'unknown').replace('suba-', '', 1)}-{slug(field)}"[:64].rstrip("-")


# ---------- templates ---------------------------------------------------------------------------

def synth(schema, doc, envelope, mode, root=ROOT, desc=None, override=False):
    """A value for a schema: a template (every scalar a <placeholder>) or a filled sample that must validate.
    A $ref's own description is more specific than the definition's, so it wins."""
    if "$ref" in schema:
        c = Check(envelope, root)
        target, tdoc = c.resolve(schema["$ref"], doc)
        mine = schema.get("description")
        target = dict(target or {}, **({"examples": schema["examples"]} if "examples" in schema else {}))
        return synth(target, tdoc, envelope, mode, root, mine or desc, override=bool(mine) or override)
    d = desc if (override and desc) else (schema.get("description") or desc)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return f"<{' | '.join(map(str, schema['enum']))}>" if mode == "template" else schema["enum"][0]
    if "anyOf" in schema:
        if mode == "template":
            return f"<{d or 'value'}>"
        return synth(schema["anyOf"][0], doc, envelope, mode, root, d)
    t = schema.get("type")
    t = t[0] if isinstance(t, list) else t
    if t == "object":
        return {k: synth(v, doc, envelope, mode, root) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return [synth(schema.get("items", {}), doc, envelope, mode, root, d) for _ in range(max(1, schema.get("minItems", 0)))]
    if t == "boolean":
        return "<true | false>" if mode == "template" else False
    if t in ("integer", "number"):
        return f"<{t}: {d}>" if mode == "template" and d else (f"<{t}>" if mode == "template" else schema.get("minimum", 1))
    ex = (schema.get("examples") or [None])[0]
    if mode == "template":
        return f"<{d or 'text'}, e.g. {ex}>" if ex is not None else f"<{d or 'text'}>"
    if ex is not None:
        return ex
    text = "sample text"
    while len(text) < schema.get("minLength", 1):
        text += " sample text"
    return text


def template(name, direct=False, mode="template", root=ROOT):
    """The envelope a suba returns, as a template or a filled sample."""
    envelope, con = envelope_schema(root), contract(name, root)
    props = envelope["properties"]

    def part(key):
        return synth(props[key], envelope, envelope, mode, root)

    out = {"envelope": 1, "suba": name, "via": "direct" if direct else "owner"}
    if not direct:
        owner = gov.OWNER.get(name, "DV")
        out["unit"] = part("unit")
        out["gov"] = dict(part("gov"), **{"from": owner, "to": owner})
    out["body"] = synth(con["returns_direct" if direct else "returns"], con, envelope, mode, root)
    out["doubts"] = part("doubts")
    if not direct:
        out["ledger"] = part("ledger")
    out["artefacts"] = part("artefacts")
    out["terminal"] = part("terminal")
    if mode == "filled":
        c = Check(envelope, root)
        c.run(out["body"], con["returns_direct" if direct else "returns"], con, "body")
        out["artefacts"] = sorted({n for _, n in c.named})
    return out


def optional_paths(schema, doc, envelope, root=ROOT, path=""):
    """Dotted paths of the optional fields under a schema (array items written as name[])."""
    if "$ref" in schema:
        target, tdoc = Check(envelope, root).resolve(schema["$ref"], doc)
        return optional_paths(target or {}, tdoc, envelope, root, path)
    out = []
    if schema.get("type") == "object" or "properties" in schema:
        req = set(schema.get("required", []))
        for k, v in schema.get("properties", {}).items():
            p = join(path, k)
            if k not in req:
                out.append(p)
            out += optional_paths(v, doc, envelope, root, p)
    elif schema.get("type") == "array" and "items" in schema:
        out += optional_paths(schema["items"], doc, envelope, root, path + "[]")
    return out


def compact(value, indent=0, width=110):
    """JSON with short objects and arrays kept on one line."""
    one = json.dumps(value, ensure_ascii=False)
    if not isinstance(value, (dict, list)) or not value or len(one) + indent <= width:
        return one
    inner, pad = " " * (indent + 2), " " * indent
    if isinstance(value, dict):
        rows = [f"{inner}{json.dumps(k, ensure_ascii=False)}: {compact(v, indent + 2, width)}" for k, v in value.items()]
        return "{\n" + ",\n".join(rows) + "\n" + pad + "}"
    return "[\n" + ",\n".join(inner + compact(v, indent + 2, width) for v in value) + "\n" + pad + "]"


def spine_block(name, direct=False, root=ROOT):
    """What build.py writes between a spine's return markers."""
    envelope, con = envelope_schema(root), contract(name, root)
    opt = [p for p in optional_paths(envelope, envelope, envelope, root)
           if not p.startswith("body") and not (direct and p.split(".")[0] in ("unit", "gov", "ledger"))]
    opt = [p for p in opt if not p.startswith(("doubts[].", "ledger.")) or p in ("ledger.where", "ledger.next", "ledger.blocked_by")]
    opt += ["body." + p for p in optional_paths(con["returns_direct" if direct else "returns"], con, envelope, root)]
    opt = [p for p in opt if p not in ("gov", "body")]
    lines = ["```json", compact(template(name, direct, root=root)), "```", "",
             "Optional — drop it when it does not apply: " + ", ".join(f"`{p}`" for p in opt) + "."]
    return "\n".join(lines)


# ---------- contracts ---------------------------------------------------------------------------

def schema_problems(schema, doc, envelope, root=ROOT, path="", allow_open=False):
    """Why a schema breaks the subset or the house rules; [] when sound."""
    out = []
    if not isinstance(schema, dict):
        return [f"{path or '/'}: a schema must be an object"]
    unknown = set(schema) - SUBSET
    if unknown:
        out.append(f"{path or '/'}: unknown keyword(s) {sorted(unknown)}")
    if "$ref" in schema:
        if Check(envelope, root).resolve(schema["$ref"], doc)[0] is None:
            out.append(f"{path or '/'}: {schema['$ref']} resolves to nothing")
        elif schema.get("examples"):
            c = Check(envelope, root)
            c.run(schema["examples"][0], {"$ref": schema["$ref"]}, doc)
            out += [f"{path or '/'}: example {schema['examples'][0]!r} fails its reference: {m}" for _, m in c.misses]
        return out
    if schema.get("type") == "object" or "properties" in schema:
        ap = schema.get("additionalProperties")
        if ap is None or (ap is True and not allow_open):
            out.append(f"{path or '/'}: open object - set additionalProperties to false")
        for k in schema.get("required", []):
            if k not in schema.get("properties", {}):
                out.append(f"{path or '/'}: required '{k}' is not a property")
        for k, v in schema.get("properties", {}).items():
            out += schema_problems(v, doc, envelope, root, join(path, k), allow_open and k == "body")
    if "items" in schema:
        out += schema_problems(schema["items"], doc, envelope, root, path + "[]")
    for i, alt in enumerate(schema.get("anyOf", [])):
        out += schema_problems(alt, doc, envelope, root, f"{path}|{i}")
    if "enum" in schema and not schema["enum"]:
        out.append(f"{path or '/'}: empty enum")
    if "pattern" in schema:
        ex = schema.get("examples") or []
        if not ex:
            out.append(f"{path or '/'}: a pattern needs an example")
        elif not re.search(schema["pattern"], str(ex[0])):
            out.append(f"{path or '/'}: example {ex[0]!r} does not match its pattern")
    return out


def contract_problems(name, root=ROOT):
    """Why a suba's contract cannot be trusted; [] when its schemas are sound and its template coherent."""
    try:
        con = contract(name, root)
    except ValueError as e:
        return [f"contract.json is not valid JSON ({e})"]
    if con is None:
        return ["no contract.json"]
    envelope = envelope_schema(root)
    out = [f"unknown top-level key '{k}'" for k in con if k not in ("description", "returns", "returns_direct", "$defs")]
    if "returns" not in con:
        out.append("no 'returns' schema")
    for d, s in con.get("$defs", {}).items():
        out += [f"$defs.{d}{p}" for p in schema_problems(s, con, envelope, root)]
    for key in ("returns", "returns_direct"):
        if key not in con:
            continue
        problems = schema_problems(con[key], con, envelope, root)
        out += [f"{key}: {p}" for p in problems]
        if problems:
            continue
        direct = key == "returns_direct"
        misses, _ = check_envelope(template(name, direct, "filled", root), None, root)
        out += [f"{key}: the filled sample fails: {p} {m}" for p, m in misses]
        misses, _ = check_envelope(template(name, direct, "template", root), None, root)
        out += [f"{key}: the template fails beyond its placeholders: {p} {m}" for p, m in misses if "placeholder" not in m]
    return out


# ---------- the log -----------------------------------------------------------------------------

def record(vdir, rows):
    """Append envelope records to <virtual>/returns.jsonl, trimmed to the latest KEEP lines."""
    if not vdir or not rows:
        return
    p = Path(vdir) / LOG
    lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
    lines += [json.dumps(r, ensure_ascii=False) for r in rows]
    wire.atomic_write(p, "\n".join(lines[-KEEP:]) + "\n")


def read_log(vdir):
    p = Path(vdir) / LOG if vdir else None
    out = []
    for line in (p.read_text(encoding="utf-8").splitlines() if p and p.is_file() else []):
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def row(info, misses, agent=None, session=None):
    """One returns.jsonl line: the envelope's metadata, never its body."""
    return {"ts": wire.now(), "gen_ai.conversation.id": session, "gen_ai.agent.name": agent or "main",
            "regency.suba": info.get("suba"), "regency.via": info.get("via"), "regency.unit": info.get("unit"),
            "regency.terminal": info.get("terminal"), "regency.ask": info.get("ask"), "regency.keys": info.get("keys") or [],
            "regency.valid": not misses, "regency.misses": [f"{p}: {m}" for p, m in misses][:10]}


# ---------- CLI ---------------------------------------------------------------------------------

def report(label, found, owner_role=None):
    for field, msg in found:
        print(wire.one_line("RETURN", label, f"{field}: {msg}"))
    to = f" to {owner_role}" if owner_role else ""
    print(f"{label}: {len(found)} finding(s) -> RETURN{to}" if found else f"{label}: shape holds")
    return 1 if found else 0


def check_message(text, name=None, direct=None, root=ROOT):
    """[(label, misses, info)] for every envelope in a message (only NAME's when given)."""
    found, names = extract(text)
    out = []
    for env, error in found:
        if env is None:
            out.append(("envelope", [("(envelope)", error)], {}))
            continue
        misses, info = check_envelope(env, names, root)
        if name and env.get("suba") != name:
            continue
        if direct is not None and (env.get("via") == "direct") != direct:
            misses.append(("via", f"expected via={'direct' if direct else 'owner'}"))
        out.append((env.get("suba") or "envelope", misses, info))
    return out


def cli(argv):
    ap = argparse.ArgumentParser(prog="returns.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="check one return (file or - for stdin)")
    who = c.add_mutually_exclusive_group(required=True)
    who.add_argument("--stage", help="ROLE.STAGE, e.g. dv.build")
    who.add_argument("--suba", help="suba-<name>")
    c.add_argument("--direct", action="store_true", help="the suba was called as a command")
    c.add_argument("path")
    sub.add_parser("envelopes", help="check every envelope in a message").add_argument("path")
    t = sub.add_parser("template", help="print a suba's envelope template")
    t.add_argument("name")
    t.add_argument("--direct", action="store_true")
    s = sub.add_parser("show", help="the latest envelope records of this project")
    s.add_argument("--repo", default=".")
    s.add_argument("--unit")
    s.add_argument("-n", type=int, default=20)
    sub.add_parser("contracts", help="check every suba contract")
    sub.add_parser("stages", help="list the stage shapes")
    a = ap.parse_args(argv)
    try:
        data = load_shapes()
    except (OSError, ValueError) as e:
        print(f"returns.py: {e}", file=sys.stderr)
        return 2
    if a.cmd == "stages":
        for name, shape in data["stages"].items():
            print(wire.one_line(name, ", ".join(sorted(shape))))
        return 0
    if a.cmd == "contracts":
        bad = 0
        for d in sorted(p for p in (ROOT / SUBAGENTS).glob("suba-*") if p.is_dir()):
            problems = contract_problems(d.name)
            bad += bool(problems)
            print(wire.one_line(d.name, "contract holds" if not problems else f"{len(problems)} problem(s)", *problems[:3]))
        return 1 if bad else 0
    if a.cmd == "template":
        if contract(a.name) is None or (a.direct and "returns_direct" not in contract(a.name)):
            print(f"returns.py: no {'direct ' if a.direct else ''}contract for {a.name}", file=sys.stderr)
            return 2
        print(spine_block(a.name, a.direct))
        return 0
    if a.cmd == "show":
        rows = read_log(wire.virtual_dir(wire.repo_root(Path(a.repo).resolve())))
        rows = [r for r in rows if not a.unit or str(r.get("regency.unit") or "").startswith(a.unit)][-a.n:]
        for r in rows:
            state = "ok" if r.get("regency.valid") else f"{len(r.get('regency.misses', []))} miss(es)"
            print(wire.one_line(r.get("ts"), r.get("regency.suba"), r.get("regency.unit"), r.get("regency.terminal"), state,
                                ",".join(r.get("regency.keys") or []) or None, r.get("regency.ask")))
        print(f"{len(rows)} record(s)")
        return 0
    if a.cmd not in ("check", "envelopes"):
        ap.print_help()
        return 0
    text = sys.stdin.read() if a.path == "-" else Path(a.path).read_text(encoding="utf-8")
    if a.cmd == "check" and a.stage:
        shape = data["stages"].get(a.stage.lower())
        if shape is None:
            print(f"returns.py: no shape for stage {a.stage!r} (see `returns.py stages`)", file=sys.stderr)
            return 2
        return report(a.stage.lower(), check_stage(text, shape, data["terminal_states"]), a.stage.split(".")[0].upper())
    if a.cmd == "check" and contract(a.suba) is None:
        print(f"returns.py: {a.suba} has no contract.json", file=sys.stderr)
        return 2
    results = check_message(text, a.suba if a.cmd == "check" else None, a.direct if a.cmd == "check" else None)
    if not results:
        return report(a.suba or "message", [("envelope", "no envelope found (a ```json fence holding an object with envelope: 1)")])
    code = 0
    for label, misses, info in results:
        owner = None if info.get("via") == "direct" else info.get("owner")
        code |= report(label + (" (direct)" if info.get("via") == "direct" else ""), misses, owner)
    return code


# ---------- self-test ---------------------------------------------------------------------------

def selftest():
    data = load_shapes()
    st, states = data["stages"], data["terminal_states"]
    cases = [(set(st) >= {"po.frame", "po.accept", "dv.build", "qa.challenge", "qa.verify", "da.shape", "da.verify"},
              f"packets.md section 4 parses: {len(st)} stage shapes")]

    def fields(found):
        return {f for f, _ in found}

    # ---- role packets
    good_dv = ("gov: order=G1 · mode=self · element=action · from=DV · to=QA · unit=M03.D02.T04\nask: verify\n"
               "```yaml\nchange_notes:\n  touched_paths: [src/a.py]\n  touched_phases: [F2]\n  surface_changed: false\n"
               "  rollback: revert commit 1a2b3c\n  new_tests: [test_split]\n```\nSUCCESS built, probes green, handed to QA")
    cases.append((check_stage(good_dv, st["dv.build"], states) == [], "stage: a sound DV build passes"))
    bad = good_dv.replace("revert commit 1a2b3c", "<how to revert>")
    cases.append(("change-notes-rollback" in fields(check_stage(bad, st["dv.build"], states)), "stage: unfilled rollback"))
    bad = good_dv.replace("  new_tests: [test_split]", "  new_tests: [test_split]\n  why: the split is obviously right")
    cases.append(("change-notes-why" in fields(check_stage(bad, st["dv.build"], states)), "stage: a 'why' field is refused"))
    bad = good_dv.replace("```\nSUCCESS", "for_dv:\n  change_class: [feat]\n```\nSUCCESS")
    cases.append(("for-dv" in fields(check_stage(bad, st["dv.build"], states)), "stage: for_dv must not leave DV"))
    cases.append(("terminal-reason" in fields(check_stage(good_dv.replace("SUCCESS built, probes green, handed to QA", "SUCCESS"),
                                                          st["dv.build"], states)), "stage: a terminal state with no reason"))
    qa = ("## Risk opinion\n- Open defects: none above S3\n- **What was not covered:** concurrency\n"
          "Version verdict: compatible addition\nSUCCESS verdict and opinion issued, line signed")
    cases.append((check_stage(qa, st["qa.verify"], states) == [], "stage: a sound QA verify passes"))
    cases.append(("approved" in fields(check_stage(qa + "\nApproved.", st["qa.verify"], states)), "stage: bare 'approved'"))
    po = ("| | |\n|---|---|\n| **Problem** | split by centre |\n| **Acceptance criteria** | Given... |\n"
          "| **Out-of-scope** | exports |\n| **Span** | F1–F3 |\n| **Cited norm** | AR4 |\n| **Criticality** | high |\n"
          "| **Maximum tolerable severity** | S2 |\nSUCCESS story framed and handed to QA")
    cases.append((check_stage(po, st["po.frame"], states) == [], "stage: a sound PO story passes"))
    cases.append(("span" in fields(check_stage(po.replace("F1–F3", "whatever"), st["po.frame"], states)), "stage: a span with no phase"))

    # ---- the schema subset
    env = envelope_schema()
    doc = {"$defs": {"n": {"type": "integer", "minimum": 2}}}

    def run(value, schema):
        c = Check(env)
        c.run(value, schema, doc)
        return c

    cases.append((run(3, {"$ref": "#/$defs/n"}).misses == [] and run(1, {"$ref": "#/$defs/n"}).misses, "$ref to local $defs"))
    cases.append((run("M03.D02.T04", {"$ref": "ids:unit"}).misses == [] and run("M3", {"$ref": "ids:unit"}).misses,
                  "ids:unit comes from library/ids.md"))
    cases.append((run("QA", {"$ref": "gov:role"}).misses == [] and run("XX", {"$ref": "gov:role"}).misses, "gov:role from gov.py"))
    cases.append((run(True, {"type": "integer"}).misses and run(2, {"type": "integer"}).misses == [], "a boolean is not an integer"))
    cases.append(([p for p, _ in run({"a": 1, "b": 2}, {"type": "object", "properties": {"a": {}}, "additionalProperties": False})
                   .misses] == ["b"], "a closed object refuses an unknown field"))
    cases.append((any(m.startswith("unfilled placeholder") for _, m in run("<fill me>", {"type": "string"}).misses),
                  "a placeholder is refused"))
    cases.append((run("RGN-PO", {"$ref": "envelope#/$defs/decider"}).misses == []
                  and run("RGN-X", {"$ref": "envelope#/$defs/decider"}).misses, "anyOf: role or person label"))
    k = run(["contract-nullable", "Bad Key"], {"type": "array", "items": {"$ref": "gov:key"}})
    cases.append((k.keys == ["contract-nullable"] and len(k.misses) == 1, "only valid keys are collected"))

    # ---- envelopes
    imp = template("suba-implementer", mode="filled")
    m, info = check_envelope(imp)
    cases.append((m == [] and info["owner"] == "DV" and "contract-nullable" in info["keys"],
                  f"a filled implementer envelope passes and yields its keys: {m[:2]}"))

    def mutate(base, fn):
        e = json.loads(json.dumps(base))
        fn(e)
        return check_envelope(e)[0]

    def paths(misses):
        return {p for p, _ in misses}

    cases.append(("body.change_notes.rollback" in paths(mutate(imp, lambda e: e["body"]["change_notes"].update(rollback="<how>"))),
                  "envelope: unfilled rollback"))
    cases.append(("body.change_notes.why" in paths(mutate(imp, lambda e: e["body"]["change_notes"].update(why="trust me"))),
                  "envelope: a field the contract does not name is refused"))
    cases.append(("body.for_dv.change_class[0]" in paths(mutate(imp, lambda e: e["body"]["for_dv"].update(change_class=["vibes"]))),
                  "envelope: a value outside its enum"))
    cases.append(("body.change_notes.surface_changed" in paths(mutate(imp, lambda e: e["body"]["change_notes"].update(surface_changed="no"))),
                  "envelope: a string where a boolean belongs"))
    cases.append(("body.change_notes.new_tests" in paths(mutate(imp, lambda e: e["body"]["change_notes"].pop("new_tests"))),
                  "envelope: a missing field"))
    cases.append(("gov" in paths(mutate(imp, lambda e: e["gov"].update(to="QA"))), "envelope: past the owner is refused"))
    cases.append(("gov" in paths(mutate(imp, lambda e: e.pop("gov"))), "envelope: no gov block to the owner"))
    cases.append(("ledger.state" in paths(mutate(imp, lambda e: e["ledger"].update(state="done"))), "envelope: never 'done'"))
    cases.append(("ledger.blocked_by" in paths(mutate(imp, lambda e: (e["ledger"].update(state="blocked"), e["ledger"].pop("blocked_by")))),
                  "envelope: blocked needs blocked_by"))
    cases.append(("ledger.where" in paths(mutate(imp, lambda e: (e["ledger"].update(state="draft"), e["ledger"].pop("where", None)))),
                  "envelope: a draft needs where"))
    cases.append((not [q for q in paths(mutate(imp, lambda e: e["ledger"].update(state="draft", where=["branch:plumbing"])))
                       if q.startswith("ledger")], "envelope: a draft with where holds"))
    cases.append(("terminal.state" in paths(mutate(imp, lambda e: e["terminal"].update(state="DONE"))), "envelope: terminal from packets.md"))
    cases.append(("suba" in paths(mutate(imp, lambda e: e.update(suba="suba-ghost"))), "envelope: an unknown suba"))
    direct = template("suba-scribe", direct=True, mode="filled")
    cases.append((check_envelope(direct)[0] == [], "direct mode: the scribe's caller envelope passes"))
    cases.append(("gov" in paths(mutate(direct, lambda e: e.update(gov=dict(imp["gov"], **{"from": "DV", "to": "DV"})))),
                  "direct mode: no gov block"))
    cases.append(("via" in paths(mutate(imp, lambda e: e.update(via="direct"))), "direct mode: only for a suba that has one"))
    cases.append(("body.text" in paths(mutate(direct, lambda e: e.update(artefacts=[]))), "an artefact named but not listed"))
    msg = "Done.\n```json\n" + json.dumps(direct) + "\n```\n"
    res = check_message(msg)
    cases.append((res and "artefacts" in paths(res[0][1]), "a listed artefact with no ARTEFACT block"))
    msg2 = msg + "<<<ARTEFACT risk-opinion\n```json\n{\"envelope\": 1}\n```\nARTEFACT>>>\n"
    res = check_message(msg2)
    cases.append((len(res) == 1 and res[0][1] == [], "an ARTEFACT block delivers it, and its own json is not an envelope"))
    found, _ = extract("```json\n{\"envelope\": 1, \"suba\": \n```")
    cases.append((found and found[0][0] is None and "not valid JSON" in found[0][1], "a broken envelope is reported, exactly"))
    cases.append((field_key("suba-validator", "body.findings[2].key") == "return-validator-findings-key", "miss keys drop indices"))
    cases.append(("envelope" not in strip_envelopes(msg2.split("<<<")[0]) and "Done." in strip_envelopes(msg2),
                  "strip_envelopes removes envelopes and keeps the rest"))

    # ---- every contract: sound schema, satisfiable, coherent template
    names = sorted(p.name for p in (ROOT / SUBAGENTS).glob("suba-*") if p.is_dir())
    bad = {n: contract_problems(n) for n in names}
    cases.append((len(names) >= 13 and not any(bad.values()),
                  f"all {len(names)} contracts hold: {[(n, p[:1]) for n, p in bad.items() if p]}"))
    cases.append((schema_problems(env, env, env, allow_open=True) == [], "the envelope schema holds"))
    open_doc = {"returns": {"type": "object", "properties": {"x": {"type": "string", "pattern": "^a$"}}}}
    probs = schema_problems(open_doc["returns"], open_doc, env)
    cases.append((any("open object" in p for p in probs) and any("needs an example" in p for p in probs),
                  "house rules: closed objects, patterns carry an example"))
    block = spine_block("suba-implementer")
    cases.append((block.startswith("```json\n{") and "`gov.key`" in block and "<how to revert>" in block, "spine block renders"))
    with tempfile.TemporaryDirectory() as tmp:
        record(tmp, [row(info, [], "dv", "s1")])
        cases.append((read_log(tmp)[0]["regency.keys"] == info["keys"] and "body" not in json.dumps(read_log(tmp)[0]),
                      "the log keeps metadata, never the body"))
    return wire.check(cases)


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in args else cli(args))
