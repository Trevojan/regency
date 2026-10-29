# History

Every version, newest first. Each section: what the version added, the Regent's decisions behind it
(`R<record>.<n>`), and the proof it carried. Decisions are quoted short; where a decision changed an earlier
one, the section says which.

---

## 2.13

2026-10-29 · branch `plumbing`, merged up to `testing`; `main` on the Regent's push · record R13

**Added**

- The plugin is described by its purpose (R13.1): AA works as a PO/DV/QA/DA team and the Regent decides at
  the review packet; the rules travel as files and scripts. 417 of the 500 characters an account accepts.
- The unit grammar is `M##.S##.T##` (R13.2, "no else"): `S##` is the step. `library/ids.md`, `hook_wire.UNIT`,
  conventions §11–§12, task granulation, orchestration, speed modes, the order and team playbooks, every suba
  spine. `conventions_check.py` (`steps`) fails on the old step letter outside `discard/`.
- The README is the repository's homepage, written like an AI-first SDK (R13.3): an SVG banner, shields.io
  pills, key features, seven install paths, a quick start, a Mermaid architecture, the API surface, runtime
  guarantees with the script that enforces each. `scripts/build.py` generates the version and count pills and
  the module map. The long form moved to `library/REFERENCE.md` (R13.4).
- MIT License, © 2026 Trevojan, shipped in the `.plugin`; `CONTRIBUTING.md` for the repository (R13.5).
- A heredoc body that is only data is never read as commands (R13.7): `guard_push.data_only()` feeds
  `guard-push`, `hook-hazard` and `hook-journal`. A body a shell reads stays; an unquoted body keeps its
  substitutions. This ended a false hazard watch set by text that merely named a destructive command.
- The pixel crown is regency's mark (`.github/assets/`).
- `.github/`: a security policy (private vulnerability reporting, scope: hooks, guards, install path), support
  and conduct pages, code owners, issue forms (defect, proposal; blank issues off), a pull-request template
  that holds the hook invariants, a doctor workflow (read-only token, no secrets, checkout pinned by SHA) and
  Dependabot for the Actions.
- README: install pinned to a release tag (`Trevojan/regency#v2.13`), release verification with `gh release
  verify`, how updates arrive, a security section.
- This folder, and `conventions_check.py` (`changelog`) failing when it does not name the version in force.
- The merge rule (conventions §4, the Regent, 2026-10-29): **update, never retrocede** — when two lines meet,
  the better resource stays whichever side it came from; keep what improves performance, efficiency or a
  bottleneck; drop what is useless, already made by existing means, or underused; destructive steps are left
  to the hooks to judge.

**Lines of work joined.** Git held two histories with no common root: `main` (2.2 baseline, 2.3) and
`plumbing` (2.4) on one; 2.8 → 2.13 on the other. A merge commit on `plumbing` joined them with 2.13's tree
whole, after checking that every 2.3 addition is in 2.13 verbatim or superseded and that 2.4 is superseded by
2.12's port. `testing` was created from it; `main`, an ancestor of the joined line, takes it on the Regent's
push. The branches `regency-2.10`, `plumbing-2.12` and `plumbing-2.13` retire as tags `archive/<name>`
(`CHECKPOINT.md` lists their tips).

**Proof.** doctor 0 fail (30 WARN: old level names in `library/orders/` and `library/team/`, suba alignment
stamps, machine-side installs); conventions selftest with the `steps` and `changelog` defects planted; guard-push
45/45, hook-hazard 77/77, health 63/63; heredoc mutants 4/4; CI green on the pushed branch.

---

## 2.12

2026-10-28 · built on branch `plumbing-2.12` (now `archive/plumbing-2.12`) · record R12

Four copies had split: the account's 2.11 (in no git), `regency-2.10`, the old `plumbing` (2.4) and the
Regent's folder (uncommitted, also 2.4).

- One 2.12 on one branch (R12.1, "Yes, all of it"): the installed 2.11 as baseline, the folder's automation
  work adopted (auto mode, headless routes: `library/automation.md`, `library/automode.json`,
  `library/headless.json`, `scripts/headless.py`, `scripts/install-automode.py`), R7 ported.
- One store (R12.2): R7's shortcuts keep no database of their own; file prints live in a `prints` table of
  idx's `index.sqlite`. Amends R7.2 and R7.4. A store holding only prints is not an index until
  `idx.py build` runs; readers never create the store.
- `/regency:health:version` (R12.3) and `/regency:health:copies` (R12.4).
- `.gitattributes`, line endings normalised to LF (R12.5).
- Agents commit as `Claude <noreply@anthropic.com>`, repository config only (R12.6, conventions §4).
- An update step may run one of regency's scripts first (`before`); 2.12's step migrates `fingerprints.json`
  into the store, then deletes it.

Proof: shortcuts 43/43, migrate 38/38, health 63/63, idx 35/35; 13 planted mutants caught; a 2.11 project
updated end to end.

---

## 2.11

2026-10-28 · built on the account's 2.10, landed in git as 2.12's baseline · record R11

- `/regency:health` (R11.1): the Regent's checkup, one line per finding with its method; levels `FAIL`,
  `WARN`, `STALE`, `UNCHECKED`, `AOK`. Subcommands `project`, `harness`, `doctor`, `shortcuts`,
  `distributable`, `engines`, `hooks`, `queues`, `context`, `pipeline`. Engine: `scripts/health.py`; doctrine
  `library/health.md`.
- `/regency:health:doctor` calls `serious-doctor-appointment` (R11.4, R11.20), which proposes each guidelines
  part's checks; it checks nothing itself (R11.21). Check sets live in `.shortcuts/`, not a new folder (R11.6).
- `/regency:health:shortcuts` replaces `/regency:virtualpath:check` (R11.8).
- Engines: each copy (regency's base, the machine's, the account's) compared with the Regent's ratified record;
  a denial brings the base back (R11.9–R11.16). The Regent holds their own engines; a project may carry its
  own, chosen per repository (R11.16, R11.22).
- `pipeline`: watched runs of declared input → process → output cases and a silent-error scan (R11.18).
- Every hook leaves a heartbeat; a wired hook that never fires is a finding (R11.11).
- regency is presented as a harness built on Claude Code (R11.5).
- The release word behind a harness reminder is heard (R11.24, the port of the old line's fix).

Proof: health 49/49 then; 15/15 mutants; the account refused a 618-character description, so doctor check 1
now fails above 500.

---

## 2.10

2026-10-28 · branch `regency-2.10` (now `archive/regency-2.10`) · record R10

- `/regency:update` (R10.1): declares exactly what changes from one version to the next and changes exactly
  that. Engine `scripts/migrate.py` (`gate`, `plan`, `apply`, `check`, `stamp`, `record`); doctrine
  `library/migrations/README.md`.
- The version gate (R10.3): a command on a project behind the harness says it must update first; on a project
  ahead, it stops. The stamp lives in `<guidelines>/.shortcuts/regency.json` (R10.4).
- Only what regency owns is rewritten (R10.5); one yes for the whole plan, in a clean git tree (R10.6).
  Migrations ship inside the plugin (R10.7).

Proof: migrate 34/34, ten mutants; a real 2.6-era project updated; `history.json` holds every template
fingerprint from 1.2 on.

---

## 2.9

2026-10-28 · record R9

- The app's own sources are English (R9.1): templates, moulds and commands never carry Portuguese; inputs may
  be in any language. The init scaffold, task and checklist states and the Tailwind samples were translated;
  `conventions_check.py` (`language`) fails on Portuguese outside a quoted input.

---

## 2.8

2026-10-28 · record R8 (answers)

- An Emission lives in its Orders (R8.7): an Order's `position` names its EMS; `/regency:order:lazy` takes them
  in number order.
- A DV still returns its change uncommitted; in the speed modes the main session commits it in the worktree.

---

## 2.7

decided 2026-10-23, built 2026-10-28 · record R8

- Three speed modes (R8.1): `/regency:order:lazy`, `/regency:team:extreme-go-horse` (two teams, fuel the Regent
  declares), `/regency:team:just-in-time` (QA seeds, small DVs draft in waves). Doctrine
  `library/team/SPEED_MODES.md`; engine `scripts/speed.py`.
- Speed trades verification depth, never T4, T5, infrastructure or a destructive action (R8.2). Drafts are
  DRAFT/UNVERIFIED, live on `plumbing` only, and a normal team pass verifies them (R8.3). Models are set at
  spawn (R8.4). One packet per pass or wave (R8.5).

---

## 2.5–2.6

between 2026-10-17 and 2026-10-23 · built in other sessions; this repository holds no decision record for them

Read from the code (present at 2.7, absent at 2.3): the suba lenses inside each role's stage with their return
contracts (`library/subagents/`, `ALIGNMENT.md`, `envelope.schema.json`), the return gate (`scripts/returns.py`)
and the exact index (`scripts/idx.py`). `library/migrations/history.json` holds the 2.6 template
fingerprints.

---

## 2.4

2026-10-28 · the old `plumbing` line · record R7 · superseded by 2.12

- The shortcuts engine (`scripts/shortcuts.py`): the entry index, drift, a generated state block refreshed at
  handoff and at session end, SQLite as its store (R7.1–R7.4).
- The release word behind a `<system-reminder>` block (cloud surfaces) was never heard; `hook_wire.regent_text`
  fixed it. Ported forward in 2.11.

---

## 2.3

2026-10-16 → 2026-10-17 · `main` before this merge

- The hazard watch scoped to the project; PO and QA role agents grant write permits under it.
- Conventions §15, the simplest sufficient: the ladder of rungs to stop at before building, and the agent
  arenas.

---

## 2.2

2026-10-10 · record R6

- `/regency:ux-init` (R6.1): a project's frontend documentation in `<guidelines>/.ux/`: brief, foundations,
  tokens, patterns, views, components, accessibility, assets, samples, rules, changelog. Engine `scripts/ux.py`.
  Tokens start from the Regent's Void/Paper palette (R6.2).

---

## 2.1

2026-10-09 · records R4, R5

- Hooks are triggers, scripts are engines (R4.1): every hook calls one standard-library script and prints at
  most one line; doctor self-tests each one, because a missing script fails open.
- A resume line at session start (R4.2); lineage fingerprints and STALE marks after a write (R4.3); a guard on
  acts, `.scope/` and banned names (R4.4); no Stop hook (R4.5).
- Cloud CLIs: reads run, a write runs only when the Regent quoted that exact command in the current pass
  (R5.1). The hazard watch ends only on a release word, `release` or `libere` (R5.2). Guards fail closed (R5.4).

---

## 2.0

2026-10-08 · records R1–R3

- Rule zero, *Mastery spares Synthesis* (R1.1): what can be written down as a script, template or registry
  entry is, so the model fills fewer gaps.
- Versioning `a.b` (R1.3); the hierarchy O4 → O1 (R2.5); the id grammar machine-checked in `library/ids.md`;
  `conventions_check.py`; the doctor.
- The north star (R1.9): (almost) full development cycles at a newcoming developer's fingertips. Glyph is a
  separate project; Glyph Explorer is the pilot repository (R1.8, R2.2).
- The newcomer kit, the absorption layout for subagents and vendors, the team expansion (R2.3, R2.4, R3.1).

---

## 1.2

Upstream, before the customisation. Its templates are the first entry of `library/migrations/history.json`.
