# Netclaw case study: finding scattered shell-authorization decisions

We used the catalog while investigating a concrete problem: making Netclaw's shell approvals and
corrections easier to improve without adding more scattered special cases. The useful finding was not
that a class was large. **Several parts of the system independently decided how to correct a tool call,
and background process startup did not use the same checks as foreground startup.**

Following declarations into their callers exposed three important examples: native-tool advice and
temporary-directory advice took different routes; Auto approval skipped one route but not the other;
and shared submission authorization did not mean shared checked process startup. The resulting plan
targeted those decision boundaries, while preserving differences that mattered, such as background-job
lifetimes and parent-versus-child recovery.

The analyzer supplied a navigable inventory. Source inspection supplied these findings. Human decisions
and later tests shaped the proposed behavior. The queries below reproduce that evidence trail for a
reader; they are an explanatory reconstruction, not a verbatim transcript of the original investigation.

This is a worked example using [Netclaw's public source at commit
`99cee4d2648379c245e07314adf30ed84dd0a47f`](https://github.com/netclaw-dev/netclaw/tree/99cee4d2648379c245e07314adf30ed84dd0a47f).
It is a historical snapshot, not an assessment of today's development branch or later refactoring results.
The selected measurements were reproduced on September 8, 2026 with Architecture Assessment v0.1.1,
.NET SDK 10.0.400, and Roslyn 5.9.0.0. No Netclaw application build or runtime access was needed.

## 1. Try it with an agent or run it manually

Both routes lead to the same evidence. Choose one; you do not need to run the commands yourself when
an installed skill can do it. The [installation guide](../README.md#use-the-skills) covers supported clients.

<details open>
<summary>With an agent: assess the old code and propose justified simplifications</summary>

Give this prompt to an agent with the package's three skills installed:

```text
Use architecture-assessment on netclaw-dev/netclaw at commit
99cee4d2648379c245e07314adf30ed84dd0a47f in a clean separate checkout.
Investigate how shell calls get approved, corrected, and launched across
the main agent, subagents, and foreground/background execution.

Try the bundled analyzer first. Use its catalog to select declarations and
candidate callers, then inspect source and tests to verify the relationships.
Show concrete requests where behavior differs, and explain which differences
are necessary versus candidates for consolidation. Cite the pinned source.

Then use simplify to propose the smallest justified changes, applying
architectural-principles to the design trade-offs. Explain what
existing code to reuse, what could disappear, and what tests would establish
the change is safe. Separate measured facts, hypotheses, and desired behavior.
Do not modify Netclaw or launch its processes. Keep generated evidence local.
```

For your own project, replace the repository, revision, and area of concern. You can select the skills
through your client's skill picker instead of naming them in prose. Ask for a browser-readable proposal
if desired. An assessment or proposal does not authorize implementation.

</details>

<details>
<summary>Run it manually: collect Git/Roslyn evidence and build SQLite</summary>

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
output directory for another run. Keep this shell open to reuse `case_output` in the queries below.

</details>

This collection contains **1,561 C# files, 3,491 declarations, and
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

## 3. Follow the data to the decision owners

At this revision, [ToolAccessPolicy filters exposed tools](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L100)
and [returns shell preflight decisions](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L181).
[ShellTool prepares and starts the process](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L93).
It also performs command and path checks. The policy performs related checks
[during authorization](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L280).

The next move was to trace where those decisions became a response to the model. The declaration
inventory gives file locations; lexical occurrences give candidate consumers. After learning the
exception names from the dispatcher, this query finds where the two response routes meet their callers:

```sql
SELECT n.name, e.name AS enclosing_type, n.file_path, n.line
FROM name_occurrences n LEFT JOIN entities e ON e.id = n.owner_id
WHERE n.name IN ('ToolAgentCorrectionRequiredException','ToolApprovalRequiredException')
  AND n.file_path IN (
    'src/Netclaw.Actors/Sessions/Pipelines/SessionToolExecutionPipeline.cs',
    'src/Netclaw.Actors/SubAgents/SubAgentActor.cs')
  AND n.context = 'CatchDeclaration'
ORDER BY n.name, n.file_path, n.line;
```

| Candidate handler | Main session pipeline | Subagent |
|---|---:|---:|
| `ToolAgentCorrectionRequiredException` | line 744 | line 1477 |
| `ToolApprovalRequiredException` | line 764 | line 1492 |

These rows are syntax locations, not a proven call graph. Reading the handlers confirms the same
distinction in both: native-tool advice uses a correction exception; temporary-directory and project
advice are selected inside an approval-exception handler. That is the kind of relationship a size
ranking alone would not reveal.

### Finding: two kinds of correction took different routes

If a model put `file_read --path notes.txt` inside `shell_execute`, the
[dispatcher](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/DispatchingToolExecutor.cs#L414)
could detect the exposed native tool and return “use that tool directly” before calling the existing
`ShellPolicyCoordinator`. Meanwhile, [temporary-directory advice](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L611)
was attached to an approval context. The
[main session](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Sessions/Pipelines/SessionToolExecutionPipeline.cs#L744)
and [subagent](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/SubAgents/SubAgentActor.cs#L1477)
each decided whether that context meant a correction rather than an approval request, including retry
and capability conditions. Project-directory advice followed that same caller-side route.

The result was more than duplicate formatting. To change when a correction should be offered, an
implementer had to understand policy, exception transport, and both caller handlers. The existing
terminal result also carried only [one correction](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAuthorizationDecision.cs#L189).
The proposal was to collect compatible correction facts in the existing coordinator, return one
decision, and let callers deliver it without independently selecting policy.

“Compatible” matters. Later work demonstrated an interactive Personal request that mistakenly used
`file_write --path <absolute temporary target>` through the shell. Both “use the native tool” and
“use managed temporary storage” applied to the intended write. The
[policy test](https://github.com/netclaw-dev/netclaw/blob/18e108101b9ab4c90bfc68c836a3a3fd32e2a8c6/src/Netclaw.Actors.Tests/Tools/DispatchingToolExecutorTests.cs#L3956)
explicitly supplies the intended structured write and checks both facts. It does not infer arbitrary
executable argument grammar. A
[controlled response test](https://github.com/netclaw-dev/netclaw/blob/18e108101b9ab4c90bfc68c836a3a3fd32e2a8c6/src/Netclaw.Actors.Tests/Sessions/SessionToolExecutionPipelineTests.cs#L367)
then checks that both facts reach one model response without prompting. These tests are at a later
revision, not part of the measured baseline; this documentation pass inspected, but did not execute, them.
They establish a concrete test design, not proof that every pair of suggestions is compatible.
Relocating an existing file read, for example, could change what the user asked to read.

### Finding: Auto approval exposed the ordering difference

In the old [approval gate](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ToolAccessPolicy.cs#L555),
Auto returns before temporary advice is evaluated. Native-tool detection happens later in the
dispatcher, so it can still stop an Auto request. “Auto skips corrections” was therefore not a
consistent description of the system: the answer depended on which correction route you followed.

The accepted design made that ordering explicit: hard denials still stop the request; applicable
corrections return together; with neither, Auto executes without an approval prompt. This includes
an intentional change for temporary advice, not just rearrangement of equivalent code. Unresolved
expressions must not silently turn Auto into manual approval. Static analysis exposed where to ask
the question; the human supplied the intended semantics.

### Finding: background authorization was not the same as checked startup

The inventory also led to `BackgroundJobExecutionActor`. We then searched the selected execution
files for actual starts. `Process` is a framework type, so this syntax catalog is not a reliable
index of its calls; use direct source search here:

```bash
rg -n '= Process\.Start\(' \
  "$case_output/netclaw/src/Netclaw.Actors/Tools/ShellTool.cs" \
  "$case_output/netclaw/src/Netclaw.Actors/Jobs/BackgroundJobExecutionActor.cs"
```

This finds three starts: [foreground at ShellTool:142](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L142),
[streaming at ShellTool:354](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L354),
and [background at BackgroundJobExecutionActor:124](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Jobs/BackgroundJobExecutionActor.cs#L124).
Counting them is only the start. Reading the callers shows that
[background submission already requests authorization](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Sessions/Pipelines/SessionToolExecutionPipeline.cs#L720).
It would be wrong to report “background jobs have no authorization.” The actual gap is that the job
actor starts the process outside `ShellTool`'s checked startup, so shared submission policy does not
establish identical launch checks or reevaluation when relevant facts change before start.

The plan therefore called for one checked start implementation across all three modes. But the
[foreground path links cancellation to its caller](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellTool.cs#L136),
while the background actor owns a longer-lived job. Calling the whole foreground method and forgetting
its task would not be sound consolidation. Share the checks and start; preserve timeout, output,
cancellation, and disposal ownership for each mode.

### Counterexample: not every repeated mechanism should be merged

The parent session has durable recovery responsibilities; a child uses a live approval bridge. The
plan retained those distinct lifetimes rather than replacing both with one state machine. It also
rejected “just run both evaluators” as a safe comparison strategy: the
[dispatcher clears applied-decision state](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/DispatchingToolExecutor.cs#L405),
and the [coordinator applies approval metadata](https://github.com/netclaw-dev/netclaw/blob/99cee4d2648379c245e07314adf30ed84dd0a47f/src/Netclaw.Actors/Tools/ShellPolicyCoordinator.cs#L356).
Those calls are not pure observations. Any comparison needs captured inputs and isolation from prompts,
processes, grants, and retry state. This constraint came from source inspection, not the metric values.

A reviewer could record a purpose such as “Controls which tools are exposed and evaluates invocation
authority” for `ToolAccessPolicy`. That sentence is a source-based interpretation written by a human
or agent, not an output that Roslyn generates. The raw import leaves `purpose` empty. Use an
[evidence-linked annotation](sqlite.md#annotating-an-entity) to store the explanation, confidence,
author, and source locations separately from measurements. The catalog can then search those explanations.

## 4. Turn the findings into a bounded change

The investigation produced a concrete direction, not “rewrite the security system”:

- Evolve the existing `ShellPolicyCoordinator`, detectors, and terminal result instead of adding a
  generic pipeline framework. Return every applicable compatible correction together; advice grants no authority.
- Move correction selection out of parent and child handlers while retaining their distinct delivery,
  recovery, and retry duties. Reevaluate corrected calls against current authority.
- Share checked startup across foreground, streaming, and background execution without sharing their
  entire process lifetimes. Preserve exact invocation facts and avoid duplicate prompts or starts.
- Characterize current behavior, test a real collection through a caller, move complete journeys,
  then delete replaced branches and update the current architecture reference.

The maintenance test was deliberately concrete: **if the host supplies a different managed temporary
directory, how many independent decision owners must change to suggest it?** Repeat the same exercise
before and after, distinguishing policy changes from mechanical payload transport. Fewer caller-side
policy branches would support the claim that later approval-fatigue improvements became easier.
It is a verification criterion, not a result established by this article.

Likewise, file sizes were not a deletion budget. Replacement code, adapters, tests, and distinct
lifetimes all have costs. The planning work did not establish a defensible net-code-reduction estimate.
Approval volume and agent recovery need controlled behavioral evaluation; syntax counts cannot measure them.

## 5. See why a name match is not a reference count

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

The practical result was a map of scattered correction decisions, a concrete Auto-ordering difference,
and a distinction between submission authorization and checked process startup. That map supported a
specific consolidation plan and identified behavior that must not be consolidated away. The catalog
helped navigate the evidence; it did not independently discover bugs or prove the design correct.

This is not a before/after refactoring study. It measures no code savings, approval reduction, agent
accuracy improvement, or engineering time saved. Netclaw's application tests and runtime behavior were
not exercised for this documentation update. Later test source is labeled separately from the baseline.
This is not a status report on the eventual rollout or completion of that work. No raw database,
private transcript, or operational data accompanies this example.

Continue with [how the analyzer works](how-it-works.md), [SQLite queries and annotations](sqlite.md),
or the smaller [synthetic example](example.md) that is exercised in CI.
