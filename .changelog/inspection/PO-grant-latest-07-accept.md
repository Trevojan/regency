# PO accept: grant-latest, attempt 7

**Decision: accepted.** This accept covers the increment 7fe5605..1c4fed2 as QA-grant-latest-07 verified it. It sits on top of the increment the attempt-6 accept covered. Two of the attempt-6 conditions still stand before the line leaves plumbing: the Regent ratifies the norm text, and the version moves to 4.0 (see "The attempt-6 conditions" below).

**Why I can accept it**
- I am PO, and DV produced the increment.
- QA signed the verifiability line for the criteria as written, with residual risk. Of the ten criteria, eight are met and two are partially met. Both partial ones come down to N22:
  - the Regent's `.git` rule: 57 of the 64 lines that reach the `.git` now ask, and seven globs that bash expands differently still do not;
  - the norm text's claim that it is complete.
- Criticality is high: no open defect above low may be introduced by the unit. QA classes N22–N25 as pre-existing, since each is allowed at 7fe5605 as well. Every compared row that changed moved from allow to ask. So the increment is within the bar. Origin and severity are QA's calls (PO §2), and I add none.
- QA's signature is qualified, so PO §12 requires a consult first. That consult is the Regent's decision of 2026-11-25: "accepted for the line, its older silent allows to the backlog", with `shell-reading-model` as a unit of its own.
- The ledger now holds every QA-07 finding:
  - N22, N24, N25, G6, G11 and the retired cases are in `guards-followups`;
  - N23 is in `hazard-piped-shell`;
  - N15, N17, N22 and N23 are in `shell-reading-model`.
  QA-07's "none in the ledger" was true when it was written; it is no longer true.
- The attestation is not ambiguous (PO §19.8): the residue is named and observed, and the Regent has disposed of it.
- I wore no lens, so there is no envelope. suba-strategy does touch residual-risk trade-offs, but it is a proposal still awaiting the Regent's ratification, and it prepares a decision rather than making one.

**What I read**
- The contract files:
  - po.md;
  - PO.md, with §19;
  - TEAM.md §3 and §7;
  - packets.md §2, row PO;
  - conventions.md;
  - ALIGNMENT.md §1 and the descriptions of the four PO lenses.
- The three inspection acts.
- CHECKPOINT's "Team" section. I also read "Next, in order", because the grant-latest ledger line points there.
- The six ledger lines.
- Not read: the diff, commit messages, DV's reasoning, and the text of judge.md and hooks.md. I judged that text as QA-07 reports it.

## Known defects

Severities are QA's. "Ledger" is where the Regent's disposal placed each one.

**Opened at attempt 7** (all pre-existing):

| Id | Severity | Ledger | Residual risk, one line |
|---|---|---|---|
| N22 | medium | guards-followups; shell-reading-model | Under `delete **`, a root glob that bash expands to include `.git` and the reader does not (`.[^.]*`, `* .[^.]*`, `.[[:alpha:]]*`, `dotglob`, `GLOBIGNORE`, `globstar dotglob`) deletes the repository's own `.git` and its unpushed history, silently. hooks.md §2's Not-read list omits these forms. |
| N23 | medium | hazard-piped-shell; shell-reading-model | An act that an `eval` places after a quoted operator (`eval true '&&' rm -rf src`, `… git reset --hard`) runs with no grant at all. |
| N24 | medium (QA notes the Regent may weigh it as D1, rated high at QA-03) | guards-followups | A glob whose wildcard matches an outward link (`rm -rf */x`, `l*/x`, `find */x -delete`, `rm -rf */`) removes outside the repository under `delete **`, silently. |
| N25 | low | guards-followups | `git -C .git/modules/<sub> reset --hard` discards a submodule's change under this repository's `discard **`. |
| G6 | test gap, fails toward allowing | guards-followups | If a root `.git` that is a file goes unseen, root recursions at a linked-worktree root become allows and the suite stays at 348/348. |
| G11 | test gap, fails toward allowing | guards-followups | If a link inside the repository to its `.git` goes unseen, `rm -rf g/objects` and `rm -rf g/` become allows and the suite stays green. |
| — | not classified (process, QA §9 rule 2) | guards-followups | DV's change notes retired three inherited allow labels without giving a reason. The reason (the Regent's `.git` rule) is recorded only in QA-07 §1 and §6. |

**Carried from the attempt-6 accept**, unchanged at attempt 7 (QA-07 §2, identical rows):

| Id | Severity | Ledger | Residual risk, one line |
|---|---|---|---|
| N17 | medium | guards-followups; shell-reading-model | Physical mode turned on by `shopt -o`, a quoted `eval`, `set -o -P`, a heredoc to `bash -P` or SHELLOPTS, or left on after an unrun `set +P`: a removal deletes outside the repository under `**`. Silent. |
| N18 | low, introduced at attempt 6 | guards-followups | Prompts only: a single-`-f` git clean asks where git removes no bare repository. |
| N19 | medium | guards-followups | git clean with pathspec magic or git's own wildcards deletes nested clones and bare repositories under `delete **`. Silent. |
| N20 | medium | guards-followups | A bare repository below a `.git` file that git does not read is deleted under `delete **`. Very low likelihood. |
| N21 | medium, outside the unit | hazard-piped-shell | A command piped into a shell runs with no grant at all. |
| N14 | low | guards-followups | Prompts only: a bare-shaped plain folder makes every recursive removal above it ask. |
| N15 | low (QA-06's rating, given while inferred) | guards-followups; shell-reading-model | QA-07 has now observed it on the wire: `rm -rf [^v]*` is allowed while bash picks a folder that holds a clone. It has not been re-rated. |
| N16 | low, inferred | guards-followups | Under sudo or doas, a folder the hook cannot read hides a nested repository from the search. |
| N3 | low | guards-followups | For a `..` through a link, granting the Judge's proposal lets the act land where the path really leads. |
| N4 | low | guards-followups | A relative-glob grant reaches wherever an inner link lands. |
| N7 | low | guards-followups | The proposal for removing an outward link by name would, if granted, also cover D1's form. |
| N9 | low | guards-followups | Prompts only, on bare-shaped plain folders. |
| N10 | low, simulated | guards-followups | An unreadable folder makes the guard ask (it fails closed); `judge.py check` may end in a traceback. |
| R6 | not classified | guards-followups | A link or repository made earlier in the same line is not seen. |
| D3 | low | guards-followups | `env/**` covers `.env`. |
| D4 | low | guards-followups | `m\ain` passes the text guard; where hook-refs is absent (R1), it reaches main. |
| R1 | high (residual) | cloud-main-guard; the Regent does not accept it as a limit (11-19) | Where the environment sets GIT_CONFIG_*, only the text guard stands over main. |
| R2 | not classified | guards-followups | hook-refs' hook-in-configuration path has never been exercised. |
| R3 | not classified | guards-followups | Several rows stay open: a force through an alias, an untagged paste, `--no-verify` forms, the ratify verb showing a count, a linked worktree under a push grant, and the station not reporting hook-refs. |
| R4 | not classified (over-ask) | guards-followups | One `$( )` makes every act in its line ask. |
| R5 | not classified, not observed | guards-followups | After the 3 s lock timeout, gov.py rewrites unlocked. |
| H12, J6, J7, J12 | test gaps, fail toward allowing | guards-followups (N14's unit; J6, J7 and J12 must be seen red there) | A regression toward allowing passes the suite. |

**Also open, with no id**, all in guards-followups:
- `git submodule foreach` is not read;
- `rd /s` switches are read as paths;
- the ask's reason is cut at 600 characters. On long roots the cut now reaches `<proj>/.git/**` first; it fails closed;
- a timed-out search's reason does not say that time ran out;
- a session opened through a link finds no session grant;
- PowerShell's `set` is read as bash's;
- a DeprecationWarning at hook-hazard.py:134;
- the two readings of a bare repository, a debt until N14 is fixed (Q1 of the attempt-6 accept).

**Closed since the attempt-6 accept:**
- D5 (QA-07, point 8);
- QA-06 §4's four cases H11, H15, H16 and H17, now in the suite, each red under its mutation.

**Changed on purpose, prompts only, not defects.** These are the costs of the break:
- every root `find … -delete` asks, whatever its tests;
- `rm -f .git/index.lock` asks under `**`;
- `git -C .git checkout -- .` asks under `discard **`.

## Residual risk

- **The `.git` rule is not whole (N22).** Under a `**` grant given for this repository, its own history can still be deleted by a common dotfile spelling. This is the very class the Regent decided is fixed in this line.
- **Some silent allows need less than the rule does.** N23 and N21 need no grant at all. N24, N17, N19 and N20 delete outside the repository, or delete a nested history, under `**`.
- **An unvalidated shell assumption (QA-07 §8).** The norm assumes the agents' shell sets no glob option (`dotglob`, `GLOBIGNORE`, `globstar`). No decision covers this, as the Regent's decision of 11-25 covers physical mode. If the assumption is false, N22 widens to every `rm -rf *` at the root. I accept it in writing for this accept. The close needs the Regent's answer (see-first item 4 below).
- **Tests that would miss a regression.** G6, G11, H12, J6, J7 and J12 all fail toward allowing with the suite green.
- **The break reaches every grant store.** Every `delete **` and relative-glob row in the session, JD.md, machine and named-file stores stops covering the `.git`, a root `rm -rf .` and a root `find -delete`. `judge.py check delete .` now exits 1. The cost is prompts.
- **The budget sits at its threshold on very large trees.** On 1.5 M files, `git clean -fdx` asked in 2 of 5 runs. Both limits fail closed, so the cost is prompts only. Q2 of the attempt-6 accept stands.
- **Not covered by QA:**
  - zsh;
  - Windows and macOS, including a case-folding `.GIT`;
  - a live Claude Code session's shell snapshot and its glob options;
  - an unprivileged user;
  - Python 3.8–3.10;
  - git versions other than 2.43;
  - a cold cache or slower machines;
  - the removals themselves;
  - the glob options `nocaseglob`, `extglob`, `failglob` and `nullglob`;
  - acts that take the `.git` away without a removal: `mv`, redirects, `truncate`, `git gc --prune`, `update-ref -d`, `reflog expire`;
  - other acts that reach nested repositories: `git rm -r`, `rsync --delete`, `submodule deinit`, `worktree remove`;
  - the named-file store (JD-P);
  - hook-judge's pop-up beyond its own self-test.

  CI on 1c4fed2, which QA-07 listed as not covered, is now covered: run 45648320281 passed (given).
- **Agent text read as the Regent's** (verbs-agent-text, suspected). Until that unit closes, a grant could be recorded from an agent's text. Every `**`-dependent row above could then be reached without the Regent's own grant.

## The attempt-6 conditions (§4 items 1–3)

1. **The span's code is the verified code: met.**
   - The span's code at plumbing's head is 1c4fed2's (given).
   - 1c4fed2 differs from 7fe5605 in four files, all inside the span, byte-identical to dv-guards7.diff (QA-07).
   - 0c45883..7fe5605 touches only `.changelog/` and the ledger, so 7fe5605 carries 0c45883's code (QA-07).
   - So the only change to the span since 0c45883 is attempt 7, which QA-07 verified.

   This condition carries forward: any commit that touches hook-hazard.py or judge.py, or that changes judge.md or hooks.md beyond the ratification text below, is outside this accept and goes back to QA.
2. **The Regent ratifies or rewords judge.md §2 and hooks.md §2, and the text is committed: half met.**
   - The Regent chose to reword (11-25), and DV's rewording is committed at 1c4fed2.
   - QA-07 finds seven of my nine points stated as the code behaves: 1–4 and 7–9, with D5 fixed.
   - Points 5 and 6 are partially met, both because of N22.
   - The ratification itself is not yet recorded: CHECKPOINT's "Next, in order", item 2, places it after this accept.
3. **The version moves to 4.0: not met.** plugin.json still says 3.3 (given). The move is a step of the close.

Both items the attempt-6 accept ordered for later are done:
- QA-06 §4's four cases went in first and were seen red on 7fe5605's code (QA-07, criterion 3, MET);
- the ledger holds R2, the truncated reason and the timeout reason.

**What remains for the close**
- The Regent ratifies judge.md §2 and hooks.md §2, as they are or reworded (next section), and answers see-first item 4. The ratification is recorded with its date, and that text is committed.
- 4.0 goes into library/registry.json and .claude-plugin/plugin.json; doctor fails if they differ.
  - A HISTORY entry for 4.0 carries the break and its consumers (QA-06 §6 and QA-07 §6), including the three retired allow cases and their reason.
  - CHECKPOINT is rewritten at 4.0. Its header and its plumbing row still read 3.3 and "waiting on QA's third pass".
- `Verified-Draft: grant-latest` is recorded. The ledger's grant-latest item leaves `ongoing`, and `guards-followups` drops D5 and QA-06 §4's four cases, both closed. CI passes on the close commit.
- A doubt for RGN: CHECKPOINT's "Next, in order", item 3, names the release `v3.4`, but the line ships as 4.0 (the Regent, 2026-11-19). The two contradict each other, and the tag's name is the Regent's call.

## judge.md §2 and hooks.md §2: ratify as is, or see first

This is as QA-07 reports the text; I have not read it.

**Ratify as is.** QA-07 checked each of these and found it states what the code does:
- **Physical mode:**
  - every `set` is applied in the order written;
  - the forms that are not read are named: `shopt -s -o physical`, a `set -P` inside a quoted `eval`, a heredoc to `bash -P`, and SHELLOPTS, now in judge.md too;
  - the text says plainly that `**` still covers a removal that lands outside the repository (N17);
  - `set -o -P` changes nothing here.
- **git clean:** git clean with one `-f`, with N20 and N18 stated; and exclude patterns and pathspecs, with N19 stated.
- **The glob sentence, as it applies to the nested search:** globs are matched by `fnmatch`, which reads `[^…]` as a literal `^`, so the search can skip a folder bash picks (N15).
- **The budget:** "measured, not promised".
- **D5's paragraph.**
- **The Regent's rule, "`**` is the whole repository short of its own `.git`", with its stated costs:**
  - every root `find … -delete` asks;
  - `rm -f .git/index.lock` asks under `**`;
  - `git -C .git checkout -- .` asks under `discard **`;
  - the Judge's proposals end in `<proj>/.git/**`.
- **The new statements QA-07 found true:**
  - `env/**` covers `.env`;
  - a relative glob that opens with a dot covers nothing;
  - `judge.py check delete` looks below its paths as the guard does.
- **hooks.md's Not-read list, as far as it goes:** it now points to judge.md §2, and "the search reaches more, never less" is gone.

**See first.** Each of these either states more than the code does, or would settle something the Regent has not yet decided:
1. **hooks.md §2's claim to list "each place where this reader reads less or more than bash".**
   - The claim is false for `dotglob`, `GLOBIGNORE`, `globstar` and POSIX classes (N22).
   - Ratified as it is, it promises a protection the guard does not give. That is exactly the reason behind my attempt-6 condition 2.
   - The fix is either to add those forms or to drop the word "each".
2. **judge.md §2's `.git` sentence:** "a glob on the root whose wildcard part matches `.git` … asks under `**`".
   - The match is `fnmatch`'s, so `.[^.]*` and `.[[:alpha:]]*` are read as not matching, and are allowed.
   - The `[^…]` limit is stated for the search only.
   - The fix is either to state the limit at this sentence or to point the sentence to the glob sentence.
3. **The three pre-existing silent allows the text now names: N23, N24 and N25.**
   - Each statement is true of the code. Ratifying them makes them stated limits of the norm rather than defects against it; their ledger lines stay either way.
   - For N24, the text states the reading ("`rm -rf lin*/x` reads as the root wherever `link` leads") but not its consequence. That sits beside judge.md's "`**` … never reaches outside it".
   - QA-07 notes the Regent may weigh N24 as D1.
4. **The glob-options assumption under the whole text.** This is a closed question, like the one the Regent answered for physical mode on 11-25:
   - (a) the agents' shell never sets `dotglob`, `GLOBIGNORE` or `globstar`: N22 stays where the ledger puts it;
   - (b) it may set them: N22 widens to every root `rm -rf *`, and the Regent chooses between raising `shell-reading-model` and an eighth attempt.

This accept covers a reword limited to items 1–3, meaning one that adds limits QA-07 observed or removes the completeness claim. Such a reword states less, never more. Any other change to the text, or to the code, goes back to QA.

## Ordered for later, not required before plumbing

- G6's and G11's cases go first in whichever unit next edits scripts/hook-hazard.py (`shell-reading-model`, `hazard-piped-shell` or `guards-followups`). Each must be seen red under its mutation before that unit's own change. When N22 is fixed, its case "rm -rf .[^.]* at the root asks" joins them.
  - *Why:* `shell-reading-model` replaces the glob reading (`fnmatch` in picker()) that the `.git` rule rests on, and G6 and G11 fail toward allowing with the suite green.
- QA re-rates N15 in `shell-reading-model`, now that it has been observed.
- I write no file. The orchestrator records these on the ledger lines.

EVENT DECISION_MADE grant-latest PO QA-grant-latest-07

**Terminal state: SUCCESS.** The accept stage is complete. The increment is accepted on QA's signed opinion and the Regent's consult of 2026-11-25, with every known defect and residual risk named. What remains is the Regent's act and the close, both already the next steps on the ledger: the ratification, with four items to see first, and the move to 4.0.