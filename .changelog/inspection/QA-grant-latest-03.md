I'm escalating this line to the Regent instead of signing it. The unit's own change is clean: no regression against the inherited suite, the gate re-runs green, and its named tests go red when the behaviour is removed. Two things stop me signing. First, a pre-existing defect in the span can let a deletion run outside the repository without asking (D1); QA §12 says such a defect is escalated at once. Second, this is the third QA pass, and T4 sends a third failure to the Regent. Version verdict: **break**.

<<<ARTEFACT risk-opinion
# Risk opinion: unit grant-latest, QA verify, pass 3

**What was tested.** Branch plumbing at 0cbf13d. The unit's change is `git diff 954e691 3396665` plus `git diff 5150c86 0cbf13d`: 34 files, all inside guards-line-files.txt, nothing outside the span.

**What I read.** Diffs and file contents only. I read no commit bodies, no CHECKPOINT or HISTORY narrative, and no earlier QA opinion. Two scratch files beside the inputs were not named in the packet (qa-verify-1.md, dv-guards-notes.yaml), and I left them unread.

**Environment.**
- Linux container with git 2.43.0. This git cannot run hooks named in its configuration.
- git-lfs, Python 3.13, gh 2.89.0 and Claude Code 2.1.328 are present.
- This session's own environment sets GIT_CONFIG_* (a cloud git proxy).

**Where the experiments ran.**
- On `git archive` exports of 954e691, 3396665, 5150c86 and 0cbf13d.
- On throwaway repositories with local bare remotes, under my scratch directory, with HOME and TMPDIR pointed there.
- Nothing was written to /home/user/regency. Nothing was pushed anywhere but a local bare remote.

**Criticality assumed.** No PO framed it, so I assumed high. These guards protect `main` and the Regent's data from an agent's own acts, and a guard that fails open does so silently (hooks.md §0). Tolerance assumed: no open defect above low introduced by this unit. Defects that existed before the unit are reported and labelled pre-existing.

## 1. Gate and inherited suite

| Check | Result |
|---|---|
| doctor at 0cbf13d, re-run by QA in a throwaway clone | 0 FAIL, 30 WARN, HEALTHY (same as gate-guards-local.txt) |
| CI at 0cbf13d (gate-guards-ci.txt) | success; the log gives no case counts |
| CI red at 5150c86, reproduced | hook-hazard 217/218 on `cmd /c "cd /d ..\other && git clean -fd"`, in both a clean and the session environment; hook-refs crashed (FileNotFoundError) only under the session's GIT_CONFIG_* |
| span self-tests at 0cbf13d, session environment and cleared environment | all green: guard-push 110, hook-refs 94, hook-hazard 220, hook-journal 11, hook-verbs 39, judge 81, gov 40, returns 47, vp 14, migrate 45, health 63, headless 27 |
| inherited suite at 954e691 | all green: 45 · 97 · 9 · 23 · 38 · 38 · 46 · 13 · 44 · 63 · 26 (hook-refs did not exist yet) |
| inherited case labels at head | every 954e691 label is present at head except two in judge: one renamed (extended), one with a changed meaning. "no path, or an unresolvable one, needs '**'" became "an unresolvable one is covered by nothing", a contract change (see §5) |
| named tests are real | removing the gate fix's backslash rule turns 3 cases red (the two new ones and the CI case). Removing hook-refs' delete check turns 1 red, its force check 2, its agent check 30. Removing guard-push's grant limits turns 10 red; removing hook-hazard's "judged where it runs" turns 25 red |

**Regression:** none found against the inherited suite. Behaviour that changed on purpose is listed in §5.

## 2. Verdict per norm claim

| Claim | Verdict | Evidence |
|---|---|---|
| hooks.md §2: guard-push.py reads the command's text and denies main/master unless a push grant names it | MET | 110/110. Wire probes deny `main`, `'main'`, `ma''in`, `HEAD~0:main`, `@:main`, `-C .`, `( )` and `sh -c`. What passes is the class §2 names: a chain that changes branch first, a substitution, an alias. `git checkout main && git push`, `git switch main; git push origin HEAD`, `$(git branch --show-current)` and `g=git; $g push` are all allowed. One form §2 does not name: D4 |
| hooks.md §2: hook-refs.py on git's pre-push, the `core.hooksPath` way (a git with no hooks in configuration) | MET | 52 real-git cases, 10 pure and 31 install cases ran. On my throwaway remote: an agent's `git push origin main` was held (exit 1, reason printed); the Regent's shell landed; `feat` landed; `--atomic origin feat main` was held. The named bypasses (`-c core.hooksPath=/dev/null`, `--no-verify`) land, as §2 says. `git hook list` is unknown on 2.43, so it fell back as §2 says |
| hooks.md §2: hook-refs.py, the hook-in-configuration way (`hook.regency.*`) | NOT VERIFIABLE (by QA) | 0 cases ran here (git 2.43: "this git has no hooks in configuration: those cases did not run"). CI says success but does not show whether those cases ran |
| hooks.md §2: where the setting is not, a context line says so | PARTIALLY MET | Cloud session: state `occupied`, nothing written, and the context line "no pre-push check here … only the text guard stands over main" (observed). Outside a repository: no context line, though §2 now reads as if one is given (D5) |
| hooks.md §2 (hazardous shell) and judge.md §2 ("Covered"): `**` and every relative glob stop at this repository; a path no script can place is covered by no grant | PARTIALLY MET | 220/220. `"$d"`, `a\ b` and `$( )` now ask under `**`; at 954e691 they did not. Not met: a symlink out of the repository (D1), a repository nested in the work tree (D2), paths with their dots stripped (D3) |
| judge.md: the push grant is the only way past the push guards. It names main or master and stands alone, never covers deletion, and `--all`, `--mirror` and `+` stay refused; a force also needs `history **` | MET on the `core.hooksPath` way | judge 81/81 (parsing, scope, session and repository reach, shell reach, two stores refused). guard-push's GRANTED table. hook-refs on real git: lands under a grant; refuses deletion, master, another session, another repository, `--git-dir`, a bare clone and a linked worktree; refuses a force until `history **` is granted |
| judge.md §4: grant lines come only from the Regent's own words; a message holding a paste records none | MET | judge and hook-verbs self-tests (tags, fences, quotes, pastes, agent reports, unattended runs) |
| conventions §4–§5 | PARTIALLY MET | Enforced as in the rows above. In a session whose environment already sets GIT_CONFIG_*, only the text guard stands (R1). The destructive-act clause carries D1–D3. "The Regent's own line" has no script and none is claimed: the guards still decide, as the text says |
| skills/latest/SKILL.md | NOT VERIFIABLE (behaviour) | The commands it calls exist. gh 2.89.0 has `release list --exclude-drafts --exclude-pre-releases --json` with `isLatest`, `release verify`, `verify-asset` and `download -p -D`. Claude Code 2.1.328 has `plugin list --json`, `marketplace list --json`, `marketplace add/remove` and `install -s user\|project\|local`. The registry entry and its alias are in sync (build --check). Moving an install was not run: no release exists, it needs the network, and it changes the machine |
| library/maintaining.md | PARTIALLY MET | What this machine can show holds. An older git falls back. Under the forwarders, the repository's own hooks, a repository `core.hooksPath`, a hooks path in `~/.gitconfig` and LFS still run. `git lfs install` refuses under `core.hooksPath` in an agent's shell. A session's GIT_CONFIG_* break the self-test unless cleared (5150c86 against 0cbf13d). The git 2.56, Windows and live-session rows cannot be reached here |
| hooks.md §3–§4: the journal and the governance files under `hook_wire.holding` | MET (Linux) | 8 processes writing 25 times each: at head, 200/200 queue lines, 200/200 packets, 200 journal lines, no lock left. The same load at 954e691 kept 96/200 lines and 90/200 packets. The Windows seek-then-write claim cannot be checked here |

## 3. Open defects, by severity

**D1: high, pre-existing, data-loss class (escalated under QA §12).** A `delete **` grant covers a removal that lands outside the repository through a symlink inside it.
- Steps: a repository with `link -> ../outside`; session grant `delete ** -- whole repo`. Then PreToolUse Bash in the repository with each of `rm -rf link/*`, `rm -rf link/`, `find link/ -delete`, `rm -rf link/precious`.
- Expected (judge.md §2: "`**` is the whole repository and never reaches outside it"): the guard asks.
- Observed: allowed, silently, at both 0cbf13d and 954e691.
  - `ls -d link/*` expands to `link/a … link/d`, and `readlink -f` places each of them in `../outside`.
  - The removal itself was not run: the harness's own safety check refused it. The data loss is therefore inferred from how the shell expands the glob; the guard's allow is observed.
- Where it happens: `hook-hazard.resolve` resolves paths by text alone (`normpath`), without following symlinks, and `judge.covers` matches them the same way.

**D2: medium, not a regression (954e691 allowed every git act under `**`).** A repository nested inside the work tree counts as "this repository".
- Steps: `git init nested` inside the repository. With session grant `history ** -- whole repo`: `git -C nested push -f origin side`. With grant `discard ** -- whole repo`: `git -C nested reset --hard` and `cd nested && git reset --hard`.
- Expected (judge.md §2 and hooks.md §2: "a git act is judged where it runs, through its -C too: `**` and every relative glob stop at this repository"): the guard asks.
- Observed: all three allowed. A force push to the nested repository's own remote runs under a grant given for the outer one.

**D3: low, pre-existing.** `judge.relative` strips dots from both ends of a path.
- Steps: with grant `delete env/** -- the env folder`: `rm .env` and `rm -rf .env/x`. With grant `delete .env -- the dotfile`: `rm .env`.
- Expected: `.env` is covered by a glob that names `.env`, and only by one.
- Observed: the `env/**` grant covers both `.env` acts, while the `.env` grant does not cover `rm .env` (it asks). A grant covers a path it does not name.

**D4: low, pre-existing.** guard-push.py lets `git push origin m\ain` through silently.
- The shell reads `m\ain` as `main` (checked: `printf %s m\ain` prints `main`).
- §2's list of what passes the text guard does not name a backslash inside a word.
- On the `core.hooksPath` way, hook-refs holds it. Where hook-refs is absent (R1), it reaches main.

**D5: low (documentation).** hooks.md §2, as the gate fix rewrote it, says: "Where the setting is not: a session opened outside a repository; …; a session whose own environment already sets GIT_CONFIG_* … A context line says so at the session's start."
- Observed: a SessionStart outside a repository answers nothing.
- §1's table promises the line only when the settings are occupied, tracked or unreadable. The two sections disagree on the outside-a-repository case.

## 4. Residual risk and coverage gaps

- **R1: high residual risk, named in the norm, acceptance not recorded.**
  - In any session whose own environment sets GIT_CONFIG_* (every cloud session like this one), hook-refs writes nothing, and only the text guard stands over main.
  - The forms an agent that forgets is likely to type pass it (observed): `git checkout main && git push`, `git switch main; git push origin HEAD`.
  - In such sessions, the promise of conventions §5 rests on guard-push alone.
  - Declaring that area out of coverage is the Regent's call (QA §12, 19.9 L3), and no ratification is recorded.
- **R2.** The hook-in-configuration way was not exercised by QA, and the CI summary does not show that it was. maintaining.md makes it the way for any git that knows `hook.<name>.*`.
- **R3: the known-open rows, with their status confirmed.**
  - A force through an alias is not asked about: `git -c alias.fp='push --force' fp origin feat` is allowed.
  - A cloud command quoted in an untagged paste or quote confirms the write: `kubectl delete ns web` was confirmed, then allowed. A tagged paste does not confirm it.
  - `ratify grants` shows a count, not the rows.
  - `--no-verify` forms the text cannot read skip both guards.
  - A linked worktree under a push grant is refused.
  - `/regency:station` does not report hook-refs.
  - Two rows the criteria name are absent from ROADMAP at 0cbf13d: "a cloud command quoted inside pasted content" and "a stub beside another pre-push". I tested both directly.
    - The first behaves as described above.
    - For the second: on the `core.hooksPath` way, the repository's own pre-push, a failing one, a repository `core.hooksPath`, a global one and LFS all still run beside the check (self-test cases).
- **R4: over-asking.** One `$( )` or backtick anywhere in a line blinds every act in it, so `rm -rf build && echo $(date)` asks under `delete **`. This errs toward stopping, and costs the Regent prompts.
- **R5: lock timeout.** `hook_wire.holding` gives up after 3 s. The journal then appends without trimming, as documented. gov.py then rewrites unlocked, so a loss under long contention stays possible. Not observed.
- **Verification cost.**
  - hook-hazard's coverage rests on a text reader that is taught one shell form at a time: 220 cases, many of them one class.
  - The classes "path through a symlink" and "repository nested in the tree" have no case at all.
  - Object Calisthenics rule 3 applies: a resolved-path type (the real path, plus the git top of each path) would turn each of those families into one case.

## 5. Version verdict: BREAK

- **The grant contract narrowed.** At 954e691, a `**` grant covered a path no script could resolve (`"$d"`, a glob, a `cd` to an unknown place). At 0cbf13d nothing covers it:
  - judge.md's "Covered" paragraph was rewritten;
  - the inherited judge case changed meaning;
  - `rm -rf "$d"` went from allow to ask.

  Consumers: every `**` row in every existing `JD.md`, machine store, named file and session store, and every workflow that relies on them.
- **conventions §4 changed.**
  - The old rule: "an agent never pushes main/master, never force-pushes, never rewrites published history".
  - The new rule: an agent pushes main "only under a `push` grant", and forces or rewrites history "only on the Regent's own line or a `history` grant".
  - `push` left judge.md's "Never granted" list and `judge.NEVER`, and became a grant kind.
- **New behaviour in every repository a session opens in.**
  - SessionStart writes `<git folder>/regency-hooks/`, `.claude/settings.local.json` and a `.git/info/exclude` line.
  - On a git with no hooks in configuration, it also puts every git hook of an agent's shell behind forwarders. `git lfs install` then exits 2 in an agent's shell (documented).
- **The version did not move.** It stayed 3.3 across the line (`library/registry.json` and `.claude-plugin/plugin.json` at 954e691, 3396665 and 0cbf13d). conventions §13 reads a reinterpreted major rule as `+a`. The number is the Regent's to decide.

## 6. Not covered

- The hook-in-configuration way of hook-refs, entirely.
- **Windows and macOS.**
  - The backslash rule depends on `os.name`, and the fix changed behaviour on Linux only, so `cmd /c "cd /d ..\other …"` on Windows is unverified.
  - Also unverified: PowerShell paths, case-insensitive ref files, and the Windows lock and timing claims.
- **Live Claude Code behaviour:**
  - settings `env` reaching a running session's shells;
  - the `if: git *` matcher;
  - whether a `!` command's shell carries the session variables;
  - `onFailure: block`.
- `/regency:latest` end to end, and `gh release verify` / `verify-asset` against a real release (none exists).
- The removal through a symlink itself: refused by the harness, and inferred from the glob's expansion.
- Submodule pushes (`--recurse-submodules`) through hook-refs.
- A hand-edited, ratified `push | **` row. `judge.matches` would read it as covering main and master, while a grant line refuses `push **`. Seen in the code, not run.
- The content of CI's log beyond its conclusion.
- **Prose-only files of the span.** These were checked by doctor only (paths, frontmatter, generated tables), not read line by line for accuracy: README, REFERENCE, CLAUDE.md, migrations/README, the arrange-cycle-commit, update, regency and judge skills, and headless.json.
- .changelog/ and ongoing.json: withheld narrative, not judged.
- The other unit's commits (3396665..5150c86).

## 7. Assumptions (TEAM §7.5)

- **Criticality.**
  - Assumption: criticality is high, and the tolerance is "no open defect above low introduced by this unit".
  - If false: at a lower criticality, D2 and R1 could be accepted without escalation.
  - Validated by: the Regent stating the criticality.
- **CI.**
  - Assumption: CI at 0cbf13d ran the same doctor as the gate log.
  - If false: the CI green says nothing about hook-refs on git 2.56.
  - Validated by: the hook-refs line of the CI log, with its case count.

## 8. Verifiability line

Not signed by QA. The line goes to the Regent for three reasons:
- D1 carries a risk of data loss (QA §12: escalate immediately).
- R1 and R2 are areas the gate would close without proof.
- This is the third QA pass, and T4 sends a third failure to the Regent.

QA does not give "approved with residual risk" on its own authority. If the Regent accepts, it is approved with residual risks R1–R5 and defects D1–D5 open.
ARTEFACT>>>

**Escalation (TEAM §7.8)**
- **Trigger:** D1, a defect in the span that risks losing data (QA §12), and the third QA pass on this line (T4).
- **Unresolved question:** may the guards line move past plumbing with D1–D5 open and R1 not accepted?
- **Evidence:** risk opinion §2–§4. The probe scripts are `hz.py`, `ko.py`, `par.py`, `setup.sh` and `lands.sh` in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3/bin/, and the doctor re-run is in /tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3/doctor-mine.txt.
- **What I did:**
  - ran the inherited suite at 954e691 and the span suite at 0cbf13d, in both environments;
  - re-ran the gate;
  - reproduced the CI red at 5150c86;
  - mutated the guards' rules to check their tests go red;
  - probed on exports and throwaway repositories.
- **Risk:** D1 is a silent deletion outside the repository under a `delete **` grant. R1 is main pushed in cloud sessions by an agent that forgets.
- **Decision needed from the Regent (one of):**
  - **A. Accept.** Record D1–D5 as known defects for a later unit, accept R1 and R2, and choose the version: 4.0 for the break, or keep 3.3.
  - **B. Return to DV.** This goes beyond T4's two loops, so only on the Regent's word. At least D2, which is this line's own claim; D1, D3 and D5 too if wanted in this line.
  - **C. Hold on plumbing.** Wait until the hook-in-configuration way is shown green, either by the CI log's hook-refs count on git 2.56 or by a run on the Regent's machine; then A or B.

EVENT ESCALATION_STARTED grant-latest QA risk-opinion

Two notes on my own runs:
- **Safety check.** The harness's safety check refused two of my commands because they held `rm -rf`. I re-ran neither: I showed the symlink case without deleting anything, and ran the mutations in fresh copies, which needed no removal.
- **Repository.** /home/user/regency is still clean, on plumbing at 0cbf13d, with no stash and no `regency-hooks` folder.

suba-validator envelope (checked: `python scripts/returns.py check --suba suba-validator -` → "suba-validator: shape holds"):

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
    "key": "grant-glob-symlink-escape",
    "ask": "sign or refuse the verifiability line of grant-latest with D1 to D5 open and R1 unaccepted"
  },
  "body": {
    "verdicts": [
      {"criterion": "hooks.md §2: guard-push.py denies main/master on the command text unless a push grant names it", "verdict": "MET", "evidence": ["guard-push selftest 110/110 at 0cbf13d, both environments", "wire probes on a throwaway repository: named forms denied, the named classes pass"]},
      {"criterion": "hooks.md §2: hook-refs.py refuses main/master on git's pre-push, core.hooksPath way", "verdict": "MET", "evidence": ["hook-refs selftest 94/94: 52 real-git cases on core.hooksPath", "throwaway bare remote: agent push of main held, the Regent's shell lands, --atomic held, named bypasses land"]},
      {"criterion": "hooks.md §2: hook-refs.py, the hook-in-configuration way", "verdict": "NOT VERIFIABLE", "evidence": ["git 2.43 here: 0 of those cases ran; the CI summary gives no case count"]},
      {"criterion": "hooks.md §2: where the setting is not, a context line says so", "verdict": "PARTIALLY MET", "evidence": ["cloud environment: occupied, nothing written, context line given", "outside a repository: no context line (D5)"]},
      {"criterion": "judge.md §2 and hooks.md §2: ** and every relative glob stop at this repository; a path no script can place is covered by no grant", "verdict": "PARTIALLY MET", "evidence": ["hook-hazard selftest 220/220; $d, backslash and $( ) now ask under **", "probes: symlink out of the repository allowed (D1), nested repository allowed (D2), dot-stripped paths (D3)"]},
      {"criterion": "judge.md: the push grant is the only way past both push guards; never deletion; force also needs history **", "verdict": "MET", "evidence": ["judge selftest 81/81", "guard-push GRANTED table", "hook-refs real-git grant cases on core.hooksPath"]},
      {"criterion": "conventions §4 and §5 as they stand at 0cbf13d", "verdict": "PARTIALLY MET", "evidence": ["enforced as above", "a session whose environment sets GIT_CONFIG_* has only the text guard (R1)", "destructive-act clause carries D1 to D3"]},
      {"criterion": "skills/latest/SKILL.md: move an install to the newest release, never back, never a branch", "verdict": "NOT VERIFIABLE", "evidence": ["CLI surface present in gh 2.89.0 and Claude Code 2.1.328", "no release exists; the move was not run"]},
      {"criterion": "library/maintaining.md: the git and Claude Code facts the guards rely on", "verdict": "PARTIALLY MET", "evidence": ["older-git fallback, forwarders, LFS refusal and the self-test's GIT_CONFIG_* clearing observed", "git 2.56, Windows and live-session rows not reachable here"]},
      {"criterion": "hooks.md §3 and §4: journal and governance files under hook_wire.holding", "verdict": "MET", "evidence": ["8 processes x 25 writes: 200/200 at head; 96/200 queue lines at 954e691"]}
    ],
    "risk": {
      "measured": [
        {"surface": "delete ** grant over a symlink that leaves the repository (D1)", "consequence": "files outside the repository removed without the Regent's ask", "likelihood": "low: needs a ** grant and a path through an outbound symlink", "detectability": "none at the time: the guard is silent", "uncertainty": "the removal itself was not run; inferred from the glob's expansion"},
        {"surface": "cloud sessions: only the text guard over main (R1)", "consequence": "main pushed by an agent that forgets, through a chain that changes branch first", "likelihood": "medium: the chain form is common", "detectability": "after the fact, on the remote", "uncertainty": "whether the host's branch rules stand behind it was not checked"}
      ],
      "missing": ["the PO's or the Regent's criticality and maximum tolerable severity for this unit"]
    },
    "findings": [
      {"key": "grant-glob-symlink-escape", "status": "new", "baseline": "954e691 inherited suite and the same probes", "type": "guard coverage wider than its grant", "severity_input": "high: data-loss class", "priority": "before any further widening of ** grants", "acts_next": "RGN"},
      {"key": "grant-nested-repo-scope", "status": "new", "baseline": "954e691 inherited suite and the same probes", "type": "claim not met: ** reaches a nested repository", "severity_input": "medium: a force push to another remote", "priority": "this line's own claim", "acts_next": "RGN"},
      {"key": "grant-dot-strip", "status": "new", "baseline": "954e691 inherited suite and the same probes", "type": "path normalisation", "severity_input": "low", "priority": "later unit", "acts_next": "RGN"},
      {"key": "push-text-backslash", "status": "new", "baseline": "954e691 guard-push on the same form", "type": "unnamed bypass of the text guard", "severity_input": "low", "priority": "later unit", "acts_next": "RGN"},
      {"key": "doc-context-line-outside-repo", "status": "new", "baseline": "hooks.md §1 against §2 at 0cbf13d", "type": "documentation disagrees with behaviour", "severity_input": "low", "priority": "with the next edit of hooks.md §2", "acts_next": "RGN"}
    ],
    "not_covered": ["hook-refs on a git with hooks in configuration", "Windows and macOS", "live Claude Code session behaviour", "/regency:latest end to end and gh release verify against a real release", "the removal through a symlink itself", "submodule pushes through hook-refs", "the CI log beyond its conclusion", "prose-only files of the span beyond doctor's checks"],
    "ambiguities": [{"criterion": "criticality and maximum tolerable severity of grant-latest", "nearest_checkable": "the Regent states criticality high or normal and the highest severity that may stay open at merge to testing"}]
  },
  "doubts": [
    {"doubt": "Does the Regent accept that sessions whose environment sets GIT_CONFIG_* rest on the text guard alone over main: yes or no?", "key": "gap-cloud-push-guard", "decides": "RGN"}
  ],
  "artefacts": ["risk-opinion"],
  "terminal": {"state": "ESCALATED", "why": "a data-loss-class defect in the span (QA §12) and the third QA pass on the line (T4) put the decision with the Regent"}
}
```

Terminal state: **ESCALATED**. A defect in the span risks losing data (QA §12), and this is the third QA pass on the line (T4), so the decision is the Regent's.
