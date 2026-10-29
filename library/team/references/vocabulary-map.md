# Vocabulary map — ORCHESTRATION.md v3.0 onto a project document set

`ORCHESTRATION.md` v3.0 speaks, for the tree itself, the vocabulary the repositories already use
(Ideal and MVP, module `M#`, step `D#`, task `T#`, phases `F0`–`F6`). Three things still need a
translation: **what a project calls each level**, **what Rule A, Rule B and the F3 manifest are in
that project**, and **the places where two documents disagree**. This file records them. Every mapping
carries an epistemic status (TEAM §7.3): a `SUPPORTED` mapping traces to a document; an `INFERRED` one
is this skill's reading and **must** be confirmed before it is treated as a norm.

The mapping below is written for the classic Orbital layout and the dotted layout
(`library/layouts.md` §2). Where a project defines its own id grammar, **the project's grammar is
authoritative** and only the *role* of each term carries over.

## 1. Terms

| ORCHESTRATION v3.0 term | In a project | Status | Basis |
|---|---|---|---|
| Ideal (MAX) | `GRAND_PLAN.md` | SUPPORTED | ORCH §3 names the file |
| MVP (MIN) | `MINIMUM_PLAN.md` | SUPPORTED | ORCH §3 names the file; termination condition of the system |
| Module `M#` (level O3) | classic: `M<n>` and `LADDER_PLAN_M_<n>.md`; dotted: implicit unless the project names modules | SUPPORTED | `library/task-granulation.md`: holds the features, decoupled from other modules |
| Step `S##` (level O2, *degrau*) | dotted: a ladder part, `LADDER_PLAN_PART_X`; classic: no equivalent | SUPPORTED | Regent, 2026-10-05: the step of the development ladder, holds the concepts to build a module, coupled to sibling steps |
| Task `T##` (level O1) | classic `T<nn>`; dotted: a backlog item (`B-…`), see C1 | SUPPORTED | Regent, 2026-10-05: one code file, a coupled part of its step; one session, one or more commits |
| Phase `F0`–`F6` | `F0`–`F6` | SUPPORTED | identical names and order (classic `AR20`) |
| Span `[F1–F3]` | classic: the `F<k>` in `M<n>.F<k>.T<nn>`, read as a one-phase span; dotted: declared in the item | INFERRED | the range of phases a task may touch |
| `PHASES.md` | classic `DECISIONS/ARCHITECTURE.md` §4 (`AR20`, `AR21`); dotted: the phase table in the architecture norms | INFERRED | `PHASES.md` itself may not exist |
| Rule A — declaration legality | classic `AR10`–`AR12`; dotted: the project's own path/anchor/format gates | INFERRED | "is it declared where and as what it claims to be" |
| Rule B — reference direction | classic `AR3`–`AR7` (the inward arrow); dotted: the layering norm | INFERRED | "does it reference only what it may" |
| F3 manifest | classic `SOURCES/API_SURFACE.md`; dotted `.sources/API_ENDPOINTS.md` | INFERRED | the outward surface F3 publishes |
| `Ev` / `Cmd` | events and commands in the data model and the surface document | INFERRED | no such prefixes exist in the id grammar |
| Task states `active` / `blocked` / `revoked` (older projects: `ativa` / `bloqueada` / `revogada`, read as input) | the item's status in the checklist or backlog | INFERRED | ORCH §6; only `active` counts as pending progress |
| Delivered / closed / concluded | all tasks of a step done / step with the gate passed / module with every step closed | SUPPORTED | ORCH §5, §22 |
| Review packet | the five-item packet in `skills/team/SKILL.md`, Step 7 | SUPPORTED | ORCH §15 |
| Human | the human operator, RA escalation L4 | SUPPORTED | TEAM §6, §7.8 |
| Risk opinion | the same term | SUPPORTED | TEAM §6 |

## 2. Conflicts, and the default this skill applies

Each conflict is resolved **conservatively** until the human decides otherwise: the more restrictive
reading applies, and the conflict is listed in `defects` of any pass it affects.

**C1 — the word "step" (degrau). Closed by the Regent on 2026-10-05** (`library/task-granulation.md`).
A *step* `S##` (level O2) is the *degrau* of the development ladder: it holds the concepts that build one
module and is coupled to its sibling steps. Ladder parts written as `LADDER_PLAN_PART_X` are steps.
A *module* `M##` (level O3) holds features and is decoupled from other modules; a *task* `T##` (level O1) is
one code file. What stays open is only granularity: a backlog item that touches several files is not yet a task
(see the rules in `library/task-granulation.md`). *Default:* quote the project's own term and write
`tree_mapping` in the declaration; do not invent module ids for a project that documents only steps.

**C2 — parallel work.**
ORCH v3.0 §4 parallelises across modules only; §21 puts it last in the adoption order, and only with
review latency stable at one module. *Default:* no parallel dispatch. It is enabled at adoption stage 5,
and only across units the plan shows to be independent.

**C3 — the developer's change notes versus withholding the developer's reasoning.**
TEAM §3 has the DV hand QA "notes on what changed"; ORCH §11 says QA receives only artefacts (the diff,
the tests, the criteria, the lint result) and never the narrative. *Default:* change notes are allowed in a
fixed shape that has **no field for justification** (touched paths, touched phases, rollback path,
surface change yes/no, new tests). See `packets.md`. The coordination does not edit the notes; notes that
argue for the change are returned to DV mechanically.

**C4 — who ratifies a norm.** *Closed by ORCH v3.0 §7:* F0 is human-anchored; an agent may draft a norm and
propose an id, and a human ratifies before any rule cites it. Consistent with TEAM §7.12.

**C5 — adoption stage.**
ORCH v3.0 §21 defines five stages, but no document records which one the team is at. *Default:*
`UNRESOLVED` until recorded in the decisions register. The skill asks once, closed, and never assumes.

**C6 — where ORCHESTRATION.md lives.**
The project's own copy wins; otherwise `library/team/ORCHESTRATION.md`. If neither exists, report it as a
defect, not as a path to search for.

**C7 — "one phase" is no longer the rule.**
The earlier map (written for ORCH v1.0) forced a task to span exactly one phase. ORCH v3.0 §7 says a task
declares a **span**, a range of phases, and its work must stay inside it. *Default:* a range is legal; the
classic `M<n>.F<k>.T<nn>` is read as the one-phase span `[F<k>]`. A unit that declares no span, or touches
a phase outside it, goes back to the PO (check 5).

## 3. Rule A and Rule B, as gate checks

Until the mappings above are confirmed, the gate runs these checks. Any part with no automated check is run
by hand and declared `manual` in the pass.

| Check | Question | Norms (classic layout) |
|---|---|---|
| Rule A | does each touched file sit in the concept folder and under the prefix the type table assigns it? | `AR10`, `AR11`, `AR12` |
| Rule B | does every new reference point inward — `_PANEL → _DRIVE → _CORE → _ENGINE`? | `AR3`–`AR7` |
| Span | are the phases touched a subset of the span declared? | ORCH §7 |
| Tests | did a failing test precede the change, and is the inherited suite green, project by project? | DV §10, QA §10 |
| Surface diff | did the F3 manifest change, and was that declared? | ORCH §15 |
| Project creation | was any project created without the confirmation `AR9` requires? | `AR9` |

In a dotted-layout project the "Norms" column is the project's own equivalents; read
`library/layouts.md` §2 and report the mapping you used.
