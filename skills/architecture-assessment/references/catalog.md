# Queryable architecture evidence

After successful collection, build and query this local SQLite catalog before deep source inspection
in a C# architecture assessment. Other workflows can use it when inventories need filtering or separately recorded
interpretations. A compact human-facing architecture remains the output; do not feed the
entire database back into context. No database server or persistent agent service is needed.

## Current prototype and its limits

The schema separates repository files, declaration profiles, lexical name occurrences, base-type
syntax, and agent-inferred purposes. The initial importer accepts the C# flavor's schema-2 JSON;
the architecture skill remains language-neutral, but other languages do not yet have entity adapters.
All tracked regular files remain in the file inventory, including non-C# experience artifacts.

This is a **syntax inventory**, not a compiler-bound object graph. IDs identify declarations within
one snapshot. Partial types are not merged, project membership is not evaluated, same-name entities
remain distinct, and inactive preprocessor branches are not inventoried. `profiles.lexical_name_occurrences`
and `lexical_owner_count` count name matches across the scan, not references or runtime instances.
`same_name_declarations` exposes ambiguity; a value of one still does not establish semantic identity.
Do not use these counts to claim dead code, API reachability, coupling, or safe removal.

## Build and query

Collect a committed file baseline and C# analysis at the same revision using the linked procedures.
Build tooling outside the target repository and keep the target's tracked worktree clean. Build/run
commands and timings belong in the case-study evidence. The importer verifies matching revisions,
analyzed file hashes, complete regular `.cs` file coverage, and per-file declaration totals; parse
diagnostics, conditional directives, and exclusions remain in snapshot metadata. These checks detect
truncated inventories but cannot prove that an analyzer interpreted the source correctly.

```sh
python3 <skill>/scripts/architecture_catalog.py build <output>/catalog.sqlite \
  --repository <non-sensitive-repository-label> \
  --baseline <output>/baseline.json --analysis <output>/csharp.json
python3 <skill>/scripts/architecture_catalog.py query <output>/catalog.sqlite \
  'SELECT qualified_name,file_path,line,branch_nodes FROM profiles ORDER BY branch_nodes DESC LIMIT 20'
```

`query` opens read-only, returns at most 100 rows by default, and reports truncation. Use ordinary SQLite
tools for additional analysis. The database refuses overwrite. Create a separate database for a new
revision or configuration; no annotation automatically carries over. Commit accepted architectural
conclusions in the project's normal form, not these generated databases or duplicated history documents.

Useful queries distinguish evidence from interpretation:

```sql
-- Find same-named declarations to inspect, not proven duplication.
SELECT name,arity,count(*) AS declarations FROM entities
GROUP BY name,arity HAVING count(*) > 1 ORDER BY declarations DESC LIMIT 20;
-- Search inferred responsibilities, then inspect their source evidence.
SELECT p.name,p.purpose,i.confidence,i.evidence_json FROM purpose_search p
JOIN interpretations i ON i.entity_id=p.entity_id WHERE purpose_search MATCH 'approval';
-- Scope completeness: what is outside the C# declaration inventory?
SELECT extension,count(*) AS files,sum(lines) AS lines FROM files GROUP BY extension;
```

The only resolved type relationship in this prototype is lexical containment (`entities.parent_id`).
`declared_bases.target_text` needs compiler binding before graph traversal can imply dependencies.

## Infer purpose without promoting guesses into facts

Read the declaration, representative consumers, composition/dispatch wiring, and relevant tests. Record
a concise responsibility and why apparently similar types may legitimately differ. Use confidence as
an explicit judgment, not a calculated probability. An empty purpose is unassessed, not purposeless.

Apply a batch of interpretations with `architecture_catalog.py annotate <database> <annotations.json>`:

```json
{
  "repository": "example",
  "commit": "exact-commit-sha",
  "interpretations": [{
    "entity_id": "src/Policy.cs:123",
    "purpose": "Combines permission facts into one decision; does not request user consent.",
    "confidence": "medium",
    "author": "reviewer-or-model",
    "evidence": [{"path": "src/Policy.cs", "line": 20}]
  }]
}
```

The batch must match repository and revision, refer to known declarations, and include in-snapshot
evidence locations. Updates are atomic and update the purpose search index. These checks establish
provenance, not whether a claim is true. Sampling independent reviews remains necessary. No model
is called automatically, and historical annotations stay with their original snapshot.

## Validate usefulness, not just import success

Compare queries against source inspection on a bounded journey. Include a plausible duplicate and
a justified distinction if the evidence supports them; a supported non-finding is a valid result.
Report types profiled versus interpreted, incorrect/ambiguous name matches, missed indirect or
cross-language consumers, collection/query cost, and what the catalog helped an agent find.
Do not claim improved agent accuracy or reduced engineering time without a matched comparison.
