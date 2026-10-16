# Tokens

| File | Is | Edit |
|---|---|---|
| `tokens.json` | every value: colours per theme, type, spacing, radius, sizes, shadows | here, values only |
| `theme.css` | GENERATED: custom properties per theme, plus Tailwind v4 `@theme` mapping | never; rebuild it |

```bash
python <regency>/scripts/ux.py check tokens.json                    # roles, names, computed contrast
python <regency>/scripts/ux.py build tokens.json --out theme.css    # after every value change
python <regency>/scripts/ux.py synced tokens.json --css theme.css   # FAIL when theme.css was hand-edited
```

## Rules

- **Change values, never names.** Add a role when a new meaning appears; never drop one (the check
  requires the 23 colour roles of `../.foundations/color.md`).
- **Names are roles** (`accent`, `fix-soft`), never values (`cyan`, `red-600`).
- **The first theme is the brand theme**; a token missing a value in another theme inherits the first.
- **Contrast is computed** by the check, never estimated; a pair that fails is fixed here, not
  excused on the screen.
- The file has the Design System artifact shape, so the same file can seed a published design system.

## Wiring

- Plain CSS: load `theme.css`, then `../.components/components.css`. Theme switch: `data-theme` on
  `<html>` (⟨void⟩ default, ⟨paper⟩).
- Tailwind v4: paste `theme.css` after the Tailwind import; utilities `bg-surface`, `text-ink-muted`,
  `border-line-strong` follow.
- This project loads it from: ⟨path in the codebase⟩.
