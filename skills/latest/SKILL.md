---
name: latest
description: "Regency latest. Bring this machine's installed regency to the newest GitHub release, never to a branch or a working tree: read how it is installed, compare it with the release, then move it on the Regent's one yes, or hand over the verified .plugin when the install is the account's. Never builds from a folder, never moves back, never edits an installed copy. Use for /regency:latest, when a project is newer than the plugin, or 'update the plugin', 'update regency itself', 'is regency up to date'."
argument-hint: "[check]"
disable-model-invocation: true
---

# latest — fit the installed regency to the newest release

> **Root.** This file is `skills/latest/SKILL.md`; the regency root is two directories above it, and
> `library/…`, `scripts/…` paths are relative to it. Read `library/conventions.md` once per session.

`/regency:update` fits a project to the installed regency; this fits the installed regency to the newest
release of `Trevojan/regency`, the only official source. A branch, a working tree or a `dist/` archive is
never "latest": to run one of those for a session, use `claude --plugin-dir <path>` (`library/maintaining.md`).

## Procedure

1. **Read.** Nothing here writes.

   ```bash
   claude plugin list --json              # the entries whose id opens regency@: version, scope, notes
   claude plugin marketplace list --json  # where a marketplace install comes from: repo, ref
   gh release list -R Trevojan/regency --json tagName,isLatest,isDraft,isPrerelease
   ```

   The newest release is the row with `isLatest`; its version is the tag without the `v`. `gh` missing or
   failing is a blocker to report, never "no release": only `[]` means none. An entry noted as not loaded is not
   the install in force. When the regency root is not the entry's `installPath`, say that this session runs from
   that root (`--plugin-dir`), not from the install.

2. **Compare**, version by number (`3.10` is newer than `3.9`). One line:
   `installed <have> (<scope>) · newest release <want>`.

   | Finding | Say, and do |
   |---|---|
   | no release | "regency has no release yet, so there is nothing to move to": step 6, then stop. Publishing one is the Regent's act |
   | same version | "the install fits": step 6, then stop |
   | the install is newer | "the install is ahead of the newest release": step 6, then stop. Never move back |
   | behind, or no install | go on |

   `/regency:latest:check` runs steps 1, 2 and 6 and stops.

3. **Route**, from the entry's `scope`:

   | Install | Route |
   |---|---|
   | `synced`: the account's | Two ways; the pop-up offers both. **The account:** the CLI has no upload, so in a new, empty folder: `gh release download v<want> -R Trevojan/regency -p regency-<want>.plugin -D <folder>`, then `gh release verify-asset v<want> <folder>/regency-<want>.plugin -R Trevojan/regency`. Give the Regent the file's full path: they install it on the account (README, path 7). Never open or run the file. **This machine only:** the no-install route below; a `user` install takes precedence over the account's copy, which cloud sessions keep reading. |
   | `user` or `local`: a marketplace | `gh release verify v<want> -R Trevojan/regency`, then `claude plugin marketplace remove <marketplace>`, `claude plugin marketplace add Trevojan/regency#v<want>`, `claude plugin install regency@regency -s <scope>`. `plugin update` never moves a pinned install and `add` refuses a second ref under one name, so it takes all three; `remove` uninstalls the plugin until `install` brings it back. A marketplace on a path or a branch stops following it: the pop-up says so. |
   | `project` | Declared in that repository's `.claude/settings.json`, so it is the team's: report it and stop. |
   | no install | The marketplace route without `remove`, with `-s user`. |

4. **One yes.** One pop-up: "Move regency `<have>` to `<want>` by `<route>`?", options *Move it* and *Do not
   move*. With several entries, it names each and the one that moves. Read the free text too. No yes, no move.

5. **Move.** Run the route's commands in order, one per call. A failure ends the route, a failed verification
   included: report what it printed, hand nothing over, and never retry another way. A session keeps the copy it
   started with, so nothing changes until a restart.

6. **Machine pieces.** A plugin update moves none of them, and these checks write nothing:

   ```bash
   python <regency>/scripts/install-agents.py --check
   python <regency>/scripts/install-rules.py --check
   python <regency>/scripts/install-automode.py --check
   ```

   A red one names its command, the same line without `--check`. It writes to `~/.claude`, so it runs only on
   the Regent's yes, after the restart, from the new copy.

7. **Report** in the shape below. Commit nothing.

```text
regency latest · installed 3.1 (synced) · newest release 3.4 · behind
Route     account: <full path>/regency-3.4.plugin verified; install it on the account, then restart
Machine   agents current · rules missing · auto-mode missing
Next      /regency:latest:check after the restart; /regency:update in any project its gate names
```

## Boundaries

Never builds or installs from a folder, a branch or a `dist/` archive, never moves an install back, never edits,
moves or deletes anything under `~/.claude/plugins` by hand, never publishes a release, never commits or pushes.
