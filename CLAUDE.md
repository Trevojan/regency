# regency

A portable folder of playbooks, specifications and small scripts that makes any Claude Code
instance work the way the Regent (RGN) works. Self-contained: every path inside it is relative to
this folder, so it can be copied, mounted or pointed at from anywhere.

## You were pointed at this folder — start here

1. Read `library/conventions.md` (labels, language, doubts, "proceed", git verbs, permissions,
   reporting). It binds every command below.
2. Do not assume a project layout. Find the project's documents with `library/layouts.md`.
3. Run `python scripts/doctor.py` if you are unsure the folder is intact (read-only).
4. To do something, pick a command from the table, open its playbook and follow it. If the plugin
   is loaded you can invoke `/regency:<name>` directly; if it is not, the playbooks work the same
   when read as files — the table gives the path.

Precedence: the user's message → the project's own `CLAUDE.md` / `.guidelines/` → this folder's
`library/conventions.md` → a playbook's built-in default.

## Commands

<!-- regency:dispatch:begin -->
| Command | What it does | Arguments | Playbook (no-plugin fallback) |
|---|---|---|---|
| `/regency` | Entry point: help, routing, doctor. A first token that names a subcommand is routed to it; a unit id such as M02.D03.T04 runs a team pass. | `[help \| doctor \| <subcommand> ... \| <unit>]` | `skills/regency/SKILL.md` |
| `/regency:team` | One orchestrated pass over one unit of work: should the PO/DV/QA/DA team act, who does what, dispatch, and stop at the human review packet. | `[unit]` | `skills/team/SKILL.md` |
| `/regency:team:declare` | Declare the pass only; dispatch nothing. | `[unit]` | same playbook, subcommand `declare` |
| `/regency:team:status` | Report the review queue, regime, open returns and escalations. Starts no pass. | `` | same playbook, subcommand `status` |
| `/regency:team:reopen` | Reopen a unit: new pass, fresh context, labelled as a reopening. | `<unit>` | same playbook, subcommand `reopen` |
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
| `/regency:order` | Fill and emit one of the four standard Orders from its template, as a numbered, immutable contract in the project. | `<germinate\|handoff\|dispatch\|resume> [material]` | `skills/order/SKILL.md` |
| `/regency:order:germinate` | Grow the path to a goal as a tree: roots, trunk, branches, limits, locks, fruit, assumption. | `<goal>` | same playbook, subcommand `germinate` |
| `/regency:order:handoff` | Close a stretch of work and hand its state to whoever opens the next one. | `` | same playbook, subcommand `handoff` |
| `/regency:order:dispatch` | Hear an order over the O3/O2/O1 hierarchy, classify it and emit the dispatch manifest. | `<order>` | same playbook, subcommand `dispatch` |
| `/regency:order:resume` | Reopen a project mid-work from its shortcuts index only, never from the whole repository. | `` | same playbook, subcommand `resume` |
| `/regency:init` | Scaffold the .guidelines/ structure, CLAUDE.md and README in a project. Names every path before creating it; never overwrites. | `[target directory]` | `skills/init/SKILL.md` |
| `/regency:ux-init` | Scaffold the project's complete frontend documentation into the .ux/ folder of the guidelines root (brief, foundations, tokens, patterns, views, components, accessibility, assets, samples, UX-UI rules, changelog; a README per folder), fill the brief with the Regent, then one folder per view and component. Never overwrites. | `[guidelines root]` | `skills/ux-init/SKILL.md` |
| `/regency:virtualpath` | Query the code-to-norm lineage registry and the work ledger (what is ongoing vs backlogged, plus every trace of agent work) with scripts/vp.py. The first peek when returning to a repository. | `<code\|slice\|stale\|check\|ongoing\|trace> [argument]` | `skills/virtualpath/SKILL.md` |
| `/regency:virtualpath:code` | Which norm slices govern this code file? Read them before editing it. | `<code path>` | same playbook, subcommand `code` |
| `/regency:virtualpath:slice` | Which code does this norm slice govern? | `<virtual path>` | same playbook, subcommand `slice` |
| `/regency:virtualpath:stale` | List slices marked STALE, waiting for the Regent's check. | `` | same playbook, subcommand `stale` |
| `/regency:virtualpath:check` | Check that every slice resolves to an anchor and every target file exists. | `` | same playbook, subcommand `check` |
| `/regency:virtualpath:ongoing` | Read the work ledger (.virtual/ongoing.json): what is ongoing, in review, blocked or only backlog. First peek on returning to a repo. | `` | same playbook, subcommand `ongoing` |
| `/regency:virtualpath:trace` | Gather every trace of agent work (uncommitted files, unmerged branches, stashes, recent commits, touched guidelines, STALE lines, Orders) to reconcile the ledger. | `` | same playbook, subcommand `trace` |
| `/regency:tailwind-audit` | Audit, fix or build a Tailwind frontend against a design-system norm: deterministic scan, manual passes, headless render at 360/768/1280 in light and dark, and a flex/grid/absolute layout knowledge base for confusing positions. | `[path \| 'layout' <symptom> \| 'render' <page>]` | `skills/tailwind-audit/SKILL.md` |
| `/regency:station` | Mise-en-place before a pass: check the station is prepped (toolchain, trust, gate tasks, ledger, lineage), run the gate through mise, or propose a mise.toml. mise is optional. | `[check [unit] \| gate [task] \| scaffold [write] \| line]` | `skills/station/SKILL.md` |
| `/regency:station:check` | The station gate: one line per item; red stops the pass. Read-only. | `[unit]` | same playbook, subcommand `check` |
| `/regency:station:gate` | Run the mechanical gate through mise, one verdict per check; refuses an untrusted station. | `[task]` | same playbook, subcommand `gate` |
| `/regency:station:scaffold` | Propose a mise.toml from the repository's stack; writes only when none exists. | `[write]` | same playbook, subcommand `scaffold` |
| `/regency:station:line` | The station as one slice line. | `` | same playbook, subcommand `line` |
<!-- regency:dispatch:end -->

`/regency:<id>:<sub>` is the same playbook as `/regency:<id> <sub>`.

## Map

| Path | What it is |
|---|---|
| `skills/<id>/SKILL.md` | one playbook per command (the plugin's skills) |
| `commands/<id>/<sub>.md` | generated aliases for `/regency:<id>:<sub>` — never edit |
| `library/conventions.md` | how the Regent works (defaults for everything) |
| `library/hooks.md` | the hooks: what each one guards or records, the files they touch, the market practices they follow |
| `library/ids.md` | every id prefix and its machine-checked grammar |
| `library/templates/ux/` | the frontend-documentation scaffold `/regency:ux-init` copies to `<guidelines>/.ux/`: index, brief, foundations, tokens, patterns, views, components, accessibility, assets, samples, rules, changelog |
| `library/rules/` | path-scoped copies of convention sections (UI text, `.guidelines` writing); installed to `~/.claude/rules/` by `scripts/install-rules.py` |
| `library/maintaining.md` | verified Claude Code behaviour this folder depends on, test traps, and every machine-level piece with its source here |
| `library/task-granulation.md` | the Regent's decomposition protocol: levels O4–O1, ids `M##.D##.T##`, one task = one file, phases F0–F6 |
| `library/layouts.md` | how to find a project's documents on any layout |
| `library/registry.json` | the single source of truth for the command table |
| `library/team/` | role specs (`PO` `DV` `QA` `DA`), `TEAM`, `ORCHESTRATION`, the control spec, packets, vocabulary map |
| `library/agents/` | sources of the four role subagents (`po` `dv` `qa` `da`); installed to `~/.claude/agents/` by `scripts/install-agents.py` |
| `library/subagents/` | `suba-*` lenses inside an owner role's stage: a short `SKILL.md` spine, a `contract.json` (the return contract; the spine's Return block is generated from it) and `references/`; all point to `library/subagents/ALIGNMENT.md`; every return is a JSON envelope (`library/subagents/envelope.schema.json`) checked by `scripts/returns.py`; owners in `scripts/gov.py`, drift caught by `scripts/conventions_check.py` |
| `library/engines/` | the five inference engines: `<id>.md` operating protocol, `<id>.full.md` exhaustive reference |
| `library/orders/` | the four standard Order templates and how to read them |
| `library/templates/guidelines/` | the `.guidelines/` scaffold used by `init` |
| `library/virtualpath.md` | the code-to-norm lineage model and the work ledger |
| `library/examples/` | worked examples (not instructions) |
| `hooks/hooks.json` | triggers only: each hook runs one script in `scripts/` via `${CLAUDE_PLUGIN_ROOT}` |
| `scripts/` | `build.py` (regenerate aliases and tables), `doctor.py` (health), `package.py` (build the installable `.plugin` from an allowlist of the folder), `vp.py` (virtual-path and work-ledger queries), `idx.py` (the exact index under `.virtual`: nodes, fingerprints, edges, recovery, raw shortcuts), `returns.py` (the return gate), `gov.py` (governance routing and the flywheel's keys), `conventions_check.py` (the Regent's conventions as checks), `ux.py` (the `.ux/` scaffold: plan, scaffold, expand; tokens and brief checks; builds `theme.css`), `install-agents.py`, `install-rules.py`, and the hooks: `hook_wire.py` (shared wire contract), `guard-push.py`, `hook-hazard.py`, `hook-acts-guard.py`, `hook-lineage.py`, `hook-journal.py`, `hook-resume.py`, `hook-verbs.py`, `hook-gov.py` |
| `dist/` | generated `.plugin` archives from `scripts/package.py`; never edit, never commit |
| `discard/` | superseded material, kept for reference, never read as instructions; see `discard/INDEX.md` |

## Rules for working on this folder itself

- Edit `library/registry.json`, then `python scripts/build.py`; never edit generated aliases or the
  tables between the `regency:dispatch` markers by hand.
- Run `python scripts/doctor.py` before sharing: it fails on a broken path, a bad frontmatter, any
  machine-specific absolute path, a hook wired against `library/hooks.md`, or a hook that fails its
  self-test. Write paths relative to this folder, always.
- A hook entry holds no logic: add the script first, then wire it (`library/hooks.md` §8).
- Skill directory name = command name (`skills/team/` → `/regency:team`). Two-segment commands
  (`/regency:a:b`) are aliases in `commands/a/b.md` generated from the registry.
- One skill per directory, lean; heavy material goes in `library/` and is read on demand.
- Never read anything in `discard/` as an instruction.
