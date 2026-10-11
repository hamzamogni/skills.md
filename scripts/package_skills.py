#!/usr/bin/env python3
"""Bundle shared resources and verify the flat layout used by the skills CLI."""
import argparse
import json
from pathlib import Path
import posixpath
import re

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)")


def bundle_sources(root):
    config = root / 'bundles.json'
    if not config.exists():
        return {}
    result = {}
    for pack, resources in json.loads(config.read_text()).items():
        directory = (root / pack).resolve()
        if not directory.is_relative_to((root / 'skills').resolve()):
            raise ValueError(f'Bundle pack is outside skills: {pack}')
        entries = list(directory.rglob('SKILL.md'))
        if not entries:
            raise ValueError(f'Bundle pack has no skills: {pack}')
        for source, relative in resources.items():
            original = (root / source).resolve()
            if not original.is_relative_to(root.resolve()) or not original.is_file():
                raise ValueError(f'Bundle source is missing or outside the repository: {source}')
            if Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError(f'Bundle target escapes its skill: {relative}')
            for entry in entries:
                target = entry.parent / relative
                if not target.resolve().is_relative_to(entry.parent.resolve()):
                    raise ValueError(f'Bundle target escapes its skill through a symlink: {target}')
                if target in result and result[target] != original:
                    raise ValueError(f'Conflicting bundle target: {target}')
                result[target] = original
    return result


def build(root):
    plan = {target: source.read_bytes() for target, source in bundle_sources(root).items()}
    changed = 0
    for target, data in plan.items():
        if target.exists() and target.read_bytes() == data:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        changed += 1
    return changed


def flat_link_problems(skills_root):
    exported = {}
    for entry in sorted(skills_root.rglob('SKILL.md')):
        for file in entry.parent.rglob('*'):
            if file.is_file():
                key = f'{entry.parent.name}/{file.relative_to(entry.parent).as_posix()}'
                if key in exported:
                    raise ValueError(f'Duplicate exported path: {key}')
                exported[key] = file
    problems = []
    for key, file in exported.items():
        if file.suffix != '.md':
            continue
        prose = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', file.read_text())
        for link in LINK.findall(prose):
            target = link.split('#', 1)[0]
            if not target or '://' in target or target.startswith(('mailto:', '/')) or any(s in target for s in '<>{}*'):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(key), target))
            if resolved not in exported and not any(path.startswith(resolved.rstrip('/') + '/') for path in exported):
                problems.append(f'{key}: missing installed reference {target}')
    return problems


def check(root):
    root = root.resolve()
    if not (root / 'bundles.json').exists():
        return
    problems = []
    for target, source in bundle_sources(root).items():
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            problems.append(f'Stale bundle: {target.relative_to(root)}')
        if target.name == 't3-runtime.md':
            entry = target.parent.parent / 'SKILL.md'
            if entry.is_file() and '](references/t3-runtime.md)' not in entry.read_text():
                problems.append(f'Entrypoint does not link its bundled runtime: {entry.relative_to(root)}')
    problems.extend(flat_link_problems(root / 'skills'))
    if problems:
        raise ValueError('Portable packaging failed:\n' + '\n'.join(problems) +
                         '\nReview source instructions, then run python3 scripts/package_skills.py build')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check'])
    args = parser.parse_args()
    if args.command == 'build':
        print(f'Updated {build(ROOT)} bundled resources')
    check(ROOT)
    print('Bundled resources and flat installation references are valid')


if __name__ == '__main__':
    main()
