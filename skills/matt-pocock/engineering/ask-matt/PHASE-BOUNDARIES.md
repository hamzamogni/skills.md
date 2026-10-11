# Phase boundaries in T3

Choose at a boundary rather than discarding context mid-interview.

1. Continue when the next phase needs the current reasoning, especially interview
   to spec and spec to tickets. Preserve decisions and their rationale.
2. Start a fresh T3 session when the next ticket is self-contained and the current
   context is disposable. The user opens it; a recommendation is not permission
   for the agent to create a standalone thread.
3. Use `handoff` when changing provider, project, directory, or collaborator.
   Save the actual inputs and decisions in a portable file and tell the user how
   to open it. Do not launch a new conversation just because a file exists.
4. Use bounded `delegate_task` for a scoped side task while keeping the parent
   context. The brief must include readable pointers and the needed constraints.
5. Use provider-supported compaction when necessary. Do not assume universal
   commands or a fixed safe token count; consult the current environment.

Any summary loses detail. Check that a saved spec and tickets retain the decisions
needed by their consumers. A long-term teaching workspace remains stateful; a
self-contained implementation ticket can start with a fresh context.
