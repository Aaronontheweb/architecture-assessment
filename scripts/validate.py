#!/usr/bin/env python3
"""Validate the two-skill package and repository-relative Markdown links."""
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'architecture-assessment', 'simplify'}
REPOSITORY = 'https://github.com/Aaronontheweb/architecture-assessment'


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
    codex = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
    marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
    check(claude['name'] == codex['name'] == marketplace['name'] == 'architecture-assessment', 'Package names differ')
    check(claude['version'] == codex['version'] == marketplace['plugins'][0]['version'], 'Package versions differ')
    check(re.fullmatch(r'\d+\.\d+\.\d+', codex['version']), 'Expected release version')
    check(claude['repository'] == codex['repository'] == REPOSITORY, 'Repository metadata differs')
    check(codex['skills'] == './skills/', 'Incorrect Codex discovery path')
    check(set(claude['skills']) == {'./skills/' + s for s in EXPECTED}, 'Incorrect Claude skill list')
    check(marketplace['plugins'][0]['source'] == './', 'Incorrect marketplace root')
    check({p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()} == EXPECTED, 'Unexpected skill directories')
    check((ROOT / 'CLAUDE.md').is_symlink() and (ROOT / 'CLAUDE.md').resolve() == ROOT / 'AGENTS.md', 'Agent guidance symlink differs')
    for name in EXPECTED:
        body = (ROOT / 'skills' / name / 'SKILL.md').read_text()
        check(body.startswith('---\n'), f'{name}: missing frontmatter')
        frontmatter = body.split('---', 2)[1]
        check(f'name: {name}\n' in frontmatter, f'{name}: mismatched skill name')
        check(re.search(r'^description: .+', frontmatter, re.M), f'{name}: missing description')
    links = 0
    for path in ROOT.rglob('*.md'):
        if any(part.startswith('.') for part in path.relative_to(ROOT).parts):
            continue
        for destination in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
            url = urlsplit(destination)
            if url.scheme or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            check(target.is_relative_to(ROOT) and target.exists(), f'{path.relative_to(ROOT)}: missing or external local link {destination}')
            links += 1
    print(f'Package valid: two skills, version {codex["version"]}, {links} local file links.')


if __name__ == '__main__':
    main()
