---
artifact: ORCHESTRATION
nome_completo: Agent Orchestration over the Planning Vertical
versao: 3.0
tipo: definicao_de_processo
relacionados: [PHASES.md, GRAND_PLAN.md, MINIMUM_PLAN.md, PO.md, DV.md, QA.md, DA.md]
---

# Agent Orchestration

> Split software into units small enough to be verified without anyone having to
> read everything.

## 1. Principle

Agents make code production cheap. Review remains expensive, because it remains
human. When production accelerates and review does not, a queue of merged work
that no one has checked forms, and the team accumulates risk while appearing more
productive.

**Human review capacity is the limiting resource.** An orchestration that
produces more than can be reviewed has not increased throughput; it has moved the
queue elsewhere.

The goal of the method is not to multiply agents. It is **review compression**:
making a unit of work judgeable as trustworthy without anyone having to read
everything it contains. Every rule that follows serves that end. A rule that
stops serving it is wrong.

The method is agnostic to language, framework and tool. What it fixes is the shape
of the decomposition, who decides what, and what must be true before a commit
exists.

## 2. The tree

Work is decomposed into six levels. Each level decides less than the one above,
and this progressive reduction is the method's safety property: whoever works at
one level cannot renegotiate the level above.

```
Ideal      the complete solution, which will not be built
  │
MVP        the same solution without non-functional requirements. It is what will be built
  │
M#         Module, a feature that works without depending on the others
  │
D#         Step, a part of the module, coupled to its siblings
  │
T#         Task, a piece of code. One work session; the DV decides how many commits
  │
F0–F6      Phase, the layer the task is allowed to touch
```

Example of reading the full tree:

> A commissions system has the Computation module, `M03`. Inside it, a step
> handles the apportionment calculation, `M03.D02`. Inside the step, a task
> implements the rule for dividing by revenue center, `M03.D02.T04`, and declares
> that it will touch only from contract to exposure, `[F1–F3]`. Requiring a change
> to the interface, `F5`, stops the task and returns it to whoever defined it. It
> does not widen itself.

## 3. Ideal and MVP

**Ideal** is the complete solution to the problem situation that gave rise to the
project. Also referred to as MAX; it lives in `GRAND_PLAN.md`.

**MVP** is the same plan without any non-functional requirement, entirely
pragmatic. Also referred to as MIN; it lives in `MINIMUM_PLAN.md`.

The Ideal is never given to an agent as a target. It exists to make the MVP
defensible by contrast: without the Ideal written down, no one knows what was cut
or why. Handed to an agent as a target, it produces scope inflation with no
counterweight, because the agent has no cost model and no share of the
maintenance burden. The Ideal may be cited as justification; never pursued.

The MVP is the system's only termination condition. Each task ends on its own, and
none of them knows when the project is over. Only the human closes it, and it is
the MVP that says when. Without an MVP there is no completion, there is only
fatigue.

## 4. Module

A module is a feature that works without depending on the others. Independence is
not organizational convenience: it is the precondition for two agents working at
the same time without colliding. One workspace per module, one branch per module.

Two agents inside the same module is a false economy. They contest the same
contract vocabulary, and reconciling that costs more than the parallelism
yielded. A module large enough for two agents is, in fact, two modules that have
not yet been separated.

Completing a module means finishing all of its content: all steps closed and the
non-functional checklist clean. The effect is to release a new feature to
production. It is not a progress marker, it is delivery.

## 5. Step

Steps are parts of a module. Unlike modules, they need not work decoupled: they
carry the concepts that, added together, make the module functional.

A step may contain a non-functional requirement, such as frontend animation or a
backend utility, with no harm at all. What it cannot do is stay invisible: being a
condition for delivering the module, it is in the module's checklist, markable
and countable.

**Delivered is not closed.** A step with all tasks completed is ready for
sign-off. The gate is what closes it. Until the gate passes, the step counts as
open. A report that marks a step as done because the tasks are finished is
reporting engineering and calling it delivery.

## 6. Task

A task is pure code, with norms and conventions applied. It is the smallest
dispatchable unit.

**One task, one work session, one or more commits.** The DV decides how many commits a
task takes. What holds the mapping together is that the commit is the object of review:
every commit belongs to exactly one task and cites it, and no commit spans two tasks. A
commit that belongs to no task, or to two, detaches the granularity of review from the
granularity of the plan, and the plan stops describing the repository.

A reopened task is a new session, labelled as a reopening, with clean context and
an explicit declaration of what is being re-entered. It is not a continuation of
the previous context.

Every task has a state:

| State | Meaning | Counts toward progress |
|---|---|---|
| `active` | In progress or to do | Yes |
| `blocked` | Stopped by an external dependency | No |
| `revoked` | Cancelled by a recorded decision | No |

A revoked task is not a pending task. Counting it as pending contaminates every
sum above it.

## 7. Phase

Phases are not stations on an assembly line. Nothing leaves one phase and enters
the next. They are layers of depth of the system, each with an owner:

| F | Name | Owner | Contribute | Never |
|---|---|---|---|---|
| **F0** | Norm | Human + PO | QA (ambiguity), DA (measurability) | An agent authoring alone |
| **F1** | Contract | DV | DA (shape of `Ev`/`Cmd`), QA (testability) | PO deciding types |
| **F2** | Rule | DV | QA (coverage, before implementing) | PO, DA |
| **F3** | Exposure | DV | QA, DA | PO widening |
| **F4** | Consumption | DV | QA | — |
| **F5** | Surface | DV | QA, PO (acceptance) | DA |
| **F6** | Closure | PO decides, DV+QA+DA supply | — | An agent accepting itself |

A task declares a **span**, the range of phases it is allowed to touch.
`M03.D02.T04 [F1–F3]` may only work from contract to exposure. The span
determines which roles take part in that task.

There is no progress from F0 to F6. A task does not advance from phase to phase;
it is contained in the span it declared. Leaving the span is a containment
failure, not progress.

F0 is anchored in a human. An agent authorized to write norms writes the norm that
justifies the code it has already produced. Norms are the court of appeal and the
defendant does not compose the court. An agent may draft a norm and propose an
identifier; a human ratifies it before any rule cites it.

F6 is never self-accepted. Whoever produced the increment does not declare it
ready. The PO accepts, on the QA's risk opinion.

## 8. Identifiers

The code of any object comes from its position in the tree:

```
M04                  module 4
M04.D02              second step of module 4
M04.D02.T03          third task of that step
M04.D02.T03 [F1–F3]  the same task, with the declared span
```

Identifiers are derived, never typed. If the position changes, the code changes.
A hand-written code diverges from the tree, and from then on the plan stops
describing the repository.

## 9. Execution order

The tree says what belongs to what. It does not say what to do first.

If module `M01` is only ready once step `D03` of `M04` is resolved, `M04.D03.T*`
is handled so as to deliver `M01` as early as possible. Every task may declare
which module it unblocks, and the path to a delivery is assembled from those
declarations, not from the numbering.

The order changes over the course of the project, and that is expected. The gain
is not in the plan's immutability: it is that, once defined, whether altered
later or not, what remains is to follow the sequence and conclude topic by topic.

## 10. Roles

Four roles take part. They may be people or agents; the interface is the same.

| Acronym | Role | Answers for |
|---|---|---|
| **PO** | Product Owner | What is worth building and in what order |
| **DV** | Developer | How it works, and at what maintenance cost |
| **QA** | Quality Analyst | Whether it really works, and how it breaks |
| **DA** | Data Analyst | What the data support, and with what confidence |

`PO.md`, `DV.md`, `QA.md` and `DA.md` define identity, scope, input and output
contracts with acceptance condition, and anti-patterns of each role. They serve
directly as agent specification. Agent prompts written separately create a second
source of truth that diverges from the first.

## 11. Context isolation

Separating agents by role does not serve speed. It serves to make each role
unable to see what would corrupt its judgment.

| Agent | Receives | Cannot receive |
|---|---|---|
| PO | Norms, backlog, metrics, the QA's risk opinion | Implementation reasoning |
| DV | Story and acceptance criteria, `PHASES.md`, F3 manifest, previous code | The PO's internal debate on priority |
| QA | Acceptance criteria, the artifact, the diff, the manifest | The DV's reasoning or justification |
| DA | Business question and the associated decision, schema, event spec | The expected answer |

The QA line is the most loaded. A QA agent that reads the DV's explanation of why
the code is correct agrees with it. Agreement is the default failure mode of a
language model reviewing language model output. The QA receives only artifacts:
the diff, the tests, the criteria, the lint result. Never the narrative.

The DA line is the same failure in another form. An analysis told the expected
result finds that result.

From this follows the general rule: agents do not exchange reasoning, they
exchange artifacts. A manifest, a signature, a bug report, a test. Reasoning
transferred between agents is unverifiable and accumulates error silently; an
artifact can be checked.

## 12. Coordination

Someone, a person or a process, selects the module, sequences the tasks,
dispatches the agents, runs the gate and routes returns. This coordination does
not constitute a fifth role. It has no opinion on product, code, quality or data,
owns no phase and authors no artifact.

A coordination that starts issuing product judgment has become a role without
accountability: outside the contract tables, invisible to the checklist,
answering to no one.

## 13. Gate

The gate is the set of mechanical checks that runs when a task ends, before any
person or QA agent sees anything:

| Check | Verifies |
|---|---|
| **Rule A** | Legality of the declaration: what was declared is declarable at that point |
| **Rule B** | Direction of reference: nothing references a layer it should not |
| **Tests** | The suite passes, and a failing test preceded the rule change |
| **F3 manifest diff** | The exposed surface has not grown without declaration |

For a person, these rules prevent drift over time. For an agent, they are the
compression mechanism: a machine-verifiable claim that the output is where it says
it is, which removes from the human the largest category of review work.

Output that fails the gate is not reviewed, it is returned. A high return rate at
the gate is good and cheap, and indicates that the gate works.

## 14. The cycle of a task

```
                      MVP  (termination condition, in the human's hands)
                       │
       ┌───────────────┼───────────────┐
      M01             M02             M03      ← parallel, isolated workspaces
       │
   D01 D02 …                                   ← serial within the module
       │
   ┌───┴───┐
   │  T##  │                                   ← one task, one session, one or more commits
   └───┬───┘
  span [F1–F3]
       │
  PO → QA → DA → DV → QA → PO                  ← roles, exchanging only artifacts
       │
  GATE: Rule A, Rule B, tests, manifest diff
       │
  HUMAN REVIEW  ← the scarce resource
       │
  the commit(s)
       │
  the step closes when the gate of D## passes
       │
  the module is completed when all D## close → feature in production
```

**1 · Frame (PO).** Issues the story: problem, acceptance criteria, what is out of
scope, the declared span and the citation of the F0 norm it serves. Rejected if
the span is not declared or the norm is not cited.

**2 · Challenge (QA).** Reads the criteria before implementation and returns the
ambiguities. It is the cheapest defect removal in the cycle and the one most often
skipped. An ambiguity found here costs a sentence; found at the surface, it costs
an entire task.

**3 · Model (DA, when applicable).** When touching an event, a command or anything
measured, the DA specifies name, trigger, payload, types and mandatory or optional
status before the DV implements. Instrumentation added afterward produces data
without history, and data without history answers no question.

**4 · Build (DV).** Implements strictly within the span. A need to exceed the span
stops the task and returns it to the PO, with no silent widening. Span violation
is the main containment failure in agent-generated code.

**5 · Gate (machine).** The four checks of section 13. Failure returns to the DV
without consuming the attention of the QA or the human.

**6 · Verify (QA).** Artifacts only. Issues a risk opinion, not a verdict: open
defects, severity, and explicitly what was not covered. "Approved" is not QA
output; "approved with residual risk X" is.

**7 · Accept (PO).** Decides on the risk opinion. Accepting with known defects is a
legitimate decision, and recording it is the point.

**8 · Close.** Changelog, documentation, backlog adjustment, manifest change if the
exposed surface grew. Then the commit or commits.

## 15. The review packet

The human does not review the code. The human reviews the packet:

- the declared span against the span actually touched
- the gate result
- the F3 manifest diff, normally empty and noisy when it is not
- the QA's risk opinion
- the diff, read last and selectively

When the packet is trustworthy, most tasks are approved on the first four items.
That is the throughput mechanism.

When the packet stops being trustworthy, the response is to tighten the gate, not
to read more code. Reading more code does not scale, and agents produce faster
than anyone reads.

## 16. Task checklist

The checklist answers the question "what remains to complete this" without having
to open the code files. Whoever resumes interrupted work reads these marks and
finds where it stopped, whether a new person on the team or the next agent.

- [ ] The task cites an F0 norm ratified by a human
- [ ] Phase span declared before dispatch
- [ ] QA challenged the criteria before implementation
- [ ] DA specified the instrumentation before the DV · **conditional**
- [ ] Phases touched within the declared span
- [ ] Rule A and Rule B pass
- [ ] Tests pass, and a failing test preceded the rule change
- [ ] F3 manifest diff empty or explicitly declared · **conditional**
- [ ] QA risk opinion issued, naming what was not covered
- [ ] PO accepted, with known defects recorded
- [ ] Human reviewed the packet
- [ ] Every commit cites this task, and none spans another task

Each item takes one of three states: `pending`, `met` or `not applicable`.
The third is mandatory because two items are conditional. A task that does not
touch data will never have DA instrumentation and, counted out of twelve, would
never reach one hundred percent. **The denominator is the number of applicable
items.** Marking "not applicable" is a recorded decision, not an omission.

The resumption rules live in the project's guidelines folder (`Docs/.guidelines/` in the classic layout; `library/layouts.md` finds it on any layout). A norm, a convention or a
defect pattern that exists in `CHANGELOG.md` or `RESUMING.md` but did not reach
the canonical location is half written: that is where the next agent looks, and
where it does not find it.

## 17. Version

The version number is computed from the tree, never typed:

| Field | Derives from |
|---|---|
| **major** | There has been an official deployment to production |
| **minor** | Number of completed modules |
| **patch** | Number of steps with the gate closed |
| **+hash** | The measured revision |

The principle behind it: a number that appears in two places has a single origin.
A development dashboard and a customer report that disagree indicate that one of
the two types what it should compute.

## 18. Failure modes

| Failure | How it appears | Countermeasure |
|---|---|---|
| Span leakage | The diff touches phases outside the declared span | Gate check: declared against touched |
| Norm invention | A norm appears without human ratification | F0 requires a human signature |
| Sycophantic review | The QA approves everything | The QA does not receive the DV's reasoning; track the escape rate |
| Self-acceptance | Whoever produced it closes its own task | Closing requires a different role |
| Module contention | Two agents in the same contract vocabulary | One agent per module |
| Silent widening | The exposed surface grows inside another commit | Manifest diff in every packet |
| Context leakage | An agent cites information it never received | Isolated contexts; treat as a containment bug |
| Invented code | A typed identifier diverges from the tree | Identifiers derived from position |
| Falsely closed step | Completed tasks counted as closure | Closing requires the gate, not just the tasks |
| Progress by phase | A task reported as advancing from F0 to F6 | Phase is depth; measure by the checklist |
| Review debt | The queue of merged and unreviewed work grows | Stop dispatching. The queue is the ceiling |
| Plan drift | Commits stop corresponding to tasks | One session per task; every commit cites its task; no commit spans tasks |

The last two kill the system. The rest are noisy and, for that reason,
survivable.

## 19. Health metrics

- **Review latency**, from dispatch to the human decision. The real throughput
  number.
- **Merged and unreviewed**, which must tend to zero. When rising, dispatch less.
- **Span violation rate**: tasks that touched undeclared phases.
- **QA escape rate**: defects that passed through the QA and failed in human
  review or in production. When rising, the QA agent has become sycophantic.
- **Gate return rate**, whose high value indicates the gate is working.
- **Tasks per module before integration**: long sequences hide divergence.
- **Norms drafted by agents against norms ratified by humans**. A rising ratio
  indicates the court of appeal being packed.

The first two deserve the same prominence as the test count. They are what lock up
the system; the test count describes what has already passed.

## 20. Anti-patterns

- Giving the Ideal to an agent as a target
- Parallelizing inside a module
- Letting an agent author and cite its own norm
- Passing reasoning between agents instead of artifacts
- Showing the QA the implementer's justification
- Telling the DA the expected result
- A coordination that develops product opinion
- A QA verdict of "approved" with no statement of residual risk
- Widening the exposed surface as a side effect
- Increasing the number of agents while review latency rises
- Reopening a task by continuing the previous context
- Writing agent prompts that duplicate the role documents
- Typing an identifier that the tree already determines
- Counting a revoked or blocked task as pending
- Declaring a step closed before the gate passes

## 21. Adoption order

Adoption starts with the gate, not with the agent topology.

1. **Gate first, no agents.** Rule A, Rule B, manifest diff and span check,
   running by hand if necessary. An untrustworthy gate makes agents produce
   garbage faster.
2. **One role.** Only the DV, with the human covering PO, QA and DA. You learn
   where span leakage happens in that codebase.
3. **QA, isolated.** Artifacts only. An escape rate at zero for several tasks in a
   row is grounds for suspecting sycophancy, not for celebration.
4. **DA**, when retroactive instrumentation starts to hurt.
5. **Parallel modules**, last, and only with review latency stable in a single
   module.

Each stage sustains its metrics before the next. The system's ceiling is review
capacity at all of them, and adding agents before the gate is strict only raises
the queue.

## 22. Glossary

| Term | Definition |
|---|---|
| **Ideal** (MAX) | The complete solution to the originating problem. It will not be built |
| **MVP** (MIN) | The Ideal without non-functional requirements. It is what will be built |
| **Module** (`M#`) | Feature that works without depending on the others. Unit of parallelism |
| **Step** (`D#`) | Part of the module, coupled to its siblings. Closes through the gate |
| **Task** (`T#`) | A piece of code. One session; one or more commits, each citing the task |
| **Phase** (`F0`–`F6`) | Layer of depth the task may touch |
| **Span** | The range of phases the task declared it would touch |
| **Gate** | Rule A, Rule B, tests and manifest diff. Runs before the human |
| **Packet** | The summary the human reviews in place of the code |
| **Risk opinion** | QA output: open defects and what was not covered |
| **F3 manifest** | The list of what the module exposes to the outside |
| **Delivered** | All of the step's tasks completed. Not yet closed |
| **Closed** | Delivered and with the gate approved |
| **Completed** | Module with all steps closed. Goes to production |
