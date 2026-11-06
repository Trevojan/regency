# Roadmap

Where regency is going, what of the way is built, and what waits for the Regent. Status words: **built**
(runs today), **partial**, **open** (decided or proposed, not built), **candidate** (seen, not decided).

## North star

(Almost) full development cycles at a newcoming developer's fingertips (R1.9). regency is the practical part
of *Hackiavelli — The Manual of Good Regency*; Glyph Explorer is its pilot repository (R1.8, R2.2). Glyph is a
separate project: regency reads its Orders and Emissions and carries none of its code.

## The method chain (the MAX of the ladder)

The whole cycle the harness aims to run, step by step, each pausing where the Regent decides.

| # | Step | Command or part | Status |
|---|---|---|---|
| 1 | Scaffold a project's guidelines | `/regency:init` | built |
| 2 | The Regent feeds `.scope/` (raw material, read-only for agents) | convention, `hook-acts-guard.py` | built |
| 3 | Grow the path to a goal as a tree | `/regency:order:germinate` | built |
| 4 | One normalised Briefing from every role's plan, with question waves | `/regency:briefing` | open |
| 5 | Break the solution down, O4 → O1, phases F0–F6 | `library/task-granulation.md` (doctrine, no command) | partial |
| 6 | The entry index and lineage a returning agent reads first | `shortcuts.py`, `vp.py`, `idx.py`, `/regency:virtualpath` | built |
| 7 | The team pass: frame, build, gate, verify, review packet | `/regency:team`, `/regency:proceed`, speed modes | built |
| 8 | Keep the project on the harness's version | `/regency:update`, the version gate | built |
| 9 | The checkup | `/regency:health` | built |
| 10 | Adopt misplaced files into the layout | `/regency:normalise` (R5 · 2026-10-21, on the update engine, R10.2) | open |
| 11 | Run the whole chain end to end | `/regency:solution:end-to-end` | open |
| 12 | Bind each mechanism to its chapter of the Manual | `/regency:manual` and a manual map in `library/`, neither created yet (R1.4) | open |
| 13 | Specialise the harness for a domain: adopt any plugin or skill, per project | `/regency:pack`, `library/packs.md` (3.0) | built |
| 14 | Standing permissions: where and how an act may run without asking, granted only by the Regent | `/regency:judge`, `library/judge.md` (3.1) | built |
| 15 | The Judge leads a session for an autonomous developer (RGN-DV), inside a charter the Regent ratified | the RGN-DV charter | open |

The MIN that runs today: steps 1–3, 6–9, 13 and 14, plus the engines, roles, Orders, the Scribe, `ux-init`,
`tailwind-audit` and `station`.

## Packs: the next limits to break

Studied with the Regent ("if there is a limit, we may study together to break it"). Each is a candidate, not a
decision.

| Limit | Today | Way past it |
|---|---|---|
| A pack is adopted once | `adopt` refuses an existing pack | re-adopt beside it with a diff; the better side stays (conventions §4) |
| Six events dispatched | SubagentStart, Notification, TaskCreated and TaskCompleted hooks are listed, not run | wire the dispatcher on them; Stop and SubagentStop stay refused (R4.5) |
| Native sockets | a pack brings playbooks, commands, agents, hooks and MCP servers | items for regency's own parts: health check sets, station gate tasks, suba lenses, phase checklists, vocabulary, id grammars, scaffolds |
| LSP, output styles, monitors, themes, `bin/` on PATH | listed under `unsupported` | a per-project plugin generated from the active packs, installed with `--plugin-dir`; or left out |
| Private packs for every project on one machine | not a chosen layer | a machine layer (`~/.claude/regency/packs/`), one more entry in `layer_dirs` |
| Packs not in health or the resume line | `packs.py check` only | `/regency:health` and the resume line report active, waiting and STALE packs |
| Frontend still built in | `ux-init`, `tailwind-audit` | moved into `packs/frontend` as the first public pack |

## The Judge: the next limits

| Limit | Today | Way past it |
|---|---|---|
| The pop-up's answers at `PostToolUse` | read from three shapes, not yet seen live | confirm on the first live grant; drop the shapes no surface uses |
| A grant on cloud | the repository's `JD.md`, ratified once per fresh machine; `REGENCY_JD` | a private grant file packed into the account's build of the plugin |
| `edit` and `move` | not kinds: regency asks before neither | the Judge writes Claude Code permission rules (`Edit(path)`) on the Regent's answer, so Claude Code stops asking too |
| A machine grant for every repository | `*` in the `repo` column, by a ratified hand edit | a `for machine *` scope word |
| The Judge as a session's lead | grants only | the RGN-DV charter: projects, units, fuel; the Judge may deny or stop, never approve its own way past a grant; the work ends at the review packet |

## Milestones walked

| Version | Capability gained |
|---|---|
| 2.0 | the conventions, the id grammar and the doctor |
| 2.1 | the hooks: guards, recorders, the hazard watch, cloud writes on the Regent's word |
| 2.2 | frontend documentation (`ux-init`) |
| 2.3 | the hazard watch scoped; write permits; the simplest sufficient |
| 2.5–2.6 | suba lenses with contracts; the return gate; the exact index |
| 2.7–2.8 | speed modes |
| 2.9 | English sources |
| 2.10 | update and the version gate |
| 2.11 | the checkup |
| 2.12 | one line of work, one store |
| 2.13 | the public repository: homepage, community, CI, this changelog |
| 3.0 | domain packs: any plugin adopted as it is, per project, hooks on the Regent's consent |
| 3.1 | the Judge: the Regent's grants replace the hazard watch |
| 3.2 | Windows consoles: UTF-8 hook streams, pack hooks cut on time; this folder's own ledger |
| 3.3 | the Regent authors, Claude [Model] co-authors; a `.template` merged by hand is recorded |

## Queued from the book

Decisions taken while writing the Manual, waiting to be applied (dated; the source is the Project's
`claude/BOOK_TO_REGENCY.md`). Each is a candidate for the next version.

| Date | Id | What | Where it lands |
|---|---|---|---|
| 2026-10-22 | hazard-cloud | a hazard hold that could not be released in a cloud session; 2.11's reminder fix answers the release word, but permits still need the role agents installed | `library/hooks.md` §0, `hook-hazard.py` |
| 2026-10-13 | returned-span | a returned span reaches the Regent as the PO's plan (a G2 packet); a wider span is a new version opened by the Regent | `library/team/ORCHESTRATION.md` §14 |
| 2026-10-13 | alarms-once | an alarm the Regent already answered is recorded once and never raised again | a warnings record in `.decisions/` |
| 2026-10-13 | qa-shell | QA's shell writes: compare the tree after QA returns with the state the gate passed | the team playbook |
| 2026-10-13 | infrastructure | money-related operations are the Regent's; a cloud API reached by an HTTP client is classified as a write | `hook-hazard.py` |
| 2026-10-13 | exposure | an exposure slot in the PO's frame, compared with the gate's F3 diff | the frame, the gate |
| 2026-10-13 | intake notes | the first freeze of a quality brief goes to the Regent; PO acceptance is a recommendation; sample the G1 ledger | `ORCHESTRATION.md`, `gov.py` |
| 2026-10-10 | C-09 | phases are a sequence: a task passes F0 to F6 within its declared span | `ORCHESTRATION.md` §7, §18 |
| 2026-10-10 | C-13 | one map between mechanisms and chapters, seeded with seven patterns | the manual map in `library/` (step 12 above) |
| 2026-10-10 | C-12 | drop the words "Big-O basis"; the levels are named O4 to O1, largest to smallest | conventions §11, `ids.md`, task granulation |
| 2026-10-10 | C-10 | cloud writes: the Regent's quoted command stands for the owner's confirmation; align §6's wording | conventions §6 |

## Open doubts (the Regent decides)

| Id | Doubt | Options seen |
|---|---|---|
| N1 | which conventions `/regency:normalise` follows | regency's conventions citing the Manual, or the Manual's text directly |
| N2 | `.scope/` after the project starts | out of `normalise`'s reach, or adopted later too |
| N3 | two records both numbered R5 (cloud CLIs; normalise) | rename one by R11.2's rule |
| N4 | the record's machine-side pending block | drop it, or keep it until each line is confirmed |
| N10 | seventeen silent exception handlers in the scripts | declare the meant ones (`health: allow-silent`), or make each report what it skipped |
| N11 | installs on this machine (2026-11-06): `regency@regency` from this folder's working tree is live and shadows the account's `regency~g3` 3.1, which cloud sessions still read; `regency` 3.0 and `regency~g2` 3.1 sit in `~/.claude/plugins/.trash` | keep one, or keep a second on purpose |
| N14 | projects already carrying the old step letter in ledgers, Orders and trailers | a migration step rewrites regency-owned shapes, or history stays and new ids use `S##` |
| N18 | `main`'s ruleset wants signed commits and a linear history; the re-authored history is unsigned and holds one merge (`053f97d`), so every push of `main` bypasses it | sign from now on and re-sign the history, or drop those two rules |

Closed with 3.1: N13 (the folder moved to `plumbing`; its 2.4 draft, all of it already in 3.0, dropped 2026-11-02) and
N16 (`main` took `testing`). Closed with 2.13: N12 (the old branches merged into one line; their retirement is the Regent's act,
`CHECKPOINT.md`), N15 (where 2.13 landed), N17 (community files). N16 (`main` shows the homepage) closes with
the Regent's merge of `testing` into `main` (done 2026-10-29).

## Candidates seen while building

- The 25 old level names (`D` followed by a digit) left in `library/orders/` and `library/team/`: step 4 of
  the original build plan renames them; doctor warns on each.
- Two suba spines whose alignment stamps drifted (`suba-strategy`, `suba-research`): re-read, then re-stamp.
- The required status check `doctor` on `main`: the workflow last passed there at 3.1.
- The `v3.3` release from `main`, with the `.plugin` attached; the README's pinned install points at it.
- This folder's own ledger (`.shortcuts/.virtual/ongoing.json`) is read by `vp.py` alone: the hooks and
  `/regency:health` find a ledger under a `.guidelines/` root only (`hook_wire.virtual_dir`), and a `.guidelines/`
  here would make the folder an unstamped project for the version gate.
- `vp.py trace` counts the format example in `library/hooks.md` as a STALE line waiting for the Regent: this
  folder's guidelines root is the repository root, so the scan reads every Markdown file here.
- `vp.py trace` lists every recently touched file in this folder as a guideline (179 on 2026-11-06, `scripts/` and
  `.github/` among them), from the same root.
- [Issue #2, "Team's Sleepy Runs"](https://github.com/Trevojan/regency/issues/2) (the Regent, 2026-11-05): at work, a
  team pass spent about 2 h on framing and challenge loops before any code, when the user wanted build first, review
  after. The issue proposes reviewing behaviour on multiple parallel runs, with many concurring models.
- `install-agents.py`, `install-rules.py` and `install-automode.py` ignore an unknown flag, so `--help` runs the
  install (it did on 2026-11-06, for the role agents).
- `package.py` builds from the working tree as it stands and checks only the generated files, so a dirty tree ships
  under the version in force, one version naming two contents. `/regency:latest` never builds, so it does not close this.
- `health.py copies` says each installed copy loads its skills and hooks, but a synced copy shadowed by a local install
  does not load (2026-11-06): it reads the disk, not `claude plugin list`.
- `hook-verbs.py` records a cloud command quoted inside pasted content as confirmed, against conventions §6 (QA,
  2026-11-06). It needs its own unit.
- `ratify grants` shows a count, not the rows: a `push` row that arrived outside the hooks opens `main` for every session
  of the repository on that one verb (QA, 2026-11-06).
- `hook-refs.py` writes no stub beside another `pre-push` or under `core.hooksPath`: a way to chain them, and
  `/regency:station` reporting it.
- `hook-hazard.py` reads force from text, so a wrapped or continued force-push outside `main` is not asked about. It also
  asks on `--force --no-force`, and the push guard denies `--no-dry-run -n`: both err toward stopping (QA, 2026-11-06).
