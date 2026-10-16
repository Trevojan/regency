---
name: ux-init
description: "Regency ux-init. Scaffold a project's complete frontend documentation into the .ux/ folder of its guidelines root, from the bundled template: an index README, the brief, foundations (principles, colour, type, space, iconography, content), role-named tokens with a generated stylesheet, interaction patterns and state models, view archetypes, a component catalogue with ready CSS, accessibility, assets, a rendered sample, UX-UI rules and a changelog — a README in every folder. Then fills the brief with the Regent and creates one folder per view and component. Names every path before creating it; never overwrites. Use for /regency:ux-init, or 'document the frontend', 'start the UX docs', 'set up the design system docs' in a project."
argument-hint: "[guidelines root]"
disable-model-invocation: true
---

# ux-init — scaffold the frontend documentation

> **Root.** This file is `skills/ux-init/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` and `scripts/…` are relative to that root. Read `library/conventions.md` first.

The template is `library/templates/ux/`; its index is `library/templates/ux/README.md`. The engine is
`scripts/ux.py` (`plan`, `scaffold`, `brief`, `check`, `build`, `expand`). The playbook decides; the
script copies, checks and generates.

## Procedure

1. **Target.** The argument, else the project's guidelines root found with `library/layouts.md` §1.
   No guidelines root: offer `/regency:init` first and stop; `.ux/` lives beside the other axes.
2. **Look before creating.** If `<root>/.ux/` exists, report what is there; offer to fill gaps only.
3. **Name every path.** `python scripts/ux.py plan <root>` lists each file it would create and each that
   already exists. Show the list and ask for a yes in one pop-up. The template's folders are fixed;
   do not add or drop one at scaffold time.
4. **Scaffold.** `python scripts/ux.py scaffold <root> --yes`. It never overwrites: a file already
   there gets `<name>.template` beside it; an identical one is skipped. Report every `.template`.
5. **The brief, with the Regent.** Open `.ux/BRIEF.md`. Fill the holes the repository answers as fact
   (name, stack, paths, the engine and its levels) and cite each source. Ask the rest in pop-up waves,
   one section per wave, in the brief's order: Product → The artefact → The engine → Actors → The commit
   action → Views → Components → Commands → Vocabulary → Out of scope. Read both the option and the free
   text of every answer. Never guess a hole; a hole left open stays as an `ask`.
   `python scripts/ux.py brief <root>/.ux/BRIEF.md` after each wave: 0 FAIL before going on.
   Archetype `data app`: say the tailwind-audit norm fits better and ask whether to continue.
6. **Expand.** `python scripts/ux.py expand <root>/.ux` creates `.views/<Code>/README.md` for each view
   row and `.components/<Name>/README.md` for each component row with a contract, and refreshes both
   index tables. A component with no contract is skipped and reported: write its contract in
   `.components/README.md` first (the Regent ratifies it), then expand again.
7. **Tokens.** The tokens start from the Regent's Void/Paper palette. Change values only on request;
   then `ux.py check <root>/.ux/.tokens/tokens.json` (0 FAIL) and
   `ux.py build <root>/.ux/.tokens/tokens.json --out <root>/.ux/.tokens/theme.css`.
8. **The index.** Fill `.ux/README.md` "Where I am" from the facts: holes left, views and components
   documented, the date. Point the project's entry index (`.shortcuts/README.md`) at `.ux/README.md`
   with one line.
9. **Report** the created paths, the `.template` files, the holes left (as asks), and the one next step.
   Do not commit (`/regency:arrange-cycle-commit` does that).

## What the scaffold holds

| Path in `.ux/` | Holds |
|---|---|
| `README.md` | the index: where I am, the map, rules, precedence, commands |
| `BRIEF.md` | product, artefact, engine with severity and lifecycle mappings, actors, commit action, views, components, commands, vocabulary |
| `.foundations/` | principles and anti-patterns; `color.md`, `type.md`, `space-shape.md`, `iconography.md`, `content.md` |
| `.tokens/` | `tokens.json` (23 colour roles, two themes, type, space, radius, sizes, shadows) and the generated `theme.css` |
| `.patterns/` | interaction rules; `states.md` (severity, lifecycle, actors); `keyboard.md` |
| `.views/` | the seven archetypes, the views index, `_view.template.md`, one folder per view after expand |
| `.components/` | 41 contracts in 8 groups, the in-use index, `_component.template.md`, `components.css`, one folder per component after expand |
| `.accessibility/` | each guarantee with its check |
| `.assets/` | marks, icons, fonts: register and rules |
| `.samples/` | `workspace.html`: shell and main view, both themes |
| `.rules/` | `UX-UI-##` decisions that override the rest |
| `.changelog/` | interface changes, dated |

## Rules the scaffold carries (do not weaken them while filling)

- The index points, never copies: a value lives in `tokens.json`, a behaviour in `.patterns/`.
- Generated files (`theme.css`, the index tables between `ux:` markers) are never hand-edited.
- A UI rule changes in `.ux/` first, then in code; a deviation is a `UX-UI-##` the Regent ratifies.
- Screen text is terse; reasoning lives in comments and here (`library/rules/ui-text.md`).
- Black ground, never grey; colours named by role, never by value; contrast computed, never estimated.
