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
  language  FAIL for Portuguese in the app's own sources (conventions §2): templates, playbooks, scripts and
            samples are English; an input is quoted in backticks or double quotes, and the Regent's verbs
            (conventions §9) are input
  subagent  each library/subagents/suba-*: SKILL.md present, name == folder, metadata.owner agrees with
            gov.py OWNER (FAIL); every spine link into references/ resolves (FAIL); a contract.json returns.py
            accepts and a generated return block in the spine (FAIL); the alignment stamp still matches the owner's role
            spec and agent file (WARN: drifted, re-check then re-stamp); metadata.status: proposal (WARN
            until the Regent ratifies); an OWNER entry with no folder (WARN) (library/subagents/ALIGNMENT.md)

Every finding is one line, so a reader takes a slice instead of inferring the whole.
Pure standard library, Python 3.8+. Reads only; writes nothing (the self-test writes to a temp dir).
"""
import hashlib
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
FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
STAMP = re.compile(r"([\w./-]+\.md)#([0-9a-f]{12})")
REF_LINK = re.compile(r"(?:\]\(|`)(references/[^)`\s#]+)")
PT_CHARS = re.compile(r"[ãõçÃÕÇ]")
PT_WORDS = re.compile(r"(?<![\w@./-])(não|você|também|então|porque|isso|isto|essa|esse|esta|este|uma|seu|sua|pelo|pela|"
                      r"está|são|já|até|quando|onde|ainda|nunca|sempre|mais|como|sem|nenhum|nenhuma|deve|pode|fazer|"
                      r"sobre|entre|depois|antes|aqui|agora|para|que|com|quem|qual|cada|foi|ser|tem|muito)(?![\w-])", re.I)
QUOTED = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"|“[^”\n]*”")  # an input quoted as it is
LANG_SUFFIXES = {".md", ".json", ".py", ".xml", ".html", ".css", ".js", ".mjs", ".txt", ".toml", ".yml", ".yaml", ".pgml"}
LANG_INPUT = {  # where Portuguese is input, not source: the file, and the section it is confined to (None: whole file)
    "library/conventions.md": "## 9.",   # the Regent's verbs
    "scripts/hook-verbs.py": None,       # the same table, as the hook's test fixture
    "scripts/conventions_check.py": None,  # its self-test plants Portuguese on purpose
}


def fingerprint(path):
    """First 12 hex of sha256 over the file with line endings normalised (a CRLF checkout is no drift)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def contract_problems(name, root):
    """returns.py's verdict on a suba's contract.json: [] when its schemas hold and its template is coherent."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import returns  # noqa: E402  (stdlib-only sibling)
    return returns.contract_problems(name, root)


def owner_map():
    """gov.py's OWNER: the single source of which role owns which subagent."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gov  # noqa: E402  (stdlib-only sibling)
    return dict(gov.OWNER)


def front_fields(text):
    """Top-level and metadata.* scalars of a SKILL.md frontmatter, quotes stripped; {} when absent."""
    m = FRONT.match(text.replace("\r\n", "\n"))
    if not m:
        return {}
    out, section = {}, None
    for line in m.group(1).split("\n"):
        k = re.match(r"^(\s*)([A-Za-z][\w-]*):\s*(.*)$", line)
        if not k:
            continue
        indent, key, val = k.groups()
        val = val.strip().strip('"').strip("'")
        if not indent:
            section = key if not val else None
            if val:
                out[key] = val
        elif section:
            out[f"{section}.{key}"] = val
    return out


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

    def check_language(self):
        hits = 0
        for p in self.walk():
            r = self.rel(p)
            if not p.is_file() or (p.suffix not in LANG_SUFFIXES and p.name != ".gitignore") or r.startswith("dist/"):
                continue
            if r in LANG_INPUT and LANG_INPUT[r] is None:
                continue
            section, inside = LANG_INPUT.get(r), False
            for i, line in enumerate(p.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
                if section and line.startswith("## "):
                    inside = line.startswith(section)
                if inside:
                    continue
                bare = QUOTED.sub(" ", line)
                word = PT_CHARS.search(bare) or PT_WORDS.search(bare)
                if word:
                    hits += 1
                    self.rec("FAIL", "language", f"{r}:{i}: Portuguese in an app source ({word.group(0)!r}); "
                                                 "write it in English, or quote it if it is input")
        if not hits:
            self.rec("OK", "language", "the app's own sources are English (inputs quoted)")

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

    def check_subagent(self, owners=None):
        subs = self.root / "library" / "subagents"
        if not subs.is_dir():
            return
        owners = owner_map() if owners is None else owners
        fails = warns = 0
        present = set()
        for d in sorted(p for p in subs.iterdir() if p.is_dir() and p.name.startswith("suba-")):
            name, spine = d.name, d / "SKILL.md"
            present.add(name)
            r = self.rel(spine)
            if not spine.is_file():
                fails += 1
                self.rec("FAIL", "subagent", f"{self.rel(d)}: no SKILL.md")
                continue
            text = spine.read_text(encoding="utf-8-sig")
            f = front_fields(text)
            if f.get("name") != name:
                fails += 1
                self.rec("FAIL", "subagent", f"{r}: name={f.get('name')!r} differs from its folder")
            owner, want = f.get("metadata.owner"), owners.get(name)
            if owner != want:
                fails += 1
                self.rec("FAIL", "subagent", f"{r}: metadata.owner={owner!r} but gov.py OWNER says {want!r}")
            for problem in contract_problems(name, self.root):
                fails += 1
                self.rec("FAIL", "subagent", f"{self.rel(d)}/contract.json: {problem}")
            if "<!-- regency:return:begin" not in text:
                fails += 1
                self.rec("FAIL", "subagent", f"{r}: no generated return block (regency:return markers); run build.py")
            if f.get("metadata.status") == "proposal":
                warns += 1
                self.rec("WARN", "subagent", f"{r}: proposal, awaiting the Regent's ratification (ALIGNMENT §9)")
            for link in sorted(set(REF_LINK.findall(text))):
                if not (d / link).exists():
                    fails += 1
                    self.rec("FAIL", "subagent", f"{r}: points to {link}, which does not exist")
            stamps = STAMP.findall(f.get("metadata.aligned", ""))
            if not stamps:
                warns += 1
                self.rec("WARN", "subagent", f"{r}: no metadata.aligned stamp; check it against its owner, then stamp")
            for doc, sha in stamps:
                target = self.root / doc
                if not target.is_file():
                    fails += 1
                    self.rec("FAIL", "subagent", f"{r}: aligned with {doc}, which does not exist")
                elif fingerprint(target) != sha:
                    warns += 1
                    self.rec("WARN", "subagent", f"{r}: drifted, {doc} changed since #{sha} (now #{fingerprint(target)});"
                                                 " re-read the suba against it, then re-stamp")
        for name in sorted(set(owners) - present):
            warns += 1
            self.rec("WARN", "subagent", f"gov.py OWNER names {name} ({owners[name]}), no folder in library/subagents")
        if not fails and not warns:
            self.rec("OK", "subagent", f"{len(present)} subagent(s) aligned with their owners")

    def run(self):
        for fn in (self.check_version, self.check_ids, self.check_legacy, self.check_language,
                   self.check_banned, self.check_canonical, self.check_suba, self.check_subagent):
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
        (root / "library" / "templates").mkdir()
        (root / "library" / "templates" / "README.md").write_text(
            "# Start\n\nPonto de partida para um projeto novo.\nAções do pedido\n"
            "Quote the input: `pode seguir`, \"vê isso\".\n", encoding="utf-8")
        (root / "library" / "conventions.md").write_text(
            "## 2. Language\n\nescreva sempre assim\n\n## 9. Verbs\n\n| prossiga, vê isso | queue |\n\n## 10. Next\n\nok\n",
            encoding="utf-8")
        (root / "scripts").mkdir()
        (root / "scripts" / "StringHelper.py").write_text("def parse_utils():\n    pass\n", encoding="utf-8")
        found = Checker(root).run()
        want = [("version", "is not a.b"), ("version", "versions differ"), ("legacy", "plan.md:1"),
                ("banned", "StringHelper"), ("banned", "parse_utils"), ("canonical", "readme.md"),
                ("suba", "must start with suba-"), ("suba", "must end with -vendor"),
                ("suba", "outside library/subagents"), ("language", "templates/README.md:3"),
                ("language", "templates/README.md:4"), ("language", "conventions.md:3")]
        for check, needle in want:
            hit = any(c == check and needle in m and lvl in ("FAIL", "WARN") for lvl, c, m in found)
            cases.append((hit, check, needle))
        ok_ids = any(c == "ids" and lvl == "OK" for lvl, c, _ in found)
        cases.append((ok_ids, "ids", "real grammar passes"))
        quiet = not any(c == "canonical" and "examples/" in m for _, c, m in found)
        cases.append((quiet, "canonical", "example files are exempt"))
        lang = [m for _, c, m in found if c == "language"]
        cases.append((not any("templates/README.md:5" in m for m in lang), "language", "quoted input is not source"))
        cases.append((not any("conventions.md:7" in m for m in lang), "language", "the Regent's verbs (§9) are input"))
        cases.append((not any("conventions.md:11" in m or "plan.md" in m for m in lang), "language", "English raises nothing"))
    with tempfile.TemporaryDirectory() as tmp:  # subagent: one clean suba and one planted defect per rule
        root = Path(tmp)
        team = root / "library" / "team"
        (team / "references").mkdir(parents=True)
        (team / "DV.md").write_text("role: DV\n", encoding="utf-8")
        real = Path(__file__).resolve().parent.parent
        for rel in ("library/ids.md", "library/team/references/packets.md", "library/subagents/envelope.schema.json"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text((real / rel).read_text(encoding="utf-8"), encoding="utf-8")
        sha = fingerprint(team / "DV.md")
        subs = root / "library" / "subagents"

        sound = {"returns": {"type": "object", "required": ["note"], "additionalProperties": False,
                             "properties": {"note": {"type": "string", "minLength": 1, "description": "a note"}}}}

        def suba(name, owner, aligned, link="references/doctrine.md", real_name=None, make_ref=True,
                 ret="## Return to the owner\n\n<!-- regency:return:begin -->\n<!-- regency:return:end -->\n", status="",
                 con=sound):
            d = subs / name
            (d / "references").mkdir(parents=True)
            if make_ref:
                (d / "references" / "doctrine.md").write_text("x\n", encoding="utf-8")
            if con is not None:
                (d / "contract.json").write_text(json.dumps(con), encoding="utf-8")
            (d / "SKILL.md").write_text(
                f'---\nname: {real_name or name}\ndescription: "x"\nmetadata:\n  owner: {owner}\n'
                f'  aligned: "{aligned}"\n{status}---\n\n{ret}\nDepth: [doctrine]({link})\n', encoding="utf-8")

        suba("suba-good", "DV", f"library/team/DV.md#{sha}")
        suba("suba-drift", "QA", "library/team/DV.md#000000000000")
        suba("suba-wrong", "DA", f"library/team/DV.md#{sha}", link="references/nope.md", real_name="suba-other")
        suba("suba-mute", "DV", f"library/team/DV.md#{sha}", ret="## Return\n\nWhatever seems right.\n")
        suba("suba-loose", "DV", f"library/team/DV.md#{sha}", con={"returns": {"type": "object", "properties": {"x": {}}}})
        suba("suba-bare", "DV", f"library/team/DV.md#{sha}", con=None)
        suba("suba-draft", "PO", f"library/team/DV.md#{sha}", status="  status: proposal\n")
        (subs / "suba-empty").mkdir()
        owners = {"suba-good": "DV", "suba-drift": "QA", "suba-wrong": "PO", "suba-empty": "DV", "suba-absent": "DA",
                  "suba-mute": "DV", "suba-draft": "PO", "suba-loose": "DV", "suba-bare": "DV"}
        ck = Checker(root)
        ck.check_subagent(owners)
        found = ck.out
        want = [("FAIL", "suba-wrong/SKILL.md: name="), ("FAIL", "metadata.owner='DA' but gov.py OWNER says 'PO'"),
                ("FAIL", "points to references/nope.md"), ("FAIL", "suba-empty: no SKILL.md"),
                ("WARN", "suba-drift/SKILL.md: drifted"), ("WARN", "names suba-absent (DA), no folder"),
                ("FAIL", "suba-mute/SKILL.md: no generated return block"), ("WARN", "suba-draft/SKILL.md: proposal"),
                ("FAIL", "suba-loose/contract.json: returns: /: open object"), ("FAIL", "suba-bare/contract.json: no contract.json")]
        for lvl, needle in want:
            cases.append((any(l == lvl and c == "subagent" and needle in m for l, c, m in found), "subagent", needle))
        cases.append((not any("suba-good" in m for _, _, m in found), "subagent", "a clean suba raises nothing"))
        (team / "DV.md").write_text("role: DV\nchanged\n", encoding="utf-8")
        ck = Checker(root)
        ck.check_subagent({"suba-good": "DV"})
        cases.append((any("suba-good/SKILL.md: drifted" in m for _, _, m in ck.out), "subagent",
                      "editing the owner's spec makes a clean suba drift"))
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
