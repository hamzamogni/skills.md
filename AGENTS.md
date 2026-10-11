# Working in skills.md

Edit personal skills under `skills/<name>`, pstack under `skills/pstack/<name>`,
and Matt's pack under `skills/matt-pocock/{engineering,productivity}/<name>`.
Read `docs/combined-workflow.md` for the one-pager names and local helpers. Do not edit `upstream/` by hand. Import changes with
`python3 scripts/skills.py sync pstack` and merge them into the adapted copy with
`python3 scripts/skills.py merge pstack`. Read `docs/upstream-updates.md` and
`docs/t3-port.md` before porting an update. Generate `report pstack --diff`, review
native mappings, then run `merge pstack --continue` even after a clean text merge.
Use `matt-pocock` in place of `pstack` for Matt's updates. Commit the editable
pack, map, and adaptation lock together. Keep original upstream paths in map keys;
explicit path aliases preserve merges after an installed-name migration.

Deliver repository changes through a PR. Do not push directly to main or merge
update PRs on the user's behalf unless they explicitly change that instruction.

Before committing, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/skills.py validate
```

Keep upstream copyright notices. Do not execute newly imported scripts as part
of an update check. Do not merge update PRs automatically. Keep native runtime
corrections when adopting p3 reference changes. Verify changed skills in the
actual T3 provider before claiming live runtime support.
