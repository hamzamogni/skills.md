# Review and merge an update

GitHub Actions checks only `cursor/plugins/pstack` every six hours. A changed
subtree opens one review-request PR. It updates the raw snapshot and its lock,
leaving your editable skills alone. It never auto-merges. Email depends on your
GitHub review-request notification settings. Run **Actions → Check upstream
skills → Run workflow** for an immediate check.

You can perform these steps yourself or ask an agent to help. Start with a clean
checkout, or commit your current edits first.

## 1. Read what changed

From the skills.md checkout:

```sh
gh pr checkout <number>
python3 scripts/skills.py report pstack --diff
```

Read `.work/pstack-update.md` and `.work/pstack-upstream.diff`. The report lists
changed, added, deleted, and excluded files since the last accepted port. The diff
shows the original upstream changes since your adaptation base, including updates
you deferred. These reports are local and ignored by Git. Inspect the PR diff for
README and license changes too; the report covers the upstream `skills` directory.

The upstream comparison link can include other Cursor plugins; this PR imports
only pstack. Do not edit `upstream/pstack` or execute its downloaded scripts.

## 2. Apply the text merge

```sh
python3 scripts/skills.py merge pstack
```

The command compares the pinned original upstream base, your editable skills,
and the new raw snapshot. It preserves local additions and tries Git's three-way
merge. Deep rewrites often conflict because T3 differs substantially from Cursor.
Excluded Cursor scripts stay excluded.

Finish or discard a pending merge before importing another snapshot. Acceptance rejects a raw snapshot that advanced after the merge began.

The port remains pending even with zero conflicts. A clean text merge cannot
decide whether an upstream instruction still makes sense in T3.

Resolve text markers in `skills/pstack`. For binary, add/add, or edit/delete
conflicts, inspect `.sync-conflicts/pstack/{base,ours,upstream}`. A missing version
means that side deleted the file. The command initially keeps your local binary
or deletion choice; explicitly choose whether to retain, replace, or delete it.
When a native rewrite conflicts, keep its T3 mechanics and port the upstream
intent. Do not choose the entire upstream file just to clear markers.

## 3. Review meaning and map new files

Read every changed instruction and its bundled references. Use the mappings in
[the port guide](t3-port.md). Watch for:

- Changed tool schemas, even when a tool name stays the same.
- Model roles, provider instance IDs, and advertised effort options. Missing
  roles inherit the parent; configuration aliases are not API values.
- Self-contained worker briefs and parent-owned PR watches. Standalone threads
  require the user's request and an explicit workspace binding.
- Scheduling, messaging, and merge authorization. A watch wake is information,
  not permission to merge.
- New files that need a port, and deletions that leave broken links. Renames
  behave as add/delete, so inspect both paths and transfer local edits yourself.
- License changes and useful behavior hidden in excluded Cursor scripts. Carry
  new notices into the editable pack manually, preserving the existing p3 notice;
  the skill-file merge does not merge the top-level license.

For a new file, edit its T3 version, then classify the upstream-relative path:

```sh
python3 scripts/skills.py classify pstack new-skill/SKILL.md \
  --strategy native-rewrite --reason "Uses native T3 delegation and parent-owned PR watches"
```

Use `upstream-retained` for vendor-neutral content, or `excluded` when it should
not be installed. For an exclusion, remove the copied file from `skills/pstack`
yourself. Classification records your decision; it does not edit or delete files.
Keep existing filenames stable when possible. Mapping does not automatically
relocate local edits between renamed files.

## 4. Accept, verify, and publish

Only after resolving conflicts and reviewing native behavior:

```sh
python3 scripts/skills.py merge pstack --continue
python3 scripts/skills.py validate
python3 -m unittest discover -s tests -v
git diff
```

`--continue` rejects unresolved markers, unmapped files, known Cursor remnants,
excluded files reintroduced into the pack, unknown pinned tool names, and broken
local Markdown links. It records the accepted hashes and clears pending state.
It does not run T3 or certify that the wording is correct.

Restart your T3 session and exercise changed workflows using the
[smoke-check guide](t3-smoke.md). After further edits, validate again. Commit the
editable pack, map, and adaptation lock together on the incoming PR branch:

```sh
git add skills/pstack ports/pstack.json adaptations.lock.json
git commit -m "Port the pstack upstream update to T3"
git push
```

Review the entire final diff and merge the PR when ready. Your push runs PR
validation. The Actions token's initial PR creation does not trigger another
Actions run, so a raw-only PR may have no new validation run. You can dispatch
**Validate skills** manually on its branch.

## Defer, retry, or check locally

To defer porting, merge the raw-only PR without running `merge`. The adaptation
lock keeps its older base and the map keeps the last accepted hashes. Later
reports and merges cover the accumulated updates.

To discard an uncommitted merge attempt, preserve earlier personal edits,
restore `skills/pstack`, `ports/pstack.json`, and `adaptations.lock.json` from Git,
then remove `.sync-conflicts/pstack`. Inspect untracked new files separately;
`git restore` does not remove them. Avoid broad clean commands over your skills.
Generated `.work` reports can be deleted and regenerated.

For a local check without a PR:

```sh
python3 scripts/skills.py sync pstack
python3 scripts/skills.py report pstack --diff
```

The importer compares subtree hashes. Changes elsewhere in Cursor leave the
snapshot and lock unchanged. A pending PR pauses new automatic proposals until
you close or merge it. Closing without accepting the snapshot can cause the same
update to be proposed again.
