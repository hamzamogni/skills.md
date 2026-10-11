# skills.md

My skills and adapted skill packs, with reviewable updates from other authors.
The first pack is [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack).
Only the `pstack` folder is imported from `cursor/plugins`.

## Use the skills in T3 Code

Clone this repository on the machine running your T3 Code agent:

```sh
gh repo clone hamzamogni/skills.md
cd skills.md
python3 scripts/skills.py install --provider codex --project /absolute/path/to/your-project
```

For Claude, use `--provider claude`. Restart the agent session in T3 Code, then
select `$poteto-mode`. The installer creates links in the project's `.agents/skills`
for Codex or `.claude/skills` for Claude. Keep this checkout at the same path.
Existing skills with the same name are preserved and cause installation to stop.
Re-running installation adds missing links and leaves matching links alone.

The pack keeps all 52 upstream skill names and builds on
[p3-stack's native T3 port](https://github.com/uzairansaruzi/p3-stack).
Delegation, model roles, PR watches, scheduling, history, and runtime proof use
T3 instructions. Cursor scripts stay in the raw snapshot and are excluded from
installation. Start with `setup-pstack` to choose model roles, or let unspecified
roles inherit your parent model.

Read [the port and tool mapping](docs/t3-port.md) and the
[T3 runtime contract](skills/pstack/poteto-mode/references/t3-runtime.md).
Static checks and skill discovery do not establish live T3 behavior; use the
[smoke checks](docs/t3-smoke.md) when changing native workflows.

See T3 Code's [composer docs](https://github.com/pingdotgg/t3code/blob/main/docs/user/composer.md)
and [Claude skill discovery](https://github.com/pingdotgg/t3code/blob/main/docs/user/providers-claude.md#skills).

## Make it yours

Edit `skills/pstack/<skill>/SKILL.md` to adapt an imported skill. Create personal
skills at `skills/<your-skill>/SKILL.md`, with `name` and `description` frontmatter.
The install command includes both personal skills and imported packs.
Skill names must be unique across the installed collection.

Run `python3 scripts/skills.py validate` after edits.

## Review upstream updates

GitHub Actions checks pstack every six hours, at minute 23 UTC. A changed pstack
tree creates a pull request requesting `hamzamogni`'s review. GitHub delivers the
review notification through your account's web, mobile, and email settings.
Enable review-request notifications in [GitHub notification settings](https://github.com/settings/notifications)
if you want email. A notification is requested; email delivery depends on those settings.

The workflow opens one pull request per source at a time. It waits for your review
before proposing further updates. It never merges a PR or changes your editable
skills. Changes elsewhere in `cursor/plugins` do not create update PRs.
Use **Actions → Check upstream skills → Run workflow** for an immediate check.
Scheduled runs can be delayed by GitHub. Inactive public repositories can have
schedules disabled; this repository starts private.

For the merge steps, read [Review and merge an update](docs/upstream-updates.md).
The workflow uses `GITHUB_TOKEN`; no personal token is required. The repository
must allow Actions to create pull requests in **Settings → Actions → General →
Workflow permissions**. That setting is enabled during initial setup.

## Repository layout

| Path | Purpose |
| --- | --- |
| `skills/` | Editable pstack adaptations and personal skills |
| `upstream/pstack/` | Unmodified upstream snapshot, including its MIT license |
| `sources.json` | Repository, branch, subtree, and reviewer for each source |
| `sources.lock.json` | Commit and subtree hash of each imported snapshot |
| `adaptations.lock.json` | Upstream revision used as each adaptation's merge base |
| `ports/` | File mappings, accepted source hashes, and pinned T3 tool inventory |
| `scripts/` | Import, three-way merge, validation, installation, and PR creation |

Python 3.10 or newer and Git are required. Automated PR creation also uses GitHub
CLI, which is available on GitHub's Ubuntu runners. Run the behavior tests with
`python3 -m unittest discover -s tests -v`.

Additional authors can be added to `sources.json` with a separate source name and
an explicit subtree. Source packs must include a license. Import with
`python3 scripts/skills.py init <source>` to create its snapshot, editable copy,
and merge base. The first T3 port is specific to pstack;
other packs need their own runtime adaptation.

Imported pstack material is copyright 2026 Lauren Tan and licensed under
[MIT](upstream/pstack/LICENSE). The editable pack retains her notice and Uzair
Ansar's T3 adaptation notice in [its license](skills/pstack/LICENSE).
Original code and documentation in this repository are reserved to the author
unless a separate license is added.
