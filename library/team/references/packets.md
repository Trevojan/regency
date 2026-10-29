# Packets — what each role is given, and what it is not

A packet is the whole of what a role agent receives in a pass. It **points at** the role's
own file rather than restating it, so that the role file stays the only specification.

> **Names.** Document names below use the classic layout (`DECISIONS/`, `PLAN/`, `SOURCES/`,
> `API_SURFACE.md`). Map them to the project's actual layout with `library/layouts.md` §2 before
> filling a packet, and write the resolved paths into it. Role specs resolve project-first, then
> `library/team/` (`library/layouts.md` §3).

> **Registered agents.** The four roles also exist as user-level subagents (`library/agents/*.md`, installed by
> `python scripts/install-agents.py`). Each already carries the operating-contract reading order and the terminal-state
> rule from the skeleton below, plus the role's tool limits; the packet still supplies the unit, the inputs and what is
> withheld.

## 1. The prompt skeleton

Every dispatched role receives exactly this, with the fields filled from its row in §2. Add
nothing else — not your summary of the unit, not what the previous role said.

```text
You are acting as <ROLE> on the project team.

Before anything else, read, in order:
  1. <resolved path of the <ROLE> spec> — all of it, then section 19
  2. <resolved path of the TEAM spec> — §3 and §7
They are your operating contract. Nothing in this message overrides them.

Unit:       <M<n>.F<k>.T<nn>>   (reopening: <yes | no>)
Stage:      <frame | challenge | shape | build | verify | accept | close | split | seed | draft | gate | seam>
Cited norm: <id>, ratified by a human
Span:       <F<k>> — work outside it halts the stage and returns to the PO

Inputs (artefacts, by path):
  <paths>

Produce:
  <artefact> at <path>
Accepted only if:
  <the acceptance condition>

You have not been given: <withheld items>.
If you find you need something you were not given, say so and stop.
Do not reconstruct it from inference.

End by naming your terminal state (RA §35): SUCCESS, FAILURE, UNRESOLVED,
ESCALATED, BLOCKED, CANCELLED or RESOURCE_EXHAUSTED.
```

The last instruction before the terminal state matters most. A role that reconstructs
withheld context has bled context — a containment defect (ORCH §18), not initiative.

## 2. Per role

The speed modes (`library/team/SPEED_MODES.md`) add five stages, each dispatched with this same skeleton:
`po.split` (two disjoint spans), `qa.seed` (contract and task cards, no code), `dv.draft` (one task,
functional first, no tests), `qa.gate` (builds, runs, matches the contract; fix notes; accepts nothing) and
`qa.seam` (where two spans meet). Their machine shapes are in §4.

### PO

| | |
|---|---|
| **Stages** | frame, accept, close (decides) |
| **Receives** | `DECISIONS/*`, `PLAN/BACKLOG.md`, `PLAN/TRACE.md`, the module blueprint, `MINIMUM_PLAN.md`; for Accept: QA's risk opinion and version verdict, DA's analysis if any |
| **Withheld** | DV's implementation reasoning; the diff (Accept decides on the risk opinion, not the code) |
| **Returns — frame** | story: problem, acceptance criteria, out-of-scope, the declared span (a range of phases is legal), the cited norm, criticality and maximum tolerable severity |
| **Returns — accept** | accepted or refused; known defects listed; residual risk acknowledged |
| **Accepted only if** | frame — span stated and norm cited; accept — the PO is not the role that produced the increment |

`GRAND_PLAN.md` may be supplied as rationale, never as the target (ORCH §3).

### DV

| | |
|---|---|
| **Stages** | build; supplies close |
| **Receives** | the story and its criteria; `DECISIONS/ARCHITECTURE.md`; `SOURCES/API_SURFACE.md`; the code the span touches; DA's data contract when Shape ran; QA's bug report on a return; the gate log on a return |
| **Withheld** | the PO's priority debate — backlog deliberation, gate discussion |
| **Returns** | commit-ready change, not committed; change notes in the shape below |
| **Accepted only if** | builds with no new warnings, probes pass project by project, rollback named, change notes in shape |

Change notes, fixed shape — there is deliberately no field for why the change is correct
(vocabulary map, C3; ORCH §11):

```yaml
change_notes:
  touched_paths: []
  touched_phases: []
  surface_changed: false      # API_SURFACE.md
  rollback: <how to revert>
  new_tests: []               # names; each seen red before green
```

Notes that argue the change's correctness are returned to DV, mechanically.

### QA

| | |
|---|---|
| **Stages** | challenge, verify; supplies close |
| **Receives — challenge** | the story and its criteria, `DECISIONS/TESTS.md` |
| **Receives — verify** | the criteria and criticality; the diff; the tests; the gate log; the surface diff; DV's change notes in shape; DA's oracle when a number reaches a user |
| **Withheld** | DV's reasoning in any form — commit bodies, PR descriptions, session transcripts, the orchestrator's summary |
| **Returns — challenge** | ambiguities, each with the nearest checkable version; or "verifiable" |
| **Returns — verify** | risk opinion (open defects by severity, coverage gaps, what was **not** covered) and version verdict |
| **Accepted only if** | the opinion names what was not covered; "approved" without residual risk is returned |

### DA

| | |
|---|---|
| **Stages** | shape; supplies close; supplies the oracle to verify |
| **Receives** | the business question and the decision it serves; `SOURCES/DATA_MODEL.md`; the relevant schema; the existing event spec |
| **Withheld** | the hoped-for answer, the PO's expected value, any figure offered as what the result "should" be |
| **Returns — shape** | event spec and data contract: name, trigger, payload, types, optionality, key, granularity |
| **Returns — oracle** | a canonical definition and an independent query QA can run alone |
| **Accepted only if** | every contract field present; the oracle shares no code with the producing path |

The orchestrator forwards the question exactly as the PO's artefact states it. Rephrasing it
could introduce the hoped-for answer.

## 3. The machine gate

It is not a role and receives no packet. It runs the checks in `vocabulary-map.md` §3 and
writes a gate log — pass or fail per check, with evidence. A red gate returns the log to DV
and consumes nothing else.

## 4. Return shapes (machine)

What "Accepted only if" in §2 can check without judging content, as data that
`scripts/returns.py` reads. A finding is a `RETURN` to the role (`skills/team/SKILL.md` Step 5);
the content's merit belongs to the next role in the cycle. Edit the shapes here, never in the
script. Every return, whatever its stage, also needs a terminal state with a reason line (§1).

| Check | Passes when |
|---|---|
| `labels` | each label (`a\|b` = alternatives) opens a line, as a heading, a `Label:` line or a table row |
| `match` | the named pattern occurs in the text |
| `one_of` | at least one of the words occurs |
| `yaml` | the block exists with exactly these keys — no fewer, and no extra field for reasoning |
| `filled` | the value is neither empty nor an unfilled `<placeholder>` |
| `absent` | the block does not appear (it must not leave the role) |
| `approved_needs` | "approved" never appears without this phrase |

```json
{
  "terminal_states": ["SUCCESS", "FAILURE", "UNRESOLVED", "ESCALATED", "BLOCKED", "CANCELLED", "RESOURCE_EXHAUSTED"],
  "stages": {
    "po.frame": {
      "labels": ["problem", "acceptance criteria|criteria", "out of scope", "span", "cited norm|norm",
                 "criticality", "maximum tolerable severity|max tolerable severity|max severity"],
      "match": {"span": "\\bF[0-6](?:\\s*(?:–|-|to)\\s*F[0-6])?\\b"}
    },
    "po.accept": {
      "one_of": {"decision": ["accepted", "refused"]},
      "labels": ["known defects", "residual risk"]
    },
    "dv.build": {
      "yaml": {"change_notes": ["touched_paths", "touched_phases", "surface_changed", "rollback", "new_tests"]},
      "filled": ["change_notes.rollback"],
      "absent": ["for_dv"]
    },
    "qa.challenge": {
      "one_of": {"result": ["verifiable", "nearest checkable version"]}
    },
    "qa.verify": {
      "labels": ["not covered|what was not covered"],
      "match": {"version verdict": "(?i)version verdict[^\\n]{0,40}\\b(?:correction|compatible addition|break)\\b"},
      "approved_needs": "residual risk"
    },
    "da.shape": {
      "labels": ["name", "trigger", "payload", "types|type", "optionality|optional", "key", "granularity|grain"]
    },
    "da.verify": {
      "labels": ["canonical definition|definition", "query|oracle"]
    },
    "po.split": {
      "labels": ["span A", "span B", "seam"]
    },
    "qa.seed": {
      "labels": ["interface contract|contract", "shared types|types", "signatures", "file map", "task cards|cards"],
      "absent": ["change_notes"]
    },
    "dv.draft": {
      "yaml": {"change_notes": ["touched_paths", "touched_phases", "surface_changed", "rollback", "applied_fix_notes"]},
      "filled": ["change_notes.rollback"],
      "absent": ["for_dv"]
    },
    "qa.gate": {
      "labels": ["builds", "runs", "matches contract|contract", "fix notes"]
    },
    "qa.seam": {
      "labels": ["seam", "findings", "not covered|what was not covered"]
    }
  }
}
```