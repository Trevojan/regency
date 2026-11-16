---
name: locate-with-fts5
description: "Regency locate-with-fts5. Before a broad Grep, ask where a word, identifier or phrase lives: a contentless SQLite FTS5 index over the project's structural nodes returns locations - path, line of the first hit, node range, section chain - never text, re-indexing only files whose size or mtime moved. Falls back to the rg line it prints when FTS5 or the project's store is missing. Use for /regency:locate-with-fts5, 'where is X handled', 'which file defines Y', before exploratory searches in a regency project."
argument-hint: "<terms> [--path PREFIX] [--any]"
---

# locate-with-fts5 — know where to look before searching

> **Root.** This file is `skills/locate-with-fts5/SKILL.md`; the regency root is two directories above it.
> Paths like `scripts/…` are relative to that root. The store is described in `library/shortcuts.md` §7.

Mostly called by the harness itself: one query replaces the grep-refine-grep loop when the location is unknown,
and returns locations to read instead of matching lines to interpret.

## Use

```bash
python scripts/locate.py query <terms> [--path <folder>] [--limit 20] [--any] [--raw]
```

| Flag | Means |
|---|---|
| (none) | every term must appear in the same node; each term is quoted, so no input breaks the query |
| `word*` | a prefix |
| `--any` | any of the terms |
| `--path` | only under that folder |
| `--raw` | the terms are FTS5 syntax as written (`NEAR`, `OR`, column filters) |

The first line is the header (`files`, `refreshed`, `hits`); each next line is one hit: `path`, `line`, `lines`
(the node's range), `node`, `chain`. Read the hit with the Read tool at that line; the node's range bounds what
to read.

## When it does not answer

| Output | Do |
|---|---|
| exit 3, `"index": "none"` | run the `fallback` line it gives (or the Grep tool): FTS5 or `.shortcuts/.virtual` is missing here |
| `hits: 0` | the words are not in the indexed files: try `--any` or a prefix, then Grep for a regular expression |
| a pattern, a multiline match, an exact error string | Grep is the right tool: the index is lexical, not a regex engine |

The first query in a project builds the index (`python scripts/locate.py index` does it ahead);
`--guidelines-only` on `index` limits it to the guidelines root. The index is a cache in the one store, rebuilt
from the files at any time.
