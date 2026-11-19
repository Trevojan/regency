# Checkpoint · regency 3.3 · 2026-11-06

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 3.3 | doctor fails when they differ |
| the Regent's folder and GitHub: `testing`, `main` | 3.3 | `954e691`: 64 commits, none authored by Claude; force-pushed 2026-11-06 |
| `plumbing` | 3.3, ahead | the Regent's own line, the `push` grant, `/regency:latest`, the flag-reading fixes and `hook-refs.py`, on top of `954e691`; QA refused `3326385` and then `b760d8f` on the guards, and this work answers both: the check now lives in the repository (`library/hooks.md` §2); doctor green, waiting on QA's third pass. Beside it, the hooks journal (the Regent, 2026-11-07): it stays tracked and the cycle commits it last and alone, `vp.py trace` and `migrate.py apply` name journal-only dirt in one line, a lock orders parallel writers of the journal and the governance files, and writes outside the repository leave no line (`library/hooks.md` §3–§4) |
| a release tag | none yet | the README's pinned install points at `v3.3`, which does not exist; immutable releases are off, and `/regency:latest` verifies against them |
| this machine's installs | 3.3 label | `regency@regency` from this folder's working tree, user scope (2026-11-06), so it runs the uncommitted work; it takes precedence over the account's `regency~g3` 3.1, which stays on disk (N11) |
| the at-work fork | 3.2, 3.1 | holds nothing this folder lacks: its two new commits are picked here, under Trevojan |

## What 3.3 added

Commits name the Regent as author and Claude [Model] as co-author (conventions §4); a session on an older install
reads the old rule until it updates. `migrate.py merged` records a `.template` merged by hand, so the plan stops
putting it back.

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` and `scripts/hook-refs.py` refuse an agent's push to `main` with no `push` grant. The superseded branches are retired as
`archive/regency-2.10`, `archive/plumbing-2.12` and `archive/plumbing-2.13`; the last two keep their commits under
the old author.

## Team

regency runs at adoption stage 5 (`library/team/ORCHESTRATION.md` §21; the Regent, 2026-11-18): every role is an
agent. QA opinions are acts kept byte for byte in `inspection/`, with their probes beside them; they stay in the
repository and never ship (`scripts/package.py`). The first QA pass on the analytics lane (`QA-analytics-lane-01`)
refused its four Major defects; the Regent accepted the lane writes and `locate.py` with QA's residual risk, and defined the reread
measure's "carried" as line-level (its fourth defect). The second QA pass met all four; the PO accepted
`e34f27c` with conditions (`inspection/PO-analytics-lane-02-accept.md`). The Regent, the same day: close only once
the conditions land and QA sees them; the interleaved-session limit (D17 there) stands as a stated limit; reads
journalled before line offsets stay out of the measure, counted apart. QA's third pass met both conditions
(`inspection/QA-analytics-lane-03.md`) and the unit closed on `plumbing` (`Verified-Draft: analytics-lane`); its
open defects wait in the ledger (`elicitation-followups`, `docs-lag-D19`). The guards line's gate is green since `0cbf13d` (CI
run 44568896975); its third QA pass escalated (`inspection/QA-grant-latest-03.md`). The Regent, 2026-11-19: back to
DV past T4 for the symlink and nested-repository defects, the rest to the backlog; the cloud-session gap over `main`
is not accepted (backlog); the line ships as 4.0; a subagent's hand-back read as the Regent's words by
`hook-verbs.py` becomes a unit of its own (`verbs-agent-text`); the station gains Make (`station-make`): runner-neutral,
the Makefile ratified by its contents, regency's own Makefile, its repeated targets offered to the Judge as grants,
built by a team pass once grant-latest closes. The guards line's gate is red in CI since `3396665` (`hook-refs.py` passes
there; `hook-hazard.py` 217/218): its QA pass waits on DV, and the fixes `a2c4e24` and `1cbdb2f` sit unmerged on
`origin/ccr-6dc600c5-kfeqpi`.

## Health

- `python scripts/doctor.py` on the Regent's machine (Windows, 2026-11-06): 0 fail; the 29 warnings are the 25 old
  level names, the two proposal subas and two machine-side installs (path-scoped rules, auto-mode entries).
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`; it last passed on all three at 3.3 (2026-11-06).
- The repository is public. Its hardening is the Regent's in GitHub's settings: rulesets on `main` and the release
  tags, the `doctor` check required on `main`, private vulnerability reporting, secret scanning, Discussions.
- `main`'s ruleset `main-tain` refuses force-pushes, merge commits and unsigned commits. The re-authored history is
  unsigned and holds one merge (`053f97d`), so a push of `main` passes only by the Regent's admin bypass (N18).

## Next, in order

1. Any other clone of this repository resets to the new heads and never pulls: a pull there recreates the merges.
2. DV on `plumbing`: the guards line's defects through a symlink and in a nested repository, in
   `inspection/QA-grant-latest-03.md`, then a fresh QA; accept or refuse. The analytics lane is verified on `plumbing`; `plumbing` → `testing` waits on the guards
   line, which comes before it in the same history. Then bump to 4.0 (the Regent, 2026-11-19); D19 (`docs-lag-D19`); merge up to `main`. Once grant-latest closes, the
   team pass on `station-make` (the Regent, 2026-11-19).
3. The Regent pushes `main`, turns on immutable releases and publishes `v3.4` with its `.plugin` attached;
   `/regency:latest` moves this machine to the tag; test the pinned install line.
4. Keep one install on this machine and the account (N11).
5. First pop-up grant: confirm where its answers arrive (`library/judge.md` §7). A `grant:` line ran live on 2026-11-06.
6. Issue #2, Sleepy Runs (`ROADMAP.md`, candidates).
7. The RGN-DV charter (`ROADMAP.md`, the Judge's next limits).

## How to resume here

1. Read this file, then `../CLAUDE.md`.
2. `python scripts/vp.py ongoing` — this folder's ledger (`.shortcuts/.virtual/ongoing.json`): what is ongoing,
   in review, blocked on the Regent or only backlog; each item points at its row here or in `ROADMAP.md`.
3. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
4. `git log --oneline -15` on `plumbing` for the latest commits.
5. In a project (not this folder), `/regency:virtualpath:ongoing`, `/regency:pack list`, `/regency:judge` and the
   resume line give that project's own state; this folder's state is this file and its ledger.
