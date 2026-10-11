---
name: matt-mode
description: Start one phase of Matt Pocock's workflow for a task, then hand back its result and next command. Use when asked for matt-mode or Matt's workflow.
---

# Matt mode

Run one useful phase, then stop at its completion boundary. `ask-matt` is advice
only. `poteto-mode` is the alternative implementation method; do not run both
builders on the same ticket. Read the [T3 runtime contract](references/t3-runtime.md)
before native delegation or external actions.

Read the user's task and existing artifacts. Choose the first unmet phase whose
inputs are available, and read that installed skill before starting it. Resolve
its name through the session's skill catalog and use the reported absolute
`SKILL.md` path. Prefer this collection's project entry over a same-named global
installation. If the catalog is unavailable, inspect the project's
`.agents/skills/<name>/SKILL.md` or `.claude/skills/<name>/SKILL.md` and resolve
symlinks. Do not assume the installed files retain repository category folders.
If the required skill is missing, report it and the full-collection install command
instead of inventing its workflow.

| Situation | Phase to run |
| --- | --- |
| Unclear product decisions with a project | `grill-with-docs` |
| Interview without a project | `grill-me` |
| A design question needs a runnable answer | `prototype` |
| A specific factual question needs primary sources | `research` |
| An interview is settled and a spec is requested | `to-spec` |
| A spec needs self-contained dependent tickets | `to-tickets` |
| A clear ticket is ready to build | `implement` |
| The user requests implementing the whole ticket graph | `implement-spec` |
| The task is a standards/spec review | `matt-code-review` |
| A hard bug needs a reliable reproduction | `diagnosing-bugs` |
| A multi-session effort still has unresolved decisions | `wayfinder` |
| The user requests a retrospective | `retro` |

Skip unnecessary planning for a small, clear task. Do not create issues, branches,
schedules, standalone threads, or PRs just because they are later on the road.
Follow the chosen phase and existing task authorization. Product decisions belong
to the user; facts should be established by reading or a scoped experiment.

On completion, report the phase, actual result and artifact pointers, pending
product decisions, and one suggested next command with its inputs. Do not execute
the next phase automatically. Keep interview-to-spec-to-tickets reasoning in the
same session when needed; recommend a fresh T3 session for a self-contained build
ticket. A research phase can launch its bounded background task and hand back
its ID; report its eventual result before claiming the phase is complete.

The combined-workflow guide in the skills.md checkout explains setup, naming,
and how to hand off to `poteto-mode` at the implementation boundary.
