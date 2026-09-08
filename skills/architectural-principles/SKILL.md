---
name: architectural-principles
description: Guide design, implementation, and review decisions about new constructs, feature organization, state, contracts, and extension points. Apply maintainability and reversibility defaults within the requested change; not a whole-system assessment or a delivery-planning workflow.
---

# Architectural principles

Make the requested change understandable, maintainable, and inexpensive to revise. These are defaults
for architectural decisions, not a mandatory architecture, a score, or an always-on mode.

Read the affected code, its consumers, and relevant project guidance first. Establish the required
behavior, compatibility boundaries, and ranked goals. Distinguish discoverable implementation facts
from human-owned priorities. Apply only the principles relevant to the change; do not reorganize an
unrelated codebase to make it conform. For C#, read [the implementation flavor](references/csharp.md).
Other languages use their own equivalent mechanisms; no particular compiler or tool is required.

## Decision defaults

- **Reuse what fits; justify what is new.** Look for existing capabilities, standard-library or native
  features, and suitable installed dependencies before inventing a mechanism. Reuse requires matching
  responsibilities and contracts, not merely similar code. Compare the ownership and operational cost
  of a new dependency with implementing the needed behavior; neither choice is automatically smaller.
- **YAGNI.** Introduce the fewest lasting concepts needed for actual requirements. New types, layers,
  configuration, and extension points must earn their place. Do not build hypothetical features or
  hide complexity in generic wrappers and parameter bags to reduce apparent counts.
- **Fewest moving parts.** Meet actual requirements with the fewest independent mechanisms, policy
  owners, and coordination paths. Consolidate competing ways of doing the same job; do not merely hide
  them behind one facade. Preserve distinct responsibilities and lifetimes where they matter: fewer
  parts does not mean one giant component, fewer files, or the shortest implementation.
- **High cohesion, low coupling.** Organize by capability and purpose. Prefer vertical slices with
  related behavior and contracts adjacent, rather than global buckets for enums, interfaces, or helpers.
  Keep a cohesive unit and its small supporting types together, including in one file when readable.
  Separate independently useful types and genuinely shared infrastructure by their named responsibility.
  A real dependency or public-contract boundary can justify a dedicated abstractions package.
- **Explicit dependencies, outcomes, and invariants.** Prefer meaningful inputs, typed outcomes, and
  explicit transitions over hidden shared state, contradictory flags, or many optional parameters.
  Make illegal states unrepresentable where practical. Use value objects and the type system to enforce
  real invariants; validate untrusted inputs at boundaries. Typed events can help without requiring an
  event-driven architecture or ceremonial wrappers for every primitive.
- **Immutable data by default.** Prefer immutable values and explicit state transitions. Localize
  necessary mutation to a clear owner with a justified lifecycle or performance need. Check contained
  collections and aliases; an immutable-looking outer declaration does not prove immutable contents.
- **Narrow contracts and intentional extension.** Keep constructs implementation-private and closed
  to inheritance unless consumers need a supported extension contract. Prefer composition over
  inheritance. Do not change an existing public or overridable contract merely to apply these defaults.
  Avoid speculative fallbacks and optional inputs that conceal failed assumptions. A required
  compatibility or recovery path needs explicit conditions, outcomes, and verification.
- **Readability over cleverness.** Prefer obvious control flow and named steps to nested ternaries,
  dense chains, and compressed expressions. Optimize for a human understanding and reviewing the unit,
  not minimum lines, files, or declarations. Simple expressions need no mechanical expansion.
- **Extend-only at compatibility boundaries.** Preserve released public API, wire, storage, schema,
  and behavioral contracts relied upon by consumers or older versions. Prefer additive, opt-in evolution
  with compatibility verification. This does not freeze private implementation. Retirement or a breaking
  change requires an agreed migration/versioning decision; local simplicity does not erase obligations.
- **Preserve optionality.** Consider the cost of changing a decision, recovering data, or replacing a
  dependency. A modest, justified cost now can preserve inexpensive future choices without implementing
  speculative features. Do not let a convenient abstraction dictate destructive domain behavior.
  Event sourcing, soft deletion, and replaceable boundaries are techniques, not universal requirements;
  respect the project's data-retention and deletion requirements.
- **Preserve guarantees and proof.** Do not obtain a smaller implementation by silently removing
  required behavior, safety checks, or meaningful verification. Make intended behavior changes explicit.
  Compatibility adapters and focused tests may legitimately increase code while reducing overall risk.

## Resolve trade-offs and finish

Evaluate user suggestions against the same principles and source evidence as your own proposals.
When a suggestion creates concrete coupling, compatibility risk, or an unreviewable expansion, say
what would change, why that matters, and recommend a narrower or more reversible alternative. Ground
pushback in affected behavior or code, not a principle's name alone; label uncertain consequences as
inferences. Do not invent objections to appear rigorous. Respect an informed user choice within hard
constraints and authorized scope; record the accepted trade-off without repeatedly relitigating it.

For consequential, hard-to-reverse choices or conflicts with project priorities, pause that decision
before committing the design or implementation. Present a short recommendation, viable alternatives,
and the consequences; ask one focused human question. Continue independent, authorized work if useful.
Do not treat the absence of a preferred language feature as a blocker or impose event sourcing,
inheritance bans, or a new framework to comply with these defaults.

Produce the requested design, code, or review, not a separate principles report. Explain only material
new constructs, departures, and unresolved trade-offs in the existing artifact or PR. When work spans
turns, checkpoint those decisions and remaining verification there rather than accumulating new notes.
Finish at the requested scope with verification results and limits; an assessment does not authorize
implementation, and applying these principles does not authorize adjacent refactoring or rollout.

The compatibility and reversibility defaults draw on
[extend-only design](https://aaronstannard.com/extend-only-design/) and
[high-optionality programming](https://petabridge.com/blog/high-optionality-programming-pt1/).
These explanations are background, not additional mandatory runtime reading.
