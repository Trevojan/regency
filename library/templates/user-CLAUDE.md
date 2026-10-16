# Personal defaults — the Regent

These apply in every project. A project's own `CLAUDE.md` and `.guidelines/` override them.
The source of truth is the regency folder; edit conventions there, not here.

@{{REGENCY_ROOT}}/library/conventions.md

- Regency is installed: `/regency` lists its commands (`/regency:team`, `/regency:proceed`,
  `/regency:order:resume`, `/regency:engine:critical`, …). Its playbooks and scripts live in
  `{{REGENCY_ROOT}}`.
- Returning to a repository: first peek is the work ledger — `python {{REGENCY_ROOT}}/scripts/vp.py ongoing`,
  then `trace`; reconcile before reading anything else.
- A hook blocks pushes to `main`/`master` (`scripts/guard-push.py`, shipped in the plugin's `hooks/hooks.json`).
  Push your own branch; the Regent pushes main.
