# Release notes

## 0.1.2

- Includes `architectural-principles` as the third skill, with shared defaults and a C# implementation
  flavor. Assessment and simplification link to it for design choices, not another required report.
- Updates installation examples, package validation, and Copilot discovery/resource checks for all
  three skills. Includes the existing principles behavioral scenarios; these are not executed model evals.
- Includes the public Netclaw investigation: concrete findings, pinned source evidence, agent prompts,
  and manual commands, with a usefulness synopsis in the README.

Collector code and database schema are unchanged. Existing plugin users should update the plugin;
users who copied skills must include the new directory and its supporting reference.

## 0.1.1

- Architecture assessments always try the bundled analyzer before deep source exploration. For C#,
  collect the Git baseline and Roslyn inventory, then build and query SQLite to choose where to look.
  A failed prerequisite or run must be disclosed before a bounded manual fallback; non-C# assessments
  do not require .NET. Verified matching catalogs can be reused.
- Added behavioral scenarios for analyzer-first ordering, failed tooling, and non-C# scopes.
- Documented plugin and copied-skill updates for Claude Code, GitHub Copilot, and Codex, including
  reloading and reconciling obsolete copied files.

Collector code and database schema are unchanged. These instructions improve the expected workflow;
automated collector and packaging tests do not prove model compliance.
