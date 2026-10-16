# State models

Three models cover every state the interface shows. A product maps its own engine levels and
artefact states onto them in `../BRIEF.md`; it does not add colours.

## Severity — the health of a source

| Level | Mark | Text / fill | Blocks the commit action |
|---|---|---|---|
| `fix` | ■ | `fix` / `fix-soft` | yes |
| `ask` | ◆ | `ask` / `ask-soft` | no: counted, carried as a missing marker |
| `note` | ● | `system` / `system-soft` | no |
| `ok` | ✓ | `ok` / `ok-soft` | — |

Problems sort fix → ask → note. A badge shows the worst level with its count.

## Lifecycle — where an artefact stands

| State | Mark | Text / fill |
|---|---|---|
| `draft` | ○ | `ink-muted` / `surface-raised` |
| `issued` | ● | `ok` / `ok-soft` |
| `reissued` | ↻ | `accent` / `accent-soft` |
| `stale` | ◆ | `ask` / `ask-soft` |
| `blocked` | ■ | `fix` / `fix-soft` |

Severity and lifecycle are separate: an artefact can be issued and still carry an `ask`.

## Actors — who plays a stage

| Kind | Chip | This product |
|---|---|---|
| `agent` | `ink` on `line-strong` | ⟨from BRIEF⟩ |
| `human` | `human` on `human-soft` | ⟨from BRIEF⟩ |
| `machine` | `system` on `system-soft` | ⟨from BRIEF⟩ |

Stage statuses: `active` · `reused` (carries its artefact) · `skipped` (carries its reason) · `human` ·
`pending` · `blocked`.
