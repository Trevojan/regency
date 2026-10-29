# regency — reference

The long form behind the repository's homepage (`README.md`): how regency works, every command, the team,
the hooks, the machine-level pieces, how it stays portable, and where everything lives. Installation, the
quick start and development commands are on the homepage.

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

**Projects follow the harness's version.** Each project carries a stamp (`.shortcuts/regency.json`). A
project behind the installed regency is updated before anything writes into it: `/regency:update` plans
every change to what regency owns, applies it on one yes in a clean git tree, and leaves the project's own
text alone. A project ahead of it stops the session until the plugin is updated
(`library/migrations/README.md`).

**Speed when the fuel is short.** Three speed modes seed the whole terrain first and leave the
cultivating to normal passes: `/regency:order:lazy` runs an Emission's Orders and skips every one that
needs you; `/regency:team:extreme-go-horse` runs two full teams on the fuel you declare;
`/regency:team:just-in-time` drafts a whole range, DRAFT/UNVERIFIED on `plumbing` until a normal pass
verifies it. Speed trades verification depth, never the hard rules (`library/team/SPEED_MODES.md`).

The method in full: `library/team/ORCHESTRATION.md`. The ids it uses: `library/ids.md`.

## Commands

Every command and subcommand, from `library/registry.json`:

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
| `hook-acts-guard.py` | before a file write | denies writes in `.scope/`, rewrites of acts (Orders, gates, ladder plans, opinions, dated handoffs), a hand edit of the entry index's generated state block, changes under a `lock` slice, and new names with banned tokens |
| `hook-lineage.py` | after a file write | records the file's fingerprint in the one store (`index.sqlite`), re-indexes it, and writes a STALE line under each norm slice whose governed nodes changed |
| `hook-gov.py` | a subagent starts or returns | gives a role or suba its governance line; routes the returned packet (G1 to the ledger, G2 and G3 to the Regent); checks a packet that names its stage against that stage's return shape, and every suba envelope in it against its contract |
| `hook-journal.py` | after writes, git and hazardous shell commands, subagents, tasks, compaction, session end | appends one checkpoint line (OpenTelemetry GenAI keys), latest 200 kept |
| `hook-resume.py` | session start, resume, clear, compaction | one resume line: a version mismatch first, then ledger counts, STALE lines, latest Order, last checkpoint, the index, the entry index's check and drift counts |
| `hook-shortcuts.py` | session end | rewrites the generated state block of `.shortcuts/README.md` when the state moved |
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
- **Heavy material on demand.** The always-on cost of the whole plugin is its skill descriptions plus
  one resume line per session — measured by `/regency:health:context` (the runtime's own count, when
  `claude plugin details regency` describes this version); engines, role specs, subagents and templates
  load only when a command needs them.
- **The Regent's way of working travels with it** in `library/conventions.md`, so a fresh instance
  needs no prior conversation to behave correctly.

## Layout

```text
regency/
├── .claude-plugin/        plugin.json, marketplace.json (the folder is its own marketplace)
├── .github/assets/        the README banner (an SVG; not shipped in the .plugin)
├── CLAUDE.md              read by Claude Code when opened here
├── README.md              the repository's homepage
├── CONTRIBUTING.md        how a change is proposed and checked (not shipped in the .plugin)
├── LICENSE                MIT
├── hooks/hooks.json       triggers only: every hook runs a script in scripts/ (library/hooks.md)
├── skills/<id>/SKILL.md   the playbooks, one per command
├── commands/<id>/<sub>.md generated aliases for /regency:<id>:<sub>
├── library/               REFERENCE (this file), conventions, ids, layouts, registry, hooks, health,
│                          virtualpath, shortcuts, automation, task-granulation, maintaining; team/,
│                          agents/, subagents/, engines/, orders/, rules/, templates/, migrations/, examples/
├── scripts/               build · doctor · package · health · migrate · conventions_check · vp · idx ·
│                          shortcuts · gov · returns · speed · station · ux · headless · install-agents ·
│                          install-rules · install-automode · guard-push · hook_wire · hook-*
├── dist/                  generated .plugin archives (package.py); never edit, never commit
└── discard/               superseded material (see discard/INDEX.md); safe to omit when sharing
```

## Read next

| File | What it holds |
|---|---|
| `library/conventions.md` | how the Regent works: rule zero, labels, language, doubts, git verbs, permissions |
| `library/team/ORCHESTRATION.md` | the method: review compression, the tree, the cycle of a task, the review packet |
| `library/team/TEAM.md` | the common standard of the four roles |
| `library/subagents/ALIGNMENT.md` | what every suba inherits, and its return envelope |
| `library/hooks.md` | every hook: what it guards or records, and the files it touches |
| `library/virtualpath.md` | the code-to-norm lineage, the work ledger and the exact index |
| `library/shortcuts.md` | the entry index, its generated state block, drift, and the one store it shares with the exact index |
| `library/maintaining.md` | verified Claude Code behaviour, and the traps met while building this |
