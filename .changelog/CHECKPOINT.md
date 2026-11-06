# Checkpoint · regency 3.2 · 2026-11-06

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 3.2 | doctor fails when they differ |
| the Regent's folder: `plumbing`, `testing`, `main` | 3.2 | `main` waits for the Regent's push |
| GitHub `plumbing`, `testing` | 3.2 | the same commit as the folder's `main` |
| GitHub `main` | 3.1 | at `8427d0b` until the Regent pushes; doctor green in CI there |
| a release tag | none yet | `v3.2` goes out from `main` once pushed; the README's pinned install points at `v3.2` |
| this machine's installs | 3.1 | `regency~g3` is the only live copy (`health.py copies`, 2026-11-06), behind this folder's 3.2 (N11) |

## What 3.2 added

Windows consoles work as they are: `hook_wire` puts every hook's stdin, stdout and stderr on UTF-8 (a cp1252 pipe
garbled `§` into `�` and crashed four doctor checks), and a pack hook past its timeout ends with everything it
started. This folder keeps its own work ledger (`.shortcuts/.virtual/ongoing.json`), and `vp.py` no longer reads the
scaffold seed in `library/templates/` as one.

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` denies an agent's push to `main`. The superseded branches are retired as
`archive/regency-2.10`, `archive/plumbing-2.12` and `archive/plumbing-2.13`.

## Health

- `python scripts/doctor.py` on the Regent's machine (Windows, a plain cp1252 console, 2026-11-03): 0 fail; the
  warnings are the old level names in `library/orders/` and `library/team/`, the two proposal subas and the
  machine-side installs.
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`; it passed on `main` at `b4ec8cb`.
- The repository is public. Its hardening is the Regent's in GitHub's settings: rulesets on `main` and the release
  tags, the `doctor` check required on `main`, private vulnerability reporting, secret scanning, Discussions.

## Next, in order

1. The Regent pushes `main` (3.2); CI runs doctor there.
2. Publish the release `main` holds, with its `.plugin` attached, and test the pinned install line.
3. Keep one install of 3.2 on this machine and the account (N11).
4. First live grant: confirm where the pop-up's answers arrive (`library/judge.md` §7).
5. The RGN-DV charter (`ROADMAP.md`, the Judge's next limits).

## How to resume here

1. Read this file, then `../CLAUDE.md`.
2. `python scripts/vp.py ongoing` — this folder's ledger (`.shortcuts/.virtual/ongoing.json`): what is ongoing,
   in review, blocked on the Regent or only backlog; each item points at its row here or in `ROADMAP.md`.
3. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
4. `git log --oneline -15` on `plumbing` for the latest commits.
5. In a project (not this folder), `/regency:virtualpath:ongoing`, `/regency:pack list`, `/regency:judge` and the
   resume line give that project's own state; this folder's state is this file and its ledger.
