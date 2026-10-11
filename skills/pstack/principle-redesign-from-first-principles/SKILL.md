---
name: principle-redesign-from-first-principles
description: "Apply when integrating a new requirement into an existing design."
disable-model-invocation: true
---

## T3 Code runtime

Read [T3 Code runtime guidance](../poteto-mode/references/t3-runtime.md) before
following the workflow below. That guidance replaces Cursor-specific tool, model,
configuration, and history instructions in this skill and its references.

# Redesign From First Principles

When integrating a change, don't bolt it onto the existing design. Redesign as if the requirement had been a foundational assumption from the start.

- Read all affected files and understand the current design
- Ask: "if we were writing this from scratch with this new requirement, what would we build?"
- Propagate the change through every reference: types, docs, examples, rationale sections
- Think about the whole redesign, then deliver it incrementally

This is the method for preserving option value when integrating changes into an existing design.
