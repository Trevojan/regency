# Orders — the four standard templates

An **Order** is a contract that dispatches work. It is not a plan (a plan schedules) and not a
decision (a decision authorises): it says what is to be done, under which constraints, and which
deliverables come back. This folder holds the four standard Order *templates*, compiled from Glyph
(engine 3.4.7.05) to XML. They are templates: slots to fill, never finished orders.

| File | Kind | Purpose | Emits |
|---|---|---|---|
| `germinate.xml` | `/regency:order:germinate` | Grow the path to a goal as a tree: roots (the problem), trunk (the ordered effort), branches (resources leant on), limits (out of reach), locks (what no step may bend), fruit (the observable end state). Closes on one assumption that can be knocked down in a line. | the tree, in chat; saved only on request |
| `handoff.xml` | `/regency:order:handoff` | Close a stretch of work and hand it over. Read by the next session as *opening context, never as an order*. Sections: state, root-cause, closed, measured, open, next, method. | an update to the project's state file and shortcuts index |
| `dispatch.xml` | `/regency:order:dispatch` | Hear an order over the D3/D2/D1 hierarchy, classify it, and emit the dispatch manifest for the team. Never re-fragments what an earlier command already fragmented. | the dispatch manifest (YAML) |
| `resume.xml` | `/regency:order:resume` | Reopen a project left mid-work: read the shortcuts index (the one file read whole), the previous/current/next step only, never the repository from the top. | the four state lines and the next step |

## Numbering and life cycle in a project

- Filled Orders live in the project at `…/.orders/ORD-####/ORD-####.xml`. The number is the largest
  existing plus one. Never reuse a cancelled number.
- **One Order open at a time.** Two concurrent Orders are forbidden.
- **An open Order is immutable except by version.** Material that arrives while one is open is
  *intake* (`INTAKE-*.md`), never an amendment.
- A closed Order stays: it is the contract of what was delivered.
- Opening an Order is the Regent's act. An agent may fill and propose; it does not open one by itself.

## Reading the XML

Each file is `<glyph-package>` → nested `<block binds="…">` / `<section binds="…">`. Read it as a
structured instruction set:

| Element | Meaning |
|---|---|
| `<context>` | when this Order applies (`<user-input>` lines are literal text) |
| `<skill imperative="true" binds="call-team">` | the executor of the Order. `call-team` is now **`/regency:team`**; a tree template without a binding is executed by the model directly |
| `<section binds="x">` | a named part of the output; `<user-input>x</user-input>` is its title |
| `<needs slot="n">text</needs>`, `<user-input slot="n">text</user-input>` | a **slot**: a fact to fill. `text` says what it must contain |
| `<note>` | guidance for the filler, not output. `<human/>` inside it means *a human must answer* |
| `<define-symbol>` | a term and its meaning (D3 = feature, D2 = concept, D1 = task) |
| `<reference>`, `<where>`, `<get>` | where to look or what to read; read it, never re-derive it |
| `<do-not>`, `<limitation>`, `<restriction>`, `<constraint>` | boundaries |
| `<never force="editorial">` | an editorial prohibition on how the result may be written |
| `<target>`, `<ready>`, `<finally>` | the end state, stated as an observable condition |
| `<assumption>`, `<question>` | what is taken as given and unverified / what to ask; `<human/>` forces a pop-up |
| `<validate>` | the check the finished result must pass |
| `<condition>`, `<ask>`, `<only-if>`, `<go>` | conditional steps (for example: missing paths → ask, then create exactly those) |
| `<invoke reads="[…]">` | Glyph shorthand for an operation. These glosses are the definition used here; nothing outside this folder is needed to read or fill an Order: `[ERROR[CTX]]` treat the context as the problem; `[ADD[CORE]],[NEV[VRFY]]` take as given, never verified; `[CTX[GET[CORE],[WHR[LOGIC-NONE]]],[ASK]]` ask for what the core lacks; `[GEN[RMBR]],[ADD[CORE]]` state a lesson that outlives the stretch; `[CMP-CTX[CNST]]…` compare the result with the constraint |

## Filling slots

1. A slot answerable from **facts in the project documents** is filled from them, and cites the source.
2. A slot that needs a **decision, a preference or a number only the Regent has** is asked, in one
   pop-up for all open slots, blockers first. Never invent a slot value.
3. A slot you cannot fill and the Regent does not know stays `⟨unresolved⟩` and goes to the
   open-questions queue. A template with holes is honest; an invented slot lies.
