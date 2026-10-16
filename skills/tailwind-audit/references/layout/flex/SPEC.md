# Flex

**Use flex** when items run in one direction and their own content decides their size: bars, toolbars, the inside of a button, a media object, a card's header/body/footer column. If items must also line up with the row above or below, use grid.

## Model

- One **main axis** (`flex-row`, the default, or `flex-col`) and one **cross axis**.
- `justify-*` acts on the main axis, `items-*` on the cross axis, `self-*` on one item, `content-*` only on wrapped lines.
- Default `items-stretch`: every item fills the cross axis. This is what gives equal heights in a row; `items-center` or `items-start` removes it.
- `flex-col` swaps the axes: `justify-*` becomes vertical.

## Sizing: how an item gets its width

Each item starts at its **basis**, then the free space is shared by **grow**, or the shortage is taken back by **shrink**.

| Utility | `flex` value | Means |
|---|---|---|
| `flex-1` | `1 1 0%` | ignore content, share space equally → equal columns, "take the rest" |
| `flex-auto` | `1 1 auto` | start from content, then grow/shrink |
| `flex-initial` | `0 1 auto` | default: content size, may shrink |
| `flex-none` | `none` | content size, never grows or shrinks |
| `grow` / `shrink-0` | | change one factor only |

**The rule behind most flex bugs.** A flex item has `min-width: auto`, which means it never shrinks below its content's minimum width. A long word, URL, `truncate` child, table or `<pre>` therefore pushes the item, its row and finally the page wider. Fix: `min-w-0` on the item (and on every flex item between it and the row that has the width). In a `flex-col` the same is true for height: `min-h-0` lets a `flex-1` child shrink so its scroller can scroll.

**The exemption that hides the bug.** An item whose own `overflow` is not `visible` (and `truncate` includes `overflow-hidden`; `overflow-y-auto` too) gets an automatic minimum of 0. So `<p class="flex-1 truncate">` directly in the row works, and the same text wrapped in a plain `<div class="flex-1">` breaks. That is why the bug appears "randomly" after someone adds a wrapper for a subtitle. Rule of thumb: every plain wrapper that is a flex item and holds text or a scroller gets `min-w-0` (row) or `min-h-0` (column).

## Patterns (rendered in `samples.html`)

| Id | Pattern | Classes | Notes |
|---|---|---|---|
| F01 | Bar: start / end | row `flex items-center justify-between gap-4`; start `min-w-0`; end `flex shrink-0 items-center gap-2` | app header, card header, toolbar |
| F02 | Truncating middle | row `flex items-center gap-2`; icon `shrink-0`; text wrapper `min-w-0 flex-1`, its lines `truncate`; trailing `shrink-0` | **trap pair**: wrapper without `min-w-0` overflows the row |
| F03 | Push to the edge | `ms-auto` on the first item to push (or `mt-auto` in a column) | avoids an extra wrapper; use instead of `justify-between` when only one item moves |
| F04 | Column with pinned footer | `flex flex-col`; body `flex-1`; footer last | equal-height cards in a grid row, page `min-h-dvh flex flex-col` with `main` `flex-1`. **Trap pair**: body without `flex-1` leaves footers at different heights |
| F05 | Scroll inside a column | parent `flex flex-col` with a height; each plain `flex-1` wrapper on the way `min-h-0`; scroller `flex-1 overflow-y-auto` | **trap pair**: wrapper without `min-h-0` spills past the panel |
| F06 | Wrapping toolbar | `flex flex-wrap items-center gap-2` | filters, chips; `gap` handles both axes, `space-x-*` breaks on wrap |
| F07 | Stack → row | `flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between` | page header: title over actions on mobile, side by side from `sm` |
| F08 | Baseline | `flex items-baseline gap-1` | a number and its unit, label and value of different sizes |
| F09 | Control content | `inline-flex items-center justify-center gap-2 whitespace-nowrap`; icon `size-4 shrink-0` | inside every button, badge, tab |
| F10 | Equal segments | container `flex`; each child `flex-1` | segmented control, full-width button pair; text width does not change segment width |
| F11 | Centre in an area | `flex items-center justify-center` (or grid G10) with a fixed height on the area | empty and error states; keep the area height stable across states |
| F12 | Media object | `flex items-start gap-3`; media `shrink-0`; text `min-w-0` | avatar + name/description, alert icon + message |

## Trap table

| Symptom | Cause | Fix |
|---|---|---|
| `truncate` shows no ellipsis, row is wider than its parent | item has `min-width: auto` | `min-w-0` on the truncating item and its flex ancestors (F02) |
| Icon gets squashed when text is long | icon shrinks like any item | `shrink-0` on icons, avatars, buttons beside text |
| Inner list grows the page instead of scrolling | `min-height: auto` in `flex-col` | `min-h-0` on the `flex-1` scroller (F05) |
| Cards' footers do not line up | body not `flex-1`, or row uses `items-start` | F04; leave the row on `items-stretch` |
| `flex-1` columns are unequal | content wider than the share, or `flex-auto` used | `flex-1 min-w-0` |
| `space-x-*` gap looks wrong after wrap or with a hidden child | margins, not gaps | `gap-*` |
| `justify-between` with one child puts it at the start | nothing to distribute | `ms-auto` on that child (F03) |
| `h-full` child does not fill a flex row | percentage heights need a definite parent height | rely on `items-stretch`, or `self-stretch` |
| Visual order differs from keyboard order | `order-*` / `flex-row-reverse` | change the DOM order instead |
| Image inside a flex item distorts | image is a flex item that stretches | wrap it, or `self-start` + `object-cover` with a fixed size |

## Checks before calling it done

- [ ] Every text that can be long has `min-w-0` on its flex item, or a `max-w-*`.
- [ ] Icons, avatars and controls beside text have `shrink-0`.
- [ ] No `space-x/y-*` on rows that can wrap.
- [ ] At 360px the row wraps or stacks (F06, F07) rather than overflowing.
