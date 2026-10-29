# Subagent alignment — what every suba inherits instead of restating

A **suba** is a specialised lens *inside* its owner's stage. It is not a fifth role and owns no stage
of its own; the skill format is only the vehicle. Above a suba there is exactly one owner role, and
above the owner the Regent (`RGN`).

Every `suba-*/SKILL.md` points here. **Nothing below is copied into a suba**: a rule written twice is a
rule that drifts (ORCHESTRATION §10).

## 1. Owner

| Owner | Subagents | Owner map (source of truth) |
|---|---|---|
| PO | suba-requirements-analyst, suba-strategy, suba-research, suba-design | `scripts/gov.py` → `OWNER` |
| QA | suba-recon, suba-tester, suba-validator | same |
| DA | suba-acquisition, suba-analysis, suba-modeling | same |
| DV | suba-scribe, suba-architect, suba-implementer | same |

A suba's frontmatter names its owner in `metadata.owner`; `scripts/conventions_check.py` fails when it
disagrees with `OWNER`.

## 2. How an owner uses a suba

A role agent cannot spawn agents of its own, so a suba is **worn, not dispatched**: the owner reads
the suba's `SKILL.md` and works under it for the part of the stage the suba covers. The suba's
"return" is what that lens hands back into the owner's packet.

Read before acting, in this order:

1. The owner's role spec — the project's own `<ROLE>.md` wins (`library/layouts.md`), otherwise
   `library/team/<ROLE>.md` — and its **§19 Control Binding**.
2. The owner's row in `library/team/references/packets.md` §2: what the owner receives, what is
   **withheld**, what it returns.
3. `library/conventions.md`, if not already in context.
4. `library/virtualpath.md` §5 — before touching any governed file, `python scripts/vp.py code <file>`
   and read the slices that govern it.

The packet the owner holds is the suba's whole input. A suba never sees more than its owner may see,
and never uses more than its owner's tools (`library/agents/<role>.md`, `tools:`): QA's subas write no
files, PO's subas run no shell.

## 3. Inherited, never restated

| Concern | Lives in |
|---|---|
| Tree, span, phases F0–F6 | ORCHESTRATION §2, §7 — a suba works **inside the owner's declared span**; needing more halts the work and returns to the owner |
| Cycle order (frame → challenge → model → build → gate → verify → accept) | ORCHESTRATION §14 |
| Managers (PO, QA) and operators (DA, DV); DA ↔ DV never direct | `scripts/gov.py` (`MANAGERS`, `OPERATORS`, `problems()`) |
| Context isolation; artefacts, never reasoning | ORCHESTRATION §11 |
| Escalation (decides alone / consults first / escalates immediately) | owner's spec §12 |
| Definition of done | owner's spec §10 |
| Terminal states | owner's spec §19.11, `library/team/REINFORCED_AGENT.md` §35 |
| Forward-only (SPEC vN+1, no rollback of requirements) | CODE-CONVENTIONS V2, T4 |
| Acts never rewritten | conventions §7 |
| Labels (`RGN`, `RGN-PO`, `RGN-Client`) | conventions §1 |

## 4. Returning

- A suba returns **to its owner only**. The owner routes onward; the suba never addresses another
  role, a sibling suba, a manager or the Regent directly. When a sibling's work is needed, the suba
  names it and the owner obtains it.
- The return is **one JSON envelope** in a `json` code fence — `library/subagents/envelope.schema.json`
  for its frame, the suba's own `contract.json` for its `body`. Each spine's Return section shows the
  template, generated from that contract by `scripts/build.py`:

  | Field | Holds |
  |---|---|
  | `envelope`, `suba`, `via` | the version (1), the suba, and `owner` or `direct` |
  | `unit` | the unit worked on (`library/ids.md` grammar) |
  | `gov` | the hand-up: `order`, `mode: self`, `element`, `from` and `to` the owner (`scripts/gov.py` OWNER), the main finding's `key`, one `ask` |
  | `body` | the suba's own return, exactly as its contract names it |
  | `doubts` | queued doubts (conventions §3), each a closed question with its `key` |
  | `ledger` | what the work ledger needs: `state` (never `done`), with `where` for ongoing, `next` for review, `blocked_by` for blocked |
  | `artefacts` | every `<<<ARTEFACT <name>` block the message delivers — long text never goes into a JSON string |
  | `terminal` | the `state` from the owner's §19.11, and `why` |

  The owner re-heads its own packet when it passes the work on.
- Every `key` names a finding class, so `gov.py recur` can count it: `miss-<topic>` when the answer
  existed but was not reached, `gap-<topic>` when the docs are silent, `gap-skill-<name>` when a
  tactical skill was needed and missing (§6).
- **No field argues correctness**: every object in a contract is closed, so a field the contract does
  not name is refused mechanically.
- The role's final message carries **one envelope per suba it wore**; the boundary checks and records
  them (§10). The orchestrator never forwards an envelope: a later role's packet is built from
  artefacts (packets.md §2).
- **Direct mode** is the one exception. A suba the toolkit also exposes as a command — today only
  suba-scribe, through `/regency:scribe` — returns to whoever called the command with `via: direct`
  and no `gov` block, carries none of its owner's authority there, and follows its contract's
  `returns_direct`.

## 5. Limits shared by every suba

- Never ratifies a norm, never accepts its own work (T5), never widens the span.
- Never reconstructs withheld context from inference; names what is missing and stops.
- Never reverses a documented decision silently: that stops the work and goes up through the owner.

## 6. Skills: core and tactical

| Kind | Used | Listed |
|---|---|---|
| **core** | the suba's own chain, each skill on its "use when" | the spine's **Skills** table |
| **tactical** | extra equipment, worn **only when its trigger fires** — never by default | the spine's **Tactical** table, with the trigger and when to skip it |

Not every suba needs tactical skills; one that needs none lists none. When a trigger fires and the
tactical skill is not installed, the suba carries on with its core skills and names the missing
skill as a doubt keyed `gap-skill-<name>`, so `gov.py recur` shows how often it was missed.

## 7. Shape

```
suba-<name>/
  SKILL.md          the spine: identity, when, input, skills, workflow, return, limits — short
  contract.json     the return contract: the envelope's body, as a schema (§10)
  references/       the doctrine, loaded on demand
```

The spine points; `references/` holds the depth; `contract.json` is the one source of the return
shape, and the spine's Return block is generated from it — never edited by hand. A link from the
spine to a file that does not exist fails `conventions_check.py`. A proposal (§9) may have no
`references/` yet, but it has a contract.

## 8. Drift

`metadata.aligned` in each spine records a fingerprint of the owner's role spec and agent file at the
moment the suba was last checked against them:

```
aligned: library/team/DV.md#c1e1f6a8c3b8 library/agents/dv.md#5f88a4c5c091
```

When either file changes, `conventions_check.py` warns that the suba has drifted and prints the new
fingerprint. The stamp is renewed **only after** the suba has been read against the changed file —
the same rule as removing a `STALE` line (virtualpath §2).

## 9. Proposals

A suba drafted by an agent carries `metadata.status: proposal` and says so in its first line.
`conventions_check.py` warns while the line is there. Only the Regent ratifies — by deleting the line —
and nothing cites a proposal before that (conventions §1).

## 10. Checking returns

A script checks presence and shape, never truth (conventions §15.2).

| What | Checked by | When |
|---|---|---|
| a suba's envelope, against `envelope.schema.json` and its `contract.json` | `python scripts/returns.py check --suba <name> -` | by the owner, before the lens output enters its packet; an owner with no shell (PO) builds it from the template |
| every envelope in a role's final message | `scripts/hook-gov.py` through `scripts/returns.py` | at the boundary, on every role return: logged to `<virtual>/returns.jsonl` (metadata — suba, unit, terminal, ask, keys, misses — never the body), keys counted for `recur`, each miss counted as `key=return-<suba>-<field>`, a suba returned by a role that does not own it refused, a ledger line that disagrees with `ongoing.json` named |
| a role's packet, against its stage shape (`library/team/references/packets.md` §4) | the same hook, when the dispatch carried `Stage:` | at the boundary; each miss counted as `key=return-<stage>-<field>` |

The schemas use a JSON Schema subset the standard library validates (`scripts/returns.py`). A fact
that lives elsewhere is referenced, never copied: `ids:<kind>` reads `library/ids.md`, `gov:<name>`
reads `scripts/gov.py`, `packets:terminal` reads packets.md §4. Beyond the subset, the gate refuses a
value that is wholly `<…>` (an unfilled placeholder), an envelope to its owner without a `gov` block
running from and to the owner, a direct-mode envelope with one, a body naming an artefact the envelope
does not list, a listed artefact the message does not deliver, and a ledger line missing what its
state needs. Envelope text never raises the role's own order: routing reads the message without it.

`conventions_check.py` fails a suba with no `contract.json`, a contract with an open object, a
pattern with no example or a reference that resolves to nothing, a contract whose filled sample fails
or whose template fails beyond its placeholders, and a spine with no generated return block.
`python scripts/returns.py contracts` runs the same checks; `returns.py template <name>` prints a
template; `returns.py show [--unit <id>]` reads the log.
