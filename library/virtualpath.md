# Virtual paths — the lineage between norms and code

## 1. The problem

Most projects link code to norms in **one direction**: a source file cites `§layout-stable`, and the
norm has no idea who obeys it. When the code changes, the norm silently rots. A virtual-path registry
closes the loop: each **slice** of a norm declares, once, which code it governs, so a tool (and an
agent) can go from a file to its rules, from a rule to its files, and notice when a rule has aged.
This is also called *context lineage*, *reverse traceability* or *documentation impact radius*.

Tools: `scripts/vp.py` (read-only queries) and `scripts/idx.py` (the exact index, §6). Procedure:
`skills/virtualpath/SKILL.md`.

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
| `refers_to` | the code the slice governs — a **list**, relative to the repository root (one norm often governs many files). An entry is a file (`src/Page.razor`: every node in it) or one node (`src/Page.razor#n:3f2a9b1c0d4e`: the id `idx.py node` prints) |
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
| `mark_stale` | norms and decisions — a human decides | when a governed node changes, a warning line is written right under the anchor and stays until a human checks the slice against the code |
| `lock` | hard constraints | the change is refused |
| ~~`reconcile`~~ | — | **not part of the model**: an agent rewriting a norm itself breaks *an agent does not ratify a norm it wrote*. Acceptable only for derived facts, by explicit Regent decision |

The warning line, in the project's notation, starts with `STALE`, carries the date, the changed file
and the changed node ids, and is removed **only** by a human who has checked the slice.

What counts as a change is decided **node by node** by the index (§6). A slice governs every node of
a file it cites bare, the one node of a `#n:` selector, and any node — in any file — that cites its
anchor. The warning is written when one of those nodes was added, removed, or changed its shape hash.
A write that only moves whitespace changes no shape and writes nothing. The baseline is the index's
last record of the file: a file the index has never seen counts as changed, and without an index
every write to a cited file counts — the conservative rule, so a missing index can only add warnings,
never hide one.

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
| `draft` | drafted by a speed mode, **DRAFT/UNVERIFIED**: on the plumbing branch only, no tests, not verified (`library/team/SPEED_MODES.md` §6) | `where`: the branch (never `main`, `master` or `testing`) and the files; `next`: the verifying pass |
| `review` | the agent finished; a human or QA must check | what is being waited on, in `next` |
| `blocked` | waits on a named decision | `blocked_by`: who decides, and what |
| `backlog` | decided or planned, **not started** | `source`: where it was decided |
| `done` | finished; stays only until the next handoff, then is removed (version control is the record) | — |

Rules:

- **It points, it never copies.** A short `title`; the detail lives in `source`.
- **An agent never writes `done` on its own work.** It writes `review`.
- **A `draft` leaves `draft` only through a normal `/regency:team` pass over its unit**: `ongoing` when that
  pass starts, `review` when it ends, and its commit carries `Verified-Draft: <unit>`. Nothing else promotes a
  draft. `python scripts/vp.py drafts` lists every unverified draft (ledger items and `Draft: UNVERIFIED`
  commits no verifying commit closed) and exits 1 while one remains; nothing merges past plumbing until it
  exits 0.
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
4. **The index is built** — `python scripts/idx.py build` — and staleness turns node-exact (§2, §6).
   The index is a cache: deleting it loses nothing, and rebuilding it changes no id.

A gate is trusted only after it has been **seen failing** on a planted defect.

## 5. Agent protocol

Before editing code: `vp.py code <file>` — or `idx.py governs <file>:<line>` for the slices governing
that exact node — and read the slices; `idx.py get <id>` returns a node's exact bytes. After editing:
report which slices are now out of date. Never remove a `STALE` line; never edit a norm to match the
code. If the code is right and the norm is wrong, that is a decision for the Regent.

## 6. The index — exact, for the harness

`scripts/idx.py` keeps a cache at `<virtual>/index.sqlite` (gitignored by `<virtual>/.gitignore`,
rebuilt by `idx.py build`). It is written for the harness, not for a reader: every answer is a JSON
line, every position exact. The human-readable anchor stays the interface; it resolves to a node.

| Layer | What it is | Exactness |
|---|---|---|
| Nodes | every structural node of every indexed file: the file itself; in Markdown, each heading's section, paragraph, list, table, table row, code fence and front matter; in any other file, blocks found by one language-agnostic rule — indentation and blank lines, with attached comments, attributes and closing lines — down to three levels | the parser never guesses a language |
| Stable ids | 12 hex derived from the node's structural key (a `§anchor` or the heading text; a block's first line that is not a comment or attribute; a glyph block's name) and its parent's chain — never its position | an insertion elsewhere changes no id, and a rebuild from nothing gives the same ids; identical siblings are numbered among themselves; renaming a key changes its id, and recovery proposes the relink |
| Ranges | bytes `[b0, b1)` and lines `l0`–`l1` (1-based, inclusive) over the file as stored | `idx.py get <id>` returns exactly those bytes |
| Order | `ord`: document order within the file | `before(a, b)` is a comparison |
| Fingerprints | `exact`: sha256 of the node (CRLF read as LF, `STALE` lines left out); `shape`: whitespace collapsed, spaces beside punctuation dropped, indentation kept as relative ranks | a reformat keeps the shape; a re-indent that moves a line into or out of a block does not |
| Edges | manifest slice → governed nodes; node → the `§anchors` and ids it cites (`library/ids.md`: unit, gate, UI rule, Order, conflict), attributed to the deepest node holding the citing line | a citation in the code is evidence the manifest did not have to infer |
| Recovery | a removed node leaves a tombstone; a node that reappears with the same shape (moved), the same body under a new key (renamed) or a close trigram sketch (similar) is recorded as a move | `idx.py check` proposes the relink with its score; nothing is relinked silently |

The write hook re-indexes only the written file — the cost is the nodes of that file, not the
repository — and decides staleness from the node diff (§2). Queries: `node`, `get`, `governs`,
`cites`, `check`, `shortcuts`.

**Raw shortcuts.** `idx.py shortcuts` resolves the prose index (the links in `.shortcuts/README.md`),
the ledger's `where` evidence, every `STALE` slice and the latest Order to exact rows — path, node id,
line and byte range, hash — so a resumed session reads the bytes it needs instead of re-inferring
the prose.

Still direction: per-language syntax trees (the block rule is deliberately one rule), order labels
that survive an edit without renumbering the file, and a full-text FM-index; the trigram sketch
covers recovery today.

## 7. Ancestry worth remembering

An earlier prototype, a *capability index*, tracked reusable algorithms through states `DISCOVERED →
GENERATED → VALIDATED → REGISTERED`, with these contracts that still hold for any registry:
discovery is observable but is not validation; only a `REGISTERED` item is reusable; `VALIDATE`
precedes `REGISTER` and an approval is always explicit; a rejected operation preserves the previous
snapshot; author content is never a harness command. The prototype itself is no longer part of this folder.
