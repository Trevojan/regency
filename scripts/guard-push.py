#!/usr/bin/env python3
"""guard-push.py - a Claude Code PreToolUse hook that blocks pushes to main (or master).

Why: "the Regent pushes main" must hold even when an agent forgets it (library/conventions.md §4).
Pushes of any OTHER branch pass. Only the protected branch names are guarded, on every remote.

Modes
  (no args)          hook mode: reads the PreToolUse JSON on stdin, answers on stdout
  --selftest         run the built-in decision table (no git needed); exit 1 on any mismatch
  --snippet          print the settings.json "hooks" block for THIS machine (absolute path)

Hook answers (exit code is always 0 so the JSON decides):
  deny  - the command pushes to a protected branch        -> the call is blocked, reason shown
  ask   - the target cannot be determined (variables, globs) -> the user is asked
  (nothing printed)  - not a push, or a push of another branch -> the call proceeds

What it understands: git push in a chain (&&, ||, ;, |, newlines, $( ), backticks), `git -C dir push`,
`git -c k=v push`, a full path to git.exe, env-var prefixes, `bash -c "..."` / `powershell -Command "..."`,
refspecs (src:dst, +src, HEAD, refs/heads/x), --delete, --all, --mirror, --dry-run, and a bare
`git push` (resolved from the current branch and its upstream).
What it does NOT understand: git aliases (`git p`), scripts that push internally, `gh pr merge`.
A missing/broken script FAILS OPEN in Claude Code, so run --selftest after moving this folder.

Pure standard library, Python 3.8+.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROTECTED = {"main", "master"}
SEPARATORS = set(";|&\n()`{}")
SHELLS = {"bash", "sh", "zsh", "dash", "powershell", "pwsh", "cmd", "eval", "env"}
TAKES_VALUE = {"-o", "--push-option", "--receive-pack", "--exec", "--repo"}
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


# ---------- tokenising -------------------------------------------------------------------------

def segments(cmd):
    """Split a shell/PowerShell command into segments of tokens (quotes removed). Quote-aware."""
    segs, cur, tok, quote, has = [], [], [], None, False
    i, n = 0, len(cmd)

    def end_tok():
        nonlocal tok, has
        if has or tok:
            cur.append("".join(tok))
        tok, has = [], False

    def end_seg():
        nonlocal cur
        end_tok()
        if cur:
            segs.append(cur)
        cur = []

    while i < n:
        c = cmd[i]
        if quote:
            if c == quote:
                quote = None
            else:
                tok.append(c)
        elif c in "'\"":
            quote, has = c, True
        elif c in SEPARATORS:
            end_seg()
        elif c.isspace():
            end_tok()
        elif c == "$" and cmd[i:i + 2] == "$(":
            end_seg()
            i += 1
        else:
            tok.append(c)
        i += 1
    end_seg()
    return segs


def basename(tok):
    return re.split(r"[\\/]", tok)[-1].lower()


def git_pushes(cmd, depth=0):
    """Yield (cwd_override, args_after_push) for every `git ... push ...` found in cmd."""
    if depth > 3:
        return
    for seg in segments(cmd):
        # shells carrying a command string: look inside the string arguments
        if any(basename(t).rsplit(".", 1)[0] in SHELLS for t in seg[:3]):
            for t in seg[1:]:
                if (" " in t or "\n" in t or ";" in t) and "git" in t and "push" in t:
                    yield from git_pushes(t, depth + 1)
        for i, t in enumerate(seg):
            if basename(t) not in ("git", "git.exe"):
                continue
            j, cwd = i + 1, None
            while j < len(seg) and seg[j].startswith("-"):
                opt = seg[j]
                if opt == "-C" and j + 1 < len(seg):
                    cwd = seg[j + 1]
                    j += 2
                elif opt in GIT_VALUE_OPTS and j + 1 < len(seg):
                    j += 2
                else:
                    j += 1
            if j < len(seg) and seg[j] == "push":
                yield cwd, seg[j + 1:]


# ---------- git facts --------------------------------------------------------------------------

def run_git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd or ".", *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def real_current(cwd):
    return run_git(cwd, "symbolic-ref", "--short", "-q", "HEAD")


def real_upstream(cwd):
    up = run_git(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    return up.split("/", 1)[1] if "/" in up else up


# ---------- decision ---------------------------------------------------------------------------

def norm(ref):
    ref = ref.lstrip("+")
    return ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref


def judge_push(args, cwd, current, upstream):
    """Return ('deny'|'ask'|'allow', reason) for one push."""
    flags, pos, i = set(), [], 0
    delete = False
    while i < len(args):
        a = args[i]
        if a.startswith("-") and a != "-":
            flags.add(a.split("=", 1)[0])
            if a in ("-d", "--delete"):
                delete = True
            if a in TAKES_VALUE and "=" not in a:
                i += 1
        else:
            pos.append(a)
        i += 1
    if flags & {"--dry-run", "-n"}:
        return "allow", ""
    if flags & {"--mirror", "--all", "--branches"}:
        return "deny", "pushes every branch, which includes main"
    has_repo = "--repo" in flags
    refspecs = pos if has_repo else pos[1:]
    if not refspecs:
        if flags & {"--tags"} and not flags & {"--follow-tags"}:
            return "allow", ""  # tags only
        cur = current(cwd)
        up = upstream(cwd)
        if cur in PROTECTED or up in PROTECTED:
            return "deny", f"a bare push from '{cur or '?'}' (upstream '{up or '?'}') pushes the protected branch"
        if not cur:
            return "ask", "cannot tell which branch a bare push would send"
        return "allow", ""
    for spec in refspecs:
        if re.search(r"[$%*{}]", spec):
            return "ask", f"cannot resolve the push target '{spec}'"
        s = spec.lstrip("+")
        if delete:
            src, dst = "", s
        elif ":" in s:
            src, dst = s.rsplit(":", 1)[0], s.rsplit(":", 1)[1]
        else:
            src, dst = s, s
        if dst in ("HEAD", "@"):
            dst = current(cwd)
        if not dst and ":" in s:
            return "ask", f"empty push destination in '{spec}'"
        if norm(dst) in PROTECTED:
            return "deny", f"'{spec}' pushes to the protected branch '{norm(dst)}'"
    return "allow", ""


def decide(command, hook_cwd, current=real_current, upstream=real_upstream):
    worst = ("allow", "")
    for cwd_override, args in git_pushes(command):
        cwd = cwd_override if cwd_override else hook_cwd
        if cwd_override and hook_cwd and not os.path.isabs(cwd_override):
            cwd = os.path.join(hook_cwd, cwd_override)
        verdict = judge_push(args, cwd, current, upstream)
        if verdict[0] == "deny":
            return verdict
        if verdict[0] == "ask" and worst[0] == "allow":
            worst = verdict
    return worst


MESSAGE = ("Pushing to {branch} is the Regent's act (regency conventions §4): {why}. "
           "Push your own branch instead, or ask the Regent to push main.")


def hook():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd or "push" not in cmd:
        return 0
    verdict, why = decide(cmd, data.get("cwd") or os.getcwd())
    if verdict == "allow":
        return 0
    reason = MESSAGE.format(branch="main/master", why=why) if verdict == "deny" else f"Unclear push target: {why}. Confirm before pushing."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": verdict,
                                              "permissionDecisionReason": reason}}))
    return 0


# ---------- self-test and snippet --------------------------------------------------------------

CASES = [  # command, current branch, upstream branch, expected
    ("git push origin main", "feat", "feat", "deny"),
    ("git push origin master", "feat", "feat", "deny"),
    ("git push origin feature/x", "main", "main", "allow"),
    ("git push", "main", "main", "deny"),
    ("git push", "feat", "feat", "allow"),
    ("git push", "feat", "main", "deny"),
    ("git push -u origin HEAD", "feat", "", "allow"),
    ("git push -u origin HEAD", "main", "", "deny"),
    ("git push origin HEAD:main", "feat", "feat", "deny"),
    ("git push origin feat:refs/heads/main", "feat", "feat", "deny"),
    ("git push origin +main", "feat", "feat", "deny"),
    ("git push --force origin main", "feat", "feat", "deny"),
    ("git push --force-with-lease origin feat", "feat", "feat", "allow"),
    ("git push --all", "feat", "feat", "deny"),
    ("git push --mirror origin", "feat", "feat", "deny"),
    ("git push origin --delete main", "feat", "feat", "deny"),
    ("git push origin :main", "feat", "feat", "deny"),
    ("git push origin --delete old-branch", "feat", "feat", "allow"),
    ("git -C ../other push origin main", "feat", "feat", "deny"),
    ("git -c user.name=x push origin main", "feat", "feat", "deny"),
    ("cd x && git push origin main", "feat", "feat", "deny"),
    ("git add . ; git commit -m x; git push origin master", "feat", "feat", "deny"),
    ("echo ok | git push origin main", "feat", "feat", "deny"),
    ("FOO=1 git push origin master", "feat", "feat", "deny"),
    ('bash -c "git push origin main"', "feat", "feat", "deny"),
    ("powershell -Command \"git push origin main\"", "feat", "feat", "deny"),
    ('"C:\\Program Files\\Git\\cmd\\git.exe" push origin main', "feat", "feat", "deny"),
    ("$(git push origin main)", "feat", "feat", "deny"),
    ("git push origin main --dry-run", "feat", "feat", "allow"),
    ("git push origin $BRANCH", "feat", "feat", "ask"),
    ("git push --tags", "main", "main", "allow"),
    ("git push --follow-tags", "main", "main", "deny"),
    ("git push origin main:feature", "feat", "feat", "allow"),
    ("git push origin feat", "main", "main", "allow"),
    ("git status", "main", "main", "allow"),
    ("git log --oneline | head -5", "main", "main", "allow"),
    ('echo "git push origin main"', "feat", "feat", "allow"),
    ("git commit -m 'fix: push origin main docs'", "feat", "feat", "allow"),
]


def selftest():
    bad = 0
    for cmd, cur, up, want in CASES:
        got, why = decide(cmd, ".", current=lambda c, cur=cur: cur, upstream=lambda c, up=up: up)
        if got != want:
            bad += 1
            print(f"MISMATCH  want {want:5} got {got:5}  {cmd!r}  ({why})")
    print(f"guard-push selftest: {len(CASES) - bad}/{len(CASES)} ok")
    return 1 if bad else 0


def snippet():
    here = str(Path(__file__).resolve()).replace("\\", "/")
    cmd = f'python "{here}"'
    block = {"hooks": {"PreToolUse": [
        {"matcher": "Bash", "hooks": [{"type": "command", "if": "Bash(git *)", "command": cmd}]},
        {"matcher": "PowerShell", "hooks": [{"type": "command", "if": "PowerShell(git *)", "command": cmd}]},
    ]}}
    print(json.dumps(block, indent=2))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else snippet() if "--snippet" in a else hook())
