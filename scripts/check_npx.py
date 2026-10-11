#!/usr/bin/env python3
"""Install the full collection with the real skills CLI in disposable projects."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from package_skills import flat_link_problems
from skills import ROOT, files, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli-version', default='latest')
    parser.add_argument('--source', default=str(ROOT), help='Defaults to this checkout; use a GitHub branch URL to check publication')
    parser.add_argument('--codex-parser', action='store_true', help='Also check the Codex installation with the local app-server parser')
    args = parser.parse_args()
    validate(ROOT)
    expected = {entry.parent.name: files(entry.parent) for entry in (ROOT / 'skills').rglob('SKILL.md')}
    evidence = ROOT / '.work/npx-check'
    evidence.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'npm_config_cache': str(ROOT / '.work/npm-cache'),
           'DISABLE_TELEMETRY': '1', 'DO_NOT_TRACK': '1', 'NODE_DISABLE_COMPILE_CACHE': '1'}
    with tempfile.TemporaryDirectory() as temporary:
        cases = [('codex', 'codex', '.agents/skills', False),
                 ('claude-code', 'claude-code', '.claude/skills', False),
                 ('codex-migration', 'codex', '.agents/skills', True)]
        for label, agent, location, migrate in cases:
            project = Path(temporary) / label
            project.mkdir()
            if migrate:
                old = Path(temporary) / 'old-checkout/skills'
                shutil.copytree(ROOT / 'skills', old)
                before = files(old)
                destination = project / location
                destination.mkdir(parents=True)
                for entry in old.rglob('SKILL.md'):
                    (destination / entry.parent.name).symlink_to(entry.parent.resolve(), target_is_directory=True)
            command = ['npx', '--yes', f'skills@{args.cli_version}', 'add', args.source,
                       '--skill', '*', '--agent', agent, '--yes']
            result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=180)
            (evidence / f'{label}.log').write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f'{label}: CLI failed; see {evidence / (label + ".log")}')
            installed = project / location
            actual = {path.name: files(path) for path in installed.iterdir() if (path / 'SKILL.md').is_file()}
            if actual != expected:
                changed = sorted(name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name))
                raise RuntimeError(f'{agent}: installed files differ for {changed}')
            if any(not path.resolve().is_relative_to(project.resolve()) for path in installed.iterdir()):
                raise RuntimeError(f'{label}: installed files still depend on a source checkout')
            if migrate and files(old) != before:
                raise RuntimeError('Replacing old installation links modified their source checkout')
            problems = flat_link_problems(installed)
            if problems:
                raise RuntimeError('\n'.join(problems))
            lock = json.loads((project / 'skills-lock.json').read_text())
            if set(lock['skills']) != set(expected):
                raise RuntimeError(f'{agent}: installed collection is not fully tracked for updates')
            if args.codex_parser and label == 'codex':
                subprocess.run([sys.executable, str(ROOT / 'scripts/check_discovery.py'),
                                '--project', str(project), '--output', str(evidence / 'codex-discovery.json')], check=True)
            print(f'{label}: {len(actual)} skills, all files byte-exact, bundled resources and links present, update lock complete')
    print(f'Saved CLI evidence in {evidence}; disposable installations removed')


if __name__ == '__main__':
    main()
