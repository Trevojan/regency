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
| An installed plugin runs from a **cached copy** (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`), refreshed only when `version` changes | after a change: bump `version` in `.claude-plugin/plugin.json` and `library/registry.json`; a marketplace on a path or a branch then takes `claude plugin marketplace update regency` and `claude plugin update regency@regency`, then a restart; a pinned one moves only by `/regency:latest` |
| A hook whose script is missing or broken **fails open** | `doctor.py` runs every hook script's `--selftest` and feeds each one a real event on stdin |
| A headless session (`claude -p`) cannot read files outside its working directory without `--add-dir <regency path>` | say so in any automation that points at this folder |
| In git-bash, `claude -p "/regency…"` is rewritten into a Windows path | set `MSYS_NO_PATHCONV=1` first |
| A headless `claude` in a shell uses that shell's login, not the desktop app's | a live test needs `claude login` in that shell |
| `--setting-sources project` also drops the user-level login | isolate a test from user hooks with a tagged copy of the plugin (`--plugin-dir`), not by dropping user settings |
| Subagents cannot ask pop-up questions | role agents return `BLOCKED` / `UNRESOLVED` instead |
| Subagents inherit the user-level `CLAUDE.md` | an `@` import of `library/conventions.md` there reaches the role agents too |
| Tool limits in an agent's frontmatter are real for edit tools; a shell can still write files | QA's read-only contract is behavioural when it has a shell; PO has no shell at all |

## Install and git facts (Claude Code 2.1.302, seen 2026-11-06)

| Fact | Consequence here |
|---|---|
| A plugin synced from claude.ai runs from `~/.claude/plugins/synced/<account>/<name>~g<n>/`, and the `claude plugin` CLI has no upload | an account install moves only by the Regent's upload (`/regency:latest`) |
| `claude --plugin-dir <path>` shadows a synced plugin of the same name: `plugin list` notes `synced-plugin-shadowed` and "takes precedence" | one session can run this folder, hooks included, with no upload or commit; **seen in the listing, not yet in a live session** |
| `plugin update` leaves an install pinned at a ref where it is ("already at the latest version"), `marketplace add` refuses a second ref under one name, and `marketplace remove` uninstalls the plugin | moving a pinned install takes remove, add, install: run from 2.13 to 3.3 at user scope in an isolated config (`CLAUDE_CONFIG_DIR`) |
| `gh release list --json` answers `[]` and exit 0 with no release; `gh release view` exits 1 | `/regency:latest` reads the list, so "no release" is never mistaken for a failure |
| A user-scope install also shadows a synced plugin of the same name: `plugin list` shows the synced one "not loaded", with no `installPath`, and its files stay on disk | a marketplace install frees one machine from the account's upload; cloud sessions keep reading the account's copy; seen in the listing |
| `gh release verify` and `gh release verify-asset` | **not yet run**: regency has no release (2026-11-06) |
| A session's hooks read their scripts from the cached folder at each call: a reinstall under the same version label was in force after only `/reload-skills` | a guard can change under a running session; bump the version for anything but a deliberate, temporary load |
| `/reload-plugins` left a synced copy as it was on disk after an update on another machine | whether a full restart syncs it is **not yet seen** |
| `git push` takes a unique prefix of a long flag and a cluster of short ones: `--mir` is `--mirror`, `-fd` deletes, `-odn` is a push option and a real push. A destination `heads/main` lands on `refs/heads/main` | `guard-push.flag_names` and `norm` read them as git does; every form in its table ran against a real bare remote |
| With GitHub Desktop running, a local branch reset behind its upstream came back by itself: reflog `pull: fast-forward`, no checkout, one second after `FETCH_HEAD` | a reset of a published branch lasts until the next fetch, so re-point and force-push in one go |

## Auto mode and headless facts (Claude Code 2.1.302, docs read 2026-10-17)

| Fact | Consequence here |
|---|---|
| `autoMode` is read from `~/.claude/settings.json`, managed settings and `--settings`, never from a project's `.claude/settings*.json` | the profile is `library/automode.json`: installed by `scripts/install-automode.py`, passed by `scripts/headless.py` |
| A list in `autoMode` without `"$defaults"` replaces every built-in rule of that list | the installer validates the source and creates every list with `"$defaults"` first |
| The built-in *Git Push Destination* rule allows pushing the default branch | `hard_deny` carries the main-branch rule |
| `--permission-prompts none` denies whatever would prompt and removes `AskUserQuestion` | the `work` profile uses it; doubts go in the reply |
| In `dontAsk`, the built-in read-only command set still runs | the `read` profile lists no git commands of its own |
| A slash command in a `-p` prompt read from stdin is expanded (seen live: `headless.py status`) | the runner sends every prompt on stdin |
| `claude` installed by npm on Windows is a `.cmd` shim, so its arguments pass through `cmd.exe` | no free text on the command line; the runner refuses an argument `cmd.exe` would reparse |
| `/auto-mode-setup` writes a machine-specific `environment` list to `~/.claude/settings.json`, without `"$defaults"` | the installer keeps that list as it is and appends regency's entries |

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
| `CLAUDE_PLUGIN_DATA` is the plugin's persistent data folder | session state (cloud confirmations, session grants) lives there, never in a repository |
| `PostToolUse` on `Agent`/`Task` carries `tool_input.subagent_type` and the subagent's returned text in `tool_response` | `hook-gov.py` routes packets from it |
| `AskUserQuestion` answers at `PostToolUse` — where a surface puts them is not documented | **not yet seen live**: `hook-judge.py` reads `tool_input.answers`, then `tool_response.answers`, then a `"question"="answer"` text, and names the typed `grant:` line when none arrives; confirm on the first live pop-up (`library/judge.md` §7) |
| Hook types beyond `command` exist (`http`, `mcp_tool`, `prompt`, `agent` — the last experimental; docs read 2026-10-29) | regency's hooks stay `command` scripts (R4.1); a model-judged hook is a candidate for the RGN-DV charter, never for the grant check, which is a lookup |

## Traps met while testing

- The push guard also blocks a test that pushes `main` to a throwaway remote. Seed such a remote with
  `git -C remote.git fetch ../work main:seed` instead of pushing.
- Testing a plugin hook while the same guard is installed at user level: both deny, so the user-level one
  hides the result. Load a copy with a renamed plugin and a tagged deny reason, then look for the tag.
- The hazard hook asks before `rm`. A live test that cleans up its own scratch folder runs without asking
  once the Regent granted it: `grant: delete <absolute scratch path>/** -- test clean-up` (`library/judge.md`).
- A Windows pipe speaks the code page (cp1252), never UTF-8: a script that prints `§` or `⟨` into one crashes,
  and a hook's `§` reached Claude Code as `�` (seen live 2026-11-02, 3.0's hazard watch). `hook_wire` sets
  UTF-8 on stdin, stdout and stderr for every script that imports it; `doctor.py` sets `PYTHONIOENCODING`
  for its children. A new script that prints outside the wire does the same.
- Under `shell=True` on Windows a timeout kills `cmd.exe` only: the command keeps the pipes and the wait
  lasts as long as it runs (a 1 s cut took 6 s). `hook-packs.py` ends the whole tree (`taskkill /T`, a
  process group on POSIX).
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
| 2026-10-09 | R5: cloud reads run, a cloud write needs the exact command quoted by the Regent in the pass; the hazard watch ends only on a release verb; checkpoint journal and fingerprints are tracked in git; guards fail closed | cloud and guards yes; the watch: R15 |
| 2026-10-17 | the hazard watch interrupts nobody: it starts only when a destructive command reached the project, refuses the writes no permit covers, and a `po` or `qa` role agent grants the permits — a session list, when needed; the release verb still ends it | no: R15 |
| 2026-10-08 | R4: hooks are triggers, scripts are engines; SessionStart resume slice; PostToolUse fingerprint + STALE; PreToolUse acts and naming guard with the hazard watch; no Stop hook (`library/hooks.md`) | yes |
| 2026-10-29 | R15: the Judge's grants replace the hazard watch — each hazardous act is judged when it happens against the Regent's grants (where, how, session / repo / machine / a named file); only the Regent grants, by a `grant:` line or the Judge's pop-up; a store changed outside the hooks is STALE until ratified; PO/QA permits and the release verbs retire (`library/judge.md`) | yes |
| 2026-11-06 | the Regent's own line: a command the Regent writes alone on its line runs whole and as written (conventions §5). A `push` grant of the Judge is the only way past `guard-push.py`, and no grant covers deleting the branch, `--all`, `--mirror` or a `+` refspec (`library/judge.md` §2) | yes |
| 2026-11-06 | `/regency:latest`: "latest" is the newest GitHub release only, never a branch, a working tree or a `dist/` archive, so nothing moves until a release exists; an account install ends in the Regent's upload | yes |
| 2026-10-28 | R10: `/regency:update` fits a project to the installed regency on one yes, touching only what regency owns; every writing command runs the version gate first; migrations ship inside the plugin, and a project newer than the plugin means the plugin must be updated (`library/migrations/README.md`) | yes |
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
| `autoMode` entries opening with `Regency ` in `~/.claude/settings.json` | `library/automode.json` | `scripts/install-automode.py` |
| `~/.claude/CLAUDE.md` (one import) | `library/templates/user-CLAUDE.md` | by hand: copy it, replace `{{REGENCY_ROOT}}` with this folder's path |
| push guard without the plugin | `scripts/guard-push.py --snippet` | by hand, into `~/.claude/settings.json` |
| session grants | written by `scripts/hook-verbs.py`, `scripts/hook-judge.py` | none: `$CLAUDE_PLUGIN_DATA/sessions/`, or the system temp folder |
| `~/.claude/regency/JD.md`, `judge.json` | machine grants and every store's fingerprint (`library/judge.md` §3) | none: written by the hooks from the Regent's words; `judge.py ratify --yes` after a hand edit |
