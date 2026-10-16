---
name: engine
description: "Regency inference engines. Run one of five rigorous protocols on a claim, plan, decision, system or repository: critical (audit the truth and validity of a claim, argument or design goal), causal (turn goals, resources and constraints into a causal, testable architecture and the smallest sufficient roadmap), decision (structure a choice under uncertainty, ending in a recommendation, a deferral or a frontier), control (analyse or design a system that must regulate itself: feedback, delay, stability), clean (inspect, plan and, only with approval, clean a repository or context). Use for /regency:engine[:critical|causal|decision|control|clean], 'run the inference engine', 'audit this idea', 'design the roadmap', 'help me decide', 'is this stable', 'clean this repo'."
argument-hint: "<critical|causal|decision|control|clean> <material>"
---

# engine — five protocols, one entry

> **Root.** This file is `skills/engine/SKILL.md`; the regency root is two directories above it.
> Paths like `library/…` are relative to that root. Read `library/conventions.md` once per session.

The engines are not independent skills: they are specifications in `library/engines/`, loaded on
demand through this entry. Keep them out of context until one is chosen.

## 1. Choose

If the first argument names an engine, use it. Otherwise choose by the operation required — never
run all five, and never run one "to sound rigorous":

| The material is… | Engine | Protocol file | Not for |
|---|---|---|---|
| a claim, argument, hypothesis or design goal whose **truth/validity** is in question | `critical` | `library/engines/critical.md` | designing something; ordinary Q&A; requests for validation |
| goals + resources + constraints that need a **dependency-ordered, testable architecture** and the smallest sufficient roadmap | `causal` | `library/engines/causal.md` | brainstorming; motivation; systems with intrinsic feedback forced into a straight line |
| a **choice between actions** under uncertainty, competing objectives, unclear reversibility | `decision` | `library/engines/decision.md` | low-stakes choices with no real alternatives; truth questions |
| a system with **state, feedback, delay, disturbance** that must hold a target over time | `control` | `library/engines/control.md` | static one-time decisions; metaphorical "feedback" |
| a **repository, workspace, prompt set or agent context** whose hygiene (structure, duplication, stale objects, naming) is the problem | `clean` | `library/engines/clean.md` | ordinary local refactoring of source code with no broader hygiene goal |

Unclear which? Ask one closed question (a pop-up) with the two or three candidates and a one-line
reason for each. Do not guess.

## 2. Run

1. Read the chosen **protocol file** completely. It is the operating specification: follow its
   passes, its separation of fact / assumption / inference, and its output contract.
2. `control`, `decision` and `clean` also have an exhaustive reference, `library/engines/<id>.full.md`.
   Open it only when the protocol file points to a section you need, or when the Regent asks for the
   full treatment.
3. Apply it to the material given in the arguments. If the material is missing or is only a topic, ask
   for the material; do not invent it.
4. Honour the engine's own boundaries (for `clean`: **inspect, diagnose and plan freely; execute only
   after explicit approval**, per its authority model).
5. Keep reasoning and result apart: give the result in the engine's output shape, then at most five
   lines on what it does not establish.

## 3. Chaining

Engines may follow one another when a result changes the object: a contradiction found by `critical`
sends a plan back to `causal`; a decision that changes the architecture reopens `causal`; a hidden
feedback dependency invokes `control`. Chain only when a new dependency, contradiction or uncertainty
appears — never to add complexity. The **Scribe** (`/regency:scribe`) is the orchestrator for
sequences of engines; call it for anything longer than two.

## 4. Sub-commands

`/regency:engine:critical`, `:causal`, `:decision`, `:control`, `:clean` are the same skill with the
engine fixed as the first argument.
