# C#/.NET evidence flavor

Read project files, SDK pinning, and central packages to identify scope and available tooling.
Defer runtime registration and implementation inspection until collection has been attempted and its
result or blocker reported, as required by the assessment's analyzer-first rule.
Separate production, tests, benchmarks, samples, generated code, and vendored sources explicitly.
A test project under `src/` is still a test project. Preserve the same scope for before/after counts.

For a C# architecture assessment, the single-file app `../scripts/csharp-metrics.cs` and
[SQLite catalog](catalog.md) are the first evidence-gathering attempt, not optional follow-up measurements.
This requirement belongs to `architecture-assessment`; a bounded `simplify` task using this reference
does not automatically require a whole-system assessment. The collector requires
.NET SDK 10.0.300 or later and references that SDK's bundled Roslyn assemblies, without loading a solution.
Check `dotnet --list-sdks` and the SDK selected in the collector's build directory. Build the collector
outside the target repository, then run its DLL against a clean target worktree:

```sh
dotnet build <skill>/scripts/csharp-metrics.cs -o <working-output>/collector
dotnet <working-output>/collector/csharp-metrics.dll <target-worktree> > <working-output>/csharp.json
```

Collect the [file baseline](metrics.md) at that worktree's `HEAD`, then build and query the catalog
before selecting source to inspect. Surface missing SDKs or failed collection before falling back to
bounded manual evidence; never imply that collection succeeded. This collector does not require restoring or building the target
solution; do not execute its build hooks just to obtain syntax evidence.

It reports compiler version, collector binary hash, revision, file hashes, syntax branch counts,
constructor arity, defaulted parameters, type declarations, and lexical name occurrences.
Type-level branch/method/constructor counts exclude nested type bodies; physical line spans include them.
These are syntax observations, not cyclomatic
complexity, semantic dependencies, live public API size, or proof that a type can be removed. Conditional
compilation uses default symbols; inspect reported directives and parse errors before drawing conclusions.
Generated files and tests remain visible in the raw data for explicit classification. Source and hashes
come from committed Git blobs, so checkout line-ending conversion does not invalidate the snapshot.
Only lowercase `.cs` paths are analyzed; differently cased extensions remain in the file baseline.

For queryable profiles and agent-written purpose annotations, use [the catalog procedure](catalog.md).
Declaration IDs identify file locations, not semantic symbols: partial declarations stay separate.
Name occurrences can refer to unrelated same-named types or variables. Aliases, implicit construction,
reflection, framework dispatch, external consumers, and other languages make use counts incomplete.
Neither a name match nor a zero match establishes a dependency or dead code. Base-type text is unbound.
When a decision requires exact references, use a project-aware semantic collector for the relevant
build configuration; do not turn a name join into a purported dependency graph.

For deeper analysis, prefer installed analyzers, compiler symbol tools, coverage reports, and API
compatibility tooling. Record versions, commands, configurations, and errors. Do not install a large
analysis stack or execute target build hooks merely to obtain an inventory when source inspection is enough.

Trace these relationships explicitly:

- Project references and their conditions; imported MSBuild properties can change the effective graph.
- Dependency injection registrations, service lifetimes, keyed services, factories, and plugin loading.
- Actor messages, child creation, subscriptions, state transitions, restarts, and termination signals.
- Async continuations, cancellation ownership, shared mutable state, and resource disposal.
- Serialization, reflection, source generation, and consumers outside the repository.

An unused-reference search is insufficient to declare reflected, serialized, public, or actor-dispatched
code dead. Optional parameters can represent valid states; many parameters can signal several owned
responsibilities, but adding a dependency bag merely hides the measurement. Partial types and generated
members can invalidate per-file size interpretations. Inspect representative callers before reporting debt.

If coverage is available, use it to locate missing proof alongside complexity. Record its revision and
configuration; absent or stale coverage is unknown, not zero coverage. Do not treat high coverage as
proof of compatibility, authority, cancellation, or recovery behavior.
