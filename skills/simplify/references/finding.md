# Finding contract

Use this structure only for substantiated candidates, not every metric outlier:

- **Responsibility and evidence:** inspected revision, source locations, current behavior, and why the
  competing mechanisms or misplaced concerns create friction.
- **Proposed simplification:** what is reused, removed, consolidated, introduced, or retained; explain
  necessary compatibility and platform distinctions.
- **Counterevidence and confidence:** why this might be intentional, callers checked, unknowns, and
  relevant known or readily discoverable unmerged work that could already address it. State whether
  that work was checked; do not conduct an unbounded PR search. Never mix it into the pinned baseline.
- **Preserved outcomes:** public behavior, authority, upgrade safety, resource ownership, and other
  relevant constraints. Do not invent a new project priority.
- **Verification:** a reproducible procedure, required fixtures/environment, pass condition, and
  checks inspected versus actually run. State evidence cost and what remains human judgment.
- **Sequence:** bounded enabling change, dependencies, human decisions, and expected net effect.
- **Expected payoff:** when a reduction estimate is requested, identify removable source spans and
  replacement assumptions. Show gross removal, additions, and a net range with confidence. Justify
  other benefits with concrete current and proposed edit paths, not claims such as "more extensible."

Code and Markdown counts can provide repeatable baselines; competing concepts require a reviewed
before/after inventory. A reduction in file count is not useful if it creates an unreadable monolith.
Keep production, tests, generated code, and documentation accounting separate and stable across revisions.
Distinguish temporary compatibility coexistence from steady-state savings. Do not add overlapping or
mutually exclusive candidates together. Test additions are a cost worth showing, not a failed cleanup.
