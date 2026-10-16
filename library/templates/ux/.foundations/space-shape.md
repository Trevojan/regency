# Space, shape, layout

Values: `../.tokens/tokens.json` (`spacing`, `radius`, `size`, `shadow`).

## Space

4px base: `space-1` 4 · `space-2` 8 · `space-3` 12 · `space-4` 16 · `space-6` 24 · `space-8` 32.
Dense by default: rows `row-h` 26px, controls `control-h` 28px.

## Shape

Nearly square: `radius-xs` chips and gutter marks, `radius-sm` controls and tabs, `radius-md` cards,
popovers, toasts. The brand theme has no drop shadows: elevation is `surface-raised` plus a hairline
(`shadow-pop`).

## The shell

```text
┌ bar-h ─────────── title bar: mark · crumbs · palette entry · engine ──────────────┐
│ rail-w │ the view                                                                  │
│ rail   │                                                                           │
├ status-h ──────── status bar: engine · severities · open run │ view state ─────────┤
```

Main view: `nav-w` navigator · flexible centre · `inspector-w` inspector. Each view's own layout:
`../.views/<Code>/README.md`.

## Rules

- Selection is a row fill (`accent-soft`), never a coloured left border.
- The shell never scrolls the page, only its panes.
- No motion beyond instant state changes. ⟨exceptions, if any, as UX-UI-## in `../.rules/`⟩
- Target width ⟨1280⟩ and up. Below ⟨1024⟩ the inspector folds under the centre.
