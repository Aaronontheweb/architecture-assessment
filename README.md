# Architecture Assessment

Understand what a codebase does, why its parts exist, and where it could become simpler—before asking
an agent to change it.

> This is an early extract from a larger library of SDLC skills I'm still working on privately.
> I'm making these two skills and their analysis tools available because people have asked about them.
> You don't need the rest of that library to use this. Expect iteration, not a finished analysis platform.

## Start here

- [Use the skills](#use-the-skills)
- [Run the tools without an agent](#run-the-tools-without-an-agent)
- [How the analyzer works](docs/how-it-works.md)
- [SQLite tables and query recipes](docs/sqlite.md)
- [Worked example and actual output](docs/example.md)
- [Limits and verification](#limits-and-verification)

## What's included

| Component | What it does |
|---|---|
| [architecture-assessment](skills/architecture-assessment/SKILL.md) | Reconstructs responsibilities, relationships, contracts, and important execution journeys from evidence. |
| [simplify](skills/simplify/SKILL.md) | Investigates debt and overlapping mechanisms; proposes justified simplifications with counterevidence, costs, and verification. |
| Git file collector | Measures committed files, sizes, and physical line counts reproducibly. |
| Roslyn C# collector | Inventories declarations, syntax branches, constructor parameters, and possible name usages. |
| SQLite catalog | Makes that evidence queryable; stores agent-written purpose explanations separately from measurements. |
| Static proposal template | Helps present findings as a readable, self-contained HTML page when requested. |

The skills are language-neutral. The optional declaration collector currently supports **C# only**.
It is **syntax-based, not symbol-bound**: matching names are leads to inspect, not exact references,
runtime instance counts, or proof of dead code. Neither skill authorizes automatic code changes.

## Use the skills

### Claude Code

Install both skills and their supporting files as a plugin:

```text
/plugin marketplace add Aaronontheweb/architecture-assessment
/plugin install architecture-assessment@architecture-assessment
```

Then, in your target repository:

```text
/architecture-assessment:architecture-assessment Assess the payment retry path, including failures. Do not change code.
/architecture-assessment:simplify Use that assessment to propose simplifications while preserving retry behavior.
```

These are optional routes, not a mandatory whole-repository audit. You can request `simplify` directly
when the relevant architecture is already understood. See [Claude's plugin documentation](https://code.claude.com/docs/en/discover-plugins).

### Codex and other skill-capable agents

Copy **both complete skill directories**, keeping them adjacent, into your harness's skill directory.
For Codex, a repository-local `.agents/skills/` directory is one option; use a location appropriate
to your setup and do not overwrite existing skills. See [the official skills documentation](https://developers.openai.com/codex/skills/).
The `simplify` skill links to the assessment's shared evidence references, so copying only `SKILL.md`
loses useful behavior. A Codex plugin manifest is also included for plugin-capable integrations.

Example prompts after discovery:

```text
$architecture-assessment Explain this repository's job lifecycle, including cancellation. Record what you cannot verify.
$simplify Find justified simplifications in that lifecycle. Preserve distinct ownership and cancellation contracts.
```

If you already installed these skills through another package, choose one source for this invocation.
Optional references to `interview` and `plan` do not require those skills; the included guidance works
without them. No credentials or agent service are needed to run the local analysis tools.

## Run the tools without an agent

Prerequisites: Git, Python 3.10+ with SQLite FTS5 support, and .NET SDK 10.0.300 or newer in the 10.0
series for the single-file C# application. CI uses .NET 10 on Ubuntu. Other platform behavior has not
been comprehensively verified. The Python collector/catalog use only the standard library.

Clone this repository, then run from its root. Replace the target path with a **clean worktree** of
the repository you want to inspect. The example uses Bash; output is stored outside the target.

```bash
git clone https://github.com/Aaronontheweb/architecture-assessment.git
cd architecture-assessment
target_repo=/absolute/path/to/clean-target-worktree
analysis_output=$(mktemp -d)

dotnet build skills/architecture-assessment/scripts/csharp-metrics.cs -o "$analysis_output/collector"
python3 skills/architecture-assessment/scripts/repository_baseline.py "$target_repo" > "$analysis_output/baseline.json"
dotnet "$analysis_output/collector/csharp-metrics.dll" "$target_repo" > "$analysis_output/csharp.json"
python3 skills/architecture-assessment/scripts/architecture_catalog.py build "$analysis_output/catalog.sqlite" \
  --repository example --baseline "$analysis_output/baseline.json" --analysis "$analysis_output/csharp.json"
python3 skills/architecture-assessment/scripts/architecture_catalog.py query "$analysis_output/catalog.sqlite" \
  'SELECT qualified_name,file_path,line,branch_nodes FROM profiles ORDER BY branch_nodes DESC LIMIT 10'
```

Stop if any command fails. The importer rejects mismatched revisions and content rather than merging
inconsistent evidence. Choose a non-sensitive repository label. No target solution build is required:
Roslyn parses source without executing the target application's build hooks or product code.

Want to see output first? Run the [small, reproducible example](docs/example.md).

## Limits and verification

Use metrics to choose where to look—not to score architectural quality or justify deleting code.
The agent must inspect source, consumers, composition/dispatch wiring, and tests before making claims.
Public APIs, reflection, dependency injection, partial types, conditional compilation, and mixed-language
systems require particular care. See the [full explanation](docs/how-it-works.md).

Generated catalogs are private working evidence, not canonical architecture documents. Keep them ignored
and don't upload catalogs, internal source, or customer data in issues. The tools don't call a model
or upload source; the agent harness you choose has its own data-handling behavior.

CI validates packaging and links, exercises collector/import/annotation boundaries and the worked
example, and checks the HTML template in Chromium. These checks do not prove an agent's architectural
judgment or demonstrate measured time savings. [Behavioral scenarios](evals/assessment-cases.md) describe
additional evaluations; they are not automated model evaluations in CI.

[Origin and maintenance](PROVENANCE.md) · [MIT license](LICENSE)
