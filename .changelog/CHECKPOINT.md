# Checkpoint · regency 2.13 · 2026-10-29

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 2.13 | doctor fails when they differ |
| GitHub `Trevojan/regency`, branches `plumbing`, `testing`, `main` | 2.13 | one line of history since 2.13 (the two old roots joined) |
| a release tag | none yet | `v2.13` is the next act; the README's pinned install points at it |
| the Claude account | last seen 2.12 | a cloud session can install `regency-<version>.plugin` built by `python scripts/package.py` |

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` denies an agent's push to `main`.

Retired as tags, every commit still reachable from `main`:

| Tag | Was | Tip |
|---|---|---|
| `archive/regency-2.10` | 2.8 → 2.10 | `b739d36` |
| `archive/plumbing-2.12` | 2.11 baseline → 2.12 | `2ef7667` |
| `archive/plumbing-2.13` | 2.13 before the merge | `83b803f` |

## Health

- `python scripts/doctor.py`: 0 fail, 30 WARN. The warnings: 25 old level names in `library/orders/` and
  `library/team/`, two drifted suba alignment stamps, and machine-side installs (role agents, path-scoped
  rules) that a cloud session does not hold.
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`.
- The repository is public. Its hardening is the Regent's to apply in GitHub's settings: rulesets on `main`
  and the release tags, Actions approval for outside contributors and a read-only token, private
  vulnerability reporting, secret scanning, Discussions. The files that belong in the repository are in
  `.github/`.

## Next, in order

1. Tag `v2.13` on `main` and publish its release with `regency-2.13.plugin` attached (draft, attach, publish).
2. Add `doctor` as a required status check on `main` once the workflow has run there.
3. Pick the next version's scope from [`ROADMAP.md`](ROADMAP.md): the book's queue (C-07, C-09, C-10, C-12,
   C-13 and the 2026-10-13 notes), the old level names, the open doubts N1–N14.

## How to resume here

1. Read this file, then `../CLAUDE.md`.
2. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
3. `git log --oneline -15` on `plumbing` for the latest commits.
4. In a project (not this folder), `/regency:virtualpath:ongoing` and the resume line give that project's own
   state; this folder's state is only what this file says.
