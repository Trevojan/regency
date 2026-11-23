---
name: blocks
description: "Regency blocks. Before writing a script, a python -c or a multi-step shell for a routine operation, ask which tested block already does it: blocks.py find names the block and its exact call; run checks the arguments against the block's card, writes atomically and applies its confirmation (read runs, agent writes and reports, regent waits for the Regent's yes in one pop-up). Use for /regency:blocks, 'is there a block for', 'bump the version', 'next id', before any ad-hoc code."
argument-hint: "<intent> | run <id> key=value ... | list | test [id]"
---

# blocks — call the tested block, never write it again

> **Root.** This file is `skills/blocks/SKILL.md`; the regency root is two directories above it. Paths like
> `scripts/…` are relative to that root. The model is `library/blocks.md`.

Rule zero (`library/conventions.md` §0): code that exists is called, not generated again from the Regent's words.
The Regent never opens a block. What the Regent sees is one SUMMARY line and, at the regent level, one pop-up; the
trust rests on each block's selftest, which `scripts/doctor.py` runs, not on reading code.

## The flow, every time

1. **Find.** `python scripts/blocks.py find <intent words> --repo <project>`: up to three blocks, best first, each
   with its `CALL` line. Exit 1 means no block: go to step 5.
2. **Show**, only when an argument is unclear: `python scripts/blocks.py show <id>`.
3. **Run** the `CALL` line with the values filled: `python scripts/blocks.py run <id> key=value ... --repo <project>`.
   Quote a value that holds spaces. `--plan` prints the writes and writes nothing.
4. **Confirm by the level the first line names**, `BLOCK <id> (<layer>, <level>)`:

   | Level | The runner | You |
   |---|---|---|
   | `read` | runs, writes nothing | use `RESULT` |
   | `agent` | writes at once, one `WRITE` line per file | report the `SUMMARY` line |
   | `regent` | prints the plan, `TOKEN`, `ASK`, `ON-APPLY`; exit 2; writes nothing | pass the `ASK` JSON to the pop-up as one question, as given; on **Apply** run `ON-APPLY` exactly as printed; on anything else, write nothing and report "not applied" |

   `REFUSED token … does not match` means the arguments or the files moved after the Regent saw the plan: plan
   again, ask again. Never type a token yourself, never pass `--yes` without the Regent's Apply in this pass.
5. **No block.** Write the code inline, as before. When the same intent comes back (a second time in the session,
   or in a second session), propose it as a block: `python scripts/blocks.py run block-new id=<id> intent="<one line>"`
   (regent level). Then write its `run()` and `selftest()` until `python scripts/blocks.py test <id>` prints `OK`.
   A block ships tested or not at all.

## Reporting

- To the Regent: the `SUMMARY` line, or "not applied". No code and no `WRITE` list unless asked.
- Exit 0 done · 1 refused: the `REFUSED` line says why; change the input, never repeat the same call · 2 waiting for
  the Regent's yes.
- `python scripts/blocks.py list` is the catalogue; `test` runs every selftest.

Not a block: what one line does (`library/conventions.md` §15.1, rung 6), a git or cloud act (the hooks judge
those), a judgement. `library/blocks.md` §6.
