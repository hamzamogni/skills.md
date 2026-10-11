# Check the pack in your T3 installation

Use a disposable project and fresh session after installation. Run scenarios
affected by the update. Record the T3 version, provider, calls, observable result,
and missing capabilities. Read the activity timeline when prose omits what ran.

1. Select `poteto-mode` and ask it to explain the project. Confirm it reads the
   runtime contract and finds bundled references. Discovery alone proves neither.
2. Run `setup-pstack`. Check proposed models against `orchestrator_capabilities`
   and inspect `.pstack-models.md`. Missing roles and `inherit-parent` should omit
   `target` in delegation. Effort uses advertised option IDs and values.
3. Ask for one read-only delegated check: read a named fixture containing `2 + 3`,
   return `5`, and change no files. Check its absolute input path, returned task ID,
   and completion without an agent polling loop. Cancel a disposable second task
   and verify its actual state.
4. For a user-requested separate thread, check its workspace binding before work
   starts. Confirm cwd and branch. Ordinary subtasks should use delegation.
5. For a PR you want monitored, request `check` first; it should read once. Then
   request background monitoring. The parent should arm `watch_pull_request` with
   repository and number, end the turn, and triage a real wake. Workers return PR
   state to that parent. Stop monitoring and check the watch is removed. Monitoring
   must not merge the PR.
6. Only if you want recurring work, request a short disposable schedule. Check its
   ID and next run, repeat the request to check deduplication, observe a run, then
   delete it and verify cleanup. Skill updates need no T3 schedule.
7. For history, browser, or simulator changes, exercise the corresponding tools.
   Check project scope, actual interaction, and captured evidence. Missing optional
   tools should produce a limitation rather than a verification claim.

PR watches and schedules change real application state. Run those checks only
when you want those actions. For prose-only changes, discovery and a read-only
delegation can be sufficient.
