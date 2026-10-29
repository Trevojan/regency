# Security policy

regency installs hooks that run Python on the user's machine during every Claude Code session. A flaw in
a hook, a guard or the install path reaches everyone who installed it, so reports are welcome and handled
in private.

## Report a vulnerability

Use **[Report a vulnerability](https://github.com/Trevojan/regency/security/advisories/new)** (GitHub
private vulnerability reporting). Never open a public issue, discussion or pull request for one.

Include:

- the regency version (`version` in `.claude-plugin/plugin.json`) and the Claude Code version
  (`claude --version`);
- the command, hook event or file involved;
- the steps to reproduce, what happened and what you expected;
- whether you believe it is being exploited.

Leave out tokens, keys, session transcripts and private paths. If a reproduction needs them, say so in the
report and the maintainer will agree a safe way with you.

## What to expect

regency has one maintainer, who reads reports weekly, best effort. A valid report gets an answer, a fix
released as a new version, and credit in the advisory unless you ask otherwise. Give the fix time to ship
before publishing details.

## Supported versions

| Version | Supported |
|---|---|
| the latest `a.b` release | yes |
| anything older | no: update first |

## In scope

- Hooks: `hooks/hooks.json`, `scripts/hook*.py`, `scripts/hook_wire.py`, `scripts/guard-push.py`. Code
  execution, a guard that can be bypassed, a network call, a process other than `git`, or a write to a file
  that `library/hooks.md` §4 does not list.
- Scripts that read or write a user's project, such as `scripts/migrate.py`, `scripts/vp.py` and
  `scripts/shortcuts.py`.
- The install path: `.claude-plugin/`, release assets, the marketplace entry.

Out of scope: Claude Code itself (report it to Anthropic), GitHub, and forks of this repository.

## Official source

The only official source is [github.com/Trevojan/regency](https://github.com/Trevojan/regency) and its
releases. Forks are welcome under the MIT License; they are not reviewed or supported here.
