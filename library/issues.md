# Issues — the tracker against the project's records

A repository's issues are a queue kept outside the repository. `/regency:issues` reconciles it with the queues
kept inside: the work ledger and the project's notes. Engine: `scripts/issues.py`. Playbook: `skills/issues/SKILL.md`.

## 1. The verbs

Three groups, nine verbs, one function each.

| Group | Verb | Answers | Changes |
|---|---|---|---|
| verdict | `adopt` | is this work here? yes, as a ledger item | the project's records |
| verdict | `flatten` | is this work here? only a note | the project's records |
| verdict | `ignore` | is this work here? no | the project's records |
| tracker | `close` | the issue ends | the tracker |
| tracker | `publish` | a record becomes an issue | the tracker |
| read | `status` | where does it stand? | nothing |
| status | `question` | what is missing to decide? one comment | the tracker |
| status | `revise` | what does the issue say now? a new description | the tracker |
| status | `measure` | what would it change? | nothing |

`check` runs them together: every issue against its verdict.

## 2. The verdict record

`<guidelines>/.shortcuts/.virtual/issues.json`, beside the work ledger (`library/layouts.md` §2). One row per issue;
a new verdict replaces the old one.

```json
{"schema": 1, "updated": "2026-11-11",
  "issues": [
    {"n": 2, "verdict": "adopt", "on": "2026-11-05", "why": "a pass must show where its time went", "to": "slow-pass"},
    {"n": 8, "verdict": "flatten", "on": "2026-11-09", "why": "housekeeping", "to": ".changelog/ROADMAP.md#candidates"},
    {"n": 11, "verdict": "ignore", "on": "2026-11-11", "why": "out of this project's scope"}
  ]}
```

- `adopt` names a ledger item that exists; the ledger holds the work, the row only points.
- `flatten` names the file (and anchor) of the note that holds the issue in one line.
- `ignore` carries its reason and nothing else.
- A verdict is the Regent's decision: the row is written from the Regent's answer, never from an agent's reading.

## 3. What `check` reports

| Level | Means | Settled by | Fails |
|---|---|---|---|
| `UNTRIAGED` | an open issue with no verdict | a verdict | yes |
| `BROKEN` | adopted as a ledger item the ledger no longer holds | restore the item, or a new verdict | yes |
| `ORPHAN` | a verdict for an issue the tracker does not have | remove the row | yes |
| `CLOSED` | adopted, closed on the tracker, the ledger item still standing | close the item, or reopen the issue | no |
| `OPEN` | flattened or ignored, still open | `close`, or leave it on purpose | no |
| `MOVED` | the issue changed after its verdict | read it again; record the verdict anew | no |

A closed issue with no verdict is quiet.

## 4. Tracker writes

`close`, `publish`, `question` and `revise` reach outside the machine and are read by other people. Each prints
its plan (the act and the exact text) and changes nothing; `--yes` runs it, passed only after the Regent's yes
(conventions §5). They never run headless, and never in a repository the Regent does not own (conventions §6).

A flattened issue is finished on the tracker by `revise --fold` (its description kept under one line that says where
the note lives) and `close --reason not-planned`.

## 5. Measuring

`measure <n>` prepares the slice (the paths the issue cites that exist here, those that do not, its checklist, its
verdict); the measurement itself is `/regency:measure-changes` in `issue` mode, with the same output block. Nothing is
applied and nothing is posted: a measurement reaches the issue as a `question`.
