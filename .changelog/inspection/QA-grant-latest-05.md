I'm refusing this line and sending it to the Regent. N1, N2 and N8 are fixed as I wrote them, and D1 and D2 still ask. But the new logical `cd` brings in one silent allow, N11: after `set -P` in the line, a removal outside the repository now runs under `delete **`, where it asked before. N5 is fixed for its named steps but not for two git clean forms (N12, N13). Version verdict: **break**.

<<<ARTEFACT risk-opinion
# Risk opinion: unit grant-latest, QA verify, attempt 5

**Verdict in one line.** N1, N2 and N8 are fixed as I wrote them, and D1 and D2 still ask. The logical `cd` that fixes them brings in one regression in D1's class (N11). N5 is met for its six steps and every other removal form I tried. It is not met for git clean with an exclude pattern (N12), or with a single `-f` over a bare repository (N13). I refuse the verifiability line, and the decision goes to the Regent. Version verdict: **break**.

**What was tested.**
- Branch plumbing at 63cd097. The change is `git diff c392858 63cd097`: four files, all inside the span.
- dv-guards5.diff is byte-identical to that diff. The surface diff (registry.json, hooks.json) is empty.
- c392858 differs from 9fbb2c1, where QA-04 verified the line, only in `.changelog/` and the ledger. So c392858 is the regression baseline.
- A usage limit cut the run on 2026-11-23, and it resumed on 2026-11-25. Plumbing stayed at 63cd097 with a clean tree throughout.

**What I read.**
- criteria-guards5.md, the change notes, dv-guards5.diff and gate-guards5-local.txt.
- File contents at both commits.
- QA-grant-latest-04.md and QA-grant-latest-03.md, with their probes.
- Not read: git log, commit messages, CHECKPOINT and HISTORY, and every other file in the scratch folder.

**Change notes, checked against the diff.**
- `touched_paths` match the diff, and `surface_changed: false` matches the empty surface diff.
- Rollback is named.
- The 11 `new_tests` names map to the 31 new hook-hazard cases and the 2 new judge cases (5+4+3+2+8+6+1+1+1 and 1+1).
- The notes argue nothing.
- `touched_phases` is empty and was not checked: no phase reference was given.

**Environment.**
- A Linux container, run as root, with git 2.43.0 and Python 3.13 (3.11 and 3.12 also present). The session sets GIT_CONFIG_*.
- Probes ran on `git archive` exports of both commits and on throwaway fixtures under my scratch folder, with TMPDIR and HOME pointed there.
- No removal, reset, clean or push was run for real. Where an act lands was shown with `pwd -P`, `readlink -f` and `git rev-parse`. What git clean reaches was shown only by its own dry run (`git clean -n …`), which removes nothing.
- /home/user/regency ends clean, on plumbing at 63cd097, with no stash. I committed nothing.

**Criticality assumed.** High, with a tolerance of no open defect above low introduced by the unit (criteria-guards5). The Regent has stated nothing else.

## 1. Gate and inherited suite

| Check | Result |
|---|---|
| doctor at 63cd097, re-run by QA in a throwaway clone | 0 FAIL, 30 WARN, HEALTHY. The OK lines are identical to gate-guards5-local.txt |
| 33 self-tests (those doctor runs), at c392858 and 63cd097, in the session environment and in a cleared one | All green. hook-hazard went from 248 to 279 cases and judge from 84 to 86; every other count is unchanged |
| hook-hazard, judge and hook-judge on Python 3.11 and 3.12 | 279/279, 86/86 and 10/10 |
| inherited case labels in hook-hazard, judge, hook-judge, hook-verbs and hook-refs, compared at runtime | None lost; 31 + 2 added. guard-push.py, hook-refs.py, hook_wire.py, hook-resume.py, hook-verbs.py, hook-judge.py and hooks.json are untouched by the diff |
| named tests are real | 20 mutations, each removing one part of the fix in a fresh copy. 17 turn their cases red: the logical `cd`, 10; canonical's folder check, 1; `cd -P`, 1; nothing reached, 11; `rm` never recursive, 6; a second `-f` never read, 3; the glob's wildcard part, 1; no `**` beside, 1; no deadline passed, 1; `find` reaching nothing, 2; and five judge mutations (going on below a found repository, following links, entering `.git`, the own `.git`, no `check` search), 1 each. Ignoring the deadline turns 2 red. An uncaught scandir error crashes hook-hazard's self-test. **Three turn nothing red:** the glob's dot rule; the early return for a path outside; and `check` refusing a timed-out search. All three fail toward asking |
| stdin wire (hook-hazard.py fed the event, a real process) | N1's first step, N2's first step and `git clean -ffdx` ask. N8's step is allowed. N12's `git clean -ffdx -e keep` and N13's `git clean -fdx` are allowed |

## 2. Verdict per criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| N1 as QA-04 wrote it: under `discard`, `history` and `delete **`, the five `cd current … ../../sibling` git acts ask | MET | sib.py on the sib fixture: 5 × allow at c392858, 5 × ask at 63cd097, and the first step on the wire too. The `side` push asks now (stack.py). bash lands in `sibling` (`pwd -P`), whose status shows ` M a`. Also asking now: `pushd` forms, a trailing slash, `./current/…`, a quoted target, `;` chains, a three-step chain, `cd current/.. && git -C ../sibling …`, `bash -c '…'`, `cd -L`, and `Set-Location` |
| N2 as QA-04 wrote it: `cd current && cd .. && rm -rf cache/*`, `cd current/.. && rm -rf cache/precious` (`delete **`) and `cd current && cd ../cache && git reset --hard` (`discard **`) ask | MET | cdl.py: 3 × allow at c392858, 3 × ask at 63cd097. Also asking now: `find cache/ -delete`, `pushd` forms, `cd ../cache/ && rm -rf *`, `git -C cache …` after the chain, and `cd current/../cache`. `cd current && cd .. && rm -rf src` stays allowed |
| N8 as QA-04 wrote it: `cd link/.. && rm -rf build` and `cd link && cd .. && rm -rf build` are covered by `delete **` | MET | ex.py row L: ask at c392858, allow at 63cd097, and on the wire too. bash is in `proj` (`pwd -P`). **Side effect: N11** |
| N5 as the Regent reads it: a recursive act that reaches a repository nested below a folder it names asks, and the same acts with no repository below stay as they were | PARTIALLY MET | Met for the six steps (ex.py row F: 6 × allow at c392858, 6 × ask at 63cd097). Also met for `/bin/rm`, `--recursive`, `-r -f`, `-Rf x/`, `./*`, `x/lib/..`, `find … -exec rm`, `find -L`, `-mindepth`, `bash -c`, `sudo`, `rd /s`, `cd x && rm -rf .`, `pushd x && rm -rf *`, and PowerShell `Remove-Item`/`ri` in five forms (tool PowerShell). The Judge's proposal, granted, covers the act; `rm -rf src`, `find src -delete` and `Remove-Item -Recurse docs` stay covered. `judge.py check delete` answers as the guard does (`.` and `tmp` exit 1, `src` exit 0). **Not met:** git clean with an exclude pattern (N12); a single `-f` over a bare repository (N13); a negated bracket glob (N15, inferred). **Not as they were:** a folder that only looks like a bare repository (N14) |
| D1 and D2 (QA-03) keep asking | MET | hz.py rows identical at both commits: D1's four steps and D2's three steps ask |
| N3, N4, N7, N9, N10, R6, D3, D4, D5 and R1–R5: neither fixed nor made worse | PARTIALLY MET | N3, N4, N7, R6 and `git submodule foreach` give the same ex.py rows at both commits. N10 gives the same simulated result (eacces5.py). D3, R3 and R4 give the same hz.py and ko.py rows. The files of D4, D5, R1, R2 and R5 are untouched; D5's paragraph of hooks.md is outside the changed hunk. **N9 is made wider: N14** |
| Regression: the line as QA-04 verified it at 9fbb2c1 still holds, except where N1, N2, N8 and N5 change it on purpose, and the inherited suite does not get worse | PARTIALLY MET | The suite holds (§1). Every ex.py, cdl.py, sib.py, hz.py and ko.py row is unchanged except those of N1, N2, N8 and N5. W1 is still allowed, and `git -C current/../../sibling …` is still allowed (git refuses: "cannot change to"). **Two acts changed that were not meant to:** N11 (an ask became an allow) and N14 (allows became asks) |
| Criterion 4: the drafted judge.md §2 and hooks.md §2 state what the code does | PARTIALLY MET | Clause by clause below |
| D1/D2's norm: "`**` … never reaches outside it"; "a git act is judged where it runs" | PARTIALLY MET | Met for every N1 and N2 form above. Not met under `set -P`/`set -o physical` (N11) |
| The hook's budget: hooks.json runs it with `"timeout": 10` and `"onFailure": "block"` | MET (this machine, warm cache) | §5. At most 3.08 s end to end on the wire, including on 1.5 M files. hooks.json is unchanged |

**Clause by clause (criterion 4).**

judge.md §2:
- **"A `cd` (`pushd`, `Push-Location`) … moves the shell as bash moves it: logically … where bash's own reading finds no folder, and under `cd -P`, it lands where the file system does."** The code does this: canonical() checks a folder before each `..`, then falls back to the file system's landing, and `cd -P` is read with the last of `-L`/`-P` winning. **The text states more than the code:** under `set -P` or `set -o physical`, bash moves physically and the code does not (N11). hooks.md names this exception ("Not read"); judge.md does not.
- **"A recursive removal (`rm -r`, `find`, `Remove-Item -Recurse`, `rd /s`, `del /s`, `git clean` with a second `-f`) … also acts on every repository nested below it."** Met for the listed forms, except git clean with an exclude pattern given as its own word (N12). **The text states less than git does:** git clean removes an untracked bare repository with one `-f`, and needs the second only for one holding a `.git` (N13; git-clean(1) and its dry run).
- **"Each is a place of its own … the Judge proposes each beside the act's own place, and an act that names no path still needs `**` too."** Met: the self-test round trip, and the proposals in the ex.py and gc fixtures, `delete ** <proj>/tmp/clone/** <proj>/vendor.git/**`.
- **"A glob reaches the folders its wildcard part matches, as a shell expands it."** Only the first wildcard part filters, so deeper parts are searched whole; that asks more, never less. `[^…]` is read unlike bash (N15). **The text states more than the code.**
- **"The search below follows no link, enters no `.git`, passes a folder its user cannot read … and ends at each repository it finds; one that runs past 3 seconds places nothing, so the act asks."** Met, by mutations, eacces5.py and §5. The parenthesis "(the act cannot go below it either)" does not hold under `sudo`/`doas`, which the reader strips (N16, inferred).
- **"`judge.py check delete` looks below its paths the same way."** Met.

hooks.md §2:
- **"git's global `-C` moves as git does, where the file system lands it."** Met.
- **"A recursive removal (… `git clean -ff`) also reaches every repository nested below a folder it names … stops after 3 seconds, when the act asks."** Met, except N12 and N13 (as above).
- **"The search took 0.45 s over 26,064 folders and 200,036 files on Linux; 1.4 million files run past its 3 seconds."** Consistent with my second measure on this machine: 0.59–0.68 s end to end on 26,064 folders and 208,512 files, and past 3 s on 1.5 M files (§5).
- **"Not read: `set -P` or `set -o physical` …, PowerShell's own reading of a `..` in a path, and git's `--recurse-submodules`."** Accurate. It does not say that the first one now lets a removal outside the repository run silently (N11). `Set-Location` is read the bash way; whether PowerShell moves that way is not covered.

## 3. Open defects, by severity

**N11: medium. A regression introduced by this attempt, in D1's class (data loss outside the repository possible).** After `set -P` or `set -o physical` in the line, a `cd` through an outward link and back is read logically, while bash moves physically.
- *Setup* (fx.py): `proj` is a git repository with `link -> <D>/a/b/c/outside`, where `<D>/a/b/c/x` exists. Session grant: `delete **`.
- *Steps:* PreToolUse Bash with cwd `proj`, each of:
  - `set -P; cd link && cd .. && rm -rf x`
  - `set -o physical; cd link && cd .. && rm -rf x`
- *Expected* (judge.md §2: "`**` … never reaches outside it"; a `cd` moves as bash moves it): ask.
- *Observed:*
  - **Allow at 63cd097, both. Ask at c392858, both**, which proposed `delete <D>/a/b/c/x/**`.
  - bash under `set -P`: `cd link && cd ..` leaves `pwd` at `<D>/a/b/c`, outside the repository. The removal would land at `<D>/a/b/c/x`; this is inferred, since nothing was run.
  - Without `set -P`, the same line is N8's and is rightly allowed. `cd -P link && cd .. && rm -rf x` asks at both commits.
- *Cause (INFERRED, not the reported defect):* the reader reads `cd -P` but not `set -P`/`set -o physical`. hooks.md names this as "Not read"; judge.md does not.
- *Wider if* the agent's shell starts with `set -o physical` from the Regent's profile: then every `cd <outward link> && cd .. && <relative removal>` deletes outside, silently (assumption §8).
- *Evidence:* why.py and fx.py, on fixture frm. Not caught by any case in the suite.

**N12: medium. Pre-existing (allowed at c392858 too); a residue of N5, which the Regent decided is fixed in this attempt.** git clean with an exclude pattern given as its own word is searched only below the pattern.
- *Setup* (fixture gc): `proj` is a git repository. Untracked in it: `tmp/clone` (a `git init`), `vendor.git` (a `git init --bare`), `keep/`, `src/f` and `x.log`. Session grant: `delete **`.
- *Steps:*
  - `git clean -ffdx -e keep`
  - `git clean -ffdx -e '*.log'`
  - `git clean -ffdxe keep`
  - `git clean -ffdx --exclude keep`
- *Expected* (the Regent's N5 reading; judge.md §2 on git clean with a second `-f`): ask.
- *Observed:*
  - Allow at both commits, and on the wire.
  - git's dry run, `git clean -n -ffdx -e keep`: "Would remove src/, tmp/, vendor.git/, x.log". The removal takes the clone and the bare repository.
  - These ask: `git clean -ffdx`, `--exclude=keep` and `-e keep -- .`.
- *Cause (INFERRED):* the pattern after `-e`/`--exclude` is read as a path to clean, so the search looks only below it.

**N13: medium. Pre-existing; a residue of N5. A named case pins it.** git clean with a single `-f` removes an untracked bare repository in the work tree, and is allowed.
- *Setup:* the gc fixture.
- *Step:* `git clean -fdx` under `delete **`.
- *Expected* (the Regent's reading lists "a bare repository"): ask.
- *Observed:*
  - Allow at both commits, and on the wire.
  - `git clean -n -fdx`: "Would skip repository tmp/clone", "Would remove vendor.git/".
  - The new case "and a removal that reaches no repository below stays covered: git clean -fdx" runs in a fixture that holds `vendor.git`, built as "a bare repository in the work tree". The suite therefore asserts the allow as correct.
  - The drafted norm names only "a second `-f`".

**N14: low. Introduced; it widens N9.** A plain folder holding `HEAD`, `objects/` and `refs/`, which git does not read as a repository, now makes every recursive removal above it ask.
- *Setup:* `data/HEAD` (holding "not a repo"), `data/objects/` and `data/refs/`, and no repository below. `git -C data rev-parse --git-dir` answers `proj/.git`.
- *Steps* under `delete **`: `rm -rf .`, `rm -rf *`, `find . -delete`, `git clean -ffdx`.
- *Expected* (the Regent: "the same acts on a folder with no repository below it stay as they were"): allow.
- *Observed:* allow at c392858; ask at 63cd097, proposing `delete ** <proj>/data/**`.
- It asks more, never less.

**N15: low. Pre-existing. The mechanism is observed; the verdict is inferred.** A negated bracket glob `[^…]` is matched by Python's fnmatch as a literal `^`.
- In bash, `[^v]*` expands to `src`.
- fnmatch translates it to `[\^v].*`: `src` is not picked and `vendor` is.
- So a recursive removal written `[^v]*` over a clone in `src` is not searched below `src`, and `delete **` would cover it (INFERRED). `[!v]*` agrees with bash.
- The harness's safety check refused the probe that fed this line to the hook, and I did not re-issue it in any form.

**N16: low. Inferred, not run.**
- Under `sudo` or `doas`, the search still passes a folder the hook's user cannot read. The reader strips `sudo`, but root's `rm -r` can go below that folder.
- Simulated: with scandir raising EACCES on `data/db`, `rm -rf data` is allowed under `delete **` (eacces5.py).
- Not reproduced as a real unprivileged user, because this container runs as root.

**Still open and unchanged, as the Regent decided:** N3, N4, N7, N9 (widened by N14), N10, R6, D3, D4, D5 and R1–R5.

**Seen in passing, the same at both commits:**
- For `rd /s /q vendor`, the Judge proposes `delete /s /q vendor/** …`: the switches are read as paths.
- A DeprecationWarning at hook-hazard.py:133 (it was :129).
- `find -L` with an outward link was not probed.

## 4. Residual risk and coverage gaps

- **N11 is the cost of reading `cd` logically when the shell reads it physically.** The in-line form can be read from the text, as `cd -P` already is. The profile form cannot be known to a hook.
- **N12 and N13 are what remains of N5.** Both are git clean forms a reset-minded agent types. They delete a nested repository's unpushed history under a grant given for this one.
- **The three untested parts** (§1, mutations) all fail toward asking.
- **Large trees.** Where the search runs past 3 s (about 1.4 M files and up, on this machine), every recursive removal from the root asks, and no grant can cover it. The reason it gives ("No script can tell where it lands") does not say that time ran out.
- **Only the session store tested.** The new cases ran against session grants only. The other stores go through the same `covers()`, so the same result there is inferred.
- **Verification cost.** Object Calisthenics rules 3 and 4 apply.
  - `act_paths` now returns one raw list that mixes `Path`, `None` (unplaceable) and the string `"**"` (judge.ALL). Both `covers()` and `propose()` special-case it.
  - git clean's option grammar is parsed again by hand, and `-e` taking a value is missed (N12).
  - A first-class reach value (named places, reached repositories, needs-`**`, unknown) would turn N12's family into one case. So would a table of git clean's value-taking options.
- **Cases to add to the coherence matrix** (QA writes no files here). Each must be seen red at 63cd097:
  - "git clean -ff with an exclude pattern over a nested clone asks";
  - "git clean -f over an untracked bare repository in the work tree asks". The new allow case for `git clean -fdx` then needs a fixture with no bare repository;
  - "set -P, then a cd through an outward link and back, then a removal: asks".

## 5. The hook's budget

Measured end to end on the stdin wire (a real process, Python start-up included), under `delete **`, with a warm cache:

| Tree (empty files, no repository below) | c392858 | 63cd097 |
|---|---|---|
| 26,064 folders, 208,512 files: `rm -rf .` (3 runs) | 0.06–0.08 s, allow | 0.59–0.68 s, allow |
| one folder of 1,000,000 files: `rm -rf .` (3 runs) | 0.07 s, allow | 0.85–0.91 s, allow |
| 150,000 folders, 1,500,000 files: `rm -rf .` (3 runs) | 0.08 s, allow | 3.06–3.08 s, ask ("No script can tell where it lands") |
| three recursive acts in one line (small, flat and big trees) | — | 1.89 s, 2.15 s and 3.08 s: one deadline is shared |

That leaves at least 6.9 s of the 10 s timeout here, and a timed-out search fails closed.

## 6. Version verdict: BREAK

This covers the increment c392858..63cd097.

**The correction part.** Three silent allows of D1's and D2's class now ask, as the norm already promised: N1, N2 and their variants. N8's needless prompt is gone.

**Earlier behaviour also changed, by the Regent's N5 reading:**
- A `delete **` grant no longer covers `rm -rf vendor`, `rm -rf .`, `find . -delete` or `git clean -ffdx` when a repository is nested below.
- Where the search runs past 3 s, no grant covers such an act at all.
- N14 adds asks.
- `judge.py check delete` changes its exit code from 0 to 1 and its proposal text for those paths.
- Consumers: every `delete **` row in session, JD.md, machine and named-file stores; workflows that clean trees holding vendored clones or bare repositories; readers of `check`'s exit code.

**A widening.** N11, the `set -P` form.

**Norm and version.** judge.md §2 and hooks.md §2 are agent-drafted text, and ratifying them is the Regent's call. The version is still 3.3; the number is the Regent's.

## 7. Not covered

- **Windows and macOS.** Also unverified:
  - realpath over junctions;
  - case folding (`.GIT`);
  - the `nt` branches;
  - `rd /s` and `del /s` under a real cmd;
  - `/tmp -> /private/tmp`.
- **A live Claude Code session.** Not covered:
  - whether the event's `cwd` is logical or physical;
  - whether the Bash tool's shell carries `set -o physical` from a profile;
  - PowerShell's own `Set-Location` reading. Only its events were fed to the hook.
- **The budget beyond this container:** a cold cache, network or slow file systems, slower machines. A single folder's listing is not interrupted by the deadline.
- Python 3.8–3.10 (not installed).
- The destructive acts themselves. Landing was shown read-only, and git clean's reach by its own dry run.
- **Fed to the hook only as inferences:**
  - N15's line (the harness refused the probe);
  - N16 as a real unprivileged user.
- Grant stores other than the session store, for the new cases.
- CI for 63cd097 (only the local gate was given).
- **Other acts that reach nested repositories, not probed:** `git rm -r`, `rsync --delete`, `mv` over one, `git submodule deinit -f`, `git worktree remove`, `git stash drop`, `find -L` through an outward link.
- The backlog items beyond confirming they are unchanged.

## 8. Assumptions (TEAM §7.5)

- **Criticality.**
  - Assumption: high, with no open defect above low introduced by the unit.
  - If false: at normal criticality, N11 could be accepted as a known defect.
  - Validated by: the Regent stating criticality.
- **Shell.**
  - Assumption: the agent's Bash runs bash with the default logical `cd`, and nothing in its profile sets `set -o physical`.
  - If false: N11 is not limited to lines that write `set -P`. Every `cd <outward link> && cd .. && <relative removal>` deletes outside, silently.
  - Validated by: the Regent's shell profile, or the Bash tool's shell snapshot.
- **git clean's reach.**
  - Assumption: git's dry run with the same flags shows what the act removes (git-clean(1)).
  - If false: N12 and N13 may reach less than shown.
  - Validated by: a real run on a throwaway fixture, which the packet forbids here.

## 9. Verifiability line

Refused. N11 is a defect introduced by the unit, above the assumed tolerance, and in a data-loss class (QA §12). N5 is only partially met (N12 and N13). This attempt already runs past T4 on the Regent's word, so the next step is the Regent's.
ARTEFACT>>>

**Escalation (TEAM §7.8)**
- **Trigger:** N11. The attempt turns a removal outside the repository that asked at c392858 into a silent allow under `delete **`, when `set -P` or `set -o physical` comes earlier in the line. This is data-loss class (QA §12), on a line already past T4. Beside it, N12 and N13 leave N5, which the Regent decided is fixed here, partly open.
- **Unresolved question:** may the guards line stay as it is with N11–N13 open, or does it go back for a sixth attempt?
- **Evidence:**
  - Risk opinion §3 and §5.
  - Probes in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa5/bin/:
    - fx.py, why.py, whyps.py and wire.sh (N11–N14, the stdin wire);
    - eacces5.py (N10, N16);
    - tree.py (§5);
    - mutate5.py;
    - suite5.sh;
    - QA-04's sib.py, stack.py, cdl.py, ex.py, hz.py and ko.py, re-run as they were.
  - My doctor re-run: /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa5/doctor-mine.txt.
  - The mutation results: /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa5/mutate5.txt.
- **What I did:**
  - ran the full suite at both commits, in two environments and on three Pythons;
  - re-ran doctor in a clone;
  - mutated each part of the fix;
  - re-ran every QA-03 and QA-04 probe;
  - probed N1, N2, N5 and N8 beyond their steps;
  - measured the budget on three large trees;
  - showed landing read-only and git clean's reach by its dry run.
- **Risk:**
  - Under a `**` grant for this repository, `set -P; cd <outward link> && cd .. && rm -rf x` deletes outside it (N11).
  - Also under a `**` grant, `git clean -ffdx -e <pattern>` and `git clean -fdx` delete nested clones or bare repositories (N12, N13).
- **Decision needed from the Regent (one of):**
  - **A. Accept.** Record N11–N16 as known defects, beside the backlog. Ratify or reword the drafted norm text, and choose the version.
  - **B. Return to DV for a sixth attempt (the Regent's word only).** At least N11, N12 and N13.
  - **C. Hold on plumbing** until A or B.
- **Doubt (closed):** does the agent's shell on your machines ever start with `set -o physical` (or `set -P`) from your profile? Yes or no.

EVENT VALIDATION_FAILED grant-latest QA grant-cd-physical-option
EVENT ESCALATION_STARTED grant-latest QA risk-opinion

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
    "key": "grant-cd-physical-option",
    "ask": "sign or refuse the verifiability line of grant-latest attempt 5, with a regression introduced in D1's class and N5 partly open"
  },
  "body": {
    "verdicts": [
      {"criterion": "N1 as QA-grant-latest-04 wrote it: the five cd current ... ../../sibling git acts ask under discard, history and delete **", "verdict": "MET", "evidence": ["sib.py: 5 x allow at c392858, 5 x ask at 63cd097; the first step on the stdin wire asks", "stack.py: the side push asks", "pushd, trailing slash, quoted, ';', three-step, bash -c, cd -L and Set-Location variants ask"]},
      {"criterion": "N2 as QA-grant-latest-04 wrote it: cd current && cd .. && rm -rf cache/*, cd current/.. && rm -rf cache/precious, cd current && cd ../cache && git reset --hard ask", "verdict": "MET", "evidence": ["cdl.py: 3 x allow at c392858, 3 x ask at 63cd097", "find, pushd, glob and -C variants ask; cd current && cd .. && rm -rf src stays allowed"]},
      {"criterion": "N8 as QA-grant-latest-04 wrote it: cd link/.. && rm -rf build and cd link && cd .. && rm -rf build are covered by delete **", "verdict": "MET", "evidence": ["ex.py row L: ask at c392858, allow at 63cd097, and on the wire", "bash is in proj (pwd -P)"]},
      {"criterion": "N5 as the Regent reads it: a recursive act reaching a repository nested below a folder it names asks; the same acts with no repository below stay as they were", "verdict": "PARTIALLY MET", "evidence": ["ex.py row F: 6 x allow at c392858, 6 x ask at 63cd097; rm, find, sudo, bash -c, rd /s and PowerShell Remove-Item forms ask", "not met: git clean -ffdx -e keep and --exclude keep allowed while git's dry run removes a clone and a bare repository (N12)", "not met: git clean -fdx allowed while its dry run removes an untracked bare repository (N13)", "not as they were: a bare-shaped plain folder makes rm -rf . ask (N14)"]},
      {"criterion": "D1 and D2 (QA-grant-latest-03) keep asking", "verdict": "MET", "evidence": ["hz.py rows identical at c392858 and 63cd097: D1's four and D2's three steps ask"]},
      {"criterion": "N3, N4, N7, N9, N10, R6, D3, D4, D5, R1-R5 neither fixed nor made worse", "verdict": "PARTIALLY MET", "evidence": ["ex.py, hz.py, ko.py and eacces5.py rows unchanged for N3, N4, N7, N10, R6, D3, R3, R4", "files of D4, D5, R1, R2, R5 untouched", "N9 widened: every recursive removal above a bare-shaped plain folder now asks (N14)"]},
      {"criterion": "regression: the line as QA-grant-latest-04 verified it at 9fbb2c1 holds except where N1, N2, N8 and N5 change it on purpose; the inherited suite does not get worse", "verdict": "PARTIALLY MET", "evidence": ["33 self-tests green at both commits in two environments; no inherited label lost; doctor re-run 0 FAIL with OK lines identical to the gate log", "set -P; cd link && cd .. && rm -rf x: ask at c392858, allow at 63cd097 (N11)", "bare-shaped plain folder: allow at c392858, ask at 63cd097 (N14)"]},
      {"criterion": "criterion 4: judge.md §2 and hooks.md §2 as drafted state what the code does", "verdict": "PARTIALLY MET", "evidence": ["code matches: logical cd with the file system's fallback and cd -P, -C physical, the listed recursive forms, the search's limits, the Judge's proposals, check delete", "judge.md states more than the code: 'as bash moves it' without the set -P exception (N11); 'as a shell expands it' for [^...] (N15); 'the act cannot go below it either' under sudo (N16)", "both state less than git: git clean removes a bare repository with one -f (N13)"]},
      {"criterion": "the hook's budget: timeout 10 s, onFailure block", "verdict": "MET", "evidence": ["stdin wire, warm cache: 0.59-0.68 s on 208,512 files, 0.85-0.91 s on a 1,000,000-entry folder, 3.06-3.08 s and ask on 1,500,000 files; one deadline shared across a line", "hooks.json unchanged"]}
    ],
    "risk": {
      "measured": [
        {"surface": "a logical reading of cd under set -P or set -o physical, through an outward link and back (N11, introduced)", "consequence": "rm -rf of a path outside the repository runs under a delete ** grant for this one", "likelihood": "low: needs set -P or set -o physical, an outward link, a cd through it and back, and a ** grant", "detectability": "none at the time: the guard is silent", "uncertainty": "whether the Regent's shell profile sets physical mode, which would widen it to every such cd chain"},
        {"surface": "git clean with an exclude pattern or a single -f over nested repositories (N12, N13, pre-existing)", "consequence": "a nested clone or an untracked bare repository deleted with its unpushed history", "likelihood": "medium for N12: -e keeps are common in clean-up lines; low for N13: a bare repository in a work tree is rare", "detectability": "none at the time", "uncertainty": "git's dry run stands for the act; nothing was removed for real"}
      ],
      "missing": ["the Regent's or the PO's criticality and maximum tolerable severity for this unit, still assumed high with tolerance low"]
    },
    "findings": [
      {"key": "grant-cd-physical-option", "status": "regression", "baseline": "c392858 (= 9fbb2c1 code) on the same fixture and commands", "type": "guard coverage wider than its grant: a removal outside the repository allowed", "severity_input": "medium: D1's class, data loss possible, low likelihood", "priority": "before the line leaves plumbing", "acts_next": "RGN"},
      {"key": "grant-nested-descent", "status": "recurring", "baseline": "QA-grant-latest-04 N5 and c392858 on the same fixture", "type": "claim not met: a recursive removal reaching a nested repository covered by **", "severity_input": "medium: a nested repository's history deleted; N12 and N13 observed by git's dry run, N15 and N16 inferred", "priority": "with this line, as the Regent decided N5 is fixed here", "acts_next": "RGN"},
      {"key": "grant-over-ask-landing", "status": "recurring", "baseline": "c392858 on the same fixture", "type": "over-ask: a bare-shaped plain folder read as a repository, now by every recursive removal above it", "severity_input": "low: asks more, never less", "priority": "later unit", "acts_next": "RGN"}
    ],
    "not_covered": ["Windows and macOS", "a live Claude Code session: logical or physical cwd, shell options carried from a profile, PowerShell's Set-Location", "the budget on a cold cache, network file systems or slower machines", "Python 3.8 to 3.10", "the removals themselves (landing by pwd -P, readlink, rev-parse; git clean by its dry run)", "N15 fed to the hook (refused by the harness) and N16 as a real unprivileged user", "grant stores other than the session store for the new cases", "CI for 63cd097", "git rm -r, rsync --delete, mv, submodule deinit, worktree remove, stash drop, find -L through an outward link"],
    "ambiguities": []
  },
  "doubts": [
    {"doubt": "Does the agent's shell on the Regent's machines ever start with set -o physical or set -P from the profile: yes or no?", "key": "gap-shell-physical-mode", "decides": "RGN"}
  ],
  "artefacts": ["risk-opinion"],
  "terminal": {"state": "ESCALATED", "why": "a regression in D1's class, data loss possible, was introduced in an attempt already past T4 on the Regent's word, and N5 is only partly met; the line is refused and only the Regent can accept, return or hold it"}
}
```

Terminal state: **ESCALATED**. N11 is a regression this attempt introduces, in the data-loss class and above the assumed tolerance, and N12 and N13 leave N5 partly open, on a line already past T4 on the Regent's word. The line is refused, and only the Regent can accept, return or hold it.