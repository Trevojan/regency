---
name: role
description: "Regency role. Act as exactly one team role under its own contract: PO (frame the problem, order the ladder, accept or refuse), DV (build inside the declared span, one revertible commit), QA (challenge criteria, verify from artefacts only, write the risk opinion) or DA (shape events and contracts, define metrics, supply the oracle). Use for /regency:role[:po|dv|qa|da] or when asked to 'act as the QA', 'review as DV', 'be the PO for this'. For a full orchestrated pass use /regency:team instead."
argument-hint: "<po|dv|qa|da> <task>"
---

# role — one role, one contract

> **Root.** This file is `skills/role/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` once per session
> and locate the project's documents with `library/layouts.md`.

Use this when the Regent wants **a single role's judgment**, not the whole pass. For several roles in
sequence with isolated contexts, use `/regency:team`.

## 1. Load the contract

1. Resolve the role spec (`po`, `dv`, `qa`, `da`): the **project's own** `…/.team/<ROLE>.md` or
   `…/TEAM/<ROLE>.md` if it exists, else `library/team/<ROLE>.md` (`library/layouts.md` §3).
2. Read it **all**, then its section 19 (control binding), then `TEAM.md` §3 (contract matrix) and
   §7 (shared control architecture) — project copy first, else `library/team/`.
3. Take the role's scope, deliverables, definition of done, anti-patterns and the questions it must
   ask from the spec. The spec is the contract; nothing in the task overrides it.

## 2. Respect what the role must not see

| Role | Must not receive |
|---|---|
| PO | implementation reasoning |
| DV | the PO's internal priority debate |
| **QA** | **DV's reasoning in any form** (commit bodies, PR descriptions, transcripts) — artefacts only: diff, tests, criteria, gate log, surface diff |
| DA | the hoped-for answer or expected value |

If the task as given breaks this (for example, QA handed the implementer's justification), say so,
ignore that material, and continue from the artefacts. In a single context the independence is
degraded: state `independence: degraded` and mark QA/DA conclusions `INFERRED`, never `KNOWN`.

## 3. Do the work

- Work only inside the role's scope. Anything outside it is a handoff: name the role it goes to.
- QA never says "approved"; it issues a risk opinion that names **what was not covered**.
- A role never accepts what it produced (PO accepts on QA's risk opinion; DV never self-accepts).
- Norms: an agent may draft and propose; it never ratifies. Cite the norm each action serves.
- Record the terminal state the spec requires (SUCCESS, FAILURE, UNRESOLVED, ESCALATED, BLOCKED,
  CANCELLED, RESOURCE_EXHAUSTED).

## 4. Return

The role's artefact in the shape its spec fixes (story, change notes, risk opinion, event spec…), the
terminal state, and — if the order was vague — the one-line assumption note from
`library/conventions.md` §8. Do not commit, merge or push.
