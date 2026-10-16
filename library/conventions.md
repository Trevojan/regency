# Conventions — how the Regent works

Defaults for every `/regency` command. They travel with this folder, so any Claude Code
instance behaves the same way without prior conversation.

**Precedence, highest first:** the user's message in this session → the project's own
`CLAUDE.md` / `.guidelines/` documents → this file → a skill's built-in default. A project
document that contradicts a line here wins for that project; say so in one line and follow it.

## 0. Rule zero — Mastery spares Synthesis

*Domínio evita Síntese.* Whatever can be transcribed into a script, a template, a registry entry, a
hook or a short note **is** transcribed, and the agent reads it instead of inferring it again. The less
the harness has to fill gaps, the better both sides perform.

- A rule that a script can check is checked by a script (`scripts/conventions_check.py`, `scripts/doctor.py`).
- A rule that must hold at the moment of a tool call is a hook: the trigger lives in `hooks/hooks.json`,
  the engine is a script in `scripts/` (`library/hooks.md`).
- Script output is **sliced**: one finding or one subject per line or per short file, so a reader takes the
  slice it needs instead of reconstructing the whole. Slices are also the recovery path when something goes off.
- When a prose instruction keeps being re-explained, that is the signal to turn it into code or a template.

## 1. People and labels

- **RGN** is the **Regent** (*Regente* in Portuguese): the human behind the account. Only that
  person is a bare `RGN`. A Regent decides; an agent measures, proposes and refuses, and
  **never ratifies a norm it wrote**.
- Other humans carry the prefix so a role is never confused with a person: `RGN-PO` (the
  product's human owner), `RGN-Client`, `RGN-DA`, `RGN-DV-<n>` for other developers on the
  team. The project glossary names who is who.
- `PO`, `DV`, `QA`, `DA` **without** the prefix are the agent roles (the lenses). Never write a
  bare "PO" when a decision belongs to a human owner: write `RGN-PO`.
- The agent set that serves the Regent is called the **TEAM**. The Regent calls the AI side **AA**
  (*Advanced Algorithm*).

## 2. Language

Choose by who the reply is for:

| The reply is for | Language |
|---|---|
| the Regent, in the working chat | English — European English, not US |
| a public post, README or anything published | English (European) |
| an enterprise / client project | the project's own language (PT-BR where the project is Brazilian) |

When the Regent's message switches language, it is usually to reduce translation noise: follow it.
Project glossaries beat habit: use the project's terms and never a word the glossary bans.
User-facing text in a product is **terse and objective**, with no developer notes, annotations or
explanations leaking into the screen. In Brazilian Portuguese write *sua/seu*, never *tua/teu*.
Visual defects (borders, misplaced or misaligned elements) are what a client notices first: fix them
before anything cosmetic or optional. The path-scoped copy of these lines is `library/rules/ui-text.md`.
A project's frontend is documented in `<guidelines>/.ux/`, scaffolded by `/regency:ux-init` and started
from its brief; a UI rule changes there first, then in code.

## 3. Doubts, pop-ups and how far to go

- **Queue doubts; keep working.** A doubt that does not block goes into the project's
  open-questions queue (blockers first). Only a true blocker stops the work.
- **Exception: a documented decision.** If the work would reverse an accepted ADR, a business
  rule or a stated scope, stop and ask **now** with a pop-up. Do not undo a decision silently.
- **Ask in pop-ups** (the interactive question tool) whenever a decision is the Regent's:
  at least two options, a free-text way out, concise. Read **both** the marked option and the free
  text of every answer — the free text may add a change, cut an answer short, or say *do not proceed*.
  If an answer is cut off, ask the cut part again. Do the side-requests hidden in an answer.
- **Record answers** in the project's docs, with the date, marking the newest answer as the one in
  force and pointing back to the one it replaces.
- **"Proceed" and its synonyms** (*prossiga*, *siga em frente*, *continue*, *vá em frente*, *bora*)
  mean: work the **whole queue** until a blocker or an empty queue — not one task.
- Never deduce what the Regent did not say. When unsure whether something was already said, **search
  the project docs and the handoff first**, then cite the source and its date. If the docs are silent,
  that is a gap to report, not to fill.

## 4. Git

- **"Commit"** means small, split commits, each with a descriptive message: `feat`, `fix`, `docs`,
  `add`, `test`, kept apart (the Regent cannot follow 100% of generated code, so separation is the
  review aid). Work stays on the branch/working tree in use; never create a worktree on your own.
- **"Commit and merge"** additionally merges the branches up to `main` following the project's
  documented branch contract. If the contract is not documented, ask before merging.
- **The Regent pushes `main`.** An agent never pushes `main`/`master`, never force-pushes, never rewrites
  published history; a hook (`scripts/guard-push.py`) enforces the first. `/regency:arrange-cycle-commit`
  may push the *other* branches it touched (plain `git push -u origin <branch>`, no tags, no `--all`), and
  asks first when the project says pushing that branch triggers a pipeline or deploy. When `main` is ready,
  say so.
- Stage only the files that belong to the work. Other uncommitted changes in the tree are the
  Regent's: leave them untouched and unstaged.
- One step per commit, verification green at each step. Format-only differences (spaces,
  indentation, alignment) are *non-impactful convention*: run the formatter, follow what it does,
  do not go back to check. Parameters, methods, classes, instances, folders, files, names and
  functions are what matter.

## 5. Environment and permissions

Without asking, an agent may: read, search, edit inside the task, run the build, tests, linters, the
app, containers and local servers, and kill its own stray processes.
Ask first before: deleting, force operations, "danger-zone" commands, changing worktree or branch
layout, installing system software, and **anything that touches cloud, production or shared data**.
`scripts/hook-hazard.py` asks for the destructive ones before they run and, once one has run, keeps
file writes waiting for the Regent until the Regent says a release verb (§9; `library/hooks.md` §2).

## 6. Scope and ownership

- The Regent's scope is **application code, UX, diagrams, database/migration rules and data
  visualisation**. **Cloud** (accounts, IAM, secrets, build, deploy, infrastructure) belongs to its
  owner: advise only. Read pasted logs, explain the cause, and write the exact request for the owner.
  Cloud CLIs may **read** freely (list, get, describe, logs, plan). A cloud **write** runs only when the
  Regent quoted that exact command in a message of the current pass (the work between two of the
  Regent's messages); `scripts/hook-hazard.py` denies every other one.
- In a repository or dataset the Regent does not own: study and document on a separate branch, apply
  no fixes, do not edit shared configuration (`CLAUDE.md`, pipelines, queries owned by others), and ask
  before touching anything outside the Regent's own code.
- Resolve ownership from the project docs first; ask when they are silent.

## 7. Documents

- `.guidelines/` (or the project's equivalent) is the **memory that travels with the repository**.
  Anything important is written there, because a fresh context knows nothing else.
- **Update the guidelines at the end of each task** (not after every edit), and list which documents
  moved. A handoff updates the shortcuts index and the project state file, not a new loose file.
- **The index points, it never copies.** A fact in two places means one of them is wrong.
- **State the present, never the correction.** Text that said "this is A" becomes "this is B"; it does
  not gain "no longer A". Remove what no longer matches; version control is the record.
- Documents before code: a rule changes in the norm document first, then the code.
- **Acts are never rewritten**: ladder plans, gate sheets (`GT-##`), opinions, closed Orders (`ORD-####`)
  and dated handoffs. Add a new one instead; `scripts/hook-acts-guard.py` refuses the rewrite. The
  path-scoped copy of this section is `library/rules/guideline-docs.md`.
- Do not create files nobody asked for. Smallest sufficient answer first; depth on request.

## 8. Reporting

- **Status** is a topic list with sub-topics: **done / left / blocked**, each with a **percentage and
  fraction** (`60% — 6/10`). The goal is orientation: where we are, where we go, how far.
- Numbers come with their method. A figure without a method is an estimate wearing a number.
- **Assumption line.** When an order was vague and a choice had to be made, end the reply with one
  line: `Assumed X because the order did not say Y. Next time: <rewritten order>.` Only when something
  was really assumed.
- Writing for people (reports, emails, specs): write to be read — concrete, no filler, every sentence
  doing work; third person and technical register for documents handed to a stakeholder.

## 9. Verbs the Regent uses (what they mean here)

`scripts/hook-verbs.py` reads this table: a short message opening with one of these verbs gets its
command named in context, and a release verb ends the hazard watch. Edit the table here, never in a script.

| Says | Means | Command |
|---|---|---|
| prossiga, siga, continue, bora | work the whole queue | `/regency:proceed` |
| commite, mescle | split commits, merge up to main, push the other branches (never main) | `/regency:arrange-cycle-commit` |
| vê isso, diga o que mudaria, mede | report what would change; apply nothing | `/regency:measure-changes` |
| handoff, retomada, resumo | close the stretch and hand the state over | `/regency:order:handoff` |
| retome | reopen from the shortcuts index only | `/regency:order:resume` |
| chame o TEAM | one orchestrated pass | `/regency:team` |
| libere, release | end the hazard watch: file writes stop asking | `hook-hazard.py --clear` |

## 10. Returning to a repository

Work resumes from **traces**, not from memory. On returning to a project:

1. **First peek: the work ledger** (`.shortcuts/.virtual/ongoing.json`, `python scripts/vp.py ongoing`):
   what is `ongoing`, what is `review`, `blocked`, and what is merely `backlog`. The session already
   opens with a one-line resume slice (ledger counts, STALE lines, latest Order, last checkpoint) from
   `scripts/hook-resume.py`.
2. **Gather every trace of agent work** (`python scripts/vp.py trace`): uncommitted files, unmerged
   branches, stashes, recent commits, recently touched guidelines, `STALE` lines, Orders, and the
   checkpoint journal (`python scripts/hook-journal.py --tail 20`).
3. **Reconcile** the two (ghosts, orphan work, stale claims — `library/virtualpath.md` §3) and ask the
   Regent about anything that is a decision. Never adopt orphan work silently.
4. Then read the project's entry index and go to the line.

While working, keep the ledger true without asking: it is the agent's own index. Details of the model:
`library/virtualpath.md` §3.

## 11. Task granulation

The Regent breaks a solution into four levels named on a **Big-O** basis: **O4** the Solution (no
nickname), **O3** Modules `M##` (decoupled features), **O2** Steps `D##` (the *degrau* of the development
ladder, dependent concepts) and **O1** Tasks `T##` (one code file). A task is conducted through seven
fixed, numbered Phases **F0–F6**, bound to the Business Rules, and every commit builds. Full protocol:
`library/task-granulation.md`.

## 12. Ids

Every prefix regency uses — `M##.D##.T##`, `O1`–`O4`, `F0`–`F6`, `GT-##` (gates), `UX-UI-##` (UI rules),
`ORD-####` (Orders), `C-##` (conflicts), the `RGN` labels — is defined once, with its grammar, in
`library/ids.md`. A new id is added there before it is used; `scripts/conventions_check.py` validates
the grammar.

## 13. Versioning

regency itself is versioned **`a.b`**, with no cap on either part (`99.999` is valid):

- **`+b`** — a content change.
- **`+a`** — a major rule finished, reinterpreted or invented.

`library/registry.json` and `.claude-plugin/plugin.json` carry the same value; doctor fails when they differ.
Application code governed by the Regent's projects keeps its own scheme (`a.b.c.dd+e`); `a.b` is for
long-running conventions such as this plugin.

## 14. Naming

- Banned name tokens, in paths and in Python `def`/`class` names: `Base`, `Abs`, `Mgr`, `Helper`,
  `Common`, `Utils`. Name by role, never by value. `scripts/hook-acts-guard.py` refuses a new path
  that carries one.
- Canonical documents are `UPPER_CASE` (`AGENTS.md`, `CLAUDE.md`, `PROTOCOL.md`, `TEAM-ORCHESTRATION.md`,
  `LADDER_*`, `README.md`, `CHANGELOG.md`, `BRIEFING.md`).
- `suba-<name>` is a subagent and its folder goes under library/subagents; `<name>-vendor` is a capability
  a subagent consumes and its folder goes under library/vendors; any other hyphen-case name is a skill.
  `scripts/conventions_check.py` fails a `suba-` or `-vendor` folder found anywhere else.
- regency's own code is Python, standard library only.
