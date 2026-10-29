---
name: update
description: "Regency update. Bring a project to the installed regency: read its stamp, plan every operation the newer version needs (replace untouched scaffold files, put the new text beside edited ones, create, rename, move, delete, rewrite what regency owns, then stamp), apply the whole plan on the Regent's one yes in a clean git tree, and check. Never touches the project's own prose, its acts or .scope/. Use for /regency:update, when a command says the project needs an update first, or 'update this project to the new regency', 'migrate the guidelines'."
argument-hint: "[plan | check]"
disable-model-invocation: true
---

# update — fit the project to the installed regency

> **Root.** This file is `skills/update/SKILL.md`; the regency root is two directories above it, and
> `library/…`, `scripts/…` paths are relative to it. Read `library/conventions.md` once per session and
> `library/migrations/README.md` before the first update of a session.

The engine is `scripts/migrate.py`. It decides what changes; this playbook only runs it, shows it and
asks once. Run every command from inside the project.

## Procedure

1. **Gate.** `python <regency>/scripts/migrate.py gate`.
   - exit 2 (the project is newer): stop. Say so in its words and give the two plugin commands from
     `library/migrations/README.md` §3. Never move a project back.
   - exit 0 (agree): say "the project fits regency `<version>`", run `check`, and stop.
   - exit 1 (behind or unstamped): go on.
2. **Plan.** `python <regency>/scripts/migrate.py plan`. Show it as it prints: one numbered line per
   operation, the refused ones, the plan id. Group nothing and drop nothing.
3. **Clean tree.** `apply` refuses uncommitted changes and a folder that is not a git repository. If the
   tree is dirty, say which files, and offer `/regency:arrange-cycle-commit` first; do not stash or commit
   the Regent's work yourself.
4. **One yes.** One pop-up: "Apply plan `<id>` — `<n>` operations (replace, beside, create, rename, delete,
   rewrite, stamp)?", options *Apply* and *Do not apply*. Read the free text too. No yes, no apply.
5. **Apply.** `python <regency>/scripts/migrate.py apply --yes <id>`. A refusal (the plan changed, the tree
   got dirty) means: plan again and ask again.
6. **Check.** `python <regency>/scripts/migrate.py check` must exit 0.
7. **Ledger.** One item, state `review`: `regency update <from> -> <to>`, `where` the changed files and
   the plan id, `next` "merge the `.template` files by hand" when there are any.
8. **Report** in the shape below. Commit nothing; offer `/regency:arrange-cycle-commit`.

```text
regency update 2.6 -> 2.10 · plan UPD-1a2b3c4d · 9/9 applied (100%)
Replaced  7 untouched files     Beside  1 (.plan/README.md.template — merge by hand)
Renamed   0  Deleted 0  Rewritten 0  Created 0  Refused 0
Stamp     .guidelines/.shortcuts/regency.json -> 2.10   check: fits
```

## `plan` and `check` alone

`/regency:update:plan` runs steps 1–2 and stops: a dry run. `/regency:update:check` runs `check` and reports
its line.

## Boundaries

Never edits a file by hand to "help" the plan, never applies without the Regent's yes to that plan id,
never rewrites the project's own prose, an act or `.scope/`, never downloads anything, never commits.
