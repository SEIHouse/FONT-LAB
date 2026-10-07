"""Build every cuts/*.json, its opted-in styles, web subsets and native specimens.

python -X utf8 display/build_all_cuts.py --output-dir dist/display-production
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from fontTools.ttLib import TTFont
from display.build_subsets import build_cut_subsets, font_style, write_css
from display.make_display import build_style
from display.production import ROOT, asset_record, font_path, load_cuts, style_plan
from display.specimens import write_specimens


def build_all(cuts_dir=HERE/'cuts', output_dir=None, *, specimens_only=False):
    cuts = load_cuts(cuts_dir)
    # Resolve every per-cut style plan before writing anything.
    plans = [(cut, style_plan(cut['settings'])) for cut in cuts]
    root = Path(output_dir).resolve() if output_dir is not None else ROOT
    fonts, metadata = root/'display/fonts', root/'display'
    metadata.mkdir(parents=True, exist_ok=True)
    manifest = dict(version=1, license='LICENSE', css='display/fonts.css', cuts=[])
    sources = []
    for cut, plan in plans:
        row = dict(name=cut['name'], slug=cut['slug'], settings=cut['settings'], styles=[],
                   specimen=f'site/display/{cut["slug"]}/index.html')
        for face in plan:
            source = font_path(fonts, cut, face['label'])
            asset_dir = metadata if root == ROOT and face['label']=='Regular' else source.parent
            if not specimens_only:
                built = build_style(face['settings'], source.parent, metadata_dir=asset_dir,
                                    style=face['style'], oblique=face['oblique'])
                if built != source:
                    raise ValueError('Builder output disagrees with production inventory')
                build_cut_subsets(source)
            with TTFont(source) as font:
                family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
                weight = font['OS/2'].usWeightClass
                slope = font_style(font)
            spacing = asset_dir/f'spacing_{cut["slug"]}.json'
            assets = [source, source.with_suffix('.woff2'),
                      *[source.with_suffix('.'+subset+'.woff2') for subset in
                        ('latin-basic', 'symbols', 'latin-extended', 'cyrillic', 'greek', 'vietnamese')], spacing]
            row['styles'].append(dict(label=face['label'], family=family, weight=weight, slope=slope,
                                      settings=face['settings'], otf=source.relative_to(root).as_posix(),
                                      woff2=source.with_suffix('.woff2').relative_to(root).as_posix(),
                                      spacing=spacing.relative_to(root).as_posix(),
                                      assets=[asset_record(path, root) for path in assets]))
            sources.append(source)
        manifest['cuts'].append(row)
    write_css(sources, metadata/'fonts.css')
    if root != ROOT:
        for name in ('LICENSE', 'FONT-LICENSE.txt'):
            shutil.copyfile(ROOT/name, root/name)
    write_specimens(manifest, root)
    target = metadata/'production-manifest.json'
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(f'Production: {len(cuts)} cuts, {len(sources)} styles -> {target}', flush=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cuts', type=Path, default=HERE/'cuts')
    parser.add_argument('--output-dir', type=Path, help='Self-contained bundle root; leaves shipped fonts/spacing untouched')
    parser.add_argument('--specimens-only', action='store_true', help='Generate inventory, CSS and specimens from existing built fonts')
    args = parser.parse_args()
    build_all(args.cuts, args.output_dir, specimens_only=args.specimens_only)


if __name__ == '__main__':
    main()
