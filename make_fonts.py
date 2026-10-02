"""
Builds SEIReader from the drawing rules in engine.js.

  python3 make_fonts.py                   uses settings.json
  python3 make_fonts.py my_changes.json   adds the changes copied from the SEIReader page

Needs: fonttools, skia-pathops, brotli, playwright (chromium).
Output: fonts/SEIReader-Regular.otf and .woff2
"""
import json, re, sys, os
import pathops
from pathops import Path, PathOp, LineCap, LineJoin, OpBuilder
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from fontTools.agl import UV2AGL
from fontTools.qu2cu import quadratic_to_curves

HERE = os.path.dirname(os.path.abspath(__file__))
SC = 2            # 2000 units per em: whole-number points, fine enough that rounding is invisible
UPM = 1000 * SC
BIG = 16          # stroke at 16x size for precise round ends, then shrink back

# vertical room reserved now so accented letters (É, Ǻ, Vietnamese stacks) fit later without changing line spacing
ASCENT, DESCENT = 950, 250

settings = json.load(open(os.path.join(HERE, 'settings.json'), encoding='utf-8'))
if __name__ == '__main__' and len(sys.argv) > 1:
    ch = json.load(open(sys.argv[1], encoding='utf-8'))
    for k in ('weights', 'weight', 'xHeight', 'ascender', 'lowercaseRoundness', 'capitalRoundness', 'letterWidth', 'wordSpace', 'overshoot', 'uFoot',
              'spaceBetweenAllLetters', 'letterSpace', 'pairSpace'):
        if k in ch: settings[k] = ch[k]
S = settings['weight']; F = settings['contrast']; ROUND = settings['lowercaseRoundness']
XHT = settings.get('xHeight', 520); CAPR = settings.get('capitalRoundness', 210)
WS = settings.get('letterWidth', 1.0); WORD = settings.get('wordSpace', 250)
import math
SLANT = settings.get('italicAngle', 9); TAN = math.tan(math.radians(SLANT))
ITAL = False   # set per build
ITAL_EXTRA_SPACE = 4   # italic gets a little extra room between letters
ITAL_CENTER = 330   # slant around this height so letters stay centered in their space
TRACK = settings['spaceBetweenAllLetters']; VERSION = settings['version']; FAMILY = settings['family']

def export():
    """Evaluate the configured drawing engine in Chromium and capture glyphs, anchors and pairs."""
    from playwright.sync_api import sync_playwright
    page = (open(os.path.join(HERE, 'export_head.html'), encoding='utf-8').read()
            + open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
            + open(os.path.join(HERE, 'export_tail.js'), encoding='utf-8').read() + '</script></body></html>')
    tmp = os.path.join(HERE, '_export.html'); open(tmp, 'w', encoding='utf-8').write(page)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + tmp)
        pg.evaluate(f"P.round={ROUND}; P.contrast={F}; P.xh={XHT}; P.caprx={CAPR}; P.ws={WS}; P.base={S}; P.os={1 if settings.get('overshoot', True) else 0}; P.ufoot={1 if settings.get('uFoot', True) else 0}; P.ital={1 if ITAL else 0}; P.straight={settings.get('uprightStraightness', 1)}; P.asc={settings.get('ascender', 770)}; P.trk={track_for(S) + (ITAL_EXTRA_SPACE if ITAL else 0)};")
        out = {'glyphs': pg.evaluate(f'exportGlyphs({S})'), 'alternates': pg.evaluate(f'exportAlternates({S})'),
               'kern': pg.evaluate('getKern()'), 'basemap': pg.evaluate('getBaseMap()'),
               'screenStroke': pg.evaluate(f'readingStroke({S})')}
        b.close()
    os.remove(tmp)
    return out

TOK = re.compile(r'([MLCZ])|(-?\d+(?:\.\d+)?)')
def parse(d):
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

def stroke(cmds, dx, width=None):
    """Oval pen: stretch the drawing tall, stroke it, squash it back. Vertical strokes keep the full
    weight, horizontal strokes come out thinner by the contrast amount, and curves blend smoothly."""
    path = Path(); pen = path.getPen()
    T = lambda pt: ((pt[0] + dx) * SC * BIG, -pt[1] * SC * BIG * F)
    open_ = False
    for c in cmds:
        if c[0] == 'M':
            if open_: pen.endPath()
            pen.moveTo(T(c[1])); open_ = True
        elif c[0] == 'L': pen.lineTo(T(c[1]))
        elif c[0] == 'C': pen.curveTo(T(c[1][0]), T(c[1][1]), T(c[1][2]))
        elif c[0] == 'Z': pen.closePath(); open_ = False
    if open_: pen.endPath()
    path.stroke((width or S) * SC * BIG, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
    path.convertConicsToQuads(0.05)
    return path.transform(scaleX=1.0/BIG, scaleY=1.0/(BIG*F))

def circle(cx, cy, r, dx):
    """Create a filled dot from four cubic arcs at the shared font-unit scale."""
    K = 0.5522847498; x, y, R = (cx + dx) * SC, -cy * SC, r * SC
    path = Path(); pen = path.getPen()
    pen.moveTo((x + R, y))
    pen.curveTo((x + R, y + K*R), (x + K*R, y + R), (x, y + R))
    pen.curveTo((x - K*R, y + R), (x - R, y + K*R), (x - R, y))
    pen.curveTo((x - R, y - K*R), (x - K*R, y - R), (x, y - R))
    pen.curveTo((x + K*R, y - R), (x + R, y - K*R), (x + R, y))
    pen.closePath(); return path

def outline(g, dx):
    """Merge a glyph's strokes, fills and dots, then apply its real italic shear."""
    shapes = [stroke(parse(p['d']), dx, p['w']) for p in g['paths']] + [circle(cx, cy, r, dx) for cx, cy, r in g['circles']]
    for f in g.get('fills', []):            # filled shapes (holes allowed), plus a round-cornered outline unless turned off
        cmds = parse(f['d'])
        if f['sw'] > 0: shapes.append(stroke(cmds, dx))
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
    r = thin_joins(r)
    if ITAL:
        r = r.transform(skewX=TAN, translateX=-TAN * ITAL_CENTER * SC)
    return r

JOIN_SCOOP = 0.55    # size of the gentle scoop at a join (share of stroke thickness)
JOIN_DEPTH = 0.0     # join carving is OFF: in this rounded style it shows up as dents when zoomed in (tried in 0.22)
JOIN_MIN_TURN = 35   # only sharp inside corners (degrees of turn) count as joins

def thin_joins(path):
    """Find sharp inside corners (where two strokes meet) and carve a tiny round notch there,
    so joins don't look heavier than the strokes around them."""
    import math
    rc = S * SC * JOIN_SCOOP; depth = S * SC * JOIN_DEPTH
    if depth <= 0: return path
    contours = list(path.contours)
    if not contours: return path
    def signed_area(pts):
        """Measure polygon orientation for the optional concave-join carving pass."""
        return sum(pts[i][0]*pts[(i+1) % len(pts)][1] - pts[(i+1) % len(pts)][0]*pts[i][1] for i in range(len(pts))) / 2
    corners = []
    biggest = None
    for c in contours:
        segs = [s for s in c.segments if s[0] not in ('moveTo', 'closePath', 'endPath')]
        start = next((s[1][0] for s in c.segments if s[0] == 'moveTo'), None)
        if start is None or not segs: continue
        # tangents in and out of every on-curve point
        prev = start; items = []
        for verb, pts in segs:
            pts = list(pts); end = pts[-1]
            first = pts[0] if len(pts) > 1 else end
            last = pts[-2] if len(pts) > 1 else prev
            items.append((prev, end, (first[0]-prev[0], first[1]-prev[1]), (end[0]-last[0], end[1]-last[1])))
            prev = end
        onpts = [it[1] for it in items]
        area = signed_area(onpts)
        if biggest is None or abs(area) > abs(biggest): biggest = area
        n = len(items)
        for i in range(n):
            a = items[i]; b = items[(i+1) % n]
            tin, tout = a[3], b[2]
            la, lb = math.hypot(*tin), math.hypot(*tout)
            if la < 1e-6 or lb < 1e-6: continue
            cross = (tin[0]*tout[1] - tin[1]*tout[0]) / (la*lb)
            dot = (tin[0]*tout[0] + tin[1]*tout[1]) / (la*lb)
            turn = math.degrees(math.atan2(cross, dot))
            corners.append((a[1], turn))
    if biggest is None: return path
    fill_on_left = biggest > 0
    for pt, turn in corners:
        concave = (turn < -JOIN_MIN_TURN) if fill_on_left else (turn > JOIN_MIN_TURN)
        if not concave: continue
        # find the open wedge beside this join: its middle direction and how wide it is
        opens = []
        for ang in range(0, 360, 4):
            dx_, dy_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            if all(not path.contains((pt[0] + dx_ * S*SC * f, pt[1] + dy_ * S*SC * f)) for f in (0.15, 0.4, 0.8)):
                opens.append(ang)
        if not opens: continue
        # the open angles form one run (may wrap past 360): find its middle and width
        opens.sort(); runs = [[opens[0]]]
        for aa in opens[1:]:
            if aa - runs[-1][-1] <= 4: runs[-1].append(aa)
            else: runs.append([aa])
        if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] >= 356: runs[0] = [x - 360 for x in runs[-1]] + runs[0]; runs.pop()
        run = max(runs, key=len)
        width = (run[-1] - run[0] + 4)
        if width < 20 or width > 150: continue          # not a real crotch
        mid = math.radians((run[0] + run[-1]) / 2)
        ux, uy = math.cos(mid), math.sin(mid)
        half = math.radians(width / 2)
        wall = depth * 0.45                              # how much it shaves off the walls
        dd = (depth - wall) / max(1e-3, (1 - math.sin(half)))   # distance of the scoop centre from the corner
        rho = dd + depth                                 # scoop radius: reaches `depth` past the corner
        rc = rho
        cx_, cy_ = pt[0] + ux * dd, pt[1] + uy * dd
        cut = Path(); pen = cut.getPen(); K = 0.5523 * rc; x, y = cx_, cy_
        pen.moveTo((x + rc, y)); pen.curveTo((x + rc, y + K), (x + K, y + rc), (x, y + rc))
        pen.curveTo((x - K, y + rc), (x - rc, y + K), (x - rc, y)); pen.curveTo((x - rc, y - K), (x - K, y - rc), (x, y - rc))
        pen.curveTo((x + K, y - rc), (x + rc, y - K), (x + rc, y)); pen.closePath()
        path = pathops.op(path, cut, PathOp.DIFFERENCE, fix_winding=True)
    path.convertConicsToQuads(0.02)
    return path

# ---------------------------------------------------------------- automatic pair spacing
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

def profiles(path, ys):
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

def auto_pairs(paths, hm, cmap):
    """Measure the real empty space between letter shapes and even it out (per style)."""
    step = 10 * SC
    capY = [y for y in range(0, 700*SC + 1, step)]
    lowY = [y for y in range(0, round(XHT*SC) + 1, step)]
    depth = AUTO_DEPTH * UPM
    prof = {}
    for ch in AUTO_CHARS:
        n = cmap.get(ord(ch))
        if not n: continue
        p = paths.get(n)
        Lc, Rc = profiles(p, capY); Ll, Rl = profiles(p, lowY)
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
    lower = set('abcdefghijklmnopqrstuvwxyzﬁﬂ')
    t_low = gap('n', 'n', 'low') if 'n' in prof else 0
    t_cap = gap('H', 'H', 'cap') if 'H' in prof else 0
    caps = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'); digits = set('0123456789')
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


def optical_pairs(paths, hm, cmap, kern, italic):
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
    body_y = range(round(XHT*SC*.12), round(XHT*SC*.88), 10*SC)
    full_y = range(0, 700*SC+1, 5*SC)
    depth = 60*SC
    prof = {}
    for ch in chars:
        name = cmap.get(ord(ch))
        if not name: continue
        left, right = profiles(paths[name], full_y)
        body = profiles(paths[name], body_y)
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

def private_dict(stroke_weight):
    """Screen-tuning info: the lines letters must snap to (baseline, lowercase height, capital height,
    descender) and the usual stem thickness, so the auto-tuner can keep small text crisp."""
    os_ = 10 * SC; xh = round(XHT * SC); cap = 700 * SC; asc = round(settings.get('ascender', 770) * SC)
    blues = sorted({(-os_, 0), (xh, xh + os_), (cap, cap + os_), (asc, asc + os_)})
    flat = [v for pair in blues for v in pair]
    return {'BlueValues': flat, 'OtherBlues': [-200*SC - os_, -200*SC],
            'StdVW': round(stroke_weight * SC), 'StdHW': round(stroke_weight * SC / F)}

def autohint(path_otf):
    """Run Adobe's auto-tuner (otfautohint) on the finished file, in place."""
    import subprocess, shutil
    tmp = path_otf + '.hinted.otf'
    executable = shutil.which('otfautohint') or os.path.join(os.path.dirname(sys.executable),
                                                            'otfautohint.exe' if os.name == 'nt' else 'otfautohint')
    r = subprocess.run([executable, path_otf, '-o', tmp], capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(tmp):
        shutil.move(tmp, path_otf); return True
    print('    screen tuning failed:', (r.stderr or r.stdout)[-300:]); return False

def draw_fitted(path, pen):
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

def charstring(path, adv):
    """Encode the fitted outline and advance as a CFF Type 2 charstring."""
    pen = T2CharStringPen(adv, None)          # whole-number points at 2000 units per em
    if path is not None: draw_fitted(path, pen)
    return pen.getCharString()

def lsb_of(path):
    """Return the rounded left ink bound, or zero for an empty glyph."""
    if path is None: return 0
    bp = BoundsPen(None); path.draw(bp); return round(bp.bounds[0]) if bp.bounds else 0

def center_ink(path, advance):
    """Place the finished outline, including its stroke and italic slant, in the middle of its advance."""
    bp = BoundsPen(None); path.draw(bp)
    if not bp.bounds: return path
    left, _, right, _ = bp.bounds
    return path.transform(translateX=(advance - (right - left)) / 2 - left)

def gname(ch):
    """Use the Adobe glyph name when available, otherwise a Unicode-derived name."""
    u = ord(ch)
    return UV2AGL.get(u, f'uni{u:04X}' if u <= 0xFFFF else f'u{u:05X}')

WCLASS = {'Thin':100, 'ExtraLight':200, 'Light':300, 'Regular':400, 'Medium':500, 'SemiBold':600, 'Bold':700, 'ExtraBold':800, 'Black':900}
STYLE_KERN = {}
LANGUAGE_KERN = {}
RHYTHM_BASELINE = os.path.join(HERE, 'old', '0.31')
with open(os.path.join(RHYTHM_BASELINE, 'settings.json'), encoding='utf-8') as f:
    rhythm_settings = json.load(f)
with open(os.path.join(RHYTHM_BASELINE, 'kern_styles.json'), encoding='utf-8') as f:
    rhythm_pairs = json.load(f)
RHYTHM_SETTINGS = ('weight','weights','contrast','lowercaseRoundness','spaceBetweenAllLetters',
                   'letterSpace','xHeight','capitalRoundness','letterWidth','overshoot','uFoot',
                   'italicAngle','uprightStraightness','ascender')
PRESERVE_RHYTHM = all(settings.get(k) == rhythm_settings.get(k) for k in RHYTHM_SETTINGS)


def retain_reading_pairs(kern, style):
    """Keep approved letter rhythm for the default build; custom settings remeasure it."""
    if not PRESERVE_RHYTHM: return
    letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzﬁﬂ')
    previous = rhythm_pairs[style]
    for pair in kern.keys() | previous.keys():
        if len(pair) == 2 and all(ch in letters for ch in pair):
            if pair in previous: kern[pair] = previous[pair]
            else: kern.pop(pair, None)


def clear_text_marks(paths, hm, cmap, kern, basemap):
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
        sampled[ch] = hm[name], profiles(paths[name],ys)
    for pair in pairs:
        closest = []
        for a in members[pair[0]]:
            advance, (_,right) = sampled[a]
            for b in members[pair[1]]:
                _, (left,_) = sampled[b]
                closest.extend(advance-r+l for r,l in zip(right,left) if r is not None and l is not None)
        if closest:
            kern[pair] = max(kern[pair], math.ceil((35*SC-min(closest))/SC))


SEPARATE_LATIN = set('ĄąĘę')


def ogonek_pairs(paths,hm,cmap,kern,basemap):
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
    sampled={ch:(hm[cmap[ord(ch)]],profiles(paths[cmap[ord(ch)]],ys))
             for ch in SEPARATE_LATIN|set(punctuation) if ord(ch) in cmap}
    for new in sorted(SEPARATE_LATIN):
        for other in punctuation:
            for a,b in ((new,other),(other,new)):
                advance,(_,right)=sampled[a];_,(left,_)=sampled[b]
                gaps=[advance-r+l for r,l in zip(right,left) if r is not None and l is not None]
                if gaps: kern[a+b]=max(kern.get(a+b,0),math.ceil((35*SC-min(gaps))/SC))


def hungarian_caps(paths,hm,cmap,kern):
    """Add clearance for uppercase Hungarian TY/TTY digraphs, only under lang=hu."""
    ys=range(0,700*SC+1,2*SC)
    sampled={ch:profiles(paths[cmap[ord(ch)]],ys) for ch in 'TY'}
    pairs={}
    for pair in ('TT','TY'):
        a,b=pair;right=sampled[a][1];left=sampled[b][0]
        gaps=[hm[cmap[ord(a)]]+kern.get(pair,0)*SC-r+l for r,l in zip(right,left) if r is not None and l is not None]
        delta=max(0,math.ceil((35*SC-min(gaps))/SC))
        if delta: pairs[pair]=delta
    return pairs

def track_for(thick):
    """Adjust the configured tracking by stroke weight relative to Regular."""
    reg = settings['weight']
    return TRACK + (thick - reg) * (0.25 if thick > reg else 0.1)

def build(data, out, style='Regular', italic=False):
    """Build and hint one style with the shared character set and OpenType features."""
    TR = track_for(S) + (ITAL_EXTRA_SPACE if italic else 0)
    ps_style = ('Italic' if style == 'Regular' else style + 'Italic') if italic else style
    shown = ('Italic' if style == 'Regular' else style + ' Italic') if italic else style
    KERN = {}
    ovr = settings.get('letterSpace', {})
    order = ['.notdef', 'space']; cmap = {32: 'space', 160: 'space'}; paths = {}; hm = {}; records = {}; origins = {}
    PRIVATE = {0xE000:'Ⓢ', 0xE001:'🎧', 0xE002:'💻', 0xE003:'📖', 0xE004:'🔖', 0xE005:'🔍', 0xE006:'🔔',
               0xE007:'🎤', 0xE008:'💿', 0xE009:'🔊', 0xE00A:'⚙', 0xE00B:'⌂', 0xE00C:'⚡', 0xE00D:'☀', 0xE00E:'☯', 0xE00F:'♥'}
    nd = Path(); pen = nd.getPen()
    pen.moveTo((60*SC,0)); pen.lineTo((460*SC,0)); pen.lineTo((460*SC,700*SC)); pen.lineTo((60*SC,700*SC)); pen.closePath()
    pen.moveTo((110*SC,50*SC)); pen.lineTo((110*SC,650*SC)); pen.lineTo((410*SC,650*SC)); pen.lineTo((410*SC,50*SC)); pen.closePath()
    nd.simplify(fix_winding=True)
    paths['.notdef'] = nd; paths['space'] = None; hm['.notdef'] = 520*SC; hm['space'] = round(WORD*SC)
    for ch, g in data['glyphs'].items():
        o = ovr.get(ch) or ovr.get(data.get('basemap', {}).get(ch, ''), {}) or {}; before, after = o.get('before', 0), o.get('after', 0)
        left = 0 if g.get('mark') else TR + g['sb0'] + before
        name = gname(ch); order.append(name); cmap[ord(ch)] = name
        records[name] = g; origins[name] = left
        try:
            paths[name] = outline(g, left)
        except pathops.PathOpsError as exc:
            raise RuntimeError(f'Could not union {shown} glyph {name}') from exc
        hm[name] = 0 if g.get('mark') else round((left + g['w'] + S + g['sb1'] + after + TR) * SC)
        if ch in '\u2009\u202f': hm[name] = 120 * SC

    # Add unencoded alternates without touching the proportional digit outlines or metrics.
    digits = '0123456789'
    digit_names = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
    tabular_advance = max(hm[gname(d)] for d in digits)
    for d, name in zip(digits, digit_names):
        alt = name + '.tf'
        order.append(alt)
        paths[alt] = center_ink(paths[gname(d)], tabular_advance)
        hm[alt] = tabular_advance

    for name, g in data['alternates'].items():
        if name.endswith('.tf'): continue  # same exact outline as the original digit, positioned above
        order.append(name)
        records[name] = g; origins[name] = TR + g['sb0']
        try:
            paths[name] = outline(g, TR + g['sb0'])
        except pathops.PathOpsError as exc:
            raise RuntimeError(f'Could not union {shown} alternate {name}') from exc
        hm[name] = round((2*TR + g['sb0'] + g['w'] + S + g['sb1']) * SC)

    # The small figures share a measured advance within each weight/style.
    supers = '⁰¹²³⁴⁵⁶⁷⁸⁹'; subs = '₀₁₂₃₄₅₆₇₈₉'
    mini_names = [gname(ch) for ch in supers + subs] + [name + suffix for name in digit_names for suffix in ('.numr', '.dnom')]
    mini_advance = max(hm[name] for name in mini_names)
    for name in mini_names:
        paths[name] = center_ink(paths[name], mini_advance)
        hm[name] = mini_advance

    fraction_name = gname('⁄')
    hm[fraction_name] = round(190 * SC)
    paths[fraction_name] = center_ink(paths[fraction_name], hm[fraction_name])
    for ch, numerator, denominator in (('½', 'one', 'two'), ('¼', 'one', 'four'), ('¾', 'three', 'four')):
        num_name, den_name = numerator + '.numr', denominator + '.dnom'
        left = paths[num_name]
        slash = paths[fraction_name].transform(translateX=hm[num_name])
        right = paths[den_name].transform(translateX=hm[num_name] + hm[fraction_name])
        paths[gname(ch)] = pathops.op(pathops.op(left, slash, PathOp.UNION, fix_winding=True),
                                     right, PathOp.UNION, fix_winding=True)
        hm[gname(ch)] = hm[num_name] + hm[fraction_name] + hm[den_name]

    for code, ch in PRIVATE.items():
        if ord(ch) in cmap: cmap[code] = cmap[ord(ch)]
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    ps = f'{FAMILY}-{ps_style}'
    fb.setupCFF(ps, {'FullName': f'{FAMILY} {shown}', 'version': VERSION, 'Weight': style,
                     'ItalicAngle': -SLANT if italic else 0},
                {n: charstring(paths[n], hm[n]) for n in order}, private_dict(data['screenStroke']))
    fb.setupHorizontalMetrics({n: (hm[n], lsb_of(paths[n])) for n in order})
    if italic:
        fb.setupHorizontalHeader(ascent=ASCENT*SC, descent=-DESCENT*SC, lineGap=0,
                                 caretSlopeRise=1000, caretSlopeRun=round(1000*TAN), caretOffset=0)
    else:
        fb.setupHorizontalHeader(ascent=ASCENT*SC, descent=-DESCENT*SC, lineGap=0)
    names = {'uniqueFontIdentifier': f'{FAMILY} {shown} {VERSION}', 'fullName': f'{FAMILY} {shown}',
             'psName': ps, 'version': f'Version {VERSION}', 'copyright': 'SEIHouse Productions LLC'}
    if style in ('Regular', 'Bold'):
        names.update({'familyName': FAMILY,
                      'styleName': (('Italic' if style == 'Regular' else 'Bold Italic') if italic else style)})
    else:   # apps that only understand Regular/Bold/Italic still list it, as "SEIReader Light"
        names.update({'familyName': f'{FAMILY} {style}', 'styleName': 'Italic' if italic else 'Regular',
                      'typographicFamily': FAMILY, 'typographicSubfamily': shown})
    fb.setupNameTable(names)
    fb.setupOS2(sTypoAscender=ASCENT*SC, sTypoDescender=-DESCENT*SC, sTypoLineGap=0,
                usWinAscent=1100*SC, usWinDescent=320*SC, sxHeight=round(XHT*SC), sCapHeight=700*SC,
                achVendID='SEIH', fsType=0,
                fsSelection=((0x40 if (style != 'Bold' and not italic) else 0) | (0x20 if style == 'Bold' else 0)
                             | (0x01 if italic else 0) | 0x80),  # + use typographic line metrics
                usWeightClass=WCLASS.get(style, 400), version=4)
    fb.font['head'].macStyle = (1 if style == 'Bold' else 0) | (2 if italic else 0)
    fb.font['head'].fontRevision = float(VERSION)
    os2 = fb.font['OS/2']; os2.recalcUnicodeRanges(fb.font); os2.recalcCodePageRanges(fb.font)
    from fontTools.otlLib.builder import buildStatTable
    wv = WCLASS.get(style, 400)
    buildStatTable(fb.font, [
        dict(tag='wght', name='Weight', values=[dict(value=wv, name=style, flags=(0x2 if style == 'Regular' else 0))]),
        dict(tag='ital', name='Italic', values=[dict(value=1, name='Italic')] if italic else
                                               [dict(value=0, name='Roman', flags=0x2, linkedValue=1)]),
    ], elidedFallbackName=2)
    fb.setupPost(isFixedPitch=0, underlinePosition=-120*SC, underlineThickness=60*SC, italicAngle=-SLANT if italic else 0)

    AUTO = auto_pairs(paths, hm, cmap)
    KERN.update(AUTO); KERN.update(data['kern'])
    KERN.update(optical_pairs(paths, hm, cmap, KERN, italic))
    retain_reading_pairs(KERN, ps_style)
    clear_text_marks(paths, hm, cmap, KERN, data.get('basemap', {}))
    # Additive foundation: retain every approved old pair when geometry is unchanged.
    latin_dir = os.path.join(HERE, 'old', '0.33')
    with open(os.path.join(latin_dir, 'settings.json'), encoding='utf-8') as file: latin_settings = json.load(file)
    if all(settings.get(k) == latin_settings.get(k) for k in RHYTHM_SETTINGS):
        with open(os.path.join(latin_dir, 'kern_styles.json'), encoding='utf-8') as file: old_kern = json.load(file)[ps_style]
        with TTFont(os.path.join(latin_dir, f'SEIReader-{ps_style}.woff2')) as old_font: old_codes = set(old_font.getBestCmap())
        for pair in list(KERN):
            if all(ord(ch) in old_codes for ch in pair) and pair not in old_kern: del KERN[pair]
        KERN.update(old_kern)
    ogonek_pairs(paths,hm,cmap,KERN,data['basemap'])
    # User-reported decimal fix: numeric separators override frozen/automatic pairs.
    numeric_pairs = {pair: value for pair, value in data['kern'].items()
                     if len(pair) == 2 and ((pair[0] in digits and pair[1] in '.,')
                                           or (pair[0] in '.,' and pair[1] in digits))}
    KERN.update(numeric_pairs)
    for k, v in settings.get('pairSpace', {}).items(): KERN[k] = v
    STYLE_KERN[ps_style] = dict(KERN)
    LANGUAGE_KERN[ps_style]={'hu':hungarian_caps(paths,hm,cmap,KERN)}
    if style == 'Regular' and not italic:
        json.dump(AUTO, open(os.path.join(HERE, 'kern_auto.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'    {len(AUTO)} automatic pairs')
    # pair spacing written with groups, so letters added later (accents) join the right group automatically
    left_groups, right_groups, lines = set(), set(), []
    for pair, v in KERN.items():
        a, b = pair[0], pair[1]
        if ord(a) not in cmap or ord(b) not in cmap or v == 0: continue
        left_groups.add(a); right_groups.add(b)
        lines.append(f'  pos @L_{gname(a)} @R_{gname(b)} {round(v*SC)};')
    bm = data.get('basemap', {})
    members = lambda c: ' '.join([gname(c)] + [gname(a) for a, b in sorted(bm.items()) if b == c and ord(a) in cmap and a not in SEPARATE_LATIN]
                                + (['i.dotless','i.loclTRK','i.below.dotless'] if c == 'i' else ['j.dotless'] if c == 'j' else []))
    cls = [f'@L_{gname(c)} = [{members(c)}];' for c in sorted(left_groups)] + \
          [f'@R_{gname(c)} = [{members(c)}];' for c in sorted(right_groups)]
    from latin_layout import latin_features
    fea = latin_features(records, origins, hm, cmap, SC, TAN if italic else 0, ITAL_CENTER)
    fea += '\n'.join(cls) + '\nfeature kern {\n lookupflag IgnoreMarks;\n' + '\n'.join(lines) + '\n} kern;\n'
    # Equal adjustments for every tabular digit preserve formatted-number alignment.
    # Separate classes leave ordinary digit widths and digit-to-digit spacing intact.
    # Zero's final separator overrides control the shared tabular margin.
    fea += '@tabular_figures = [' + ' '.join(name + '.tf' for name in digit_names) + '];\n'
    fea += 'feature kern {\n lookupflag IgnoreMarks;\n'
    for separator in '.,':
        fea += f' pos @tabular_figures {gname(separator)} {round(KERN.get("0" + separator, 0)*SC)};\n'
        fea += f' pos {gname(separator)} @tabular_figures {round(KERN.get(separator + "0", 0)*SC)};\n'
    fea += '} kern;\n'
    hu=LANGUAGE_KERN[ps_style]['hu']
    if hu:
        fea+='feature kern {\n script latn; language HUN; lookup HungarianCaps {\n lookupflag IgnoreMarks;\n'
        fea+='\n'.join(f' pos {gname(pair[0])} {gname(pair[1])} {value*SC};' for pair,value in hu.items())
        fea+='\n } HungarianCaps;\n} kern;\n'
    if ord('ﬁ') in cmap and ord('ﬂ') in cmap:   # joined fi / fl, switched on automatically
        fea += f"feature liga {{\n  sub {gname('f')} {gname('i')} by {gname('ﬁ')};\n  sub {gname('f')} {gname('l')} by {gname('ﬂ')};\n}} liga;\n"
        # where the text cursor can stop inside a joined letter (between the f and the i / l)
        cut = hm[gname('f')]
        fea += f"table GDEF {{\n  LigatureCaretByPos {gname('ﬁ')} {cut};\n  LigatureCaretByPos {gname('ﬂ')} {cut};\n}} GDEF;\n"
    plain = ' '.join(gname(d) for d in digits)
    tabular = ' '.join(name + '.tf' for name in digit_names)
    numerator = ' '.join(name + '.numr' for name in digit_names)
    denominator = ' '.join(name + '.dnom' for name in digit_names)
    fea += f"@figures = [{plain}];\n@numerators = [{numerator}];\n@denominators = [{denominator}];\n"
    fea += f"feature sups {{ sub @figures by [{' '.join(gname(ch) for ch in supers)}]; }} sups;\n"
    fea += f"feature subs {{ sub @figures by [{' '.join(gname(ch) for ch in subs)}]; }} subs;\n"
    fea += f"""feature frac {{
      sub @figures {gname('/')}\u0027 @figures by {fraction_name};
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
    addOpenTypeFeaturesFromString(fb.font, fea)
    fb.font['name'].removeNames(platformID=1)
    fb.save(out)
    if not autohint(out):
        raise RuntimeError(f'Screen tuning failed for {shown}; stopping the build')
    t = TTFont(out); t.flavor = 'woff2'; t.save(out.replace('.otf', '.woff2'))

if __name__ == '__main__':
    outdir = os.path.join(HERE, 'fonts'); os.makedirs(outdir, exist_ok=True)
    weights = dict(settings.get('weights', {}))
    weights['Regular'] = settings['weight']            # the main Thickness slider is Regular
    for italic in (False, True):
        ITAL = italic
        for style, w in weights.items():
            S = w
            data = export()
            if style == 'Regular' and not italic:
                json.dump(data['kern'], open(os.path.join(HERE, 'kern_base.json'), 'w', encoding='utf-8'), ensure_ascii=False)
            fname = (('Italic' if style == 'Regular' else style + 'Italic') if italic else style)
            build(data, os.path.join(outdir, f'{FAMILY}-{fname}.otf'), style, italic)
            print('built', FAMILY, VERSION, fname, 'thickness', w)
    with open(os.path.join(HERE, 'kern_styles.json'), 'w', encoding='utf-8') as f:
        json.dump(STYLE_KERN, f, ensure_ascii=False)
    with open(os.path.join(HERE, 'kern_languages.json'), 'w', encoding='utf-8') as f:
        json.dump(LANGUAGE_KERN,f,ensure_ascii=False)
    from build_subsets import build_subsets
    build_subsets()
