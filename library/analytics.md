# Analytics — analyse once, keep the evidence, read only what a task needs

Decided with the Regent on 2026-11-16: an `analytics` lane beside the branch contract, one folder per pass, the
analyst is suba-recon in direct mode, an alpha release is a tag with its manifest. Engines: `scripts/analytics.py`
(the lane) and `scripts/alpha.py` (the release). Commands: `/regency:repository-analytics-baseline`,
`/regency:repository-analytics-delta`, `/regency:repository-analytics-triage`, `/regency:alpha-simple-release`.

## 1. The problem it removes

A coding agent that returns to a repository rebuilds its understanding of it before the first line: which spec
applies, what the code already does, where the two disagree. Done inside the coding session, that work fills the
context the code needs, and it is done again by the next agent. The lane moves it out:

| Concern | Lives in | Survives in |
|---|---|---|
| the code | `plumbing` → `testing` → `main` (conventions §4) | the branches |
| the understanding of the code against the spec | an analysis pass, made by an isolated agent | the `analytics` branch |
| what the Regent accepts of that understanding | the axes on the working branch, through triage | `.plan/`, `.decisions/`, `.constraints/`, `.sources/`, the ledger |

A pass is **residue until triaged**: it is never a norm, nothing cites it as binding, and every finding ends
promoted, recycled or trashed.

## 2. The lane

`analytics` is an **orphan branch**: it shares no history with the code, so git refuses to merge it anywhere by
accident, and `/regency:arrange-cycle-commit` never touches it. It is written only by `analytics.py`, with git's
plumbing commands on a temporary index: the working tree, the current branch and the Regent's uncommitted files
are never touched. Creating it is a branch-layout change: the commands ask the Regent once (conventions §5).

```text
README.md                         generated: what the lane is, the passes, the live findings
<guidelines>/.analytics/
  INDEX.json                      every pass and every finding's current state (the only file that changes)
  AN-03/                          one pass: written once, never rewritten (an act)
    manifest.json                 mode, the two pinned commits, scope, previous pass, what was re-checked
    findings.json                 the analyst's envelope body: the canonical findings
    gaps.md                       generated view: kind gap
    diagnostic.md                 generated view: kind diagnostic
    findings.md                   generated view: kind finding
    suggestions.md                generated view: kind suggestion
```

The four views are the Regent's four categories. They are generated from `findings.json` (F4): one finding has one
id (`AN-##-##`, `library/ids.md`), one evidence trail and one state, whichever view shows it.

## 3. Two pinned commits

A pass compares **the spec** at a commit of `main` (the guidelines root there) with **the code** at a commit of
`testing` or `plumbing`. Both SHAs go into the manifest; the analyst reads both through `git show <sha>:<path>`,
never from the working tree, so a pass states exactly what it compared and stays true after both branches move.

| Mode | Reads | Runs when |
|---|---|---|
| baseline | every spec document and the code in the scope | the first pass; a new subsystem; an architecture change; a delta that would read most of the repository |
| delta | the files changed since the previous pass's code commit, the guideline files changed since its spec commit, and the live findings either touches | after a stretch of work, a failed review or an alpha the Regent tested |

`analytics.py plan` builds the packet deterministically from git. A delta with nothing changed on either side
stops there: **no pass, no inference**. A live finding whose files and spec slice did not change stays valid
without being read again — that is the amortisation.

## 4. The analyst

suba-recon in direct mode (`library/subagents/suba-recon/SKILL.md`, *Direct mode*), dispatched as **one isolated
agent** with the packet, so the coding session receives the recorded pass and none of the reading. It reads,
never writes; its return is one envelope `returns.py` checks against `returns_direct`.

| Kind | View | Holds | Default destination when promoted |
|---|---|---|---|
| `gap` | `gaps.md` | the spec asks, the code lacks | `.plan/` (or the ledger's backlog) |
| `diagnostic` | `diagnostic.md` | how a part behaves, with the command that shows it | `.sources/`, only if it decides something |
| `finding` | `findings.md` | a defect, or a constraint the code breaks | the ledger (a defect) or `.decisions/`'s unratified list (a constraint candidate) |
| `suggestion` | `suggestions.md` | a decision only the Regent can take | `.decisions/`, dated, once the Regent decides |

`observed` holds what is seen; `inferred` holds what is concluded. Every finding names `where` at the code commit
and `evidence` (the command and what it showed). Its `key` feeds `gov.py recur` like any return (ALIGNMENT §4): a
class of finding that keeps coming back is the signal to transcribe it into a check (conventions §0).

## 5. States and triage

| State | Set by | Means |
|---|---|---|
| `open` | `record` | untriaged; read by `brief` |
| `recycled` | the Regent, at triage | kept for the next delta to re-check; read by `brief` |
| `promoted` | the Regent, at triage | written into its axis on the working branch through that axis's own contract; `to` names the slice |
| `trashed` | the Regent, at triage | discarded with a one-line reason (nothing disappears in silence) |
| `cleared` | `record` of a delta | the analyst observed it no longer holds at the newer code commit |

Only the Regent triages (`/regency:repository-analytics-triage`, one pop-up per batch). Promoting is not copying:
the agent writes the axis entry the axis's README asks for, cites the finding id, and the commit is ordinary docs
work for `/regency:arrange-cycle-commit`.

## 6. Alpha simple release

A bounded state of the application for the Regent to exercise: one commit (normally `testing`), one scope.

| Part | Where |
|---|---|
| the pin | the annotated tag `alpha-###` on that commit; a tag never moves, so the capsule never drifts |
| the manifest | the tag's message: id, ref and SHA, scope included and excluded, build command, artefacts, known limits, how to check it out, open findings of the lane at that commit |
| the files | `<repo>/.alpha/alpha-###/`: `source/` from `git archive`, the build's output and `build.log`; `.alpha/` ignores itself and never enters a commit |

Pushing the tag publishes it, so `/regency:alpha-simple-release` asks first. The Regent's notes on the release are
material for the next `/regency:repository-analytics-delta`; feedback about an excluded part is backlog, not a
failure of the capsule.

## 7. What the next agent reads

`python scripts/analytics.py brief <path> [<path> ...]` prints, one line each, the live findings whose `where` or
`against` touches those paths; `analytics.py show AN-##-##` prints one finding whole. A coding agent reads the
brief of the files of its task, not the passes: the archive stays on the branch, the brief is the retrieval.

## 8. What it refuses

- **A pass per commit.** A pass costs inference; it pays only when reused. Small isolated changes need none.
- **Writing into the axes from a pass.** Findings reach an axis only through triage.
- **Merging `analytics`.** It holds no code; it has no history in common with anything that does.
- **Rewriting a pass.** A wrong finding is trashed with its reason; a newer pass supersedes, it never edits.

## 9. Operating

| Need | Command |
|---|---|
| the packet for a pass | `python scripts/analytics.py plan --mode baseline\|delta [--spec main] [--target testing] [--scope PATH ...]` |
| record the analyst's return | `python scripts/analytics.py record FILE\|- [--create-branch] [--trailer LINE ...]` |
| passes and live counts | `python scripts/analytics.py status` |
| live findings for these files | `python scripts/analytics.py brief PATH ...` |
| one finding whole | `python scripts/analytics.py show AN-##-##` |
| the Regent's dispositions | `python scripts/analytics.py triage AN-##-##=promoted:<path#anchor> AN-##-##=recycled AN-##-##=trashed:<reason> ...` |
| cut an alpha | `python scripts/alpha.py plan [--ref testing]`, then `python scripts/alpha.py cut MANIFEST [--build]` |
| list the alphas | `python scripts/alpha.py list` |
| health | `python scripts/analytics.py --selftest`, `python scripts/alpha.py --selftest` (doctor runs both) |
