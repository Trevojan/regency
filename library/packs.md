# Packs — regency, specialised

A **pack** is what regency becomes in one domain. It is a folder holding `pack.json` and its files: adopted from any
Claude Code plugin or skill as it is, or written native. regency 3.0 introduced packs (the Regent, 2026-10-29: "as an
open-source Harness, it must be the most flexible and the most adaptable as possible"). Engine:
`scripts/packs.py`; dispatcher: `scripts/hook-packs.py`; playbook: `skills/pack/SKILL.md`.

## 1. Layers

| Layer | Folder | Travels with | Rule |
|---|---|---|---|
| public | `<regency>/packs/<id>/` | regency's repository and its `.plugin` | an open-source license regency may redistribute; `adopt` refuses a source without one |
| project | `<guidelines>/.packs/<id>/` | the project's repository | any license; the material stays with the project that owns it |

A project pack with the id of a public pack **shadows** it in that project; `packs.py check` says so. A machine layer
(private packs for every project on one computer) was offered and not chosen; adding it later is one more entry in
`layer_dirs`.

## 2. Why regency reads packs itself

Claude Code loads what a plugin's manifest declares once per install, for every project, from paths inside the plugin.
That is the limit a per-project specialisation meets, and it is passed by reading packs at run time:

| Claude Code's limit | The way past it |
|---|---|
| Skills, hooks and MCP servers load per install, never per project | `/regency:pack run` opens a pack's playbooks as files; `hook-packs.py` runs a pack's hooks only where the pack is active |
| Every registered skill costs always-on tokens in every session | pack playbooks are not registered: one router skill (`pack`) reaches all of them, at no extra always-on cost |
| Component paths must stay inside the plugin's folder | the router and the dispatcher read packs from any layer |
| A top-level `bin/` blocks a claude.ai install | an adopted `bin/` sits under `packs/<id>/upstream/`, not at regency's top level |

## 3. The manifest

```json
{
  "schema": 1,
  "id": "glyph",
  "title": "glyph-markup",
  "summary": "one line",
  "version": "the source's own version, or null",
  "origin": {"kind": "adopted", "from": "skill | plugin", "name": "…", "source": "…", "repository": null,
             "ref": null, "sha": null, "license": "MIT | null", "adopted": "YYYY-MM-DD", "tree": "<sha12 of upstream>"},
  "root": "upstream",
  "when": {"files": ["*.pgml"]},
  "requires": [{"tool": "node", "why": "upstream/scripts/glyph-cli.js"}],
  "items": [{"key": "playbook:glyph-markup", "kind": "playbook", "name": "glyph-markup", "path": "upstream/SKILL.md"}],
  "unsupported": [{"what": "…", "path": "…", "why": "…"}]
}
```

`root` is where `${CLAUDE_PLUGIN_ROOT}` points for this pack. `when.files` only suggests the pack (`packs.py
suggest`); activation is always explicit. A native pack writes the same manifest by hand, with `"origin": {"kind":
"native"}` and no `root`.

## 4. Adoption: what an incoming plugin becomes

`packs.py adopt <folder | git url> --id <id> --layer public|project` copies the source verbatim under
`<layer>/<id>/upstream/` and writes `pack.json`. A git url is cloned shallow and its commit recorded. Nothing is
rewritten, so no rework and no re-proposal: the source keeps its own conventions (regency's checks skip
`packs/*/upstream/`).

| In the plugin | Becomes | In 3.0 |
|---|---|---|
| `skills/<name>/SKILL.md`, manifest `skills`, a root `SKILL.md` | `playbook:<name>` | run through `/regency:pack run` |
| `commands/*.md`, manifest `commands` (paths or map with `source`) | `command:<name>` | run through `/regency:pack run` |
| `agents/*.md`, manifest `agents` | `agent:<name>` | dispatched as a subagent whose prompt is the file's body |
| `hooks/hooks.json`, manifest `hooks` (files or inline) | `hook:<Event>:<n>`, one per handler | dispatched once ratified (§6) |
| `.mcp.json`, manifest `mcpServers` | `mcp:<name>` | `packs.py mcp <id> --write --yes` adds them to the project's `.mcp.json` |
| a `LICENSE`, `COPYING` or the manifest's `license` | `origin.license` | required in the public layer |
| scripts by extension, launchers in commands | `requires` | `show` says which are missing from PATH |

Listed under `unsupported`, each with its reason, never dropped silently: LSP servers, output styles, workflows,
themes, monitors, `settings.json`, `bin/` on PATH, `userConfig`, channels, plugin dependencies, inline command bodies,
prompt / agent / http hooks, hooks reading `${user_config.*}`, an `if` filter other than `Tool(glob)`, and hooks on
events the dispatcher does not serve. Stop and SubagentStop hooks are refused by R4.5.

A pack is adopted once. Re-adopting a newer upstream with a diff, keeping the better side (conventions §4), is on the
roadmap.

## 5. Activation and consent belong to the project

`<guidelines>/.packs/active.json`:

```json
{"schema": 1, "packs": {"glyph": {"layer": "project", "since": "2026-10-29",
                                  "ratified": {"hook:PreToolUse:0": {"tree": "<sha12>", "on": "2026-10-29"}}}}}
```

- `activate` switches a pack on: its playbooks become runnable here. `deactivate` drops it and its ratifications.
- `ratify <id> <item | hooks | all>` without `--yes` is the review: each hook's event, matcher and exact command.
- `ratify ... --yes` records the Regent's consent at the pack's **tree fingerprint** (every file of the pack folder).
  `hook-hazard.py` asks on that call (kind `consent`): ratification is the Regent's alone (T5).
- Any change to any file of the pack makes its ratified items STALE; a STALE hook does not run.

What the fingerprint protects against: changes arriving unnoticed (a pull, a merge, an agent's edit). It does not
protect against someone who can already write `active.json`; that person holds the project.

## 6. The dispatcher

`scripts/hook-packs.py` is wired on SessionStart, UserPromptSubmit, PreToolUse (`*`), PostToolUse (`*`), PreCompact and
SessionEnd. For one event it runs every hook item of every active pack that is ratified at the current tree and
matches the event (the matcher against the tool name, session source or compact trigger; an `if` of the form
`Tool(glob)` against the command or path). Each runs as Claude Code would run it: the event on stdin,
`${CLAUDE_PLUGIN_ROOT}` at the pack, `${CLAUDE_PLUGIN_DATA}` at a folder of its own, `${CLAUDE_PROJECT_DIR}` at the
repository, within its timeout and the dispatcher's 110 s budget.

| A pack hook answers | The dispatcher passes on |
|---|---|
| `permissionDecision: deny` or `ask` (PreToolUse) | the most restrictive, with each pack's reason |
| `permissionDecision: allow`, `updatedInput` | **nothing**: a pack may add a guard, never remove one |
| exit 2 | deny (PreToolUse), block (PostToolUse, UserPromptSubmit), a message elsewhere |
| `additionalContext`; plain stdout on SessionStart and UserPromptSubmit | the text, prefixed `[<pack>]` |
| `systemMessage` | the message, prefixed with the pack |
| `continue: false` | stop, with the pack's reason |
| a crash, a timeout, a missing interpreter | one `systemMessage` line naming the pack and the hook |

Async hooks start and are not waited for. The dispatcher has no `onFailure: block`: a broken pack never stops the
session, it is reported instead.

**Cost.** It runs on every tool call of every project, so its fast path parses nothing and imports nothing heavy: it
stats `<guidelines>/.packs/active.json` under the session's project and exits. Measured on Linux: 21.7 ms against
13.9 ms for a bare Python start (+7.8 ms) with no pack active. With active packs it reads the manifests and checks
the fingerprint through a stat-signature cache (size, mtime and, on POSIX, change time), re-hashing only what moved.

## 7. Checks

- `packs.py check`: manifests (schema, id = folder, unique keys, item paths inside the pack, hooks on dispatched
  events), the public layer's licenses, upstream drift since adoption, shadowing, and in a project: active packs that
  exist, STALE ratifications, hooks waiting for consent.
- `scripts/doctor.py` runs `packs.py --selftest` and `check` on the public layer; the hook's own self-test runs with
  the other hooks.

## 8. Roadmap

| Next | What it adds |
|---|---|
| re-adopt with a diff | a newer upstream lands beside the pack; the better side stays (conventions §4); ratifications go STALE |
| native sockets | items a pack declares for regency's own parts: health check sets, station gate tasks, suba lenses, phase checklists, vocabulary, id grammars, scaffolds |
| frontend as a pack | `ux-init` and `tailwind-audit` moved into `packs/frontend` |
| more of the plugin format | LSP servers, monitors and output styles, through a generated per-project plugin, or not at all |
| health and resume | `/regency:health` and the resume line report packs: active, waiting, STALE |
