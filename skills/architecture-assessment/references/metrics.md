# Reproducible baseline

Architecture assessments run this baseline before deep source exploration. Other workflows can use
it when measurements help. The Python 3 collector uses only the standard library and Git:

```sh
python3 <skill>/scripts/repository_baseline.py <repository> --revision <commit> > <working-output>/baseline.json
```

It measures regular blobs from the requested commit, regardless of dirty working files. It reports
revision and collector hash, bytes, physical and nonblank lines, extension totals, excluded links and
submodules, and files whose text could not be measured. Comments are included. No file content is emitted.
An exact content hash can locate identical files; identity alone is not a debt finding.

Use the per-file inventory to classify production, tests, samples, generated code, and vendored code.
Record classification rules with the assessment. Markdown file count and bytes help assess documentation
burden; they do not measure how much guidance an agent actually loads. Count active and archived material
separately when investigating retrieval burden. Do not confuse allocated disk usage with content bytes.

Compare the same collector version and classification rules across revisions. Report changed exclusions
or file classifications before claiming reductions. Keep full JSON outside routine agent context and
summarize only the aggregates and outliers that matter to the investigation.
