# Regency

**Good practice for software development with AA** — the Regent's portable toolkit for Claude Code.

Welcome, Regent.

Software development already has its practices. What it does not have yet is an official name for the
person who gives the commands when an AI writes the code. Regency gives one: that person is the
**Regent**, and the AI is the **Advanced Algorithm** — **AA**.

Regency manages AA's capabilities. It sets down what developing with AA takes — who decides, who
builds, who verifies, what must be true before a commit exists — as files AA reads and scripts that
check them. The knowledge and patterns behind it are refined in a manual, *Hackiavelli — The Manual of
Good Regency*; this repository is its practical part, built alongside the book and run on it, so that
every candidate practice is proved first-hand.

It exists to solve a problem. AA makes code cheap; review stays human. When production speeds up and
review does not, work that nobody has checked piles up, and the team gathers risk while it looks more
productive. Regency's answer is a few adjustments to software development as it already is: the
familiar roles — product owner, developer, quality analyst, data analyst — played by AA, working in
units small enough to judge without reading everything, through a machine gate before any human looks,
up to a review packet where the Regent decides.

It is a vanguard idea, and it needs people. If you develop software with AA, it was written for you:
try it on real work, and help refine it.

**Portable by construction.** The folder is self-contained and relocatable: every path in it is
relative to the folder itself, the scripts use only the Python standard library, and nothing points at
a machine, a user or a project. Copy it, mount it, clone it, or point any Claude Code instance at it.

## Start in a minute

1. **Load it** for one session: `claude --plugin-dir <path>`, where `<path>` is this folder. Every other
   way is [below](#use-it--pick-one-way).
2. **Check it:** `/regency doctor`. It checks the folder and makes every hook prove itself on a real
   event.
3. **Try an engine** — no project needed: `/regency:engine:critical <a claim you would defend>`.
4. **In a project:** `/regency:init` scaffolds the guidelines, `/regency:team <unit>` runs one pass and
   stops at the review packet, and `/regency:virtualpath:ongoing` is the first peek when you come back.

## How it works

**Rule zero — Mastery spares Synthesis** (*Domínio evita Síntese*). Whatever can be written down as a
script, a template, a registry entry or a hook is written down, and AA reads it instead of inferring it
again. The less AA has to fill gaps, the better both sides perform.

**The Regent decides.** AA measures, proposes and refuses; it never ratifies a norm it wrote. A choice
that belongs to the Regent comes back as a closed question, never as a guess.

**Work is cut until it can be judged.** Ideal (MAX) → MVP (MIN) → Module → Step → Task → Phases F0–F6.
The Ideal is never a target: it makes the MVP defensible by contrast. Each task declares the span of
phases it may touch; needing one outside it stops the task and sends it back.

**A team, isolated by role.** Each role sees only what cannot corrupt its judgement, and the roles
exchange artefacts, never reasoning: QA never reads DV's explanation of why the code is right, because
agreement is the default failure of a model reviewing a model. DA joins when the work touches data.

```text
/regency:team <unit>          should the team act? who does what?
   │
   ▼
PO frames → QA challenges → DA models → DV builds → gate → QA verifies → PO weighs the risk
   │                     artefacts only, never reasoning
   ▼
review packet                 span declared vs touched · gate result · manifest diff
   │                          · QA's risk opinion · the diff, read last
   ▼
the Regent decides
```

**Returns are checked before you read them.** Every subagent return is a JSON envelope under its own
contract, checked against it by `scripts/returns.py`, and again by `hook-gov.py` when the owner's
packet comes back. A finding that keeps returning is counted by its class (`scripts/gov.py recur`), so
a class that recurs shows itself instead of hiding behind new instances.

**Memory travels with the repository.** The project's guidelines hold its norms; `.shortcuts/.virtual/`
holds the work ledger and the code-to-norm lineage, with an exact index kept beside them as a local
cache, so a fresh session resumes from traces, not from memory.

The method in full: `library/team/ORCHESTRATION.md`. The ids it uses: `library/ids.md`.

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

**Verified.** On Claude Code 2.1.201: ways 1, 4 and 5 in live sessions (`/regency` help,
`/regency doctor`, `/regency:engine:critical`, and a read-only `/regency:team:status` on a real project
with a different layout); way 2 by `claude plugin validate` plus install in an isolated config; way 3
by loading it as a skills-directory plugin. Way 7 runs in Claude's cloud sessions: regency 2.3,
installed on the account, loads its skills and hooks there. Way 6 follows the documented settings shape
and has not been run. On Claude Code 2.1.305, regency 2.6 passes `claude plugin validate`. Cloud
sessions do not load local plugins: use way 7, or way 4 or 5.

**Permissions.** A session whose working directory is a project reads regency's files from outside
that directory. In a headless run (`claude -p`) that read is denied unless you grant it: add
`--add-dir <path>` (or a `Read(<path>/**)` rule). Interactively, Claude Code asks the first time.

## What you get

Every command, from `library/registry.json`:

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
| `/regency:virtualpath` | Query the code-to-norm lineage registry and the work ledger (what is ongoing, drafted, in review or backlogged, plus every trace of agent work) with scripts/vp.py. The first peek when returning to a repository. | `<code\|slice\|stale\|check\|ongoing\|trace\|drafts> [argument]` | `skills/virtualpath/SKILL.md` |
| `/regency:virtualpath:code` | Which norm slices govern this code file? Read them before editing it. | `<code path>` | same playbook, subcommand `code` |
| `/regency:virtualpath:slice` | Which code does this norm slice govern? | `<virtual path>` | same playbook, subcommand `slice` |
| `/regency:virtualpath:stale` | List slices marked STALE, waiting for the Regent's check. | `` | same playbook, subcommand `stale` |
| `/regency:virtualpath:check` | Check that every slice resolves to an anchor and every target file exists. | `` | same playbook, subcommand `check` |
| `/regency:virtualpath:ongoing` | Read the work ledger (.virtual/ongoing.json): what is ongoing, drafted, in review, blocked or only backlog. First peek on returning to a repo. | `` | same playbook, subcommand `ongoing` |
| `/regency:virtualpath:trace` | Gather every trace of agent work (uncommitted files, unmerged branches, stashes, recent commits, touched guidelines, STALE lines, Orders) to reconcile the ledger. | `` | same playbook, subcommand `trace` |
| `/regency:virtualpath:drafts` | List every unverified speed-mode draft (ledger items and DRAFT commits no verifying commit closed); exits 1 while one remains, and nothing merges past plumbing until it is 0. | `` | same playbook, subcommand `drafts` |
| `/regency:tailwind-audit` | Audit, fix or build a Tailwind frontend against a design-system norm: deterministic scan, manual passes, headless render at 360/768/1280 in light and dark, and a flex/grid/absolute layout knowledge base for confusing positions. | `[path \| 'layout' <symptom> \| 'render' <page>]` | `skills/tailwind-audit/SKILL.md` |
| `/regency:station` | Mise-en-place before a pass: check the station is prepped (toolchain, trust, gate tasks, ledger, lineage), run the gate through mise, or propose a mise.toml. mise is optional. | `[check [unit] \| gate [task] \| scaffold [write] \| line]` | `skills/station/SKILL.md` |
| `/regency:station:check` | The station gate: one line per item; red stops the pass. Read-only. | `[unit]` | same playbook, subcommand `check` |
| `/regency:station:gate` | Run the mechanical gate through mise, one verdict per check; refuses an untrusted station. | `[task]` | same playbook, subcommand `gate` |
| `/regency:station:scaffold` | Propose a mise.toml from the repository's stack; writes only when none exists. | `[write]` | same playbook, subcommand `scaffold` |
| `/regency:station:line` | The station as one slice line. | `` | same playbook, subcommand `line` |
<!-- regency:dispatch:end -->

`/regency:<id>:<sub>` is the same playbook as `/regency:<id> <sub>`. With no plugin loaded, open the
playbook named in the last column and follow it.

## The team and its subagents

Four roles, played by AA under their own contracts (`library/team/`). PO and QA are managers: they frame
the work and judge it. DV and DA are operators: they produce it, as code and as data contracts. DA and
DV never talk directly; what one needs from the other goes through a manager.

| Role | Answers for | Its subagents |
|---|---|---|
| **PO** — Product Owner | what is worth building, and in what order | suba-requirements-analyst · suba-design · suba-strategy\* · suba-research\* |
| **QA** — Quality Analyst | whether it really works, and how it breaks | suba-recon · suba-tester · suba-validator |
| **DA** — Data Analyst | what the data support, and with what confidence | suba-acquisition · suba-analysis · suba-modeling |
| **DV** — Developer | how it works, and at what maintenance cost | suba-scribe · suba-architect · suba-implementer |

\* proposals, awaiting ratification.

A subagent — a *suba* — is a lens inside its owner's stage: the owner wears it rather than dispatching
it, and it never sees more than its owner may see. `library/subagents/ALIGNMENT.md` holds what every
suba inherits; `scripts/gov.py` holds who owns which. The Scribe is also a command: `/regency:scribe`
writes a text for you, with none of DV's authority.

## Hooks

Shipped with the plugin in `hooks/hooks.json`; each one runs a script in `scripts/` and answers with one
line at most. Full reference: `library/hooks.md`.

| Hook | When | What it does |
|---|---|---|
| `guard-push.py` | before a git command | denies a push to `main`/`master` in any form |
| `hook-hazard.py` | before / after a shell command, after a role agent returns | lets cloud reads run; denies a cloud write unless the Regent quoted that exact command in this pass; asks before deleting, discarding, force or history rewrites, worktree layout, system installs; after a destructive step, keeps file writes waiting for a PO or QA permit or the Regent's release verb |
| `hook-acts-guard.py` | before a file write | denies writes in `.scope/`, rewrites of acts (Orders, gates, ladder plans, opinions, dated handoffs), changes under a `lock` slice, and new names with banned tokens |
| `hook-lineage.py` | after a file write | refreshes the file's fingerprint, re-indexes it, and writes a STALE line under each norm slice whose governed nodes changed |
| `hook-gov.py` | a subagent starts or returns | gives a role or suba its governance line; routes the returned packet (G1 to the ledger, G2 and G3 to the Regent); checks a packet that names its stage against that stage's return shape, and every suba envelope in it against its contract |
| `hook-journal.py` | after writes, git and hazardous shell commands, subagents, tasks, compaction, session end | appends one checkpoint line (OpenTelemetry GenAI keys), latest 200 kept |
| `hook-resume.py` | session start, resume, clear, compaction | one resume line: ledger counts, STALE lines, latest Order, last checkpoint, the index |
| `hook-verbs.py` | the Regent's message | opens a pass: records the quoted cloud commands, ends the hazard watch on a release verb, names the command for a Regent verb (conventions §9) |

Recorders write only in a project that already has `.shortcuts/.virtual/`; outside the Regent's projects
the hooks are silent. A guard whose script cannot start blocks its call (`onFailure: block`, Claude Code
2.1.295 and later); a recorder, or a guard on an older version, fails open — so `scripts/doctor.py` runs
every hook's self-test and feeds each one a real event. Without the plugin (ways 4 and 5),
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
- **One source of truth.** `library/registry.json` defines the commands and each suba's `contract.json`
  its return; `scripts/build.py` generates the nested aliases, the command tables and the return
  templates. `scripts/doctor.py` proves the folder is consistent.
- **Heavy material on demand.** The always-on cost of the whole plugin is its fourteen skill
  descriptions — about 2.7k tokens on Claude Code 2.1.305 (`claude --plugin-dir <path> plugin details
  regency`) — plus one resume line per session; engines, role specs, subagents and templates load only
  when a command needs them.
- **The Regent's way of working travels with it** in `library/conventions.md`, so a fresh instance
  needs no prior conversation to behave correctly.

## Layout

```text
regency/
├── .claude-plugin/        plugin.json, marketplace.json (the folder is its own marketplace)
├── CLAUDE.md              read by Claude Code when opened here
├── README.md
├── hooks/hooks.json       triggers only: every hook runs a script in scripts/ (library/hooks.md)
├── skills/<id>/SKILL.md   the playbooks (14)
├── commands/<id>/<sub>.md generated aliases for /regency:<id>:<sub>
├── library/               conventions, ids, layouts, registry, hooks, virtualpath, task-granulation,
│                          maintaining; team/, agents/, subagents/, engines/, orders/, rules/,
│                          templates/, examples/
├── scripts/               build · doctor · package · conventions_check · vp · idx · gov · returns ·
│                          station · ux · install-agents · install-rules · guard-push · hook_wire · hook-*
├── dist/                  generated .plugin archives (package.py); never edit, never commit
└── discard/               superseded material (see discard/INDEX.md); safe to omit when sharing
```

## Maintain

```bash
python scripts/build.py     # after editing library/registry.json or a suba's contract.json
python scripts/doctor.py    # before sharing; exit code 1 means something is broken
python scripts/package.py   # after a version bump: dist/<name>-<version>.plugin for way 7
```

regency is versioned `a.b`: `+b` for a content change, `+a` for a major rule finished, reinterpreted or
invented, with no cap on either. `library/registry.json` and `.claude-plugin/plugin.json` carry the same
value.

Requirements: Python 3.8+ on the PATH as `python` (scripts and hooks, standard library only) and a
Claude Code version that supports plugins.

## Read next

| File | What it holds |
|---|---|
| `library/conventions.md` | how the Regent works: rule zero, labels, language, doubts, git verbs, permissions |
| `library/team/ORCHESTRATION.md` | the method: review compression, the tree, the cycle of a task, the review packet |
| `library/team/TEAM.md` | the common standard of the four roles |
| `library/subagents/ALIGNMENT.md` | what every suba inherits, and its return envelope |
| `library/hooks.md` | every hook: what it guards or records, and the files it touches |
| `library/virtualpath.md` | the code-to-norm lineage, the work ledger and the exact index |
| `library/maintaining.md` | verified Claude Code behaviour, and the traps met while building this |

## Help shape it

Regency improves on evidence from real use. The most useful kinds: a rule that failed on real work, a
doubt that kept coming back, an instruction AA needed explained twice — which, by rule zero, wants to
become a script or a template. Bring it as an issue or a pull request, with its evidence: a practice
enters as a proposal and becomes a rule only when ratified.
