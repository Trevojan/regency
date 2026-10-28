# Shortcuts — start here

> **The entry point.** Whoever resumes the project reads this file first and only then opens what they
> need. The aim is that only **the previous step, the current one and the next** need deciphering;
> everything else is reached by shortcut instead of being rebuilt by inference.
>
> This index **points**. It never copies. If a fact is in two places, one of them is wrong and nobody
> knows which.

## Where I am

| | |
|---|---|
| version | ⟨fill in⟩ |
| suite | ⟨the command, and whether it is green⟩ |
| last milestone | ⟨what has just been finished⟩ |
| next | ⟨what comes next — or a link to `.plan/`⟩ |

## The axes

> **The dot in front of the name is deliberate.** It marks a low-level path, read by the harness, not by
> the person who opens the repository to see what the project does. The root keeps the front doors; the
> thinking stays here.

| axis | what it holds |
|---|---|
| [`.sources/`](../.sources/) | external references actually used, and what each one **decided** |
| [`.decisions/`](../.decisions/) | decisions taken, who took them, and why |
| [`.plan/`](../.plan/) | what comes next, and what was put off |
| [`.orders/`](../.orders/) | the Orders — the contract that dispatches the work, immutable and numbered |
| [`.constraints/`](../.constraints/) | what the project **forbids itself** |
| [`.changelog/`](../.changelog/) | what changed, and how the version number moves |
| `.shortcuts/` | this file, and [`.virtual/`](.virtual/README.md) — the agent's first peek: what is ongoing, what is only backlog, and which norm governs which code |

The four in the middle are a cycle, and that is the order to read them in:
**decide → schedule → commission → record.**

[`.history/`](../.history/) sits beside them and **is not an axis**: it is the attic, where a superseded
document leaves the reading path without leaving the repository.

## The project's map, in five lines

> Five lines, no more. If it does not fit in five, the rest is a document, not a shortcut, and it goes to
> the axis it belongs to.

1. ⟨which file is the core, and what consumes what⟩
2. ⟨what the source of truth is, and which are its projections⟩
3. ⟨what **cannot** be the source of truth, and why⟩
4. ⟨how the project treats the incomplete case — an error, or a question?⟩
5. ⟨where every format change passes, and what it is measured against⟩

## The documents consulted most

> The left column is **the question the person has**, not the document's title. Whoever resumes a
> project knows what they want to know; they rarely know where it was written.

| when the question is | open |
|---|---|
| ⟨"…?"⟩ | ⟨`FILE.md`⟩ |

## The project's vocabulary

> Only the terms coined **here** — the ones a reader would not find outside this repository. A term in
> public use does not go in.

- **⟨term⟩** — ⟨what it means in this project⟩