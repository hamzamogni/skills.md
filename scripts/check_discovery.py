#!/usr/bin/env python3
"""Check the installed collection with Codex's real parser, without a model turn."""
import json
import os
from pathlib import Path
from queue import Queue, Empty
import subprocess
import tempfile
from threading import Thread
import time

from skills import ROOT, install


def main():
    expected_paths = {path.parent.name: path.resolve() for path in (ROOT / 'skills').rglob('SKILL.md')}
    expected = set(expected_paths)
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary)
        project = scratch / 'project'
        project.mkdir()
        install(ROOT, project, 'codex')
        codex_home = scratch / 'codex-home'
        codex_home.mkdir()
        env = {**os.environ, 'CODEX_HOME': str(codex_home)}
        with (scratch / 'stderr').open('w') as errors:
            proc = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=errors, text=True,
                                    env=env, cwd=project)
            messages = Queue()
            def read():
                for line in proc.stdout:
                    messages.put(line)
                messages.put(None)
            reader = Thread(target=read, daemon=True)
            reader.start()
            def send(value):
                proc.stdin.write(json.dumps(value) + '\n')
                proc.stdin.flush()
            def response(request_id):
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    try:
                        line = messages.get(timeout=max(0, deadline - time.monotonic()))
                    except Empty:
                        break
                    if line is None:
                        raise RuntimeError('Codex stopped before replying: ' + (scratch / 'stderr').read_text())
                    value = json.loads(line)
                    if value.get('id') == request_id:
                        if 'error' in value:
                            raise RuntimeError(value['error'])
                        return value['result']
                raise TimeoutError('Codex parser did not reply')
            try:
                send({'id': 1, 'method': 'initialize', 'params': {
                    'clientInfo': {'name': 'skills-discovery-check', 'version': '1.0'}}})
                response(1)
                send({'method': 'initialized', 'params': {}})
                send({'id': 2, 'method': 'skills/list', 'params': {
                    'cwds': [str(project)], 'forceReload': True}})
                result = response(2)
                discovered = {skill['name'] for entry in result['data'] for skill in entry['skills']}
                correct_paths = {skill['name'] for entry in result['data'] for skill in entry['skills']
                                 if skill['name'] in expected_paths and Path(skill['path']).resolve() == expected_paths[skill['name']]}
                failures = [error for entry in result['data'] for error in entry.get('errors', [])]
                if failures or expected - discovered or expected - correct_paths:
                    raise RuntimeError(f'Parser errors: {failures}; missing collection paths: {sorted(expected - correct_paths)}')
                output = ROOT / '.work/codex-discovery.json'
                output.parent.mkdir(exist_ok=True)
                output.write_text(json.dumps(result, indent=2) + '\n')
                print(f'Codex discovered all {len(expected)} collection skills without parsing errors. Saved {output}')
                duplicates = sorted({skill['name'] for entry in result['data'] for skill in entry['skills']
                                     if skill['name'] in expected_paths and Path(skill['path']).resolve() != expected_paths[skill['name']]})
                if duplicates:
                    print('Other installations also expose these names; select the project collection paths: ' + ', '.join(duplicates))
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                reader.join(timeout=5)
                proc.stdin.close()
                proc.stdout.close()


if __name__ == '__main__':
    main()
