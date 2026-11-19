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
             A 'cd' earlier in the chain moves where later paths resolve. A grant opens only what this reader can place:
             a path or a folder no script can know ("$d", $( ), GIT_DIR, xargs) is covered by no grant, '**' included.

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
import importlib.util
import os
import re
import sys
import tempfile
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
    that unless it climbs out after the glob."""
    if here is None or re.search(r"[$%{]", arg) or (os.name != "nt" and "\\" in arg):
        return None
    glob = GLOB.search(arg)
    if glob:
        if ".." in re.split(r"[\\/]", arg[glob.start():]):
            return None
        arg = re.match(r"^(?:.*[\\/])?", arg[:glob.start()]).group(0) or "."
    m = re.match(r"^/([a-zA-Z])/(.*)$", arg) if os.name == "nt" else None
    p = Path(f"{m.group(1)}:/{m.group(2)}" if m else os.path.expanduser(arg))
    return Path(os.path.normpath(str(p if p.is_absolute() else Path(here) / p)))


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


def act_paths(kind, label, w, here, root=None):
    """The paths an act names, for a grant to cover: [] names none (it needs '**'); a None in the list is one no script can
    know, which no grant covers; None = never grantable. A git act is judged where it runs: what it names resolves against
    that folder, and `**` is this repository, the one whose .git is on the way up from there."""
    if name(w[0]) in ("sudo", "doas"):
        w = words(w[1:])
    cmd, args = name(w[0]), w[1:]
    if kind not in judge.KINDS or cmd in UNGRANTABLE or cmd.startswith("mkfs."):
        return None
    if cmd in RM_COMMANDS:
        return [resolve(a, here) for a in operands(args)] or [None]
    if cmd == "find":
        stop = next((i for i, a in enumerate(args) if a.startswith(("-", "!"))), len(args))
        return [resolve(a, here) for a in args[:stop]] or [here]
    if cmd != "git":
        return []
    where = git_folder(args, here)
    if where is None:
        return [None]
    if label in ("git checkout -- <paths>", "git restore", "git clean -f"):
        verb = next((i for i, a in enumerate(args) if a in ("checkout", "restore", "clean")), None)
        rest = args[verb + 1:] if verb is not None else []
        paths = rest[rest.index("--") + 1:] if "--" in rest else [a for a in rest if not a.startswith("-")]
        if paths:
            return [resolve(a, where) for a in paths]
    top = next((p for p in [where] + list(where.parents) if (p / ".git").exists()), None)
    return [] if root is None or top == root else [where]


def acts(command, cwd, depth=0, root=None):
    """Every finding with the paths it names: [(kind, label, paths)], nested shells included. A 'cd' moves where the later
    segments of the chain resolve their paths, and a line this reader cannot place leaves a None for no grant to cover."""
    out, here = [], Path(cwd) if cwd else None
    root = root or here
    text = re.sub(r"\\\r?\n", " ", guard_push.data_only(command))
    for seg in guard_push.segments(text):
        w = words(seg)
        if depth < 3 and any(name(t) in SHELLS for t in seg[:1] + w[:1]):
            for t in seg[1:]:
                if " " in t:
                    out += acts(t, here, depth + 1, root)
        if w and name(w[0]) in CD_COMMANDS:
            target = [t for t in operands(w[1:]) if t.lower() != "/d"]  # cmd's cd /d <folder>
            # a 'cd' inside ( ) ends with it, and which ones those are is more than this reader follows
            here = None if "(" in text or not target or target[0] == "-" else resolve(target[0], here)
            continue
        f = classify_words(w)
        if f:
            paths = act_paths(f[0], f[1], w, here, root)
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
    found_all = acts(command, cwd, root=repo)
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
        for cmd in ("rm -rf build*", "rm -rf src/*.log", "rm -rf src build", "find src -delete", "find . -name x -delete",
                    "for d in a b; do git clean -fd; done", "git \\\n clean -fd", "command git clean -fd", "if true; then git reset --hard; fi"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7"))) == "allow", f"and still covers what it can: {cmd}"))
        for cmd in ("GIT_WORK_TREE=../other git clean -fd sub", "GIT_DIR=../other/.git GIT_WORK_TREE=../other git restore sub/f"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s8"))) == "ask", f"nor does a relative glob: {cmd}"))
        for cmd in ("git branch -D x", "git update-ref -d refs/heads/x", "rm -rf x"):
            cases.append((verdict(respond(ev("PreToolUse", cmd, sid="s7", cwd=bare))) == "ask", f"a session moved to a folder outside: {cmd}"))
        out = respond(ev("PreToolUse", 'rm -rf "$X"', sid="s7"))
        cases.append(("no grant covers it" in reason(out) and "proposes" not in reason(out), "and it says so, proposing no grant that would not cover it"))
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


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else wire.serve(respond, guard=True))
