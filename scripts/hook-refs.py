#!/usr/bin/env python3
"""hook-refs.py - the push guard that reads what git is really sending, not what a command says.

guard-push.py reads a command's text before it runs, so a chain that changes branch first, a wrapper, a line continuation
or a revision such as HEAD^{}:main goes past it. git hands its pre-push hook the refs themselves, after all of that has
been resolved, so nothing here reads a command (library/hooks.md §2; the Regent's call, 2026-11-06).

  SessionStart   writes a small stub to the repository's .git/hooks/pre-push, and rewrites its own stub when the plugin
                 moved. hook-hazard.py does the same for a repository a push is about to run in. It never replaces a
                 hook it did not write, and says so in one context line: another pre-push is there, or core.hooksPath
                 sends hooks elsewhere.
  --pre-push     what the stub runs. A push onto main or master needs a `push` grant for that branch; deleting one never
                 passes; a forced update also needs a `history **` grant. Any failure refuses.

The stub passes at once in a shell Claude Code did not start (CLAUDE_CODE_SESSION_ID, CLAUDECODE), so the Regent's own
terminal and GitHub Desktop are never touched.

What it promises: it stops an agent that forgets. --no-verify, -c core.hooksPath= and git send-pack skip it, and a
repository with no stub has only the text guard. An agent set on evading the guards with the Regent's credentials is out
of reach of any local check (conventions §5).

Modes:  (no args) hook · --pre-push <remote> <url> · --install [dir] · --check [dir] · --selftest
Pure standard library, Python 3.8+.
"""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_wire as wire  # noqa: E402
import judge  # noqa: E402  (the Regent's grants, R15)

MARK = "# regency:hook-refs"
ZERO = re.compile(r"^0+$")
BRANCH = "refs/heads/"
SESSION_VARS = ("CLAUDE_CODE_SESSION_ID", "CLAUDECODE")


# ---------- the stub ---------------------------------------------------------------------------

def stub(script=None, python=None):
    script = Path(script or __file__).resolve().as_posix()
    python = Path(python or sys.executable).as_posix()
    return ("#!/bin/sh\n"
            f"{MARK}: scripts/hook-refs.py writes this file and rewrites it when the plugin moves.\n"
            "# A shell Claude Code did not start passes at once: your own terminal and GitHub Desktop are untouched.\n"
            '[ -n "$CLAUDE_CODE_SESSION_ID$CLAUDECODE" ] || exit 0\n'
            f'[ -f "{script}" ] || {{ echo "regency: {script} is gone, so this push is refused; start a new session" >&2; exit 1; }}\n'
            f'exec "{python}" "{script}" --pre-push "$@"\n')


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def survey(cwd):
    """(state, detail, target): written or rewritten when a stub is owed, else current, foreign, managed or absent."""
    if git(cwd, "rev-parse", "--is-bare-repository") != "false":
        return "absent", f"{cwd} is not a working repository", None
    where = git(cwd, "config", "--get", "core.hooksPath")
    if where:
        return "managed", f"core.hooksPath sends this repository's hooks to {where}", None
    target = Path(cwd) / git(cwd, "rev-parse", "--git-common-dir") / "hooks" / "pre-push"
    old = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else None
    if old is None:
        return "written", str(target), target
    if MARK not in old:
        return "foreign", f"{target} is not regency's", None
    return ("current", str(target), None) if old == stub() else ("rewritten", str(target), target)


def install(cwd):
    """Write the stub where one is owed; returns (state, detail). Never replaces a hook it did not write."""
    state, detail, target = survey(cwd)
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stub().encode("utf-8"))
        os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return state, detail


# ---------- the check --------------------------------------------------------------------------

def refused(lines, may_push, may_force, descends):
    """Why git must not send these refs, or None. lines: (local ref, local id, remote ref, remote id), as git gives them."""
    for line in lines:
        if len(line) != 4:
            return f"git sent a line this check cannot read: {' '.join(line)}"
        _, new, ref, old = line
        branch = ref[len(BRANCH):] if ref.startswith(BRANCH) else None
        if branch not in judge.PUSH_BRANCHES:
            continue
        if ZERO.match(new):
            return f"this push deletes '{branch}', which no grant covers"
        if not may_push(branch):
            return f"this push lands on '{branch}' with no `push` grant in force"
        if not ZERO.match(old) and not descends(old, new) and not may_force():
            return f"this push forces '{branch}', which also needs a `history **` grant"
    return None


def pre_push():
    if not any(os.environ.get(v) for v in SESSION_VARS):
        return 0
    try:
        lines = [tuple(l.split()) for l in sys.stdin.read().splitlines() if l.strip()]
        event, repo = judge.shell_event(), wire.repo_root(Path.cwd())
        why = refused(lines, lambda b: judge.covers(event, repo, "push", [b]) is not None,
                      lambda: judge.covers(event, repo, "history", []) is not None,
                      lambda old, new: git(Path.cwd(), "merge-base", "--is-ancestor", old, new) is not None)
    except Exception as e:  # noqa: BLE001 - in an agent's shell, a check that cannot read the grants refuses
        why = f"the grants could not be read ({type(e).__name__}: {e})"
    if why is None:
        return 0
    print(f"regency: {why}. Pushing to main is the Regent's act (conventions §4); only a `push` grant of theirs lifts this "
          "(library/judge.md §2).", file=sys.stderr)
    return 1


def respond(event):
    if event.get("hook_event_name") not in (None, "SessionStart"):
        return None
    state, detail = install(event.get("cwd") or os.getcwd())
    if state == "written":
        return wire.context("SessionStart", f"regency wrote its pre-push check: {detail} (library/hooks.md §2)")
    if state in ("foreign", "managed"):
        return wire.context("SessionStart", f"regency: no pre-push check here, because {detail}; only the text guard "
                                            "stands over main (library/hooks.md §2)")
    return None


# ---------- self-test ----------------------------------------------------------------------------

def remove_tree(path):
    for folder, _, files in os.walk(path):  # git keeps its objects read-only, which Windows refuses to delete
        for f in files:
            try:
                os.chmod(os.path.join(folder, f), stat.S_IWRITE | stat.S_IREAD)
            except OSError:  # health: allow-silent rmtree below reports nothing either; this is a temp folder
                pass
    shutil.rmtree(path, ignore_errors=True)


def run(cwd, *args, env=None):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)


def commit(cwd, name):
    (Path(cwd) / name).write_text(name, encoding="utf-8")
    run(cwd, "add", name)
    run(cwd, "commit", "-q", "-m", name)


def pure_cases():
    yes, no = (lambda *_: True), (lambda *_: False)
    a, b, z = "a" * 40, "b" * 40, "0" * 40
    line = lambda new, ref="refs/heads/main", old=a: ("refs/heads/x", new, ref, old)  # noqa: E731
    return [(refused([line(b, "refs/heads/feat")], no, no, no) is None, "another branch passes"),
            (refused([line(b, "refs/tags/main")], no, no, no) is None, "a tag named main is not the branch"),
            ("no `push` grant" in (refused([line(b)], no, no, yes) or ""), "main with no grant is refused"),
            (refused([line(b)], yes, no, yes) is None, "main with a grant passes when it descends"),
            (refused([line(b, old=z)], yes, no, no) is None, "a new main with a grant has nothing to force"),
            ("forces" in (refused([line(b)], yes, no, no) or ""), "a forced main needs history too"),
            (refused([line(b)], yes, yes, no) is None, "a forced main with both grants passes"),
            ("deletes" in (refused([line(z)], yes, yes, yes) or ""), "deleting main never passes"),
            ("cannot read" in (refused([("x", "y")], yes, yes, yes) or ""), "a line it cannot read refuses")]


def real_git_cases(tmp):
    """Real git on a throwaway bare remote: the refs, not the text. Every form is one that got past the text guard."""
    fix, cases = Path(tmp).resolve() / "fix", []
    fix.mkdir()
    remote, work = fix / "remote.git", fix / "work"
    run(fix, "init", "-q", "--bare", "-b", "main", str(remote))
    run(fix, "clone", "-q", str(remote), "work")
    run(work, "checkout", "-q", "-b", "main")
    commit(work, "A")
    run(work, "branch", "master")
    run(work, "branch", "feat")
    run(work, "push", "-q", "origin", "main", "master", "feat")
    for branch, name in (("feat", "C"), ("master", "M"), ("main", "B")):
        run(work, "checkout", "-q", branch)
        commit(work, name)
    run(work, "checkout", "-q", "feat")
    install(work)

    state, home = fix / "state", fix / "home"
    agent = dict(os.environ, CLAUDE_CODE_SESSION_ID="s1", REGENCY_HOOK_STATE=str(state), REGENCY_JUDGE_HOME=str(home))
    for k in ("CLAUDE_PLUGIN_DATA", "CLAUDE_CONFIG_DIR", "REGENCY_JD"):
        agent.pop(k, None)
    regent = {k: v for k, v in agent.items() if k not in SESSION_VARS}

    def tips():
        return run(remote, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads").stdout

    start = tips()

    def lands(*args, env=agent):
        """True when the push moved a ref on the remote; the remote goes back to where it was either way."""
        run(work, *args, env=env)
        moved = tips() != start
        for row in start.splitlines():
            ref, sha = row.split()
            run(remote, "update-ref", ref, sha)
        return moved

    os.environ.update(REGENCY_HOOK_STATE=str(state), REGENCY_JUDGE_HOME=str(home))
    for form in (["push", "origin", "main"], ["push", "origin", "feat:main"], ["push", "origin", "feat:heads/main"],
                 ["push", "origin", "HEAD^{}:main"], ["push", "origin", "HEAD@{0}:main"], ["push", "origin", ":main"],
                 ["push", "--delete", "origin", "master"], ["push", "--mirror", "origin"], ["push", "--all", "origin"],
                 ["push", "-ofoo", "origin", "main"], ["-c", "alias.p=push", "p", "origin", "main"],
                 ["-c", "push.default=matching", "push"], ["-c", "remote.origin.push=feat:main", "push", "origin"]):
        cases.append((not lands(*form), f"no grant, refused: git {' '.join(form)}"))
    run(work, "checkout", "-q", "main")
    cases.append((not lands("push"), "no grant, refused: a bare push after switching to main"))
    cases.append((not lands("push", "origin", "HEAD"), "no grant, refused: HEAD after switching to main"))
    run(work, "checkout", "-q", "feat")
    cases.append((lands("push", "origin", "feat"), "another branch still lands"))
    cases.append((lands("push", "origin", "main", env=regent), "a shell Claude Code did not start lands: the Regent's"))

    judge.record({"session_id": "s1"}, work, "push main -- planted for the test", "Regent: message")
    cases.append((lands("push", "origin", "main"), "under a push grant, main lands"))
    cases.append((not lands("push", "origin", ":main"), "under a push grant, deleting main is refused"))
    cases.append((not lands("push", "origin", "master"), "under a grant of main, master is refused"))
    other = dict(agent, CLAUDE_CODE_SESSION_ID="s2")
    cases.append((not lands("push", "origin", "main", env=other), "a session grant stays in its session"))

    run(work, "branch", "-f", "side", start.split()[1])  # any tip that main's remote id does not descend from works below
    run(work, "checkout", "-q", "main")
    run(remote, "update-ref", "refs/heads/main", run(work, "rev-parse", "main").stdout.strip())
    rewound = run(work, "rev-parse", "main~1").stdout.strip()
    run(work, "checkout", "-q", "feat")
    forced = tips()
    run(work, "push", "-f", "origin", f"{rewound}:refs/heads/main", env=agent)
    cases.append((tips() == forced, "under a push grant alone, a forced main is refused"))
    judge.record({"session_id": "s1"}, work, "history ** -- planted for the test", "Regent: message")
    run(work, "push", "-f", "origin", f"{rewound}:refs/heads/main", env=agent)
    cases.append((tips() != forced, "with a history grant too, it lands"))
    for row in start.splitlines():
        ref, sha = row.split()
        run(remote, "update-ref", ref, sha)

    data = fix / "h2" / ".claude" / "plugins" / "data"
    for name in ("one", "two"):
        (data / name / "sessions").mkdir(parents=True)
        shutil.copy(state / "sessions" / "s1.grants.json", data / name / "sessions" / "s1.grants.json")
    twin = dict(agent, HOME=str(fix / "h2"), USERPROFILE=str(fix / "h2"))
    twin.pop("REGENCY_HOOK_STATE")
    cases.append((not lands("push", "origin", "main", env=twin), "two stores for one session: the check refuses"))

    hook = Path(work) / ".git" / "hooks" / "pre-push"
    hook.write_text(stub(script="/gone/hook-refs.py"), encoding="utf-8")
    cases.append((not lands("push", "origin", "main") and lands("push", "origin", "main", env=regent),
                  "a stub whose script is gone refuses an agent and passes the Regent"))
    cases.append((install(work)[0] == "rewritten" and hook.read_text(encoding="utf-8") == stub() and install(work)[0] == "current",
                  "the stub is rewritten when the plugin moves, and then left alone"))
    return cases


def install_cases(tmp):
    base = Path(tmp).resolve() / "inst"
    base.mkdir()
    fresh, cases = base / "fresh", []
    run(base, "init", "-q", str(fresh))
    hook = fresh / ".git" / "hooks" / "pre-push"
    plain = base / "plain"
    plain.mkdir()
    cases.append((install(plain)[0] == "absent", "not a repository: nothing written"))
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    cases.append(("wrote" in str(out) and MARK in hook.read_text(encoding="utf-8"), "SessionStart writes the stub and says so"))
    cases.append((respond({"hook_event_name": "SessionStart", "cwd": str(fresh)}) is None, "already there: silent"))
    cases.append((respond({"hook_event_name": "PreCompact", "cwd": str(fresh)}) is None, "other events: ignored"))
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    cases.append(("no pre-push check" in str(out) and MARK not in hook.read_text(encoding="utf-8"),
                  "another pre-push is never replaced, and the context line says so"))
    hook.unlink()
    run(fresh, "config", "core.hooksPath", ".husky")
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    cases.append(("core.hooksPath" in str(out) and not hook.exists(), "a repository with core.hooksPath is left alone, and says so"))
    return cases


def selftest():
    tmp = tempfile.mkdtemp(prefix="hook-refs-")
    saved = {k: os.environ.get(k) for k in ("REGENCY_HOOK_STATE", "REGENCY_JUDGE_HOME")}
    try:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state0")
        cases = pure_cases()
        if shutil.which("git"):
            cases += install_cases(tmp) + real_git_cases(tmp)
        else:
            cases.append((True, "git is not on PATH: the real-git cases did not run"))
        return wire.check(cases)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.update({k: v})
        remove_tree(tmp)


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if argv[:1] == ["--pre-push"]:
        return pre_push()
    if argv[:1] in (["--install"], ["--check"]):
        where = argv[1] if len(argv) > 1 else os.getcwd()
        state, detail = install(where) if argv[0] == "--install" else survey(where)[:2]
        print(f"hook-refs: {state}: {detail}")
        return 0 if state in ("current", "written", "rewritten") and (argv[0] == "--install" or state == "current") else 1
    return wire.serve(respond)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
