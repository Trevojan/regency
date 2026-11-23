# Blocks — tested code the Agent calls instead of writing

A routine operation (the next id of a series, a version bump, one value in a JSON file) is written once, tested once,
and from then on **called**. The Agent no longer turns the Regent's words into fresh code, so a call needs no test of
its own: the block's selftest already proved it, and `scripts/doctor.py` proves it again on every run. The playbook is
`skills/blocks/SKILL.md`; the runner is `scripts/blocks.py`; the catalogue is `scripts/blocks/`.

## 1. A block

One file, `scripts/blocks/<id>.py`, named by role (conventions §14), holding three names and nothing else the runner
reads:

| Name | What it is |
|---|---|
| `CARD` | what the block does, its arguments, who confirms (§2) |
| `run(args, root)` | pure: reads what it needs under `root`, returns `{"summary", "result", "writes"}`; refuses by raising `ValueError("one line")` |
| `selftest(tmp)` | plants inputs under a fresh temporary folder, calls `run()`, asserts on every result and every refusal |

`run()` never writes. Each entry of `writes` is `{"path", "text", "detail"}`, and the runner is the only writer: it
checks each path stays inside the root, then writes through a temporary file and an atomic replace.

## 2. The card

| Field | Meaning |
|---|---|
| `id` | the file name; the runner refuses a card whose id differs |
| `intent` | one line, as `find` should match it |
| `when` | the phrases an intent is asked in; their words are what `find` scores |
| `args` | `name: {type, default, choices, help}`; type is `str`, `int`, `bool` (yes/no), `path`, `list` or `paths` (comma-separated); no default means required |
| `confirm` | `read`, `agent` or `regent` (§3) |
| `regent_if` | optional: `{arg: [values]}` raises the level to `regent` when the argument holds one of them; `["*"]` means "given at all" |
| `returns` | the shape of `result` |

The runner checks every argument against the card before `run()` sees it: an unknown key, a missing required one, a
wrong type, a value outside its choices, or a path that leaves the root (a trust boundary, conventions §15.3) is
refused in one line.

## 3. Confirmation

| Level | Who confirms | The runner |
|---|---|---|
| `read` | nobody: nothing is written | runs; a read block that returns writes is refused |
| `agent` | the Agent, inside the task (conventions §5) | writes at once and prints one `WRITE` line per file |
| `regent` | the Regent, in one pop-up | prints the plan, a `TOKEN`, the pop-up as `ASK` (JSON ready for the question tool) and the `ON-APPLY` line; exits 2 and writes nothing |

The token is a hash of the block, its arguments, every target file's current bytes and the text to be written. The
Regent's Apply is bound to that plan: if an argument or a file changes after the pop-up, `--yes` refuses and the plan
is shown again. The token proves the plan applied is the plan the Regent saw; that the yes came from the Regent rests
on the playbook, as every pop-up in regency does.

## 4. Layers

The runner reads regency's `scripts/blocks/` and then the project's own `<root>/scripts/blocks/`, where a project keeps
its code. A project block with the id of a regency block replaces it for that project, and every output
line names the layer (`regency` or `project`), so the replacement is never silent. A project block runs only from the
project's own folder: it is the project's code, trusted as its tests are.

## 5. Adding a block

1. The trigger is measured, not guessed: the same intent written as code a second time, or a `find` that came back
   `NONE` for an intent already seen.
2. `blocks.py run block-new id=<id> intent="<one line>" [confirm=read|agent|regent]` — regent level, because it creates
   a file (AR9). It scaffolds the card, a `run()` that refuses and a `selftest()` that fails until written.
3. Fill `when`, `args`, `run()` and `selftest()`. `blocks.py test <id>` must print `OK`; a regency block is also
   run by `blocks.py --selftest`, which `scripts/doctor.py` calls, so a failing block fails doctor.
4. Commit it apart (`add`), with its selftest, under the task it served.

## 6. Not a block

- **One line does it** (conventions §15.1, rung 6): a block would be machinery around nothing.
- **A git or cloud act**: deletes, history, pushes and cloud writes are judged by the hooks and the Regent's grants
  (`library/judge.md`), not by a block. A block writes text files under the root, nothing else.
- **A judgement**: which commit type, whether a change is a fix. A block computes; it never decides.
- **A question with parameters**: slots, dependencies and invalidation belong to the elicitation engine
  (`library/elicitation.md`). A block's confirmation is one yes on one plan.

## 7. Output and exit codes

One subject per line (conventions §0, sliced output):

| Line | Meaning |
|---|---|
| `BLOCK <id> (<layer>, <level>)` | which block ran, from which layer, at which level |
| `SUMMARY` | the one line to report to the Regent |
| `WRITE <path> <detail>` | one file written, or to be written |
| `RESULT <json>` | the block's result |
| `PLAN` / `DONE` | nothing written (`--plan`) / what was written |
| `TOKEN` · `ASK` · `ON-APPLY` · `WAIT` | the regent level's plan: its hash, the pop-up, the exact apply call, the wait |
| `REFUSED <why>` | an input, a card or a token refused |
| `NONE` | `find` matched no block |

Exit 0 done · 1 refused · 2 waiting for the Regent's yes.

## 8. Rungs refused (conventions §15.2)

- **The elicitation engine** (`scripts/elicit.py`) already confirms through pop-ups, but with schemas, slots and a
  store; one yes on one plan needs none of them, so the runner hashes the plan instead.
- **The registry and the headless routes** (`library/registry.json`, `library/headless.json`) route commands and
  scripts, not the small operations inside a task; `find` covers what they leave out.
- **A hook that refuses ad-hoc code** where a block exists would be the elaborate machine that enforces minimalism;
  it earns its place the day a measurement shows blocks being bypassed.
