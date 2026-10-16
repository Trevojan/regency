# Grid

**Use grid** when items must line up in two directions, or when the container, not the content, decides the sizes: page columns, KPI rows, forms, galleries, label/value lists, and any overlap that should still size its parent (G07). Inside a cell, switch to flex.

## Model

- The container defines **tracks** (`grid-cols-*`, `grid-rows-*`); items are placed into cells automatically, in DOM order, row by row.
- `gap-*` is the only spacing between items. No margins on items.
- Alignment inside cells: `justify-items-*` / `items-*` (all items), `justify-self-*` / `self-*` (one item), `place-items-center` (both). Default is `stretch` both ways: items fill their cell, which gives equal heights in a row.
- Rows you did not declare are **implicit**: sized by `auto-rows-*` (default `auto`, i.e. content height).

## Track sizing

| Utility | Template | Means |
|---|---|---|
| `grid-cols-3` | `repeat(3, minmax(0, 1fr))` | three equal columns that may shrink below content |
| `grid-cols-none` | `none` | back to a single implicit column |
| `grid-cols-subgrid` | `subgrid` | reuse the parent's column lines (G08) |
| `col-span-2`, `col-start-1`, `col-end-3`, `col-span-full` | | placement |
| `auto-rows-fr` | `minmax(0, 1fr)` | every implicit row as tall as the tallest (G09) |
| `grid-flow-dense` | | back-fill holes; breaks reading order, avoid |

Tailwind's numbered columns already use `minmax(0, 1fr)`. **A hand-written template with plain `1fr` does not**: `1fr` means `minmax(auto, 1fr)`, so one long word, table or `<pre>` widens its column and the grid blows out (G11). Write `minmax(0, 1fr)` in every custom template.

**Custom templates are named, never arbitrary.** The norm bans `grid-cols-[...]`. A layout that needs its own template gets an `@utility` with a name that says what it is, declared next to the tokens:

```css
@utility grid-shell   { grid-template-columns: 16rem minmax(0, 1fr); }              /* G04 sidebar + content */
@utility grid-gallery { grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr)); } /* G03 cards that reflow */
@utility grid-dl      { grid-template-columns: max-content minmax(0, 1fr); }          /* G06 label / value */
```

`@utility` names work with variants: `lg:grid-shell`.

## Patterns (rendered in `samples.html`)

| Id | Pattern | Classes | Notes |
|---|---|---|---|
| G01 | 12-column page grid | `grid grid-cols-1 gap-6 lg:grid-cols-12`; items `lg:col-span-8` + `lg:col-span-4` | **trap pair**: unprefixed `col-span-8` in a 1-column grid creates implicit columns and overflows on mobile |
| G02 | Responsive count | `grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4` | KPI row; with 3 items use `xl:grid-cols-3`, never leave a hole |
| G03 | Reflowing gallery | `grid gap-6 grid-gallery` | as many columns as fit, no breakpoints; `auto-fill` keeps empty tracks, `auto-fit` collapses them and stretches few items |
| G04 | Sidebar shell | `grid min-h-dvh grid-cols-1 lg:grid-shell`; sidebar hidden or drawer below `lg` | content column must be `minmax(0, 1fr)` |
| G05 | Form, two columns | `grid gap-4 md:grid-cols-2`; full-width field `md:col-span-2` | one column until `md`; pair only short related fields |
| G06 | Label / value list | `<dl class="grid grid-dl gap-x-4 gap-y-2">` with `dt` / `dd` pairs | labels align to the widest label, values truncate or wrap |
| G07 | Stack without absolute | container `grid`; every child `col-start-1 row-start-1`; align with `self-*` / `justify-self-*` | overlay, caption over image, loading veil, before/after: the container sizes to the largest child, unlike absolute |
| G08 | Subgrid alignment | parent `grid gap-6 md:grid-cols-3`; each card `row-span-3 grid grid-rows-subgrid gap-2` | card titles, bodies and footers line up across cards even when one title wraps |
| G09 | Equal-height rows | `auto-rows-fr` | every row as tall as the tallest anywhere in the grid; use only for uniform tiles |
| G10 | Centre | `grid place-items-center` | one child, both axes; simpler than flex for a lone item |
| G11 | Blowout guard | custom template with `minmax(0, 1fr)`; item `min-w-0` if it is a plain wrapper | **trap pair**: `1fr 1fr` with a long URL makes one column swallow the other |

## Trap table

| Symptom | Cause | Fix |
|---|---|---|
| Page scrolls sideways on mobile, extra empty columns appear | `col-span-N` without breakpoint prefix in a grid that has fewer columns there | prefix the span with the same breakpoint as the columns (G01) |
| One column wider than the others, page overflows | custom template uses `1fr` (= `minmax(auto, 1fr)`) and content is wide | `minmax(0, 1fr)` (G11); for a plain wrapper item, `min-w-0` too |
| Cards in a row have different heights | `items-start` / `items-center` on the grid, or card not filling (`h-full` missing on an inner wrapper) | keep default stretch; card is `flex flex-col` with body `flex-1` (flex F04) |
| Card contents misalign between cards (titles of different lengths) | each card lays out alone | subgrid (G08) |
| Last row has a hole | item count does not match columns | change column count for that count (G02), or `grid-gallery` |
| `gap` plus item margins doubles the space | margins on items | remove margins; only `gap` |
| Items reorder and tab order jumps | `grid-flow-dense`, explicit `row-start` / `order-*` | keep DOM order equal to visual order |
| Overlay made with absolute does not size the box | absolute leaves the flow | grid stack (G07) |
| Fixed-height row cuts content | `grid-rows-N` or `auto-rows-fr` with uneven content | `auto-rows-auto` (default); `fr` rows only for uniform tiles |

## Checks before calling it done

- [ ] Every `col-span-*` / `col-start-*` carries the same breakpoint as the `grid-cols-*` it relies on.
- [ ] Every custom template is an `@utility` with `minmax(0, 1fr)`, never `grid-cols-[...]`.
- [ ] Row combinations are the allowed ones (12 · 6+6 · 8+4 · 4+4+4 · 3+3+3+3).
- [ ] At 360px the grid is one column and nothing overflows.
