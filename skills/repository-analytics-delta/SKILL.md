---
name: repository-analytics-delta
description: "Regency repository-analytics-delta. A follow-up analysis pass on the analytics branch: only the code changed since the previous pass, the guideline files changed on main, and the live findings either touches are re-read by an isolated agent wearing suba-recon; nothing changed means no pass and no inference. Takes the Regent's notes on an alpha release as material. Use for /regency:repository-analytics-delta, after a stretch of work, a failed review or an alpha the Regent tested."
argument-hint: "[scope paths] [spec=<ref>] [code=<ref>] [notes]"
disable-model-invocation: true
---

# repository-analytics-delta — re-read only what moved

> **Root.** This file is `skills/repository-analytics-delta/SKILL.md`; the regency root is two directories
> above it. Paths like `library/…` and `scripts/…` are relative to that root. Read `library/conventions.md` once
> per session; the model is `library/analytics.md` §3.

A delta reuses everything the previous passes established and re-reads only what changed. It never edits the
working tree, writes an axis, merges or pushes `main`.

## 0. Preconditions

Those of `/regency:repository-analytics-baseline` §0, in the same order. `status` with no pass → stop and offer
`/regency:repository-analytics-baseline`: a delta needs a previous pass.

## 1. The packet

```bash
python scripts/analytics.py plan --mode delta [--spec <ref>] [--target <ref>] [--scope <path> ...]
```

| Packet says | Do |
|---|---|
| `nothing_changed: true` and `recheck: []` | report `nothing changed since AN-##: no pass` and stop — the cheapest pass is the one not run |
| `code_changed.list` or `spec_changed.list` is `null` | the change is past the listing limit: offer the baseline instead (pop-up) |
| otherwise | go on; `still_valid` findings are not re-read |

The Regent's notes in the arguments (an alpha's feedback, a review remark) are material for the analyst: add
them to the prompt verbatim, under `NOTES`, with the alpha id when they come from one (`alpha-###`).

## 2. The analyst

Dispatch **one** agent (Agent tool, general-purpose, foreground), as in the baseline's §2, with the delta packet
and this line added to the prompt:

```text
This is a delta: read only "code_changed", "spec_changed" and the files of the findings in "recheck".
NOTES (the Regent's words, quoted; omit when none):
<notes>
```

## 3. Check, record, push

The baseline's §3 and §4, unchanged. `record` re-derives which live findings the delta had to answer; any it
did not answer stays live and is reported as `unanswered`.

## 4. Report

```text
Pass      AN-## delta of AN-## · spec <ref>@<sha7> · code <ref>@<sha7>
Read      code changed <n> · spec changed <n> · re-checked <n> · still valid without reading <n>
Findings  <n>: gaps <g> · diagnostic <d> · findings <f> · suggestions <s>
Carried   still <n> · cleared <n> · unanswered <n>
Lane      analytics @ <commit7> · pushed | not pushed: <why>
Next      /regency:repository-analytics-triage
```

## Boundaries

The baseline's, plus: a delta never reads a file the packet did not name, except a spec slice that a named file
cites.
