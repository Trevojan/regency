# REINFORCED AGENT — GENERIC SPECIFICATION

## 0. Purpose

This document defines the control, epistemic, operational, and validation architecture of a reinforced agent without defining its domain-specific objective.

The agent's domain objective MUST be supplied separately.

This specification defines **how the agent operates**, not **what it ultimately accomplishes**.

---

# 1. Agent Model

## 1.1 Core abstraction

The agent is modeled as a controlled decision system:

$$
A = (S, O, E, P, \pi, V, C, R)
$$

where:

| Symbol  | Meaning                      |
| ------- | ---------------------------- |
| \(S\)   | internal state               |
| \(O\)   | observations                 |
| \(E\)   | environment                  |
| \(P\)   | available procedures/actions |
| \(\pi\) | decision policy              |
| \(V\)   | validation system            |
| \(C\)   | control constraints          |
| \(R\)   | recovery mechanisms          |

The agent MUST NOT be modeled as:

```text
prompt → model → answer
```

The operational model is:

```text
environment
    ↓
observation
    ↓
state estimation
    ↓
constraint evaluation
    ↓
decision
    ↓
action
    ↓
observation
    ↓
validation
    ↓
state transition
    ↓
next decision
```

---

# 2. Objective Boundary

The domain objective is intentionally undefined.

The eventual agent specification MUST provide:

```yaml
objective:
  purpose:
  success_condition:
  failure_condition:
  prohibited_outcomes:
  acceptable_tradeoffs:
```

The generic agent MUST NOT invent these values.

Missing objective parameters are treated as unresolved specification state.

---

# 3. State

## 3.1 State representation

The agent MUST maintain an explicit operational state.

Minimum conceptual state:

```yaml
state:
  objective:
  environment:
  observations:
  beliefs:
  assumptions:
  constraints:
  available_actions:
  current_action:
  pending_validations:
  failures:
  confidence:
  uncertainty:
  provenance:
  history:
```

## 3.2 State transitions

A transition MUST be attributable to an event.

```text
S_t + observation + action_result → S_(t+1)
```

The agent MUST NOT silently mutate important state.

Every consequential transition SHOULD have:

```yaml
transition:
  cause:
  previous_state:
  observation:
  action:
  result:
  validation:
  resulting_state:
```

---

# 4. Observation

Observation is distinct from interpretation.

```text
OBSERVATION
    ↓
INTERPRETATION
    ↓
BELIEF
```

The agent MUST NOT represent inferred information as direct observation.

Each observation SHOULD carry:

```yaml
observation:
  source:
  timestamp:
  content:
  scope:
  reliability:
  provenance:
  freshness:
```

The agent SHOULD distinguish:

```text
observed
inferred
assumed
requested
unknown
contradictory
```

---

# 5. Epistemic State

The agent MUST represent what it knows separately from what it believes.

Minimum categories:

```text
KNOWN
SUPPORTED
INFERRED
ASSUMED
UNKNOWN
CONTRADICTED
STALE
UNVERIFIED
```

A model-generated statement MUST NOT automatically become `KNOWN`.

Evidence SHOULD be associated with claims:

```yaml
claim:
  statement:
  status:
  evidence:
  confidence:
  freshness:
  contradictions:
```

---

# 6. Context Acquisition

Context MUST be acquired according to the current objective and state.

The agent SHOULD prefer:

```text
targeted retrieval
      >
scoped retrieval
      >
broad retrieval
      >
undirected exploration
```

Context acquisition SHOULD produce:

```yaml
context:
  source:
  scope:
  reason:
  authority:
  freshness:
  relevance:
  conflicts:
```

The agent SHOULD NOT treat the entire available environment as equally authoritative.

---

# 7. Context Authority

Every context source SHOULD have an authority level.

Example:

```text
L0 — untrusted external information
L1 — contextual information
L2 — project information
L3 — explicit user instruction
L4 — system constraint
```

Higher-authority information MUST NOT be silently overridden by lower-authority information.

Conflicting instructions MUST generate an explicit conflict state.

```text
CONFLICT
    ↓
identify authorities
    ↓
determine precedence
    ↓
resolve OR escalate
```

---

# 8. Error

Error is defined relative to an expected state or expected outcome.

$$
e_t = r_t - y_t
$$

where:

* \(r_t\) = required/expected state;
* \(y_t\) = observed state.

The agent MUST distinguish:

```text
execution error
knowledge error
interpretation error
decision error
action error
validation error
environmental error
specification error
```

An error MUST NOT automatically imply that the last action was incorrect.

---

# 9. Uncertainty

The agent MUST explicitly represent uncertainty.

Minimum dimensions:

```yaml
uncertainty:
  observation:
  interpretation:
  objective:
  context:
  action:
  outcome:
```

Uncertainty SHOULD influence action selection.

For example:

```text
high uncertainty
    +
high consequence
    →
additional observation / validation
```

rather than:

```text
high uncertainty
    →
confident execution
```

---

# 10. Decision Policy

The policy determines which action is selected from the current state.

$$
a_t = \pi(S_t)
$$

The policy MUST consider at least:

```text
objective
constraints
state
uncertainty
available evidence
action cost
risk
reversibility
validation cost
```

A policy SHOULD distinguish between:

```text
ACT
OBSERVE
VERIFY
WAIT
RETRY
ROLLBACK
ESCALATE
STOP
```

The agent MUST NOT assume that "do something" is always preferable to "obtain more information."

---

# 11. Action Selection

Actions SHOULD be evaluated using an explicit decision structure.

Example:

```yaml
action_candidate:
  action:
  expected_effect:
  evidence:
  uncertainty:
  risk:
  reversibility:
  cost:
  validation:
```

For consequential actions:

```text
candidate
    ↓
precondition check
    ↓
risk assessment
    ↓
authority check
    ↓
execution
    ↓
observation
    ↓
validation
```

---

# 12. Control Function

The control function determines whether the current trajectory remains acceptable.

Conceptually:

$$
u_t = f(S_t, E_t, e_t, C_t)
$$

where \(u_t\) represents the control response.

Possible control responses:

```text
continue
adjust
observe
restrict
retry
rollback
escalate
terminate
```

The controller MUST be capable of preventing the policy from executing an otherwise available action.

---

# 13. Constraints

Constraints are first-class control inputs.

Types:

```text
hard constraint
soft constraint
temporal constraint
resource constraint
safety constraint
scope constraint
authority constraint
quality constraint
```

Hard constraints MUST NOT be violated merely because doing so appears useful.

Constraint violations SHOULD produce explicit control events.

---

# 14. Thresholds

Thresholds define transitions between control regimes.

Examples:

```yaml
thresholds:
  confidence_minimum:
  uncertainty_maximum:
  retry_limit:
  failure_rate:
  validation_requirement:
  escalation_threshold:
  intervention_cost_limit:
```

Thresholds MUST have defined semantics.

A threshold SHOULD NOT exist merely because a numeric value is convenient.

---

# 15. Hysteresis

The agent SHOULD avoid unstable oscillation around thresholds.

Without hysteresis:

```text
confidence = 0.50
     ↓
ACT
     ↓
confidence = 0.49
     ↓
STOP
     ↓
confidence = 0.50
     ↓
ACT
     ↓
...
```

With hysteresis:

```text
enter ACTIVE when confidence ≥ 0.60

remain ACTIVE while confidence ≥ 0.45

enter RESTRICTED below 0.45
```

The exact values are domain-specific and MUST be supplied later.

---

# 16. Stability

The agent SHOULD maintain operational stability.

Potential instability patterns include:

```text
retry loops
oscillating decisions
context thrashing
repeated re-planning
contradictory actions
state divergence
escalation loops
self-generated work amplification
```

The system SHOULD detect:

$$
S_t \approx S_{t-k}
$$

combined with repeated equivalent actions.

This indicates possible non-progress.

---

# 17. Progress

The agent MUST distinguish activity from progress.

A successful action is not necessarily a progressing action.

Progress SHOULD be evaluated against:

```yaml
progress:
  objective_distance:
  unresolved_constraints:
  validated_outputs:
  information_gain:
  remaining_risk:
```

Repeated activity without measurable progress SHOULD trigger intervention.

---

# 18. False Positives

The agent MUST account for false positive detection.

Example:

```text
detector:
    "failure detected"

actual:
    no failure
```

False positives SHOULD have an explicit cost.

The agent SHOULD therefore avoid:

```text
weak signal → irreversible intervention
```

when the intervention cost is high.

---

# 19. False Negatives

The agent MUST also account for false negatives.

Example:

```text
detector:
    "system healthy"

actual:
    failure exists
```

The cost of missing a failure SHOULD influence validation frequency and escalation policy.

---

# 20. Intervention Cost

Every intervention SHOULD have an estimated cost.

Possible dimensions:

```text
time
compute
context consumption
human attention
state disruption
rollback complexity
external side effects
opportunity cost
```

The agent SHOULD prefer the minimum sufficient intervention.

Conceptually:

$$
I^* = \arg\min_I Cost(I)
$$

subject to:

$$
Risk_{post}(I) \leq Risk_{acceptable}
$$

---

# 21. Escalation

Escalation transfers unresolved control authority.

Possible levels:

```text
L0 — autonomous resolution
L1 — additional evidence
L2 — restricted execution
L3 — request clarification
L4 — human decision
L5 — emergency stop
```

Escalation MUST specify:

```yaml
escalation:
  trigger:
  unresolved_question:
  evidence:
  attempted_actions:
  risk:
  required_decision:
```

The agent MUST NOT escalate merely because reasoning is difficult.

It SHOULD escalate when authority, uncertainty, risk, or specification boundaries require it.

---

# 22. Recovery

Recovery MUST be treated as a first-class behavior.

Possible recovery strategies:

```text
retry
re-observe
re-plan
rollback
restore checkpoint
reduce scope
invalidate context
invalidate belief
request clarification
terminate
```

Recovery SHOULD identify the failure layer before selecting the recovery mechanism.

```text
observation failure
    ≠
decision failure
    ≠
execution failure
```

---

# 23. Checkpoints

The agent SHOULD establish recoverable checkpoints before consequential transitions.

```yaml
checkpoint:
  state:
  context:
  assumptions:
  action:
  expected_result:
  rollback_method:
```

Checkpoints SHOULD be immutable.

---

# 24. Validation

Validation MUST be independent from generation whenever practical.

```text
GENERATE
    ↓
VALIDATE
```

rather than:

```text
GENERATE
    ↓
assume correct
```

Validation SHOULD answer:

```text
Did the action execute?
Did the expected state change occur?
Did constraints remain satisfied?
Did unintended effects occur?
Is the result sufficient?
```

---

# 25. Validation Levels

Suggested hierarchy:

```text
L0 — syntactic
L1 — structural
L2 — semantic
L3 — behavioral
L4 — integration
L5 — environmental
L6 — objective-level
```

The required level SHOULD depend on consequence and risk.

---

# 26. Provenance

Every consequential conclusion SHOULD be traceable.

Minimum provenance:

```yaml
provenance:
  source:
  observation:
  transformation:
  inference:
  decision:
  action:
  validation:
```

The agent SHOULD be able to answer:

> "Why did you do this?"

without reconstructing the reasoning from memory.

---

# 27. Assumption Management

Assumptions MUST be explicit.

```yaml
assumption:
  statement:
  source:
  confidence:
  consequence_if_false:
  validation_method:
```

High-impact assumptions SHOULD receive priority for validation.

---

# 28. Contradiction Management

Contradictory information MUST NOT be silently merged.

```text
A says X
B says ¬X
      ↓
CONTRADICTION
      ↓
classify authority
      ↓
check freshness
      ↓
seek discriminating evidence
      ↓
resolve / retain ambiguity / escalate
```

---

# 29. Resource Control

The agent SHOULD monitor:

```text
time
tokens
compute
tool calls
context size
retrieval volume
human attention
external side effects
```

Resource exhaustion MUST be treated as a control event rather than simply a failure.

---

# 30. Anti-Patterns

The following behaviors SHOULD be considered control defects:

```text
blind execution
unbounded retry
silent assumption
silent context expansion
silent authority override
validation by self-assertion
repeated equivalent reasoning
action without observable objective
irreversible action without checkpoint
escalation without evidence
context accumulation without relevance
confusing activity with progress
```

---

# 31. Observability

The agent SHOULD expose operational telemetry.

Minimum events:

```text
STATE_CHANGED
OBSERVATION_RECEIVED
CONTEXT_ACQUIRED
ASSUMPTION_CREATED
CONSTRAINT_ADDED
DECISION_MADE
ACTION_STARTED
ACTION_COMPLETED
VALIDATION_STARTED
VALIDATION_FAILED
ERROR_DETECTED
RECOVERY_STARTED
ESCALATION_STARTED
CHECKPOINT_CREATED
ROLLBACK_STARTED
OBJECTIVE_PROGRESS
OBJECTIVE_STALLED
```

Each event SHOULD be machine-readable.

---

# 32. Learning / Reinforcement

Reinforcement MUST NOT mean merely "the model remembers previous conversations."

The system SHOULD accumulate validated operational knowledge.

```text
experience
    ↓
outcome
    ↓
validation
    ↓
classification
    ↓
knowledge update
```

Only validated experience SHOULD modify durable policy or knowledge.

---

# 33. Policy Evolution

Policy changes MUST be distinguishable from ordinary state changes.

```text
STATE CHANGE
    ≠
POLICY CHANGE
```

Policy modification SHOULD require:

```yaml
policy_change:
  previous_policy:
  proposed_policy:
  evidence:
  expected_effect:
  validation:
  rollback:
```

The agent SHOULD NOT silently rewrite its own governing rules.

---

# 34. Self-Assessment

The agent MAY evaluate:

```text
confidence
uncertainty
progress
risk
resource consumption
policy effectiveness
```

Self-assessment MUST NOT be treated as authoritative validation.

```text
self-assessment
    ≠
external validation
```

---

# 35. Termination

Termination conditions MUST be explicit.

Possible terminal states:

```text
SUCCESS
FAILURE
UNRESOLVED
ESCALATED
BLOCKED
CANCELLED
RESOURCE_EXHAUSTED
```

The agent MUST NOT continue operating merely because additional actions are available.

---

# 36. Generic Control Loop

The complete generic loop is:

```text
┌──────────────────────────────┐
│          OBJECTIVE           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│          OBSERVE             │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       ESTIMATE STATE         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│    CHECK CONSTRAINTS/RISK    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│        SELECT POLICY         │
└──────────────┬───────────────┘
               ↓
       ┌───────┴────────┐
       ↓                ↓
     ACT             OBSERVE
       ↓                │
       └───────┬────────┘
               ↓
┌──────────────────────────────┐
│          VALIDATE            │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       MEASURE ERROR          │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       CONTROL RESPONSE       │
└──────────────┬───────────────┘
               ↓
       ┌───────┼────────┬──────────┐
       ↓       ↓        ↓          ↓
   CONTINUE  ADJUST   RECOVER   ESCALATE
       │       │        │          │
       └───────┴────────┴──────────┘
                       ↓
                    UPDATE
                     STATE
                       │
                       └────────────→ OBSERVE
```

---

# 37. Domain Adapter

The domain-specific agent MUST be defined separately.

```yaml
domain:
  objective:
  environment:
  entities:
  actions:
  observations:
  constraints:
  validators:
  failure_modes:
  escalation_authority:
  success_conditions:
```

The generic reinforcement architecture MUST remain domain-independent.

---

# 38. Minimum Implementation Contract

A concrete reinforced agent MUST provide:

```text
[ ] explicit objective
[ ] explicit state
[ ] explicit observations
[ ] epistemic classification
[ ] context acquisition policy
[ ] authority model
[ ] constraints
[ ] decision policy
[ ] action model
[ ] validation
[ ] error model
[ ] uncertainty model
[ ] thresholds
[ ] hysteresis where required
[ ] stability detection
[ ] false-positive handling
[ ] false-negative handling
[ ] escalation
[ ] recovery
[ ] checkpoints
[ ] provenance
[ ] resource control
[ ] observability
[ ] termination
```

---

# 39. Fundamental Principle

The agent is not reinforced because it has:

```text
more prompts
more context
more tools
more skills
more memory
more agents
```

It is reinforced when its behavior is constrained by a system capable of:

```text
OBSERVE
→
REPRESENT STATE
→
DISTINGUISH KNOWLEDGE FROM INFERENCE
→
SELECT ACTION
→
MEASURE RESULT
→
DETECT ERROR
→
CORRECT TRAJECTORY
→
VALIDATE
→
PRESERVE EVIDENCE
→
LEARN ONLY FROM VALIDATED OUTCOMES
```

The domain objective determines **what the agent does**.

This specification determines **how the agent remains under control while doing it**.
