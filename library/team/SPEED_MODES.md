# Speed modes

Three commands for when time or tokens are short. They follow one doctrine: **seed the whole terrain
first, cultivate after.** A speed mode brings results out of blank space at the first pass; normal team
passes grow them afterwards. Decided with the Regent on 2026-10-23 (§9).

| Command | Runs | Ends at |
|---|---|---|
| `/regency:order:lazy [EMS-id]` | the Orders of one Emission, in sequence, skipping every Order that needs the Regent | one report: done / skipped / blocked chain |
| `/regency:team:extreme-go-horse [range] fuel=<n>\|fuel=all` | two full teams on disjoint spans, passes chained until the fuel runs out | one packet per pass; the Regent reviews them |
| `/regency:team:just-in-time <from> <to>` | an Opus QA seeds a contract, Haiku DVs draft every task in waves | DRAFT/UNVERIFIED code on plumbing; a normal pass verifies it |

The playbooks are `skills/order/SKILL.md` (lazy) and `skills/team/SKILL.md` (the other two). This file is
the doctrine they point to; read it whole before the first run of a session.

## 1. What speed trades, and what it never trades

| Speed trades | Speed never trades |
|---|---|
| verification depth: fewer reviews, later | **T5** — no role accepts its own work: QA gates and reviews, never accepts; a unit ends at `review` or `draft`, never `done` |
| the human review between passes: the run's own packets wait for one review at the end | **T4** — two QA → DV loops at most; the third failure goes to the Regent |
| the human approval before a commit: the main session commits each DV's change in its worktree and merges it into `plumbing`; nothing goes further | the role contracts: a DV still returns its change uncommitted, a QA still edits nothing |
| framing per task: the PO splits, or the QA seeds a contract | **infrastructure stays with the Regent**: accounts, environments, triggers, scheduled jobs, cloud writes |
| tests, in drafts only (`just-in-time`): they come with the verifying pass | **nothing irreversible or destructive-class runs without the Regent** (below) |
| | the gate: never skipped, only narrowed (`just-in-time` §5) and run in full by the verifying pass |
| | one agent per module (`ORCHESTRATION.md` §4, team check 9); a norm is never ratified by an agent; a span is never widened silently |
| | `main` is the Regent's: everything merges into `plumbing` only |

**Destructive-class** means: anything `library/conventions.md` §5 says to ask about first (deleting,
force, danger-zone commands, worktree or branch layout, system installs, cloud, production or shared
data), every command `scripts/hook-hazard.py` asks about or denies, and reversing a documented decision
(conventions §3). A speed mode stops **before** such an action and names it in its report. The
worktrees a speed mode opens through the Agent tool (§2) are the one layout change the invocation itself
authorises.

**The review queue.** Team check 1 (`skills/team/SKILL.md`) holds a pass while a packet awaits a human
decision. Inside a speed run it counts only the packets that existed **before** the run: the run's own
packets queue up for the Regent's one review at the end. A packet older than the run still holds it.

## 2. Shared mechanics

- **The main session dispatches every agent.** Subagents cannot spawn subagents, so the playbook is
  the coordination of `ORCHESTRATION.md` §12: it splits nothing, judges nothing, and forwards files,
  never its summary of them. A QA steers only through what it writes (a packet, fix notes).
- **Every dispatch uses the prompt skeleton** of `library/team/references/packets.md` §1, with its
  `Stage:` line, so `scripts/hook-gov.py` checks each return against its stage shape (§4 there:
  `po.split`, `qa.seed`, `qa.gate`, `qa.seam`, `dv.draft`, plus the usual ones).
- **Models are set at spawn**, with the Agent tool's `model` override: `opus` (Opus 5.5), `sonnet`
  (Sonnet 5.5), `haiku` (Haiku 5.5). PO and DA get no override and run on the session's model. The role
  sources in `library/agents/` carry no `model:` line and never get one.
- **One worktree per DV** (`ORCHESTRATION.md` §4: one workspace per module): each DV runs with the Agent
  tool's `isolation: "worktree"` and returns its change uncommitted, as its contract says. The main session
  commits it in that worktree, one commit per task, the task id in the subject (and the draft trailers of
  §6 in `just-in-time`), then merges the worktree branches into `plumbing`. A merge conflict between two spans or two
  modules stops that merge and goes to the Regent. Worktrees stay in place after the merge and are listed
  in the report; removing one is the Regent's call (`git worktree remove` asks).
- **`plumbing` only.** If the project's branch contract calls its first branch something else, use that
  name; never `testing`, never `main`. Nothing is pushed.
- **The run's folder** is `<guidelines>/.shortcuts/.virtual/speed/<run>/`, where `<run>` is the mode's
  short name, the date and a counter (`kraken-2026-10-28-1`, `jit-2026-10-28-1`). Every file in it is
  written once: a new pass or wave writes a new file, never over an old one.
- **The ledger stays true** (`library/virtualpath.md` §3): the run writes itself as evidence
  (`pass:<run>`) on each unit it touches; `extreme-go-horse` ends a reviewed unit at `review`;
  `just-in-time` ends a drafted unit at `draft`.
- **Hooks still bind**: the push guard, the hazard hook and the Regent's grants (`library/judge.md`), the acts guard,
  the governance boundary.
- **Fuel, waves and packets are computed, not inferred**: `python scripts/speed.py fuel|range|waves|packet`
  (§7). A playbook step that `speed.py` refuses does not run.

## 3. `/regency:order:lazy [EMS-id]` — the no-brainer run

**The Emission.** An Emission (`EMS-###`, `library/ids.md`) is the set of Orders that name it: every
production Order carries its Emission in its `position` slot ("to which EMS this ORD belongs?"), beside
`goal`, `step`, `repo`, `author` and `deadline`. Find them in the project's `.orders/` (`library/layouts.md`
§2) and take them in the order of their numbers. Without an argument, take the Emission the open Order
names. Nothing found, or Orders that name no Emission: stop with one line naming what was probed. The
Regent opening the Emission's Order is what authorises the run; `lazy` then takes the Emission's Orders
in sequence and never opens another Emission. regency reads Orders; it never writes them.

**For each Order, in sequence:**

1. **Depends on a skipped or blocked Order?** Mark it part of a blocked chain, skip it, take the next.
2. **Needs the Regent?** A slot only the Regent can fill, a decision, a preference or a number only the
   Regent has (`library/orders/README.md`, "Filling slots"), or a documented decision it would reverse:
   **skip it, never guess.** Log it as `SKIP <ORD-id> · <question> · (a) <answer> · (b) <answer>`, two
   candidates each, in the report and in the project's open-questions queue (blockers first).
3. **Destructive-class next step?** Stop the run there (§1).
4. **Otherwise execute it**, deciding on its own wherever the conventions or the Emission settle the
   matter: through its executor (`<skill binds="call-team">` is a `/regency:team` pass, which ends at its
   review packet), or by the model directly for a tree template. Record what was assumed in the project's
   state file, as `/regency:proceed` does.

**Stops at** the end of the Emission, a destructive-class action, or every remaining Order blocked. It
commits, merges and pushes nothing: the work stays in the tree for `/regency:arrange-cycle-commit`.

**Report, once, at the end:**

```text
EMS-011 · lazy · 4/7 done (57%) · 2 skipped · 1 blocked
Done      ORD-0031  <what changed, observable>   packet: <pass or check, green|red>
Skipped   ORD-0033  <question>   (a) <answer>   (b) <answer>
Blocked   ORD-0034  <- ORD-0033
Stopped   end of Emission | destructive: <the action> | all remaining blocked
```

## 4. `/regency:team:extreme-go-horse [range] fuel=<n>|fuel=all` — "Release the Kraken!"

**Fuel first.** It runs only when the Regent has declared the fuel: `fuel=<n>` passes, or `fuel=all`
(until the usage limit stops the session), as an argument or in a message of this conversation. Without
it, refuse in one line: `python scripts/speed.py fuel <arguments>` prints the refusal.

**The range** is two unit ids (`<from> <to>`) or one module or step id; without one, the active tasks of
the module in flight (team check 2). `python scripts/speed.py range` checks the ids against
`library/ids.md`.

**The cast** — eight agents, all dispatched by the main session:

| Role | Team A | Team B | Model | Does |
|---|---|---|---|---|
| PO | PO-A | PO-B | session | PO-A splits the range into span A and span B, along module boundaries (one agent per module); PO-B receives span B. Each hands its span to its DV in ladder order, the criteria cited from the plan. Neither frames, challenges nor accepts during the run. |
| DA | DA-A | DA-B | session | shapes the span's data-touching tasks in one batch before the build; `skipped` when the span touches no data |
| DV | DV-A | DV-B | `sonnet` | builds its whole span straight through, in its own worktree |
| QA | QA-A | QA-B | `opus` | reviews its own team's span at the end of the pass; then both check the seam |

A range inside a single module has one span: team B is not spawned, and the report says so.

**One pass:**

1. **Open.** First pass: the split (`Stage: split`). Later passes: the last packet; its returns go first,
   each to the DV of its team with the artefact exactly as QA or the gate wrote it.
2. **Shape** (DA), when the span touches data.
3. **Build.** Each DV takes its returns first, then continues its span from where it stopped, straight
   through, no review in between. It stops at the end of its span, a span overrun (to its PO, then the
   Regent), a destructive-class step, or its context running out; it names where it stopped.
4. **Merge and gate.** The main session merges both worktree branches into `plumbing` and runs the
   machine gate per task. A red gate is a return to the DV, carried in the packet; that task skips the
   review.
5. **Review.** Each QA reviews its team's span in one batch (`Stage: verify`): one risk opinion per task,
   DV's reasoning withheld as in a normal pass. Then both QAs check the seam where the spans meet
   (`Stage: seam`): shared contracts, imports across the boundary, the merged build.
6. **Packet.** Write `PASS-<nn>.json` (§7), check it with `speed.py packet`, set the reviewed units to
   `review` in the ledger, and report the pass.
7. **Fuel.** One pass spent. Fuel left and work left → the next pass opens from this packet. Fuel spent →
   stop and wait for the Regent.

**T4 inside the chain.** Each return carries its attempt count. A return that fails a third time leaves
the packet and goes to the Regent as an escalation; the pass goes on with everything else.

**Stops** when the fuel is spent (the pass in flight finishes its review and saves its packet first), the
range is built with no return left, a destructive-class action is next, or a span conflict needs the
Regent. Under `fuel=all` the usage limit may stop the session mid-pass: the packet of every finished pass
is already on disk, so only the pass in flight is lost.

**Report, per pass:**

```text
kraken-2026-10-28-1 · pass 2 · fuel 2/3 used
Tasks     A 6 built (M01.S01.T01–M01.S02.T02) · B 5 built (M02.S01.T01–M02.S01.T05)
Verdicts  9 pass · 2 return · 0 not reviewed
Returns   2 carried (attempts 1, 2) · Escalated 1 (M02.S01.T03, third failure) -> RGN
Seam      1 finding
Models    DV sonnet · QA opus · PO, DA session
Packet    .shortcuts/.virtual/speed/kraken-2026-10-28-1/PASS-02.json
```

## 5. `/regency:team:just-in-time <from> <to>` — draft everything, verify later

For example `M01.S01.T01 M03.S06.T09`: every task from one unit to the other, drafted fast so the whole
range exists, verified later.

1. **Seed** — one QA on `opus` (`Stage: seed`) reads the range and writes the interface contract (shared
   types, signatures, the file map) and one task card per task: unit, file, the tasks it depends on, the
   contract parts it uses, its functional goal. It drafts no code. QA has no edit tools, so it returns
   both in its final message; the main session stores them byte for byte as `CONTRACT.md` and
   `cards.json` in the run's folder.
2. **Waves** — `python scripts/speed.py waves cards.json` orders the cards by their dependencies, at most
   one task per module per wave (one agent per module).
3. **Draft** — one DV on `haiku` per card (`Stage: draft`), each in its own worktree, all the wave's DVs
   at once. Each gets its card, the contract and the previous gate's fix notes, applies the fix notes
   first, then drafts its task, functional first, no tests, and returns it uncommitted; the main session
   commits it in the DV's worktree with the draft trailers (§6).
4. **Merge** — the main session merges the wave's worktree branches into `plumbing`.
5. **Gate** — the seeding QA (`Stage: gate`), continued with its context; when it cannot be continued, a
   fresh QA on `opus` that receives `CONTRACT.md`, `cards.json` and the earlier `WAVE-<nn>.json`. It checks
   only that the merged code builds, runs, and matches the contract. It writes fix notes (`FX-<wave>-<n>`) for the next wave and **accepts nothing**. This is
   the build-and-run part of the machine gate; the full gate runs in the verifying pass.
6. **Ledger** — every drafted unit goes `draft`, its `where` naming `branch:plumbing` and its file, its
   `next` the verifying pass. An open question gets the most functional option, and the choice goes into
   the item's `assumed` list (`"<question> -> <option taken>"`) for the Regent to review.

Next wave until the range is drafted. The last wave's fix notes go into the report.

**Report:**

```text
jit-2026-10-28-1 · M01.S01.T01 -> M03.S02.T02 · 12/12 drafted (100%) · 4 waves
Waves     1: 3 · 2: 3 · 3: 3 · 4: 3 (three modules, one DV each per wave)
Gate      wave 2: builds, runs, 2 contract mismatches -> FX-2-1, FX-2-2 (applied in wave 3)
Assumed   M02.S01.T03: date format -> ISO 8601 (review)
Verify    /regency:team M01.S01.T01 … — every unit is DRAFT/UNVERIFIED on plumbing
```

## 6. Drafts: how they are marked, and how they stop being drafts

**Marked twice.** Every draft commit ends with these trailers, and every drafted unit is `draft` in the
ledger (`library/virtualpath.md` §3):

```text
Draft: UNVERIFIED
Unit: M01.S01.T01
Speed-Mode: just-in-time
```

**Held on `plumbing`.** `python scripts/vp.py drafts` lists every unverified draft, ledger item and
commit, and exits 1 while one remains. `/regency:arrange-cycle-commit` runs it before any merge past
`plumbing` and merges nothing further while it fails.

**Verified only by a normal `/regency:team` pass over the unit** — no exception to T3 (§9, decision 1):

| Stage | For a draft |
|---|---|
| Frame, Challenge | `active`, never `reused`: a seed card is an input, not a frame |
| Build | `active`, starting from the draft; DV writes the named tests (T1) |
| Gate | the full machine gate |
| Verify | a fresh QA, never the one that seeded or gated the draft (T5); mutation analysis before the green suite counts (T3) — it is also the red-before-green evidence for code that existed before its test |
| Accept, Close | as always; Close only after the human approves, and its commit carries `Verified-Draft: <unit>` |

The unit goes `ongoing` when the verifying pass starts and `review` when it ends; `vp.py drafts` stops
counting it once the `Verified-Draft:` commit exists.

## 7. The fuel packet

One JSON file per pass (`PASS-<nn>.json`) or per wave (`WAVE-<nn>.json`), written once, in the run's
folder. It is the whole hand-over from one pass to the next: the next pass reads it and nothing else of
the previous one. `python scripts/speed.py packet <file> [previous]` checks it.

```json
{
  "packet": 1,
  "mode": "extreme-go-horse",
  "run": "kraken-2026-10-28-1",
  "pass": 2,
  "fuel": {"declared": "3", "used": 2},
  "range": {"from": "M01.S01.T01", "to": "M02.S03.T04"},
  "teams": {
    "A": {"span": ["M01"], "stopped_at": "M01.S02.T02", "models": {"dv": "sonnet", "qa": "opus"}},
    "B": {"span": ["M02"], "stopped_at": "M02.S01.T05", "models": {"dv": "sonnet", "qa": "opus"}}
  },
  "tasks": [
    {"unit": "M01.S01.T01", "team": "A", "gate": "green", "verdict": "pass", "ledger": "review"}
  ],
  "returns": [
    {"unit": "M02.S01.T02", "team": "B", "from": "QA", "key": "defect-null-total", "attempts": 1,
     "artefact": ".shortcuts/.virtual/speed/kraken-2026-10-28-1/returns/M02.S01.T02-1.md"}
  ],
  "escalations": [
    {"unit": "M02.S01.T03", "key": "defect-rounding", "attempts": 3, "to": "RGN"}
  ],
  "seam": {"findings": ["M01 exports Money as float; M02 imports it as decimal"]}
}
```

| Field | Rule `speed.py packet` checks |
|---|---|
| `mode`, `run`, `pass` / `wave` | known mode; the run id's short name matches the mode; numbered from 1, one more than the previous packet |
| `fuel` | `extreme-go-horse` only: `declared` is a whole number or `all`; `used` equals `pass` and never exceeds a numbered fuel |
| `teams` | at most two; spans disjoint; DV on `sonnet`, QA on `opus` |
| `tasks` | unit ids by `library/ids.md`; `verdict` is `pass`, `return` or `not-reviewed`; a red gate is never `pass`; `ledger` is never `done` |
| `returns` | attempts 1 or 2; a third failure is an escalation, never a carried return; each names its artefact |
| `escalations` | attempts 3 or more, to `RGN` |
| a wave (`just-in-time`) | `units`, `gate` (`builds`, `runs`, `contract`: true or false), `fix_notes` (`FX-<wave>-<n>`), ledger `draft` for every unit |

## 8. Claude Code facts relied on (not yet seen live)

Confirm each row on the first live run, then move it to `library/maintaining.md`.

| Fact | Consequence here |
|---|---|
| The Agent tool takes `model` (`opus`, `sonnet`, `haiku`), which overrides the agent definition's model | the pairing is set at spawn; `library/agents/` stays model-free |
| The Agent tool takes `isolation: "worktree"`: the subagent works in its own git worktree, removed if it made no change | one workspace per DV; the main session merges the branches |
| Subagents cannot spawn subagents | the main session dispatches every agent; the QA steers through what it writes |
| Several Agent calls in one message run in parallel | both teams build at once; a wave's DVs draft at once |
| `SendMessage` continues a spawned agent with its context intact | the QA that seeded a `just-in-time` run gates its waves; without it, a fresh QA gets the run's files |

## 9. Decisions

Decided with the Regent on 2026-10-23 (Project doc `FEATURE_SPEED_MODES.md`).

| # | Subject | Decision |
|---|---|---|
| 1 | `just-in-time` and T3/T5 | no exception to T3; drafts are marked DRAFT/UNVERIFIED and live on plumbing only; a normal `/regency:team` pass verifies them |
| 2 | `extreme-go-horse` models | per team, DV on Sonnet 5.5 and QA on Opus 5.5, set at spawn |
| 3 | `extreme-go-horse` review | none during the pass; at its end, gathered into one packet; the next pass opens from it |
| 4 | the limit | the fuel the Regent declares: `fuel=<n>` passes or `fuel=all`; T4 still applies inside the chain |
| 5 | `just-in-time` drafting | an Opus 5.5 QA seeds the contract and the task cards and gates each wave; Haiku 5.5 DVs draft; the main session dispatches everyone; the QA gates, never accepts |
| 6 | version | `+b`: regency 2.7 |
