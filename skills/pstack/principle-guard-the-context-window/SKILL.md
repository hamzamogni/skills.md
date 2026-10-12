---
name: principle-guard-the-context-window
description: "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to delegated tasks; keep summaries in the main thread, not raw payloads."
disable-model-invocation: true
---

Read the [T3 runtime contract](references/t3-runtime.md) before executing this skill.

# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
