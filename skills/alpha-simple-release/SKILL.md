---
name: alpha-simple-release
description: "Regency alpha-simple-release. Cut a bounded release for the Regent to test: an annotated tag alpha-### on one pinned commit (normally testing) carrying its manifest - scope included and excluded, build, artefacts, how to check it, known limits, the analytics lane's open findings - plus the source exported and built under .alpha/, which never enters a commit. Pushing the tag waits for the Regent's yes. Use for /regency:alpha-simple-release, 'cut an alpha', 'give me a build to test'."
argument-hint: "[ref] [what the Regent wants to test]"
disable-model-invocation: true
---

# alpha-simple-release — one pinned commit, one bounded scope, for the Regent to try

> **Root.** This file is `skills/alpha-simple-release/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` and `scripts/…` are relative to that root. Read `library/conventions.md` once per
> session; the model is `library/analytics.md` §6.

A capsule is a tag, not a branch: it never moves, and it merges into nothing. This command touches no branch,
commits nothing and never pushes `main`.

## 0. Preconditions

1. A git repository; the version gate, `python scripts/migrate.py gate` (conventions §10).
2. `python scripts/vp.py drafts` exits 0 when the ref is `testing` or `main`: an unverified draft never ships in
   a capsule past `plumbing`. A capsule of `plumbing` is allowed and its manifest says so in `limits`.

## 1. The manifest

```bash
python scripts/alpha.py plan [--ref <ref>] > <scratchpad>/alpha.json
```

Fill every `<…>` from the project's documents (the branch flow, the build or run instructions, `mise.toml` when
the station has one) and from what the Regent asked to test. Ask the Regent (one pop-up) only for what the
documents leave open: the scope included, what is left out on purpose, and whether to build here. Never invent
a build command: when none is documented, leave `build.command` empty and say so.

## 2. Cut

```bash
python scripts/alpha.py cut <scratchpad>/alpha.json [--build]
```

The script refuses a placeholder left in, an id that already exists and an empty scope. A red build is
reported with its exit and the missing artefacts; the tag stays (a capsule never moves) and the next attempt is
the next id.

## 3. Publish — only on the Regent's yes

Pushing the tag publishes the release: ask first (pop-up). On yes, `git push origin <alpha-###>`, one tag, never
`--tags`. A rejection is reported, never forced.

## 4. Report

```text
Alpha     alpha-### · <ref>@<sha7> · included <list> · excluded <list>
Files     .alpha/alpha-###/source · build green | red (exit <n>, missing <list>) | not run
Check     <the steps from the manifest>
Tag       local | pushed | held: <why>
Next      the Regent tests; their notes go to /regency:repository-analytics-delta as material
```

## Boundaries

No branch created or moved, no commit, no push of `main`, no build command the project's documents do not give,
no reuse of an existing id.
