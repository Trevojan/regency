#!/usr/bin/env python3
"""hook-refs.py - the push guard that reads what git is really sending, not what a command says.

guard-push.py reads a command's text before it runs, so a chain that changes branch first, a wrapper, a line continuation
or a revision such as HEAD^{}:main goes past it. git hands its pre-push hook the refs themselves, after all of that has
been resolved, so nothing here reads a command (library/hooks.md §2).

Where it lives, the Regent's call (2026-11-06): in the repository, nothing machine-wide.

  <git folder>/regency-hooks/   pre-push, and a forwarder per other hook, so the repository's own hooks still run
  .claude/settings.local.json   env: core.hooksPath through GIT_CONFIG_*, which only what Claude Code starts inherits

So the Regent's own terminal and GitHub Desktop never see this folder, nothing goes in .git/hooks (where Git LFS needs the
one pre-push slot), and the setting follows that session's shells into every repository they touch, however they get there.

  SessionStart   writes both, and rewrites them when the plugin moved. It merges into the settings file and never takes a
                 GIT_CONFIG_* another tool set; one context line when it wrote them or could not.
  --pre-push     what the hook runs when main or master is among the refs. A push onto one needs a `push` grant for that
                 branch; deleting one never passes; a forced update also needs a `history **` grant. Any failure refuses.
                 A shell with neither session variable is no agent's: it passes.

What it promises: it stops an agent that forgets. --no-verify, -c core.hooksPath=, a scrubbed environment and git send-pack
skip it. An agent set on evading the guards with the Regent's credentials is out of reach of any local check (conventions §5).

Modes:  (no args) hook · --pre-push <remote> <url> · --install [dir] · --check [dir] · --uninstall [dir] · --selftest
Pure standard library, Python 3.8+.
"""
import json
import os
import re
import shlex
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
FOLDER = "regency-hooks"
SETTINGS = ".claude/settings.local.json"
ZERO = re.compile(r"^0+$")
BRANCH = "refs/heads/"
SESSION_VARS = ("CLAUDE_CODE_SESSION_ID", "CLAUDECODE")
ENV_COUNT, ENV_KEY, ENV_VALUE = "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"
FORWARDED = ("applypatch-msg", "pre-applypatch", "post-applypatch", "pre-commit", "pre-merge-commit", "prepare-commit-msg",
             "commit-msg", "post-commit", "pre-rebase", "post-checkout", "post-merge", "pre-auto-gc", "post-rewrite",
             "sendemail-validate", "pre-receive", "update", "post-receive", "post-update")
REAL_HOOKS = """dir=
while read -r scope value; do [ "$scope" = command ] || dir=$value; done <<EOF
$(git config --type=path --show-scope --get-all core.hooksPath 2>/dev/null)
EOF
[ -n "$dir" ] || dir=$(git rev-parse --git-common-dir)/hooks
"""
FORWARD = f"""#!/bin/sh
{MARK}: runs the repository's own hook, wherever its configuration keeps it. Only the session's setting does not count.
name=$1; shift
{REAL_HOOKS}[ -x "$dir/$name" ] && exec "$dir/$name" "$@"
exit 0
"""


# ---------- the files ----------------------------------------------------------------------------

def pre_push_hook(script=None, python=None):
    script = shlex.quote(Path(script or __file__).resolve().as_posix())
    python = shlex.quote(Path(python or sys.executable).as_posix())
    return ("#!/bin/sh\n"
            f"{MARK}: scripts/hook-refs.py writes this file and rewrites it when the plugin moves.\n"
            "input=$(cat)\n"
            'case "$input" in *refs/heads/main*|*refs/heads/master*)\n'
            f"  if [ -f {script} ] && [ -f {python} ]; then\n"
            f"""    printf '%s\\n' "$input" | {python} {script} --pre-push "$@" || exit 1\n"""
            '  elif [ -n "$CLAUDE_CODE_SESSION_ID$CLAUDECODE" ]; then\n'
            '    echo "regency: the check on main and master cannot start, so this push is refused; open a new session, or push from your own terminal" >&2\n'
            "    exit 1\n"
            "  fi;;\n"
            "esac\n"
            f"{REAL_HOOKS}"
            """if [ -x "$dir/pre-push" ]; then printf '%s\\n' "$input" | "$dir/pre-push" "$@"; exit $?; fi\n"""
            """if grep -qs 'filter=lfs' .gitattributes; then printf '%s\\n' "$input" | git lfs pre-push "$@"; exit $?; fi\n"""
            "exit 0\n")


def hook_files():
    files = {"pre-push": pre_push_hook(), "forward.sh": FORWARD}
    files.update({name: f'#!/bin/sh\nexec sh "$(dirname "$0")/forward.sh" {name} "$@"\n' for name in FORWARDED})
    return files


def executable(path, text):
    path.write_bytes(text.encode("utf-8"))
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def where(cwd):
    """(the folder every worktree of this repository shares, this folder's path from its top), or None outside a work tree."""
    rows = (git(cwd, "rev-parse", "--is-inside-work-tree", "--git-common-dir", "--show-prefix") or "").split("\n") + [""]
    if rows[0] != "true":
        return None
    return (Path(cwd).resolve() / rows[1]).resolve(), rows[2]


def read_settings(path):
    """The settings as a dict; {} when the file is absent; ValueError when it holds something else."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("env", {}), dict):
        raise ValueError("it is not a settings object")
    return data


def write_settings(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    wire.atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def foreign(env):
    """True when these variables already carry some other configuration."""
    return env.get(ENV_COUNT, "1") != "1" or env.get(ENV_KEY, "core.hooksPath") != "core.hooksPath"


def survey(cwd):
    """(state, detail, owed files, owed settings): 'written' or 'rewritten' when something is owed, else 'current',
    'occupied', 'unreadable' or 'absent'. Changes nothing."""
    place = where(cwd)
    if place is None:
        return "absent", f"{cwd} is not a working repository", {}, None
    hooks, settings = place[0] / FOLDER, Path(cwd) / SETTINGS  # Claude Code reads the settings of the folder it opened in
    try:
        data = read_settings(settings)
    except ValueError as e:
        return "unreadable", f"{settings} does not read: {e}", {}, None
    env = data.get("env", {})
    if foreign(env) or foreign(os.environ):
        return "occupied", f"{ENV_COUNT} is already set for something else", {}, None
    if git(cwd, "ls-files", "--error-unmatch", SETTINGS) is not None:
        return "occupied", f"{settings} is tracked, and it would hold a machine's path", {}, None
    owed = {n: t for n, t in hook_files().items() if not (hooks / n).is_file() or (hooks / n).read_bytes() != t.encode("utf-8")}
    want = {ENV_COUNT: "1", ENV_KEY: "core.hooksPath", ENV_VALUE: hooks.as_posix()}
    new = None if all(env.get(k) == v for k, v in want.items()) else dict(data, env=dict(env, **want))
    if not owed and new is None:
        return "current", str(hooks), {}, None
    return ("written" if new is not None or not (hooks / "pre-push").is_file() else "rewritten"), str(hooks), owed, new


def install(cwd):
    """Write what is owed; returns (state, detail). Merges into the settings file; never takes what another tool set."""
    state, detail, owed, new = survey(cwd)
    if state not in ("written", "rewritten"):
        return state, detail
    common, prefix = where(cwd)
    hooks = common / FOLDER
    hooks.mkdir(parents=True, exist_ok=True)
    for name, text in owed.items():
        executable(hooks / name, text)
    if new is not None:
        write_settings(Path(cwd) / SETTINGS, new)
    if git(cwd, "check-ignore", "-q", SETTINGS) is None:  # the file holds a machine's path: it never shows in a commit
        exclude = common / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as f:
            f.write(f"\n/{prefix}{SETTINGS}\n")
    return state, detail


def uninstall(cwd):
    """Take out what install wrote and nothing else; returns what left. ValueError when the settings do not read."""
    place = where(cwd)
    if place is None:
        return []
    hooks, settings, gone = place[0] / FOLDER, Path(cwd) / SETTINGS, []
    data = read_settings(settings)
    env = data.get("env", {})
    if env.get(ENV_VALUE) == hooks.as_posix():
        env = {k: v for k, v in env.items() if k not in (ENV_COUNT, ENV_KEY, ENV_VALUE)}
        write_settings(settings, {k: v for k, v in dict(data, env=env).items() if k != "env" or env})
        gone.append(str(settings))
    if (hooks / "pre-push").is_file() and MARK in (hooks / "pre-push").read_text(encoding="utf-8"):
        shutil.rmtree(hooks, ignore_errors=True)
        gone.append(str(hooks))
    return gone


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
            return f"this push would delete '{branch}', which no grant covers"
        if not may_push(branch):
            return f"this push would land on '{branch}' with no `push` grant in force"
        if not ZERO.match(old) and not descends(old, new) and not may_force():
            return f"this push would force '{branch}', which also needs a `history **` grant"
    return None


def pre_push():
    if not any(os.environ.get(v) for v in SESSION_VARS):
        return 0
    try:
        lines = [tuple(l.rsplit(None, 3)) for l in sys.stdin.read().splitlines() if l.strip()]
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
    try:
        state, detail = install(event.get("cwd") or os.getcwd())
    except OSError as e:
        state, detail = "unreadable", f"it could not be written ({e})"
    if state == "written":
        return wire.context("SessionStart", f"regency wrote its pre-push check: {detail} and {SETTINGS} (library/hooks.md §2)")
    if state in ("occupied", "unreadable"):
        return wire.context("SessionStart", f"regency: no pre-push check here, because {detail}; only the text guard stands "
                                            "over main (library/hooks.md §2)")
    return None


# ---------- self-test ----------------------------------------------------------------------------

def remove_tree(path):
    for folder, _, files in os.walk(path):  # git keeps its objects read-only, which Windows refuses to delete
        for f in files:
            try:
                os.chmod(os.path.join(folder, f), stat.S_IWRITE | stat.S_IREAD)
            except OSError:  # health: allow-silent the rmtree below ignores errors too: this is a temp folder
                pass
    shutil.rmtree(path, ignore_errors=True)


def run(cwd, *args, env=None):
    """git in a fixture; with no env, as a shell outside Claude Code runs it, whatever session is running the test."""
    if env is None:
        env = {k: v for k, v in os.environ.items() if k not in SESSION_VARS and not k.startswith("GIT_CONFIG_")}
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)


def commit(cwd, name, env=None):
    (Path(cwd) / name).write_text(name, encoding="utf-8")
    run(cwd, "add", name, env=env)
    return run(cwd, "commit", "-q", "-m", name, env=env)


def pure_cases():
    yes, no = (lambda *_: True), (lambda *_: False)
    a, b, z = "a" * 40, "b" * 40, "0" * 40
    line = lambda new, ref="refs/heads/main", old=a: ("refs/heads/x", new, ref, old)  # noqa: E731
    return [(refused([line(b, "refs/heads/feat")], no, no, no) is None, "another branch passes"),
            (refused([line(b, "refs/heads/mainline")], no, no, no) is None, "a branch that only starts with main passes"),
            (refused([line(b, "refs/tags/main")], no, no, no) is None, "a tag named main is not the branch"),
            ("no `push` grant" in (refused([line(b)], no, no, yes) or ""), "main with no grant is refused"),
            (refused([line(b)], yes, no, yes) is None, "main with a grant passes when it descends"),
            (refused([line(b, old=z)], yes, no, no) is None, "a new main with a grant has nothing to force"),
            ("force" in (refused([line(b)], yes, no, no) or ""), "a forced main needs history too"),
            (refused([line(b)], yes, yes, no) is None, "a forced main with both grants passes"),
            ("delete" in (refused([line(z)], yes, yes, yes) or ""), "deleting main never passes"),
            ("cannot read" in (refused([("x", "y")], yes, yes, yes) or ""), "a line it cannot read refuses")]


def install_cases(tmp):
    base = Path(tmp).resolve() / "inst"
    base.mkdir()
    fresh, cases = base / "fresh", []
    run(base, "init", "-q", str(fresh))
    plain = base / "plain"
    plain.mkdir()
    cases.append((install(plain)[0] == "absent", "not a repository: nothing written"))
    settings, hooks = fresh / SETTINGS, fresh / ".git" / FOLDER
    cases.append((survey(fresh)[0] == "written" and not settings.exists() and not hooks.exists(), "--check's survey writes nothing"))
    settings.parent.mkdir()
    settings.write_text('{"permissions": {"allow": ["Read"]}, "env": {"KEEP": "1"}}', encoding="utf-8")
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    data = json.loads(settings.read_text(encoding="utf-8"))
    cases.append(("wrote" in str(out) and MARK in (hooks / "pre-push").read_text(encoding="utf-8")
                  and data["env"][ENV_KEY] == "core.hooksPath" and Path(data["env"][ENV_VALUE]) == hooks,
                  "SessionStart writes the hooks and the setting, and says so"))
    cases.append((data["permissions"] == {"allow": ["Read"]} and data["env"]["KEEP"] == "1", "what was in the settings stays"))
    cases.append((not (fresh / ".git" / "hooks" / "pre-push").exists(), "nothing goes in .git/hooks, where LFS needs the slot"))
    cases.append((run(fresh, "status", "--short").stdout.strip() == "", "the settings file never shows in git status"))
    cases.append((respond({"hook_event_name": "SessionStart", "cwd": str(fresh)}) is None and survey(fresh)[0] == "current",
                  "already there: silent, and --check says current"))
    (fresh / "sub" / "deep").mkdir(parents=True)
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh / "sub" / "deep")})
    nested = fresh / "sub" / "deep" / SETTINGS
    cases.append(("wrote" in str(out) and Path(json.loads(nested.read_text(encoding="utf-8"))["env"][ENV_VALUE]) == hooks
                  and run(fresh, "status", "--short").stdout.strip() == "",
                  "opened in a subfolder: the setting goes where Claude Code reads it, the hooks stay in the git folder, and git status stays clean"))
    cases.append((set(uninstall(fresh / "sub" / "deep")) == {str(hooks), str(nested.resolve())} or not hooks.exists(), "--uninstall from there takes out both"))
    cases.append((install(fresh)[0] == "written" and survey(fresh)[0] == "current", "the next session puts the hooks back"))
    cases.append((respond({"hook_event_name": "PreCompact", "cwd": str(fresh)}) is None, "other events: ignored"))
    (hooks / "pre-push").write_text(pre_push_hook(script="/gone/hook-refs.py"), encoding="utf-8")
    cases.append((respond({"hook_event_name": "SessionStart", "cwd": str(fresh)}) is None and (hooks / "pre-push").read_bytes() == pre_push_hook().encode("utf-8"),
                  "the hook is rewritten, silently, when the plugin moved"))
    settings.write_text(settings.read_text(encoding="utf-8").replace(hooks.as_posix(), "/moved"), encoding="utf-8")
    cases.append((survey(fresh)[0] == "written", "the setting is rewritten when the repository moved"))
    install(fresh)
    cases.append((set(uninstall(fresh)) == {str(hooks), str(settings)} and not hooks.exists()
                  and json.loads(settings.read_text(encoding="utf-8")) == {"permissions": {"allow": ["Read"]}, "env": {"KEEP": "1"}},
                  "--uninstall takes out only what it wrote"))
    cases.append((uninstall(fresh) == [] and uninstall(plain) == [], "--uninstall with nothing there takes out nothing"))
    settings.write_text('{"env": {"GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "a.b"}}', encoding="utf-8")
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    cases.append(("no pre-push check" in str(out) and "a.b" in settings.read_text(encoding="utf-8") and not hooks.exists(),
                  "another tool's GIT_CONFIG_* in the file is left alone, and says so"))
    settings.write_text("{ not json", encoding="utf-8")
    out = respond({"hook_event_name": "SessionStart", "cwd": str(fresh)})
    cases.append(("no pre-push check" in str(out) and settings.read_text(encoding="utf-8") == "{ not json",
                  "a settings file it cannot read is left alone, and says so"))
    settings.unlink()
    saved = {k: os.environ.get(k) for k in (ENV_COUNT, ENV_KEY, ENV_VALUE)}
    os.environ.update({ENV_COUNT: "1", ENV_KEY: "a.b", ENV_VALUE: "c"})
    cases.append((survey(fresh)[0] == "occupied", "so is a GIT_CONFIG_* the session already has from elsewhere"))
    for k, v in saved.items():
        os.environ.pop(k, None) if v is None else os.environ.update({k: v})
    settings.write_text("{}", encoding="utf-8")
    run(fresh, "add", "-f", SETTINGS)
    cases.append((survey(fresh)[0] == "occupied", "a tracked settings file is left alone: it would hold a machine's path"))
    return cases


def real_git_cases(tmp):
    """Real git on a throwaway bare remote: the refs, not the text. Every form is one that got past the text guard."""
    fix, cases = Path(tmp).resolve() / "fix", []
    fix.mkdir()
    remote, work, other = fix / "remote.git", fix / "work", fix / "other"
    run(fix, "init", "-q", "--bare", "-b", "main", str(remote))
    run(remote, "config", "receive.advertisePushOptions", "true")
    run(remote, "config", "receive.denyDeleteCurrent", "ignore")
    run(fix, "clone", "-q", str(remote), "work")
    run(work, "checkout", "-q", "-b", "main")
    commit(work, "A")
    run(work, "branch", "master")
    run(work, "branch", "feat")
    run(work, "push", "-q", "origin", "main", "master", "feat")
    run(fix, "clone", "-q", str(remote), "other")
    run(other, "checkout", "-q", "main")
    commit(other, "O")
    for branch, name in (("feat", "C"), ("master", "M"), ("main", "B")):
        run(work, "checkout", "-q", branch)
        commit(work, name)
    run(work, "checkout", "-q", "feat")
    install(work)
    hooks = work / ".git" / FOLDER

    state, home = fix / "state", fix / "home"
    agent = dict(os.environ, CLAUDE_CODE_SESSION_ID="s1", REGENCY_HOOK_STATE=str(state), REGENCY_JUDGE_HOME=str(home))
    for k in ("CLAUDE_PLUGIN_DATA", "CLAUDE_CONFIG_DIR", "REGENCY_JD"):
        agent.pop(k, None)
    regent = {k: v for k, v in agent.items() if k not in SESSION_VARS and k not in (ENV_COUNT, ENV_KEY, ENV_VALUE)}
    agent.update({ENV_COUNT: "1", ENV_KEY: "core.hooksPath", ENV_VALUE: hooks.as_posix()})

    def tips():
        return run(remote, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads").stdout

    start = tips()
    cases.append((all(f"refs/heads/{b} " in start for b in ("main", "master", "feat")), "the throwaway remote holds main, master and feat"))

    def lands(*args, env=agent, cwd=work):
        """True when the push moved a ref on the remote; the remote goes back to where it was either way."""
        run(cwd, *args, env=env)
        moved = tips() != start
        for row in tips().splitlines():
            ref, _ = row.split()
            if ref not in start:
                run(remote, "update-ref", "-d", ref)
        for row in start.splitlines():
            ref, sha = row.split()
            run(remote, "update-ref", ref, sha)
        return moved

    os.environ.update(REGENCY_HOOK_STATE=str(state), REGENCY_JUDGE_HOME=str(home))
    forms = (["push", "origin", "main"], ["push", "origin", "feat:main"], ["push", "origin", "feat:heads/main"],
             ["push", "origin", "HEAD^{}:main"], ["push", "origin", "HEAD@{0}:main"], ["push", "origin", ":main"],
             ["push", "--delete", "origin", "master"], ["push", "--mirror", "origin"], ["push", "--all", "origin"],
             ["push", "-ofoo", "origin", "main"], ["-c", "alias.p=push", "p", "origin", "main"],
             ["-c", "push.default=matching", "push"], ["-c", "remote.origin.push=feat:main", "push", "origin"])
    for form in forms:
        cases.append((lands(*form, env=regent) and not lands(*form), f"no grant, refused only in an agent's shell: git {' '.join(form)}"))
    run(work, "checkout", "-q", "main")
    cases.append((not lands("push"), "no grant, refused: a bare push after switching to main"))
    cases.append((not lands("push", "origin", "HEAD"), "no grant, refused: HEAD after switching to main"))
    run(work, "checkout", "-q", "feat")
    cases.append((lands("push", "origin", "HEAD", cwd=other, env=regent) and not lands("push", "origin", "HEAD", cwd=other),
                  "another repository, with nothing of its own installed, is refused too"))
    cases.append((not lands("-C", str(other), "push", "origin", "HEAD"), "so is one reached by -C"))
    cases.append((not lands("--git-dir", str(other / ".git"), "push", "origin", "HEAD"), "so is one reached by --git-dir"))
    fresh = fix / "fresh"
    run(fix, "clone", "-q", str(remote), "fresh", env=agent)
    run(fresh, "checkout", "-q", "main", env=agent)
    commit(fresh, "F", env=agent)
    cases.append((not lands("push", "origin", "HEAD", cwd=fresh), "so is a clone made in that same shell"))
    made = fix / "made"
    run(fix, "init", "-q", "-b", "main", str(made), env=agent)
    commit(made, "G", env=agent)
    run(made, "remote", "add", "origin", str(fix / "empty.git"), env=agent)
    run(fix, "init", "-q", "--bare", str(fix / "empty.git"))
    run(made, "push", "-u", "origin", "HEAD", env=agent)
    cases.append((run(fix / "empty.git", "for-each-ref").stdout == "", "so is a repository made in that same shell"))
    run(fix, "clone", "-q", "--bare", str(other), "bare.git")
    run(fix / "bare.git", "remote", "add", "up", str(remote))
    cases.append((lands("push", "up", "main", cwd=fix / "bare.git", env=regent) and not lands("push", "up", "main", cwd=fix / "bare.git"),
                  "so is a bare clone"))
    cases.append((lands("push", "origin", "feat"), "another branch still lands"))
    inherited = {k: v for k, v in agent.items() if k not in SESSION_VARS}
    cases.append((lands("push", "origin", "main", env=inherited), "a shell with the folder but no session variable is no agent's: it lands"))

    judge.record({"session_id": "s1"}, work, "push main -- planted for the test", "Regent: message")
    cases.append((lands("push", "origin", "main"), "under a push grant, main lands"))
    cases.append((not lands("push", "origin", ":main"), "under a push grant, deleting main is refused"))
    cases.append((not lands("push", "origin", "master"), "under a grant of main, master is refused"))
    cases.append((not lands("push", "origin", "main", env=dict(agent, CLAUDE_CODE_SESSION_ID="s2")), "a session grant stays in its session"))
    cases.append((not lands("push", "origin", "HEAD", cwd=other), "and in its repository"))

    run(remote, "update-ref", "refs/heads/main", run(work, "rev-parse", "main").stdout.strip())
    rewound = run(work, "rev-parse", "main~1").stdout.strip()
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

    for gone in ({"script": "/gone/hook-refs.py"}, {"python": "/gone/python"}):
        (hooks / "pre-push").write_text(pre_push_hook(**gone), encoding="utf-8")
        cases.append((not lands("push", "origin", "main") and lands("push", "origin", "feat") and lands("push", "origin", "main", env=inherited),
                      f"a hook whose {next(iter(gone))} is gone refuses main in an agent's shell, and only there, and only main"))
    install(work)
    return cases + project_hook_cases(fix, work, agent, regent, remote)


def project_hook_cases(fix, work, agent, regent, remote):
    """The repository's own hooks keep running in an agent's shell, and its Git LFS is left alone in the Regent's."""
    cases = []
    own = work / ".git" / "hooks"
    own.mkdir(exist_ok=True)
    executable(own / "pre-commit", "#!/bin/sh\necho ran > .git/ran-pre-commit\n")
    executable(own / "pre-push", "#!/bin/sh\ncat > .git/ran-pre-push\n")
    commit(work, "n1", env=agent)
    run(work, "push", "origin", "feat", env=agent)
    cases.append(((work / ".git" / "ran-pre-commit").exists(), "the repository's pre-commit still runs"))
    cases.append(("refs/heads/feat" in (work / ".git" / "ran-pre-push").read_text(encoding="utf-8"), "its pre-push still runs, with git's lines on stdin"))
    executable(own / "pre-push", "#!/bin/sh\ncat >/dev/null\nexit 1\n")
    commit(work, "n2", env=agent)
    cases.append((run(work, "push", "origin", "feat", env=agent).returncode != 0, "and when it fails, the push stops"))
    (own / "pre-push").unlink()
    (own / "pre-commit").unlink()
    husky = work / ".husky"
    husky.mkdir()
    executable(husky / "pre-commit", "#!/bin/sh\necho ran > .git/ran-husky\n")
    run(work, "config", "--local", "core.hooksPath", ".husky")
    commit(work, "n3", env=agent)
    cases.append(((work / ".git" / "ran-husky").exists(), "a repository's own core.hooksPath is still honoured"))
    run(work, "config", "--local", "--unset", "core.hooksPath")
    shutil.rmtree(husky, ignore_errors=True)
    mine = fix / "globalhooks"
    mine.mkdir()
    executable(mine / "pre-commit", "#!/bin/sh\necho ran > .git/ran-global\n")
    gitconfig = fix / "gitconfig"
    gitconfig.write_text(f'[core]\n\thooksPath = "{mine.as_posix()}"\n', encoding="utf-8")
    commit(work, "n4", env=dict(agent, GIT_CONFIG_GLOBAL=str(gitconfig)))
    cases.append(((work / ".git" / "ran-global").exists(), "so is one in the Regent's own ~/.gitconfig"))

    if run(work, "lfs", "version", env=regent).returncode != 0:
        print("hook-refs: git-lfs is not installed: the LFS cases did not run")
        return cases
    clone = fix / "lfsclone"
    run(fix, "clone", "-q", str(remote), "lfsclone", env=regent)
    run(clone, "checkout", "-q", "feat", env=regent)
    cases.append((run(clone, "lfs", "install", "--local", env=regent).returncode == 0, "in the Regent's shell, git lfs install works"))
    run(clone, "lfs", "track", "*.bin", env=regent)
    (clone / "x.bin").write_bytes(b"\x00" * 2048)
    run(clone, "add", ".gitattributes", "x.bin", env=regent)
    run(clone, "commit", "-q", "-m", "lfs", env=regent)
    run(clone, "push", "origin", "feat", env=agent)
    objects = remote / "lfs" / "objects"

    def stored():
        return [p for p in objects.rglob("*") if p.is_file()] if objects.exists() else []

    cases.append((len(stored()) == 1, "set up by the Regent and pushed by an agent, the LFS object reaches the remote"))
    plain = fix / "lfsplain"
    run(fix, "clone", "-q", str(remote), "lfsplain", env=regent)
    run(plain, "checkout", "-q", "main", env=regent)
    if run(plain, "config", "--get", "filter.lfs.clean", env=agent).stdout.strip():  # Git for Windows sets the filters system-wide
        run(plain, "lfs", "track", "*.dat", env=agent)
        (plain / "y.dat").write_bytes(b"\x01" * 2048)
        run(plain, "add", ".gitattributes", "y.dat", env=agent)
        run(plain, "commit", "-q", "-m", "lfs2", env=agent)
        run(plain, "push", "origin", "HEAD:feat2", env=agent)
        cases.append((len(stored()) == 2, "tracked and pushed by an agent with no LFS hook installed, the object still reaches the remote"))
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
            print("hook-refs: git is not on PATH: the real-git cases did not run")
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
    if argv[:1] in (["--install"], ["--check"], ["--uninstall"]):
        here = argv[1] if len(argv) > 1 else os.getcwd()
        if argv[0] == "--uninstall":
            try:
                print("hook-refs: took out " + (", ".join(uninstall(here)) or "nothing"))
                return 0
            except ValueError as e:
                print(f"hook-refs: {SETTINGS} does not read, so nothing was taken out: {e}")
                return 1
        state, detail = install(here) if argv[0] == "--install" else survey(here)[:2]
        owed = argv[0] == "--check" and state in ("written", "rewritten")
        print(f"hook-refs: {'owed' if owed else state}: {detail}")
        return 0 if state == "current" or (argv[0] == "--install" and state in ("written", "rewritten")) else 1
    return wire.serve(respond)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
