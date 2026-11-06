# Checkpoint · regency 3.3 · 2026-11-06

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 3.3 | doctor fails when they differ |
| the Regent's folder and GitHub: `testing`, `main` | 3.3 | `954e691`: 64 commits, none authored by Claude; force-pushed 2026-11-06 |
| `plumbing` | 3.3, ahead | the Regent's own line, the `push` grant, `/regency:latest`, the flag-reading fixes and `hook-refs.py`, on top of `954e691`; QA refused `3326385` and then `b760d8f` on the guards, and this work answers both: the check now lives in the repository (`library/hooks.md` §2); doctor green, waiting on QA's third pass |
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
2. QA's third pass on `plumbing`, against the forms it landed on `b760d8f`; accept or refuse; bump to 3.4; merge up to `main`.
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
