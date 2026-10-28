# ⟨project⟩

⟨One sentence saying what this project is. Then one sentence saying what the source of truth is and what
derives from it.⟩

## Start here — always

**[`.guidelines/.shortcuts/README.md`](.guidelines/.shortcuts/README.md)**

It is the index: where the work stopped, what comes next, and which document answers which question. It
**points and never copies**, and this file does the same on purpose. Do not rebuild by inference what is
one shortcut away.

| axis | holds |
|---|---|
| [`.decisions/`](.guidelines/.decisions/) | what has been decided, by whom, and why |
| [`.plan/`](.guidelines/.plan/) | what comes next, and what was put off |
| [`.orders/`](.guidelines/.orders/) | the Orders — the contract that dispatches the work. **One open at a time** |
| [`.constraints/`](.guidelines/.constraints/) | what the project forbids itself — **read before proposing** |
| [`.changelog/`](.guidelines/.changelog/) | how the version number moves |
| [`.sources/`](.guidelines/.sources/) | the external references that decided something |

## Verify

```bash
⟨the verification command⟩
```

⟨What it runs.⟩ **One step per commit, green at each one.**

⟨If a file is generated from another, say here which is the source, which is the copy, and which command
rebuilds it — before someone edits the copy.⟩

## Two constraints that catch every new agent

The full set is in [`.constraints/`](.guidelines/.constraints/README.md). These two change what you do in
the first hour:

- **⟨the constraint of this project that costs most to find out late⟩**
- **State the present, never the correction.** Text that said "this is A" **becomes** "this is B"; it
  does not gain a "no longer A, now B". Accumulated micro-corrections become residue the reader infers
  and throws away, because they do not help the final state. Where retirement has to act, it acts on the
  mechanism, not on the prose.

## Vocabulary

- **Regent** — who decides. An agent measures, proposes and refuses; it does not ratify.
- **⟨term coined here⟩** — ⟨what it means in this project⟩