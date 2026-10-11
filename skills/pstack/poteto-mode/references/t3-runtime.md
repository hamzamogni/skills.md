# T3 Code runtime guidance

This is the first port of Cursor pstack to T3 Code. Apply this guidance before
Cursor-specific instructions in this pack, including playbooks and references.
Keep the engineering workflow while adapting its execution to the current provider.

## Tools and agents

T3 Code wraps the selected provider. Use the tools actually exposed in the session.
`Task`, `AskQuestion`, `generalPurpose`, `poteto-agent`, and `Comment Sicko` are Cursor
interfaces, not a guarantee that equivalent tools or registered agents exist here.
If delegation is available, give the worker the relevant skill and its role's
instructions. The original agent definitions remain in `upstream/pstack/agents`
in this skills repository for reference; the installer does not register them.

If delegation is unavailable, do the steps sequentially and report that limitation.
Do not describe a sequential self-review as an independent review or a multi-model
evaluation. For a playbook that requires independence to authorize a merge, stop
at the reviewable result when the required reviewer cannot run.

Use the current provider's question tool when available, or ask in chat.
Cursor cloud agents, `/loop`, Custom Modes, and Cursor automation scheduling need
a separate implementation. Do not invoke them as if T3 Code supplied them.

## Model configuration

Inherit the current model by default. Do not pass Cursor model slugs to a different
provider or assume a provider supports selecting a model for each worker.
Read `.pstack-models.md` in the target project's root if it exists. Interpret its
role choices only against models and delegation controls the session exposes.
If a configured choice is unavailable, report it and use the current model.

For `setup-pstack`, replace the Cursor rule-writing steps with a project-local
`.pstack-models.md` containing the chosen roles and confirmed model names.
If there is no per-worker model selection, record `inherit-parent` for those roles.
Do not create `~/.cursor/rules/pstack-models.mdc` or assume any file is automatically
injected into a T3 Code session. Skills read the project configuration explicitly.

## Skills and verification

Select skills with `$` in the T3 Code composer. Slash skill aliases depend on T3
settings and provider support. Resolve other skills from installed sibling folders.
Use `poteto-mode` as the default entry point and read its requested playbook.
Treat the mode as a conversational preference for this chat; persistence across
new sessions requires invoking it again or adding your own project instructions.

`create-skill`, `deslop`, `control-cli`, and `control-ui` are not bundled here.
When one is requested, use an available equivalent or perform its stated job
directly with the session's tools. For verification, run the real project or a
named driver and state what you observed. Do not claim to have loaded a missing
skill or completed a gate that depends on unavailable tools.

Bundled scripts retain upstream code and dependencies. Inspect the script before
running it. Bun, TypeScript packages, shell utilities, GitHub CLI, and provider
history stores are separate prerequisites, not installed by this repository.
Cursor-specific scripts such as `worktree-audit.sh` require a port before use.

## History and privacy

Use the current chat and provider-supported history retrieval. Do not use Cursor's
transcript paths in `recall`, `automate-me`, or eval workflows. Do not search unrelated
projects or claim access to transcripts that the provider has not made available.
If the history needed for a task is missing, explain the missing evidence.
