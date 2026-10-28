#!/usr/bin/env python3
"""doctor.py - is this copy of regency intact and portable?

Run from anywhere:  python scripts/doctor.py        (exit 0 = healthy, 1 = a FAIL was found)

Checks
  1. plugin manifest is valid JSON and names the plugin 'regency'
  2. registry <-> skills <-> generated commands are consistent (same as build.py --check)
  3. every skill has frontmatter: name == directory, description present and <= 1024 chars
  4. every repo-relative path written in backticks (library/..., scripts/..., skills/..., commands/...) resolves
  5. no machine-specific absolute path leaked into a tracked file (portability)
  6. all JSON and XML under the root parse
  7. the push guard's built-in decision table passes (scripts/guard-push.py --selftest)
  8. the four role-agent sources are valid; WARN if they are not installed (or are stale) in ~/.claude/agents
  9. frontmatter of skills, commands and agent sources parses strictly (an unquoted ": " drops every field), and
     no description carries an XML-like tag (`claude plugin validate` rejects the plugin for it)
 10. `claude plugin validate` on the components, when the CLI is available
 11. WARN while unapproved drafts exist in library/team/_draft
 12. hooks/hooks.json is wired as library/hooks.md declares: every command is a script in scripts/ run
     through ${CLAUDE_PLUGIN_ROOT} (R4.1), every required trigger is present, guards fail closed
     (onFailure: block), and there is no Stop hook (R4.5)
 13. the path-scoped rule sources (library/rules) are valid; WARN if they are not installed (or are stale) in ~/.claude/rules
 14. the Regent's conventions hold (scripts/conventions_check.py: a.b version, id grammar, O-levels,
     banned names, canonical UPPER_CASE, suba-/-vendor placement) and its self-test detects every planted defect
 15. every hook script passes its own --selftest, and answers the real wire: an empty event and a
     sample event on stdin give exit 0 and either nothing or valid JSON (a broken hook FAILS OPEN)
 16. the .ux/ scaffold holds (scripts/ux.py): its self-test detects every planted defect and scaffolds a
     throwaway project, the template tokens pass (roles, naming, computed contrast), theme.css matches
     them, the template brief parses
 17. the shortcuts engine holds (scripts/shortcuts.py --selftest): store, migration, node ids against
     vp.resolve, drift, refresh, index check and the state-block guard, one planted defect per rule (R7)

Pure standard library, Python 3.8+. Reads only; writes nothing (hook self-tests write to temp dirs).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"discard", ".git", "node_modules", "__pycache__"}
# documents that describe OTHER projects' paths or are verbatim imports: not scanned for path/abs-path rules
IMPORTED = ("library/team/_draft/", "library/templates/", "library/examples/", "library/team/ORBITAL_AGENTS.md",
            "library/engines/", "library/orders/")
ABS_PATTERNS = [re.compile(p) for p in (
    r"[A-Za-z]:\\+Users\\", r"[A-Za-z]:/Users/", r"/Users/[A-Za-z0-9_.-]+/", r"/home/[A-Za-z0-9_.-]+/", r"/mnt/(user|skills|data)",
    r"AppData[\\/]",
)]
PATH_TOKEN = re.compile(r"`((?:library|scripts|skills|commands)/[^`\s<>*{}|]*)`")
HOOK_SCRIPT = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/([A-Za-z0-9_.-]+\.py)")
# (event, matcher value that must be covered, script) — the wiring library/hooks.md declares
REQUIRED_WIRING = (
    ("PreToolUse", "Bash", "guard-push.py"), ("PreToolUse", "PowerShell", "guard-push.py"),
    ("PreToolUse", "Bash", "hook-hazard.py"), ("PreToolUse", "PowerShell", "hook-hazard.py"),
    ("PreToolUse", "Edit", "hook-acts-guard.py"), ("PreToolUse", "Write", "hook-acts-guard.py"),
    ("PreToolUse", "NotebookEdit", "hook-acts-guard.py"),
    ("PostToolUse", "Edit", "hook-lineage.py"), ("PostToolUse", "Write", "hook-lineage.py"),
    ("PostToolUse", "Bash", "hook-hazard.py"), ("PostToolUse", "PowerShell", "hook-hazard.py"),
    ("PostToolUse", "Agent", "hook-hazard.py"), ("PostToolUse", "Task", "hook-hazard.py"),
    ("PostToolUse", "Edit", "hook-journal.py"), ("PostToolUse", "Bash", "hook-journal.py"),
    ("SessionStart", "startup", "hook-resume.py"), ("SessionStart", "resume", "hook-resume.py"),
    ("SessionStart", "compact", "hook-resume.py"),
    ("UserPromptSubmit", "", "hook-verbs.py"),
    ("PreCompact", "", "hook-journal.py"), ("SubagentStop", "", "hook-journal.py"),
    ("SessionEnd", "", "hook-shortcuts.py"),
    ("SubagentStart", "", "hook-gov.py"), ("PostToolUse", "Agent", "hook-gov.py"), ("PostToolUse", "Task", "hook-gov.py"),
)
GUARDS = {"guard-push.py", "hook-hazard.py", "hook-acts-guard.py"}
FORBIDDEN_EVENTS = {"Stop": "R4.5: no Stop hook; the next-step line lives in each playbook"}

results = []


def rec(level, msg):
    results.append((level, msg))


def files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            yield p


def rel(p):
    return p.relative_to(ROOT).as_posix()


def frontmatter(text):
    m = re.match(r"^﻿?---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).split("\n"):
        k = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if k:
            out[k.group(1)] = k.group(2).strip().strip('"')
    return out


def check_manifest():
    p = ROOT / ".claude-plugin" / "plugin.json"
    if not p.is_file():
        return rec("FAIL", ".claude-plugin/plugin.json is missing")
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return rec("FAIL", f"plugin.json is not valid JSON: {e}")
    if d.get("name") != "regency":
        rec("FAIL", f"plugin.json name is {d.get('name')!r}, expected 'regency'")
    else:
        rec("OK", f"plugin.json: name=regency version={d.get('version', '?')}")


def check_build():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), "--check"],
                       capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout + r.stderr).strip()
    rec("OK" if r.returncode == 0 else "FAIL", "build --check: " + out.replace("\n", " | "))


def check_skills():
    reg = json.loads((ROOT / "library" / "registry.json").read_text(encoding="utf-8"))
    declared = {c["skill"] for c in reg["commands"]}
    dirs = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    for missing in sorted(declared - dirs):
        rec("FAIL", f"registry names skill '{missing}' but skills/{missing}/SKILL.md does not exist")
    for orphan in sorted(dirs - declared):
        rec("FAIL", f"skills/{orphan}/ exists but no registry command uses it")
    for d in sorted(dirs):
        text = (ROOT / "skills" / d / "SKILL.md").read_text(encoding="utf-8")
        fm = frontmatter(text)
        if fm is None:
            rec("FAIL", f"skills/{d}/SKILL.md has no frontmatter")
            continue
        if fm.get("name") != d:
            rec("FAIL", f"skills/{d}/SKILL.md name is {fm.get('name')!r}, must equal the directory '{d}'")
        desc = fm.get("description", "")
        if not desc:
            rec("FAIL", f"skills/{d}/SKILL.md has no description")
        elif len(desc) > 1024:
            rec("FAIL", f"skills/{d}/SKILL.md description is {len(desc)} chars (limit 1024)")
    rec("OK", f"{len(dirs)} skill(s) checked against the registry")


def check_paths():
    bad = 0
    for p in files():
        r = rel(p)
        if p.suffix != ".md" or r.startswith(IMPORTED):
            continue
        for tok in PATH_TOKEN.findall(p.read_text(encoding="utf-8-sig", errors="replace")):
            t = tok.rstrip(".,;:)")
            segs = [s.rsplit(".", 1)[0] for s in t.split("/")]
            if "…" in t or "..." in t or any(len(s) == 1 for s in segs):  # placeholder, not a real path
                continue
            if not (ROOT / t).exists():
                rec("FAIL", f"{r}: path `{t}` does not resolve")
                bad += 1
    if not bad:
        rec("OK", "every backticked repo-relative path resolves")


def check_absolute_paths():
    bad = 0
    for p in files():
        r = rel(p)
        if p.suffix.lower() in {".zip", ".skill", ".png", ".jpg", ".gif", ".pdf"}:
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        for pat in ABS_PATTERNS:
            m = pat.search(text)
            if m:
                line = text[: m.start()].count("\n") + 1
                lvl = "WARN" if r.startswith(("library/team/_draft/", "library/templates/", "library/examples/", "library/engines/")) else "FAIL"
                rec(lvl, f"{r}:{line}: machine-specific path {m.group(0)!r}")
                bad += 1
                break
    if not bad:
        rec("OK", "no machine-specific absolute paths")


def check_parse():
    n = 0
    for p in files():
        if p.suffix == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8-sig"))
                n += 1
            except Exception as e:
                rec("FAIL", f"{rel(p)}: invalid JSON ({e})")
        elif p.suffix == ".xml":
            try:
                ET.fromstring(p.read_bytes())
                n += 1
            except Exception as e:
                rec("FAIL", f"{rel(p)}: invalid XML ({e})")
    rec("OK", f"{n} JSON/XML file(s) parse")


def check_guard():
    g = ROOT / "scripts" / "guard-push.py"
    if not g.is_file():
        return rec("FAIL", "scripts/guard-push.py is missing")
    r = subprocess.run([sys.executable, str(g), "--selftest"], capture_output=True, text=True, encoding="utf-8")
    out = " | ".join((r.stdout + r.stderr).strip().splitlines())
    rec("OK" if r.returncode == 0 else "FAIL", "guard-push: " + out)


def check_agents():
    s = ROOT / "scripts" / "install-agents.py"
    if not s.is_file():
        return rec("FAIL", "scripts/install-agents.py is missing")
    r = subprocess.run([sys.executable, str(s), "--check"], capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    broken = [l for l in lines if l.startswith("SOURCE")]
    if broken:
        return rec("FAIL", "agent sources: " + " | ".join(broken))
    off = [l for l in lines if not l.startswith("ok")]
    if off:
        rec("WARN", "role agents not (fully) installed on this machine: " + " | ".join(" ".join(l.split()) for l in off)
            + "  -> python scripts/install-agents.py")
    else:
        rec("OK", f"{len(lines)} role agent(s) installed and current in ~/.claude/agents")


def hook_entries():
    """[(event, matcher, handler)] from hooks/hooks.json; raises ValueError when it does not parse."""
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    out = []
    for event, groups in (data.get("hooks") or {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                out.append((event, g.get("matcher", ""), h))
    return out


def covers(matcher, value):
    if not matcher or matcher == "*":
        return True
    if not value:
        return False
    return value in [m.strip() for m in re.split(r"[|,]", matcher)]


def check_hooks():
    h = ROOT / "hooks" / "hooks.json"
    if not h.is_file():
        return rec("FAIL", "hooks/hooks.json is missing: the plugin would ship without its guards")
    try:
        entries = hook_entries()
    except ValueError as e:
        return rec("FAIL", f"hooks/hooks.json does not parse: {e}")
    bad = 0
    for event, why in FORBIDDEN_EVENTS.items():
        if any(e == event for e, _, _ in entries):
            bad += 1
            rec("FAIL", f"hooks/hooks.json wires {event}: {why}")
    for event, matcher, h in entries:
        cmd = h.get("command", "")
        m = HOOK_SCRIPT.search(cmd)
        if h.get("type") != "command" or not m:
            bad += 1
            rec("FAIL", f"hooks/hooks.json {event}[{matcher}]: not a ${{CLAUDE_PLUGIN_ROOT}}/scripts/*.py command (R4.1)")
            continue
        if not (ROOT / "scripts" / m.group(1)).is_file():
            bad += 1
            rec("FAIL", f"hooks/hooks.json {event}[{matcher}]: scripts/{m.group(1)} does not exist")
        if event == "PreToolUse" and m.group(1) in GUARDS and h.get("onFailure") != "block":
            rec("WARN", f"hooks/hooks.json {event}[{matcher}] {m.group(1)}: guard without onFailure=block fails open")
    for event, value, script in REQUIRED_WIRING:
        if not any(e == event and covers(mt, value) and script in h.get("command", "") for e, mt, h in entries):
            bad += 1
            rec("FAIL", f"hooks/hooks.json: {script} is not wired to {event}[{value or '*'}] (library/hooks.md)")
    if not bad:
        n = len({HOOK_SCRIPT.search(h.get('command', '')).group(1) for _, _, h in entries})
        rec("OK", f"hooks/hooks.json: {len(entries)} handler(s), {n} script(s), wiring matches library/hooks.md, no Stop hook")


SAMPLE_EVENTS = {  # one realistic event per script, fed through stdin exactly as Claude Code does
    "guard-push.py": {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
    "hook-hazard.py": {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf build"}},
    "hook-acts-guard.py": {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "x/.scope/a.txt"}},
    "hook-lineage.py": {"hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_input": {"file_path": "nowhere.txt"}},
    "hook-journal.py": {"hook_event_name": "PreCompact", "trigger": "auto"},
    "hook-resume.py": {"hook_event_name": "SessionStart", "source": "startup"},
    "hook-shortcuts.py": {"hook_event_name": "SessionEnd", "reason": "other"},
    "hook-verbs.py": {"hook_event_name": "UserPromptSubmit", "prompt": "prossiga"},
    "hook-gov.py": {"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "suba-validator"},
                    "tool_response": "gov: order=G2 · mode=co · element=image · from=QA · to=RGN\nask: approve SPEC v3"},
}


def check_hook_scripts():
    try:
        scripts = sorted({HOOK_SCRIPT.search(h.get("command", "")).group(1) for _, _, h in hook_entries()
                          if HOOK_SCRIPT.search(h.get("command", ""))})
    except (OSError, ValueError):
        return rec("FAIL", "hook scripts: hooks/hooks.json unreadable")
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, REGENCY_HOOK_STATE=str(Path(tmp) / "state"), CLAUDE_PLUGIN_ROOT=str(ROOT))
        env.pop("CLAUDE_PROJECT_DIR", None)
        for s in scripts:
            path = ROOT / "scripts" / s
            if not path.is_file():
                continue  # reported by check_hooks
            t = subprocess.run([sys.executable, str(path), "--selftest"], capture_output=True, text=True,
                               encoding="utf-8", env=env, cwd=tmp)
            last = (t.stdout.strip().splitlines() or ["(no output)"])[-1]
            if t.returncode != 0:
                misses = [l for l in t.stdout.splitlines() if l.startswith(("MISS", "MISMATCH"))]
                rec("FAIL", f"{s} --selftest: {last} | " + " | ".join(misses[:3]))
                continue
            for label, payload in (("empty event", "{}"), ("sample event", json.dumps(dict(SAMPLE_EVENTS.get(s, {}), cwd=tmp)))):
                w = subprocess.run([sys.executable, str(path)], input=payload, capture_output=True, text=True,
                                   encoding="utf-8", env=env, cwd=tmp, timeout=30)
                out = w.stdout.strip()
                ok = w.returncode == 0
                if ok and out:
                    try:
                        ok = isinstance(json.loads(out), dict)
                    except ValueError:
                        ok = False
                if not ok:
                    rec("FAIL", f"{s} on the wire ({label}): exit {w.returncode}, stdout {out[:120]!r}, stderr {w.stderr.strip()[:120]!r}")
                    break
            else:
                rec("OK", f"{s}: {last}; answers the wire")


def check_ux():
    s = ROOT / "scripts" / "ux.py"
    if not s.is_file():
        return rec("FAIL", "scripts/ux.py is missing")
    runs = (("selftest", ["--selftest"]), ("tokens", ["check"]), ("theme.css", ["synced"]),
            ("brief", ["brief", str(ROOT / "library" / "templates" / "ux" / "BRIEF.md")]))
    for label, args in runs:
        r = subprocess.run([sys.executable, str(s), *args], capture_output=True, text=True, encoding="utf-8")
        lines = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
        if r.returncode != 0:
            bad = [l for l in lines if l.startswith(("FAIL", "MISS"))] or lines[-1:]
            rec("FAIL", f"ux {label}: " + " | ".join(bad[:3]))
        else:
            last = lines[-1] if label == "selftest" else next((l.split(None, 1)[1] for l in lines if l.startswith("OK")), "ok")
            rec("OK", f"ux {label}: {last}")


def check_shortcuts():
    s = ROOT / "scripts" / "shortcuts.py"
    if not s.is_file():
        return rec("FAIL", "scripts/shortcuts.py is missing")
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, REGENCY_HOOK_STATE=str(Path(tmp) / "state"))
        r = subprocess.run([sys.executable, str(s), "--selftest"], capture_output=True, text=True,
                           encoding="utf-8", env=env, cwd=tmp)
    lines = [l for l in r.stdout.strip().splitlines() if l.strip()] or ["(no output)"]
    if r.returncode != 0:
        rec("FAIL", "shortcuts selftest: " + " | ".join([l for l in lines if l.startswith("MISS")][:3] or lines[-1:]))
    else:
        rec("OK", f"shortcuts: {lines[-1]}")


def check_rules():
    s = ROOT / "scripts" / "install-rules.py"
    if not s.is_file():
        return rec("FAIL", "scripts/install-rules.py is missing")
    r = subprocess.run([sys.executable, str(s), "--check"], capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    broken = [l for l in lines if l.startswith("SOURCE") or l.startswith("no rule sources")]
    if broken:
        return rec("FAIL", "rule sources: " + " | ".join(broken))
    off = [l for l in lines if not l.startswith("ok")]
    if off:
        rec("WARN", "path-scoped rules not (fully) installed on this machine: " + " | ".join(" ".join(l.split()) for l in off)
            + "  -> python scripts/install-rules.py")
    else:
        rec("OK", f"{len(lines)} path-scoped rule(s) installed and current in ~/.claude/rules")


def check_conventions():
    s = ROOT / "scripts" / "conventions_check.py"
    if not s.is_file():
        return rec("FAIL", "scripts/conventions_check.py is missing")
    t = subprocess.run([sys.executable, str(s), "--selftest"], capture_output=True, text=True, encoding="utf-8")
    if t.returncode != 0:
        rec("FAIL", "conventions selftest: " + " | ".join(l for l in t.stdout.splitlines() if l.startswith("MISS")))
    r = subprocess.run([sys.executable, str(s)], capture_output=True, text=True, encoding="utf-8")
    for line in (r.stdout + r.stderr).strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] in ("OK", "WARN", "FAIL"):
            rec(parts[0], "conventions " + parts[1])


RISKY_START = tuple("[{*&!|>%@`")
XML_LIKE = re.compile(r"<[A-Za-z/!?][^>]*>?")


def frontmatter_risks(path):
    """Unquoted frontmatter values the YAML parser rejects (the runtime then drops ALL the fields)."""
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return []
    out = []
    for i, line in enumerate(m.group(1).split("\n"), 2):
        k = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not k or not k.group(2):
            continue
        v = k.group(2)
        if v[0] == '"':
            ok = len(v) > 1 and v.endswith('"') and '"' not in v[1:-1].replace('\\"', "")
        elif v[0] == "'":
            ok = len(v) > 1 and v.endswith("'")
        else:
            ok = not (": " in v or " #" in v or v[0] in RISKY_START or v.endswith(":"))
        if not ok:
            out.append(f"{rel(path)}:{i}: unquoted or malformed value for '{k.group(1)}' - quote it")
        if k.group(1) == "description" and XML_LIKE.search(v):
            out.append(f"{rel(path)}:{i}: description contains {XML_LIKE.search(v).group(0)!r}, which plugin validation "
                       "rejects as an XML tag - write it without angle brackets")
    return out


def check_frontmatter():
    bad = []
    for pat in ("skills/*/SKILL.md", "commands/**/*.md", "library/agents/*.md"):
        for p in sorted(ROOT.glob(pat)):
            bad += frontmatter_risks(p)
    for b in bad:
        rec("FAIL", "frontmatter: " + b)
    if not bad:
        rec("OK", "frontmatter of skills, commands and agents is strictly parseable")


def check_cli_validate():
    cli = shutil.which("claude")
    if not cli:
        return rec("WARN", "claude CLI not on PATH: could not run 'claude plugin validate' on the components")
    r = subprocess.run([cli, "plugin", "validate", str(ROOT / ".claude-plugin" / "plugin.json")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout + r.stderr
    errs = [l.strip() for l in out.splitlines() if l.strip().startswith("❯") and "frontmatter" in l or "✘ Found" in l]
    if r.returncode != 0 or "Validation failed" in out:
        rec("FAIL", "claude plugin validate (components): " + " | ".join(errs[:4] or ["see the CLI output"]))
    else:
        rec("OK", "claude plugin validate (components) passed")


def check_drafts():
    d = ROOT / "library" / "team" / "_draft"
    if d.is_dir():
        n = sum(1 for p in d.rglob("*") if p.is_file())
        rec("WARN", f"{n} unapproved draft file(s) in library/team/_draft: review the report in that folder (SECOND_PASS_REPORT.md)")


CHECKS = (check_manifest, check_build, check_skills, check_paths, check_absolute_paths, check_parse, check_guard,
          check_agents, check_frontmatter, check_cli_validate, check_drafts, check_hooks, check_rules,
          check_conventions, check_hook_scripts, check_ux, check_shortcuts)


def main(argv):
    if sys.version_info < (3, 8):
        print("FAIL python 3.8+ required")
        return 1
    only = {a[len("--only="):] for a in argv if a.startswith("--only=")}
    for fn in CHECKS:
        if not only or fn.__name__[len("check_"):] in only:
            try:
                fn()
            except Exception as e:  # noqa: BLE001 - one broken check must not hide the others
                rec("FAIL", f"{fn.__name__} crashed: {type(e).__name__}: {e}")
    order = {"FAIL": 0, "WARN": 1, "OK": 2}
    for lvl, msg in sorted(results, key=lambda x: order[x[0]]):
        print(f"{lvl:<4}  {msg}")
    fails = sum(1 for l, _ in results if l == "FAIL")
    warns = sum(1 for l, _ in results if l == "WARN")
    print(f"\nregency doctor: {fails} fail, {warns} warn -> {'HEALTHY' if not fails else 'NOT HEALTHY'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
