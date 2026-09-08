# Origin and maintenance

This is an early public extract from Systematize, Aaron Stannard's larger, still-private collection
of software-development lifecycle skills. It is available independently because of interest in the
architecture assessment and analysis tooling. Access to that library is not required.

Initial copy: source revision `f75386bc4aaa0da8ebd5c37c7ce618a53a4e373a`, September 8, 2026.
Copied the complete `architecture-assessment` and `simplify` skill trees, their assessment scenarios,
collector regression tests, proposal browser test, and MIT license. Public installation documentation,
the detailed analyzer explainer, packaging, and the worked synthetic example were added here.

The public repository has fresh history. Private case studies, databases, research, execution plans,
PR discussions, and the other SDLC skills are not included. The initial skill and collector contents
are unchanged. Later improvements may be ported in either direction through explicit review;
neither repository automatically updates the other. This is not a promise of a stable schema or roadmap.

The analyzer-first instruction update is maintained in both repositories: assessments attempt bundled
collection before deep source inspection, with disclosed tooling failures and language-specific limits.
The collector implementations and schema are unchanged by that instruction update.

Version 0.1.2 adds the complete `architectural-principles` skill, its C# implementation flavor, and
behavioral scenarios from Systematize revision `c958f0f1fd412c4c0d0422342ff0a4477d5be0d5`.
The copied skill is unchanged. The public assessment and simplification entrypoints now link to it
for design choices; current-state discovery still does not require a principles audit or extra report.
