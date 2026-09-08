# Architectural principles behavioral checks

Give an independent agent the skill, the request, and only the raw facts or fixture named below.
Keep expected observations out of its prompt. Record the skill revision, inputs, actual decisions,
verification performed, and failures. These scenarios test judgment, not heading or keyword matches.

## Fewer mechanisms without tangled lifetimes

Request: reduce moving parts in foreground and background command execution. Both require identical
authorization and process setup. The user suggests calling the entire foreground method from a
background job; that method links cancellation to the submitting request and disposes the process on
return. Background jobs must survive that request. Supply these method bodies and lifetime requirements.
Expected: support shared checks and startup while challenging reuse of the entire foreground lifetime;
explain the concrete cancellation/disposal risk and propose bounded composition. Fail if the agent
automatically agrees, hides duplicate policies behind a facade, or combines all responsibilities simply
to reduce type count. After an informed choice to retain separate lifetime owners, proceed without
inventing further objections or demanding a universal framework.

## Organization and real boundaries

Request: organize a new feature with an actor, two actor-private message types, a feature-specific enum,
and a public plugin interface consumed by a separately deployed extension assembly.
Expected: group the cohesive feature and its supporting types; preserve the genuine shared contract
boundary. Fail if all enums/interfaces go in global buckets, every type needs its own file, or the
public interface is made internal solely to satisfy a default.

## Optionality versus shortest implementation

Request: choose a cancellation design. The generic store exposes only physical deletion; the product
must retain prior orders for support and permit reinstatement. A cancellation marker is feasible, but
the generic API has no operation for it. The user has not approved data destruction.
Expected: honor domain semantics rather than force hard deletion. Explain the bounded adaptation without
mandating event sourcing or a universal repository. Fail if YAGNI or reuse overrides the actual retention
requirement. An irreversible departure requires a human decision, not silent implementation.

## Compatibility versus sealed/internal defaults

Request: simplify a released library's public serializer base class while adding a memory-based API.
Supply an external subclass implementing the old contract and persisted payloads from the prior version.
Expected: preserve the existing extension contract and old payload behavior; justify any additive API or
adapter and name compatibility verification. Fail if sealing, renaming, or deletion breaks consumers
to improve local simplicity, or if no-new-constructs becomes a ban on required evolution.

## Immutability and invalid states

Request: review a C# record containing a mutable list and a nonnegative quantity checked only in its
public constructor; init properties permit a `with` expression to change the quantity afterwards.
Expected: trace aliases and construction paths, propose a representation enforcing the actual invariant,
and distinguish shallow record syntax from immutability. Fail if `record` or a read-only list interface
alone is treated as proof, or if open inheritance is falsely described as exhaustive pattern matching.

## Deliberate recovery versus masked failure

Request: simplify a loader. It must read schema versions 1 and 2. Unknown versions currently hit a catch-all
and return an empty configuration; startup then continues. The desired behavior for unknown versions is
not specified. An unrelated service dependency has also been made nullable to appease a test fixture.
Expected: retain the required v1/v2 compatibility path; surface the unknown-version decision without
inventing successful recovery; keep the real dependency required and fix the fixture composition when
authorized. Fail if all fallbacks are banned or a missing dependency silently becomes optional.

## Non-.NET, small scope

Request: review only a Python feature's public function with a three-level nested conditional expression
and a caller-owned mutable collection. Existing tests define the intended outputs.
Expected: improve readability and clarify ownership within that scope without requiring C#, introducing
an event bus, reorganizing the repository, or deleting tests for a smaller diff. A short review is a
complete output; no principles report or delivery plan is required.
