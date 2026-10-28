---
name: order
description: "Regency Orders. Fill and emit one of the four standard Orders from its template: germinate (grow the path to a goal as a tree), handoff (close a stretch of work and hand its state over), dispatch (hear an order over the D3/D2/D1 hierarchy, classify it, emit the dispatch manifest) and resume (reopen a project mid-work from its shortcuts index only); or lazy (run an Emission's Orders, skipping those that need the Regent). Use for /regency:order[:germinate|handoff|dispatch|resume|lazy], 'prepare a handoff', 'retomada', 'resume the project', 'grow the plan', 'classify this order', 'run EMS-011'."
argument-hint: "<germinate|handoff|dispatch|resume> [material] | lazy [EMS-id]"
---

# order — four templates, one procedure

> **Root.** This file is `skills/order/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` once per session
> and locate the project's documents with `library/layouts.md`.

## 1. Choose and load

The first argument names the kind (`germinate`, `handoff`, `dispatch`, `resume`). If it does not, ask
(pop-up) which. Then read `library/orders/README.md` (how to read the XML, slot filling, numbering)
and the template `library/orders/<kind>.xml`. `lazy` fills no template: it runs the Orders an Emission
already carries (§3, *lazy*).

## 2. Fill

Fill the slots as `library/orders/README.md` §"Filling slots" says: from project facts with the
source cited; pop-up for anything only the Regent can answer (one pop-up for all, blockers first);
never invent; leftovers become `⟨unresolved⟩` and enter the open-questions queue.

## 3. By kind

### germinate — the tree

Output sections, in order: **roots** (the problem, stated as the problem the goal closes, not as the
thing to build) → **trunk** (the ordered effort) → **branches** (what it leans on, each named) →
**limits** (what is out of reach and the guarantees the result must not break) → **locks** (what no
step may bend; always including: no self-attested gate, no acceptance criterion rewritten so the work
passes) → **fruit** (the end state as an observable condition for someone who did not do the work) →
**assumption** (one assumption that can be knocked down in one line, and what happens to the tree if
it is). Then validate the tree against the criterion in the template. Show it in chat; save it
(`.plan/`, or as an Order) only if asked.

### handoff — close the stretch

The result is **opening context for the next session, never an order**. Sections: **state** (where the
work is, not where it should be: version/checkpoint and branch, plus the one standing command that
decides whether the state is true and what it exits with; the last completed task to resume from) →
**root-cause** (the one shape behind the blockers, if there is one; one named case per line; the
lesson stated so it survives outside this stretch) → **closed** (each item observable by someone who
did not do the work, stated as behaviour that changed, not as files that moved) → **measured**
(figures with their method) → **open** (decisions only the Regent can take, and what each blocks;
unverified assumptions) → **next** (the next step in dependency order, no detail, plus what continues
without waiting on the open questions) → **method** (a rule that held, written so it binds the next
agent).

Where it goes — follow the project's documented convention. If it has none: **update the state file
(`.plan/RESUMING.md` or equivalent) and the four lines of the shortcuts index, and the files under
`.shortcuts/` and `.shortcuts/.virtual/` that exist to get the next agent to the line faster** (they
are written for the agent, not for the Regent to read). Do not create a new loose file.

**The ledger is part of every handoff** (`.shortcuts/.virtual/ongoing.json`, model in
`library/virtualpath.md` §3): reconcile it with `python scripts/vp.py trace` first, then make it true —
remove `done` items, give each `ongoing` item its evidence and `next`, give each `blocked` item its
`blocked_by`, mark finished work `review`, set `updated`. The handoff's *state*, *open* and *next*
sections must agree with the ledger, and point to it instead of repeating it. Never commit; offer
`/regency:arrange-cycle-commit`.

### dispatch — hear, classify, emit

Hierarchy (`library/task-granulation.md`): **D4** = the whole solution (no id, never a target);
**D3** = module, what holds the features (`M##`, fragments into D2, never worked directly); **D2** = step,
the *degrau* of the development ladder (`D##`; holds the concepts that build one D3; owns its file; acts as
checkpoint); **D1** = task (`T##`, atomic, one code file; the unit of work and of resume). Read where the breakdown already lives and **never re-derive or
re-fragment it**. Classify the order's level, then emit the manifest:

```yaml
order: ORD-#### | ad-hoc
level: D3 | D2 | D1
d3: <the problem it closes, as a problem>
d2: [ <concepts in dependency order, one line each> ]
d1: [ { id: <id>, file: <path>, state: done|open } ]    # existing tasks named by id and file
route: { pass: "/regency:team <unit>" }                  # or { role: po|dv|qa|da }
resume_from: <last completed D1>                         # never from the top of the tree
open_questions: [ ]
```

The manifest is the hand-off to `/regency:team`; do not start the pass yourself unless asked.

### resume — from the index only

**First peek, before the index:** `python scripts/vp.py ongoing`, then `python scripts/vp.py trace`, and
reconcile (ghosts, orphan work, stale claims — `library/conventions.md` §10). It is a few lines and it
tells you what is ongoing and what is only backlog. Then read the project's entry index
(`.shortcuts/README.md` or equivalent) **whole**; it stays the one document read whole. Decipher only the previous step, the current one and the next; reach everything else by
shortcut. If an expected path does not exist: name every missing path and ask permission to create
exactly those — create nothing beyond them, and never route a fact elsewhere because its path is
missing. Output: **ongoing / backlog** (from the ledger, reconciled with the traces), **version**,
**suite** (the command, and whether it is green — run it only if cheap and read-only), **last
milestone** (the last completed D1), **next** — filled, never inferred — then offer `/regency:proceed`.

### lazy — run an Emission, skip what needs the Regent

A speed mode: read `library/team/SPEED_MODES.md` §1–§3 first; it holds the doctrine this list obeys.

1. **Find the Emission**: the `EMS-###` named in the arguments, else the one the project marks open, under
   `.orders/` (§3 there). None, or two open: stop with one line naming what you probed.
2. **First peek**: `python scripts/vp.py ongoing` and `python scripts/vp.py trace`, as for any return to a
   repository; the run writes itself into the ledger as `pass:lazy-<EMS-id>`.
3. **Each Order, in sequence**: one that depends on a skipped or blocked Order joins the blocked chain;
   one that needs the Regent is **skipped, never guessed**, logged as
   `SKIP <ORD-id> · <question> · (a) <answer> · (b) <answer>` in the open-questions queue (blockers first);
   one whose next step is destructive-class stops the run; every other one runs through its executor (a
   `/regency:team` pass ends at its review packet) and decides on its own wherever the conventions or the
   Emission settle the matter.
4. **Stop** at the end of the Emission, at a destructive-class action, or when every remaining Order is
   blocked. Make the ledger true; commit, merge and push nothing.
5. **Report once**, in the shape of `library/team/SPEED_MODES.md` §3: done / skipped (questions grouped,
   two candidates each) / blocked chain, and why it stopped. Then offer `/regency:arrange-cycle-commit`.

## 4. Opening an Order in the project

If the Regent wants the filled template commissioned as a contract: write it as
`…/.orders/ORD-####/ORD-####.xml` (number rules in `library/orders/README.md`), update the project's
`.orders/README.md` table (one open Order only), and stop. An agent proposes an Order; the Regent opens it.

## Boundaries

No invented slot values, no second open Order, no amendment of an open Order, no commit, no
re-fragmenting a breakdown that exists, no reading the whole repository to "get context". `lazy` opens no
Order and no Emission, and answers none of the Regent's questions on the Regent's behalf.
