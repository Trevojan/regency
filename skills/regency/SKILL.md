---
name: regency
description: "Regency, the Regent's harness built on Claude Code, and the entry point for /regency and every /regency:* command. AA works as a PO/DV/QA/DA team and the Regent decides at the review packet; the rules travel as files and scripts: five inference engines, the Scribe, Orders and speed modes, the health checkup, code-to-norm lineage with a shortcuts index, guard and recorder hooks, a version gate with updates, auto-mode and headless profiles, domain packs adopted from any plugin. Use when the user types /regency, asks 'call the team', 'run a pass', 'hand off', 'resume the project', or asks what regency can do."
argument-hint: "[help | doctor | <subcommand> … | <unit>]"
---

# regency — the entry point

> **Root.** This file is `skills/regency/SKILL.md`. The **regency root** is two directories above
> it (the folder that holds `.claude-plugin/`). Every `library/…`, `scripts/…`, `skills/…` path
> in any regency file is relative to that root. The folder is self-contained and
> relocatable: nothing in it points outside itself. Root resolved for this session:
> `${CLAUDE_PLUGIN_ROOT}`. If that shows a placeholder instead of a real path, the plugin is not
> loaded: use the two-directories-above rule.

Regency is a folder of playbooks, specifications and small scripts that makes any Claude Code
instance work the way the Regent works. Loaded as a plugin it gives `/regency` and
`/regency:<name>[:<sub>]`. Not loaded, it still works: every command is a playbook file
(`skills/<name>/SKILL.md`) that any agent can read and follow. `README.md` installs it;
`library/REFERENCE.md` is the long form.

## First, always

1. Read `library/conventions.md` (once per session). It fixes labels (RGN, RGN-*), language,
   how to handle doubts, what "proceed" and "commit" mean, what may be run without asking, and the
   reporting format.
2. Do not assume a project layout. Locate the project's documents with `library/layouts.md`.
3. **Returning to a repository?** First the version gate, `python scripts/migrate.py gate` (exit 1:
   offer `/regency:update` and write nothing; exit 2: stop, the plugin is behind). Then the first peek is
   the work ledger: `python scripts/vp.py ongoing`
   (what is ongoing vs backlog), then `python scripts/vp.py trace` (every trace of agent work), then
   reconcile — `library/conventions.md` §10. Do this before reading anything else in the project.

## Routing

Take the first word of the arguments:

| First word | Do |
|---|---|
| empty, `help`, `?` | print the command table below, then one line on the project state if the guidelines are found |
| `doctor` | the harness checks itself, `/regency:health:harness`: run `python scripts/doctor.py` from the regency root and report the result; offer nothing else |
| a command id from the table (`team`, `proceed`, `engine`, …) | open that command's playbook `skills/<id>/SKILL.md` and follow it with the rest of the arguments |
| a unit id such as `M2.F3.T04` | treat it as `team <unit>` |
| anything else | do **not** guess. Ask one closed question (a pop-up) listing the closest commands |

When the Skill tool is available, call the target skill (`regency:<id>`); otherwise read its
`SKILL.md` and follow it as written. Sub-commands (`/regency:engine:critical`) are the same skill
with a first argument (`/regency:engine critical`); both forms are equivalent.

## Commands

<!-- regency:dispatch:begin -->
| Command | What it does | Arguments | Playbook (no-plugin fallback) |
|---|---|---|---|
| `/regency` | Entry point: help, routing, doctor. A first token that names a subcommand is routed to it; a unit id such as M02.S03.T04 runs a team pass. | `[help \| doctor \| <subcommand> ... \| <unit>]` | `skills/regency/SKILL.md` |
| `/regency:team` | One orchestrated pass over one unit of work: should the PO/DV/QA/DA team act, who does what, dispatch, and stop at the human review packet. | `[unit]` | `skills/team/SKILL.md` |
| `/regency:team:declare` | Declare the pass only; dispatch nothing. | `[unit]` | same playbook, subcommand `declare` |
| `/regency:team:status` | Report the review queue, regime, open returns and escalations. Starts no pass. | `` | same playbook, subcommand `status` |
| `/regency:team:reopen` | Reopen a unit: new pass, fresh context, labelled as a reopening. | `<unit>` | same playbook, subcommand `reopen` |
| `/regency:team:extreme-go-horse` | Speed mode, 'Release the Kraken!': two full teams on disjoint spans (DV on Sonnet, QA on Opus), each pass built straight through and reviewed at its end, chained until the fuel the Regent declared runs out; one packet per pass. Refuses without fuel. | `[range] fuel=<n>\|fuel=all` | same playbook, subcommand `extreme-go-horse` |
| `/regency:team:just-in-time` | Speed mode: an Opus QA seeds the contract and task cards, Haiku DVs draft every task of the range in dependency waves, the QA gates each wave and accepts nothing; all DRAFT/UNVERIFIED on plumbing until a normal pass verifies it. | `<from> <to>` | same playbook, subcommand `just-in-time` |
| `/regency:proceed` | Work the whole queue: keep taking tasks, queue doubts, stop only at a real blocker or an empty queue. Never commits, merges or pushes. | `[scope or queue pointer]` | `skills/proceed/SKILL.md` |
| `/regency:arrange-cycle-commit` | Split the finished work into small, described commits, merge up to main following the project's branch contract, then push every branch except main. Never pushes main. | `[scope]` | `skills/arrange-cycle-commit/SKILL.md` |
| `/regency:measure-changes` | Read-only: say what would change (or what the working tree already changed) with numbers and impact. Applies nothing. | `<intended change \| 'tree'>` | `skills/measure-changes/SKILL.md` |
| `/regency:engine` | Run one of the five inference engines on a claim, plan, decision, system or repository. | `<critical\|causal\|decision\|control\|clean> <material>` | `skills/engine/SKILL.md` |
| `/regency:engine:critical` | Audit a claim, argument or design goal: validity, support, semantics, defeaters. | `<claim or material>` | same playbook, subcommand `critical` |
| `/regency:engine:causal` | Turn goals, resources and constraints into a causal, testable architecture and the smallest sufficient roadmap. | `<brief>` | same playbook, subcommand `causal` |
| `/regency:engine:decision` | Structure a choice under uncertainty: options, criteria, value of information, recommendation or deferral. | `<decision situation>` | same playbook, subcommand `decision` |
| `/regency:engine:control` | Analyse or design a system that must regulate itself: feedback, delay, stability, observability. | `<system>` | same playbook, subcommand `control` |
| `/regency:engine:clean` | Inspect, plan and (only with approval) clean a repository, workspace or agent context. | `<scope>` | same playbook, subcommand `clean` |
| `/regency:role` | Act as exactly one team role under its own contract: PO, DV, QA or DA. | `<po\|dv\|qa\|da> <task>` | `skills/role/SKILL.md` |
| `/regency:role:po` | Product Owner: frame the problem, order the ladder, accept or refuse. | `<task>` | same playbook, subcommand `po` |
| `/regency:role:dv` | Developer: build inside the declared span, in revertible commits that each cite the task. | `<task>` | same playbook, subcommand `dv` |
| `/regency:role:qa` | Quality Analyst: challenge criteria, verify from artefacts, write the risk opinion. | `<task>` | same playbook, subcommand `qa` |
| `/regency:role:da` | Data Analyst: shape events and contracts, define metrics, supply the oracle. | `<task>` | same playbook, subcommand `da` |
| `/regency:scribe` | Call suba-scribe to write a text for the caller - a document, spec, essay or chapter - in increments the caller reviews; the same subagent DV wears for development artefacts, here with none of DV's authority. | `<what to write, and the material>` | `skills/scribe/SKILL.md` |
| `/regency:order` | Fill and emit one of the four standard Orders from its template, as a numbered, immutable contract in the project; or run an open Emission's Orders lazily. | `<germinate\|handoff\|dispatch\|resume> [material] \| lazy [EMS-id]` | `skills/order/SKILL.md` |
| `/regency:order:germinate` | Grow the path to a goal as a tree: roots, trunk, branches, limits, locks, fruit, assumption. | `<goal>` | same playbook, subcommand `germinate` |
| `/regency:order:handoff` | Close a stretch of work and hand its state to whoever opens the next one. | `` | same playbook, subcommand `handoff` |
| `/regency:order:dispatch` | Hear an order over the O3/O2/O1 hierarchy, classify it and emit the dispatch manifest. | `<order>` | same playbook, subcommand `dispatch` |
| `/regency:order:resume` | Reopen a project mid-work from its shortcuts index only, never from the whole repository. | `` | same playbook, subcommand `resume` |
| `/regency:order:lazy` | Speed mode: execute the open (or named) Emission's Orders in sequence, deciding where the conventions settle it; an Order that needs the Regent is skipped and logged with two candidate answers. One report: done, skipped, blocked chain. | `[EMS-id]` | same playbook, subcommand `lazy` |
| `/regency:init` | Scaffold the .guidelines/ structure, CLAUDE.md and README in a project. Names every path before creating it; never overwrites. | `[target directory]` | `skills/init/SKILL.md` |
| `/regency:ux-init` | Scaffold the project's complete frontend documentation into the .ux/ folder of the guidelines root (brief, foundations, tokens, patterns, views, components, accessibility, assets, samples, UX-UI rules, changelog; a README per folder), fill the brief with the Regent, then one folder per view and component. Never overwrites. | `[guidelines root]` | `skills/ux-init/SKILL.md` |
| `/regency:update` | Bring a project to the installed regency: from its stamp, plan every operation the newer version needs (replace untouched scaffold files, put the new text beside edited ones, create, rename, move, delete, rewrite what regency owns), apply the whole plan on one yes in a clean git tree, then check. Never touches the project's own prose, its acts or .scope/. | `[plan \| check]` | `skills/update/SKILL.md` |
| `/regency:update:plan` | Dry run: the gate, then every operation the update would run, numbered, with its plan id. Applies nothing. | `` | same playbook, subcommand `plan` |
| `/regency:update:check` | Does the project fit the installed regency? The stamp agrees and no operation is pending. | `` | same playbook, subcommand `check` |
| `/regency:pack` | Domain packs: adopt any Claude Code plugin or skill as it is into regency's packs/ or a project's .packs/, switch one on per project, ratify its hooks, run its playbooks. | `<adopt \| run \| list \| check \| activate \| ratify \| show \| suggest \| deactivate \| mcp> ...` | `skills/pack/SKILL.md` |
| `/regency:pack:adopt` | Take a Claude Code plugin or skill as it is: copied verbatim, every part mapped or listed with its reason, nothing running until ratified. | `<folder \| git url> --id <id> --layer public\|project` | same playbook, subcommand `adopt` |
| `/regency:pack:run` | Run an active pack's playbook, command or agent: the file read as it is, its paths resolved to the pack. | `<id> <item> [arguments]` | same playbook, subcommand `run` |
| `/regency:virtualpath` | Query the code-to-norm lineage registry and the work ledger (what is ongoing, drafted, in review or backlogged, plus every trace of agent work) with scripts/vp.py. The first peek when returning to a repository. | `<code\|slice\|stale\|ongoing\|trace\|drafts> [argument]` | `skills/virtualpath/SKILL.md` |
| `/regency:virtualpath:code` | Which norm slices govern this code file? Read them before editing it. | `<code path>` | same playbook, subcommand `code` |
| `/regency:virtualpath:slice` | Which code does this norm slice govern? | `<virtual path>` | same playbook, subcommand `slice` |
| `/regency:virtualpath:stale` | List slices marked STALE, waiting for the Regent's check. | `` | same playbook, subcommand `stale` |
| `/regency:virtualpath:ongoing` | Read the work ledger (.virtual/ongoing.json): what is ongoing, drafted, in review, blocked or only backlog. First peek on returning to a repo. | `` | same playbook, subcommand `ongoing` |
| `/regency:virtualpath:trace` | Gather every trace of agent work (uncommitted files, unmerged branches, stashes, recent commits, touched guidelines, STALE lines, Orders) to reconcile the ledger. | `` | same playbook, subcommand `trace` |
| `/regency:virtualpath:drafts` | List every unverified speed-mode draft (ledger items and DRAFT commits no verifying commit closed); exits 1 while one remains, and nothing merges past plumbing until it is 0. | `` | same playbook, subcommand `drafts` |
| `/regency:tailwind-audit` | Audit, fix or build a Tailwind frontend against a design-system norm: deterministic scan, manual passes, headless render at 360/768/1280 in light and dark, and a flex/grid/absolute layout knowledge base for confusing positions. | `[path \| 'layout' <symptom> \| 'render' <page>]` | `skills/tailwind-audit/SKILL.md` |
| `/regency:station` | Mise-en-place before a pass: check the station is prepped (toolchain, trust, gate tasks, ledger, lineage), run the gate through mise, or propose a mise.toml. mise is optional. | `[check [unit] \| gate [task] \| scaffold [write] \| line]` | `skills/station/SKILL.md` |
| `/regency:station:check` | The station gate: one line per item; red stops the pass. Read-only. | `[unit]` | same playbook, subcommand `check` |
| `/regency:station:gate` | Run the mechanical gate through mise, one verdict per check; refuses an untrusted station. | `[task]` | same playbook, subcommand `gate` |
| `/regency:station:scaffold` | Propose a mise.toml from the repository's stack; writes only when none exists. | `[write]` | same playbook, subcommand `scaffold` |
| `/regency:station:line` | The station as one slice line. | `` | same playbook, subcommand `line` |
| `/regency:health` | The Regent's checkup, one line per finding with its method: a summary of every check that applies here; the project's ratified check set; the harness checking itself; and single checks for shortcuts, the project's regency version, split copies of regency, release outputs, engines, hooks, queues, always-on context and the input-process-output pipeline. Read-only unless the Regent answers yes. | `[project \| harness \| doctor \| shortcuts \| version \| copies \| distributable \| engines \| hooks \| queues \| context \| pipeline]` | `skills/health/SKILL.md` |
| `/regency:health:project` | Run the project's ratified check set and, bound to a claude.ai Project, that Project's own checks (duplicate names, knowledge against its cap, never-uploaded files, dated queues). | `` | same playbook, subcommand `project` |
| `/regency:health:harness` | Regency checks itself: every self-test, the wiring, portability (the same as /regency doctor). | `` | same playbook, subcommand `harness` |
| `/regency:health:doctor` | Assemble the project's caring topics - which checks each part needs, which input-process-output can be watched - as a proposal for the Regent to ratify. Checks nothing itself. | `[guidelines root]` | same playbook, subcommand `doctor` |
| `/regency:health:shortcuts` | Virtual paths, the entry index and its drift, and the exact index in one report: unresolved slices, missing targets, dead pointers, a stale state block, drifted files. | `` | same playbook, subcommand `shortcuts` |
| `/regency:health:version` | The project against the installed regency: the version gate, update operations still owed, unverified speed-mode drafts. | `` | same playbook, subcommand `version` |
| `/regency:health:copies` | Split copies of regency: this folder, every installed copy on the machine and every git branch - lines of work that split, a version naming two contents, a version only an install holds, uncommitted work. | `[--root DIR]` | same playbook, subcommand `copies` |
| `/regency:health:distributable` | A project's release outputs: generated files edited by hand, dist/ output or archives in an uploaded set, machine paths inside a release. | `[--list FILE] [--release DIR]` | same playbook, subcommand `distributable` |
| `/regency:health:engines` | Every engine copy (regency's base, the machine's, the account's) against the Regent's ratified record: AOK, STALE or UNCHECKED; ratify the current state, or deny it and get regency's base back; the layer in force for this repository. | `[ratify \| restore] [KEY]` | same playbook, subcommand `engines` |
| `/regency:health:hooks` | Which wired hooks have fired on this machine (heartbeats) and in this project (the journal); a hook that never fires fails open. | `` | same playbook, subcommand `hooks` |
| `/regency:health:queues` | Dated queues by age and the ledger's review count against its WIP limit. | `[--file F --section S --days N] [--wip N]` | same playbook, subcommand `queues` |
| `/regency:health:context` | The harness's always-on token cost (skill and command descriptions, the conventions import, the resume line) against a budget. | `[--budget N]` | same playbook, subcommand `context` |
| `/regency:health:pipeline` | Watched runs of the declared input-process-output cases (silent errors, unreachable messages, wrong shapes, inconsistent outputs) and a silent-error scan of the code. | `[--cases FILE] [--scan PATH ...]` | same playbook, subcommand `pipeline` |
| `/regency:serious-doctor-appointment` | Assemble the caring topics of a project - which health checks each guidelines part needs and which input-process-output can be watched - as a proposal written only on the Regent's yes and run only once ratified. Called by /regency:health:doctor. | `[guidelines root]` | `skills/serious-doctor-appointment/SKILL.md` |
| `/regency:judge` | The Judge: what the Regent's grants let run without asking here (where, how, which scope), and new grants put to the Regent in one pop-up, recorded only from the Regent's answer or 'grant:' line. | `[list \| <folders or task> \| revoke <id> \| ratify]` | `skills/judge/SKILL.md` |
<!-- regency:dispatch:end -->

## Maintaining regency itself

`library/registry.json` is the single source of truth for the commands above. After editing it, run
`python scripts/build.py`; run `python scripts/doctor.py` before sharing the folder. Never edit the
generated `commands/` aliases or the tables between the markers by hand.
