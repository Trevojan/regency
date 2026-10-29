# Checkpoint · regency 4.0 · 2026-10-29

Rewritten in place each time the version moves or the state below changes. The road to here is in
[`HISTORY.md`](HISTORY.md); the road ahead in [`ROADMAP.md`](ROADMAP.md).

## Version in force

| Where | Version | Note |
|---|---|---|
| `library/registry.json`, `.claude-plugin/plugin.json` | 4.0 | doctor fails when they differ |
| the Regent's folder, branch `plumbing` | 4.0 | built there through the device bridge; on GitHub after the Regent's push |
| GitHub `plumbing`, `testing`, `main` | 3.0 | all three at `b4ec8cb` |
| a release tag | none yet | `v3.0` can go out from `main` now; the README's pinned install on `plumbing` points at `v4.0` |
| the Claude account | last seen 3.0 | a cloud session can install `regency-<version>.plugin` built by `python scripts/package.py` |

## What 4.0 added

The Judge (`library/judge.md`): the Regent's grants say where and how a delete, discard, history rewrite or
worktree change may run without regency's ask, for this session, the repository (`JD.md`), this machine or a
file the Regent names. Each act is judged when it happens; nothing locks the session. Only the Regent grants, by
a `grant:` line or the Judge's pop-up; a store changed outside the hooks is STALE until the Regent ratifies it.

## Branches

The contract is `plumbing` → `testing` → `main` (conventions §4): `plumbing` takes the agents' first code,
`testing` the last validated pass, `main` the docs and the reviewed merge. Agents push `plumbing` and
`testing`; `scripts/guard-push.py` denies an agent's push to `main`. The superseded branches are retired as
`archive/regency-2.10`, `archive/plumbing-2.12` and `archive/plumbing-2.13`.

## Health

- `python scripts/doctor.py` on the Regent's machine: 0 fail besides `claude plugin validate`, which the device
  bridge's binary cannot run; the warnings are the old level names in `library/orders/` and `library/team/`, the
  two proposal subas and the machine-side installs.
- CI: `.github/workflows/doctor.yml` runs `build.py --check` and doctor on pull requests and on pushes to
  `main`, `testing` and `plumbing*`; it passed on `main` at `b4ec8cb`.
- The repository is public. Its hardening is the Regent's in GitHub's settings: rulesets on `main` and the release
  tags, the `doctor` check required on `main`, private vulnerability reporting, secret scanning, Discussions.

## Next, in order

1. The Regent pushes `plumbing` (4.0) from the folder; CI runs doctor there, then `testing` and `main` follow.
2. Publish the release `main` holds, with its `.plugin` attached, and test the pinned install line.
3. Re-install the role agents (`python scripts/install-agents.py`): the `po` and `qa` contracts changed.
4. First live grant: confirm where the pop-up's answers arrive (`library/judge.md` §7).
5. The RGN-DV charter (`ROADMAP.md`, the Judge's next limits).

## How to resume here

1. Read this file, then `../CLAUDE.md`.
2. `python scripts/doctor.py` — the folder is intact when it says `0 fail`.
3. `git log --oneline -15` on `plumbing` for the latest commits.
4. In a project (not this folder), `/regency:virtualpath:ongoing`, `/regency:pack list`, `/regency:judge` and the
   resume line give that project's own state; this folder's state is only what this file says.
