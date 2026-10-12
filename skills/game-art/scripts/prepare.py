#!/usr/bin/env python3
"""Prepare an offline game-art skill directory from a pinned reference commit.

Copies only the skill's active files and fixed public reference documents.
Never fetches, installs, reads evaluation cases or accesses credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

REFERENCES = (
    'art/2d.md', 'art/blender.md', 'ai/graphics.md', 'skills/SPEC-studio.md',
    'skills/studio/manifest.schema.json', 'skills/studio/validate_manifest.py',
    'README.md', 'LICENSE',
)
LINKS = {
    '../../art/2d.md': 'art/2d.md',
    '../../art/blender.md': 'art/blender.md',
    '../../ai/graphics.md': 'ai/graphics.md',
    '../SPEC-studio.md': 'skills/SPEC-studio.md',
    '../studio/manifest.schema.json': 'skills/studio/manifest.schema.json',
    '../studio/validate_manifest.py': 'skills/studio/validate_manifest.py',
}
MAX_FILE = 1024 * 1024


def git(repo, *args):
    return subprocess.run(
        ['git', '-c', 'credential.helper=', '-c', 'core.hooksPath=/dev/null',
         '-C', str(repo), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True, timeout=30).stdout


def prepare(repo, commit, output):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('reference commit must be a full immutable 40-hex commit ID')
    if git(repo, 'cat-file', '-t', commit).strip() != b'commit':
        raise ValueError('reference must identify a commit')
    skill = Path(__file__).resolve().parents[1]
    files = {}
    modes = {}
    source_hashes = {}
    for source in [skill / 'SKILL.md', *sorted((skill / 'scripts').glob('*.py'))]:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_FILE:
            raise ValueError('active skill files must be plain files under 1 MiB')
        path = str(source.relative_to(skill))
        files[path] = source.read_bytes()
        source_hashes[path] = hashlib.sha256(files[path]).hexdigest()
        modes[path] = 0o755 if source.stat().st_mode & 0o111 else 0o644
    for path in REFERENCES:
        mode = git(repo, 'ls-tree', commit, '--', path).split(maxsplit=1)[0]
        if mode not in {b'100644', b'100755'}:
            raise ValueError('reference documents must be plain Git blobs')
        data = git(repo, 'show', commit + ':' + path)
        if len(data) > MAX_FILE:
            raise ValueError('reference document exceeds 1 MiB')
        files['references/' + path] = data
        modes['references/' + path] = 0o644
    text = files['SKILL.md'].decode('utf-8')
    for old, new in LINKS.items():
        if '(' + old + ')' not in text:
            raise ValueError('skill reference link is missing: ' + old)
        text = text.replace('(' + old + ')', '(references/' + new + ')')
    files['SKILL.md'] = text.encode('utf-8')
    if len(files) > 64 or sum(len(data) for data in files.values()) > 8 * MAX_FILE:
        raise ValueError('prepared skill exceeds its file or byte limit')
    # All source validation completes before creating a new output directory.
    output.mkdir(parents=True, exist_ok=False)
    for path, data in files.items():
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(modes[path])
    receipt = {
        'bundle': 'game-art-offline-1', 'reference_commit': commit,
        'source_skill_files_sha256': source_hashes,
        'files': {path: hashlib.sha256(data).hexdigest()
                  for path, data in sorted(files.items())},
        'no_evaluation_cases': True, 'no_network': True,
    }
    (output / 'BUNDLE.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--reference-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = prepare(args.repo, args.reference_commit, args.output)
    except (ValueError, OSError, subprocess.SubprocessError, IndexError) as error:
        message = 'pinned reference Git data unavailable' if isinstance(error, subprocess.SubprocessError) else str(error)
        print(json.dumps({'pass': False, 'error': message}), file=sys.stderr)
        return 2
    print(json.dumps({'pass': True, 'files': len(receipt['files']),
                      'reference_commit': receipt['reference_commit']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
