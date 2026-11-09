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

## Packages and releases: the plan

A candidate (the causal engine, 2026-11-09, on the Regent's request), not a decision. The aim: one version, one
content, from the tag to every install. Today a version names more than one: `.changelog/`, `CLAUDE.md` and the README
ship in the `.plugin` and change between bumps (four of them since `954e691`, still 3.3), and Claude Code refreshes an
install only when the version changes (`library/maintaining.md`).

| # | Step | Who | Because | Complete when |
|---|---|---|---|---|
| R0 | Decide: (a) every version that reaches `main` is one immutable release `v<a.b>`, tagged on `main` only; (b) an account trial takes a `testing` build, and a change after a trial bumps `b`; (c) the release attestation alone, or build provenance too; (d) Windows in CI; (e) `v3.3` by hand now, or `v3.4` first | RGN | the cache keys on the version; only the Regent publishes | the five answers are dated here |
| R1 | Immutable releases on; a ruleset on `refs/tags/v*` (the Regent creates; no update, no delete); `doctor` required on `main` | RGN | a published immutable release takes no fix, so it is published from a draft that already holds its asset | the settings show all three |
| R2 | `doctor.yml` as a matrix: `ubuntu-latest`, `ubuntu:24.04` (git 2.43), `windows-latest`; the `claude` CLI at a pinned version, so doctor runs `claude plugin validate` | DV | the last week's defects were platform ones (cp1252 in 3.2, `hazard-cmd-linux`, `refs-old-git`), and CI never ran Claude Code's own validator | the two Linux defects show red on their job, then green after their fixes; all three jobs green at 3.4's commit |
| R3 | `release.yml` on a pushed `v*` tag, its one job holding `contents: write`: check out the tag; refuse unless the tag equals `plugin.json` and `registry.json`, the commit is on `main` and `.changelog` names the version; `build.py --check`, doctor, `package.py`; a draft release with `regency-<v>.plugin`, its `.sha256` and `HISTORY.md`'s section as notes | DV | a build from a clean checkout of the tag closes `package-dirty`; a tag runs the workflow from its own commit, so the workflow ships inside the version it releases | on a scratch copy of the repository, a tag yields a draft whose asset matches a local `package.py` build of the commit byte for byte; a tag that disagrees with `plugin.json` yields none |
| R4 | `build.py` generates the README's pinned install and verify lines from `plugin.json` | DV | the README pins `v3.3`, which does not exist: the line is hand-written | `build.py --check` fails on a pin that differs from the version |
| R5 | Ship 3.4: the matrix green, QA's third pass, `testing`, `main`; the Regent tags `v3.4`, reads the draft, publishes | RGN, QA | `/regency:latest`, `release.yml` and the generated pin exist on `plumbing` only; the first release must carry them, or its installs cannot follow the next one by command | `gh release verify v3.4` and `verify-asset` pass, their first live run; `marketplace add Trevojan/regency#v3.4` installs 3.4 |
| R6 | Converge the installs: `/regency:latest` on the machine, the verified asset on the account, the folder install kept on purpose or removed (N11) | RGN | an install from a working tree runs content no release holds, under a release's version | `/regency:latest:check` says the install fits; `health copies` shows no version naming two contents; a cloud session lists 3.4 |

R2, R3 and R4 run in parallel on `plumbing`; R1 lands before R5, which waits for all three. After 3.4 the loop holds
itself: a content change bumps `b`, each version on `main` is released, and `/regency:latest:check` with `health
copies` are the sensors of drift.

**GitHub Packages: none now.** No consumer reads a registry: Claude Code installs regency from a git marketplace or
an account upload, and regency has no dependency to publish (standard library only), so nothing enters (conventions
§15.4). The one candidate, a station image on `ghcr.io` for the CI matrix and cloud environments, stops at rung 4:
the runners and `ubuntu:24.04` already give the platforms. It reopens when the matrix's tool setup passes a threshold
the Regent declares, or a cloud environment's setup script needs the same pinned tools.

Not established: whether an immutable release can be withdrawn after a bad publish; whether the runners still offer
Python 3.8, the floor doctor enforces; whether a required check binds the Regent's admin pushes (N18); whether
`claude plugin validate` runs in CI without a login.

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

## On GitHub

Issues hold only what improves the harness, as `main` holds it, and link to `main`; code issues are always lesser,
noted under the candidates below and never posted (the Regent, 2026-11-09: "the issues must live in main always and
aim to improve Harnessing"; "code issues must be noted, but not as true regency struggle").

| Issue | What |
|---|---|
| [#2](https://github.com/Trevojan/regency/issues/2) | Sleepy Runs (the Regent, 2026-11-05): at work, a team pass spent about 2 h on framing and challenge loops before any code, when the user wanted build first, review after; review behaviour on multiple parallel runs, with many concurring models |
| [#3](https://github.com/Trevojan/regency/issues/3) | the open doubts N1, N2 and N14 |
| [#4](https://github.com/Trevojan/regency/issues/4) | the Judge: the next limits |
| [#5](https://github.com/Trevojan/regency/issues/5) | packs: the next limits to break |
| [#7](https://github.com/Trevojan/regency/issues/7) | the method chain's open steps: 4, 5, 10, 11, 12 and 15 |
| [#9](https://github.com/Trevojan/regency/issues/9) | queued from the book, all but `hazard-cloud`, C-10 and C-12 |

## Candidates seen while building

Lesser issues, noted here and never posted: every code issue, and anything that does not improve the harness (On GitHub,
above).

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
- `install-agents.py`, `install-rules.py` and `install-automode.py` ignore an unknown flag, so `--help` runs the
  install (it did on 2026-11-06, for the role agents).
- `package.py` builds from the working tree as it stands and checks only the generated files, so a dirty tree ships
  under the version in force, one version naming two contents. `/regency:latest` never builds, so it does not close this.
- `health.py copies` says each installed copy loads its skills and hooks, but a synced copy shadowed by a local install
  does not load (2026-11-06): it reads the disk, not `claude plugin list`.
- `ratify grants` shows a count, not the rows: a `push` row that arrived outside the hooks opens `main` for every session
  of the repository on that one verb (QA, 2026-11-06).
- `/regency:station` reporting `hook-refs.py`: installed, current, or kept out, and whether this session's shells have the
  setting.
- `hook-hazard.py` reads force from text, so a wrapped or continued force-push outside `main` is not asked about. It also
  asks on `--force --no-force`, and the push guard denies `--no-dry-run -n`: both err toward stopping (QA, 2026-11-06).
- `--no-verify` is asked about only where the text guard can read it, so a continuation, an alias or a wrapper reaches no ask
  (QA, 2026-11-06). The Regent's call put that out of the promise; a real fix needs something that runs after git parses.
- A linked worktree of a repository with a `push` grant is refused: the grant is keyed on the folder. It errs toward
  stopping (QA, 2026-11-06).
- `hook-hazard.py --selftest` misses one case on Linux, `cmd /c "cd /d ..\other && git clean -fd"` (added in `b4a9987`):
  217/218, so doctor fails in CI on `plumbing` from run 26 (`3396665`, 2026-11-08).
- `hook-refs.py --selftest` crashes on git 2.43: the case for a moved plugin writes `.git/regency-hooks/pre-push`
  before that folder exists (`FileNotFoundError`). CI's git 2.56 takes the configuration path and passes 147/147.
