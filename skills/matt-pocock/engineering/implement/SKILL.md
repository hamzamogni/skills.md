---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Read the [T3 runtime contract](references/t3-runtime.md) before executing this skill.

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Read and follow [Matt's TDD skill](../tdd/SKILL.md) where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, read and follow the installed skill "matt-code-review" to review the work.

Commit only when the current task authorizes it, preserving existing edits. Otherwise leave a reviewable diff and verification report. Do not push or merge without task authorization.
