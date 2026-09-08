# Release notes

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
