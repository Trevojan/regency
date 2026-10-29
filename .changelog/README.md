# .changelog — how regency got here, and where it stands

This folder is enough for a model with no prior context to wear the harness and know the road so far.
The code states the present; this folder holds the path, the reasons and the next stop.

## If you just arrived

Read in this order, and stop as soon as you have what the task needs:

| # | File | Gives you | Cost |
|---|---|---|---|
| 1 | [`CHECKPOINT.md`](CHECKPOINT.md) | the version in force, the branches, what is live, what is pending, the next step | one screen |
| 2 | [`../CLAUDE.md`](../CLAUDE.md) | how to work in this folder: start here, every command, the map | one screen + the command table |
| 3 | [`../library/conventions.md`](../library/conventions.md) | how the Regent works; binds every command | long; read the section the task touches |
| 4 | [`ROADMAP.md`](ROADMAP.md) | the north star, the method chain with what is built, the queue, the open doubts | two screens |
| 5 | [`HISTORY.md`](HISTORY.md) | every version, newest first: what it added, the Regent's decisions behind it, the proof | read one version at a time |

Terms you will meet: **the Regent** (RGN) is the human who decides; **AA** is the AI side; **PO, DV, QA, DA** are
the four team roles (`library/team/`); a **unit** is `M##.S##.T##` with an optional phase span `[F1–F3]`
(`library/ids.md`); **R13.2** names the Regent's decision 2 of record 13 (`HISTORY.md` lists them);
**N14** names an open doubt (`ROADMAP.md`).

## The version rule

regency is versioned `a.b` (`library/conventions.md` §13):

| part | moves when |
|---|---|
| `a` | a major rule is finished, reinterpreted or invented |
| `b` | any content change |

No cap on either part. `library/registry.json` and `.claude-plugin/plugin.json` carry the same value; doctor
fails when they differ. An installed plugin refreshes only when the version changes.

## What each version decided

One line per version: the decision, not the file list. Detail in [`HISTORY.md`](HISTORY.md).

| version | what it decided |
|---|---|
| **2.13** | the public face: purpose description, the `S##` step, an SDK-style homepage, MIT, community files and CI, this folder; one line of history, old branches archived |
| **2.12** | one line of work: four split copies consolidated; R7's shortcuts on idx's one store; health checks version and copies |
| **2.11** | `/regency:health`: the Regent's checkup, a check per part, engines ratified or restored, heartbeats |
| **2.10** | `/regency:update` and the version gate: a project and the harness must agree before anything writes |
| **2.9** | the app's own sources are English, and checked |
| **2.8** | an Emission lives in its Orders (`position`); speed-mode fixes ship forward |
| **2.7** | speed modes: seed the whole terrain first, cultivate after; drafts stay DRAFT/UNVERIFIED on plumbing |
| **2.5–2.6** | suba lenses with return contracts, the return gate, the exact index (built in other sessions; read from the code) |
| **2.4** | the shortcuts engine on the old line; superseded by 2.12's port |
| **2.3** | the hazard watch scoped to the project; PO/QA write permits; the simplest sufficient (§15) |
| **2.2** | `/regency:ux-init`: a project's frontend documentation scaffold on the Regent's palette |
| **2.1** | hooks are triggers, scripts are engines: guards, recorders, the hazard watch, cloud writes only on the Regent's quoted command |
| **2.0** | rule zero, the conventions, the id grammar, the doctor; the customisation of upstream 1.2 begins |

## Writing here

- When the version moves: add its section on top of `HISTORY.md`, its row on top of the table above, and
  rewrite `CHECKPOINT.md` in place. `scripts/conventions_check.py` (`changelog`) fails until all three name the
  version in force.
- A released version's section is never rewritten (forward-only, V2); a correction goes in the next one.
- One subject, one place: a fact already held by a playbook, a library file or the git log is pointed at, not
  copied. This folder carries the *why* and the *order*; git carries the line-by-line.
- The question to ask when closing any change: **where else was this written?**
