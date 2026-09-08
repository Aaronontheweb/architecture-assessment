---
name: architecture-assessment
description: Reconstruct a software system's current architecture from code, runtime wiring, tests, and history. Use for architecture discovery, a legacy-system assessment, or preparing a simplification effort; ordinary feature work does not require a whole-system assessment.
---

# Architecture assessment

Explain how the system works, why its durable parts exist, and which constraints govern changes.
This is an assessment; it does not authorize refactoring, deleting specifications, or changing policy.

## Establish the evidence boundary

Identify the repository, revision, scope, and intended use of the result. Discover facts before asking
the human for priorities or intent. Preserve existing checkout changes. When a clean baseline is needed,
use a separate worktree from the agreed branch and record its commit. Do not substitute another fork
or an unmerged branch without saying so.

Read repository guidance and the relevant existing documentation. Treat historical plans as claims to
check. Keep observed behavior, declared goals, inferred rationale, and desired changes distinct.
This includes canonical glossaries: reuse supported distinctions, but label definitions that describe
planned or retired behavior rather than importing them into the current architecture.
Record missing evidence and contradictions instead of quietly reconciling them into invented truth.
Distinguish the user's ranked goals from observed implementation choices. If a consequential decision
depends on an unknown priority, ask about that trade-off rather than inferring a project constitution.

## Select only relevant implementation flavors

The reasoning and outputs below apply across languages. Languages and execution surfaces supply
additional evidence methods; they do not impose an architecture or create new personas.

- For C#/.NET, read [the C# flavor](references/csharp.md).
- For services, libraries, workers, or actor systems, read [backend evidence](references/backend.md).
- For browser, native, terminal, or chat experiences, read [experience evidence](references/experience.md).

Combine relevant flavors. When no flavor exists, use the repository's established tools and report
their limits. Do not invent a plugin framework or another skill just to support a new tool.

## Reconstruct the system

Start with a bounded inventory of products, processes, modules, dependencies, and existing verification.
The optional `scripts/repository_baseline.py` collects reproducible file and size counts from a Git
commit. It neither reads uncommitted content nor measures architectural quality.
Read [baseline procedure and limits](references/metrics.md) when collecting or comparing measurements.

Trace representative journeys across boundaries, including an important failure or recovery path.
For each substantial responsibility, establish:

- its purpose, callers, consumers, and authoritative owner;
- the state and resource lifetimes it owns;
- contracts, side effects, dependencies, and ordering constraints;
- how new behavior enters through existing seams;
- tests or runtime evidence that support these claims.

Inspect composition roots and indirect dispatch as well as static dependencies. Folder names and type
counts alone do not establish bounded contexts or responsibility. Distinguish reusable mechanisms,
platform adapters, and compatibility paths from competing implementations of the same responsibility.

If parallel reviewers are authorized, divide by coherent subsystem or journey. Give each the same
revision and evidence contract. Reconcile shared boundaries centrally; do not concatenate reports into
an architecture. Treat source size as an investigation signal, not a reason to split a component.

## Produce a compact current model

Use the existing canonical artifact when suitable. Otherwise create a small navigable report in the
agreed workspace. Include a system overview, a diagram where relationships warrant it, responsibility
and ownership boundaries, important contracts and journeys, evidence links, and known uncertainties.
Keep detailed inventories in machine-readable output and historical rationale available by reference.
Do not generate one document per class or reproduce the entire specification corpus.
For large inventories that need selective queries and purpose annotations, use the optional
[SQLite catalog](references/catalog.md). Keep measured facts separate from inferred responsibilities;
the catalog is a derived revision-scoped work product, not another canonical specification system.

The report must identify the inspected revision, scope, measurement procedure, exclusions, and areas
not inspected. Link conclusions to source locations and distinguish test inspection from test execution.
Keep project-specific goals and lessons in the project; do not promote them into this shared skill.

For multi-turn work, checkpoint coverage, evidence, open questions, and the next inspection step in the
assessment artifact. Resume from that state. Completion means the agreed scope has a supported model
and explicit gaps, not that every file has been read. Hand off to `simplify` only when
requested; a missing runtime environment yields a partial claim, not fabricated verification.
Reuse this model in a proposal rather than producing a competing architecture document. After an
authorized change, consolidate verified responsibilities and constraints into the current model;
keep superseded decisions accessible through Git or the existing history instead of routine context.
