---
name: measure-context-reconstruction
description: "Regency measure-context-reconstruction. Read-only: how much of what each session reads was already read, unchanged, by an earlier session - the context rebuilt from scratch - with the ratio per session, the in-session repeats, and the files most often re-read unchanged, as the candidates to transcribe into the entry index, a brief or a script. Numbers come from the reads hook-reads.py journals, with their method. Use for /regency:measure-context-reconstruction, 'how much context do we rebuild', 'where do the tokens go on resume'."
argument-hint: "[sessions=<n>] [top=<n>]"
disable-model-invocation: true
---

# measure-context-reconstruction — measure the rebuild before building anything against it

> **Root.** This file is `skills/measure-context-reconstruction/SKILL.md`; the regency root is two directories
> above it. Paths like `scripts/…` are relative to that root. The measure is described in `library/shortcuts.md`
> §8.

This command changes nothing. It turns the Regent's estimate ("40% of usage gathers the same context") into a
number with its method, for this project, so what gets built against it is chosen by measurement
(conventions §15.1, rung 1).

## 1. Measure

```bash
python scripts/reconstruction.py report [--sessions <n>] [--top <n>]
```

`no read journalled yet` → the hook records from the next session on; say so and stop. A project without
`.shortcuts/.virtual` journals nothing: offer `/regency:init`.

## 2. Read the numbers

| Line | Means | When it is high |
|---|---|---|
| `carried` and `ratio` | content an earlier session already read, unchanged, read again | the entry index, the ledger or a brief does not carry what sessions need: transcribe it |
| `repeated` | the same lines read twice in one session | the agent lost track inside the session: a slice or a shorter file helps |
| `rebuilt <path>` | a file re-read unchanged in that many sessions | the first candidate for a shortcut row, an analytics brief or a `locate-with-fts5` query |

## 3. Report

```text
Window    <n> session(s) · read <KB> (~tokens) · carried <KB> · ratio <%> · repeated <KB>
Rebuilt   <path> × <sessions> (one line each, the top ones)
Proposal  <one line per rebuilt file: the cheapest rung that would carry it - an index row, a brief, a script>
Method    <the method line, as printed>
Not measured  Bash reads, Grep and Glob output, tool results, the system prompt, the prompt cache
```

Offer exactly one next command and do not run it.
