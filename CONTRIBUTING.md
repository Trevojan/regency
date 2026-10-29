# Contributing to regency

regency changes on evidence from real use. This file says what a proposal carries, which checks a change
must pass, and how commits, branches and versions are kept.

## What to bring

| Kind | Evidence it carries |
|---|---|
| A rule that failed | the unit, the rule, what happened, what should have happened |
| A recurring doubt | where it came back, and how many times |
| An instruction AA needed twice | both occurrences; by rule zero it becomes a script, a template or a registry entry |
| A defect | the command, the input, the output, the expected output, `python scripts/doctor.py` output |

Open an issue for a proposal or a defect, or a pull request with the change and its evidence. A practice
enters as a proposal (a subagent carries `metadata.status: proposal`) and becomes a rule only when the
maintainer ratifies it.

## Before a pull request

```bash
python scripts/build.py     # regenerate everything derived from library/registry.json and the contracts
python scripts/doctor.py    # must exit 0: every self-test, the wiring, portability, the conventions
```

A change that adds a check adds a planted defect to its script's `--selftest`: a check that never fails
proves nothing.

## Rules the checks hold

| Rule | Checked by |
|---|---|
| `library/registry.json` is the only source of the command table; generated files are never edited by hand | `scripts/build.py --check` |
| Every path inside the folder is relative; no drive letter, home directory or machine path | `scripts/doctor.py` |
| Python standard library only, 3.8 or later | review; doctor runs every script |
| The app's own sources are English; an input may be in any language, quoted | `scripts/conventions_check.py` (`language`) |
| No `Base`, `Abs`, `Mgr`, `Helper`, `Common`, `Utils` in names; name by role, never by value | `conventions_check.py` (`banned`), `hook-acts-guard.py` |
| Unit ids are `M##.S##.T##`; every id grammar lives in `library/ids.md` | `conventions_check.py` (`ids`, `steps`) |
| A hook entry holds no logic: the script comes first, then the trigger | `scripts/doctor.py` (wiring) |
| Every hook script passes its own `--selftest` and answers a real event | `scripts/doctor.py` |

## Commits and branches

- Small commits, split by kind: `feat`, `fix`, `docs`, `add`, `test`. Each commit builds and passes doctor.
- An agent's commit is authored `Claude <noreply@anthropic.com>` and ends with its `Co-Authored-By:` trailer.
- Branch contract: `plumbing` (first code) → `testing` (validation) → `main` (docs and the reviewed merge).
- Only the maintainer pushes `main`. No force-push, no rewrite of published history (`scripts/guard-push.py`).

## Versions

regency is versioned `a.b`: `+b` for a content change, `+a` for a major rule finished, reinterpreted or
invented. Bump `library/registry.json` and `.claude-plugin/plugin.json` together. When a template changed,
run `python scripts/migrate.py record`; when a project must change beyond its templates, add a step to
`library/migrations/steps.json` (`library/migrations/README.md` §5).

## License

Contributions are accepted under the [MIT License](LICENSE).
