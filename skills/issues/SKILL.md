---
name: issues
description: "Regency issues: check the repository's issues against the project's own records. Give each a verdict (adopt, flatten, ignore), act on the tracker (close, publish), read one (status), comment (question), rewrite its description (revise) or measure it. Use for /regency:issues[:sub], 'check the issues', 'triage the issues', 'verifique as issues'."
argument-hint: "[check | adopt|flatten|ignore <n> | close <n> | publish <item> | status [n] | question|revise|measure <n>]"
---

# issues — the tracker against the project's records

> **Root.** This file is `skills/issues/SKILL.md`; the regency root is two directories above it. `scripts/…` and
> `library/…` paths are relative to that root. Doctrine: `library/issues.md`. Read `library/conventions.md` once per
> session.

Every verb is one function of `scripts/issues.py`. Bare `/regency:issues` is `check`.

| Group | Verb | Does | Writes |
|---|---|---|---|
| verdict | `adopt <n>` | the issue is work here, held by a ledger item | `issues.json`, the ledger |
| verdict | `flatten <n>` | the issue is lesser: one note line in the project's queue | `issues.json`, the note |
| verdict | `ignore <n>` | nothing is owed here | `issues.json` |
| tracker | `close <n>` | closes the issue, `completed` or `not-planned` | the tracker |
| tracker | `publish <item>` | a ledger item, a doubt or a finding becomes a new issue | the tracker |
| read | `status [n]` | one line per issue, or one issue whole | nothing |
| status | `question <n>` | adds one comment; changes nothing else | the tracker |
| status | `revise <n>` | replaces the description | the tracker |
| status | `measure <n>` | the issue as the intended change of `/regency:measure-changes` | nothing |

## Commands

```bash
python <regency-root>/scripts/issues.py check                                  # exit 1 while one is untriaged or broken
python <regency-root>/scripts/issues.py status [n]
python <regency-root>/scripts/issues.py measure <n>
python <regency-root>/scripts/issues.py adopt <n> --to <ledger id> --why "<reason>"
python <regency-root>/scripts/issues.py flatten <n> --to <path[#anchor]> --why "<reason>"
python <regency-root>/scripts/issues.py ignore <n> --why "<reason>"
python <regency-root>/scripts/issues.py close <n> [--reason completed|not-planned] [--yes]
python <regency-root>/scripts/issues.py publish --title "<title>" --body-file <file> [--label <l>] [--yes]
python <regency-root>/scripts/issues.py question <n> --body-file <file> [--yes]
python <regency-root>/scripts/issues.py revise <n> --body-file <file> | --fold --why "<reason>" [--yes]
```

The issues come from `gh`. Without it, list them with the session's GitHub tool, save the answer as it came and
pass `--json <file>`; a tracker write is then done by that tool, with the text the plan printed.

## Two gates

1. **A verdict is the Regent's.** Propose one per untriaged issue, with its reason in one line, in one pop-up
   (conventions §3); record only what the Regent answered. An issue the Regent's message already ruled on needs no
   pop-up. Never adopt in silence (conventions §10).
2. **A tracker write is published.** `close`, `publish`, `question` and `revise` print their plan first: the exact
   act and text. Show it, wait for the Regent's yes, then run the same line with `--yes`. A message of this pass that
   names the verb and the issue is that yes for the text shown. In a repository the Regent does not own (conventions
   §6), and in a headless run, no tracker write runs.

## Procedure

- **check** — run it; report its lines as they are. For each `UNTRIAGED`, read the issue, then gate 1. `BROKEN`,
  `ORPHAN`, `CLOSED`, `OPEN` and `MOVED` are named with what settles them (`library/issues.md` §3).
- **adopt** — add the ledger item first (`state: backlog`, `source`: the issue's URL), then record with `--to <id>`.
  The issue stays open until the work is accepted; then `close --reason completed`.
- **flatten** — write the note line where the project's queue holds such notes (`library/layouts.md`), citing the
  issue; record with `--to <that place>`. Two tracker acts finish it, each through gate 2: `revise --fold` and
  `close --reason not-planned`.
- **ignore** — record the reason. Leaving the issue open or closing it is the Regent's call; ask it in the same pop-up.
- **close** — `completed` when the work the issue asked for is accepted; `not-planned` otherwise.
- **publish** — draft from the project's issue form when it has one (`.github/ISSUE_TEMPLATE/`), in the form's own
  headings; point at the record, never copy it whole. After the yes, adopt the new issue against the item it came from.
- **status** — the script's lines; for one issue, read its comments too and add what is waiting on whom.
- **question** — one comment: a doubt, a finding or a measurement. It never edits, labels or closes.
- **revise** — the whole new description in a file; the reply shows what changes against the current one.
  `--fold` keeps the description as filed under one line.
- **measure** — run the script for the slice, then follow `skills/measure-changes/SKILL.md` in its `issue` mode. The
  result goes to the Regent; posting it on the issue is a `question`.

## Output

```text
Issues    <n> (<open> open) · adopted <a> · flattened <f> · ignored <i> · untriaged <u>
<one line per finding or per act: LEVEL #n what, and what settles it>
Tracker   <acts run, with their links | planned, waiting for yes | none>
Records   <files written>
```

Offer exactly one next command.
