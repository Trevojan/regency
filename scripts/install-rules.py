#!/usr/bin/env python3
"""install-rules.py - install regency's path-scoped rules as user-level Claude Code rules.

Source of truth: library/rules/*.md (each carries a `paths:` frontmatter; Claude Code loads it only when a
                 matching file is touched).
Destination:     ~/.claude/rules/<name>.md

The installed copy is the source plus one marker line, so the script can tell its own files from yours.
Same contract as install-agents.py.

Usage
  python scripts/install-rules.py              install or update (never overwrites a file it did not create)
  python scripts/install-rules.py --check      report missing / stale / conflicting; exit 1 if any
  python scripts/install-rules.py --uninstall  remove only the files this script created
  python scripts/install-rules.py --force      overwrite a conflicting file (a .bak copy is kept)
  python scripts/install-rules.py --dest DIR   another destination (default: ~/.claude/rules)

Re-run after editing library/rules/. Pure standard library, Python 3.8+.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "library" / "rules"
MARK = "<!-- installed by regency scripts/install-rules.py from library/rules/{name}; edit the source there and re-run -->"
MARK_RE = re.compile(r"<!-- installed by regency scripts/install-rules\.py")


def sources():
    return sorted(SRC.glob("*.md"))


def validate(text):
    m = re.match(r"^---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        return ["no frontmatter"]
    fm = m.group(1)
    if not re.search(r"^paths:\s*$", fm, re.M) or not re.search(r'^\s+-\s+"[^"]+"\s*$', fm, re.M):
        return ["frontmatter needs `paths:` with at least one quoted glob (a rule without paths loads everywhere)"]
    return []


def render(path):
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    head, rest = text.split("\n---\n", 1)
    return f"{head}\n---\n{MARK.format(name=path.name)}\n{rest}"


def main(argv):
    dest = Path.home() / ".claude" / "rules"
    if "--dest" in argv:
        dest = Path(argv[argv.index("--dest") + 1])
    check, uninstall, force = "--check" in argv, "--uninstall" in argv, "--force" in argv
    srcs = sources()
    if not srcs:
        print(f"no rule sources in {SRC}")
        return 1
    bad = 0
    for p in srcs:
        for pr in validate(p.read_text(encoding="utf-8-sig")):
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
        state = "missing" if have is None else "ok" if have == want else "stale" if ours else "conflict"
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
