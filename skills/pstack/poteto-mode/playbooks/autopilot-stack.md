---
name: autopilot-stack
description: Build and verify one linear base-branch stack, then hand it to the operator to review and land.
---

### Autopilot-stack

Read the [runtime contract](../references/t3-runtime.md). This playbook builds and
verifies the queue while the operator retains landing authority. Use
[Autopilot-full](autopilot-full.md) when the user explicitly grants landing.

1. **Run bounded implementation passes.** Follow Autopilot-full steps 1 through 5
   for briefs, model roles, exclusive checkout paths, trails, independent proof,
   and fresh fix rounds. A delegated worker builds and returns its PR URL, head,
   base, checks, blockers, and trail. The ordinary parent owns watches and queue
   state. Only user-requested standalone owners bind workspaces through
   `t3_thread_launch`; ordinary delegation does not allocate worktrees.
2. **Keep landing with the operator.** No worker or parent merges, closes a PR, or
   arms auto-merge. A request to state the plan is not a go. Preserve named review
   gates. On a stop, cancel tasks and watches and pause requested audits.
3. **Verify each round.** Require a clean independent verdict at the final patch
   per Autopilot-full step 4. Report STACK-READY with its exact head and base SHAs
   and evidence. A changed patch requires new proof under Shipping's patch-id
   rules. CI and mergeability rerun after every rewritten push.
4. **Append in verified order.** The root targets trunk; each higher PR targets its
   predecessor's branch. The parent is the only topology writer. Owners write
   only their assigned branches and return intended parent and tip. Fetch that
   parent, reconcile the child onto the exact tip, then push an owned branch with
   `--force-with-lease` after checking the remote tip. Preserve existing work.
   Use `gh pr create --base <parent-branch>` or `gh pr edit <pr> --base <parent-branch>`.
   Do not require Graphite. Attach each PR with `link_pull_request` and check
   `list_thread_pull_requests` against the intended bottom-to-top order.
5. **Reconcile drift and reverify.** Work bottom-up after trunk changes. Delegate
   bounded conflict fixes to the code owner; keep topology changes in the parent.
   Rewritten SHAs invalidate verdicts unless Shipping's patch-id rules preserve
   the specific evidence. A new behavior needs another independent review round.
   Do not count inherited green checks as current proof.
6. **The parent monitors readiness.** Read existing comments and checks, then use
   [Babysit](babysit.md) on the frontier. Arm `watch_pull_request` in the ordinary
   parent and end the turn. A delegated child returns status; it cannot watch.
   Fix verified findings through fresh tasks. A wake never authorizes landing.
   Use recurring audits only if requested, as in Autopilot-full step 8.
7. **Deliver and hand back.** Report the stack root and tip, order, final SHAs,
   verdict and evidence for each link, pending gates, and excluded work. The
   operator reviews and lands it. Remove watches and recurring audits when
   handing control back unless continued monitoring was requested.
