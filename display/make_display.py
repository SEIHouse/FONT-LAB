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
from display.build_subsets import build_cut_subsets, write_css


def build_style(settings, outdir, *, metadata_dir=None, style='Regular', oblique=False):
    """Build a real style through the shared core; drawing choices stay in settings."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    metadata_dir = Path(metadata_dir) if metadata_dir is not None else outdir
    metadata_dir.mkdir(parents=True, exist_ok=True)
    builder = FontBuilderCore(settings, display=True, asset_dir=str(metadata_dir))
    data = builder.export()
    label = ('Oblique' if style == 'Regular' else style+'Oblique') if oblique else style
    suffix = '' if label == 'Regular' else '-'+label
    out = outdir / f'SEIHouseDisplay-{settings["name"].replace(" ", "")}{suffix}.otf'
    if oblique:
        builder.build(data, str(out), style, oblique=True)
    else:
        builder.build(data, str(out), style)
    print('built', builder.FAMILY, label, builder.VERSION, '->', out, flush=True)
    return out


def build_cut(cut_file, outdir=None):
    """Build a cut's full OTF/WOFF2, six web subsets and their stylesheet."""
    settings = json.loads(Path(cut_file).read_text(encoding='utf-8'))
    name = settings.get('name', 'Soft')
    slug = name.lower().replace(' ', '-')
    candidate = outdir is not None
    metadata_dir = Path(outdir) if outdir else HERE
    outdir = Path(outdir) if outdir else HERE / 'fonts' / slug
    out = build_style(settings, outdir, metadata_dir=metadata_dir)
    if not candidate:
        sources = sorted((HERE/'fonts').glob('*/SEIHouseDisplay-*.otf'))
        css = HERE/'fonts.css'
    else:
        sources = [out]
        css = outdir/'fonts.css'
    # Shared CSS must only reference subsets freshly made from each included OTF.
    for source in sources:
        build_cut_subsets(source)
    write_css(sources, css)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cut', nargs='?', type=Path, default=HERE / 'cuts' / 'soft.json')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    build_cut(args.cut, args.output_dir)


if __name__ == '__main__':
    main()
