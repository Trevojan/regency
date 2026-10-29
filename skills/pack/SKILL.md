---
name: pack
description: "Regency packs: what regency becomes in one domain. Adopt any Claude Code plugin or skill as it is, switch it on per project, ratify its hooks, run its playbooks. Use for /regency:pack[:adopt|run], 'adopt this plugin', 'which packs are active'."
argument-hint: "<adopt | run | list | check | activate | ratify | show | suggest | deactivate | mcp> ..."
---

# pack — regency, specialised

> **Root.** This file is `skills/pack/SKILL.md`; the regency root is two directories above it. `scripts/…` and
> `library/…` paths are relative to that root. Doctrine: `library/packs.md`. Read `library/conventions.md` once per
> session.

A pack is what regency becomes in one domain: a folder with `pack.json` and its files, adopted from any Claude Code
plugin or skill as it is, or written native. It lives in one of two layers:

| Layer | Folder | Travels with | Rule |
|---|---|---|---|
| public | `<regency>/packs/<id>/` | regency's repository | an open-source license regency may redistribute |
| project | `<guidelines>/.packs/<id>/` | the project's repository | any license; a project pack shadows a public one of the same id |

Claude Code loads plugins per install, never per project, so regency reads packs itself: this playbook opens a pack's
files, and `scripts/hook-packs.py` runs a pack's hooks only where the pack is active and the Regent ratified them.

## Commands

```bash
python <regency-root>/scripts/packs.py list
python <regency-root>/scripts/packs.py adopt <folder | git url> --id <id> --layer public|project [--when "*.ext,..."]
python <regency-root>/scripts/packs.py adopt ... --yes        # writes; without --yes it only prints the plan
python <regency-root>/scripts/packs.py check
python <regency-root>/scripts/packs.py show <id> [<item key>]
python <regency-root>/scripts/packs.py suggest
python <regency-root>/scripts/packs.py activate <id> [--yes]
python <regency-root>/scripts/packs.py deactivate <id> [--yes]
python <regency-root>/scripts/packs.py ratify <id> <item key | hooks | all>        # the review; records nothing
python <regency-root>/scripts/packs.py mcp <id> [--write --yes]
```

Add `--repo DIR` when the current directory is not inside the project.

## adopt

1. Run the plan without `--yes` and show it to the Regent whole: the source, its license, every item by kind, every
   part **not adopted** with its reason, the requirements (node, python, bash…) and where the pack lands.
2. The layer is the Regent's choice. Public publishes the pack with regency; `adopt` refuses a source with no
   open-source license there. Material the Regent keeps private, or that another project owns (Glyph's, by R2.2),
   goes to the project layer.
3. On the Regent's yes, run it with `--yes`. Nothing runs yet: every item is a proposal.
4. `--when` takes the file globs that suggest the pack for a project (`packs.py suggest` reads them).

## activate · ratify

- `activate` switches a pack on in this project (`<guidelines>/.packs/active.json`). Its playbooks become runnable.
  Its hooks do not run.
- `ratify` without `--yes` is the **review**: each hook's event, matcher and exact command. Show it to the Regent.
- `ratify ... --yes` is the Regent's consent. The hazard hook asks the Regent on that call: approve only when the
  Regent said so for this pack after reading the review. **Never ratify on your own judgement** (T5: no role accepts
  its own work, and the agent that adopted a pack is the last one to clear its code).
- Any later change to any file of the pack makes its ratified hooks STALE: they stop until ratified again.

## run

`/regency:pack run <id> <item> [arguments]` (or `/regency:pack:run`):

1. `packs.py show <id> <item>`. Refuse when the pack is not active here; offer `activate`.
2. A `playbook:` or `command:` item: read the file it names and follow it with the given arguments, as if the
   Regent had invoked it. Its relative paths resolve against its own folder; replace `${CLAUDE_PLUGIN_ROOT}` with
   the root `show` prints. Its requirements (`show` names them) must be on PATH; say which is missing instead of
   improvising.
3. An `agent:` item: dispatch a subagent whose prompt is the agent file's body, then the task.
4. Say `proposal` when the item is not ratified: the Regent's invocation is consent to run it this once.

## What a pack may and may not do

- A pack adds; it never overrides regency's guards. Its hooks run after regency's own, through the dispatcher, which
  passes on deny and ask, and drops allow and a rewritten tool input.
- Precedence: the Regent's message → the project's own guidelines → active packs → regency's conventions → a
  playbook's default.
- Parts a pack cannot bring in this version (LSP servers, output styles, themes, monitors, settings, `bin/` on PATH,
  prompt and http hooks, Stop hooks) are listed in its `pack.json` under `unsupported`, never dropped silently.

## Report

One line per pack touched: `pack <id> · <layer> · <n> item(s) · active | inactive · hooks running <k>/<m>`, then the
next act (`activate`, `ratify`, `run`) the Regent may choose.
