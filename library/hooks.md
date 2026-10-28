# Hooks — triggers that call scripts

Decision records R4 and R5 (`REGENCY_CUSTOMIZATION.md`). Wiring: `hooks/hooks.json`. Health: `scripts/doctor.py`
checks 12 and 15. Every script here is Python standard library and imports `scripts/hook_wire.py`.

## 0. The rule

**Hooks are triggers, scripts are engines (R4.1).** A hook entry holds no logic: it runs one script from
`scripts/` through `${CLAUDE_PLUGIN_ROOT}`. The script answers with at most **one slice line** of context
or one permission decision. Every script has a `--selftest` that plants one defect per rule, and doctor
also feeds each script a real event on stdin, because a broken hook fails open.

Two kinds:

| Kind | Does | On its own error |
|---|---|---|
| **guard** | decides a tool call: `deny`, `ask`, or nothing (allow) | answers `ask` with the error: the Regent decides, nothing passes silently; `onFailure: block` covers a script that cannot start |
| **recorder** | writes a trace or adds one context line; never blocks | stderr only; the session is never disturbed |

**Adoption gate.** Recorders write only in a project that already has `<guidelines>/.shortcuts/.virtual/`.
They never create guideline folders (`library/layouts.md` §1). Outside the Regent's projects the plugin
is silent.

**No Stop hook (R4.5).** The next-step line lives in each playbook. `SubagentStop` is wired only to the
journal, which records and never blocks. Doctor fails if a `Stop` hook appears.

## 1. What runs, when

| Event | Matcher | Script | Kind | Answer |
|---|---|---|---|---|
| `SessionStart` | `startup\|resume\|clear\|compact` | `hook-resume.py` | recorder | one resume line (R4.2) |
| `UserPromptSubmit` | — | `hook-verbs.py` | recorder | opens a pass: records the cloud writes the Regent quoted; a release verb ends the hazard watch; routes a Regent verb |
| `PreToolUse` | `Bash`, `PowerShell` (`if: git *`) | `guard-push.py` | guard | `deny` a push to main/master |
| `PreToolUse` | `Bash`, `PowerShell` | `hook-hazard.py` | guard | `deny` an unconfirmed cloud write; `ask` destructive, layout, install |
| `PreToolUse` | `Edit\|Write\|MultiEdit\|NotebookEdit` | `hook-acts-guard.py` | guard | `deny` `.scope/`, acts, a hand edit of the shortcuts state block (R7), lock slices, banned names, and under hazard watch a path no PO/QA permit covers (R4.4) |
| `PostToolUse` | `Edit\|Write\|MultiEdit\|NotebookEdit` | `hook-lineage.py` | recorder | fingerprint into the shortcuts store; STALE under governing slices (R4.3, R7) |
| `PostToolUse` | `Bash\|PowerShell` | `hook-hazard.py` | recorder | switches the hazard watch on after a destructive command that reached the project |
| `PostToolUse` | `Agent\|Task` | `hook-hazard.py` | recorder | records the write permits a `po` or `qa` role agent returned |
| `PostToolUse`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `PreCompact`, `SessionEnd` | as wired | `hook-journal.py` | recorder (async) | none: appends one checkpoint line |
| `SubagentStart` | — | `hook-gov.py` | recorder | one governance slice line for a regency role or `suba-` (§3) |
| `PostToolUse` | `Agent\|Task` | `hook-gov.py` | recorder | routes the returned packet: G1 → ledger, G2/G3 → Regent; one context line |
| `SessionEnd` | — | `hook-shortcuts.py` | recorder | none: rewrites the generated state block of `.shortcuts/README.md` when the state moved (R7.3) |

## 2. Guards

### Push to main — `guard-push.py`

Unchanged: the Regent pushes `main` (conventions §4). 38-case table.

### Hazardous shell — `hook-hazard.py`

| Kind | Examples | PreToolUse | Starts the watch |
|---|---|---|---|
| `cloud-read` | `kubectl get`, `aws s3 ls`, `aws ec2 describe-*`, `gcloud … list`, `terraform plan`, `--help` | nothing: runs | no |
| `cloud-write` | every other cloud CLI call, an unknown verb included | **deny**, unless the Regent quoted that exact command in this pass (conventions §6, R5.1) | no |
| `history` | `git rebase`, `git push --force`, `git filter-repo` | ask | yes |
| `discard` | `git reset --hard`, `git checkout -- <paths>`, `git restore` | ask | yes |
| `delete` | `rm`, `Remove-Item`, `git clean -f`, `git branch -D`, `find -delete`, `DROP TABLE` | ask | yes |
| `layout` | `git worktree add/remove` | ask | no |
| `install` | `sudo …`, `apt-get install`, `brew install`, `winget install` | ask | no |

Commands are tokenised by `guard-push.py`'s quote-aware splitter: text inside a commit message or an
`echo` is not a command; `bash -c "…"` is read inside. Every segment of a chain is judged: a confirmed
cloud write chained with `rm` still asks for the `rm`.

**Where the cloud verb sits.** `kubectl`, `helm`, `terraform`, `gsutil`, `bq` and the other single-verb
CLIs: the first word after the command. `aws`: the second (`aws <service> <operation>`, where
`describe-`, `list-`, `get-` read). `gcloud`, `az`, `doctl`, `oci`: the first known verb after the group.
A verb that is neither a known read nor a known write counts as a write.

**Confirming a cloud write.** A *pass* is the work between two messages of the Regent. At each message,
`hook-verbs.py` collects the cloud commands the Regent quoted (in backticks, in a code block, or alone on
a line) and they replace the previous list. A cloud write runs only when it equals one of them token by
token: quotes and spacing do not count, any other difference does (`--region us-east1` is not
`--region us-west1`).

### Writes — `hook-acts-guard.py`

First match wins:

1. **`.scope/`** anywhere in the path → deny. The Regent's raw material is read-only (R4.6).
2. **An existing act** → deny; writing a *new* one passes. Acts by file name: `ORD-####…`, `GT-##…`,
   `GATE_…`, `LADDER_…`, `…opinion…`, `…handoff…YYYY-MM-DD…` (conventions §7).
3. **A lock slice** cites the file in the manifest → deny; the Regent changes the norm first.
4. **A new name** (file or missing folder) carries `Base`, `Abs`, `Mgr`, `Helper`, `Common`, `Utils`
   → deny (conventions §14). Existing files keep their names.
5. **Hazard watch on** and no permit covers the path → deny, naming the two ways through: a permit, or
   the Regent's release verb.

### The hazard watch

```text
off ──(a destructive command reached the project: PostToolUse)──▶ on ──(the Regent says a release verb: UserPromptSubmit)──▶ off
              while on: a file write no permit covers is refused; reading, searching, git status stay free
              an ordinary message from the Regent keeps it on (R5.2)
```

**Reaching the project.** `history` and `discard` always do. A `delete` does unless every path it names
lies outside the project root: `rm -rf` on a temp or scratch folder starts nothing. A path the hook cannot
resolve (`$d`, a glob) counts as inside.

**Permits.** The watch interrupts nobody: the refusal goes to the agent, not to a pop-up. The agent
dispatches the `po` or `qa` role agent with the files it needs and why; the role agent answers with one
line per grant, `permit: <glob>[, <glob>] -- <reason>`, and `hook-hazard.py` (`PostToolUse Agent|Task`)
records the globs for the session. A line without a reason grants nothing; any other agent's lines are
ignored, so the agent that needs a permit never grants it (conventions §1). A role agent may grant ahead
of any watch: that is the session's permission list. Globs match the path relative to the project root.
Permits need the role agents installed (`scripts/install-agents.py`); without them, only the release
verb opens the watch.

The release verbs are the rows of conventions §9 whose command is `hook-hazard.py --clear`
(`libere`, `release`); the ask shown on every write names them. Session-scoped, stored outside the
repository (`$CLAUDE_PLUGIN_DATA`, else the system temp folder). Manual release:
`python scripts/hook-hazard.py --clear`.

## 3. Recorders

### Lineage — `hook-lineage.py`

After a file write in an adopted project:

- `shortcuts.record()` → `<virtual>/shortcuts.db`: the file's row (sha256, bytes, mtime, the hash it replaced,
  when, session) and, for a guideline doc, its nodes (`library/shortcuts.md` §3); a norm doc the hook writes a
  STALE line into is recorded too, so the hook's own write never reads as drift
- each `mark_stale` slice citing the file gets, once per changed file, right under its anchor:
  `[warn'STALE' on='YYYY-MM-DD' changed='<rel>' by='hook-lineage'] check this slice against the code; only a human removes this line`
- a `ledger_row` slice is never written inside its table: the context line names it instead
- one context line lists the slices now out of date

The slice resolver is `scripts/vp.py` (`resolve`); `vp.py stale` lists what the hook wrote.

### Journal — `hook-journal.py`

`<virtual>/checkpoints.jsonl`, append-only, trimmed to the latest 200 lines. One line per file write,
git state change, hazardous command, subagent start/stop, task created/completed, compaction and
session end. Harmless shell commands and reads are not recorded.

```json
{"ts": "2026-10-09T20:28:20-03:00", "regency.event": "PostToolUse",
 "gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": "Edit", "gen_ai.tool.call.id": "toolu_…",
 "gen_ai.conversation.id": "<session>", "gen_ai.agent.name": "main",
 "regency.target": "src/Page.razor", "regency.unit": "M03.D02.T04"}
```

Keys follow the OpenTelemetry GenAI semantic conventions so the file can be shipped to an OTel backend
as is. `python scripts/hook-journal.py --tail 20` prints the last lines.

### Governance — `hook-gov.py` (engine: `scripts/gov.py`)

After Jan Kooiman (*Modern Governance*, 1993, ed.; *Governing as Governance*, 2003). Every packet a role or
`suba-` returns opens with two lines:

```text
gov: order=G2 · mode=co · element=image · from=QA · to=RGN · unit=M03.D02.T04
ask: approve SPEC v3 (criterion C-04 untestable)
```

| Field | Values |
|---|---|
| `order` | `G1` solving problems · `G2` institutions (SPEC vN+1, gates, ladder, escalation) · `G3` norms (conventions, maxims) |
| `mode` | `hier` down the tree (and PO → QA dispatch) · `co` between managers, or a manager and the Regent · `self` inside the span |
| `element` | `image` (spec, criterion, intent) · `instrument` (hook, gate, lint, template) · `action` (test, build, defect) |

G1 stays in the ledger; G2 and G3 reach the Regent. A missing, malformed or under-declared header routes up (E2):
a G1 whose text names a spec version or escalation climbs to G2, one that names a convention to G3. DA ↔ DV,
`hier` upward, `co` from an operator, G3 to anyone but the Regent and G2 to an operator are refused.
Tags are G1/G2/G3, never O#: regency's levels already use O4–O1.

### Resume — `hook-resume.py`

```text
regency resume · ledger 1 ongoing / 1 review / 1 blocked / 2 backlog · STALE 1 · latest Order ORD-0001
· last checkpoint 2026-10-09T20:28:20-03:00 Edit src/Page.razor · shortcuts check 0 · drift 0
· first peek: shortcuts.py peek, vp.py trace
```

`shortcuts check N · drift N` comes from `shortcuts.summary_part()` (R7). After compaction it reads
`regency resume after compact`. `--print` shows the line for the current folder.

### Shortcuts — `hook-shortcuts.py`

At `SessionEnd`, `shortcuts.refresh()`: the block between the `shortcuts:state` markers of
`.shortcuts/README.md` is rewritten when the state moved and left alone when it did not; no markers, no
write. No hashing, so it fits the shared 1.5 s `SessionEnd` budget. The engine is `scripts/shortcuts.py`
(`library/shortcuts.md`).

### Verbs — `hook-verbs.py`

Every message of the Regent opens a pass. The hook:

1. records the cloud commands quoted in the message as the pass's confirmed writes (replacing the last
   list; a message with none clears it);
2. ends the hazard watch when the message opens with a release verb;
3. otherwise, for a message of 80 characters or fewer that opens with a verb, adds one line:
   `Regent verb 'prossiga' = work the whole queue -> /regency:proceed (conventions §9)`.

Verbs come from the table in `library/conventions.md` §9, the only copy (`hook_wire.regent_verbs`).
Slash commands are never routed. `--table` prints the verbs as parsed.

## 4. Files the hooks touch

| File | Written by | Read by | Where |
|---|---|---|---|
| `<virtual>/shortcuts.db` | lineage, shortcuts, `shortcuts.py index` | `shortcuts.py drift`, `check`, `peek`; resume | project, gitignored (`<virtual>/.gitignore`) |
| `.shortcuts/README.md` state block | shortcuts | every returning agent | project |
| `<virtual>/checkpoints.jsonl` | journal | resume, handoff | project |
| `<virtual>/gov-queue.jsonl` | gov | `gov.py queue`, `gov.py fit`, the Regent | project |
| norm slices (one STALE line) | lineage | `vp.py stale`, the Regent | project |
| `<state>/sessions/<session>.hazard.json` | hazard | acts guard, verbs | machine, outside any repository |
| `<state>/sessions/<session>.cloud.json` | verbs | hazard | machine, outside any repository |

`<virtual>` is `<guidelines>/.shortcuts/.virtual/`. `checkpoints.jsonl` and `gov-queue.jsonl` are tracked in git
with the ledger (R5.3); `shortcuts.db` is a gitignored cache any clone rebuilds with `shortcuts.py index` (R7.2,
which replaces the tracked `fingerprints.json`); the session files never leave the machine.

## 5. Market standards and where regency meets them

| Practice | Reference implementation | Regency mechanism |
|---|---|---|
| Durable execution: persist state per step, resume a thread from its last checkpoint | LangGraph checkpointers keyed by `thread_id` | journal + resume line; `PreCompact` writes a checkpoint before context is lost |
| Human-in-the-loop interrupt, resumed by human input | LangGraph `interrupt()` / `Command(resume=…)` | `ask` decisions; the hazard watch, released by a release verb |
| Approval scoped to one exact tool call | tool-call approval in agent SDKs | a cloud write runs only as the exact command the Regent quoted, for one pass |
| Idempotent side effects (a resumed step may run twice) | LangGraph interrupt rules (upsert, not create) | STALE written once per changed file; fingerprints upsert; journal append-only and trimmed |
| Tool guardrails with a tripwire that halts the run | OpenAI Agents SDK input, output and tool guardrails | PreToolUse guards (`deny` = tripwire) |
| Input routing before the model call | router / triage agents | `hook-verbs.py`, by table instead of inference |
| Handoffs between agents | OpenAI Agents SDK handoffs; A2A tasks | Orders (`handoff`, `dispatch`), role agents, `invoke_agent` lines in the journal |
| Task life cycle as explicit states | A2A task states | the work ledger (`library/virtualpath.md` §3), mapped below |
| Agent observability with a shared vocabulary | OpenTelemetry GenAI semantic conventions (status: Development) | journal keys `gen_ai.*` |
| Policy as code, failing closed | admission controllers, CI gates | guards answer `ask` on error; `onFailure: block`; doctor proves every guard fails on a planted defect |
| Least privilege per agent | scoped tool sets per agent | role agents' tool limits (`library/agents/`) |
| Data lineage and impact analysis | lineage graphs in data platforms | virtual paths + lineage hook |

A2A task state → ledger state:

| A2A | Ledger | Note |
|---|---|---|
| `submitted` | `backlog` | decided, not started |
| `working` | `ongoing` | needs evidence in `where` |
| `input-required`, `auth-required` | `blocked` | `blocked_by` names who decides |
| `completed` | `review` → `done` | an agent never writes `done` on its own work (T5) |
| `canceled`, `rejected`, `failed` | removed | version control and the handoff are the record |

## 6. Claude Code facts these hooks rely on

Checked against the Claude Code hooks reference on 2026-10-09.

| Fact | Consequence here |
|---|---|
| Exit 0 + JSON on stdout decides; exit 2 blocks with stderr; any other exit is a non-blocking error | every script exits 0 and lets the JSON decide |
| `PreToolUse` answers `permissionDecision`: `allow`, `deny`, `ask`, `defer` | guards use `deny` and `ask`; silence is allow |
| `additionalContext` is wrapped as a system reminder; each string is capped at 10 000 characters | one slice line, capped at 600 by `hook_wire.MAX_LINE` |
| Imperative, command-like context text can trip prompt-injection defences | context lines state facts, never orders |
| `if` is evaluated only on tool events | `if` is used only on `PreToolUse` |
| `async: true` runs in the background, has no timeout and cannot block | the journal is async except on `PreCompact` and `SessionEnd` |
| `onFailure: "block"` blocks the call when the hook cannot start, times out or answers badly (newer versions; older ones ignore the key) | set on every guard; doctor WARNs if one lacks it |
| `SessionEnd` hooks share a 1.5 s budget | the journal's `SessionEnd` entry has a 2 s timeout |
| `CLAUDE_PLUGIN_DATA` is the plugin's persistent data folder | the hazard watch lives there |
| A hook whose script is missing or broken fails open | doctor runs every `--selftest` and the wire test |

The command is `python "<script>"`. A machine where `python` is not on the PATH cannot start any hook:
the guards then block their calls (`onFailure`) and the recorders stay silent. Doctor runs with the same
interpreter it was started with, so run it as `python scripts/doctor.py`.

## 7. Operating

| Need | Command |
|---|---|
| health of every hook | `python scripts/doctor.py` |
| one hook's rules | `python scripts/<hook>.py --selftest` |
| release the hazard watch now | `python scripts/hook-hazard.py --clear` |
| last checkpoints | `python scripts/hook-journal.py --tail 20` |
| the resume line here | `python scripts/hook-resume.py --print` |
| the first read on resume | `python scripts/shortcuts.py peek` |
| is the entry index honest / what changed outside the hooks | `python scripts/shortcuts.py check` · `python scripts/shortcuts.py drift` |
| the verbs as parsed | `python scripts/hook-verbs.py --table` |
| write a packet header | `python scripts/gov.py header --order G2 --mode co --element image --from QA --to RGN --ask "…"` |
| route a packet before sending | `python scripts/gov.py check packet.md --sender suba-validator` |
| what reached the Regent / is the load sustainable | `python scripts/gov.py queue` · `python scripts/gov.py fit --capacity 3` |
| confirm a cloud write | quote the exact command in a message: `` `gcloud run deploy api --region us-east1` `` |

## 8. Adding a hook

1. A new script in scripts/, named hook-<role>.py: import `hook_wire`; a pure `respond(event)`; `--selftest` against
   `hook_wire.build_fixture` with one planted case per rule.
2. Wire it in `hooks/hooks.json` with `${CLAUDE_PLUGIN_ROOT}`; a guard gets `onFailure: "block"`.
3. Add its rows to `REQUIRED_WIRING` and `SAMPLE_EVENTS` in `scripts/doctor.py`.
4. Add its row to §1 here.
5. `python scripts/doctor.py`.

## Sources

- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) and [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [OpenAI Agents SDK primitives](https://futureagi.com/blog/what-is-openai-agents-sdk-2026/)
- [OpenTelemetry GenAI semantic conventions explained](https://www.dash0.com/knowledge/opentelemetry-genai-semantic-conventions-explained)
- [A2A task states](https://a2a.hexdocs.pm/0.2.0/A2A.Task.Status.html)
