---
paths:
  - "**/*.razor"
  - "**/*.cshtml"
  - "**/*.html"
  - "**/*.jsx"
  - "**/*.tsx"
  - "**/*.vue"
  - "**/*.svelte"
---

# End-user text in the UI

Source: regency `library/conventions.md` §2 and §7. The project glossary wins on any term.

- Text the end user can see is terse and objective: what happened, then what to do, in as few words as the message allows.
  Example of the register: "A API demorou demais para responder. Tente de novo em instantes."
- Nothing meant for developers reaches the screen: no notes, annotations, rationale, decision or task ids,
  TODOs or explanations in visible markup. They belong in comments or in the guidelines.
- Use the project glossary's words for every term and never a word it bans. In Brazilian Portuguese write
  "sua/seu", never "tua/teu".
- Visual defects (borders, misplaced or misaligned elements) are what a client notices first: fix them
  before anything cosmetic or optional.
