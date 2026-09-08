---
name: simplify
description: Identify and prioritize technical debt, competing mechanisms, and safe code simplifications using architecture evidence, metrics, and history. Use when asked to assess debt or reduce system complexity; findings do not authorize automatic refactoring.
---

# Simplify

Find changes that reduce the system's lasting maintenance and reasoning burden while preserving intended
capabilities and verification. Work from a current architecture model, or reconstruct enough of the
affected system first. The model may come from `architecture-assessment` or an equivalent source.

## Ground the assessment

Record revision, scope, goals, constraints, and measurement methods. Use project-specific debt strategies
when present; inspect their supporting history before treating local lessons as universal rules.
For relevant languages and execution surfaces, consult only the applicable evidence flavor:
[C#/.NET](../architecture-assessment/references/csharp.md),
[backend](../architecture-assessment/references/backend.md), or
[user experiences](../architecture-assessment/references/experience.md).
If those companion resources are unavailable, use equivalent local tooling. Core reasoning does not
depend on any one programming language or analyzer.

Use metrics to select places to investigate: size concentration, branching, parameter load, coupling,
duplication, churn, and repeated defects. Check raw examples and counterexamples. Declare unavailable
metrics. Do not turn thresholds into findings or infer conceptual duplication from text similarity alone.
For a bounded source-level question, explicitly stating that metrics were unnecessary is sufficient.

## Account for the concepts

Use [architectural-principles](../architectural-principles/SKILL.md) when judging proposed alternatives:
apply the relevant defaults within project priorities and the requested scope, not as a separate
report or a reason to retrofit unrelated code.

For each candidate, compare the responsibilities and mechanisms that exist with a smaller proposed
arrangement. Trace callers, authority, state lifetime, side effects, failure behavior, and public,
wire, or storage compatibility. Explain why reuse, extension, or consolidation is adequate.

Distinguish necessary complexity from accidental complexity. Keep a rejected candidate when its
counterevidence prevents a likely future mistake. Replacing an existing mechanism can still introduce
a durable construct; account for additions, removals, and coexistence rather than counting only deletions.

Consider deleting proven dead paths, consolidating duplicated policy, reusing platform primitives,
retiring obsolete adapters, or restoring clear ownership. Do not conceal dependencies in parameter bags,
compress source formatting, remove useful tests, or weaken validation to improve a metric.

## Propose bounded work

Use [the finding contract](references/finding.md) for concrete findings. Rank by demonstrated friction,
expected simplification, risk, and verification readiness. Avoid numerical precision without evidence.
Separate small enabling changes from larger redesigns. Prefer paying down debt on the requested change
path before layering new functionality over it; do not expand this into unrelated cleanup.
When a human-facing proposal is requested, use [the proposal contract](references/proposal.md).
Keep the current model, decision, and eventual result distinct; these are logical outputs, not three
mandatory documents. Move between understanding, evaluation, decision, and verification as evidence
requires. Agree on the review stopping point before treating a proposal as implementation authority.

When alternatives conflict with ranked goals or create substantial future obligations, frame a short
human decision with viable alternatives and a recommendation. If `interview` is available, pass the
outcome, facts, constraints, and decision areas as context; otherwise use the same concise conversation
directly. A finding may remain pending that decision without blocking independent assessment work.

## Deliver and retain only useful state

Produce a compact prioritized assessment with source evidence, metric provenance, counterevidence,
expected concept changes, preserved behaviors, verification procedures, and uncovered areas. Maintain
this artifact across turns instead of an append-only investigation transcript.

Completion means the agreed areas have actionable findings, explicit deferrals, or supported non-findings.
An assessment may conclude that no change is warranted. Assessment is not
implementation or proof of achieved reductions. A later implementation must compare the same baseline,
record the actual result, and update the current system model. Keep invocation history in Git and link
specific rationale when needed. Promote recurring successful tactics into the project's compact debt
strategy; shared skill changes require broader evidence than one cleanup.
