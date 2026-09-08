# Worked example: why name counts need interpretation

This example is synthetic and public. It is not output from an internal product, and is deliberately
small enough to check by reading all [three source files](../examples/source/).

`Example.Billing.RetryPolicy` accepts a maximum attempt count and answers whether a transient failure
may be retried. It does not schedule retries or execute any work. `Usage` calls it. Two unrelated records
are both named `Params`: one holds billing attempts and the other holds a report title.

## Reproduce it

Run from this repository root, with the prerequisites in the [README](../README.md):

```bash
example_output=$(mktemp -d)
dotnet build skills/architecture-assessment/scripts/csharp-metrics.cs -o "$example_output/collector"
python3 scripts/test-example.py --csharp-dll "$example_output/collector/csharp-metrics.dll"
```

The script copies only the synthetic source into a temporary Git repository, commits it with a fixture
identity, collects the baseline and syntax observations, builds SQLite, queries profiles, adds an
explicit example interpretation, and exercises full-text search. It checks the values below and cleans
up its temporary snapshot. It does not call a model or touch another project. The collector build remains
in `example_output`; choose your own output location for longer-lived experiments.

## Selected output

| Qualified declaration | Methods | Branch nodes | Max constructor parameters | Name occurrences | Same-name declarations |
|---|---:|---:|---:|---:|---:|
| `Example.Billing.RetryPolicy` | 1 | 1 | 1 | 1 | 1 |
| `Example.Billing.Params` | 0 | 0 | 1 | 2 | 2 |
| `Example.Reporting.Params` | 0 | 0 | 1 | 2 | 2 |
| `Example.Usage` | 1 | 0 | 0 | 0 | 1 |

The script prints these actual profile fields as JSON, followed by this search result:

```json
{
  "name": "Example.Billing.RetryPolicy",
  "purpose": "Decides whether another retry is allowed; does not schedule or execute one."
}
```

That purpose is supplied explicitly by the example, not inferred by Roslyn. A real assessment agent
would inspect source and consumers before authoring it. The full annotation also records author,
confidence, revision, entity ID, and evidence locations.

## What a reviewer should notice

Both `Params` profiles report two occurrences. The calls are namespace-qualified, but the collector
does not bind symbols: SQL pools the simple name and generic arity. There is one actual call site for
each record in the example, not two verified references to each record. Same names do not mean their
responsibilities should be merged.

`Usage` has zero recorded name occurrences. That does not prove it is safely removable in a real
project: external callers, implicit wiring, reflection, or scope exclusions may matter.

The one branch in `RetryPolicy` comes from its `if`. The comparison in its return expression isn't an
extra branch under this metric's definition. This illustrates why the count should not be called
cyclomatic complexity.

The useful next question is not "which number is biggest?" It is "what does this responsibility own,
and which behavior must be preserved if we change it?" The two skills guide that investigation.
