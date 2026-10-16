# Layout knowledge: flex, grid, absolute

This folder is about where boxes go, not what they look like. It holds no colours, radii, shadows or brand tokens, so it stays true after any redesign. A new design changes `references/theme.css` and `references/components/`; it never changes this folder.

| Folder | Read when | Patterns |
|---|---|---|
| [flex/](flex/SPEC.md) | items in one direction, sized by their content | F01–F12 |
| [grid/](grid/SPEC.md) | items aligned in two directions, or sized by the container | G01–G11 |
| [absolute/](absolute/SPEC.md) | a box sits on top of another, out of the flow (also `fixed`, `sticky`, top layer) | A01–A10 |
| [debug.js](debug.js) | console helpers for the triage below | — |

Each folder holds `SPEC.md` (the mechanics and a trap table) and `samples.html`: a **body fragment**, one `data-pattern` block per pattern, traps as a `broken` / `fixed` pair. Explanations live in HTML comments; the visible text is sample data only. Render with `python scripts/preview.py`, which pastes each fragment into `references/render-shell.html` and adds Tailwind and the tokens to its `<head>`.

## Choosing the primitive

Ask in this order. The first yes wins.

1. **Does it sit on top of something, or stick to an edge?** → absolute family.
   - Attached to one box (badge, icon in input, menu under a button) → `absolute` inside a `relative` parent (A01–A05).
   - Attached to the viewport, above everything (modal, menu that must escape clipping) → the **top layer**: `<dialog>` / `popover` (A10). `fixed` only for things like a toast stack (A06).
   - Scrolls, then sticks (page header, table head) → `sticky` (A07).
   - Overlaps but should still size its parent (caption over image, loading veil) → **grid stack** (G07), not absolute.
2. **Must items line up across rows and columns, or does the container decide the sizes?** (page columns, KPI rows, forms, galleries, label/value lists) → grid.
3. **Otherwise** (a row or column of things sized by their content: toolbars, bars, button content, media objects) → flex.

Grid for the skeleton, flex for the contents, absolute for decoration. A card in a grid cell is a flex column; its header is a flex row; its badge may be absolute.

## Triage: "the position is confusing"

Work from evidence, not guesses. Each step names a helper in [debug.js](debug.js) (paste it in the console, or run it through the browser tool).

1. **Find the box that is wrong.** `outlineAll()` draws every box. Name the element: too wide, misplaced, clipped, under something, or not sticking?
2. **Read its chain.** `chain(el)` prints `display`, `position`, `overflow`, `min-width`, `min-height`, containing-block makers (`transform`, `translate`, `filter`, `backdrop-filter`, `contain`) and `z-index` for the element and every ancestor. Most bugs live in an ancestor.
3. **Classify the symptom**, then open the matching spec:
   | Symptom | First suspect | Pattern |
   |---|---|---|
   | page scrolls sideways / text won't truncate / column blows out | `min-width: auto` on a flex or grid item | F02, G11 |
   | inner area won't scroll, pushes the page instead | `min-height: auto` in a flex column | F05 |
   | absolute box placed against the wrong ancestor | missing `relative`, or a transform/filter ancestor | A01, A06 |
   | menu or tooltip cut off | `overflow-hidden` / `overflow-auto` ancestor | A04, A10 |
   | tooltip text wraps into a narrow column | absolute box shrinks to its anchor's width | A05 |
   | `z-50` still under something | stacking context | A09 |
   | `sticky` does nothing | overflow ancestor, no `top-*`, or parent as tall as the item | A07 |
   | cards in a row have different heights | `items-start`/`items-center` on the row, or body not `flex-1` | F04, G09 |
   | grid adds stray columns on mobile | unprefixed `col-span-*` | G01 |
   | `stackingContexts(el)` / `containingBlock(el)` disagree with intent | see A06, A09 | — |
4. **Fix at the lowest box that owns the cause.** `min-w-0` on the item, not `overflow-hidden` on the page. Remove the transform from the ancestor, not `z-[9999]` on the child.
5. **Re-render** at 360, 768 and 1280px. At 360px `overflowCulprits()` must return an empty list.

## Invariants (true in every design)

- Space between siblings is `gap`, never margins on children. Exception: `ms-auto` / `mt-auto` to push (F03).
- DOM order is reading and tab order. Never reorder visually (`order-*`, `*-reverse`, grid placement) against it.
- Logical sides (`start`/`end`, `ps`/`pe`, `ms`/`me`) for anything that mirrors in right-to-left languages.
- `dvh`, not `vh`, for full-height layouts on mobile (`min-h-dvh`).
- A layout fix never needs an arbitrary value. If it seems to, name the template as an `@utility` (G03, G04, G06).
