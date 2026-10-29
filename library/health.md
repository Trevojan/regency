# Health — what the harness checks, and why

`/regency:health` is the Regent's checkup: one line per finding, every figure with its method, read-only
unless the Regent answers yes. `scripts/health.py` is the engine; `skills/health/SKILL.md` the procedure;
`skills/serious-doctor-appointment/SKILL.md` assembles what a project needs checked. Decided with the
Regent on 2026-10-28 (R11).

## 1. Three layers

| Layer | Command | Checks | Who decides what is checked |
|---|---|---|---|
| the harness | `/regency:health:harness` (also `/regency doctor`) | regency itself: `scripts/doctor.py` | regency |
| the project | `/regency:health:project` | the project's ratified check set | the Regent, from the appointment's proposal |
| the surfaces | inside `project`, and the single checks below | what each surface the Regent works from can reach | regency, per surface |

`/regency:health:doctor` does not check anything: it **assembles the caring topics** of a project — which
checks its parts need — and writes them as a proposal. Nothing runs until the Regent ratifies it.

## 2. The checks

| Check | Finds | Level of a finding |
|---|---|---|
| `names` | one name for two files: each copy gets a suggested name (`Aa1`, `Aa2`) and a candidate keeps the name (the first born; a copy in a specific folder over a loose one); identical copies are called copies | WARN; a name a runtime fixes (`SKILL.md`, `plugin.json`) is INFO, reported once |
| `size` | knowledge weight against a cap: a surface's own figure, or the local upload set | WARN from 80 %, FAIL over the cap |
| `queues` | a dated queue (a markdown section of dated items) older than N days; the ledger's review count over its WIP limit (P-14) | WARN |
| `shortcuts` | virtual paths (`vp.py check`), the entry index and its drift (`shortcuts.py check`, `drift`; `library/shortcuts.md`) and the exact index (`idx.py check`) in one report; it never creates the store | FAIL broken reference, WARN drift or an entry-index problem |
| `version` | the project against the installed regency: the version gate (`library/migrations/README.md` §2), update operations still owed while the stamp agrees, unverified speed-mode drafts (`vp.py drafts`) | FAIL newer than the plugin; WARN behind, unstamped, owed operations, a draft |
| `copies` | split copies of regency (R12): this folder, every installed copy (the CLI's cache, the account's synced copies) and every branch — lines of work no branch holds together, one version naming two contents, a version only an install holds, uncommitted work, a branch ahead of the folder | WARN; INFO for an install that is only behind; UNCHECKED without git |
| `distributable` | a generated file edited by hand (F4); dist/ output or an archive in an uploaded set; a machine path in a release (F5) | FAIL, FAIL, WARN |
| `engines` | every engine copy against regency's base and the Regent's record | AOK, STALE, UNCHECKED |
| `hooks` | a wired hook with no heartbeat on this machine; torn journal lines | WARN |
| `context` | the harness's always-on token cost against a budget | WARN over budget |
| `pipeline` | watched runs of declared cases, and a scan for silent errors | FAIL, WARN |
| `underuse` | a part holding nothing but its README; a loose file at the guidelines root | WARN |

**Levels.** FAIL (exit 1) · WARN · STALE (waits for the Regent) · UNCHECKED (not reachable from this
surface; never read as clean) · AOK (ratified) · OK · INFO.

## 3. Engines: yours, the project's, regency's

- **regency's base** is `library/engines/<id>.md`. A copy with the same text is AOK.
- **your copies** live on your machine (`~/.claude/skills/`) and on your account. A copy that differs
  from the base is **STALE** until you ratify its current state; ratified, it is **AOK**; changed again,
  STALE again. Deny it and regency's base comes back: on the machine the script moves your text aside
  (`SKILL.denied-<date>.md`) first; on the account the playbook says what to put back, since regency
  cannot write there.
- **the ratified record** is `~/.claude/regency/engines.json`, on your machine (R11.15): per copy, the
  fingerprint and date you ratified; per repository, which engines you follow there. A claude.ai session
  reaches it through the device bridge; without the bridge the record and the machine copies read
  UNCHECKED.
- **a project's engines** are declared in `<guidelines>/.sources/ENGINES.md` (orientation files live in
  `.sources/`). In a repository that declares them, you choose — yours or the project's — for that
  repository only (R11.16); the choice is recorded on your machine, so nothing is written into a
  repository you do not own (conventions §6).

A STALE line clears only on the Regent's ratification, never on an agent's (T5).

## 4. The pipeline: input → process → output

A **case** is something that can be watched: a command, its input, what it must answer. Declared in
`<guidelines>/.shortcuts/.health/pipeline.json`:

```json
{"cases": [{"id": "export", "run": ["python", "app.py", "export", "--json"], "stdin": null, "cwd": ".",
            "timeout": 60, "logs": ["logs/app.log"], "ignore": ["\\d{4}-\\d{2}-\\d{2}T[0-9:.]+"],
            "expect": {"exit": 0, "json": true, "stdout": "regex", "stable": true, "reach": ["stdout"]}}]}
```

| Finding | Means |
|---|---|
| silent error | the process failed with no message at all |
| unreachable message | the only readable message went where the Regent does not look (a channel outside `reach`, or a log file) |
| wrong shape | the output is not JSON, or does not match its pattern |
| inconsistent output | the same input gave two outputs; the similarity is the measure. Declare volatile parts in `ignore` |

The **scan** reads the code for silences: an exception swallowed, a process result dropped, an empty
catch. A silence that is meant carries `health: allow-silent <why>` on its line; it is counted, never hidden.

## 5. Check sets

`<guidelines>/.shortcuts/.health/<part>.json`, one file per part (R11.6: in `.shortcuts/`, not a new
folder). Each topic: `id`, `check`, `args`, `why`, `ratified` (a date, or null). The appointment writes
them with `ratified: null`; `health.py appointment ratify --yes` stamps them on the Regent's answer; a
check set edited by hand is never overwritten (the new one goes beside it as `.template`).

## 6. Heartbeats

Every hook leaves one small file per (script, event) under the plugin's state folder, holding the last
time it ran (`hook_wire.heartbeat`). They live on the machine, never in a repository. A hook the surface
never calls leaves none — which is how a hook that fails open on a surface becomes visible.
