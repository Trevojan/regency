# Maintaining regency

Facts about Claude Code that this folder depends on, verified while building it, and the traps met on the
way. Read before changing the plugin's structure. Commands for routine maintenance are in `README.md`
("Maintain"); the folder's own rules are in `CLAUDE.md` ("Rules for working on this folder itself").

## Verified behaviour (Claude Code 2.1.201)

| Fact | Consequence here |
|---|---|
| The skill **directory name** is the command name; a colon in a skill's frontmatter `name` is ignored | `skills/team/` is `/regency:team`; never rename a directory without the registry |
| `commands/<a>/<b>.md` gives `/regency:a:b` | two-segment commands are generated aliases (`scripts/build.py`) |
| A skill named like the plugin answers the bare `/regency` | `skills/regency/` is the entry point |
| `${CLAUDE_PLUGIN_ROOT}` expands in skills, commands and `hooks/hooks.json` | hooks and playbooks never carry a machine path |
| An unquoted `: ` in YAML frontmatter makes the runtime drop **all** fields of that file | generated descriptions and argument hints are JSON-quoted; `doctor.py` has a strict frontmatter check |
| `claude plugin validate <dir>` with a `marketplace.json` present validates only the marketplace | validate `.claude-plugin/plugin.json` to check the components; `doctor.py` does both |
| An installed plugin runs from a **cached copy** (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`), refreshed only when `version` changes | after a change: bump `version` in `.claude-plugin/plugin.json` and `library/registry.json`, then `claude plugin marketplace update regency` and `claude plugin update regency@regency`, then restart |
| A hook whose script is missing or broken **fails open** | `doctor.py` runs every hook script's `--selftest` and feeds each one a real event on stdin |
| A headless session (`claude -p`) cannot read files outside its working directory without `--add-dir <regency path>` | say so in any automation that points at this folder |
| In git-bash, `claude -p "/regency…"` is rewritten into a Windows path | set `MSYS_NO_PATHCONV=1` first |
| A headless `claude` in a shell uses that shell's login, not the desktop app's | a live test needs `claude login` in that shell |
| `--setting-sources project` also drops the user-level login | isolate a test from user hooks with a tagged copy of the plugin (`--plugin-dir`), not by dropping user settings |
| Subagents cannot ask pop-up questions | role agents return `BLOCKED` / `UNRESOLVED` instead |
| Subagents inherit the user-level `CLAUDE.md` | an `@` import of `library/conventions.md` there reaches the role agents too |
| Tool limits in an agent's frontmatter are real for edit tools; a shell can still write files | QA's read-only contract is behavioural when it has a shell; PO has no shell at all |

## Hook facts (Claude Code hooks reference, read 2026-10-09)

Not yet seen live on the Regent's machine: confirm each row in a session before relying on it beyond
the self-tests. The consequences are in `library/hooks.md` §6.

| Fact | Consequence here |
|---|---|
| Exit 0 with JSON decides; exit 2 blocks; another exit code is a non-blocking error | every hook script exits 0 |
| `PreToolUse` decisions: `allow`, `deny`, `ask`, `defer` | guards answer `deny` or `ask`, silence allows |
| `additionalContext` strings are capped at 10 000 characters and arrive as a system reminder | one slice line per hook, capped at 600 |
| `if` is evaluated only on tool events | `if: Bash(git *)` stays on the push guard only |
| `onFailure: "block"` exists from 2.1.295; older versions ignore the key | guards carry it; on 2.1.201 they still fail open, so doctor stays the safety net |
| `async: true` hooks run in the background, unbounded, and cannot block | the journal is async except on `PreCompact` and `SessionEnd` |
| `SessionEnd` hooks share a 1.5 s budget | the journal's `SessionEnd` entry has a 2 s timeout |
| `CLAUDE_PLUGIN_DATA` is the plugin's persistent data folder | session state (the hazard watch) lives there, never in a repository |
| `PostToolUse` on `Agent`/`Task` carries `tool_input.subagent_type` and the subagent's returned text in `tool_response` | `hook-gov.py` routes packets and `hook-hazard.py` records PO/QA permits from it; confirm on the first live permit |

## Traps met while testing

- The push guard also blocks a test that pushes `main` to a throwaway remote. Seed such a remote with
  `git -C remote.git fetch ../work main:seed` instead of pushing.
- Testing a plugin hook while the same guard is installed at user level: both deny, so the user-level one
  hides the result. Load a copy with a renamed plugin and a tagged deny reason, then look for the tag.
- The hazard hook asks before `rm`. A live test that cleans up inside the project then sees every write
  refused until a PO/QA permit or the Regent's `libere`; clean up in a temp folder instead, which starts
  no watch. Release with `python scripts/hook-hazard.py --clear`.
- Run `doctor.py` with `PYTHONUTF8=1` on Windows: under the cp1252 console the hook wire check and the
  `ux brief` check crash on `§` and `⟨` before they test anything.
- Hook self-tests build their project with `hook_wire.build_fixture` in a temp folder and point session
  state at `REGENCY_HOOK_STATE`; never run a self-test against a real project.

## Decisions

| Date | Decision (the Regent) | In force |
|---|---|---|
| 2026-10-06 | regency is self-contained: every convention, rule and template it relies on has its source inside this folder; machine-level copies are installed from here | yes |
| 2026-10-06 | `scripts/install-rules.py` manages `~/.claude/rules/` (it took over the hand-made copies; `.bak` kept) | yes |
| 2026-10-06 | the UI-text rule also loads for `.jsx`, `.tsx`, `.vue`, `.svelte` | yes |
| 2026-10-06 | the push guard ships with the plugin (`hooks/hooks.json`); the user-level hook stays as a second guard until the plugin hook is confirmed live | yes |
| 2026-10-06 | Glyph is outside regency's scope for now: the Order templates are read from `library/orders/README.md` alone; revisit when Glyph joins | yes |
| 2026-10-09 | R5: cloud reads run, a cloud write needs the exact command quoted by the Regent in the pass; the hazard watch ends only on a release verb; checkpoint journal and fingerprints are tracked in git; guards fail closed | yes |
| 2026-10-17 | the hazard watch interrupts nobody: it starts only when a destructive command reached the project, refuses the writes no permit covers, and a `po` or `qa` role agent grants the permits — a session list, when needed; the release verb still ends it | yes |
| 2026-10-08 | R4: hooks are triggers, scripts are engines; SessionStart resume slice; PostToolUse fingerprint + STALE; PreToolUse acts and naming guard with the hazard watch; no Stop hook (`library/hooks.md`) | yes |
| 2026-10-28 | R9: the app's own sources are English — templates, moulds, commands, playbooks, scripts, samples; only inputs vary, quoted as they are; `scripts/conventions_check.py` fails on Portuguese elsewhere | yes |
| 2026-10-23 | speed modes `order:lazy`, `team:extreme-go-horse`, `team:just-in-time` (`library/team/SPEED_MODES.md` §9): speed trades verification depth, never T4, T5, infrastructure or a destructive-class action; drafts stay DRAFT/UNVERIFIED on plumbing until a team pass verifies them; models set at spawn, never in `library/agents/` | yes |

## Machine-level pieces and their sources

Everything installed outside this folder has its source here; the installers never overwrite a file they
did not create (`--check`, `--uninstall`, `--force` keeps a `.bak`).

| Installed at | Source here | Installer |
|---|---|---|
| plugin hooks | `hooks/hooks.json` → `scripts/` (`library/hooks.md`) | none: ship with the plugin |
| `~/.claude/agents/{po,dv,qa,da}.md` | `library/agents/` | `scripts/install-agents.py` |
| `~/.claude/rules/*.md` | `library/rules/` | `scripts/install-rules.py` |
| `~/.claude/CLAUDE.md` (one import) | `library/templates/user-CLAUDE.md` | by hand: copy it, replace `{{REGENCY_ROOT}}` with this folder's path |
| push guard without the plugin | `scripts/guard-push.py --snippet` | by hand, into `~/.claude/settings.json` |
| hazard watch state | written by `scripts/hook-hazard.py` | none: `$CLAUDE_PLUGIN_DATA/sessions/`, or the system temp folder |
