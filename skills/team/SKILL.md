---
name: team
description: "Regency team pass. Declare, for one pass over one unit of work, whether the PO/DV/QA/DA team should act and who does what, then dispatch the role agents with isolated context, route their returns and stop at the human review packet. Speed modes: extreme-go-horse (two teams, passes chained on declared fuel) and just-in-time (draft a range, unverified, on plumbing). Use for /regency:team, /regency:team:declare|status|reopen|extreme-go-horse|just-in-time, a unit id such as M03.D02.T04, or when asked to 'call the team', 'run a pass', 'dispatch the agents', 'who does what next', 'should the team act', 'release the Kraken'. Works on any project that has guidelines (see library/layouts.md)."
argument-hint: "[unit] | declare | status | reopen <unit> | extreme-go-horse [range] fuel=<n> | just-in-time <from> <to>"
---

# team — one pass, one declaration

> **Root.** This file is `skills/team/SKILL.md`; the regency root is two directories above it, and
> every `library/…` path below is relative to that root. Read `library/conventions.md` once per
> session. Find the project's documents with `library/layouts.md`; do not assume a layout.

A **pass** answers two questions about one unit of work, and nothing else:

1. **Should the team act?** — a decision, taken by the first precondition that fails.
2. **Who does what?** — which role runs each stage of the step cycle, with which inputs,
   producing which artefact, accepted under which condition.

Then, if the environment allows it, the pass dispatches the roles and ends at the human
review packet. It never ends at a commit.

## What you are in this skill

You are the **coordination** of `ORCHESTRATION.md` §12 (not a fifth role): you select the unit, run the
checks, dispatch the roles, route the returns and assemble the packet. You have **no
opinion** on product, code, quality or data.

Every decision you make is procedural and cites the document it came from. If you notice
yourself judging whether code is good, whether a feature is worth it, or whether a number
looks right, stop — that is a role's call; route it to that role. An orchestrator with
opinions becomes an unaccountable fifth role, outside every contract table and invisible to
every Definition of Done.

## Sources — read them, never restate them

The role documents are the agent specifications. Do not write parallel prompts that paraphrase
them; paraphrases drift (`ORCHESTRATION.md` §10). Packets **point at** the files.

Resolve every document through `library/layouts.md` (guidelines root, layout, role-spec precedence).
In the table, `<G>` is the guidelines root of the project.

| Read | For |
|---|---|
| the entry/index document of `<G>` (`.shortcuts/README.md` or `AGENTS.md`) | reading order, id grammar, the rules that do not bend |
| role specs: `TEAM.md` §3, §7, then `<ROLE>.md` §19 — project copy first, else `library/team/` | the contract matrix; the shared control binding; each role's control binding |
| `library/team/ORCHESTRATION.md` | this skill's process basis |
| the plan documents (`CHECKLIST`, `LADDER_PLAN_*`, `GATE_*`, state file) | the unit, its phase, its gate |
| the decisions register (`DECISIONS.md`) | ratified norms; the adoption stage, if recorded |

**Precedence.** Where `ORCHESTRATION.md` and the rest of the document set disagree, the rest of
the set wins, and the disagreement is resolved by `library/team/references/vocabulary-map.md` —
read it at the first pass of every session. It also says how `ORCHESTRATION.md`'s terms (Ideal/MVP,
module M#, step D#, task T#, phases F0–F6, Rule A/B, the F3 manifest) translate into the project.

**A path that does not resolve is a defect.** Report it in the declaration; do not improvise
around it.

## Arguments

| Invocation | Meaning |
|---|---|
| `/regency:team` | the next unit: the first **active** task (state `active`) of the module in flight, per the checklist; `blocked` and `revoked` tasks are skipped |
| `/regency:team M03.D02.T04` | that unit (the span is read from the task, e.g. `[F1–F3]`) |
| `/regency:team:declare [unit]` (or `/regency:team declare`) | declare only; dispatch nothing |
| `/regency:team:status` (or `/regency:team status`) | no new pass — report open packets, review queue, regime, returns in flight |
| `/regency:team:reopen M03.D02.T04` (or `/regency:team reopen …`) | a reopening: new pass, fresh context, labelled as a reopening (`ORCHESTRATION.md` §6) |
| `/regency:team:extreme-go-horse [range] fuel=<n>\|fuel=all` | speed mode: two full teams, chained passes until the declared fuel runs out (§ *Speed modes*) |
| `/regency:team:just-in-time M01.D01.T01 M03.D06.T09` | speed mode: draft every task of the range, DRAFT/UNVERIFIED on plumbing (§ *Speed modes*) |

**Identifiers come from the tree, never from typing:** `M03` is a module, `M03.D02` its second step, `M03.D02.T04` the fourth task of that step, `[F1–F3]` the span the task declared. A code typed by hand diverges from the tree, and from then on the plan stops describing the repository. If the project still uses the classic grammar `M<n>.F<k>.T<nn>`, read `F<k>` as the span (`library/team/references/vocabulary-map.md`).

If the unit cannot be resolved from the arguments and the checklist, ask one closed question
listing the candidates (a pop-up). Do not guess a unit. A unit may also arrive from an Order
(`/regency:order:dispatch`): use the manifest it emitted as the unit, and never re-derive the
breakdown it already holds.

## The pass

### Step 0 — First peek

`python scripts/vp.py ongoing` and `python scripts/vp.py trace` (read-only): what is already ongoing,
under review or blocked, and every trace of agent work in the repo. An `ongoing` item on this unit
whose evidence is gone, or dirty files that belong to no item, are findings for the declaration's
`defects` — never silently adopted. The pass writes itself into the ledger as `pass:<unit>` evidence
when it starts, and ends the unit at `review` (never `done`) until the human approves.

**A unit in `draft`** is a speed mode's output, DRAFT/UNVERIFIED (`library/team/SPEED_MODES.md` §6): this
pass is its verification. Frame and Challenge are `active`, never `reused` (a seed card is an input, not a
frame); Build starts from the draft and DV writes the named tests; Verify goes to a fresh QA, never the one
that seeded or gated the draft, and mutation analysis comes before the green suite counts. Close carries
`Verified-Draft: <unit>` in its commit.

### Step 1 — Establish state

Build the working state of `TEAM.md` §7.2 for the unit. Every observation carries its source
and an epistemic status from §7.3. Retrieval is targeted: the documents the unit cites, then
the reading order in `AGENTS.md` — never the whole repository "for context" (RA §6).

Detect the dispatch mode now, by looking at your tools — do not assume. (In Claude Code the
Agent tool provides isolated subagents; without it, the mode is single-context.)

- **isolated** — a subagent/Task tool exists, so each role can run in a fresh context
- **single-context** — no such tool; every role would share this context
- **declare-only** — the user asked for it, or single-context and the user has not asked to run

### Step 2 — Go / no-go

Run the checks **in order**. The **first** failing check decides the pass; do not keep
evaluating to find a way to act. "Do something" is not preferable to "obtain more
information" (RA §10).

| # | Check | Fails when | Decision | Routed to | Source |
|---|---|---|---|---|---|
| 0 | Halt | an L5 escalation is open anywhere in the module | `STOP` | human | TEAM §7.8 |
| 1 | Review queue | a previous packet awaits a human decision, or anything is merged unreviewed | `HOLD` | human | ORCH §18 — the queue is the ceiling |
| 2 | Unit resolves | the id is absent from the checklist or does not match its place in the tree, or its blueprint is missing; **or** the task is `revoked` (a revoked task is not pending) → `RETURN`; `bloqueada` → `HOLD`, routed to whoever owns the dependency | `RETURN` / `HOLD` | PO / dependency owner | ORCH §6, §8 |
| 3 | Module gate | the module has no signed gate sheet with three attestations | `RESTRICT` — framing and attestation stages only; no build | PO | TEAM §4, PO §19 |
| 4 | Norm ratified | the cited norm is missing, or was drafted by an agent and not ratified by a human | `HOLD` | human | ORCH §7 — F0 is human-anchored |
| 5 | Span | the task declares no span, or the phases it touches are not inside the span it declared (a range such as `[F1–F3]` is legal) | `RETURN` | PO | ORCH §7 |
| 6 | Premises | any premise is `CONTRADICTED` or `STALE` | `RESTRICT` — observe and verify only | the premise's owner | TEAM §7.6 |
| 7 | Retry budget | equivalent attempts on this unit reach the retry limit | `ESCALATE` (L4) | human | TEAM §7.10 |
| 8 | Roles enabled | a stage needs a role not yet enabled at the adoption stage | proceed; the **human** plays that role, and the declaration says so | human | ORCH §21 |
| 9 | Parallelism | the request would run two agents inside one module | refuse that part; one agent per module | — | ORCH §4 |

All checks pass → `ACT`.

The decision vocabulary maps onto RA §12's control responses: `ACT` → continue,
`RESTRICT` → restrict or observe, `HOLD` → wait, `RETURN` → adjust, `ESCALATE` → escalate,
`STOP` → terminate.

**The adoption stage** (ORCH §21, stages 1–5) decides which roles are agents. Look for it in
`DECISIONS.md`. If it is not recorded, ask the human once, as a closed question with the five
stages, and propose recording the answer as a `DC#` — do not assume a stage.

### Step 3 — Declare who does what

The task cycle of `ORCHESTRATION.md` §14, bound to the repository. For each stage, the
declaration sets a status: `active`, `reused`, `skipped` (with its reason) or `human`.

| Stage | Owner | Runs when | Produces | Accepted only if (TEAM §3) |
|---|---|---|---|---|
| 1 Frame | PO | criteria for this span are absent or changed | story: problem, criteria, out-of-scope, declared span, cited norm | span stated, norm cited |
| 2 Challenge | QA | after Frame, before any build | ambiguities returned, or "verifiable" | every criterion checkable by a stranger |
| 3 Shape | DA | the unit touches `DATA_MODEL.md`, an event, a data contract, or a number a user sees | event spec + data contract | name, trigger, payload, types, optionality, key, granularity |
| 4 Build | DV | decision is `ACT` | commit-ready change + change notes | passes CI, rollback named, notes in the fixed shape of `library/team/references/packets.md` |
| 5 Gate | machine | after every Build | gate log | see vocabulary map — Rule A/B, span, tests, surface diff |
| 6 Verify | QA | gate green | risk opinion + version verdict | open bugs by severity, coverage gaps, what was **not** covered |
| 7 Accept | PO | risk opinion issued | acceptance, with known defects recorded | a different role from the producer (F6 is never self-accepted) |
| 8 Close | PO decides; DV, QA, DA supply | **only after human approval** | changelog, docs, backlog delta, surface change | the commit(s), task id in each subject |

**Frame and Challenge are per span, not per task.** If this span's criteria were already
framed and challenged, and nothing about them has changed since, mark both `reused` and cite
the artefact. Re-run them when criteria changed, or when any return blamed ambiguity. This is
the hysteresis of TEAM §7.6 applied to framing: entering costs a full frame; staying costs
nothing until something moves.

**The gate is never skipped.** If no automated check exists for part of it, that part is run
by hand and declared `manual` — not omitted. Everything about review compression depends on
this stage being strict (ORCH §13).

### Step 4 — Build the packets

Each active role gets a packet built from `library/team/references/packets.md`: what it loads, the
artefacts it receives, what is **withheld** from it, the artefact it must return and the
acceptance condition.

Two withholdings carry the weight:

- **QA never receives DV's reasoning.** Only the diff, the tests, the criteria, the gate log
  and the surface diff. A reviewer who reads the implementer's justification tends to agree
  with it — that is the default failure mode of a model reviewing a model.
- **DA never receives the hoped-for answer.** An analyst told what result is wanted will find
  it.

You forward **files**, never your summary of them. When routing a return, forward the
artefact — the bug report, the gate log — not your interpretation. A summary is reasoning,
and reasoning passed between agents is unverifiable (ORCH §11).

### Step 5 — Dispatch

**Isolated mode.** One fresh subagent per active stage, its prompt being the packet and
nothing else. Stages run in order within the unit. When a subagent returns, check the
acceptance condition **mechanically** — are the required fields present — not whether the
content is good: `python scripts/returns.py check --stage <role>.<stage> <file|->` (the hook
already appends its verdict to the context line when the prompt carried `Stage:`, and checks every
suba envelope in the message). A finding is a `RETURN` to that role; the content's merit belongs to
the next role in the cycle. Envelopes are never forwarded: the next role's packet is built from
artefacts, row by row (`library/team/references/packets.md` §2).

**Role agents.** Dispatch each stage to the registered role agent: Agent tool `subagent_type` `po`, `dv`, `qa` or `da` (installed into `~/.claude/agents/` by `python scripts/install-agents.py`; check with `--check`). They carry the role's tool limits: QA has no edit tools and returns its artefacts verbatim in its final message (store them byte for byte, never reworded); the PO has no shell; none can ask the user questions, so a missing decision comes back as terminal state `BLOCKED` or `UNRESOLVED`. If a role agent is not installed, say so in the declaration's `defects`, fall back to `general-purpose` with the same packet, and mark `tool limits: not enforced`.

**Single-context mode.** Default to `declare-only`. If the user asks to run anyway, the roles
run in sequence in this context, and independence is degraded — you, running QA, have just
seen DV's reasoning. So:

- the declaration says `independence: degraded`
- QA's risk opinion and DA's oracle confirmation enter as `INFERRED`, never `KNOWN`
- the packet recommends the human run Verify in a fresh session

Never present a single-context run as isolated.

### Step 6 — Route returns

| Return | From | To | Carrying |
|---|---|---|---|
| criterion ambiguous | QA (Challenge) | PO | the criterion and the nearest checkable version |
| span must be exceeded | DV | PO | what does not fit; the pass halts — never widen silently (ORCH §14) |
| gate red | machine | DV | the gate log; QA and the human are not consumed |
| datum missing | DV or DA | DA → DV | event spec and contract |
| defect found | QA | DV | the bug report exactly as QA wrote it |
| number disagrees with oracle | QA | DA + DV | the diverging record |
| norm wrong or unobeyable | any | human | an RA §21 escalation block |
| context bleed — a role cites what it was never given | any | human | the citation; treat it as a containment defect (ORCH §18) |

Every return adds one attempt to the unit (check 7).

### Step 7 — Assemble the review packet and stop

In this order (ORCH §15), because a trustworthy packet lets the human decide from the first
four items:

1. declared span vs. span actually touched
2. the gate result
3. the surface diff — usually empty, and loud when not
4. QA's risk opinion
5. the diff itself, last

Then stop. The human reviews. Only after the human approves does Close run, producing
the commit or commits (the DV decides how many), each carrying the fully-qualified task id in its
subject and none spanning two tasks. Never commit before approval.

## Counting, closing and ordering (ORCH §5, §6, §9, §16, §17)

These rules decide what a pass may *report*, and they are what keeps `status` honest.

**Task states count differently.**

| State | Meaning | Counts as pending progress |
|---|---|---|
| `active` | in progress or to do | yes |
| `blocked` | stopped by an external dependency | no |
| `revoked` | cancelled by a recorded decision | no |

A revoked task is not a pending task: counting it as pending contaminates every sum above it.
A project written before these names may still use `ativa` / `bloqueada` / `revogada` and `pendente` /
`cumprido` / `não se aplica`: read them as input, as the same states.

**Delivered is not closed.** A step whose tasks are all done is *delivered* and ready to be signed;
**the gate closes it**, and until the gate passes it counts as open. A report that marks a step done
because its tasks ended is reporting engineering and calling it delivery. A module is *concluded*
when every step is closed and the non-functional checklist is clean: that is delivery to
production, not a progress mark.

**The checklist of a task** (twelve items: ratified F0 norm cited; span declared before dispatch; QA
challenged the criteria; DA specified instrumentation *if applicable*; phases touched inside the span;
Rule A and B pass; tests pass and a failing test preceded the rule change; F3 manifest diff empty or
declared *if applicable*; QA risk opinion naming what was not covered; PO accepted with known defects
recorded; human reviewed the packet; every commit cites the task and none spans another task). Each item is `pending`, `met` or `not
applicable`. **The denominator is the number of applicable items**: a task that touches no data never has a
DA item, and counted over twelve it could never reach one hundred percent. Marking an item not
applicable is a recorded decision, never an omission.

**Progress is read from the checklist, never from the phase.** A task is contained in the span it
declared; it does not advance from F0 to F6, and leaving the span is a containment failure.

**The version is derived from the tree, never typed:** major = an official production deployment;
minor = modules concluded; patch = steps with the gate closed; `+hash` = the revision measured. If the
project types a version by hand somewhere that a tree could compute it, report that as a defect.

**Execution order is not numbering.** A task may declare the module it unblocks; the path to a delivery
is assembled from those declarations. The order changes during a project, and that is expected.

## Speed modes

Read `library/team/SPEED_MODES.md` whole before the first speed run of a session: §1 (what speed trades
and never trades), §2 (shared mechanics), and the section of the mode. The pass above still applies to
each unit a speed mode touches, with four differences the doctrine states: team check 1 counts only
packets older than the run; the PO splits or the QA seeds instead of framing each task; the human reviews
the run's packets at the end instead of between passes; and you commit each DV's change in its worktree
(the DV still returns it uncommitted) and merge it into `plumbing`, never further. Every agent is dispatched from here (a
subagent cannot spawn one), with the skeleton of `library/team/references/packets.md` §1 and its
`Stage:` line.

### `extreme-go-horse [range] fuel=<n>|fuel=all` — "Release the Kraken!"

1. **Fuel**: `python scripts/speed.py fuel <arguments>`. Exit 2 → print its one line and stop. Fuel the
   Regent declared in a message of this conversation counts; name it in the first report line.
2. **Range**: `python scripts/speed.py range <from> [<to>]` (default: the active tasks of the module in
   flight). Run Step 0–2 above for the range; a failing check decides as usual (check 1 counts only
   packets older than the run).
3. **Cast**: PO-A, DA-A, DV-A, QA-A and PO-B, DA-B, DV-B, QA-B. DVs with `model: sonnet`, QAs with
   `model: opus`, PO and DA without an override; each DV with `isolation: "worktree"`. A range inside one
   module has one span: team B is not spawned.
4. **Each pass** (§4 there): open (the split on the first pass, `Stage: split`; the last packet's returns
   first afterwards) → shape → build straight through, both DVs at once → commit each DV's change in its
   worktree, merge both worktree branches into `plumbing`, machine gate per task → review, each QA its own span in one batch (`Stage: verify`),
   then both the seam (`Stage: seam`) → write `PASS-<nn>.json`, `python scripts/speed.py packet <it>
   <previous>` must hold → ledger: reviewed units `review` → report the pass → spend one pass of fuel.
5. **T4**: a return failing a third time leaves the packet as an escalation to the Regent.
6. **Stop** when the fuel is spent (finish the review, save the packet), the range is built with no
   return left, a destructive-class action is next, or a span conflict needs the Regent.

### `just-in-time <from> <to>` — draft everything, verify later

1. **Range**: `python scripts/speed.py range <from> <to>`; Step 0–2 above for the range.
2. **Seed**: one QA with `model: opus`, `Stage: seed`: the interface contract and one task card per task,
   no code. Store both byte for byte as `CONTRACT.md` and `cards.json` in the run's folder.
3. **Waves**: `python scripts/speed.py waves cards.json`.
4. **Each wave**: one DV per card with `model: haiku`, `isolation: "worktree"`, `Stage: draft`, all at once
   (card, contract, the previous gate's fix notes; functional first, no tests) → commit each change in its
   worktree with the draft trailers → merge into `plumbing` → the seeding QA, continued (else a fresh one
   on `opus` with the run's files), `Stage: gate`: builds, runs, matches the contract, fix notes for the
   next wave, accepts nothing → write `WAVE-<nn>.json`, `speed.py packet` must hold → ledger: each unit
   `draft`, open questions answered with the most functional option and listed in its `assumed`.
5. **Report** in the shape of §5 there, ending with the verifying passes the drafts wait for.

## Output — the Pass Declaration

ALWAYS emit this block first, whatever the decision:

```yaml
pass:
  unit: M03.D02.T04            # derived from the tree, or UNRESOLVED
  task_state: active | blocked | revoked
  reopening: false
  cites: BR7                   # the norm; ratified: true | false
  span: [F1–F3]                # declared by the task
  unblocks: M01                # module this task releases, or none
  checklist: "7/10 applicable (70%)"   # met / applicable; not applicable leaves the denominator
  mode: isolated | single-context | declare-only
  independence: full | degraded
  adoption_stage: 1..5 | UNRESOLVED
  regime: ACTIVE | RESTRICTED | HALTED
  decision: ACT | RESTRICT | HOLD | RETURN | ESCALATE | STOP
  decided_by: "check <n> — <source>"
  attempts: 0
  stages:
    - { stage: frame,     who: PO,      status: reused,  artefact: <path> }
    - { stage: challenge, who: QA,      status: reused,  artefact: <path> }
    - { stage: shape,     who: DA,      status: skipped, reason: "touches no data" }
    - { stage: build,     who: DV,      status: active,  returns: <path>, accept_if: <TEAM §3> }
    - { stage: gate,      who: machine, status: active,  manual: [<parts run by hand>] }
    - { stage: verify,    who: QA,      status: active,  withheld: [DV reasoning] }
    - { stage: accept,    who: PO,      status: pending }
    - { stage: close,     who: PO,      status: blocked, until: human approval }
  defects: []                  # unresolved paths, context bleed, conflicts found
  next: <the single thing that happens after this pass>
```

Then the events, one line each (TEAM §7.11):

```text
EVENT DECISION_MADE M03.D02.T04 ORCH check-8
```

Then at most five lines of prose: the decision, what decided it, and what the human needs to
do, if anything. For `ESCALATE`, append RA §21's escalation block. For `HOLD` or `RETURN`,
name the artefact whose arrival would release the pass.

## Examples

**The queue is full.** The previous unit's packet has no human decision.

```yaml
decision: HOLD
decided_by: "check 1 — ORCHESTRATION §18, the queue is the ceiling"
next: human decides on the M03.D02.T03 review packet
```

No stage is dispatched, including ones that look harmless. Dispatching into a full queue only
raises the queue.

**An ordinary build pass.** The gate is signed, BR7 is ratified, the criteria for the span
[F1–F3] were challenged two tasks ago and have not changed, and the unit touches no data. Frame and
Challenge are `reused`, Shape is `skipped`, Build, Gate and Verify are `active`, and Close is
`blocked` until the human approves.

## Boundaries

This skill never:

- gives `GRAND_PLAN.md` to an agent as a target — it may be quoted as rationale only
- authors, drafts-and-cites, or ratifies a norm
- widens a span, or runs two agents inside one module
- accepts an increment, or lets the producing role accept it
- commits before human approval, or lets a commit span two tasks
- judges code, product, quality or data
- continues a reopened unit in the old context
- paraphrases a role file into a prompt
- types an identifier the tree already determines
- counts a `revoked` or `blocked` task as pending
- calls a step closed before its gate has passed, or reports progress "by phase"
- runs `extreme-go-horse` without the fuel the Regent declared, or lets a speed mode's output leave
  `plumbing` before a normal pass has verified it

## `/regency:team:status`

Report, with their sources and in the status format of `library/conventions.md` §8: the review queue
(packets awaiting a human decision), per step the tasks by state and the checklist percentage over
applicable items, steps **delivered** versus **closed**, the version if the tree can derive it, open
returns and their attempt counts, the regime, open escalations, and whichever of `ORCHESTRATION.md` §19's
health metrics can be computed from the repository. Mark the rest `UNRESOLVED` rather than estimating them.
