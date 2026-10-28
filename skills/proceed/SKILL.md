---
name: proceed
description: "Regency proceed. Work the whole queue: keep taking the next task, queue every non-blocking doubt, and stop only at a real blocker or an empty queue. Never commits, merges or pushes. Use for /regency:proceed, or when the Regent says prossiga, siga em frente, continue, vá em frente, bora, 'keep going', 'resume from where it stopped'."
argument-hint: "[scope or queue pointer]"
disable-model-invocation: true
---

# proceed — the whole queue

> **Root.** This file is `skills/proceed/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` (once per
> session) and locate the project's documents with `library/layouts.md`.

"Proceed" means: **work the queue until a blocker or until it is empty** — not one task.

## 0. First peek — the work ledger

Before anything else, see what is already going on: `python scripts/vp.py ongoing`, then
`python scripts/vp.py trace`, then reconcile as `library/conventions.md` §10 says (ghosts, orphan work,
stale claims go to the Regent as questions). Never start a `backlog` item just because it is free: the
queue decides what moves from `backlog` to `ongoing`. If the project keeps no ledger, say so once and
carry on; create one only with the Regent's yes.

## 1. Find the queue (never invent one)

In this order, first hit wins, and name which source you used:

1. the argument, if it points at a document or a list;
2. the project's state file (`.plan/RESUMING.md`, or the entry index's "next");
3. the next unchecked items of the checklist for the module/step in flight;
4. the open Order, if exactly one is open;
5. nothing found → say so in one line and ask (pop-up) where the queue is. Do not improvise work.

Read only the previous step, the current one and the next (the index → the state file → the
cited documents). Never reconstruct the project by reading the repository from the top.

## 2. The loop

For each item, in order:

1. **Check the gate before touching anything.** An item that needs a ratified norm, a signed gate
   or an answer that is not there is a blocker (§3); skip around it, do not wait for it.
2. **Do the item** inside its declared scope. If the project uses the team model, run it as a
   pass with `/regency:team <unit>` instead of doing the build yourself; stop the loop on `HOLD`,
   `ESCALATE` or `STOP`.
3. **Verify** with the project's own check (the command in the entry document). Red → fix within
   scope, once; red again → treat as a blocker.
4. **Record** what you decided and what you assumed in the project's state file, as you go, and keep
   the ledger true: the item goes `ongoing` (with evidence in `where`) when you start it, its `next`
   is refreshed at each boundary, and it ends `review` — never `done` — when you finish it.
5. Take the next item.

Do **not** commit, merge or push. Leave the work in the tree; `/regency:arrange-cycle-commit`
does the commits when the Regent asks.

## 3. Doubts and blockers

- A doubt that does not block → add it to the project's open-questions queue
  ("Open, waiting for the Regent" in `.plan/README.md`, or the project's equivalent), and keep going with an explicit assumption.
- A **blocker** (a decision only the Regent can take, a missing ratified norm, a failing gate you
  cannot fix in scope, work that would leave your scope or touch cloud/production/shared data)
  → add it to the queue **first in line**, then route around everything it touches and continue with
  what is still free.
- **Reversing a documented decision** (an accepted ADR, a business rule, a stated scope) is never
  a queue item: stop and ask now with a pop-up, offering the reversal as one explicit option.
- Stop for good only when: the queue is empty; every remaining item is behind a blocker; the
  review queue is full (`HOLD`); or an escalation is open.

## 4. When you stop — one pop-up, then the report

If there are open questions, ask **all of them at once**, blockers first, in a single pop-up
(2+ options each, free text allowed; read the marked option **and** the free text). Record the answers
in the project docs with the date, newest marked as in force.

Before reporting, make the ledger true: every item you touched has the right state, a blocked one
names `blocked_by`, and `updated` is set. Then report in the status format of
`library/conventions.md` §8:

```text
Done      <n>/<total> (<pct>%)   – item · item · item
Left      <n>/<total> (<pct>%)   – item · item
Blocked   <n>                    – item → what unblocks it (who decides)
Next      the single next step
Assumed X because the order did not say Y. Next time: <rewritten order>.   ← only if you assumed
```

## Boundaries

This skill never commits, merges or pushes; never runs cloud or production commands; never edits
files outside the project's scope; never widens a declared span; never ratifies a norm it wrote.
