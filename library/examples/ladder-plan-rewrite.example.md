# Plan — rewrite `Docs/.guidelines/PLAN/` as an execution ladder

> A worked example from a client project, kept as the client wrote its artefacts: file names, code
> identifiers and commit messages in backticks are that project's own, quoted as they were.

## Context

The client asked for a development plan **from the minimum to the maximum**, organised as a checklist
from the simplest thing up to the deliverable system, with a literal hierarchy:

```
rung = module → phases → to-dos → files → code → norm → test → mission accomplished
```

Each step is a commit; the effort lives in the ladder, not in GRAND or in MINIMUM. The first attempt at
the plans (written before this explanation) was too light on execution, and the gate sheet failed the
opening. On top of that, the root `PLAN.md` — the real backlog, with 141 items and their dependencies
declared — sat outside the folder and had not been brought in.

**The blueprint before the walls.** All **seven** rungs are written now, with the same rigour and the same
detail: phases, to-dos, files, functions, norm and test for each one. What waits for the right moment is
the **content** — the code. This does not conflict with rule 3 of `PLANOS.md` ("a `LADDER` is never
overwritten"), because a rung only **freezes** when its gate is signed `SOLUTION: sim`; before that it is
a blueprint, and a blueprint is corrected by what reality answers on the earlier rungs.

**Expected result:** `PLAN/` with an executable plan of 7 rungs and about 129 to-dos named one by one, two
milestones (MVP-0 at 22 commits, MVP-1 at 78), item-by-item tracing against the backlog, and a checklist
that can be ticked.

**Decisions the client had already taken:** amend the gate formula into a sum; rename the backlog to
`BACKLOG.md`; name two MVPs; **not** run the reconciliation POC with real cards now.

---

## 1. Moving files

| Action | From | To |
|---|---|---|
| `git mv` | `PLAN.md` (root) | `Docs/.guidelines/PLAN/BACKLOG.md` |
| Rewrite | `PLAN/GRAND_PLAN.md` | the same — trimmed, capped at 120 lines |
| Rewrite | `PLAN/MINIMUM_PLAN.md` | the same — capped at 90 lines, gains §MVP reach and §Core POC |
| Rewrite | `PLAN/LADDER_PLAN_PART_1.md` | the complete Registration module, in detail |
| Create | — | `PLAN/LADDER_PLAN_PART_2.md` … `PART_7.md` — **the same detail as PART_1** |
| Create | — | `PLAN/CHECKLIST.md`, `PLAN/TRACE.md`, `PLAN/README.md` |
| Delete | `PLAN/GATE_2026-08-14_PARTE_1.md` | replaced by `GATE_PARTE_1_<date>.md` |
| Amend | `PLAN/PLANOS.md` | a dated `## Amendments` block at the end — **without touching the client's text** |

`git mv`, not a copy: it keeps the history of the backlog's 880 lines.

---

## 2. The hierarchy, with an operational definition

**The 7 phases are fixed on every rung** — dictated by `DECISIONS/ARCHITECTURE.md`, so that two people
decompose the same way. An empty phase is declared empty, not left out.

| Phase | Name | Where it works | Contract it publishes |
|---|---|---|---|
| F0 | Norm | `DECISIONS/`, `SOURCES/` | the citable rule the next phases obey |
| F1 | Contract | `Models/`, `Services/I*.cs`, `Data/Migrations/` | types, signatures, schema |
| F2 | Rule | `Services/*.cs` + `REMUNERACAO_PROBE` | proven behaviour |
| F3 | Exposure | `API_PANEL/Controllers/`, `Auth/Perfis.cs` | HTTP route + authorisation |
| F4 | Consumption | `UPLINK_DRIVE/` | typed client |
| F5 | Screen | `VIEW_CORE/` + `Telas.Prontas` + `VIEW_PROBE` | a navigable screen, marked ready |
| F6 | Closing | `CHANGELOG.md`, `API_ENDPOINTS.md`, `BACKLOG.md`, gate | the next rung opens |

**A to-do is one commit.** Closed criterion: builds with no new warnings; both `*_PROBE` suites green, run
project by project; fits in one imperative sentence without "and"; and can be reverted on its own.
Calibration: a to-do is always difficulty 1 on the backlog's scale.

**A phase is a dependency boundary; a to-do is a reversibility boundary.** Swapping two phases breaks the
system (F3 before F2 puts a rule in the Controller, which `ARCHITECTURE.md` forbids with `[MAND]`);
swapping two to-dos of the same phase breaks nothing.

**Norm** = the citable rule that code obeys: a `[MAND]` of `ARCHITECTURE.md`, a line of
`BUSINESS_RULES.md`, or an ADR. Every to-do cites its own — a to-do with no norm is code with no
acceptance criterion.

---

## 3. The ladder — 7 rungs, about 129 to-dos

| # | Rung | Module | Commits | Total | Milestone |
|---|---|---|---:|---:|---|
| 1 | Registration and administration | 8th module (DHO) | 22 | 22 | **MVP-0 — Registration pilot** |
| 2 | Approval & invoice | 3 | 22 | 44 | — |
| 3 | Monthly reconciliation | 4 | 19 | 63 | — |
| 4 | Individual statement (read) | 6a | 15 | 78 | **MVP-1 — One month closed** |
| 5 | Payroll | 5 | 19 | 97 | — |
| 6 | Closing & sending | 6b | 18 | 115 | — |
| 7 | Management P&L | 7 | 14 | 129 | **Top-of-the-line deliverable** |

**Ordered by real dependency, not by preference:** rung 1 is the only one with no incoming dependency; it
fills `gestor_id`/`centro_receita_id`, which Module 3 needs to route the approval, and creates the manager
and finance accounts without which Module 3 **cannot be signed off** — a hand-off between three roles is
not accepted with a single account. From rung 2 on, the backlog's order holds: with no card in `Recebido`
there is no reconciliation, with no calculation there is no statement, with no closed month there is no
P&L.

**A non-functional requirement does not become a rung.** It anchors in F0 or F5 of the first rung that
would suffer without it; if none would, it stays `[late]` in the backlog and never enters the ladder.

---

## 4. What each file holds

### `GRAND_PLAN.md` — capped at 120 lines
The template's sections plus **`## Definition of the top-of-the-line deliverable`**: the 7 modules plus the
non-functional conventions that speed up the core (the engine as the single source, the visibility
restriction in the Service, shielding by build configuration, proof by `*_PROBE`). It is what gives the
last rung its criterion.
**Does not go in:** file names, signatures, estimates, backlog ids.

### `MINIMUM_PLAN.md` — capped at 90 lines
The factor table **shrinks to 4 columns** (`# | Factor | Depends on | Target rung`) — the attestation
columns leave, because attestation belongs to the ladder. It gains:
- **`## MVP reach`** — declares `N_mvp = 4`, which the amended gate formula consumes.
- **`## Core POC`** — the e-mail provider, with five fields: the unproven risk, the closed question, how
  it gets answered, the discard criterion, what changes if the answer is no. It runs in parallel with
  rung 1 because it is not code work, and three things depend on it (password recovery in ADR-012, rung
  1's initial credential, rung 6's statement sending).
- **`## Amendments`** — an append-only block, empty at the opening.
- **`## Risks accepted without proof`** — records that the engine has never met a real card and that the
  reconciliation against the office's spreadsheet was put off to rung 4, by the PO's decision on that
  date.

### `LADDER_PLAN_PART_1.md` … `PART_7.md` — where the effort lives
**All seven have the same structure, the same rigour and the same level of detail.** The sections of
`PLANOS.md` (why this rung now, affected functions, scope, attestations, POC needed, completion
criterion) plus the central section `## Phases and to-dos`, with one table per phase:

| To-do | Covers | Files | Function / signature | Norm | Test | Commit |
|---|---|---|---|---|---|---|
| `P1.F2.A03` | `B-CAD-01` | `REMUNERACAO_CORE/Services/CadastroService.cs` | `Task<PessoaViewModel> CriarPessoaAsync(PessoaRequest, EscopoUsuario)` | ADR-005 · BR §Validations | `CadastroServiceTests.CriarPessoaAsync_NascePendenteDeTroca` | `feat(CADASTRO): criar pessoa com senha provisória gerada` |

What **is** written now, for all seven: the path of each file, the name and signature of each function,
the norm that governs it, the name of the test that proves it and the commit message. What is **not**
written: the bodies of the functions. Blueprint, not wall.

**Where the blueprint is necessarily less firm, it says so** instead of faking precision — for example,
downloading the `.xlsx` in a Photino window (rung 7, F5) is a real unknown: a native window has no browser
downloads folder. It is recorded as that rung's `POC needed`, with the question it answers.

### `CHECKLIST.md` — the ramp that was asked for
A file of its own, single, global, **derived** from the ladder (a line with no originating to-do is a
process bug). Tickable with `- [ ]`. A declared, reproducible order: topological first, increasing
difficulty within what is free, `[late]` only when nothing else is free. Milestone markers for MVP-0,
MVP-1 and the top of the line. It stays outside the `LADDER` files because ticking a box is writing to
the file, and rule 3 says a `LADDER` is not overwritten: **the LADDER is what was decided, the CHECKLIST
is what was done.**

### `TRACE.md` — nothing is lost, nothing comes from nowhere
One line per backlog item, a stable id `B-<AREA>-<nn>` and **exactly four states**: covered (with the
to-do), deferred (with the target rung), off the ladder (with the reason), discarded (with the reason). No
empty cell.
- **Direction 1:** the number of TRACE lines == the number of items in Part II of the BACKLOG.
- **Direction 2:** every to-do cites a `B-id`, or `origin: GRAND`, or `origin: norm`.

Direction 2 already catches two real holes: `Shell.razor` §routing and §exit guard, and the ADR on the
residue policy — work promised in Part III with no card in Part II.

### `BACKLOG.md` (the old `PLAN.md`)
Structure kept. Four changes: a `B-<AREA>-<nn>` id on every line of Parts I and II; correct "18
categories" to 19; the "Functions to implement" block of Part III becomes raw material with a pointer
`→ LADDER_PART_X §Phase N`; and the precedence note rewritten:

> **The BACKLOG rules on fact** (what exists, what is missing, what it costs).
> **GRAND/MINIMUM/LADDER rule on decision** (what is done, in what order, under which criterion).
> **A business rule lives in neither** — it lives in `DECISIONS/BUSINESS_RULES.md`.

### The folder's `README.md`
A table of file → the question it answers → owner → when it changes; the reading order; a dated index of
the gates issued.

---

## 5. Amendments to `PLANOS.md` (a dated block, the client's text intact)

**5. The effort lives in the ladder** — GRAND ≤ 120 lines, MINIMUM ≤ 90. The excess moves.

**6. The gate formula** *(authorised by the client)*:
```
((MINIMUM < GRAND) & (MINIMUM <= (Σ LADDER_PART_1..N_mvp + POC))) = SOLUTION
```
with `N_mvp` declared in `MINIMUM_PLAN §MVP reach`. It does not loosen anything: it still demands full
coverage by written rungs plus a bounded POC. Replicate it in `TEAM/TEAM.md §4` and `TEAM/PO.md §8`, or the
roles contradict the law.

**7. The whole blueprint is written before the first wall.** All seven `LADDER` files exist, with the
same detail, before execution opens. What the client's rule 4 governs is the **opening** of a rung, not
the existence of its blueprint.

**8. A `LADDER` only freezes when its gate is signed `SOLUTION: sim`.** Before that it is a blueprint and
may be corrected by what the earlier rungs teach — which is what allows the first attempt to be thrown
away without breaking rule 3.

**9. Two kinds of gate sheet** — `tipo: triangulacao` (once, at the opening of P1) and `tipo: degrau` (on
the following ones: the previous part's criterion + QA's verdict + no TRACE item regressed).

**10. Two kinds of POC** — *core* (in MINIMUM, on the MVP's viability) and *rung* (in the LADDER, on that
rung's viability). A POC lives on a branch that never reaches `main`; the only artefact that survives is a
document.

**11. The rung-closing cycle** (all in the same commit): check the criterion → mark the rung done in the
CHECKLIST → move the covered items from Part II to Part I of the BACKLOG, keeping the `B-id` → update
TRACE → issue the next part's gate → revise the next rung's blueprint with what was learnt → freeze the
rung that closed.

**12. A rung in execution does not change scope** — a new request goes to the BACKLOG.

---

## 6. References to fix in the same commit as the move

- `SOURCES/AGENTS.md` — the `PLAN/` table cites the root `PLAN.md`; it now cites `PLAN/BACKLOG.md`. Also
  correct "18 areas" → 19.
- `SOURCES/README.md` — describes `PLAN/` only as "templates".
- `SOURCES/GLYPH_LEGEND.md` — lists the root `PLAN.md` among the non-Glyph files; the path changes.
- `TEAM/TEAM.md` and `TEAM/PO.md` — the gate formula, in three places.

---

## 7. Verification

There is no code in this delivery; the verification is of coherence and of counts.

1. **Tracing closes both ways:** `the number of lines in TRACE.md == the number of items in Part II of
   BACKLOG.md`, zero lines with no state, and zero to-dos with no declared origin.
2. **Equal detail:** the seven `LADDER` files have the same sections and every to-do has all seven columns
   filled — no "to be defined" cell outside `POC needed`.
3. **Commit sum:** the count per rung in `CHECKLIST.md` matches the sum of each `LADDER_PART_X`'s tables,
   and the total closes at 129.
4. **Caps:** `wc -l GRAND_PLAN.md` ≤ 120 and `MINIMUM_PLAN.md` ≤ 90.
5. **Gate:** the new sheet closes `SOLUTION: sim` with the amended formula and `N_mvp = 4`.
6. **No broken reference:** `grep -rn "PLAN.md" --include=*.md .` does not point at the root.
7. **Git:** `git log --follow Docs/.guidelines/PLAN/BACKLOG.md` shows the file's earlier history — proof
   that `git mv` kept the timeline.

## Out of scope for this delivery

No production code. Rung 1 opens only after the gate is approved, and its first to-do (`P1.F0.A01`) is to
write the registration ADR.