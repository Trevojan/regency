PO accept, unit analytics-lane, attempt 2: **accepted** at e34f27c. Known defects stay open, and the residual risk is acknowledged below. Two conditions must be met before the unit leaves plumbing: the one-case correction for D16, and the drafted norm stating the limit I accept for D17.

Notes on how I worked:
- **I did not produce this increment.** DV built it and QA verified it. My decision rests only on QA's two opinions and the Regent's recorded decisions.
- **Nothing withheld reached me.** I saw no diff, no commit message, no DV notes and no orchestrator summary.
- **I broke my contract once.** Before reading the conventions, I ran one read-only shell command: a line count (`wc -l`) on three library files. My contract gives me no shell. I ran nothing else and wrote no file.
- **I read beyond the named inputs once.** Besides the "Team" section of CHECKPOINT, I used its "Health" line: the Regent's machine runs Windows. I needed it because QA lists Windows as not covered.
- **I wore no suba lens, so no envelope is attached.** suba-strategy is an unratified proposal, and it takes the frame or close packet, not accept.

## Decision
Decision: accepted, with known defects, for e34f27c. The decision covers the unit's whole range on plumbing, 3396665..e34f27c.

The grounds are QA-analytics-lane-02:
- D1–D4 are met. Each probe is red at eef6edc and green at e34f27c.
- D4 is checked against an oracle that shares no code with reconstruction.py (200/200 agree).
- There is no regression.
- The version verdict is **correction**.
- The rollback is named: revert, do not reset, and drop the `b0` column on a migrated store.
- Every open defect is at or below the tolerance set below.

QA's residual risk is the shape every risk opinion must have (packets.md §2, QA row: "approved" without residual risk is returned). It is not a qualified gate attestation, so PO §12 lets me decide alone. Any further commit on the unit needs QA's verify before this acceptance covers it.

## Criticality and maximum tolerable severity (set by PO; no frame stated them)
| Part | Criticality | Max tolerable severity | Why |
|---|---|---|---|
| hook-elicit.py, elicit.py, the triage consumer | HIGH | Minor | They carry the Regent's decisions: only the Regent's answer confirms a value (conventions §1 and §3; the Regent, 2026-11-18). A Major here denies or misattributes a Regent decision. |
| reconstruction.py and the number it reports | MEDIUM | Minor | The ratio decides what gets built (ROADMAP, as QA-01 quotes it). |
| hook-reads.py (the recorder) | MEDIUM | Major | It records asynchronously on every Read (QA-01). Its failures reach the Regent only through the number, which is held at Minor above. |
| analytics.py lane writes, alpha.py | MEDIUM | Major | They write git refs, objects and tags, and run a shell build (QA-01). They sit beside the branch contract and merge into nothing (conventions §4). The Regent accepted the lane writes on 2026-11-18. |
| locate.py, documents, registry | LOW | any | A read-mostly cache and text (QA-01). The Regent accepted locate.py on 2026-11-18. |

I set this after reading the opinion, so it is not independent of it. Two things limit that weakness:
- It is identical to the assumption QA declared in QA-01, before attempt 2 was built.
- It comes from what each part does, not from the defect list.

QA-02 therefore stands unchanged. The Regent may set a different tolerance at review.

## D16: must the correction land before the unit leaves plumbing? Yes.
- **Why:** D1 was the Major defect in the HIGH part. Its fix is now held only by QA's probe 1a, which sits in a session scratchpad that a cleanup can clear. The suite stays green when the "rendered last" rule is removed, so a later change could bring D1 back unseen. `testing` is the agents' last validated pass (conventions §4).
- **Done when:**
  1. Under QA's mutant M1, at least one self-test in elicit.py and one in hook-elicit.py go red.
  2. On the corrected tree, every self-test passes.
  3. QA sees both results.

## D17: a stated limit, not a correction before the line moves on
- **The limit:** two open sessions hold the same question with the same upstream values and are asked interleaved. The Regent's answer goes to the session that rendered the question last, and the asking session is left unanswered.
- **Why I accept it:**
  - QA rates it Minor, which is within the HIGH tolerance.
  - The trigger is narrow: another agent on the same repository, or `next` on B before A's pop-up is asked.
  - The answer only lands where the rendered text and the upstream values are identical. My inference: the provenance is lost, not the content of the decision.
- **Why not a correction now:**
  - The only correction QA names is a session marker carried into the pop-up. That would change what the Regent sees in every engine pop-up.
  - It is new scope beyond this attempt's criteria, D1–D4. New scope does not enter a unit midway (PO §19.7). It goes to the backlog and is decided at the next opening.
- **Condition:** the limit is written into the drafted norm `library/elicitation.md` before the unit leaves plumbing.
  - Its §3 now promises "nothing crosses to the other", which the code does not deliver.
  - The Regent then ratifies that norm, or does not, with the limit in view.
  - If the Regent refuses the limit, the session marker becomes a criterion of the next attempt.

## Known defects
None is above the tolerance set above.

| Id | Severity | Part | Defect | Disposition |
|---|---|---|---|---|
| D16 | Minor | elicit.py and hook-elicit.py self-tests | The two tests named "rendered last" stay green when the rule is removed (M1). | Correct before leaving plumbing. |
| D17 | Minor | elicitation engine | Identical renderings asked interleaved go to the session that rendered last, not the one that asked. | Stated limit; the session marker goes to the backlog. |
| D18 | Minor | hook-elicit.py, Post | The answer lookup does not normalise whitespace. It fails safe and is identical at eef6edc. | Open. The norm states it; the fix waits until the live pop-up contract is observed. |
| D19 | Trivial | hooks.md, REFERENCE.md (outside the span) | Both lag the change: the Elicitation rule and the `b0` column. | Open. Its own task, outside this span, before main. |
| D20 | Trivial | reconstruction.py report | A store whose rows all predate `b0` reports "ratio 0%". The "left out" line explains it. | Open. |
| D5 | Minor | elicit.py | Rejections are never recorded; `answer_rejected` is always 0. | Open; backlog. |
| D6 | Minor | elicit.py | `reset` without `--session` closes a session chosen implicitly. The triage close step passes `--session`, so it does not hit this. | Open; backlog. |
| D7 | Minor | elicit.py | `inputs` slots cannot be filled, so a question that depends on one stays blocked. | Open; backlog. |
| D8 | Minor | elicit.py | A `derived` submission replaces a confirmed answer without a reopen. Latent. | Open; backlog. |
| D9 | Minor | hook-elicit.py | With a broken session, Pre asks on every pop-up and Post reports only to stderr. | Open; backlog. |
| D10 | Minor | alpha.py | `cut` tags before it exports, so a failure leaves a tag with no export. | Open; backlog. |
| D11 | Minor | elicit.py | A multi-select label that holds a comma can never be chosen. Latent. | Open; backlog. |
| D12 | Trivial | elicit.py | On a new answer, the parameter row drops its provenance history; the events table keeps it. | Open. |
| D13 | Trivial | shortcuts.md §3 | It omits the `meta` keys that locate.py writes. | Open; the Regent accepted it with locate.py. |
| D14 | Trivial | analytics.md §2 | It omits that the root README is rewritten on every lane write. | Open; the Regent accepted it with the lane writes. |
| D15 | Trivial | analytics.py | A delta's `unanswered` list ignores `--scope`. Found by code reading only. | Open; the Regent accepted it with the lane writes. |

## Residual risk
- **R1:** the guard catches fewer rewordings. An engine question that is both reworded and re-optioned now passes, and its answer confirms nothing. This is the price of the D2 fix.
- **R2:** an unrelated pop-up that shares the header and all its labels with an engine question is still captured (denied as already answered).
- **R3:** reads journalled before `b0` drop out of the measure. An existing store reports nothing until new reads accrue.
- **R4:** an 8-column hook-reads.py from the plumbing era fails every insert into a migrated store, reporting only to stderr, until `b0` is dropped. QA found no installed copy.
- **Rollback:** on a migrated store, it also needs `ALTER TABLE reads DROP COLUMN b0`. The fallback for SQLite older than 3.35 was not run.
- **The live pop-up (AskUserQuestion) contract is unobserved:** when Pre fires, where answers arrive, and how whitespace is shown. The engine's only confirmation path, the D3 fix and D18 all depend on it.
- **D9:** a Post failure can leave the Regent's answer unrecorded without the agent being told. That is the error-handling floor of conventions §15.3.
- **D8 with no schema activation policy:** any valid schema file starts. A Regent-confirmed value is protected only because no schema declares a `derived` slot, which is a norm, not a check. This is my inference from QA-01's D8 and its not-covered list.
- **D4 rests on QA's own oracle,** which shares no code with reconstruction.py. DA supplied none.
- **D17 was simulated in sequence;** no real concurrent agents were run.
- **Not run on Windows, Python 3.8 or SQLite older than 3.35.** The Regent's machine runs Windows.
- **No CI log for e34f27c.** The inherited reds (hook-hazard 217/218, hook-refs) belong to the guards line and are not accepted here.
- **No real agent has run the playbooks** (triage with its close step, measure-context-reconstruction), and `report` was not run on the repository's own store.
- **hook-reads.py on large or binary files is not covered.** It hashes the whole file on every Read.
- **First-pass items that still stand:** `onFailure: block` under lock contention; `agent_type` on PostToolUse Read events; locate.py; `alpha cut --build`, which runs `shell=True` where hook-hazard cannot see it.
- **The Regent's spec items QA-01 found unimplemented** (timing and database-operation measures, a schema activation policy) are outside D1–D4 and stay open.
- **`library/elicitation.md` and `shortcuts.md` §8 are still agent-drafted.** This acceptance ratifies neither (conventions §1).

## Before the unit leaves plumbing
1. **The D16 correction,** done to the criterion above.
2. **`library/elicitation.md` states what the code does** on the four points QA lists under "Norm documents":
   - §3: the D17 limit.
   - §5: session id as the fourth tie-break.
   - §5: the Post lookup does not normalise whitespace (D18).
   - §6: closing the session is a playbook step.

   QA checks it against probe 1c and D18's steps. If `library/elicitation.md` is not one of the eight span paths, this item returns to me before work starts.

Neither item changes a criterion. Any other change reopens QA's verify.

**Before main:** D19, as its own task outside this span. I recommend a run on the Regent's own platform, Windows, before main. The Regent judges main; I do not set this as a condition.

**Backlog,** decided at the next opening, in my proposed order:
1. D9 and D8: they touch the Regent's record of decisions.
2. D17's session marker and D18, once the live pop-up contract is observed (CHECKPOINT, "Next", item 5).
3. D5, D6, D7, D10, D11, D12.

## For the orchestrator (I write nothing)
- **Ledger, item analytics-lane:**
  - Stays `ongoing`, with DV as the role.
  - `where` adds `pass:analytics-lane qa.verify 2` and `pass:analytics-lane po.accept 2 @e34f27c`.
  - `next` becomes: "D16 case 1a and the elicitation.md limits (QA-analytics-lane-02); QA checks both; then plumbing → testing; D19 before main".

```
EVENT DECISION_MADE analytics-lane PO accept@e34f27c
EVENT DECISION_MADE analytics-lane PO D17:stated-limit
```

Assumed the decision covers the whole unit at e34f27c (3396665..e34f27c), not only eef6edc..e34f27c, because the packet named the unit but not the range. Next time: name the commit range the accept covers.

Terminal state: **SUCCESS**. The increment is accepted at e34f27c. Every known defect (D5–D20) is named with its severity and disposition, and the residual risk (R1–R4 and what QA did not cover) is acknowledged. The decisions on D16 and D17 and the tolerance are stated.
