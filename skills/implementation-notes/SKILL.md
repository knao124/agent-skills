---
name: implementation-notes
description: Use this skill when Codex is asked to implement a specification or code change while maintaining a running implementation-notes.html file, implementation notes, design log, decision log, deviations from a spec, tradeoff record, or open-question tracker. Trigger on requests to capture design decisions, deviations, tradeoffs, and open questions during implementation.
license: MIT
---

# Implementation Notes

## Overview

Use this skill to keep a durable `implementation-notes.html` file alongside implementation work. The notes are for user-relevant interpretation of the spec: decisions, deviations, tradeoffs, open questions, and validation state, not a complete command log.

## Output Contract

- Create or update `implementation-notes.html` early, before the first substantial code edit once the target root is clear.
- Default to the repository root. If the work is clearly scoped to a nested package, app, or user-specified directory, place the file there and mention the path in the final response.
- Keep the file standalone HTML with inline CSS only unless the user asks for something else. Do not fetch external assets.
- Preserve existing notes. Add a new dated work session or update the current session instead of replacing unrelated history.
- Include these sections: `Summary`, `Design Decisions`, `Deviations`, `Tradeoffs`, `Open Questions`, and `Validation`.
- If a section has no entries, write `None currently` or an equivalent explicit empty state.
- Do not include hidden reasoning or private chain-of-thought. Record observable choices, assumptions, rationale, impact, and evidence.

## Workflow

1. Read the spec and identify the implementation scope.
2. Initialize the notes file with the current timestamp, a short spec summary, and empty required sections.
3. During implementation, update the file whenever you:
   - interpret an ambiguous requirement
   - choose a non-obvious design, API, data model, dependency, or migration path
   - intentionally depart from the spec
   - pick one meaningful alternative over another
   - discover something the user should confirm or revise
4. After implementation and validation, update the notes with the final behavior, tests or checks run, checks not run, and remaining open questions.
5. In the final response, include the `implementation-notes.html` path and any important unresolved question.

For short tasks, at minimum initialize the file before editing and do a final update before replying. For longer tasks, keep it current after each meaningful implementation decision.

## Entry Format

Use concise, user-facing entries. Each entry should answer:

- `Status`: pending, decided, implemented, verified, superseded, or needs-confirmation.
- `Context`: the requirement, spec area, or component affected.
- `Note`: the decision, deviation, tradeoff, or question.
- `Rationale`: why this interpretation or approach was chosen.
- `Impact`: user-visible behavior, compatibility, migration, risk, or maintenance effect.
- `Evidence`: files, tests, commands, screenshots, or other validation when useful.

## Category Guidance

- `Design Decisions`: Ambiguous areas resolved by the implementation.
- `Deviations`: Intentional departures from the spec. Include the reason and the risk.
- `Tradeoffs`: Alternatives considered and why the selected option was better for this task.
- `Open Questions`: Items that need user confirmation. If work proceeds with an assumption, state the assumption.
- `Validation`: Checks run, important results, and checks skipped with a reason.

## HTML Shape

Use a simple structure like this and adapt it to the project:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Implementation Notes</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }
      main { max-width: 960px; margin: 0 auto; }
      section { border-top: 1px solid #ddd; padding: 1rem 0; }
      .meta, .empty { color: #666; }
      li { margin-bottom: 0.75rem; }
    </style>
  </head>
  <body>
    <main>
      <h1>Implementation Notes</h1>
      <p class="meta">Updated: 2026-05-20 12:00 UTC</p>
      <section id="summary"><h2>Summary</h2></section>
      <section id="design-decisions"><h2>Design Decisions</h2></section>
      <section id="deviations"><h2>Deviations</h2></section>
      <section id="tradeoffs"><h2>Tradeoffs</h2></section>
      <section id="open-questions"><h2>Open Questions</h2></section>
      <section id="validation"><h2>Validation</h2></section>
    </main>
  </body>
</html>
```

## Guardrails

- Keep implementing and validating the requested change. The notes are supporting context, not a substitute for the work.
- Do not document every command, file touch, or routine local choice.
- If the spec changes mid-work, add a timestamped update and mark obsolete entries as `superseded` rather than deleting useful history.
- If the user or another agent edits `implementation-notes.html`, preserve those edits and work around them.
