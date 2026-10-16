# Frontend norm (condensed, for auditing)

Source of truth: this file and `theme.css`, for Tailwind v4. They were taken from the Regent's design-system document "Frontend Design System — Base para Apps" (a private claude.ai doc, not needed to use this skill); `§` keeps that document's section numbers. A change to the norm is made here first. If the project has its own design document, it wins; say so in one line and audit against it.

Canonical markup for each component: `components/` (catalogue in `components/README.md`). Layout mechanics and traps, independent of this design: `layout/` (pattern ids F##, G##, A##).

Principles in precedence order: readability > aesthetics · one scale for everything (4px grid, no arbitrary values) · hierarchy by weight and text colour, not background · semantic colour has one meaning · predictable density · explicit states.

## Passes

Run one pass at a time, over every file, before starting the next. `auto` = `skills/tailwind-audit/scripts/audit.py` finds candidates. `manual` = needs reading or rendering.

### P1 Setup and tokens (§1, §2)
| Id | Rule | Check |
|---|---|---|
| R05 | Browser build is `@tailwindcss/browser@4`, never `cdn.tailwindcss.com` (v3 Play CDN ignores `@theme`) | auto |
| R15 | `<style>` carrying `@theme` has `type="text/tailwindcss"` | auto |
| M00 | Browser build: no Tailwind import line inside the `text/tailwindcss` style, not even in a comment (the build then skips its own import: no preflight, no utilities, no error) | manual |
| R14 | `<html lang>` always set | auto |
| R01 | Semantic tokens only (`bg-surface`, `text-ink-muted`), never `bg-slate-50`, `text-white`, `bg-blue-600` | auto |
| R02 | No arbitrary values (`p-[13px]`, `text-[15px]`); use the nearest scale step | auto |
| R13 | No hex/rgb/hsl literals outside the `@theme` block | auto |
| R19 | State colours are `success`/`warning`/`danger`/`info`, never raw red/green | auto |
| M01 | Colour use matches the §2.2 table (e.g. `surface` not for page background, `primary` not for "positive") | manual |

### P2 Type, spacing, shape (§2.3–§2.6)
| Id | Rule | Check |
|---|---|---|
| R03 | No `font-bold` (700); use `font-semibold` | auto |
| R10 | Spacing steps only 1, 1.5, 2, 3, 4, 5, 6, 8, 12 (4px grid) | auto |
| R12 | Cards at rest: `border border-line`, no shadow. `shadow-xs` on secondary buttons and inputs; `shadow-md` dropdown, popover, hover card; `shadow-lg` modal, toast | auto (candidates) |
| R06 | z-index only 10 (sticky thead), 30 (page header), 40 (dropdown), 50 (modal), 60 (toast) | auto |
| R09 | `transition-colors duration-150 ease-standard`; `duration-200` panels; nothing over 300ms; `motion-reduce:transition-none` | auto |
| M02 | Radius grows with object (badge sm, button md, card lg, modal xl); child radius ≤ parent; `rounded-full` only badge, avatar, toggle | manual |
| M03 | Body 14px minimum, labels 12px; at most 3 text sizes per card; ritmo: card padding < gutter < section gap (5 < 6 < 8) | manual |
| M04 | Type roles match §2.3 table (H1 `text-2xl font-semibold tracking-tight`, KPI value `text-3xl font-semibold tabular-nums`, overline `text-xs font-medium uppercase tracking-wide text-ink-muted`) | manual |

### P3 Layout (§3)
| Id | Rule | Check |
|---|---|---|
| M05 | Shell: sticky header (`z-30`), centred `max-w-7xl`, `px-4 sm:px-6`, page header, 12-col grid | manual |
| M06 | Grid `grid-cols-1 gap-6 lg:grid-cols-12`; allowed rows 12, 6+6, 8+4, 4+4+4, 3+3+3+3; never 7+5 or 9+3 | manual |
| M07 | Same-row cards share height (`flex flex-col`, body `flex-1`); KPIs `sm:grid-cols-2 xl:grid-cols-4`, never 3 in a 4-col row | manual |
| M08 | At most one primary button per page, last on the right; forms one column to `md` | manual |

### P4 Components (§4)
| Id | Rule | Check |
|---|---|---|
| M09 | Controls share one height table: sm `h-8 px-3 text-xs`, md `h-9 px-4 text-sm`, lg `h-10 px-5 text-sm`. Same row = same size. Touch targets under `sm` ≥ 40px | manual |
| M10 | Button variants primary/secondary/ghost/danger/link with canonical classes; label is a 1–3 word infinitive verb; icon `shrink-0 aria-hidden`; icon-only has `aria-label` + `title`; loading keeps width, spinner, `aria-busy`, `disabled` | manual |
| M11 | Field = label + control + help/error; error uses `aria-invalid` + `aria-describedby`, message says what to do; mark optional, not required; width fits content | manual |
| M12 | Badge: dot + text + tone, never clickable; filters are `sm` buttons | manual |
| M13 | Card: `rounded-lg border border-line bg-surface`, header/body/footer, `px-5` (`px-4` in dense 4+ grids); clickable card is an `<a>` with no buttons inside | manual |
| M14 | KPI: neutral icon, colour only on the delta, delta has ▲/▼ + sign + comparison base; "up is bad" metrics colour by meaning | manual |
| M15 | Table: text left, numbers right with `tabular-nums`, row `h-12` (dense `h-10` only with 20+ rows), actions column last `w-px whitespace-nowrap`, sortable header is a `<button>` with `aria-sort`, sticky `thead` `z-10`, paginate 25 | manual |
| M16 | Tabs vs segmented (max 4 options); alert tones match badge, `role="alert"` for errors, page alert right under the page header | manual |
| M17 | Overlays: dropdown `z-40`, modal uses `<dialog>` with focus trap, Esc, focus return; toast `z-60`, 5s, errors persist | manual |
| R16 | `truncate` inside a plain `flex-1` wrapper needs `min-w-0` on the wrapper; `shrink-0` on neighbours (layout F02) | auto (candidates) + `shoot.mjs --probe` |
| M18 | Data cards define loading (skeleton with final shape), empty (why + what to do), error (what failed + retry); card height stable across states | manual |

### P5 Data visualisation and numbers (§5, §6)
| Id | Rule | Check |
|---|---|---|
| M19 | Chart type follows the question (§5.1); no dual Y axis, no donut with 5+ slices, no pie 3D; bars start at zero | manual |
| M20 | Series colours `data-1…6` in fixed order, same category = same colour app-wide; semantic colours only for good/bad data; not colour alone | manual |
| M21 | Chart height `h-72` (6/8 cols), `h-60` (4 cols); grid horizontal only; unit visible; `role="img"` + `aria-label` with the conclusion | manual |
| M22 | Every number declares definition, period, update time; formatted with `Intl.*` using page `lang`; missing value is `—` in `ink-subtle`, never `0`/`null`/`N/A` | manual |
| M23 | Text wrapping: controls and numbers `whitespace-nowrap`; titles `truncate`; descriptions `line-clamp-2`; prose `max-w-prose`; URLs/hashes `break-all` | manual |
| M24 | Copy: sentence case, no trailing period on titles/labels/buttons/badges, same action = same word | manual |

### P6 Interaction, accessibility, responsiveness, dark mode (§7)
| Id | Rule | Check |
|---|---|---|
| R04 | Never `outline-none` without `focus-visible` replacement | auto |
| R17 | Every interactive element has a visible `focus-visible` style (global rule counts) | auto (candidates) |
| R11 | Hover only recolours one scale step; never size, border width or layout | auto |
| R07 | Clickable things are `<button>`/`<a>`, never `<div onclick>` | auto |
| R08 | Every `<img>` has `alt` | auto |
| R18 | No centred paragraphs over 2 lines | auto (candidates) |
| M25 | Disabled = `opacity-50 pointer-events-none` + reason; selected = `bg-primary-50 text-primary-700`; active one step darker than hover | manual |
| M26 | Contrast ≥ 4.5:1 text, ≥ 3:1 control borders; every input has `<label for>`; `<th scope>`; one `<header>`, one `<main>`, labelled `<nav>`; keyboard reaches everything in visual order | manual |
| M27 | Responsive: no horizontal page scroll at 360px (only inner `overflow-x-auto`); below `sm` one column and stacked page header; mobile-first classes | manual |
| M28 | Dark mode only redefines semantic tokens; screens change no classes; elevation by `line-strong` border; contrast re-measured | manual |

### P7 Markup hygiene (§8.1)
| Id | Rule | Check |
|---|---|---|
| M29 | Class order: layout → box → border/radius → background → type → text colour → effects → states → responsive. Delegate to `prettier-plugin-tailwindcss` | tool |
| M30 | JS and test hooks use `data-*`, never style classes; page sections have kebab-case `id` + `aria-labelledby` | manual |
| M31 | A class block repeated more than 3 times becomes a component (framework) or `@utility` (no framework) | manual |

## Severity
high = breaks the norm's core promise (tokens, focus, semantics, wrong build). med = visible inconsistency. low = polish or candidate needing a look.

## Anti-patterns (§8.3), quick reference
Rainbow KPI icons · dual Y axis · donut with 5+ slices · `shadow-md` at rest · `font-bold` everywhere · placeholder as label · full-screen spinner · `N/A`/`null`/`0` for missing · status by colour only · `outline-none` bare · `p-[13px]` / `text-[15px]`.
