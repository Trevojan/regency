# Migrations — fitting a project to the installed regency

A project scaffolded by an older regency carries older structure: axis READMEs, ledger shapes, file names.
Ruling it with a newer regency means declaring exactly what changes from one version to the next, then
changing exactly that. `/regency:update` does it (`skills/update/SKILL.md`); `scripts/migrate.py` is the
engine, and `/regency:normalise` will share it. Decided with the Regent on 2026-10-28 (R10).

## 1. What regency owns in a project

Only what regency wrote. Everything else is the project's, and the project's text is input: never rewritten.

| Owned | How an update treats it |
|---|---|
| a **refresh** file of a scaffold (`scaffolds.json`): an axis README, a `.ux/` foundation or pattern | untouched since regency wrote it → **replaced** by the new text; edited by the project → the new text goes **beside** it as `<name>.template`, to merge by hand; missing where its folder exists → **created** |
| a **seed** of a scaffold: the root README, CLAUDE.md, CHANGELOG, the entry index, the ledger, the brief, the tokens | never touched: written once, then the project's |
| a path a **step** names (`steps.json`) | renamed, moved, deleted or rewritten exactly as the step says |
| the **stamp**, `<guidelines>/.shortcuts/regency.json` | rewritten last: the version, the fingerprints of the files that hold regency's current text, the history of updates |

Never touched, whatever a step says: an act (an Order, a gate sheet, a ladder plan, an opinion, a dated
handoff — the acts guard's own table), anything under `.scope/`, anything outside the guidelines root.
Such an operation is listed as **refused** in the plan.

"Untouched" is decided by fingerprint: the stamp's record of what regency wrote, or, for a project with no
stamp, any text a version ever shipped (`history.json`).

## 2. The gate

Every command that writes into a project first runs `python scripts/migrate.py gate`
(`library/conventions.md` §10):

| Exit | The project is | Say, and do |
|---|---|---|
| 0 | on the installed version, or has no guidelines | go on |
| 1 | behind it, or carries no stamp | "I need to update this before going on": stop and offer `/regency:update` |
| 2 | ahead of it | "I can't go on: this project is on a newer regency": stop; the plugin is what must be updated |

The session's resume line names a mismatch before anything is asked (`scripts/hook-resume.py`).

## 3. Where the new version comes from

The migrations ship **inside the plugin**: a project is brought to the regency that is installed, which is
the one that will rule it. A project newer than the plugin means the plugin is behind: update the plugin
from its marketplace (the regency repository), never the project from the network.

```bash
claude plugin marketplace update regency
claude plugin update regency@regency
```

## 4. One yes

`migrate.py plan` lists every operation with a number, and a plan id. The Regent approves the whole plan
with one yes; `migrate.py apply --yes <plan id>` runs it only when the id still matches a fresh plan and the
project is a git repository with a clean tree, so every operation can be reverted with git. It commits
nothing: the changes wait in the tree for `/regency:arrange-cycle-commit`.

## 5. Adding a step (maintainers)

When a version changes what a project must hold beyond its templates:

1. Add `{"to": "<new version>", "ops": [...]}` to `steps.json`. Paths are relative to the guidelines root.

   | `op` | Fields | Runs when |
   |---|---|---|
   | `mkdir` | `path` | the folder is missing |
   | `rename` (or `move`) | `path`, `to` | the source exists and the target does not |
   | `delete` | `path` | the file exists |
   | `rewrite` | `path`, `replace`: `[[old, new], …]` literal pairs | the file holds at least one `old` |

   Every op carries a `why`. A rewrite is only for a file regency owns (a ledger shape, a generated block):
   the project's prose is never a target. An op may also carry `before`: `["<script>.py", "<arg>", …]`, one
   of regency's own scripts, run with `--repo <project>` right before the op; a non-zero exit stops the plan
   there (what already ran stays in the tree, and git undoes it). Use it when an op would lose what a script
   must carry first: 2.12 runs `shortcuts.py migrate` (the old `fingerprints.json` into the one store) before
   deleting that file. The plan shows it as `[first: …]`; a `before` naming anything else is refused.
2. When a template changed, run `python scripts/migrate.py record` after the version bump: it files the
   templates' fingerprints under the new version in `history.json`. `scripts/doctor.py` fails while one is
   missing.
3. Prove the step on a copy of a real project from the previous version: `plan`, `apply`, `check`.

## Files

| File | Holds |
|---|---|
| `scaffolds.json` | each scaffold's template folder, how its paths map into the guidelines root, its seeds |
| `steps.json` | the explicit operations, by the version that needs them |
| `history.json` | every template fingerprint each version shipped (generated by `migrate.py record`) |
