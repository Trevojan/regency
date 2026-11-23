"""version-bump - bump or set a version by the Regent's two schemes, in every file that carries it, layout kept.

v1  a.b.c.dd+e, projects (conventions V1): a release (+a) resets b, c and dd; +b, +c, +dd reset nothing; e never
    resets. <AssemblyVersion> and <FileVersion> take a.b.c.dd, each part at most 65535 (C-V1).
ab  a.b, regency itself (conventions section 13): +a resets b; +b is a content change.
A JSON file carries it in its top-level "version"; a .csproj/.props/.targets/.xml in its <Version>-style tags.
"""
import json
import re
from pathlib import Path

CARD = {
    "id": "version-bump",
    "intent": "bump or set a version by the Regent's schemes (V1 a.b.c.dd+e for projects, a.b for regency) in "
              "every file that carries it",
    "when": ["bump version", "version bump", "new version", "release version", "increment version", "set version",
             "csproj version", "plugin version", "registry version"],
    "args": {
        "files": {"type": "paths", "help": "comma-separated files that carry the version"},
        "scheme": {"type": "str", "choices": ["v1", "ab"], "help": "v1 = a.b.c.dd+e; ab = regency's a.b"},
        "part": {"type": "str", "default": "", "choices": ["", "a", "b", "c", "dd", "e"],
                 "help": "the position to bump"},
        "set": {"type": "str", "default": "", "help": "an exact version instead of a bump, e.g. off 0.1.0"},
    },
    "confirm": "agent",
    "regent_if": {"part": ["a"], "set": ["*"]},
    "returns": "{from, to, files}",
}
SHAPE = {"v1": re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\+(\d+)$"), "ab": re.compile(r"^(\d+)\.(\d+)$")}
JSON_KEY = re.compile(r'("version"\s*:\s*")([^"]*)(")')
TAGS = re.compile(r"(<(Version|InformationalVersion|AssemblyVersion|FileVersion)>)([^<]*)(</\2>)")
NUMERIC = {"AssemblyVersion", "FileVersion"}
DOTNET_CAP = 65535


def bump(scheme, version, part):
    m = SHAPE[scheme].match(version)
    if not m:
        raise ValueError(f"{version!r} is not {'a.b.c.dd+e' if scheme == 'v1' else 'a.b'}; pass set=<version> once")
    g = list(m.groups())
    if scheme == "ab":
        if part not in ("a", "b"):
            raise ValueError("scheme ab has parts a and b only")
        a, b = int(g[0]), int(g[1])
        return f"{a + 1}.0" if part == "a" else f"{a}.{b + 1}"
    a, b, c, dd, e = g
    if part == "a":
        return f"{int(a) + 1}.0.0.{'0' * len(dd)}+{e}"
    keep = {"b": 1, "c": 2, "dd": 3, "e": 4}[part]
    g[keep] = str(int(g[keep]) + 1).zfill(len(g[keep]))
    return f"{g[0]}.{g[1]}.{g[2]}.{g[3]}+{g[4]}"


def numeric(version):
    return version.split("+", 1)[0]


def current(path, text):
    if path.suffix.lower() == ".json":
        try:
            v = json.loads(text).get("version")
        except (ValueError, AttributeError):
            raise ValueError(f"{path.name}: not a JSON object")
        if not isinstance(v, str):
            raise ValueError(f"{path.name}: no top-level \"version\" string")
        return v
    full = [m.group(3) for m in TAGS.finditer(text) if m.group(2) not in NUMERIC]
    if not full:
        raise ValueError(f"{path.name}: neither a JSON \"version\" nor a <Version>/<InformationalVersion> tag")
    if len(set(full)) > 1:
        raise ValueError(f"{path.name}: its version tags disagree: {', '.join(sorted(set(full)))}")
    return full[0]


def rewrite(path, text, old, new):
    if path.suffix.lower() == ".json":
        hits = [m for m in JSON_KEY.finditer(text) if m.group(2) == old]
        if len(hits) != 1:
            raise ValueError(f"{path.name}: \"version\": \"{old}\" appears {len(hits)} times; edit it by hand")
        m = hits[0]
        out = text[:m.start(2)] + new + text[m.end(2):]
        before, after = json.loads(text), json.loads(out)
        before["version"] = new
        if before != after:
            raise ValueError(f"{path.name}: the rewrite touched more than the top-level version")
        return out

    def one(m):
        want = numeric(old) if m.group(2) in NUMERIC else old
        if m.group(3) != want:
            raise ValueError(f"{path.name}: <{m.group(2)}> holds {m.group(3)!r}, expected {want!r}")
        value = numeric(new) if m.group(2) in NUMERIC else new
        if m.group(2) in NUMERIC and any(int(x) > DOTNET_CAP for x in value.split(".")):
            raise ValueError(f"{path.name}: <{m.group(2)}> {value} passes .NET's {DOTNET_CAP} per part")
        return m.group(1) + value + m.group(4)
    return TAGS.sub(one, text)


def run(a, root):
    if bool(a["part"]) == bool(a["set"]):
        raise ValueError("give exactly one of part=<a|b|c|dd|e> or set=<version>")
    if not a["files"]:
        raise ValueError("files is empty")
    texts = {}
    for f in a["files"]:
        p = Path(root) / f
        if not p.is_file():
            raise ValueError(f"{f} does not exist")
        texts[f] = p.read_text(encoding="utf-8")
    olds = {f: current(Path(f), t) for f, t in texts.items()}
    if a["set"]:
        if not SHAPE[a["scheme"]].match(a["set"]):
            raise ValueError(f"set={a['set']!r} does not fit scheme {a['scheme']}")
        new = a["set"]
    else:
        if len(set(olds.values())) > 1:
            raise ValueError("the files disagree: " + ", ".join(f"{f}={v}" for f, v in olds.items()))
        new = bump(a["scheme"], next(iter(olds.values())), a["part"])
    writes = [{"path": f, "text": rewrite(Path(f), texts[f], olds[f], new), "detail": f"version {olds[f]} -> {new}"}
              for f in texts if olds[f] != new]
    old = ", ".join(sorted(set(olds.values())))
    how = f"set {new}" if a["set"] else f"part {a['part']}"
    return {"summary": f"{old} -> {new} ({a['scheme']}, {how}) in {len(writes)} file(s)",
            "result": {"from": old, "to": new, "files": [w["path"] for w in writes]}, "writes": writes}


def selftest(tmp):
    def refuses(args):
        try:
            run(args, str(tmp))
        except ValueError:
            return True
        return False

    plugin = '{\n  "name": "x",\n  "version": "3.3",\n  "nested": {"version": "9"}\n}\n'
    registry = '{"plugin": "x", "version": "3.3",\n "commands": [ {"id": "a", "version": "3.3x"} ]}\n'
    (tmp / "plugin.json").write_text(plugin, encoding="utf-8")
    (tmp / "registry.json").write_text(registry, encoding="utf-8")
    ab = {"files": ["plugin.json", "registry.json"], "scheme": "ab", "part": "b", "set": ""}
    out = run(ab, str(tmp))
    assert out["result"]["to"] == "3.4" and len(out["writes"]) == 2, out["summary"]
    assert out["writes"][1]["text"] == registry.replace('"version": "3.3"', '"version": "3.4"'), "layout kept"
    assert run(dict(ab, part="a"), str(tmp))["result"]["to"] == "4.0"
    assert refuses(dict(ab, part="c")), "ab has no part c"
    assert refuses(dict(ab, part="", set="")) and refuses(dict(ab, set="3.9")), "exactly one of part or set"
    (tmp / "other.json").write_text('{"version": "2.0"}', encoding="utf-8")
    assert refuses(dict(ab, files=["plugin.json", "other.json"])), "files that disagree are refused"

    proj = "<Project><PropertyGroup><Version>1.2.3.09+17</Version><AssemblyVersion>1.2.3.09</AssemblyVersion>" \
           "<FileVersion>1.2.3.09</FileVersion></PropertyGroup></Project>\n"
    (tmp / "App.csproj").write_text(proj, encoding="utf-8")
    v1 = {"files": ["App.csproj"], "scheme": "v1", "part": "dd", "set": ""}
    text = run(v1, str(tmp))["writes"][0]["text"]
    assert "<Version>1.2.3.10+17</Version>" in text and "<AssemblyVersion>1.2.3.10</AssemblyVersion>" in text, text
    assert run(dict(v1, part="a"), str(tmp))["result"]["to"] == "2.0.0.00+17", "a release resets b, c, dd, keeps e"
    assert run(dict(v1, part="b"), str(tmp))["result"]["to"] == "1.3.3.09+17", "+b resets nothing"
    assert run(dict(v1, part="e"), str(tmp))["result"]["to"] == "1.2.3.09+18"
    (tmp / "Old.props").write_text("<Project><PropertyGroup><Version>0.1.0</Version></PropertyGroup></Project>",
                                   encoding="utf-8")
    old = dict(v1, files=["Old.props"])
    assert refuses(old), "a non-conforming version needs set="
    assert run(dict(old, part="", set="0.1.0.0+1"), str(tmp))["result"]["to"] == "0.1.0.0+1"
    assert refuses(dict(v1, part="", set="70000.0.0.0+1")), ".NET cap on AssemblyVersion"
