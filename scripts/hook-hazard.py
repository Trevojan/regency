#!/usr/bin/env python3
"""hook-hazard.py - the shell's hazardous ground (Bash and PowerShell), before and after the call.

PreToolUse   classify every command segment:
               cloud read    get, list, describe, logs, plan, ...                 nothing (allowed)
               cloud write   anything else on a cloud CLI                         deny, unless the Regent
                             confirmed that exact command in this pass            (conventions §6, R5.1)
               destructive   deleting, discarding work, force / history rewrites  ask (conventions §5)
               layout, install                                                    ask
PostToolUse  when a destructive command actually ran inside the project, switch on the session's
             HAZARD WATCH: hook-acts-guard.py then refuses every write no permit covers, until the
             Regent says a release verb (conventions §9, R5.2). The agent may still look around (R4.4).
             A delete whose every path lies outside the project (a temp or scratch folder) starts nothing.
PostToolUse  Agent|Task: a PO or QA role agent that returns 'permit: <glob>[, <glob>] -- <reason>'
             lines grants this session writes to those paths while the watch is on. The agent that
             needs the permit never grants it (conventions §1).

A pass is the work between two messages of the Regent. hook-verbs.py records, at each message, the
cloud commands the Regent quoted (in backticks, a code block, or on a line of their own); only those
exact commands, compared token by token, may write to the cloud until the next message.

Market pattern: human-in-the-loop approval of a specific tool call (LangGraph interrupt) plus a
circuit breaker that stays open until a human closes it.

Modes:  (no args) hook · --selftest · --clear (release every hazard watch on this machine)
Pure standard library, Python 3.8+.
"""
import fnmatch
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

_spec = importlib.util.spec_from_file_location("guard_push", HERE / "guard-push.py")
guard_push = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard_push)  # one tokenizer for every shell guard
_spec = importlib.util.spec_from_file_location("hook_gov", HERE / "hook-gov.py")
hook_gov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook_gov)  # one reader for what a subagent returned

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


def words(seg):
    """The segment without its leading env assignments (FOO=1 cmd ...)."""
    out = list(seg)
    while out and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", out[0]):
        out.pop(0)
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
    a, j = args, 0
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
    if verb == "push" and flags & {"-f", "--force", "--force-with-lease", "--force-if-includes"}:
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
    return None


def findings(command, depth=0):
    """Every finding in a command, nested shells included: [(kind, label)]."""
    out = []
    for seg in guard_push.segments(guard_push.data_only(command)):
        if depth < 3 and seg and name(seg[0]) in SHELLS:
            for t in seg[1:]:
                if " " in t:
                    out += findings(t, depth + 1)
        f = classify_words(words(seg))
        if f:
            out.append(f)
    return out


RM_COMMANDS = {"rm", "rmdir", "unlink", "shred", "del", "erase", "rd", "remove-item", "ri"}


def inside(arg, cwd, repo):
    """True unless the path surely lies outside the project; a variable or a glob counts as inside."""
    if re.search(r"[$%*?{]", arg):
        return True
    m = re.match(r"^/([a-zA-Z])/(.*)$", arg) if os.name == "nt" else None
    p = Path(f"{m.group(1)}:/{m.group(2)}" if m else os.path.expanduser(arg))
    p = p if p.is_absolute() else Path(cwd) / p
    try:
        Path(os.path.normpath(str(p))).relative_to(repo)
        return True
    except ValueError:
        return False


def hits_project(command, cwd, depth=0):
    """The first destructive finding that reaches the project, or None. A delete that names only
    paths outside the project (temp, scratch) does not reach it."""
    repo = wire.repo_root(Path(cwd))
    for seg in guard_push.segments(guard_push.data_only(command)):
        if depth < 3 and seg and name(seg[0]) in SHELLS:
            for t in seg[1:]:
                found = hits_project(t, cwd, depth + 1) if " " in t else None
                if found:
                    return found
        w = words(seg)
        f = classify_words(w)
        if not f or f[0] not in DESTRUCTIVE:
            continue
        paths = [a for a in w[1:] if not a.startswith("-")]
        if name(w[0]) not in RM_COMMANDS or not paths or any(inside(a, cwd, repo) for a in paths):
            return f
    return None


# ---------- permits: a PO or QA role agent lets writes through the watch -------------------------

PERMITTERS = ("po", "qa")
PERMIT_LINE = re.compile(r"(?im)^[\s>*-]*permit:\s*(.+?)\s+(?:--|—)\s+(\S.*)$")


def permits(text):
    """[(globs, reason)] from the permit lines of a returned packet; a line without a reason is no permit."""
    return [([g.strip("`") for g in re.split(r"[,\s]+", m.group(1)) if g.strip("`")], m.group(2).strip())
            for m in PERMIT_LINE.finditer(text or "")]


def permitted(event, rel):
    st = wire.load_state(event, "permit") or {}
    return any(fnmatch.fnmatchcase(rel, g) for g in st.get("globs", []))


def grant(event):
    """Record the permits a PO or QA role agent returned; one context line, or None."""
    agent = str(wire.tool_input(event).get("subagent_type") or "")
    if agent.split(":")[-1].strip().lower() not in PERMITTERS:
        return None
    found = permits(hook_gov.returned_text(event))
    if not found:
        return None
    st = wire.load_state(event, "permit") or {"globs": [], "grants": []}
    for globs, reason in found:
        st["globs"] += [g for g in globs if g not in st["globs"]]
        st["grants"].append({"by": agent, "globs": globs, "reason": reason, "at": wire.now()})
    wire.save_state(event, "permit", st)
    return wire.context("PostToolUse", f"permit from {agent}: writes to {', '.join(st['globs'])} pass the hazard watch "
                                       f"for this session ({found[-1][1]})")


ORDER = {"cloud-write": 0, "history": 1, "discard": 2, "delete": 3, "layout": 4, "install": 5}
DESTRUCTIVE = {"history", "discard", "delete"}


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
    if event.get("hook_event_name") == "PostToolUse" and event.get("tool_name") in hook_gov.AGENT_TOOLS:
        return grant(event)
    if event.get("tool_name") not in wire.SHELL_TOOLS:
        return None
    command = wire.tool_input(event).get("command", "")
    phase = event.get("hook_event_name")
    if phase == "PreToolUse":
        found_all = findings(command)
        writes = [label for kind, label in found_all if kind == "cloud-write"]
        missing = [c for c in writes if c not in confirmed(event)]
        if missing:
            return wire.permission("deny", f"cloud write '{missing[0]}' was not confirmed by the Regent in this pass. "
                                           "Cloud belongs to its owner: reads run freely, a write runs only when the "
                                           "Regent quotes that exact command in a message (conventions §6)")
        local = sorted((f for f in found_all if f[0] in ORDER and f[0] != "cloud-write"), key=lambda f: ORDER[f[0]])
        if local:
            return wire.permission("ask", f"{local[0][0]}: '{local[0][1]}' needs the Regent's yes (conventions §5)")
        return None
    found = hits_project(command, event.get("cwd") or os.getcwd()) if phase == "PostToolUse" else None
    if found:
        kind, label = found
        wire.save_state(event, "hazard", {"label": label, "kind": kind, "at": wire.now()})
        words_ = "', '".join(wire.release_words()) or "a release verb"
        return wire.context("PostToolUse", f"hazard watch on: '{label}' ran. Writes no PO/QA permit covers are refused "
                                           f"until the Regent says '{words_}' (conventions §9); reading and inspecting stay free (R4.4)")
    return None


def clear_all():
    n = 0
    for p in wire.state_dir().glob("*.hazard.json"):
        p.unlink()
        n += 1
    print(f"hazard watch released in {n} session(s)")
    return 0


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
]


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")

        def ev(phase, cmd, sid="s1", tool="Bash"):
            return {"hook_event_name": phase, "tool_name": tool, "session_id": sid, "cwd": tmp,
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
        cases.append((respond(ev("PostToolUse", "ls")) is None and wire.load_state(ev("x", ""), "hazard") is None,
                      "post: harmless command leaves no watch"))
        cases.append((respond(ev("PostToolUse", "sudo apt-get install jq")) is None
                      and wire.load_state(ev("x", ""), "hazard") is None, "post: install is not destructive"))
        out = respond(ev("PostToolUse", "git reset --hard"))
        st = wire.load_state(ev("x", ""), "hazard")
        cases.append((bool(out) and bool(st) and st.get("label") == "git reset --hard", "post: reset --hard sets the watch"))
        cases.append((wire.load_state(ev("x", "", sid="s2"), "hazard") is None, "post: watch is per session"))
        outside = Path(tmp).parent / "elsewhere-regency" / "scratch"
        cases.append((respond(ev("PostToolUse", f'rm -rf "{outside}"', sid="s3")) is None,
                      "post: a delete outside the project starts no watch"))
        cases.append((bool(respond(ev("PostToolUse", f'rm -rf "{outside}" build', sid="s3"))),
                      "post: one path inside the project is enough"))
        cases.append((bool(respond(ev("PostToolUse", 'rm -rf "$d"', sid="s4"))), "post: an unknown path counts as inside"))

        def agent(kind, text, sid="s5"):
            return respond({"hook_event_name": "PostToolUse", "tool_name": "Agent", "session_id": sid, "cwd": tmp,
                            "tool_input": {"subagent_type": kind},
                            "tool_response": {"content": [{"type": "text", "text": text}]}})
        pkt = "Granted.\npermit: library/*.md, `scripts/hook-*.py` -- rewrite of the chapter the agent reset\npermit: x.md"
        cases.append((agent("general-purpose", pkt) is None and wire.load_state(ev("x", "", sid="s5"), "permit") is None,
                      "permit: only a PO or QA role agent grants"))
        out = agent("regency:po", pkt)
        e5 = ev("x", "", sid="s5")
        cases.append((bool(out) and permitted(e5, "library/conventions.md") and permitted(e5, "scripts/hook-hazard.py")
                      and not permitted(e5, "x.md") and not permitted(e5, "README.md"),
                      "permit: globs recorded; a line without a reason grants nothing"))
        return wire.check(cases)


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else clear_all() if "--clear" in a else wire.serve(respond, guard=True))
