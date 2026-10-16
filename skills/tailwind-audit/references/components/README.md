# Component samples

Canonical markup for every component in the norm, built from semantic tokens (`references/theme.css`) and the layout patterns (`references/layout/`). Copy a block whole and change only its content. Each file is a **body fragment**: render it with `python scripts/preview.py`, which pastes it into `references/render-shell.html`.

These files are the design-specific layer. After a redesign that keeps the token names, they stay valid and only `theme.css` changes. After a redesign that changes components, rewrite this folder; `layout/` stays.

## Catalogue

| Component | File · `data-pattern` | Layout patterns | Norm |
|---|---|---|---|
| Reference page (header, page header, KPI row, chart rows, table card, pagination) | `shell.html` | A07, F01, F07, F06, G02, G01, F04, F02 | §3, §4.5–§4.7, §4.11 |
| Button: variants, sizes, icon-only, loading, disabled | `controls.html` · `button` | F09, F06 | §4.1, §4.2 |
| Field: label, help, error, optional, width by content | `controls.html` · `field` | G05 | §4.3 |
| Select, search input, textarea | `controls.html` · `field` | A02 | §4.3 |
| Checkbox, radio | `controls.html` · `field` | F09 | §4.3 |
| Segmented control | `controls.html` · `segmented` | F10 | §4.8 |
| Tabs | `controls.html` · `tabs` | F01, overflow-x-auto row | §4.8 |
| Badge tones | `data.html` · `badge` | F09 | §4.4 |
| Card anatomy, progress, clickable card | `data.html` · `card` | F01, F04, G01 | §4.5, §5.1 |
| KPI card (incl. "up is bad") | `shell.html` | F01 | §4.6 |
| Table: sortable header, sticky head, numbers | `data.html` · `table` | A07 | §4.7 |
| Label / value detail | `data.html` · `detail-list` | G06 | — (see gaps) |
| Avatar: sizes, group, with text | `data.html` · `avatar` | F12 | §4.12 |
| Alert tones | `feedback.html` · `alert` | F12 | §4.9 |
| Data states: loading, empty, error | `feedback.html` · `data-states` | F11, G01 | §4.13 |
| Toast | `feedback.html` · `toast` | A06 | §4.10 |
| Dropdown menu (absolute and popover) | `overlays.html` · `dropdown` | A04, A10 | §4.10 |
| Modal (static mock and `<dialog>`) | `overlays.html` · `modal` | A10, G10 | §4.10 |
| Tooltip | `overlays.html` · `tooltip` | A05 | — (proposal, see gaps) |

## Rules the samples follow

- Visible text is sample data only. Explanations, ids and rationale live in HTML comments (`library/rules/ui-text.md`).
- Every interactive element carries the focus style; every icon is `aria-hidden`; icon-only buttons have `aria-label` and `title`.
- Spacing, z-index and colours stay on the norm's scales. `scripts/audit.py references/` reports zero findings except the deliberate F02 broken case.
- Harness-only attributes, never part of a product copy: `data-pattern`, `data-case`, `data-room`, `data-force-open`, and the `demo` / `demo-fill` classes in layout samples.

## Norm gaps found while building the samples

Proposals for the norm's owner. Nothing here is decided; the samples mark each spot in a comment.

| # | Gap | Where it shows | Proposal |
|---|---|---|---|
| 1 | Dark theme does not redefine `primary-100`, so avatars (`bg-primary-100`) stay a light blob in dark mode | `shell.html` header, `data.html` avatars | add `--color-primary-100` (and check `primary-200`, `primary-500`) to the dark block |
| 2 | §5.3 asks for `h-60` charts in 4-column cards and also "same row, same height"; an 8+4 row cannot satisfy both | `shell.html` chart row | in a mixed row, every chart takes the row's tallest height (`h-72`) |
| 3 | No tooltip component; only the chart tooltip is styled (§5.3) | `overlays.html` tooltip | adopt the sample: `bg-ink text-ink-inverse text-xs rounded-md px-2 py-1`, A05 placement, shown on hover and focus |
| 4 | No label/value (detail) list component | `data.html` detail list | adopt G06 (`grid-dl`) with `dt` in `ink-muted` |
| 5 | Row-menu placement inside the table card: the card is `overflow-hidden`, so an absolute menu is clipped | `shell.html` table | row menus are popovers (A10) |
| 6 | Sticky table head inside the norm's `overflow-x-auto` wrapper sticks to the wrapper, not the page; and that wrapper needs `relative` or `sr-only` labels widen the page at 360px | `shell.html`, `data.html` | wrapper is `relative overflow-x-auto`; sticky head only with a `max-h-*` on the wrapper |
| 7 | The norm's header uses `backdrop-blur`, which captures `fixed` descendants | `shell.html` header | menus from the header are popovers; toasts and modals render outside it |
| 8 | Touch targets: md controls are 36px; §4.1 asks ≥ 40px below `sm` only for "main actions" | `shell.html` at 360px | define which actions count as main, or use `h-10 sm:h-9` on all page-header controls |
