# PO accept: grant-latest, attempt 6

**Decision: ACCEPTED.** It covers the increment 40e1982..0c45883 as QA-grant-latest-06 verified it. Three items must land before the line leaves plumbing (§4).

**Why I can accept it:**
- I am PO; DV produced the increment.
- Every attempt-6 criterion is met except two:
  - the Regent's "a cd is logical unless the line says otherwise" is partially met; the residue is N17, which is pre-existing and which the Regent sent to the backlog on 2026-11-25;
  - criterion 4 (the drafted norm text) is partially met; see §3.
- Criticality is high, and the one defect the unit introduces is N18, which is low. That is within "no open defect above low introduced by the unit".
- QA's signature is qualified, so PO §12 requires a consult first. The Regent's 2026-11-25 decision ("accepted for the line…, next, the PO's accept") is that consult.
- I wore no suba lens: none of the PO's lenses covers the accept stage. So there is no envelope.

## Known defects

Severities are QA's. Where QA classified none, I add none (severity is QA's call, PO §2).

| Id | Severity | Origin | Where it goes | Residual risk, one line |
|---|---|---|---|---|
| N17 | medium | pre-existing | guards-followups (RGN 11-25) | Under a `**` grant, a removal deletes outside the repository after physical mode is turned on by `shopt -o`, `eval`, `set -o -P`, a heredoc to `bash -P` or SHELLOPTS, or after a `set +P` that bash never runs. Silent. |
| N18 | low | introduced | guards-followups | Prompts only: single-`-f` git clean asks where git removes no bare repository, and past the 3 s search it always asks. |
| N19 | medium | pre-existing | guards-followups | git clean with pathspec magic (`:!`, `:^`, `:(exclude)`, `:/`) or git's own wildcards deletes nested clones and bare repositories, with their unpushed history, under `delete **`. Silent. |
| N20 | medium | pre-existing | guards-followups | A bare repository below a `.git` file that git does not read is deleted under `delete **`. Very low likelihood. |
| N21 | medium | pre-existing, outside the unit | its own unit, hazard-piped-shell (RGN) | A command piped into a shell runs with no grant at all. It is the widest open allow, because it needs no `**`. |
| N14 | low | introduced at attempt 5 | guards-followups (RGN 11-23) | Prompts only: a bare-shaped plain folder makes every recursive removal above it ask. |
| N15 | low | pre-existing; verdict inferred | guards-followups | A `[^…]` glob may skip the search below the folder bash picks, so a nested clone there could go under `delete **`. Never fed to the hook. |
| N16 | low | inferred, not run | guards-followups | Under sudo/doas, the search passes a folder the hook cannot read but root's removal can, so a nested repository there could go under `delete **`. |
| N3 | low | pre-existing | guards-followups | For a `..` through a link, the Judge proposes the written place; granting it lets the act delete where the path really lands. |
| N4 | low | pre-existing | guards-followups | A relative-glob grant inside the repository is matched by the written name, so it reaches where an inner link lands. |
| N7 | low | introduced at attempt 4 | guards-followups | Removing an outward link by name asks, and the Judge's proposal for it, if granted, would also cover D1's delete-through-the-link form. |
| N9 | low | introduced at attempt 4, widened by N14 | guards-followups | Prompts only, on bare-shaped plain folders. |
| N10 | low | introduced at attempt 4; simulated | guards-followups | An unreadable folder makes the guard error and ask (it fails closed); `judge.py check` may end in a traceback (inferred). |
| R6 | not classified | residual | guards-followups | A link or repository made earlier in the same line is not seen, so an act through it or in it is allowed under `**`. |
| D3 | low | pre-existing | guards-followups | A grant on `env/**` covers `.env`, which it does not name. |
| D4 | low | pre-existing | guards-followups | `m\ain` passes the text guard; where hook-refs is absent (R1), it reaches main. |
| D5 | low (documentation) | pre-existing | guards-followups | hooks.md §2 promises a context line outside a repository that never appears, and §1 disagrees. |
| R1 | high (residual) | pre-existing | cloud-main-guard; the Regent does not accept it as a limit (11-19) | In every session whose environment sets GIT_CONFIG_*, only the text guard stands over main, and the common chain forms pass it. |
| R2 | not classified | coverage gap | **no ledger line** | The hook-in-configuration way of hook-refs has never been exercised by QA. On a git that uses it, the guard over main rests on an unverified path. |
| R3 | not classified | known-open rows | guards-followups | Several rows stay open: a force through an alias is not asked; an untagged paste confirms a cloud write; `--no-verify` forms skip both guards; the ratify verb shows a count, not the rows; a linked worktree under a push grant is refused; the station does not report hook-refs. |
| R4 | not classified (over-ask) | pre-existing | guards-followups | Prompts only: one `$( )` makes every act in its line ask. |
| R5 | not classified, not observed | pre-existing | guards-followups | After the 3 s lock timeout, gov.py rewrites unlocked, so a lost write under long contention is possible. |

Also accepted open, without ids:
- `git submodule foreach` is not read as hazardous (guards-followups).
- `rd /s` switches are read as paths (guards-followups).

Seen by QA in passing, with **no ledger line**:
- The ask's reason is cut with "…" (`one_line`, in hook_wire.py, outside the span), so the Regent can be shown an incomplete grant proposal.
- The reason given when the search times out does not say that time ran out (QA-05 §4).
- A session opened through a link to the repository finds no session grant (it asks).
- PowerShell's `set` is read as bash's (it asks more).
- A DeprecationWarning at hook-hazard.py:134.

## Residual risk

- **Tests that would miss a regression.** QA-06 §4: mutations H11, H15, H16 and H17 turn today's correct asks into allows and the suite stays at 310/310. H12, J6, J7 and J12 also fail toward allowing. N12's named case proves nothing about "over a nested clone"; it passes on `vendor.git` alone.
- **Shell assumption.** The Regent decided the agents' shell never starts in physical mode. If that is false, N11/N17 widen to every `cd <outward link> && cd ..`.
- **Not covered by QA:**
  - zsh `chase_links`/`chase_dots` (a Mac's agent shell);
  - Windows and macOS;
  - a live Claude Code session;
  - an unprivileged user;
  - Python 3.8–3.10;
  - git versions other than 2.43;
  - the budget on a cold cache, network file systems or slower machines;
  - grant stores other than the session store;
  - CI for 0c45883;
  - the removals themselves (shown only by `pwd -P` and git's dry run);
  - other acts that reach nested repositories (`git rm -r`, `rsync --delete`, `mv`, `submodule deinit`, `worktree remove`).
- **Agent text read as the Regent's** (verbs-agent-text, suspected, not observed). Until it closes, a grant could be recorded from an agent's text. Every `**`-dependent row above could then be reached without the Regent's own grant.

## 3. Drafted norm text: where QA reports it states more or less than the code

The physical-mode text is the same in judge.md §2 and hooks.md §2. All points are QA-06 §2 unless marked.

1. "Only the line itself turns physical mode on: `set -P` or `set -o physical`, until `set +P` or `set +o physical`, or … `bash -P -c` / `bash -o physical -c`."
   - **States less than bash:** `shopt -s -o physical`, a `set -P` inside `eval`, and `bash -P` fed by a heredoc also turn physical mode on. judge.md also lacks the SHELLOPTS exception that hooks.md names.
   - **States more than the code** ("until"): a `set +P` after `||`, in an untaken `if`, in a pipe or with `&` still ends physical mode for the reader (N17).
2. "A `set` reads as bash reads it…" **States more than the code** for `set -o -P`: bash goes on to `-P`, while the reader takes `-P` as the `-o` name.
3. "git clean with one `-f` … git passes whole only a folder whose `.git` it reads as a repository…"
   - **States more than the code:** a `.git` file that git does not read is passed whole by the code, and git removes the folder (N20).
   - **States more than git:** with no `-d`, or with `-X`, git removes no bare repository there (N18). The text owns this choice; its cost is prompts.
4. "A git clean names the paths git reads as its own: the pattern of `-e`/`--exclude` … is none." Met for `-e`/`--exclude`. **States more than the code** for pathspec magic and git's wildcards that match across `/` (N19).
5. "A glob reaches the folders its wildcard part matches, as a shell expands it." Unchanged. **States more than the code:** `[^…]` is not expanded as bash expands it (N15). For git clean, an unexpanded glob is git's pathspec (N19).
6. hooks.md "Not read: SHELLOPTS…, PowerShell's `..`, git clean's `-d` and exclude patterns (the search reaches more, never less), `--recurse-submodules`." Accurate as far as it goes, but **it omits** N17's other forms, N20, and N19, where the search reaches *less*.
7. hooks.md "1.4 million files run past its 3 seconds…" Consistent with QA's measure. It is one machine with a warm cache: a measurement, not a promise.
8. hooks.md §2's paragraph on the context line outside a repository. **States more than the code** (D5, QA-03; the paragraph is untouched since).
9. **Matches the code, but worth the Regent's eye at ratification** (QA-04, in passing): "the repository's own `.git` stays in it" means `delete **` covers `rm -rf .git`.

Clauses QA found met: `cd -P` / `-L` / the shell's mode with the file system as fallback, the set-letter and unknown-`-o` rules for the probed forms, single-`-f` git clean over bare repositories as git's dry run shows, the `-e` exclusion, and the 3 s search failing to an ask.

## 4. What must land before the line leaves plumbing

1. **The span's code must be 0c45883's.** The coordinator reports plumbing at 4596eb9. I was given nothing that shows what lies between 0c45883 and 4596eb9. If any commit there touches scripts/hook-hazard.py, scripts/judge.py, library/judge.md or library/hooks.md beyond the item below, this accept does not cover it, and the line goes back to QA.
2. **The Regent ratifies or rewords judge.md §2 and hooks.md §2 (§3 above), and that text is committed.** This is part of QA-06's option A, and CHECKPOINT does not yet record it. The reason: a norm that promises a protection the guard does not give turns the backlog's known silent allows (N17, N19, N20) into unknown ones for every later reader who decides on a `**` grant (conventions §7: state the present; nothing cites an unratified norm).
3. **The version moves to 4.0.** The Regent decided this on 2026-11-19, but QA-06 §6 reports the files still at 3.3 on a break verdict. The close owes it, so that no branch past plumbing carries the break under 3.3.

**Not required before plumbing, but ordered:**
- QA-06 §4's four cases go first in whichever unit next edits scripts/hook-hazard.py (hazard-piped-shell or guards-followups), each seen red under its mutation before that unit's own change. N12's case also gets a nested clone with no bare repository.
  - *Not now:* the Regent chose option A over option B, and QA placed these four cases in B.
  - *Ordered anyway:* hazard-piped-shell reads input that a nested shell runs, which is the area of H11/N17, and it could regress N11's and N12's fixes with the suite still green.
- The orchestrator adds ledger lines for R2, the truncated reason, and the timeout reason. I write no file.

## 5. Q1 and Q2

**Q1: two readings of "bare repository". Decision: accept the debt until N14 is fixed. No single reading is required now.**
- Both ways of getting one reading are closed:
  - The names reading for both widens N14 to git clean. The Regent ruled that out on 2026-11-23: "the same acts with no repository below stay as they were".
  - git's reading for both is N14's own fix. The Regent placed N14 in the backlog, and doing it now would reopen the removal search on a line the Regent has accepted.
- The debt costs verification (QA-06 §4 notes the extra code paths) and N14's prompts, which ask more, never less.
- The debt closes with N14, in guards-followups. That unit's criteria must include J6 (linked HEAD), J7 (unreadable HEAD) and J12 (missing HEAD), each seen red. Then converging on one reading is proven not to turn today's asks into allows.

**Q2: the 3-second search deadline. Decision: accept 3 s for this line.**
- QA-06 §5 measured at most 3.09 s end to end. That leaves at least 6.9 s of the 10 s timeout.
- Both limits fail closed: past 3 s the act asks, and past 10 s `onFailure: block` stops it. So the value can only cost prompts, never let an act through silently.
- The prompts it costs: on trees past about 1.4–1.5 M files, `rm -rf .` and `git clean -fdx` always ask, and no grant covers them there.
- Not measured: a cold cache, network file systems, slower machines. A slower machine moves the threshold down, which means more prompts, still closed.
- The value becomes a norm only when the Regent ratifies the §2 text that carries it (§4 item 2).

EVENT DECISION_MADE grant-latest PO QA-grant-latest-06

Assumed that the Regent's "accepted for the line" (2026-11-25) chose QA-06's option A, which also carries the ratify-or-reword and the version, because the decision did not say so in those words. Next time: "accepted for the line on option A; norm text: ratified / reworded as …".

**Terminal state: SUCCESS.** The accept stage is complete. The increment is accepted on QA's signed opinion and the Regent's consult, with every known defect and residual risk named. What remains (§4) is the Regent's ratification and the close, both already the next step on the ledger.