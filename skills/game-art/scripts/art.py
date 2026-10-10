#!/usr/bin/env python3
"""Local PNG packaging and measurements. JSON reports; exit 0 pass, 1 mismatch, 2 error.

Requires ImageMagick convert (6) or magick (7); never installs or downloads.
Inputs are forced through the PNG decoder. Output files/directories must be new.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

MAX_PIXELS = 16_777_216
PNG = b'\x89PNG\r\n\x1a\n'


def im(args, data=None):
    exe = shutil.which('magick') or shutil.which('convert')
    if not exe:
        raise ValueError('ImageMagick magick or convert is required; nothing installed')
    return subprocess.run([exe, '-limit', 'memory', '256MiB', '-limit', 'map',
                           '256MiB', '-limit', 'disk', '256MiB', '-limit', 'thread',
                           '1', *args], input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=60, check=True).stdout


def read_png(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('input must be a PNG file under 128 MiB')
    data = path.read_bytes()
    if data[:8] != PNG or data[12:16] != b'IHDR' or len(data) < 33:
        raise ValueError('input must have a PNG IHDR')
    w, h = struct.unpack('>II', data[16:24])
    if not w or not h or w * h > MAX_PIXELS:
        raise ValueError('image dimensions exceed the 16M-pixel limit')
    # APNG would silently lose frames if only its default image were decoded.
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        if data[offset + 4:offset + 8] == b'acTL':
            raise ValueError('animated PNG is unsupported; export individual frames')
        offset += length + 12
    rgba = im(['png:-', '-alpha', 'on', '-depth', '8', 'rgba:-'], data)
    if len(rgba) != w * h * 4:
        raise ValueError('decoded PNG length does not match its dimensions')
    return w, h, rgba


def write_png(path, w, h, data):
    if not w or not h or w * h > MAX_PIXELS:
        raise ValueError('output exceeds the 16M-pixel limit')
    out = im(['-size', f'{w}x{h}', '-depth', '8', 'rgba:-', '-strip',
              '-define', 'png:exclude-chunks=date,time', 'png:-'], data)
    with Path(path).open('xb') as f:
        f.write(out)


def cell_size(w, h, cell):
    cw, ch = cell
    if cw < 1 or ch < 1 or w % cw or h % ch:
        raise ValueError('positive cells must divide the image exactly')
    return cw, ch


def cells(w, h, rgba, cell):
    cw, ch = cell_size(w, h, cell)
    for y in range(0, h, ch):
        for x in range(0, w, cw):
            yield b''.join(rgba[((y + dy) * w + x) * 4:
                               ((y + dy) * w + x + cw) * 4] for dy in range(ch))


def cut(a):
    w, h, data = read_png(a.input)
    cw, ch = cell_size(w, h, a.cell)
    out = Path(a.output)
    frames = list(cells(w, h, data, a.cell))
    out.mkdir()  # no overwriting an earlier frame set
    for i, frame in enumerate(frames):
        write_png(out / f'{i:04d}.png', cw, ch, frame)
    return {'pass': True, 'frames': len(frames), 'cell': [cw, ch], 'order': 'row-major'}


def pack(a):
    frames = [read_png(p) for p in a.inputs]
    cw, ch, _ = frames[0]
    if any((w, h) != (cw, ch) for w, h, _ in frames):
        raise ValueError('frames must have identical dimensions; no automatic trimming')
    if a.columns < 1 or len(frames) % a.columns:
        raise ValueError('columns must divide frame count, without padded cells')
    w, h = cw * a.columns, ch * (len(frames) // a.columns)
    if w * h > MAX_PIXELS:
        raise ValueError('packed image exceeds the 16M-pixel limit')
    data = bytearray(w * h * 4)
    for i, (_, _, frame) in enumerate(frames):
        x, y = (i % a.columns) * cw, (i // a.columns) * ch
        for dy in range(ch):
            pos = ((y + dy) * w + x) * 4
            data[pos:pos + cw * 4] = frame[dy * cw * 4:(dy + 1) * cw * 4]
    write_png(a.output, w, h, data)
    return {'pass': True, 'size': [w, h], 'cell': [cw, ch],
            'frames': [{'file': p, 'index': i, 'x': i % a.columns * cw,
                        'y': i // a.columns * ch} for i, p in enumerate(a.inputs)]}


def color(s):
    if len(s) != 7 or s[0] != '#':
        raise ValueError('colors must use #rrggbb')
    return bytes.fromhex(s[1:])


def check(a):
    w, h, data = read_png(a.input)
    cw, ch = cell_size(w, h, a.cell or [w, h])
    palette = {color(c) for c in a.palette.split(',')} if a.palette else None
    matte = color(a.matte) if a.matte else None
    rules = []
    def rule(name, measured, threshold, passed):
        rules.append({'id': name, 'pass': bool(passed), 'measured': measured,
                      'threshold': threshold})
    rule('size', [w, h], a.size, [w, h] == a.size)
    if a.frames is not None:
        n = w // cw * (h // ch)
        rule('frames', n, a.frames, n == a.frames)
    transparent = sum(data[i] == 0 for i in range(3, len(data), 4))
    partial = sum(0 < data[i] < 255 for i in range(3, len(data), 4))
    if a.alpha == 'transparent':
        rule('alpha', {'transparent': transparent, 'partial': partial},
             'at least one transparent pixel', transparent > 0)
    elif a.alpha == 'opaque':
        rule('alpha', transparent + partial, 0, transparent + partial == 0)
    if palette is not None:
        bad = sum(data[i + 3] == 255 and data[i:i + 3] not in palette
                  for i in range(0, len(data), 4))
        rule('palette', bad, 0, bad == 0)
    if matte is not None:
        bad = sum(data[i + 3] > 0 and data[i:i + 3] == matte
                  for i in range(0, len(data), 4))
        rule('matte', bad, 0, bad == 0)
    anchors, interior = [], 0
    for frame in cells(w, h, data, [cw, ch]):
        points = []
        for y in range(ch):
            for x in range(cw):
                alpha = frame[(y * cw + x) * 4 + 3]
                if alpha == 255:
                    points.append((x, y))
                if a.edge_alpha and 0 < alpha < 255:
                    boundary = any(nx < 0 or nx >= cw or ny < 0 or ny >= ch or
                                   frame[(ny * cw + nx) * 4 + 3] == 0
                                   for nx, ny in ((x + dx, y + dy)
                                                 for dx in (-1, 0, 1)
                                                 for dy in (-1, 0, 1) if dx or dy))
                    interior += not boundary
        if a.anchors:
            anchors.append([(min(x for x, _ in points) + max(x for x, _ in points)) / 2,
                            max(y for _, y in points)] if points else None)
    if a.edge_alpha:
        rule('partial-alpha-edge', interior, 0, interior == 0)
    if a.anchors:
        valid = all(v is not None for v in anchors)
        spread = [max(v[i] for v in anchors) - min(v[i] for v in anchors)
                  for i in (0, 1)] if valid else None
        rule('anchors', {'positions': anchors, 'spread': spread},
             'range <= 1 px per axis; no empty frames', valid and max(spread) <= 1)
    return {'pass': all(r['pass'] for r in rules), 'rules': rules}


def revision(a):
    w, h, before = read_png(a.before)
    rw, rh, after = read_png(a.after)
    mw, mh, mask = read_png(a.mask)
    if (rw, rh) != (w, h) or (mw, mh) != (w, h):
        raise ValueError('before, after and mask must have identical dimensions')
    # Nonzero alpha AND nonzero RGB means allowed. Black/transparent is protected.
    changes = sum(before[i:i + 4] != after[i:i + 4] and
                  not (mask[i + 3] and any(mask[i:i + 3]))
                  for i in range(0, len(before), 4))
    return {'pass': changes == 0, 'outside_mask_changed_pixels': changes,
            'threshold': 0, 'mask': 'nonblack with nonzero alpha allows changes'}


def manifest(a):
    spec = importlib.util.spec_from_file_location('studio_manifest',
               Path(__file__).resolve().parents[2] / 'studio/validate_manifest.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    root = Path(a.root).resolve(strict=True)
    def contained(s):
        if validator.path_error(s):
            raise ValueError(f'unsafe project-relative path: {s!r}')
        path = (root / s).resolve()
        if path == root or root not in path.parents:
            raise ValueError(f'path escapes project root: {s!r}')
        return path
    exports = contained(a.exports)
    for ip in a.import_path:
        contained(ip)
    row = json.loads(Path(a.row).read_text())
    target = exports / 'MANIFEST.json'
    if target.is_symlink():
        raise ValueError('manifest must not be a symlink')
    m = json.loads(target.read_text()) if target.exists() else {'manifest_version': 1, 'assets': []}
    if not isinstance(row, dict) or not isinstance(m, dict) or not isinstance(m.get('assets'), list):
        raise ValueError('row and manifest must be objects with valid asset lists')
    old_errors = validator.validate(m)
    if old_errors:
        raise ValueError(f'existing manifest invalid: {old_errors}')
    rows = [r for r in m['assets'] if r['file'] != row.get('file')]
    candidate = {'manifest_version': m['manifest_version'], 'assets': rows + [row]}
    errs = validator.validate(candidate)
    if errs:
        raise ValueError(f'manifest invalid: {errs}')
    for r in candidate['assets']:
        for key in ('file', 'master', 'build_script', 'consent_record'):
            if r.get(key) is not None:
                resolved = contained(r[key])
                if key in ('master', 'build_script'):
                    for ip in a.import_path:
                        imported = contained(ip)
                        if resolved == imported or imported in resolved.parents:
                            raise ValueError(f'{key} resolves inside engine import path')
    for path in exports.rglob('*'):
        if path.is_symlink() and root not in path.resolve().parents:
            raise ValueError('export symlink escapes project root')
    errs = validator.validate(candidate, root, a.exports, a.import_path)
    if errs:
        raise ValueError(f'manifest invalid: {errs}')
    fd, temp = tempfile.mkstemp(prefix='.manifest-', dir=exports)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(candidate, f, indent=2); f.write('\n')
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return {'pass': True, 'manifest': str(target), 'rows': len(candidate['assets'])}


def credits(a):
    spec = importlib.util.spec_from_file_location('studio_manifest',
               Path(__file__).resolve().parents[2] / 'studio/validate_manifest.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    m = json.loads(Path(a.input).read_text())
    if errs := module.validate(m):
        raise ValueError(f'manifest invalid: {errs}')
    def safe(x):
        return str(x).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = ['| Asset | Source and license | Model and weights terms |', '|---|---|---|']
    for row in m['assets']:
        lines.append('| ' + ' | '.join(safe(x) for x in (row['file'],
                     f"{row['source'] or 'Original'}; {row['source_license'] or 'not reused'}",
                     f"{row['model'] or 'None'}; {row['weights_license'] or 'not used'}")) + ' |')
        for text in row.get('text', []):
            lines.append(f"\nFont for {safe(row['file'])}: {safe(text['font'])}.")
    print('\n'.join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('cut'); c.add_argument('input'); c.add_argument('output')
    c.add_argument('--cell', nargs=2, type=int, required=True); c.set_defaults(run=cut)
    c = sub.add_parser('pack'); c.add_argument('output'); c.add_argument('inputs', nargs='+')
    c.add_argument('--columns', type=int, required=True); c.set_defaults(run=pack)
    c = sub.add_parser('check'); c.add_argument('input')
    c.add_argument('--size', nargs=2, type=int, required=True)
    c.add_argument('--cell', nargs=2, type=int); c.add_argument('--frames', type=int)
    c.add_argument('--alpha', choices=['any', 'opaque', 'transparent'], default='any')
    c.add_argument('--palette'); c.add_argument('--matte')
    c.add_argument('--edge-alpha', action='store_true'); c.add_argument('--anchors', action='store_true')
    c.set_defaults(run=check)
    c = sub.add_parser('revision')
    for name in ('before', 'after', 'mask'): c.add_argument(name)
    c.set_defaults(run=revision)
    c = sub.add_parser('manifest'); c.add_argument('--root', required=True)
    c.add_argument('--row', required=True); c.add_argument('--exports', default='assets')
    c.add_argument('--import-path', action='append', required=True); c.set_defaults(run=manifest)
    c = sub.add_parser('credits'); c.add_argument('input'); c.set_defaults(run=credits)
    a = p.parse_args()
    try:
        report = a.run(a)
        if report is not None:
            print(json.dumps(report)); return 0 if report['pass'] else 1
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as e:
        print(json.dumps({'pass': False, 'error': str(e)}), file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
