# Backend evidence flavor

Map the execution model actually present: services, actors, request handlers, jobs, pipelines, or
in-process library calls. Trace an input to its side effects and response, including failure and retry.
Identify composition roots, policy decisions, transport adapters, persistent contracts, and resource owners.

Where several paths appear to overlap, compare their consumers, authority, state lifetime, failure
semantics, and compatibility duties. Separate policy duplication from necessary transport differences.
An actor or coordinator may legitimately own a lifecycle while accumulating too many policy decisions.
Propose consolidation only after identifying a coherent existing seam and behavior-preservation evidence.

Validate dependency graphs against dynamic wiring. A static acyclic project graph does not establish
acyclic runtime interactions. Record which relationships were traced and which remain inferred.
