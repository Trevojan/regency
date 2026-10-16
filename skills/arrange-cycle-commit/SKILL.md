---
name: arrange-cycle-commit
description: "Regency arrange-cycle-commit. Split the finished work into small, described commits (feat, fix, docs, add, test kept apart), merge up to main following the project's documented branch contract, then push every branch except main. Never pushes main: the Regent does, and a hook enforces it. Use for /regency:arrange-cycle-commit, or when the Regent says commite, mescle, 'commit and merge', 'prepare the merge', 'separe os commits'."
argument-hint: "[scope]"
disable-model-invocation: true
---

# arrange-cycle-commit — split, commit, merge up to main, push the branches (never main)

> **Root.** This file is `skills/arrange-cycle-commit/SKILL.md`; the regency root is two
> directories above it. Paths like `library/…` are relative to that root. Read
> `library/conventions.md` §4 (Git) and locate the project's documents with `library/layouts.md`.

## 0. Preconditions

Run `git status` and `git branch --show-current`. Stop and say so if this is not a git repository.

1. **Learn the project's branch contract** from its docs (the entry index, `AGENTS.md`, a "branch
   flow" section): which branch carries which kind of work, what merges onto what, what the
   verification command is, and any rule such as "code commits carry no new tests" or "tests are a
   separate pass". Quote the rule you are applying. If the contract is not documented, **ask**
   (pop-up) before merging; committing on the current branch needs no such answer.
2. **Whose changes are these?** List every modified/untracked file. Group them into: (a) work done in
   this session, (b) everything else. Stage only (a). Files in (b) belong to the Regent: leave them
   untouched and unstaged, and name them in the report. If a file mixes both, ask.

## 1. Split

Group (a) into the smallest coherent commits, one purpose each:

| Type | For |
|---|---|
| `feat` | a new capability the user can perceive |
| `fix` | a defect repaired (always its own commit) |
| `docs` | guideline, plan, changelog, README changes |
| `add` | a new file or resource with no behaviour yet |
| `test` | tests only — never inside a code commit unless the compiler forces the adaptation |
| `refactor` / `chore` | structure or tooling with no behaviour change |

Order them so each commit builds and passes on its own ("one step per commit, green at each step").
Format-only differences ride with the commit that touched the lines.

## 2. Commit

For every commit: stage exactly its files (`git add <paths>`, never `-A`/`.`), run the project's
verification command if it is quick and available, then commit with a message that states **what
changed and why**, in the project's language and commit style (read `git log` for it). Body in
detail for anything non-obvious. End the message with the attribution line the harness requires.

Never use `--no-verify`, never amend a commit that is not yours from this run, never rewrite
history, never create a worktree.

## 3. Merge up to main

Follow the contract from §0, branch by branch, in the documented direction. Prefer the project's
stated method (fast-forward vs merge commit). After each merge run the verification command.
Conflicts: resolve only the ones inside your own commits' files; anything else → stop and ask.
Do not merge onto `main` unless the contract says that is the next step.

## 4. Push the branches — never `main`

After the commits and merges, push **the branches this run touched, except `main`/`master`**:

1. **Check the remote and the branch.** Use `origin` unless the project documents another remote. No
   remote → skip the push and say so. Skip a branch that is already level with its remote.
2. **Ask first when a push is more than a push.** If the project docs say that pushing a branch
   triggers a pipeline — a build, a migration, a deploy, anything on cloud or production — do not
   push it: put it in a pop-up (pushing it is a cloud-adjacent act, `library/conventions.md` §5–§6)
   and let the Regent decide. Read the branch flow documents for this; do not guess.
3. **Push plainly:** `git push -u origin <branch>`, one branch per command, so each can succeed or
   fail on its own. Never `--force`, `--force-with-lease`, `--all`, `--mirror`, `--delete`; never
   tags unless the order asks for them.
4. **A rejection stops that branch.** Non-fast-forward or any refusal: report it with the message and
   leave it for the Regent. Do not retry with force, and do not rebase to make it fit.
5. **`main` is never pushed by an agent.** A hook (`scripts/guard-push.py`) blocks it; do not look for a
   way around it, and do not push `main` under another name (`HEAD:main`, `refs/heads/main`). When
   `main` is ready, say so: the push is the Regent's act.

## 5. Report

```text
Commits   <n>   – <hash> <subject> (one line each)
Merged    <branch> → <branch> … (or "none: <why>")
Verified  <command> → green | red <where>
Pushed    <branch> → origin (or "none: <why>"; branches held back for a pipeline: <list>)
Untouched your uncommitted files: <list> (not staged)
Ready     main is at <hash>; push is yours.
Assumed X because the order did not say Y. Next time: <rewritten order>.   ← only if you assumed
```

## Boundaries

No push of `main`/`master`, no force, no tags unasked, no history rewrite, no worktree, no staging of
others' changes, no cloud or production command (a push that starts a pipeline counts as one), no merge
outside the documented contract.
