"""Measure how dark the Reader looks at each app text size, per browser and hinting.

python verify_size_density.py <output-directory> [--browser chromium|webkit|firefox] [--channel chrome|msedge] [--grayscale] [--dpr 1 2 3]

Every size sets the same paragraph in a column 30em wide, so line breaks and
glyphs are identical and only the size changes. Ink is the summed coverage of a
screenshot divided by the square of the device-pixel size: a constant number
means enlarging the text changes size but not apparent weight. A step between
neighboring app sizes above JUMP_LIMIT is reported as a jump.

Each weight is rendered three ways. `shipped` is the released font. The other two
are measurement-only copies, never shipped: `no-vstem` drops the vertical-stem
hints (the ones that round letter stems to whole pixels across the line) and keeps
the horizontal hints that align the baseline, x-height and caps; `unhinted` drops
all hints. Comparing them shows whether a jump comes from hinting rather than
from the drawn stroke weight.

`--grayscale` turns off Chromium's subpixel (ClearType-style) text, as Chrome
itself does when ClearType is off or text sits in an animated or translucent
layer. Grayscale text can only place a stem edge on whole pixels.
"""
from pathlib import Path
import argparse
import io
import json
import math
import platform
import tempfile

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
# The Reader's text sizes in NovelExpanded (Development, src/narrative/readerText.ts).
APP_SIZES = (15, 17.2, 18.5, 20, 22)
WEIGHTS = {300: 'Light', 400: 'Regular', 500: 'Medium'}
VARIANTS = ('shipped', 'no-vstem', 'unhinted')
JUMP_LIMIT = 0.15
PARAGRAPH = ('The gate will remain closed until morning, Iñés said. Lian placed Mei’s entry '
             'beside the lamp and read it again. The note asked for a minimum of three '
             'witnesses before anyone opened the inner court. Two parallel paths followed '
             'the river, where willow branches moved in the wind. He listened for the murmur '
             'beneath the bridge, then turned back to the ledger.')


def desubroutinized(font):
    """Inline every subroutine so each glyph's complete hint program can be edited."""
    options = Options()
    options.glyph_names = options.notdef_outline = options.name_legacy = True
    options.layout_features = ['*']
    options.name_IDs = ['*']
    options.desubroutinize = True
    subsetter = Subsetter(options)
    subsetter.populate(glyphs=font.getGlyphOrder())
    subsetter.subset(font)


def drop_vertical_stems(program):
    """Return a Type 2 program without vstem hints, rewriting hint masks to match."""
    out, stack, masks, hstems, vstems, masked = [], [], [], 0, 0, False
    for token in program:
        if isinstance(token, bytes):
            masks.append(len(out))
            out.append(token)
        elif not isinstance(token, str):
            stack.append(token)
        else:
            if token in ('hstem', 'hstemhm'):
                hstems += len(stack) // 2
                out.extend(stack + [token])
            elif token in ('vstem', 'vstemhm') or (token in ('hintmask', 'cntrmask') and not masked):
                # Stem pairs go; an odd leading number is the advance width and stays.
                vstems += len(stack) // 2
                out.extend(stack[:len(stack) % 2])
                if token in ('hintmask', 'cntrmask'):
                    masked = True
                    out.append(token)
            else:
                out.extend(stack + [token])
            stack = []
    out.extend(stack)
    for index in reversed(masks):
        bits = ''.join(f'{byte:08b}' for byte in out[index])[:hstems + vstems][:hstems]
        if hstems:
            bits = bits.ljust(math.ceil(hstems / 8) * 8, '0')
            out[index] = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
        else:
            del out[index - 1:index + 1]  # No stems remain, so the mask goes too.
    return out


def variant_font(source, variant):
    """Return WOFF-free OTF bytes for one measurement variant of a shipped font."""
    font = TTFont(source)
    font.flavor = None
    if variant == 'unhinted':
        options = Options()
        options.glyph_names = options.notdef_outline = options.name_legacy = True
        options.layout_features = ['*']
        options.name_IDs = ['*']
        options.hinting = False
        subsetter = Subsetter(options)
        subsetter.populate(glyphs=font.getGlyphOrder())
        subsetter.subset(font)
    elif variant == 'no-vstem':
        desubroutinized(font)
        top = font['CFF '].cff.topDictIndex[0]
        for name in font.getGlyphOrder():
            charstring = top.CharStrings[name]
            charstring.decompile()
            charstring.program = drop_vertical_stems(charstring.program)
        for key in ('StdVW', 'StemSnapV'):
            if hasattr(top.Private, key):
                delattr(top.Private, key)
                top.Private.rawDict.pop(key, None)
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def page(faces, sizes):
    """One block per variant/weight/size, black on white, 30em wide."""
    css = ''.join(f"@font-face{{font-family:'{family}';src:url('{file}') format('opentype');font-weight:{weight}}}"
                  for family, file, weight in faces)
    blocks = ''.join(
        f'<p id="{family}-{str(size).replace(".", "_")}" style="font-family:\'{family}\';font-weight:{weight};'
        f'font-size:{size}px">{PARAGRAPH}</p>'
        for family, _, weight in faces for size in sizes)
    return ('<!doctype html><meta charset="utf-8"><style>' + css +
            'html{background:#fff}body{margin:0;padding:8px;color:#000;'
            'font-kerning:normal;-webkit-font-smoothing:antialiased}'
            'p{width:30em;line-height:1.5;margin:0 0 8px;white-space:normal}</style>' + blocks)


def ink(png):
    """Summed coverage (0 = white, 1 = black) of a grayscale screenshot."""
    from PIL import Image
    import numpy
    pixels = numpy.asarray(Image.open(io.BytesIO(png)).convert('L'), dtype=float)
    return float((255 - pixels).sum() / 255)


def measure(output, browser='chromium', ratios=(1,), channel=None, grayscale=False, fonts=ROOT / 'fonts'):
    """Render and score every variant, weight and app size; return the report."""
    from playwright.sync_api import sync_playwright
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        faces = []
        for weight, style in WEIGHTS.items():
            for variant in VARIANTS:
                name = f'{style}-{variant}.otf'
                (folder / name).write_bytes(variant_font(fonts / f'SEIReader-{style}.otf', variant))
                faces.append((f'{style}-{variant}', name, weight))
        (folder / 'index.html').write_text(page(faces, APP_SIZES), encoding='utf-8')
        label = (channel or browser) + ('-grayscale' if grayscale else '')
        report = {'browser': label, 'os': platform.platform(), 'sizes_px': list(APP_SIZES),
                  'jump_limit': JUMP_LIMIT, 'paragraph': PARAGRAPH, 'results': {}}
        with sync_playwright() as playwright:
            engine = getattr(playwright, browser).launch(**({'channel': channel} if channel else {}),
                                                         args=['--disable-lcd-text'] if grayscale else [])
            report['browser_version'] = engine.version
            for ratio in ratios:
                tab = engine.new_page(viewport={'width': 1400, 'height': 900}, device_scale_factor=ratio)
                tab.goto((folder / 'index.html').as_uri())
                tab.evaluate('document.fonts.ready')
                loaded = tab.evaluate('[...document.fonts].filter(f => f.status === "loaded").length')
                assert loaded == len(faces), f'{loaded} of {len(faces)} faces loaded'
                for family, _, weight in faces:
                    scores = []
                    for size in APP_SIZES:
                        shot = tab.locator(f'#{family}-{str(size).replace(".", "_")}').screenshot()
                        if family.endswith('-shipped'):
                            (output / f'{label}-dpr{ratio}-{family}-{size}.png').write_bytes(shot)
                        scores.append(ink(shot) / (size * ratio) ** 2)
                    base = scores[0]
                    relative = [round(score / base, 3) for score in scores]
                    steps = [round(after / before - 1, 3) for before, after in zip(scores, scores[1:])]
                    report['results'][f'dpr{ratio}/{family}'] = {
                        'ink_per_px2': [round(score, 2) for score in scores],
                        'relative_to_15px': relative,
                        'steps': steps,
                        'largest_step': max(steps, key=abs),
                        'jump': any(abs(step) > JUMP_LIMIT for step in steps),
                    }
                tab.close()
            engine.close()
    (output / f'size-density-{report["browser"]}.json').write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                                         encoding='utf-8')
    return report


def summary(report):
    """One line per measurement, readable in a CI log."""
    lines = [f"{report['browser']} {report['browser_version']} on {report['os']}",
             'sizes ' + ' '.join(f'{size:>6}' for size in report['sizes_px'])]
    for key, row in report['results'].items():
        flag = 'JUMP' if row['jump'] else 'ok'
        lines.append(f"{key:<26} " + ' '.join(f'{value:>6.3f}' for value in row['relative_to_15px'])
                     + f"  largest step {row['largest_step']:+.3f} {flag}")
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('output')
    parser.add_argument('--browser', default='chromium', choices=('chromium', 'webkit', 'firefox'))
    parser.add_argument('--channel', help='an installed browser instead of the bundled one')
    parser.add_argument('--grayscale', action='store_true', help='Chromium only: no subpixel text')
    parser.add_argument('--dpr', type=float, nargs='+', default=[1])
    args = parser.parse_args()
    ratios = [int(r) if r == int(r) else r for r in args.dpr]
    print(summary(measure(args.output, args.browser, ratios, args.channel, args.grayscale)))
