"""Build the SEIHouse Noto redraw candidate fonts from letters.py."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pathops  # noqa: E402
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString  # noqa: E402
from fontTools.fontBuilder import FontBuilder  # noqa: E402
from fontTools.pens.t2CharStringPen import T2CharStringPen  # noqa: E402

import letters  # noqa: E402
import spacing  # noqa: E402

UPM = 1000
VERSION = '0.010'
FAMILY = 'SEIHouse Noto'
WEIGHTS = [dict(name='Light', weight=.86, cls=300), dict(name='Regular', weight=1.0, cls=400),
           dict(name='Medium', weight=1.2, cls=500), dict(name='Bold', weight=1.46, cls=700)]
# True italics: the same four weights, with italic lowercase forms, condensed and slanted.
ITALICS = [dict(spec, name='Italic' if spec['name'] == 'Regular' else spec['name']+' Italic', italic=True)
           for spec in WEIGHTS]


# Alignment zones and standard stems, for rasterisers and later autohinting.
PRIVATE = dict(BlueValues=[-letters.OV, 0, letters.X, letters.X+letters.OV, letters.CAP, letters.CAP+letters.OV,
                           letters.ASC, letters.ASC+letters.OV],
               OtherBlues=[letters.DESC-letters.OV, letters.DESC], BlueScale=.0375, BlueShift=7, BlueFuzz=0)


def glyph_name(char):
    return 'space' if char == ' ' else f'u{ord(char):04X}'


def build_font(spec, out_dir=None):
    italic = spec.get('italic', False)
    source, groups, ghosts = letters.draw(spec['weight'], spec.get('tilt', 0.0), italic=italic)
    box = pathops.Path()
    pen = box.getPen()
    for pts in ([(90, 0), (510, 0), (510, 700), (90, 700)], [(160, 70), (160, 630), (440, 630), (440, 70)]):
        pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()
    glyphs = {'.notdef': (600, box)}
    cmap = {}
    for char, (width, path) in source.items():
        cmap[ord(char)] = glyph_name(char)
        glyphs[glyph_name(char)] = (width, path)
    if 'space' not in glyphs:
        glyphs['space'] = (248, pathops.Path()); cmap[32] = 'space'
    order = list(glyphs)
    metrics, charstrings = {}, {}
    for name, (width, path) in glyphs.items():
        pen = T2CharStringPen(width, None)
        path.draw(pen)
        charstrings[name] = pen.getCharString(private=None, globalSubrs=None)
        metrics[name] = (width, round(path.bounds[0]) if list(path.verbs) else 0)
    style = spec['name']
    psname = f"SEIHouseNoto-{style.replace(' ', '')}"
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=960, descent=-260)
    ribbi = style in ('Regular', 'Bold', 'Italic', 'Bold Italic')
    weight_name = style.replace(' Italic', '').replace('Italic', 'Regular')
    fb.setupNameTable(dict(
        familyName=FAMILY if ribbi else f'{FAMILY} {weight_name}',
        styleName=style if ribbi else ('Italic' if italic else 'Regular'),
        **({} if ribbi else dict(typographicFamily=FAMILY, typographicSubfamily=style)), uniqueFontIdentifier=f'{psname}-{VERSION}',
        fullName=f'{FAMILY} {style}', psName=psname, version='Version '+VERSION,
        copyright='Original drawings for SEIHouse Productions LLC, 2026.',
        description='Latin design candidate. Not a production or multilingual release.'))
    fb.setupOS2(version=4, sTypoAscender=960, sTypoDescender=-260, sTypoLineGap=0, usWinAscent=1000,
                usWinDescent=300, sxHeight=letters.X, sCapHeight=letters.CAP, usWeightClass=spec['cls'],
                fsSelection=(0xC0 if style == 'Regular' else 0xA0 if weight_name == 'Bold' else 0x80) | (0x01 if italic else 0),
                achVendID='SEIH')
    fb.setupPost(italicAngle=-letters.SLANT if italic else 0)
    if italic:
        fb.font['hhea'].caretSlopeRise = 1000
        fb.font['hhea'].caretSlopeRun = round(1000*math.tan(math.radians(letters.SLANT)))
    fb.font['head'].fontRevision = float(VERSION)
    fb.font['OS/2'].ulCodePageRange1 = 1
    fb.font['OS/2'].ulCodePageRange2 = 0
    fb.setupCFF(psname, dict(FullName=f'{FAMILY} {style}', FamilyName=FAMILY, Weight=weight_name,
                             **(dict(ItalicAngle=-letters.SLANT) if italic else {})), charstrings, PRIVATE)
    pairs, exceptions = spacing.kerning(source, groups, ghosts=ghosts)
    members = {}
    for composite, base in groups.items():
        members.setdefault(base, []).append(composite)
    kerned = sorted({c for pair in pairs for c in pair})
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    for c in kerned:
        fea.append(f"@k_{glyph_name(c)} = [{' '.join(glyph_name(m) for m in [c, *members.get(c, [])])}];")
    fea.append('feature kern {')
    fea += [f'pos {glyph_name(a)} {glyph_name(b)} {v};' for (a, b), v in exceptions.items()]
    fea += [f'pos @k_{glyph_name(a)} @k_{glyph_name(b)} {v};' for (a, b), v in pairs.items()]
    fea.append('} kern;')
    addOpenTypeFeaturesFromString(fb.font, '\n'.join(fea))
    fb.font['head'].macStyle = (1 if weight_name == 'Bold' else 0) | (2 if italic else 0)
    fb.font['head'].created = fb.font['head'].modified = 3877200000
    out = Path(out_dir or ROOT/'fonts')
    out.mkdir(parents=True, exist_ok=True)
    fb.save(out/f'{psname}.otf')
    fb.font.flavor = 'woff2'
    fb.save(out/f'{psname}.woff2')
    return dict(style=style, psname=psname, glyphs=len(order), kerning_pairs=len(pairs)+len(exceptions), characters=''.join(source),
                sha256=hashlib.sha256((out/f'{psname}.woff2').read_bytes()).hexdigest())


def glyph_proof(psname='SEIHouseNoto-Regular', columns=12):
    """Draw every encoded glyph from the built font, with baseline and x-height guides."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.ttLib import TTFont
    with TTFont(ROOT/'fonts'/f'{psname}.otf') as font:
        cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
        codes = [c for c in sorted(cmap) if c not in (0x20, 0xA0)]
        rows = -(-len(codes)//columns)
        cell_w, cell_h = 100, 132
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{columns*cell_w+24}" height="{rows*cell_h+56}" '
                 f'viewBox="0 0 {columns*cell_w+24} {rows*cell_h+56}">',
                 '<rect width="100%" height="100%" fill="#fffcf6"/>',
                 f'<text x="12" y="28" font-family="sans-serif" font-size="16" fill="#273b35">'
                 f'SEIHouse Noto Redraw 02 {psname.split("-")[1]}: every encoded glyph ({len(codes)})</text>']
        for i, code in enumerate(codes):
            x, y = (i % columns)*cell_w+12, (i//columns)*cell_h+48
            pen = SVGPathPen(glyphs)
            glyphs[cmap[code]].draw(pen)
            advance = font['hmtx'][cmap[code]][0]
            offset = (cell_w-8-advance*.08)/2
            parts += [f'<path d="M{x} {y+84} h{cell_w-8} M{x} {y+84-letters.X*.08:.1f} h{cell_w-8}" stroke="#e2e4d8" fill="none"/>',
                      f'<path d="{pen.getCommands()}" transform="translate({x+offset:.1f} {y+84}) scale(.08 -.08)" fill="#273b35"/>',
                      f'<text x="{x}" y="{y+116}" font-family="sans-serif" font-size="9" fill="#65736a">U+{code:04X}</text>']
        parts.append('</svg>')
        (ROOT/'proofs').mkdir(exist_ok=True)
        (ROOT/'proofs'/('redraw-glyphs.svg' if psname.endswith('-Regular') else 'redraw-glyphs-italic.svg')).write_text('\n'.join(parts)+'\n', encoding='utf-8')


def sync_page(characters):
    """Tell the comparison page exactly which characters the fonts hold."""
    import re
    page = (ROOT/'index.html').read_text(encoding='utf-8')
    literal = json.dumps(''.join(sorted(set(characters) - {'\u00a0'})), ensure_ascii=False)
    page, count = re.subn(r'/\*CHARSET\*/.*?/\*END\*/', lambda m: f'/*CHARSET*/{literal}/*END*/', page, flags=re.S)
    if count != 1:
        raise ValueError('index.html has no single CHARSET marker')
    (ROOT/'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    reports = [build_font(spec) for spec in WEIGHTS + ITALICS]
    (ROOT/'manifest.json').write_text(json.dumps(dict(
        family=FAMILY, version=VERSION, status='candidate', foundation='Balanced (Study B)',
        metrics=dict(unitsPerEm=UPM, xHeight=letters.X, capHeight=letters.CAP, ascender=letters.ASC, descender=letters.DESC),
        fonts=reports), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    sync_page(reports[0]['characters'])
    glyph_proof()
    glyph_proof('SEIHouseNoto-Italic')
    print(json.dumps([{k: r[k] for k in ('style', 'glyphs', 'kerning_pairs', 'sha256')} for r in reports], indent=2))
