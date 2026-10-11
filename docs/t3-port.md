# How this T3 port is maintained

The editable pack keeps 52 upstream skills, including `poteto-mode`,
`poteto-help`, and `setup-pstack`. It builds on native rewrites from
[p3-stack at 09909ebb](https://github.com/uzairansaruzi/p3-stack/tree/09909ebb5c0125e27fad3e57d96b81e832696d69).
The upstream-only `ketchup` skill remains vendor-neutral. Worker and comment-review
briefs are bundled in `poteto-mode/references/agents`.

## Runtime mapping

| Upstream mechanism | T3 port | Review on updates |
| --- | --- | --- |
| Cursor subagents and fixed model names | `delegate_task`, `orchestrator_capabilities`, `.pstack-models.md` | Actual provider, model, option IDs, complete brief |
| Cursor orchestration and worktree scripts | Native tasks; user-requested `t3_thread_launch` with workspace binding | Exclusive writes, task IDs versus thread IDs, separate-thread authorization |
| Bundled PR polling script | Parent-owned `watch_pull_request` | Delegates cannot watch; wake is not merge authorization |
| Cursor loop and recurring automation | User-authorized `schedule_task` | Structured schedule, deduplication, stop/cleanup, inherited runtime |
| Cursor transcript files | Scoped `t3_thread_search` and `t3_thread_read` | Project scope and actual activity evidence |
| External app control recipes | Available `preview_*`, `device_*`, or a real CLI driver | Capability availability and actual behavior proof |

The [runtime contract](../skills/pstack/poteto-mode/references/t3-runtime.md) is the
common rulebook. Each skill carries and links to a generated copy, with the worker
brief and license notices required for a portable install. `bundles.json` declares
those resources; `package_skills.py build` refreshes them and validation checks
their bytes and references in the flat CLI layout. The contract overrides inherited assumptions about
tool inputs, thread ownership, and user authorization. Delegated PR workers return
state to their parent for watching. The long-running playbooks retain their gates.

Run `setup-pstack` in T3 to choose roles from live capabilities. It writes the
project's `.pstack-models.md`, or a global file when requested. Setup is optional;
unspecified roles inherit the parent model.

## Files that preserve history

| File | What it records |
| --- | --- |
| `sources.lock.json` | Latest imported Cursor pstack snapshot |
| `adaptations.lock.json` | Cursor revision used by the editable pack, plus pending merge state |
| `ports/pstack.json` | Per-file strategies, accepted source hashes, exclusions, pinned p3 provenance |
| `ports/t3-tools.json` | Tool names and definition paths at the pinned T3 revision |

The p3 commit records reference provenance. The three-way merge base remains the
original Cursor snapshot, and explicit name mappings preserve the merge relationship. Pstack's `teach`
and `tdd` install as `poteto-teach` and `poteto-tdd` to coexist with Matt's pack. This lets
future Cursor updates be compared with your T3 rewrites.

`p3-rewrite` and `p3-addition` describe initially imported p3 material; local fixes
can differ from it. `support` covers bundled briefs. For new classifications use
`native-rewrite`, `upstream-retained`, or `excluded`. The raw snapshot retains all
excluded files. Cursor bootstrap, orchestration, PR watcher, and worktree scripts
are excluded from installation, along with old Cursor help recipes. The portable
decision-log shell helper remains.

## Updating the T3 or p3 reference

For this pack, Cursor pstack is the automatic feed. Matt and shadcn have separate
source feeds. p3 and T3 are pinned references. Review
them manually after a T3 behavior change or when adopting a p3 improvement.

Refresh tool names from a clean T3 source checkout into a candidate:

```sh
python3 scripts/t3_inventory.py --reference /path/to/t3code \
  --output .work/t3-tools-candidate.json
git diff --no-index ports/t3-tools.json .work/t3-tools-candidate.json
```

Read changed schemas and implementations, update the instructions, then copy the
reviewed inventory to `ports/t3-tools.json`. It checks names, not argument shapes
or behavior. The live session's catalog is authoritative.

Compare a newer p3 reference without resetting your local work:

```sh
python3 scripts/seed_t3_port.py --reference /path/to/p3-stack \
  --destination .work/p3-candidate --manifest .work/p3-candidate-map.json
git diff --no-index skills/pstack .work/p3-candidate
```

The generator refuses existing destination and manifest paths. Its baseline
candidate includes aliases and provenance, but does not reproduce subsequent
local runtime corrections. Adopt selected changes and keep those corrections.
Record a new reference commit for material you adopt; never blindly replace the
live map. Comparison exit code 1 means differences were found.

Do not casually change the legacy `transform` function. Existing adaptation locks
need the same normalized original base. Changing it needs an explicit baseline
migration, otherwise every file can appear changed.

## Verification and license

Tests exercise selected-subtree imports, three-way merges, conflict retention,
exclusions, mapping audits, pending-port acceptance, and repeatable installation.
Codex's actual parser checks discovery. Pinned T3 source establishes the names and
restrictions used here. None of these proves live T3 behavior. Use
[the smoke checks](t3-smoke.md) to exercise changed native workflows.

The editable pack keeps both Lauren Tan's original MIT notice and Uzair Ansar's
T3 adaptation notice in [its license](../skills/pstack/LICENSE).
