"""Package existing WOFF2 bytes for an app, using only the Python standard library.

python build_distribution.py
python build_distribution.py --weights 400
python build_distribution.py --delivery subsets
This does not rebuild, subset, or alter any font.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
WEIGHTS = (300, 400, 500, 600, 700)
SUBSETS = ('latin-basic', 'symbols-icons', 'latin-extended')


def family_faces(root=ROOT):
    """Read the checked-in CSS mapping, keeping its authoritative face order."""
    css = (root/'fonts.css').read_text(encoding='utf-8')
    faces = {}
    for block in re.findall(r'@font-face\s*\{([^}]+)\}', css):
        match = re.search(r'url\("\./fonts/SEIReader-([A-Za-z]+)\.(latin-basic|symbols-icons|latin-extended)\.woff2"\)', block)
        if not match:
            raise ValueError('Unexpected font URL in fonts.css')
        style, subset = match.groups()
        weight = int(re.search(r'font-weight:\s*(\d+);', block).group(1))
        slant = re.search(r'font-style:\s*(normal|italic);', block).group(1)
        face = faces.setdefault(style, {'style': style, 'weight': weight, 'slant': slant, 'blocks': {}})
        if (face['weight'], face['slant']) != (weight, slant) or subset in face['blocks']:
            raise ValueError(f'Conflicting or duplicate face: {style}')
        face['blocks'][subset] = '@font-face {' + block + '}'
    if len(faces) != 10 or {(f['weight'], f['slant']) for f in faces.values()} != {
            (w, s) for w in WEIGHTS for s in ('normal', 'italic')}:
        raise ValueError('Expected five weights, each upright and italic')
    if any(tuple(f['blocks']) != SUBSETS for f in faces.values()):
        raise ValueError('Subset face order or inventory changed')
    return list(faces.values())


def version(root=ROOT):
    """Read a safe font version for filenames and package metadata."""
    value = json.loads((root/'settings.json').read_text(encoding='utf-8'))['version']
    if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', value):
        raise ValueError(f'Unsupported distribution version: {value}')
    return value


def full_stylesheet(faces, font_version):
    """Register full fonts, with relative URLs and no Unicode face splitting."""
    blocks = [f'/* SEIReader {font_version}: full web family; keep next to fonts/. */']
    for face in faces:
        blocks.append(f'''@font-face {{
  font-family: "SEIReader";
  src: url("./fonts/SEIReader-{face['style']}.woff2") format("woff2");
  font-style: {face['slant']};
  font-weight: {face['weight']};
  font-display: swap;
}}''')
    return ('\n\n'.join(blocks) + '\n').encode('utf-8')


def replace_bytes(path, data):
    """Replace a generated file only when needed, without truncating a synced file."""
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.distribution-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def write_full_css(root=ROOT):
    """Refresh the dependency-free app stylesheet alongside the existing subset CSS."""
    replace_bytes(root/'fonts-full.css', full_stylesheet(family_faces(root), version(root)))


def build_archive(delivery='full', weights=WEIGHTS, output_dir=None, root=ROOT):
    """Write a deterministic archive from an explicit runtime file allowlist."""
    weights = tuple(sorted(set(weights)))
    if delivery not in ('full', 'subsets') or not weights or not set(weights) <= set(WEIGHTS):
        raise ValueError('Choose full/subsets and supported weights')
    font_version = version(root)
    package = json.loads((root/'package.json').read_text(encoding='utf-8'))
    npm_version = font_version if font_version.count('.') == 2 else font_version + '.0'
    if package['version'] != npm_version:
        raise ValueError('Update package.json to match settings.json before packaging')
    faces = [f for f in family_faces(root) if f['weight'] in weights]
    if delivery == 'full':
        css = full_stylesheet(faces, font_version)
    else:
        css = ('\n\n'.join(f['blocks'][s] for f in faces for s in SUBSETS) + '\n').encode('utf-8')
    files = {'fonts.css': css, 'FONT-LICENSE.txt': (root/'FONT-LICENSE.txt').read_bytes()}
    intro = (f'SEIReader {font_version} app bundle\nDelivery: {delivery}\nWeights: {", ".join(map(str, weights))}\n'
             'Only these selected weights and their real italics are included.\n\n')
    files['README.md'] = intro.encode('utf-8') + (root/'docs/APP-INSTALL.md').read_bytes()
    font_entries = []
    for face in faces:
        suffixes = ('',) if delivery == 'full' else tuple('.' + s for s in SUBSETS)
        for suffix in suffixes:
            name = f"fonts/SEIReader-{face['style']}{suffix}.woff2"
            data = (root/name).read_bytes()
            if data[:4] != b'wOF2' or int.from_bytes(data[8:12], 'big') != len(data):
                raise ValueError(f'Invalid WOFF2 file: {name}')
            files[name] = data
            font_entries.append({'path': name, 'weight': face['weight'], 'style': face['slant']})
    manifest = {'family': 'SEIReader', 'version': font_version, 'delivery': delivery,
                'weights': list(weights), 'fonts': font_entries,
                'font_bytes': sum(len(files[f['path']]) for f in font_entries),
                'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in sorted(files.items())}}
    files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    write_full_css(root)
    label = '' if weights == WEIGHTS else '-w' + '-'.join(map(str, weights))
    output_dir = root/'dist' if output_dir is None else Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir/f'SEIReader-{font_version}-web-{delivery}{label}.zip'
    descriptor, temporary = tempfile.mkstemp(prefix='.distribution-', dir=output_dir)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    print(f'{destination.name}: {len(font_entries)} WOFF2 files; {manifest["font_bytes"]:,} font bytes; {destination.stat().st_size:,} archive bytes')
    return destination


def main():
    """Build the recommended family or an explicitly selected weight/subset delivery."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', choices=('full', 'subsets'), default='full')
    parser.add_argument('--weights', type=int, nargs='+', choices=WEIGHTS, default=WEIGHTS)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    build_archive(args.delivery, args.weights, args.output_dir)


if __name__ == '__main__':
    main()
