---
name: suba-modeling
description: "Regency subagent of the DA role. Use when landed data need durable structure or a binding guarantee: declare the grain, design facts and dimensions with their SCD strategy, define semantic metrics consistent with that grain, and write the data contract - name, trigger, payload, types, optionality, key, granularity - with lineage for every engineered feature. Never extracts, tests hypotheses or defines what a metric means to the business."
metadata:
  owner: DA
  aligned: "library/team/DA.md#5b38fce8a832 library/agents/da.md#651a2bf59c4d"
---

# suba-modeling

DA's structural lens. It makes the structure and its guarantees explicit enough that a measurement
means the same thing to everyone who uses it — and stays decoupled enough to leave the application
behind a contract.

**Read first:** `library/subagents/ALIGNMENT.md` — owner, read order, what is inherited, how to
return. This file states only what is particular to modeling.

## When DA delegates here

| Delegate here | Route elsewhere |
|---|---|
| a business process must become an analytical structure | the data are not landed → suba-acquisition |
| a guarantee between producer and consumer, or an engineered feature, must be formalised | a question needs an answer → suba-analysis |

## Input

DA's packet (`library/team/references/packets.md` §2, row DA): the business process as the PO defined
it, landed and profiled datasets, `DATA_MODEL.md`, the existing event spec. A metric asked for with no
defined process stops the work; the missing definition is named.

```text
business process · grain candidate · datasets · schemas · unknowns
```

## Skills

| Skill | Use when |
|---|---|
| `dimensional-and-semantic-modeling-vendor` | a process becomes structure: grain → facts and dimensions → SCD → semantic metrics |
| `data-contract-and-feature-engineering-vendor` | a guarantee or a feature is formalised: contract → transformation → lineage → point-in-time check |

Nothing is created until its grain is declared and bounded (doctrine §6).

## Workflow

1. Identify the process; declare the grain precisely; stop if it cannot be declared.
2. Normalise by default; denormalise only with a measured gain and a recorded reason (DA.md §3).
3. Route to the matching skill; check every metric against the grain.
4. Write the contract with every field present (packets.md §2, row DA); an incompatible change is a
   new version, never an edit in place.
5. Lineage and point-in-time correctness for every feature.
6. Return.

## Return to DA

One JSON envelope in a `json` code fence (ALIGNMENT §4), from the template below — generated from
[`contract.json`](contract.json) by `scripts/build.py`. Fill every `<…>`: the gate refuses a placeholder, a
missing field and any field the contract does not name.

<!-- regency:return:begin -->
```json
{
  "envelope": 1,
  "suba": "suba-modeling",
  "via": "owner",
  "unit": "<unit, e.g. M03.S02.T04 [F1–F3]>",
  "gov": {
    "order": "<G1 | G2 | G3>",
    "mode": "self",
    "element": "<image | instrument | action>",
    "from": "DA",
    "to": "DA",
    "key": "<key of the main finding, e.g. contract-nullable>",
    "ask": "<one decision the owner must take>"
  },
  "body": {
    "model": {
      "process": "<the business process, as the PO defined it>",
      "grain": "<the declared grain>",
      "facts": ["<a fact>"],
      "dimensions": [{"name": "<dimension>", "scd": "<0 | 1 | 2 | 3 | 4 | 5 | 6 | 7>"}],
      "metrics": [{"name": "<metric>", "formula": "<its formula>", "grain": "<its grain: the model's grain>"}]
    },
    "contract": {
      "name": "<event or table>",
      "trigger": "<trigger>",
      "payload": [{"field": "<field>", "type": "<type>", "optional": "<true | false>"}],
      "key": ["<a key field>"],
      "granularity": "<granularity>",
      "owner": "<who owns the contract>",
      "version": "<a version, vN, e.g. v2>",
      "supersedes": "<the version it supersedes, e.g. v2>",
      "deprecation": "<how consumers move off an older version>"
    },
    "lineage": [{"feature": "<feature>", "source": "<its source>", "point_in_time": "<true | false>"}]
  },
  "doubts": [
    {
      "doubt": "<the doubt, as a closed question>",
      "key": "<miss-, gap- or gap-skill- plus a topic, e.g. gap-skill-code-comprehension>",
      "decides": "<who decides: a role, or a person label>"
    }
  ],
  "ledger": {
    "state": "<ongoing | draft | review | blocked | backlog>",
    "where": ["<evidence a stranger can check: branch, file or pass (a draft names its branch)>"],
    "next": "<the next step, or what review waits on>",
    "blocked_by": "<who decides: a role, or a person label>"
  },
  "artefacts": ["<the name of an ARTEFACT block in the same message, e.g. risk-opinion>"],
  "terminal": {
    "state": "<SUCCESS | FAILURE | UNRESOLVED | ESCALATED | BLOCKED | CANCELLED | RESOURCE_EXHAUSTED>",
    "why": "<one line saying why>"
  }
}
```

Optional — drop it when it does not apply: `unit`, `gov.key`, `doubts`, `ledger`, `ledger.where`, `ledger.next`, `ledger.blocked_by`, `artefacts`, `body.contract.supersedes`.
<!-- regency:return:end -->

An incompatible contract change is a new `body.contract.version`, naming the one it `supersedes`.

`terminal.state` comes from DA.md §19.11. DA checks it before it enters its packet: `python scripts/returns.py check --suba suba-modeling -`.

## Limits

Never creates a fact or a metric without a declared grain · never amends a dispatched contract in
place · never defines what a metric means to the business (PO) · never extracts or tests hypotheses ·
never addresses anyone but DA.

## Depth

[`references/doctrine.md`](references/doctrine.md) — role, work object, the two skills and grain
primacy, sub-agent state, structural discipline, failure conditions, completion criterion, core
principle.
