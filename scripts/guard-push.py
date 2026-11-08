#!/usr/bin/env python3
"""guard-push.py - a Claude Code PreToolUse hook that blocks pushes to main (or master).

Why: "the Regent pushes main" must hold even when an agent forgets it (library/conventions.md §4).
Pushes of any OTHER branch pass. Only the protected branch names are guarded, on every remote.
A `push` grant of the Regent's that names the branch lets a push onto it through (library/judge.md §2).
Deleting it, --all, --mirror and a '+' refspec stay denied, and a failed lookup reads as no grant.

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
refspecs (src:dst, +src, HEAD, refs/heads/x, heads/x), --delete, --all, --mirror, --dry-run, flags as git
reads them (a unique prefix such as --del, a short cluster such as -fd), and a bare `git push` (resolved
from the current branch and its upstream).
It reads a command's text before it runs, and hooks/hooks.json fires it only when Claude Code's `if: git *` matches:
`cd x && git push ...` and `bash -c "git push ..."` reached it in a live session (2.1.302), but nothing here decides
what that filter lets through, so no row of the table says a given form gets this far.
What it does NOT read: a chain that changes branch first, revisions with braces, line continuations,
redirects glued to a word, substitutions, git aliases (`git p`), scripts that push internally, `gh pr
merge`, a push that configuration widens (`push.default=matching`, `remote.<name>.mirror`).
hook-refs.py stands behind it, on the refs git really sends (library/hooks.md §2).
A missing/broken script FAILS OPEN in Claude Code, so run --selftest after moving this folder.

Pure standard library, Python 3.8+.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
PROTECTED = {"main", "master"}
SEPARATORS = set(";|&\n()`{}")
SHELLS = {"bash", "sh", "zsh", "dash", "powershell", "pwsh", "cmd", "eval", "env"}
TAKES_VALUE = {"-o", "--push-option", "--receive-pack", "--exec", "--repo"}
PUSH_FLAGS = ("--all", "--atomic", "--branches", "--delete", "--dry-run", "--exec", "--follow-tags", "--force",
              "--force-if-includes", "--force-with-lease", "--ipv4", "--ipv6", "--mirror", "--no-dry-run", "--no-tags",
              "--no-verify", "--porcelain", "--progress", "--prune", "--push-option", "--quiet", "--receive-pack",
              "--recurse-submodules", "--repo", "--set-upstream", "--signed", "--tags", "--thin", "--verbose", "--verify")
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env", "--attr-source"}


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


HEREDOC = re.compile(r"<<(-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|\\?([A-Za-z_][A-Za-z0-9_]*))")
SUBSTITUTION = re.compile(r"\$\((?:[^()]|\([^()]*\))*\)|`[^`\n]*`")


def data_only(cmd):
    """The command as a shell would run it, with heredoc bodies that are only data taken out.

    A heredoc body is text fed to a command's stdin. It runs as commands only when a shell reads it
    (`bash <<'EOF'`, `cat <<EOF | sh`): then it stays. Otherwise a quoted delimiter (<<'EOF', <<"EOF",
    <<\\EOF) makes it pure data, so it goes; an unquoted one still expands $( ) and backticks, so only
    those substitutions stay. Text written about `rm -rf` or a push is never read as the act itself.
    """
    lines = (cmd or "").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            delim = m.group(2) or m.group(3) or m.group(4)
            quoted = bool(m.group(2) or m.group(3)) or line[m.start():m.end()].lstrip("<-  \t").startswith("\\")
            body = []
            while i < len(lines) and (lines[i].lstrip("\t") if m.group(1) else lines[i]) != delim:
                body.append(lines[i])
                i += 1
            closing = lines[i] if i < len(lines) else None
            i += 1 if closing is not None else 0
            fed_to_shell = any(basename(t).rsplit(".", 1)[0] in SHELLS for seg in segments(line) for t in seg)
            if fed_to_shell:
                out += body
            elif not quoted:
                out += [s for b in body for s in SUBSTITUTION.findall(b)]
            if closing is not None:
                out.append(closing)
    return "\n".join(out)


def basename(tok):
    return re.split(r"[\\/]", tok)[-1].lower()


def git_pushes(cmd, depth=0):
    """Yield (cwd_override, args_after_push) for every `git ... push ...` found in cmd."""
    if depth > 3:
        return
    for seg in segments(data_only(cmd)):
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
    """The branch a destination lands on: git also matches heads/main against refs/heads/main."""
    return re.sub(r"^(?:refs/)?heads/", "", ref.lstrip("+"))


def no_grant(branch, cwd):
    return False


def regent_grant(event):
    """The Judge's lookup for this event: (branch, cwd) -> covered. Any failure reads as no grant: the denial stands."""
    def covered(branch, cwd):
        try:
            import hook_wire as wire
            import judge
            return judge.covers(event, wire.repo_root(Path(cwd)), "push", [branch]) is not None
        except Exception:
            return False
    return covered


def flag_names(tok):
    """The flags one token sets, as git's option parser reads it: a long flag or a unique prefix of one (--del is
    --delete), or a cluster of short ones (-fd), which ends at -o because the rest of the token is its value."""
    if tok.startswith("--"):
        name = tok.split("=", 1)[0]
        hits = [f for f in PUSH_FLAGS if f.startswith(name)]
        return {hits[0] if len(hits) == 1 and name not in PUSH_FLAGS else name}
    names = set()
    for c in tok[1:]:
        names.add(f"-{c}")
        if c == "o":
            break
    return names


def judge_push(args, cwd, current, upstream, granted=no_grant):
    """Return ('deny'|'ask'|'allow', reason) for one push."""
    flags, pos, i = set(), [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("-") and a != "-":
            names = flag_names(a)
            flags |= names
            if names & TAKES_VALUE and "=" not in a and (a.startswith("--") or a.index("o") == len(a) - 1):
                i += 1  # the next token is its value, unless a short -o already holds one (-ofoo)
        else:
            pos.append(a)
        i += 1
    delete = bool(flags & {"-d", "--delete"})
    if flags & {"--dry-run", "-n"} and "--no-dry-run" not in flags:
        return "allow", ""
    if flags & {"--mirror", "--all", "--branches"}:
        return "deny", "pushes every branch, which includes main"
    passed = ("ask", "--no-verify skips the pre-push check") if "--no-verify" in flags else ("allow", "")
    has_repo = "--repo" in flags
    refspecs = pos if has_repo else pos[1:]
    if not refspecs:
        if flags & {"--tags"} and not flags & {"--follow-tags", "--no-tags"}:
            return passed  # tags only
        cur = current(cwd)
        up = upstream(cwd)
        if cur in PROTECTED or up in PROTECTED:
            if all(granted(b, cwd) for b in {cur, up} & PROTECTED):
                return passed
            return "deny", f"a bare push from '{cur or '?'}' (upstream '{up or '?'}') pushes the protected branch"
        if not cur:
            return "ask", "cannot tell which branch a bare push would send"
        return passed
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
            # a grant covers a push onto the branch, never its deletion or a '+' force
            if delete or not src or spec.startswith("+") or not granted(norm(dst), cwd):
                return "deny", f"'{spec}' pushes to the protected branch '{norm(dst)}'"
    return passed


def decide(command, hook_cwd, current=real_current, upstream=real_upstream, granted=no_grant):
    worst = ("allow", "")
    for cwd_override, args in git_pushes(command):
        cwd = cwd_override if cwd_override else hook_cwd
        if cwd_override and hook_cwd and not os.path.isabs(cwd_override):
            cwd = os.path.join(hook_cwd, cwd_override)
        verdict = judge_push(args, cwd, current, upstream, granted)
        if verdict[0] == "deny":
            return verdict
        if verdict[0] == "ask" and worst[0] == "allow":
            worst = verdict
    return worst


MESSAGE = ("Pushing to {branch} is the Regent's act (regency conventions §4): {why}. "
           "Push your own branch instead, or ask the Regent to push main. "
           "Only a `push` grant of the Regent's lifts this (library/judge.md §2).")


def hook():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd or "push" not in cmd:
        return 0
    verdict, why = decide(cmd, data.get("cwd") or os.getcwd(), granted=regent_grant(data))
    if verdict == "allow":
        return 0
    reason = MESSAGE.format(branch="main/master", why=why) if verdict == "deny" else f"{why}. Confirm before pushing."
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
    # heredocs: text written about a push is data; a body a shell reads, or a substitution, still runs
    ("cat > notes.md <<'EOF'\nnever run git push origin main\nEOF", "feat", "feat", "allow"),
    ("cat > notes.md <<\"EOF\"\n`git push origin main` is the Regent's\nEOF", "feat", "feat", "allow"),
    ("python3 - <<'PY'\nprint('git push origin main')\nPY\ngit push origin main", "feat", "feat", "deny"),
    ("bash <<'EOF'\ngit push origin main\nEOF", "feat", "feat", "deny"),
    ("cat <<'EOF' | sh\ngit push origin main\nEOF", "feat", "feat", "deny"),
    ("cat > out.txt <<EOF\n$(git push origin main)\nEOF", "feat", "feat", "deny"),
    ("cat > notes.md <<EOF\ngit push origin main opens this line, as text\nEOF", "feat", "feat", "allow"),
    # flags as git reads them, each form run against a real bare remote on 2026-11-06
    ("git push --del origin main", "feat", "feat", "deny"),
    ("git push -fd origin main", "feat", "feat", "deny"),
    ("git push --al origin", "feat", "feat", "deny"),
    ("git push --br origin", "feat", "feat", "deny"),
    ("git push --mir origin", "feat", "feat", "deny"),
    ("git push --m origin", "feat", "feat", "deny"),
    ("git push --dry origin main", "feat", "feat", "allow"),
    ("git push -un origin main", "feat", "feat", "allow"),
    ("git push -nd origin main", "feat", "feat", "allow"),
    ("git push --dry-run --no-dry-run origin main", "feat", "feat", "deny"),
    ("git push -odn origin main", "feat", "feat", "deny"),
    ("git push -o dn origin main", "feat", "feat", "deny"),
    ("git push -o main origin feat", "feat", "feat", "allow"),
    ("git push -uo main origin feat", "feat", "feat", "allow"),
    ("git push origin feat:heads/main", "feat", "feat", "deny"),
    ("git push origin HEAD:heads/master", "feat", "feat", "deny"),
    ("git push origin heads/main", "feat", "feat", "deny"),
    ("git push -ofoo origin main", "feat", "feat", "deny"),
    ("git push -oo origin main", "feat", "feat", "deny"),
    ("git push -uoo origin main", "feat", "feat", "deny"),
    ("git push -oo origin :master", "feat", "feat", "deny"),
    ("git push -d -ofoo origin master", "feat", "feat", "deny"),
    ("git push -ofoo --mirror origin", "feat", "feat", "deny"),
    ("git push --tags --no-tags", "main", "main", "deny"),
    ("git push --tag --no-ta origin", "main", "main", "deny"),
    ("git push --no-verify origin feat", "feat", "feat", "ask"),
    ("git push --no-verify origin main", "feat", "feat", "deny"),
]

GRANTED = [  # the same decision with a `push` grant of main in force
    ("git push origin main", "feat", "feat", "allow"),
    ("git push --force-with-lease origin plumbing testing main", "feat", "feat", "allow"),  # hook-hazard.py asks
    ("git push", "main", "main", "allow"),
    ("git push", "feat", "main", "allow"),
    ("git push origin HEAD:main", "feat", "feat", "allow"),
    ("git push origin master", "feat", "feat", "deny"),
    ("git push origin main master", "feat", "feat", "deny"),
    ("git push", "master", "master", "deny"),
    ("git push origin +main", "feat", "feat", "deny"),
    ("git push origin +feat:main", "feat", "feat", "deny"),
    ("git push origin --delete main", "feat", "feat", "deny"),
    ("git push origin :main", "feat", "feat", "deny"),
    ("git push --all", "feat", "feat", "deny"),
    ("git push --mirror origin", "feat", "feat", "deny"),
    ("git push origin $BRANCH", "feat", "feat", "ask"),
    ("git push --del origin main", "feat", "feat", "deny"),
    ("git push --de origin main", "feat", "feat", "deny"),
    ("git push -fd origin main", "feat", "feat", "deny"),
    ("git push -df origin main", "feat", "feat", "deny"),
    ("git push -ud origin main", "feat", "feat", "deny"),
    ("git push --al origin", "feat", "feat", "deny"),
    ("git push --mir origin", "feat", "feat", "deny"),
    ("git push --force-with-lease=main:abc origin main", "feat", "feat", "allow"),  # hook-hazard.py asks
    ("git push -fu origin main", "feat", "feat", "allow"),  # hook-hazard.py asks
    ("git push -odn origin main", "feat", "feat", "allow"),  # a push option, so a real push the grant covers
    ("git push origin feat:heads/main", "feat", "feat", "allow"),
    ("git push origin +feat:heads/main", "feat", "feat", "deny"),
    ("git push -ofoo origin main", "feat", "feat", "allow"),
    ("git push -ofoo --mirror origin", "feat", "feat", "deny"),
    ("git push", "master", "main", "deny"),
    ("git push --no-verify origin main", "feat", "feat", "ask"),
]


def lookup_cases():
    """The real lookup: a grant judge.py recorded opens main in its session and its repository only."""
    import hook_wire as wire
    import judge
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        os.environ["REGENCY_JUDGE_HOME"] = str(Path(tmp) / "home")
        os.environ.pop("REGENCY_JD", None)
        root, other = wire.build_fixture(Path(tmp) / "proj"), wire.build_fixture(Path(tmp) / "other")
        ev, ev2 = {"session_id": "s1"}, {"session_id": "s2"}
        judge.record(ev, root, "push main -- the re-authored history", "Regent: message")
        covered = regent_grant(ev)

        def wire_answer(sid):
            event = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"},
                     "session_id": sid, "cwd": str(root)}
            r = subprocess.run([sys.executable, __file__], input=json.dumps(event), capture_output=True, text=True, encoding="utf-8")
            return r.stdout.strip()

        return [(covered("main", root), "the Regent's grant covers its branch"),
                (not covered("master", root), "and no other"),
                (not regent_grant(ev2)("main", root), "a session grant stays in its session"),
                (not covered("main", other), "a session grant stays in its repository"),
                (not covered("main", None), "a failed lookup reads as no grant"),
                (wire_answer("s1") == "", "on the wire, the hook lets a granted push through"),
                ('"deny"' in wire_answer("s2"), "on the wire, the hook denies it to another session")]


def selftest():
    bad = 0
    for table, granted in ((CASES, no_grant), (GRANTED, lambda b, c: b == "main")):
        for cmd, cur, up, want in table:
            got, why = decide(cmd, ".", current=lambda c, cur=cur: cur, upstream=lambda c, up=up: up, granted=granted)
            if got != want:
                bad += 1
                print(f"MISMATCH  want {want:5} got {got:5}  {cmd!r}  ({why})")
    looked_up = lookup_cases()
    for ok, label in looked_up:
        if not ok:
            bad += 1
            print(f"MISMATCH  lookup: {label}")
    total = len(CASES) + len(GRANTED) + len(looked_up)
    print(f"guard-push selftest: {total - bad}/{total} ok")
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
