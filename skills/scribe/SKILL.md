---
name: scribe
description: "Regency Scribe. Call suba-scribe to write a text for the Regent or for the role that asks - a document, spec, essay, chapter or post - chaining the inference engines only where the material needs them and growing a long text in increments the caller reviews. Direct mode: the same subagent DV wears for development artefacts, here with none of DV's authority. Use for /regency:scribe, 'write this up', 'draft the chapter', 'turn these notes into a document'."
argument-hint: "<what to write, and the material>"
---

# scribe — call suba-scribe to write a text

> **Root.** This file is `skills/scribe/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` once per session.

This command is a door, not a second Scribe. The Scribe lives in `library/subagents/suba-scribe/`;
DV wears it for development artefacts inside a pass. Here it is called **directly**, for a text, so
it is not locked to DV's use — and it carries none of DV's authority.

1. Read `library/subagents/suba-scribe/SKILL.md`: the two-modes table, then **Direct mode** and
   **Return to the caller**. Its doctrine, `library/subagents/suba-scribe/references/doctrine.md`,
   is read on demand, one section at a time.
2. Work in direct mode: write for the caller; decide nothing the caller could not decide; a text that
   would set a rule is a draft for the Regent to ratify.
3. Hand over one increment at a time, each checked first with
   `python scripts/returns.py check --suba suba-scribe --direct -`.

When the material is a development problem inside a pass, DV wears the Scribe instead
(`/regency:team`, `/regency:role:dv`). This command never acts with DV's authority.
