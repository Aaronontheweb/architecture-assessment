# SQLite structure and useful queries

The schema lives in [`architecture_catalog.py`](../skills/architecture-assessment/scripts/architecture_catalog.py).
SQLite foreign keys are enabled on tool connections. FTS5 must be available in Python's SQLite build.
The catalog schema version is currently **1**, stored in `snapshot.metadata_json`; C# input schema
version **2** is a separate contract. Both are early formats, not a promised stable external API.

## Tables and relationships

| Table/view | Key and relationship | Contents |
|---|---|---|
| `snapshot` | One row per database | `repository`, `commit_sha`, baseline/analysis SHA-256, metadata JSON |
| `files` | `path` primary key | Extension, hash, bytes, nullable physical/nonblank line counts |
| `entities` | `id` primary key; `file_path` → files; nullable `parent_id` → entities | Names, arity, kind, source span, modifiers, branch/method/constructor metrics |
| `declared_bases` | `entity_id` → entities | Unbound `target_text`, such as a written interface name |
| `name_occurrences` | `(file_path, offset)` key; nullable `owner_id` → entities | Candidate spelling, arity, line and syntax context |
| `interpretations` | `entity_id` primary key → entities | Current purpose, confidence, author, evidence JSON, timestamp |
| `purpose_search` | Explicitly maintained FTS5 index | Entity ID, qualified name, purpose |
| `profiles` | SQL view | Entity columns plus lexical counts, ambiguity, purpose and confidence |

`parent_id` represents declaration nesting. It is not inheritance, a project reference, or a runtime
dependency. `declared_bases` cannot be traversed as resolved edges. Namespaces are not separate entities.

Indexes support name/arity and containment/owner lookups. `profiles` computes correlated counts by
name/arity; it does not store a materialized dependency graph. `purpose_search` is maintained by
`annotate`, not by triggers. Direct SQL edits can violate these conventions; prefer the supplied CLI.

## Query recipes

Pass any of these SELECTs to `architecture_catalog.py query <database> '<SQL>'`.

```sql
-- Inspect provenance before treating a result as current.
SELECT repository,commit_sha,metadata_json FROM snapshot;

-- Find source to investigate, not automatic refactoring candidates.
SELECT qualified_name,file_path,line,branch_nodes,max_constructor_parameters
FROM profiles ORDER BY branch_nodes DESC LIMIT 20;

-- Expose pooled counts for ambiguous names.
SELECT qualified_name,lexical_name_occurrences,same_name_declarations
FROM profiles WHERE same_name_declarations > 1 ORDER BY name LIMIT 20;

-- Locate individual candidates; inspect the code to decide what they mean.
SELECT file_path,line,context FROM name_occurrences
WHERE name='RetryPolicy' AND arity=0 LIMIT 20;

-- Discover which files lack C# declaration coverage.
SELECT extension,count(*) AS files,sum(lines) AS physical_lines
FROM files GROUP BY extension;

-- Search explanations, including their supporting evidence.
SELECT p.name,p.purpose,i.confidence,i.evidence_json
FROM purpose_search p JOIN interpretations i ON i.entity_id=p.entity_id
WHERE purpose_search MATCH 'retry';

-- Unassessed is not unused or unneeded.
SELECT count(*) AS unassessed FROM profiles WHERE purpose IS NULL;
```

The command emits JSON with `rows` and `truncated`. `--limit` changes the default 100-row output cap;
SQL LIMIT and the CLI output cap are independent. Source coverage and interpretation coverage are
also different: count both rather than saying the agent has understood every profiled declaration.

## Annotating an entity

First query its actual ID and snapshot. Then write a JSON batch:

```json
{
  "repository": "example",
  "commit": "REPLACE_WITH_SNAPSHOT_COMMIT",
  "interpretations": [{
    "entity_id": "REPLACE_WITH_QUERIED_ENTITY_ID",
    "purpose": "Decides whether another retry is allowed; it does not schedule or execute one.",
    "confidence": "medium",
    "author": "source-reviewer",
    "evidence": [{"path": "Policy.cs", "line": 3}]
  }]
}
```

```sh
python3 skills/architecture-assessment/scripts/architecture_catalog.py annotate /path/to/catalog.sqlite /path/to/annotations.json
```

The placeholders are intentional: never reuse IDs or commits from another assessment. The executable
[example](example.md) obtains real values and exercises an annotation transaction.

No automatic migration or annotation carry-forward is provided. Keep old snapshots for investigations
that need them; maintain accepted architectural conclusions in the project's normal documentation.
