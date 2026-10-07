"""Render/audit every exported Display glyph at 400px; any outline flag fails.

Checks the actual hinted CFF, including unencoded glyphs and web-font delivery.
Proof pages keep the 400px em size, rather than shrinking glyphs to fit cells.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct
import zlib

import freetype
import unicodedata
from display.counter_geometry import counter_flags, topology_flags
from fontTools.ttLib import TTFont
import pathops

from display.shape_geometry import contours, chord_turn, length

ROOT = Path(__file__).resolve().parent
CUTS = ('soft', 'edge', 'ink', 'wide')
SIZE = 400
DESIGN = ROOT/'docs/proofs/display-step1/design.json'
SHARED_REFERENCE = ROOT/'tests/fixtures/reader-0.39-identity.json'
SHARED_DESIGN = ROOT/'tests/fixtures/display-step2-design-0.39.json'
COUNTER_TOPOLOGY = ROOT/'tests/fixtures/display-counter-topology.json'
ALTERNATE_TOPOLOGY = ROOT/'tests/fixtures/display-alternate-topology.json'
BLANK_GLYPHS = frozenset(('space', 'uni2009', 'uni202F'))
WEB_TABLES = ('CFF ', 'hmtx', 'GPOS', 'GSUB', 'GDEF', 'OS/2', 'hhea')


def design_flags(font, cut, reference, shared_design=None, variants=None):
    """Keep original metrics, encoded mappings and the approved alternate inventory.

    Step 2 adds combining marks, numeric alternates and Latin letters from the
    shared Reader. Original encoded mappings and vertical metrics remain
    protected, with one exact Edge clipping-height exception for inherited
    Vietnamese ink. Advances follow the reviewed Reader 0.28 inheritance
    deltas; every current advance is frozen independently. Step 4 may append
    only the explicitly supplied stylistic glyphs after the shared inventory.
    """
    found = []
    expected = reference['fonts'][cut]
    if not set(expected['order']) <= set(font.getGlyphOrder()):
        found.append(dict(kind='glyph-inventory'))
    cmap = {str(code): name for code, name in font.getBestCmap().items()}
    if any(cmap.get(code) != name for code, name in expected['cmap'].items()):
        found.append(dict(kind='character-map'))
    current = shared_design['fonts'][cut] if shared_design is not None else expected
    if shared_design is not None:
        extra = sorted({name for spec in (variants or {}).values() for choice, name in spec['choices'].items()
                        if choice != spec['default']})
        if font.getGlyphOrder()[:len(current['order'])] != current['order'] or sorted(font.getGlyphOrder()[len(current['order']):]) != extra:
            found.append(dict(kind='shared-glyph-inventory'))
        if cmap != current['cmap']:
            found.append(dict(kind='shared-character-map'))
    for name, width in current['advances'].items():
        if name in font.getGlyphOrder() and font['hmtx'][name][0] != width:
            found.append(dict(kind='advance-width', glyph=name, before=width,
                              after=font['hmtx'][name][0]))
    for table, fields in current['metrics'].items():
        for field, value in fields.items():
            if getattr(font[table], field) != value:
                found.append(dict(kind='line-metric', table=table, field=field))
    return found


def validate_design_reference(original, shared, reader):
    """Reject an inconsistent fixture rather than blessing arbitrary changes.

    The Step 1 evidence is immutable. Every approved changed old advance must
    identify its original value, final value and documented inherited reason.
    The Step 2 fixture has no regeneration option in this verifier.
    """
    if shared['cuts'] != original['cuts']:
        raise ValueError('Step 2 cannot change original cut settings')
    if shared['reader_skeleton_sha256'] != reader['reader_skeleton_sha256']:
        raise ValueError('Step 2 must use the frozen Reader skeleton tables')
    for cut in CUTS:
        before, after = original['fonts'][cut], shared['fonts'][cut]
        metric_changes = after.get('previous_metric_changes', {})
        changed_metrics = {f'{table}.{field}' for table, fields in before['metrics'].items()
                           for field, value in fields.items()
                           if after['metrics'][table][field] != value}
        if set(metric_changes) != changed_metrics:
            raise ValueError(f'{cut}: every clipping metric difference must be listed explicitly')
        for key, row in metric_changes.items():
            # This is the single reviewed metadata exception, derived from the
            # final Edge CFF's Vietnamese ink. Never permit arbitrary changes
            # to baseline/line spacing, other cuts, or later clipping extents.
            if ((cut, row['table'], row['field'], row['before'], row['after'], row['delta'], row['reason']) !=
                    ('edge', 'OS/2', 'usWinAscent', 2200, 2220, 20, 'phase4-edge-vietnamese-clipping') or
                    key != 'OS/2.usWinAscent' or row['reason'] not in shared['reasons'] or
                    row['before'] != before['metrics'][row['table']][row['field']] or
                    row['after'] != after['metrics'][row['table']][row['field']]):
                raise ValueError(f'{cut}/{key}: unapproved clipping metric difference')
        changes = after['previous_advance_changes']
        changed = {name for name, width in before['advances'].items()
                   if after['advances'].get(name) != width}
        if set(changes) != changed:
            raise ValueError(f'{cut}: every inherited advance difference must be listed explicitly')
        for name, row in changes.items():
            if (row['before'] != before['advances'][name] or
                    row['after'] != after['advances'][name] or
                    row['delta'] != row['after']-row['before'] or
                    row['reason'] not in shared['reasons']):
                raise ValueError(f'{cut}/{name}: inconsistent inherited advance evidence')


def outline(font, name):
    """Read exported curves, including Type 2 rounding and hint-tool changes."""
    path = pathops.Path()
    font.getGlyphSet()[name].draw(path.getPen())
    return path


def blank_flags(name, path):
    """Only the explicit space glyphs may have no exported ink."""
    return [] if path or name in BLANK_GLYPHS else [dict(kind='empty-glyph')]


def web_flags(font, woff):
    """Require identical layout and vertical metrics in the browser delivery."""
    found = []
    if font.getGlyphOrder() != woff.getGlyphOrder() or font.getBestCmap() != woff.getBestCmap():
        found.append(dict(kind='web-inventory'))
    for table in WEB_TABLES:
        if font[table].compile(font) != woff[table].compile(woff):
            found.append(dict(kind='web-table', table=table))
    return found


def flags(path, upm=2000):
    """Reject small contour debris, tiny segments, needle corners and overlaps.

    A needle must have a short shoulder as well as an acute tip; full-size star,
    arrow and letter corners are not debris. Distances are in pixels at 400px.
    """
    scale = SIZE/upm
    found = []
    for ci, contour in enumerate(path.contours):
        if abs(contour.area)*scale**2 < 1:
            found.append(dict(kind='micro-contour', contour=ci,
                              area_px2=round(abs(contour.area)*scale**2, 4)))
    for ci, segments in enumerate(contours(path)):
        for si, before in enumerate(segments):
            after = segments[(si+1) % len(segments)]
            short = min(length(before), length(after))*scale
            if length(before)*scale < .4:
                found.append(dict(kind='tiny-segment', contour=ci, segment=si,
                                  length_px=round(length(before)*scale, 4)))
            angle = chord_turn(before, after, 2/scale)
            if abs(angle) > 150 and short < 8:
                found.append(dict(kind='convex-spike' if angle > 0 else 'concave-spike',
                                  contour=ci, segment=si, turn=round(angle, 2),
                                  shoulder_px=round(short, 4), point=list(before[-1])))
            previous = chord_turn(segments[si-1], before, 2/scale)
            following = chord_turn(after, segments[(si+2) % len(segments)], 2/scale)
            if (60 < abs(angle) <= 150 and short < 16 and
                    max(length(before), length(after))*scale < 24 and
                    angle*previous < 0 and angle*following < 0 and
                    abs(previous) > 10 and abs(following) > 10 and
                    abs(previous+angle+following) < 15):
                found.append(dict(kind='spur-or-notch', contour=ci, segment=si,
                                  turn=round(angle, 2), shoulder_px=round(short, 4),
                                  point=list(before[-1])))
    if path:
        clean = path.transform()
        clean.simplify(fix_winding=True)
        # Signed area counts repeated ink; simplified area counts it once.
        leftover = abs(abs(path.area)-abs(clean.area))*scale**2
        if leftover > .25:
            found.append(dict(kind='self-overlap', area_px2=round(leftover, 4)))
        odd = path.transform()
        odd.fillType = pathops.FillType.EVEN_ODD
        odd.simplify(fix_winding=True)
        ambiguity = abs(abs(clean.area)-abs(odd.area))*scale**2
        if ambiguity > .25:
            found.append(dict(kind='fill-rule-disagreement', area_px2=round(ambiguity, 4)))
    return found


def render(face, index, size=SIZE):
    """Rasterize by glyph ID so .notdef, spaces and unencoded glyphs are covered."""
    face.set_pixel_sizes(0, size)
    face.load_glyph(index, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING |
                    freetype.FT_LOAD_NO_BITMAP)
    bitmap = face.glyph.bitmap
    pitch, width, height = bitmap.pitch, bitmap.width, bitmap.rows
    data = bytes(bitmap.buffer)
    rows = [data[y*abs(pitch):y*abs(pitch)+width] for y in range(height)]
    if pitch < 0:
        rows.reverse()
    return dict(width=width, height=height, left=face.glyph.bitmap_left,
                top=face.glyph.bitmap_top, pixels=b''.join(rows))


def write_png(file, width, height, pixels):
    """Write a grayscale PNG with only the standard library."""
    def chunk(kind, body):
        return (struct.pack('>I', len(body)) + kind + body +
                struct.pack('>I', zlib.crc32(kind+body) & 0xffffffff))
    rows = b''.join(b'\0' + pixels[y*width:(y+1)*width] for y in range(height))
    file.write_bytes(b'\x89PNG\r\n\x1a\n' +
                     chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def label_face():
    """Use an installed UI font for proof labels, never for the glyph specimens."""
    for file in (Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/segoeui.ttf',
                 Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')):
        if file.exists():
            return freetype.Face(str(file))
    return None


def paste(canvas, width, height, bitmap, x, y):
    """Composite black glyph coverage onto a white grayscale canvas."""
    for row in range(bitmap['height']):
        yy = y + row
        if not 0 <= yy < height:
            continue
        for col in range(bitmap['width']):
            xx = x + col
            if 0 <= xx < width:
                pos = yy*width+xx
                canvas[pos] = min(canvas[pos], 255-bitmap['pixels'][row*bitmap['width']+col])


def label(canvas, width, height, face, text, x, baseline, size=16):
    """Draw readable glyph IDs and page metadata above the 400px specimens."""
    if face is None:
        return
    for char in text:
        bitmap = render(face, face.get_char_index(ord(char)), size)
        paste(canvas, width, height, bitmap, x+bitmap['left'], baseline-bitmap['top'])
        x += face.glyph.advance.x >> 6


def proofs(directory, cut, items):
    """Paginate all glyphs in 8x8 sheets with a constant 400px em."""
    directory.mkdir(parents=True, exist_ok=True)
    ui = label_face()
    cell_w = max(240, max(item['bitmap']['width'] for item in items)+44)
    top = max(item['bitmap']['top'] for item in items)
    bottom = max(item['bitmap']['height']-item['bitmap']['top'] for item in items)
    cell_h = top+bottom+70
    files = []
    for first in range(0, len(items), 64):
        page = items[first:first+64]
        rows = math.ceil(len(page)/8)
        width, height = cell_w*8, cell_h*rows+60
        canvas = bytearray(b'\xff')*(width*height)
        label(canvas, width, height, ui, f'{cut.title()} | 400px em | glyphs {first}-{first+len(page)-1}', 20, 35, 24)
        for i, item in enumerate(page):
            x, y = (i % 8)*cell_w, (i//8)*cell_h+60
            label(canvas, width, height, ui, f"{item['index']}: {item['name']}", x+16, y+24)
            bitmap = item['bitmap']
            paste(canvas, width, height, bitmap, x+(cell_w-bitmap['width'])//2,
                  y+50+top-bitmap['top'])
        file = directory/f'{cut}-{first//64+1:02}.png'
        write_png(file, width, height, canvas)
        files.append(file.name)
    return files


def compare(directory, before_fonts, after_fonts):
    """Make compact 400px before/after proofs for the reported Ink/Edge glyphs."""
    directory.mkdir(parents=True, exist_ok=True)
    ui = label_face()
    for cut, text in (('ink', 'RayWkes'), ('edge', 'KR')):
        rows = []
        for root in (before_fonts, after_fonts):
            file = root/cut/f'SEIHouseDisplay-{cut.title()}.otf'
            with TTFont(file) as font:
                face = freetype.Face(str(file))
                rows.append([render(face, font.getGlyphID(font.getBestCmap()[ord(ch)])) for ch in text])
        bitmaps = rows[0]+rows[1]
        cell_w = max(240, max(b['width'] for b in bitmaps)+60)
        top = max(b['top'] for b in bitmaps)
        bottom = max(b['height']-b['top'] for b in bitmaps)
        cell_h = top+bottom+100
        width, height = cell_w*len(text), cell_h*2+60
        canvas = bytearray(b'\xff')*(width*height)
        label(canvas, width, height, ui, f'{cut.title()} | before / after | 400px em', 20, 36, 24)
        for row, specimens in enumerate(rows):
            y = row*cell_h+60
            label(canvas, width, height, ui, 'Before' if row == 0 else 'After', 20, y+28, 20)
            for column, (ch, bitmap) in enumerate(zip(text, specimens)):
                x = column*cell_w
                label(canvas, width, height, ui, ch, x+cell_w//2, y+56, 20)
                paste(canvas, width, height, bitmap, x+(cell_w-bitmap['width'])//2,
                      y+80+top-bitmap['top'])
        write_png(directory/f'{cut}-before-after.png', width, height, canvas)


def verify(fonts, proof_dir=None):
    """Audit/rasterize both formats of all four cuts and record reproducible evidence."""
    reference = json.loads(DESIGN.read_text(encoding='utf-8'))
    shared_design = json.loads(SHARED_DESIGN.read_text(encoding='utf-8'))
    shared = json.loads(SHARED_REFERENCE.read_text(encoding='utf-8'))
    validate_design_reference(reference, shared_design, shared)
    topology = json.loads(COUNTER_TOPOLOGY.read_text(encoding='utf-8'))
    alternate_topology = json.loads(ALTERNATE_TOPOLOGY.read_text(encoding='utf-8'))
    if topology['size_px'] != SIZE or set(topology['cuts']) != set(CUTS):
        raise ValueError('Counter topology fixture must cover all canonical cuts at 400px')
    report = dict(size_px=SIZE, flags=[], cuts={}, thresholds=dict(
        micro_contour_px2=1, tiny_segment_px=.4, spike_turn_degrees=150,
        spike_shoulder_px=8, spur_short_shoulder_px=16, spur_long_shoulder_px=24,
        spur_root_turn_degrees=15, overlap_px2=.25, counter_clearance_px=6,
        counter_min_area_px2=24, counter_min_relative_span=.2,
        aperture_min_area_px2=200, aperture_min_relative_area=.02))
    report['counter_topology_reference'] = dict(
        source_commit=topology['source_commit'],
        sha256=hashlib.sha256(COUNTER_TOPOLOGY.read_bytes()).hexdigest())
    report['alternate_topology_reference'] = dict(
        source_commit=alternate_topology['source_commit'],
        sha256=hashlib.sha256(ALTERNATE_TOPOLOGY.read_bytes()).hexdigest())
    for cut in CUTS:
        file = ROOT/f'display/cuts/{cut}.json'
        settings = json.loads(file.read_text(encoding='utf-8'))
        settings.pop('production', None)  # Delivery choices are separate from immutable drawing inputs.
        if settings.pop('alternates', None) != alternate_topology['defaults'][cut]:
            report['flags'].append(dict(cut=cut, kind='alternate-defaults'))
        canonical = json.dumps(settings, sort_keys=True,
                               ensure_ascii=False, separators=(',', ':')).encode()
        if hashlib.sha256(canonical).hexdigest() != reference['cuts'][cut]:
            report['flags'].append(dict(cut=cut, kind='cut-settings'))
    # The Reader tables are the sole source after Step 2. Their frozen source
    # hash predates this refactor; Step 1's original design/proofs stay intact.
    skeleton = (ROOT/'engine.js').read_text(encoding='utf-8').split('const P =', 1)[0]
    if hashlib.sha256(skeleton.encode()).hexdigest() != shared['reader_skeleton_sha256']:
        report['flags'].append(dict(cut='all', kind='letter-skeletons'))
    for cut in CUTS:
        otf = fonts/cut/f'SEIHouseDisplay-{cut.title()}.otf'
        web = otf.with_suffix('.woff2')
        with TTFont(otf) as font, TTFont(web) as woff:
            names = font.getGlyphOrder()
            snapshot = fonts/cut/f'spacing_{cut}.json'
            if not snapshot.exists(): snapshot = ROOT/'display'/f'spacing_{cut}.json'
            variants = json.loads(snapshot.read_text(encoding='utf-8'))['variants']
            if variants != alternate_topology['variants'][cut]:
                report['flags'].append(dict(cut=cut, kind='alternate-manifest'))
            report['flags'].extend(dict(cut=cut, **flag) for flag in design_flags(font, cut, reference, shared_design, variants))
            summary = dict(glyphs=len(names), rendered=0, flags=0,
                           sha256={file.suffix[1:]: hashlib.sha256(file.read_bytes()).hexdigest()
                                   for file in (otf, web)})
            report['flags'].extend(dict(cut=cut, **flag) for flag in web_flags(font, woff))
            face = freetype.Face(str(otf))
            stream = io.BytesIO()
            woff.flavor = None
            woff.save(stream)
            web_face = freetype.Face(io.BytesIO(stream.getvalue()))
            items = []
            # Symbols such as beamed music notes legitimately enclose exterior
            # space between their stems/heads. Test letter/number apertures;
            # enclosed counter clearance and all outline gates cover every glyph.
            aperture_names = {name for code, name in font.getBestCmap().items()
                              if unicodedata.category(chr(code))[0] in 'LN'}
            aperture_names.update(name for name in names if name.endswith(('.tf', '.numr', '.dnom')))
            aperture_names.update(name for spec in variants.values() for choice,name in spec['choices'].items()
                                  if choice != spec['default'])
            expected_topology = dict(topology['cuts'][cut]['glyphs'])
            expected_topology.update(alternate_topology['cuts'][cut]['glyphs'])
            if set(expected_topology) != aperture_names:
                report['flags'].append(dict(cut=cut, kind='counter-topology-inventory'))
            summary['topology_glyphs'] = len(aperture_names)
            for index, name in enumerate(names):
                path = outline(font, name)
                report['flags'].extend(dict(cut=cut, glyph=name, **flag) for flag in blank_flags(name, path))
                for flag in flags(path, font['head'].unitsPerEm):
                    report['flags'].append(dict(cut=cut, glyph=name, **flag))
                bitmap = render(face, index)
                report['flags'].extend(dict(cut=cut, glyph=name, **flag) for flag in
                                       counter_flags(bitmap, apertures=name in aperture_names))
                if name in aperture_names:
                    if name not in expected_topology:
                        report['flags'].append(dict(cut=cut, glyph=name, kind='missing-counter-topology'))
                    else:
                        report['flags'].extend(dict(cut=cut, glyph=name, **flag) for flag in
                                               topology_flags(bitmap, expected_topology[name]))
                web_bitmap = render(web_face, index)
                summary['rendered'] += 2
                if bitmap != web_bitmap:
                    report['flags'].append(dict(cut=cut, glyph=name, kind='web-render'))
                if bool(path) != bool(any(bitmap['pixels'])):
                    report['flags'].append(dict(cut=cut, glyph=name, kind='missing-raster'))
                items.append(dict(index=index, name=name, bitmap=bitmap))
            if proof_dir:
                summary['proofs'] = proofs(proof_dir, cut, items)
            summary['flags'] = sum(flag['cut'] == cut for flag in report['flags'])
            report['cuts'][cut] = summary
            print(f"{cut.title()}: {len(names)} glyphs, {summary['rendered']} renders at 400px, {summary['flags']} flags")
    report['flag_counts'] = dict(Counter(flag['kind'] for flag in report['flags']))
    print(f"Gate: {len(report['flags'])} flags")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, default=ROOT/'display/fonts')
    parser.add_argument('--proof-dir', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--compare-fonts', type=Path, help='Original fonts for compact before/after proofs')
    parser.add_argument('--comparison-dir', type=Path, default=ROOT/'docs/proofs/display-step2')
    args = parser.parse_args()
    result = verify(args.fonts, args.proof_dir)
    if args.compare_fonts:
        compare(args.comparison_dir, args.compare_fonts, args.fonts)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(bool(result['flags']))
