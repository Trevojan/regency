---
name: health
description: "Regency health, the Regent's checkup: one line per finding with its method. Bare: a summary of every check that applies here. project: the ratified check set, plus a claude.ai Project's own checks. harness: regency checks itself. doctor: assemble what to check. Single checks: shortcuts, version, copies, distributable, engines, hooks, queues, context, pipeline. Use for /regency:health[:sub], 'health check', 'checkup'."
argument-hint: "[project | harness | doctor | shortcuts | version | copies | distributable | engines [ratify|restore] | hooks | queues | context | pipeline]"
---

# health — the checkup

> **Root.** This file is `skills/health/SKILL.md`; the regency root is two directories above it.
> `scripts/…` and `library/…` paths are relative to that root. Read `library/conventions.md` once per
> session; the doctrine is `library/health.md`.

Read-only. Nothing here writes into a project or a record unless the Regent answered yes in a pop-up;
`health.py` refuses every writing mode without `--yes`.

## Routing

| Argument | Run | Report |
|---|---|---|
| empty | `python <root>/scripts/health.py all` | its lines as they come |
| `project` | `health.py project`, then the **Project surface** below when this session is bound to a claude.ai Project | every finding, FAIL first |
| `harness` | `health.py harness` (the same as `/regency doctor`) | the doctor's FAIL lines and its summary |
| `doctor` | open `skills/serious-doctor-appointment/SKILL.md` and follow it | the proposal, then the Regent's answer |
| `shortcuts` · `version` · `distributable` · `hooks` · `queues` · `context` · `pipeline` | `health.py <check>` with the arguments below | its lines |
| `copies` | `health.py copies` from the Regent's regency folder (`--root DIR` names another copy); run from an installed copy, its branches are UNCHECKED | every WARN: the Regent decides which line of work stays |
| `engines` | `health.py engines` with the surfaces below; then **Ratify or deny** | AOK, STALE, UNCHECKED lines |

Every run takes `--repo DIR` (default: the nearest `.git` above the working directory).

## The Project surface (a session bound to a claude.ai Project)

The Project's own health check, R11.1. Report each with its number.

1. **Names.** Call the Projects tool `project_info`; write its `docs` and `files` to a file in the
   scratchpad (`{"docs": [...], "files": [...]}`), then `health.py names --list <file>`.
2. **Knowledge.** `health.py size --used <knowledge_size> --cap <max_knowledge_size>` from the same answer.
3. **Never uploaded.** `health.py distributable --list <file>`.
4. **Dated queues.** For a queue the Project's instructions name (for example "To apply" in
   `claude/BOOK_TO_REGENCY.md`): `project_read` it, save it to the scratchpad, then
   `health.py queues --file <saved> --section "To apply" --days 7`.

Name the surface in the first line: *Project "<name>" · <n> files*. Locally the same checks run on the
upload set: `health.py names --upload-set` and `health.py size --root .`.

## Surfaces for `engines`

| Session | Pass |
|---|---|
| local (Claude Code on the Regent's machine) | nothing: the machine is `~/.claude/skills`, the record `~/.claude/regency/engines.json`; the account reads UNCHECKED here |
| cloud or claude.ai, bridge linked | `--account <the folder this session's skill listing shows the account skills in>`; stage the machine's `~/.claude/skills` and `~/.claude/regency/engines.json` through the bridge and pass `--machine` and `--record` |
| cloud or claude.ai, no bridge | `--account <that folder> --machine none`; the machine copies and the record read UNCHECKED — say so, never call them clean |

### Ratify or deny

For each STALE copy, one pop-up: *ratify its current state* / *deny it: regency's base comes back*.

- ratify → `health.py engines ratify --yes <key>` (the key as the line names it, `machine:<name>` or `account:<name>`);
- deny on the machine → `health.py engines restore --yes machine:<name>` (your text moves aside first);
- deny on the account → regency cannot write there: say which file to put back (`library/engines/<id>.md`
  as that skill's `SKILL.md`), or that the skill can be removed;
- a project that declares its engines (`.sources/ENGINES.md`) and no choice yet → pop-up *yours* /
  *the project's*, then `health.py engines ratify --yes repo --follow regent|project`.

Never ratify or restore without that answer. A cloud session writes the record through the bridge.

## Arguments the single checks take

```bash
health.py queues --file .guidelines/.plan/BACKLOG.md --section "To apply" --days 7 --wip 3
health.py distributable --list listing.json --release release/
health.py context --budget 3000
health.py pipeline [--cases FILE] [--scan src app] [--no-runs | --no-scan]
```

A project's own arguments live in its check set; `/regency:health:project` passes them.

## Reporting

One line per finding, FAIL first, as the script prints it; then one line: done / left / blocked with a
percentage and a fraction (conventions §8). End with the one next step the findings ask for — usually a
ratification, or `/regency:health:doctor` when the project has no check set yet.
