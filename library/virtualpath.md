# Virtual paths — the lineage between norms and code

## 1. The problem

Most projects link code to norms in **one direction**: a source file cites `§layout-stable`, and the
norm has no idea who obeys it. When the code changes, the norm silently rots. A virtual-path registry
closes the loop: each **slice** of a norm declares, once, which code it governs, so a tool (and an
agent) can go from a file to its rules, from a rule to its files, and notice when a rule has aged.
This is also called *context lineage*, *reverse traceability* or *documentation impact radius*.

Tool: `scripts/vp.py` (read-only). Procedure: `skills/virtualpath/SKILL.md`.

## 2. The model (as implemented in the reference project)

One **global manifest**, one entry per slice (not one per Order: Orders are few and the norms are many
and stable):

```json
{ "virtual_context": [
  { "virtual_path": ".decisions/ARCHITECTURE.md#layout-stable",
    "refers_to": ["src/Pages/A.razor", "src/Pages/B.razor"],
    "selector_type": "markdown_anchor",
    "on_mutation": "mark_stale" } ] }
```

| Field | Meaning |
|---|---|
| `virtual_path` | the **slice**, not the file: `FILE.md#anchor`, relative to the guidelines root |
| `refers_to` | the code the slice governs — a **list**, relative to the repository root (one norm often governs many files) |
| `selector_type` | how the anchor is found: `markdown_anchor` (a heading carrying `§name`, or a heading whose whole text is the name), `glyph_block` (`[block'name'`), `ledger_row` (a table row by the bold label of its first cell; a paid row may be struck through) |
| `on_mutation` | what happens to the slice when a target changes: `mark_stale` or `lock` |

Rules that make it trustworthy:

- **Anchors are exact.** A prefix citation does not resolve. A heading without `§` is cited by its
  whole text, parentheses and slashes included.
- **A heading carries no state.** A checkbox or counter in a heading would kill every citation the day
  the right thing happens; state lives on the line below.
- **When an anchor exists in several files, the slice is the one under the guidelines root.**
- **The index points; it never copies.** The manifest holds locations, not content.

`on_mutation` values:

| Value | Used for | Effect |
|---|---|---|
| `mark_stale` | norms and decisions — a human decides | a warning line is written right under the anchor and stays until a human checks the slice against the code |
| `lock` | hard constraints | the change is refused |
| ~~`reconcile`~~ | — | **not part of the model**: an agent rewriting a norm itself breaks *an agent does not ratify a norm it wrote*. Acceptable only for derived facts, by explicit Regent decision |

The warning line, in the project's notation, starts with `STALE`, carries the date and the changed
file, and is removed **only** by a human who has checked the slice. "Newer" is decided by git
topology (the newest commit touching a target vs. the newest commit touching the slice's own lines),
not by wall clock, and counts only changes after a recorded **baseline commit**.

Documents that are **acts** (ladder plans, gate sheets, opinions, closed Orders, dated handoffs) are
not scanned and not rewritten: they record the name a norm had on the day they were written.

## 3. The work ledger — the first peek on returning

The lineage manifest answers *which norm governs which code*. A second file in the same folder
answers the question every returning agent asks first: **what is ongoing, and what is only
backlog?** It is `.shortcuts/.virtual/ongoing.json`, written for the agent (the Regent does not need
to read it), and it is the first thing looked at when work resumes.

```json
{ "schema": 1, "updated": "2026-10-05",
  "items": [
    { "id": "B-DAT-08", "title": "revenue-centre splitter",
      "state": "ongoing",
      "who": "DV",
      "since": "2026-09-29",
      "where": ["branch:plumbing", "src/Board.cs", "pass:M2.F3.T04"],
      "next": "second half of the probe: mutation round",
      "source": ".plan/RESUMING.md#splitter" } ] }
```

| `state` | Means | Required |
|---|---|---|
| `ongoing` | started and not closed | `where`: evidence a stranger can check — a branch, the files, a pass or Order id |
| `review` | the agent finished; a human or QA must check | what is being waited on, in `next` |
| `blocked` | waits on a named decision | `blocked_by`: who decides, and what |
| `backlog` | decided or planned, **not started** | `source`: where it was decided |
| `done` | finished; stays only until the next handoff, then is removed (version control is the record) | — |

Rules:

- **It points, it never copies.** A short `title`; the detail lives in `source`.
- **An agent never writes `done` on its own work.** It writes `review`.
- **Promoting `backlog` to `ongoing` is the queue's or the Regent's act**, not an accident of
  opportunity. An agent does not start backlog items to be helpful.
- **Updated by the agent, without asking**, at: starting an item, each boundary (`next`), finishing
  (`review`), stopping, and handoff. State the present; remove what no longer holds.

**Resuming = gather every trace, then reconcile.** `python scripts/vp.py ongoing` shows the ledger;
`python scripts/vp.py trace` gathers what agents leave behind that the ledger might have missed:
uncommitted files, local branches not merged into the default branch, stashes, the latest commits, the
guideline files touched recently, `STALE` lines and the Orders. Then compare:

| Finding | Meaning | Do |
|---|---|---|
| `ongoing` item whose evidence is gone | **ghost** | report; propose demoting to `backlog` or removing; ask |
| evidence with no item (a dirty file, an unmerged branch, a stash) | **orphan work** | report with the evidence; ask which item it belongs to; do not adopt it silently |
| `ongoing` item older than two weeks with no recent commit | **stale claim** | report; ask |
| ledger absent but `.virtual/` exists | not adopted yet | offer to create it from the template; create only with a yes |

## 4. How a project adopts it (cheapest first)

1. **Anchors resolve** — every cited `§anchor` exists. Costs nothing and pays for itself.
2. **The manifest is valid** — each slice resolves, each target exists. Born listing, not failing:
   fix the dead citations, then turn the gate on.
3. **Staleness fires** — the gate writes the warning when a target changes after the baseline.

A gate is trusted only after it has been **seen failing** on a planted defect.

## 5. Agent protocol

Before editing code: `vp.py code <file>`, read the slices. After editing: report which slices are now
out of date. Never remove a `STALE` line; never edit a norm to match the code. If the code is right
and the norm is wrong, that is a decision for the Regent.

## 6. Direction, not yet built (design notes absorbed from earlier research)

Treat these as the intended direction. Nothing here is implemented by `vp.py`. Layers (2), (3) and (5)
exist in `scripts/shortcuts.py` (R7): stable node ids that are the exact anchors, document order as a
column, and a fingerprint per node over its own lines (`library/shortcuts.md` §3). Offsets/ropes (4), the
dependency graph (6) and the recovery index (7) are not built.

> **Do not index text. Index semantic positions in ordered structures.** The text is only the
> physical representation; the human-readable anchor stays as the interface, but it resolves once to a
> stable node id.

Layers: (1) a document becomes an **AST**; (2) every structural node gets a **stable id** — identity
must not be the ordinal ("third paragraph"), which shifts on every insertion; (3) **order
maintenance** keeps `before(a, b)` valid under insert/move/delete (the classic order-maintenance
problem, Dietz–Sleator, O(1) order queries); (4) an **offset/rope** map `NodeID → [start, end)`
extracts content in `O(log n + L)`; (5) **fingerprints** detect that a node's state changed without
comparing meaning; (6) a **dependency graph** between code and documentation propagates invalidation;
(7) a **recovery index** (q-gram/FM-index search) is used only when structural identity fails.

Consequence: "what comes above X?" stops being a retrieval problem and becomes an order query plus a
range query, and the agent consumes relations that are already materialised instead of re-inferring
them on every run. Incremental update cost is `O(k log n)` with `k` the number of structural nodes
touched, not the size of the repository.

## 7. Ancestry worth remembering

An earlier prototype, a *capability index*, tracked reusable algorithms through states `DISCOVERED →
GENERATED → VALIDATED → REGISTERED`, with these contracts that still hold for any registry:
discovery is observable but is not validation; only a `REGISTERED` item is reusable; `VALIDATE`
precedes `REGISTER` and an approval is always explicit; a rejected operation preserves the previous
snapshot; author content is never a harness command. The prototype itself is no longer part of this folder.
