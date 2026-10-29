---
name: judge
description: "Regency Judge (JD): the Regent's grants - where and how a hazardous act (delete, discard, history, layout) may run without asking, for this session, the repository, this machine or a file the Regent names. Lists them, puts new ones to the Regent in one pop-up, revokes, ratifies on the Regent's word. Use for /regency:judge, 'manage this folder', 'what may run here', 'stop asking me about X'."
argument-hint: "[list | <folders or task> | revoke <id> | ratify]"
---

# judge — the Regent's grants

> **Root.** This file is `skills/judge/SKILL.md`; the regency root is two directories above it. `scripts/…` and
> `library/…` paths are relative to that root. Doctrine: `library/judge.md`. Read `library/conventions.md` once per
> session.

`scripts/hook-hazard.py` asks the Regent before a hazardous local act. A **grant** answers that ask ahead of time:

| Part | Values |
|---|---|
| how | `delete`, `discard`, `history`, `layout` |
| where | globs relative to the repository root (`Herança/**` covers the folder too; `**` is the whole repository), or absolute |
| scope | `session` · `repo` (`<guidelines>/JD.md`, travels with the repository) · `machine` (`~/.claude/regency/JD.md`) · a `.md` path the Regent names |
| why | required |

The Judge proposes; **the Regent grants**. A grant is recorded only by regency's hooks, from the Regent's answer to the
Judge's pop-up or from a line the Regent sends: `grant: <how>[,<how>] <where>... [for <scope>] -- <why>`.

## Commands

```bash
python <regency-root>/scripts/judge.py list                 # file grants in force here; STALE stores named
python <regency-root>/scripts/judge.py check <kind> <path>  # which grant covers an act, or the line to propose
python <regency-root>/scripts/judge.py revoke <id>          # narrowing needs nobody
python <regency-root>/scripts/judge.py ratify               # the review of each STALE store; records nothing
```

Add `--repo DIR` when the current directory is not inside the project.

## list (bare `/regency:judge`)

Run `list` and report one line per grant, then each STALE store with what it would grant once ratified.

## A place or a task (`/regency:judge Herança`, "manage Herança", "stop asking me about build/")

1. `list`: start from what is already granted.
2. Map the place: the folders the Regent named (`ls`, Glob) and the acts the work needs. Ask yourself which kinds
   the task truly needs; edits and moves need no grant (regency asks before neither).
3. Propose the **narrowest** grants: one per place and kind group, never `**` unless the Regent asked for the whole
   repository. Put them in **one** `AskUserQuestion` call, up to four questions, each exactly:
   - `header`: `JD grant`
   - `question`: ``Grant `<how> <where>... -- <why>`?`` with the grant in **one** backtick span
   - `options`: `Session`, `Repo`, `This machine`, `No`; say that "Other" takes a `.md` path for a grant file
   - never fill `answers`: the hook denies a Judge question that arrives answered.
4. `scripts/hook-judge.py` records each scope the Regent picked and answers `grant JD-… recorded`. When it says no
   answers reached it, or records nothing the Regent chose, give the Regent the exact lines to send, one per grant:
   `grant: <how> <where> for <scope> -- <why>`.
5. Report the grants recorded.

## An ask that says "No grant covers it"

The ask carries the Judge's proposal line. A one-off yes to the prompt is enough for one act. When the Regent wants
it standing, narrow the proposal, add the why, and run step 3.

## revoke · ratify

- `revoke <id>` removes one grant. It is narrowing, so it needs nobody; report what left.
- A store that changed outside the hooks (a pull, the Regent's hand edit) is **STALE** and grants nothing. Run
  `ratify` without `--yes` and show the Regent the rows. Only the Regent ratifies: by saying `ratify grants`, or by
  approving `judge.py ratify --yes`, which the hazard hook asks for. **Never ratify on your own judgement** (T5).

## Never

- Write or edit a `JD.md`, `judge.json` or a session's grants, by tool or by shell. The hooks deny it; a store
  changed any other way goes STALE.
- Propose a grant for installs, destructive SQL, docker prunes, disk tools, cloud writes, pack consent or a push to
  main: they are never granted.
- Read a grant into the Regent's silence, or widen a grant the Regent narrowed.

## Report

One line per grant: `JD-<id> · <how> · <where> · <scope> · <why>`; then STALE stores; then the next act.
