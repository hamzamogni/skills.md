# Review and merge an update

1. Check out the update PR in this repository:

   ```sh
   gh pr checkout <number>
   ```

2. Review its diff. The workflow updates only `upstream/<source>` and the import
   lock file. The upstream comparison link may include unrelated folders, while
   the PR diff contains only pstack.

3. Merge the new snapshot into your editable skills:

   ```sh
   python3 scripts/skills.py merge pstack
   ```

   The command downloads the adaptation's pinned upstream revision as the base.
   It compares that base with your skills and the new imported snapshot. It keeps
   local additions, carries non-conflicting upstream changes, and reports overlaps.
   Run it again without further snapshot changes and it makes no changes.

4. If there are conflicts, edit the affected files in `skills/pstack`. Text
   conflicts contain Git's diff3 markers. For add/add, edit/delete, and binary
   conflicts, inspect `.sync-conflicts/pstack/{base,ours,upstream}` and explicitly
   choose the result. A missing version means that side deleted the file.
   Files with binary or deletion conflicts retain your local choice initially.

   After resolving every listed conflict, accept your choices:

   ```sh
   python3 scripts/skills.py merge pstack --continue
   ```

   This command removes the conflict artifacts and confirms the new adaptation
   base. It checks for remaining text markers; you are responsible for choosing
   binary and deletion resolutions before continuing.

5. Validate the adapted pack and try changed skills with your T3 Code provider:

   ```sh
   python3 scripts/skills.py validate
   python3 -m unittest discover -s tests -v
   git diff
   ```

6. Commit and push your adaptations to the PR branch. Merge the PR when ready.
   To keep the updated upstream snapshot while deferring the port, merge the
   snapshot PR without running `merge`. The adaptation lock retains the older
   base, so you can merge all accumulated upstream changes later.

To discard a local merge attempt, restore `skills/pstack` and
`adaptations.lock.json` from Git, then remove the generated
`.sync-conflicts/pstack` folder. Keep any earlier uncommitted edits before restoring.

To check locally without creating a PR:

```sh
python3 scripts/skills.py sync pstack
git diff --stat
```

The importer compares the subtree hash, rather than the full repository's latest
commit. An unrelated upstream commit leaves the lock and your files unchanged.
The PR workflow does not execute downloaded upstream scripts. Keep the imported
snapshot unedited so its provenance and later merge bases remain accurate.

The built-in Actions token does not trigger another Actions run when it creates
a PR. The importer tests run before the scheduled import. After committing your
adaptations, your push runs PR validation, or run **Validate skills** manually on
the PR branch. This is why automatic merging is disabled.
