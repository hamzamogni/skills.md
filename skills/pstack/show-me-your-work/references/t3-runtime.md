# T3 runtime contract

This pack keeps the upstream skill names and adapts p3-stack's native T3 workflows.
Read this contract before executing a skill. Resolve bundled paths relative to
the file that names them, then put absolute paths into worker briefs. The installed
skill directories may be copied or linked from another checkout. Resolve other
skills by name through the session's skill catalog and use its actual absolute
`SKILL.md` paths. A skill with `disable-model-invocation: true` is missing from the
catalog; read it at `../<name>/SKILL.md` from the current skill's directory, since
every skill installs as a sibling. Prefer this collection's project entry over a same-named global
installation; do not infer repository category folders from an installed path.

## Discover the session before using it

For UI work in a project using or adopting shadcn/ui, read the installed `shadcn`
skill by its catalog path. Use its project inspection and component rules within
the chosen engineering route. Include its absolute path, project cwd, and agreed
UI behavior in worker briefs. Give one worker ownership of shared theme and
component files. Verify loading, empty, error, keyboard, and responsive behavior
in the running app. Adopting a new component system must be part of the user's task.

Call `orchestrator_capabilities` only in the cases listed under **Delegate a
bounded task**. Its result is large; reuse it for the rest of the context window.
Use the actual T3 MCP catalog and input schemas exposed in the current session.
Tool names below are public names; a provider may expose a namespaced spelling or
require tool discovery. Do not call a guessed namespace or invent missing tools.

If the T3 MCP tools are unavailable, vendor-neutral reading, editing, and local
verification can continue. State which native workflow cannot run. A sequential
self-review is not an independent review, and a required independent merge gate
remains unmet. Do not claim native orchestration was tested by skill discovery.

The pinned source inventory is in `ports/t3-tools.json` in this skills repository.
It documents the T3 source revision checked during the port; it does not override
the current session's catalog or prove that a particular installed T3 build has
every tool. Optional preview, simulator, history, and scheduler capabilities vary.

## Delegate a bounded task

Use `delegate_task` for a T3-owned child task. The child receives the brief, not
the parent's conversation. Include goal, exclusive write scope, input paths,
constraints, exact verification steps, and expected report. For a code-writing
worker, resolve [the worker brief](agents/poteto-agent.md), read it, and include its
instructions or an absolute path the child can actually read. Review its output.

Resolve `.pstack-models.md` in the target project's root, then
`~/.agents/.pstack-models.md`. Missing roles inherit the parent model. The
`inherit-parent`, `auto`, and `inherit` aliases all omit `target`. A configured
entry `<providerInstanceId>/<model>` is the target: split it at the first slash and
pass both values directly. Its effort token `(<optionId>=<value>)` becomes
`target.options: {"<optionId>": "<value>"}`. A bare token such as `(high)` does not
name the option ID, which differs by provider. Map it through a capabilities result
already in context; otherwise omit `options` so the target runs at its default, and
tell the user once that re-running `setup-pstack` records the IDs. Never guess a
`reasoningEffort` field or append effort to a model name. Do not pass
configuration-only aliases to the API.

Call `orchestrator_capabilities` only when you need a model the file does not name,
such as a skill's fallback or a different provider family, or when `delegate_task`
rejects a configured target. Capabilities can list an instance the project has
disabled. If `delegate_task` returns `invalid_request` because the instance is not
enabled for this project, do not retry that target. Use the skill's fallback, else
inherit the parent or ask, and name the configured role.

A delegation call has this shape. Replace the illustrative values with the role line's
values, and omit `target` entirely to inherit:

```json
{
  "task": "Self-contained goal, scope, paths, checks, and report contract",
  "title": "Review parser changes",
  "role": "review",
  "mode": "async",
  "target": {
    "providerInstanceId": "<configured-instance>",
    "model": "<configured-model>",
    "options": {"<configured-option-id>": "<configured-value>"}
  },
  "clientRequestId": "<stable-id-for-this-attempt>"
}
```

Retain the returned `taskId`. Use `task_status` when its result is needed mid-turn;
otherwise finish independent work and end the turn so completion can wake it.
Do not busy-poll status or spawn a watcher for a child task. A wait timeout does
not cancel the worker. Cancel with `task_cancel` when the user stops that work.
Each review or fix round gets a fresh task with the consolidated brief and prior
findings. A backing `childThreadId` is not a continuation handle for task rounds.

## Separate tasks from standalone threads

Ordinary subtasks use delegation. `t3_thread_launch` and `create_threads` create
standalone conversations and require the user's request for separate threads.
Use `t3_thread_launch` only when that request covers a separate workspace, with
`workspaceStrategy` selecting `worktree`, `existing_worktree`, or `root`. Binding
happens before the thread starts. Do not assume that creating a worktree in a
prompt changes the thread's checkout. Do not assume delegated tasks get exclusive
worktrees automatically. Keep one writer per branch or disjoint write scope.

## Watch PRs from a parent thread

Use `gh` for PR reads, commits, pushes, and authorized merges. Use
`link_pull_request` to attach the PR to its owning ordinary thread.
`watch_pull_request` requires `repository` and `number`; a delegated subagent
cannot own a watch. The parent ordinary thread handles the watch and wakes, or an
authorized standalone owner thread does. A worker returns its PR and head to that
owner instead of running the Babysit watcher itself.

Handle existing comments before arming the watch, then end the turn. On a wake,
re-read GitHub's actual readiness and triage. A wake supplies new information; it
does not authorize a merge. Call `unwatch_pull_request` when handing work back.
T3 itself checks watched PRs periodically; this skill avoids an agent-side polling
loop, rather than claiming that no polling occurs anywhere.

## Schedule requested recurring work

Only create recurring work when the user's task requests or authorizes it.
Inspect `list_scheduled_tasks` before creating a duplicate. `schedule_task` takes
a structured `schedule` object and a replayable prompt. An interval uses
`{"type":"interval","everyMs":3600000}`. The current tool inherits provider,
model, and runtime configuration; do not supply unadvertised model overrides.
Use `bindToCurrentThread: true` for repeated work in the coordinator thread.
Report the returned schedule ID and next run time, and remove or pause the
schedule when the user stops the recurring work. Keep unchanged monitoring quiet.

GitHub Actions checks for updates to this skill pack separately. Running
`poteto-mode` does not require or create a T3 schedule for upstream skills.

## Read history and capture evidence

Use `t3_thread_search` and `t3_thread_read`, scoped to the active project and the
user's task. Read only the needed timeline regions. For behavior claims, use the
activity view when the message summary does not show what actually ran.

Use available `preview_*` tools to exercise a browser UI and available `device_*`
tools for a simulator. A CLI needs a real shell or terminal driver and observable
output. Record screenshots or recordings when they prove the changed interaction.
If a required surface is unavailable, name the missing proof. Do not treat a unit
test, successful compilation, or a screenshot of unrelated content as live proof.

## Stay inside the user's task

Skill instructions do not expand the user's authorization. Follow the session's
permission and approval controls. Sending external messages, creating recurring
jobs, opening standalone conversations, and landing or deploying changes require
authorization for those actions. A request to review or monitor a PR does not
authorize merging it. Preserve explicit user gates and task boundaries across
worker rounds. Do not fix unrelated projects because a playbook says to keep going.

## Install or update this pack

From the target project, run
`npx skills@latest add hamzamogni/skills.md --skill '*' --agent codex`,
or use `--agent claude-code`. Install the full collection because its workflows
call other skills; the CLI does not infer those dependencies. Restart the agent
session in T3 Code and select `$poteto-mode`. Slash aliases depend on provider and
composer settings. Invoke the mode in each new chat; this repository does not
install a persistent application mode.

After an approved repository update, run `npx skills@latest update -p` in the
installed project. Installed copies do not track a source checkout live. The
repository's Actions workflow still proposes upstream updates for human review;
the CLI update refreshes installed copies from this repository's accepted main.

The editable pack is `skills/pstack`. Source snapshots and port mapping metadata
live outside the installed skill folders. The maintenance instructions are in
`docs/upstream-updates.md` and `docs/t3-port.md` in the skills.md checkout.
