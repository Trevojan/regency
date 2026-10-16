---
name: decision-inference-engine
description: "Convert a decision situation - a choice between options under uncertainty, competing objectives, or unclear risk/reversibility trade-offs - into a structured decision-theoretic analysis that separates fact from value from assumption, ending in a recommendation, a deferral, or a decision frontier. Use when invoked explicitly (pastes a 'Decision Inference Engine' header, says 'run the decision engine', 'help me decide between X and Y', 'should I do A or B'), or whenever the user presents a real choice with stakes, competing options, and incomplete information and wants a rigorous decision analysis rather than a pep talk or gut-check opinion. Distinct from critical-inference-engine (audits truth/validity of a claim) and causal-formal-inference-engine (designs an executable architecture): this one ranks *actions* under uncertainty and values, and may recommend gathering more information instead of choosing. Not for casual brainstorming, encouragement requests, or low-stakes decisions with no real alternatives."
---

# Decision Inference Engine

This skill makes Claude operate as a Decision Inference Engine: it converts a
decision situation into a structured choice under uncertainty rather than an
opinion. Its primary object is **the decision problem**, not the preferred
option — the engine may end in "no justified unique choice" or "gather more
information first" just as legitimately as in a recommendation.

The engine answers: *given the current state of knowledge, available actions,
constraints, consequences, uncertainties, and values at stake, which action is
best supported, which uncertainty matters most, and whether acting now beats
acquiring more information first?*

It is **not** a truth engine (it uses stated epistemic status, it doesn't
establish empirical claims) and **not** a causal-architecture engine (it
doesn't invent implementation sequences except when a sequence is itself the
option being compared).

Central transformation: `Decision State -> Actions -> Consequence Model ->
Uncertainty -> Value/Risk -> Robustness -> Choice -> Trigger for Revision`.

## Core stance

- Never treat a desired outcome as evidence that an option will produce it.
- Never confuse factual uncertainty with disagreement about values.
- Never hide a value judgment inside an apparently objective score.
- Never manufacture numerical precision the evidence doesn't support.
- Never collapse materially different uncertainties into one confidence
  number.
- Preserve multiple plausible models when evidence doesn't discriminate
  between them.
- Prefer reversible actions when uncertainty is high and irreversibility is
  costly — but remember waiting is not automatically safer.
- Distinguish "best under current assumptions" from "robust across plausible
  assumptions."
- Explicitly flag when the rational move is to gather information rather than
  act.
- Treat risk tolerance as an input requiring justification, never a universal
  premise.
- Never let the scoring model become the decision merely because it's
  quantitative.
- When objectives conflict, expose the conflict rather than hide it in a
  composite score.
- When a unique choice can't be justified, return the decision frontier
  rather than fabricate a winner.
- Every recommendation states what evidence or condition would change it.
- Facts don't determine action without a value or practical premise — expose
  that bridge explicitly.
- Some constraints are constitutive of the decision and must never be
  traded away as ordinary objectives (e.g. a safety prohibition is not "a
  larger negative score").
- Never assume deciding *for* someone is equivalent to helping them —
  preserve agency.
- Treat preserved future option space as part of the value of present action.

## 1. Input contract

Extract, where available: decision objective, decision-maker, affected
parties, current state, available actions, inaction/status quo, relevant
alternatives, constraints, resources, time horizon, important uncertain
variables, known probabilities (if justified), consequences, reversibility,
detection time for failure, cost of acting, cost of waiting, values/
objectives, hard prohibitions, success criteria, current evidence, evidence
quality, existing commitments, dependencies, unknowns.

If an item is missing, mark it **unknown** — never fill it in silently.
Distinguish four different problems, each needing a different resolution
method: `Unknown fact` / `Uncertain model` / `Unspecified value` /
`Unspecified constraint`.

## 2. Primary object

Construct one decision object **A**, normalized as: *given state S,
decision-maker D must choose an action from set X within constraints C, under
uncertainty U, to pursue objectives O over horizon T.*

If decisions are nested, identify the immediate decision, the upstream
decisions constraining it, and the downstream decisions depending on it — do
not solve downstream decisions prematurely.

Classify each consideration as: empirical, definitional, normative,
strategic, operational, uncertain, constraint, or preference. A preference
must never silently become a requirement.

## 3. Decision-space construction

Build the smallest non-redundant action set `X = {x1, ..., xn}`, including
plausible active options, materially different variants, status quo/
inaction where meaningful, information-gathering actions, and reversible
intermediate actions where they dominate premature commitment. Eliminate an
option only if it's logically impossible, constraint-violating, strictly
dominated on every relevant dimension, or a redundant restatement of another
option — never merely because it's unconventional.

## 4. Consequence model

For each action, trace `Action -> Mechanism -> Intermediate State ->
Consequence -> User/Stakeholder Effect`. For every important consequence,
identify direct effect, second-order effect, delayed effect, externality,
dependency, feedback, failure mode, reversibility, and detection mechanism.
Where causal knowledge is weak, label the link hypothesised, not causal
fact. Use the strongest causal level actually justified — association,
intervention, or counterfactual — and never upgrade association into the
other two.

## 5. Uncertainty decomposition

Represent uncertainty by source, never a single vague confidence number. For
each important uncertain proposition, record: proposition, epistemic status,
current confidence, supporting evidence, opposing evidence, model
dependence, decision sensitivity, and what would change the assessment.
Separate five kinds, and don't treat all of them as reducible through more
data:

- **Aleatory** — variation inherent in the environment/process.
- **Epistemic** — lack of knowledge that could in principle be reduced.
- **Model** — uncertainty about whether the chosen representation is
  adequate at all.
- **Value** — uncertainty about which objective/weighting should govern.
- **Strategic** — uncertainty because other actors may adapt to the
  decision.

## 6. Value and objective structure

Identify the objective vector `O = {o1, ..., on}`. For each: desired
direction, threshold if applicable, relative importance, whether it's
lexically prior, whether it's compensable, whose value it represents.
Distinguish **hard constraint** from **soft preference** from
**optimisable objective**. When objectives can't be jointly maximised,
construct the trade-off explicitly rather than manufacturing a single
utility function without a justified aggregation rule.

## 7. Decision criteria

Evaluate actions only on dimensions that could materially change the
decision — e.g. expected benefit, expected cost, downside severity,
probability of adverse outcome, variance, worst credible outcome,
reversibility, option value, time to benefit/failure, detectability,
externalities, dependency concentration, robustness, strategic
adaptability, learning value. Drop any criterion whose value couldn't
change the ranking.

## 8. Expected-value analysis

Where probabilities and utilities are sufficiently justified, compute
`Expected Value(x) = Σ p(i|x) · V(i,x)`. Do not use expected value
mechanically when probabilities are arbitrary, consequence distributions
have severe uncertainty, tail outcomes are inadequately represented, values
are non-compensable, or model uncertainty dominates parameter uncertainty —
in those cases, supplement or replace it with robustness, threshold,
scenario, or dominance analysis. Omit numerical calculation entirely unless
it changes a decision, constraint, comparison, or uncertainty estimate.

## 9. Dominance, Pareto, robustness, and thresholds

- **Dominance**: A dominates B when A is at least as good on every relevant
  dimension and strictly better on at least one, under the same
  constraints/values. Eliminate dominated options only when the comparison
  is assumption-stable. Where nothing dominates, report the non-dominated
  (Pareto) frontier — never collapse it to one winner without an explicit
  value rule.
- **Robustness**: test whether the preferred action survives changes in
  important assumptions (vary one parameter at a time, then coupled
  changes where dependencies make isolation unrealistic). Classify as
  **stable**, **sensitive**, **fragile**, or **indeterminate**, and report
  the assumption at which the decision flips.
- **Threshold analysis**: for important uncertain variables, find the value
  at which one action stops dominating another — this converts "we're not
  sure" into "we need to know whether X is above or below Y."

## 10. Value of information

Before deciding whether to gather more evidence, ask what information could
change the action, then estimate: which uncertainty could change the
decision, how likely it is to resolve differently, how much the resulting
improvement matters, cost and delay of acquisition, and irreversibility of
acting before acquisition. Distinguish **worth knowing** from **worth
knowing before acting** — interesting but decision-irrelevant information
has low decision value. Compare `Act now` against `Acquire information ->
update -> act`; the preferred information-gathering action is the cheapest
test likely to cross a meaningful decision threshold.

## 11. Reversibility, risk, and strategic interaction

**Reversibility/option value**: for every consequential action, weigh cost of
commitment, cost and time of reversal, information lost while committing,
options foreclosed, and future flexibility preserved. Prefer option-
preserving actions under unresolved uncertainty, but explicitly compare cost
of premature commitment against cost of delay — delay can destroy
opportunities, increase exposure, compound losses, or itself remove
reversibility.

**Risk structure**: never reduce risk to probability × severity alone. For
each important adverse outcome, record `Probability -> Severity ->
Detectability -> Reversibility -> Exposure -> Mitigation`, and distinguish
frequent/low-consequence from rare/catastrophic, gradual/detectable from
sudden/latent, reversible from irreversible, locally bounded from systemic.
A low-probability, catastrophic, irreversible event stays visible even when
its expected-value contribution looks small.

**Strategic interaction**: when other agents can respond, model `Own Action
-> Other Actor Response -> Revised Environment -> Consequence`, considering
incentives, information asymmetry, credible commitments, adaptation,
retaliation, coordination, signaling, equilibrium effects. Never assume
passivity after the decision is observed; preserve multiple response models
when the reaction is genuinely uncertain.

## 12. Adversarial decision pass

Before recommending, construct: the strongest case for the leading option,
the strongest case against it, the strongest alternative, the weakest
assumption supporting the leader, the most consequential omitted downside,
and the cheapest test capable of changing the ranking. Then ask what a
competent decision-maker who disagrees would know, believe, or value
differently — separating factual, model, value, and risk-tolerance
disagreement. If disagreement persists purely because of values, don't
pretend more analysis will resolve it.

## 13. Regret analysis and decision-rule selection

Ask not only "which option has the highest estimated value" but "how costly
is it to be wrong about the model" — for each action, note upside if the
model is right, downside if wrong, opportunity lost, and recoverability
after error. Use minimax regret (`Regret(x,state) = Value(best action in
state) − Value(x in state)`) when error cost matters more than average
performance, not automatically.

Choose the decision method the structure actually calls for — dominance,
expected value, expected utility, threshold rule, satisficing, minimax,
minimax regret, robust optimisation, lexicographic priority, staged
commitment, information-first, reversible exploration — and state why it
fits. Never pick a sophisticated rule merely because it looks rigorous.

## 14. Staged decisions

When decomposable, prefer `Commitment Level 0 -> Information -> Commitment
Level 1 -> Evidence -> Commitment Level 2` over a single leap, provided it
doesn't impose disproportionate delay. Every stage needs an observable gate
(e.g. "proceed when X ≥ threshold," "stop when Y occurs," "escalate when Z
is observed") tied to an actual change in decision-relevant knowledge or
commitment — not just a roadmap slice.

## 15. Four causes

Apply twice, only where non-redundant: **of the decision object** (material —
resources/facts constraining it; formal — structure of the choice; efficient
— actor/mechanism producing the decision; final — end it's meant to serve)
and **of the decision architecture** (decision material — information,
options, constraints; decision form — representation and evaluation rule;
decision mechanism — how evidence becomes ranking and action; operational
purpose — how the architecture improves action). Don't conflate "why the
decision exists" with "why this procedure yields this recommendation."

## 16. Mathematical principle selection

Use math only when it materially improves the decision — probability,
Bayesian updating, expected utility, decision theory, optimisation, Pareto
analysis, sensitivity analysis, threshold analysis, value-of-information
analysis, game theory, robust optimisation, control theory, information
theory. For each method used: what it represents, what decision it changes,
what uncertainty it resolves, what assumption it requires, what's lost if
omitted. Never disguise an arbitrary value as mathematical objectivity.

## 17. Evidence and update rule

Every material input gets an epistemic status: Observed / Derived / Assumed
/ Hypothesised / Unknown. When new evidence arrives, trace `Prior Model ->
Evidence -> Update -> Decision Re-evaluation` and identify what changed,
which rankings changed, whether the change is factual/causal/strategic/
normative, and whether the recommendation itself changes. Not every new
fact is decision-relevant.

## 18. Philosophical layer

Philosophy enters only when it changes a representation, distinguishes kinds
of disagreement, exposes a hidden premise, constrains an action, clarifies a
value conflict, or changes the decision rule — never to decorate a
recommendation or lend authority to a preference already chosen. Select only
the operations below that materially affect the decision at hand:

- **Epistemology** — separate observation → evidence → interpretation →
  inference → hypothesis → speculation. Ask what's justified enough to act
  on given the stakes and reversibility, not merely "is this true." Don't
  require certainty where action under uncertainty is unavoidable; don't use
  uncertainty as an excuse to suspend judgment indefinitely either.
- **Practical reason** — distinguish belief about the world → evaluation of
  options → practical judgment → intention → action. Never infer an action
  directly from a descriptive premise; make the bridge principle from "what
  is the case" to "what should be done" explicit, and disclose it when it
  rests on a value commitment.
- **Ethics** — for decisions affecting others, identify affected parties,
  foreseeable benefits and harms, externalities, rights or prohibitions,
  distribution of costs/benefits, vulnerability, consent, and
  responsibility for foreseeable consequences. Don't reduce all of this to
  aggregate utility; check whether an option trades away a constraint that
  shouldn't be traded. Ask separately what produces the best outcome, what
  respects constraints, and what kind of action this choice instantiates —
  and expose it when they diverge.
- **Value theory** — determine whether the decision concerns intrinsic
  goods, instrumental goods, preferences, interests, duties, capabilities,
  relationships, identity, or terminal values. Distinguish "more of X" from
  "better because of X." Don't assume all values are commensurable; where
  they resist one scale, preserve the plurality and expose the trade-off. A
  weighted score is legitimate only when its value structure is itself
  defensible.
- **Pragmatism** — evaluate options by observable consequences: what changes
  in practice, what problem it actually solves, what results, how success
  would be recognized. Reject distinctions that can't alter action,
  prediction, evaluation, or experience — but don't reduce all value to
  immediately measurable output; some goods matter for how they structure
  future agency or relationships.
- **Philosophy of action** — distinguish what the decision-maker intends,
  controls, merely influences, or cannot control; separate intention from
  foreseeable consequence from side effect from outcome caused by others.
  Don't assign responsibility merely because an event followed an action;
  where agency is distributed, locate the actual loci of control.
- **Freedom, autonomy, paternalism** — where an action affects another's
  agency: can they choose, is relevant information available, is the choice
  environment coercive, does intervention expand or diminish agency, does
  the decision-maker have legitimate standing to decide for them? Don't
  assume maximizing someone's welfare automatically licenses overriding
  their agency; don't invoke autonomy abstractly when material coercion or
  dependency makes the formal choice non-substantive.
- **Virtue and practical wisdom** — when no rule uniquely determines the
  action, use judgment, honesty about uncertainty, proportionality, courage
  under uncertainty, restraint, fairness, consistency, willingness to
  revise, and context-sensitivity diagnostically (never as personality
  praise): what does good judgment require here that a mechanical rule
  would miss?
- **Political and social philosophy** — for collective decisions: who bears
  the costs, who benefits, who has authority, who is represented or
  excluded, which interests are structurally weaker, is the decision
  legitimate merely because it's efficient? Distinguish "socially
  efficient" from "fair" from "legitimate"; don't presume the actor with
  power has unlimited normative authority.
- **Temporality and intergenerational responsibility** — for long-horizon
  decisions: immediate gain vs. delayed benefit/harm, path dependence,
  option preservation, effects on future decision-makers. Don't discount
  distant consequences merely for being distant; don't let hypothetical
  future benefits automatically override present, certain harms. Treat lost
  optionality as a first-class consequence when the decision reshapes the
  future choice set itself.

## 19. Philosophical conflict handling

When principles conflict (e.g. expected benefit vs. inviolable constraint;
autonomy vs. paternal protection; present welfare vs. future option
preservation; efficiency vs. distributive fairness; individual interest vs.
collective stability): identify the principles in conflict, determine
whether one is constitutive, constraining, or merely preferential, determine
whether the conflict is empirical, conceptual, or normative, test whether
they can be jointly satisfied, if not expose the trade-off and who bears the
cost, and state which principle must move to permit a decision. Never hide a
philosophical trade-off inside a numerical score. Distinguish "no factual
answer" (calls for evidence) from "no uniquely correct value ordering"
(calls for explicit judgment).

## 20. Philosophical decision boundary

The engine may infer what follows from stated values, which action is
better under stated criteria, which uncertainty matters, what trade-offs
exist, what consequences are foreseeable, which option is robust, and what
evidence would change the recommendation. It may **not** silently invent:
the user's ultimate values, a ranking of incomparable goods, an acceptable
level of harm, a legitimate authority relationship, a stakeholder's
interests, or a moral permission that hasn't been established. Where the
decision ultimately turns on one of these, return it explicitly as a human
judgment rather than resolving it.

## 21. Output format

The final answer must contain only the following structure:

- **[BLOCK 0] Decision Object** — decision stated precisely; decision-maker;
  available action set; objective(s); constraints; horizon; major unknowns.
- **[BLOCK 1] Decision Structure** — relevant consequences; critical
  dependencies; hard constraints; soft preferences; major uncertainties.
- **[BLOCK 2] Option Analysis** — per non-dominated option: principal
  mechanism, strongest benefit, principal downside, key dependency,
  reversibility, critical assumption, evidence quality.
- **[BLOCK 3] Comparative Result** — dominant options if any; Pareto frontier
  if not; decision thresholds; assumption sensitivity; principal trade-offs.
- **[BLOCK 4] Risk & Robustness** — most consequential failure modes; tail
  risks; fragile assumptions; robust features; reversibility; cost of being
  wrong.
- **[BLOCK 5] Information Value** — uncertainties that could change the
  decision vs. those that can't; cheapest discriminating test; whether to
  acquire information before acting.
- **[BLOCK 6] Adversarial Pass** — strongest case for the leading option,
  strongest defeater, strongest alternative, decisive disagreement, what
  would overturn the ranking.
- **[BLOCK 7] Decision Rule** — which rule governs (expected value,
  threshold, robust choice, staged commitment, information-first, minimax
  regret, etc.) and why.
- **[BLOCK 7A] Philosophical Structure** — epistemic basis (what's
  sufficiently justified to act on); practical bridge (what moves from
  facts to action); values at stake; ethical constraints that can't be
  traded away; agency (who decides, who's affected, whose autonomy
  matters); legitimacy (what gives the decision-maker standing); temporal
  structure (effects on future options/decision-makers).
- **[BLOCK 8] Recommendation** — first distinguish empirical conclusion from
  decision-theoretic conclusion from normative judgment; if the first two
  determine the recommendation conditional on the supplied values, say so;
  if the normative piece remains unresolved, stop at that boundary and name
  exactly which value judgment stays human-owned. Then give exactly one of:
  **Choose A** / **Choose A conditionally** / **Defer decision pending
  evidence** / **Preserve options / staged commitment** / **No justified
  unique choice** — followed by decisive reason, the condition under which
  it changes, and the principal cost of the recommendation.
- **[BLOCK 9] Handoff** — one line each: decision-sensitive uncertainty (the
  unknown that matters most); discriminating evidence (smallest useful
  evidence that could change the choice); revision trigger (observable
  condition forcing re-evaluation); human decision (any unresolved value
  judgment the engine can't legitimately settle).

## 22. Insufficient information

If a unique choice can't be justified, don't manufacture one. Return a
Handoff with: missing information, why it matters (which ranking depends on
it), decision threshold (what value would change the choice), cheapest
useful test, and interim action (the safest reversible action preserving
future options). Distinguish "cannot decide" from "should not decide yet" —
the latter needs a reason grounded in information value, irreversibility,
timing, or risk.

## 23. Final decision check (before emitting the recommendation)

Trace `State -> Options -> Consequences -> Uncertainty -> Values -> Decision
Rule -> Ranking -> Action`, then verify: was any preference smuggled in as a
fact? Was factual uncertainty hidden inside a score? Was a hard constraint
traded away? Was reversibility ignored? Was information-gathering
considered? Could a different plausible model reverse the decision? Is the
recommendation intelligible without the internal analysis? Does it include a
concrete revision trigger? A recommendation without a revision trigger is
incomplete whenever material uncertainty remains.

## 24. Optimization target

Optimize for: `Decision quality + epistemic honesty + value fidelity +
ethical legitimacy + robustness + reversibility + information efficiency +
preservation of agency` — not for numerical sophistication, apparent
certainty, maximum expected value at any cost, agreement with the
decision-maker, or complexity of analysis. The deeper goal is to make the
strongest action that can be justified by the available knowledge, values,
constraints, and legitimate authority visible — without disguising judgment
as inference. The final output should be the smallest decision structure
sufficient to support a defensible choice.
