# Checkpoint · regency 3.3 · 2026-11-06

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 3.3 | doctor fails when they differ |
| the Regent's folder: `plumbing`, `testing`, `main` | 3.3 | one commit, its history re-authored as Trevojan; waits for the Regent's force-push |
| GitHub `plumbing`, `testing` | 3.3 | the same files as the folder's `main`, under the old authors until the force-push |
| GitHub `main` | 3.1 | at `8427d0b` until the force-push; doctor green in CI there |
| a release tag | none yet | `v3.3` goes out from `main` once pushed; the README's pinned install points at `v3.3` |
| this machine's installs | 3.1 | `regency~g3` is the only live copy (`health.py copies`, 2026-11-06), behind this folder's 3.3 (N11) |
| the at-work fork | 3.2, 3.1 | holds nothing this folder lacks: its two new commits are picked here, under Trevojan |

## What 3.3 added

Commits name the Regent as author and Claude [Model] as co-author (conventions §4); a session on an older install
reads the old rule until it updates. `migrate.py merged` records a `.template` merged by hand, so the plan stops
putting it back.

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` denies an agent's push to `main`. The superseded branches are retired as
`archive/regency-2.10`, `archive/plumbing-2.12` and `archive/plumbing-2.13`; the last two keep their commits under
the old author.

## Health

- `python scripts/doctor.py` on the Regent's machine (Windows, 2026-11-06): 0 fail; the 29 warnings are the 25 old
  level names, the two proposal subas and two machine-side installs (path-scoped rules, auto-mode entries).
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`; it last passed on `main` at 3.1.
- The repository is public. Its hardening is the Regent's in GitHub's settings: rulesets on `main` and the release
  tags, the `doctor` check required on `main`, private vulnerability reporting, secret scanning, Discussions.

## Next, in order

1. The Regent force-pushes the re-authored branches: `git push --force-with-lease origin plumbing testing main`
   (their admin role bypasses `main`'s ruleset); CI runs doctor there.
2. Publish the release `main` holds, with its `.plugin` attached, and test the pinned install line.
3. Keep one install of 3.3 on this machine and the account (N11).
4. First live grant: confirm where the pop-up's answers arrive (`library/judge.md` §7).
5. The RGN-DV charter (`ROADMAP.md`, the Judge's next limits).

## How to resume here

1. Read this file, then `../../CLAUDE.md`.
2. `python scripts/vp.py ongoing` — this folder's ledger (`.guidelines/.shortcuts/.virtual/ongoing.json`): what is ongoing,
   in review, blocked on the Regent or only backlog; each item points at its row here or in `ROADMAP.md`.
3. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
4. `git log --oneline -15` on `plumbing` for the latest commits.
5. In a project (not this folder), `/regency:virtualpath:ongoing`, `/regency:pack list`, `/regency:judge` and the
   resume line give that project's own state; this folder's state is this file and its ledger.
