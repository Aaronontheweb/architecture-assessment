# Architecture Assessment

Understand what a codebase does, why its parts exist, and where it could become simpler—before asking
an agent to change it.

> This is an early extract from a larger library of SDLC skills I'm still working on privately.
> I'm making these two skills and their analysis tools available because people have asked about them.
> You don't need the rest of that library to use this. Expect iteration, not a finished analysis platform.

## Start here

- [Use the skills](#use-the-skills)
- [Sample prompts](#sample-prompts)
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

The skills are language-neutral. For a **C#** architecture assessment, always try the repository
baseline, Roslyn declaration collection, and SQLite catalog/query steps before deep source reading.
If a prerequisite or analyzer run fails, disclose it and use a bounded manual fallback rather than
claiming analyzer-backed evidence. Non-C# assessments remain language-neutral and do not require the
.NET collector; a bounded `simplify` request may also be scoped without a full assessment when explicitly requested.
The Roslyn collector is **syntax-based, not symbol-bound**: matching names are leads to inspect, not exact references,
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

### GitHub Copilot

For **Copilot CLI**, register this marketplace and install the plugin:

```bash
copilot plugin marketplace add Aaronontheweb/architecture-assessment
copilot plugin install architecture-assessment@architecture-assessment
copilot skill list
```

Start a new session in your target repository, then ask for a concrete outcome:

```text
Use /architecture-assessment to explain our notification pipeline, including failure and retry. Do not change code.
Use /simplify to propose consolidations in that pipeline while preserving delivery guarantees. Stop at a proposal.
```

The CLI uses the existing `.claude-plugin` manifests; there is no separate Copilot copy of the skills.
Prefer marketplace installation: recent CLI versions warn that direct repository installs are being
deprecated. Use `copilot plugin update architecture-assessment` to update the installed plugin.
See [GitHub's plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference).

For **repository-local Copilot skills**, including use in supported IDE agent modes or the cloud agent,
copy both complete directories from this repository's `skills/` into your target's `.github/skills/`:

```text
.github/skills/
├── architecture-assessment/  # Include SKILL.md, references/, and scripts/.
└── simplify/                 # Include SKILL.md, references/, and assets/.
```

Preserve existing skills; do not overwrite another installation. Copying just the Markdown entrypoints
loses the collectors, shared references, and proposal template. CLI installation is local to that CLI;
it does not install skills into your GitHub cloud-agent environment. Follow your client's discovery and
enablement instructions. See [GitHub's skill support documentation](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).

The install check exercises CLI discovery and resource integrity, not model behavior in every Copilot
client. Installing the package neither installs .NET/Python nor authorizes code changes or tool execution.
Existing project/personal skills with the same names can take precedence; inspect the reported source
with `copilot skill list` if the wrong version appears.

### Updating an installed copy

Updates depend on how the skills were installed:

- **Claude Code marketplace plugin:** refresh the marketplace if needed, then update the installed
  plugin. For the commands used above:

  ```text
  claude plugin marketplace update architecture-assessment
  claude plugin update architecture-assessment@architecture-assessment
  ```

  Use the same `--scope` as the original installation when it was not at user scope. Run
  `/reload-plugins` in an existing session. Marketplace installs may also be configured for automatic
  updates. See [Claude Code's plugin
  documentation](https://code.claude.com/docs/en/plugins-reference).

- **GitHub Copilot CLI marketplace plugin:** update the installed plugin with:

  ```bash
  copilot plugin update architecture-assessment
  ```

  Use `--all` only when you intend to update every installed plugin. If the marketplace catalog is
  stale, refresh it first with `copilot plugin marketplace update architecture-assessment`. If a
  running session still shows the old components, start a new session. See [GitHub's Copilot CLI
  plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference).

- **Copied repo-local Copilot skills:** there is no plugin update command for copied directories.
  Reconcile both complete `skills/architecture-assessment/` and `skills/simplify/` directories from
  the newer repository revision into the target repository's `.github/skills/`: remove obsolete files
  from those bundled directories when a release deletes or renames them, while preserving unrelated
  local skills. Then run `/skills reload` or start a new Copilot CLI session. See [GitHub's
  agent skills documentation](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills).

- **Copied Codex skill directories:** there is no update command for an arbitrary copied directory.
  Reconcile both complete skill directories in the chosen `.agents/skills/` location: remove obsolete
  files from those bundled directories when a release deletes or renames them, while preserving
  unrelated local skills. Codex detects local skill changes automatically; restart Codex if the new
  version does not appear. See [OpenAI's
  official Codex skills documentation](https://developers.openai.com/codex/skills/).

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

## Sample prompts

Start with the goal you want to accomplish. These examples use Codex's `$skill-name` notation;
in Claude Code, replace it with `/architecture-assessment:architecture-assessment` or
`/architecture-assessment:simplify`. In Copilot, use `Use /architecture-assessment` or `Use /simplify`.
Adapt the named feature and constraints to your project.

### Understand an unfamiliar codebase

```text
$architecture-assessment I'm new to this repository. Give me a compact map of its
main components and what each owns. Trace one important user request from entry
point to stored state or output, including a failure path. Link your explanation
to concrete code and tests. Separate current behavior from outdated documentation
and things you couldn't verify. Start with an overview; don't inventory every
class or change the code.
```

Useful output: a navigable system map, a representative journey, source evidence, and explicit gaps.

### Find out why one feature is hard to change

```text
$architecture-assessment We need to add another notification provider. Investigate
how the existing providers are selected, configured, called, and retried. Show me
the concrete places a new provider would need changes, which mechanisms can be
reused, and where responsibilities overlap. Preserve existing delivery guarantees.
If intended behavior is unclear, ask me about that specific trade-off. Produce an
assessment, not an implementation or a new provider framework.
```

Useful output: an evidence-backed extension path and obstacles, not an automatic redesign.

### Analyzer-first C# evidence workflow

```text
$architecture-assessment Use the bundled Roslyn and SQLite tools on a clean
snapshot of this C# repository. Keep generated output ignored and local. Use the
catalog to identify a small set of types worth inspecting for concentrated
branching, large constructors, or potentially overlapping responsibilities.
Read those types and representative consumers before explaining their purpose.
Show the queries, source evidence, and limits behind your conclusions. Name
matches are not symbol references; don't claim zero matches prove dead code.
```

Useful output: a reproducible catalog plus a short source-reviewed shortlist—not a database dump or
a claim that the entire architecture has been understood. If the analyzer cannot run, record why and
keep any manual assessment bounded. The collector does not require a target build.

### Propose less code without losing behavior

```text
$simplify Assess the request-validation path for duplicated rules and competing
owners. Reconstruct enough of that path to understand it first. Propose the
smallest useful consolidations, and include reasons to keep apparently similar
mechanisms separate. Estimate removable production code, replacement code, and
net change only where source evidence supports it; account for test additions
separately. Preserve public behavior and explain which existing tests should stay
unchanged and which new checks are needed. Don't implement anything yet.
```

Useful output: prioritized candidates with concrete before/after responsibilities, honest estimates,
counterevidence, and verification. "No justified simplification" is a valid answer.

### Get a proposal you can actually review

```text
$simplify Investigate whether our background job runners can share more code
without changing cancellation, output handling, or ownership. Present the result
as a self-contained HTML proposal using the bundled template where helpful.
Show current code and proposed changes before introducing architecture jargon.
Make any decisions you need from me obvious; include alternatives, risks, and
verification gaps. Check narrow-screen and printed readability if browser tools
are available, or report that presentation check as unrun. Save it locally and
stop for review. Don't expose a server, publish findings, or modify product code.
```

Useful output: a human-readable decision artifact, not implementation approval. Any estimate remains
a projection until an authorized change has been implemented and verified.

### Assess a non-C# or mixed-language system

```text
$architecture-assessment Trace how a user changes a preference in our web UI and
how it reaches the backend and storage. Follow validation and error handling on
both sides. Use existing repository tools and source inspection; don't force the
C# collector onto JavaScript, HTML, or CSS. Explain the cross-layer contract and
which relationships you verified versus inferred. Do not change the application.
```

Useful output: one coherent cross-layer explanation with honest tooling coverage. The skills work
across languages; the bundled declaration collector currently supports C# only.

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
example, checks the HTML template in Chromium, and tests Copilot CLI installation/discovery with an
isolated configuration. These checks do not prove an agent's architectural
judgment or demonstrate measured time savings. [Behavioral scenarios](evals/assessment-cases.md) describe
additional evaluations; they are not automated model evaluations in CI.

[Origin and maintenance](PROVENANCE.md) · [MIT license](LICENSE)
