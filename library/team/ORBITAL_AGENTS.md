# AGENTS — entry point

This is the **Orbital** template: a scaffold that turns a client's problem statement into a
ladder of modules that runs from nothing to a deliverable.

The solution ships empty on purpose. Projects arrive when a briefing asks for them.

> **Everything referenced in this document set exists inside this repository.** There is no
> canonical copy elsewhere, no home-directory documentation, no external hub. If a document
> points somewhere that does not resolve, that is a defect — report it rather than
> improvising around it.

---

## Start here

**Starting a new project?** Run `PROTOCOL.md` from S0. Do not read ahead and do not design
anything before the briefing is complete — that is the one rule the whole scaffold rests
on.

**Working inside a project already underway?** Read in this order:

1. `DECISIONS/ARCHITECTURE.md` — conventions and the `AR#` norms
2. `SOURCES/BRIEFING.md` — the problem everything descends from
3. `PLAN/GRAND_PLAN.md` — the ceiling of coherence
4. `PLAN/MINIMUM_PLAN.md` — the path to the MVP
5. `PLAN/LADDER_PLAN_M_<current>.md` — the module in flight
6. `DECISIONS/BUSINESS_RULES.md` — the `BR#` norms
7. `DECISIONS/DECISIONS.md` — the `DC#` register; **never contradict an accepted one
   without writing the one that supersedes it**
8. `SOURCES/DATA_MODEL.md` and `SOURCES/API_SURFACE.md` — the shapes in play
9. `DECISIONS/TESTS.md` and `DECISIONS/DEPENDENCIES.md` — how it is proven and what it needs

`TEAM/` is read when the work involves planning, hand-off or deciding who owns a call.

**Acting as a role?** Read `TEAM/TEAM.md` §7, then section 19 of that role's file. They bind
`TEAM/REINFORCED_AGENT.md` — the control architecture every role operates under — to this
repository. The generic spec itself is read when a binding is unclear, and is never edited to
fit a role.

---

## The document set

Divided by **nature**, not by subject. The distinction matters: an out-of-date fact is a
documentation defect, an out-of-date rule is a process defect, and the two are repaired
differently.

| Folder | Nature | Holds |
|---|---|---|
| `SOURCES/` | **Facts** — what the system is | `BRIEFING`, `DATA_MODEL`, `API_SURFACE`, `CHANGELOG` |
| `DECISIONS/` | **Rules** — what may and may not | `ARCHITECTURE` (`AR#`), `DECISIONS` (`DC#`), `BUSINESS_RULES` (`BR#`), `TESTS`, `DEPENDENCIES` |
| `TEAM/` | **Roles** — who decides what | `TEAM`, `REINFORCED_AGENT`, `PO`, `DV`, `QA`, `DA` |
| `PLAN/` | **The ladder** — what gets built, in what order | `PLANNING`, `GRAND_PLAN`, `MINIMUM_PLAN`, `BACKLOG`, `LADDER_PLAN_M_*`, `CHECKLIST`, `TRACE`, `GATE_*` |

Plus `PROTOCOL.md` at the root of the set: the algorithm that fills all of it.

**This is the only canonical location.** Per-app `Docs/` folders are scratch space, are
gitignored, and are never published. Duplicating this set into app folders is what produced
the defect that `DC1` records.

---

## The id grammar

| Prefix | Means | Lives in |
|---|---|---|
| `DC<n>` | Decision — architecture, limits, duties | `DECISIONS/DECISIONS.md` |
| `AR<n>` | Architecture rule | `DECISIONS/ARCHITECTURE.md` |
| `BR<n>` | Business rule | `DECISIONS/BUSINESS_RULES.md` |
| `D1`–`D3` | Difficulty — Simple, Dense, Very dense | a scale, not a register |
| `B<n>` | Backlog item | `PLAN/BACKLOG.md` |
| `M<n>` | Module — one step of the ladder | `PLAN/LADDER_PLAN_M_<n>.md` |
| `F0`–`F6` | Phase — fixed, in every module | inside a module |
| `T<nn>` | Task — one commit | inside a phase |

A **norm** is any `DC<n>`, `AR<n>` or `BR<n>`. Every task cites one.
A fully-qualified task looks like **`M2.F3.T04`** and appears in the checklist, the trace
and the commit subject.

Normative force in prose uses **MUST**, **MUST NOT**, **SHOULD**, **MAY**, **NOTE**. The
bold keyword is the norm; the same word in ordinary prose is not.

---

## Commands

The solution is empty until a project is added, so `dotnet build` warns that it found
nothing to restore. That warning is expected and disappears with the first project.

```bash
dotnet build _ORBITAL.slnx
```

```bash
dotnet sln _ORBITAL.slnx list
```

Adding a project — only after the confirmation `AR9` requires, as a task inside `M1.F1`:

```bash
dotnet new classlib -o <APP>_ORBITAL/<CONCEPT>_<DOMAIN>
```

```bash
dotnet sln _ORBITAL.slnx add <APP>_ORBITAL/<CONCEPT>_<DOMAIN>
```

Tests run **project by project**, never through the solution, so that a project with a
pre-build step cannot drag an unrelated toolchain into the test run:

```bash
dotnet test <APP>_ORBITAL/<CONCEPT>_PROBE
```

---

## Rules that do not bend

1. **No project is created without explicit confirmation** — `AR9`. Complexity that looks
   like it needs one is planned, presented, and only then built.
2. **Nothing is invented silently** — `PROTOCOL.md`. Every derived fact traces to a briefing
   field, a recorded answer, or a norm.
3. **Documents before code.** A business rule changes in `BUSINESS_RULES.md` first, then the
   test goes red, then the service goes green, then the changelog.
4. **Never contradict an accepted `DC#`** without writing the decision that supersedes it.
5. **A task cites a norm and names its test**, or it is not ready to start.
6. **A module in execution does not change scope.** New requests become backlog items and
   are decided at the next module's opening.

---

## Agent working files

`CLAUDE.md` and `AGENTS.md` at the repository **root** are gitignored and stay local — they
are personal working setup, not published content. This file, at
`Docs/.guidelines/AGENTS.md`, is the published one and is tracked.

After cloning, point your local root `CLAUDE.md` here. One line is enough:

```markdown
Read `Docs/.guidelines/AGENTS.md` before acting.
```
