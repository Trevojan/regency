# Absolute, fixed, sticky and the top layer

**Use this family** when a box sits on top of another or sticks to an edge: a badge on an avatar, an icon inside an input, a menu under its button, a tooltip, a sticky header, a toast, a modal. If the overlapping box should still give its parent a size (caption over an image, loading veil over a card), use a grid stack (grid G07) instead: absolute boxes take no space.

## Model

| Position | Placed against | Takes space | Scrolls with page |
|---|---|---|---|
| `relative` | its own normal spot (offsets nudge it) | yes | yes |
| `absolute` | its **containing block** (below) | no | with its containing block |
| `fixed` | the viewport, unless an ancestor captures it (below) | no | no |
| `sticky` | its nearest **scroll container**, between `top-*` and its parent's edges | yes | until it sticks |
| top layer (`<dialog>` via `showModal()`, `popover`) | the viewport, above everything | no | no |

**Containing block of an absolute box** = the nearest ancestor that is positioned (`relative`, `absolute`, `fixed`, `sticky`) **or** has a `transform`, `translate`, `scale`, `rotate`, `filter`, `backdrop-filter`, `perspective`, `contain: paint/layout`, `will-change: transform` or `container-type`. No such ancestor → the page.

**A fixed box is captured by the same non-position list.** `fixed` inside a parent with `backdrop-blur`, any `translate-*`/`scale-*`, a `filter`, or `@container` is positioned against that parent, not the viewport. This is the most confusing bug in the family: the norm's own sticky header uses `backdrop-blur`, so a `fixed` menu or modal rendered inside it is trapped in the header. Use the top layer or render the overlay outside the header.

Tailwind v4 note: `translate-*`, `scale-*` and `rotate-*` set the individual `translate`/`scale`/`rotate` properties; they capture fixed descendants and create stacking contexts exactly like `transform`.

## Offsets and size

- `inset-0` = all four sides 0 (fills the containing block). `inset-x-0`, `inset-y-0`, `top-0`, `end-0`, `bottom-full` (just above), `top-full` (just below), `start-1/2`.
- Prefer logical `start`/`end` to `left`/`right`: they mirror in right-to-left languages.
- An absolute box is **shrink-to-fit**, capped by the containing block's width minus its offset. A tooltip anchored to a 32px icon wraps its text into a 32px column (A05): give it `w-max max-w-xs`.
- Opposite offsets size the box: `inset-x-0` makes it as wide as the containing block.
- Centring: `top-1/2 start-1/2 -translate-x-1/2 -translate-y-1/2`, or `inset-0 m-auto size-fit`, or (inside a control) `inset-y-0 start-3 flex items-center`.
- Absolute boxes take no space. Reserve it on the neighbour: `ps-9` on an input that has a 16px icon at `start-3` (A02).

## Stacking

`z-*` decides order **only among siblings inside the same stacking context**. A new context is created by: positioned element with a `z-index`, flex or grid child with a `z-index`, `opacity` < 1, any transform/translate/scale/rotate, `filter`, `backdrop-filter`, `isolation: isolate`, `mix-blend-mode`, `contain: paint`, `fixed`, `sticky`. A `z-50` inside a `z-10` context can never rise above a sibling of that context with `z-30` (A09). Fixes, in order of preference: render the overlay in the top layer; move it out of the trapping ancestor; raise the ancestor; add `isolate` to components so their internal `z-*` cannot leak.

Norm scale: `z-10` sticky table head, `z-30` page header, `z-40` dropdown and popover, `z-50` overlay and modal, `z-60` toast. The top layer ignores `z-*` entirely.

## Clipping

`overflow-hidden`, `overflow-auto`, `overflow-x-auto` and `overflow-clip` on any ancestor between an absolute box and its containing block cut it off. Common case: a card with `overflow-hidden` (to clip rounded corners) whose row menu is clipped at the card edge (A04). Fixes: top layer (`popover`), or move the clipping to the child that needs it (round the image, not the card). Note `overflow-x-auto` also makes `overflow-y` compute to `auto`, so a horizontally scrolling table wrapper clips vertically too.

## Sticky rules

- Needs an offset (`top-0`). Without one it never sticks.
- Sticks inside its **nearest scrolling ancestor**. Any ancestor with `overflow-hidden/auto/scroll/clip` becomes that container; if that ancestor does not itself scroll, the element never moves. `stickyScroller(el)` in `debug.js` names it.
- Stays inside its parent: a sticky element in a parent of the same height has nowhere to travel.
- Sticky table head: put `sticky top-0 z-10` on `thead` (or on each `th` for older engines) and give the scrolling wrapper a height (`max-h-96 overflow-auto`). Inside the norm's `overflow-x-auto` table wrapper, the head sticks to that wrapper, not to the page (A07).

## Top layer

- Modal: `<dialog>` opened with `showModal()`: above everything, background inert, `Esc` closes, focus moves in and returns to the opener; the backdrop is `backdrop:` styled. No `z-*` needed, no clipping possible.
- Menus and popovers: `popover` attribute + `popovertarget` on the button: light-dismiss, top layer, no JS. By default the browser centres it in the viewport; anchor it to its button with CSS anchor positioning (`anchor-name` / `position-anchor` / `position-area`) where supported, or a positioning library (Floating UI) otherwise. Check current browser support before relying on anchor positioning.

## Patterns (rendered in `samples.html`)

| Id | Pattern | Classes | Notes |
|---|---|---|---|
| A01 | Corner anchor | parent `relative inline-flex`; child `absolute -end-1 -top-1` | notification dot, count on avatar or icon button. **Trap pair**: parent without `relative` sends the dot to the page corner |
| A02 | Icon inside a control | wrapper `relative`; icon `pointer-events-none absolute inset-y-0 start-3 my-auto size-4`; input `ps-9` | select chevron: same at `end-3`, select `pe-9 appearance-none`; `pointer-events-none` so clicks reach the input |
| A03 | Full cover | parent `relative`; cover `absolute inset-0` | loading veil, stretched link (`after:absolute after:inset-0` on the card's title link) |
| A04 | Menu under a trigger | wrapper `relative inline-block`; menu `absolute end-0 top-full z-40 mt-1 w-max min-w-48` | **trap pair**: inside an `overflow-hidden` card the menu is cut |
| A05 | Tooltip | anchor `relative inline-flex`; tip `absolute bottom-full start-1/2 mb-2 w-max max-w-xs -translate-x-1/2` | **trap pair**: without `w-max` the text wraps to the anchor's width |
| A06 | Fixed captured by an ancestor | — | **broken only**: `fixed` inside a `backdrop-blur` box lands in the box, not the viewport |
| A07 | Sticky header and table head | header `sticky top-0 z-30`; scroll wrapper `max-h-* overflow-auto`, `thead` `sticky top-0 z-10` | head sticks to the wrapper; give the wrapper a height |
| A08 | Centred overlay in a box | `absolute inset-0 m-auto size-fit` | spinner over a chart, empty-state icon |
| A09 | Stacking context trap | — | **trap pair**: `z-50` child of a `z-10` parent stays under a `z-30` sibling; fixed by lifting the parent (`z-40`) or using the top layer |
| A10 | Top layer | `<button popovertarget="m">` + `<div id="m" popover>`; `<dialog>` + `showModal()` | escapes every `overflow` and stacking context |

## Trap table

| Symptom | Cause | Fix |
|---|---|---|
| Badge or icon flies to the page corner | no positioned ancestor | `relative` on the intended parent (A01) |
| Absolute box placed against the wrong ancestor | a closer ancestor is positioned or transformed | `containingBlock(el)` names it; move `relative` or remove the transform |
| `fixed` modal or toast stays inside a card/header | ancestor has `backdrop-blur`, `filter`, `translate-*`, `scale-*` or `@container` | top layer (A10), or render outside that ancestor (A06) |
| Menu or tooltip cut off | `overflow-*` ancestor | top layer, or move the clipping (A04) |
| Page scrolls sideways at 360px, but every visible box fits | an absolute box (often `sr-only` in a `th`) inside an `overflow-x-auto` wrapper that is not its containing block: overflow clips only boxes whose containing block is the scroller or inside it | `relative` on the scroll wrapper; `overflowCulprits()` names the box |
| Tooltip text one word per line | shrink-to-fit against a small anchor | `w-max max-w-xs` (A05) |
| `z-50` element under a `z-30` one | stacking context | `stackingContexts(el)`; lift the context, `isolate`, or top layer (A09) |
| Click on the input icon does nothing | icon sits on top of the input | `pointer-events-none` on the icon (A02) |
| Text runs under the icon | absolute takes no space | `ps-9` / `pe-9` on the input (A02) |
| Sticky never sticks | no `top-*`, an `overflow-*` ancestor that does not scroll, or parent no taller than the item | `stickyScroller(el)`; fix the ancestor (A07) |
| Full-screen overlay leaves a gap on mobile | `h-screen` = `100vh` ignores browser chrome | `inset-0` or `h-dvh` |
| Layout jumps when a menu opens | menu is `relative`/static, so it takes space | `absolute` or `popover` |

## Checks before calling it done

- [ ] Every `absolute` has an intended `relative` parent, and `containingBlock(el)` agrees.
- [ ] No `fixed` element lives inside a transformed, filtered or blurred ancestor.
- [ ] Menus, popovers and tooltips are not clipped at the card or table edge; modals use `<dialog>`.
- [ ] `z-*` values are only the norm's scale; nothing above `z-60`.
- [ ] Icons over inputs have `pointer-events-none` and the input reserves the space.
