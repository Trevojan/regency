---
name: tailwind-audit
description: "Regency tailwind-audit. Audit, clean up and build the frontend of a project that uses Tailwind CSS against a written design-system norm. Runs a deterministic scan for token, spacing, accessibility and setup violations, works through the manual rules in separate passes, renders the result headlessly at mobile, tablet and desktop widths in light and dark mode, and carries a layout knowledge base (flex, grid, absolute) for when a component's position is confusing, plus canonical component samples. Use when asked to 'audit the frontend', 'organise the Tailwind', 'clean up the UI', 'check the design system', 'why is this element here / not here', 'fix this layout', 'build this screen', or before shipping a screen. Use for /regency:tailwind-audit."
argument-hint: "[path | 'layout' <symptom> | 'render' <page>]"
---

# tailwind-audit

Why this exists: "organise the whole frontend" in one request makes an agent skim. This skill replaces that with a fixed method: scan everything for one rule at a time, report coverage, render to see, then edit by category.

## What is where

| Need | Read |
|---|---|
| Which rule applies | `references/norm.md` (passes P1–P7, rule ids R## / M##) |
| A position is confusing, a box overflows, a menu is clipped, `z-50` loses | `references/layout/README.md` → triage, then `layout/flex|grid|absolute/SPEC.md` |
| How a component should be written | `references/components/README.md` → the sample file |
| Tokens and named layout templates | `references/theme.css`, `references/layout/utilities.css` |
| The project's own frontend documentation (brief, tokens, views, components, rules) | `<guidelines>/.ux/README.md`; none yet: `/regency:ux-init` scaffolds it from `library/templates/ux/` |

The layout folder holds no design: it stays valid after any redesign. The design layer (`norm.md`, `theme.css`, `components/`) is what changes when the design system does. If the project has its own norm, it replaces the design layer; the layout layer still applies.

A project with `<guidelines>/.ux/` (scaffolded by `/regency:ux-init`) carries its own design layer: audit against `.ux/` and its tokens (`python scripts/ux.py check <guidelines>/.ux/.tokens/tokens.json`), with this skill's layout layer, render pipeline and pass method. This folder's norm is the default for **data apps** (dashboards, tables, forms) with no `.ux/`.

## Precedence

1. The user's message. 2. The project's own `CLAUDE.md` / `.guidelines/` / design doc. 3. The project's `.ux/`, else `references/norm.md`. If the project defines its own tokens or scale, audit against those and say so in one line.

## Scripts

| Script | Does | Needs |
|---|---|---|
| `scripts/audit.py <dir>` | regex scan, counts per rule, `file:line` per finding; `--max 0`, `--json`, `--ignore R16` | Python 3 |
| `skills/tailwind-audit/scripts/preview.py` | pastes body fragments into `references/render-shell.html`, adds Tailwind v4 browser build + tokens + layout utilities to `<head>`; `--wrap a.html b.html` for any fragment (e.g. a project component), `--out DIR` | Python 3 |
| `scripts/shoot.mjs <page.html>` | headless screenshots over the DevTools protocol, waits for Tailwind's CSS; `--widths 360,768,1280 --themes light,dark`, `--probe` (page overflow, culprits, non-clipping truncates), `--before "<js>" --viewport` (open a menu or dialog first) | Node ≥ 22, local Edge or Chrome, network for the CDN |
| `references/layout/debug.js` | console helpers: `outlineAll`, `chain`, `containingBlock`, `stackingContexts`, `overflowCulprits`, `stickyScroller` | any browser |

Render through `shoot.mjs` when no interactive browser can open local pages. With an interactive browser, `preview.py --out DIR` and open the files.

## Method

1. **Detect the stack.** Read `package.json`, the CSS entry and any `tailwind.config.*`. Record: Tailwind major version (v3: `tailwind.config.js`, `@tailwind base`; v4: `@import "tailwindcss"`, `@theme`), framework, where tokens live, whether a project norm exists, and which design layer applies (data app or workspace). On v3, tokens map to `theme.extend`; keep going.
2. **Scan.** `python scripts/audit.py <src>`. The counts are the evidence: state files scanned and class attributes seen. Do not summarise from a partial look.
3. **Triage.** Group findings by pass (P1 setup/tokens … P7 markup). Counts per rule with severity.
4. **Manual passes.** One pass at a time, every file that renders UI, its `M##` rules, `file:line` per finding. Never mix passes in one edit sweep. Compare against the matching sample in `references/components/`.
5. **Render.** Never call a screen done from reading classes. Static HTML: `shoot.mjs` directly. Framework app: run the dev server, or extract the component's rendered HTML and `preview.py --wrap` it. Capture 360, 768, 1280 in light and dark; run `--probe` at 360 (must report `pageScrolls:false` and no `truncateNotClipping`). Check focus with Tab, equal card heights, contrast of the pairs actually used. If rendering was impossible, say so.
6. **Position problems.** When something sits in the wrong place, follow `references/layout/README.md` triage: find the box, read its chain, classify the symptom, fix at the lowest box that owns the cause, re-render. Cite the pattern id (F##, G##, A##) in the change note.
7. **Fix on approval.** Report first, edit after a yes unless the user already said to apply. One category per change: tokens → type/spacing → layout → components → a11y. Each step keeps the build green. Prefer the root (shared component, `@utility`) over 40 call sites. Run the formatter (`prettier-plugin-tailwindcss`) last; do not review ordering diffs.
8. **Re-scan and re-render.** Before/after counts per rule; screenshots of the changed screens. Remaining items are listed, not hidden.

## Boundaries

- Repos the user does not own: study and document on a separate branch, apply no fixes.
- Do not change product behaviour or copy meaning; copy rules (M24) touch casing, punctuation and word consistency only.
- A rule that fights the project's reality is reported as a norm proposal (see `components/README.md`, "Norm gaps"), never silently allowed or silently "fixed".
- Never invent contrast numbers. Measure, or label them calculated.
- Browser-build trap: never write the Tailwind import line inside a `text/tailwindcss` style element, not even in a comment. The build looks for that text and skips its own import (no preflight, no utilities, no error).

## Report format

Status as a topic list with `done / left / blocked`, each with percentage and fraction and its method, e.g. `P1 tokens: 60% - 6/10 rules clean, by audit.py re-scan`.

```
Stack: Tailwind v4 · React · tokens in src/index.css
Coverage: 142 files, 1 310 class attrs (audit.py) · rendered: 3 screens x 3 widths x 2 themes (shoot.mjs)
P1 done 100% - 8/8 · P2 left 50% - 4/8 · ...
Findings (before -> after): R01 87 -> 0 · R02 23 -> 4 · ...
Probe @360: pageScrolls false · truncateNotClipping 0
Not covered: <what was not looked at>
Proposals for the norm: <rules that did not fit>
```

End with an assumption line only if something was really assumed.

## Scanner notes

`audit.py` is regex per line over `.html .jsx .tsx .vue .svelte .astro .css .js .ts .mdx`, skipping `node_modules`, `dist`, `build`; comments and `@theme` blocks are blanked first. Class strings split across lines, built with template literals or `cn()` may hide matches (false negatives). R16 only catches the plain-wrapper truncate trap when wrapper and child sit on consecutive lines; `shoot.mjs --probe` is the reliable check. The scanner never edits files. Extend a rule in the `RULES` table; keep ids stable so reports stay comparable.
