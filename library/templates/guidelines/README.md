# guidelines-template

A starting point for a new project: the `.guidelines/` structure on six axes, with the root files
already pointing at it.

It solves one problem. When what a project has learnt lives in the agent's memory or in the chat
history, it **does not travel with the repository**: a fresh context window opens with nothing pointing
anywhere, and the first hour goes on rebuilding by inference what was already decided. `CLAUDE.md` at the
root is what the harness reads on its own; it points to the index, and the index points to the rest.

## The axes

`.guidelines/` holds the details that raise **mastery** over inference as the project's load grows in
context.

| axis | holds |
|---|---|
| `.sources` | external references actually used — and what each one **decided** |
| `.decisions` | decisions taken, who took them, and why |
| `.plan` | what comes next, and what was put off |
| `.orders` | the Orders — the contract that dispatches the work, immutable and numbered |
| `.constraints` | what the project forbids itself |
| `.changelog` | what changed, and how the version number moves |
| `.shortcuts` | **the index** — the entry point that points to everything else |

The four in the middle are a cycle: **decide → schedule → commission → record.** Beside them sits
`.history`, which **is not an axis**: it is the attic, the place that makes removing something different
from deleting it.

**The dot in front of the name is deliberate.** It marks a low-level path, read by the harness and not by
whoever opens the repository to see what the project does. The root keeps the front doors; the thinking
stays in `.guidelines/`.

The aim: on resuming, decipher **only the previous step, the current one and the next**. Everything else
is reached by shortcut.

## Use it

1. **Use this template** on GitHub, or clone it and delete its `.git`.
2. Fill in the `⟨…⟩`. They are the only holes, and each one says what it expects.
3. Start in the order that avoids rework:

   | first | because |
   |---|---|
   | `CLAUDE.md` | it is what the agent reads without being told. While it has holes, every new session starts blind |
   | `.shortcuts/README.md` | "Where I am" and "the map in five lines". The rest can wait for the first real decision |
   | `.constraints/README.md` → **Of the artefact** | the other three tables come filled in: they are the method, and they do not change from project to project |
   | the rest | when there is something to record. An empty axis is honest; an invented one lies |

4. Delete this `README.md` and write your project's own.

## The rules the structure carries

They live in the files, not here, but three of them decide whether the thing works:

- **The index points, it never copies.** If a fact is in two places, one of them is wrong and nobody
  knows which.
- **Prose states the present, never the correction.** Text that said "this is A" becomes "this is B".
  Accumulated micro-corrections become residue the reader infers and throws away.
- **An agent never ratifies a norm it wrote.** It measures, proposes and refuses.

## What this template is not

It is not a task manager or a substitute for an issue tracker. `.plan/` holds what is **open and
decided**, not the whole queue of ideas. Nor is it a place for reports: what closed leaves the plan and
becomes a line in the changelog. The exception is `.orders/`, where a closed Order **stays**, because it
is the contract of what was delivered.

It does not try to guess your domain either. Every axis may stay empty, and empty is honest; invented
lies.