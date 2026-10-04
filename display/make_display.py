"""Build one Display cut using the same engine and OpenType core as Reader.

python -X utf8 display/make_display.py display/cuts/ink.json
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from font_builder import FontBuilderCore


def build_cut(cut_file, outdir=None):
    """Load a cut's unchanged settings and build its full OTF/WOFF2 pair."""
    settings = json.loads(Path(cut_file).read_text(encoding='utf-8'))
    name = settings.get('name', 'Soft')
    slug = name.lower().replace(' ', '-')
    outdir = Path(outdir) if outdir else HERE / 'fonts' / slug
    outdir.mkdir(parents=True, exist_ok=True)
    builder = FontBuilderCore(settings, display=True, asset_dir=str(HERE))
    data = builder.export()
    out = outdir / f'SEIHouseDisplay-{name.replace(" ", "")}.otf'
    builder.build(data, str(out))
    print('built', builder.FAMILY, builder.VERSION, '->', out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cut', nargs='?', type=Path, default=HERE / 'cuts' / 'soft.json')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    build_cut(args.cut, args.output_dir)


if __name__ == '__main__':
    main()
