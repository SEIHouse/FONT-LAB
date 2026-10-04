"""Build the ten Reader styles with the shared engine and font builder.

python -X utf8 make_fonts.py [my_changes.json] [--output-dir path/to/fonts]
The default settings and asset filenames retain the approved Reader output.
"""
import argparse
import json
from pathlib import Path

from font_builder import FontBuilderCore

HERE = Path(__file__).resolve().parent


def build_fonts(settings, outdir=None):
    """Build upright/italic weights, spacing data and the standard web subsets."""
    outdir = Path(outdir) if outdir else HERE / 'fonts'
    outdir.mkdir(parents=True, exist_ok=True)
    builder = FontBuilderCore(settings)
    weights = dict(settings.get('weights', {}))
    weights['Regular'] = settings['weight']
    for italic in (False, True):
        builder.ITAL = italic
        for style, weight in weights.items():
            builder.S = weight
            data = builder.export()
            if style == 'Regular' and not italic:
                (HERE / 'kern_base.json').write_text(json.dumps(data['kern'], ensure_ascii=False), encoding='utf-8')
            name = (('Italic' if style == 'Regular' else style + 'Italic') if italic else style)
            builder.build(data, str(outdir / f'SEIReader-{name}.otf'), style, italic)
            print('built', builder.FAMILY, builder.VERSION, name, 'thickness', weight)
    (HERE / 'kern_styles.json').write_text(json.dumps(builder.STYLE_KERN, ensure_ascii=False), encoding='utf-8')
    (HERE / 'kern_languages.json').write_text(json.dumps(builder.LANGUAGE_KERN, ensure_ascii=False), encoding='utf-8')
    from build_subsets import build_subsets
    if outdir.resolve() == (HERE / 'fonts').resolve():
        build_subsets()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('changes', nargs='?')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    settings = json.loads((HERE / 'settings.json').read_text(encoding='utf-8'))
    if args.changes:
        changes = json.loads(Path(args.changes).read_text(encoding='utf-8'))
        for key in ('weights', 'weight', 'xHeight', 'ascender', 'lowercaseRoundness', 'capitalRoundness',
                    'letterWidth', 'wordSpace', 'overshoot', 'uFoot', 'spaceBetweenAllLetters',
                    'letterSpace', 'pairSpace', 'corners', 'ends', 'joins', 'penAngle', 'slant'):
            if key in changes:
                settings[key] = changes[key]
    build_fonts(settings, args.output_dir)


if __name__ == '__main__':
    main()
