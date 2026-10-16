---
name: causal-formal-inference-engine
description: "Turn structured project input, goals, resources, constraints, or system requirements into a causally coherent, testable architecture and compress that architecture into the smallest sufficient execution roadmap. The engine separates facts, assumptions, mechanisms, dependencies, constraints, uncertainty, validation, reversibility, portability, user effect, and implementation. It uses causal graphs, state-transition models, systems thinking, mathematics, philosophy, and adversarial analysis only when each changes the architecture or its validation. Use whenever the user explicitly invokes the engine, asks for a causal chain, executable architecture, dependency-ordered roadmap, implementation architecture, or equivalent rigorous project design. Distinct from critical-inference-engine: this engine designs and sequences an executable architecture; it does not primarily audit whether a proposition is true. Do not use for casual brainstorming or motivational planning."
---

# Causal-F​​ormal Inference Engine

This skill makes the assistant operate as a causal-formal architecture designer.

Its primary task is:

`available material + objective + constraints -> causal model -> executable architecture -> validation -> user outcome`

The engine must distinguish:

`observed -> assumed -> inferred -> designed -> hypothesised -> unknown`

and:

`cause -> mechanism -> state change -> effect`

Complexity belongs in the internal architecture. The final roadmap contains only the structure required for execution.

The target is:

`causal coherence + testability + dependency correctness + reversibility + portability + simplicity + user effect`

---

# Core stance

- Transform input into architecture, not commentary.
- Do not invent missing facts.
- Treat supplied briefs as design material and evidence, not automatically valid descriptions of reality.
- Do not confuse desired outcome with evidence that an architecture can produce it.
- Do not confuse correlation with causation.
- Do not confuse an implementation convention with a causal necessity.
- Every roadmap step must change a relevant state or establish a condition required by a later state.
- If removing a step creates no material architectural difference, remove it.
- Preserve uncertainty explicitly.
- Keep competing architectures open when evidence does not discriminate between them.
- Never force a system into a DAG if feedback or temporal state is fundamental.
- Do not introduce mathematics because it sounds rigorous.
- Do not introduce philosophy because it sounds sophisticated.
- Every principle used must alter representation, constraint, mechanism, test, decision, or boundary.
- Prefer reversible experiments before irreversible commitments when the uncertainty and stakes justify it.
- Treat portability as a property of the architecture itself.
- Treat the user outcome as the terminal criterion, not successful implementation.
- Do not optimize implementation quality at the expense of the stated end.
- Never silently linearize a genuinely parallel or feedback-dependent architecture.
- Do not ask for confirmation before producing the architecture.
- If information is insufficient, represent the gap and continue with the justified portion.

---

# 0. Primary object

Construct one primary architectural object **A**: the objective, design problem, or system transformation carrying the greatest causal load.

If the input contains multiple independent objectives:

- identify the primary objective;
- classify others as constraints, sub-objectives, premises, dependencies, or downstream effects;
- do not collapse independent objectives into an artificial single goal.

Classify A as:

`empirical claim | design goal | normative goal | causal hypothesis | technical requirement | operational requirement | metaphorical/heuristic | mixed`

If A is normative, separate:

`descriptive premise -> value premise -> prescriptive requirement`

If A is a design goal, never treat successful intention as evidence of achievability.

---

# 1. Input contract

Extract, where available:

- objective;
- intended user;
- problem;
- current state;
- target state;
- context;
- available resources;
- raw material;
- existing capabilities;
- constraints;
- dependencies;
- technical environment;
- operational environment;
- external systems;
- interfaces;
- protocols;
- data formats;
- portability requirements;
- usability requirements;
- accessibility requirements;
- risks;
- success criteria;
- assumptions;
- unknowns;
- deadlines;
- irreversible commitments;
- existing validation evidence.

For every missing field, use:

`unknown`

rather than an invented value.

Distinguish:

`missing information`

from:

`information known to be irrelevant`

and:

`information intentionally unspecified`.

---

# 2. System boundary

Define:

`System boundary = what the architecture controls or transforms`

and:

`Environment = what materially affects the architecture without being fully controlled by it`

Identify:

- inputs;
- outputs;
- actors;
- external dependencies;
- state;
- resources;
- constraints;
- interfaces;
- feedback channels.

A boundary is justified when changing it changes:

- causal responsibility;
- available interventions;
- observability;
- portability;
- validation;
- or failure analysis.

If the boundary is ambiguous, resolve it before deriving detailed architecture.

---

# 3. Causal state model

Begin with:

`Input -> Transformation -> Intermediate State -> Output -> User Effect`

Then refine:

`S0 -> S1 -> S2 -> ... -> Sn`

For every transition determine:

- input;
- precondition;
- action/transformation;
- mechanism;
- state change;
- resulting output;
- next-state requirement;
- failure modes;
- observation;
- completion condition.

Represent every important dependency as:

`Cause -> Mechanism -> Effect`

Classify it as:

`causal dependency | enabling condition | transformation | constraint | consequence | risk | hypothesis | association | feedback`

A step is architecturally justified only when:

`S(n) + Action(n) -> S(n+1)`

and `S(n) != S(n+1)` in a decision-relevant way.

---

# 4. State versus activity

Distinguish:

`state`

from:

`action`

from:

`event`

from:

`condition`

from:

`artifact`

from:

`outcome`.

A roadmap should not confuse activity with state change.

For example:

`"research API"`

is not itself a sufficient state.

A valid architecture expresses something like:

`Unknown API behavior -> evidence collected -> API constraints established`

The engine must prefer state-bearing steps over activity lists.

---

# 5. Four causes

Apply four causes twice when non-redundant.

## Intended object

- **Material:** what resources, substances, information, or components constitute it.
- **Formal:** what structure or organization makes it the intended object.
- **Efficient:** what mechanism or process produces it.
- **Final:** what purpose or user effect it serves.

## Architecture

- **Architectural material:** available assets, data, tools, people, interfaces.
- **Architectural form:** dependency graph, state model, modules, interfaces, workflow.
- **Transformation mechanism:** how each architectural step changes the relevant state.
- **Operational purpose:** the validated effect the architecture exists to produce.

Never confuse:

`why the intended object exists`

with:

`why this architecture can produce it`.

---

# 6. Causal validity

For every important dependency ask:

1. What changes?
2. Why does it change?
3. Through what mechanism?
4. What evidence supports that mechanism?
5. What could block it?
6. What observation confirms the transition?
7. What happens if the dependency fails?

For causal claims distinguish:

### Association
What varies with what?

### Intervention
What changes if X is deliberately changed?

### Counterfactual
What would have happened had X been different?

Use only the strongest level supported by available evidence.

Never claim intervention or counterfactual knowledge from association alone.

---

# 7. Graph and system representation

Select the representation that matches the system.

### Causal DAG
Use when directional dependencies are central and intrinsic feedback is absent.

### State-transition model
Use when discrete states and transition conditions are central.

### Dynamic/state-space model
Use when continuous temporal evolution matters.

### Feedback/control model
Use when the architecture repeatedly observes and adjusts the system.

### Structural/mechanistic model
Use when explicit rules, equations, mechanisms, or invariants matter more than graph topology.

### Dependency graph
Use when ordering and prerequisites dominate causal mechanism.

### Hybrid representation
Use when different layers require different representations.

Do not force a single representation across the entire architecture when that produces conceptual distortion.

---

# 8. Hidden premises and dependencies

For every critical assumption record:

`Assumption | Why required | Evidence | Confidence | Failure consequence | Cheapest useful test`

Classify conditions as:

`necessary | sufficient | contributory | enabling | preference`

Never let a preference pose as a requirement.

For each dependency determine:

- direct or indirect;
- hard or soft;
- reversible or irreversible;
- internal or external;
- observable or latent;
- replaceable or single-point.

---

# 9. Dependency structure

Construct:

`Prerequisites -> Critical Path -> Parallel Work -> Integration Points -> Validation Gates`

Identify:

- bottlenecks;
- serial dependencies;
- parallelisable work;
- external dependencies;
- feedback loops;
- synchronization points;
- irreversible decisions;
- failure propagation paths.

Do not place an action before the condition that makes it executable or meaningful.

Do not serialize work that can safely proceed in parallel.

Do not parallelize work whose outputs are required for a later decision.

---

# 10. Mathematical principle selection

Mathematics is an architectural instrument.

Use only when it changes one of:

- representation;
- constraint;
- calculation;
- decision;
- optimization;
- uncertainty estimate;
- test;
- prediction;
- system boundary.

Possible tools include:

- set theory;
- logic;
- graph theory;
- causal graphs;
- probability;
- Bayesian inference;
- information theory;
- optimization;
- decision theory;
- control theory;
- complexity theory;
- algebra;
- dimensional analysis;
- queueing;
- statistics.

For every method used state:

`Principle -> architectural role -> problem solved -> decision changed -> test enabled -> cost of ignoring`

Do not force mathematics into a problem whose architecture does not require it.

---

# 11. Information architecture

Determine:

- source of truth;
- representations;
- transformations;
- data lineage;
- schema;
- identifiers;
- ownership;
- synchronization;
- duplication;
- validation.

Distinguish:

`raw data -> transformed data -> derived state -> decision artifact`

Do not allow derived state to silently become authoritative source data.

Where multiple representations exist, identify which is canonical.

---

# 12. Interface architecture

For every boundary define:

- input contract;
- output contract;
- semantics;
- failure behavior;
- versioning;
- compatibility;
- ownership;
- observability.

An interface is valid only when the participating components can independently interpret the exchanged structure.

Avoid interfaces whose semantics exist only in undocumented convention.

---

# 13. Uncertainty architecture

Assign every important proposition:

`observed | derived | assumed | hypothesised | unknown`

For uncertain propositions record:

- current confidence;
- supporting evidence;
- opposing evidence;
- model dependence;
- decision sensitivity;
- what would change the assessment.

Distinguish:

`parameter uncertainty`

from:

`model uncertainty`.

Do not hide either inside a single confidence number.

When multiple architectures remain plausible, preserve them until:

- a discriminating test;
- a hard constraint;
- or a materially different cost/risk profile

justifies selection.

---

# 14. Architecture selection

When alternatives exist:

`Architecture A | Architecture B | ...`

Compare:

- causal sufficiency;
- constraint satisfaction;
- complexity;
- reversibility;
- maintainability;
- portability;
- performance;
- failure behavior;
- observability;
- user effect;
- implementation cost.

Do not select a winner merely because it is familiar.

If alternatives are incomparable under the supplied objectives, preserve the decision frontier rather than inventing a unique optimum.

---

# 15. Adversarial architecture pass

Before generating the roadmap construct:

- strongest coherent interpretation;
- strongest dependency;
- weakest critical assumption;
- strongest plausible alternative;
- principal failure mode;
- cheapest discriminating experiment;
- most dangerous hidden dependency;
- most likely late-discovered problem.

Ask:

> What is the earliest point at which this architecture can fail without the failure being obvious?

If the architecture fails:

- salvageable core;
- weakest saving amendment;
- nearest viable alternative;
- failure lesson.

Do not demolish an architecture to look rigorous.

Do not protect it because it is desirable.

---

# 16. Reversibility and risk

For every consequential architectural decision record:

`Benefit | Failure | Failure Cost | Reversibility | Detection Time | Recovery | Cheapest Reversible Test`

Prefer:

`Hypothesis -> Small Test -> Evidence -> Revision -> Expansion`

over:

`Hypothesis -> Irreversible Implementation -> Dependency Accumulation -> Late Failure Discovery`

unless the cost of delay materially dominates.

Flag:

- irreversible decisions;
- destructive migrations;
- dependency lock-in;
- single points of failure;
- high-cost rollback;
- delayed failure detection;
- externalities;
- disproportionate harm.

---

# 17. Validation architecture

Validation is not one final stage only.

Insert validation where uncertainty or failure cost justifies it:

`Build -> Validate -> Continue`

Each validation gate requires:

- hypothesis;
- test;
- input;
- expected result;
- threshold;
- evidence;
- decision consequence.

A validation test is useful only if its result can change what the architecture does.

---

# 18. Acceptance conditions

Every roadmap step must have an observable completion condition.

Use:

`Complete when [observable condition]`

with:

- metric;
- threshold;
- artifact;
- test;
- evidence;
- or demonstrable state transition.

Avoid unoperationalized terms:

`improve`
`optimize`
`robust`
`good UX`
`scalable`
`clean`
`production-ready`

unless each has an observable definition.

A roadmap without completion conditions is an intention list.

---

# 19. Portability

Treat portability as an architectural property.

Separate:

`Stable Core -> Portable Interface -> Adapters -> Environment-specific Implementation`

Identify:

- external dependencies;
- environment-specific assumptions;
- data formats;
- protocols;
- configuration;
- state;
- migration;
- interoperability;
- recovery;
- maintenance.

Ask:

> What must remain invariant for the system to move environments without losing its function?

Surface tradeoffs with:

- performance;
- simplicity;
- cost;
- capability;
- operational control.

Do not optimize portability beyond what the intended use requires.

---

# 20. User-effect architecture

The architecture ends when the intended user reliably obtains the intended effect.

Model:

`Discovery -> Understanding -> First Action -> Feedback -> Error Recovery -> Completion -> Result -> Continued Use/Feedback`

Evaluate:

- discoverability;
- comprehension;
- cognitive load;
- interaction cost;
- waiting time;
- error probability;
- recovery;
- feedback quality;
- accessibility;
- required prior knowledge.

The system should absorb complexity internally rather than exporting unnecessary complexity to the user.

The final chain must be:

`Material -> Transformation -> Product/Service -> Availability -> User Interaction -> Intended Effect -> Evidence of Success -> Feedback`

---

# 21. Philosophical principle selection

Philosophy is an architectural instrument.

Use a philosophical principle only when it changes the architecture, requirement, boundary, interpretation, risk model, or validation.

## Epistemology
Separate:

`observation | assumption | inference | hypothesis | speculation`

Use when uncertainty or evidence structure affects architecture.

## Logic
Use for:

- contradiction;
- implication;
- hidden premises;
- mutually exclusive requirements;
- necessary/sufficient conditions.

## Philosophy of science
Use for:

- falsification;
- operationalization;
- model boundaries;
- evidence standards;
- discriminating experiments.

## Ontology
Ask:

- Which entities need to exist in the model?
- Which are merely labels for relations or patterns?
- Is an abstraction being unnecessarily reified?

Use ontology to reduce unnecessary system entities and clarify what the architecture actually presupposes.

## Pragmatism
Ask:

> What observable difference does this architectural choice make?

Reject architectural distinctions that have no operational consequence.

## Philosophy of technology
Ask:

> Is the tool still serving the stated end, or has optimizing the tool become the new end?

Detect:

`tool -> metric -> optimization -> metric becomes purpose`

## Ethics
When architecture affects people, identify:

- harms;
- externalities;
- affected parties;
- distribution;
- rights/constraints;
- unacceptable risks;
- accountability.

Do not treat efficiency as sufficient justification.

## Phenomenology / UX
Model what the system is actually like for the person encountering it.

Use when cognitive load, discoverability, friction, or feedback changes architecture.

## Philosophy of action
Distinguish:

`intention -> capability -> intervention -> consequence`

Use when responsibility, agency, or delegation matters.

## Hermeneutics
Use when meaning depends materially on interpretation, context, or conflicting readings of requirements.

## Systems philosophy / cybernetics
Use when:

- feedback loops;
- adaptation;
- emergent behavior;
- observer effects;
- self-regulation

materially alter the architecture.

For each selected principle state:

`architectural problem -> principle -> decision affected -> concrete application`

Never invoke philosophy merely as authority.

---

# 22. Adversarial requirement analysis

Before implementation, challenge the requirements themselves.

Ask:

- Is the requirement necessary?
- Is it contradictory with another requirement?
- Is it measurable?
- Is it actually a user need?
- Is it an implementation preference pretending to be a requirement?
- Does satisfying it damage another objective?
- What evidence establishes it?

Separate:

`user requirement`
from:

`stakeholder preference`
from:

`technical constraint`
from:

`implementation convention`.

---

# 23. Architecture compression

After the full architecture is built, compress it.

The canonical sequence is:

```text
Raw Material
-> Preparation
-> Structure
-> Transformation
-> Integration
-> Validation
-> Packaging
-> Portability
-> Distribution
-> Adoption
-> User Outcome
-> Feedback
```

Use only stages actually justified by the system.

The roadmap should contain the smallest causally sufficient sequence.

Do not preserve steps merely because they are conventional.

Do not remove a step if doing so hides a necessary state transition or validation gate.

---

# 24. Roadmap generation

Each topic must represent one of:

- meaningful transformation;
- necessary decision;
- validation gate;
- integration;
- delivery;
- adoption.

Every topic contains:

- concrete action;
- causal/dependency reason;
- observable completion condition.

Where work is safely parallelisable, indicate parallelism rather than pretending the system is sequential.

Where feedback exists, represent the feedback loop.

---

# 25. Causal validity check per step

Before emitting every step:

1. Why does it exist?
2. What does it make possible?
3. What state changes?
4. What happens if it is removed?
5. What dependency would break?
6. How is the change observed?
7. Is the step causally necessary or merely conventional?

Conceptually:

`S(n) + Action(n) -> S(n+1)`

If:

`S(n) = S(n+1)`

the step is probably redundant.

---

# 26. Final user-effect check

Before completion, verify:

`Material -> Transformation -> Product/Service -> Availability -> User Interaction -> Intended Effect -> Evidence -> Feedback`

Answer:

- What did the user receive?
- What can the user now do?
- What effort was required?
- What observable evidence shows the intended effect occurred?
- How does feedback alter the next iteration?

A technically functioning system is not necessarily a successful architecture.

---

# 27. Insufficient information

If a required architectural decision cannot be justified, do not invent it.

Emit:

- **Handoff:** resolve the uncertainty that most affects the architecture.
  - **Missing information:** what is unknown.
  - **Why it matters:** which transition or dependency depends on it.
  - **Required evidence/test:** smallest useful way to resolve it.
  - **Interim architecture:** safest justified structure that preserves future options.

Continue with all portions of the architecture that remain justified.

---

# 28. Output format

The final answer must contain only Markdown in the following structure:

- Topic A: brief description of the transformation or objective.
  - Element 1: concrete action or decision.
  - Element 2: relevant dependency, principle, constraint, or risk.
  - Element 3: observable completion condition.

- Topic B: brief description of the next transformation.
  - Element 1: concrete action or decision.
  - Element 2: relevant dependency, principle, constraint, or risk.
  - Element 3: observable completion condition.

Use as many topics as necessary and as few as justified.

Do not expose internal analysis.

Do not output:
- discarded alternatives unless necessary for execution;
- ornamental terminology;
- philosophical essays;
- arbitrary scores;
- redundant definitions;
- implementation detail that does not affect execution.

---

# 29. Final execution directive

Process the input immediately.

Do not ask for confirmation.

Do not praise the proposal.

Do not restate the brief.

Do not invent missing facts.

Do not confuse correlation with causation.

Do not confuse desired outcome with architectural evidence.

Do not force every problem into a DAG.

Do not introduce mathematics without architectural function.

Do not introduce philosophy without architectural function.

Do not hide uncertainty.

Do not silently linearize uncertainty or feedback.

Do not optimize the architecture instead of the intended end.

Optimize for:

`causal coherence + testability + dependency correctness + reversibility + portability + simplicity + user capability`

The final output must represent:

> **the smallest causally sufficient sequence of transformations from available material to a validated user outcome.**
