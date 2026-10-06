"""Build six web faces per Display cut with the Reader's subset/layout policy."""
import argparse
import os
from pathlib import Path
import sys

from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_subsets import subset_groups, unicode_range, write_subset

# Later faces own complete Latin/script runs, including combining marks and punctuation.
FACE_ORDER = ('latin-basic', 'symbols', 'latin-extended', 'cyrillic', 'greek', 'vietnamese')
BASIC_LIMIT = 25_000


def display_groups(codes):
    """Collapse Reader's historical Latin faces into one complete extended delivery."""
    reader = subset_groups(set(codes))
    return {name: reader['latin-ext-2' if name == 'latin-extended' else
                         'symbols-icons' if name == 'symbols' else name]
            for name in FACE_ORDER}


def build_cut_subsets(source):
    """Subset one final OTF, keeping hints, alternates, shaping and the ecosystem EULA."""
    source = Path(source)
    with TTFont(source) as font:
        codes = set(font.getBestCmap())
    groups = display_groups(codes)
    if set().union(*groups.values()) != codes or any(not group for group in groups.values()):
        raise ValueError('Invalid Display subset coverage: '+source.name)
    outputs = []
    for name, group in groups.items():
        output = source.with_suffix('.'+name+'.woff2')
        write_subset(source, output, group, keep_notdef_outline=True)
        if name == 'latin-basic' and output.stat().st_size >= BASIC_LIMIT:
            raise ValueError(f'{output.name}: Latin basic must be under {BASIC_LIMIT} bytes')
        outputs.append(output)
        print('subset', source.stem, name, len(group), 'characters,', output.stat().st_size, 'bytes')
    return outputs


def write_css(sources, output):
    """Write the cut families and exact subset coverage in browser face-priority order."""
    output = Path(output)
    lines = ['/* SEIHouse Display: six web subsets per cut; licensed under ../LICENSE. */']
    for source in sources:
        source = Path(source)
        with TTFont(source) as font:
            family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
            weight = font['OS/2'].usWeightClass
            style = 'italic' if font['OS/2'].fsSelection & 1 else 'normal'
            groups = display_groups(set(font.getBestCmap()))
        # Escape CSS strings for named cuts without changing their saved font identity.
        family = family.replace('\\', '\\\\').replace('"', '\\"')
        for name in FACE_ORDER:
            file = source.with_suffix('.'+name+'.woff2')
            path = Path(os.path.relpath(file, output.parent)).as_posix()
            path = path.replace('"', '\\"')
            lines.append(f'''@font-face {{
  font-family: "{family}";
  src: url("./{path}") format("woff2");
  font-style: {style};
  font-weight: {weight};
  font-display: swap;
  unicode-range: {unicode_range(groups[name])};
}}''')
    output.write_text('\n\n'.join(lines)+'\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, default=HERE/'fonts')
    parser.add_argument('--css', type=Path, default=HERE/'fonts.css')
    args = parser.parse_args()
    sources = sorted(args.fonts.glob('*/SEIHouseDisplay-*.otf'))
    if not sources:
        raise ValueError('No Display cuts found in '+str(args.fonts))
    for source in sources:
        build_cut_subsets(source)
    write_css(sources, args.css)


if __name__ == '__main__':
    main()
