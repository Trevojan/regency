#!/usr/bin/env python3
"""conventions_check.py - do regency's own files follow the Regent's conventions?

Run:  python scripts/conventions_check.py            one line per finding, exit 1 on any FAIL
      python scripts/conventions_check.py --selftest  prove every check detects its own defect

Checks (library/conventions.md section 0, 11, 12, 13; library/ids.md)
  version   registry.json and .claude-plugin/plugin.json carry the same a.b version
  ids       library/ids.md machine grammar parses, every pattern compiles, every example matches
  legacy    WARN for D1-D4 used as level names (renamed O1-O4)
  banned    FAIL for S3 banned name tokens in paths and in Python def/class names
  canonical FAIL for a canonical document name not in UPPER_CASE (N5)
  suba      FAIL for suba-/-vendor folders outside library/subagents and library/vendors (N1, N2)

Every finding is one line, so a reader takes a slice instead of inferring the whole.
Pure standard library, Python 3.8+. Reads only; writes nothing (the self-test writes to a temp dir).
"""
import json
import re
import sys
import tempfile
from pathlib import Path

SKIP_DIRS = {"discard", ".git", "node_modules", "__pycache__"}
BANNED = {"base", "abs", "mgr", "helper", "helpers", "common", "util", "utils"}
CANONICAL = {"agents", "claude", "protocol", "team", "team-orchestration", "orchestration",
             "readme", "changelog", "briefing"}
LEGACY_LEVEL = re.compile(r"(?<![\w.-])D[1-4](?![\w])")
LEGACY_EXEMPT = ("library/ids.md", "library/examples/", "discard/")
CANONICAL_EXEMPT = ("library/examples/", "discard/")  # samples are named after what they show
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.S)
VERSION = re.compile(r"^\d+\.\d+$")


def tokens(name):
    """Split a name into lowercase word tokens: camelCase, kebab, snake, dots."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return [t.lower() for t in re.split(r"[\s\-_./]+", spaced) if t]


class Checker:
    def __init__(self, root):
        self.root = Path(root)
        self.out = []

    def rec(self, level, check, msg):
        self.out.append((level, check, msg))

    def rel(self, p):
        return p.relative_to(self.root).as_posix()

    def walk(self):
        for p in sorted(self.root.rglob("*")):
            parts = p.relative_to(self.root).parts
            if not any(part in SKIP_DIRS for part in parts):
                yield p

    def check_version(self):
        reg_p = self.root / "library" / "registry.json"
        man_p = self.root / ".claude-plugin" / "plugin.json"
        found = {}
        for label, p in (("registry", reg_p), ("plugin.json", man_p)):
            if not p.is_file():
                self.rec("WARN", "version", f"{label} not present here")
                continue
            v = str(json.loads(p.read_text(encoding="utf-8-sig")).get("version", ""))
            found[label] = v
            if not VERSION.match(v):
                self.rec("FAIL", "version", f"{label} version {v!r} is not a.b")
        if len(set(found.values())) > 1:
            self.rec("FAIL", "version", f"versions differ: {found}")
        elif found:
            self.rec("OK", "version", f"a.b = {next(iter(found.values()))}")

    def check_ids(self):
        p = self.root / "library" / "ids.md"
        if not p.is_file():
            return self.rec("FAIL", "ids", "library/ids.md is missing")
        m = JSON_BLOCK.search(p.read_text(encoding="utf-8"))
        if not m:
            return self.rec("FAIL", "ids", "library/ids.md has no ```json grammar block")
        try:
            grammar = json.loads(m.group(1))
        except ValueError as e:
            return self.rec("FAIL", "ids", f"grammar block does not parse: {e}")
        bad = 0
        for key, spec in grammar.items():
            try:
                ok = re.match(spec["pattern"], spec["example"])
            except (KeyError, re.error) as e:
                ok, bad = None, bad + 1
                self.rec("FAIL", "ids", f"{key}: {e}")
                continue
            if not ok:
                bad += 1
                self.rec("FAIL", "ids", f"{key}: example {spec['example']!r} does not match its pattern")
        if not bad:
            self.rec("OK", "ids", f"{len(grammar)} id grammars compile and match their examples")

    def check_legacy(self):
        hits = 0
        for p in self.walk():
            r = self.rel(p)
            if not p.is_file() or p.suffix not in {".md", ".xml"} or r.startswith(LEGACY_EXEMPT):
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
                if LEGACY_LEVEL.search(line):
                    hits += 1
                    self.rec("WARN", "legacy", f"{r}:{i}: D1-D4 level name, rename to O1-O4")
        if not hits:
            self.rec("OK", "legacy", "no D1-D4 level names left")

    def check_banned(self):
        bad = 0
        for p in self.walk():
            r = self.rel(p)
            hit = BANNED.intersection(tokens(p.stem if p.is_file() else p.name))
            if hit:
                bad += 1
                self.rec("FAIL", "banned", f"{r}: name uses banned token {sorted(hit)}")
            if p.is_file() and p.suffix == ".py":
                text = p.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    d = re.match(r"\s*(?:def|class)\s+([A-Za-z_]\w*)", line)
                    if d and BANNED.intersection(tokens(d.group(1))):
                        bad += 1
                        self.rec("FAIL", "banned", f"{r}:{i}: identifier {d.group(1)!r} uses a banned token")
        if not bad:
            self.rec("OK", "banned", "no Base/Abs/Mgr/Helper/Common/Utils names")

    def check_canonical(self):
        bad = 0
        for p in self.walk():
            if not (p.is_file() and p.suffix == ".md"):
                continue
            if self.rel(p).startswith(CANONICAL_EXEMPT):
                continue
            stem = p.stem
            low = stem.lower()
            if (low in CANONICAL or low.startswith(("ladder_", "ladder-"))) and stem != stem.upper():
                bad += 1
                self.rec("FAIL", "canonical", f"{self.rel(p)}: canonical document must be UPPER_CASE")
        if not bad:
            self.rec("OK", "canonical", "canonical documents are UPPER_CASE")

    def check_suba(self):
        bad = 0
        subs = self.root / "library" / "subagents"
        vends = self.root / "library" / "vendors"
        for p in self.walk():
            if not p.is_dir():
                continue
            r = self.rel(p)
            if p.parent == subs and not p.name.startswith("suba-"):
                bad += 1
                self.rec("FAIL", "suba", f"{r}: a subagent folder must start with suba-")
            elif p.parent == vends and not p.name.endswith("-vendor"):
                bad += 1
                self.rec("FAIL", "suba", f"{r}: a vendor folder must end with -vendor")
            elif p.name.startswith("suba-") and p.parent != subs:
                bad += 1
                self.rec("FAIL", "suba", f"{r}: suba- folder outside library/subagents")
            elif p.name.endswith("-vendor") and p.parent != vends:
                bad += 1
                self.rec("FAIL", "suba", f"{r}: -vendor folder outside library/vendors")
        if not bad:
            self.rec("OK", "suba", "suba-/-vendor placement holds")

    def run(self):
        for fn in (self.check_version, self.check_ids, self.check_legacy,
                   self.check_banned, self.check_canonical, self.check_suba):
            fn()
        return self.out


def selftest():
    """Each check must fire on a planted defect (T3: a check that never fails proves nothing)."""
    src_ids = Path(__file__).resolve().parent.parent / "library" / "ids.md"
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "library" / "subagents" / "recon").mkdir(parents=True)
        (root / "library" / "vendors" / "suba-x").mkdir(parents=True)
        (root / "skills" / "suba-loose").mkdir(parents=True)
        (root / ".claude-plugin").mkdir()
        (root / "library" / "registry.json").write_text('{"version": "2.0"}', encoding="utf-8")
        (root / ".claude-plugin" / "plugin.json").write_text('{"version": "1.2.0"}', encoding="utf-8")
        (root / "library" / "ids.md").write_text(src_ids.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "library" / "readme.md").write_text("x\n", encoding="utf-8")
        (root / "library" / "examples").mkdir()
        (root / "library" / "examples" / "ladder-plan.example.md").write_text("x\n", encoding="utf-8")
        (root / "library" / "plan.md").write_text("classify at D3 or D2\n", encoding="utf-8")
        (root / "scripts").mkdir()
        (root / "scripts" / "StringHelper.py").write_text("def parse_utils():\n    pass\n", encoding="utf-8")
        found = Checker(root).run()
        want = [("version", "is not a.b"), ("version", "versions differ"), ("legacy", "plan.md:1"),
                ("banned", "StringHelper"), ("banned", "parse_utils"), ("canonical", "readme.md"),
                ("suba", "must start with suba-"), ("suba", "must end with -vendor"),
                ("suba", "outside library/subagents")]
        for check, needle in want:
            hit = any(c == check and needle in m and lvl in ("FAIL", "WARN") for lvl, c, m in found)
            cases.append((hit, check, needle))
        ok_ids = any(c == "ids" and lvl == "OK" for lvl, c, _ in found)
        cases.append((ok_ids, "ids", "real grammar passes"))
        quiet = not any(c == "canonical" and "examples/" in m for _, c, m in found)
        cases.append((quiet, "canonical", "example files are exempt"))
    for hit, check, needle in cases:
        print(f"{'pass' if hit else 'MISS'}  {check}: {needle}")
    missed = sum(1 for hit, _, _ in cases if not hit)
    print(f"selftest: {len(cases) - missed}/{len(cases)} cases")
    return 1 if missed else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = Path(__file__).resolve().parent.parent
    found = Checker(root).run()
    order = {"FAIL": 0, "WARN": 1, "OK": 2}
    for lvl, check, msg in sorted(found, key=lambda x: order[x[0]]):
        print(f"{lvl:<4}  {check}: {msg}")
    return 1 if any(l == "FAIL" for l, _, _ in found) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
