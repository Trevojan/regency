---
name: measure-changes
description: "Regency measure-changes. Read-only: say what would change, or what the working tree already changed, with numbers and impact radius (files, tests, norms, STALE slices, risk). Applies nothing, writes nothing. Use for /regency:measure-changes, or when the Regent says 'vê isso', 'diga o que mudaria', 'mede', 'how big is this change', 'what would this touch', without wanting it done."
argument-hint: "<intended change | 'tree'>"
disable-model-invocation: true
---

# measure-changes — measure, never apply

> **Root.** This file is `skills/measure-changes/SKILL.md`; the regency root is two directories
> above it. Paths like `library/…` and `scripts/…` are relative to that root. Read
> `library/conventions.md` and locate the project's documents with `library/layouts.md`.

This command **changes nothing**: no edit, no new file, no commit, no branch, no formatter run,
no migration. If you catch yourself about to apply something, stop — that is another command.
Reading, searching and running read-only queries are allowed.

## Modes

- **`tree`** (or no argument and the tree has uncommitted changes): measure what is already changed.
  Use `git status --short`, `git diff --stat` and `git diff` as evidence.
- **an intended change** (any other argument): measure what *would* change if it were done. Find the
  code by reading and searching; never by trying it.

## What to measure

1. **Footprint.** Files and approximate lines that would change; new vs modified vs deleted.
2. **Impact radius.** What references what you would touch (callers, consumers, routes, schemas).
   If the project has a virtual-path manifest, run
   `python scripts/vp.py code <file>` for each touched code file: the slices it returns are norms to
   read first and norms that would turn `STALE` after the change (`/regency:virtualpath:code`).
3. **Norms and decisions.** Which accepted decisions, business rules or constraints this touches or
   would contradict. A contradiction is a finding, not a footnote.
4. **Tests.** Which existing tests cover it, which would have to change, which are missing.
   Project rules about tests (e.g. a separate test pass) are stated, not applied.
5. **Docs that would move.** The guideline documents to update at the end of the task.
6. **Cost and risk.** Size (S/M/L with the reason), reversibility, data/migration exposure, anything that
   touches cloud, production or shared data (flag; do not act).
7. **What was not measured.** Name it. A measurement that hides its blind spots is an estimate wearing
   a number.

## Output

```text
Change     <one line: what, and mode (tree | intended)>
Footprint  <n> files (<m> modified · <a> new · <d> deleted), ~<lines> lines
Radius     <consumers/callers/slices affected>, evidence: <command or file>
Norms      touches: <ids> · contradicts: <ids or none>
Tests      covering: <n> · to change: <n> · missing: <n>
Docs       to update: <list>
Risk       <S|M|L> — <reason>; reversible: <yes|no, how>
Not measured  <list>
Verdict    <safe to apply as scoped | apply after <decision> | do not apply: <why>>
Assumed X because the order did not say Y. Next time: <rewritten order>.   ← only if you assumed
```

Keep it short: numbers and names, no narrative. Offer exactly one next command (for example
`/regency:proceed` or `/regency:team <unit>`), and do not run it.
