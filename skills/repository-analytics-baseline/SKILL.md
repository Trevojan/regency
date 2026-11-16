---
name: repository-analytics-baseline
description: "Regency repository-analytics-baseline. One full analysis pass on the orphan analytics branch: an isolated agent wearing suba-recon reads the spec on main and the code on testing or plumbing at two pinned commits, and returns gaps, diagnostics, findings and suggestions; the pass is recorded as AN-## without touching the working tree. Use for /regency:repository-analytics-baseline, the first pass of a project, a new subsystem or an architecture change."
argument-hint: "[scope paths] [spec=<ref>] [code=<ref>]"
disable-model-invocation: true
---

# repository-analytics-baseline — the first full pass on the analytics lane

> **Root.** This file is `skills/repository-analytics-baseline/SKILL.md`; the regency root is two directories
> above it. Paths like `library/…` and `scripts/…` are relative to that root. Read `library/conventions.md` once
> per session; the model is `library/analytics.md`.

The pass separates the analysis from the coding: an isolated agent reads, this session records, and the coding
agent later reads only the brief of its own files. Nothing here edits the working tree, writes an axis, merges or
pushes `main`.

## 0. Preconditions

1. A git repository with a guidelines root (`library/layouts.md` §1). None → say so and stop: the spec is the
   guidelines.
2. The version gate: `python scripts/migrate.py gate` (conventions §10).
3. When a remote exists, `git fetch origin analytics` (an absent branch is not an error), so the pass number
   follows the lane the Regent already has.
4. `python scripts/analytics.py status`. Branch `absent` → ask the Regent once (pop-up): create the orphan
   `analytics` lane? Only a yes adds `--create-branch` in §3.

## 1. The packet

```bash
python scripts/analytics.py plan --mode baseline [--spec <ref>] [--target <ref>] [--scope <path> ...]
```

`spec=` and `code=` in the arguments map to `--spec` and `--target`; bare paths are the scope. Defaults: spec
`main`, code `testing`, else `plumbing`. When `code_files.list` is `null` the scope is past the listing limit:
ask the Regent for the folders (pop-up, options from `code_files.by_folder`), then plan again.

## 2. The analyst

Dispatch **one** agent (Agent tool, general-purpose, foreground) with this prompt, the packet pasted whole:

```text
Wear suba-recon in direct mode. Read library/subagents/suba-recon/SKILL.md (sections "Direct mode" and
"Return to the caller") and library/subagents/ALIGNMENT.md §4-§5, relative to the regency root <root>.
Read the spec and the code only through the packet's git commands at its two SHAs: no checkout, no file
written, no commit. Answer every id in "recheck" in "carried". Return only the envelope.
PACKET:
<the packet JSON>
```

## 3. Check and record

1. Save the agent's final message to a file in the scratchpad, then
   `python scripts/returns.py check --suba suba-recon --direct <file>`.
2. Misses → send them back once to the same agent (SendMessage). A second miss stops the command: report it
   (T4: two loops at most).
3. Record, with the session's attribution lines as trailers:

```bash
python scripts/analytics.py record <file> [--create-branch] --trailer "<Co-Authored-By line>" --trailer "<session line>"
```

## 4. Push the lane

`git push -u origin analytics` — one plain push; never `--force`. A rejection stops the push: report it with its
message (the remote holds a pass this clone has not fetched). No remote → say so.

## 5. Report

```text
Pass      AN-## baseline · spec <ref>@<sha7> · code <ref>@<sha7> · scope <paths | whole>
Findings  <n>: gaps <g> · diagnostic <d> · findings <f> · suggestions <s>
Carried   still <n> · cleared <n> · unanswered <n>
Lane      analytics @ <commit7> · pushed | not pushed: <why>
Next      /regency:repository-analytics-triage · a coder reads `python scripts/analytics.py brief <paths>`
```

## Boundaries

No checkout, no edit of the working tree, no write into an axis (triage does that, on the Regent's word), no
merge of `analytics` into anything, no push of `main`, no second analyst for the same pass.
