I'm signing the verifiability line for attempt 3, with residual risk: both of the PO's conditions are met. The version verdict is **correction**.

Notes on how I worked:
- **Nothing withheld reached me.** I read no commit messages. I did not open `dv-build-3-notes.yaml` or any other team-pass file my packet did not name. I read code only through `git diff` and file contents.
- **The repository is as I found it:** HEAD daba076 on plumbing, `git status` clean. Every run used `git archive` exports in my own directory (`/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3/`), with `TMPDIR` set there and `PYTHONDONTWRITEBYTECODE=1`. My own probes are in `/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3/probes/` (`mutate3.py`, `q3_norm.py`, `ast_cmp.py`).
- **I wore no suba lens.** ALIGNMENT §1 gives QA suba-recon, suba-tester and suba-validator. I did not read their SKILL.md files, so no envelope is attached. That is a deviation from my contract.

<<<ARTEFACT risk-opinion
# Risk opinion: analytics-lane attempt 3 (plumbing, 6dc5bdc..daba076), QA verify, 2026-11-18

**Cited norm:**
- `.changelog/inspection/PO-analytics-lane-02-accept.md`: the "D16" section and item 2 of "Before the unit leaves plumbing".
- The Regent's decision of 2026-11-18, as quoted in criteria-3.md.
- `library/elicitation.md` is agent-drafted and not ratified. I checked that it states what the code does, not that the limit is acceptable; the Regent ratifies.

## Scope and inputs
- **Diff:** `git diff 6dc5bdc daba076` is byte-identical to dv-build-3.diff (sha256 d3382645…). It touches 3 files, exactly the span and the `touched_paths`.
- **Base:** between e34f27c (the accepted commit) and 6dc5bdc only `.changelog/` and the ledger changed. So 6dc5bdc's code is the accepted code.
- **Surface diff:** empty. `library/registry.json`, `hooks/hooks.json`, `hooks/` and `library/hooks.md` are unchanged.
- **Rollback:** valid as named. daba076 has one parent and is already on origin/plumbing (local ref, not fetched), so revert it; do not reset. No store, schema or data is touched.
- **Change notes:** in shape, with one omission (D22).
- **DA oracle:** not needed. No number reaches a user in this attempt.

## Conditions
| Condition | Verdict | Evidence |
|---|---|---|
| **D16.1** Under M1, at least one self-test in elicit.py and one in hook-elicit.py go red | **met** | **On 6dc5bdc:** elicit 31/31 and hook-elicit 18/18, all green, so D16 is reproduced.<br>**On daba076:** elicit 31/32, MISS "D1. the older session rendered the question last: it owns it, not the newer one". hook-elicit 18/19, MISS "D1. the older session rendered the question last: the pop-up and its answer are its own". Nothing else goes red.<br>**Not flaky (by code reading):** `last_presented` ranks by `MAX(event_id)`, which is monotonic. Under M1 the rank falls to `updated_at` (one-second resolution) and then session id, and both pick the newer session. |
| **D16.2** On the corrected tree, every self-test passes | **met** for the unit | elicit 32/32 and hook-elicit 19/19. Every other check in doctor is OK.<br>The two inherited reds (hook-hazard 217/218; hook-refs with a FileNotFoundError traceback) are unchanged, and the PO's accept and criteria-3 item 4 put them outside the unit. **Read literally across the repository, this item is not met because of those two reds.** I took the unit's reading. |
| **D16.3** QA sees both results | **met** | This opinion, the two rows above. |
| **M2–M8 after the change** | unchanged | On both trees the same named tests go red as in attempt 2; only the totals rise by one. |
| **Norm §3:** the D17 limit, checked against probe 1c | **met** | **q123 1c:** A `{}`, B `rule=A confirmed`. Identical at both trees.<br>**My q3_norm 1c:** B's provenance says `task: task-b` ("under B's task"). `next` on A returns Q_RULE again, Pre allows it, and Post records it in A ("still to ask").<br>"Nothing crosses to the other" has been removed. The limit text uses the PO's words for the trigger.<br>One gap in what it states: D23. |
| **Norm §5:** session id as the fourth tie-break | **met** | Code: the rank is `(worded, last_presented, updated_at, session_id)` and the highest wins.<br>**Probe S4** (neither session rendered, equal `updated_at`): the answer goes to EL-0002.<br>Edge cases: D24. |
| **Norm §5:** the Post lookup without whitespace normalisation, checked against D18's steps | **met** | **Answer keyed single-spaced:** "D_AN-01-01: no answer"; params `{}`; `next` returns the question again.<br>**Question echoed single-spaced in the result text:** "no answers reached the hook … nothing was confirmed; the questions stay eligible"; params `{}`; `next` returns it again.<br>**Control (keyed verbatim):** accepted.<br>**Entry single-spaced by the agent and keyed as the entry:** accepted ("exactly as the entry carries it").<br>**Recognition and Pre:** they compare with `spoken()` (`str.split`), as the rescoped sentence says.<br>A related defect in the same lookup: D21. |
| **Norm §6:** closing the session is a playbook step | **met** | `triage --from-elicit` leaves the session `open` (probe). `skills/repository-analytics-triage/SKILL.md`, lines 49–50, carries `elicit.py reset --session EL-####`. |
| **No other change** ("any other change reopens QA's verify") | **holds** | Every changed line maps to D16 or to one of the four points. |
| **The Regent's decision of 2026-11-18** | **holds** | **Not corrected in code:** the code outside `selftest()` is AST-identical between the trees.<br>**Reads journalled before offsets stay out of the measure, counted apart:** reconstruction.py is unchanged, and the case "a read journalled without its offset is left out of the measure, and the report says so" is red under M6 at both trees. |

## Regression
- **No engine or hook behaviour change:**
  - Every top-level node outside `selftest()` is AST-identical: elicit.py 73/73, hook-elicit.py 21/21.
  - Both diff hunks sit inside `selftest()`.
  - q123_edges (paths masked) and q3_norm (timestamps masked) give identical output at both trees.
- **Inherited suite:**
  - doctor at daba076 is byte-identical to gate-dv3-local.txt.
  - doctor at 6dc5bdc is byte-identical to gate-dv2-local.txt.
  - The two runs differ only in the elicit (31→32) and hook-elicit (18→19) counts. Both show 2 FAIL and 30 WARN.
  - hook-hazard.py and hook-refs.py, run directly, give identical output at both trees once temp paths are masked. Their scripts are unchanged.

## Open defects

### MINOR
- **D21 (new; already present at 6dc5bdc; latent).** An empty `tool_input.answers` stops the Post lookup before it reaches `tool_response.answers`.
  - Steps: Post with `tool_input.answers = {}` and `tool_response.answers = {<question verbatim>: "Recycle"}`.
  - Observed: "no answers reached the hook…", and nothing is recorded.
  - Expected: §5 line 133 says answers are read from tool_input, "then" tool_response. The new §5 text says "as a key of `answers`".
  - It fails safe, but the Regent would be asked again. It depends on the live contract, which nobody has observed. Same class as D18.
- **Still open from earlier passes, not changed here:**
  - D17: now a stated limit.
  - D18: now stated in the norm.
  - D5–D11.

### TRIVIAL
- **D22.** The change notes' `new_tests` names only the elicit.py case. The hook-elicit.py case is missing. I saw both cases red under M1.
- **D23.** The §3 limit does not say what the asking agent is told.
  - In 1c, A's Post context line reads "rule = A accepted … `next --session EL-0002`".
  - If A asks the stale rendering again, it is denied as "already answered".
  - So "still to ask" is true in the store, but the asking agent is told the opposite. It behaves the same at 6dc5bdc.
- **D24.** Edge cases of the tie-breaks the norm now states. Found by code reading and a comparison only, not run end to end.
  - The id comparison is on strings, so from EL-10000 on "higher session id" fails: EL-9999 beats EL-10000.
  - `updated_at` is compared as a local-time ISO string, so "updated last" can invert across a DST change.
  - Both are reached only when the earlier tie-breaks tie.
- **Still open from earlier passes, not changed here:** D12–D15, D19, D20.

**Closed:** D16, to the PO's criterion.

## Coverage gaps
- **G1. The suite holds only one of the four ordering rules in §5 against removal.** I made five rank mutants. Each misroutes the Regent's answer in one probe scenario while both suites stay green, at both trees (5 runs on daba076, 2 on 6dc5bdc):

  | Mutant | What it breaks | Effect |
  |---|---|---|
  | X5 | drops "the rendering the entry carries" | in S1, base_option goes to B |
  | X2 | uses the first rendering instead of the last | in S2, the answer goes to B |
  | X1 | ranks "updated last" before "rendered last" | in S3, the answer goes to B |
  | X3 / X4 | inverts or drops the fourth tie-break | in S4, the answer goes to the lower id |

  - This is not new and is outside the PO's conditions. The exposure is the same as D16's: a later change can misroute a Regent decision with the suite green.
  - S1–S4 in `q3_norm.py` are candidate cases.
- **No suite case** for the D17 interleaving, D18 or D21. They are held only by QA's probes.

## What was not covered
- **The live AskUserQuestion contract:** when Pre fires, where answers arrive, how whitespace is shown, and whether `tool_input.answers` is present at Post. Only simulated events were used. D18, D21 and the §5 lookup sentence depend on it.
- **Real concurrent agents for D17.** 1c was run in sequence.
- **Other platforms:** Windows (the Regent's platform), any Python other than 3.13.18, and any SQLite other than this machine's.
- **The triage playbook run by a real agent.** I checked the close step by reading the playbook and probing `triage`.
- **A CI log for daba076.** I have only the local gate log and my own doctor runs on exports.
- **Repeated M1 runs.** I ran M1 once per tree; its determinism is argued from the code.
- **D24 end to end:** no store with EL-10000 and no run across a DST change.
- **Items outside this attempt:** D5–D15, the D17 session marker, D18's fix, D19 and D20 were not re-verified beyond "the code is identical outside `selftest()`".
- **The suba lenses** (suba-recon, suba-tester, suba-validator) were not worn.
- **Ratification of `library/elicitation.md`**, which is the Regent's.

## Version verdict
Version verdict: **correction** (against 6dc5bdc).
- The norm goes back to stating what the code does, and two test cases were added.
- No engine or hook behaviour, command, wiring or registry entry changed.
- The one consumer (triage) and its playbook are unchanged.
- It would be a break only for a reader who took §3's earlier promise, "nothing crosses to the other", as a guarantee. That text was never ratified, and the code never delivered it.

## Recommendation (for the PO, who decides)
- **Line signed with residual risk:** D21 (Minor), D22–D24 (Trivial), G1, and the items not covered above.
- **Both conditions for leaving plumbing are met.**
- **For the backlog:** G1's cases S1–S4, D21 next to D18, and D23 in the limit text before the Regent ratifies.

EVENT VALIDATION_PASSED analytics-lane QA PO-analytics-lane-02-accept#D16
EVENT VALIDATION_PASSED analytics-lane QA PO-analytics-lane-02-accept#before-plumbing-2
ARTEFACT>>>

Terminal state: **SUCCESS**. The verdict and risk opinion are issued, and the line is signed with residual risk. Both of the PO's conditions are met, with evidence at 6dc5bdc and daba076; there is no regression, and no open defect is above the PO's Minor tolerance.
