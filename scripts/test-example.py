#!/usr/bin/env python3
"""Run the documented example on synthetic source in an isolated Git snapshot."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'skills/architecture-assessment/scripts'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csharp-dll', type=Path, required=True)
    args = parser.parse_args()
    baseline = module('baseline', TOOLS / 'repository_baseline.py')
    catalog = module('catalog', TOOLS / 'architecture_catalog.py')
    with tempfile.TemporaryDirectory(prefix='architecture-example-') as directory:
        output = Path(directory)
        target = output / 'source'
        shutil.copytree(ROOT / 'examples/source', target)

        def git(*arguments):
            return subprocess.check_output(['git', '-C', str(target), *arguments]).decode().strip()

        git('init', '-q')
        git('add', '.')
        git('-c', 'user.name=Example', '-c', 'user.email=example@example.invalid',
            '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Synthetic example')
        commit = git('rev-parse', 'HEAD')
        baseline_path, analysis_path = output / 'baseline.json', output / 'csharp.json'
        baseline_path.write_text(json.dumps(baseline.collect(target, commit)))
        analysis_path.write_bytes(subprocess.check_output(['dotnet', str(args.csharp_dll.resolve()), str(target)]))
        database = output / 'catalog.sqlite'
        catalog.build(database, baseline_path, analysis_path, 'example')
        profiles = catalog.query(database, '''SELECT name,qualified_name,method_declarations,branch_nodes,
            max_constructor_parameters,lexical_name_occurrences,same_name_declarations
            FROM profiles ORDER BY qualified_name''')['rows']
        assert len(profiles) == 4, profiles
        policy = next(p for p in profiles if p['name'] == 'RetryPolicy')
        assert (policy['method_declarations'], policy['branch_nodes'],
                policy['max_constructor_parameters'], policy['lexical_name_occurrences']) == (1, 1, 1, 1), policy
        params = [p for p in profiles if p['name'] == 'Params']
        assert len(params) == 2
        assert all(p['lexical_name_occurrences'] == 2 and p['same_name_declarations'] == 2 for p in params)
        entity = catalog.query(database, "SELECT id,file_path,line FROM entities WHERE name='RetryPolicy'")['rows'][0]
        annotation = {'repository': 'example', 'commit': commit, 'interpretations': [{
            'entity_id': entity['id'], 'purpose': 'Decides whether another retry is allowed; does not schedule or execute one.',
            'confidence': 'medium', 'author': 'synthetic-example',
            'evidence': [{'path': entity['file_path'], 'line': entity['line']}]}]}
        annotations = output / 'annotations.json'
        annotations.write_text(json.dumps(annotation))
        catalog.annotate(database, annotations)
        purposes = catalog.query(database, "SELECT name,purpose FROM purpose_search WHERE purpose_search MATCH 'retry'")['rows']
        assert len(purposes) == 1
        assert git('status', '--porcelain') == ''
        print(json.dumps({'profiles': profiles, 'purpose_search': purposes}, indent=2))
        print('Example passed: snapshot import, metrics, ambiguity, annotation, search, and clean source.')


if __name__ == '__main__':
    main()
