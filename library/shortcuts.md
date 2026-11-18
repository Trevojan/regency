# Shortcuts — the entry index and its store

Decision records R7 (the entry index, its state block, drift) and R12 (one store: R7's parts on
`idx.py`'s index), in `REGENCY_CUSTOMIZATION.md`. Engine: `scripts/shortcuts.py`. Lineage and the work
ledger stay in `scripts/vp.py` (`library/virtualpath.md`); the exact index stays in `scripts/idx.py`
(`virtualpath.md` §6). `shortcuts.py` keeps no database of its own.

## 1. Layers and engines

| Layer | Holds | Engine |
|---|---|---|
| `.shortcuts/README.md` | the entry index: where I am, the five-line map, the lookup table, the generated state block | `shortcuts.py` |
| `.shortcuts/.virtual/index.sqlite` | **the one store**: the exact index (nodes, edges, recovery) and, in its `prints` table, every recorded file's fingerprint | `idx.py` (nodes), `shortcuts.py` (prints) |
| `.shortcuts/.virtual/manifest*.json` | norm slice ↔ code lineage | `vp.py` |
| `.shortcuts/.virtual/ongoing.json` | the work ledger | `vp.py` |
| `.shortcuts/.virtual/checkpoints.jsonl` | the journal | `hook-journal.py` |
| `.shortcuts/regency.json` | the regency stamp: the version the project fits | `migrate.py` |

## 2. What each part costs and what it buys

| Part | Cost | Buys |
|---|---|---|
| `check` | low: reads the index and the guideline docs | dead pointers, dead anchors, a map past five lines, copied prose and a stale state block are found before a cold agent follows them |
| `drift` | low: a stat per recorded file, a hash only when size or mtime moved | files changed outside the hooks (hand edits, pulls, other tools), named down to the section that moved |
| `refresh` | moderate: git, ledger, journal, a STALE scan | the state lines of the index stop being written by hand (F4) |
| `peek` | low | the first read on resume: the index whole, the live state, the counts, one call |
| `index` / `record` | the first `index` builds the exact index (guidelines only) when there is none; after that, cheap | every guideline doc and manifest target fingerprinted, and re-indexed where it moved |

## 3. The store

`<guidelines>/.shortcuts/.virtual/index.sqlite`, SQLite, **gitignored** (`.virtual/.gitignore`, written by
`idx.connect`). It is a cache: any clone rebuilds it with `shortcuts.py index` (or `idx.py build`). Raw
and exact, written for the harness, not for reading.

| Table | Written by | Row | Columns |
|---|---|---|---|
| `prints` | `shortcuts.py` (`record`, `index`, `refresh`), `hook-lineage.py` | one fingerprinted file | `path` (repo-relative), `sha256`, `bytes`, `mtime_ns`, `prev_sha256` (what the last change replaced), `at`, `session`, `source` (`hook`, `lineage`, `scan`, `refresh`, `manual`, `import`) |
| `nodes`, `files`, `cites`, `tombs`, `moves`, `shortcuts` | `idx.py` | one structural node, file, citation, tombstone, move, raw shortcut | `virtualpath.md` §6 |
| `search` (FTS5, contentless), `search_rows`, `search_files` | `locate.py` | one node's own lines in the inverted index; its location; one indexed file's size, mtime and hash | §7 |
| `reads` | `hook-reads.py` | one Read of a file: session, agent, path, sha256, lines (`l0`–`l1`), bytes, `b0` (the byte offset the first line starts at) | §8 |
| `elicit_schemas`, `elicit_sessions`, `elicit_params`, `elicit_questions`, `elicit_events` | `elicit.py` (the hook calls it) | one schema snapshot; one session; one slot's value, status, revision, provenance, fingerprint; one question's presentation; one transition | `library/elicitation.md` |
| `meta` | both | one fact about the store | `schema`, `built` (set by `idx.py build`), `prints_migrated_from`, `prints_migrated_at`, `prints_migrate_error` |

Rules:

- **One store, one writer per table.** `idx.py build` clears its own tables and keeps every other;
  `shortcuts.py` writes only `prints` and reads the nodes; `locate.py` writes only the `search` tables;
  `hook-reads.py` writes only `reads`; `elicit.py` writes only the `elicit_*` tables.
- **A store that holds only prints is not an index.** Until `idx.py build` (or the first `shortcuts.py
  index`) sets `meta.built`, the write hook keeps the conservative file-level rule (`virtualpath.md` §2)
  and never grows a partial index.
- **Identity is idx's stable id; the anchor is its label.** `drift` names a moved section by its label
  (the `§name`, else the heading text) — the same anchor `vp.py` resolves. A section's range covers its
  subsections, so a change inside a child moves the parent's hash too; `drift` names the deepest section
  that changed, never its parents.
- **Order is a column** (`nodes.ord`): `before(a, b)` is a comparison within one file.
- **The prefilter trusts size + mtime.** An edit that keeps both is invisible to `drift` until the next
  `record` or a full `index`; that is the price of not hashing every file on every look.
- **`fingerprints.json` (schema 1, regency 2.11 and earlier) is imported, then retired.** The first open of
  the store imports its rows once into `prints` with `source = import` and `mtime_ns = -1`, so the next
  look re-hashes them. `/regency:update` to 2.12 then deletes the file, after running
  `shortcuts.py migrate` (the step's `before`), on the Regent's one yes to the plan; git keeps its history.
  This retires R5.3's tracking of fingerprints in git: a fingerprint is a cache, rebuilt from the files.
- **`export`** prints the prints and the store's meta as JSON, for reading and diffing.

## 4. The entry index

`.shortcuts/README.md` is still the one document read whole. `check` holds it to the rules the
guidelines template already states:

| Rule | Source | `check` reports |
|---|---|---|
| the index points, it never copies | conventions §7 | `copy`: a line of 60+ characters found verbatim in another guideline doc |
| every pointer resolves | layouts §1 | `dead`: a link or backticked path that exists under none of the index folder, the guidelines root, the repository |
| every anchor resolves | virtualpath §2 | `anchor`: `path#anchor` naming no section of that file; a repeated heading in the index |
| the map is five lines | `orders/resume.xml` | `map`: the section titled *Map* past five lines (blockquoted guidance is not counted) |
| generated text is never hand-edited | F4 | `state`: block missing, markers broken, or content different from a fresh render |

A pointer inside a `⟨hole⟩` of the template is still unfilled and is not checked.

### The generated state block

```text
<!-- shortcuts:state · generated by shortcuts.py refresh; never edit by hand -->
| state | value |
|---|---|
| branch | plumbing |
| version | 2.3 |
| regency | 2.12 |
| ledger | 1 ongoing / 1 draft / 1 review / 1 blocked / 2 backlog (updated 2026-10-26) |
| ongoing | M01.S01.T01 splitter → mutation round |
| draft | M02.S01.T01 parser (UNVERIFIED) |
| review | M01.S01.T02 board |
| blocked | M01.S02.T01 ← RGN |
| last checkpoint | 2026-10-26T11:40:02-03:00 Edit src/Board.cs (M01.S01.T01) |
| STALE | 1 |
| latest Order | ORD-0003 |
<!-- /shortcuts:state -->
```

`version` is the project's own (`VERSION`, else its plugin manifest, else its latest tag); `regency` is
the stamp `migrate.py` wrote. Deterministic: no clock and no commit hash (committing the block would
change the hash it shows). `refresh` writes only between the markers, keeps the file's line endings,
writes nothing when the block is current, and records its own write so it never reads as drift.
Without markers it writes nothing; `refresh --init` appends the block once. `hook-acts-guard.py` denies
a hand edit inside it.

**When it is written:** at every handoff (`order:handoff` runs `refresh`) and at every session end
(`SessionEnd` → `hook-shortcuts.py`). The second one makes the tracked index change once per session in
which the state moved; that is accepted (R7.3).

## 5. Triggers (hooks are triggers, scripts are engines — R4.1)

| Event | Script | Calls |
|---|---|---|
| `PostToolUse` Edit/Write | `hook-lineage.py` | `shortcuts.record()` for the file; again for a norm doc it wrote a STALE line into (`source = lineage`) |
| `PreToolUse` Edit/Write | `hook-acts-guard.py` | `shortcuts.guard_generated()`: deny a hand edit of the state block |
| `SessionStart` | `hook-resume.py` | `shortcuts.summary_part()`: `shortcuts check N · drift N` in the resume line |
| `SessionEnd` | `hook-shortcuts.py` | `shortcuts.refresh()`: silent, adoption-gated, never fails; fits the 1.5 s budget (no scan) |
| `PostToolUse` Read | `hook-reads.py` | one `reads` row (§8); async, adoption-gated |

## 6. Operating

| Need | Command |
|---|---|
| first read on resume | `python scripts/shortcuts.py peek` |
| is the index honest? | `python scripts/shortcuts.py check` (exit 1 on a problem) |
| what changed outside the hooks? | `python scripts/shortcuts.py drift` (exit 1 on drift) |
| bring the store up to date | `python scripts/shortcuts.py index` |
| rewrite the state block | `python scripts/shortcuts.py refresh` (`--init` once) |
| import the old JSON | `python scripts/shortcuts.py migrate` (also automatic on first open) |
| the prints as JSON | `python scripts/shortcuts.py export` |
| where does this word live? | `python scripts/locate.py query <terms>` (§7) |
| how much context do sessions rebuild? | `python scripts/reconstruction.py report` (§8) |
| health | `python scripts/shortcuts.py --selftest`, `locate.py --selftest`, `reconstruction.py --selftest` (doctor runs them) |

## 7. Search — `locate.py`

Where a word lives, before a broad grep (`/regency:locate-with-fts5`, mostly called by the harness). A contentless
FTS5 table indexes, for every structural node `idx.py`'s parser finds, only the node's **own** lines — those no
child node holds — so every line is indexed once and a hit names the deepest node holding it. The store keeps the
inverted index and the node rows, never the text: a hit is a location (path, the first matching line, the node's
range and id, its section chain), and the text is read from the file.

| Rule | How |
|---|---|
| fresh at every query | each candidate file's size and mtime against `search_files`; only the files that moved are re-parsed (the parser's light mode: ids and ranges, no hashes) |
| scope | the guidelines root, the manifest's targets and the files git tracks; `index --guidelines-only` narrows it |
| an SQLite without contentless delete | the index is rebuilt whole when a file changed (`meta.search_delete = rebuild`) |
| no FTS5, or no `.shortcuts/.virtual` | one JSON line with the `rg` command to run instead, exit 3 |
| lexical, not a regex engine | patterns, multiline matches and exact error strings stay with Grep |

## 8. Reads and the reconstruction measure

`hook-reads.py` adds one row to `reads` per Read of a file in the repository (session, agent, path, sha256, the
lines returned, their bytes and the byte offset the first of them starts at). `scripts/reconstruction.py report`
measures, per session, the bytes read; the bytes **carried** — only the lines of a read that an earlier session
already read at the same path and the same hash, counted in bytes (line-level, the Regent's definition of 2026-11-18)
— and their ratio; the bytes **repeated** inside the session; and the files most often re-read unchanged across
sessions, a session counting when it re-read any of the file's lines (`/regency:measure-context-reconstruction`).
Carried bytes are exact: the rows of one content hold the line ranges and byte offsets they cover. A row journalled
without an offset (before the column existed) is left out of the measure and counted on a line of its own; the hook
adds the column to such a store on its next write. Tokens are bytes / 4, an estimate. Bash reads, Grep and Glob output,
tool results, the system prompt and the prompt cache are not measured.
