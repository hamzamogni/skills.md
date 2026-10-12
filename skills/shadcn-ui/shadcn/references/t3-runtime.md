# shadcn guidance in T3 Code

Use this skill for projects using or explicitly adopting shadcn/ui. It supplies
component and design-system guidance inside the current prototype, implementation,
or review phase. Matt or poteto remains the builder. Preserve the current task's
scope, authorization, and handback. Do not introduce shadcn into an app using
another component system unless adoption is requested.

## Inspect the actual project

Read the project's instructions, package manager, `components.json`, and existing
UI conventions. Run the appropriate package runner's `shadcn@latest info --json`
through the session's command tool with an explicit project cwd. This port does
not rely on automatic command injection or provider-specific command allowlists.
Read the command output. Do not invent injected configuration when the command
fails. Inspect local configuration to diagnose a failure and report any blocker.
Refresh the output after changing configuration or adding components.

Use the returned framework, base library, aliases, component inventory, and file
paths. Use the actual session tool schemas to run commands, fetch the URLs from
`shadcn docs`, and inspect the UI. The project's runner may be npx, pnpm, or bun.
The CLI is sufficient; a shadcn MCP connection is optional. This skill does not
write MCP configuration or assume particular MCP tools exist.

## Start a new project

Keep the product interview and agreed work with Matt's phases when those phases
are being used. Before scaffolding, settle the framework, base library, preset,
and any brand or design constraints that materially affect the result. Use prior
decisions and task authorization. Ask only for missing product or design choices
that cannot be inferred. Record those choices in the project's existing docs or
spec. A `DESIGN.md` is useful for a requested design system, not mandatory for every
application.

Initialize the agreed application in its intended directory, then run project
inspection. Add the components needed for the feature. Installing the full
component catalog belongs to a requested design-system showcase. Follow the
design-system references when that is the actual task, with the agreed base and
preset. Keep a throwaway UI prototype separate from production implementation.
Carry accepted interactions and visual decisions into the spec and tickets.

## Add a feature to an existing app

Inspect the app before proposing changes. Reuse its configured base, theme,
component variants, aliases, and customized component files. If configuration is
missing, determine whether the app uses shadcn or another UI system before running
initialization. An ordinary feature does not authorize resetting presets or
replacing a component system.

Check installed components first. Read relevant component docs and rule files
before composing the UI. Use `add --dry-run` and `add --diff` before updating an
existing component. Preserve local changes. Use `--overwrite` only within explicit
authorization. For preset changes, prepare the overwrite, partial, merge, or skip
choice before making the authorized change. Use the registry already specified
by the user or project policy; ask if the required registry choice is still missing.

## Delegate and verify

Resolve the installed `shadcn` entry through the session's actual skill catalog.
References and assets are relative to that installed skill folder. Give a UI
worker the absolute skill path, project cwd, relevant references, agreed behavior,
and file ownership. Do not assume repository pack folders exist after npx
installation. Give one worker ownership of shared theme and component files when
other tickets run concurrently. Preserve blocking ticket relationships and the
chosen builder's phase boundaries.

Verification follows the requested UI behavior. Check the running page, relevant
loading, empty, and error states, validation, keyboard use, responsive layout, and
dark mode when supported. Run the project's relevant checks. Report which states
were exercised and any unavailable browser or runtime evidence. Static skill
discovery and a successful CLI command do not prove interactive behavior.

## Update guidance separately from components

This repository tracks only the upstream skill folder and `LICENSE.md`. Its
six-hour watcher proposes upstream changes in a `sync/shadcn-ui` PR for human
review. Use `report shadcn-ui --diff`, merge into the native port, review runtime
changes and retained helpers, regenerate bundles, then accept the port with
`merge shadcn-ui --continue`. The repository update guide has the full procedure.

After landing an approved port, refresh installed skills with
`npx skills@latest update -p`. Rerun the full collection's `add` command when adding
this skill to an older installation. Skill refreshes change agent guidance. App
components are updated separately through the shadcn CLI and their application PR.
Do not execute newly imported helper scripts during source sync or packaging checks.
