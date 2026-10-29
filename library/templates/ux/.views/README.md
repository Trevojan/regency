# Views

One folder per view of ⟨product name⟩, named by its rail code: `<Code>/README.md`, created from
`_view.template.md` by `python <regency>/scripts/ux.py expand ..` for every row of `../BRIEF.md` (Views).

<!-- ux:views:begin -->
| Code | Archetype | Purpose | Keys |
|---|---|---|---|
<!-- ux:views:end -->

Every view mounts inside **AppFrame** (`../.components/README.md`). Regions use the `size` tokens.
Every view documents its **layout**, the **state shown** in its sample, the **rules** the layout does
not make obvious, and its **empty, loading and problem states**.

## The archetypes

### 1. Workspace — navigate, edit, see the output, check, issue

The home view. The person opens an artefact, edits its source, sees what the engine makes of it,
checks it and issues it.

```text
┌ nav-w ──────────┬ flexible ─────────────────────────┬ inspector-w ─────────┐
│ TreeNav         │ TabBar                            │ FieldCheck / packet  │
│                 │ SourceEditor        (SOURCE)      │ links (point, never  │
│                 │ OutputPane          (OUTPUT)      │   copy)              │
│ InsertPalette   │ ProblemList  (this file only)     │ StepCycle (compact)  │
│ (chips)         │                                   │ actions              │
└─────────────────┴───────────────────────────────────┴──────────────────────┘
```

- The inspector follows the navigator's selection: an artefact shows its own fields; any other file
  shows its frontmatter or metadata.
- The problems pane here is this file only, and says so in its head; the status bar is workspace-wide.
- The output pane is engine output, never an editor. Its format switch (Segmented) lists the brief's
  output formats.
- An edited source marks its tab dirty; the commit action (Issue / Re-issue) sits in the inspector.

### 2. Library — browse a vocabulary, read one entry, insert it

```text
┌ nav-w ─────────────┬ flexible ──────────────────┬ inspector-w ─────────┐
│ ViewHead tabs       │ SearchField · FilterChips  │ EntryDetail          │
│ NavList (categories │ DataTable (entries)        │ example output       │
│  with counts)       │                            │ actions (Insert)     │
└─────────────────────┴────────────────────────────┴──────────────────────┘
```

- Category counts and kind-filter counts come from the engine's vocabulary, never typed by hand;
  filter counts follow the current category.
- Enter inserts into the last focused editor; the view stays open for the next insert.
- Every definition, formula and example is engine output.

### 3. Template form — fill holes, see the expansion live

```text
┌ nav-w ──────────┬ flexible ──────────────────┬ flexible ───────────────┐
│ NavList          │ TemplateForm               │ OutputPane (expansion)  │
│ (templates)      │ (gloss, holes, call, body) │ ProblemList             │
└──────────────────┴────────────────────────────┴─────────────────────────┘
```

- An empty hole stays empty on purpose: it becomes a missing-value marker in the output and an `ask`,
  never a blocker.
- Two inserts: the call (short form) and the expanded body.

### 4. Run — one pass of work, who does what, the gate, the commit

A run is one pass of the project's orchestration over one unit (with regency: one `/regency:team` pass
over `M##.S##.T##`). It issues one packet per active agent stage.

```text
┌ nav-w ──────────┬ flexible ──────────────────────────────────────────────┐
│ RunList          │ ViewHead: run id · unit · span · norm · decision        │
│                  │ StepCycle (who does what)                               │
│                  │ TrafficGraph (what each stage reads and writes)  │ Preflight │
│                  │ RunTimeline (events)                                    │
└──────────────────┴─────────────────────────────────────────────────────────┘
```

- Which roles run as agents is read from the project's recorded decision, never chosen here. A stage
  the human plays carries the `human` mark and gets no packet; the gate is the machine.
- Withholding is structural: the graph shows only what a packet passes, by path. What a stage must not
  receive never gets an edge.
- The commit action (Issue run) is disabled under the failing preflight row; the partial path
  ("Issue ready (n)") is offered when one exists. Every issue is reversible from the attic.
- Close stays blocked until the human approves; the step says so.

### 5. Problems — every problem, its exact span, a verified fix

```text
┌ flexible ───────────────────────────┬ inspector-w + ────────────────────┐
│ ViewHead (group by · Re-check)      │ SourceSpan                        │
│ FilterChips (severity · source)     │ KV (code · message · facts)       │
│ ProblemList grouped by file         │ ProposalDiff (re-check result)    │
│ engine stores (health)              │ actions: Apply · Open in workspace│
└─────────────────────────────────────┴───────────────────────────────────┘
```

- Messages are the engine's, verbatim; codes are never renamed.
- A proposal appears only after the engine re-checked its result, and says so ("re-check: 0 fix").
- Apply is undoable; Open jumps to the line in the workspace.
- Sources are listed by name (the engine, a rules file, frontmatter, lineage): a problem always
  names where it came from.

### 6. Settings — one file, searchable, explicit save

```text
┌ nav-w ──────────────┬ flexible ───────────────────────────────────────────┐
│ SearchField          │ SettingsSection                                     │
│ NavList (sections,   │   SettingRow · SettingRow (modified mark, Reset)   │
│  ask marks)          │ SettingsSection …                                   │
│                      │ save bar: what changed · Save (Ctrl S) · Open source│
└──────────────────────┴─────────────────────────────────────────────────────┘
```

- Every setting lives in one file `../BRIEF.md` names; Open source shows the same settings.
- Switches apply at once; fields and selects count as unsaved until Save; the save bar names them.
- A required value left empty shows `ask` on its row and on its section in the nav.
- A locked setting says what locks it in its hint. A value read from another document (the team, a
  recorded decision) is shown read-only with its source; changing it means proposing a decision for
  the Regent to ratify.
- An unrecorded value shows `UNRESOLVED` with the recommended value, never a guess.

### 7. Command palette — every command, from any view

An overlay (`Ctrl K`) over `scrim`, not a rail view.

- Recent first, then the brief's command groups. Each row: label, the view code it lands in, its shortcut.
- A prefix switches the search (vocabulary, files); a path opens the file.
- Esc closes and returns focus to where it was.
