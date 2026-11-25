I sign the verifiability line for this attempt's criteria as written, with residual risk, and I'm sending the residue to the Regent.

The `.git` rule asks wherever the reader can see the `.git`: in 57 of 64 lines that reach it, and in 19 of the suite's own cases. The Judge proposes the `.git` as its own place, and granting that proposal covers the act in the session, repo and machine stores. QA-06 §4's four cases are live, and each was seen red under its mutation on 7fe5605's code. The norm text now states points 1–9 of the PO's §3 as the code behaves, and D5 is fixed.

Nothing changed toward allowing, and nothing the unit introduces is above low.

Four findings remain, all allowed at 7fe5605 too and none in the ledger:
- **N22 (medium):** the `.git` rule leaks through globs that bash expands differently from the reader: `.[^.]*`, `[[:alpha:]]`, and `dotglob`/`GLOBIGNORE`.
- **N23 (medium):** an `eval` after a quoted operator runs with no grant at all. This attempt's norm text names it.
- **N24 (medium):** a link a glob's wildcard matches lets a removal land outside the repository. This attempt's norm text names it.
- **N25 (low):** a git act in a submodule's git folder runs in the submodule under this repository's `**`. This attempt's norm text names it.

Version verdict: **break**.

<<<ARTEFACT risk-opinion
# Risk opinion: unit grant-latest, QA verify, attempt 7

**Verdict in one line.** The Regent's `.git` rule is met wherever the reader can see the `.git`, and the Judge's proposal round-trips. QA-06 §4's cases are live, the drafted norm states the PO's nine points as the code does, and nothing changed toward allowing.

The rule is not met where bash's glob expansion reaches the `.git` and the reader's does not (N22, medium). The reworded norm also states three pre-existing silent allows that no ledger line holds: N23 (medium, with no grant at all), N24 (medium, outside the repository) and N25 (low). All four are allowed at 7fe5605 as well, so none is introduced. Line signed for the criteria as written, with residual risk. Version verdict: **break**.

**What was tested.**
- Branch plumbing at 1c4fed2. The change is `git diff 7fe5605 1c4fed2`: four files, all inside the span. dv-guards7.diff is byte-identical to it, and the surface diff (registry.json, hooks.json) is empty.
- 0c45883..7fe5605 touches only `.changelog/` and `.shortcuts/.virtual/ongoing.json` (file names, from `--stat`). So 7fe5605 carries the code QA-06 verified, and it is the regression baseline.

**What I read.**
- The four inputs and the contract files (qa.md, QA.md with §19, TEAM.md §3 and §7, packets.md §2 row QA).
- PO-grant-latest-06-accept.md, QA-grant-latest-06.md, and the QA-03/04/05/06 probes.
- File contents at both commits, and the suba-validator spine.
- The ledger titles of grant-latest, guards-followups and hazard-piped-shell, only to see whether a finding already has a line.
- Not read: git log, commit messages, CHECKPOINT and HISTORY, and any other file in the scratch folder.

**Change notes, checked against the diff.**
- `touched_paths` match the diff, `surface_changed: false` matches the empty surface diff, the rollback is named, and the notes argue nothing.
- The eleven `new_tests` names cover 32 of the 41 hook-hazard labels added, and all 4 judge labels.
- **They omit** the eight cases "and an act that does not reach it stays covered", the allow side, as attempt 6's notes also did. They also omit the relabelled "and still covers what it can: find src -name x -delete".
- **They do not record three retired inherited cases.** These are "and still covers what stays in this repository: rm -f .git/index.lock", "and a removal that reaches no repository below stays covered: rm -rf .git/modules", and "and still covers what it can: find . -name x -delete".
  - Each was an allow that the Regent's `.git` decision turns into an ask, and each command comes back as an ask case. The retirement is on purpose.
  - But nothing records its reason (QA §9 rule 2).
- `touched_phases` is empty and was not checked: no phase reference was given.

**Environment.**
- A Linux container, run as root, with bash 5.2.21, git 2.43.0 and Python 3.13 (3.11 and 3.12 also present).
- Probes ran on `git archive` exports of both commits and on fixtures in my scratch folder, with TMPDIR and HOME pointed there.
- Nothing was removed for real. What an act would reach was shown by bash's own `echo` of the glob, by `git rev-parse` and by `git clean -n`.
- /home/user/regency ends clean, on plumbing at 1c4fed2, with no stash. I committed nothing.

**Criticality.** High (the Regent, 2026-11-25): no open defect above low introduced by the unit.

## 1. Gate and inherited suite

| Check | Result |
|---|---|
| doctor at 1c4fed2, re-run by QA in a throwaway clone | 0 FAIL, 30 WARN, HEALTHY. The whole output is identical to gate-guards7-local.txt |
| the 33 self-tests doctor runs, at 7fe5605 and 1c4fed2, in the session environment and in a cleared one (GIT_CONFIG_* and the session variables unset) | All green in all four runs. hook-hazard goes from 310 to 348 and judge from 87 to 91; every other count is unchanged |
| hook-hazard, judge and hook-judge on Python 3.11 and 3.12 | 348/348, 91/91 and 10/10 |
| inherited labels in hook-hazard, judge, hook-judge, hook-verbs, hook-refs and guard-push, compared at runtime | 41 added to hook-hazard and 4 to judge. **Three retired**, all hook-hazard allows turned into asks by the `.git` rule (above). No other label lost |
| QA-03/04/05 probes (hz 16, ko 7, ex 58, sib 8, stack 2, cdl 7 rows) and QA-06's line files (n11 49, gc 42, n14 6), at both commits | Identical, except hz `rm -rf .git` and ex `rm -rf .git/modules/sub`: both allow → ask, by the rule |
| permission simulations (eacces.py, eacces5.py) | Identical, except `rm -rf .` allow → ask, by the rule |
| named tests are real: 44 mutations, each removing one part of a fix in a fresh copy (QA-06's 33, plus 11 against the new `.git` code) | **35 turn their cases red.** Of QA-06's 33, 26: H11, H15, H16 and H17 are now red. Of the new eleven, 9: G1, G2, G3, G4, G5, G7, G8, G9, G10 |
| | **9 turn nothing red.** Six fail toward allowing: H12, J6, J7 and J12 (unchanged, in N14's unit by the PO's order), plus **G6** (a root `.git` that is a file) and **G11** (a link inside the repository to the `.git`). Three fail toward asking: H18, J2 and J8. See §4 |

## 2. Verdict per criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| The Regent: `**` stops short of the repository's own `.git`. A removal that reaches it (naming it, a path in or under it, or a recursion from a folder above it) asks under `**` and every relative glob | **PARTIALLY MET** | **Met for:** 64 lines that reach it, under `delete **` (git-lines-a.txt). 57 go from allow at 7fe5605 to ask at 1c4fed2: 33 name it or a path in it, 13 recurse from the root, 11 are root globs that the reader matches against `.git`. **Not met:** the other 7 globs, allowed at both commits (N22). Detail below the table |
| The Judge proposes it as a place of its own, and granting that covers the act | MET | Detail below the table |
| QA-06 §4's four cases go in first, each red under its mutation before the change; N12's case also holds a nested clone with no bare repository | MET | Detail below the table |
| The norm text states the code, point by point against the PO's §3 (1–9, D5 included): "nothing the code does not do is promised" | **PARTIALLY MET** | Each of points 1–9 is now stated as the code behaves, and D5 is fixed (clause by clause below). **Not met:** hooks.md §2 says each place where the reader reads less than bash "is `library/judge.md` §2". It is not: bash's glob options (`dotglob`, `GLOBIGNORE`, `globstar`) and POSIX classes (`[[:alpha:]]`) are named nowhere. The `[^…]` limit is stated for "the search" only, not for the `.git` sentence it also defeats (N22) |
| The orchestrator's reading (criteria §3): N5's control holds except where the `.git` rule reaches the root's own `.git`, so `rm -rf .` and `find . -delete` at the root now ask | **MET (reading confirmed, wider than its two examples)** | Detail below the table |
| What attempts 4 to 6 fixed keeps its verdict: D1, D2, N1, N2, N5's six steps, N8, N11, N12, N13 | MET | Detail below the table |
| The backlog items N3, N4, N7, N9, N10, N14–N21, R6, D3, D4, R1–R5: not fixed, and not made worse | MET | Detail below the table |
| No open defect above low introduced by the unit | MET | Every compared row that changed went from allow to ask, by the rule. The four findings in §3 are allowed at 7fe5605 too. The rule's own costs are prompts: the root's `find` with any tests, `rm -f .git/index.lock` under `**`, and `git -C .git checkout -- .` under `discard **` (git refuses that act anyway) |
| Regression: the line as QA-06 verified it still holds except where the `.git` rule changes it on purpose; the inherited suite is no worse | MET | §1 |
| The hook's budget: hooks.json runs hook-hazard.py with `"timeout": 10` and `"onFailure": "block"` | MET (this machine, warm cache) | §5. At most 3.10 s end to end. hooks.json is unchanged, for both Bash and PowerShell |

**The `.git` rule, in detail.**
- *Naming it, or a path in it.* These ask: `rm -rf .git`, `-r`, `-fr ./.git`, `--recursive --force`, `-- .git`, `sudo` and `/bin/rm`; `rm -f .git/index.lock`, `rm .git/HEAD`, `shred -u .git/config`, `unlink`, `rmdir`; `src/../.git` and `.git/../.git`; a link inside the repository to it (`rm -rf g/`, `g/objects`, `rm g`); and `self/.git`.
- *Through a `cd` or a nested shell.* `cd .git && rm …`, `pushd .git && …`, `cd src && rm -rf ../.git`, `bash -c`, `eval rm -rf .git` and `eval 'rm -rf .git'` ask. So do `find .git … -delete`, and PowerShell's `ri -r -fo .git`, `Remove-Item -Recurse -Force ./.git` and `Remove-Item .git/index.lock`.
- *Recursion from the root.* These ask: `rm -rf .`, `./`, `../proj`, `cd src && rm -rf ..`, `cd .. && rm -rf proj`, `rm -rf self/`, `Remove-Item -Recurse .`, and every root `find … -delete`, whatever its tests.
- *Root globs that `fnmatch` matches against `.git`.* These ask: `.*`, `.g*`, `.git*`, `.?it`, `.[g]it`, `.[!.]*`, `.??*`, `.[a-z]*`, `./.g*`, `.g*/index.lock` and `* .*`.
- *Under a relative glob that names it* (`delete .git/**`): every one of these asks.
- *A linked-worktree root*, whose `.git` is a file: `rm -rf .`, `rm .git`, `rm -rf .*` and `find . -delete` ask.
- *Acts that do not reach it stay allowed.* These are 14 lines, among them `rm -rf *`, `rm -f .gitignore`, `rm -rf .github`, `rm -rf [.]git` (bash does not expand it), `git clean -fdx` and `-ffdx`, and `rm -rf src/.git`.
- *Not met: 7 globs, allowed at both commits (N22).* Each is a glob bash expands to include `.git`, shown by bash's own `echo` in the fixture: `.[^.]*`, `* .[^.]*`, `.[[:alpha:]]*`, `shopt -s dotglob; rm -rf *` (also with `&&`), `GLOBIGNORE=x; rm -rf *`, and `shopt -s globstar dotglob; rm -rf **`.

**The Judge's proposal, in detail.**
- With no grant, a path in the `.git` is proposed as an absolute place: `delete <proj>/.git/**`, or `delete <proj>/.git/index.lock`. A recursion from the root is proposed as `delete ** <proj>/.git/**`.
- I granted the proposal of 9 acts exactly as given, in each of three stores (session, repo, machine), on a fresh fixture each time. The 9 acts were `rm -rf .git`, `rm -f .git/index.lock`, `rm -rf .`, `find . -name '*.o' -delete`, `rm -rf .*`, `cd src && rm -rf ..`, `rm -rf g/objects`, `rm -rf .git src` and `Remove-Item -Recurse -Force .git`.
- Every act is then allowed. A session grant does not carry to another session; a repo or machine grant does. A neighbour act is opened only where the granted text names it (rt7.py).
- `judge.py check delete` answers as the guard does: `.`, `.git`, `.git/index.lock`, `g/objects`, `../proj` and `self` exit 1 with the same proposal; `src` and `.github` exit 0.

**QA-06 §4's four cases, in detail.**
- All four are in the suite under QA-06's exact labels.
- On 7fe5605's code, run with 1c4fed2's self-test, they are green. Each goes red under its own mutation: H11 (pushd), H15 (`--exc`), H17 (`--force --force`), and H16 for `git clean -ffdx` and the exclude forms.
- N12's four commands also run in a new `clone` fixture, which holds a nested clone and no bare repository. H16, H13 and H21 turn them red.

**The orchestrator's reading, in detail.**
- On a fixture with no repository below, N5's six steps are `rm -rf *`, `rm -rf .`, `rm -rf vendor`, `find . -delete`, `find vendor -delete` and `git clean -ffdx`. Of these, only `rm -rf .` and `find . -delete` go from allow to ask, both proposing `delete ** <proj>/.git/**`. `git clean -fdx` stays allowed.
- **The exception is wider than its two examples.** Every recursive removal from the root asks, whatever `find`'s tests: `find . -name '*.o' -delete`, `find . -path ./.git -prune -o … -delete`, `rm -rf .*`, `cd src && rm -rf ..`, `Remove-Item -Recurse .`. judge.md states this ("`find .` whatever its tests").

**What attempts 4 to 6 fixed, in detail.**
- The hz, ex, cdl, sib and stack rows are identical at both commits: D1's and D2's steps ask; N1's, N2's and N5's steps ask over nested repositories; N8's are allowed.
- QA-06's n11 rows (49) and gc rows (42) are identical: N11's two steps and every variant ask; N12's and N13's steps ask.

**The backlog items, in detail.**
- Identical at both commits: N14's six rows, the ex rows for N3, N4, N7, N9 and R6, the hz rows for D3, the hz and ko rows for R3 and R4, and the eacces rows for N10 and N16. Also identical: N17's rows in n11, N18's and N19's rows in gc, N20 (`stale/` removed by git's dry run, allowed), N21 (`echo 'rm -rf …' | bash`, allowed with no grant), and N15.
- **N15, now fed to the wire:** `rm -rf [^v]*` is allowed at both commits, while bash picks `nest` (holding a clone) and `stale`.
- The files of D4, R1, R2 and R5 are untouched.
- D5 is fixed (point 8 below).

**Clause by clause** (the PO's §3, against the reworded text and the code).

1. **Physical mode.**
   - judge.md: "Every `set` in the line is applied in the order written, whether bash runs it or not: one after `||`, in a branch not taken, in a pipe or in the background counts."
   - judge.md: "Not read, though each turns physical mode on in bash: `shopt -s -o physical`, a `set -P` inside a quoted `eval`, a heredoc fed to `bash -P`, and `SHELLOPTS` … for a shell the line starts."
   - It then says plainly that `**` still covers the removal that lands outside (N17).
   - This matches QA-06's N17 rows, which are identical here. **Met.** The SHELLOPTS exception is now in judge.md too.
2. **`set -o -P`.** "`-o` always takes the next word as its name, so `set -o -P` changes nothing here, where bash turns physical mode on." **Met.**
3. **git clean with one `-f`.**
   - "a folder whose `.git` is a file, whatever the file holds … a bare repository below a `.git` file git does not read is removed and not seen (N20)." This is bare_meets as it is: N20's row is allowed, and git's dry run removes `stale/`.
   - "The search runs whatever `-d`, `-x`, `-X` or `-n` say … (N18: prompts only)."
   - **Met.**
4. **Exclude patterns and pathspecs.** "git's pathspec magic … is read as a folder that does not exist, and git's own wildcards … as a shell glob on one level, so the search finds less than git removes … (N19)." **Met.**
5. **Globs.** "A glob reaches the entries its first wildcard part matches, dot names only when that part opens with a dot, matched by Python's `fnmatch`: … `[^…]` as a literal `^` … so the search can skip a folder bash picks (N15)."
   - Met for the search, and true of the code.
   - **But the same `fnmatch` reading decides the `.git` sentence ("a glob on the root whose wildcard part matches `.git`").** There, `.[^.]*` removes the `.git` under `**`, and the text does not say so.
   - POSIX classes, which `fnmatch` does not know, and bash's glob options are stated nowhere (N22).
6. **hooks.md's "Not read".**
   - It now points to judge.md §2 and lists N17, N19, N20, N15 with the link a wildcard matches, N9/N14, N3, N4 and R6. It adds N21 and the `eval` after a quoted operator, both "not read at all".
   - The earlier "the search reaches more, never less" is gone.
   - **Partially met:** its claim to list "each place where this reader reads less or more than bash" misses `dotglob`, `GLOBIGNORE`, `globstar` and `[[:class:]]`.
7. **The budget.** "Measured, not promised (QA-grant-latest-06 …)".
   - Consistent with QA-06 and with §5. On 1.5 M files here, `git clean -fdx` asks in 2 of 5 runs and is allowed in 3: the deadline sits at the threshold.
   - The sentence's own caveat covers that. **Met.**
8. **D5.** "a session opened outside a repository, where nothing is written and nothing is said."
   - SessionStart fed outside a repository returns nothing and writes nothing.
   - Inside one, with this environment's `GIT_CONFIG_COUNT` set, it returns one context line ("no pre-push check here"). In a cleared environment it writes the check and says so. hooks.md §1 agrees.
   - **Met; D5 is fixed.**
9. **"The repository's own `.git` stays in it."** Replaced by the Regent's rule ("`**` is the whole repository short of its own `.git`"), and the code follows it. **Met.**

Statements this attempt adds, each checked true against the code:
- "`env/**` covers `.env` and a relative glob that opens with a dot covers nothing": `./src/**`, `.cache/**` and `.*` cover nothing at both commits.
- "`rm -rf lin*/x` reads as the root wherever `link` leads" (N24).
- "`eval true '&&' rm -rf x` … is read as a word of the command before it" (N23).
- "a submodule's git folder under `.git/modules/` [is read as this repository], though git reads that folder as the submodule's own repository" (N25).
- "`judge.py check delete` looks below its paths the same way, the root's `.git` included."

## 3. Open defects, by severity

**N22: medium. Pre-existing (allowed at 7fe5605, where `delete **` covered every removal of the `.git`); what remains of the Regent's `.git` rule.** A root glob that bash expands to include `.git`, but the reader does not, is allowed under `delete **`.
- *Setup:* fx7.py. `proj` is a git repository with one commit, holding `src/`, `build/`, `.cache/`, `.github/`, `.gitignore` and `.gitmodules`; nothing is nested below. Session grant: `delete **`.
- *Steps:* PreToolUse Bash with cwd `proj`, each of:
  - `rm -rf .[^.]*` and `rm -rf * .[^.]*`;
  - `rm -rf .[[:alpha:]]*`;
  - `shopt -s dotglob; rm -rf *` and `shopt -s dotglob && rm -rf *`;
  - `GLOBIGNORE=x; rm -rf *`;
  - `shopt -s globstar dotglob; rm -rf **`.
- *Expected* (judge.md §2: "a glob on the root whose wildcard part matches `.git` … asks under `**`"; the Regent: "a removal that reaches it … asks"): ask.
- *Observed:* allow at both commits.
  - bash's `echo` of each glob in `proj` lists `.git` (`.[^.]*` → `.cache .git .github .gitignore .gitmodules`; `dotglob *` → the same plus the plain names). So each removal would delete the repository's history (inferred; nothing was removed).
  - `rm -rf .[!.]*`, `.??*` and `.*` ask.
- *Cause (INFERRED, not the reported defect):* picker() matches with `fnmatch`, which reads `[^…]` as a literal `^` and knows no `[[:class:]]`, and no `shopt` glob option is read.
- *Likelihood:* low, but `.[^.]*` is the common spelling of "every dotfile".

**N23: medium. Pre-existing; outside this unit's criteria, in N21's class; newly stated in hooks.md, with no ledger line.** An act that an `eval` puts after a quoted operator is not read at all.
- *Steps,* with **no grant**, cwd `proj`: `eval true '&&' rm -rf src`, `eval true '&&' rm -rf .git`, `eval true '||' rm -rf x`, `eval true ';' rm -rf x` and `eval echo hi '&&' git reset --hard`.
- *Expected:* ask, as `rm -rf src` alone does.
- *Observed:* allow at both commits. bash's `eval` joins its words and runs the `rm`.
- hooks.md now says it: "Not read at all, so the act runs with no grant: … an act an `eval` puts after a quoted operator". The ledger's "a cd inside eval not carried" is a different row.

**N24: medium. Pre-existing; D1's class; newly stated in judge.md, with no ledger line.** A symbolic link that a glob's wildcard matches is not followed, so the removal lands outside the repository under `delete **`.
- *Setup:* fx7.py; `link -> <F>/a/b/c/outside`, and `<F>/a/b/c/outside/x` exists.
- *Steps:* `rm -rf */x`, `rm -rf l*/x`, `find */x -delete` and `rm -rf */`.
- *Expected* (judge.md: "`**` … never reaches outside it"; `rm -rf link/x` asks, proposing `delete <F>/a/b/c/outside/x/**`): ask.
- *Observed:* allow at both commits. bash expands `*/x` to `link/x`, which lands at `<F>/a/b/c/outside/x`.
- `rm -rf */` would also take `g/` and `self/` in this fixture, which are links to the `.git` and to the root (inferred from rm's reading of a trailing slash; not run).
- judge.md states the reading ("`rm -rf lin*/x` reads as the root wherever `link` leads"), not its consequence.
- *Likelihood:* low to medium: `rm -rf */build` at a root with an outward link.
- *Severity:* this is the D1 form that D1's fix leaves: the link sits in the glob's wildcard part, not in its literal part. No earlier QA reported it.
  - QA-03 rated D1 high, when any path through a link was allowed.
  - I rate N24 medium, because it needs an outward link at the very level the wildcard matches. The Regent may weigh it as D1.

**N25: low. Pre-existing; newly stated in judge.md, with no ledger line.** A git act in a submodule's git folder runs in the submodule under this repository's `**`.
- *Setup:* a real submodule `sub` (file protocol), with `sub/u` modified.
- *Step:* `git -C .git/modules/sub reset --hard` under `discard **`.
- *Expected:* ask, as `git -C sub reset --hard` does.
- *Observed:* allow at both commits. `git -C .git/modules/sub rev-parse --show-toplevel` is `<proj>/sub`, and its status shows ` M u`. So the reset would discard the submodule's change (inferred; not run). Very low likelihood.

**Changed on purpose, prompts only, no id.** All are stated in judge.md; they are costs of the break (§6), not defects:
- Every root `find … -delete` asks, `-path ./.git -prune` forms included.
- `rm -f .git/index.lock` asks under `**`.
- `git -C .git checkout -- .` asks under `discard **`.

**Still open and unchanged, as the Regent decided:** N3, N4, N7, N9, N10, N14–N21, R6, D3, D4 and R1–R5.

**Seen in passing.**
- Every root proposal now ends with `<proj>/.git/**`. The known truncation of the ask's reason at 600 characters (`one_line`, hook_wire.py, outside the span; it has a ledger line) therefore reaches that path first, on a root with several nested repositories at long paths.
- That truncation fails closed: a grant made from a cut proposal does not cover the act.

## 4. Residual risk and coverage gaps

- **N22 is the class of the Regent's rule that remains.** It deletes the repository's own history under a `**` grant given for the repository. N24 deletes outside it, and N23 needs no grant at all.
- **Tests that would miss a regression** (mutations; the code is right today):
  - **G6:** if a root `.git` that is a file goes unseen, `rm -rf .`, `rm -rf .*` and `find . -delete` at a linked-worktree root turn into allows, and the suite stays 348/348. No case has a root whose `.git` is a file.
  - **G11:** if `in_own_git` reads the written path instead of where links land, `rm -rf g/objects` and `rm -rf g/` (with `g -> .git`) turn into allows, and the suite stays green. No case has a link inside the repository to its `.git`.
  - H12, J6, J7 and J12 still fail toward allowing. The PO placed the three J cases in N14's unit.
- **Cases to add**, each seen red under its mutation:
  - "a recursive removal at a root whose .git is a file asks" (G6);
  - "a removal through a link inside the repository to its .git asks" (G11);
  - and, with N22's fix, "rm -rf .[^.]* at the root asks".
- **Grant stores.** The suite's new cases use the session store only. I ran the round trip in the session, repo and machine stores; the named-file store (`JD-P`) was not tried.
- **Verification cost.**
  - Object Calisthenics rule 3: a glob is a bare string read by `fnmatch` in picker(), which both the nested search and the `.git` rule depend on.
  - A first-class "glob as bash expands it" (bracket negation, POSIX classes, the glob options of the line) would turn N15's and N22's family into one case.
  - The `.git` rule runs through three paths (`relative`/`in_own_git` for named paths, `own_git` for globs and recursion, `own_git_below` shared with `judge.py check`). Each needs its own case, which is why G6 and G11 slipped.

## 5. The hook's budget

Measured end to end on the stdin wire (a real process, Python start-up included), under `delete **`, warm cache:

| Tree (empty files, in a git repository) | 7fe5605 | 1c4fed2 |
|---|---|---|
| 26,064 folders, 208,512 files: `rm -rf .`, `git clean -fdx`, `git clean -ffdx`, a root `find`, `rm -rf t` (3 runs each) | 0.44–0.52 s | 0.45–0.55 s (`rm -rf .` and `find` now ask) |
| the same, four removals in one line | 1.62–1.66 s | 1.63–1.67 s |
| 150,000 folders, 1,500,000 files, same acts | 2.81–3.09 s | 2.81–3.10 s |

- On the large tree, at both commits, the search sometimes finishes before the 3 s deadline and sometimes not. `git clean -fdx` at 1c4fed2: 2 asks, 3 allows in 5 runs. An allow there is correct, because nothing is nested below.
- The `.git` rule adds no measurable time.
- At least 6.9 s of the 10 s timeout is left, and both limits fail closed.

## 6. Version verdict: BREAK

This covers the increment 7fe5605..1c4fed2.

**Earlier behaviour changed, by the Regent's `.git` decision:**
- `delete **`, and every relative glob, no longer cover:
  - `rm -rf .git`, or any path on or in it (`rm -f .git/index.lock`, `rm -rf .git/modules/…`);
  - `rm -rf .` or `find . … -delete` at the root, whatever the tests;
  - root globs that match `.git`.
- `*/**` no longer covers `.git/x`. `discard **` no longer covers `git -C .git checkout -- .`.
- `judge.py check delete .` now exits 1, and the Judge's proposals for root removals add `<proj>/.git/**`.
- Three inherited allow cases are retired for it.
- Consumers:
  - every `delete **` and relative-glob row in the session, repo (JD.md), machine and named-file stores;
  - workflows that clear `.git/index.lock`, or run `find . -name … -delete` or `rm -rf .` at the root under a grant;
  - callers of `judge.py check`;
  - the Judge's pop-up, which shows the proposals;
  - readers of judge.md §2 and hooks.md §2.

**The correction part.** The norm text now states what the code does (PO §3 points 1–8). D5 is fixed. QA-06 §4's cases are added; they are coverage only, with no behaviour change.

**Version number.** .claude-plugin/plugin.json still says 3.3 at 1c4fed2. The PO's §4 item 3 owes the move to 4.0 before the line leaves plumbing. It lies outside this attempt's span, and the number is the Regent's.

## 7. Not covered

- **zsh** (not installed), **Windows and macOS** (their `nt` branches, and a case-folding file system where `.GIT` is the `.git`).
- **A live Claude Code session.** Not covered: whether its shell snapshot sets `dotglob`, `GLOBIGNORE` or physical mode.
- **An unprivileged user**, **Python 3.8–3.10**, and **git versions other than 2.43**.
- **The budget beyond this container:** a cold cache, network file systems, slower machines.
- **The removals themselves.** Reach was shown by bash's `echo`, `git rev-parse` and `git clean -n`. `rm -rf */` through a link with a trailing slash is inferred, not run.
- **Glob options not fed:** `nocaseglob`, `extglob`, `failglob`/`nullglob` with an unmatched glob.
- **Acts that take the `.git` away without a removal**, which the guard's table does not hold: `mv .git …` (allowed under `layout **` at both commits; not tried with no grant), redirects or `truncate` into `.git`, `git gc --prune=now`, `git update-ref -d`, `git reflog expire`.
- **Other acts that reach nested repositories:** `git rm -r`, `rsync --delete`, `git submodule deinit -f`, `git worktree remove`.
- **The named-file grant store (`JD-P`)** for the new round trip.
- **hook-judge's pop-up** with the new proposals, beyond its own self-test.
- **CI for 1c4fed2** (only the local gate was given).
- **`touched_phases`.**
- **The backlog items**, beyond confirming they are unchanged.

## 8. Assumptions (TEAM §7.5)

- **Shell.**
  - Assumption: the agent's Bash runs bash, starts logical, and has no glob option set (`dotglob`, `GLOBIGNORE`).
  - If false: N22 widens to every `rm -rf *` at the root.
  - Validated by: the Regent's decision on physical mode. There is none for glob options.
- **git clean's reach.**
  - Assumption: git's dry run with the same flags shows what the act removes.
  - If false: N20's row and the round trip's git clean rows may reach more or less.
  - Validated by: a real run on a throwaway fixture, which the packet forbids.
- **Path resolution.**
  - Assumption: `rm` and `find` act on where the kernel lands a path with a link in a middle component (`link/x` → `outside/x`).
  - If false: N24 does not reach outside.
  - Validated by: POSIX path resolution. Not run here.

## 9. Verifiability line

**Signed for the criteria as written, with residual risk N22, N23, N24 (medium, pre-existing) and N25 (low, pre-existing).**
- Every criterion is met except two: the `.git` rule (N22) and the norm text's completeness claim, both partially met.
- No defect above low is introduced, and no compared row changed toward allowing.
- I do not declare the residue acceptable (QA §2). N22 risks losing the repository's own history in the very class the Regent decided is fixed in this attempt, and N23 and N24 risk losing data with no ledger line. So they go to the Regent (QA §12).
ARTEFACT>>>

**Escalation (TEAM §7.8)**
- **Trigger:** the line passes its criteria and introduces nothing above low. But silent allows remain that risk losing data (QA §12):
  - **N22:** in the class the Regent decided is fixed here. `rm -rf .[^.]*`, `.[[:alpha:]]*`, and `dotglob`/`GLOBIGNORE` forms delete the `.git` under `delete **`.
  - **N23:** an `eval` after a quoted operator runs with no grant at all.
  - **N24:** a glob through an outward link deletes outside the repository under `**`.
  - This attempt's own norm text states N23, N24 and N25, but no ledger line holds them.
- **Unresolved question:** does N22 go to the backlog beside N15 and N17, or back for an eighth attempt? And where do N23, N24 and N25 go?
- **Evidence:**
  - The risk opinion, §2–§5.
  - Probes in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa7/bin/: fx7.py, rt7.py, mut4.py, mutate7.py, reg7.sh, suite7.sh, tree7.py, time7.py.
  - Line files and tables in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa7/: git-lines-a.txt, git-a-7fe5605.txt, git-a-1c4fed2.txt, out-*-*.txt, n5-*.txt, n11-*.txt, gcl-*.txt, n14-*.txt, labels-*.txt, mutate7.txt, suite-all.txt, doctor-mine.txt, and reg-7fe5605/ and reg-1c4fed2/.
- **What I did:**
  - ran the full suite at both commits in two environments, and the changed self-tests on three Pythons;
  - re-ran doctor in a clone;
  - ran 44 mutations, and QA-06 §4's four on baseline code;
  - re-ran every QA-03/04/05/06 probe;
  - probed the `.git` rule in 82 lines, under six grants and with none, at a linked-worktree root and through a real submodule;
  - round-tripped the Judge's proposal in three stores;
  - measured the budget on two large trees.
- **Risk:** under a `delete **` grant for this repository:
  - `rm -rf * .[^.]*` at its root deletes its `.git` (N22);
  - `rm -rf */x` deletes through an outward link (N24);
  - with no grant, `eval true '&&' rm -rf src` runs (N23).
- **Decision needed from the Regent (one of):**
  - **A. Accept the line.** Record N22–N25 as known defects beside the backlog: N22 and N24 in guards-followups, and N23 in hazard-piped-shell (it is N21's class). Add G6's and G11's cases there, and ratify the reworded norm text.
  - **B. Return to DV for an eighth attempt (the Regent's word only).** At least N22, plus G6's and G11's cases.
  - **C. Hold on plumbing** until A or B.

EVENT VALIDATION_PASSED grant-latest QA risk-opinion
EVENT ESCALATION_STARTED grant-latest QA grant-glob-bash-reading

suba-validator envelope (checked with `python scripts/returns.py check --suba suba-validator -` over this whole message → "suba-validator: shape holds"):

```json
{
  "envelope": 1,
  "suba": "suba-validator",
  "via": "owner",
  "gov": {
    "order": "G1",
    "mode": "self",
    "element": "action",
    "from": "QA",
    "to": "QA",
    "key": "grant-glob-bash-reading",
    "ask": "sign the verifiability line of grant-latest attempt 7 with residual risk, and send to the Regent the data-loss residues left in the .git rule and the pre-existing silent allows this attempt's norm text names"
  },
  "body": {
    "verdicts": [
      {"criterion": "the Regent: ** stops short of the repository's own .git; a removal that reaches it (naming it, a path in or under it, recursion from a folder above) asks under ** and every relative glob", "verdict": "PARTIALLY MET", "evidence": ["64 lines that reach it under delete **: 57 allow at 7fe5605 and ask at 1c4fed2 (naming, path in it, links into it, cd, nested shells, eval, PowerShell, root recursion, every root find, fnmatch-matched globs)", "asks under the relative grant .git/** and at a linked-worktree root", "not met: rm -rf .[^.]*, * .[^.]*, .[[:alpha:]]*, shopt -s dotglob; rm -rf *, GLOBIGNORE=x; rm -rf *, shopt -s globstar dotglob; rm -rf ** allowed at both commits while bash expands each to include .git (N22)"]},
      {"criterion": "the Judge proposes the .git as a place of its own, and granting that covers the act", "verdict": "MET", "evidence": ["proposals delete <proj>/.git/** or the path in it, and delete ** <proj>/.git/** for a root recursion", "9 acts x session, repo and machine stores: granted as proposed, then allowed; neighbours opened only where the grant names them", "judge.py check delete answers as the guard does for 8 paths"]},
      {"criterion": "QA-grant-latest-06 section 4's four cases first, each red under its mutation before the change; N12's case also over a nested clone with no bare repository", "verdict": "MET", "evidence": ["7fe5605 code with 1c4fed2's self-test: the four green, red under H11, H15, H16, H17 respectively", "the four exclude forms also run in a clone-only fixture; H16, H13 and H21 turn them red"]},
      {"criterion": "judge.md section 2 and hooks.md section 2 state what the code does, point by point against the PO's section 3 (points 1-9, D5 included)", "verdict": "PARTIALLY MET", "evidence": ["points 1-9 each now stated as the code behaves; N17, N18, N19, N20, N15 stated; D5's paragraph matches SessionStart outside and inside a repository", "new statements true: dot-led relative globs cover nothing, lin*/x, eval after a quoted operator, a submodule's git folder, judge.py check", "not met: hooks.md's 'each place where this reader reads less or more than bash' omits dotglob, GLOBIGNORE, globstar and [[:class:]]; the [^...] limit is stated for the search only, not for the .git sentence (N22)"]},
      {"criterion": "the orchestrator's reading: N5's control holds except where the .git rule reaches the root's own .git (rm -rf . and find . -delete at the root now ask)", "verdict": "MET", "evidence": ["of N5's six steps with no repository below, only rm -rf . and find . -delete change; git clean -fdx and -ffdx stay allowed", "wider than the two examples: every root recursion and every root find whatever its tests now asks, as judge.md states"]},
      {"criterion": "what attempts 4 to 6 fixed keeps its verdict: D1, D2, N1, N2, N5's six steps, N8, N11, N12, N13", "verdict": "MET", "evidence": ["hz, ex, cdl, sib, stack rows identical at both commits except the two .git rows", "QA-06's n11 (49) and gc (42) rows identical"]},
      {"criterion": "N3, N4, N7, N9, N10, N14-N21, R6, D3, D4, R1-R5 not fixed and not made worse", "verdict": "MET", "evidence": ["n14, ex, hz, ko, eacces rows identical; N15 fed on the wire, allowed at both; N20 and N21 allowed at both", "files of D4, R1, R2, R5 untouched"]},
      {"criterion": "criticality high: no open defect above low introduced by the unit", "verdict": "MET", "evidence": ["every compared row that changed went allow to ask, by the rule", "N22, N23, N24, N25 allowed at 7fe5605 too"]},
      {"criterion": "regression: the line as QA-06 verified it still holds except where the .git rule changes it; the inherited suite is no worse", "verdict": "MET", "evidence": ["33 self-tests green at both commits in two environments; 3.11 and 3.12 green; doctor in a clone identical to the gate log", "three inherited allow labels retired, each turned to ask by the rule and back as an ask case; the retirement unrecorded in the change notes"]},
      {"criterion": "the hook's budget: timeout 10 s, onFailure block", "verdict": "MET", "evidence": ["stdin wire, warm cache: 0.45-0.55 s on 208,512 files, 2.81-3.10 s on 1,500,000 files at both commits", "hooks.json unchanged for Bash and PowerShell"]}
    ],
    "risk": {
      "measured": [
        {"surface": "a root glob bash expands to include .git and the reader does not (N22)", "consequence": "the repository's own .git deleted, with its unpushed history, under a delete ** grant", "likelihood": "low: .[^.]* is a common dotfile spelling; dotglob is rare", "detectability": "none at the time: the guard is silent", "uncertainty": "whether the agent's shell sets a glob option"},
        {"surface": "an act an eval puts after a quoted operator (N23)", "consequence": "rm or git reset --hard runs with no grant at all", "likelihood": "low: an unusual spelling", "detectability": "none at the time", "uncertainty": "whether an agent types it"},
        {"surface": "a glob whose wildcard matches an outward link (N24)", "consequence": "a removal outside the repository under delete **", "likelihood": "low to medium: rm -rf */build at a root holding an outward link", "detectability": "none at the time", "uncertainty": "rm's reading of a trailing slash on a link, not run"}
      ],
      "missing": []
    },
    "findings": [
      {"key": "grant-glob-bash-reading", "status": "recurring", "baseline": "7fe5605 on the fx7 fixture and the same lines", "type": "claim not met: a glob bash expands to a protected place, read by the reader as not reaching it (N15's cause), here the repository's own .git under **", "severity_input": "medium: history of the repository lost, observed by bash's own expansion, low likelihood (N22)", "priority": "the Regent's: backlog or an eighth attempt", "acts_next": "RGN"},
      {"key": "hazard-piped-shell", "status": "recurring", "baseline": "7fe5605 and 1c4fed2 alike, with no grant", "type": "guard blind spot: an act after a quoted operator in eval is not read", "severity_input": "medium: a removal runs with no grant, outside this unit (N23)", "priority": "backlog beside N21, for the PO", "acts_next": "RGN"},
      {"key": "grant-glob-symlink-escape", "status": "recurring", "baseline": "7fe5605 on the fx7 fixture; D1 in QA-grant-latest-03", "type": "guard coverage wider than its grant: a removal outside the repository allowed through a link a glob's wildcard matches", "severity_input": "medium: D1's class (rated high at QA-03), needs an outward link at the level the wildcard matches; observed by bash's own expansion (N24)", "priority": "the Regent's: backlog or an eighth attempt", "acts_next": "RGN"},
      {"key": "grant-nested-descent", "status": "recurring", "baseline": "7fe5605 on a real submodule", "type": "claim not met: a git act in a submodule's git folder read as this repository's", "severity_input": "low: very unlikely spelling, a submodule's uncommitted change (N25)", "priority": "later unit", "acts_next": "RGN"}
    ],
    "not_covered": ["zsh", "Windows and macOS, and a case-folding .GIT", "a live Claude Code session's shell snapshot and glob options", "an unprivileged user", "Python 3.8 to 3.10", "git versions other than 2.43", "the budget on a cold cache, network file systems or slower machines", "the removals themselves (bash echo, rev-parse and git clean -n stand for them)", "nocaseglob, extglob, failglob and nullglob", "acts that take the .git away without a removal (mv, redirects, truncate, git gc --prune, update-ref -d, reflog expire)", "git rm -r, rsync --delete, submodule deinit, worktree remove", "the named-file grant store", "hook-judge's pop-up beyond its self-test", "CI for 1c4fed2", "touched_phases"],
    "ambiguities": []
  },
  "doubts": [
    {"doubt": "Does N22 go to the backlog beside N15 and N17 (yes), or back to DV for an eighth attempt (no)?", "key": "gap-residue-disposal", "decides": "RGN"}
  ],
  "artefacts": ["risk-opinion"],
  "terminal": {"state": "ESCALATED", "why": "the line passes its criteria with nothing above low introduced, but a data-loss residue remains in the .git rule the Regent decided is fixed here, and the attempt's norm text names pre-existing silent allows no ledger line holds; only the Regent can dispose them"}
}
```

Terminal state: **ESCALATED**. The line passes its criteria as written and introduces nothing above low. But N22 is a data-loss residue in the very rule the Regent decided is fixed in this attempt. N23 and N24 are pre-existing data-loss allows that the attempt's own norm text names and no ledger line holds. The line is past T4, so only the Regent can accept them as backlog or return the line (QA §12).