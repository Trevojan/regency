# Checkpoint · regency 3.0 · 2026-10-29

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 3.0 | doctor fails when they differ |
| GitHub `Trevojan/regency`, branches `plumbing`, `testing` | 3.0 | one line of history since 2.13 (the two old roots joined) |
| GitHub `main` | 3.0 on the Regent's merge | `main` takes `testing` by the Regent's push or merge; `guard-push.py` keeps agents off it. When this was written it still held 2.3 |
| a release tag | none yet | `v3.0` is the first release; the README's pinned install points at it |
| the Claude account | last seen 2.12 | a cloud session can install `regency-<version>.plugin` built by `python scripts/package.py` |

## What 3.0 added

Domain packs (`library/packs.md`): any Claude Code plugin or skill adopted as it is into regency's public `packs/`
(none shipped yet) or a project's `<guidelines>/.packs/`, switched on per project, its hooks run by
`scripts/hook-packs.py` only once the Regent ratifies them at the pack's fingerprint. The first pack, `glyph`
(the Regent's `glyph-markup` skill), belongs in Glyph Explorer's repository; it was built and proved on a stand-in
and handed to the Regent as a folder.

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` denies an agent's push to `main`.

Superseded, every commit already in `plumbing`'s history. Each retires as the tag `archive/<branch>` at its
tip, then the branch goes (conventions §4). Both acts are the Regent's: a cloud session's network refuses tag
pushes, and branch deletion needs the Regent's permission.

| Branch | Was | Tip | Retires as |
|---|---|---|---|
| `regency-2.10` | 2.8 → 2.10 | `b739d36` | `archive/regency-2.10` |
| `plumbing-2.12` | 2.11 baseline → 2.12 | `2ef7667` | `archive/plumbing-2.12` |
| `plumbing-2.13` | 2.13 before the merge | `83b803f` | `archive/plumbing-2.13` |

## Health

- `python scripts/doctor.py`: 0 fail, 30 WARN. The warnings: 25 old level names in `library/orders/` and
  `library/team/`, two drifted suba alignment stamps, and machine-side installs (role agents, path-scoped
  rules) that a cloud session does not hold.
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`.
- The repository is public. Its hardening is the Regent's to apply in GitHub's settings: rulesets on `main`
  and the release tags, Actions approval for outside contributors and a read-only token, private
  vulnerability reporting, secret scanning, Discussions. The files that belong in the repository are in
  `.github/`. When this was written none of the settings was on yet.

## Next, in order

1. The Regent brings `main` to `testing`, pushes the three `archive/` tags and deletes the three superseded
   branches (the table above).
2. Tag `v3.0` on `main` and publish its release with `regency-3.0.plugin` attached (draft, attach, publish).
3. The `glyph` pack goes into Glyph Explorer's `<guidelines>/.packs/glyph/`, then `/regency:pack activate glyph`
   there.
4. Add `doctor` as a required status check on `main` once the workflow has run there.
5. Pick the next version's scope from [`ROADMAP.md`](ROADMAP.md): the packs' next steps, the book's queue, the
   old level names, the open doubts.

## How to resume here

1. Read this file, then `../CLAUDE.md`.
2. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
3. `git log --oneline -15` on `plumbing` for the latest commits.
4. In a project (not this folder), `/regency:virtualpath:ongoing`, `/regency:pack list` and the resume line give
   that project's own state; this folder's state is only what this file says.
