---
name: virtualpath
description: "Regency virtual paths and work ledger. Query the code-to-norm lineage registry with scripts/vp.py (which norm slices govern a code file, which code a slice governs, which slices are STALE, whether everything still resolves) and read or reconcile the work ledger (.virtual/ongoing.json): what is ongoing versus backlogged, plus every trace of agent work in the repo. Use for /regency:virtualpath[:code|slice|stale|check|ongoing|trace|drafts], before editing governed code, and FIRST when returning to a repository: 'what is ongoing', 'what did the agents leave', 'resume'."
argument-hint: "<code|slice|stale|check|ongoing|trace|drafts> [argument]"
---

# virtualpath — the lineage between norms and code

> **Root.** This file is `skills/virtualpath/SKILL.md`; the regency root is two directories above it.
> `library/…` and `scripts/…` paths are relative to that root. Read `library/virtualpath.md` for the
> model; this file is only the procedure.

A project may keep a **manifest** (`.shortcuts/.virtual/manifesto.json` or `manifest.json`, found by
`library/layouts.md`) linking each **norm slice** (an anchor inside a guidelines document) to the code
that slice governs. It is written for the agent: it gets you from a file to its rules, and from a rule
to its files, without searching the repository.

## Commands (all read-only; run from anywhere inside the project)

```bash
python <regency-root>/scripts/vp.py code  <code path>           # norms that govern this file
python <regency-root>/scripts/vp.py slice <virtual_path> --show # code it governs, and the slice text
python <regency-root>/scripts/vp.py stale                       # STALE warnings waiting for the Regent
python <regency-root>/scripts/vp.py check                       # every slice and target resolves?
python <regency-root>/scripts/vp.py ongoing                     # the work ledger: ongoing / draft / review / blocked / backlog
python <regency-root>/scripts/vp.py trace                       # every trace of agent work: git, guidelines, orders
python <regency-root>/scripts/vp.py drafts                      # unverified speed-mode drafts; exit 1 while one remains
```

Add `--manifest FILE` or `--repo DIR` if auto-discovery picks the wrong place. If no manifest exists,
say so in one line: the project does not use virtual paths; do not create one.

**Exact queries** (`library/virtualpath.md` §6) — JSON lines for the harness, once `idx.py build` has run:

```bash
python <regency-root>/scripts/idx.py governs <path>:<line>   # slices governing that exact node (manifest or citation)
python <regency-root>/scripts/idx.py node <path>[:<line>]    # node ids, line and byte ranges, hashes
python <regency-root>/scripts/idx.py get <id>                # one node's exact bytes
python <regency-root>/scripts/idx.py check                   # unresolved slices, missing nodes, relink proposals
python <regency-root>/scripts/idx.py shortcuts               # the prose index, ledger, STALE and latest Order, resolved
```

Read the bytes a node id points to instead of re-reading a whole file or re-deriving where a rule
lives. Relink proposals from `check` are proposals: the manifest changes only when the Regent says so.

## When to use it

| Moment | Do |
|---|---|
| **Before editing** a code file in a project that has a manifest | `code <file>`, then read the slices it lists (`slice <path> --show`). They are norms the edit must respect. |
| **After editing** | `code <file>` again: those slices may now be out of date. Report them; do not clear them. |
| **Opening a session / planning** | `stale` for the list of norms waiting for a human check. |
| **Before sharing** | `check`. Report problems; do not "fix" the manifest unasked. |

## The work ledger — first peek on returning (`ongoing`, `trace`)

`.shortcuts/.virtual/ongoing.json` says what is **ongoing** and what is only **backlog** (model and
schema: `library/virtualpath.md` §3). When you return to a repository, in this order:

1. `ongoing` — read the ledger. If it is absent but `.virtual/` exists, say so and offer to create it
   from `library/templates/guidelines/.guidelines/.shortcuts/.virtual/ongoing.json` (only with a yes).
2. `trace` — gather what agents leave behind: uncommitted files, unmerged branches, stashes, recent
   commits, recently touched guidelines, `STALE` lines, Orders.
3. **Reconcile.** An `ongoing` item whose evidence is gone is a **ghost**; evidence with no item is
   **orphan work**; an old claim with no recent commit is a **stale claim**. Report each with its
   evidence and ask the Regent about every one that is a decision. Never adopt orphan work silently and
   never promote `backlog` to `ongoing` on your own.
4. `drafts` — when the ledger or `trace` shows a draft: every unverified speed-mode draft, ledger item and
   commit. A draft is verified only by a `/regency:team` pass over its unit (`library/team/SPEED_MODES.md`
   §6); report the list, never promote a draft by hand.
5. Keep the ledger true as you work, without asking: `ongoing` + `where` (evidence) when you start an
   item, `next` at each boundary, `review` (never `done`) when you finish, removal of `done` items at
   handoff, and `updated` set. It points to the document with the detail and never copies it.

## What you may and may not do

- You may read slices, report staleness, and quote the slice you relied on.
- A `STALE` warning line **comes out only when a human has checked the slice against the code**. An
  agent never deletes it, and never edits a norm slice to make it "match" the code. If the code is right
  and the norm is wrong, that is a decision for the Regent (state it, propose the edit, do not make it
  silently).
- `on_mutation: lock` slices are hard constraints: a change that contradicts one is refused, not
  negotiated. `mark_stale` slices warn. (`reconcile`, an agent rewriting the norm itself, is
  deliberately not part of the model: an agent does not ratify a norm.)
- Do not edit the **manifest** (`manifesto.json`) unless asked; the project's own gate regenerates and
  validates it. The **ledger** (`ongoing.json`) is the opposite: it is yours to keep current.

## Report

```text
File      <code path>
Governed by   <virtual_path> [selector, on_mutation]   (one line each)
Read      <slices you read before editing>
Now stale <slices that this change makes out of date>
Problems  <from check, or none>
```
