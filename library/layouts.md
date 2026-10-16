# Layouts — finding a project's documents

Regency works on projects it has never seen. Every skill resolves document locations with this
file instead of hard-coding paths. **Probe in order; the first hit wins; a missing document is a
defect to report, never a path to improvise around.**

## 1. Find the guidelines root

Probe from the repository root (the nearest ancestor containing `.git`, else the current directory):

1. `.guidelines/`
2. `Docs/.guidelines/`
3. `docs/.guidelines/`

None found → the project has no guidelines. Say so, continue with the library defaults, and offer
`/regency:init`. Do not create folders without naming them first and getting a yes.

## 2. Two known layouts under that root

| Concept | **Dotted** (current Regent standard) | **Classic Orbital** |
|---|---|---|
| Entry / index | `.shortcuts/README.md` | `AGENTS.md` |
| Project state | `.plan/RESUMING.md` | `PLAN/CHECKLIST.md`, `PLAN/TRACE.md` |
| Plan documents | `.plan/` (`GRAND_PLAN`, `MINIMUM_PLAN`, `LADDER_PLAN_PART_<n>`, `CHECKLIST`, `GATE_*`, `BACKLOG`) | `PLAN/` (`GRAND_PLAN`, `MINIMUM_PLAN`, `LADDER_PLAN_M_<n>`, `CHECKLIST`, `GATE_*`, `BACKLOG`) |
| Norms | `.decisions/` (`DECISIONS`, `ARCHITECTURE`, `BUSINESS_RULES`, `TESTS`, `DEPENDENCIES`) | `DECISIONS/` (same names) |
| Facts | `.sources/` (`DATA_MODEL`, `API_ENDPOINTS`, `AGENTS`) | `SOURCES/` (`BRIEFING`, `DATA_MODEL`, `API_SURFACE`) |
| Prohibitions | `.constraints/README.md` | inside `DECISIONS/` |
| Orders | `.orders/` (`ORD-####`) | — |
| Changelog | `.changelog/` | `SOURCES/CHANGELOG.md` |
| Team role specs | `.team/` (`TEAM`, `PO`, `DV`, `QA`, `DA`) | `TEAM/` |
| Frontend documentation | `.ux/` (index `.ux/README.md`, brief `.ux/BRIEF.md`; scaffolded by `/regency:ux-init`) | — |
| Attic (superseded docs) | `.history/` | — |
| Code ↔ norm lineage | `.shortcuts/.virtual/manifesto.json` (or `manifest.json`) | — |
| Work ledger (ongoing vs backlog) — the first peek on returning | `.shortcuts/.virtual/ongoing.json` | — |
| Id grammar | project's own (D3/D2/D1; ADR-n; B-xxx) | `DC<n>`, `AR<n>`, `BR<n>`, `M<n>.F<k>.T<nn>` — see `library/team/ORBITAL_AGENTS.md` |

Mixed or custom names: match by purpose using the table above, and report the mapping you used.

## 3. Role specs: project first, library second

For role `X` in `PO DV QA DA` (and `TEAM`):

1. the project's own `…/.team/X.md` or `…/TEAM/X.md` — **a project spec overrides the library**;
2. otherwise `library/team/X.md` in this folder.

Either way, the generic control specification is `library/team/REINFORCED_AGENT.md`; read it only
when a binding in a role's section 19 is unclear, and never edit it to fit a role.

## 4. Orchestration vocabulary

`library/team/ORCHESTRATION.md` speaks in MAX/MIN/L#/S#/F#. Translate it with
`library/team/references/vocabulary-map.md` (it carries the conflicts and the conservative default
for each). For the dotted layout, read `LADDER_PLAN_PART_<n>` wherever the map says
`LADDER_PLAN_M_<n>`, and `API_ENDPOINTS.md` wherever it says `API_SURFACE.md`.

## 5. Writing paths in regency's own files

Inside this folder, every path is **relative to the regency root** (the directory holding
`.claude-plugin/`): `library/…`, `scripts/…`, `skills/…`. A skill finds the root two directories
above its own `SKILL.md`. Never write an absolute path, a drive letter or a home directory in a
tracked file; `scripts/doctor.py` fails the build if one appears.
