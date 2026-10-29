# The Judge — the Regent's grants

Decision record R15 (`REGENCY_CUSTOMIZATION.md`). Engine: `scripts/judge.py`. Hooks: `scripts/hook-hazard.py`
(checks), `scripts/hook-verbs.py` and `scripts/hook-judge.py` (record), `scripts/hook-acts-guard.py` (protects).
Playbook: `/regency:judge`.

## 1. The idea

A **grant** is a standing answer the Regent gives ahead of time to `hook-hazard.py`'s ask, for named places and
kinds of act. Each act is judged when it happens, against the grants in force then; nothing locks the session after
a destructive step, and a path outside the project (a scratch clone in a temp folder) is judged where it really is.

Rule zero holds: *the check is a lookup, not an inference*. The AA side of the Judge only interviews and proposes;
whether an act is covered is decided by `judge.covers()`, a script.

## 2. A grant

| Part | Rule |
|---|---|
| **how** | `delete`, `discard`, `history`, `layout`: the kinds `hook-hazard.py` asks about and a grant may cover |
| **where** | globs relative to the repository root, or absolute. `X/**` covers the folder `X` itself; `*` crosses folders; `**` is the whole repository and never reaches outside it; a relative glob holds no `..` |
| **scope** | where the grant lives (§3); the narrowest, `session`, when the Regent names none |
| **why** | required: a grant without a reason grants nothing |

Ids: `JD-S##` (session), `JD-R##` (repo), `JD-M##` (machine), `JD-P##` (a file the Regent names), numbered per store.

**Covered** means: every path the act names matches a glob of **one** grant of its kind. An act that names no path
(`git reset --hard`, `git rebase`, `git branch -D`) and a path no script can resolve (`"$d"`, a glob, a `cd` to an
unknown place) need `**`. A `cd` earlier in the chain moves where the later paths resolve.

**Never granted**, so they keep asking or denying whatever a grant says: installing system software, destructive SQL,
docker prunes and disk tools (data outside files), cloud writes (conventions §6), pack consent (T5) and a push to main
(`guard-push.py`). `edit` and `move` are not kinds: regency asks before neither, so there is nothing to grant.

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
   in any message length; a line inside a harness `<system-reminder>` never does. This way works on every surface.
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

Revoking needs nobody (`judge.py revoke <id>`): it only narrows, and it keeps a ratified store ratified.

## 6. What protects the stores

- `hook-acts-guard.py` denies a tool write to any `JD.md`, to `judge.json` and to a file the Regent named.
- `hook-hazard.py` denies a shell command that would write them: a redirect into one, or any command naming one that
  is not a reader (`cat`, `grep`, …), a `git` read or `add`/`commit`, or `judge.py` itself.
- The fingerprint catches the rest: a file store changed past the guards goes STALE.

These are behavioural limits for an agent with a shell, like QA's read-only contract (`library/maintaining.md`): a
determined shell can still write `judge.json` itself. The guards make that a refused act the Regent sees, never a
silent one.

## 7. Facts relied on

| Fact | Consequence here |
|---|---|
| `UserPromptSubmit` carries the Regent's text; some surfaces prepend `<system-reminder>` blocks | `hook_wire.regent_text` strips them before grant lines are read |
| `PreToolUse` runs before the permission component fills `AskUserQuestion` answers | answers present at `PreToolUse` came from the agent: denied |
| Where a surface puts the answers at `PostToolUse` | **not yet seen live**: read from `tool_input.answers`, then `tool_response.answers`, then a `"question"="answer"` text; when none arrives the hook names the typed line instead |
| A `PreToolUse` hook's silence approves nothing | a grant never overrides Claude Code's own permissions |

## 8. Next

The Judge as a session's lead for an autonomous developer (RGN-DV) is the next version: the Judge steering only
inside a charter the Regent ratified (projects, units, fuel), able to deny or stop, never to approve its own way past
a grant, the work still ending at the Regent's review packet.
