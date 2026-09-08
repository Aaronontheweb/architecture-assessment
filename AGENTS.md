# Agent guidance

This public repository contains two skills: `architecture-assessment` and `simplify`, plus bundled
source-analysis tools. Keep it independently usable. Do not introduce dependencies on the author's
private SDLC library or publish internal project examples, transcripts, endpoints, or generated catalogs.
`CLAUDE.md` is a symlink to this file.

The collectors produce syntax evidence, not semantic references or proof of safe deletion. Preserve
revision/hash checks, explicit uncertainty, and separation of observations from interpretations.
Skill outputs are assessments and proposals, not automatic permission to refactor a target project.

Keep skill directories flat and preserve their supporting resources and relative links. The optional
`interview` and `plan` handoffs are not bundled prerequisites. Do not add neighboring SDLC skills.

Run `python3 scripts/validate.py`, build the collector outside the target repository, and run
`python3 scripts/test-analysis-tools.py --csharp-dll <collector>/csharp-metrics.dll` plus
`python3 scripts/test-example.py --csharp-dll <collector>/csharp-metrics.dll` after relevant changes.
For HTML template changes, also run `python3 scripts/test-proposal-browser.py` with Playwright Chromium
and `pdftotext` installed. Behavioral cases in `evals/` are not automated semantic tests.

Keep derived data ignored. Prefer public synthetic fixtures. Packaging changes must keep both plugin
versions and the Claude marketplace version synchronized. Updates from the original library are
deliberate reviewed copies, not automatic synchronization; see `PROVENANCE.md`.
