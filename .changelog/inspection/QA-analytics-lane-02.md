QA verify, unit analytics-lane, attempt 2: I sign the verifiability line with residual risk. All four criteria D1–D4 are met. Each criterion probe fails at eef6edc and passes at e34f27c, and my own probes (independent of DV's self-tests) confirm the fixes. I found no regression against the inherited suite or against D5–D15. Three Minor defects and two Trivial ones are open. The most important is D16: two of DV's D1 self-tests stay green when the "rendered last" rule they name is removed. The version verdict is **correction**.

Notes on how I worked:
- **HEAD moved during the pass.** The coordinator reported it. I checked it myself without reading the commit message: e34f27c is one commit on eef6edc, its diff hashes the same as dv-build-2.diff (e7a68a0f…), it touches the same 8 files, and the working tree is clean. Every result below is for e34f27c. My first attempt at an eef6edc export ran `git archive HEAD` after HEAD had moved, so it was really e34f27c; I threw it away and exported eef6edc by id. The origin/plumbing ref (not fetched) also points at e34f27c, so the unverified draft is already on the remote.
- **Nothing withheld reached me.** I did not open dv-build-2-notes.yaml, qa-verify-1.md or the other files in team-pass/ that my packet did not name, nor the scratchpad/head/ export. I read no commit messages.
- **The repository is as I found it.** I made no writes: no stash, the ignored `scripts/__pycache__/` is unchanged, and every probe ran with `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR` in my own directory. Read-only `git status` may have refreshed the stat cache in .git/index; no content changed.
- **No suba lens was worn**, so no envelopes are attached.

<<<ARTEFACT risk-opinion
# Risk opinion: analytics-lane attempt 2 (plumbing, eef6edc..e34f27c), QA verify, 2026-11-18

Cited norm:
- `.changelog/inspection/QA-analytics-lane-01.md`, D1–D4.
- The Regent's definition of "carried", ratified 2026-11-18: line-level.
- `library/elicitation.md` and `library/shortcuts.md` §8 are agent-drafted and not ratified. I treated them as the implementation's claims.

## Scope and inputs
- **Span:** `git diff --name-only eef6edc e34f27c` equals the 8 `touched_paths` exactly.
- **Surface diff:** empty. `library/registry.json` and `hooks/hooks.json` are unchanged.
- **Rollback:** valid as named. e34f27c is a single commit on eef6edc, so `git revert e34f27c` works. It is already on origin/plumbing, so revert it; do not reset.
  - The second rollback step is also needed. On a store this change migrated, the eef6edc hook-reads.py fails with "table reads has 9 columns but 8 values were supplied". After `ALTER TABLE reads DROP COLUMN b0` it records again (checked on SQLite 3.53.1).
- **Change notes:** in the fixed shape.
- **DA oracle:** none was supplied. For D4 I used my own oracle, which shares no code with reconstruction.py (below).
- **My probes:** in `/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa2/probes/`. They are `q123_edges.py`, `q2f_q3c.py`, `q4_oracle.py`, `mutate.py`, `mutate0.py`, `q_store.py` and `q_perf.py`; each takes the scripts directory as its argument.
- **Exports:** eef6edc is in `.../qa2/base` and e34f27c in `.../qa2/headx`.

## Criticality assumed
The Regent stated no tolerance. I kept the first pass's assumption (RA §27):

| Part | Criticality | Max tolerable severity |
|---|---|---|
| hook-elicit.py, elicit.py, the triage consumer | HIGH | Minor |
| hook-reads.py, reconstruction.py | MEDIUM | Minor for the number, Major otherwise |

If the PO states a different tolerance, this opinion may change.

## Criteria
| Criterion | Verdict | Evidence |
|---|---|---|
| **D1** cross-session leakage | **met** (named test partial: D16; residual: D17) | **p1:** at eef6edc, deny, and the answer overwrote the old session (rev 2). At e34f27c, allowed: new session `rule=A confirmed`, old session keeps `B`.<br>**p2:** at eef6edc the old session took B. At e34f27c the new session has `B confirmed` and the old session `{}`.<br>**p13**, completed by me (the probe stops before Trash's reason question): at eef6edc day 2 is denied. At e34f27c both day-2 rounds are allowed, `triage --from-elicit` gives `AN-01-01=trashed` with `undecided []`, and day-1 params are untouched.<br>**1a:** the older-id session renders last and owns the pop-up and its answer.<br>**1b:** renderings that differ by an upstream value go to the right session.<br>**1e:** `repeat_denied` is counted in the owning session only. |
| **D2** capture by header | **met** (residual: R1, R2) | **p10:** deny at eef6edc, allowed at e34f27c.<br>**2a:** an unrelated pop-up with header `owner` (case differs) passes.<br>**2h:** an unrelated Post records nothing; `owner` stays `RGN confirmed`.<br>**The guard still catches single deviations:** a reworded question with the same labels is denied (2d), the verbatim question with changed labels is denied (2e), and a "(Recommended)" label is still recognised (2g). |
| **D3** whitespace in prompts | **met** (residual: D18) | **p11** and **p12:** deny at eef6edc, allowed at e34f27c.<br>**3a, end to end** (title with a double space and a tab): Pre on the verbatim question is allowed, and so is Pre on the agent's single-spaced version. Post records it, and `triage --from-elicit` gives `AN-01-01=recycled`. |
| **D4** carried, line-level | **met** | **p6:** at eef6edc carried 500/500, ratio 1.0. At e34f27c 0, ratio 0.0, which is the hand oracle.<br>**`q4_oracle.py`, 5 seeds × 40 random rounds:** 200/200 agree with an independent (path, sha, line) oracle. The rounds cover multibyte UTF-8, CRLF, a file with no final newline, reads past EOF, and files changed between sessions.<br>**The same oracle against eef6edc:** 7/40 agree, so it discriminates.<br>The METHOD line, the docstring, shortcuts.md §8 and the skill all state the line-level definition. |

## Named new tests (red first, by mutation in copies of e34f27c)
- **M0 (`locate_question` put back to its eef6edc body):** every new D1, D2 and elicit-level D3 test goes red.
- **8 of 10 named tests** fail when the behaviour they name is removed (M2–M8):
  - hook D2 red under M2;
  - elicit D3 red under M3, hook D3 red under M4;
  - reconstruction D4 red under M5;
  - left-out red under M6;
  - b0 red under M7;
  - old-store migration red under M7 and M8.
- **2 of 10 stay green when the rule they name is removed.** These are "the one that rendered it last owns it" (elicit) and "the answer goes to the session that rendered the question last" (hook-elicit). See D16.

## Regression
- **doctor, eef6edc against e34f27c:** the same 2 FAIL outside the unit (hook-hazard 217/218; hook-refs "(no output)") and the same 30 WARN.
  - The only differences are the counts of the touched self-tests: elicit 29→31, hook-elicit 14→18, reconstruction 7→9, hook-reads 6→8.
  - My run is byte-identical to gate-dv2-local.txt.
- **Self-tests:** elicit 31/31, hook-elicit 18/18, reconstruction 9/9, hook-reads 8/8, analytics 22/22.
- **D5–D15 are neither fixed nor made worse:**
  - p3, p4 (a–d), p5, p7 and p9 give identical output at both trees (temp paths, times and hashes masked).
  - p8's invariants hold at both trees: 0 errors, revisions strictly +1, no stale-fingerprint confirmation. Its last status line varies with process scheduling at both; eef6edc showed "invalidated" in 3 of 12 runs.
  - The files behind D10 and D12–D15 are untouched (alpha.py; accept(); locate.py and shortcuts.md §3; analytics.md and analytics.py).
  - The triage playbook's new close step uses the explicit `reset --session`, which closes only the named session (checked). D6 is not reached by it.
- **Exploratory:**
  - Pre with 500 open sessions takes 0.09 s (eef6edc: 0.12 s) against a 10 s budget.
  - 3 runs of 12 parallel first writes on a pre-b0 store: 12/12 rows each time, column added, no failure.
  - A store whose rows all predate b0 prints a report and does not crash.

## Open defects

### MINOR

**D16. Two D1 tests do not hold the "rendered last" rule they name.**
- **Steps:**
  1. In a copy of e34f27c, set the rank in `elicit.locate_question` to `(worded, updated_at, session_id)` (mutate.py M1).
  2. Run `elicit.py --selftest` and `hook-elicit.py --selftest`.
- **Expected:** the two tests named "rendered last" fail.
- **Observed:** 31/31 and 18/18, all green.
  - On the same mutant, probe 1a sends the Regent's answer to EL-0002 instead of EL-0001, the session that rendered last.
  - Both tests render in the higher-id session, so the session-id tie-break satisfies them.
- **They are real against the original defect** (red under M0), but not against the rule.
- **Risk:** a later change can drop the ranking with the suite still green, and D1 comes back for the ordering where the older session renders last.
- **Correction:** add case 1a, where the older-id session renders last and owns the pop-up and its answer.

**D17. Identical renderings asked in an interleaved order go to the session that rendered last, not the one that asked (probe 1c).**
- **Steps:**
  1. Open two sessions of the example schema, A = EL-0001 and B = EL-0002.
  2. Run `next` on A, then Pre on A's rendering (allowed).
  3. Run `next` on B; the rendering is identical.
  4. Post the Regent's answer "A".
- **Expected** (spec "Prevent cross-session state leakage"; elicitation.md §3 "nothing crosses to the other"): the answer is recorded in A.
- **Observed:** A `{}`, B `rule=A confirmed`.
- **This follows the drafted norm (§5).** The pop-up carries no session identity, so two identical renderings cannot be told apart.
- **Trigger:** two open sessions holding the same question with the same upstream values, interleaved. That means another agent on the same repository, or `next` on B before A's pop-up is asked.
- **Same class as D1, narrower trigger.** PO to decide: accept it as a stated limit, or carry a session marker into the pop-up.

**D18. The answer lookup in Post does not normalise whitespace.** This existed at eef6edc and depends on the surface.
- **Steps:**
  1. Record a finding titled with a double space, then run `next`.
  2. Post with the answer keyed by, or echoed in the result text with, the single-spaced question.
- **Expected:** elicitation.md §5 says "compared as the pop-up shows it … on both sides".
- **Observed:** "no answers reached the hook … nothing was confirmed" (result text) and "D_AN-01-01: no answer" (answers keyed single-spaced).
- **Fail-safe, and identical at eef6edc.** Whether any surface echoes normalised wording is unknown, because the live contract has not been observed.

### TRIVIAL
- **D19. Documents outside the span lag the change.**
  - library/hooks.md §Elicitation still says "nothing is read for it" and does not carry the header + wording/labels rule.
  - library/REFERENCE.md's hook-reads row omits b0.
- **D20. The first report on an existing store reads as "no reconstruction".** When every row predates b0, it prints "0 session(s) … ratio 0%". The "left out: N" line that follows explains it.

## Residual risk, stated in the drafted norm (not defects)
- **R1. The guard catches fewer rewordings than before.** An engine question that is both reworded and re-optioned now passes; eef6edc denied it (probe 2f). Its answer confirms nothing (2i). This is the price of the D2 fix.
- **R2. An unrelated pop-up can still be captured.** It is captured when it shares the header and all its labels are labels of the engine question (2b: header `Rule`, labels A/B, denied as already answered).
- **R3. Older reads leave the measure.** Rows journalled before b0 are left out, so existing stores report nothing until new reads accrue.
- **R4. Plumbing-era copies of hook-reads fail on a migrated store.** The 8-column hook-reads (eef6edc and earlier, plumbing only) fails every insert into a store with b0, reporting to stderr only, until the column is dropped. I found no installed copy on this machine.

## Norm documents (criterion 5)
The code does what they state, except where they state more:
- **elicitation.md §3**, "nothing crosses to the other": see D17.
- **elicitation.md §5**, "on both sides": not on the Post answer lookup (D18). "As the pop-up shows it" is a claim about the live UI that nobody has observed.
- **elicitation.md §5** leaves a fourth tie-break, session id, unstated.
- **elicitation.md §6**, "the session is closed … once no finding in it is undecided": stated as a property, but it is a playbook step the agent performs. `triage --from-elicit` leaves the session open.
- **shortcuts.md §8:** every statement checked (exact bytes, the left-out line, the column added on next write, the `rebuilt` counting).
  - "Exact" holds within the hook's line model: LF lines, raw bytes.
  - That model does not include the Read tool's own truncation of long lines. This is not new with this change.

## Coverage gaps
- No suite case for the older-id session rendering last (D16).
- No case for interleaved Pre and Post across sessions (D17).
- No case for the Post answer lookup with whitespace (D18).

## What was NOT covered
- **The live AskUserQuestion contract:** when Pre fires, where answers arrive, and how whitespace is shown or echoed. D3 and D18 depend on it.
- **An oracle from DA** for D4. I used my own: it records reads through hook-reads.py and reads file bytes itself, sharing no code with reconstruction.py.
- **Real concurrent agents for D17.** I simulated it sequentially.
- **Python 3.8, Windows, and SQLite older than 3.35.** On old SQLite the rollback's fallback (drop the reads table) was not run.
- **`report` on the repository's own store.** I did not run it because opening the store writes a `meta` row.
- **The playbooks run by a real agent:** triage with its close step, and measure-context-reconstruction.
- **A CI log for e34f27c.** None was given.
- **hook-reads on large or binary files.**
- **First-pass items that still stand:** `onFailure: block` under lock contention, `agent_type` on PostToolUse Read events, locate.py, and `alpha cut --build`.

## Version verdict
**Correction** (against eef6edc).
- D1–D3 bring the hook back to what hooks.md and the spec already promised.
- D4 brings the number back to its advertised meaning, now the Regent's ratified line-level definition.
- No command, hook wiring or registry entry changed.
- The b0 column is additive and is added in place.
- None of the four scripts exists on main or testing, so there is no released consumer.
- **It would be a break for:** the plumbing-era hook copies (R4), anyone relying on the wider guard (R1), and the measure's legacy rows (R3).

## Recommendation (for the PO, who decides)
- **Line signed, with residual risk:** D16, D17 and D18 (Minor), D19 and D20 (Trivial), and R1–R4.
- Accepting this build means accepting those defects open (§12).
- **Before merging to testing:** a one-case correction for D16 (probe 1a).
- **For the PO:** decide on D17, either as a stated limit or a session marker carried in the pop-up.

EVENT VALIDATION_PASSED analytics-lane QA QA-analytics-lane-01#D1-D4
EVENT VALIDATION_FAILED analytics-lane QA elicit.py:D1-named-tests(M1)
ARTEFACT>>>

Terminal state: **SUCCESS**. The verdict and risk opinion are issued and the line is signed with residual risk: D1–D4 are met, there is no regression, and no open defect is above the assumed Minor tolerance. D16–D18 stay open for the PO's accept decision.
