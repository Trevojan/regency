#!/usr/bin/env python3
"""Regency package: build the installable `.plugin` archive from this folder.

The archive is what a Claude account installs, so that /regency: commands work in sessions that
cannot load a local plugin (cloud sessions, Cowork). It is a generated artefact: never edit it,
rebuild it.

What goes in is an allowlist, not "everything in the folder": only the parts that make the plugin.
A stray file dropped into the folder can never ship by accident.

Usage (from anywhere; the root is found relative to this file):
  python scripts/package.py              build dist/<name>-<version>.plugin
  python scripts/package.py --out DIR    build into DIR instead
  python scripts/package.py --check      build nothing; report what would ship and what is wrong

Refuses to build when scripts/build.py --check reports generated files out of date.
The archive is deterministic: the same folder gives the same bytes (fixed timestamps, sorted entries).
Pure standard library, Python 3.8+. No absolute paths, no network.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
SHIPPED = [".claude-plugin", "CLAUDE.md", "README.md", "commands", "hooks", "library", "scripts", "skills"]
SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".plugin"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def shipped_files():
    files = []
    for name in SHIPPED:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for p in sorted(path.rglob("*")):
                rel = p.relative_to(ROOT)
                if p.is_file() and not (set(rel.parts) & SKIP_DIRS) and p.name not in SKIP_FILES \
                        and p.suffix not in SKIP_SUFFIXES:
                    files.append(p)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def problems(manifest, files):
    out = []
    name = manifest.get("name", "")
    if not KEBAB.match(name):
        out.append(f"plugin.json: name '{name}' is not kebab-case")
    if not manifest.get("version"):
        out.append("plugin.json: no version (an installed plugin refreshes only when the version changes)")
    rels = {p.relative_to(ROOT).as_posix() for p in files}
    skills = sorted({r.split("/")[1] for r in rels if r.startswith("skills/") and r.count("/") >= 2})
    for skill in skills:
        if f"skills/{skill}/SKILL.md" not in rels:
            out.append(f"skills/{skill}/ has no SKILL.md")
    for rel in sorted(r for r in rels if r.endswith(".json")):
        try:
            json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except ValueError as exc:
            out.append(f"{rel}: invalid JSON ({exc})")
    for name in SHIPPED:
        if not (ROOT / name).exists():
            out.append(f"missing: {name}")
    return out, skills


def build_is_current():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), "--check"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def write_archive(target, files):
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Build the installable .plugin archive.")
    parser.add_argument("--out", type=Path, default=ROOT / "dist", help="output directory (default: dist/)")
    parser.add_argument("--check", action="store_true", help="build nothing; report only")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = shipped_files()
    found, skills = problems(manifest, files)
    current, build_report = build_is_current()
    if not current:
        found.append("generated files are out of date: run python scripts/build.py (" + build_report + ")")

    stray = sorted(p.name for p in ROOT.iterdir() if p.name not in SHIPPED
                   and p.name not in {"discard", "dist"} and not p.name.startswith("."))
    for name in stray:
        print(f"note  not shipped (outside the allowlist): {name}")
    print(f"plugin {manifest.get('name')} {manifest.get('version')} · {len(files)} files · {len(skills)} skills")
    for problem in found:
        print(f"FAIL  {problem}")
    if found:
        return 1
    if args.check:
        print("check: ready to package")
        return 0

    target = args.out / f"{manifest['name']}-{manifest['version']}.plugin"
    write_archive(target, files)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    try:
        shown = target.relative_to(ROOT).as_posix()
    except ValueError:
        shown = target.name
    print(f"wrote {shown} · {target.stat().st_size} bytes · sha256 {digest[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
