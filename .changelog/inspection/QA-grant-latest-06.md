I sign the verifiability line for this attempt's criteria as written, with residual risk, and I'm sending the residue to the Regent. N11, N12 and N13 are fixed as I wrote them, and §4's three cases are live and were seen red at 40e1982. What attempts 4 and 5 fixed still holds, the backlog is unchanged, and the only defect the attempt introduces is low (N18, over-asking). Three pre-existing silent allows remain, in the very classes the Regent decided are fixed here (N17, N19, N20, all medium). A fourth sits outside the unit (N21). Version verdict: **break**.

<<<ARTEFACT risk-opinion
# Risk opinion: unit grant-latest, QA verify, attempt 6

**Verdict in one line.** N11, N12 and N13 are met as QA-05 wrote them (setup, steps, expected, observed), and §4's three cases are live. No defect above low is introduced: the one introduced is N18, which asks more, never less. N11's class still has silent allows through other spellings of physical mode (N17), and so does N12's class through git's pathspec forms (N19), and N13's through a `.git` file git does not read (N20). All three are medium, observed, and also allowed at 40e1982. The line is signed for the criteria as written; whether the residue is accepted or returned is the Regent's call. Version verdict: **break**.

**What was tested.**
- Branch plumbing at 0c45883. The change is `git diff 40e1982 0c45883`: four files, all inside the span. dv-guards6.diff is byte-identical to it. The surface diff (registry.json, hooks.json) is empty.
- 40e1982 differs from 63cd097, where QA-05 verified the line, only in `.changelog/` and `.shortcuts/.virtual/ongoing.json`. So 40e1982 carries 63cd097's code and is the regression baseline.

**What I read.**
- The four inputs, file contents at both commits, the contract files, and QA-03, QA-04 and QA-05 with their probes.
- Not read: git log, commit messages, CHECKPOINT and HISTORY (only their names, in a `--stat`), and every other file in the scratch folder.

**Change notes, checked against the diff.**
- `touched_paths` match the diff, and `surface_changed: false` matches the empty surface diff.
- Rollback is named, and the notes argue nothing.
- The seven `new_tests` names cover 23 of the 32 hook-hazard cases added, and the one new judge case. The count is 31 net, because one inherited case moved fixture. **They omit the eight cases "and where bash stays logical, the 'cd' back stays in this repository"**, the allow side of N11.
- `touched_phases` is empty and was not checked: no phase reference was given.

**Environment.**
- A Linux container, run as root, with bash 5.2.21 (`sh` is dash), git 2.43.0 and Python 3.13 (3.11 and 3.12 also present). zsh is not installed.
- Probes ran on `git archive` exports of both commits and on throwaway fixtures under my scratch folder, with TMPDIR and HOME pointed there.
- No removal, reset or clean was run for real:
  - bash's landing was shown with `pwd -P` in place of the removal;
  - what git clean reaches was shown only by its dry run (`git clean -n …`).
- /home/user/regency ends clean, on plumbing at 0c45883, with no stash. I committed nothing.

**Criticality.** High, stated by the Regent on 2026-11-25: no open defect above low introduced by the unit.

## 1. Gate and inherited suite

| Check | Result |
|---|---|
| doctor at 0c45883, re-run by QA in a throwaway clone | 0 FAIL, 30 WARN, HEALTHY. The whole output is identical to gate-guards6-local.txt |
| 33 self-tests (those doctor runs), at 40e1982 and 0c45883, in the session environment and in a cleared one (GIT_CONFIG_* and the session variables unset) | All green in all four runs. hook-hazard went from 279 to 310 cases and judge from 86 to 87; every other count is unchanged |
| hook-hazard, judge and hook-judge on Python 3.11 and 3.12 | 310/310, 87/87 and 10/10 |
| inherited case labels in hook-hazard, judge, hook-judge, hook-verbs and hook-refs, compared at runtime | None lost; 31 + 1 added. The `git clean -fdx` allow label kept its name and moved to a fixture with no bare repository, as QA-05 asked. guard-push.py, hook-refs.py, hook_wire.py, hooks.json and registry.json are untouched |
| named tests are real: 33 mutations, each removing one part of the fix in a fresh copy | **22 turn their cases red.** The `set` reading, 7. A letter bash does not know, 1. An unknown `-o` name, 1. `set +P`, 2. `--` and `-`, 1. `-o` taking its name, 1. A started shell's options, 3. The child shell starting logical, 1. `cd -L` under physical mode, 1. A cd with no flag following the shell's mode, 10. The exclude pattern, 7. A cluster ending in `e`, 2. One `-f` searching nothing, 6. One `-f` searching every repository, 1. Two `-f` searching only bare ones, 1. And seven judge mutations: a clone passed whole; HEAD content; a detached HEAD; `ref:` with no space; the bare switch; a passed folder counted; a passed folder searched through |
| | **11 turn nothing red.** Eight fail toward allowing: pushd under physical mode (H11), `--rcfile` (H12), `--exclude` cut to a prefix (H15), `-ff` inside one cluster (H16), `--force` (H17), a linked HEAD (J6), an unreadable HEAD (J7) and a missing HEAD (J12). Three fail toward asking (H18, J2, J8). See §4 |
| the stdin wire (hook-hazard.py fed the event, a real process) | N11's two steps, N12's four steps and N13's step ask at 0c45883 and are allowed at 40e1982. `git clean -fdx -e vendor.git src` is allowed. N19's `git clean -ffdx ':!keep'` is allowed at both |
| the Judge's round trip | Granting the proposal `delete ** <proj>/junk/inner.git/** <proj>/vendor.git/**` covers `git clean -fdx` and `git clean -fdx -e keep`; `git clean -ffdx` still asks |

## 2. Verdict per criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| N11 as QA-05 wrote it: `set -P; cd link && cd .. && rm -rf x` and `set -o physical; …` ask under `delete **` | MET | n11 table and the wire: allow at 40e1982, ask at 0c45883, proposing `delete <F>/a/b/c/x/**`. bash lands at `<F>/a/b/c` (`pwd -P`). Also ask: the DV's eight variants; `set -P; cd -L link && cd .. …`; `bash -c 'set -P; …'`; `{ set -P; }`; `builtin set -P`; `command set -P`; `eval set -P`; `set -P x -s`; `set -oP physical`; `bash -Pc`, `/bin/bash -P -c`, `env bash -P -c`, `bash --norc -P -c` and `bash -O extglob -P -c`; `set -P; cd link/..`; `find … -delete` and `git clean -ffdx` after the chain; and the multi-line form |
| N12 as QA-05 wrote it: `git clean -ffdx -e keep`, `-e '*.log'`, `-ffdxe keep` and `--exclude keep` ask over the gc fixture | MET | allow at 40e1982, ask at 0c45883, and on the wire too. The dry run removes tmp/ and vendor.git/. Also ask: `--exc keep`, `--e keep`, `-fe keep -d`, `--forc -f … -e keep` |
| N13 as QA-05 wrote it: `git clean -fdx` over an untracked bare repository asks | MET | allow at 40e1982, ask at 0c45883, proposing `delete ** <proj>/junk/inner.git/** <proj>/vendor.git/**`. This matches the dry run: it removes vendor.git/ and junk/ and skips both clones. `git clean -fdx src`, `-ffdx src` and `-fdx -e vendor.git src` stay allowed; the last asked at 40e1982 and git removes only src/ |
| §4's three cases in the coherence matrix, each seen red at the baseline | MET | All three are in the suite under their exact labels: 2, 4 and 5 commands, all allowed at 40e1982 and asked at 0c45883. The `git clean -fdx` allow case now runs in the `plain` fixture, which holds no bare repository. Removing the fix turns them red (H1, H10, H13, H19). **Gap:** N12's case passes on gc's bare `vendor.git` alone, so it does not prove the "over a nested clone" in its name (H16, §4) |
| the Regent's reading: "a cd is logical unless the line itself says otherwise (cd -P, set -P, set -o physical)" | PARTIALLY MET | Met for every form above. **Not met (N17):** the line turns physical mode on, or never turns it off, and the reader reads logical. Allowed at both commits |
| what attempts 4 and 5 fixed keeps its verdict | MET | The QA-03/04/05 probes give identical rows at both commits (hz 16, ko 7, ex 58, sib 8, stack 2, cdl 7): D1's and D2's steps ask; N1's five and N2's three steps ask; N8's two are allowed; N5's six ask. On a fixture with no repository below, the six steps and `git clean -fdx` are allowed at both |
| N14, N15, N16, N3, N4, N7, N9, N10, R6, D3, D4, D5, R1–R5: neither fixed nor made worse | MET | N14's four steps ask at both commits and `rm -rf data/objects` asks at both. `git clean -fdx` over the bare-shaped plain folder is allowed at both; git itself reads `data` as no repository. N10 and N16 give the same simulated results (eacces.py, eacces5.py). N3, N4, N7, N9 and R6 give the same ex.py rows. D3, R3 and R4 give the same hz.py and ko.py rows. N15's glob pick is unchanged in the diff; I did not re-feed its line, because the harness refused it at QA-05. The files of D4, R1, R2 and R5 are untouched, and so is D5's paragraph of hooks.md |
| no open defect above low introduced by the unit | MET | Every probe row compared, 197 in all, shows no ask turned into an allow except `git clean -fdx -e vendor.git src`, which git confirms is right. The one introduced defect is N18 (low, asks more) |
| regression: the line as QA-05 verified it at 63cd097 holds, except where N11–N13 change it on purpose, and the inherited suite is no worse | MET | §1, and the identical probe rows above. The changed rows are N11's, N12's and N13's and their variants, plus N18's over-asks, which hooks.md states |
| criterion 4: judge.md §2 and hooks.md §2, as drafted, state what the code does | PARTIALLY MET | Clause by clause below |
| the hook's budget: hooks.json runs it with `"timeout": 10` and `"onFailure": "block"` | MET (this machine, warm cache) | §5. At most 3.09 s end to end; hooks.json is unchanged |

**Clause by clause (criterion 4).** Both files carry the same physical-mode text; the judge.md wording is quoted.

- **"…where bash's own reading finds no folder, under `cd -P` and in physical mode, it lands where the file system does."** The code does this: moved() takes the shell's mode unless `cd -P` or `-L` names one.
- **"Only the line itself turns physical mode on: `set -P` or `set -o physical`, until `set +P` or `set +o physical`, or a shell it starts as `bash -P -c …` or `bash -o physical -c …`; `cd -L` still moves logically."** Met for those forms. bash confirms each landing.
  - **It states less than bash:** `shopt -s -o physical`, a `set -P` inside `eval '…'`, and `bash -P` fed by a heredoc also turn it on. So does `SHELLOPTS`, which hooks.md names as not read and judge.md does not.
  - **It states more than the code means by "until":** a `set +P` that bash runs elsewhere or not at all still ends physical mode for the reader (N17).
- **"A `set` reads as bash reads it: one holding a letter bash does not know changes nothing, and an `-o` name bash does not know stops it there."** Met against real bash for `-Ps`, `-o nosuch -P`, `-P -o nosuch`, `-- -P` and `-P x -s`. **Not met** for `set -o -P`: bash lists the options and goes on to `-P`, while the reader takes `-P` as the `-o` name.
- **"`git clean` with one `-f` acts on every bare repository below it: git passes whole only a folder whose `.git` it reads as a repository, and removes a bare one, read as git reads it."** Met: git's dry run agrees on the gc fixture and on the judge test's own fixture (data/ with inner.git, detached.git and top.git removed, the clone left).
  - **It states more than the code:** a folder whose `.git` is a file git does not read as a repository is passed whole by the code, and removed by git (N20).
  - **It states more than git:** with no `-d` (or with `-X`), git clean does not go into untracked folders, so it removes no bare repository there (N18). The text owns this: "neither that pattern nor `-d` narrows it".
- **"A `git clean` names the paths git reads as its own: the pattern of `-e` or `--exclude` … is none."** Met for the `-e` and `--exclude` forms. **It states more than the code:** pathspec magic (`:!…`, `:^…`, `:(exclude)…`, `:/`) and git's own wildcards, which match across `/`, are read as folders or as a shell glob (N19).
- **"A glob reaches the folders its wildcard part matches, as a shell expands it."** Unchanged (N15). For git clean, a glob that reaches git unexpanded is git's pathspec (N19).
- **"One that runs past 3 seconds places nothing, so the act asks."** Met, for git clean's search too.
- **hooks.md, "1.4 million files run past its 3 seconds, so there `rm -rf .` and `git clean -fdx` ask under `delete **`."** Consistent: on 1.5 M files both ask at 3.06–3.09 s.
- **hooks.md, "Not read: `SHELLOPTS` …, PowerShell's `..`, git clean's `-d` and its exclude patterns (the search reaches more, never less), and `--recurse-submodules`."** Accurate as far as it goes. It omits N17's other forms, N20, and N19, where the search reaches *less*, not more.

## 3. Open defects, by severity

**N17: medium. Pre-existing (allowed at 40e1982 too); what remains of N11's class.** The line turns physical mode on, or never turns it off, and the reader reads the later `cd` logically.
- *Setup:* fx6.py. `proj` is a git repository with `link -> <F>/a/b/c/outside`, and `<F>/a/b/c/x` exists. Session grant: `delete **`.
- *Steps:* PreToolUse Bash with cwd `proj`, each of these (n11-lines.txt):
  - `shopt -so physical; cd link && cd .. && rm -rf x`, and `shopt -s -o physical; …`
  - `eval 'set -P'; cd link && cd .. && rm -rf x`
  - `set -P; eval 'cd link && cd .. && rm -rf x'`, and `set -P; eval cd link '&&' cd .. '&&' rm -rf x`
  - `set -P; true || set +P; …`, `set -P; if false; then set +P; fi; …`, `set -P; set +P | cat; …`, `set -P; set +P & wait; …`
  - `set -o -P; cd link && cd .. && rm -rf x`
  - `bash -P <<'EOF'` with `cd link && cd .. && rm -rf x` as its body
  - `set -o physical; export SHELLOPTS; bash -c '…'`, and `env SHELLOPTS=physical bash -c '…'`, both named in hooks.md
- *Expected* (the Regent's reading; judge.md: "`**` … never reaches outside it", "a `set` reads as bash reads it"): ask.
- *Observed:* allow at both commits. With `pwd -P` in place of the removal, bash lands at `<F>/a/b/c` in every form, so the removal would land at `<F>/a/b/c/x` (inferred; nothing was removed). `eval set -P; …` and `bash -P -s <<< '…'` ask.
- *Cause (INFERRED, not the reported defect):*
  - every `set` word is applied in order, whatever runs it;
  - `eval`'s words are read as a new shell that starts logical (`acts(…, started)`);
  - `shopt -o` is not read.

**N19: medium. Pre-existing; what remains of N12's class.** git clean pathspecs that the reader takes for folders.
- *Setup:* gc6.sh. `proj` has one commit, and these untracked entries:
  - clones `tmp/clone` and `nest/clone2`, where nest/clone2 holds the bare `inner.git`;
  - bare repositories `vendor.git` and `junk/inner.git`;
  - `keep/`, `src/f`, `x.log`, and a bare-shaped `data/`.
  - Session grant: `delete **`.
- *Steps and dry runs:*
  - `git clean -ffdx ':!keep'`, `':^keep'` and `':(exclude)keep'`: the dry run removes nest/, tmp/, vendor.git/ and junk/.
  - `git clean -fdx ':!keep'`: the dry run removes vendor.git/ and junk/.
  - `git clean -ffdx ':/'`, also from `src`: the whole tree.
  - `git clean -ffdx '*clone*'`: the dry run removes nest/clone2/ and tmp/clone/.
  - `git clean -fdx '*inner*'`: the dry run removes junk/inner.git/.
- *Expected* (judge.md: "A `git clean` names the paths git reads as its own"): ask.
- *Observed:* allow at both commits, and on the wire.
- *Cause (INFERRED):* pathspec magic resolves to a folder that does not exist, and git's wildcard is matched as a shell glob over the first level only, so the search finds nothing.

**N20: medium. Pre-existing; a residue of N13 in the new bare search.** A `.git` file git does not read as a repository is passed whole.
- *Setup:* `stale/.git` holds `gitdir: <D>/nowhere/.git/worktrees/stale` (a stale worktree pointer), and `stale/inner.git` is a bare repository. `git -C stale rev-parse` answers "not a git repository". Session grant: `delete **`.
- *Step:* `git clean -fdx`.
- *Expected* (judge.md: "git passes whole only a folder whose `.git` it reads as a repository"): ask.
- *Observed:* allow at both commits. The dry run says "Would remove stale/". `git clean -ffdx` and `rm -rf stale` ask.
- *Cause (INFERRED):* bare_meets passes every folder whose `.git` is not a directory, without reading it. Likelihood very low: it needs a broken pointer and a bare repository below it.

**N21: medium. Pre-existing, in hook-hazard.py but outside this unit's criteria.** A command piped into a shell is not read.
- *Step:* `echo 'rm -rf x' | bash`, with no grant at all.
- *Expected:* ask.
- *Observed:* allow at both commits.
- `bash <<'EOF'` with `rm -rf x` as its body asks, as hooks.md states. No earlier QA reported this form.

**N18: low. Introduced; N13's fix asks where git removes nothing.**
- *Steps* under `delete **` over gc: `git clean -f`, `git clean -fx`, `git clean -fdX` and the dry run `git clean -fdx -e keep -n`.
- *Observed:* allowed at 40e1982; ask at 0c45883. Yet `git clean -n -f` removes only x.log.
- And on a tree past the search's 3 s, `git clean -fdx` now always asks (0.06 s allow, then 3.07 s ask).
- hooks.md states both; the cost is prompts. It asks more, never less.

**Still open and unchanged, as the Regent decided:** N14, N15, N16, N3, N4, N7, N9, N10, R6, D3, D4, D5 and R1–R5.

**Seen in passing, the same at both commits:**
- The ask's reason is cut with "…" once a proposal names many places (`one_line` in hook_wire.py, outside the span). The Regent then sees an incomplete grant line, for example for `git clean -ffdx -e keep` on gc.
- `set` in a PowerShell event is read as bash's: PowerShell's `set` is Set-Variable. It asks more, never less.
- A DeprecationWarning at hook-hazard.py:134.

## 4. Residual risk and coverage gaps

- **N17, N19 and N20 are the classes of N11, N12 and N13 that remain.** Each is observed and allowed at both commits, so none is introduced. Each deletes outside the repository, or deletes a nested clone's or bare repository's history, under a `**` grant given for this one.
- **Tests that do not catch a regression** (mutations; the code is right today).
  - H16: if `-ff` inside one cluster is counted once, `git clean -ffdx` and `git clean -ffdx -e keep` over a nested clone with no bare repository turn into allows, and the suite stays 310/310. N12's named case passes on gc's `vendor.git` alone.
  - H15 (`--exc keep`), H17 (`--force --force`) and H11 (`set -P; pushd link/.. && rm -rf x`) turn into allows the same way.
  - H12, J6, J7 and J12 also fail toward allowing.
- **Cases to add**, each seen red under its mutation:
  - "git clean -ffdx over a nested clone with no bare repository asks";
  - "git clean -ffdx --exc keep over a nested clone asks";
  - "git clean --force --force -dx over a nested clone asks";
  - "set -P, then pushd through an outward link's .. and a removal: asks".
- **Only the session store tested.** The new cases ran against session grants only. The other stores go through the same `covers()`, so the same result there is inferred.
- **Verification cost.** Object Calisthenics rules 3 and 4 apply.
  - Physical mode is a bare boolean threaded through `acts`, and a nested shell gets `started` instead of the line's mode, which is N17's `eval` form.
  - git clean's grammar (`forces`, `takes_pattern`, `clean_args`) is parsed by hand beside pathspec magic it does not read.
  - A first-class shell state (mode, cwd, known or unknown) and a git pathspec value would each turn a family of cases into one.

## 5. The hook's budget

Measured end to end on the stdin wire (a real process, Python start-up included), under `delete **`, warm cache, three runs each:

| Tree (empty files, no repository below) | `rm -rf .` 40e1982 → 0c45883 | `git clean -fdx` 40e1982 → 0c45883 | `git clean -ffdx` 0c45883 |
|---|---|---|---|
| 26,064 folders, 208,512 files | 0.70–0.74 s → 0.63–0.70 s, allow | 0.07 s → 0.62–0.70 s, allow | 0.63–0.69 s, allow |
| one folder of 1,000,000 files | 0.81–0.82 s → 0.76–0.81 s, allow | 0.06–0.10 s → 0.80–0.87 s, allow | 0.82–0.88 s, allow |
| 150,000 folders, 1,500,000 files | 3.07 s → 3.07–3.09 s, ask | 0.06–0.07 s allow → 3.07 s, ask | 3.06–3.09 s, ask |

- One deadline is shared across a line. Four recursive acts take 2.51 s on the small tree, and the same line takes 3.08 s on the big one.
- That leaves at least 6.9 s of the 10 s timeout here, and a timed-out search fails closed.

## 6. Version verdict: BREAK

This covers the increment 40e1982..0c45883.

**The correction part.**
- N11 and its variants: removals outside the repository after the line turns physical mode on now ask, as the norm already promised.
- N12: git clean's exclude pattern is no longer read as a path.
- The over-ask on `git clean -fdx -e vendor.git src` is gone.

**Earlier behaviour also changed, by the Regent's N13 decision:**
- `delete **` no longer covers `git clean -f…` with a single `-f` where an untracked bare repository lies below, including the no-`-d` and dry-run forms (N18).
- On trees past about 1.4 M files, no grant covers `git clean -fdx`.
- The Judge's proposals for single `-f` now list bare repositories.
- Consumers: every `delete **` row in the session, JD.md, machine and named-file stores; workflows that run git clean in trees holding bare repositories or in very large trees; readers of the hook's verdict.

**Norm and version.** judge.md §2 and hooks.md §2 are agent-drafted text, and ratifying them is the Regent's call. The version is still 3.3; the number is the Regent's.

## 7. Not covered

- **zsh** (not installed): `setopt chase_links` and `chase_dots`, where a Mac's agent shell is zsh.
- **Windows and macOS**, and their `nt` branches.
- **A live Claude Code session.** Not covered: whether the Bash tool's shell is bash, and whether its snapshot carries physical mode. The Regent decided it does not.
- **A `set` in a sourced file** (`. ./s.sh`) or a profile. It is not the line, so it is out of the Regent's reading.
- **An unprivileged user:** J7, and N16 for real. This container runs as root.
- **Python 3.8–3.10** (not installed).
- **The budget beyond this container:** a cold cache, network file systems, slower machines.
- **git versions other than 2.43**, whose git clean may treat nested repositories differently.
- **The removals themselves.** Landing was shown by `pwd -P`, and git clean's reach by its dry run.
- **N15's line**, not re-fed to the hook (the harness refused it at QA-05).
- **Grant stores other than the session store**, for the new cases.
- **CI for 0c45883** (only the local gate was given).
- **Other acts that reach nested repositories**, not probed: `git rm -r`, `rsync --delete`, `mv` over one, `git submodule deinit -f`, `git worktree remove`.
- **The backlog items**, beyond confirming they are unchanged.

## 8. Assumptions (TEAM §7.5)

- **Shell.**
  - Assumption: the agent's Bash runs bash and starts logical (the Regent, 2026-11-25).
  - If false: N11 and N17 widen to every `cd <outward link> && cd ..`.
  - Validated by: the Regent's decision.
- **git clean's reach.**
  - Assumption: git's dry run with the same flags shows what the act removes (git-clean(1)).
  - If false: N18, N19 and N20 may reach more or less than shown.
  - Validated by: a real run on a throwaway fixture, which the packet forbids here.

## 9. Verifiability line

**Signed for the criteria as written, with residual risk N17, N19, N20, N21 (medium, pre-existing) and N18 (low, introduced).**
- Every criterion the Regent set is met, except criterion 4's text, which is partially met.
- No defect above low is introduced.
- I do not declare the residue acceptable (QA §2). N17, N19 and N20 risk losing data, in the classes the Regent decided are fixed in this attempt, so they go to the Regent (QA §12).
ARTEFACT>>>

**Escalation (TEAM §7.8)**
- **Trigger:** the line passes its criteria, but three pre-existing silent allows remain in the classes the Regent decided are fixed here. Each risks losing data under a `**` grant (QA §12):
  - N17: physical mode by `shopt -o`, `eval`, a `set +P` that does not run, `set -o -P`, a heredoc to `bash -P`;
  - N19: git clean's pathspec magic and git's own wildcards;
  - N20: a `.git` file git does not read.
  - N21 is outside the unit and needs no grant at all.
- **Unresolved question:** do N17, N19 and N20 go to the backlog beside N14–N16, or back for a seventh attempt?
- **Evidence:**
  - Risk opinion §2–§5.
  - Probes in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa6/bin/: fx6.py, lines.py, why6.py, one.py, grant6.py, gc6.sh, suite6.sh, mutate6.py.
  - Line files and tables in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa6/: n11-lines.txt, n11-40e1982.txt, n11-0c45883.txt, gc-lines.txt, gc-40e1982.txt, gc-0c45883.txt, n14-lines.txt, n5.txt, mutate6.txt, suite-*.txt, doctor-mine.txt.
  - QA-03/04/05's probes, re-run as they were: /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa6/reg-40e1982/ and /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa6/reg-0c45883/.
- **What I did:**
  - ran the full suite at both commits, in two environments, and the changed self-tests on three Pythons;
  - re-ran doctor in a clone;
  - ran 33 mutations;
  - re-ran every QA-03/04/05 probe;
  - probed N11–N13 beyond their steps against real bash and git's dry run;
  - measured the budget on three large trees.
- **Risk:** under a `**` grant for this repository:
  - `shopt -so physical; cd <outward link> && cd .. && rm -rf x` deletes outside it (N17);
  - `git clean -ffdx ':!keep'` deletes nested clones and bare repositories (N19).
- **Decision needed from the Regent (one of):**
  - **A. Accept the line.** Record N17–N21 as known defects beside the backlog, ratify or reword the drafted norm text (§2), and choose the version.
  - **B. Return to DV for a seventh attempt (the Regent's word only).** At least N17, N19 and N20, and the four cases of §4.
  - **C. Hold on plumbing** until A or B.

EVENT VALIDATION_PASSED grant-latest QA risk-opinion
EVENT ESCALATION_STARTED grant-latest QA grant-cd-physical-option

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
    "ask": "sign the verifiability line of grant-latest attempt 6 with residual risk, and send to the Regent the pre-existing data-loss residues left in the classes decided fixed"
  },
  "body": {
    "verdicts": [
      {"criterion": "N11 as QA-grant-latest-05 wrote it: set -P; cd link && cd .. && rm -rf x and set -o physical; ... ask under delete **", "verdict": "MET", "evidence": ["n11 table: allow at 40e1982, ask at 0c45883 proposing delete <F>/a/b/c/x/**; on the stdin wire too", "bash lands at <F>/a/b/c (pwd -P)", "the DV's 8 variants and 20 more forms ask"]},
      {"criterion": "N12 as QA-grant-latest-05 wrote it: git clean -ffdx -e keep, -e '*.log', -ffdxe keep, --exclude keep ask over the gc fixture", "verdict": "MET", "evidence": ["allow at 40e1982, ask at 0c45883, and on the wire", "git clean -n shows tmp/ and vendor.git/ removed"]},
      {"criterion": "N13 as QA-grant-latest-05 wrote it: git clean -fdx over an untracked bare repository asks", "verdict": "MET", "evidence": ["allow at 40e1982, ask at 0c45883, proposal lists junk/inner.git and vendor.git as git's dry run removes them", "git clean -fdx -e vendor.git src now allowed; git removes only src/"]},
      {"criterion": "the three cases of QA-grant-latest-05 §4 live in the coherence matrix and seen red at the baseline", "verdict": "MET", "evidence": ["the labels are in hook-hazard's self-test; their commands are allowed at 40e1982 and asked at 0c45883", "mutations H1, H10, H13 and H19 turn them red", "N12's case passes on the bare vendor.git alone (H16)"]},
      {"criterion": "the Regent's reading: a cd is logical unless the line itself says otherwise (cd -P, set -P, set -o physical)", "verdict": "PARTIALLY MET", "evidence": ["met for every set -P, set -o physical and bash -P -c form probed", "not met: shopt -so physical, eval 'set -P', set -P then eval, a set +P after || or in an untaken if or a pipe or &, set -o -P, bash -P fed by a heredoc (N17), allowed at both commits"]},
      {"criterion": "what attempts 4 and 5 fixed keeps its verdict", "verdict": "MET", "evidence": ["hz, ko, ex, sib, stack and cdl rows identical at 40e1982 and 0c45883", "N5's six steps and git clean -fdx allowed at both with no repository below"]},
      {"criterion": "N14, N15, N16, N3, N4, N7, N9, N10, R6, D3, D4, D5, R1-R5 neither fixed nor made worse", "verdict": "MET", "evidence": ["N14 rows identical; N10 and N16 simulations identical; ex, hz and ko rows identical", "N15's glob pick unchanged in the diff; D4, R1, R2, R5 files and D5's paragraph untouched"]},
      {"criterion": "no open defect above low introduced by the unit", "verdict": "MET", "evidence": ["197 probe rows compared at both commits: no ask became an allow except git clean -fdx -e vendor.git src, which git's dry run confirms", "the one introduced defect, N18, asks more and is low"]},
      {"criterion": "regression: the line as QA-grant-latest-05 verified it at 63cd097 holds except where N11-N13 change it, and the inherited suite is no worse", "verdict": "MET", "evidence": ["33 self-tests green at both commits in two environments; 3.11 and 3.12 green; no inherited label lost", "doctor re-run in a clone: 0 FAIL, output identical to the gate log"]},
      {"criterion": "criterion 4: judge.md §2 and hooks.md §2 as drafted state what the code does", "verdict": "PARTIALLY MET", "evidence": ["met: physical mode by set -P, set -o physical and bash -P -c; set's letter and -o name rules against real bash; git clean -f and bare repositories as git's dry run shows; the exclude pattern; the 3 s search", "states more than the code: until set +P (N17); as bash reads a set, for set -o -P; git passes whole only a folder whose .git it reads, for a .git file (N20); the paths git reads as its own, for pathspec magic and git's wildcards (N19)", "states less than bash: shopt -o physical, eval, a heredoc to bash -P; judge.md lacks the SHELLOPTS exception"]},
      {"criterion": "the hook's budget: timeout 10 s, onFailure block", "verdict": "MET", "evidence": ["stdin wire, warm cache: 0.62-0.70 s on 208,512 files, 0.80-0.88 s on a 1,000,000-entry folder, 3.06-3.09 s and ask on 1,500,000 files; one deadline shared", "hooks.json unchanged"]}
    ],
    "risk": {
      "measured": [
        {"surface": "physical mode turned on by a form the reader misses, or a set +P it reads but bash never runs (N17)", "consequence": "rm -rf outside the repository runs under a delete ** grant for this one", "likelihood": "low: needs an unusual spelling of physical mode, an outward link, a cd through it and back and a ** grant", "detectability": "none at the time: the guard is silent", "uncertainty": "whether an agent ever types these forms"},
        {"surface": "git clean with pathspec magic or git's own wildcards (N19)", "consequence": "nested clones and bare repositories deleted with their unpushed history", "likelihood": "low to medium: ':!' exclusions and ':/' appear in clean-up lines", "detectability": "none at the time", "uncertainty": "git's dry run stands for the act"},
        {"surface": "a .git file git does not read, above a bare repository (N20)", "consequence": "the bare repository deleted under delete **", "likelihood": "very low: a broken worktree pointer with a bare repository below", "detectability": "none at the time", "uncertainty": "git's dry run stands for the act"}
      ],
      "missing": []
    },
    "findings": [
      {"key": "grant-cd-physical-option", "status": "recurring", "baseline": "40e1982 (= 63cd097 code) on the same fixture and commands", "type": "guard coverage wider than its grant: a removal outside the repository allowed", "severity_input": "medium: D1's class, observed, low likelihood", "priority": "the Regent's: backlog or a seventh attempt", "acts_next": "RGN"},
      {"key": "grant-nested-descent", "status": "recurring", "baseline": "40e1982 on the gc and gitfile fixtures", "type": "claim not met: a git clean reaching a nested clone or bare repository covered by **", "severity_input": "medium: N12's and N13's class, observed by git's dry run (N19, N20)", "priority": "the Regent's: backlog or a seventh attempt", "acts_next": "RGN"},
      {"key": "grant-over-ask-landing", "status": "recurring", "baseline": "40e1982 on the gc fixture", "type": "over-ask: git clean -f with no -d, -X or -n asks where git removes no bare repository", "severity_input": "low: asks more, never less, stated in hooks.md", "priority": "later unit", "acts_next": "RGN"},
      {"key": "hazard-piped-shell", "status": "new", "baseline": "40e1982 and 0c45883 alike", "type": "guard blind spot: a command piped into a shell is not read", "severity_input": "medium: a removal runs with no grant, outside this unit", "priority": "backlog, for the PO", "acts_next": "RGN"}
    ],
    "not_covered": ["zsh setopt chase_links and chase_dots", "Windows and macOS", "a live Claude Code session's shell and snapshot", "a set in a sourced file or profile", "an unprivileged user (J7, N16)", "Python 3.8 to 3.10", "the budget on a cold cache, network file systems or slower machines", "git versions other than 2.43", "the removals themselves (pwd -P and git's dry run stand for them)", "N15 re-fed to the hook", "grant stores other than the session store", "CI for 0c45883", "git rm -r, rsync --delete, mv, submodule deinit, worktree remove"],
    "ambiguities": []
  },
  "doubts": [
    {"doubt": "Do N17, N19 and N20 go to the backlog beside N14-N16 (yes), or back to DV for a seventh attempt (no)?", "key": "gap-residue-disposal", "decides": "RGN"}
  ],
  "artefacts": ["risk-opinion"],
  "terminal": {"state": "ESCALATED", "why": "the line passes its criteria with no defect above low introduced, but pre-existing data-loss residues remain in the classes the Regent decided fixed, on a line past T4, so only the Regent can dispose them"}
}
```

Terminal state: **ESCALATED**. The line passes its criteria as written and introduces no defect above low. But N17, N19 and N20 are pre-existing data-loss residues in the very classes the Regent decided are fixed in this attempt (QA §12), on a line past T4, so only the Regent can accept them as backlog or return the line.