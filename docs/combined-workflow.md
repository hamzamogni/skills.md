# Use the combined workflow in T3 Code

This collection implements the workflow in your skills one-pager, using pstack,
Matt Pocock's published engineering/productivity pack, and three local helpers.
It contains 82 installed skills: 52 pstack, 27 Matt, and `matt-mode`, `code-review`,
and `deslop`. Upstream snapshots and update decisions stay separate from the
editable instructions.

## Install and set up a project

After this PR is merged, clone or pull the repository, then:

```sh
python3 scripts/skills.py install --provider codex --project /absolute/path/to/project
```

For Claude in T3, use `--provider claude`. Restart the agent session. Select skills
with `$`, or with `/` when T3's **Show skills in slash menu** setting is enabled.
Use `$code-review` or `$deslop` if a provider also offers a built-in slash command
with the same name. The guide uses slash names to match the one-pager; they are skills, not a guarantee
of provider-independent built-in commands.

Run `setup-matt-pocock-skills` once per project. It drafts your issue tracker,
triage labels, glossary and ADR layout, and asks about the choices that matter.
For a disposable smoke test, choose local Markdown so no real issue tracker is
changed. `setup-pstack` optionally configures role models from live T3 capabilities.
Missing roles inherit the parent model.

The installer links actual editable directories, so edits are visible after an
agent restart. Reinstall after adding skills or accepting an update. It migrates
only declared old symlinks owned by this checkout. It refuses unrelated links or
real directories with colliding names. Keep the checkout at the same path. If you
already installed another copy of either pack globally, inspect duplicate skill
names in T3 before using it; this installer does not manage that other copy.

## Start at the right place

| Request | Use |
| --- | --- |
| "Which Matt skill fits this?" | `ask-matt`, advice only |
| "Start Matt's flow on this task" | `matt-mode`, runs one selected phase then hands back |
| "Build and prove this change" | `poteto-mode`, selects the relevant engineering route |

`matt-mode` is a local router, not a skill from Matt's upstream repository. It
reads the chosen skill, performs that phase, and reports its result, artifact
pointers, and suggested next command. It does not automatically run the next
phase or open another conversation.

## The main road

| Stage | Skills | Result |
| --- | --- | --- |
| Sharpen the idea | `grill-with-docs`, or `grill-me` without a project | Agreed decisions, glossary and ADRs where appropriate |
| Settle a specific doubt | `prototype`, `research` | A runnable answer or cited notes |
| Write the agreed work | `to-spec`, `to-tickets` | Spec and self-contained tickets with blocking edges |
| Build with one method | `implement`/`implement-spec`, or `poteto-mode` | Tested implementation and actual behavior proof |
| Attack the result | `matt-code-review`, `interrogate`, `blast-radius`, `code-review` | Spec/standards alignment and concrete defect findings |
| Improve the environment | `retro`, `correct`, `reflect` | Proposed or task-authorized improvements to checks and guidance |

Choose one builder for a ticket. A useful mix is Matt's interview/spec/tickets,
then hand the self-contained ticket to `poteto-mode`. Another is Matt's
`implement` with Matt's TDD, followed by pstack's independent review tools.
Do not run competing builders in the same checkout.

The sheet's front-door note says to use fresh sessions at each stage, while its
footer says to keep stages 1–3 together. This setup preserves the interview through
spec and tickets, then uses fresh sessions per self-contained implementation
unit. Separate prototype or research work returns readable artifacts to the
original decision session. Provider compaction is optional and environment-specific.

## Names that intentionally differ

| Installed name | Source and purpose |
| --- | --- |
| `teach` | Matt: stateful teaching across sessions |
| `poteto-teach` | Pstack: explain code using `how` and `why` |
| `tdd` | Matt: vertical red-green-refactor development |
| `poteto-tdd` | Pstack: cheap failing-test-first bug fixes |
| `matt-code-review` | Matt: separate Standards and Spec review axes |
| `code-review` | Local helper: concrete correctness bugs and regressions |
| `deslop` | Local helper: remove proven unnecessary code in the requested diff |

The one-pager labels `code-review` and `deslop` as built in. This repository
supplies portable local helpers for those names instead of assuming every T3
provider has those commands. It does not alter provider built-ins.

Other commands in the sheet are available directly: `how`, `why`,
`diagnosing-bugs`, `benchmark-checklist`, `architect`, `arena`, `codebase-design`,
`domain-modeling`, `wayfinder`, `figure-it-out`, `swarm`, `show-me-your-work`,
`wait-what`, `bro`, `recall`, `handoff`, `pr`, `no-comments`, `unslop`,
`technical-writing`, `create-verification-skill`, `wizard`, and `triage`.

## Boundaries and project policy

Skills do not grant commits, pushes, external messages, recurring jobs, or merge
authority beyond the current task. Prepare a reviewable outcome and honor already
granted authorization. A skill can recommend a fresh session; it cannot create a
standalone thread unless the user requested one. Ordinary workers use native T3
delegation with complete briefs and explicit checkout ownership. PR watches belong
to parent ordinary threads.

The one-pager's Kitaru restriction is project-specific reference material. This
repo does not silently impose it on every project. To use that human-landing policy
in Kitaru, add it to Kitaru's own `AGENTS.md` or `CLAUDE.md`: do not use Shipping or
Autopilot-full, and hand every PR to a human. No skill overrides that project rule.
This collection's upstream update PRs always require your decision and never
merge themselves.

## What Matt material is included

The raw snapshot tracks the whole upstream `skills/` directory and root `LICENSE`
at commit `49dd158d1076134a641b33efb035946536778336`. The installed pack includes
`engineering/` and `productivity/`. Experimental `in-progress/`, special-purpose
`misc/`, and deprecated material stay raw-only with explicit exclusions in
`ports/matt-pocock.json`. They are still visible in update reports. To adopt one
later, remove its directory exclusion, port it, classify its files, validate, and
reinstall. This does not install Matt's marketplace plugin or its upstream auto-updater.

The snapshot omits Matt's development configuration, package files, and repository
README. Changes to those do not produce update PRs. Skill and license changes do.
The selected-content lock uses a SHA-256 fingerprint of Git entries, while pstack
keeps its existing Git subtree hash. Both compare content, not unrelated commits.

## Maintain it yourself

Read [the update guide](upstream-updates.md). Use source name `matt-pocock` for
Matt's pack and `pstack` for poteto's. Each source gets its own six-hour check,
review-request PR, pending-port acceptance, and per-file map. The watcher becomes
active for Matt after this feature PR is merged into main.

Adapted paths can differ from upstream paths. `ports/<source>.json` stores explicit
`path_aliases` and `skill_aliases`; both merge inputs pass through the same name
mapping. Keep source map keys upstream-relative. Do not rename files without
updating this mapping and checking all callers. Reports show the adapted path.

For a candidate baseline of Matt's current imported snapshot:

```sh
python3 scripts/seed_matt_port.py --destination .work/matt-candidate-new \
  --manifest .work/matt-candidate-map-new.json
git diff --no-index skills/matt-pocock .work/matt-candidate-new
```

This generator refuses existing outputs. It applies baseline aliases, discovery
metadata, and native skill-loading guidance. It does not reproduce later manual
workflow corrections or the local runtime guide. Adopt selected improvements;
never overwrite the live pack or map blindly. A diff exit code of 1 is normal.

## Check the actual T3 behavior

The repository suite checks imports, alias-aware merges, exclusions, independent
source PRs, collision-safe installation, and pending acceptance. Run `python3 scripts/check_discovery.py` to check the installed collection with
Codex's actual parser. It starts no model turn and uses an isolated Codex home.
Codex's real parser can discover all 82 skills. Those checks do not prove live T3 execution.

Use [the T3 smoke guide](t3-smoke.md), and also check:

1. `ask-matt` recommends without running the phase; `matt-mode` executes one phase
   and stops with actual results and next-step pointers.
2. Matt's TDD and teaching route to `tdd`/`teach`; pstack calls resolve to
   `poteto-tdd`/`poteto-teach`. Standards/spec review reaches `matt-code-review`.
3. With local tracker setup, write a small agreed spec and two dependent tickets.
   Verify the interview decisions survive and the second ticket remains blocked
   until its dependency is implemented and verified.
4. Exercise `implement-spec` on disposable checkouts. Confirm explicit cwd, one
   integration writer, task IDs, current review evidence, and human PR handback.
   A worker failure must not unblock dependent tickets or close a landed-work issue.
