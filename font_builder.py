"""Shared glyph export, outline construction, spacing and OpenType font builder.

Reader defaults retain the current 0.39 construction and hint programs, and
the original 0.35 outlines and metrics.
Display options add rotated pens, perpendicular flat caps, bounded joins and
cleanup without maintaining another glyph or layout implementation.
"""
import json, re, sys, os
import pathops
from pathops import Path, PathOp, LineCap, LineJoin
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from fontTools.agl import UV2AGL
from fontTools.qu2cu import quadratic_to_curves
import math
import tempfile
from fontTools.pens.basePen import BasePen
class _Flat(BasePen):
    def __init__(self):
        """Initialize the flattened contour collection used for ink-profile measurements."""
        super().__init__(None); self.polys = []; self.cur = []
    def _moveTo(self, p):
        """Start a new flattened contour at the supplied point."""
        self.cur = [p]
    def _lineTo(self, p):
        """Append a straight segment endpoint to the current contour."""
        self.cur.append(p)
    def _curveToOne(self, p1, p2, p3):
        """Sample a cubic curve into six linear edges for ink-profile measurement."""
        p0 = self.cur[-1]
        for i in range(1, 7):
            t = i / 6; u = 1 - t
            self.cur.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0], u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    def _qCurveToOne(self, p1, p2):
        """Sample a quadratic curve into four linear edges for ink-profile measurement."""
        p0 = self.cur[-1]
        for i in range(1, 5):
            t = i / 4; u = 1 - t
            self.cur.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    def _closePath(self):
        """Store a nonempty polygon and clear the current contour."""
        if len(self.cur) > 2: self.polys.append(self.cur)
        self.cur = []
    _endPath = _closePath
from pathlib import Path as FilePath
from fontTools.pens.roundingPen import RoundingPen
from display.outline_cleanup import cleanup
from phase4_support import release_version

SC = 2            # 2000 units per em: whole-number points, fine enough that rounding is invisible
UPM = 1000 * SC
BIG = 16          # stroke at 16x size for precise round ends, then shrink back
ASCENT, DESCENT = 950, 250
ITAL_CENTER = 330   # slant around this height so letters stay centered in their space
ASSET_PREFIX = 'SEIReader'  # Existing app URLs remain stable after the family rename.
PROJECT_URL = 'https://github.com/SEIHouse/seihouse-font-lab'
LICENSE_URL = PROJECT_URL + '/blob/main/LICENSE'
OWNER = 'SEIHouse Productions LLC'
LICENSE_DESCRIPTION = ('Licensed under the SEIHouse Sans Ecosystem License, version 1.0. '
    'Ecosystem users may use and customize this font for personal or commercial creative work. '
    'Authorized SEIHouse app/web distribution and installable document embedding are permitted. '
    'Independent product embedding and standalone font redistribution require written permission. '
    'All recipients remain subject to the license at ' + LICENSE_URL)
TOK = re.compile(r'([MLCZ])|(-?\d+(?:\.\d+)?)')
AUTO_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzﬁﬂ0123456789.,:;!?\'"‘’“”‚„‛‟ʻʼ()-–—/&'
AUTO_STRENGTH = 0.6      # how much of the difference to correct (1 = all of it)
AUTO_DEPTH = 0.10        # how far into a letter's open space counts (share of the em)
AUTO_MIN, AUTO_MAX = -0.12, 0.04   # limits, as share of the em
AUTO_THRESHOLD = 15      # ignore small corrections (units per 1000)
AUTO_LOWLOW = 12         # catch visible uneven gaps inside long lowercase words
AUTO_LOWLOW_MIN, AUTO_LOWLOW_MAX = -0.035, 0.025  # gentler than capital/punctuation pairs
APOSTROPHE_TUCK = 25     # raised apostrophes need less empty space beside lowercase letters
RHYTHM_WORDS = ('minimum', 'murmur', 'river', 'climate', 'parallel', 'everywhere',
                'rival', 'arrival', 'vivid', 'willow', 'weary', 'yearly', 'twilight')
RHYTHM_THRESHOLD = 5    # minimum useful residual in source units; ink separation takes precedence
WCLASS = {'Thin':100, 'ExtraLight':200, 'Light':300, 'Regular':400, 'Medium':500, 'SemiBold':600, 'Bold':700, 'ExtraBold':800, 'Black':900}
RHYTHM_SETTINGS = ('weight','weights','contrast','lowercaseRoundness','spaceBetweenAllLetters',
                   'letterSpace','xHeight','capitalRoundness','letterWidth','overshoot','uFoot',
                   'italicAngle','uprightStraightness','ascender')
SEPARATE_LATIN = set('ĄąĘęĮįŲų')
MITER_LIMIT = 2

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'old', '0.31', 'settings.json'), encoding='utf-8') as file:
    rhythm_settings = json.load(file)
with open(os.path.join(HERE, 'old', '0.31', 'kern_styles.json'), encoding='utf-8') as file:
    rhythm_pairs = json.load(file)


class FontBuilderCore:
    """Independent build state; both entry points use this same construction core."""

    def __init__(self, settings, *, display=False, asset_dir=None):
        self.settings = settings
        self.display = display
        self.asset_dir = asset_dir or HERE
        self.S = settings['weight']; self.F = settings['contrast']
        self.ROUND = settings['lowercaseRoundness']
        self.XHT = settings.get('xHeight', 520); self.CAPR = settings.get('capitalRoundness', 210)
        self.WS = settings.get('letterWidth', 1); self.WORD = settings.get('wordSpace', 250)
        self.SLANT = settings.get('slant', 0) if display else settings.get('italicAngle', 9)
        self.TAN = math.tan(math.radians(self.SLANT))
        self.PEN = settings.get('penAngle', 0)
        self.CAP_FLAT = settings.get('ends', 'round') == 'flat'
        self.JOIN_SHARP = settings.get('joins', 'round') == 'sharp'
        self.configured_shapes = display or self.PEN != 0 or self.CAP_FLAT or self.JOIN_SHARP or settings.get('slant', 0) != 0 or settings.get('corners', 'soft') != 'soft'
        self.ITAL = False
        self.ITAL_EXTRA_SPACE = 0 if display else 4
        self.TRACK = settings['spaceBetweenAllLetters']
        self.VERSION = settings.get('version', '0.1') if display else release_version()
        self.FAMILY = 'SEIHouse Display '+settings.get('name', 'Soft') if display else settings['family']
        self.STYLE_KERN = {}; self.LANGUAGE_KERN = {}
        self.PRESERVE_RHYTHM = not self.configured_shapes and all(settings.get(k) == rhythm_settings.get(k) for k in RHYTHM_SETTINGS)


    def export(self):
        """Evaluate the configured drawing engine in Chromium and capture glyphs, anchors and pairs."""
        from playwright.sync_api import sync_playwright
        page = (open(os.path.join(HERE, 'export_head.html'), encoding='utf-8').read()
                + open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
                + open(os.path.join(HERE, 'export_tail.js'), encoding='utf-8').read() + '</script></body></html>')
        with tempfile.TemporaryDirectory(prefix='seihouse-font-export-') as temp, sync_playwright() as p:
            tmp = FilePath(temp) / 'export.html'
            tmp.write_text(page, encoding='utf-8')
            b = p.chromium.launch()
            try:
                pg = b.new_page(); pg.goto(tmp.as_uri())
                if self.display:
                    self.F = pg.evaluate('displayContrast(...' + json.dumps([
                        self.S, self.settings['contrast'], self.XHT,
                        self.settings.get('ends', 'round')]) + ')')
                pg.evaluate(f"P.round={self.ROUND}; P.contrast={self.F}; P.xh={self.XHT}; P.caprx={self.CAPR}; P.ws={self.WS}; P.base={self.S}; P.os={1 if self.settings.get('overshoot', True) else 0}; P.ufoot={1 if self.settings.get('uFoot', True) else 0}; P.ital={1 if self.ITAL else 0}; P.straight={self.settings.get('uprightStraightness', 1)}; P.asc={self.settings.get('ascender', 770)}; P.trk={self.track_for(self.S) + (self.ITAL_EXTRA_SPACE if self.ITAL else 0)};")
                pg.evaluate("Object.assign(P, " + json.dumps(dict(
                    corner=self.settings.get('corners', 'soft'), cap=self.settings.get('ends', 'round'),
                    join=self.settings.get('joins', 'round'), penAngle=self.PEN,
                    obliqueAngle=self.settings.get('slant', 0))) + ");")
                if self.display:
                    pg.evaluate('(choices)=>P.alternates=displayChoices(choices)', self.settings.get('alternates', {}))
                out = {'glyphs': pg.evaluate(f'exportGlyphs({self.S})'), 'alternates': pg.evaluate(f'exportAlternates({self.S})'),
                       'kern': pg.evaluate('getKern()'), 'basemap': pg.evaluate('getBaseMap()'),
                       'screenStroke': pg.evaluate(f'readingStroke({self.S})'),
                       'scriptchars': pg.evaluate('getScriptChars()')}
                if self.display:
                    out['designs'] = pg.evaluate('displayManifest()')
            finally:
                b.close()
        return out

    def parse(self, d):
        """Parse the engine's absolute SVG move, line, cubic and close commands."""
        toks = [(m.group(1), m.group(2)) for m in TOK.finditer(d)]; i = 0; cmds = []
        def num():
            """Consume the next numeric token from the SVG path stream."""
            nonlocal i
            v = float(toks[i][1]); i += 1; return v
        while i < len(toks):
            c = toks[i][0]; i += 1
            if c == 'M': cmds.append(('M', (num(), num())))
            elif c == 'L': cmds.append(('L', (num(), num())))
            elif c == 'C': cmds.append(('C', ((num(), num()), (num(), num()), (num(), num()))))
            elif c == 'Z': cmds.append(('Z',))
        return cmds

    def stroke(self, cmds, dx, width=None):
        """Oval pen: stretch the drawing tall, stroke it, squash it back. Vertical strokes keep the full
        weight, horizontal strokes come out thinner by the contrast amount, and curves blend smoothly."""
        if self.configured_shapes:
            return self.configured_stroke(cmds, dx, width)
        path = Path(); pen = path.getPen()
        T = lambda pt: ((pt[0] + dx) * SC * BIG, -pt[1] * SC * BIG * self.F)
        open_ = False
        for c in cmds:
            if c[0] == 'M':
                if open_: pen.endPath()
                pen.moveTo(T(c[1])); open_ = True
            elif c[0] == 'L': pen.lineTo(T(c[1]))
            elif c[0] == 'C': pen.curveTo(T(c[1][0]), T(c[1][1]), T(c[1][2]))
            elif c[0] == 'Z': pen.closePath(); open_ = False
        if open_: pen.endPath()
        path.stroke((width or self.S) * SC * BIG, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
        path.convertConicsToQuads(0.05)
        return path.transform(scaleX=1.0/BIG, scaleY=1.0/(BIG*self.F))

    def circle(self, cx, cy, r, dx):
        """Create a filled dot from four cubic arcs at the shared font-unit scale."""
        K = 0.5522847498; x, y, R = (cx + dx) * SC, -cy * SC, r * SC
        path = Path(); pen = path.getPen()
        pen.moveTo((x + R, y))
        pen.curveTo((x + R, y + K*R), (x + K*R, y + R), (x, y + R))
        pen.curveTo((x - K*R, y + R), (x - R, y + K*R), (x - R, y))
        pen.curveTo((x - R, y - K*R), (x - K*R, y - R), (x, y - R))
        pen.curveTo((x + K*R, y - R), (x + R, y - K*R), (x + R, y))
        pen.closePath(); return path

    def outline(self, g, dx):
        """Merge a glyph's strokes, fills and dots, then apply its real italic shear."""
        if self.configured_shapes:
            return self.configured_outline(g, dx)
        shapes = [self.stroke(self.parse(p['d']), dx, p['w']) for p in g['paths']] + [self.circle(cx, cy, r, dx) for cx, cy, r in g['circles']]
        for f in g.get('fills', []):            # filled shapes (holes allowed), plus a round-cornered outline unless turned off
            cmds = self.parse(f['d'])
            if f['sw'] > 0: shapes.append(self.stroke(cmds, dx))
            fp = Path(); pen = fp.getPen(); open_ = False
            for c in cmds:
                pt = None if c[0] == 'Z' else ((c[1][0] + dx) * SC, -c[1][1] * SC)
                if c[0] == 'M':
                    if open_: pen.closePath()
                    pen.moveTo(pt); open_ = True
                elif c[0] == 'L': pen.lineTo(pt)
                elif c[0] == 'Z': pen.closePath(); open_ = False
            if open_: pen.closePath()
            fp.fillType = pathops.FillType.EVEN_ODD
            fp.simplify(fix_winding=True)
            shapes.append(fp)
        if not shapes: return None
        r = shapes[0]                           # merge one at a time (the batch merge could drop simple fills)
        for s in shapes[1:]:
            r = pathops.op(r, s, PathOp.UNION, fix_winding=True)
        # A single stroked path can overlap itself at tight turns (v/w/2/3/4/5).
        # Resolve its winding before CFF export and hinting, even when no union ran.
        r.simplify(fix_winding=True)
        r.convertConicsToQuads(0.02)
        if self.ITAL:
            r = r.transform(skewX=self.TAN, translateX=-self.TAN * ITAL_CENTER * SC)
        return r

    def profiles(self, path, ys):
        """For each height y: the leftmost and rightmost ink (None where there is no ink)."""
        if path is None: return [None] * len(ys), [None] * len(ys)
        fp = _Flat(); path.draw(fp)
        L, R = [], []
        for y in ys:
            xs = []
            for poly in fp.polys:
                n = len(poly)
                for i in range(n):
                    (x0, y0), (x1, y1) = poly[i], poly[(i+1) % n]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            L.append(min(xs) if xs else None); R.append(max(xs) if xs else None)
        return L, R

    def auto_pairs(self, paths, hm, cmap, extra_chars=''):
        """Measure the real empty space between letter shapes and even it out (per style)."""
        step = 10 * SC
        capY = [y for y in range(0, 700*SC + 1, step)]
        lowY = [y for y in range(0, round(self.XHT*SC) + 1, step)]
        depth = AUTO_DEPTH * UPM
        prof = {}
        for ch in AUTO_CHARS + extra_chars:
            n = cmap.get(ord(ch))
            if not n: continue
            p = paths.get(n)
            Lc, Rc = self.profiles(p, capY); Ll, Rl = self.profiles(p, lowY)
            xsL = [v for v in Lc if v is not None]; xsR = [v for v in Rc if v is not None]
            if not xsL: continue
            prof[ch] = dict(name=n, adv=hm[n], Lmin=min(xsL), Rmax=max(xsR), cap=(Lc, Rc), low=(Ll, Rl))
        def gap(a, b, zone):
            """Average the clipped edge gaps across the cap or lowercase sample band."""
            A, B = prof[a], prof[b]
            RA = A[zone][1]; LB = B[zone][0]; tot = 0; k = 0
            for ra, lb in zip(RA, LB):
                ra_eff = max(ra if ra is not None else -1e9, A['Rmax'] - depth)
                lb_eff = min(lb if lb is not None else 1e9, B['Lmin'] + depth)
                tot += (A['adv'] - ra_eff) + lb_eff; k += 1
            return tot / max(k, 1)
        lower = set('abcdefghijklmnopqrstuvwxyzﬁﬂ') | {ch for ch in extra_chars if ch.islower()}
        t_low = gap('n', 'n', 'low') if 'n' in prof else 0
        t_cap = gap('H', 'H', 'cap') if 'H' in prof else 0
        caps = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ') | {ch for ch in extra_chars if ch.isupper()}; digits = set('0123456789')
        lowp = set('.,'); quotes = set('\'"‘’“”'); letters = caps | lower
        def wanted(a, b):
            """Select supported pair types, retaining the separate lowercase limits."""
            if 'j' in (a, b): return False                         # j's tail curls under its neighbour; leave it
            if a in lower and b in lower: return 'lowlow'           # smooth gaps inside words, with a tighter limit
            if a in caps and (b in caps or b in lower): return True    # AV, LT, To, Ya ...
            if (a in letters or a in digits) and b in lowp: return True  # r. y, P. 7.
            if a in quotes and (b in letters or b in digits): return True   # “A ’s
            if (a in letters or a in lowp) and b in quotes: return True    # L’ s” .”
            if a == '(' and (b in letters or b in digits): return True
            if (a in letters or a in digits) and b == ')': return True
            # Numbers get their own even-width set later.
            return False
        out = {}
        for a in prof:
            for b in prof:
                w = wanted(a, b)
                if not w: continue
                zone = 'low' if (a in lower or b in lower) else 'cap'
                target = t_low if zone == 'low' else t_cap
                k = AUTO_STRENGTH * (target - gap(a, b, zone))
                low, high = (AUTO_LOWLOW_MIN, AUTO_LOWLOW_MAX) if w == 'lowlow' else (AUTO_MIN, AUTO_MAX)
                k = max(low * UPM, min(high * UPM, k))
                if ((a in lower and b in "'’") or (a in "'’" and b in lower)):
                    k = max(AUTO_MIN * UPM, k - APOSTROPHE_TUCK * SC)
                limit = AUTO_LOWLOW if w == 'lowlow' else AUTO_THRESHOLD
                if abs(k) >= limit * SC:
                    out[a + b] = round(k / SC)       # stored per 1000, like the hand-set pairs
        return out

    def optical_pairs(self, paths, hm, cmap, kern, italic):
        """Small, outline-measured corrections for the reported and broader reading cases.

        Measure the central lowercase band to avoid letting tall stems or italic
        exits dominate perceived space. Limit open-edge depth, preserve extra room
        for rn/rm, and protect the closest actual ink from small-size crowding.
        The glyph contours and all advances remain untouched.
        """
        focus = set('Li ia an In ne es bl la ad de En nt tr ry Me ei ac cq qu ui it tt ta al ri rn rm cl li fi fl'.split())
        broader = {a+b for word in RHYTHM_WORDS for a, b in zip(word, word[1:])} - focus
        focus.update(broader)
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzﬁﬂ'
        focus.update(a+b for a in chars for b in chars
                     if 'j' not in (a, b) and ('ﬁ' in (a, b) or 'ﬂ' in (a, b)))
        body_y = range(round(self.XHT*SC*.12), round(self.XHT*SC*.88), 10*SC)
        full_y = range(0, 700*SC+1, 5*SC)
        depth = 60*SC
        prof = {}
        for ch in chars:
            name = cmap.get(ord(ch))
            if not name: continue
            left, right = self.profiles(paths[name], full_y)
            body = self.profiles(paths[name], body_y)
            prof[ch] = (hm[name], min(x for x in left if x is not None),
                        max(x for x in right if x is not None), body, (left, right))
        def measured(a, b):
            """Return the clipped central gap and closest sampled actual ink gap."""
            A, B = prof[a], prof[b]
            gaps = [A[0] - max(r if r is not None else -1e9, A[2]-depth)
                    + min(l if l is not None else 1e9, B[1]+depth)
                    for r, l in zip(A[3][1], B[3][0])]
            closest = min(A[0]-r+l for r, l in zip(A[4][1], B[4][0])
                          if r is not None and l is not None)
            return sum(gaps)/len(gaps)/SC, closest/SC
        target, _ = measured('n', 'n')
        out = {}
        for pair in sorted(focus):
            a, b = pair
            if a not in prof or b not in prof: continue
            gap, closest = measured(a, b)
            current = kern.get(pair, 0)
            cushion = 20 if a == 'r' and b in 'inmh' else 0
            residual = .55*(target+cushion-gap-current)
            delta = max(-25 if italic else -18, min(22, residual))
            value = max(-60 if italic else -45, min(40, round(current+delta)))
            floor = 100 if pair in ('rn', 'rm') else 55 if pair in ('ry', 'tt', 'fi', 'fl') else 80
            value = max(value, math.ceil(floor-closest))
            if pair in broader and abs(value-current) < RHYTHM_THRESHOLD and closest+current >= floor:
                continue
            if value != current: out[pair] = value
        return out

    def private_dict(self, stroke_weight):
        """Screen-tuning info: the lines letters must snap to (baseline, lowercase height, capital height,
        descender) and the usual stem thickness, so the auto-tuner can keep small text crisp."""
        os_ = 10 * SC; xh = round(self.XHT * SC); cap = 700 * SC; asc = round(self.settings.get('ascender', 770) * SC)
        blues = sorted({(-os_, 0), (xh, xh + os_), (cap, cap + os_), (asc, asc + os_)})
        flat = [v for pair in blues for v in pair]
        return {'BlueValues': flat, 'OtherBlues': [-200*SC - os_, -200*SC],
                'StdVW': round(stroke_weight * SC), 'StdHW': round(stroke_weight * SC / self.F)}

    def autohint(self, path_otf):
        """Run Adobe's auto-tuner (otfautohint) on the finished file, in place."""
        import subprocess, shutil
        tmp = path_otf + '.hinted.otf'
        executable = shutil.which('otfautohint') or os.path.join(os.path.dirname(sys.executable),
                                                                'otfautohint.exe' if os.name == 'nt' else 'otfautohint')
        r = subprocess.run([executable, path_otf, '-o', tmp], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(tmp):
            shutil.move(tmp, path_otf); return True
        print('    screen tuning failed:', (r.stderr or r.stdout)[-300:]); return False

    def draw_fitted(self, path, pen):
        """Draw with long smooth curves: runs of many small pieces are merged into a few cubic curves."""
        for contour in path.contours:
            segs = list(contour.segments)
            start = None; run = []; cur = None
            def flush():
                """Fit pending quadratic segments to cubic curves and emit them through the font pen."""
                nonlocal run
                if not run: return
                for c in quadratic_to_curves(run, max_err=0.35, all_cubic=True):
                    pen.curveTo(c[1], c[2], c[3])
                run = []
            for verb, pts in segs:
                if verb == 'moveTo':
                    cur = pts[0]; pen.moveTo(cur)
                elif verb == 'lineTo':
                    flush(); pen.lineTo(pts[0]); cur = pts[0]
                elif verb == 'qCurveTo':
                    run.append([cur] + list(pts)); cur = pts[-1]
                elif verb == 'curveTo':
                    flush(); pen.curveTo(*pts); cur = pts[-1]
                elif verb == 'closePath':
                    flush(); pen.closePath()
                elif verb == 'endPath':
                    flush(); pen.endPath()

    def charstring(self, path, adv):
        """Encode the fitted outline and advance as a CFF Type 2 charstring."""
        pen = T2CharStringPen(adv, None)          # whole-number points at 2000 units per em
        if path is not None:
            if self.configured_shapes:
                fitted = Path()
                self.draw_fitted(path, RoundingPen(fitted.getPen()))
                cleanup(fitted).draw(pen)
            else:
                self.draw_fitted(path, pen)
        return pen.getCharString()

    def lsb_of(self, path):
        """Return the rounded left ink bound, or zero for an empty glyph."""
        if path is None: return 0
        bp = BoundsPen(None); path.draw(bp); return round(bp.bounds[0]) if bp.bounds else 0

    def center_ink(self, path, advance):
        """Place the finished outline, including its stroke and italic slant, in the middle of its advance."""
        bp = BoundsPen(None); path.draw(bp)
        if not bp.bounds: return path
        left, _, right, _ = bp.bounds
        return path.transform(translateX=(advance - (right - left)) / 2 - left)

    def gname(self, ch):
        """Use the Adobe glyph name when available, otherwise a Unicode-derived name."""
        u = ord(ch)
        return UV2AGL.get(u, f'uni{u:04X}' if u <= 0xFFFF else f'u{u:05X}')

    def retain_reading_pairs(self, kern, style):
        """Keep approved letter rhythm for the default build; custom settings remeasure it."""
        if not self.PRESERVE_RHYTHM: return
        letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzﬁﬂ')
        previous = rhythm_pairs[style]
        for pair in kern.keys() | previous.keys():
            if len(pair) == 2 and all(ch in letters for ch in pair):
                if pair in previous: kern[pair] = previous[pair]
                else: kern.pop(pair, None)

    def clear_text_marks(self, paths, hm, cmap, kern, basemap):
        """Keep mark/figure pairs clear of actual ink, including their accented classes."""
        marks = set('.,:;…!?\'"‘’“”-–—()[]¡¿0123456789')
        pairs = [pair for pair in kern if len(pair) == 2 and any(ch in marks for ch in pair)
                 and all(ord(ch) in cmap for ch in pair)]
        members = {}
        for pair in pairs:
            for ch in pair:
                members[ch] = [ch] + [a for a,b in basemap.items() if b == ch and ord(a) in cmap]
        sampled = {}
        ys = range(-250*SC,1100*SC+1,2*SC)
        for ch in {member for group in members.values() for member in group}:
            name = cmap[ord(ch)]
            sampled[ch] = hm[name], self.profiles(paths[name],ys)
        for pair in pairs:
            closest = []
            for a in members[pair[0]]:
                advance, (_,right) = sampled[a]
                for b in members[pair[1]]:
                    _, (left,_) = sampled[b]
                    closest.extend(advance-r+l for r,l in zip(right,left) if r is not None and l is not None)
            if closest:
                kern[pair] = max(kern[pair], math.ceil((35*SC-min(closest))/SC))

    def ogonek_pairs(self, paths,hm,cmap,kern,basemap):
        """Give new connected tails their own classes and measured punctuation room.

        Every old pair remains frozen. Ordinary inherited values are copied to the
        new classes; only their own punctuation pairs receive extra ink clearance.
        """
        def variants(ch):
            """List a base character and its separate ogonek derivatives for inherited pair values."""
            return [ch]+[new for new in sorted(SEPARATE_LATIN) if basemap.get(new)==ch]
        for pair,value in list(kern.items()):
            for a in variants(pair[0]):
                for b in variants(pair[1]):
                    if a+b!=pair: kern[a+b]=value
        punctuation='.,:;…!?\'"‘’“”‚„‛‟-–—()[]0123456789'
        ys=range(-320*SC,1100*SC+1,2*SC)
        sampled={ch:(hm[cmap[ord(ch)]],self.profiles(paths[cmap[ord(ch)]],ys))
                 for ch in SEPARATE_LATIN|set(punctuation) if ord(ch) in cmap}
        for new in sorted(SEPARATE_LATIN):
            for other in punctuation:
                for a,b in ((new,other),(other,new)):
                    advance,(_,right)=sampled[a];_,(left,_)=sampled[b]
                    gaps=[advance-r+l for r,l in zip(right,left) if r is not None and l is not None]
                    if gaps: kern[a+b]=max(kern.get(a+b,0),math.ceil((35*SC-min(gaps))/SC))

    def hungarian_caps(self, paths,hm,cmap,kern):
        """Add clearance for uppercase Hungarian TY/TTY digraphs, only under lang=hu."""
        ys=range(0,700*SC+1,2*SC)
        sampled={ch:self.profiles(paths[cmap[ord(ch)]],ys) for ch in 'TY'}
        pairs={}
        for pair in ('TT','TY'):
            a,b=pair;right=sampled[a][1];left=sampled[b][0]
            gaps=[hm[cmap[ord(a)]]+kern.get(pair,0)*SC-r+l for r,l in zip(right,left) if r is not None and l is not None]
            delta=max(0,math.ceil((35*SC-min(gaps))/SC))
            if delta: pairs[pair]=delta
        return pairs

    def script_clearance(self, paths, hm, cmap, kern, basemap):
        """Protect new-script neighbors, including aliases, without changing Latin pairs."""
        chars=[chr(code) for code in cmap if 0x370<=code<=0x3ff or 0x400<=code<=0x491]
        ys=range(-250*SC,1100*SC+1,4*SC)
        sampled={ch:(hm[cmap[ord(ch)]],self.profiles(paths[cmap[ord(ch)]],ys)) for ch in chars}
        result={}
        for a in chars:
            advance,(_,right)=sampled[a]
            for b in chars:
                _,(left,_)=sampled[b]
                inherited=kern.get(basemap.get(a,a)+basemap.get(b,b),0)
                gaps=[advance-r+l for r,l in zip(right,left) if r is not None and l is not None]
                if gaps and min(gaps)+inherited*SC<35*SC:
                    result[a+b]=max(inherited,math.ceil((35*SC-min(gaps))/SC))
        return result

    def vietnamese_clearance(self, paths,hm,cmap,kern,basemap):
        """Add literal clearance only for new Vietnamese glyphs and their neighbors.

        Every derivative remains in its root letter's kerning class; literal pairs
        override it only where horns or a tone stack need extra ink separation.
        """
        from build_subsets import VIETNAMESE_NEW
        new={chr(code) for code in cmap if code in VIETNAMESE_NEW}
        if not new: return {}
        import unicodedata
        others={chr(code) for code in cmap if unicodedata.category(chr(code)).startswith('L')
                or chr(code) in '0123456789.,:;…!?\'"‘’“”‚„‛‟-–—()[]{}«»‹›'}
        ys=range(-360*SC,1100*SC+1,4*SC)
        sampled={ch:(hm[cmap[ord(ch)]],self.profiles(paths[cmap[ord(ch)]],ys)) for ch in others|new}
        result={}
        for changed in sorted(new):
            for other in sorted(others):
                for a,b in ((changed,other),(other,changed)):
                    advance,(_,right)=sampled[a];_,(left,_)=sampled[b]
                    inherited=kern.get(a+b,kern.get(basemap.get(a,a)+basemap.get(b,b),0))
                    gaps=[advance-r+l for r,l in zip(right,left) if r is not None and l is not None]
                    if gaps and min(gaps)+inherited*SC<35*SC:
                        result[a+b]=max(inherited,math.ceil((35*SC-min(gaps))/SC))
        return result

    def track_for(self, thick):
        """Adjust the configured tracking by stroke weight relative to Regular."""
        reg = self.settings['weight']
        return self.TRACK + (thick - reg) * (0.25 if thick > reg else 0.1)

    def build(self, data, out, style='Regular', italic=False, *, oblique=False):
        """Build and hint one style with the shared character set and OpenType features."""
        if oblique and (not self.display or italic or self.ITAL):
            raise ValueError('Display obliques use slant settings, without italic letter substitutions')
        sloped = italic or oblique
        TR = self.track_for(self.S) + (self.ITAL_EXTRA_SPACE if italic else 0)
        ps_style = ('Italic' if style == 'Regular' else style + 'Italic') if italic else style
        shown = ('Italic' if style == 'Regular' else style + ' Italic') if italic else style
        if oblique:
            ps_style = 'Oblique' if style == 'Regular' else style + 'Oblique'
            shown = 'Oblique' if style == 'Regular' else style + ' Oblique'
        KERN = {}
        ovr = self.settings.get('letterSpace', {})
        order = ['.notdef', 'space']; cmap = {32: 'space', 160: 'space'}; paths = {}; hm = {}; records = {}; origins = {}
        PRIVATE = {0xE000:'Ⓢ', 0xE001:'🎧', 0xE002:'💻', 0xE003:'📖', 0xE004:'🔖', 0xE005:'🔍', 0xE006:'🔔',
                   0xE007:'🎤', 0xE008:'💿', 0xE009:'🔊', 0xE00A:'⚙', 0xE00B:'⌂', 0xE00C:'⚡', 0xE00D:'☀', 0xE00E:'☯', 0xE00F:'♥'}
        nd = Path(); pen = nd.getPen()
        pen.moveTo((60*SC,0)); pen.lineTo((460*SC,0)); pen.lineTo((460*SC,700*SC)); pen.lineTo((60*SC,700*SC)); pen.closePath()
        pen.moveTo((110*SC,50*SC)); pen.lineTo((110*SC,650*SC)); pen.lineTo((410*SC,650*SC)); pen.lineTo((410*SC,50*SC)); pen.closePath()
        nd.simplify(fix_winding=True)
        paths['.notdef'] = nd; paths['space'] = None; hm['.notdef'] = 520*SC; hm['space'] = round(self.WORD*SC)
        for ch, g in data['glyphs'].items():
            o = ovr.get(ch) or ovr.get(data.get('basemap', {}).get(ch, ''), {}) or {}; before, after = o.get('before', 0), o.get('after', 0)
            left = 0 if g.get('mark') else TR + g['sb0'] + before
            name = self.gname(ch); order.append(name); cmap[ord(ch)] = name
            records[name] = g; origins[name] = left
            try:
                paths[name] = self.outline(g, left)
            except pathops.PathOpsError as exc:
                raise RuntimeError(f'Could not union {shown} glyph {name}') from exc
            hm[name] = 0 if g.get('mark') else round((left + g['w'] + self.S + g['sb1'] + after + TR) * SC)
            if ch in '\u2009\u202f': hm[name] = 120 * SC

        # Add unencoded alternates without touching the proportional digit outlines or metrics.
        digits = '0123456789'
        digit_names = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
        tabular_advance = max(hm[self.gname(d)] for d in digits)
        for d, name in zip(digits, digit_names):
            alt = name + '.tf'
            order.append(alt)
            paths[alt] = self.center_ink(paths[self.gname(d)], tabular_advance)
            hm[alt] = tabular_advance

        for name, g in data['alternates'].items():
            if name.endswith('.tf'): continue  # same exact outline as the original digit, positioned above
            order.append(name)
            before, after = 0, 0
            if self.display:
                source = next((source for source, spec in data['designs'].items() if name in spec['choices'].values()), None)
                if source is not None:
                    override = ovr.get(source) or ovr.get(data['basemap'].get(source, ''), {}) or {}
                    before, after = override.get('before', 0), override.get('after', 0)
            left = TR + g['sb0'] + before
            records[name] = g; origins[name] = left
            try:
                paths[name] = self.outline(g, left)
            except pathops.PathOpsError as exc:
                raise RuntimeError(f'Could not union {shown} alternate {name}') from exc
            hm[name] = round((2*TR + g['sb0'] + before + g['w'] + self.S + g['sb1'] + after) * SC)

        # The small figures share a measured advance within each weight/style.
        supers = '⁰¹²³⁴⁵⁶⁷⁸⁹'; subs = '₀₁₂₃₄₅₆₇₈₉'
        mini_names = [self.gname(ch) for ch in supers + subs] + [name + suffix for name in digit_names for suffix in ('.numr', '.dnom')]
        mini_advance = max(hm[name] for name in mini_names)
        for name in mini_names:
            paths[name] = self.center_ink(paths[name], mini_advance)
            hm[name] = mini_advance

        if self.display:
            for source, spec in data['designs'].items():
                original = self.gname(source) if len(source) == 1 else source
                for name in spec['choices'].values():
                    if name == source:
                        continue
                    if original.endswith('.tf'):
                        paths[name] = self.center_ink(paths[name], tabular_advance)
                        hm[name] = tabular_advance
                    elif original in mini_names:
                        paths[name] = self.center_ink(paths[name], mini_advance)
                        hm[name] = mini_advance

        fraction_name = self.gname('⁄')
        hm[fraction_name] = round(190 * SC)
        paths[fraction_name] = self.center_ink(paths[fraction_name], hm[fraction_name])
        for ch, numerator, denominator in (('½', 'one', 'two'), ('¼', 'one', 'four'), ('¾', 'three', 'four')):
            num_name, den_name = numerator + '.numr', denominator + '.dnom'
            left = paths[num_name]
            slash = paths[fraction_name].transform(translateX=hm[num_name])
            right = paths[den_name].transform(translateX=hm[num_name] + hm[fraction_name])
            paths[self.gname(ch)] = pathops.op(pathops.op(left, slash, PathOp.UNION, fix_winding=True),
                                         right, PathOp.UNION, fix_winding=True)
            hm[self.gname(ch)] = hm[num_name] + hm[fraction_name] + hm[den_name]
            if self.display and ch in data['designs']:
                spec = data['designs'][ch]
                name = next(name for choice, name in spec['choices'].items() if choice != spec['default'])
                den_spec = data['designs'][den_name]
                alternate_den = den_spec['choices'][next(choice for choice in den_spec['choices'] if choice != den_spec['default'])]
                right = paths[alternate_den].transform(translateX=hm[num_name]+hm[fraction_name])
                paths[name] = pathops.op(pathops.op(left, slash, PathOp.UNION, fix_winding=True),
                                        right, PathOp.UNION, fix_winding=True)
                hm[name] = hm[self.gname(ch)]

        for code, ch in PRIVATE.items():
            if ord(ch) in cmap: cmap[code] = cmap[ord(ch)]
        fb = FontBuilder(UPM, isTTF=False)
        fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
        ps = f'{self.FAMILY.replace(" ", "")}-{ps_style}'
        fb.setupCFF(ps, {'FullName': f'{self.FAMILY} {shown}', 'version': self.VERSION, 'Weight': style,
                         'ItalicAngle': -self.SLANT if sloped else 0},
                    {n: self.charstring(paths[n], hm[n]) for n in order}, self.private_dict(data['screenStroke']))
        fb.setupHorizontalMetrics({n: (hm[n], self.lsb_of(paths[n])) for n in order})
        if sloped:
            fb.setupHorizontalHeader(ascent=ASCENT*SC, descent=-DESCENT*SC, lineGap=0,
                                     caretSlopeRise=1000, caretSlopeRun=round(1000*self.TAN), caretOffset=0)
        else:
            fb.setupHorizontalHeader(ascent=ASCENT*SC, descent=-DESCENT*SC, lineGap=0)
        names = {'uniqueFontIdentifier': f'{self.FAMILY} {shown} {self.VERSION}', 'fullName': f'{self.FAMILY} {shown}',
                 'psName': ps, 'version': f'Version {self.VERSION}',
                 'copyright': f'Copyright 2026 {OWNER}. All rights reserved except as licensed.',
                 'trademark': f'SEIHouse Sans is a font family name used by {OWNER}. No trademark registration is claimed.',
                 'manufacturer': OWNER, 'designer': OWNER,
                 'vendorURL': PROJECT_URL, 'designerURL': PROJECT_URL,
                 'licenseDescription': LICENSE_DESCRIPTION, 'licenseInfoURL': LICENSE_URL}
        if style in ('Regular', 'Bold'):
            names.update({'familyName': self.FAMILY,
                          'styleName': (('Italic' if style == 'Regular' else 'Bold Italic') if italic else style)})
        else:   # apps that only understand Regular/Bold/Italic still list it, as "SEIReader Light"
            names.update({'familyName': f'{self.FAMILY} {style}', 'styleName': 'Italic' if italic else 'Regular',
                          'typographicFamily': self.FAMILY, 'typographicSubfamily': shown})
        if oblique:
            names.update(styleName='Bold Italic' if style == 'Bold' else 'Italic',
                         typographicFamily=self.FAMILY, typographicSubfamily=shown)
        fb.setupNameTable(names)
        win_ascent, win_descent = 1100*SC, 320*SC
        if self.display:
            # Retain a released family's Windows clipping reservation even if
            # counter compensation reduces its current accent-stack bounds.
            # Edge acquired this 1110-unit budget with the Phase 4 repertoire.
            if self.settings.get('name') == 'Edge':
                win_ascent = 1110*SC
            # Windows clipping must include newly inherited accent stacks.
            # Keep Reader's approved metrics and both families' line spacing.
            charstrings = fb.font['CFF '].cff.topDictIndex[0].CharStrings
            bounds = [charstrings[name].calcBounds(None) for name in order]
            bounds = [box for box in bounds if box is not None]
            win_ascent = max(win_ascent, math.ceil(max(box[3] for box in bounds)))
            win_descent = max(win_descent, math.ceil(-min(box[1] for box in bounds)))
        fb.setupOS2(sTypoAscender=ASCENT*SC, sTypoDescender=-DESCENT*SC, sTypoLineGap=0,
                    usWinAscent=win_ascent, usWinDescent=win_descent, sxHeight=round(self.XHT*SC), sCapHeight=700*SC,
                    achVendID='SEIH', fsType=0,  # Installable document embedding, subject to the ecosystem EULA.
                    fsSelection=((0x40 if (style != 'Bold' and not sloped) else 0) | (0x20 if style == 'Bold' else 0)
                                 | (0x01 if sloped else 0) | (0x200 if oblique else 0) | 0x80),
                    usWeightClass=WCLASS.get(style, 400), version=4)
        fb.font['head'].macStyle = (1 if style == 'Bold' else 0) | (2 if sloped else 0)
        fb.font['head'].fontRevision = float(self.VERSION)
        os2 = fb.font['OS/2']; os2.recalcUnicodeRanges(fb.font); os2.recalcCodePageRanges(fb.font)
        from fontTools.otlLib.builder import buildStatTable
        wv = WCLASS.get(style, 400)
        axes = [dict(tag='wght', name='Weight', values=[dict(value=wv, name=style, flags=(0x2 if style == 'Regular' else 0))])]
        if oblique:
            # Keep the true slope and the binary style link. Elide the slope
            # label so the following Oblique value supplies the name only once.
            axes.append(dict(tag='slnt', name='Slant', values=[dict(value=-self.SLANT, name='Oblique', flags=0x2)]))
        axes.append(dict(tag='ital', name='Italic', values=[dict(value=1, name='Oblique' if oblique else 'Italic')] if sloped else
                         [dict(value=0, name='Roman', flags=0x2, linkedValue=1)]))
        buildStatTable(fb.font, axes, elidedFallbackName=2)
        fb.setupPost(isFixedPitch=0, underlinePosition=-120*SC, underlineThickness=60*SC, italicAngle=-self.SLANT if sloped else 0)

        if self.display:
            from display.title_spacing import DisplaySpacing
            display_spacing = DisplaySpacing(self, paths, hm, cmap, AUTO_CHARS+data.get('scriptchars', ''))
            AUTO = display_spacing.auto_pairs()
            AUTO.update(display_spacing.title_pairs())
        else:
            AUTO = self.auto_pairs(paths, hm, cmap, data.get('scriptchars', ''))
        KERN.update(AUTO); KERN.update(data['kern'])
        if self.display:
            # Final title/body measurements replace inherited Reader letter assumptions.
            KERN.update(AUTO)
        else:
            KERN.update(self.optical_pairs(paths, hm, cmap, KERN, italic))
        self.retain_reading_pairs(KERN, ps_style)
        self.clear_text_marks(paths, hm, cmap, KERN, data.get('basemap', {}))
        # Additive foundation: retain every approved old pair when geometry is unchanged.
        latin_dir = os.path.join(HERE, 'old', '0.33')
        with open(os.path.join(latin_dir, 'settings.json'), encoding='utf-8') as file: latin_settings = json.load(file)
        if not self.configured_shapes and all(self.settings.get(k) == latin_settings.get(k) for k in RHYTHM_SETTINGS):
            with open(os.path.join(latin_dir, 'kern_styles.json'), encoding='utf-8') as file: old_kern = json.load(file)[ps_style]
            with TTFont(os.path.join(latin_dir, f'SEIReader-{ps_style}.woff2')) as old_font: old_codes = set(old_font.getBestCmap())
            for pair in list(KERN):
                if all(ord(ch) in old_codes for ch in pair) and pair not in old_kern: del KERN[pair]
            KERN.update(old_kern)
        self.ogonek_pairs(paths,hm,cmap,KERN,data['basemap'])
        # User-reported decimal fix: numeric separators override frozen/automatic pairs.
        numeric_pairs = {pair: value for pair, value in data['kern'].items()
                         if len(pair) == 2 and ((pair[0] in digits and pair[1] in '.,')
                                               or (pair[0] in '.,' and pair[1] in digits))}
        KERN.update(numeric_pairs)
        if self.PRESERVE_RHYTHM:
            with open(os.path.join(HERE,'old','0.34','kern_styles.json'),encoding='utf-8') as file:
                approved=json.load(file)[ps_style]
            with TTFont(os.path.join(HERE,'old','0.34',f'SEIReader-{ps_style}.woff2')) as font:
                approved_codes=set(font.getBestCmap())
            for pair in list(KERN):
                if all(ord(ch) in approved_codes for ch in pair) and pair not in approved:
                    del KERN[pair]
            KERN.update(approved)
        for k, v in self.settings.get('pairSpace', {}).items(): KERN[k] = v
        script_exceptions = self.script_clearance(paths, hm, cmap, KERN, data['basemap'])
        script_exceptions.update(self.vietnamese_clearance(paths, hm, cmap, KERN, data['basemap']))
        KERN.update(script_exceptions)
        self.STYLE_KERN[ps_style] = dict(KERN)
        self.LANGUAGE_KERN[ps_style]={'hu':self.hungarian_caps(paths,hm,cmap,KERN)}
        if style == 'Regular' and not italic:
            name = 'kern_auto_'+self.settings['name'].lower().replace(' ', '-')+'.json' if self.display else 'kern_auto.json'
            with open(os.path.join(self.asset_dir, name), 'w', encoding='utf-8') as file:
                json.dump(AUTO, file, ensure_ascii=False)
        print(f'    {len(AUTO)} automatic pairs')
        # pair spacing written with groups, so letters added later (accents) join the right group automatically
        left_groups, right_groups, lines = set(), set(), []
        for pair, v in KERN.items():
            a, b = pair[0], pair[1]
            if ord(a) not in cmap or ord(b) not in cmap: continue
            if v == 0 and pair not in script_exceptions: continue
            if pair in script_exceptions:
                lines.append(f'  pos {self.gname(a)} {self.gname(b)} {round(v*SC)};')
                continue
            left_groups.add(a); right_groups.add(b)
            lines.append(f'  pos @L_{self.gname(a)} @R_{self.gname(b)} {round(v*SC)};')
        bm = data.get('basemap', {})
        figure_alternates = {source: [name for name in spec['choices'].values() if name != source]
                             for source, spec in data.get('designs', {}).items() if source in '469' and len(source)==1}
        members = lambda c: ' '.join([self.gname(c)] + [self.gname(a) for a, b in sorted(bm.items()) if b == c and ord(a) in cmap and a not in SEPARATE_LATIN]
                                    + figure_alternates.get(c, [])
                                    + (['i.dotless','i.loclTRK','i.below.dotless'] if c == 'i' else ['j.dotless'] if c == 'j' else []))
        alternate_lines, alternate_classes = [], []
        if self.display:
            from display.letter_alternates import alternate_kerning
            alternate_lines, alternate_classes = alternate_kerning(
                display_spacing, data['designs'], bm, paths, hm, self.gname, SC,
                left_groups, right_groups)
        cls = [f'@L_{self.gname(c)} = [{members(c)}];' for c in sorted(left_groups)] + \
              [f'@R_{self.gname(c)} = [{members(c)}];' for c in sorted(right_groups)]
        from latin_layout import latin_features
        shear = self.TAN if italic else math.tan(math.radians(self.settings.get('slant', 0)))
        fea = latin_features(records, origins, hm, cmap, SC, shear, ITAL_CENTER)
        fea += '\n'.join(cls) + '\nfeature kern {\n lookupflag IgnoreMarks;\n' + '\n'.join(lines) + '\n} kern;\n'
        if self.display:
            fea += '\n'.join(alternate_classes)+'\nfeature kern {\n lookupflag IgnoreMarks;\n'+'\n'.join(alternate_lines)+'\n} kern;\n'
        # Equal adjustments for every tabular digit preserve formatted-number alignment.
        # Separate classes leave ordinary digit widths and digit-to-digit spacing intact.
        # Zero's final separator overrides control the shared tabular margin.
        tabular_names = [name+'.tf' for name in digit_names]
        if self.display:
            tabular_names += [name for source, spec in data['designs'].items() if source.endswith('.tf')
                             for name in spec['choices'].values() if name != source]
        fea += '@tabular_figures = [' + ' '.join(tabular_names) + '];\n'
        fea += 'feature kern {\n lookupflag IgnoreMarks;\n'
        for separator in '.,':
            fea += f' pos @tabular_figures {self.gname(separator)} {round(KERN.get("0" + separator, 0)*SC)};\n'
            fea += f' pos {self.gname(separator)} @tabular_figures {round(KERN.get(separator + "0", 0)*SC)};\n'
        fea += '} kern;\n'
        hu=self.LANGUAGE_KERN[ps_style]['hu']
        if hu:
            fea+='feature kern {\n script latn; language HUN; lookup HungarianCaps {\n lookupflag IgnoreMarks;\n'
            fea+='\n'.join(f' pos {self.gname(pair[0])} {self.gname(pair[1])} {value*SC};' for pair,value in hu.items())
            fea+='\n } HungarianCaps;\n} kern;\n'
        if ord('ﬁ') in cmap and ord('ﬂ') in cmap:   # joined fi / fl, switched on automatically
            fea += f"feature liga {{\n  sub {self.gname('f')} {self.gname('i')} by {self.gname('ﬁ')};\n  sub {self.gname('f')} {self.gname('l')} by {self.gname('ﬂ')};\n}} liga;\n"
            # where the text cursor can stop inside a joined letter (between the f and the i / l)
            cut = hm[self.gname('f')]
            fea += f"table GDEF {{\n  LigatureCaretByPos {self.gname('ﬁ')} {cut};\n  LigatureCaretByPos {self.gname('ﬂ')} {cut};\n}} GDEF;\n"
        plain = ' '.join(self.gname(d) for d in digits)
        tabular = ' '.join(name + '.tf' for name in digit_names)
        numerator = ' '.join(name + '.numr' for name in digit_names)
        denominator = ' '.join(name + '.dnom' for name in digit_names)
        fea += f"@figures = [{plain}];\n@numerators = [{numerator}];\n@denominators = [{denominator}];\n"
        fea += f"feature sups {{ sub @figures by [{' '.join(self.gname(ch) for ch in supers)}]; }} sups;\n"
        fea += f"feature subs {{ sub @figures by [{' '.join(self.gname(ch) for ch in subs)}]; }} subs;\n"
        fea += f"""feature frac {{
          sub @figures {self.gname('/')}\u0027 @figures by {fraction_name};
          sub @figures\u0027 {fraction_name} by @numerators;
          rsub @figures\u0027 @numerators by @numerators;
          sub {fraction_name} @figures\u0027 by @denominators;
          sub @denominators @figures\u0027 by @denominators;
        }} frac;
    """
        # HarfBuzz applies 'frac' to the slash and following digits for ASCII input. A later
        # default ligature pass completes the surrounding numerators and denominators after
        # the slash becomes U+2044; it also handles directly typed fraction slashes.
        fea += f"""feature liga {{
          sub @figures\u0027 {fraction_name} by @numerators;
          rsub @figures\u0027 @numerators by @numerators;
          sub {fraction_name} @figures\u0027 by @denominators;
          sub @denominators @figures\u0027 by @denominators;
        }} liga;
    """
        # Apply tabular figures last: sups/subs/frac must still see proportional digit names.
        fea += f"feature tnum {{ sub @figures by [{tabular}]; }} tnum;\n"
        if self.display:
            from display.letter_alternates import stylistic_features
            fea += stylistic_features(data['designs'], self.gname)
            capitals = sorted({name for code, name in cmap.items() if chr(code).isupper()})
            capitals += [name for source, spec in data['designs'].items() if len(source)==1 and source.isupper()
                         for name in spec['choices'].values() if name != source]
            extra = display_spacing.capital_space * SC
            fea += ('@display_capitals = ['+' '.join(capitals)+'];\n'
                    'feature cpsp { lookupflag IgnoreMarks;\n'
                    f' pos @display_capitals <{extra//2} 0 {extra} 0>;\n}} cpsp;\n')
        addOpenTypeFeaturesFromString(fb.font, fea)
        fb.font['name'].removeNames(platformID=1)
        fb.save(out)
        if not self.autohint(out):
            raise RuntimeError(f'Screen tuning failed for {shown}; stopping the build')
        t = TTFont(out); t.flavor = 'woff2'; t.save(out.replace('.otf', '.woff2'))
        if self.display:
            from display.title_spacing import write_spacing
            write_spacing(out, self.settings, origins, display_spacing, self.asset_dir, data['designs'])

    def configured_stroke(self, cmds, dx, width=None, cap_mask=(True, True)):
        """Expand in oval-pen space, then construct flat caps in stroke coordinates.

        The butt stroke supplies the two true offset walls. A terminal trapezoid
        joins those walls to a face perpendicular to the original endpoint tangent.
        Its extent is the nib's support along that tangent (a square cap for F=1).
        """
        # An upright Reader with display options must retain zero shear.
        shear = self.TAN if self.display or self.ITAL else math.tan(math.radians(self.settings.get('slant', 0)))
        # Each open subpath owns its caps; an endpoint must never clip another stroke.
        subpaths = []
        for command in cmds:
            if command[0] == 'M':
                subpaths.append([])
            subpaths[-1].append(command)
        if len(subpaths) > 1:
            result = Path()
            for subpath in subpaths:
                result = pathops.op(result, self.configured_stroke(subpath, dx, width, cap_mask), PathOp.UNION)
            return result
        path = Path(); pen = path.getPen()
        T = lambda pt: ((pt[0] + dx) * SC * BIG, -pt[1] * SC * BIG)
        open_ = False
        for c in cmds:
            if c[0] == 'M':
                if open_: pen.endPath()
                pen.moveTo(T(c[1])); open_ = True
            elif c[0] == 'L': pen.lineTo(T(c[1]))
            elif c[0] == 'C': pen.curveTo(T(c[1][0]), T(c[1][1]), T(c[1][2]))
            elif c[0] == 'Z': pen.closePath(); open_ = False
        if open_: pen.endPath()
        # angled oval pen: map the drawing into "pen space" (where the pen is round), stroke, map back
        t = math.radians(self.PEN); c, s_ = math.cos(t), math.sin(t)
        def mat(k):   # R(t) * scaleY(k) * R(-t)
            """Return the rotated oval-pen scale matrix for the given ratio."""
            return (c*c + k*s_*s_, (1 - k)*c*s_, (1 - k)*c*s_, s_*s_ + k*c*c)
        a, b, cc, d = mat(self.F)            # into pen space
        path = path.transform(scaleX=a, skewX=b, skewY=cc, scaleY=d)
        cap = LineCap.BUTT_CAP if self.CAP_FLAT else LineCap.ROUND_CAP
        join = LineJoin.MITER_JOIN if self.JOIN_SHARP else LineJoin.ROUND_JOIN
        path.stroke((width or self.S) * SC * BIG, cap, join, MITER_LIMIT)
        path.convertConicsToQuads(0.05)
        path.simplify(fix_winding=True)
        a, b, cc, d = mat(1.0 / self.F)      # back out
        path = path.transform(scaleX=a, skewX=b, skewY=cc, scaleY=d)
        path = path.transform(scaleX=1.0/BIG, scaleY=1.0/BIG)
        if self.CAP_FLAT and cmds[-1][0] != 'Z':
            from display.shape_geometry import contours, tangent
            segments = contours(self.center_path(cmds, dx))[0]
            # contours() does not add a closing edge to an open path.
            if segments[0][0] != segments[-1][-1]:
                radius = (width or self.S)*SC/2
                for segment, at_end, enabled in ((segments[0], False, cap_mask[0]),
                                                 (segments[-1], True, cap_mask[1])):
                    if not enabled: continue
                    tx, ty = tangent(segment, at_end)
                    norm = math.hypot(tx, ty)
                    if not norm: continue
                    tx, ty = tx/norm, ty/norm
                    if not at_end: tx, ty = -tx, -ty
                    # Build the face after the cut's oblique shear. A perpendicular
                    # cap built before shear would no longer be perpendicular in Ink.
                    tx, ty = tx+shear*ty, ty
                    norm = math.hypot(tx, ty); tx, ty = tx/norm, ty/norm
                    nx, ny = -ty, tx
                    # C=A*Aᵀ is the pen covariance. Its normal support gives
                    # offset width; C*n/support is the actual wall contact vector.
                    fa, fb = a+shear*cc, b+shear*d
                    xx, xy, yy = fa*fa+fb*fb, fa*cc+fb*d, cc*cc+d*d
                    hn = math.sqrt(nx*(xx*nx+xy*ny)+ny*(xy*nx+yy*ny))
                    ht = math.sqrt(tx*(xx*tx+xy*ty)+ty*(xy*tx+yy*ty))
                    vx, vy = radius*(xx*nx+xy*ny)/hn, radius*(xy*nx+yy*ny)/hn
                    px, py = segment[-1] if at_end else segment[0]
                    px += shear*py
                    ex, ey = px+radius*ht*tx, py+radius*ht*ty
                    cap_path = Path(); cap_pen = cap_path.getPen()
                    points = [(px+vx, py+vy), (ex+radius*hn*nx, ey+radius*hn*ny),
                              (ex-radius*hn*nx, ey-radius*hn*ny), (px-vx, py-vy)]
                    points = [(x-shear*y, y) for x, y in points]
                    cap_pen.moveTo(points[0])
                    for point in points[1:]: cap_pen.lineTo(point)
                    cap_pen.closePath()
                    path = pathops.op(path, cap_path, PathOp.UNION, fix_winding=True)
        return path

    def center_path(self, cmds, dx):
        """Read a skeleton at font scale for terminal attachment and join construction."""
        path = Path(); pen = path.getPen(); opened = False
        pt = lambda p: ((p[0]+dx)*SC, -p[1]*SC)
        for command in cmds:
            if command[0] == 'M':
                if opened: pen.endPath()
                pen.moveTo(pt(command[1])); opened = True
            elif command[0] == 'L': pen.lineTo(pt(command[1]))
            elif command[0] == 'C': pen.curveTo(*(pt(p) for p in command[1]))
            elif command[0] == 'Z': pen.closePath(); opened = False
        if opened: pen.endPath()
        return path

    def configured_outline(self, g, dx):
        """Join strokes, dots and fills, clean the outline, then apply the cut slant."""
        inputs = [(self.parse(p['d']), p['w']) for p in g['paths']]
        bodies = [self.configured_stroke(cmds, dx, width, (False, False)) for cmds, width in inputs]
        dots = [self.circle(cx, cy, r, dx) for cx, cy, r in g['circles']]
        shapes = []
        from display.shape_geometry import contours, sample, length, tangent
        centers = [contours(self.center_path(cmds, dx)) for cmds, width in inputs]
        endpoints = [(i, point) for i, items in enumerate(centers)
                     if inputs[i][0][-1][0] != 'Z' for segments in items
                     for point in (segments[0][0], segments[-1][-1])]
        terminals = []
        for i, (cmds, width) in enumerate(inputs):
            mask = [True, True]
            if self.CAP_FLAT and cmds[-1][0] != 'Z':
                segments = centers[i][0]
                for side, point in enumerate((segments[0][0], segments[-1][-1])):
                    attached = any(body.contains(point) for j, body in enumerate(bodies) if j != i)
                    attached |= any(dot.contains(point) for dot in dots)
                    attached |= any(j != i and math.dist(point, q) <= 2*SC for j, q in endpoints)
                    # A returning path can join its own stem (P/R/e). Check the
                    # other centerline segments, excluding its adjacent segment.
                    others = segments[1:] if side == 0 else segments[:-1]
                    for segment in others:
                        count = max(1, math.ceil(length(segment)/2))
                        if any(math.dist(point, sample(segment, j/count)) <= 2*SC
                               for j in range(count+1)):
                            attached = True
                            break
                    mask[side] = not attached
                    direction = tangent(segments[0] if side == 0 else segments[-1], side == 1)
                    if side == 1: direction = (-direction[0], -direction[1])
                    if segments[0][0] != segments[-1][-1]:
                        terminals.append((i, point, direction, width))
            shapes.append(self.configured_stroke(cmds, dx, width, mask) if self.CAP_FLAT else bodies[i])
        shapes += dots
        # Two terminal rays at the same knot form a join, not two capped strokes.
        # Stroke a tiny, tangent-aligned connector with the active join/miter rule.
        # This fills the outer corner without extending either terminal into a spur.
        for ti, (owner, point, direction, width) in enumerate(terminals):
            for other, q, outgoing, other_width in terminals[ti+1:]:
                if owner == other or math.dist(point, q) > 2*SC: continue
                join = ((point[0]+q[0])/2, (point[1]+q[1])/2)
                ray = lambda v: (join[0]+v[0]/math.hypot(*v), join[1]+v[1]/math.hypot(*v))
                if not math.hypot(*direction) or not math.hypot(*outgoing): continue
                pts = [ray(direction), join, ray(outgoing)]
                cmds = [('M' if j == 0 else 'L', (x/SC-dx, -y/SC)) for j, (x,y) in enumerate(pts)]
                shapes.append(self.configured_stroke(cmds, dx, min(width, other_width), (False, False)))
        for f in g.get('fills', []):            # filled shapes (holes allowed), plus a round-cornered outline unless turned off
            cmds = self.parse(f['d'])
            if f['sw'] > 0: shapes.append(self.configured_stroke(cmds, dx))
            fp = Path(); pen = fp.getPen(); open_ = False
            for c in cmds:
                pt = None if c[0] == 'Z' else ((c[1][0] + dx) * SC, -c[1][1] * SC)
                if c[0] == 'M':
                    if open_: pen.closePath()
                    pen.moveTo(pt); open_ = True
                elif c[0] == 'L': pen.lineTo(pt)
                elif c[0] == 'Z': pen.closePath(); open_ = False
            if open_: pen.closePath()
            fp.fillType = pathops.FillType.EVEN_ODD
            fp.simplify(fix_winding=True)
            shapes.append(fp)
        if not shapes: return None
        r = shapes[0]                           # merge one at a time (the batch merge could drop simple fills)
        for s in shapes[1:]:
            r = pathops.op(r, s, PathOp.UNION, fix_winding=True)
        r.convertConicsToQuads(0.02)
        r = cleanup(r)
        if self.ITAL or self.settings.get('slant', 0):
            shear = self.TAN if self.ITAL else math.tan(math.radians(self.settings.get('slant', 0)))
            r = r.transform(skewX=shear, translateX=-shear * ITAL_CENTER * SC)
        return cleanup(r)
