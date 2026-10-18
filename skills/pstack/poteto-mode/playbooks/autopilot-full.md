---
name: autopilot-full
description: Build and independently verify each PR, then land authorized changes from the parent with a current verdict.
---

### Autopilot-full

Read the [runtime contract](../references/t3-runtime.md). Use this playbook when
the user grants authority to build and land a queue. A request for a plan means
state the plan and wait. Operator-named review gates remain with the operator.
Autopilot-stack builds a reviewable chain when landing authority is withheld.

1. **Assign ownership and scope.** The ordinary parent thread owns the PR queue,
   watches, verdicts, and authorized merges. Dispatch one bounded `delegate_task`
   per implementation round, `mode: "async"`, using the configured role from
   `.pstack-models.md`. A user-requested
   standalone owner may carry a PR's full lifecycle in its own ordinary thread,
   with `t3_thread_launch` binding its workspace before work starts. A delegated
   child is not a standing owner and cannot arm a PR watch.
2. **Give each writer an explicit checkout and brief.** Use exclusive checkout
   paths or disjoint scopes, one writer per branch and worktree. A delegate does
   not receive a private worktree automatically. Include the goal, write scope,
   standing orders, bundled worker brief, checks, and report contract. Ask it to
   build, run relevant checks, strip slop, perform the comment pass, and publish a
   branch and PR only within the user's authorization. Keep a decision trail per
   **show-me-your-work** and return its path. Return the PR URL, branch, base and
   head SHA, self-proof, blockers, and child task IDs. End the bounded pass there.
3. **Run independent work concurrently.** Independent PRs branch from trunk;
   dependent work lands before branching the next unit. Do not share mutable
   checkouts. Retain each returned task ID, do independent work, and let completion
   wake the parent. Query `task_status` when a result is needed; do not busy-poll.
4. **Verify the actual patch.** At the code-ready head SHA, dispatch independent
   read-only verifiers using **swarm**. They rerun the required gates, audit the
   diff, and exercise the actual behavior through available `preview_*`,
   `device_*`, or a real driver. Compare with trunk where the scenario exists;
   otherwise verify the added behavior against a literal expected result. Use a
   different provider or model family where available. CI green alone is not a
   clean verdict. Missing live proof leaves a required gate unmet. Each verifier
   returns evidence, findings, and the exact head and base it inspected.
5. **Fix findings in a fresh pass.** Consolidate proven findings into one new
   implementation brief, including regression tests or a concrete reproduction.
   Do not resume-chain the previous task by its child thread ID. A changed patch
   starts a new verification round. Reuse prior evidence only under the patch-id
   rules in [Shipping](shipping.md), and record which evidence stays valid.
6. **The parent drives readiness.** Attach returned PRs with `link_pull_request`.
   Read existing CI and review threads through `gh`, triage bot claims against the
   code, and delegate bounded fixes when needed. Use [Babysit](babysit.md) in the
   parent: arm `watch_pull_request`, end the turn, and handle wakes there. A child
   returns PR state instead of babysitting. The watch never grants merge authority.
7. **Land only with authority and a current verdict.** Operator review items stop
   at merge-ready. For other items, landing needs both the user's grant and the
   parent's clean verdict. Fetch trunk, reconcile the branch, verify the final
   head's patch-id against the verdict, rerun CI and mergeability after rewritten
   pushes, and reverify changed behavior. Recheck current trunk for overlapping
   changes and CI configuration drift before the authorized squash merge. Publish
   rebases only on an owned branch with `--force-with-lease` after checking the
   remote tip. Preserve shared branches and existing edits. The parent merges,
   or an explicitly authorized standalone owner does after the verdict.
8. **Use an audit schedule only when requested.** If the user requests recurring
   audits, inspect existing schedules, then create `schedule_task` with a replayable
   prompt, `bindToCurrentThread: true`, and the requested structured interval.
   At each tick, inspect actual commits, PR state, tasks, and trails. A quiet task
   alone is not proof of a stall. Diagnose its state before cancellation or
   replacement. Keep unchanged monitoring quiet and remove the schedule at handoff.
   Do not add a recurring job merely because the queue uses this playbook.
9. **Honor stops and gates.** On a stop, cancel delegated tasks with `task_cancel`,
   interrupt authorized standalone owners with `t3_thread_interrupt`, remove watches,
   and pause or delete recurring audits. Preserve completed work and report pending
   decisions. Approval controls remain binding; a verifier cannot bypass them.

Report each PR's owner, head SHA, verdict and evidence, what landed, pending user
gates, active watches or schedules, and the trail paths.
