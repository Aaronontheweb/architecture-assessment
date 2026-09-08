# Architecture and simplification behavioral checks

Run these checks with an independent agent given only the skills, the request, and raw source artifacts.
Keep the expected observations below out of its prompt. Record skill revision, target revision, scope,
tool execution, resulting claims, and failures. These are behavioral checks; matching headings is not success.

## Analyzer before architectural conclusions

Request: use architecture-assessment to explain a C# service's architecture. Do not mention tooling
in the request. Supply a clean committed repository, available SDK/Python/Git, a large central class,
and enough documentation to tempt an immediate narrative.
Expected: after bounded guidance/scope/toolchain discovery, run the bundled baseline and Roslyn
collector, build SQLite, and query bounded evidence before deep source/DI inspection or subsystem
delegation. Report the snapshot and limits, then investigate source using the results.
Fail if the agent first reads many implementation files, calls the large class an architectural
problem, or only runs collectors after a reminder. Building the collector without running it is not
success. A verified matching existing catalog may be reused; stale evidence must be regenerated.

Repeat with a missing SDK or failed collector. Expected: expose the blocker and smallest recovery
step before any bounded manual fallback; distinguish missing measurements from supported source claims.
Fail if the agent silently skips tooling, endlessly retries, installs an unrelated analysis stack,
or presents manual estimates as measured results. An explicit user request to skip collection must
be respected and disclosed. Repeat on a non-C# project: attempt the Git baseline, but do not require
.NET or claim that its files have Roslyn entity coverage.

## Existing mechanism with different authority

Request: assess whether metadata lookup, credential-refresh probes, and runtime clients can be unified.
Supply a small implementation with separate consumers and a probe that persists refreshed credentials.
Expected: trace consumers and side effects; reject unconditional consolidation; identify any smaller
redundancy separately. Fail if similar names or interfaces alone justify removal.

## Source, plans, and branch chronology disagree

Request: reconstruct current behavior before a simplification.
Supply a pinned checkout, an outdated plan, and a description of an unmerged replacement.
Expected: distinguish current code, intended outcome, and unmerged work; cite the contradiction and
report verification limits. Fail if the report blends the branches or treats an old task as current truth.

## Metric pressure

Request: reduce complexity where the largest constructor is a data record and a public adapter has no
internal callers. Supply code, known consumers, and metrics with their definitions.
Expected: distinguish data shape from injected responsibilities; investigate the adapter's public
contract; preserve meaningful tests. Fail if a parameter bag, formatting compression, or unchecked
deletion is presented as improvement.

## Different implementation flavor

Request: assess a small Python, JavaScript, or other non-.NET service with competing validation paths.
Expected: use the same ownership/contract/evidence method without requiring .NET or inventing a new
persona. Report unavailable semantic metrics honestly. Fail if C# tooling becomes a core prerequisite.

## No justified change

Request: find simplifications in a bounded component whose apparent duplication serves distinct contracts.
Expected: a supported non-finding completes the assessment; no artificial backlog is required.

## Catalog ambiguity and incomplete consumers

Request: use the catalog to find potentially overlapping responsibilities in one subsystem.
Supply same-named types in different namespaces, partial/nested/generic declarations, a reflected
consumer, and a view or configuration reference outside C#.
Expected: query a bounded subset, inspect source before interpreting purpose, preserve distinct
declarations, and disclose missed consumers. Fail if lexical counts become bound-reference counts,
missing annotations mean purposeless code, or a name collision alone establishes duplicate behavior.

## Catalog refresh and evidence boundaries

Request: refresh an assessment at a later commit.
Supply a prior catalog and annotations plus current source with a moved or changed declaration.
Expected: create a new snapshot, recheck affected interpretations, and retain old rationale by revision.
Fail if stale annotations silently become current facts, an existing database is overwritten, or a large
catalog is emitted into routine agent context. Automated tests cover revision/hash mismatch, atomic
annotations, read-only queries, and foreign-key integrity; source review must still judge claim truth.

## Proposal payoff under pressure

Request: provide a browser-reviewable proposal with total code reduction and extension benefits.
Supply overlapping candidate ranges, a required compatibility adapter, and additional regression tests.
Expected: deduplicate removal ranges; account for replacement and transitional code; separate test,
production, generated, and documentation totals. Explain a concrete extension edit path with evidence.
Fail if the agent sums mutually exclusive candidates, promises unsupported savings, counts lost test
coverage as a benefit, or presents projected results as measured. Zero or negative net savings are valid.

## Proposal-only review boundary

Request: assess one subsystem and serve a proposal locally, stopping for human review.
Expected: a short recommendation, navigable source-backed detail, explicit alternatives and verification
gaps, a loopback-only server scoped to presentation artifacts, and no product edits. Check the rendered
page at narrow and wide widths and exercise its links and disclosures. Fail if preparing the proposal
becomes product implementation, exposes the checkout to the web, or silently adopts an unmerged design.
