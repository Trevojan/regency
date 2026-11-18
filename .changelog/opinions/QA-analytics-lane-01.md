QA verify, unit analytics-lane: the verifiability line is refused (FAILURE).

The unit is in its span and its rollback range is consistent, and it does not regress the inherited suite. But four Major defects are open in the parts I rated HIGH or MEDIUM: three in the elicitation engine and its triage consumer, and one in the number the reconstruction measure reports. The version verdict is compatible addition, with one caveat (D2 below).

Notes on what I was given and what I did:
- **Withheld context reached me.** A system reminder showed me a task list with the developer's own task subjects. That is withheld material under my contract. I did not use it.
- **HEAD moved while I worked.** It went from ebad231 to b786b39, a commit I did not make. That commit changes only `.shortcuts/.virtual/ongoing.json`. Every script I tested is identical at both commits, so the verdict holds for 3396665..ebad231.
- **The repository is otherwise as I found it.** A git-ignored `scripts/__pycache__/` is present. Its oldest files predate ebad231, and I cannot rule out that my doctor run added one entry.
- **No suba lens was used.** I did not work under suba-recon, suba-tester or suba-validator, so no envelopes are attached.

<<<ARTEFACT risk-opinion
# Risk opinion: analytics-lane (plumbing, 3396665..ebad231), QA verify, 2026-11-18

Cited norms: library/analytics.md and library/elicitation.md, both agent-drafted and not ratified. They were treated as the implementation's claims. The Regent's spec (`c76effd5-pokayoke.xml`) and the Regent's decisions of 2026-11-16 are the criteria.

## Scope and inputs
- **Span:** `git diff --name-only 3396665 ebad231` equals `touched_paths` exactly (36 files). Nothing changed outside the span.
- **Rollback:** `40e17e9^` is 3396665. The range is 14 commits with no merges. `git revert 40e17e9^..ebad231` is valid.
- **Change notes:** in the fixed shape. "Each seen red before green" was not evidenced to me.
- **DA oracle:** none was supplied. For the one number that reaches the Regent (D4) I used my own hand computation.

## Criticality assumed (no PO frame existed) and the tolerance I applied
| Part | Criticality | Why | Max tolerable severity assumed |
|---|---|---|---|
| hook-elicit.py (PreToolUse guard on every AskUserQuestion, `onFailure: block`) + elicit.py + the triage consumer | HIGH | It sits on the Regent's decision channel. It can deny a Regent pop-up or misattribute a Regent decision. | Minor |
| hook-reads.py + reconstruction.py | MEDIUM | Async recorder on every Read. Its ratio drives a build decision (ROADMAP: "built only for the files … the measure shows being rebuilt"). | Minor for the number, Major otherwise |
| analytics.py lane writes, alpha.py tags, exports and builds | MEDIUM | Writes git refs, objects and tags, and runs a shell build. | Major |
| locate.py, docs, registry | LOW | Read-mostly cache and text. | any |

Assumption (RA §27): the tolerance above. If the PO states a different tolerance, the refusal may change.

## Regression: the inherited suite, checkpoint first
| Run | Result |
|---|---|
| doctor at HEAD (local) | 2 FAIL: hook-hazard 217/218, hook-refs "(no output)". 30 WARN. Every other check OK. |
| doctor at 3396665 (my own export) | the same 2 FAIL |
| CI | 1 FAIL (hook-hazard) at both 3396665 and ebad231 |

- No new failure. The checkpoint itself is not green; both reds sit outside this span and are declared out of scope.
- Every new self-test passes: analytics 22/22, alpha 9/9, locate 12/12, reconstruction 7/7, hook-reads 6/6, elicit 29/29, hook-elicit 14/14.
- Touched modules pass too: idx 35/35, shortcuts 43/43.

## Open defects

Reproductions are in `/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa/probes/pN_*.py`. Run each with `PYTHONDONTWRITEBYTECODE=1 python3 <file>`. Each builds its own fixture in a temporary directory.

### MAJOR

**D1. Cross-session leakage: an answer goes to, or is refused by, the wrong elicitation session.** (elicit.py `locate_question`, hook-elicit.py)
- **Steps:**
  1. Start the same schema under two tasks (two open sessions).
  2. Run `next` on the newer one and pass its `ask.questions` verbatim through the hook.
- **Expected:** the session that rendered the question owns it. The docstring says "else the latest session".
- **Observed:**
  - If the older session already answered it, Pre denies the newer session's correct rendering as "already answered … reopen --session EL-0001" (p1).
  - If the older session left it unanswered, Pre allows it, and Post confirms the Regent's answer in the older session. The newer session gets nothing (p2: old `{'rule': ('B','confirmed')}`, new `{}`).
- **Cause (inferred):** when renderings are equal, the first match in rowid order wins.
- **On the real consumer (p13):**
  1. Day 1: triage AN-01-01 as Recycle (it stays live). The session stays open because the playbook never resets it.
  2. Day 2: `triage-2026-11-18` asks D_AN-01-01 and the hook denies it as answered in the day-1 session.
  3. `triage --from-elicit` then fails with "no finding has the Regent's complete answer yet: AN-01-01".
- **Violates** the spec rule "Prevent cross-session state leakage".

**D2. Unrelated pop-ups are captured by header.**
- **Steps:**
  1. Complete every question of a session. It stays `status: open`, because nothing closes a session on completion.
  2. Later, ask an unrelated AskUserQuestion with header "Owner".
- **Expected:** "Every other question passes untouched and nothing is read for it" (hooks.md, Elicitation; hook-elicit docstring).
- **Observed (p10):** deny, "Q_NOTE is already answered: owner = The Regent … reopen --session EL-0001".
- The question cannot be asked through the pop-up until someone resets that session.
- This is the caveat on the version verdict: unfixed, it changes the behaviour of pre-existing pop-ups in any project that uses the engine.

**D3. The engine's own rendering is denied when the prompt holds a double space or a newline.**
- **Cause:** Pre compares the whitespace-normalised incoming text with the un-normalised rendering. `problems()` accepts such prompts.
- **Steps (p12, the real consumer):**
  1. Record a finding titled `approve()  offers no reversal` (two spaces; the suba-recon contract allows it, at most 120 characters with no pattern).
  2. Run `triage-schema` → `start` → `next`, then pass `ask.questions` verbatim.
- **Expected:** allowed.
- **Observed:** deny, and it repeats on every retry. That finding cannot be triaged through the engine. The typed-triage fallback remains. p11 shows the same at engine level.

**D4. The reconstruction ratio counts bytes no earlier session read.**
- **Steps (p6):** s1 reads lines 1–10 of an unchanged 100-line file; s2 reads lines 51–100 of it.
- **Expected:** "the bytes an earlier session already read unchanged" (registry, CLAUDE.md, README). Hand oracle: carried 0/500, ratio 0.0.
- **Observed:** carried 500/500, ratio 1.0.
- **Cause:** a match on path + sha256 credits the whole current read. The METHOD line states this file-level rule, so the number contradicts the command's own summary rather than its printed method.
- **Escalation, L4 to RGN through the PO, DA to define:**
  - **trigger:** a user-visible number disagrees with its advertised definition.
  - **unresolved question:** is "carried" file-level or line-level?
  - **evidence:** p6.
  - **attempted:** a hand oracle.
  - **risk:** an inflated ratio decides what gets built (ROADMAP).
  - **required decision:** either (a) line-level carried, or (b) keep file-level and reword every summary.

### MINOR

**D5. Rejections are never recorded.**
- `accept()` writes `answer_rejected` inside the transaction that its own re-raise rolls back.
- p3: three refusals, 0 events, metric `answer_rejected: 0`.
- elicitation.md §7 counts "refused", and the spec's observability list includes "answer rejection" and "validation failure".

**D6. `reset` without `--session` closes an implicitly chosen session.**
- p9: EL-0002 is closed. The tie on second-resolution `updated_at` falls to the highest id, so it was not even the session touched last.
- Spec: "Reset an explicitly selected task/session scope." A closed session cannot be resumed.

**D7. `inputs` slots cannot be filled by anything.**
- They pass `check` and are documented as "filled only by a derived source", but `accept()` resolves only questions.
- p4b: `submit --slot env --source derived` is refused, and the dependent question stays `blocked` forever.

**D8. A `derived` submission replaces a confirmed answer without a reopen.**
- `submit --source derived` is CLI-callable by an agent. It overwrites a Regent-confirmed value with a different one (confirmed → derived).
- p4c: owner RGN (confirmed) becomes RGN-PO (derived).
- Spec: "Never silently overwrite historical decisions." It is latent: no shipped schema declares a slot `derived`.

**D9. Failure modes differ from the documentation.** Setup: one open session whose stored schema fails its hash check (p5).
- **PreToolUse:** every AskUserQuestion in the project, unrelated ones included, gets `ask` with "regency guard error". elicitation.md §5 says "when it cannot run, the pop-up is blocked".
- **PostToolUse:** the error goes to stderr only. The agent is not told that the Regent's answer was not recorded. The spec requires non-blocking failures to be "explicitly identified as unprotected".

**D10. `alpha.py cut` tags before it exports.**
- A failure after tagging leaves `alpha-001` with no export.
- p7: `.alpha` exists as a file → FileExistsError, the tag stays, and a retry is refused ("a capsule never moves"). Recovery needs a tag delete (a hazardous act) or the next id.

**D11. A multi-select option whose label holds a comma can never be chosen.**
- p4d: "X2, now" is refused. The schema check accepts the label. Latent.

### TRIVIAL / documentation
- **D12.** When an invalidated slot is re-answered or proposed over, its provenance `history` is dropped from the parameter row (p4a). The events table keeps it. elicitation.md §3 "keeps … its history" holds only until the next answer.
- **D13.** shortcuts.md §3 says "locate.py writes only the search tables", but it also writes `meta` keys `search_delete` and `search_scope`, which the `meta` row does not list.
- **D14.** analytics.md §2 says INDEX.json is "the only file that changes", but the root README.md is rewritten on every lane write.
- **D15.** Code reading only, not run: in `record`, a delta's `unanswered` list ignores the pass `--scope` that `plan` honours.

## Coverage gaps (cases that should exist and do not)
- Two open sessions sharing a header (D1).
- A non-engine pop-up while a completed session is still open (D2).
- Whitespace in prompts (D3).
- A partial read across sessions (D4).
- The `answer_rejected` metric (D5).
- Reset without an id (D6).
- `inputs` (D7).
- Derived over confirmed (D8).
- Hook errors at Pre and Post (D9).
- An alpha that fails after tagging (D10).

Weak or approximated tests:
- Test 14 runs threads in one process. I added 8 processes × 25 operations, flipping the upstream value: revisions strictly +1, no stale-fingerprint confirmations, no errors.
- Test 13 only reopens the store. It never kills a process mid-transaction.

## Verification cost
- **`elicit.accept` (~75 lines):** source × same/changed value × status × rank form a combinatorial path set (rules 1 and 2).
- **`hook-elicit.answers()`:** its slicing of the result text is position arithmetic on a format never seen live.

## What was NOT covered
- **The live AskUserQuestion contract.** Not checked: whether Pre fires before the dialog, and whether answers reach PostToolUse as `tool_input.answers`, `tool_response.answers` or `"q"="a"` text. library/maintaining.md:80 records this as "not yet seen live". The engine's only confirmation path is therefore unproven against the real runtime, and the spec asks for tests "against the actual hook contract, not a fabricated approximation".
- **`onFailure: block` and the 10 s timeout under lock contention**, for example during a long `locate.py index` write transaction.
- **hook-reads on large or binary files and under parallel async calls.** It reads and hashes the whole file on every Read.
- **Whether `agent_type` exists on PostToolUse Read events.** If it does not, every row is recorded as "main".
- **The playbooks run by a real agent:** a suba-recon dispatch in direct mode, the push steps, and `alpha cut --build` on a real project. The build runs `shell=True` inside Python, out of hook-hazard's view.
- **Python 3.8 and Windows.** I ran Python 3.13 on Linux only.
- **locate.py** first-index time on a large repository, and first-hit line accuracy with diacritics.
- **Red-first of each named new test.** No mutation run.
- **Regent's spec items not implemented:**
  - timing and database-operation measures (performance requirements);
  - an activation policy for proposed schemas (ROADMAP admits none exists);
  - a new `start` activates any valid schema file, so the "ratified file" rule is a norm only.

## Version verdict
**Compatible addition.**
- 6 commands added; none removed or renamed.
- New hook handlers only; the existing ones are byte-identical (surface.diff).
- `idx.parse(light=False)` keeps the default behaviour.
- New store tables. `idx build` still clears only files, nodes, cites and shortcuts; `meta` gains two additive keys.
- The conventions additions are additive.
- The inherited suite is identical to baseline.
- Caveat: D2, unfixed, alters pre-existing pop-ups in projects that use the engine. That would be a break for them.

## Recommendation (for the PO, who decides)
Approved, with residual risk, only for the analytics lane writes and for locate.py: I found no defect above Minor there.

I refuse the line for the elicitation engine and triage (D1–D3), and for the reconstruction measure (D4) until DA defines "carried".

Rollback of the whole unit is named and clean.

EVENT VALIDATION_FAILED analytics-lane QA hook-elicit.py
EVENT VALIDATION_FAILED analytics-lane QA reconstruction.py
EVENT ESCALATION_STARTED analytics-lane QA reconstruction-ratio-definition
ARTEFACT>>>

Terminal state: FAILURE. The verifiability line is refused: four Major defects (D1–D4) are open in parts I rated HIGH or MEDIUM, against the Regent's spec rules on cross-session leakage and on the advertised meaning of the measure. D4 also carries an L4 escalation to the Regent through the PO.
