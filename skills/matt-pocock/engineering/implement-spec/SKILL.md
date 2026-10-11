---
name: implement-spec
description: Implement a spec's ticket graph on one integration branch, with native T3 workers and independent review.
disable-model-invocation: true
---

Read the [T3 runtime contract](references/t3-runtime.md) before executing this skill.

Read the spec and tickets using the project's configured issue tracker. If that
configuration is missing, request `setup-matt-pocock-skills`. Treat dependencies
as a graph; only tickets whose blockers are satisfied enter the ready frontier.
The deliverable is a verified integration branch and, when requested, a reviewable
PR. Work is implemented before it is landed; do not close tracker items early
when their completion contract requires a merged PR.

1. Pin the spec, ticket graph, current branch, and initial integration head. Create
   an owned integration branch, preserving existing edits. The coordinator is its
   only writer. Record each ticket's task ID, branch, input base, and state.
2. Delegate optional read-only exploration through `delegate_task`, with a cited
   notes file accessible to later workers. Include the actual input paths and
   brief; children do not inherit the conversation.
3. For each ready ticket, create an exclusive checkout based on the current
   integration tip. Use a bounded `delegate_task` with that absolute cwd, scope,
   tracker/spec pointers, and checks. The child reads [Matt's TDD](../tdd/SKILL.md),
   builds vertical red-green slices, runs relevant checks, and returns its branch,
   base/head SHAs, evidence, and blockers. Commit or publish only when authorized.
   A user-requested standalone worker instead binds its worktree through
   `t3_thread_launch`; ordinary delegation does not allocate one automatically.
4. Retain task IDs, do independent work, and handle completions without busy
   polling. The coordinator integrates one completed branch at a time. Inspect
   the diff and receipts, reconcile drift, and run integration checks. Delegate
   conflicts to a fresh bounded writer in an exclusive checkout. Never reset a
   dirty checkout or force-push shared history to make a task fit.
5. Update the frontier only after dependency work is integrated and verified.
   Dispatch newly ready tickets. Failure or cancellation does not satisfy an
   edge. Detect dependency cycles and report a concrete blocked set.
6. If the user requested a PR, create a draft after the integration branch has a
   change. Attach it with `link_pull_request`. Workers return PR facts; parent-only
   PR watches handle any requested monitoring. Opening a PR is not merge authority.
7. After the final ticket, read and run [Matt's standards/spec review](../matt-code-review/SKILL.md) against the integration
   base and spec. Consolidate findings into fresh fix tasks, then reverify the
   changed behavior at the final head. A self-review is not independent review.
8. Mark an authorized draft ready when verification passes. Report ticket states,
   final branch and SHA, proof, PR URL, and pending human gates. Keep issues open
   when they close on landing. Remove only worktrees created for this run after
   preserving their commits and uncommitted work. Never merge the PR merely
   because all tickets are implemented.
