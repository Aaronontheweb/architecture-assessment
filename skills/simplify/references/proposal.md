# A proposal for human review

Produce enough structure to support a decision. A small finding can fit in an existing PR; a consequential
cross-component change may need a navigable page. Keep the investigation adaptive. A supported decision
to retain the current design is a valid outcome.

## Minimum decision contract

- **Current model:** the inspected revision, bounded journey, responsibilities, and relevant ranked
  goals. Separate user-owned priorities, source behavior, and inferred rationale.
- **Recommendation:** the specific change, alternatives (including retention), counterevidence,
  and what is removed, reused, retained, or introduced. State the requested human decision.
- **Expected payoff:** gross removal, replacement code, net range, confidence, assumptions, and
  source ranges. Separate production, tests, generated code, and documentation. Include transition
  cost and steady-state effect. Avoid double-counting ranges or treating removed tests as a benefit.
- **Other benefits and costs:** name a concrete extension, defect class, or maintenance task. Show
  how its current edit path changes and why. Label projections as unverified; do not invent speedups,
  approval-rate improvements, or whole-system savings from a local change.
- **Verification:** preserved guarantees, existing and missing proof, reproducible procedures,
  prerequisites, and pass conditions. Distinguish inspected tests, executed tests, and human judgment.
- **Delivery, when planning implementation:** a coherent PR sequence, dependencies, intermediate
  behavior, verification gates, and retirement of replaced mechanisms. Hand off to `plan` when
  available; an assessment need not invent a detailed delivery plan before a direction is selected.
- **Result, later:** compare actual outcomes with estimates at the same scope and measurement
  definition. Until implementation is authorized and verified, mark results as not measured.

Use diagrams for meaningful changes in ownership or sequence. State when diagrams and pseudocode omit
steps. Include failure, cancellation, recovery, or compatibility detail when it governs the decision.
An exact count of existing lines does not make a replacement estimate exact. If the range spans no
improvement or the evidence is insufficient, say so rather than inventing a positive return.

## Show the code before naming the abstraction

When explaining a proposed code change, start with a concrete example from the current implementation:
the relevant code, what it does, and why that creates a problem. Then show what would change, what
would remain, and why the difference helps. Introduce architectural terminology through that example,
not as vocabulary the reviewer must already know. Source links support the explanation; they do not
replace it. Clearly label abbreviated source and proposed pseudocode; preserve important guards.

Compare current and proposed behavior at the same level of detail. Put delivery sequencing and approval
requests after the reviewer understands the change. For greenfield work, use a concrete proposed behavior
or call site and label it as proposed; do not invent existing code.

Review question: can the reader explain what code would change and why without opening the linked
source files or already knowing the architectural vocabulary? If not, distill the explanation rather
than merely moving more text behind disclosures.

## Make human decisions unmistakable

After explaining the code change, group unresolved human choices in a visible "Decisions I need from
you" section. Each item needs a direct question, a concrete example where the options differ, a
recommendation with its trade-off and meaningful alternative, and what the answer affects or blocks.
Distinguish observed examples from illustrative scenarios still requiring verification. Do not turn
missing engineering evidence into a question for the human, invent choices to fill the section, or
present a recommendation as an accepted decision. If no answer is needed, say so.

Keep useful design explanations in a separate, clearly labeled supporting section. Link questions to
their relevant explanation instead of duplicating it. Supporting material must not conceal additional
asks. Route unanswered questions to their dependent work; keep evidence-gathering tasks with the agent.

## Browser delivery

When the user requests a self-hosted proposal, prefer static, self-contained HTML and a lightweight local
server. The optional [HTML starter](../assets/proposal.html) supplies layout and progressive disclosure;
adapt it rather than filling every possible section. It is not product UI or approved project branding.

Start with the concrete code explanation above, then the recommendation, meaningful alternative,
payoff uncertainty, and decision requested. A short proposal-only status label can remain at the top.
Keep approval-blocking questions visible; put detailed evidence, arithmetic, and commands behind
clearly labeled disclosure controls. Use semantic headings, keyboard-accessible
controls, responsive diagrams/tables, and usable print output. No remote fonts, scripts, or services
are needed. Keep source snippets escaped and link them to the pinned revision.

Serve only the chosen presentation directory, not the repository, database, secrets, or raw research
directory. Bind to loopback by default. Explain any access limitation instead of opening the listener
to the network without agreement. Verify the page in a browser: layout, links, disclosure controls,
narrow-screen behavior, and errors. A static check alone does not prove readable presentation.
Check expanded sections, table cells, and long commands, not only document-level overflow. The starter's
`stack-table` class supports prose tables on narrow screens when every body cell has a `data-label`
matching its column heading; retain explicit table/row/cell roles. Wrap commands without changing their
copyable text. Inspect printed pages for missing disclosure content, stranded headings, and clipped tables.
Repository maintainers can run `scripts/test-proposal-browser.py` against a local URL or its synthetic
fixture. Its deterministic checks support, but do not replace, visual and adversarial semantic review.

## Lifecycle and stopping point

Checkpoint the proposal's evidence and unresolved decisions in its current artifact, not an append-only
transcript. A proposal-only assignment stops at review, even if the recommended change looks obvious.
Do not implement product changes or create review-approval claims to complete the document.

After an authorized change, retain the decision and actual result in the project's Git/PR history.
Update the compact current architecture with verified responsibilities and constraints. Retire the
proposal from routine context; do not let temporary plans become another current specification corpus.
The evidence catalog stays optional and revision-scoped. New language adapters or automation should
follow a demonstrated decision need, not become prerequisites for every assessment.
