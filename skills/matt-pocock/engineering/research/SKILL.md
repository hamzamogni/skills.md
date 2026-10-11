---
name: research
description: Research a question against primary sources and save cited Markdown notes, using a T3 background task when available.
---

Read the [T3 runtime contract](references/t3-runtime.md) before executing this skill.

Choose the notes path using the project's convention. Give one `delegate_task`
a self-contained brief with the question, scope, primary-source requirements,
absolute output path, exclusive write permission for that file, and report shape.
Use `mode: "async"`; retain its task ID and continue independent work. Let completion
wake the parent, then read the actual notes and check the cited evidence.

The researcher follows claims to official docs, source code, specs, or first-party
APIs. It distinguishes facts, inference, uncertainty, and source dates, and writes
one Markdown file with direct source links. If this skill runs inside that worker,
perform the research directly instead of spawning another researcher for the
same question. Without native delegation, research sequentially and state that
limitation. Research feeds decisions; it does not authorize implementation,
external messages, publishing, or a recurring job.
