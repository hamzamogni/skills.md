#!/usr/bin/env python3
"""Open one review request per source; never merge or edit adapted skills."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from skills import ROOT, read_json, snapshot, source
from porting import manifest


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    for name in read_json(ROOT / "sources.json"):
        config = source(ROOT, name)
        branch = f"sync/{name}"
        existing = json.loads(command("gh", "pr", "list", "--repo", repository,
                                      "--head", branch, "--state", "open", "--json", "number"))
        if existing:
            print(f"{name}: review pending on PR #{existing[0]['number']}; leaving it unchanged")
            continue
        previous = read_json(ROOT / "sources.lock.json").get(name, {})
        if not snapshot(ROOT, name):
            continue
        # Only the reviewed importer runs. No code from the downloaded pack is executed.
        command("git", "checkout", "-B", branch)
        command("git", "add", f"upstream/{name}", "sources.lock.json")
        revision = read_json(ROOT / "sources.lock.json")[name]
        title = f"chore: update {name} upstream to {revision['tree'][:10]}"
        command("git", "-c", "user.name=github-actions[bot]",
                "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
                "commit", "-m", title)
        # This dedicated branch is bot-owned. Refuse to overwrite a concurrent update.
        remote = command("git", "ls-remote", "origin", f"refs/heads/{branch}")
        lease = remote.split()[0] if remote else ""
        command("git", "push", f"--force-with-lease=refs/heads/{branch}:{lease}", "origin", branch)
        url = config["web_url"]
        old = previous.get("commit", revision["commit"])
        if manifest(ROOT, name) is not None:
            steps = f'''python3 scripts/skills.py report {name} --diff
python3 scripts/skills.py merge {name}
# Resolve conflicts and review native T3 behavior, even after a clean text merge.
python3 scripts/skills.py merge {name} --continue
python3 scripts/skills.py validate'''
        else:
            steps = f'''python3 scripts/skills.py merge {name}
# If conflicts were reported, resolve them and run merge {name} --continue.
python3 scripts/skills.py validate'''
        body = f'''The upstream `{config['path']}` folder changed. This PR imports only that folder.

[Upstream changes]({url}/compare/{old}...{revision['commit']}) · [Updated folder]({url}/tree/{revision['commit']}/{config['path']})

Your editable `skills/{name}` copy is unchanged. To bring these changes into it, check out this PR and run:

```sh
{steps}
```

Review and commit any adaptation changes on this branch, then merge this PR when ready.
See `docs/upstream-updates.md` for the maintenance procedure and what to watch for.
The comparison link includes other upstream folders; this PR's diff contains only the selected folder.
'''
        with tempfile.TemporaryDirectory() as temporary:
            body_file = Path(temporary) / "body.md"
            body_file.write_text(body)
            args = ["gh", "pr", "create", "--repo", repository, "--base", "main",
                    "--head", branch, "--title", title, "--body-file", str(body_file)]
            if config.get("reviewer"):
                args.extend(["--reviewer", config["reviewer"]])
            print(command(*args))
        command("git", "checkout", "main")


if __name__ == "__main__":
    main()
