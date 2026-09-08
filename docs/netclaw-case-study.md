# Netclaw case study: from source inventory to useful questions

Suppose you want to understand where Netclaw decides whether a shell command may run.
Two obvious starting points are `ShellTool`, which executes commands, and `ToolAccessPolicy`,
which makes tool-access decisions. The catalog gives you a small, queryable starting point.
It does not tell you whether those responsibilities are correctly divided.

This is a worked example using [Netclaw's public source at commit
`99cee4d2648379c245e07314adf30ed84dd0a47f`](https://github.com/netclaw-dev/netclaw/tree/99cee4d2648379c245e07314adf30ed84dd0a47f).
It is a historical snapshot, not an assessment of today's development branch or later refactoring results.
The selected measurements were reproduced on September 8, 2026 with Architecture Assessment v0.1.1,
.NET SDK 10.0.400, and Roslyn 5.9.0.0. No Netclaw application build or runtime access was needed.

## 1. Collect a snapshot you can reproduce

From an Architecture Assessment checkout at `v0.1.1`, run the following Bash commands.
Use the [README prerequisites](../README.md#run-the-tools-without-an-agent).
The temporary directory holds the target checkout, collector build, JSON, and database outside your project.

```bash
case_output=$(mktemp -d)
git clone --filter=blob:none --no-checkout https://github.com/netclaw-dev/netclaw.git "$case_output/netclaw"
git -C "$case_output/netclaw" checkout --detach 99cee4d2648379c245e07314adf30ed84dd0a47f

dotnet build skills/architecture-assessment/scripts/csharp-metrics.cs -o "$case_output/collector"
python3 skills/architecture-assessment/scripts/repository_baseline.py "$case_output/netclaw" \
  --revision 99cee4d2648379c245e07314adf30ed84dd0a47f > "$case_output/baseline.json"
dotnet "$case_output/collector/csharp-metrics.dll" "$case_output/netclaw" > "$case_output/csharp.json"
python3 skills/architecture-assessment/scripts/architecture_catalog.py build "$case_output/catalog.sqlite" \
  --repository netclaw --baseline "$case_output/baseline.json" --analysis "$case_output/csharp.json"
```

Check each command succeeds before continuing. The importer rejects an existing database; use a new
output directory for another run. This collection contains **1,561 C# files, 3,491 declarations, and
63,529 lexical name occurrences**. It includes tests, benchmarks, and generated sources—not just
production code. The run reported zero parse errors and five files with preprocessor directives.
Default parser symbols still limit coverage; zero parse errors do not establish a valid application build.

## 2. Ask a small question instead of reading thousands of types

```bash
python3 skills/architecture-assessment/scripts/architecture_catalog.py query "$case_output/catalog.sqlite" \
  "SELECT name,file_path,line,method_declarations,branch_nodes,
          max_constructor_parameters,lexical_name_occurrences,
          lexical_owner_count,same_name_declarations,purpose
   FROM profiles WHERE name IN ('ShellTool','ToolAccessPolicy') ORDER BY name"
```

The selected output is:

| Observation | ShellTool | ToolAccessPolicy |
|---|---:|---:|
| Declaration start line | 22 | 18 |
| Method declarations | 16 | 43 |
| Branch nodes | 49 | 85 |
| Maximum constructor parameters | 3 | 9 |
| Lexical name occurrences | 137 | 153 |
| Distinct enclosing declarations among those matches | 24 | 50 |
| Declarations with the same name and generic arity | 1 | 1 |
| Purpose in a freshly imported catalog | `null` | `null` |

The rows point to [ShellTool.cs](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L22)
and [ToolAccessPolicy.cs](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L18).
The declaration start includes attributes; it need not be the line containing the `class` keyword.

The useful interpretation is: **inspect the policy's decisions and the executor's checks together**.
The higher branch count makes the policy an investigation lead. It does not make it a bad class.
The constructor count is a reason to inspect its dependencies, not a recommendation to hide them in a parameter bag.
The counts include neither a complete public API nor a compiler-bound dependency graph.

## 3. Read code to explain what the measurements cannot

At this revision, [ToolAccessPolicy filters exposed tools](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L100)
and [returns shell preflight decisions](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L181).
[ShellTool prepares and starts the process](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L93).
It also performs command and path checks. The policy performs related checks
[during authorization](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L280).

That gives a concrete next question: **are these intentional checks at different boundaries, or
independent decisions that could drift?** Answering requires callers, execution modes, and tests.
Removing a repeated security check just because it appears twice would be an unsafe conclusion.
This example establishes a place to investigate, not a security review or permission to remove code.

A reviewer could record a purpose such as “Controls which tools are exposed and evaluates invocation
authority” for `ToolAccessPolicy`. That sentence is a source-based interpretation written by a human
or agent, not an output that Roslyn generates. The raw import leaves `purpose` empty. Use an
[evidence-linked annotation](sqlite.md#annotating-an-entity) to store the explanation, confidence,
author, and source locations separately from measurements. The catalog can then search those explanations.

## 4. See why a name match is not a reference count

This query finds a real candidate location:

```sql
SELECT file_path,line,name,context FROM name_occurrences
WHERE name='ShellTool'
  AND file_path='benchmarks/Netclaw.Benchmarks/ShellDrainBenchmarks.cs'
ORDER BY line LIMIT 1;
```

It returns `ShellTool`, line 49, with context `SimpleMemberAccessExpression`.
The [source line](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/benchmarks/Netclaw.Benchmarks/ShellDrainBenchmarks.cs#L49)
calls `ShellTool.TruncateOutput`. This is a benchmark using an output helper—not a new runtime
instance of `ShellTool`, and not necessarily a consumer of its authorization behavior.

Now look at a more misleading name:

```sql
SELECT qualified_name,file_path,line,lexical_name_occurrences,same_name_declarations
FROM profiles WHERE name='Params' AND arity=0 ORDER BY qualified_name LIMIT 3;
```

| Qualified declaration | Name occurrences | Same-name declarations |
|---|---:|---:|
| `Netclaw.Actors.Jobs.CheckBackgroundJobTool.Params` | 80 | 32 |
| `Netclaw.Actors.Memory.SqliteFindMemoriesTool.Params` | 80 | 32 |
| `Netclaw.Actors.Memory.SqliteGetMemoriesTool.Params` | 80 | 32 |

There are **32 distinct declarations named `Params`** with generic arity zero. Each receives the
same pooled count of **80** name matches. The SQL view joins names and arity, not compiler symbols.
These are not 80 verified references to each type.

For example, [CheckBackgroundJobTool.Params](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Jobs/CheckBackgroundJobTool.cs#L25)
contains a job ID and cancellation choice.
[SqliteFindMemoriesTool.Params](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Memory/SqliteFindMemoriesTool.cs#L29)
contains a memory-search query and search options. Shared spelling does not make these duplicate responsibilities.

Run these SQL examples with the same `architecture_catalog.py query` command used above, or any SQLite client.

## What this case study establishes

The tool can reduce a large source inventory to a few reproducible, source-linked questions.
It preserves the difference between a measured observation and a reviewer's explanation.
It also makes an important limitation visible: lexical names are not semantic identities.

This is not a before/after refactoring study. It measures no code savings, approval reduction, agent
accuracy improvement, or engineering time saved. Netclaw's application tests and runtime behavior were
not exercised. No raw database, private discussion, or operational data accompanies this example.

Continue with [how the analyzer works](how-it-works.md), [SQLite queries and annotations](sqlite.md),
or the smaller [synthetic example](example.md) that is exercised in CI.
