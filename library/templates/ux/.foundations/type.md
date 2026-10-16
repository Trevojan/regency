# Type

Families and styles: `../.tokens/tokens.json` (`type`). In CSS: `font: var(--type-body)`; tracked styles
add `letter-spacing: var(--type-<name>-tracking)`.

| Family | Font | Used for |
|---|---|---|
| sans | ⟨IBM Plex Sans⟩ | everything in the interface that is not code |
| mono | ⟨IBM Plex Mono⟩ | every id, path, key, file name and code pane |

| Style | Size / line | Use |
|---|---|---|
| `display` | 28/32, 600 | empty-state and onboarding titles only |
| `title` | 15/20, 600 | view, panel and card titles |
| `body` | 13/20, 400 | the default |
| `label` | 11/16, 600, uppercase, tracked | pane heads only; never a sentence |
| `caption` | 12/16, 400 | metadata, counts, hints, the status bar |
| `code` | 13/20 mono | source and output panes |
| `code-sm` | 12/18 mono | navigator rows, paths, field values |
| `token` | 12/16 mono, 600 | vocabulary chips, rail mnemonics |

- A project may swap the families; the scale stays.
- Load: ⟨how the fonts load: Google Fonts link, self-hosted files in `../.assets/fonts/`⟩.
