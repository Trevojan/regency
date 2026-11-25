#!/usr/bin/env python3
"""hook-hazard.py - the shell's hazardous ground (Bash and PowerShell), before the call.

PreToolUse   classify every command segment:
               cloud read    get, list, describe, logs, plan, ...                 nothing (allowed)
               cloud write   anything else on a cloud CLI                         deny, unless the Regent
                             confirmed that exact command in this pass            (conventions §6, R5.1)
               destructive   deleting, discarding work, force / history rewrites  ask, unless a grant of the
               layout        git worktree add / remove                            Regent's covers every path it
                                                                                  names (judge.py, R15)
               install       system software                                      ask (never granted)
               consent       packs.py / judge.py ratify --yes                     ask (the Regent's alone, T5)
               grant store   a shell command that writes a JD.md, judge.json or   deny: only the Regent's words
                             session grants                                       change them (library/judge.md)
             A 'cd' earlier in the chain moves where later paths resolve, as bash moves it (logically, until the line
             turns physical mode on: set -P, set -o physical). A recursive removal also names every repository nested
             below the folders it names (git clean's single -f, the bare ones), and the repository's own .git when it
             names the root; a path on or in that .git is a place of its own (git clean never). A grant opens only what
             this reader can place: a path or a folder no script can know ("$d", $( ), GIT_DIR, xargs) is covered by no
             grant, '**' included.

It reads text, so what it does not read it does not ask about: an alias, a script, a word a substitution prints.

A pass is the work between two messages of the Regent. hook-verbs.py records, at each message, the
cloud commands the Regent quoted (in backticks, a code block, or on a line of their own); only those
exact commands, compared token by token, may write to the cloud until the next message.

Nothing here locks the session: every act is judged when it happens, against the grants in force then.

Market pattern: human-in-the-loop approval of a specific tool call (LangGraph interrupt), with standing
approvals scoped by place and kind (policy-as-code allow lists).

Modes:  (no args) hook · --selftest
Pure standard library, Python 3.8+.
"""
import fnmatch
import importlib.util
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402
import judge  # noqa: E402  (the Regent's grants, R15)

_spec = importlib.util.spec_from_file_location("guard_push", HERE / "guard-push.py")
guard_push = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard_push)  # one tokenizer for every shell guard

SHELLS = guard_push.SHELLS
INSTALLERS = {"apt", "apt-get", "yum", "dnf", "pacman", "zypper", "brew", "choco", "winget", "scoop", "snap"}
SQL_CLIENTS = {"psql", "mysql", "sqlite3", "sqlcmd", "mongosh", "mongo", "cqlsh", "duckdb"}
DESTRUCTIVE_SQL = re.compile(r"(?i)\b(drop\s+(table|database|schema|index)|truncate\b|delete\s+from)\b")

# ---------- cloud: where the verb sits, and which verbs only read --------------------------------
VERB_FIRST = {"kubectl", "oc", "helm", "terraform", "tofu", "pulumi", "vercel", "netlify", "wrangler", "firebase",
              "flyctl", "fly", "cdk", "sam", "serverless", "sls", "eksctl", "heroku", "gsutil", "bq"}
VERB_SECOND = {"aws"}                                         # aws <service> <operation>
VERB_SCAN = {"gcloud", "az", "azd", "doctl", "oci", "ibmcloud"}  # <group> [<subgroup>...] <verb>
CLOUD = VERB_FIRST | VERB_SECOND | VERB_SCAN
READ_VERBS = {"get", "list", "ls", "describe", "show", "view", "status", "logs", "log", "read", "tail", "version",
              "help", "whoami", "info", "inspect", "top", "explain", "plan", "validate", "output", "cat", "du", "stat",
              "history", "search", "diff", "lint", "template", "graph", "providers", "query-only", "api-resources",
              "api-versions", "cluster-info", "print-access-token", "print-identity-token"}
READ_PREFIXES = ("describe-", "list-", "get-", "show-", "search-", "lookup-", "batch-get-", "query-")
WRITE_VERBS = {"create", "delete", "rm", "cp", "mv", "sync", "rsync", "put", "apply", "destroy", "deploy", "update",
               "set", "unset", "patch", "edit", "replace", "scale", "rollout", "run", "exec", "start", "stop",
               "restart", "import", "init", "login", "logout", "upgrade", "install", "uninstall", "rollback",
               "publish", "push", "remove", "add", "attach", "detach", "enable", "disable", "invoke", "submit",
               "cancel", "taint", "untaint", "label", "annotate", "expose", "cordon", "uncordon", "drain", "mb", "rb",
               "acl", "iam", "grant", "revoke", "modify", "register", "deregister", "terminate", "reboot", "resize",
               "export", "mount", "ssh", "scp", "port-forward", "proxy", "use-context", "configure", "query", "load",
               "mk", "rm-r", "promote", "release", "refresh"}
WRITE_PREFIXES = ("create-", "delete-", "put-", "update-", "remove-", "terminate-", "run-", "start-", "stop-",
                  "modify-", "attach-", "detach-", "associate-", "disassociate-", "register-", "deregister-",
                  "enable-", "disable-", "reboot-", "set-", "add-", "import-", "invoke-", "send-", "publish-", "tag-",
                  "untag-", "revoke-", "authorize-", "copy-", "restore-", "upload-", "reset-", "replace-")


ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
WRAPPERS = {"env", "eval", "command", "builtin", "exec", "time", "nohup", "nice", "xargs", "!", "if", "elif", "then", "else",
            "while", "until", "do"}  # what may stand before a command and leave it the same command
WRAPPER_VALUE = {"-u", "-n", "-a", "-C", "-S", "-I", "-L", "-P", "-d", "-s"}


def words(seg):
    """The command a segment runs: what stands before it goes (FOO=1, env, command, time, a shell's `do` or `then`)."""
    out = list(seg)
    while out:
        if ASSIGNMENT.match(out[0]):
            out.pop(0)
        elif name(out[0]) in WRAPPERS:
            wrapper = name(out.pop(0))
            while out and out[0].startswith("-"):
                if wrapper == "command" and out[0] in ("-v", "-V"):
                    return []  # `command -v rm` names rm and runs nothing
                out = out[2:] if out[0] in WRAPPER_VALUE else out[1:]
        else:
            break
    return out


def name(tok):
    return guard_push.basename(tok).rsplit(".exe", 1)[0]


def canon(w):
    """A command compared token by token: quotes and spacing do not count, the executable path does not."""
    return " ".join([name(w[0])] + list(w[1:]))


def cloud_mode(cmd, args):
    """'read' or 'write' for one cloud CLI call; an unknown verb counts as a write."""
    if {"--help", "-h", "help", "--version", "version"} & set(args):
        return "read"
    pos = [a for a in args if not a.startswith("-")]
    cand = pos[1:2] if cmd in VERB_SECOND else pos[1:] if cmd in VERB_SCAN else pos[:1]
    for tok in cand:
        v = tok.lower().split(":")[-1]
        if v in READ_VERBS or v.startswith(READ_PREFIXES):
            return "read"
        if v in WRITE_VERBS or v.startswith(WRITE_PREFIXES):
            return "write"
    return "write"


# ---------- local hazards ----------------------------------------------------------------------

def classify_git(args):
    a, j = [re.split(r"\d*[<>]", t, 1)[0] for t in args], 0  # a redirect glued to a word is not part of it
    while j < len(a) and a[j].startswith("-"):  # git global options
        j += 2 if a[j] in guard_push.GIT_VALUE_OPTS else 1
    if j >= len(a):
        return None
    verb, rest = a[j], a[j + 1:]
    flags = set(rest)
    if verb == "reset" and "--hard" in flags:
        return "discard", "git reset --hard"
    if verb == "clean" and any(f == "--force" or (f.startswith("-") and not f.startswith("--") and "f" in f) for f in rest):
        return "delete", "git clean -f"
    if verb == "checkout" and ("--" in rest or "." in rest):
        return "discard", "git checkout -- <paths>"
    if verb == "restore" and "--staged" not in flags:
        return "discard", "git restore"
    if verb == "branch" and ({"-D"} & flags or {"--delete", "--force"} <= flags):
        return "delete", "git branch -D"
    if verb == "stash" and rest[:1] and rest[0] in ("drop", "clear"):
        return "delete", f"git stash {rest[0]}"
    if verb in ("rebase", "filter-branch", "filter-repo"):
        return "history", f"git {verb}"
    if verb == "push":
        names = {n for f in rest if f.startswith("-") and f != "-" for n in guard_push.flag_names(f)}
        if names & {"-f", "--force", "--force-with-lease", "--force-if-includes", "--mirror"} or any(f.startswith("+") for f in rest):
            return "history", "git push --force"
    if verb == "worktree" and rest[:1] and rest[0] in ("add", "remove", "prune", "move"):
        return "layout", f"git worktree {rest[0]}"
    if verb == "reflog" and rest[:1] == ["expire"]:
        return "history", "git reflog expire"
    if verb == "update-ref" and "-d" in flags:
        return "delete", "git update-ref -d"
    return None


def classify_words(w):
    """(kind, label) for one command's words, or None. Kinds: cloud-read, cloud-write, history,
    discard, delete, layout, install."""
    if not w:
        return None
    cmd, args = name(w[0]), w[1:]
    if cmd in ("sudo", "doas") and args:
        return classify_words(words(args)) or ("install", f"{cmd} {args[0]}")
    if cmd in CLOUD:
        return f"cloud-{cloud_mode(cmd, args)}", canon(w)
    if cmd == "git":
        return classify_git(args)
    if cmd in ("rm", "rmdir", "unlink", "shred", "del", "erase", "rd", "remove-item", "ri"):
        return "delete", cmd
    if cmd == "find" and ("-delete" in args or "rm" in args):
        return "delete", "find -delete"
    if cmd in ("dd", "mkfs", "format", "diskpart") or cmd.startswith("mkfs."):
        return "delete", cmd
    if cmd in INSTALLERS and args[:1] and args[0] in ("install", "remove", "uninstall", "purge", "upgrade"):
        return "install", f"{cmd} {args[0]}"
    if cmd in SQL_CLIENTS and DESTRUCTIVE_SQL.search(" ".join(args)):
        return "delete", f"{cmd}: destructive SQL"
    if cmd == "docker" and args[:2] in (["system", "prune"], ["volume", "rm"], ["volume", "prune"]):
        return "delete", "docker " + " ".join(args[:2])
    script = next((i for i, a in enumerate(args) if name(a) in ("packs.py", "judge.py")), None)
    if cmd.startswith(("python", "py")) and script is not None:
        rest = args[script + 1:]
        if rest[:1] == ["ratify"] and "--yes" in rest:  # consent: a pack's hooks, or a changed grant store (T5)
            return "consent", f"{name(args[script])} ratify --yes"
    return None


RM_COMMANDS = {"rm", "rmdir", "unlink", "shred", "del", "erase", "rd", "remove-item", "ri"}
CD_COMMANDS = {"cd", "pushd", "popd", "chdir", "set-location", "sl", "push-location", "pop-location"}
UNGRANTABLE = {"dd", "mkfs", "format", "diskpart", "docker"} | SQL_CLIENTS  # data outside files: never granted
GLOB = re.compile(r"[*?\[]")
GIT_MOVED = re.compile(r"(?i)\bGIT_(?:DIR|WORK_TREE|COMMON_DIR)\b|\bcore\.worktree\b")  # an export or $env: is no segment to read
SUBSTITUTION = re.compile(r"\$\(|`|<\(")  # what it prints joins the line, and nothing here knows what that is


def resolve(arg, here):
    """The absolute path a shell would act on, or None when no script can know it ($d, an unknown cwd, a backslash off
    Windows: a separator to a Windows shell, a plain character or an escape to any other, and nothing here knows which
    shell runs the line). A glob reads as the folder its literal part leads to, since what it expands to stays under
    that unless it climbs out after the glob. Its '..' stay: the file system settles them past each symbolic link, and
    judge.relative reads the path where it lands."""
    if here is None or re.search(r"[$%{]", arg) or (os.name != "nt" and "\\" in arg):
        return None
    glob = GLOB.search(arg)
    if glob:
        if ".." in re.split(r"[\\/]", arg[glob.start():]):
            return None
        arg = glob_parts(arg)[0] or "."
    m = re.match(r"^/([a-zA-Z])/(.*)$", arg) if os.name == "nt" else None
    p = Path(f"{m.group(1)}:/{m.group(2)}" if m else os.path.expanduser(arg))
    return p if p.is_absolute() else Path(here) / p


def glob_parts(arg):
    """A glob's literal folder (up to the separator before its first wildcard) and the part of it that wildcard is in."""
    glob = GLOB.search(arg)
    folder = re.match(r"^(?:.*[\\/])?", arg[:glob.start()]).group(0)
    return folder, re.split(r"[\\/]", arg[len(folder):])[0]


def moved(target, here, physical=False):
    """Where a 'cd' leaves the shell, as bash moves it: logically, each '..' taking off the folder written before it, when
    every folder before a '..' and the end are folders; otherwise, and under 'cd -P' or in physical mode, where the file
    system lands it. The paths named later land through the file system from there (QA-grant-latest-04 N1, N2, N8;
    QA-grant-latest-05 N11)."""
    t = resolve(target, here)
    if t is None:
        return None
    logical = None if physical else canonical(t)
    if logical is not None and os.path.isdir(logical):
        return logical
    return Path(os.path.realpath(str(t))) if os.path.isdir(t) else t


def canonical(t):
    """bash's own reading of a 'cd' path (sh_canonpath): each '..' takes off the folder before it, which must be one."""
    kept = []
    for part in t.parts[1:]:
        if part == ".." and kept and not os.path.isdir(Path(t.anchor, *kept)):
            return None
        kept = kept[:-1] if part == ".." else kept + [part]
    return Path(t.anchor, *kept)


def cd_mode(args):
    """bash's 'cd -P' and 'cd -L', the last of them winning: True (physical), False (logical), or None when the 'cd' names
    neither and the shell's mode decides."""
    flags = []
    for a in args:
        if not re.fullmatch(r"-[LPe@]+", a):
            break
        flags += [c for c in a if c in "LP"]
    return {"P": True, "L": False}.get("".join(flags)[-1:])


SET_LETTERS = "abefhkmnptuvxBCEHPTo"  # bash's own one-letter options to set (o takes a name); any other voids the set
SET_NAMES = {"allexport", "braceexpand", "emacs", "errexit", "errtrace", "functrace", "hashall", "histexpand", "history",
             "ignoreeof", "interactive-comments", "keyword", "monitor", "noclobber", "noexec", "noglob", "nolog", "notify",
             "nounset", "onecmd", "physical", "pipefail", "posix", "privileged", "verbose", "vi", "xtrace"}  # its -o names


def shell_mode(args, physical, started=False):
    """bash's physical mode after a 'set' (-P or -o physical turn it on, +P or +o physical off), or after the options a shell
    is started with (bash -P -c ...): the words read in order up to '-', '--' or the first that is no option, each o taking
    the next word. A set word holding a letter bash does not know makes the whole set change nothing, and an -o name it does
    not know stops it there; a shell started so starts nothing, so its options need no such check (the Regent, 2026-11-25:
    the agent's shell starts logical, and only the line turns physical mode on)."""
    options, index = [], 0
    while index < len(args) and args[index][:1] in ("-", "+") and args[index] not in ("-", "--"):
        word, index = args[index], index + 1
        index += word in ("--rcfile", "--init-file")  # a shell's long options say nothing of the mode; these two take a file
        for letter in "" if word.startswith("--") else word[1:]:
            options.append((word[0] == "-", letter, args[index] if letter in "oO" and index < len(args) else None))
            index += letter in "oO"
    if not started and any(letter not in SET_LETTERS for _, letter, _ in options):
        return physical
    for on, letter, value in options:
        if letter == "o" and not started and value not in SET_NAMES:
            return physical
        if letter == "P" or (letter == "o" and value == "physical"):
            physical = on
    return physical


RECURSE_SHORT = re.compile(r"^-[fiIdv]*[rR][fiIrRdv]*$")  # rm's own short flags, one of them -r or -R


def recursive(cmd, args):
    """True when a removal goes down through the folders it names: find, rm -r, Remove-Item -Recurse, rd /s, del /s."""
    flags = args[:args.index("--")] if "--" in args else args
    return cmd == "find" or any(RECURSE_SHORT.match(a) or (len(a) > 2 and "--recursive".startswith(a)) or a.lower() == "/s"
                                or (len(a) > 1 and "-recurse".startswith(a.lower().split(":")[0])) for a in flags)


def forces(word):
    """How many -f one word of git clean gives: each f of a short cluster before its first e, or --force cut to a prefix."""
    if len(word) > 2 and "--force".startswith(word):
        return 1
    cluster = re.match(r"-([^-e]*)", word)
    return cluster.group(1).count("f") if cluster else 0


def takes_pattern(word):
    """A word of git clean whose pattern is the next word: -e, a short cluster ending at its first e, --exclude cut to a
    prefix (a pattern glued on, -ekeep or --exclude=keep, is in the word itself)."""
    return bool(re.fullmatch(r"-[^-e]*e", word)) or (len(word) > 2 and "--exclude".startswith(word))


def clean_args(rest):
    """git clean's own reading of its words (parse-options): how many -f it is given, and the paths it names. The pattern
    of -e or --exclude is no path; '--' ends the options, and a word that is no option is a path on either side of it."""
    forced, paths, left = 0, [], iter(rest)
    for word in left:
        if word == "--":
            return forced, paths + list(left)
        forced += forces(word)
        paths += [] if word.startswith("-") else [word]
        if takes_pattern(word):
            next(left, None)
    return forced, paths


def reached(written, here, root, deadline=None, bare=False):
    """The repositories nested in this one below the folders a recursive removal names (the Regent, 2026-11-23): each a
    place of its own, outside '**' and every relative glob; bare: only the bare ones, as git clean's single -f reaches them
    (judge.repositories_below). A glob reaches the folders its wildcard part matches, dot names only when that part opens
    with a dot, as a shell expands it. A None is a search that ran out of time."""
    out = []
    for a in written:
        p = resolve(a, here)
        if p is None or root is None:
            continue
        found = judge.repositories_below(p, root, picker(a), deadline, bare)
        out += [None] if found is None else found
    return out


def picker(written):
    """Which entries of its folder a glob names: those its first wildcard part matches, dot names only when that part opens
    with a dot, as a shell expands it; None for a path that is no glob."""
    if not GLOB.search(written):
        return None
    part = glob_parts(written)[1]
    return lambda entry: fnmatch.fnmatchcase(entry, part) and (part[:1] == "." or entry[:1] != ".")


def own_git(written, here, root, whole):
    """The repository's own .git, a place of its own, when a removal reaches it from above (the Regent, 2026-11-25): a glob
    on the root whose wildcard part matches '.git' names it (or a path in it), and a recursive removal (whole) that names
    the root goes through it. A path written on it or in it is placed by judge.relative. git clean never removes it."""
    out = []
    for a in written:
        p, pick = resolve(a, here), picker(a)
        reaches = whole if pick is None else pick(judge.GIT)
        if reaches and p is not None and root is not None:
            out += judge.own_git_below(p, root)
    return out


def operands(args):
    """Non-option arguments, everything after '--' included."""
    out, rest = [], False
    for a in args:
        if a == "--" and not rest:
            rest = True
        elif rest or not a.startswith("-"):
            out.append(a)
    return out


def git_folder(args, here):
    """Where a git command runs: each global -C read against the last, as git does; None when --git-dir or --work-tree
    says it runs somewhere no script here follows."""
    j, where = 0, here
    while j < len(args) and args[j].startswith("-"):
        if args[j] == "-C" and j + 1 < len(args):
            where = resolve(args[j + 1], where)
        if args[j].split("=")[0] in ("--git-dir", "--work-tree"):
            return None
        j += 2 if args[j] in guard_push.GIT_VALUE_OPTS else 1
    return where


def act_paths(kind, label, w, here, root=None, deadline=None):
    """The paths an act names, for a grant to cover: [] names none (it needs '**'); a None in the list is one no script can
    know, which no grant covers; None = never grantable. A git act is judged where it runs: what it names resolves against
    that folder, and `**` is this repository only when git finds it from there (judge.lands_in): no link out of it, no
    repository nested in it. A recursive removal also names every repository nested below the folders it names."""
    if name(w[0]) in ("sudo", "doas"):
        w = words(w[1:])
    cmd, args = name(w[0]), w[1:]
    if kind not in judge.KINDS or cmd in UNGRANTABLE or cmd.startswith("mkfs."):
        return None
    if cmd in RM_COMMANDS:
        written, deep = operands(args), recursive(cmd, args)
        return ([resolve(a, here) for a in written] + reached(written if deep else [], here, root, deadline)
                + own_git(written, here, root, deep) or [None])
    if cmd == "find":
        stop = next((i for i, a in enumerate(args) if a.startswith(("-", "!"))), len(args))
        return (([resolve(a, here) for a in args[:stop]] or [here]) + reached(args[:stop] or ["."], here, root, deadline)
                + own_git(args[:stop] or ["."], here, root, True))
    if cmd != "git":
        return []
    where = git_folder(args, here)
    if where is None:
        return [None]
    below = []
    if label in ("git checkout -- <paths>", "git restore", "git clean -f"):
        verb = next((i for i, a in enumerate(args) if a in ("checkout", "restore", "clean")), None)
        rest = args[verb + 1:] if verb is not None else []
        paths = rest[rest.index("--") + 1:] if "--" in rest else [a for a in rest if not a.startswith("-")]
        if label == "git clean -f":  # a second -f reaches every repository below, one -f the bare ones (QA-grant-latest-05 N13)
            forced, paths = clean_args(rest)
            below = reached(paths or ["."], where, root, deadline, bare=forced < 2)
        if paths:
            return [resolve(a, where) for a in paths] + below
    named = [] if root is None or judge.lands_in(where, root) else [where]
    return (named or ([judge.ALL] if below else [])) + below


def acts(command, cwd, depth=0, root=None, deadline=None, physical=False):
    """Every finding with the paths it names: [(kind, label, paths)], nested shells included. A 'cd' moves where the later
    segments of the chain resolve their paths, as bash moves (moved): logically, until the line turns physical mode on
    (shell_mode), and a line this reader cannot place leaves a None for no grant to cover."""
    out, here = [], Path(cwd) if cwd else None
    root = root or here
    text = re.sub(r"\\\r?\n", " ", guard_push.data_only(command))
    for seg in guard_push.segments(text):
        w = words(seg)
        if depth < 3 and any(name(t) in SHELLS for t in seg[:1] + w[:1]):
            started = bool(w) and name(w[0]) in ("bash", "sh") and shell_mode(w[1:], False, started=True)
            for t in seg[1:]:
                if " " in t:
                    out += acts(t, here, depth + 1, root, deadline, started)
        if w and name(w[0]) == "set":
            physical = shell_mode(w[1:], physical)
            continue
        if w and name(w[0]) in CD_COMMANDS:
            target = [t for t in operands(w[1:]) if t.lower() != "/d"]  # cmd's cd /d <folder>
            option = cd_mode(w[1:]) if name(w[0]) == "cd" else None
            mode = physical if option is None else option
            # a 'cd' inside ( ) ends with it, and which ones those are is more than this reader follows
            here = None if "(" in text or not target or target[0] == "-" else moved(target[0], here, mode)
            continue
        f = classify_words(w)
        if f:
            paths = act_paths(f[0], f[1], w, here, root, deadline)
            before = seg[:len(seg) - len(w)]
            blind = SUBSTITUTION.search(text) or any(name(t) == "xargs" or t.split("=")[0] in ("-C", "--chdir") for t in before)
            out.append((f[0], f[1], [None] if blind and paths is not None else paths))
    if GIT_MOVED.search(text):
        out = [(k, lbl, [None] if lbl.startswith("git ") and ps is not None else ps) for k, lbl, ps in out]
    return out


def findings(command, depth=0):
    """Every finding in a command, nested shells included: [(kind, label)]."""
    return [(k, lbl) for k, lbl, _ in acts(command, None, depth)]


STORE_MARK = re.compile(r"(?i)(?:^|[\\/\s'\"`=(,])(JD\.md|judge\.json|[\w.-]*\.grants\.json)(?=$|[\s'\"`),;])")
REDIRECT_TO_STORE = re.compile(r"(?i)>>?\s*['\"]?[^\s'\"]*(JD\.md|judge\.json|\.grants\.json)")
READERS = {"cat", "type", "less", "more", "head", "tail", "grep", "egrep", "rg", "get-content", "gc", "wc", "ls", "dir",
           "stat", "file", "diff", "sha256sum", "md5sum", "select-string", "sls", "test-path", "git"}
GIT_READS = {"diff", "log", "show", "status", "blame", "add", "commit", "ls-files", "grep"}


def touches_store(command):
    """True when a shell command would change a grant store: only the Regent's words may (library/judge.md)."""
    text = guard_push.data_only(command)
    if REDIRECT_TO_STORE.search(text):
        return True
    for seg in guard_push.segments(text):
        w = words(seg)
        if not w or not any(STORE_MARK.search(t) for t in w[1:]):
            continue
        cmd = name(w[0])
        if cmd == "git":
            verb = next((a for a in w[1:] if not a.startswith("-")), "")
            if verb in GIT_READS:
                continue
            return True
        if cmd in READERS:
            continue
        if cmd.startswith(("python", "py")) and any(name(a) == "judge.py" for a in w[1:]):
            continue  # judge.py's own modes: its ratify --yes asks as consent
        return True
    return False


ORDER = {"cloud-write": 0, "history": 1, "discard": 2, "delete": 3, "layout": 4, "install": 5, "consent": 6}


def classify(command):
    """The most serious finding that needs the Regent, or None. A cloud read needs nobody."""
    ranked = sorted((f for f in findings(command) if f[0] in ORDER), key=lambda f: ORDER[f[0]])
    return ranked[0] if ranked else None


# ---------- the Regent's confirmations ---------------------------------------------------------

def confirmations(prompt):
    """Cloud commands the Regent quoted in a message: backtick spans, code-block lines, bare lines."""
    text = prompt or ""
    pieces = re.findall(r"`([^`\n]+)`", text)
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        pieces += block.splitlines()
    pieces += [l for l in re.sub(r"```.*?```", "", text, flags=re.S).splitlines() if "`" not in l]
    found = []
    for piece in pieces:
        for seg in guard_push.segments(piece.strip().lstrip("$> ").strip()):
            w = words(seg)
            start = next((i for i, t in enumerate(w) if name(t) in CLOUD), None)
            if start is not None:
                c = canon(w[start:])
                if c not in found:
                    found.append(c)
    return found


def confirmed(event):
    st = wire.load_state(event, "cloud")
    return set(st.get("commands", [])) if st else set()


# ---------- hook ---------------------------------------------------------------------------------

def respond(event):
    if event.get("tool_name") not in wire.SHELL_TOOLS or event.get("hook_event_name") != "PreToolUse":
        return None
    command = wire.tool_input(event).get("command", "")
    cwd = event.get("cwd") or os.getcwd()
    repo = wire.repo_root(Path(cwd))
    found_all = acts(command, cwd, root=repo, deadline=time.monotonic() + judge.WALK_SECONDS)
    writes = [label for kind, label, _ in found_all if kind == "cloud-write"]
    missing = [c for c in writes if c not in confirmed(event)]
    if missing:
        return wire.permission("deny", f"cloud write '{missing[0]}' was not confirmed by the Regent in this pass. "
                                       "Cloud belongs to its owner: reads run freely, a write runs only when the "
                                       "Regent quotes that exact command in a message (conventions §6)")
    if touches_store(command):
        return wire.permission("deny", "this command would change a grant store (a JD.md, judge.json or the session's "
                                       "grants): only the Regent's own words change them. Ask the Regent for a "
                                       "'grant:' line, or run /regency:judge (library/judge.md)")
    local = sorted((f for f in found_all if f[0] in ORDER and f[0] != "cloud-write"), key=lambda f: ORDER[f[0]])
    if local and local[0][0] == "consent":
        return wire.permission("ask", f"consent: '{local[0][1]}' widens what runs without asking (a pack's hooks, or a "
                                      "grant store that changed). Only the Regent approves it, after reading the review "
                                      "the same command prints without --yes (T5)")
    open_ = [(k, lbl, ps) for k, lbl, ps in local if not judge.covers(event, repo, k, ps)]
    if not open_:
        return None
    kind, label, paths = open_[0]
    reason = f"{kind}: '{label}' needs the Regent's yes (conventions §5)"
    if paths is not None and None in paths:
        reason += ". No script can tell where it lands, so no grant covers it"
    elif paths is not None:
        reason += f". No grant covers it; the Judge proposes '{judge.propose(kind, paths, repo)}' (/regency:judge)"
    stale = judge.stale(repo)
    if stale:
        reason += f". {len(stale)} grant store(s) STALE until the Regent says 'ratify grants'"
    return wire.permission("ask", reason)


TABLE = [  # command, expected PreToolUse verdict with no confirmation
    ("ls -la", "allow"),
    ("rm -rf build", "ask"),
    ("cd x && rm notes.txt", "ask"),
    ("git reset --hard HEAD~1", "ask"),
    ("git reset --soft HEAD~1", "allow"),
    ("git clean -fd", "ask"),
    ("git clean -n", "allow"),
    ("git checkout -- src/a.cs", "ask"),
    ("git checkout feature/x", "allow"),
    ("git restore src/a.cs", "ask"),
    ("git restore --staged src/a.cs", "allow"),
    ("git branch -D old", "ask"),
    ("git branch -d merged", "allow"),
    ("git stash drop", "ask"),
    ("git stash list", "allow"),
    ("git rebase -i HEAD~3", "ask"),
    ("git push --force-with-lease origin feat", "ask"),
    ("git push --force-with-lease=feat:abc origin feat", "ask"),
    ("git push --force-w origin feat", "ask"),
    ("git push -fu origin feat", "ask"),
    ("git push -uf origin feat", "ask"),
    ("git push origin +feat", "ask"),
    ("git push --mirror origin", "ask"),
    ("git push -ofoo --mirror origin", "ask"),
    ("git push -of origin feat", "allow"),
    ("git push -o f origin feat", "allow"),
    ("git push -u origin feat", "allow"),
    ("git worktree add ../w feat", "ask"),
    ("git commit -m 'rm -rf everything'", "allow"),
    ("cat > notes.md <<'EOF'\nthe agent ran `rm -rf` once\nEOF", "allow"),
    ("python3 - <<'PY'\nprint('rm -rf build')\nPY", "allow"),
    ("cat > notes.md <<EOF\nplain words: rm -rf is named here\nEOF", "allow"),
    ("cat > notes.md <<EOF\nrm -rf opens this line, as text\nEOF", "allow"),
    ("bash <<'EOF'\nrm -rf build\nEOF", "ask"),
    ("cat <<'EOF' | sh\nrm -rf build\nEOF", "ask"),
    ("cat > out.txt <<EOF\n`rm -rf build`\nEOF", "ask"),
    ("cat > notes.md <<'EOF'\ntext\nEOF\nrm -rf build", "ask"),
    ('echo "rm -rf /"', "allow"),
    ('bash -c "rm -rf dist"', "ask"),
    ("FOO=1 rm x", "ask"),
    ("Remove-Item -Recurse -Force .\\bin", "ask"),
    ("find . -name '*.tmp' -delete", "ask"),
    ("psql -c 'DROP TABLE users'", "ask"),
    ("psql -c 'select 1'", "allow"),
    ("sudo apt-get install jq", "ask"),
    ("npm install", "allow"),
    ("docker system prune -af", "ask"),
    ("python scripts/doctor.py", "allow"),
    ("python scripts/packs.py ratify kit hooks --yes", "ask"),
    ("python3 /x/regency/scripts/packs.py ratify kit all --repo . --yes", "ask"),
    ("python scripts/packs.py ratify kit hooks", "allow"),
    ("python scripts/packs.py activate kit --yes", "allow"),
    # cloud reads run freely
    ("aws s3 ls s3://bucket", "allow"),
    ("aws ec2 describe-instances --region sa-east-1", "allow"),
    ("aws sts get-caller-identity", "allow"),
    ("gcloud run services list", "allow"),
    ("gcloud auth list", "allow"),
    ("kubectl get deploy -n web", "allow"),
    ("kubectl logs pod/api", "allow"),
    ("terraform plan", "allow"),
    ("az vm list -o table", "allow"),
    ("gsutil ls gs://bucket", "allow"),
    ("helm template ./chart", "allow"),
    ("gcloud --help", "allow"),
    # cloud writes are denied without the Regent's exact confirmation
    ("aws s3 cp a.txt s3://bucket/a.txt", "deny"),
    ("aws configure", "deny"),
    ("gcloud run deploy api --region us-east1", "deny"),
    ("gcloud config set project p1", "deny"),
    ("kubectl apply -f k8s/", "deny"),
    ("kubectl run debug --image busybox", "deny"),
    ("terraform apply -auto-approve", "deny"),
    ("az group delete -n rg1", "deny"),
    ("bq query 'delete from t where 1=1'", "deny"),
    ("cd infra && terraform destroy", "deny"),
    ('bash -c "kubectl delete ns web"', "deny"),
    # what stands before a command, and a line broken in two, leave it the same command
    ('for d in build dist; do rm -rf "$d"; done', "ask"),
    ("if [ -d build ]; then rm -rf build; fi", "ask"),
    ("while false; do rm -rf build; done", "ask"),
    ("if true; then git reset --hard; fi", "ask"),
    ("! rm -rf build", "ask"),
    ("time rm -rf build", "ask"),
    ("command rm -rf build", "ask"),
    ("nice -n 5 rm -rf build", "ask"),
    ("xargs rm -rf < list.txt", "ask"),
    ("env git clean -fd", "ask"),
    ("env -u HOME git clean -fd", "ask"),
    ("git \\\n clean -fd", "ask"),
    ("git push \\\n--force origin feat", "ask"),
    ("command git push -f origin feat", "ask"),
    ("nohup git push -f origin feat", "ask"),
    ("exec git push -f origin feat", "ask"),
    ("eval git push -f origin feat", "ask"),
    ("echo feat | xargs git push -f origin", "ask"),
    ("git push --force>/dev/null origin feat", "ask"),
    ("git --config-env x.y=HOME clean -fd", "ask"),
    ("git --attr-source HEAD clean -fd", "ask"),
    ("FOO=1 bash -c 'rm -rf dist'", "ask"),
    ("command -v rm", "allow"),
    ("time ls", "allow"),
]


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        os.environ["REGENCY_JUDGE_HOME"] = str(Path(tmp) / "home")
        os.environ.pop("REGENCY_JD", None)
        root = wire.build_fixture(Path(tmp) / "proj")
        os.environ["CLAUDE_PROJECT_DIR"] = str(root)  # a real hook always has it, and repo_root falls back on it

        def ev(phase, cmd, sid="s1", tool="Bash", cwd=None):
            return {"hook_event_name": phase, "tool_name": tool, "session_id": sid, "cwd": str(cwd or root),
                    "tool_input": {"command": cmd}}

        def verdict(a):
            return (a or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allow")

        cases = []
        for cmd, want in TABLE:
            got = verdict(respond(ev("PreToolUse", cmd)))
            cases.append((got == want, f"pre  {cmd!r} -> {got} (want {want})"))
        cases.append((verdict(respond(ev("PreToolUse", "Remove-Item x", tool="PowerShell"))) == "ask", "PowerShell tool"))
        prompt = ("confirmo o deploy: `gcloud run deploy api --region us-east1`\n```\nkubectl apply -f k8s/\n```\n"
                  "terraform apply -auto-approve\nand don't touch the rest")
        got = confirmations(prompt)
        cases.append((got == ["gcloud run deploy api --region us-east1", "kubectl apply -f k8s/",
                              "terraform apply -auto-approve"], f"confirmations read from backticks, blocks, lines: {got}"))
        wire.save_state(ev("x", ""), "cloud", {"commands": got})
        cases.append((verdict(respond(ev("PreToolUse", "gcloud  run deploy api --region 'us-east1'"))) == "allow",
                      "confirmed exact command runs (quotes and spacing ignored)"))
        cases.append((verdict(respond(ev("PreToolUse", "gcloud run deploy api --region us-west1"))) == "deny",
                      "a different argument is a different command"))
        cases.append((verdict(respond(ev("PreToolUse", "cd infra && terraform apply -auto-approve && rm -rf .tmp"))) == "ask",
                      "confirmed cloud write inside a chain: the local hazard still asks"))
        cases.append((verdict(respond(ev("PreToolUse", "kubectl apply -f k8s/", sid="s2"))) == "deny",
                      "confirmation is per session"))
        # grants replace the watch (R15): nothing locks; each act is judged against the grants in force
        cases.append((respond(ev("PostToolUse", "rm -rf build")) is None and wire.load_state(ev("x", ""), "hazard") is None,
                      "post: nothing runs after the call, nothing locks the session"))

        def grant(spec, sid="s1"):
            return judge.record(ev("x", "", sid=sid), root, spec, "Regent: message")

        def reason(a):
            return (a or {}).get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

        grant("delete build/** -- generated output")
        cases.append((verdict(respond(ev("PreToolUse", "rm -rf build"))) == "allow", "a granted delete runs without asking"))
        cases.append((verdict(respond(ev("PreToolUse", "rm -rf build/obj build/bin"))) == "allow", "every path inside the grant"))
        cases.append((verdict(respond(ev("PreToolUse", "rm -rf build src"))) == "ask", "one path outside the grant asks"))
        out = respond(ev("PreToolUse", "rm -rf src"))
        cases.append((verdict(out) == "ask" and "grant: delete src/** for session" in reason(out),
                      f"the ask carries the Judge's proposal ({reason(out)[:90]})"))
        cases.append((verdict(respond(ev("PreToolUse", "rm -rf build", sid="s2"))) == "ask", "a session grant stays in its session"))
        cases.append((verdict(respond(ev("PreToolUse", "cd src && rm -rf ../build"))) == "allow",
                      "a 'cd' in the chain moves where paths resolve"))
        cases.append((verdict(respond(ev("PreToolUse", 'cd "$X" && rm -rf build'))) == "ask",
                      "after a 'cd' to an unknown place nothing is covered"))
        cases.append((verdict(respond(ev("PreToolUse", 'rm -rf "$d"'))) == "ask", "an unresolvable path asks"))
        scratch = Path(tmp) / "scratch"
        (scratch / "rg").mkdir(parents=True)
        grant(f"delete {scratch.as_posix()}/** -- the session's scratch clones")
        cases.append((verdict(respond(ev("PreToolUse", f"cd {scratch.as_posix()} && rm -rf rg"))) == "allow"
                      and verdict(respond(ev("PreToolUse", "rm -rf rg"))) == "ask",
                      "the 2026-10-29 false alarm: 'cd /tmp && rm -rf rg' resolves outside the project"))
        cases.append((verdict(respond(ev("PreToolUse", "git reset --hard"))) == "ask", "no path: needs '**'"))
        grant("discard ** for repo -- the plumbing branch is scratch")
        cases.append((verdict(respond(ev("PreToolUse", "git reset --hard", sid="s3"))) == "allow"
                      and verdict(respond(ev("PreToolUse", "git checkout -- src/a.cs", sid="s3"))) == "allow",
                      "a repo grant of '**' covers every discard, in every session"))
        grant("history ** -- this repository only", sid="s5")
        cases.append((verdict(respond(ev("PreToolUse", "git push --force origin feat", sid="s5"))) == "allow"
                      and verdict(respond(ev("PreToolUse", "git -C . push --force origin feat", sid="s5"))) == "allow",
                      "a history grant of '**' covers a force in this repository"))
        cases.append((verdict(respond(ev("PreToolUse", "cd ../other && git push --force origin feat", sid="s5"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "git -C ../other push --force origin feat", sid="s5"))) == "ask",
                      "'**' never reaches another repository, by 'cd' or by -C"))
        cases.append((verdict(respond(ev("PreToolUse", 'cd "$X" && git push --force origin feat', sid="s5"))) == "ask",
                      "after a 'cd' to an unknown place no grant covers a git act"))
        wire.build_fixture(Path(tmp) / "other")
        for how in ("delete ** -- this repository", "discard ** -- this repository", "history ** -- this repository"):
            grant(how, sid="s7")
        grant("discard sub/** -- this repository", sid="s8")
        for cmd in ("git -C ../other clean -fd", "cd ../other && git clean -fdx", "git -C ../other checkout -- .", "git -C ../other restore .",
                    "git -C ../other restore sub/f", "git -C . -C ../other push -f origin side", "git -C .. -C other clean -fd",
                    "Push-Location ../other; git push -f origin side", "pushd ../other && git reset --hard", "git --git-dir=../other/.git clean -fd",
                    "git --work-tree ../other clean -fd", 'cd "$X" && git checkout -- f', 'cd "$X" && git clean -fd'):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"'**' stays in this repository: {cmd}"))
        for cmd in ("git clean -fd", "git -C . clean -fd", "git checkout -- .", "git restore src/a.cs", "git -C ../proj push -f origin side",
                    "git -C .. -C proj reset --hard", "pushd . && git reset --hard"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow", f"and covers it: {cmd}"))
        cases.append((verdict(respond(ev("PreToolUse", "git -C ../other checkout -- sub/f", sid="s8"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "git checkout -- sub/f", sid="s8"))) == "allow"
                      and verdict(respond(ev("PreToolUse", "git -C sub checkout -- f", sid="s8"))) == "allow",
                      "a relative glob reads paths from where git runs"))
        cases.append((verdict(respond(ev("PreToolUse", "pushd ../other && popd && git reset --hard", sid="s7"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "cd src && popd && rm -rf ../build"))) == "ask",
                      "after a popd nothing here knows the folder"))
        bare = Path(tmp) / "bare.git"
        (bare / "objects").mkdir(parents=True)
        for cmd in ("GIT_DIR=../other/.git GIT_WORK_TREE=../other git clean -fd", "GIT_WORK_TREE=../other git clean -fd",
                    "GIT_DIR=../other/.git git push -f origin side", "GIT_DIR=../other/.git git branch -D x", "GIT_DIR=../other/.git git reset --hard",
                    "export GIT_DIR=../other/.git GIT_WORK_TREE=../other; git clean -fd", "env GIT_WORK_TREE=../other git clean -fd",
                    "$env:GIT_DIR='../other/.git'; $env:GIT_WORK_TREE='../other'; git clean -fd", "git -c core.worktree=../other clean -fd",
                    "GIT_DIR=../other/.git bash -c 'git clean -fd'", "env -C ../other git clean -fd", "env --chdir=../other git clean -fd",
                    "git -C /tmp/x/other clean -fd", "cd /tmp/x/other && git clean -fdx", "git -C /tmp/x/other reset --hard",
                    "git -C /tmp/x/other push -f origin side", "git -C /tmp/x/other branch -D x",
                    "git -C ../bare.git branch -D x", "cd ../bare.git && git branch -D x", "git -C ../bare.git update-ref -d refs/heads/feat",
                    'cmd /c "cd /d ..\\other && git clean -fd"', "git -C ..\\other clean -fd", "rm -rf sub\\..\\..\\other",
                    "builtin cd ../other && git clean -fd", "command cd ../other && git clean -fd",
                    "cd ../other && command git clean -fd", "cd ../other && env git clean -fd", "command git -C ../other reset --hard",
                    "git \\\n -C ../other clean -fd", "cd ../other && git \\\n clean -fd", "git --config-env x.y=HOME -C ../other clean -fd",
                    "for d in ../other; do git -C $d clean -fd; done", 'X=../other; rm -rf "$X"', "rm -rf ../oth*", 'rm -rf "$PWD/../other"',
                    "rm -rf $(pwd)/../other", "rm -rf sub $(pwd)/../other", "rm -rf `pwd`/../other", "rm -rf */../../other", "rm -rf {a,../other}",
                    "find ../oth* -delete", "find . ../other -delete", 'find "$PWD/../other/sub" -delete', "Remove-Item -Recurse -Force ../oth*",
                    '$x="../other"; Remove-Item -Recurse -Force $x', "Remove-Item -Path:../other -Recurse", 'X=../other; cd "$X" && rm -rf sub',
                    "(cd src); rm -rf ../x", "xargs rm -rf < list.txt", "cat list | xargs rm -rf"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"'**' opens nothing it cannot place: {cmd}"))
        for cmd in ("rm -rf build*", "rm -rf src/*.log", "rm -rf src build", "find src -delete", "find src -name x -delete",
                    "for d in a b; do git clean -fd; done", "git \\\n clean -fd", "command git clean -fd", "if true; then git reset --hard; fi"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow", f"and still covers what it can: {cmd}"))
        for cmd in ("GIT_WORK_TREE=../other git clean -fd sub", "GIT_DIR=../other/.git GIT_WORK_TREE=../other git restore sub/f"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s8"))) == "ask", f"nor does a relative glob: {cmd}"))
        for cmd in ("git branch -D x", "git update-ref -d refs/heads/x", "rm -rf x"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7", cwd=bare))) == "ask", f"a session moved to a folder outside: {cmd}"))
        out = respond(ev("PreToolUse", 'rm -rf "$X"', sid="s7"))
        cases.append(("no grant covers it" in reason(out) and "proposes" not in reason(out), "and it says so, proposing no grant that would not cover it"))
        cases += repository_edge_cases(tmp, root, ev, verdict, reason)
        cases += own_git_cases(tmp, ev, verdict, reason)
        grant("delete ** -- everything", sid="s4")
        cases.append((verdict(respond(ev("PreToolUse", "psql -c 'DROP TABLE users'", sid="s4"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "sudo apt-get install jq", sid="s4"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "docker system prune -af", sid="s4"))) == "ask",
                      "never granted: destructive SQL, installs, docker prunes"))
        cases.append((verdict(respond(ev("PreToolUse", "aws s3 cp a s3://b/a", sid="s4"))) == "deny", "a grant never opens the cloud"))
        cases.append((verdict(respond(ev("PreToolUse", "python scripts/judge.py ratify --yes"))) == "ask"
                      and verdict(respond(ev("PreToolUse", "python scripts/judge.py ratify"))) == "allow"
                      and verdict(respond(ev("PreToolUse", "python3 scripts/judge.py list"))) == "allow",
                      "judge.py ratify --yes is consent; its review and list run"))
        for cmd, want in (("echo '| JD-R9 | delete | `**` |' >> .guidelines/JD.md", "deny"),
                          ("sed -i 's/a/b/' .guidelines/JD.md", "deny"),
                          ("python -c \"open('JD.md','w').write('x')\"", "deny"),
                          ("cp /tmp/x ~/.claude/regency/judge.json", "deny"),
                          ("git checkout -- .guidelines/JD.md", "deny"),
                          ("cat .guidelines/JD.md", "allow"),
                          ("git add .guidelines/JD.md && git commit -m 'grants'", "allow"),
                          ("cat > notes.md <<'EOF'\nthe JD.md table holds the grants\nEOF", "allow")):
            got = verdict(respond(ev("PreToolUse", cmd, sid="s5")))
            cases.append((got == want, f"grant store: {cmd!r} -> {got} (want {want})"))
        store = root / ".guidelines" / "JD.md"
        store.write_text(store.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
        cases.append((verdict(respond(ev("PreToolUse", "rm -rf build"))) == "allow", "a text edit outside the table changes nothing"))
        store.write_text(store.read_text(encoding="utf-8").replace("the plumbing branch is scratch", "anything goes"),
                         encoding="utf-8")
        out = respond(ev("PreToolUse", "git reset --hard", sid="s6"))
        cases.append((verdict(out) == "ask" and "STALE" in reason(out), "a changed table is STALE: it grants nothing and says so"))
        return wire.check(cases)


def repository_edge_cases(tmp, root, ev, verdict, reason):
    """Where '**' ends, as the file system lands a path: a symbolic link out of the repository, a repository nested in its
    work tree (a clone, a bare one). Session s7 holds delete, discard and history '**' for the fixture's repository."""
    def git_folder_shape(folder):  # what git reads as a repository's own folder: HEAD, objects, refs
        for part in ("objects", "refs"):
            (folder / part).mkdir(parents=True, exist_ok=True)
        (folder / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    git_folder_shape(root / ".git")  # this repository's own, as git leaves it
    git_folder_shape(root / "vendor.git")  # a bare repository in the work tree
    (root / "nested" / ".git").mkdir(parents=True)  # a clone in the work tree
    (root / "nested" / "sub").mkdir()
    cases = []
    for cmd in ("git -C nested push -f origin side", "git -C nested reset --hard", "cd nested && git reset --hard",
                "git -C nested checkout -- .", "git -C nested/sub clean -fd", "cd nested/sub && git reset --hard", "rm -rf nested",
                "rm -rf nested/sub", "git -C vendor.git branch -D x", "git -C vendor.git update-ref -d refs/heads/x", "rm -rf vendor.git/refs"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"'**' stops at a repository nested in the work tree: {cmd}"))
    cases += nested_reach_cases(tmp, root, ev, verdict, reason)
    outside = Path(tmp) / "outside"
    (outside / "precious").mkdir(parents=True)
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
        (root / "away").symlink_to(Path(tmp) / "other", target_is_directory=True)
        (root / "inner").symlink_to(root / "src", target_is_directory=True)
    except (OSError, NotImplementedError):
        print("hook-hazard: this system cannot create a symbolic link: those cases did not run")
        return cases
    for cmd in ("rm -rf link/*", "rm -rf link/", "find link/ -delete", "rm -rf link/precious", "rm -rf link/../x",
                "cd link && rm -rf ../x", "git -C link/.. clean -fd", "git -C link reset --hard", "git -C away push -f origin side",
                "cd away && git clean -fd"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"'**' stops where a symbolic link leaves the repository: {cmd}"))
    out = respond(ev("PreToolUse", "rm -rf link/precious", sid="s7"))
    cases.append((f"'grant: delete {(outside / 'precious').resolve().as_posix()}/** for session" in reason(out),
                  f"and the Judge proposes the place it lands ({reason(out)[-110:]})"))
    for cmd in ("rm -rf inner/*", "find inner/ -delete", "git -C inner reset --hard", "rm -rf src/../build",
                "git -C src reset --hard"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow", f"and still covers what stays in this repository: {cmd}"))
    return cases + logical_cd_cases(tmp, root, ev, verdict)


def logical_cd_cases(tmp, root, ev, verdict):
    """A 'cd' moves as bash moves it: logically, a '..' taking off the folder written before it (QA-grant-latest-04 N1, N2,
    N8). current -> releases/v2 is a link inside the repository; link leads outside; away leads to the repository 'other'."""
    (root / "releases" / "v2").mkdir(parents=True)
    (root / "current").symlink_to(root / "releases" / "v2", target_is_directory=True)
    cases = []
    for cmd in ("cd current && cd ../../other && git reset --hard", "cd current && cd ../../other && git push -f origin side",
                "cd current && cd ../../other && git clean -fdx", "cd current && cd ../../other && git branch -D side",
                "cd current/../../other && git reset --hard"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask",
                      f"a git act after a `cd` that climbs through a link inside the repository into another repository asks: {cmd}"))
    for cmd in ("cd current && cd .. && rm -rf link/*", "cd current/.. && rm -rf link/precious", "cd current && cd ../away && git reset --hard",
                "cd -P link && cd .. && rm -rf x"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"a 'cd' through a link and back lands where the shell lands: {cmd}"))
    for cmd in ("cd link/.. && rm -rf build", "cd link && cd .. && rm -rf build", "cd current && cd .. && git reset --hard"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow", f"and a 'cd' back into this repository stays in it: {cmd}"))
    for cmd in ("set -P; cd link && cd .. && rm -rf x", "set -o physical; cd link && cd .. && rm -rf x"):  # QA-grant-latest-05 N11
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask",
                      f"set -P, then a cd through an outward link and back, then a removal: asks: {cmd}"))
    cases.append((verdict(respond(ev("PreToolUse", "set -P; pushd link/.. && rm -rf x", sid="s7"))) == "ask",  # QA-grant-latest-06 §4
                  "set -P, then pushd through an outward link's .. and a removal: asks"))
    for cmd in ("set -eo physical; cd link && cd .. && rm -rf x", "set -Pe; cd link && cd .. && rm -rf x",
                "set -P -o nosuch; cd link && cd .. && rm -rf x", "set -P; pushd link && cd .. && rm -rf x",
                "if true; then set -P; fi; cd link && cd .. && rm -rf x", "bash -P -c 'cd link && cd .. && rm -rf x'",
                "bash -o physical -c 'cd link && cd .. && rm -rf x'", "bash -c -P 'cd link && cd .. && rm -rf x'"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask", f"and so does every other way the line turns physical mode on: {cmd}"))
    for cmd in ("set -e; cd link && cd .. && rm -rf x", "set -P; set +P; cd link && cd .. && rm -rf x",
                "set -o physical +o physical; cd link && cd .. && rm -rf x", "set -P; cd -L link && cd -L .. && rm -rf x",
                "set -Ps; cd link && cd .. && rm -rf x", "set -o nosuch -P; cd link && cd .. && rm -rf x",
                "set -- -P; cd link && cd .. && rm -rf x", "set -P; bash -c 'cd link && cd .. && rm -rf x'"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow",
                      f"and where bash stays logical, the 'cd' back stays in this repository: {cmd}"))
    for part in ("w", "src"):  # only under releases/: bash's own reading of current/../w finds no folder
        (root / "releases" / part).mkdir()
    for cmd in ("cd current/../w && cd ../.. && rm -rf build", "cd current/../w/../src && cd ../.. && rm -rf build"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow",
                      f"where bash's own reading finds no folder, the 'cd' lands where the file system does: {cmd}"))
    return cases


def nested_reach_cases(tmp, root, ev, verdict, reason):
    """A recursive removal that names a folder of this repository reaches the repositories nested below it (the Regent,
    2026-11-23, QA-grant-latest-04 N5). By now nested/ (a clone) and vendor.git (a bare one) sit at the root."""
    (root / "vendor" / "lib" / ".git").mkdir(parents=True)
    (root / "src" / "pages" / "old").mkdir(parents=True, exist_ok=True)  # folders below, none a repository
    (root / ".git" / "modules" / "sub").mkdir(parents=True)
    for part in ("HEAD", "objects", "refs"):
        (root / ".git" / "modules" / "sub" / part).mkdir()
    cases = []
    for cmd in ("rm -rf *", "rm -rf .", "rm -rf vendor", "find . -delete", "find vendor -delete", "git clean -ffdx",
                "Remove-Item -Recurse -Force vendor", "git -C vendor clean -f -f -d"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "ask",
                      f"'**' stops at a repository a recursive removal reaches below a folder it names: {cmd}"))
    for cmd in ("rm -rf src", "find src -delete", "rm -rf build*", "rm vendor"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow",
                      f"and a removal that reaches no repository below stays covered: {cmd}"))
    out = respond(ev("PreToolUse", "rm -rf vendor", sid="s7"))
    lib = (root / "vendor" / "lib").resolve().as_posix()
    proposed = f"grant: delete vendor/** {lib}/** for session"
    granted = proposed in reason(out) and judge.record(ev("x", "", sid="s7n"), root, f"{proposed[7:-12]} -- as proposed", "Regent: message")
    cases.append((bool(granted) and verdict(respond(ev("PreToolUse", "rm -rf vendor", sid="s7n"))) == "allow",
                  f"the Judge proposes each repository it reaches, and granting that covers the act ({reason(out)[-120:]})"))
    places = " ".join(f"{(root / n).resolve().as_posix()}/**" for n in ("nested", "vendor.git", "vendor/lib"))
    judge.record(ev("x", "", sid="s7p"), root, f"delete {places} -- the nested ones only", "Regent: message")
    out = respond(ev("PreToolUse", "git clean -ffdx", sid="s7p"))
    proposed = re.search(r"proposes 'grant: (.*) for session", reason(out))
    granted = proposed and judge.record(ev("x", "", sid="s7q"), root, f"{proposed.group(1)} -- as proposed", "Regent: message")
    cases.append((verdict(out) == "ask" and proposed and proposed.group(1).startswith("delete ** ") and bool(granted)
                  and verdict(respond(ev("PreToolUse", "git clean -ffdx", sid="s7q"))) == "allow",
                  "an act that names no path still needs '**' beside the repositories it reaches: git clean -ffdx"))
    budget, judge.WALK_SECONDS = judge.WALK_SECONDS, -1.0
    out = respond(ev("PreToolUse", "rm -rf src", sid="s7"))
    judge.WALK_SECONDS = budget
    cases.append((verdict(out) == "ask" and "No script can tell" in reason(out),
                  "a search below that runs out of time places nothing, so no grant covers it: rm -rf src"))
    return cases + git_clean_cases(tmp, ev, verdict)


def own_git_cases(tmp, ev, verdict, reason):
    """'**' stops short of the repository's own .git (the Regent, 2026-11-25): a removal that names it, a path on or in it,
    or a recursion from the root above it asks, as one that reaches a nested repository does. The fixture holds nothing
    below but its own .git, so that is what each ask is for."""
    own = wire.build_fixture(Path(tmp) / "own")
    for part in ("objects", "refs"):
        (own / ".git" / part).mkdir(parents=True, exist_ok=True)
    (own / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (own / "src" / "f").mkdir(parents=True)
    (own / ".gitignore").write_text("build/\n", encoding="utf-8")
    for how in ("delete", "discard"):
        judge.record(ev("x", "", sid="s10"), own, f"{how} ** -- this repository", "Regent: message")
    cases = []
    for cmd, tool in (("rm -rf .git", "Bash"), ("rm -rf ./.git/", "Bash"), ("find .git -delete", "Bash"), ("find . -delete", "Bash"),
                      ("rm -f .git/index.lock", "Bash"), ("Remove-Item -Recurse -Force .git", "PowerShell"), ("rmdir .git", "Bash"),
                      ("unlink .git", "Bash"), ("rm -rf .git/modules", "Bash"), ("rm -rf .", "Bash"), ("find -delete", "Bash"),
                      ("find . -name x -delete", "Bash"), ("rm -rf .*", "Bash"), ("rm -rf .git*", "Bash"), ("rm -f .g*/index.lock", "Bash"),
                      ("cd src && rm -rf ..", "Bash"), ("cd src && rm -rf ../.git", "Bash"), ("rm -rf ../own", "Bash"),
                      ("Remove-Item -Recurse -Force .", "PowerShell")):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s10", tool=tool, cwd=own))) == "ask",
                      f"'**' stops short of the repository's own .git: {cmd}"))
    for cmd in ("rm -rf *", "rm -rf src", "find src -delete", "rm -f .gitignore", "git clean -fdx", "git clean -ffdx",
                "git -C .git branch -D x", "git reset --hard"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s10", cwd=own))) == "allow",
                      f"and an act that does not reach it stays covered: {cmd}"))
    real = Path(os.path.realpath(str(own))).as_posix()
    for n, (cmd, tool) in enumerate((("rm -rf .git", "Bash"), ("find . -delete", "Bash"), ("rm -f .git/index.lock", "Bash"),
                                     ("rm -f .g*/index.lock", "Bash"), ("Remove-Item -Recurse -Force .git", "PowerShell"))):
        out = respond(ev("PreToolUse", cmd, sid="s10", tool=tool, cwd=own))
        proposed = re.search(r"proposes 'grant: (.*) for session", reason(out))
        granted = proposed and f"{real}/.git" in proposed.group(1) and judge.record(
            ev("x", "", sid=f"s10g{n}"), own, f"{proposed.group(1)} -- as proposed", "Regent: message")
        cases.append((bool(granted) and verdict(respond(ev("PreToolUse", cmd, sid=f"s10g{n}", tool=tool, cwd=own))) == "allow",
                      f"the Judge proposes the repository's own .git as a place of its own, and granting that covers the act: {cmd}"))
    return cases


def git_clean_cases(tmp, ev, verdict):
    """git clean as git reads it (QA-grant-latest-05 N12, N13): a second -f reaches every repository nested below where it
    runs, one -f the bare ones git reads as repositories, and an exclude pattern is no folder it names. In both fixtures
    tmp/clone is a clone; gc holds an untracked bare repository, plain a folder only shaped like one."""
    def shaped(folder, head="ref: refs/heads/main\n"):  # HEAD, objects, refs: what git reads as a repository's own folder
        for part in ("objects", "refs"):
            (folder / part).mkdir(parents=True, exist_ok=True)
        (folder / "HEAD").write_text(head, encoding="utf-8")

    gc, plain = wire.build_fixture(Path(tmp) / "gc"), wire.build_fixture(Path(tmp) / "plain")
    clone = wire.build_fixture(Path(tmp) / "clone")  # a nested clone and nothing else below: no bare repository, none shaped like one
    for root in (gc, plain, clone):
        shaped(root / ".git")
        shaped(root / "tmp" / "clone" / ".git")
        (root / "src" / "f").mkdir(parents=True)
        judge.record(ev("x", "", sid="s9"), root, "delete ** -- this repository", "Regent: message")
    shaped(gc / "vendor.git")
    shaped(plain / "data", head="not a repo\n")
    cases = []
    for cmd in ("git clean -ffdx -e keep", "git clean -ffdx -e '*.log'", "git clean -ffdxe keep", "git clean -ffdx --exclude keep"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s9", cwd=gc))) == "ask",
                      f"git clean -ff with an exclude pattern over a nested clone asks: {cmd}"))
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s9", cwd=clone))) == "ask",  # QA-grant-latest-06 §4: the clone alone
                      f"git clean -ff with an exclude pattern over a nested clone asks, with no bare repository below: {cmd}"))
    for cmd, label in (("git clean -ffdx", "git clean -ffdx over a nested clone with no bare repository asks"),  # QA-grant-latest-06 §4
                       ("git clean -ffdx --exc keep", "git clean -ffdx --exc keep over a nested clone asks"),
                       ("git clean --force --force -dx", "git clean --force --force -dx over a nested clone asks")):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s9", cwd=clone))) == "ask", label))
    for cmd in ("git clean -fdx", "git clean -fd", "git clean -f -d -x -e keep", "git clean -fdxe keep", "git clean -fdx -- ."):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s9", cwd=gc))) == "ask",
                      f"git clean -f over an untracked bare repository in the work tree asks: {cmd}"))
    cases.append((verdict(respond(ev("PreToolUse", "git clean -fdx", sid="s9", cwd=plain))) == "allow",
                  "and a removal that reaches no repository below stays covered: git clean -fdx"))
    for cmd in ("git clean -fdx src", "git clean -ffdx src", "git clean -fdx -e vendor.git src"):
        cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s9", cwd=gc))) == "allow",
                      f"and a git clean whose paths reach no repository below stays covered: {cmd}"))
    budget, judge.WALK_SECONDS = judge.WALK_SECONDS, -1.0
    out = verdict(respond(ev("PreToolUse", "git clean -fdx", sid="s9", cwd=plain)))
    judge.WALK_SECONDS = budget
    cases.append((out == "ask", "a git clean -f's search below that runs out of time places nothing, so no grant covers it"))
    return cases


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else wire.serve(respond, guard=True))
