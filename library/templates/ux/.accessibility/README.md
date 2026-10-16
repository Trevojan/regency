# Accessibility

What every screen of ⟨product name⟩ guarantees, and how each guarantee is checked. A screen is not
done until this list holds.

| Guarantee | Check |
|---|---|
| `ink`, `ink-muted`, `ink-faint` and every hue reach 4.5:1 on `ground`, `surface`, `surface-raised` in every theme | `ux.py check ../.tokens/tokens.json` (computed) |
| every hue reaches 4.5:1 on its own `-soft` fill; `ink` on every `-soft` fill; `on-accent` on `accent`; `ink` on `line-strong` | same |
| `line-strong` reaches 3:1 on the three grounds (control borders, switches, chips, fields) | same |
| focus is visible on every control: `focus-ring`, a 2px `ground` gap then 2px `accent`; inputs use `:focus-within` | Tab through every view |
| severity, status, diff lines, filters and switches never rely on colour alone: a mark, a word, a position or `aria-pressed` / `aria-checked` | read the rendered screen in greyscale |
| rail items, navigator rows, tabs and nav items expose `aria-current`, `aria-selected` or `aria-expanded` | inspect the markup |
| one overlay at a time; Esc closes it and returns focus | keyboard |
| every function reachable by keyboard, in visual order | `../.patterns/keyboard.md` |
| no page scroll at the target width; panes scroll, not the page | render at ⟨1280⟩ and ⟨1024⟩ |
| clickable things are `<button>` or `<a>`; every `<img>` has `alt`; one `<header>`, one `<main>` | inspect the markup |

## Rendering

Render each view in both themes at the target widths before calling it done:
⟨the command this project uses, e.g. `node <regency>/skills/tailwind-audit/scripts/shoot.mjs page.html --widths 1024,1280 --themes void,paper`⟩.

## Known exceptions

| Where | Exception | Rule |
|---|---|---|
| ⟨—⟩ | ⟨—⟩ | ⟨UX-UI-##⟩ |
