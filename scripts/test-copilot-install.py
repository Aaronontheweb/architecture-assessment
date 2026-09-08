#!/usr/bin/env python3
"""Test marketplace install/discovery without a model call or user config changes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'architecture-assessment', 'architectural-principles', 'simplify'}


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--copilot', type=Path, required=True, help='Path to the Copilot CLI executable')
    parser.add_argument('--source', default=str(ROOT), help='Marketplace path or owner/repo; default tests this checkout')
    args = parser.parse_args()
    executable = str(args.copilot.resolve())
    with tempfile.TemporaryDirectory(prefix='assessment-copilot-') as directory:
        working = Path(directory)
        config = working / 'config'
        environment = dict(os.environ, COPILOT_HOME=str(config), COPILOT_CACHE_HOME=str(working / 'cache'))

        def run(*arguments):
            return subprocess.check_output([executable, *arguments], cwd=working,
                                           env=environment, text=True, timeout=120)

        print(run('plugin', 'marketplace', 'add', args.source))
        print(run('plugin', 'install', 'architecture-assessment@architecture-assessment'))
        discovered = json.loads(run('skill', 'list', '--json'))
        skills = [s for s in discovered if s['name'] in NAMES]
        check(len(skills) == len(NAMES) and {s['name'] for s in skills} == NAMES,
              'All bundled skills must be discovered exactly once')
        files = 0
        for skill in skills:
            check(skill['enabled'] and skill['source'] == 'plugin', 'Expected an enabled plugin skill')
            installed = Path(skill['path'])
            # Compare the complete tracked resource set, excluding locally generated caches.
            tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z',
                                               f'skills/{skill["name"]}']).decode().split('\0')
            for relative in filter(None, tracked):
                source = ROOT / relative
                target = installed / source.relative_to(ROOT / 'skills' / skill['name'])
                check(target.is_file() and target.read_bytes() == source.read_bytes(), f'Resource missing or changed: {relative}')
                files += 1
        simplify = Path(next(s['path'] for s in skills if s['name'] == 'simplify'))
        shared = simplify.parent / 'architecture-assessment/references/csharp.md'
        check(shared.is_file(), 'Sibling evidence reference must remain reachable')
        principles = Path(next(s['path'] for s in skills if s['name'] == 'architectural-principles'))
        check((simplify.parent / 'architectural-principles').resolve() == principles.resolve(),
              'Design guidance must remain adjacent to the other skills')
        check((principles / 'references/csharp.md').is_file(), 'Principles implementation flavor is missing')
        print(f'PASS: Copilot discovers {len(NAMES)} enabled skills; {files} tracked resources match; shared references resolve.')
        print('No model execution, target analysis, or IDE/cloud-agent validation was performed.')


if __name__ == '__main__':
    main()
