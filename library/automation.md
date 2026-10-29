# Automation — auto mode and headless runs

How the Regent's rules reach a session nobody is watching step by step. Two pieces, three files, one
runner. Everything here is read by a script; the prose only says why.

| Piece | Source (edit here) | Consumer |
|---|---|---|
| Auto-mode profile | `library/automode.json` | `scripts/install-automode.py` (interactive), `scripts/headless.py` (`work` profile) |
| Headless routes | `library/headless.json` | `scripts/headless.py`, the only runner |

## 1. Auto mode

Auto mode replaces the permission prompt with a classifier. Its rules come from three places only:
`~/.claude/settings.json`, managed settings, and the `--settings` flag. **A project's `.claude/settings*.json`
is never read for `autoMode`**, so regency cannot ship the profile inside a project: it ships a settings
fragment and two ways to apply it.

- **Interactive:** `python scripts/install-automode.py` merges the entries into `~/.claude/settings.json`.
  It changes only entries that open with `Regency `, keeps a `.bak`, and `--uninstall` takes them back out.
- **Headless:** the `work` profile passes `library/automode.json` itself with `--settings`. Nothing is
  installed.

**What the profile adds, and why each line exists.** The built-in rules already cover most of
conventions §5 (destructive local commands, force-push over others' work, production deploys, shared
resources, exfiltration). The profile adds only what they miss or contradict:

| List | Entry | Why the defaults are not enough |
|---|---|---|
| `hard_deny` | main branch | the built-in *Git Push Destination* allows pushing the default branch; conventions §4 says the Regent pushes `main` |
| `hard_deny` | acts | closed Orders, gate sheets, ladders and dated handoffs are tracked files, so *Irreversible Local Destruction* does not see them (§7) |
| `hard_deny` | trust | `mise trust` is ratification (`skills/station/SKILL.md`) |
| `soft_deny` | cloud writes | the defaults judge production; conventions §6 wants every cloud write quoted, any environment |
| `soft_deny` | installs | the built-in *Toolchain Bootstrap* allows official installers; conventions §5 asks first |
| `soft_deny` | staging, branch layout, merge to main | §4 and §5; the defaults judge only destruction |
| `environment`, `allow` | toolkit folder | reading regency from another project would otherwise look like scope escalation |

Every list keeps `"$defaults"`. A list without it discards every built-in rule in that list.

**The gates stay.** The classifier is a second opinion, not the gate: the hooks (`library/hooks.md`) still
decide every call when the plugin is loaded. The profile matters most where the hooks do not run: a machine
where regency is not enabled as a plugin.

**After a change:** `python scripts/install-automode.py`, then `claude auto-mode config` (what the
classifier uses) and `claude auto-mode critique` (a review of the custom entries).

## 2. Headless runs

A headless run is a text-output machine: the Regent picks a **route** in a shell, the route runs, plain text
comes back with an exit code. The Regent drives; the run never asks.

```bash
python <regency>/scripts/headless.py                    # the routes, one line each
python <regency>/scripts/headless.py ongoing            # a script route: no model at all
python <regency>/scripts/headless.py measure tree       # a command route: /regency:measure-changes tree
python <regency>/scripts/headless.py ask "where is the ledger written?"
git diff | python <regency>/scripts/headless.py critical "this diff keeps the API stable"
python <regency>/scripts/headless.py proceed -- --max-budget-usd 3
python <regency>/scripts/headless.py <route> ... --dry-run    # print the exact call; run nothing
```

Run it from the project's directory. `headless.py --check` validates the table; doctor runs it.

### 2.1 Three kinds of route

| Kind | Runs | Cost | Use for |
|---|---|---|---|
| script | a regency script with the current Python | none | anything a script already answers (rule zero: mastery spares synthesis) |
| command | one `/regency:<command>` through `claude -p` | a model run | a playbook |
| prompt | the Regent's own text through `claude -p` | a model run | what no route names (`ask` reads, `do` works) |

A script route is the first rung of the ladder (conventions §15.1): when a script answers, no model runs.

### 2.2 Two profiles

| Profile | Permission mode | What runs | What happens to the rest |
|---|---|---|---|
| `read` | `dontAsk` | reads, searches, the built-in read-only commands, regency's read-only scripts | denied at once; the run reports it |
| `work` | `auto` with `--permission-prompts none` and `--settings library/automode.json` | what the classifier allows under §1 | denied; the run names it as a blocker |

Neither profile can ask: a soft-deny becomes a denial, which is how *ask first* (conventions §5) reads
when nobody is there.

### 2.3 What every model run gets

- `--add-dir <regency>` and `--plugin-dir <regency>`: the playbooks, scripts and hooks load from the folder
  itself. Pass `--no-plugin` when regency is already installed as a plugin, so it does not load twice.
- the preamble from `library/headless.json`, sent with `--append-system-prompt-file`: conventions bind,
  doubts go in the reply, no commit, and the reply's shape — first line `<route> · <verdict> · <summary>`,
  then done / left / blocked, Doubts, files changed, and the assumption line.
- the prompt on **stdin**, never on the command line: on Windows `claude` is often a `.cmd` shim, and
  free text there would be reparsed by `cmd.exe`. The runner refuses to pass an argument `cmd.exe` would
  misread.
- `--output-format text`. Extra flags after `--` go to `claude` as they are.

### 2.4 Refused routes

Some commands stay interactive; `library/headless.json` names each with its reason under `refused`, and
the runner answers with that reason and exit code 3. `arrange-cycle-commit` is the main one: merging and
pushing reach outside the machine, and the Regent watches each step. A headless run leaves the work in the
tree; the Regent commits with `/regency:arrange-cycle-commit` in a session.

### 2.5 Adding a route

1. Add one entry to `routes` in `library/headless.json`: `id`, `summary`, and one of `script` (with
   `args`), `command` (a registry id, `a` or `a:b`) or `prompt`; a model route also names its `profile`.
   `hint` and `default` are optional.
2. `python scripts/headless.py --check`, then `python scripts/doctor.py`.

Never add a script for a route. If a route needs logic, the logic belongs in the script the route calls.

## 3. Exit codes

| Code | Meaning |
|---|---|
| the route's own | a script route returns its script's code; a model route returns `claude`'s (0 = the run finished) |
| 2 | usage, unknown route, a broken table, or an argument a `.cmd` shim would misread |
| 3 | refused route |
