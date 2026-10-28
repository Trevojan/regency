---
name: init
description: "Regency init. Scaffold the .guidelines/ structure (sources, decisions, plan, orders, constraints, changelog, shortcuts, history), a root CLAUDE.md and README into a project, from the bundled template. Names every path before creating it and never overwrites. Use for /regency:init, or when a project has no guidelines and the Regent wants them: 'start a new project', 'create the guidelines', 'set up .guidelines'."
argument-hint: "[target directory]"
disable-model-invocation: true
---

# init — scaffold the guidelines

> **Root.** This file is `skills/init/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` first.

The template is `library/templates/guidelines/`. It carries the project's memory *with the
repository*: `CLAUDE.md` (what the harness reads on its own) points at the shortcuts index, and the
index points at everything else.

## Procedure

1. **Target.** The argument, else the current repository root. If it is not a project directory, ask.
2. **Look before creating.** Probe with `library/layouts.md` §1. If a guidelines root already exists,
   stop: report what is there and offer to *fill gaps only*.
3. **Name every path first.** List each file and folder you would create (read the template tree) and
   ask for a yes in one pop-up. Create exactly those paths, nothing beyond them. A path created without
   being named is a decision nobody took.
4. **Copy, never overwrite.** Copy the template into the target. If a file exists (a `CLAUDE.md`, a
   `README.md`, a `.gitignore`), do not replace it: write the template version next to it as
   `<name>.template` and say so, or merge only the missing lines after asking. Then, before filling
   anything, `python scripts/migrate.py stamp`: it writes `.shortcuts/regency.json` (the installed version
   and the fingerprints of the files just copied), which the version gate and `/regency:update` read;
   name it among the paths of step 3.
5. **Fill the holes.** The template's only gaps are `⟨…⟩` fields; each one says what it expects. Fill
   those you can answer from facts in the repository (name, one-line description, the verification
   command) and cite the source; leave the rest as `⟨…⟩` and list them as open questions. Never invent.
   Order that avoids rework: `CLAUDE.md` → `.shortcuts/README.md` ("Where I am" and the five-line map)
   → `.constraints/README.md` ("Of the artefact") → the rest only when there is something to record. An
   empty axis is honest; an invented one lies.
6. **The ledger.** The template includes `.shortcuts/.virtual/` with an empty `ongoing.json` (the work
   ledger: what is ongoing vs backlog), an empty `manifesto.json` (norm ↔ code lineage) and a short
   README. List them among the paths you name in step 3; agents keep the ledger current from then on.
7. **Orders.** The four standard Order templates live in regency (`library/orders/`), not in the
   project. Do not copy them. Filled Orders go to `.orders/ORD-####/` when the Regent opens one.
8. **Report** the created paths, the holes that remain, and the one next step. Do not commit
   (`/regency:arrange-cycle-commit` does that).

## Rules the structure carries (do not weaken them while scaffolding)

- The index points, never copies. A fact in two places is a defect.
- Prose states the present, never the correction.
- An agent does not ratify a norm it wrote.
- Axes: `.sources` (facts), `.decisions` (rules), `.plan` (what next), `.orders` (contracts),
  `.constraints` (prohibitions), `.changelog` (what changed), `.shortcuts` (the index); `.history` sits
  beside them as the attic, not an axis. The four middle ones read as a cycle:
  decide → schedule → commission → record.
