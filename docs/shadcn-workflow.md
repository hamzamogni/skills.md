# Build UI with Matt, poteto, and shadcn

Install the full collection in the target project:

```sh
npx skills@latest add hamzamogni/skills.md --skill '*' --agent codex
```

Use `--agent claude-code` for Claude, then restart the agent session. Rerun this
command to add `shadcn` to an older installation. The collection now has 83 skills.
Installing skills does not initialize shadcn or install components in an application.

Matt's flow decides and records the work. Choose Matt's implementation method or
poteto for each implementation unit. Shadcn supplies UI guidance within that phase.
The routers load the installed `shadcn` skill for relevant UI work. It remains
contextual guidance rather than a promised `/shadcn` command. Direct Matt phases
also read the shared runtime contract, which routes relevant UI work to shadcn.

Use the project's actual package runner and cwd. The native port explicitly runs
`shadcn@latest info --json` and reads its output, instead of assuming a provider
executes command-injection syntax. MCP is optional. The CLI provides project
inspection, component discovery, and documentation lookup.

## Start a greenfield application

For example, build a task-management MVP:

1. Start `matt-mode`: "Plan a task-management MVP using React, Vite, and shadcn/ui.
   Interview me about the core workflows before implementation." Agree on users,
   actions, data, and product boundaries. Use `setup-matt-pocock-skills` once the
   project exists to settle its tracker and document conventions.
2. Agree on the framework, base library, preset, registry, and important design
   constraints. Record those decisions. A brand-driven design system can use
   `DESIGN.md`; a small MVP can keep its decisions in the spec.
3. If an interaction is uncertain, use `prototype` with shadcn guidance. Inspect
   an initialized prototype project, find relevant components, and read their docs.
   Compare the runnable screen with the intended behavior. Keep disposable
   prototype code separate and bring accepted decisions back to the decision session.
4. Use `to-spec`, then `to-tickets`. Include empty task lists, loading, failed saves,
   validation, keyboard behavior, and responsive layout. Tickets carry their own
   context and blocking dependencies. Approve the breakdown before publication.
5. Start a fresh implementation session for each unit. For example:
   "poteto-mode: implement ticket 01 using the agreed shadcn setup and spec."
   The chosen builder reads shadcn guidance, initializes the agreed production
   setup, runs project inspection, and adds only the needed components. One owner
   handles shared theme and component files if other tickets run concurrently.
6. Exercise the app in the browser and run the project's relevant checks. Use
   `matt-code-review` for spec and standards alignment, with the appropriate defect
   review when needed. Open a PR and hand it to the human reviewer.

Keep interview, spec, and ticket decisions together. Return separate prototype
evidence to that session. Shadcn helps implement the agreed interface; choosing a
component does not settle the product's behavior.

## Add a feature to an existing application

For example, add a profile settings form:

1. Start `matt-mode`: "Add profile settings to this app. Reuse our current shadcn
   components and theme. Work out save, validation, and permission behavior first."
   Read existing screens and project instructions before choosing a design.
2. Inspect `components.json`, package manager, and actual `shadcn info --json`
   output. Reuse the configured base, aliases, icons, variants, and customized
   components. If the app uses another component system, adopting shadcn is a
   separate explicit decision. Missing configuration does not justify a reset.
3. Use a focused prototype only for unsettled interaction choices. For a larger
   feature, write a spec and self-contained tickets. A small, clear change can go
   directly to a single builder. Preserve success, failure, and accessibility criteria.
4. Run `implement` for a ticket, or give the ticket to `poteto-mode`. The builder
   loads shadcn guidance, checks installed components, reads current component docs,
   and composes the form. Preserve the customized Button and the app's theme.
5. Preview any needed updates to existing components with `add --dry-run` and
   `add --diff`. Merge necessary changes while retaining customizations. Changing
   presets or overwriting components requires authorization for that change.
6. Verify validation, failed and successful saves, loading, keyboard use, mobile
   layout, and dark mode when supported. Review related screens if a shared
   component changed, then open the application PR for human review.

## Review skill updates and component updates

The `shadcn-ui` source selects only `skills/shadcn` and root `LICENSE.md`. It
ignores changes elsewhere in that repository. A selected
content change produces a separate `sync/shadcn-ui` review-request PR through the
existing six-hour watcher. An open review PR stops further proposals for that source.

Follow [the update procedure](upstream-updates.md), using source name `shadcn-ui`.
Review new command-injection syntax, provider-specific metadata, CLI/API changes,
MCP assumptions, preset behavior, helper scripts, asset paths, and license changes.
Keep evaluation fixtures raw-only and preserve existing-app customizations.
`merge --continue` requires an explicit native-port acceptance, even after a clean merge.

The license retains its upstream filename in the raw snapshot and becomes `LICENSE`
in the editable pack. License updates are three-way merged and bundled inside the
installed skill. Run `python3 scripts/package_skills.py build` before acceptance.

For a baseline candidate, use:

```sh
python3 scripts/seed_shadcn_port.py --destination .work/shadcn-candidate-new \
  --manifest .work/shadcn-map-new.json
git diff --no-index skills/shadcn-ui .work/shadcn-candidate-new
```

The generator refuses existing destinations. It supplies baseline T3 changes,
aliases, exclusions, and a map. It does not reproduce the authored runtime guide,
bundled notice, or later manual improvements. Adopt selected changes and regenerate
bundles. Preserve the map's original upstream paths.

After approving and merging a skill port, run `npx skills@latest update -p` in
installed projects. That refresh changes agent guidance. It does not upgrade
application components. Review component updates with the shadcn CLI in their own
application change. The skill also uses current CLI documentation, so smoke-test
affected component workflows when the CLI or installed app libraries change.

## Keep the one-pager current

The README embeds [the revised one-pager](images/skills-one-pager.png). Its UI
annotations cover prototype, spec, build, review, and initial setup. The purple
UI card distinguishes greenfield choices from preservation of an existing app.
It keeps the two front doors, one builder per task, and human PR handback.
The setup label is guidance, not a slash command.

When revising the image, check every skill name against the installed collection,
preserve the workflow's handbacks, and inspect the final image for readable text.
Use this guide and [the combined workflow](combined-workflow.md) for the maintained
text behind the visual. The original PDF in Downloads remains the reference.
