#!/usr/bin/env python3
"""Build a reviewable shadcn T3 candidate without replacing editable skills."""
import argparse
import hashlib
from pathlib import Path
import re

from skills import ROOT, files, read_json, transform, write_json
from porting import map_contents

EXCLUDED = {'shadcn/evals/': 'Upstream evaluation fixtures, tracked but not installed'}


def build(root, destination):
    if destination.exists():
        raise ValueError('Use a new candidate directory; editable skills are never reset')
    upstream = root / 'upstream/shadcn-ui'
    raw = files(upstream / 'skills')
    entries, selected = {}, {}
    for path, data in raw.items():
        reason = next((reason for prefix, reason in EXCLUDED.items() if path.startswith(prefix)), None)
        entries[path] = {'strategy': 'excluded' if reason else 'upstream-retained',
                         'upstream_sha256': hashlib.sha256(data).hexdigest()}
        if reason:
            entries[path]['reason'] = reason
        else:
            selected[path] = data
    policy = {'schema_version': 1,
              'reference': {'repository': 'https://github.com/shadcn-ui/ui',
                            'commit': read_json(root / 'sources.lock.json')['shadcn-ui']['commit']},
              'excluded_prefixes': EXCLUDED,
              'path_aliases': {'shadcn/agents/openai.yml': 'shadcn/agents/openai.yaml'},
              'license_sha256': hashlib.sha256((upstream / 'LICENSE.md').read_bytes()).hexdigest(),
              'runtime_guides': ['shadcn/references/t3-runtime.md'], 'files': entries}
    output = transform(selected, 'shadcn-ui')
    entry = output['shadcn/SKILL.md'].decode()
    entry = re.sub(r'(?m)^allowed-tools:.*\n', '', entry)
    entry = re.sub(r'(?m)^user-invocable:.*\n', '', entry)
    entry = entry.replace('# shadcn/ui', 'Read the [T3 runtime contract](references/t3-runtime.md) before executing this skill.\n\n# shadcn/ui', 1)
    entry = entry.replace('```json\n!`npx shadcn@latest info --json`\n```',
                          'Run `npx shadcn@latest info --json` through the session\'s command tool in the project cwd.\nUse the project\'s package runner when known. Read its output before choosing APIs or file paths.\nIf the project is not initialized, follow the greenfield setup in the runtime contract first.')
    entry = entry.replace('The JSON above contains', 'The command output contains')
    entry = entry.replace('The injected project context contains', 'The inspected project context contains')
    for old, new in {'`aliases`': '`config.aliases`', '`isRSC`': '`project.rsc` or `config.rsc`',
                     '`tailwindVersion`': '`project.tailwindVersion`',
                     '`tailwindCssFile`': '`config.resolvedPaths.tailwindCss`',
                     '`style`': '`config.style`', '`base`': '`config.base`',
                     '`iconLibrary`': '`config.iconLibrary`', '`resolvedPaths`': '`config.resolvedPaths`',
                     '`framework`': '`project.framework`'}.items():
        entry = entry.replace(f'**{old}**', f'**{new}**')
    entry = entry.replace('Check `base` field from', 'Check `config.base` from')
    entry = entry.replace('**`packageManager`** → use this for any non-shadcn dependency installs',
                          '**Project package manager** → read `package.json` and the lockfile; use the result for non-shadcn dependency installs')
    entry = entry.replace('**Get project context** — already injected above. Run `npx shadcn@latest info` again if you need to refresh.',
                          '**Get project context** — run `npx shadcn@latest info --json` in the project cwd. Refresh after configuration changes.')
    entry = entry.replace('Without a preset code, pick the closest style and pass `--base base --preset <style>`. Then `add --all -y`.',
                          'For a new design-system showcase, agree on the base and style before initialization. For an existing project, preserve its configured base and follow its customization workflow. Use `add --all` only when the requested showcase needs the full catalog.')
    entry = entry.replace('User says "just update everything" → use `--overwrite`, but confirm first.',
                          'User explicitly authorizes overwriting everything → use `--overwrite` within that scope.')
    output['shadcn/SKILL.md'] = entry.encode()
    cli = output['shadcn/cli.md'].decode()
    cli = cli.replace("Check `packageManager` from project context to choose the right one.",
                      "Read the project's package.json and lockfile to choose the right one.")
    cli = cli.replace("Only use the flags documented below. Do not invent or guess flags — if a flag isn't listed here, it doesn't exist.",
                      "Use documented flags and the installed CLI's `--help`. Do not invent flags. Live help is authoritative when this reference differs.")
    cli = cli.replace('**Project Info fields:**',
                      '**Project Info fields:**\n\nThe current JSON nests project data under `project` and configuration under `config`.\nLegacy labels below can differ from returned JSON names: `isSrcDir` is `project.srcDirectory`,\n`isRSC` is `project.rsc`, `isTsx` is `project.typescript`, and `tailwindCssFile` is\n`config.resolvedPaths.tailwindCss`. Read actual output. Determine the package manager\nfrom the project manifest and lockfile when it is absent from the output.\n')
    output['shadcn/cli.md'] = cli.encode()
    mcp = output['shadcn/mcp.md'].decode()
    start, end = mcp.index('## Setup'), mcp.index('## Tools')
    mcp = mcp[:start] + '''## T3 setup

MCP is optional. Use the CLI when the current T3 provider does not expose a
connected shadcn MCP server. Inspect the session's actual tool schemas before
using MCP tools. The reference names below describe upstream capabilities.
This skill does not install an MCP server or write provider configuration.
Configure a connection separately when requested, using the provider's current docs.
Run project inspection through the CLI even when MCP is available.

''' + mcp[end:]
    output['shadcn/mcp.md'] = mcp.encode()
    output['shadcn/agents/openai.yml'] = output['shadcn/agents/openai.yml'].replace(
        b'Manages shadcn/ui components \xe2\x80\x94 adding, searching, fixing, debugging, styling, and composing UI.',
        b'Build and customize shadcn/ui components')
    for path, data in output.items():
        if data != raw[path]:
            entries[path]['strategy'] = 'native-rewrite'
    output = map_contents(output, policy)
    output['LICENSE'] = (upstream / 'LICENSE.md').read_bytes()
    destination.mkdir(parents=True)
    for path, data in output.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        parser.error('Use a new manifest path')
    write_json(args.manifest, build(ROOT, args.destination))
    print(f'Built candidate at {args.destination}; review before adopting it')


if __name__ == '__main__':
    main()
