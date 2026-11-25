# The Judge — the Regent's grants

Decision record R15 (`REGENCY_CUSTOMIZATION.md`). Engine: `scripts/judge.py`. Hooks: `scripts/hook-hazard.py`
(checks), `scripts/hook-verbs.py` and `scripts/hook-judge.py` (record), `scripts/hook-acts-guard.py` (protects).
Playbook: `/regency:judge`.

## 1. The idea

A **grant** is a standing answer the Regent gives ahead of time to `hook-hazard.py`'s ask or the push guards' denial
of `main`, for named places and kinds of act. Each act is judged when it happens, against the grants in force then; nothing locks the session after
a destructive step, and a path outside the project (a scratch clone in a temp folder) is judged where it really is.

Rule zero holds: *the check is a lookup, not an inference*. The AA side of the Judge only interviews and proposes;
whether an act is covered is decided by `judge.covers()`, a script.

## 2. A grant

| Part | Rule |
|---|---|
| **how** | `delete`, `discard`, `history`, `layout`: the kinds `hook-hazard.py` asks about and a grant may cover; `push`: the push guards' denial of `main` (below) |
| **where** | globs relative to the repository root, or absolute. `X/**` covers the folder `X` itself; `*` crosses folders; `**` is the whole repository short of its own `.git` and of every repository nested in it, and never reaches outside it; a relative glob holds no `..` |
| **scope** | where the grant lives (§3); the narrowest, `session`, when the Regent names none |
| **why** | required: a grant without a reason grants nothing |

Ids: `JD-S##` (session), `JD-R##` (repo), `JD-M##` (machine), `JD-P##` (a file the Regent names), numbered per store.

**Covered** means: every path the act names matches a glob of **one** grant of its kind. An act that names no path
(`git reset --hard`, `git rebase`, `git branch -D`) needs `**`. A path inside the repository is matched by its relative
form with its leading and trailing dots dropped, so `env/**` covers `.env` and a relative glob that opens with a dot
covers nothing. A glob in a path reads as the folder its literal part leads to, unless it climbs out after the
glob; a symbolic link its wildcard part matches is not followed, so `rm -rf lin*/x` reads as the root wherever `link`
leads.

**Where a `cd` leaves the shell.** A `cd` (`pushd`, `Push-Location`) earlier in the chain moves the shell as bash moves
it: logically, each `..` taking off the folder written before it, so `cd current && cd ..` is back where it started
whatever `current` links to; where bash's own reading finds no folder, under `cd -P` and in physical mode, it lands where
the file system does. The agent's shell starts logical (the Regent, 2026-11-25). The reader turns physical mode on at a
`set -P` or `set -o physical` in the line, and for a shell the line starts as `bash -P -c …` or `bash -o physical -c …`;
it turns it off at a `set +P` or `set +o physical`; `cd -L` still moves logically. Every `set` in the line is applied in
the order written, whether bash runs it or not: one after `||`, in a branch not taken, in a pipe or in the background
counts. A `set` holding a letter bash does not know changes nothing, and an `-o` name bash does not know stops it there;
`-o` always takes the next word as its name, so `set -o -P` changes nothing here, where bash turns physical mode on. Not
read, though each turns physical mode on in bash: `shopt -s -o physical`, a `set -P` inside a quoted `eval`, a heredoc fed
to `bash -P`, and `SHELLOPTS` naming `physical` for a shell the line starts; the quoted words of an `eval` are read as a
shell of their own, which starts logical. Wherever bash moves physically and the reader logically, a removal through a
link out of the repository and back lands outside it, and `**` still covers it (N17). The later paths and git acts
resolve from where the reader leaves the shell, against the file system as it stands before the line runs: a link or a
repository the line makes is not seen (R6).

**Where a path lands.** A path written inside the repository is in it only where the file system lands it: every
symbolic link on it followed, the last one too, and every `..` read from where a link leads, except a `..` that climbs
out of the repository's own text, which is read as written (N3); and short of any repository nested in the work tree, a
folder below the root that holds its own `.git` (a clone, a submodule) or holds `HEAD`, `objects` and `refs`, which a
plain folder shaped like a bare repository also does (N9). A path that lands inside is matched as written, not where a
link inside leads (N4). **`**` stops short of the repository's own `.git`** (the Regent, 2026-11-25): a removal that
names it, names a path on it or in it, or reaches it from the root above (`rm -rf .git`, `rm -f .git/index.lock`,
`rm -rf .`, `find .` whatever its tests, a glob on the root whose wildcard part matches `.git`, such as `.*`) asks under
`**` and under every relative glob, `.git/**` included, as one that reaches a nested repository does, and the Judge
proposes the `.git`, or the path in it, as an absolute place, so the Regent can grant it by name. git clean never removes
it. A git act run inside it is read as run in this repository, a submodule's git folder under `.git/modules/` included,
though git reads that folder as the submodule's own repository. A path that lands outside reads as the absolute place it
lands, so `**` and every relative glob stop short of it, an absolute glob may name it, and the Judge proposes that place.
A path written outside the repository is read as written. A git act is judged where it runs, through its `-C` too: in the
repository git finds from there, so `**` and every relative glob stop at this repository and a nested one is another.

**A recursive removal** (`rm -r`, `find`, `Remove-Item -Recurse`, `rd /s`, `del /s`, `git clean -ff`) that names a folder
of this repository also acts on every repository nested below it (the Regent, 2026-11-23), found by the names above, so
a plain folder shaped like a bare repository makes it ask too (N14). `git clean` with one `-f` acts on every bare
repository below it, read as git reads one (a `HEAD` naming a ref or a commit, beside `objects/` and `refs/`). Its search passes whole a folder whose `.git` is a folder git reads as a
repository, and a folder whose `.git` is a file, whatever the file holds; git passes the second whole only when the file
points at a repository, so a bare repository below a `.git` file git does not read is removed and not seen (N20). The
search runs whatever `-d`, `-x`, `-X` or `-n` say, so a single `-f` with no `-d`, with `-X` or with `-n` asks over a
bare repository git leaves in place (N18: prompts only). Each repository found is a place of its own, which `**` and
every relative glob stop short of, so the act asks unless an absolute glob names it, the Judge proposes each beside the
act's own place, and an act that names no path still needs `**` too. A `git clean` is searched from the paths it names,
each read as a folder: the pattern of `-e` or `--exclude`, glued on or in the next word, is none, so the search starts
where git runs, and neither that pattern nor `-d` narrows it. git's pathspec magic (`:!…`, `:^…`, `:(exclude)…`, `:/`)
is read as a folder that does not exist, and git's own wildcards, which match across `/`, as a shell glob on one level,
so the search finds less than git removes, and such a git clean can remove a nested clone or a bare repository under
`**` (N19). A glob reaches the entries its first wildcard part matches, dot names only when that part opens with a dot,
matched by Python's `fnmatch`: `[!…]` as bash reads it, `[^…]` as a literal `^`, which bash reads as `[!…]`, so the
search can skip a folder bash picks (N15). The search below follows no link, enters no `.git`, passes a folder the
hook's user cannot read, which a removal run as that user cannot go below either (one under `sudo` can: N16), and ends
at each repository it finds; one that runs past 3 seconds places nothing, so the act asks. `judge.py check delete` looks
below its paths the same way, the root's `.git` included.

A path no script can place is covered by no grant, `**` included: `"$d"`, `$( )`, backticks, `xargs`, `env -C`, `GIT_DIR`,
`GIT_WORK_TREE`, `core.worktree`, a `cd` to an unknown place or after `( )`, a git act in a folder no script can know
(`cd "$X"`, `--git-dir`), and a backslash read off Windows, where it may be a separator or an escape. What the guard does
not read at all is in `library/hooks.md` §2.

**Never granted**, so they keep asking or denying whatever a grant says: installing system software, destructive SQL,
docker prunes and disk tools (data outside files), cloud writes (conventions §6) and pack consent (T5). `edit` and
`move` are not kinds: regency asks before neither, so there is nothing to grant.

**A `push` grant** (the Regent, 2026-11-06) lets an agent push `main` or `master` in that repository, on any remote,
whether or not the Regent typed the command, for as long as the grant lasts: `grant: push main for session -- <why>`.
It names the branch and stands alone: no glob, no other kind on its line, and other branches need no grant. Both push
guards read it (`library/hooks.md` §2). It never covers deleting the branch. `guard-push.py` also refuses `--all`,
`--mirror` and a `+` refspec under it, and `hook-refs.py` refuses a forced update unless a `history` grant of `**` covers
it too. Where the auto-mode profile is installed or a headless run passes it, its `hard_deny`
(`library/automode.json`) still refuses the push. An agent proposes one only when the Regent asks for it.

A grant removes **regency's** ask only. Claude Code's own permission rules, its permission mode and the auto-mode
classifier still decide the call (a hook's silence approves nothing).

## 3. Where grants live — the Regent's choice

| Scope | File | Reaches |
|---|---|---|
| `session` | `<state>/sessions/<sid>.grants.json` (outside the repository) | this session, this repository |
| `repo` | `<guidelines>/JD.md`, else `<repo>/JD.md` | every session in this repository, every clone (committed with it) |
| `machine` | `~/.claude/regency/JD.md` | this repository, every session on this machine |
| a `.md` path | the file the Regent names, listed in `~/.claude/regency/judge.json` `sources` (or `REGENCY_JD`, `os.pathsep`-separated) | the repositories its rows name |

**Cloud sessions.** A cloud session starts on a fresh machine, so its `~/.claude` lasts as long as the session. A
grant reaches it through the repository (`repo`, visible to everyone who clones it), through `REGENCY_JD` set in the
cloud environment, or through the device bridge while the Regent's computer is awake. On a fresh machine the
repository's `JD.md` has no fingerprint yet, so it reads STALE until the Regent says `ratify grants` once (§5).

A file store's table sits between `<!-- jd:grants -->` and `<!-- /jd:grants -->`, one row per grant:
`| id | how | where | repo | why | by | at |`. `repo` is `.` in a repository's own `JD.md`; elsewhere the repository's
absolute path, or `*` for every repository (a hand edit the Regent ratifies). Text outside the markers is free.

## 4. Who grants

Only the Regent (conventions §1). Two ways in, both read by hooks from sources an agent cannot write:

1. **A `grant:` line** in a message of the Regent's (`UserPromptSubmit`, `hook-verbs.py`):
   `grant: delete, discard Herança/** for repo -- the old layout goes`. Every line that opens with `grant:` counts,
   in any message length; a quoted, listed or fenced line does not. Only the Regent's own words count, so nothing a tag
   encloses does: a reminder, a subagent's report, a command's output, from a block's first opening to its last closing,
   and a harness tag left open takes the rest of the message. It fails closed: a message holding a `<paste…` tag records
   none. The hook says how many lines it did not read. This way works on every surface.
2. **The Judge's pop-up** (`hook-judge.py`): one `AskUserQuestion` question per grant, header `JD grant`, the grant
   in one backtick span, options `Session` · `Repo` · `This machine` · `No` (a typed `.md` path picks a file). The
   grant text is the agent's proposal, read by the Regent before answering; the scope is the Regent's pick. A Judge
   question that arrives with `answers` filled in is denied (`PreToolUse`).

`judge.py` has no command that adds a grant.

## 5. STALE and ratification

Every time a hook writes the Regent's grant into a file store, `~/.claude/regency/judge.json` records the
fingerprint of its table. A store whose table changed any other way (a pull, the Regent's hand edit, an agent's shell)
reads **STALE**: it grants nothing, `hook-hazard.py` says so in its ask, and no new grant lands on it. It grants again
when the Regent says `ratify grants` (conventions §9) or approves `judge.py ratify --yes`, which `hook-hazard.py` asks
for as consent. `judge.py ratify` without `--yes` is the review: the rows as they stand.

Revoking needs nobody (`judge.py revoke <id>`): it only narrows, and it keeps a ratified store ratified. A shell inside
the session reaches that session's grants too.

## 6. What protects the stores

- `hook-acts-guard.py` denies a tool write to any `JD.md`, to `judge.json` and to a file the Regent named.
- `hook-hazard.py` denies a shell command that would write them: a redirect into one, or any command naming one that
  is not a reader (`cat`, `grep`, …), a `git` read or `add`/`commit`, or `judge.py` itself.
- The fingerprint catches the rest: a file store changed past the guards goes STALE.

These are behavioural limits for an agent with a shell, like QA's read-only contract (`library/maintaining.md`). They
stop an agent that forgets, and a refused act is one the Regent sees. A determined shell can still write `judge.json` or
a session's grants, or pipe a made-up event into `hook-verbs.py`, and nothing sees that: a session's store has no
fingerprint. No local check can stop it (conventions §5).

## 7. Facts relied on

| Fact | Consequence here |
|---|---|
| `UserPromptSubmit` carries the Regent's text; some surfaces prepend `<system-reminder>` blocks | `hook_wire.regent_text` reads only what no tag encloses, from a block's first opening to its last closing; verbs, cloud confirmations and grant lines all read through it, and `judge.grant_lines` also drops fenced blocks |
| A hook's environment has `CLAUDE_PLUGIN_DATA`, where session grants live; a shell's has only `CLAUDE_CODE_SESSION_ID` | `judge.shell_event` finds the session's file under `~/.claude/plugins/data/` |
| A subagent's report fires `UserPromptSubmit` too, with a `prompt` that opens `<agent-message from="…">` and every line of the report indented (seen live, 2026-11-06) | it is no message of the Regent's: it ends no pass, and what it holds confirms and grants nothing |
| How a paste reaches the prompt a hook receives | **not yet seen live**: `judge.grant_lines` reads nothing from a message holding a `<paste…` tag, so its exact form does not matter; a surface that passes a paste with no tag at all leaves its grant lines readable |
| `PreToolUse` runs before the permission component fills `AskUserQuestion` answers | answers present at `PreToolUse` came from the agent: denied |
| Where a surface puts the answers at `PostToolUse` | **not yet seen live**: read from `tool_input.answers`, then `tool_response.answers`, then a `"question"="answer"` text; when none arrives the hook names the typed line instead |
| A `PreToolUse` hook's silence approves nothing | a grant never overrides Claude Code's own permissions |

## 8. Next

The Judge as a session's lead for an autonomous developer (RGN-DV) is the next version: the Judge steering only
inside a charter the Regent ratified (projects, units, fuel), able to deny or stop, never to approve its own way past
a grant, the work still ending at the Regent's review packet.
