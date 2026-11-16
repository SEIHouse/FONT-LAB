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
from fontTools.otlLib.builder import buildStatTable  # noqa: E402
from fontTools.pens.t2CharStringPen import T2CharStringPen  # noqa: E402

import letters  # noqa: E402
import spacing  # noqa: E402

UPM = 1000
VERSION = '0.011'
FAMILY = 'SEIHouse Noto'
WEIGHTS = [dict(name='Light', weight=.86, cls=300), dict(name='Regular', weight=1.0, cls=400),
           dict(name='Medium', weight=1.2, cls=500), dict(name='Bold', weight=1.46, cls=700)]
# True italics: the same four weights, with italic lowercase forms, condensed and slanted.
ITALICS = [dict(spec, name='Italic' if spec['name'] == 'Regular' else spec['name']+' Italic', italic=True)
           for spec in WEIGHTS]
# Zero-reflow Night grade for light/reading weights (Light, Regular, Medium) in upright and italic.
NIGHT_WEIGHTS = ('Light', 'Regular', 'Medium')
NIGHTS = [dict(spec, name=f"{spec['name']} Night", grade=letters.NIGHT_GRADE, day_style=spec['name'])
          for spec in WEIGHTS + ITALICS
          if spec['name'].replace(' Italic', '').replace('Italic', 'Regular') in NIGHT_WEIGHTS]


# Alignment zones and standard stems, for rasterisers and later autohinting.
PRIVATE = dict(BlueValues=[-letters.OV, 0, letters.X, letters.X+letters.OV, letters.CAP, letters.CAP+letters.OV,
                           letters.ASC, letters.ASC+letters.OV],
               OtherBlues=[letters.DESC-letters.OV, letters.DESC], BlueScale=.0375, BlueShift=7, BlueFuzz=0)


def glyph_name(char):
    return 'space' if char == ' ' else f'u{ord(char):04X}'


def build_features(source, groups, layout, pairs, exceptions):
    """Build GDEF, GSUB (ccmp, locl) and GPOS (mark, mkmk, kern) OpenType features."""
    import unicodedata
    marks = layout['marks']
    bases = layout['bases']
    by_kind = {kind: [] for kind in ('top', 'bottom', 'horn', 'ogonek')}
    for ch, info in marks.items():
        by_kind[info['kind']].append((glyph_name(ch), info))

    lines = [
        'languagesystem DFLT dflt;',
        'languagesystem latn dflt;',
        'languagesystem latn ROM;',
        'languagesystem latn MOL;',
        'languagesystem latn TRK;',
        'languagesystem latn AZE;',
    ]
    for kind, items in by_kind.items():
        lines.append(f'@{kind.upper()} = [{" ".join(name for name, _ in items)}];')
        for name, info in items:
            ax, ay = info['attach']
            lines.append(f'markClass {name} <anchor {ax} {ay}> @MC_{kind};')
    lines.append('@TOP_HORN = [@TOP @HORN];')

    mark_names = {glyph_name(ch) for ch in marks}
    base_names = [glyph_name(ch) for ch in source if ch not in (' ', '\u00a0') and ch not in marks]
    base_names.extend(layout['extras'])
    lines += [
        'table GDEF {',
        f' GlyphClassDef [{" ".join(base_names)}], , [{" ".join(sorted(mark_names))}], ;',
        '} GDEF;',
    ]

    cmap_map = {ord(ch): glyph_name(ch) for ch in source}
    below_subs, top_subs = [], []
    for code, name in sorted(cmap_map.items()):
        nfd = unicodedata.normalize('NFD', chr(code))
        if len(nfd) == 2 and all(ord(c) in cmap_map for c in nfd):
            b_char, m_char = nfd[0], nfd[1]
            if m_char not in marks:
                continue
            b_name, m_name = cmap_map[ord(b_char)], cmap_map[ord(m_char)]
            if marks[m_char]['kind'] in ('bottom', 'ogonek'):
                below_subs.append(f'  sub {b_name} {m_name} by {name};')
            else:
                top_subs.append(f'  sub {b_name} {m_name} by {name};')
                if b_char == 'i':
                    top_subs.append(f'  sub u0131 {m_name} by {name};')
                elif b_char == 'j':
                    top_subs.append(f'  sub u0237 {m_name} by {name};')
    if 0x0067 in cmap_map and 0x0312 in cmap_map and 0x0123 in cmap_map:
        top_subs.append('  sub u0067 u0312 by u0123;')

    lines.append('feature ccmp {')
    if below_subs:
        lines.append(' lookup PrecomposedBelow {')
        lines.extend(below_subs)
        lines.append(' } PrecomposedBelow;')
    if top_subs:
        lines.append(' lookup PrecomposedTop {')
        lines.append('  lookupflag UseMarkFilteringSet @TOP_HORN;')
        lines.extend(top_subs)
        lines.append(' } PrecomposedTop;')
    lines += [
        ' lookup Dotless {',
        '  lookupflag UseMarkFilteringSet @TOP;',
        "  sub u0069' @TOP by u0131;",
        "  sub u006A' @TOP by u0237;",
        "  sub u012F' @TOP by u012F.dotless;",
        ' } Dotless;',
        '} ccmp;',
    ]

    lines += [
        'feature locl {',
        ' script latn;',
        ' language ROM;',
        '  sub u015E by u0218;',
        '  sub u015F by u0219;',
        '  sub u0162 by u021A;',
        '  sub u0163 by u021B;',
        ' language MOL;',
        '  sub u015E by u0218;',
        '  sub u015F by u0219;',
        '  sub u0162 by u021A;',
        '  sub u0163 by u021B;',
        '} locl;',
    ]

    lines.append('feature mark {')
    for key, anchors in bases.items():
        gname = glyph_name(key) if len(key) == 1 else key
        anchor_str = ' '.join(f'<anchor {ax} {ay}> mark @MC_{kind}' for kind, (ax, ay) in anchors.items())
        lines.append(f' pos base {gname} {anchor_str};')
    lines.append('} mark;')

    lines.append('feature mkmk {')
    for kind in ('top', 'bottom'):
        lines += [f' lookup Stack_{kind} {{', f'  lookupflag MarkAttachmentType @{kind.upper()};']
        for name, info in by_kind[kind]:
            sx, sy = info['stack']
            lines.append(f'  pos mark {name} <anchor {sx} {sy}> mark @MC_{kind};')
        lines.append(f' }} Stack_{kind};')
    lines.append('} mkmk;')

    members = {}
    for composite, base in groups.items():
        members.setdefault(base, []).append(composite)
    kerned = sorted({c for pair in pairs for c in pair})
    for c in kerned:
        mnames = [glyph_name(m) for m in [c, *members.get(c, [])]]
        if c == 'i' and 'u012F.dotless' in layout['extras']:
            mnames.append('u012F.dotless')
        lines.append(f"@k_{glyph_name(c)} = [{' '.join(mnames)}];")
    lines.append('feature kern {')
    lines.append(' lookupflag IgnoreMarks;')
    lines += [f' pos {glyph_name(a)} {glyph_name(b)} {v};' for (a, b), v in exceptions.items()]
    lines += [f' pos @k_{glyph_name(a)} @k_{glyph_name(b)} {v};' for (a, b), v in pairs.items()]
    lines.append('} kern;')
    return '\n'.join(lines) + '\n'


def build_font(spec, out_dir=None, day_cache=None):
    italic = spec.get('italic', False)
    grade = spec.get('grade', 0)
    day_style = spec.get('day_style')
    day_data = None
    if grade and day_style:
        if day_cache is not None and day_style in day_cache:
            day_source, day_groups, day_ghosts, day_layout, day_pairs, day_exceptions, day_fea = day_cache[day_style]
        else:
            day_spec = next(s for s in WEIGHTS + ITALICS if s['name'] == day_style)
            day_source, day_groups, day_ghosts, day_layout = letters.draw(
                day_spec['weight'], day_spec.get('tilt', 0.0), italic=day_spec.get('italic', False), with_layout=True)
            day_pairs, day_exceptions = spacing.kerning(day_source, day_groups, ghosts=day_ghosts)
            day_fea = build_features(day_source, day_groups, day_layout, day_pairs, day_exceptions)
            if day_cache is not None:
                day_cache[day_style] = (day_source, day_groups, day_ghosts, day_layout, day_pairs, day_exceptions, day_fea)
        day_data = (day_source, day_groups, day_ghosts, day_layout)
    source, groups, ghosts, layout = letters.draw(
        spec['weight'], spec.get('tilt', 0.0), italic=italic, grade=grade, day=day_data, with_layout=True)
    box = pathops.Path()
    pen = box.getPen()
    for pts in ([(90, 0), (510, 0), (510, 700), (90, 700)], [(160, 70), (160, 630), (440, 630), (440, 70)]):
        pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()
    glyphs = {'.notdef': (600, box)}
    cmap = {}
    for char, (width, path) in source.items():
        cmap[ord(char)] = glyph_name(char)
        glyphs[glyph_name(char)] = (width, path)
    for gname, (width, path) in layout['extras'].items():
        glyphs[gname] = (width, path)
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
    weight_name = style.removesuffix(' Night').replace(' Italic', '').replace('Italic', 'Regular')
    suffix = ' Night' if grade else ''
    legacy_family = FAMILY if ribbi else (
        f'{FAMILY} Night' if grade and weight_name == 'Regular' else f'{FAMILY} {weight_name}{suffix}')
    fb.setupNameTable(dict(
        familyName=legacy_family,
        styleName=style if ribbi else ('Italic' if italic else 'Regular'),
        **({} if ribbi else dict(typographicFamily=FAMILY, typographicSubfamily=style)), uniqueFontIdentifier=f'{psname}-{VERSION}',
        fullName=f'{FAMILY} {style}', psName=psname, version='Version '+VERSION,
        copyright='Original drawings for SEIHouse Productions LLC, 2026.',
        description='Latin design candidate. Not a production or multilingual release.'))
    fb.setupOS2(version=4, sTypoAscender=960, sTypoDescender=-260, sTypoLineGap=0, usWinAscent=1180,
                usWinDescent=420, sxHeight=letters.X, sCapHeight=letters.CAP, usWeightClass=spec['cls'], fsType=0,
                fsSelection=(0xC0 if weight_name != 'Bold' and not italic else 0xA0 if weight_name == 'Bold' else 0x80) | (0x01 if italic else 0),
                achVendID='SEIH')
    fb.setupPost(italicAngle=-letters.SLANT if italic else 0, underlinePosition=-120, underlineThickness=60)
    if italic:
        fb.font['hhea'].caretSlopeRise = 1000
        fb.font['hhea'].caretSlopeRun = round(1000*math.tan(math.radians(letters.SLANT)))
    fb.font['head'].fontRevision = float(VERSION)
    fb.font['OS/2'].recalcUnicodeRanges(fb.font)
    fb.font['OS/2'].recalcCodePageRanges(fb.font)
    axes = [dict(tag='wght', name='Weight', values=[dict(value=spec['cls'], name=weight_name, flags=(0x2 if weight_name == 'Regular' else 0))])]
    if grade:
        axes.append(dict(tag='GRAD', name='Grade', values=[dict(value=grade, name='Night')]))
    axes.append(dict(tag='ital', name='Italic', values=[dict(value=1, name='Italic')] if italic else
                     [dict(value=0, name='Roman', flags=0x2, linkedValue=1)]))
    buildStatTable(fb.font, axes, elidedFallbackName=2)
    sh_ref = letters.Sheet(spec['weight'], spec.get('tilt', 0.0), italic=italic, grade=grade)
    private = dict(PRIVATE, StdVW=round(sh_ref.lc.thick*sh_ref.wide*(letters.CONDENSE if italic else 1)),
                   StdHW=round(sh_ref.lc.thin))
    fb.setupCFF(psname, dict(FullName=f'{FAMILY} {style}', FamilyName=FAMILY, Weight=weight_name,
                             **(dict(ItalicAngle=-letters.SLANT) if italic else {})), charstrings, private)
    if grade and day_style:
        pairs, exceptions, fea_text = day_pairs, day_exceptions, day_fea
    else:
        pairs, exceptions = spacing.kerning(source, groups, ghosts=ghosts)
        fea_text = build_features(source, groups, layout, pairs, exceptions)
        if day_cache is not None:
            day_cache[spec['name']] = (source, groups, ghosts, layout, pairs, exceptions, fea_text)
    addOpenTypeFeaturesFromString(fb.font, fea_text)
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
    day_cache = {}
    reports = [build_font(spec, day_cache=day_cache) for spec in WEIGHTS + ITALICS + NIGHTS]
    (ROOT/'manifest.json').write_text(json.dumps(dict(
        family=FAMILY, version=VERSION, status='candidate', foundation='Balanced (Study B)',
        metrics=dict(unitsPerEm=UPM, xHeight=letters.X, capHeight=letters.CAP, ascender=letters.ASC, descender=letters.DESC),
        fonts=reports), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    sync_page(reports[0]['characters'])
    glyph_proof()
    glyph_proof('SEIHouseNoto-Italic')
    print(json.dumps([{k: r[k] for k in ('style', 'glyphs', 'kerning_pairs', 'sha256')} for r in reports], indent=2))
