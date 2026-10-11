#!/usr/bin/env python3
"""Build a reviewable Matt Pocock T3 candidate without replacing editable skills."""
import argparse
import hashlib
from pathlib import Path

from skills import ROOT, files, read_json, transform, write_json
from porting import map_contents, original_path

EXCLUDED = {
    'in-progress/': 'Experimental upstream skills, outside the published engineering/productivity workflow',
    'misc/': 'Special-purpose and provider-specific setup skills, outside the one-pager workflow',
    'deprecated/': 'Deprecated upstream material',
}


def build(root, destination):
    if destination.exists():
        raise ValueError('Use a new candidate directory; editable skills are never reset')
    upstream = root / 'upstream/matt-pocock'
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
              'reference': {'repository': 'https://github.com/mattpocock/skills',
                            'commit': read_json(root / 'sources.lock.json')['matt-pocock']['commit']},
              'excluded_prefixes': EXCLUDED,
              'path_aliases': {'engineering/code-review/': 'engineering/matt-code-review/'},
              'skill_aliases': {'code-review': 'matt-code-review'},
              'runtime_guides': ['t3-runtime.md'], 'files': entries}
    output = map_contents(transform(selected, 'matt-pocock'), policy)
    for path, data in output.items():
        if path.endswith('.md'):
            text = data.decode()
            replacements = {
                'Call the Skill tool twice, for': 'Read and follow both installed skills',
                'call the Skill tool twice, for': 'read and follow both installed skills',
                'Call the Skill tool with': 'Read and follow the installed skill',
                'call the Skill tool with': 'read and follow the installed skill',
                'calls the Skill tool with': 'reads and follows the installed skill',
                'calling the Skill tool with': 'reading and following the installed skill',
                'call the Skill tool for': 'read and follow the installed skill instructions for',
                '`/clear`ing context': 'starting a fresh T3 session',
                '`/clear`': 'a fresh T3 session',
                '`/compact`': 'provider-supported context compaction',
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            if path.endswith('/SKILL.md'):
                parts = text.split('---', 2)
                guide = 'references/t3-runtime.md'
                text = '---' + parts[1] + '---\n\n' + f'Read the [T3 runtime contract]({guide}) before executing this skill.\n\n' + parts[2].lstrip()
            output[path] = text.encode()
            original = original_path(policy, path)
            if original in entries and output[path] != raw[original]:
                entries[original]['strategy'] = 'native-rewrite'
    output['LICENSE'] = (upstream / 'LICENSE').read_bytes()
    destination.mkdir(parents=True)
    for path, data in output.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        source_path = upstream / 'skills' / original_path(policy, path)
        if source_path.exists():
            target.chmod(source_path.stat().st_mode & 0o777)
    return policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        parser.error('Use a new manifest path')
    policy = build(ROOT, args.destination)
    write_json(args.manifest, policy)
    print(f'Built candidate at {args.destination}; review before adopting it')


if __name__ == '__main__':
    main()
