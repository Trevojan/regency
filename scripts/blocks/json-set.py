"""json-set - set one value at a dotted key path in a JSON file, keeping its layout.

The file is rewritten only when a standard layout (indent 2, 4, tab or compact) reproduces it byte for byte; a file
laid out by hand is refused, because a rewrite would reformat every line around the one value.
"""
import json
from pathlib import Path

CARD = {
    "id": "json-set",
    "intent": "set one value at a dotted key path in a JSON file (settings, manifests, package.json), keeping its "
              "layout; refuses a file laid out by hand",
    "when": ["set json key", "edit json", "update json value", "json field", "settings json", "change key in json",
             "add key to json", "append to json list"],
    "args": {
        "file": {"type": "path", "help": "the JSON file"},
        "key": {"type": "str", "help": "dotted path: permissions.allow, items.2.state; a number indexes a list, "
                                       "a final + appends to it"},
        "value": {"type": "str", "help": "JSON text (true, 3, [\"a\"], {\"k\": 1}); text that does not parse is a "
                                         "string"},
        "create": {"type": "bool", "default": False, "help": "create missing objects on the way"},
    },
    "confirm": "agent",
    "returns": "{file, key, before, after}",
}
LAYOUTS = (2, 4, "\t", None)


def layout(text, data):
    for indent in LAYOUTS:
        for ascii_only in (False, True):
            out = json.dumps(data, indent=indent, ensure_ascii=ascii_only)
            for end in ("\n", ""):
                if out + end == text:
                    return indent, ascii_only, end
    return None


def parse_value(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def run(a, root):
    path = Path(root) / a["file"]
    if not path.is_file():
        raise ValueError(f"{a['file']} does not exist")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except ValueError as e:
        raise ValueError(f"{a['file']} is not valid JSON ({e})")
    form = layout(text, data)
    if form is None:
        raise ValueError(f"{a['file']} is laid out by hand; a rewrite would reformat it - edit it with the Edit tool")
    parts = a["key"].split(".")
    if not all(parts):
        raise ValueError(f"key {a['key']!r} has an empty part")
    node = data
    for i, part in enumerate(parts[:-1]):
        node = step(node, part, a["create"], ".".join(parts[:i + 1]))
    last, value = parts[-1], parse_value(a["value"])
    if isinstance(node, list):
        if last == "+":
            before = None
            node.append(value)
        else:
            idx = index(node, last, a["key"])
            before, node[idx] = node[idx], value
    elif isinstance(node, dict):
        if last == "+":
            raise ValueError(f"{a['key']}: + appends to a list, and this is an object")
        before = node.get(last)
        if last in node and type(before) is type(value) and before == value:
            return {"summary": f"{a['file']}: {a['key']} already holds that value", "result": {
                "file": a["file"], "key": a["key"], "before": before, "after": value}}
        node[last] = value
    else:
        raise ValueError(f"{a['key']}: the parent is not an object or a list")
    indent, ascii_only, end = form
    out = json.dumps(data, indent=indent, ensure_ascii=ascii_only) + end
    return {"summary": f"{a['file']}: {a['key']} = {json.dumps(value)}",
            "result": {"file": a["file"], "key": a["key"], "before": before, "after": value},
            "writes": [{"path": a["file"], "text": out, "detail": f"{a['key']}: {json.dumps(before)} -> "
                                                                 f"{json.dumps(value)}"}]}


def index(node, part, key):
    if not part.lstrip("-").isdigit() or not -len(node) <= int(part) < len(node):
        raise ValueError(f"{key}: {part!r} is not an index of a list of {len(node)}")
    return int(part)


def step(node, part, create, where):
    if isinstance(node, list):
        return node[index(node, part, where)]
    if not isinstance(node, dict):
        raise ValueError(f"{where}: not an object or a list")
    if part not in node:
        if not create:
            raise ValueError(f"{where} does not exist; pass create=yes to create it")
        node[part] = {}
    return node[part]


def selftest(tmp):
    def refuses(args):
        try:
            run(args, str(tmp))
        except ValueError:
            return True
        return False

    f = tmp / "s.json"
    f.write_text(json.dumps({"a": {"b": 1}, "items": [{"state": "x"}], "allow": []}, indent=2) + "\n", encoding="utf-8")
    base = {"file": "s.json", "create": False}
    out = run(dict(base, key="a.b", value="3"), str(tmp))
    assert json.loads(out["writes"][0]["text"])["a"]["b"] == 3 and out["writes"][0]["text"].endswith("}\n")
    assert json.loads(run(dict(base, key="items.0.state", value="done"), str(tmp))["writes"][0]["text"]
                      )["items"][0]["state"] == "done", "a plain word is a string"
    assert json.loads(run(dict(base, key="allow.+", value='"Bash(ls)"'), str(tmp))["writes"][0]["text"]
                      )["allow"] == ["Bash(ls)"]
    assert "writes" not in run(dict(base, key="a.b", value="1"), str(tmp)), "an equal value writes nothing"
    assert refuses(dict(base, key="x.y", value="1")), "a missing parent needs create=yes"
    assert json.loads(run(dict(base, key="x.y", value="1", create=True), str(tmp))["writes"][0]["text"])["x"] == {"y": 1}
    assert refuses(dict(base, key="items.5.state", value="1")) and refuses(dict(base, key="a..b", value="1"))
    (tmp / "h.json").write_text('{"a": 1,\n   "b": [1,2]}\n', encoding="utf-8")
    assert refuses({"file": "h.json", "key": "a", "value": "2", "create": False}), "a hand layout is refused"
    (tmp / "t.json").write_text(json.dumps({"k": "é"}, indent="\t"), encoding="utf-8")
    assert run({"file": "t.json", "key": "k", "value": "2", "create": False}, str(tmp))["writes"][0]["text"] == \
        json.dumps({"k": 2}, indent="\t"), "tab layout, no final newline, kept"
