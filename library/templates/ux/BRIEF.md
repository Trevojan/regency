# Brief — ⟨product name⟩

The facts the rest of `.ux/` depends on. Fill each `⟨…⟩` with the Regent; a hole left open is an
`ask`, never a guess. Check: `python <regency>/scripts/ux.py brief BRIEF.md`. Delete nothing; tables
keep their columns. When the tables are filled, `ux.py expand .` creates one folder per view and per
component.

## Product

| Field | Value |
|---|---|
| Name | ⟨product name, as the title bar shows it⟩ |
| Tagline | ⟨one line, five words or so: what goes in, what comes out⟩ |
| Archetype | ⟨workspace · data app⟩ |
| Primary user | ⟨who works in it, e.g. RGN⟩ |
| UI language | ⟨English · pt-BR⟩ |
| Stack | ⟨framework, and where the stylesheet is loaded⟩ |
| Product mark | ⟨path to an SVG, or "none: name in title style"⟩ |

## The artefact

| Field | Value |
|---|---|
| What the user works on | ⟨files, records, documents: the noun the navigator lists⟩ |
| Where it lives | ⟨root path or service⟩ |
| Source format | ⟨the format the editor shows⟩ |
| Output formats | ⟨the formats the output pane switches between, 2–4⟩ |
| Attic (undo store) | ⟨path where previous versions are kept⟩ |
| Settings file | ⟨path of the one settings file⟩ |

## The engine

| Field | Value |
|---|---|
| Engine | ⟨the validator, compiler or service whose output is the truth⟩ |
| Version shown | ⟨how the title bar reads its version⟩ |

Severity mapping — every engine level onto the four the interface shows (`.patterns/states.md`):

| Interface | Engine level |
|---|---|
| fix | ⟨level(s) that make the output untrustworthy⟩ |
| ask | ⟨level(s) for missing information⟩ |
| note | ⟨level(s) for shape warnings⟩ |
| ok | ⟨a passed check⟩ |

Lifecycle mapping — the artefact's states onto the five the interface shows:

| Interface | Artefact state |
|---|---|
| draft | ⟨written, never issued⟩ |
| issued | ⟨issued and current⟩ |
| reissued | ⟨issued again after a change⟩ |
| stale | ⟨issued, its sources changed since⟩ |
| blocked | ⟨cannot be issued: a fix stands⟩ |

## Actors

| Kind | Who | Read from |
|---|---|---|
| human | ⟨the Regent, and any role the human plays⟩ | ⟨the document that records it⟩ |
| agent | ⟨agent roles, e.g. DV, QA⟩ | ⟨the document that records it⟩ |
| machine | ⟨the gate or engine stage⟩ | ⟨the script that runs it⟩ |

## The commit action

| Field | Value |
|---|---|
| Action | ⟨the one action that changes files, e.g. "Issue"⟩ |
| Writes | ⟨paths it writes⟩ |
| Preflight checks | ⟨the ordered checks; the first failure decides⟩ |
| Partial path | ⟨what may be issued while a check fails, or "none"⟩ |
| Undo | ⟨how the previous version comes back⟩ |

## Views

One row per rail item. Code: three uppercase letters, unique, never a word of the product's own
vocabulary. Archetype: one of `.views/README.md` (workspace, library, template-form, run, problems,
settings). `ux.py expand` creates `.views/<Code>/README.md` per row.

| Code | Archetype | Purpose | Keys |
|---|---|---|---|
| ⟨EXP⟩ | ⟨workspace⟩ | ⟨one line⟩ | ⟨Ctrl 1⟩ |
| ⟨CFG⟩ | ⟨settings⟩ | ⟨one line⟩ | ⟨Ctrl ,⟩ |

## Components

The components the views use, by catalogue name (`.components/README.md`). `ux.py expand` creates
`.components/<Name>/README.md` per row.

| Component | Used by |
|---|---|
| ⟨AppFrame⟩ | ⟨all⟩ |
| ⟨Button⟩ | ⟨all⟩ |

## Commands

Every function the palette lists. Keys unique across this table and the views table.

| Group | Command | View | Keys |
|---|---|---|---|
| ⟨View⟩ | ⟨Command palette⟩ | ⟨any⟩ | ⟨Ctrl K⟩ |
| ⟨Edit⟩ | ⟨one function⟩ | ⟨EXP⟩ | ⟨a key or —⟩ |

## Vocabulary

The kinds of term the TermChip shows, each on one hue role (accent, human, system, ok, ink-muted).

| Kind | Hue role | Example |
|---|---|---|
| ⟨main term⟩ | ⟨accent⟩ | ⟨a sample⟩ |

## Out of scope

⟨what this frontend will not do, one line each⟩
