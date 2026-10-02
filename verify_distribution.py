"""Audit the actual ZIP/npm payloads and reject font-package bloat or broken CSS.

Uses only the standard library. No font/build/browser installation is required.
python verify_distribution.py [archive.zip ...] [--npm archive.tgz]
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent


def css_fonts(css):
    """Read shipped CSS independently and validate its relative asset references."""
    faces = []
    for block in re.findall(r'@font-face\s*\{([^}]+)\}', css):
        url = re.search(r'src:\s*url\("(\./fonts/SEIReader-[A-Za-z.-]+\.woff2)"\)', block)
        assert url, 'Invalid relative WOFF2 source'
        assert 'font-family: "SEIReader";' in block and 'font-display: swap;' in block
        assert 'format("woff2")' in block
        weight = int(re.search(r'font-weight:\s*(\d+);', block).group(1))
        slant = re.search(r'font-style:\s*(normal|italic);', block).group(1)
        faces.append((url.group(1)[2:], weight, slant, block))
    assert faces and len({p for p, _, _, _ in faces}) == len(faces), 'Missing/duplicate CSS faces'
    return faces


def verify_zip(path):
    """Check exact members, source bytes, integrity manifest, weights, and face order."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive paths'
        data = {name: archive.read(name) for name in names}
    manifest = json.loads(data['manifest.json'])
    assert manifest['family'] == 'SEIReader'
    assert manifest['version'] == json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))['version']
    weights = set(manifest['weights'])
    assert weights and weights <= {300, 400, 500, 600, 700}
    faces = css_fonts(data['fonts.css'].decode('utf-8'))
    assert {(w, s) for _, w, s, _ in faces} == {(w, s) for w in weights for s in ('normal', 'italic')}
    font_paths = {p for p, _, _, _ in faces}
    assert set(data) == font_paths | {'fonts.css', 'README.md', 'FONT-LICENSE.txt', 'manifest.json'}, 'Unexpected package contents'
    assert set(manifest['files']) == set(data) - {'manifest.json'}
    assert manifest['fonts'] == [{'path': p, 'weight': w, 'style': s} for p, w, s, _ in faces]
    for name, item in manifest['files'].items():
        assert item['bytes'] == len(data[name]) and item['sha256'] == hashlib.sha256(data[name]).hexdigest(), name
    source = {p: (w, s, block) for p, w, s, block in css_fonts((ROOT/'fonts.css').read_text(encoding='utf-8'))}
    full = {p.split('.')[0] + '.woff2': (w, s) for p, (w, s, _) in source.items()}
    if manifest['delivery'] == 'full':
        assert len(faces) == len(weights) * 2
        assert {p: (w, s) for p, w, s, _ in faces} == {p: ws for p, ws in full.items() if ws[0] in weights}
        assert all('unicode-range' not in block for _, _, _, block in faces)
    else:
        assert manifest['delivery'] == 'subsets' and len(faces) == len(weights) * 6
        expected = [p for p, (w, _, _) in source.items() if w in weights]
        assert [p for p, _, _, _ in faces] == expected, 'Subset priority changed'
        for p, w, s, block in faces:
            assert source[p] == (w, s, block), 'Subset CSS mapping/range changed'
    for name in font_paths:
        assert data[name] == (ROOT/name).read_bytes(), name
        assert data[name][:4] == b'wOF2' and int.from_bytes(data[name][8:12], 'big') == len(data[name])
    assert data['FONT-LICENSE.txt'] == (ROOT/'FONT-LICENSE.txt').read_bytes()
    assert manifest['font_bytes'] == sum(len(data[name]) for name in font_paths)
    print(f'{path.name}: exact runtime allowlist, font bytes, CSS mapping, weights and hashes pass')


def verify_npm(path):
    """Inspect npm's real tarball, including automatic files and exported CSS."""
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        assert all(m.isfile() and m.name.startswith('package/') for m in members)
        names = [m.name.removeprefix('package/') for m in members]
        assert len(names) == len(set(names)), 'Duplicate npm paths'
        data = {name: archive.extractfile(member).read() for name, member in zip(names, members)}
    meta = json.loads(data['package.json'])
    assert meta == json.loads((ROOT/'package.json').read_text(encoding='utf-8'))
    assert meta['name'] == '@seihouse/seireader' and meta['private'] and meta['license'] == 'UNLICENSED'
    font_version = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))['version']
    assert meta['version'] == (font_version if font_version.count('.') == 2 else font_version + '.0')
    assert not any(meta.get(key) for key in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies', 'scripts'))
    assert meta['sideEffects'] == ['*.css']
    assert meta['exports']['./styles.css'] == './fonts-full.css'
    faces = css_fonts(data['fonts-full.css'].decode('utf-8'))
    assert len(faces) == 10 and {(w, s) for _, w, s, _ in faces} == {
        (w, s) for w in (300, 400, 500, 600, 700) for s in ('normal', 'italic')}
    assert all('unicode-range' not in block for _, _, _, block in faces)
    assert set(data) == {p for p, _, _, _ in faces} | {'package.json', 'README.md', 'FONT-LICENSE.txt', 'fonts-full.css', 'docs/APP-INSTALL.md'}
    for name, content in data.items():
        if name != 'package.json':
            assert content == (ROOT/name).read_bytes(), name
    assert all(target.removeprefix('./') in data for target in meta['exports'].values())
    print(f'{path.name}: zero dependencies/scripts; exact 15-file payload, exports and source bytes pass')


def main():
    """Audit explicit packages, or the current-version ZIP outputs by default."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archives', type=Path, nargs='*')
    parser.add_argument('--npm', type=Path)
    args = parser.parse_args()
    font_version = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))['version']
    paths = args.archives or sorted((ROOT/'dist').glob(f'SEIReader-{font_version}-web-*.zip'))
    assert paths, 'Build the distribution first'
    for path in paths:
        verify_zip(path)
    if args.npm:
        verify_npm(args.npm)


if __name__ == '__main__':
    main()
