# Foundations

The design language of ⟨product name⟩: what every screen inherits. Values live in
`../.tokens/tokens.json`; these files say what each value is for.

| File | Subject |
|---|---|
| `color.md` | colour roles and where each one goes |
| `type.md` | families, the type scale, mono vs sans |
| `space-shape.md` | spacing, radius, shell metrics, elevation, motion, widths |
| `iconography.md` | the product mark, icons, state marks |
| `content.md` | voice, labels, ids, hints, marks, language |

## Principles

- **Data, not narration.** Show values, states and counts. Never print the interface's own reasoning.
  A proposal reads "Proposal — 1 change", not a paragraph. Rationale lives in code comments and here.
- **The engine is the source of truth.** Every mark, colour and message derives from the engine's
  output (`../BRIEF.md`, The engine). Never invent a severity; never reword an engine code or message.
- **Missing is not broken.** `ask` (missing information) never blocks; only `fix` blocks the commit
  action.
- **Point, never copy.** A link to the source of a fact beats a duplicated line.
- **Black ground, never grey.** The brand theme's ground is pure black; neutrals carry a hue.
- ⟨a principle specific to this product, or delete this line⟩

## Anti-patterns

Grey ground or grey neutrals · a colour named by value · a coloured left border for selection · a
disabled button with no reason beside it · a paragraph explaining what the screen does · a severity
the engine did not give · a reworded engine message · drop shadows on the brand theme · emoji · an
action with no keyboard path · a count that differs between two places · an apply with no undo.
