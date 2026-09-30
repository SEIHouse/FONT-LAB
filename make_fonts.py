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
if len(sys.argv) > 1:
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
    from playwright.sync_api import sync_playwright
    page = (open(os.path.join(HERE, 'export_head.html'), encoding='utf-8').read()
            + open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
            + open(os.path.join(HERE, 'export_tail.js'), encoding='utf-8').read() + '</script></body></html>')
    tmp = os.path.join(HERE, '_export.html'); open(tmp, 'w', encoding='utf-8').write(page)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + tmp)
        pg.evaluate(f"P.round={ROUND}; P.contrast={F}; P.xh={XHT}; P.caprx={CAPR}; P.ws={WS}; P.base={S}; P.os={1 if settings.get('overshoot', True) else 0}; P.ufoot={1 if settings.get('uFoot', True) else 0}; P.ital={1 if ITAL else 0}; P.straight={settings.get('uprightStraightness', 1)}; P.asc={settings.get('ascender', 770)}; P.trk={track_for(S) + (ITAL_EXTRA_SPACE if ITAL else 0)};")
        out = {'glyphs': pg.evaluate(f'exportGlyphs({S})'), 'alternates': pg.evaluate(f'exportAlternates({S})'),
               'kern': pg.evaluate('getKern()'), 'basemap': pg.evaluate('getBaseMap()')}
        b.close()
    os.remove(tmp)
    return out

TOK = re.compile(r'([MLCZ])|(-?\d+(?:\.\d+)?)')
def parse(d):
    toks = [(m.group(1), m.group(2)) for m in TOK.finditer(d)]; i = 0; cmds = []
    def num():
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
    K = 0.5522847498; x, y, R = (cx + dx) * SC, -cy * SC, r * SC
    path = Path(); pen = path.getPen()
    pen.moveTo((x + R, y))
    pen.curveTo((x + R, y + K*R), (x + K*R, y + R), (x, y + R))
    pen.curveTo((x - K*R, y + R), (x - R, y + K*R), (x - R, y))
    pen.curveTo((x - R, y - K*R), (x - K*R, y - R), (x, y - R))
    pen.curveTo((x + K*R, y - R), (x + R, y - K*R), (x + R, y))
    pen.closePath(); return path

def outline(g, dx):
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
AUTO_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;!?\'"‘’“”()-–—/&'
AUTO_STRENGTH = 0.6      # how much of the difference to correct (1 = all of it)
AUTO_DEPTH = 0.10        # how far into a letter's open space counts (share of the em)
AUTO_MIN, AUTO_MAX = -0.12, 0.04   # limits, as share of the em
AUTO_THRESHOLD = 15      # ignore small corrections (units per 1000)
AUTO_LOWLOW = 30         # lowercase+lowercase pairs are only touched when really off

from fontTools.pens.basePen import BasePen
class _Flat(BasePen):
    def __init__(self):
        super().__init__(None); self.polys = []; self.cur = []
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 7):
            t = i / 6; u = 1 - t
            self.cur.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0], u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 5):
            t = i / 4; u = 1 - t
            self.cur.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    def _closePath(self):
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
        A, B = prof[a], prof[b]
        RA = A[zone][1]; LB = B[zone][0]; tot = 0; k = 0
        for ra, lb in zip(RA, LB):
            ra_eff = max(ra if ra is not None else -1e9, A['Rmax'] - depth)
            lb_eff = min(lb if lb is not None else 1e9, B['Lmin'] + depth)
            tot += (A['adv'] - ra_eff) + lb_eff; k += 1
        return tot / max(k, 1)
    lower = set('abcdefghijklmnopqrstuvwxyz')
    t_low = gap('n', 'n', 'low') if 'n' in prof else 0
    t_cap = gap('H', 'H', 'cap') if 'H' in prof else 0
    caps = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'); digits = set('0123456789')
    lowp = set('.,'); quotes = set('\'"‘’“”'); letters = caps | lower
    def wanted(a, b):
        if 'j' in (a, b): return False                         # j's tail curls under its neighbour; leave it
        if a in caps and (b in caps or b in lower): return True    # AV, LT, To, Ya ...
        if (a in letters or a in digits) and b in lowp: return True  # r. y, P. 7.
        if a in quotes and (b in letters or b in digits): return True   # “A ’s
        if (a in letters or a in lowp) and b in quotes: return True    # L’ s” .”
        if a == '(' and (b in letters or b in digits): return True
        if (a in letters or a in digits) and b == ')': return True
        # lowercase+lowercase and number+number stay exactly as designed (t/f crossbars fool the measuring;
        # numbers get their own even-width set later)
        return False
    out = {}
    for a in prof:
        for b in prof:
            w = wanted(a, b)
            if not w: continue
            zone = 'low' if (a in lower or b in lower) else 'cap'
            target = t_low if zone == 'low' else t_cap
            k = AUTO_STRENGTH * (target - gap(a, b, zone))
            k = max(AUTO_MIN * UPM, min(AUTO_MAX * UPM, k))
            limit = AUTO_LOWLOW if w == 'lowlow' else AUTO_THRESHOLD
            if abs(k) >= limit * SC:
                out[a + b] = round(k / SC)       # stored per 1000, like the hand-set pairs
    return out

def private_dict():
    """Screen-tuning info: the lines letters must snap to (baseline, lowercase height, capital height,
    descender) and the usual stem thickness, so the auto-tuner can keep small text crisp."""
    os_ = 10 * SC; xh = round(XHT * SC); cap = 700 * SC; asc = round(settings.get('ascender', 770) * SC)
    blues = sorted({(-os_, 0), (xh, xh + os_), (cap, cap + os_), (asc, asc + os_)})
    flat = [v for pair in blues for v in pair]
    return {'BlueValues': flat, 'OtherBlues': [-200*SC - os_, -200*SC],
            'StdVW': round(S * SC), 'StdHW': round(S * SC / F)}

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
    pen = T2CharStringPen(adv, None)          # whole-number points at 2000 units per em
    if path is not None: draw_fitted(path, pen)
    return pen.getCharString()

def lsb_of(path):
    if path is None: return 0
    bp = BoundsPen(None); path.draw(bp); return round(bp.bounds[0]) if bp.bounds else 0

def center_ink(path, advance):
    """Place the finished outline, including its stroke and italic slant, in the middle of its advance."""
    bp = BoundsPen(None); path.draw(bp)
    if not bp.bounds: return path
    left, _, right, _ = bp.bounds
    return path.transform(translateX=(advance - (right - left)) / 2 - left)

def gname(ch):
    u = ord(ch)
    return UV2AGL.get(u, f'uni{u:04X}' if u <= 0xFFFF else f'u{u:05X}')

WCLASS = {'Thin':100, 'ExtraLight':200, 'Light':300, 'Regular':400, 'Medium':500, 'SemiBold':600, 'Bold':700, 'ExtraBold':800, 'Black':900}

def track_for(thick):
    reg = settings['weight']
    return TRACK + (thick - reg) * (0.25 if thick > reg else 0.1)

def build(data, out, style='Regular', italic=False):
    TR = track_for(S) + (ITAL_EXTRA_SPACE if italic else 0)
    ps_style = ('Italic' if style == 'Regular' else style + 'Italic') if italic else style
    shown = ('Italic' if style == 'Regular' else style + ' Italic') if italic else style
    KERN = {}
    ovr = settings.get('letterSpace', {})
    order = ['.notdef', 'space']; cmap = {32: 'space', 160: 'space'}; paths = {}; hm = {}
    PRIVATE = {0xE000:'Ⓢ', 0xE001:'🎧', 0xE002:'💻', 0xE003:'📖', 0xE004:'🔖', 0xE005:'🔍', 0xE006:'🔔',
               0xE007:'🎤', 0xE008:'💿', 0xE009:'🔊', 0xE00A:'⚙', 0xE00B:'⌂', 0xE00C:'⚡', 0xE00D:'☀', 0xE00E:'☯', 0xE00F:'♥'}
    nd = Path(); pen = nd.getPen()
    pen.moveTo((60*SC,0)); pen.lineTo((460*SC,0)); pen.lineTo((460*SC,700*SC)); pen.lineTo((60*SC,700*SC)); pen.closePath()
    pen.moveTo((110*SC,50*SC)); pen.lineTo((110*SC,650*SC)); pen.lineTo((410*SC,650*SC)); pen.lineTo((410*SC,50*SC)); pen.closePath()
    nd.simplify(fix_winding=True)
    paths['.notdef'] = nd; paths['space'] = None; hm['.notdef'] = 520*SC; hm['space'] = round(WORD*SC)
    for ch, g in data['glyphs'].items():
        o = ovr.get(ch) or ovr.get(data.get('basemap', {}).get(ch, ''), {}) or {}; before, after = o.get('before', 0), o.get('after', 0)
        left = TR + g['sb0'] + before
        name = gname(ch); order.append(name); cmap[ord(ch)] = name
        paths[name] = outline(g, left)
        hm[name] = round((left + g['w'] + S + g['sb1'] + after + TR) * SC)

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
        paths[name] = outline(g, TR + g['sb0'])
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
                {n: charstring(paths[n], hm[n]) for n in order}, private_dict())
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
    for k, v in settings.get('pairSpace', {}).items(): KERN[k] = v
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
    members = lambda c: ' '.join([gname(c)] + [gname(a) for a, b in sorted(bm.items()) if b == c and ord(a) in cmap])
    cls = [f'@L_{gname(c)} = [{members(c)}];' for c in sorted(left_groups)] + \
          [f'@R_{gname(c)} = [{members(c)}];' for c in sorted(right_groups)]
    fea = '\n'.join(cls) + '\nfeature kern {\n' + '\n'.join(lines) + '\n} kern;\n'
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
    fea += f"feature tnum {{ sub @figures by [{tabular}]; }} tnum;\n"
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
    addOpenTypeFeaturesFromString(fb.font, fea)
    fb.font['name'].removeNames(platformID=1)
    fb.save(out)
    autohint(out)
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
    from build_subsets import build_subsets
    build_subsets()
