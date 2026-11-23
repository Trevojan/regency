I'm refusing this line and sending it to the Regent. D1 and D2 are fixed as I wrote them. But the attempt brings in one regression, N1: some git acts that asked at e260955 now run silently in another repository. Version verdict: **break**.

<<<ARTEFACT risk-opinion
# Risk opinion: unit grant-latest, QA verify, attempt 4

**Verdict in one line.** D1 and D2 are fixed as I wrote them. The attempt also introduces one regression in D2's class (N1): a git act that the line asked about at e260955 now runs silently in another repository. I refuse the verifiability line, and the decision goes to the Regent. Version verdict: **break**.

**What was tested.**
- Branch plumbing at 9fbb2c1. The change is `git diff e260955 9fbb2c1`: four files, all inside the span.
- dv-guards4.diff is byte-identical to that diff, and the surface diff is empty.
- Between 0cbf13d (where QA-grant-latest-03 verified the line) and e260955, only `.changelog/` and the ledger moved, so e260955 is the regression baseline.
- During this pass plumbing moved to 38fb4d6. Its diff from 9fbb2c1 touches only `.changelog/CHECKPOINT.md` and the ledger, so the code and norms under review are unchanged.

**What I read.**
- The diff, file contents, criteria-guards4.md, the change notes, gate-guards4-local.txt, and QA-grant-latest-03.md with its probes (the cited norm).
- Not read: git log, commit messages, CHECKPOINT and HISTORY.
- Also not read: `dv-guards4-notes.yaml` and the other earlier files in the scratch folder. They were not named in the packet and may hold reasoning.

**Change notes, checked against the diff.**
- `touched_paths` match the diff, and `surface_changed: false` matches the empty surface diff.
- Rollback is named.
- The six `new_tests` names map to 28 new hook-hazard cases and 3 new judge cases.
- The notes argue nothing.
- `touched_phases` was not checked: no phase reference was given.

**Environment.**
- A Linux container, run as root, with git 2.43.0 and Python 3.13.18 (3.11 and 3.12 also present). The session sets GIT_CONFIG_*.
- Probes ran on `git archive` exports of both commits and on throwaway fixtures under my scratch folder, with TMPDIR and HOME pointed there.
- No deletion, reset or push was run. Where an act lands was shown with `pwd -P`, `readlink -f/-m`, `ls -d` and `git rev-parse --show-toplevel`.
- /home/user/regency ends with an empty status and no stash, on plumbing at 38fb4d6 (see above). I committed nothing.

**Criticality assumed.** High, with a tolerance of no open defect above low introduced by the unit (criteria-guards4 §4). The Regent has stated nothing else.

## 1. Gate and inherited suite

| Check | Result |
|---|---|
| doctor at 9fbb2c1, re-run by QA in a clone | 0 FAIL, 30 WARN, HEALTHY. The OK lines match gate-guards4-local.txt |
| 33 self-tests (those doctor runs), at e260955 and 9fbb2c1, in the session environment and in a cleared one | All green. hook-hazard went from 220 to 248 cases and judge from 81 to 84; every other count is unchanged |
| hook-hazard and judge on Python 3.11 and 3.12 | 248/248 and 84/84 |
| inherited case labels in hook-hazard, judge, hook-judge, hook-verbs, guard-push and hook-refs | None lost; 28 + 3 added |
| named tests are real | Nine mutations, each removing one part of the fix in a fresh copy. Each turns red the cases that name that part: relative() without lands_in, 22 + 3; the git folder walked by text, 8 (4 of them inherited); resolve() normalising again, 3; no nested check, 11 + 1; no bare-repository check, 3 + 1; no own-`.git` exception, 1; `check` normalising again, 1; outside read as written, 1 + 1; links not followed, 9 + 2 |
| stdin wire (hook-hazard.py fed the event) | D1's 4 steps and D2's 3 steps: allow at e260955, ask at 9fbb2c1. `rm -rf src` and `git reset --hard` are still allowed |

## 2. Verdict per criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| D1 as written: under `delete **` and with `link` leading out, `rm -rf link/*`, `rm -rf link/`, `find link/ -delete` and `rm -rf link/precious` ask | MET | My QA-03 probe hz.py: 4 × allow at e260955, 4 × ask at 9fbb2c1, and the same on the wire. Also asking now: PowerShell `Remove-Item -Recurse link/*`, the absolute form, `cd src && rm -rf ../link/precious`, and `rm -rf link/../src/f` |
| D2 as written: `git -C nested push -f origin side` under `history **`; `git -C nested reset --hard` and `cd nested && git reset --hard` under `discard **` ask | MET | hz.py, with nested a real `git init`: 3 × allow at e260955, 3 × ask at 9fbb2c1, and the same on the wire. A submodule's gitfile and a bare repository in the work tree ask too |
| The norm D1 cites (judge.md §2): "`**` is the whole repository and never reaches outside it" | PARTIALLY MET | Met for a path through a link and for a path in a nested repository. Not met in three cases: a removal through a link after a `cd` through another link and back (N2); a recursive act that reaches a nested repository (N5, where the norm is ambiguous); and a `..` that takes the written path outside (N3) |
| The norm D2 cites: "a git act is judged where it runs … `**` and every relative glob stop at this repository" | PARTIALLY MET | Met through `-C`, through `cd` into a nested folder, and for a relative glob that names a nested repository. Not met for a `cd` chain through a link (N1, a regression; N2) |
| Regression: the line as QA-03 verified it still holds, except where D1/D2 change it, and the inherited suite does not get worse | PARTIALLY MET | The suite holds (§1). The D3, R3 and R4 rows are unchanged (hz.py, ko.py). guard-push.py, hook-refs.py, hook_wire.py, hook-resume.py and hook-verbs.py are untouched, and D5's paragraph of hooks.md is untouched. **One act that asked at e260955 now runs silently: N1** |
| D3–D5 and R1–R5 neither fixed nor made worse | MET | As in the row above. The attempt adds new kinds of extra prompt (N7–N10), separate from R4 |
| Criterion 4: the drafted judge.md §2 and hooks.md §2 state what the code does | PARTIALLY MET | Clause by clause below |

**Clause by clause (criterion 4).**

judge.md §2:
- **"Every symbolic link on it followed, the last one too":** the code does this. One consequence is N7.
- **"Every `..` read from where a link leads":** true only while the written path stays inside the repository. A `..` that takes the written path outside is read as written (N3). **The text states more than the code does.**
- **"Short of any repository nested in the work tree … holds its own `.git` (a clone, a submodule) or is a bare repository":** met on the way up from the path. A plain folder holding HEAD, objects and refs also counts as a repository (N9). Whether `**` reaches *down* into a nested repository is not settled (N5).
- **"The repository's own `.git` stays in it":** met. `rm -f .git/index.lock` and `rm -rf .git/modules/sub` are covered.
- **"Reads as the absolute place it lands … an absolute glob may name it, and the Judge proposes that place":** met. Granting the Judge's proposal makes the same act run, for both a link and a nested repository. The exception is N3.
- **"A path written outside the repository is read as written":** met.
- **"Judged … in the repository git finds from there":** met for `-C`, which git resolves physically. Not met where the shell moves by `cd` (N1).

hooks.md §2:
- **"Each `cd` … moves where the later paths and git acts resolve, and every path is placed where the file system lands it, through each symbolic link on the way."** The code places a `cd` where the file system lands it. bash moves logically instead: `cd current/..` and `cd current && cd ..` return to the repository (`pwd -P`). After a `..` that follows a link, the two differ in both directions: silent allows (N1, N2) and extra prompts (N8). In addition, a path that lands inside the repository is matched as written, not where it lands (N4). **The text states more than the code does, and something other than what the shell does.** The earlier clause "as git and the shell would" was dropped.
- **"One nested in the work tree … is another repository":** met.
- **"Asks unless an absolute glob names the place it lands":** met, except N3.

## 3. Open defects, by severity

**N1: medium. A regression introduced by this attempt, in D2's class (data-loss possible).** A git act after a `cd` chain through a link inside the repository runs in another repository, under a grant given for this one.

*Setup* (fixture sib-fixture.sh):
- `proj` is a git repository with `current -> proj/releases/v2`, a link inside it that points into a deeper folder.
- `sibling`, beside `proj`, is a git repository with a committed file `a`, modified and uncommitted.
- Session grants for `proj`: `discard **`, `history **` and `delete **`.

*Steps:* PreToolUse Bash with cwd `proj`, each of:
- `cd current && cd ../../sibling && git reset --hard`
- `… && git push -f origin side`
- `… && git clean -fdx`
- `… && git branch -D side`
- `cd current/../../sibling && git reset --hard`

*Expected* (judge.md §2 and hooks.md §2: judged in the repository git finds from where it runs; `**` stops at this repository): ask.

*Observed:*
- **Allow at 9fbb2c1, all five. Ask at e260955, all five.**
- guard-push also allows the `side` push; it denies only main.
- bash lands in `sibling` (`pwd -P`), and git's top level there is `sibling`, whose status shows ` M a`. The reset would discard that change; this is inferred, since nothing was run.
- The guard places the act at `proj/sibling`, the file system's landing of `proj/current/../../sibling`.

*Not affected:*
- The `rm` form of the same line asks.
- `git -C current/../../sibling …` is allowed, but git itself refuses to change into that folder.

*Cause (INFERRED, not the reported defect):* a `cd` is resolved physically, while bash resolves `..` logically. Before this attempt, the git folder was walked by text, and that caught this case.

*Evidence:* `sib.py`, `sib-fixture.sh` and `stack.py`. Not caught by any case in the suite.

**N2: medium. Pre-existing (allowed at e260955 too); what D1 and D2 leave behind, with the same symptom as N1.**
- *Setup:* `proj` with `current -> proj/releases/v2` and `cache -> ../outside`, where `outside` is a git repository holding `precious`.
- *Steps:*
  - Under `delete **`: `cd current && cd .. && rm -rf cache/*` and `cd current/.. && rm -rf cache/precious`.
  - Under `discard **`: `cd current && cd ../cache && git reset --hard`.
- *Expected:* ask.
- *Observed:* allow at both commits.
  - bash returns to `proj`, where `cache/*` expands to `outside/precious`.
  - `cd current && cd ../cache` puts git's top level at `outside`.
  - The direct forms `rm -rf cache/*` and `git -C cache reset --hard` now ask.
- *Evidence:* `cdl.py` and `cdl-fixture.sh`.

**N5: medium (a risk; the norm is ambiguous). Pre-existing.** An act on a folder of this repository reaches *down* into a nested repository under `**`.
- *Setup:* `nested` and `vendor/lib` are both `git init`.
- *Steps:* under `delete **`: `rm -rf *`, `rm -rf .`, `rm -rf vendor`, `find . -delete`, `find vendor -delete` and `git clean -ffdx` (git removes untracked nested repositories only with a second `-f`).
- *Expected:* judge.md says both "`**` … stop short of it" (ask) and "covered means every path the act *names* matches" (allow).
- *Observed:* allow at both commits.
- This is the Regent's reading to decide (ambiguity below).

**N3: low. Pre-existing.** A path through a link, whose `..` takes the written path out of the repository, is read where the text points.
- *Setup:* `link -> <tmp>/a/b/c/outside`; grant `delete <tmp>/keep/**`.
- *Step:* `rm -rf link/../../keep`.
- *Expected:* ask, because the act lands at `<tmp>/a/b/keep` (`readlink -m`), which the grant does not name.
- *Observed:* allow at both commits.
- Under `delete **` it asks, but the Judge proposes `delete <tmp>/keep/**`: the written place. Granting it lets the act delete `<tmp>/a/b/keep`.

**N4: low. Pre-existing.** Inside the repository, a relative glob matches the path as written, not where it lands.
- *Setup:* `build2 -> proj/src`; grant `delete build2/**`.
- *Steps:* `rm -rf build2/*` and `find build2/ -delete`.
- *Expected (hooks.md: "placed where the file system lands it"):* ask.
- *Observed:* allow at both commits. `rm -rf src/f` asks under the same grant.

**N7: low. Introduced; the drafted norm states it ("the last one too").** Removing an outward link by its own name now asks, and the Judge offers a grant that is too wide.
- *Steps:* under `delete **`: `rm -rf link`, `unlink link`, and `rm lf` where `lf` is a link to a file outside.
- *Observed:* allow at e260955; ask at 9fbb2c1.
- The proposal is `delete <outside>/**`. That grant would also cover D1's `rm -rf link/*`.
- rm and unlink remove only the link: known POSIX behaviour, not run.

**N8: low. Introduced (same symptom as N1).**
- *Steps:* under `delete **`: `cd link/.. && rm -rf build` and `cd link && cd .. && rm -rf build`.
- *Observed:* allowed at e260955; they now ask. bash is in `proj`, but the Judge proposes `delete <tmp>/a/b/c/build`, a place the act never touches.

**N9: low. Introduced.** A plain folder holding `HEAD`, `objects/` and `refs/` counts as a bare repository: `rm -rf data/objects` now asks under `delete **`.

**N10: low. Introduced. Simulated, not reproduced.**
- An unreadable folder on the way of a path inside the repository makes `holds_repository` raise PermissionError. Python's `Path.exists` re-raises EACCES; pathlib._abc ignores only errno 2, 20, 9 and 40.
- The hook then answers `ask | regency guard error (PermissionError …)`: it fails closed. The same act was allowed at e260955.
- `judge.py check` would end in a traceback (inferred).
- Not reproduced as a real unprivileged user: that user cannot reach this session's scratch root, and I changed no permissions outside my scratch folder.

**Still open and unchanged, as the Regent decided:** D3, D4, D5 and R1–R5.

**A correct change, not a defect (W1).** `git -C ../alias reset --hard`, where `../alias -> proj`, asked at e260955 and is now covered by `discard **`; git's top level there is `proj`. `cd ../alias && rm -rf src` still asks, because it is read as written.

## 4. Residual risk and coverage gaps

- **N1, N2 and N8 share one symptom.** For a `cd` through a link followed by `..`, the guard and the shell disagree about where the line is. This is what remains of D1 and D2's class.
- **R6 (new residual).** The file system is read before the line runs, so a link or a repository that the same line creates is not seen. Allowed at both commits:
  - `ln -s <outside> l2 && rm -rf l2/*` under `delete **`;
  - `git init -q n2 && git -C n2 reset --hard` under `discard **`.
- **More prompts.** N7–N10 add prompts the Regent will answer. R4 is unchanged.
- **Outside this unit, seen in passing:**
  - `git submodule foreach git reset --hard` is not read as hazardous at all, at both commits.
  - `rm -rf .git` is covered by `delete **` by the norm ("own `.git` stays in it"), at both commits.
  - A session opened through a link to the repository finds no session grant (asks), at both commits.
  - Python 3.13 gives a DeprecationWarning at hook-hazard.py:129 (positional `maxsplit`), at both commits.
- **Only the session store tested.** The new cases ran against session grants only. The other stores go through the same `covers()`, so the same result there is inferred.
- **Verification cost.** Object Calisthenics rule 3 applies. A path still travels as a raw `Path` with two meanings, written and landed, and one model serves two movers: `cd` (logical in shells) and `-C` (physical in git). N1–N4 and N8 sit at that seam. A place type that carries the written text, the shell's place and the file system's landing would turn each of those families into one case.
- **Case to add to the coherence matrix** (QA writes no files here): "a git act after a `cd` that climbs through a link inside the repository into another repository asks", on the sib fixture. It must be seen red at 9fbb2c1.

## 5. Version verdict: BREAK

This covers the increment e260955..9fbb2c1.

**The correction part.** D1's and D2's steps now behave as the norm at e260955 promised. A relative glob can no longer name a nested repository. That is D2's cited norm, though only an absolute, machine-specific glob can now name one, so such a grant no longer travels in a repository-scope JD.md.

**Earlier behaviour also changed, beyond D1 and D2.** No evidence shows that nothing relies on it:
- Removing an outward link by name and `cd link/..` chains now ask under `delete **` (N7, N8). This is the drafted "the last one too" clause.
- A bare-shaped folder and an unreadable folder now ask (N9, N10).
- For those paths, `judge.py check` changes its exit code from 0 to 1 and its proposal text (now the absolute landing place).
- Consumers: every `**` and relative-glob row in session, JD.md, machine and named-file stores; scripts that relink outward links under a grant; readers of `check`'s exit code.

**Widenings.** One is correct (W1) and one is wrong (N1).

**Norm and version.** judge.md §2 and hooks.md §2 redefine "in the repository" in text an agent drafted, and ratifying it is the Regent's call. The line was already a break at QA-03, and the version is still 3.3; the number is the Regent's.

## 6. Not covered

- **Windows and macOS.** Also unverified:
  - realpath over junctions;
  - case folding;
  - the `nt` branches;
  - `/tmp -> /private/tmp`.
- **PowerShell and other shell forms.** Not tested:
  - whether PowerShell's `Set-Location` moves logically;
  - `pushd`/`popd` forms of N1;
  - PowerShell itself: only its events were fed to the hook.
- Python 3.8–3.10 (not installed).
- N10 as a real unprivileged user.
- A live Claude Code session; only the stdin wire was used.
- The destructive acts themselves; landing was shown read-only.
- Grant stores other than the session store, for the new cases.
- CI for 9fbb2c1 (only the local gate was given).
- Other hazardous git verbs through a link or a nested repository beyond those listed: stash drop, worktree remove, reflog expire, filter-repo.
- D3–D5 and R1–R5 beyond confirming they are unchanged.

## 7. Assumptions (TEAM §7.5)

- **Criticality.**
  - Assumption: high, with no open defect above low introduced by the unit.
  - If false: at normal criticality, N1 could be accepted as a known defect.
  - Validated by: the Regent stating criticality.
- **Shell.**
  - Assumption: the agent's Bash runs bash (or a POSIX shell) with the default logical `cd`.
  - If false: under `cd -P` or `set -o physical`, N1, N2 and N8 do not arise and the code is right.
  - Validated by: the shell Claude Code runs.

## 8. Verifiability line

Refused. N1 is a defect introduced by the unit, above the assumed tolerance, and in a data-loss class (QA §12). This attempt already runs past T4 on the Regent's word, so the next step is the Regent's.
ARTEFACT>>>

**Escalation (TEAM §7.8)**
- **Trigger:** N1. The attempt makes a git act that used to ask run silently in another repository. This is data-loss class (QA §12), on a line already past T4.
- **Unresolved question:** may the guards line stay as it is with N1 open, or does it go back for a fifth attempt?
- **Evidence:**
  - Risk opinion §3, N1.
  - Probes in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa4/bin/: sib.py, sib-fixture.sh, stack.py (N1); cdl.py, cdl-fixture.sh (N2, W1); ex.py (N3–N9, R6); eacces.py (N10); mutate.py; suite.sh.
  - My doctor re-run: /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa4/doctor-mine.txt.
- **What I did:**
  - ran the full suite at both commits, in two environments and on three Pythons;
  - re-ran doctor;
  - mutated each part of the fix;
  - re-ran D1, D2 and the QA-03 probes;
  - ran exploratory probes on throwaway fixtures, with landing confirmed read-only.
- **Risk:** under a `**` grant for this repository, a reset, clean, branch deletion or force push to a non-main branch runs in a neighbouring repository after `cd <link> && cd ../../<repo>`.
- **Decision needed from the Regent (one of):**
  - **A. Accept.** Record N1, plus N2, N3, N4, N5 and N7–N10, as known defects. Ratify or reword the drafted norm text, and choose the version.
  - **B. Return to DV for a fifth attempt (the Regent's word only).** At least N1. N2 and N8 share its symptom. Add N5 once the Regent has answered the doubt below.
  - **C. Hold on plumbing** until A or B.
- **Doubt (closed):** does a `**` grant cover an act that names a folder of this repository but recursively reaches a nested repository below it? Yes or no.

EVENT VALIDATION_FAILED grant-latest QA grant-cd-logical-escape
EVENT ESCALATION_STARTED grant-latest QA risk-opinion

suba-validator envelope (checked with `python scripts/returns.py check --suba suba-validator -` over this whole message):

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
    "key": "grant-cd-logical-escape",
    "ask": "sign or refuse the verifiability line of grant-latest attempt 4, with a regression introduced in D2's class"
  },
  "body": {
    "verdicts": [
      {"criterion": "D1 as QA-grant-latest-03 wrote it: under delete **, rm -rf link/*, rm -rf link/, find link/ -delete, rm -rf link/precious ask when link leads out of the repository", "verdict": "MET", "evidence": ["hz.py at e260955: 4 x allow; at 9fbb2c1: 4 x ask", "the same 4 steps on the stdin wire at 9fbb2c1: ask", "PowerShell Remove-Item -Recurse link/*: ask"]},
      {"criterion": "D2 as QA-grant-latest-03 wrote it: git -C nested push -f origin side (history **), git -C nested reset --hard and cd nested && git reset --hard (discard **) ask", "verdict": "MET", "evidence": ["hz.py at e260955: 3 x allow; at 9fbb2c1: 3 x ask, on a real git init nested", "stdin wire at 9fbb2c1: ask", "a submodule gitfile and a bare repository in the work tree: ask"]},
      {"criterion": "the norm D1 cites, judge.md §2: ** is the whole repository and never reaches outside it", "verdict": "PARTIALLY MET", "evidence": ["met for paths through a link and in a nested repository, and the Judge's proposal round-trips (granted, then allowed)", "not met: cd current && cd .. && rm -rf cache/* deletes outside under delete ** at both commits (N2)", "not met: rm -rf vendor, git clean -ffdx reach a nested repository under ** at both commits (N5)"]},
      {"criterion": "the norm D2 cites: a git act is judged where it runs; ** and every relative glob stop at this repository", "verdict": "PARTIALLY MET", "evidence": ["met through -C, cd into a nested folder, and relative globs naming a nested repository", "not met: cd current && cd ../../sibling && git reset --hard is allowed under discard ** at 9fbb2c1 and asked at e260955 (N1)"]},
      {"criterion": "regression: the line as QA-grant-latest-03 verified it holds except where D1 and D2 change it; the inherited suite does not get worse", "verdict": "PARTIALLY MET", "evidence": ["every self-test doctor runs green at 9fbb2c1 in the session and a cleared environment, Python 3.11, 3.12, 3.13; no inherited label lost in six suites", "doctor re-run in a clone: 0 FAIL, 30 WARN", "hz.py and ko.py rows for D3, R3 and R4 unchanged", "one behaviour that asked at e260955 is now allowed: N1"]},
      {"criterion": "criterion 4: judge.md §2 and hooks.md §2 as drafted state what the code does", "verdict": "PARTIALLY MET", "evidence": ["code matches: links followed incl. the last, nested and bare repositories, own .git kept, landing place proposed", "the norms state more than the code: a .. that leaves the repository's text is read as written (N3); a path landing inside is matched as written, not where it lands (N4); a cd is placed where the file system lands it, the shell places it logically (N1, N2, N8)"]}
    ],
    "risk": {
      "measured": [
        {"surface": "a git act after a logical cd that climbs through an in-repo link into another repository (N1, introduced)", "consequence": "git reset --hard, clean -fdx, branch -D or a force push to a non-main branch runs in another repository under a grant for this one; uncommitted work there lost", "likelihood": "low: needs a link to a deeper folder inside the repository, a cd through it and a .. climb into another repository in one line, and a ** grant", "detectability": "none at the time: both guards are silent", "uncertainty": "how often such links (current -> releases/vN) exist in the Regent's projects"},
        {"surface": "a recursive act on a folder holding a nested repository under ** (N5, pre-existing)", "consequence": "a nested repository's unpushed history and work deleted", "likelihood": "medium: git clean -ffdx and rm -rf <folder> are common", "detectability": "none at the time", "uncertainty": "whether the Regent reads ** as covering it; the norm's two sentences pull apart"}
      ],
      "missing": ["the Regent's or the PO's criticality and maximum tolerable severity for this unit, still assumed high with tolerance low"]
    },
    "findings": [
      {"key": "grant-cd-logical-escape", "status": "regression", "baseline": "e260955 (= 0cbf13d code) on the same fixture and commands", "type": "guard coverage wider than its grant: a git act in another repository allowed", "severity_input": "medium: same class as D2, data-loss possible, low likelihood", "priority": "before the line leaves plumbing", "acts_next": "RGN"},
      {"key": "grant-cd-logical-residue", "status": "new", "baseline": "e260955 on the same fixture", "type": "D1/D2-class residue: removal outside and git act in another repository after cd through a link and back", "severity_input": "medium: data-loss class, lower likelihood than D1", "priority": "with the fix of grant-cd-logical-escape", "acts_next": "RGN"},
      {"key": "grant-nested-descent", "status": "new", "baseline": "e260955 on the same fixture", "type": "norm ambiguity with a data-loss consequence", "severity_input": "medium", "priority": "the Regent decides the reading first", "acts_next": "RGN"},
      {"key": "grant-dotdot-text-escape", "status": "new", "baseline": "e260955 on the same fixture", "type": "absolute glob matched against the written place, Judge proposes it", "severity_input": "low", "priority": "later unit", "acts_next": "RGN"},
      {"key": "grant-inner-link-relative", "status": "new", "baseline": "e260955 on the same fixture", "type": "relative glob matched as written inside the repository", "severity_input": "low", "priority": "later unit", "acts_next": "RGN"},
      {"key": "grant-over-ask-landing", "status": "new", "baseline": "e260955 on the same fixture", "type": "over-ask: link removed by name, cd link/.., bare-shaped folder, unreadable folder", "severity_input": "low: asks more, never less", "priority": "later unit", "acts_next": "RGN"}
    ],
    "not_covered": ["Windows and macOS: realpath over junctions, case folding, /tmp -> /private/tmp", "PowerShell Set-Location and pushd/popd variants of N1", "Python 3.8 to 3.10", "EACCES reproduced as a real user (simulated only)", "a live Claude Code session", "the deletions themselves (landing shown by pwd -P, readlink, rev-parse)", "grant stores other than the session store for the new cases", "CI for 9fbb2c1"],
    "ambiguities": [{"criterion": "judge.md §2: ** stops short of a nested repository, while coverage is defined by the paths an act names", "nearest_checkable": "an act whose named path is in this repository but whose recursion reaches a nested repository (rm -r <folder>, find <folder> -delete, git clean -ff) asks under ** - or is covered; the Regent picks one"}]
  },
  "doubts": [
    {"doubt": "Does a ** grant cover an act that names a folder of this repository but recursively reaches a nested repository below it: yes or no?", "key": "gap-nested-descent", "decides": "RGN"}
  ],
  "artefacts": ["risk-opinion"],
  "terminal": {"state": "ESCALATED", "why": "a regression in D2's class, data-loss possible, was introduced in an attempt already past T4 on the Regent's word; the line is refused and only the Regent can accept, return or hold it"}
}
```

Terminal state: **ESCALATED**. N1 is a regression this attempt introduces, data-loss class, above the assumed tolerance, on a line already past T4 on the Regent's word. The line is refused, and only the Regent can accept, return or hold it.