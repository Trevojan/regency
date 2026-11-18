---
name: repository-analytics-triage
description: "Regency repository-analytics-triage. The Regent disposes the live findings of the analytics lane, in pop-ups: promote (written into its axis on the working branch through that axis's own contract), recycle (re-checked by the next delta) or trash (with its reason). Records every disposition on the analytics branch. Use for /regency:repository-analytics-triage, after a baseline or a delta, or when the residue of the lane piles up."
argument-hint: "[finding ids or pass id]"
disable-model-invocation: true
---

# repository-analytics-triage — review, recycle or trash the residue

> **Root.** This file is `skills/repository-analytics-triage/SKILL.md`; the regency root is two directories
> above it. Paths like `library/…` and `scripts/…` are relative to that root. Read `library/conventions.md` once
> per session; the model is `library/analytics.md` §5.

A finding of the lane is residue until the Regent disposes of it. **Only the Regent triages**: this command asks,
records the answers and writes what a promotion needs. It decides nothing itself.

## 0. Preconditions

1. When a remote exists, `git fetch origin analytics`.
2. `python scripts/analytics.py status`: the `live` lines are the queue. None → say so and stop. An argument
   narrows the queue to those ids, or to one pass (`AN-##`).

## 1. Ask — through the engine

The questions are generated, asked and checked by the elicitation engine (`library/elicitation.md` §4), so a
disposition exists only once the Regent picked it in the pop-up:

```bash
python scripts/analytics.py triage-schema [<ids> | --pass AN-##] > <scratchpad>/triage.json
python scripts/elicit.py start <scratchpad>/triage.json --task triage-<YYYY-MM-DD>
python scripts/elicit.py next --session EL-#### --wave 4
```

Pass `ask.questions` to the pop-up exactly as given; `python scripts/analytics.py show <id>` gives a finding whole
when the Regent asks for it. Per finding the engine asks the disposition (Promote, Recycle, Trash), then only the
question that follows from it: the axis of a promotion, or the reason of a trash. Repeat `next` until `complete`.
The hook records each answer and refuses a re-ask; when the Regent changes an answer in chat,
`python scripts/elicit.py reopen --session EL-#### --question <id> --because "<their words>"`, then ask again.

Read the marked option **and** the free text of every answer (conventions §3): a free text can change the
destination, cut the answer short or say do not proceed.

## 2. Record

```bash
python scripts/analytics.py triage --from-elicit EL-#### --trailer "<Co-Authored-By line>" --trailer "<session line>"
```

Only the answers the Regent confirmed are recorded; a finding still `undecided` stays live. When `undecided` comes
back empty the session has served: close it, `python scripts/elicit.py reset --session EL-####`. Typed assignments
(`analytics.py triage ID=STATE[:ARG] ...`) remain for a surface that delivers no answers to the hook, and only
with the Regent's words quoted in the report.

Then `git push -u origin analytics` (plain; a rejection is reported, never forced).

## 3. Promote

Each promoted finding is written into its axis **on the working branch**, as that axis's README asks, citing the
finding id; never copied whole (conventions §7):

| Destination | Lands as |
|---|---|
| `.plan` | an item under *Authorised by the Regent, not yet built*: what exists, what is missing |
| `ledger` | a `backlog` item in `.shortcuts/.virtual/ongoing.json` with `source` pointing at the finding |
| `.decisions` | a row in today's dated section, the Regent's reason quoted from the answer |
| `.constraints` | a row in *Of the artefact*, only with the Regent's words; otherwise the unratified list of `.decisions/` |
| `.sources` | a row whose *decided* column says what it decided; a diagnostic that decided nothing is not promoted |

These are ordinary documentation edits: nothing here commits them. `/regency:arrange-cycle-commit` does, on the
Regent's word.

## 4. Report

```text
Triaged   <n>: promoted <p> · recycled <r> · trashed <t>
Written   <axis file#anchor> ← <id> (one line each), uncommitted
Lane      analytics @ <commit7> · pushed | not pushed: <why> · live <n>
Next      /regency:arrange-cycle-commit for the axis edits
```

## Boundaries

No disposition without the Regent's answer, no edit of a pass folder (an act), no promotion that rewrites an
accepted decision silently (conventions §3: that stops and asks), no commit of the axis edits.
