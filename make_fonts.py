"""Build the ten Reader styles and their Night grades with the shared engine and font builder.

python -X utf8 make_fonts.py [my_changes.json] [--output-dir path/to/fonts]
The default settings and asset filenames retain the approved Reader output.
"""
import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from font_builder import FontBuilderCore, NIGHT_GRADE

HERE = Path(__file__).resolve().parent
# Body-text weights that receive a paired Night-mode optical grade.
NIGHT_WEIGHTS = ('Light', 'Regular', 'Medium')


def name_night_family(otf, family, style):
    """Give a Light or Medium Night face its own legacy family name.

    The shared builder names every graded face "<family> Night", which is unique for
    Regular only. Desktop menus that group by the legacy name need one family per weight.
    """
    with TTFont(otf) as font:
        font['name'].setName(f'{family} {style} Night', 1, 3, 1, 0x409)
        font.save(otf)
    with TTFont(otf) as font:
        font.flavor = 'woff2'
        font.save(otf.with_suffix('.woff2'))


def build_fonts(settings, outdir=None, *, night_only=False):
    """Build upright/italic weights, spacing data and the standard web subsets."""
    outdir = Path(outdir) if outdir else HERE / 'fonts'
    outdir.mkdir(parents=True, exist_ok=True)
    default_output = outdir.resolve() == (HERE / 'fonts').resolve()
    metadata_dir = HERE if default_output else outdir
    builder = FontBuilderCore(settings, asset_dir=str(metadata_dir))
    weights = dict(settings.get('weights', {}))
    weights['Regular'] = settings['weight']
    for italic in (False, True):
        builder.ITAL = italic; builder.GRADE = 0
        for style, weight in ([] if night_only else list(weights.items())):
            builder.S = weight
            data = builder.export()
            if style == 'Regular' and not italic:
                (metadata_dir / 'kern_base.json').write_text(json.dumps(data['kern'], ensure_ascii=False), encoding='utf-8')
            name = (('Italic' if style == 'Regular' else style + 'Italic') if italic else style)
            builder.build(data, str(outdir / f'SEIReader-{name}.otf'), style, italic)
            print('built', builder.FAMILY, builder.VERSION, name, 'thickness', weight)
        for style in (s for s in NIGHT_WEIGHTS if s in weights):
            builder.S = weights[style]; builder.GRADE = NIGHT_GRADE
            night_data = builder.export()
            night_name = (('Italic' if style == 'Regular' else style + 'Italic') if italic else style) + 'Night'
            night_otf = outdir / f'SEIReader-{night_name}.otf'
            builder.build(night_data, str(night_otf), style, italic)
            if style != 'Regular':
                name_night_family(night_otf, builder.FAMILY, style)
            print('built', builder.FAMILY, builder.VERSION, night_name, 'thickness', weights[style], 'grade', NIGHT_GRADE)
        builder.GRADE = 0
    styles_path, langs_path = metadata_dir / 'kern_styles.json', metadata_dir / 'kern_languages.json'
    existing_styles = json.loads(styles_path.read_text(encoding='utf-8')) if night_only and styles_path.exists() else {}
    styles_path.write_text(json.dumps({**existing_styles, **builder.STYLE_KERN}, ensure_ascii=False), encoding='utf-8')
    existing_langs = json.loads(langs_path.read_text(encoding='utf-8')) if night_only and langs_path.exists() else {}
    langs_path.write_text(json.dumps({**existing_langs, **builder.LANGUAGE_KERN}, ensure_ascii=False), encoding='utf-8')
    from build_subsets import build_subsets
    if default_output:
        build_subsets(night_only=night_only)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('changes', nargs='?')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--night-only', action='store_true', help='Build only the Light, Regular and Medium Night optical grade fonts')
    args = parser.parse_args()
    settings = json.loads((HERE / 'settings.json').read_text(encoding='utf-8'))
    if args.changes:
        changes = json.loads(Path(args.changes).read_text(encoding='utf-8'))
        for key in ('weights', 'weight', 'xHeight', 'ascender', 'lowercaseRoundness', 'capitalRoundness',
                    'letterWidth', 'wordSpace', 'overshoot', 'uFoot', 'spaceBetweenAllLetters',
                    'letterSpace', 'pairSpace', 'corners', 'ends', 'joins', 'penAngle', 'slant'):
            if key in changes:
                settings[key] = changes[key]
    build_fonts(settings, args.output_dir, night_only=args.night_only)


if __name__ == '__main__':
    main()
