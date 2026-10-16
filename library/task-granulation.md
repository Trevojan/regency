# Task granulation — how the Regent breaks a solution down

The Regent's protocol for decomposing work. It fixes the shape of the decomposition, what is decoupled from
what, and what a task is. `library/team/ORCHESTRATION.md` v3.0 supplies the rest of the method (roles, gate,
review packet); this file supplies the **vocabulary and the granularity** it assumes. Grammar of every id:
`library/ids.md`.

## The four levels

The levels are named on a **Big-O** basis, `O4` the largest down to `O1` the smallest.

| Level | Name | Id | What it is |
|---|---|---|---|
| **O4** | Solution | none | the whole solution. It gets **no nickname** and is not cited after the Briefing and the project's title |
| **O3** | Module | `M##` | what holds the **features** of a solution, from scratch in the MVP up to the most valuable and resourceful deliverable. Modules are **decoupled** from one another |
| **O2** | Step (*degrau*) of the development ladder | `D##` | holds the **concepts** needed to build one module. Steps are **dependent** on their sibling steps |
| **O1** | Task | `T##` | a task in the sense of a development team: **one code file** (`.py`, `.cs`, `.ts`, …), a coupled part of its step |

Read downward: a task is a coupled part of a step, a step a dependent part of a module, a module a decoupled
feature of the solution. Ids are derived from position and never typed: `M03.D02.T04 [F1–F3]`.

## Seven phases, one pattern

Every task is conducted through **seven phases, F0 to F6**: fixed, numbered and bound to the project's
Business Rules. **Each phase follows the same pattern.** (F0 Norm, F1 Contract, F2 Rule, F3 Exposure,
F4 Consumption, F5 Surface, F6 Closure: the phases of `library/team/ORCHESTRATION.md` §7.) A task declares
the span it may touch, for example `[F1–F3]`, and stays inside it.

## Rules that follow

1. **Granulate until a task is one file.** A work item that touches several files is not yet a task: split it
   into one task per file, or recognise it as the step-level concept it really is. *(Read from "a `T##` means
   a file"; the Regent confirms the first time a project's items span files.)*
2. **Decoupling stops at the module.** A failing step can corrupt the flow and crash the client, the server,
   or both. So a step is never left in a state that does not compile or build: **every commit builds**.
   Strongly typed languages catch most of this at compile time; JavaScript and related languages do not, so
   type-check, lint and run the tests before the commit, and treat a path that fails only at run time as a defect.
3. **Do not invent levels.** A project that documents only steps (for example ladder parts written as `LADDER_PLAN_PART_X`) has
   an implicit module level: do not make up module ids. Quote the project's own term and write
   `tree_mapping` in the declaration.
4. **A task is one work session and may have several commits.** The DV decides how many; every commit cites its task and none spans two tasks.
5. **Never cite the solution by a nickname.** O4 appears in the Briefing and as the project's title, nowhere else.

## Where this is used

- `/regency:order:dispatch` classifies an order at O3, O2 or O1 (O4 is never a target).
- `/regency:team` reads ids as `M##.D##.T##`, checks the declared span and refuses to count a step closed before its gate.
- `library/team/references/vocabulary-map.md` maps a project's own words onto these levels.
