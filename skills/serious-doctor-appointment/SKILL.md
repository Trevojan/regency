---
name: serious-doctor-appointment
description: "Regency's appointment: propose which health checks each guidelines part needs and which input-process-output can be watched, written on the Regent's yes and run once ratified. Called by /regency:health:doctor."
argument-hint: "[guidelines root]"
---

# serious-doctor-appointment — what this project needs checked

> **Root.** This file is `skills/serious-doctor-appointment/SKILL.md`; the regency root is two
> directories above it. The doctrine is `library/health.md` §5; the engine `scripts/health.py appointment`.

An appointment listens before it prescribes. It reads the project, proposes topics, and writes nothing
until the Regent says yes. **An agent never ratifies a check set it wrote** (T5).

## Steps

1. **Gate.** `python <root>/scripts/migrate.py gate` (conventions §10). Exit 1 or 2: stop as it says.
2. **Inventory.** `python <root>/scripts/health.py appointment plan --out <scratchpad>/health-plan.json`.
   It lists the parts the guidelines hold, the check sets that already exist, and default topics.
3. **Listen to each part.** Read each part's README and the entry index. For every part, ask what can
   go wrong there that a script can see, and add a topic for it. Prefer the checks that exist
   (`library/health.md` §2) and a `command` topic for the project's own gate or tests:
   `{"id": "tests", "check": "command", "args": {"run": ["dotnet", "test"], "exit": 0}, "why": "every commit builds"}`.
4. **The pipeline.** Ask the Regent, in one pop-up with two candidates and a free answer, which
   input → process → output can be watched: an entry point, a CLI, an export, a service call. Draft the
   cases (`library/health.md` §4) under the plan's `pipeline_cases` key, never into the project yet.
5. **Underuse.** When a part is underused or a file sits loose, the topic says so; the remedy (rework
   it, move it, or cut it) is the Regent's, asked as one closed question.
6. **Propose.** Show the plan as a short table: part · topic · why. One pop-up: *write it as proposed* /
   *change it*. On yes: `health.py appointment write --yes <plan file>`; it writes `pipeline.json` beside
   the check sets only when the plan carries accepted cases. Every topic lands with `ratified: null`.
7. **Ratify.** A second pop-up: *ratify all* / *ratify part by part* / *not now*. On the answer:
   `health.py appointment ratify --yes all` or `--yes <part>`.
8. **Report** what was written, what was ratified, and the next step: `/regency:health:project`.

## Rules

- Writes only into `<guidelines>/.shortcuts/.health/` (R11.6), and only after a yes.
- An existing check set edited by the project is never overwritten: the new one goes beside it as `.template`.
- New material goes to the specific part it belongs to, never a common-sense folder (conventions §7).
- Engines: a project that declares its own engines does so in `.sources/ENGINES.md`; the appointment
  proposes an `engines` topic for it and leaves the choice of layer to the Regent (R11.16).
