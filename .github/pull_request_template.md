## What and why

<!-- The change and its evidence (CONTRIBUTING.md → What to bring). Link the issue. -->

## Checks

- [ ] `python scripts/build.py` run; no generated file edited by hand
- [ ] `python scripts/doctor.py` exits 0
- [ ] a new check plants a defect in its script's `--selftest`
- [ ] no new dependency: Python 3.8+ standard library only

## Hooks

Hooks run on every installer's machine. Tick one:

- [ ] this pull request does not touch `hooks/`, `scripts/hook*.py`, `scripts/hook_wire.py` or `scripts/guard-push.py`
- [ ] it does, and the description says why; the hooks still make no network call, start no process
      other than `git`, and write only the files `library/hooks.md` §4 lists
