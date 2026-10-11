---
name: deslop
description: Remove unnecessary code added in the current diff while preserving required behavior. Use when asked to deslop or simplify agent-generated changes.
---

# Deslop

This is a local cleanup helper, independent of provider-specific built-in commands.

Read the requested diff and project conventions. Inspect defensive branches,
casts, duplicated paths, wrappers, and comments that merely narrate the code.
Remove one only when callers, invariants, or a concrete check establish that it
adds no required behavior. Preserve boundary validation and unknown constraints;
do not silence errors or hide type failures to shorten the diff. Keep cleanup
within the requested changes. Use the installed `no-comments` skill for a comment
review when useful, with the same bounded scope.

Run checks relevant to the behavior changed and inspect the final diff. Report
what was removed, why it was unnecessary, and how behavior was verified. Commit,
push, PR creation, and landing remain subject to current task authorization.
