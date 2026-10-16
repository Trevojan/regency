#!/usr/bin/env python3
"""install-agents.py - install the four role agents (po, dv, qa, da) as user-level Claude Code subagents.

Source of truth: library/agents/*.md (portable: they carry the placeholder {{REGENCY_ROOT}}).
Destination:     ~/.claude/agents/<name>.md  (one flat file per agent; no subfolder needed)

The installed copy is the source with {{REGENCY_ROOT}} replaced by THIS folder's absolute path and one
marker line added, so the script can tell its own files from yours.

Usage
  python scripts/install-agents.py              install or update (never overwrites a file it did not create)
  python scripts/install-agents.py --check      report missing / stale / conflicting; exit 1 if any
  python scripts/install-agents.py --uninstall  remove only the files this script created
  python scripts/install-agents.py --force      overwrite a conflicting file (a .bak copy is kept)
  python scripts/install-agents.py --dest DIR   another destination (default: ~/.claude/agents)

Re-run after moving this folder or editing library/agents/. Pure standard library, Python 3.8+.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "library" / "agents"
PLACEHOLDER = "{{REGENCY_ROOT}}"
MARK = "<!-- installed by regency scripts/install-agents.py from library/agents/{name}; edit the source there and re-run -->"
MARK_RE = re.compile(r"<!-- installed by regency scripts/install-agents\.py")


def sources():
    return sorted(SRC.glob("*.md"))


def validate(text, stem):
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        return ["no frontmatter"]
    fm = {}
    for line in m.group(1).split("\n"):
        k = re.match(r"^([A-Za-z]+):\s*(.*)$", line)
        if k:
            fm[k.group(1)] = k.group(2).strip()
    if fm.get("name") != stem:
        problems.append(f"name {fm.get('name')!r} must equal the file name {stem!r}")
    if ":" in fm.get("name", ""):
        problems.append("name must not contain ':'")
    if not fm.get("description"):
        problems.append("missing description")
    if not fm.get("tools"):
        problems.append("missing tools (an agent without a tool list inherits everything)")
    if PLACEHOLDER not in text:
        problems.append(f"does not use {PLACEHOLDER}")
    return problems


def render(path):
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    body = text.replace(PLACEHOLDER, ROOT.as_posix())
    head, rest = body.split("\n---\n", 1)
    return f"{head}\n---\n{MARK.format(name=path.name)}\n{rest}"


def main(argv):
    dest = Path.home() / ".claude" / "agents"
    if "--dest" in argv:
        dest = Path(argv[argv.index("--dest") + 1])
    check, uninstall, force = "--check" in argv, "--uninstall" in argv, "--force" in argv
    srcs = sources()
    if not srcs:
        print(f"no agent sources in {SRC}")
        return 1
    bad = 0
    for p in srcs:
        probs = validate(p.read_text(encoding="utf-8-sig"), p.stem)
        for pr in probs:
            print(f"SOURCE {p.name}: {pr}")
            bad += 1
    if bad:
        return 1
    if not check and not uninstall:
        dest.mkdir(parents=True, exist_ok=True)
    for p in srcs:
        target = dest / p.name
        want = render(p)
        have = target.read_text(encoding="utf-8-sig") if target.is_file() else None
        ours = have is not None and bool(MARK_RE.search(have))
        if uninstall:
            if ours:
                target.unlink()
                print(f"removed      {p.stem}")
            else:
                print(f"left alone   {p.stem} ({'not installed' if have is None else 'not created by regency'})")
            continue
        if have is None:
            state = "missing"
        elif have == want:
            state = "ok"
        elif ours:
            state = "stale"
        else:
            state = "conflict"
        if check:
            print(f"{state:12} {p.stem}")
            bad += state != "ok"
            continue
        if state == "ok":
            print(f"up to date   {p.stem}")
        elif state in ("missing", "stale"):
            target.write_text(want, encoding="utf-8", newline="\n")
            print(f"{'installed' if state == 'missing' else 'updated':12} {p.stem}  -> {target.as_posix()}")
        elif force:
            target.with_suffix(".md.bak").write_text(have, encoding="utf-8", newline="\n")
            target.write_text(want, encoding="utf-8", newline="\n")
            print(f"overwritten  {p.stem}  (previous copy kept as {target.name}.bak)")
        else:
            print(f"SKIPPED      {p.stem}: {target.as_posix()} exists and was not created by regency (use --force)")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
