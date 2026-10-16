---
name: station
description: "Regency station: mise-en-place before a pass. Check that the station is prepped before the first ticket (toolchain pinned and installed, mise config trusted by the Regent, gate declared as tasks, ledger entry for the unit, lineage resolving, no STALE slice), run the mechanical gate through mise with one verdict per check, or propose a mise.toml from the repository's stack. mise (mise.jdx.dev) is optional: without it the regency items still run. Use for /regency:station[:check|gate|scaffold|line], before a team pass, or when asked 'is the station ready', 'prep the station', 'run the gate', 'set up mise'."
argument-hint: "[check [unit] | gate [task] | scaffold [write] | line]"
---

# station — prep before service

> **Root.** This file is `skills/station/SKILL.md`; the regency root is two directories above it.
> `scripts/…` and `library/…` paths are relative to that root. Read `library/conventions.md` once per
> session. The idea behind it is the essay *Mise-en-place in Regency*; this file is only the procedure.

A kitchen splits its day into prep and service. A pass is service. This command checks the prep, so no
pass opens on a station that is not ready, and it runs the gate the same way on every machine.

Two layers, one script, `scripts/station.py`:

| Layer | Items | Needs |
|---|---|---|
| discipline (regency) | `ledger`, `lineage`, `stale`, `f0` | nothing beyond regency |
| instrument (mise) | `mise`, `config`, `trust`, `tools`, `lock`, `tasks`, `gate-task` | mise on PATH; optional |

## Commands

```bash
python <regency-root>/scripts/station.py check --unit M03.D02.T04   # the station gate; read-only
python <regency-root>/scripts/station.py gate [--task gate] [--log FILE]
python <regency-root>/scripts/station.py scaffold            # print a proposed mise.toml
python <regency-root>/scripts/station.py scaffold --write    # write it, only when no mise config exists
python <regency-root>/scripts/station.py line                # the station as one slice line
python <regency-root>/scripts/station.py --selftest
```

Add `--repo DIR` when the current directory is not inside the project. `check --json` gives the same
items as JSON.

## Reading `check`

One line per item: `OK`, `WARN`, `FAIL`, `SKIP` or `MANUAL`, then `station: green | amber | red`.

| Verdict | Meaning | The pass |
|---|---|---|
| green | prepped | may open |
| amber | prepped with gaps (no lock, floating pin, STALE lines, no gate task) | may open; each WARN goes into the declaration's `defects` |
| red | a FAIL | does not open: `HOLD`, routed to whoever owns the item |

Who owns a FAIL:

| Item | Owner | What releases it |
|---|---|---|
| `trust` | Regent | the Regent reviews the config and runs `mise trust` |
| `tools` | Regent | the Regent runs `mise install` |
| `tasks` | DV, by a returned task | a config that `mise tasks validate` accepts |
| `ledger` | PO | the unit listed in `.shortcuts/.virtual/ongoing.json` |
| `lineage` | Regent | `vp.py check` clean (never "fix" the manifest unasked) |

`MANUAL station.f0` is the part no script can see: norm ratified, criteria challenged, oracle supplied.
Read it from the Pass Declaration (team check 4, stages 2–3); do not restate it.

## Where it plugs into a team pass

1. **Step 0, after `vp.py ongoing` and `vp.py trace`:** run `station.py check --unit <unit>`. Paste the
   FAIL and WARN lines into `defects`. A red station decides the pass as `HOLD`, by its first FAIL.
2. **Step 5, the gate:** when `check` reports `gate-task OK`, run `station.py gate --log <new file>` instead
   of the checks by hand. Every dependency of the gate task is one check with its own verdict; a red gate
   returns the log to DV and consumes neither QA nor the human. Without a gate task, the parts run by hand
   and are declared `manual`, as before.
3. **The review packet, item 2 (the gate result):** the gate log. Its header records the mise version and
   the toolchain, so QA's evidence names what it ran on.

## Rules

- **Trust is ratification.** An agent never runs `mise trust`, `mise trust --all` or `mise untrust`.
  `mise run` trusts a config by itself, so `gate` reads `mise trust --show` first and refuses (exit 3) an
  untrusted station. Normal trust is bound to the path, not the contents. If the Regent wants trust
  bound to the contents, that is mise's paranoid mode, the Regent's setting to turn on.
- **No silent installs.** Every mise call runs with `MISE_TASK_RUN_AUTO_INSTALL=false` and without
  `MISE_YES`. An agent never runs `mise install`, `mise use` or `mise lock`: those change the toolchain,
  and `library/conventions.md` §5 asks first.
- **mise is optional.** Without mise every mise item is `SKIP` and regency works as before. Never make a
  regency script depend on mise.
- **The config is a norm.** `scaffold` prints a proposal. `scaffold --write` only when the Regent asked,
  and never over an existing config. After it: the Regent reviews, trusts, installs, locks.
- **A gate log is an act.** `gate --log` refuses an existing file; name a new one.

## Exit codes

| Command | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `check` | green or amber | red | — | — |
| `gate` | green | red | cannot run (no mise, no config, no gate task, log exists) | refused: untrusted |
| `scaffold` | printed or written | a config already exists (`--write`) | — | — |
