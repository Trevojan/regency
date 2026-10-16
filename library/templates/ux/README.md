# ⟨product name⟩ — frontend documentation

⟨one line: what the product is, for whom⟩

Everything about how this product looks, reads and behaves lives here, beside the rest of the
guidelines, so a fresh context builds the same interface without re-deciding it. Scaffolded by
`/regency:ux-init`; filled from `BRIEF.md` first.

## Where I am

| Part | State |
|---|---|
| Brief | ⟨filled · holes left: n⟩ |
| Tokens | ⟨template values · project values⟩ — `python <regency>/scripts/ux.py check .tokens/tokens.json` |
| Views | ⟨n of m documented⟩ |
| Components | ⟨n of m documented⟩ |
| Last change | ⟨date — what, see `.changelog/README.md`⟩ |

## The map

| Folder | Holds | Read it when |
|---|---|---|
| `BRIEF.md` | the facts every other file depends on: product, artefact, engine, actors, the commit action, views, commands, vocabulary | first, always |
| `.foundations/` | principles, colour roles, type, space and shape, iconography, content | designing anything new |
| `.tokens/` | `tokens.json` (the values) and the generated `theme.css` | changing a value; wiring the stylesheet |
| `.patterns/` | interaction rules, the state models (severity, lifecycle, actors), keys | deciding how something behaves |
| `.views/` | one folder per view: layout, state shown, rules, states | building or changing a screen |
| `.components/` | the catalogue of contracts, one folder per component in use, `components.css` | building or changing a part |
| `.accessibility/` | the contrast, focus, semantics and keyboard rules, and how they are checked | before calling a screen done |
| `.assets/` | the product mark, icons, fonts: what exists and where | placing a mark or an icon |
| `.samples/` | a rendered page of the shell and the main view | starting the code; checking the stylesheet |
| `.rules/` | `UX-UI-##` decisions that override or extend this documentation | a rule here seems wrong for a case |
| `.changelog/` | what changed in the interface, dated | resuming after a pause |

## Rules this folder keeps

- **The index points, never copies.** A value lives in `tokens.json`; a behaviour in `.patterns/`; a
  screen in `.views/`. Other files name them.
- **The brief before the code.** A hole in `BRIEF.md` is an open question for the Regent, not a guess.
- **Generated files are never hand-edited.** `.tokens/theme.css` comes from `tokens.json`.
- **A UI rule changes here first, then in the code.** A deviation is a `UX-UI-##` in `.rules/`.
- **State the present.** Text that said "the rail has four views" becomes "five", not "five (was four)".

## Precedence

The Regent's message → `.rules/` (`UX-UI-##`) → this folder → regency's defaults.

## Commands

| Need | Run |
|---|---|
| holes left in the brief | `python <regency>/scripts/ux.py brief BRIEF.md` |
| check the tokens (roles, names, computed contrast) | `python <regency>/scripts/ux.py check .tokens/tokens.json` |
| rebuild the stylesheet | `python <regency>/scripts/ux.py build .tokens/tokens.json --out .tokens/theme.css` |
| one folder per view and component the brief names | `python <regency>/scripts/ux.py expand .` |
