#!/usr/bin/env python3
"""packs.py - domain packs: what regency becomes in one domain, adopted as they are or written native.

A pack is a folder holding pack.json (its manifest) and its files. Two layers (the Regent, 2026-10-29):

  public   <regency>/packs/<id>/          shipped with regency; an open-source license is required
  project  <guidelines>/.packs/<id>/      travels with that project's repository

A project pack with the id of a public pack shadows it in that project. Claude Code loads plugins once per
install and never per project, so regency reads packs itself while it runs: the /regency:pack playbook opens a
pack's playbooks as files, and scripts/hook-packs.py runs a pack's hooks only where the pack is active.

Activation and consent belong to the project, never to the pack: <guidelines>/.packs/active.json

  {"schema": 1, "packs": {"<id>": {"layer": "project", "since": "YYYY-MM-DD",
                                   "ratified": {"<item key>": {"tree": "<sha12>", "on": "YYYY-MM-DD"}}}}}

A hook item runs only in a project where its pack is active and the item was ratified at the pack's current tree
fingerprint: any change to any file of the pack makes it STALE until the Regent ratifies it again.

Run
  python scripts/packs.py list [--repo DIR]
  python scripts/packs.py show <id> [<item key>] [--repo DIR]
  python scripts/packs.py adopt <dir | git url> --id ID --layer public|project [--when GLOBS] [--repo DIR] [--yes]
  python scripts/packs.py check [--repo DIR]
  python scripts/packs.py suggest [--repo DIR]
  python scripts/packs.py activate <id> [--repo DIR] [--yes]
  python scripts/packs.py deactivate <id> [--repo DIR] [--yes]
  python scripts/packs.py ratify <id> <item key | hooks | all> [--repo DIR] [--yes]
  python scripts/packs.py mcp <id> [--repo DIR] [--write --yes]
  python scripts/packs.py --selftest

Without --yes every writing command prints its plan and writes nothing. Pure standard library, Python 3.8+.
"""
import datetime
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = "packs"
PROJECT = ".packs"
ACTIVE = "active.json"
MANIFEST = "pack.json"
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKIP = {".git", "__pycache__", ".DS_Store", "Thumbs.db"}
DISPATCHED = ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "SessionEnd")
REFUSED_EVENTS = {"Stop": "R4.5: regency wires no Stop hook",
                  "SubagentStop": "a hook that can keep an agent from stopping (R4.5)"}
KINDS = ("playbook", "command", "agent", "hook", "mcp")
IF_FORM = re.compile(r"^([A-Za-z]+)\((.*)\)$")
OPEN_LICENSES = {  # SPDX id -> a phrase its text carries
    "MIT": "permission is hereby granted, free of charge", "Apache-2.0": "apache license",
    "BSD-3-Clause": "neither the name of", "BSD-2-Clause": "redistribution and use in source and binary forms",
    "ISC": "permission to use, copy, modify, and/or distribute", "MPL-2.0": "mozilla public license",
    "LGPL-3.0": "gnu lesser general public license", "GPL-3.0": "gnu general public license",
    "AGPL-3.0": "gnu affero general public license", "Unlicense": "this is free and unencumbered software",
    "CC0-1.0": "cc0 1.0 universal",
}
COPYLEFT = {"GPL-3.0", "AGPL-3.0", "LGPL-3.0", "MPL-2.0"}
INTERPRETERS = {".js": "node", ".mjs": "node", ".cjs": "node", ".ts": "node", ".py": "python", ".sh": "bash",
                ".ps1": "pwsh", ".rb": "ruby"}
LAUNCHERS = {"node", "npx", "bun", "bunx", "deno", "python", "python3", "uv", "uvx", "bash", "sh", "pwsh", "ruby"}


def today():
    return datetime.date.today().isoformat()


# ---------- reading ----------------------------------------------------------------------------------

def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def frontmatter(text):
    m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if k:
            out[k.group(1)] = k.group(2).strip().strip('"').strip("'")
    return out


def walk(base):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
        for f in sorted(filenames):
            if f not in SKIP:
                yield Path(dirpath) / f


def tree_sha(base):
    """12 hex of every file under the pack (relative path and content): the fingerprint consent is given to."""
    h = hashlib.sha256()
    base = Path(base)
    for p in walk(base):
        h.update(p.relative_to(base).as_posix().encode("utf-8") + b"\0")
        h.update(wire.sha256(p).encode("ascii") + b"\n")
    return h.hexdigest()[:12]


def stat_sig(base):
    """A cheap signature of the tree's file stats: when it holds, the cached tree_sha holds. The change time joins
    size and mtime on POSIX (no user tool sets it back), so restoring a file's mtime does not hide an edit."""
    h = hashlib.sha256()
    base = Path(base)
    for p in walk(base):
        st = p.stat()
        ctime = st.st_ctime_ns if os.name != "nt" else 0
        h.update(f"{p.relative_to(base).as_posix()}\0{st.st_size}\0{st.st_mtime_ns}\0{ctime}\n".encode("utf-8"))
    return h.hexdigest()[:16]


def tree_sha_cached(base):
    """tree_sha, re-hashed only when a file's size or mtime moved (the dispatcher runs on every tool call)."""
    try:
        cache_dir = wire.state_dir().parent / "packs"
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(str(Path(base).resolve()).encode("utf-8")).hexdigest()[:16]
        cache = cache_dir / f"tree-{key}.json"
        sig = stat_sig(base)
        held = load_json(cache) or {}
        if held.get("sig") == sig and held.get("tree"):
            return held["tree"]
        tree = tree_sha(base)
        wire.atomic_write(cache, json.dumps({"sig": sig, "tree": tree}))
        return tree
    except OSError:  # health: allow-silent a cache that cannot be written only costs a full hash
        return tree_sha(base)


# ---------- layers and discovery -----------------------------------------------------------------------

def project_dir(repo):
    g = wire.guidelines_root(repo) if repo else None
    return g / PROJECT if g else None


def layer_dirs(repo, root=ROOT):
    out = [("public", Path(root) / PUBLIC)]
    p = project_dir(repo)
    if p:
        out.append(("project", p))
    return out


class Pack:
    def __init__(self, layer, path, manifest):
        self.layer, self.path, self.m = layer, Path(path), manifest or {}
        self.id = self.m.get("id") or self.path.name
        self.shadows = None

    @property
    def plugin_root(self):
        """Where ${CLAUDE_PLUGIN_ROOT} points for this pack: the adopted upstream, or the pack folder."""
        r = self.m.get("root")
        return self.path / r if r else self.path

    def items(self):
        return [i for i in self.m.get("items", []) if isinstance(i, dict)]

    def item(self, key):
        return next((i for i in self.items() if i.get("key") == key), None)


def discover(repo=None, root=ROOT):
    """{id: Pack} over both layers; a project pack shadows the public one with its id."""
    found = {}
    for layer, d in layer_dirs(repo, root):
        if not d.is_dir():
            continue
        for sub in sorted(x for x in d.iterdir() if x.is_dir()):
            pk = Pack(layer, sub, load_json(sub / MANIFEST))
            if pk.id in found:
                pk.shadows = found[pk.id]
            found[pk.id] = pk
    return found


def load_active(repo):
    p = project_dir(repo)
    data = load_json(p / ACTIVE) if p else None
    if not isinstance(data, dict) or not isinstance(data.get("packs"), dict):
        return {"schema": 1, "packs": {}}
    return data


def save_active(repo, data):
    p = project_dir(repo)
    p.mkdir(parents=True, exist_ok=True)
    wire.atomic_write(p / ACTIVE, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def item_state(pk, entry, key, tree=None):
    """'ratified', 'stale' (ratified at another tree) or 'proposal' for one item in one project."""
    r = ((entry or {}).get("ratified") or {}).get(key)
    if not r:
        return "proposal"
    return "ratified" if r.get("tree") == (tree or tree_sha(pk.path)) else "stale"


# ---------- license --------------------------------------------------------------------------------------

def license_of(src, manifest):
    """(spdx or None, evidence): the manifest's license field, else the text of a LICENSE or COPYING file."""
    declared = str((manifest or {}).get("license") or "").strip()
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING", "COPYING.md"):
        p = Path(src) / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace").lower()
            for spdx, phrase in OPEN_LICENSES.items():
                if phrase in text and not (spdx == "GPL-3.0" and ("lesser" in text or "affero" in text)):
                    return spdx, name
            return (declared or None), name
    return (declared or None), ("plugin.json" if declared else None)


# ---------- adoption: an incoming plugin or skill, inventoried as it is -----------------------------------

def as_list(v):
    return v if isinstance(v, list) else ([] if v is None else [v])


def rel_inside(base, rel):
    """The resolved path of a manifest path inside base, or None when it escapes or is missing."""
    if not isinstance(rel, str):
        return None
    p = (Path(base) / rel).resolve()
    try:
        p.relative_to(Path(base).resolve())
    except ValueError:
        return None
    return p if p.exists() else None


def skill_dirs(src, manifest):
    """Directories holding SKILL.md: skills/<name>/, the manifest's skills paths, or the root itself."""
    roots = [Path(src) / "skills"] + [rel_inside(src, r) for r in as_list((manifest or {}).get("skills"))]
    found = []
    for r in roots:
        if not r or not r.is_dir():
            continue
        if (r / "SKILL.md").is_file():
            found.append(r)
        found += sorted(d for d in r.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
    if not found and (Path(src) / "SKILL.md").is_file() and not (Path(src) / "skills").is_dir():
        found.append(Path(src))
    seen, out = set(), []
    for d in found:
        if d.resolve() not in seen:
            seen.add(d.resolve())
            out.append(d)
    return out


def hook_files(src, manifest):
    """[(origin, hooks map)] from hooks/hooks.json and the manifest's hooks (paths or inline)."""
    out = []
    default = Path(src) / "hooks" / "hooks.json"
    if default.is_file():
        out.append(("hooks/hooks.json", (load_json(default) or {}).get("hooks") or {}))
    for h in as_list((manifest or {}).get("hooks")):
        if isinstance(h, dict):
            out.append(("plugin.json (inline)", h))
        else:
            p = rel_inside(src, h)
            if p and p.is_file() and p != default.resolve():
                out.append((p.relative_to(Path(src).resolve()).as_posix(), (load_json(p) or {}).get("hooks") or {}))
    return out


def mcp_servers(src, manifest):
    out = {}
    d = Path(src) / ".mcp.json"
    if d.is_file():
        data = load_json(d) or {}
        out.update(data.get("mcpServers", data) if isinstance(data, dict) else {})
    for m in as_list((manifest or {}).get("mcpServers")):
        if isinstance(m, dict):
            out.update(m)
        elif isinstance(m, str) and m.endswith(".json"):
            p = rel_inside(src, m)
            data = (load_json(p) or {}) if p else {}
            out.update(data.get("mcpServers", data) if isinstance(data, dict) else {})
    return {k: v for k, v in out.items() if isinstance(v, dict)}


def inventory(src, root="upstream"):
    """What an incoming plugin or skill holds, mapped to pack items: (meta, items, unsupported, requires)."""
    src = Path(src)
    manifest = load_json(src / ".claude-plugin" / "plugin.json") or {}
    pre = f"{root}/" if root else ""
    items, unsupported = [], []

    def rel(p):
        return pre + Path(p).resolve().relative_to(src.resolve()).as_posix()

    for d in skill_dirs(src, manifest):
        fm = frontmatter((d / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
        name = fm.get("name") or d.name
        items.append({"key": f"playbook:{name}", "kind": "playbook", "name": name, "path": rel(d / "SKILL.md"),
                      "summary": fm.get("description", "")[:300]})

    cmd_spec = manifest.get("commands")
    cmd_files = []
    if isinstance(cmd_spec, dict):
        for name, v in cmd_spec.items():
            if isinstance(v, dict) and v.get("source"):
                p = rel_inside(src, v["source"])
                if p:
                    cmd_files.append((name, p, v.get("description", "")))
            elif isinstance(v, dict) and "content" in v:
                unsupported.append({"what": f"command {name}", "path": "plugin.json",
                                    "why": "an inline command body; write it to a file to adopt it"})
    else:
        paths = [rel_inside(src, c) for c in as_list(cmd_spec)] if cmd_spec else [src / "commands"]
        for p in paths:
            if p and p.is_dir():
                cmd_files += [(f.relative_to(p).with_suffix("").as_posix().replace("/", ":"), f, "")
                              for f in sorted(p.rglob("*.md"))]
            elif p and p.is_file():
                cmd_files.append((p.stem, p, ""))
    for name, p, desc in cmd_files:
        fm = frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        items.append({"key": f"command:{name}", "kind": "command", "name": name, "path": rel(p),
                      "summary": (desc or fm.get("description", ""))[:300]})

    agent_paths = [rel_inside(src, a) for a in as_list(manifest.get("agents"))] if manifest.get("agents") else \
        sorted((src / "agents").rglob("*.md")) if (src / "agents").is_dir() else []
    for p in agent_paths:
        if p and p.is_file():
            fm = frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            name = fm.get("name") or p.stem
            items.append({"key": f"agent:{name}", "kind": "agent", "name": name, "path": rel(p),
                          "summary": fm.get("description", "")[:300]})

    counters = {}
    for origin, hooks in hook_files(src, manifest):
        for event, groups in (hooks or {}).items():
            for g in as_list(groups):
                if not isinstance(g, dict):
                    continue
                for h in as_list(g.get("hooks")):
                    if not isinstance(h, dict):
                        continue
                    where = f"{origin} {event}[{g.get('matcher', '')}]"
                    why = None
                    if event in REFUSED_EVENTS:
                        why = REFUSED_EVENTS[event]
                    elif event not in DISPATCHED:
                        why = f"{event} is not dispatched in this version (dispatched: {', '.join(DISPATCHED)})"
                    elif h.get("type", "command") != "command":
                        why = f"a '{h.get('type')}' hook; only command hooks are dispatched"
                    elif "${user_config." in json.dumps(h):
                        why = "reads ${user_config.*}, which regency does not prompt for"
                    elif h.get("if") and not IF_FORM.match(str(h.get("if"))):
                        why = f"an 'if' filter regency cannot read: {h.get('if')}"
                    if why:
                        unsupported.append({"what": f"hook {event}", "path": where, "why": why})
                        continue
                    n = counters.get(event, 0)
                    counters[event] = n + 1
                    item = {"key": f"hook:{event}:{n}", "kind": "hook", "event": event,
                            "matcher": g.get("matcher", ""), "command": h.get("command", ""),
                            "timeout": h.get("timeout", 60), "async": bool(h.get("async", False)), "origin": where}
                    if isinstance(h.get("args"), list):
                        item["args"] = h["args"]
                    if h.get("if"):
                        item["if"] = h["if"]
                    items.append(item)

    for name, cfg in sorted(mcp_servers(src, manifest).items()):
        items.append({"key": f"mcp:{name}", "kind": "mcp", "name": name, "config": cfg})

    for what, paths, why in (
            ("LSP servers", [".lsp.json"] + ([manifest["lspServers"]] if isinstance(manifest.get("lspServers"), str) else []),
             "loaded only by an installed plugin"),
            ("output styles", ["output-styles"], "loaded only by an installed plugin"),
            ("workflows", ["workflows"], "loaded only by an installed plugin"),
            ("themes", ["themes"], "loaded only by an installed plugin"),
            ("monitors", ["monitors/monitors.json"], "loaded only by an installed plugin"),
            ("settings", ["settings.json"], "plugin settings (agent, status line) apply only to an installed plugin"),
            ("executables", ["bin"], "put on PATH only by an installed plugin; the pack's playbooks call them by path")):
        for pth in paths:
            if (src / pth).exists():
                unsupported.append({"what": what, "path": pth, "why": why})
    for key in ("lspServers", "userConfig", "channels", "outputStyles", "workflows", "experimental", "settings"):
        if manifest.get(key) and not any(u["path"] == "plugin.json" and u["what"] == key for u in unsupported):
            unsupported.append({"what": key, "path": "plugin.json", "why": "declared in the manifest; not adopted in this version"})
    for dep in as_list(manifest.get("dependencies")):
        unsupported.append({"what": "dependency", "path": "plugin.json",
                            "why": f"needs the plugin {dep if isinstance(dep, str) else dep.get('name')}: adopt it too"})

    requires = {}
    for p in walk(src):
        tool = INTERPRETERS.get(p.suffix.lower())
        if tool and tool not in requires:
            requires[tool] = rel(p)
    for i in items:
        for word in re.findall(r"[A-Za-z0-9_.-]+", " ".join([str(i.get("command", ""))] + [str(a) for a in i.get("args", [])])
                               + " " + str((i.get("config") or {}).get("command", ""))):
            if word in LAUNCHERS:
                tool = "python" if word.startswith("python") else word
                requires.setdefault(tool, i["key"])
    meta = {"name": manifest.get("name") or src.name, "version": manifest.get("version"),
            "description": manifest.get("description") or next((i["summary"] for i in items if i["kind"] == "playbook"), ""),
            "from": "plugin" if (src / ".claude-plugin" / "plugin.json").is_file() or (src / "hooks").is_dir() else "skill",
            "manifest": manifest}
    return meta, items, unsupported, [{"tool": t, "why": w} for t, w in sorted(requires.items())]


def clone(url, into):
    r = subprocess.run(["git", "clone", "--depth", "1", url, str(into)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git clone failed: {(r.stderr or r.stdout).strip()[:300]}")
    def g(*a):
        return subprocess.run(["git", "-C", str(into), *a], capture_output=True, text=True).stdout.strip()
    return {"repository": url, "ref": g("rev-parse", "--abbrev-ref", "HEAD"), "sha": g("rev-parse", "HEAD")}


def adopt(source, pid, layer, repo=None, yes=False, when=None, root=ROOT):
    """(code, lines). Copies the source verbatim under <layer>/<id>/upstream and writes pack.json."""
    lines = []
    if not ID.match(pid or ""):
        return 1, [f"FAIL  pack id {pid!r} is not kebab-case"]
    if layer not in ("public", "project"):
        return 1, [f"FAIL  layer {layer!r}: choose public or project"]
    if layer == "public":
        dest_root = Path(root) / PUBLIC
    else:
        dest_root = project_dir(repo)
        if dest_root is None:
            return 1, ["FAIL  this project has no guidelines root: run /regency:init first (library/layouts.md §1)"]
    dest = dest_root / pid
    if dest.exists():
        return 1, [f"FAIL  {dest} exists: a pack is adopted once (re-adoption with a diff is on the roadmap)"]
    tmp = None
    origin = {"repository": None, "ref": None, "sha": None}
    src = Path(source)
    try:
        if re.match(r"^(https://|git@|ssh://|file://)", str(source)):
            tmp = tempfile.mkdtemp(prefix="regency-adopt-")
            origin = clone(source, Path(tmp) / "src")
            src = Path(tmp) / "src"
        if not src.is_dir():
            return 1, [f"FAIL  {source}: not a folder or a git url"]
        meta, items, unsupported, requires = inventory(src)
        spdx, evidence = license_of(src, meta["manifest"])
        if not items:
            return 1, [f"FAIL  {source}: no skill, command, agent, hook or MCP server found (is it a Claude Code plugin or skill?)"]
        if layer == "public" and spdx not in OPEN_LICENSES:
            return 1, [f"FAIL  the public layer ships with regency's repository: {meta['name']} needs an open-source "
                       f"license regency can redistribute; found {spdx or 'none'} ({evidence or 'no LICENSE file'}). "
                       "Adopt it into the project layer instead."]
        lines.append(f"adopt {meta['name']} ({meta['from']}{', ' + str(meta['version']) if meta['version'] else ''}) "
                     f"-> {layer} pack '{pid}' at {dest}")
        lines.append(f"license: {spdx or 'none declared'}" + (f" ({evidence})" if evidence else "")
                     + (" · copyleft: the pack stays under its own license" if spdx in COPYLEFT else ""))
        for kind in KINDS:
            names = [i["key"].split(":", 1)[1] for i in items if i["kind"] == kind]
            if names:
                lines.append(f"  {kind:<8} {len(names):>3}  {', '.join(names[:8])}{' …' if len(names) > 8 else ''}")
        for u in unsupported:
            lines.append(f"  not adopted: {u['what']} ({u['path']}): {u['why']}")
        if requires:
            lines.append("requires: " + ", ".join(f"{r['tool']} ({r['why']})" for r in requires))
        hooks = [i for i in items if i["kind"] == "hook"]
        if hooks:
            lines.append(f"{len(hooks)} hook(s) adopted: none runs until the pack is active in a project and the Regent "
                         "ratifies it there (packs.py ratify)")
        if not yes:
            lines.append("plan only: nothing written. Run again with --yes to adopt.")
            return 0, lines
        dest_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest / "upstream", ignore=shutil.ignore_patterns(*SKIP))
        manifest = {
            "schema": 1, "id": pid, "title": meta["name"], "summary": (meta["description"] or "")[:300],
            "version": meta["version"],
            "origin": {"kind": "adopted", "from": meta["from"], "name": meta["name"],
                       "source": str(source) if origin.get("repository") else f"local folder {src.name}",
                       **origin, "license": spdx, "adopted": today(), "tree": tree_sha(dest / "upstream")},
            "root": "upstream",
            "when": {"files": [w.strip() for w in (when or "").split(",") if w.strip()]},
            "requires": requires, "items": items, "unsupported": unsupported,
        }
        (dest / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        lines.append(f"adopted: {dest / MANIFEST} · {len(items)} item(s), every one a proposal until ratified")
        return 0, lines
    except RuntimeError as e:
        return 1, [f"FAIL  {e}"]
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------- check ---------------------------------------------------------------------------------------

def check(repo=None, root=ROOT):
    """[(level, line)] for every pack in both layers and the project's activation file."""
    out = []
    packs = discover(repo, root)
    for pid, pk in sorted(packs.items()):
        where = f"{pk.layer}:{pid}"
        m = pk.m
        if not m:
            out.append(("FAIL", f"{where}: {MANIFEST} is missing or does not parse"))
            continue
        if m.get("schema") != 1:
            out.append(("FAIL", f"{where}: schema {m.get('schema')!r}, expected 1"))
        if m.get("id") != pk.path.name:
            out.append(("FAIL", f"{where}: id {m.get('id')!r} differs from its folder {pk.path.name!r}"))
        if not ID.match(str(m.get("id") or "")):
            out.append(("FAIL", f"{where}: id is not kebab-case"))
        keys = [i.get("key") for i in pk.items()]
        for k in sorted({k for k in keys if keys.count(k) > 1}):
            out.append(("FAIL", f"{where}: item key {k} appears twice"))
        for i in pk.items():
            kind = i.get("kind")
            if kind not in KINDS:
                out.append(("FAIL", f"{where}: item {i.get('key')}: unknown kind {kind!r}"))
                continue
            if kind in ("playbook", "command", "agent"):
                p = rel_inside(pk.path, i.get("path"))
                if not p or not p.is_file():
                    out.append(("FAIL", f"{where}: item {i['key']}: path {i.get('path')!r} is missing or leaves the pack"))
            if kind == "hook":
                if i.get("event") not in DISPATCHED:
                    out.append(("FAIL", f"{where}: item {i['key']}: event {i.get('event')!r} is not dispatched"))
                if not i.get("command"):
                    out.append(("FAIL", f"{where}: item {i['key']}: no command"))
        origin = m.get("origin") or {}
        if pk.layer == "public":
            if origin.get("kind") == "adopted" and origin.get("license") not in OPEN_LICENSES:
                out.append(("FAIL", f"{where}: the public layer needs an open-source license; manifest says "
                                    f"{origin.get('license')!r}"))
        if origin.get("kind") == "adopted" and origin.get("tree") and pk.plugin_root.is_dir() \
                and tree_sha(pk.plugin_root) != origin["tree"]:
            out.append(("WARN", f"{where}: upstream files changed since adoption ({origin['tree']} -> {tree_sha(pk.plugin_root)}); "
                                "every ratified hook is STALE until ratified again"))
        if pk.shadows:
            out.append(("WARN", f"{where} shadows {pk.shadows.layer}:{pid} in this project"))
        if not any(l == "FAIL" and c.startswith(where) for l, c in out):
            n = {k: sum(1 for i in pk.items() if i.get("kind") == k) for k in KINDS}
            out.append(("OK", f"{where}: " + (", ".join(f"{v} {k}" for k, v in n.items() if v) or "no items")))
    if repo and project_dir(repo):
        act = load_active(repo)
        for pid, entry in sorted(act["packs"].items()):
            pk = packs.get(pid)
            if not pk:
                out.append(("FAIL", f"active.json: pack '{pid}' is active but exists in no layer"))
                continue
            tree = tree_sha(pk.path)
            for key in sorted((entry.get("ratified") or {})):
                if not pk.item(key):
                    out.append(("WARN", f"active.json: {pid} ratifies {key}, which the pack no longer has"))
                elif item_state(pk, entry, key, tree) == "stale":
                    out.append(("WARN", f"active.json: {pid} {key} is STALE: the pack changed since it was ratified"))
            waiting = [i["key"] for i in pk.items() if i.get("kind") == "hook" and item_state(pk, entry, i["key"], tree) == "proposal"]
            if waiting:
                out.append(("WARN", f"active.json: {pid} has {len(waiting)} hook(s) waiting for the Regent's ratification: "
                                    + ", ".join(waiting[:6])))
    return out


# ---------- activation and consent ------------------------------------------------------------------------

def activate(pid, repo, yes=False, on=True, root=ROOT):
    if project_dir(repo) is None:
        return 1, ["FAIL  this project has no guidelines root: run /regency:init first"]
    packs = discover(repo, root)
    act = load_active(repo)
    if on:
        pk = packs.get(pid)
        if not pk or not pk.m:
            return 1, [f"FAIL  no pack '{pid}' in either layer (packs.py list)"]
        if pid in act["packs"]:
            return 0, [f"{pid} is already active here ({act['packs'][pid].get('layer')})"]
        lines = [f"activate {pk.layer} pack '{pid}' in {repo}: its playbooks become runnable here; its "
                 f"{sum(1 for i in pk.items() if i.get('kind') == 'hook')} hook(s) still wait for ratification"]
        if yes:
            act["packs"][pid] = {"layer": pk.layer, "since": today(), "ratified": {}}
            save_active(repo, act)
            lines.append(f"written: {project_dir(repo) / ACTIVE}")
        else:
            lines.append("plan only: run again with --yes")
        return 0, lines
    if pid not in act["packs"]:
        return 0, [f"{pid} is not active here"]
    lines = [f"deactivate '{pid}': its hooks stop and its ratifications are dropped (a later activation asks again)"]
    if yes:
        del act["packs"][pid]
        save_active(repo, act)
        lines.append(f"written: {project_dir(repo) / ACTIVE}")
    else:
        lines.append("plan only: run again with --yes")
    return 0, lines


def ratify(pid, target, repo, yes=False, root=ROOT):
    """The Regent's consent. Without --yes: the review (each hook's exact command). With it: recorded at the tree."""
    pk = discover(repo, root).get(pid)
    act = load_active(repo)
    if not pk or pid not in act["packs"]:
        return 1, [f"FAIL  '{pid}' is not active in this project: activate it first"]
    if target == "hooks":
        chosen = [i for i in pk.items() if i.get("kind") == "hook"]
    elif target == "all":
        chosen = pk.items()
    else:
        chosen = [i for i in pk.items() if i.get("key") == target]
    if not chosen:
        return 1, [f"FAIL  no item {target!r} in {pid} (packs.py show {pid})"]
    tree = tree_sha(pk.path)
    lines = [f"ratify {len(chosen)} item(s) of {pk.layer}:{pid} at tree {tree} in {repo}"]
    for i in chosen:
        if i["kind"] == "hook":
            cmd = i.get("command") + (" " + " ".join(map(str, i["args"])) if i.get("args") else "")
            lines.append(f"  {i['key']} [{i.get('matcher') or '*'}] runs: {cmd}")
        else:
            lines.append(f"  {i['key']} ({i.get('path') or i.get('name')})")
    if not yes:
        lines.append("review only: nothing recorded. The Regent's consent is a run with --yes; any later change to the "
                     "pack's files makes these items STALE again.")
        return 0, lines
    entry = act["packs"][pid]
    entry.setdefault("ratified", {})
    for i in chosen:
        entry["ratified"][i["key"]] = {"tree": tree, "on": today()}
    save_active(repo, act)
    lines.append(f"ratified: written to {project_dir(repo) / ACTIVE}")
    return 0, lines


# ---------- presentation -----------------------------------------------------------------------------------

def substitute(text, pk, repo):
    return (str(text).replace("${CLAUDE_PLUGIN_ROOT}", pk.plugin_root.resolve().as_posix())
            .replace("${CLAUDE_PROJECT_DIR}", Path(repo or os.getcwd()).resolve().as_posix()))


def show(pid, key, repo, root=ROOT):
    pk = discover(repo, root).get(pid)
    if not pk or not pk.m:
        return 1, [f"FAIL  no pack '{pid}'"]
    entry = load_active(repo)["packs"].get(pid)
    tree = tree_sha(pk.path)
    if not key:
        lines = [f"{pk.layer}:{pid} · {pk.m.get('title')} {pk.m.get('version') or ''}".rstrip(),
                 f"  {pk.m.get('summary', '')}", f"  root: {pk.plugin_root.resolve().as_posix()}",
                 f"  active here: {'yes since ' + entry.get('since', '?') if entry else 'no'} · tree {tree}"]
        for r in pk.m.get("requires", []):
            lines.append(f"  requires {r['tool']}: {'found' if shutil.which(r['tool']) else 'NOT on PATH'} ({r['why']})")
        for i in pk.items():
            state = item_state(pk, entry, i["key"], tree) if entry else "inactive"
            lines.append(f"  {i['key']:<40} {state}")
        for u in pk.m.get("unsupported", []):
            lines.append(f"  not adopted: {u['what']} ({u['path']}): {u['why']}")
        return 0, lines
    i = pk.item(key)
    if not i:
        return 1, [f"FAIL  no item {key!r} in {pid}"]
    lines = [f"{pid} {key} · {item_state(pk, entry, key, tree) if entry else 'pack not active here'}"]
    if i.get("path"):
        p = (pk.path / i["path"]).resolve()
        lines += [f"  file: {p.as_posix()}", f"  its relative paths resolve against: {p.parent.as_posix()}",
                  f"  ${{CLAUDE_PLUGIN_ROOT}} = {pk.plugin_root.resolve().as_posix()}"]
    if i.get("command"):
        lines.append(f"  runs: {substitute(i['command'], pk, repo)}")
    if i.get("config"):
        lines.append("  config: " + substitute(json.dumps(i["config"]), pk, repo))
    return 0, lines


def suggest(repo, root=ROOT):
    act = load_active(repo)["packs"]
    files = []
    for p in walk(repo):
        if any(part in wire.SKIP_PARTS for part in p.relative_to(repo).parts):
            continue
        files.append(p.relative_to(repo).as_posix())
        if len(files) > 20000:
            break
    out = []
    for pid, pk in sorted(discover(repo, root).items()):
        globs = (pk.m.get("when") or {}).get("files") or []
        if pid in act or not globs:
            continue
        hit = next((f for f in files for g in globs if fnmatch.fnmatch(f, g) or fnmatch.fnmatch(Path(f).name, g)), None)
        if hit:
            out.append(f"suggest {pk.layer}:{pid}: {hit} matches its signals ({', '.join(globs)}) -> /regency:pack activate {pid}")
    return out or ["no inactive pack's signals match this project"]


def mcp(pid, repo, write=False, yes=False, root=ROOT):
    pk = discover(repo, root).get(pid)
    if not pk:
        return 1, [f"FAIL  no pack '{pid}'"]
    servers = {i["name"]: json.loads(substitute(json.dumps(i["config"]), pk, repo))
               for i in pk.items() if i.get("kind") == "mcp"}
    if not servers:
        return 0, [f"{pid} carries no MCP server"]
    lines = [json.dumps({"mcpServers": servers}, indent=2)]
    if not write:
        return 0, lines + ["add these to the project's .mcp.json, or run again with --write --yes"]
    target = Path(repo) / ".mcp.json"
    data = load_json(target) or {"mcpServers": {}}
    taken = sorted(set(servers) & set(data.get("mcpServers", {})))
    if taken:
        return 1, [f"FAIL  .mcp.json already names {', '.join(taken)}: nothing written (rename one first)"]
    if not yes:
        return 0, lines + [f"plan only: would add {len(servers)} server(s) to {target}; run again with --yes"]
    data.setdefault("mcpServers", {}).update(servers)
    wire.atomic_write(target, json.dumps(data, indent=2) + "\n")
    return 0, lines + [f"written: {target}"]


def listing(repo, root=ROOT):
    act = load_active(repo)["packs"] if repo else {}
    packs = discover(repo, root)
    if not packs:
        return ["no packs yet: regency's packs/ is empty and this project has no .packs/ (/regency:pack adopt)"]
    out = []
    for pid, pk in sorted(packs.items()):
        entry = act.get(pid)
        tree = tree_sha(pk.path) if entry else None
        hooks = [i for i in pk.items() if i.get("kind") == "hook"]
        live = sum(1 for i in hooks if entry and item_state(pk, entry, i["key"], tree) == "ratified")
        kinds = ", ".join(f"{sum(1 for i in pk.items() if i.get('kind') == k)} {k}" for k in KINDS
                          if any(i.get("kind") == k for i in pk.items()))
        out.append(f"{'*' if entry else ' '} {pk.layer:<7} {pid:<20} {kinds}"
                   + (f" · hooks running {live}/{len(hooks)}" if entry and hooks else "")
                   + (f" · shadows {pk.shadows.layer}" if pk.shadows else ""))
    return out + ["(* active in this project)"]


# ---------- self-test ----------------------------------------------------------------------------------------

def make_plugin(base, license_text=True):
    """An incoming plugin with every part the adopter maps or refuses."""
    base = Path(base)
    files = {
        ".claude-plugin/plugin.json": json.dumps({"name": "demo-tools", "version": "1.4.0", "description": "Demo plugin",
                                                  "license": "MIT", "lspServers": "./.lsp.json"}),
        "skills/review/SKILL.md": "---\nname: review\ndescription: Review a change\n---\n\nRead ${CLAUDE_PLUGIN_ROOT}/notes.md\n",
        "skills/ship/SKILL.md": "---\nname: ship\ndescription: Ship it\n---\n\nShip.\n",
        "commands/status.md": "---\ndescription: Show status\n---\n\nStatus.\n",
        "agents/checker.md": "---\nname: checker\ndescription: Checks things\n---\n\nYou check.\n",
        "hooks/hooks.json": json.dumps({"hooks": {
            "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "node \"${CLAUDE_PLUGIN_ROOT}/scripts/guard.js\""}]}],
            "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/fmt.sh\"", "timeout": 20}]}],
            "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}],
            "Notification": [{"hooks": [{"type": "command", "command": "echo hi"}]}],
            "SessionStart": [{"hooks": [{"type": "prompt", "prompt": "x"},
                                        {"type": "command", "command": "echo ${user_config.token}"}]}]}}),
        ".mcp.json": json.dumps({"mcpServers": {"demo-api": {"command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"]}}}),
        ".lsp.json": "{}", "bin/demo": "#!/bin/sh\n", "scripts/guard.js": "//\n", "scripts/fmt.sh": "#\n",
        "server.js": "//\n", "notes.md": "notes\n",
    }
    if license_text:
        files["LICENSE"] = "MIT License\n\nPermission is hereby granted, free of charge, to any person ...\n"
    for rel, text in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return base


def selftest():
    cases = []

    def ok(cond, label):
        cases.append((bool(cond), label))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        os.environ["REGENCY_HOOK_STATE"] = str(tmp / "state")
        regency = tmp / "regency"
        (regency / PUBLIC).mkdir(parents=True)
        repo = wire.build_fixture(tmp / "proj")
        plugin = make_plugin(tmp / "incoming")

        meta, items, unsupported, requires = inventory(plugin)
        keys = {i["key"] for i in items}
        ok({"playbook:review", "playbook:ship", "command:status", "agent:checker", "hook:PreToolUse:0",
            "hook:PostToolUse:0", "mcp:demo-api"} <= keys, "inventory: skills, command, agent, hooks and MCP server mapped")
        whys = " | ".join(u["what"] + ": " + u["why"] for u in unsupported)
        ok("R4.5" in whys, "inventory: a Stop hook is refused (R4.5)")
        ok("Notification is not dispatched" in whys, "inventory: an event the dispatcher does not serve is listed, not dropped")
        ok("only command hooks" in whys and "user_config" in whys, "inventory: prompt hooks and ${user_config} are listed")
        ok("LSP" in whys and "executables" in whys, "inventory: LSP servers and bin/ are listed with their reason")
        ok({r["tool"] for r in requires} >= {"node", "bash"}, "inventory: node and bash detected as requirements")
        ok(meta["version"] == "1.4.0" and meta["from"] == "plugin", "inventory: the manifest's name and version kept")

        skill = tmp / "lone-skill"
        (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: lone\ndescription: A lone skill\n---\nx\n", encoding="utf-8")
        (skill / "scripts" / "run.py").write_text("print(1)\n", encoding="utf-8")
        _, sitems, _, sreq = inventory(skill)
        ok([i["key"] for i in sitems] == ["playbook:lone"] and sitems[0]["path"] == "upstream/SKILL.md",
           "inventory: a standalone skill folder is one playbook")
        ok(any(r["tool"] == "python" for r in sreq), "inventory: a skill's python script is a requirement")

        code, lines = adopt(str(plugin), "demo", "project", repo, yes=False, root=regency)
        ok(code == 0 and not (repo / ".guidelines" / PROJECT / "demo").exists() and any("plan only" in l for l in lines),
           "adopt: without --yes nothing is written")
        code, _ = adopt(str(plugin), "demo", "project", repo, yes=True, when="*.demo", root=regency)
        pack_dir = repo / ".guidelines" / PROJECT / "demo"
        ok(code == 0 and (pack_dir / MANIFEST).is_file() and (pack_dir / "upstream" / "skills" / "review" / "SKILL.md").is_file(),
           "adopt: the source is copied verbatim under upstream/ with pack.json beside it")
        m = load_json(pack_dir / MANIFEST)
        ok(m["origin"]["license"] == "MIT" and m["origin"]["tree"] == tree_sha(pack_dir / "upstream"),
           "adopt: license and the upstream tree fingerprint recorded")
        ok(m["origin"]["source"] == "local folder incoming" and str(tmp) not in (pack_dir / MANIFEST).read_text(encoding="utf-8"),
           "adopt: a local source leaves no machine path in pack.json")
        code, lines = adopt(str(plugin), "demo", "project", repo, yes=True, root=regency)
        ok(code == 1 and "adopted once" in lines[0], "adopt: an existing pack is never overwritten")
        code, lines = adopt(str(make_plugin(tmp / "nolicense", license_text=False)), "x", "public", repo, yes=True, root=regency)
        ok(code == 0, "adopt: a manifest license field is accepted as evidence")
        bare = tmp / "bare"
        (bare / "skills" / "a").mkdir(parents=True)
        (bare / "skills" / "a" / "SKILL.md").write_text("---\nname: a\n---\n", encoding="utf-8")
        code, lines = adopt(str(bare), "bare", "public", repo, yes=True, root=regency)
        ok(code == 1 and "open-source license" in lines[0] and not (regency / PUBLIC / "bare").exists(),
           "adopt: the public layer refuses a source with no license")
        code, lines = adopt(str(plugin), "Bad_Id", "project", repo, yes=True, root=regency)
        ok(code == 1 and "kebab-case" in lines[0], "adopt: a pack id must be kebab-case")
        code, lines = adopt(str(plugin), "z", "project", tmp / "noguides", yes=True, root=regency)
        ok(code == 1 and "no guidelines root" in lines[0], "adopt: no project layer without a guidelines root")

        git_src = tmp / "gitsrc"
        shutil.copytree(skill, git_src)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"]):
            subprocess.run(["git", "-C", str(git_src), *args], capture_output=True, env=env)
        code, lines = adopt(f"file://{git_src.as_posix()}", "from-git", "project", repo, yes=True, root=regency)
        gm = load_json(repo / ".guidelines" / PROJECT / "from-git" / MANIFEST) or {}
        ok(code == 0 and len((gm.get("origin") or {}).get("sha") or "") == 40, "adopt: a git url is cloned and its commit recorded")

        found = check(repo, regency)
        ok(not any(l == "FAIL" for l, _ in found), "check: freshly adopted packs pass")
        code, _ = activate("demo", repo, yes=True, root=regency)
        act = load_active(repo)
        ok(code == 0 and "demo" in act["packs"], "activate: written to .packs/active.json on --yes")
        ok(any("waiting for the Regent's ratification" in c for _, c in check(repo, regency)),
           "check: an active pack's unratified hooks are named")
        code, lines = ratify("demo", "hooks", repo, yes=False, root=regency)
        ok(code == 0 and any("runs: node" in l for l in lines) and not load_active(repo)["packs"]["demo"]["ratified"],
           "ratify: without --yes it shows each hook's exact command and records nothing")
        ratify("demo", "hooks", repo, yes=True, root=regency)
        pk = discover(repo, regency)["demo"]
        entry = load_active(repo)["packs"]["demo"]
        ok(item_state(pk, entry, "hook:PreToolUse:0") == "ratified", "ratify: with --yes the hook is ratified at the tree")
        (pack_dir / "upstream" / "scripts" / "guard.js").write_text("// changed\n", encoding="utf-8")
        ok(item_state(pk, entry, "hook:PreToolUse:0") == "stale", "ratify: any change to the pack's files makes it STALE")
        ok(any("STALE" in c for _, c in check(repo, regency)) and any("upstream files changed" in c for _, c in check(repo, regency)),
           "check: stale ratifications and drifted upstream are reported")
        ok(tree_sha_cached(pack_dir) == tree_sha(pack_dir), "tree: the cached fingerprint equals the full one")

        (regency / PUBLIC / "demo").mkdir()
        (regency / PUBLIC / "demo" / MANIFEST).write_text(json.dumps({"schema": 1, "id": "demo", "items": []}), encoding="utf-8")
        ok(discover(repo, regency)["demo"].layer == "project" and any("shadows public:demo" in c for _, c in check(repo, regency)),
           "layers: a project pack shadows the public one and check says so")
        (regency / PUBLIC / "broken").mkdir()
        (regency / PUBLIC / "broken" / MANIFEST).write_text(json.dumps({"schema": 1, "id": "other", "items": [
            {"key": "playbook:a", "kind": "playbook", "path": "../../escape.md"},
            {"key": "playbook:a", "kind": "playbook", "path": "x.md"},
            {"key": "hook:Stop:0", "kind": "hook", "event": "Stop", "command": "x"}]}), encoding="utf-8")
        fails = [c for l, c in check(repo, regency) if l == "FAIL"]
        ok(any("differs from its folder" in c for c in fails), "check: an id that differs from its folder fails")
        ok(any("appears twice" in c for c in fails), "check: a duplicated item key fails")
        ok(any("leaves the pack" in c for c in fails), "check: a path that leaves the pack fails")
        ok(any("not dispatched" in c for c in fails), "check: a hook on an undispatched event fails")
        shutil.rmtree(regency / PUBLIC / "broken")

        code, lines = show("demo", "playbook:review", repo, regency)
        ok(code == 0 and any(l.strip().startswith("file:") and l.rstrip().endswith("SKILL.md") for l in lines),
           "show: a playbook resolves to its file and its root")
        code, lines = mcp("demo", repo, root=regency)
        ok(code == 0 and str(pack_dir.resolve().as_posix()) in lines[0], "mcp: ${CLAUDE_PLUGIN_ROOT} resolves to the pack")
        code, _ = mcp("demo", repo, write=True, yes=True, root=regency)
        code2, lines = mcp("demo", repo, write=True, yes=True, root=regency)
        ok(code == 0 and code2 == 1 and "already names demo-api" in lines[0], "mcp: never overwrites a server name")
        (repo / "src" / "a.demo").write_text("x", encoding="utf-8")
        activate("demo", repo, yes=True, on=False, root=regency)
        ok("demo" not in load_active(repo)["packs"], "deactivate: the pack and its ratifications leave active.json")
        ok(any("suggest project:demo" in l for l in suggest(repo, regency)), "suggest: a file matching the signals names the pack")
        ok(any(l.startswith("  project demo") for l in listing(repo, regency)), "list: every pack with its layer")
    return wire.check(cases)


# ---------- command line -------------------------------------------------------------------------------------

def main(argv):
    if "--selftest" in argv:
        return selftest()
    args, opt, flags = [], {}, set()
    it = iter(argv)
    for a in it:
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            opt[k] = v
        elif a[2:] in ("repo", "id", "layer", "when") and a.startswith("--"):
            opt[a[2:]] = next(it, "")
        elif a.startswith("--"):
            flags.add(a[2:])
        else:
            args.append(a)
    yes = "yes" in flags
    repo = wire.repo_root(Path(opt["repo"]) if opt.get("repo") else Path.cwd())
    if repo.resolve() == ROOT.resolve():
        repo = None  # inside regency itself: the public layer only
    cmd = args[0] if args else "list"
    if cmd == "list":
        print("\n".join(listing(repo)))
        return 0
    if cmd == "check":
        found = check(repo)
        order = {"FAIL": 0, "WARN": 1, "OK": 2}
        for lvl, line in sorted(found, key=lambda x: order[x[0]]):
            print(f"{lvl:<4}  {line}")
        if not found:
            print("OK    no packs in either layer")
        return 1 if any(l == "FAIL" for l, _ in found) else 0
    if cmd == "suggest":
        print("\n".join(suggest(repo or Path.cwd())))
        return 0
    if cmd == "adopt" and len(args) >= 2:
        code, lines = adopt(args[1], opt.get("id", ""), opt.get("layer", ""), repo, yes, opt.get("when"))
    elif cmd in ("activate", "deactivate") and len(args) >= 2:
        code, lines = activate(args[1], repo, yes, on=(cmd == "activate"))
    elif cmd == "ratify" and len(args) >= 3:
        code, lines = ratify(args[1], args[2], repo, yes)
    elif cmd == "show" and len(args) >= 2:
        code, lines = show(args[1], args[2] if len(args) > 2 else None, repo)
    elif cmd == "mcp" and len(args) >= 2:
        code, lines = mcp(args[1], repo or Path.cwd(), "write" in flags, yes)
    else:
        print(__doc__)
        return 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
