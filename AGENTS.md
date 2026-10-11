# Working in skills.md

Edit personal skills under `skills/<name>` and pstack adaptations under
`skills/pstack/<name>`. Do not edit `upstream/` by hand. Import changes with
`python3 scripts/skills.py sync pstack` and merge them into the adapted copy with
`python3 scripts/skills.py merge pstack`.

Before committing, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/skills.py validate
```

Keep upstream copyright notices. Do not execute newly imported scripts as part
of an update check. Do not merge update PRs automatically. The T3 runtime bridge
is a first port, so verify changed skills in the actual provider before describing
them as fully supported.
