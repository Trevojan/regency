# Colour

Every token is named by role, never by value (`ux.py check` fails `cyan`, `red-600`, `gray`). Values:
`../.tokens/tokens.json`. Themes: ⟨Void⟩ (brand, first) and ⟨Paper⟩ (daylight); both keep the same roles.

## Roles

| Meaning | Token | Fill behind it |
|---|---|---|
| brand · primary action · selection · focus · writes · the main term in code | `accent` | `accent-soft` |
| the human actor · pins · the second kind of term | `human` | `human-soft` |
| passed · issued · added line · literal values in code | `ok` | `ok-soft` |
| the machine and the engine · structure keywords · note · paths (`link`) | `system` | `system-soft` |
| fix · blocked · removed line | `fix` | `fix-soft` |
| ask · missing value · stale | `ask` | `ask-soft` |

## Grounds, lines, text

- `ground` under the editor and the page; `surface` for rail, navigator, inspector, title and status
  bars, pane heads; `surface-raised` for cards, the active tab, hovered rows and inputs.
- `line` for hairlines between panes; `line-strong` for every control border.
- Text: `ink` first, `ink-muted` for metadata and punctuation in code, `ink-faint` for line numbers,
  inactive tabs and archived items. `on-accent` for a label on an `accent` fill.
- `scrim` behind the command palette and any modal layer.

## Actors

An agent chip is `ink` on `line-strong`; the human is `human`; the machine is `system`. Who is which
comes from `../BRIEF.md` (Actors).

## In code panes

| Syntax role | Token | This product's terms |
|---|---|---|
| main term | `accent` | ⟨from BRIEF Vocabulary⟩ |
| second term | `human` | ⟨…⟩ |
| structure | `system` | ⟨…⟩ |
| literal | `ok` | ⟨…⟩ |
| punctuation | `ink-muted` | — |
| unknown term | `fix`, wavy underline | — |
| missing value | `ask` on `ask-soft` | — |

## Contrast

Computed, never estimated: `python <regency>/scripts/ux.py check ../.tokens/tokens.json`. The pairs it
measures are listed in `../.accessibility/README.md`.
