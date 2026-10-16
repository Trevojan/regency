# regency

The Regent's portable toolkit for Claude Code: orchestrated team passes (PO / DV / QA / DA), the
verbs *proceed*, *commit-and-merge* and *measure-changes*, five inference engines, the Scribe
sub-agent, the four standard Orders, a `.guidelines/` scaffold, a code-to-norm lineage tool, and the
hooks that hold the conventions at the moment of every tool call.

**Portable by construction.** The folder is self-contained and relocatable: every path in it is
relative to the folder itself, the scripts use only the Python standard library, and nothing points at
a machine, a user or a project. Copy it, mount it, clone it, or point any Claude Code instance at it.

## Use it — pick one way

Replace `<path>` with where this folder lives.

| # | Way | When | How |
|---|---|---|---|
| 1 | **One session** | try it, or a machine you do not own | `claude --plugin-dir <path>` |
| 2 | **Installed** (user scope) | your own machine; terminal, desktop app local sessions and VS Code share it | `claude plugin marketplace add <path>` then `claude plugin install regency@regency` |
| 3 | **Skills-directory plugin** | auto-loads every session, no marketplace | copy or link this folder to `~/.claude/skills/regency/` (a managed allowlist may need `{"source":"skills-dir"}`) |
| 4 | **Opened as the working directory** | any agent, any version, no plugin loading | `cd <path> && claude`; `CLAUDE.md` orients the agent and the playbooks work as plain files |
| 5 | **Added to another project** | work on project X with regency at hand | `claude --add-dir <path>` and say: *read `<path>/CLAUDE.md` first* |
| 6 | **A team** | everyone gets it | push this folder to a git repo, then in the project's `.claude/settings.json`: `{"extraKnownMarketplaces":{"regency":{"source":{"source":"github","repo":"<org>/<repo>"}}},"enabledPlugins":{"regency@regency":true}}` |
| 7 | **Claude account** (cloud sessions, Cowork) | sessions that cannot load a local plugin | `python scripts/package.py`, then install `dist/regency-<version>.plugin` on the account |

**Verified against this exact folder on Claude Code 2.1.201:** ways 1, 4 and 5 in live sessions
(`/regency` help, `/regency doctor`, `/regency:engine:critical`, and a read-only
`/regency:team:status` on a real project with a different layout); way 2 by `claude plugin validate`
plus install in an isolated config; way 3 by loading it as a skills-directory plugin. Way 6 follows
the documented settings shape and was not run. Way 7 is built and structurally checked, not yet run.
Cloud sessions do not load local plugins: use way 7, or way 4 or 5.

**Permissions.** A session whose working directory is a project reads regency's files from outside
that directory. In a headless run (`claude -p`) that read is denied unless you grant it: add
`--add-dir <path>` (or a `Read(<path>/**)` rule). Interactively, Claude Code asks the first time.

First command, any way: **`/regency doctor`** (or `python scripts/doctor.py`).

## What you get

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
| `/regency:scribe` | Scribe sub-agent: turn a concept, requirement or development problem into a clean, causally structured development artifact using the engines. | `<delegated material>` | `skills/scribe/SKILL.md` |
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

`/regency:<id>:<sub>` is the same playbook as `/regency:<id> <sub>`. With no plugin loaded, open the
playbook named in the last column and follow it.

## Hooks

Shipped with the plugin in `hooks/hooks.json`; each one runs a script in `scripts/` and answers with one
line at most. Full reference: `library/hooks.md`.

| Hook | When | What it does |
|---|---|---|
| `guard-push.py` | before a git command | denies a push to `main`/`master` in any form |
| `hook-hazard.py` | before / after a shell command | lets cloud reads run; denies a cloud write unless the Regent quoted that exact command in this pass; asks before deleting, discarding, force or history rewrites, worktree layout, system installs; after a destructive step, keeps writes waiting until the Regent says a release verb |
| `hook-acts-guard.py` | before a file write | denies writes in `.scope/`, rewrites of acts (Orders, gates, ladder plans, opinions, dated handoffs), changes under a `lock` slice, and new names with banned tokens |
| `hook-lineage.py` | after a file write | refreshes the file's fingerprint and writes a STALE line under every norm slice that governs it |
| `hook-journal.py` | after writes, git changes, subagents, tasks, compaction, session end | appends one checkpoint line (OpenTelemetry GenAI keys), latest 200 kept |
| `hook-resume.py` | session start, resume, clear, compaction | one resume line: ledger counts, STALE lines, latest Order, last checkpoint |
| `hook-verbs.py` | the Regent's message | opens a pass: records the quoted cloud commands, ends the hazard watch on a release verb, names the command for a Regent verb (conventions §9) |

Recorders write only in a project that already has `.shortcuts/.virtual/`; outside the Regent's projects
the hooks are silent. A hook whose script is missing **fails open**, so `scripts/doctor.py` runs every
hook's self-test and feeds each one a real event. Without the plugin (ways 4 and 5),
`python scripts/guard-push.py --snippet` prints the push guard's settings block for this machine.

## Frontend documentation for a project

`/regency:ux-init` scaffolds a project's complete frontend documentation into `<guidelines>/.ux/` from
`library/templates/ux/`: an index, the brief, foundations, role-named tokens with a generated
stylesheet, patterns and state models, view archetypes, a component catalogue with ready CSS,
accessibility, assets, a rendered sample, `UX-UI-##` rules and a changelog, with a README in every
folder. It fills the brief with the Regent, then creates one folder per view and component.
`python scripts/ux.py plan|scaffold|brief|expand|check|build` is the engine (computed contrast, role
names, brief holes as asks; never overwrites).

## Optional: set up the machine you work on

Pieces that live outside this folder and make regency's conventions hold in **every** project. Each has
its source inside this folder (`library/maintaining.md` lists them); none is required; each is small and
reversible. The installers never overwrite a file they did not create.

| Piece | Where | What it does |
|---|---|---|
| **User `CLAUDE.md`** | `~/.claude/CLAUDE.md` | from `library/templates/user-CLAUDE.md` (replace `{{REGENCY_ROOT}}`): one `@` import of `library/conventions.md`, so your labels, language rule, "proceed" and git verbs apply even where the plugin is not loaded (about 2k tokens per session) |
| **Role agents** | `~/.claude/agents/{po,dv,qa,da}.md` | the four roles as real subagents with their tool limits (QA has no edit tools, PO has no shell). Source of truth is `library/agents/`; `python scripts/install-agents.py` writes the files with this machine's path and never overwrites one it did not create (`--check`, `--uninstall`) |
| **Path-scoped rules** | `~/.claude/rules/*.md` with `paths:` frontmatter | conventions that load only when a matching file is touched: UI text in markup, writing in `.guidelines/`. Source of truth is `library/rules/`; `python scripts/install-rules.py` installs them (`--check`, `--uninstall`) |

## How it stays portable

- **Relative paths only.** A skill finds the root two directories above its `SKILL.md`; a library file
  names others as `library/…`. `scripts/doctor.py` fails on any drive letter, home directory or
  `/mnt/…` path.
- **No assumed layout.** Commands locate a project's documents through `library/layouts.md`
  (dotted `.guidelines/` or classic Orbital), prefer the project's own role specs over the bundled
  ones, and report a missing document instead of improvising.
- **One source of truth.** `library/registry.json` defines the commands; `scripts/build.py` generates
  the nested aliases and the tables above. `scripts/doctor.py` proves the folder is consistent.
- **Heavy material on demand.** The always-on cost of the whole plugin is the twelve skill descriptions
  (measure with `claude plugin details regency`) plus one resume line per session; engines, role specs
  and templates load only when a command needs them.
- **The Regent's way of working travels with it** in `library/conventions.md`, so a fresh instance
  needs no prior conversation to behave correctly.

## Layout

```text
regency/
├── .claude-plugin/        plugin.json, marketplace.json (the folder is its own marketplace)
├── CLAUDE.md              read by Claude Code when opened here
├── README.md
├── hooks/hooks.json       triggers only: every hook runs a script in scripts/ (library/hooks.md)
├── skills/<id>/SKILL.md   the playbooks (12)
├── commands/<id>/<sub>.md generated aliases for /regency:<id>:<sub>
├── library/               conventions, hooks, rules/, layouts, registry, maintaining, team/, agents/, engines/, orders/, templates/, examples/
├── scripts/               build · doctor · package · vp · conventions_check · ux · install-agents · install-rules · guard-push · hook_wire · hook-*
├── dist/                  generated .plugin archives (package.py); never edit, never commit
└── discard/               superseded material (see discard/INDEX.md); safe to omit when sharing
```

## Maintain

```bash
python scripts/build.py     # after editing library/registry.json
python scripts/doctor.py    # before sharing; exit code 1 means something is broken
python scripts/package.py   # after a version bump: dist/<name>-<version>.plugin for way 7
```

Requirements: Python 3.8+ on the PATH as `python` (scripts and hooks, standard library only) and a
Claude Code version that supports plugins. Verified on Claude Code 2.1.201.
