"""Drawing engine for the SEIHouse Noto redraw: modulated strokes, joins and soft corners.

Everything here is original geometry. A stroke is described by its centreline; its
thickness follows the stroke direction (verticals full, horizontals lighter, with an
optional stress tilt) and can taper where it grows out of a stem. Parts are united,
then every outside corner is softened by one family-wide radius.
"""
from __future__ import annotations

import math

import numpy as np
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

KAPPA = 0.5523


class Style:
    """Stroke settings shared by a group of glyphs (lowercase, capitals, figures)."""

    def __init__(self, thick, thin, tilt=0.0, soft=13.0, soft_in=0.0):
        self.thick, self.thin, self.tilt = thick, thin, math.radians(tilt)
        self.soft, self.soft_in = soft, soft_in

    def width(self, angle):
        return self.thin + (self.thick - self.thin) * np.sin(angle - self.tilt) ** 2

    def but(self, **changes):
        clone = Style(self.thick, self.thin, math.degrees(self.tilt), self.soft, self.soft_in)
        for key, value in changes.items():
            setattr(clone, key, math.radians(value) if key == 'tilt' else value)
        return clone


# ---------------------------------------------------------------- path parsing

def segments(d):
    """SVG path data -> ([(p0, p1, p2, p3) cubic control arrays], closed)."""
    pen = RecordingPen()
    parse_path(d, pen)
    out, start, current, closed = [], None, None, False
    for op, pts in pen.value:
        if op == 'moveTo':
            start = current = np.array(pts[0], float)
        elif op == 'lineTo':
            p = np.array(pts[0], float)
            out.append((current, current + (p - current) / 3, current + (p - current) * 2 / 3, p))
            current = p
        elif op == 'curveTo':
            a, b, c = (np.array(p, float) for p in pts)
            out.append((current, a, b, c))
            current = c
        elif op == 'closePath':
            closed = True
            if np.hypot(*(current - start)) > 1e-6:
                p = start
                out.append((current, current + (p - current) / 3, current + (p - current) * 2 / 3, p))
        elif op == 'endPath':
            pass
        else:
            raise ValueError(op)
    return out, closed


def reflect(d, about):
    """Mirror path data left-to-right about a vertical line."""
    segs, closed = segments(d)
    f = lambda p: f"{2*about-p[0]:.3f} {p[1]:.3f}"
    out = "M" + f(segs[0][0])
    for s in segs:
        out += " C" + " ".join(f(p) for p in s[1:])
    return out + (" Z" if closed else "")


def xform(d, sx=1, sy=1, dx=0, dy=0):
    """Scale then move path data, so a reused skeleton keeps its full stroke weight."""
    segs, closed = segments(d)
    f = lambda p: f"{p[0]*sx+dx:.3f} {p[1]*sy+dy:.3f}"
    out = "M" + f(segs[0][0])
    for s in segs:
        out += " C" + " ".join(f(p) for p in s[1:])
    return out + (" Z" if closed else "")


def bez(seg, t):
    t = np.asarray(t, float)[..., None]
    p0, p1, p2, p3 = seg
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3


def bez_d(seg, t):
    t = np.asarray(t, float)[..., None]
    p0, p1, p2, p3 = seg
    return 3*(1-t)**2*(p1-p0) + 6*(1-t)*t*(p2-p1) + 3*t**2*(p3-p2)


def unit(v):
    n = np.hypot(v[..., 0], v[..., 1])
    return v / np.where(n == 0, 1, n)[..., None]


def smooth(t):
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- curve fitting

def _fit_once(pts, u, t0, t1):
    p0, p3 = pts[0], pts[-1]
    b0, b1, b2, b3 = (1-u)**3, 3*(1-u)**2*u, 3*(1-u)*u**2, u**3
    a1, a2 = t0[None] * b1[:, None], t1[None] * b2[:, None]
    c00, c01, c11 = (a1*a1).sum(), (a1*a2).sum(), (a2*a2).sum()
    rest = pts - (p0[None]*(b0+b1)[:, None] + p3[None]*(b2+b3)[:, None])
    x0, x1 = (a1*rest).sum(), (a2*rest).sum()
    det = c00*c11 - c01*c01
    chord = np.hypot(*(p3-p0))
    if abs(det) > 1e-9:
        al, ar = (x0*c11 - x1*c01)/det, (c00*x1 - c01*x0)/det
    else:
        al = ar = chord/3
    if al < chord*1e-3 or ar < chord*1e-3:
        al = ar = chord/3
    return (p0, p0 + t0*al, p3 + t1*ar, p3)


def fit(pts, t0, t1, tol=0.35, depth=0):
    """Least-squares cubic(s) through sampled points with fixed end directions."""
    pts = np.asarray(pts, float)
    if len(pts) < 3 or np.hypot(*(pts[-1]-pts[0])) < 1e-6:
        return [(pts[0], pts[0] + (pts[-1]-pts[0])/3, pts[0] + (pts[-1]-pts[0])*2/3, pts[-1])]
    steps = np.hypot(*(pts[1:]-pts[:-1]).T)
    u = np.concatenate([[0], np.cumsum(steps)])
    u /= u[-1]
    best = None
    for _ in range(5):
        seg = _fit_once(pts, u, t0, t1)
        err = np.hypot(*(bez(seg, u) - pts).T)
        worst = int(err.argmax())
        if best is None or err[worst] < best[1]:
            best = (seg, err[worst], worst)
        if err[worst] < tol:
            return [seg]
        # One Newton step of each parameter toward the closest point on the fit.
        d1 = bez_d(seg, u)
        p0, p1, p2, p3 = seg
        tt = u[:, None]
        d2 = 6*(1-tt)*(p2-2*p1+p0) + 6*tt*(p3-2*p2+p1)
        diff = bez(seg, u) - pts
        num = (diff*d1).sum(1)
        den = (d1*d1).sum(1) + (diff*d2).sum(1)
        u = np.clip(u - num/np.where(abs(den) < 1e-9, 1, den), 0, 1)
        u[0], u[-1] = 0, 1
        u = np.maximum.accumulate(u)
    if depth > 4 or len(pts) < 7:
        return [best[0]]
    k = min(max(best[2], 2), len(pts)-3)
    tc = unit(pts[k-1] - pts[k+1])
    return fit(pts[:k+1], t0, tc, tol, depth+1) + fit(pts[k:], -tc, t1, tol, depth+1)


# ---------------------------------------------------------------- primitives

def _pen_path(contours):
    """contours: list of [start, [('L', p) | ('C', a, b, p)], ...] -> pathops.Path."""
    path = pathops.Path()
    pen = path.getPen()
    for start, parts in contours:
        pen.moveTo(tuple(start))
        for part in parts:
            if part[0] == 'L':
                pen.lineTo(tuple(part[1]))
            else:
                pen.curveTo(tuple(part[1]), tuple(part[2]), tuple(part[3]))
        pen.closePath()
    return path


def ribbon(d, style, scale=None, side=0, samples=28):
    """Modulated stroke around the centreline d.

    scale: {node index: multiplier}, interpolated smoothly between nodes (taper).
    side: 0 centred; 1 the path is the left edge; -1 the path is the right edge.
    """
    segs, closed = segments(d)
    factors = [1.0] * (len(segs) + 1)
    for index, value in (scale or {}).items():
        factors[index % (len(segs) + 1) if index < 0 else index] = value
    if closed:
        factors[len(segs)] = factors[0]

    def offsets(i, t):
        seg = segs[i]
        p, tangent = bez(seg, t), unit(bez_d(seg, t))
        f = factors[i] + (factors[i+1] - factors[i]) * smooth(np.asarray(t, float))
        w = f * style.width(np.arctan2(tangent[..., 1], tangent[..., 0]))
        normal = np.stack([-tangent[..., 1], tangent[..., 0]], -1)
        lo, ro = {0: (w/2, w/2), 1: (0*w, w), -1: (w, 0*w)}[side]
        return p + normal*lo[..., None], p - normal*ro[..., None]

    left, right = [], []
    ts = np.linspace(0, 1, samples + 1)
    eps = 1e-4
    for i, seg in enumerate(segs):
        l, r = offsets(i, ts)
        l0, r0 = offsets(i, np.array([0, eps]))
        l1, r1 = offsets(i, np.array([1-eps, 1]))
        chord = seg[3]-seg[0]
        straight = all(abs(v[0]*chord[1]-v[1]*chord[0]) < 1e-6 for v in (seg[1]-seg[0], seg[2]-seg[0])) \
            and factors[i] == factors[i+1]
        for store, pts, a, b in ((left, l, l0, l1), (right, r, r0, r1)):
            if straight:
                store.append([('L', pts[-1])])
                store[-1].insert(0, pts[0])
            else:
                cubics = fit(pts, unit(a[1]-a[0]), unit(b[0]-b[1]))
                store.append([pts[0]] + [('C', c[1], c[2], c[3]) for c in cubics])

    def forward(store):
        parts = []
        for chunk in store:
            if parts and np.hypot(*(chunk[0] - parts[-1][-1])) > 0.01:
                parts.append(('L', chunk[0]))
            parts += chunk[1:]
        return store[0][0], parts

    def backward(store):
        start, parts = forward(store)
        points = [start] + [p[-1] for p in parts]
        out = []
        for index in range(len(parts)-1, -1, -1):
            part, target = parts[index], points[index]
            out.append(('L', target) if part[0] == 'L' else ('C', part[2], part[1], target))
        return points[-1], out

    if closed:
        ls, lp = forward(left)
        rs, rp = backward(right)
        return _pen_path([(ls, lp), (rs, rp)])
    ls, lp = forward(left)
    rs, rp = backward(right)
    return _pen_path([(ls, lp + [('L', rs)] + rp)])


def poly(*points):
    return _pen_path([(np.array(points[0], float), [('L', np.array(p, float)) for p in points[1:]])])


def rect(x0, y0, x1, y1):
    return poly((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def bar(p0, p1, width, cut0='perp', cut1='perp'):
    """Straight stroke; each end is cut square ('perp'), horizontally ('h') or vertically ('v')."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    t = unit(p1 - p0)
    n = np.array([-t[1], t[0]])

    def edge(p, cut):
        if cut == 'h':
            off = np.array([width/2/abs(t[1]), 0.0]) * (1 if n[0] > 0 else -1)
        elif cut == 'v':
            off = np.array([0.0, width/2/abs(t[0])]) * (1 if n[1] > 0 else -1)
        else:
            off = n*width/2
        return p + off, p - off
    a0, b0 = edge(p0, cut0)
    a1, b1 = edge(p1, cut1)
    return poly(a0, a1, b1, b0)


def polyline(points, width):
    """Open stroke through points with mitred corners and square ends."""
    pts = [np.array(p, float) for p in points]
    dirs = [unit(b-a) for a, b in zip(pts, pts[1:])]
    normals = [np.array([-d[1], d[0]]) for d in dirs]
    left, right = [], []
    for i, p in enumerate(pts):
        if i == 0 or i == len(pts)-1:
            n = normals[0 if i == 0 else -1]
            off = n*width/2
        else:
            n = unit(normals[i-1] + normals[i])
            off = n*width/2/max(.35, float(n @ normals[i]))
        left.append(p+off)
        right.append(p-off)
    return poly(*left, *reversed(right))


def oval(x0, y0, x1, y1, k=KAPPA):
    cx, cy, rx, ry = (x0+x1)/2, (y0+y1)/2, (x1-x0)/2, (y1-y0)/2
    return _pen_path([(np.array([cx, y1]), [
        ('C', (cx+k*rx, y1), (x1, cy+k*ry), (x1, cy)), ('C', (x1, cy-k*ry), (cx+k*rx, y0), (cx, y0)),
        ('C', (cx-k*rx, y0), (x0, cy-k*ry), (x0, cy)), ('C', (x0, cy+k*ry), (cx-k*rx, y1), (cx, y1))])])


def oval_d(x0, y0, x1, y1, k=KAPPA):
    """Closed centreline for a round stroke, as path data."""
    cx, cy, rx, ry = (x0+x1)/2, (y0+y1)/2, (x1-x0)/2, (y1-y0)/2
    return (f"M{cx} {y1} C{cx+k*rx} {y1} {x1} {cy+k*ry} {x1} {cy} C{x1} {cy-k*ry} {cx+k*rx} {y0} {cx} {y0} "
            f"C{cx-k*rx} {y0} {x0} {cy-k*ry} {x0} {cy} C{x0} {cy+k*ry} {cx-k*rx} {y1} {cx} {y1} Z")


def union(*paths):
    out = pathops.Path()
    for p in paths:
        out = pathops.op(out, p, pathops.PathOp.UNION, fix_winding=True)
    return out


def keep(path, x0=-5000, y0=-5000, x1=5000, y1=5000):
    return pathops.op(path, rect(x0, y0, x1, y1), pathops.PathOp.INTERSECTION, fix_winding=True)


def minus(path, other):
    return pathops.op(path, other, pathops.PathOp.DIFFERENCE, fix_winding=True)


def move(path, dx=0, dy=0, sx=1, sy=1):
    return path.transform(sx, 0, 0, sy, dx, dy)


def flip_x(path, about):
    out = path.transform(-1, 0, 0, 1, 2*about, 0)
    return out


def rotate180(path, cx, cy):
    return path.transform(-1, 0, 0, -1, 2*cx, 2*cy)


# ---------------------------------------------------------------- corner softening

def _contours(path):
    pen = RecordingPen()
    path.draw(pen)
    out, current, start = [], None, None
    for op, pts in pen.value:
        if op == 'moveTo':
            start = current = np.array(pts[0], float)
            out.append([])
        elif op == 'lineTo':
            p = np.array(pts[0], float)
            out[-1].append([current, None, None, p])
            current = p
        elif op == 'curveTo':
            a, b, c = (np.array(p, float) for p in pts)
            out[-1].append([current, a, b, c])
            current = c
        elif op == 'qCurveTo':
            pts = [np.array(p, float) for p in pts]
            on = current
            for i, off in enumerate(pts[:-1]):
                nxt = pts[-1] if i == len(pts)-2 else (off + pts[i+1])/2
                out[-1].append([on, on + (off-on)*2/3, nxt + (off-nxt)*2/3, nxt])
                on = nxt
            current = pts[-1]
        elif op == 'closePath':
            if np.hypot(*(current-start)) > 1e-6:
                out[-1].append([current, None, None, start])
            current = start
    cleaned = []
    for contour in out:
        segs = [s for s in contour if np.hypot(*(s[3]-s[0])) > 0.05 or s[1] is not None and
                np.hypot(*(s[1]-s[0])) + np.hypot(*(s[2]-s[3])) > 0.5]
        for i, s in enumerate(segs):
            s[0] = segs[i-1][3]
        if len(segs) >= 2:
            cleaned.append(segs)
    return cleaned


def _cubic(s):
    if s[1] is None:
        return (s[0], s[0] + (s[3]-s[0])/3, s[0] + (s[3]-s[0])*2/3, s[3])
    return tuple(s)


def _tangent(s, end):
    c = _cubic(s)
    order = [c[1]-c[0], c[2]-c[0], c[3]-c[0]] if not end else [c[3]-c[2], c[3]-c[1], c[3]-c[0]]
    for v in order:
        if np.hypot(*v) > 1e-6:
            return unit(v)
    return np.array([1.0, 0.0])


def _length_table(s, n=48):
    ts = np.linspace(0, 1, n+1)
    pts = bez(_cubic(s), ts)
    return ts, np.concatenate([[0], np.cumsum(np.hypot(*(pts[1:]-pts[:-1]).T))])


def _split(s, ta, tb):
    """Sub-segment of s between parameters ta < tb."""
    if s[1] is None:
        return [s[0] + (s[3]-s[0])*ta, None, None, s[0] + (s[3]-s[0])*tb]
    def cut(c, t):
        p0, p1, p2, p3 = c
        a, b, cc = p0+(p1-p0)*t, p1+(p2-p1)*t, p2+(p3-p2)*t
        d, e = a+(b-a)*t, b+(cc-b)*t
        f = d+(e-d)*t
        return (p0, a, d, f), (f, e, cc, p3)
    c = tuple(s)
    if tb < 1:
        c, _ = cut(c, tb)
    if ta > 0:
        _, c = cut(c, ta/tb if tb else 0)
    return list(c)


def _area(contour):
    total = 0
    for s in contour:
        pts = bez(_cubic(s), np.linspace(0, 1, 9))
        total += (pts[:-1, 0]*pts[1:, 1] - pts[1:, 0]*pts[:-1, 1]).sum()
    return total/2


def soften(path, style, sharp=()):
    """Round ink corners: outside corners by style.soft, inside ones by style.soft_in.

    sharp: (x, y, radius) circles in which corners are left untouched.
    """
    contours = _contours(path)
    if not contours:
        return path
    areas = [_area(c) for c in contours]
    outer = 1 if areas[int(np.argmax(np.abs(areas)))] > 0 else -1
    result = []
    for contour in contours:
        n = len(contour)
        lengths = [_length_table(s) for s in contour]
        trims = [[0.0, 0.0] for _ in contour]   # [at start, at end] of each segment
        corners = {}
        for i in range(n):
            a, b = contour[i-1], contour[i]
            din, dout = _tangent(a, True), _tangent(b, False)
            angle = math.atan2(din[0]*dout[1]-din[1]*dout[0], din[0]*dout[0]+din[1]*dout[1])
            if abs(angle) < math.radians(14):
                continue
            radius = style.soft if angle*outer > 0 else style.soft_in
            if any(np.hypot(b[0][0]-x, b[0][1]-y) < r for x, y, r in sharp) or radius <= 0:
                continue
            half = min(abs(angle), math.radians(170))/2
            reach = min(radius*math.tan(half), 0.46*lengths[i-1][1][-1], 0.46*lengths[i][1][-1])
            if reach < 0.75:
                continue
            corners[i] = (din, dout, reach/math.tan(half), abs(angle))
            trims[i-1][1] = reach
            trims[i][0] = reach
        parts = []
        for i, s in enumerate(contour):
            ts, ls = lengths[i]
            ta = float(np.interp(trims[i][0], ls, ts))
            tb = float(np.interp(ls[-1]-trims[i][1], ls, ts))
            piece = _split(s, ta, tb)
            if i in corners:
                din, dout, r, angle = corners[i]
                handle = 4/3*math.tan(angle/4)*r
                parts.append(['corner', din*handle, -dout*handle, piece[0]])
            parts.append(piece)
        # Resolve corner starts now that every neighbour is known.
        final = []
        for i, part in enumerate(parts):
            if isinstance(part[0], str):
                prev = parts[i-1]
                final.append([prev[3], prev[3]+part[1], part[3]+part[2], part[3]])
            else:
                final.append(part)
        start = final[0][0]
        result.append((start, [('L', s[3]) if s[1] is None else ('C', s[1], s[2], s[3]) for s in final]))
    return _pen_path(result)
