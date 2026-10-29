#!/usr/bin/env python3
"""install-automode.py - merge the Regent's auto-mode entries into the user-level Claude Code settings.

Source of truth: library/automode.json (a settings fragment; headless runs pass it as is with --settings).
Destination:     ~/.claude/settings.json, key autoMode. Claude Code never reads autoMode from a project's
                 .claude/settings*.json, so the user level is the only place an interactive session sees it.

Regency's entries are the ones that open with 'Regency '. Install replaces only those and keeps every other
entry and key as it is. A list it has to create starts with "$defaults", because a list without it discards
the built-in rules. Same contract as install-rules.py: never touch what it did not create.

Usage
  python scripts/install-automode.py              install or update (a .bak of the previous file is kept)
  python scripts/install-automode.py --check      report missing / stale per list; exit 1 if any
  python scripts/install-automode.py --uninstall  remove only regency's entries
  python scripts/install-automode.py --dest FILE  another settings file (default: ~/.claude/settings.json)

Then: claude auto-mode config (the effective rules) and claude auto-mode critique (a review of them).
Re-run after editing library/automode.json. Pure standard library, Python 3.8+.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "library" / "automode.json"
LISTS = ("environment", "allow", "soft_deny", "hard_deny")
TAG = "Regency "
DEFAULTS = "$defaults"


def ours(entry):
    return isinstance(entry, str) and entry.startswith(TAG)


def validate(src):
    out = []
    am = src.get("autoMode")
    if not isinstance(am, dict):
        return ["no autoMode block"]
    for key, entries in am.items():
        if key not in LISTS:
            out.append(f"autoMode.{key}: not one of {', '.join(LISTS)}")
            continue
        if DEFAULTS not in entries:
            out.append(f"autoMode.{key}: no \"$defaults\" (the list would discard every built-in rule)")
        for e in entries:
            if e != DEFAULTS and not ours(e):
                out.append(f"autoMode.{key}: entry does not open with {TAG!r}: {str(e)[:60]}")
    return out


def merged(settings, src, remove=False):
    """settings with regency's entries replaced (or removed); every other entry kept in place."""
    out = json.loads(json.dumps(settings))
    am = out.setdefault("autoMode", {})
    for key in LISTS:
        want = [] if remove else [e for e in src["autoMode"].get(key, []) if ours(e)]
        have = am.get(key)
        if have is None:
            if want:
                am[key] = [DEFAULTS] + want
            continue
        kept = [e for e in have if not ours(e)]
        if not want and kept == [DEFAULTS]:
            del am[key]  # only what this script put there: the same as no list at all
        else:
            am[key] = kept + want
    if not am:
        del out["autoMode"]
    return out


def states(settings, src):
    am = settings.get("autoMode", {})
    out = {}
    for key in LISTS:
        want = [e for e in src["autoMode"].get(key, []) if ours(e)]
        if not want:
            continue
        have = [e for e in am.get(key, []) if ours(e)]
        out[key] = "ok" if have == want else "missing" if not have else "stale"
    return out


def main(argv):
    dest = Path.home() / ".claude" / "settings.json"
    if "--dest" in argv:
        dest = Path(argv[argv.index("--dest") + 1])
    if "--selftest" in argv:
        return selftest()
    check, uninstall = "--check" in argv, "--uninstall" in argv
    src = json.loads(SRC.read_text(encoding="utf-8"))
    bad = validate(src)
    for b in bad:
        print(f"SOURCE {b}")
    if bad:
        return 1
    try:
        settings = json.loads(dest.read_text(encoding="utf-8-sig")) if dest.is_file() else {}
    except ValueError as e:
        print(f"SKIPPED {dest.as_posix()} is not valid JSON ({e}); fix it by hand, nothing was written")
        return 1
    if check:
        st = states(settings, src)
        for key, s in st.items():
            print(f"{s:12} autoMode.{key}")
        return 1 if any(s != "ok" for s in st.values()) else 0
    new = merged(settings, src, remove=uninstall)
    if new == settings:
        print("up to date   " + dest.as_posix() if not uninstall else "left alone   nothing of regency's was there")
        return 0
    if dest.is_file():
        dest.with_suffix(".json.bak").write_text(dest.read_text(encoding="utf-8-sig"), encoding="utf-8", newline="\n")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    verb = "removed" if uninstall else "installed"
    print(f"{verb:12} regency autoMode entries -> {dest.as_posix()} (previous copy: {dest.name}.bak)")
    if not uninstall:
        print("next         claude auto-mode config   ·   claude auto-mode critique")
    return 0


# ---------- self-test ------------------------------------------------------------------------

def selftest():
    src = json.loads(SRC.read_text(encoding="utf-8"))
    misses, n = [], 0

    def check(label, ok):
        nonlocal n
        n += 1
        if not ok:
            misses.append(label)

    check("shipped source is valid", not validate(src))
    check("list without $defaults caught", validate({"autoMode": {"allow": ["Regency x"]}}))
    check("untagged entry caught", validate({"autoMode": {"allow": ["$defaults", "x"]}}))
    check("unknown key caught", validate({"autoMode": {"nope": ["$defaults"]}}))
    mine = {"theme": "dark", "autoMode": {"environment": ["**Org**: mine"], "allow": ["$defaults", "mine"]}}
    m = merged(mine, src)
    check("other keys kept", m["theme"] == "dark")
    check("user entries kept in place", m["autoMode"]["environment"][0] == "**Org**: mine"
          and m["autoMode"]["allow"][:2] == ["$defaults", "mine"])
    check("user list without $defaults left so", DEFAULTS not in m["autoMode"]["environment"])
    check("created list starts with $defaults", m["autoMode"]["hard_deny"][0] == DEFAULTS)
    check("idempotent", merged(m, src) == m)
    check("all ok after install", set(states(m, src).values()) == {"ok"})
    stale = json.loads(json.dumps(m))
    stale["autoMode"]["allow"][-1] = "Regency old wording"
    check("stale detected", states(stale, src)["allow"] == "stale")
    check("update replaces, not duplicates", merged(stale, src) == m)
    check("uninstall restores", merged(m, src, remove=True) == mine)
    check("uninstall of a clean file is a no-op", merged({}, src, remove=True) == {})
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "settings.json"
        f.write_text(json.dumps(mine), encoding="utf-8")
        main(["--dest", str(f)])
        check("writes and keeps a .bak", json.loads(f.read_text(encoding="utf-8")) == m and f.with_suffix(".json.bak").is_file())
        check("--check is green after install", main(["--check", "--dest", str(f)]) == 0)
    for x in misses:
        print("MISS", x)
    print(f"selftest: {n - len(misses)}/{n} planted defects detected")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
