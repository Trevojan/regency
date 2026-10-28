# Ids — every prefix regency uses

One file, one grammar per id. `scripts/conventions_check.py` reads the JSON block below, compiles each
pattern and proves its example matches; a new id is added here first, then used.
Where a project's own glossary defines an id, the project wins for that project.

## Hierarchy (Big-O basis)

| Level | Name | Id | Is |
|---|---|---|---|
| **O4** | Solution | none | the whole solution; no nickname, cited only in the Briefing and the project title |
| **O3** | Module | `M##` | a decoupled feature of the solution |
| **O2** | Step | `D##` | coupled concepts that build one module (*degrau* of the ladder) |
| **O1** | Task | `T##` | one code file, coupled to its step |
| — | Phase | `F0`–`F6` | the seven fixed norms every task satisfies, bound to the Business Rules |

`O1`–`O4` name **levels**; `M##`, `D##`, `T##` name **objects** at a level. A unit is written by position,
never typed: `M03.D02.T04 [F1–F3]`.

## Artefacts and rules

| Id | Names | Example |
|---|---|---|
| `GT-##` | a verification gate (T1–T5 discipline) | `GT-03` |
| `UX-UI-##` | a UI / palette rule | `UX-UI-07` |
| `ORD-####` | an Order (immutable once closed) | `ORD-0012` |
| `EMS-###` | an Emission: a Glyph emission carrying a sequence of Orders, run by `/regency:order:lazy`; read, never written | `EMS-011` |
| `FX-<wave>-<n>` | a fix note a `just-in-time` gate writes for the next wave (`library/team/SPEED_MODES.md` §5) | `FX-4-2` |
| `C-##` | a conflict between norms, open until resolved | `C-01` |
| `a.b` | regency's own version: `+b` content change, `+a` major rule finished, reinterpreted or invented; no caps | `2.0`, `99.999` |

## People

`RGN` is the Regent alone. Other humans carry the prefix: `RGN-PO`, `RGN-Client`, `RGN-DA`, `RGN-DV-<n>`.
`PO`, `DV`, `QA`, `DA` without the prefix are agent roles.

## Terms

| Term | Means |
|---|---|
| **AA** | Advanced Algorithm — the Regent's name for the AI side of the work |
| **EMS** | Glyph emissions (PGML, HGML, XML, JSON); regency reads them as input, never writes them |
| **`.scope/`** | the Regent's raw material: any folder of that name anywhere in the repo; read-only for agents |
| **TEAM** | the agent set that serves the Regent |

## Machine grammar

```json
{
  "unit":    {"pattern": "^M\\d{2}(\\.D\\d{2}(\\.T\\d{2})?)?( \\[F[0-6](–F[0-6])?\\])?$", "example": "M03.D02.T04 [F1–F3]"},
  "level":   {"pattern": "^O[1-4]$",          "example": "O3"},
  "phase":   {"pattern": "^F[0-6]$",          "example": "F4"},
  "gate":    {"pattern": "^GT-\\d{2,}$",      "example": "GT-03"},
  "ui-rule": {"pattern": "^UX-UI-\\d{2,}$",   "example": "UX-UI-07"},
  "order":   {"pattern": "^ORD-\\d{4,}$",     "example": "ORD-0012"},
  "emission":{"pattern": "^EMS-\\d{3,}$",     "example": "EMS-011"},
  "fix-note":{"pattern": "^FX-\\d+-\\d+$",    "example": "FX-4-2"},
  "conflict":{"pattern": "^C-\\d{2,}$",       "example": "C-01"},
  "version": {"pattern": "^\\d+\\.\\d+$",     "example": "2.0"},
  "person":  {"pattern": "^RGN(-(PO|Client|DA|DV-\\d+))?$", "example": "RGN-DV-2"}
}
```
