"""SEIHouse Noto redraw: the letter drawings.

Each glyph is assembled from stems, modulated ribbons and bars (see pen.py), then
softened. All coordinates are original to this study, on a 1000-unit em.
"""
from __future__ import annotations

import pathops

from pen import (Style, bar, flip_x, keep, minus, move, oval, oval_d, poly, polyline, rect, reflect,
                 ribbon, rotate180, soften, union, xform)

X, CAP, ASC, DESC, OV = 520, 700, 744, -212, 11
K = 0.585                      # Balanced's full curve


class Sheet:
    """One weight of the family. weight 1.0 is Regular."""

    def __init__(self, weight=1.0, tilt=0.0, soft=13):
        self.weight = weight
        self.wide = 1 + (weight-1)*.13        # heavier weights are drawn a little wider
        self.tight = 1 - (weight-1)*.3        # and fitted a little closer
        stem, hair = weight/self.wide, 1 + (weight-1)*.72
        soft *= weight**.5
        self.lc = Style(88*stem, 74*hair, tilt, soft)
        self.uc = Style(95*stem, 79*hair, tilt, soft)
        self.fig = Style(91*stem, 76*hair, tilt, soft)
        self.glyphs = {}
        self.groups = {}                      # composite -> base, for shared kerning

    def put(self, ch, parts, lsb, rsb, style=None, sharp=(), ref=None):
        """ref=(x0, x1): measure the sidebearings from this span instead of the ink bounds."""
        path = union(*parts) if isinstance(parts, (list, tuple)) else parts
        path = soften(path, style or self.lc, sharp)
        x0, _, x1, _ = path.bounds
        if ref:
            x0, x1 = (x0 if ref[0] is None else ref[0]), (x1 if ref[1] is None else ref[1])
        lsb, rsb = lsb*self.tight, rsb*self.tight
        self.glyphs[ch] = (round(x1-x0+lsb+rsb), move(path, lsb-x0))


def draw(weight=1.0, tilt=0.0, soft=13):
    """-> ({char: (advance, path)}, {composite: base})."""
    sh = Sheet(weight, tilt, soft)
    lower(sh)
    upper(sh)
    figures(sh)
    marks(sh)
    wide = sh.wide
    glyphs = {ch: (round(width*wide), path.transform(wide, 0, 0, 1, 0, 0)) if ch not in '0123456789'
              else (width, path.transform(wide, 0, 0, 1, width*(1-wide)/2, 0))
              for ch, (width, path) in sh.glyphs.items()}
    return glyphs, sh.groups


# ---------------------------------------------------------------- lowercase

def arch_d(cl, cr, top, depth=182, lean=.585, down=0):
    """Centreline of a shoulder: out of a stem at cl, over the top, down the stem at cr."""
    px = cl + lean*(cr-cl)
    rx = cr - px
    ysh = top - rx*1.04
    return (f"M{cl} {top-depth} C{cl+26} {top-94} {px-(px-cl)*.52} {top} {px} {top} "
            f"C{px+K*rx} {top} {cr} {ysh+K*rx*1.04} {cr} {ysh} L{cr} {down}")


def lower(sh):
    lc = sh.lc
    s, h = lc.thick, lc.thin
    top = X+OV-h/2            # centreline height of a round top
    bot = -OV+h/2
    N, B = 74, 40            # straight and round sidebearings

    # n h m u r
    nw = 366+s
    n_arch = ribbon(arch_d(s/2+3, nw-s/2, top), lc, {0: .54})
    n = union(rect(0, 0, s, X), n_arch)
    sh.put('n', n, N, N-6)
    sh.put('h', [rect(0, 0, s, ASC), n_arch], N, N-6)
    mw = 318
    sh.put('m', [rect(0, 0, s, X), ribbon(arch_d(s/2+3, mw+s/2, top, lean=.57), lc, {0: .54}),
                 ribbon(arch_d(mw+s/2+3, 2*mw+s/2, top, lean=.57), lc, {0: .54})], N, N-6)
    sh.put('u', rotate180(n, nw/2, X/2), N-6, N)
    sh.put('r', [rect(0, 0, s, X),
                 ribbon(f"M{s/2+3} {top-182} C{s/2+29} {top-94} 132 {top+2} 226 {top+2} C252 {top+2} 276 {top-3} 298 {top-12}",
                        lc, {0: .54, 2: 1.16})], N, 14)

    # o and the bowls
    ow = 536
    o_d = oval_d(s/2+1, bot, ow-s/2-1, top, K)
    sh.put('o', ribbon(o_d, lc, {1: 1.02, 3: 1.02}), B, B)
    bw = 494
    bowl_d = (f"M{s/2+3} {top-150} C{s/2+34} {top-58} 150 {top} 258 {top} C380 {top} {bw-s/2} 406 {bw-s/2} {X/2} "
              f"C{bw-s/2} 114 380 {bot} 258 {bot} C150 {bot} {s/2+34} {bot+58} {s/2+3} {bot+150}")
    taper = {0: .52, 2: 1.02, 4: .52}
    sh.put('b', [rect(0, 0, s, ASC), ribbon(bowl_d, lc, taper)], N, B)
    sh.put('p', [rect(0, DESC, s, X), ribbon(bowl_d, lc, taper)], N, B)
    mirrored = ribbon(reflect(bowl_d, bw/2), lc, taper)
    sh.put('d', [rect(bw-s, 0, bw, ASC), mirrored], B, N)
    sh.put('q', [rect(bw-s, DESC, bw, X), mirrored], B, N)

    # c e
    c = ribbon(f"M440 392 C402 458 340 {top} 270 {top} C140 {top} {s/2} 400 {s/2} {X/2} "
               f"C{s/2} 120 140 {bot} 272 {bot} C344 {bot} 406 60 448 122", lc, {0: 1.06, 4: 1.06})
    c = minus(minus(c, rect(424, X/2, 700, 700)), rect(432, -100, 700, X/2))
    sh.put('c', c, B, 30)
    ew = 498
    e = ribbon(f"M452 126 C408 62 346 {bot} 274 {bot} C142 {bot} {s/2} 122 {s/2} {X/2+2} "
               f"C{s/2} 400 136 {top} 256 {top} C378 {top} {ew-s/2} 404 {ew-s/2} 296 L{ew-s/2} 238", lc, {0: 1.06})
    e = minus(e, rect(436, -100, 700, 190))
    sh.put('e', [e, rect(s/2, 238, ew-s/2, 238+h*.9)], B, B-2)

    # a
    aw = 446
    a_top = ribbon(f"M52 404 C96 462 160 {top} 232 {top} C340 {top} {aw-s/2} 444 {aw-s/2} 344 L{aw-s/2} 0", lc, {0: 1.06})
    a_top = minus(a_top, rect(-100, 300, 58, 520))
    a_bowl = ribbon(f"M{aw-s/2+6} 286 C352 294 296 296 228 290 C112 280 {s/2-2} 232 {s/2-2} 150 "
                    f"C{s/2-2} 74 106 {bot} 192 {bot} C290 {bot} 362 88 {aw-s/2} 190", lc, {0: .94, 4: .5})
    sh.put('a', [a_top, a_bowl], B+4, N-8)

    # s
    s_d = (f"M386 404 C348 462 298 {top} 228 {top} C140 {top} 80 448 80 380 C80 318 128 290 220 262 "
           f"C316 233 370 202 370 138 C370 68 306 {bot} 216 {bot} C142 {bot} 86 56 42 116")
    sp = ribbon(s_d, lc, {0: 1.05, 2: .96, 3: 1.2, 4: .96, 6: 1.05})
    sp = minus(minus(sp, rect(374, X/2, 700, 700)), rect(-200, -100, 52, X/2))
    sh.put('s', sp, 38, 38)

    # i j l t f
    dot = oval(s/2-52, X+118, s/2+52, X+222, .62)
    sh.put('i', [rect(0, 0, s, X), dot], N, N)
    sh.put('ȷ', ribbon(f"M{s/2} {X} L{s/2} -70 C{s/2} -144 2 {DESC+h/2} -70 {DESC+h/2} C-96 {DESC+h/2} -118 -170 -138 -160",
                       lc, {3: 1.05}), N, N, ref=(0, s))
    sh.put('ı', rect(0, 0, s, X), N, N)
    sh.put('j', [ribbon(f"M{s/2} {X} L{s/2} -70 C{s/2} -144 2 {DESC+h/2} -70 {DESC+h/2} C-96 {DESC+h/2} -118 -170 -138 -160",
                        lc, {3: 1.05}), dot], N, N, ref=(0, s))
    sh.put('l', ribbon(f"M{s/2} {ASC} L{s/2} 132 C{s/2} 62 82 {h/2-2} 146 {h/2-2} C168 {h/2-2} 188 38 206 44", lc, {3: 1.05}),
           N, 22)
    cross = h*.9
    sh.put('t', [ribbon(f"M150 656 L150 138 C150 66 190 {h/2-2} 256 {h/2-2} C284 {h/2-2} 308 39 330 47", lc, {3: 1.05}),
                 rect(22, X-cross, 312, X)], 20, 18)
    sh.put('f', [ribbon(f"M150 0 L150 598 C150 676 194 {ASC+OV-h/2} 264 {ASC+OV-h/2} C292 {ASC+OV-h/2} 316 708 338 700",
                        lc, {3: 1.05}), rect(22, X-cross, 304, X)], 20, -6)

    # k v w x y z
    sh.put('k', [rect(0, 0, s, ASC), bar((s/2, 150), (384, X), h+5, 'perp', 'h'),
                 bar((196, 322), (406, 0), s, 'perp', 'h')], N, 10)
    v = union(bar((46, X), (232, 0), s-2, 'h', 'h'), bar((418, X), (232, 0), h+5, 'h', 'h'))
    sh.put('v', v, 18, 18)
    w = union(bar((44, X), (192, 0), s-3, 'h', 'h'), bar((344, X), (192, 0), h+3, 'h', 'h'),
              bar((344, X), (496, 0), s-3, 'h', 'h'), bar((644, X), (496, 0), h+3, 'h', 'h'))
    sh.put('w', keep(w, y1=X), 20, 20)
    sh.put('x', [bar((48, X), (404, 0), s, 'h', 'h'), bar((396, X), (40, 0), h+5, 'h', 'h')], 14, 14)
    y_tail = ribbon(f"M432 560 L236 16 C204 -74 172 -128 120 -156 C92 -171 62 -174 30 -168", lc, {0: .93, 1: .93, 3: 1.08})
    sh.put('y', [bar((46, X), (228, 22), s-2, 'h', 'perp'), keep(y_tail, y1=X)], 18, 18, ref=(1, None))
    sh.put('z', [rect(34, X-h, 398, X), rect(12, 0, 404, h), keep(bar((358, X+20), (52, -20), s-4, 'h', 'h'), y0=0, y1=X)],
           30, 30)

    # g: bowl, ear, link and loop
    g_bowl = ribbon(oval_d(26+s/2-2, 222+h/2-2, 410-s/2+2, top, K), lc, {1: .97, 3: .97, 0: .97, 2: .93})
    g_ear = keep(ribbon(f"M332 444 C368 476 420 {X-h*.45} 500 {X-h*.45}", lc, {0: .9, 1: .9}), x1=482)
    g_loop = ribbon("M196 252 C134 234 98 202 98 162 C98 122 134 101 196 100 L330 98 C420 96 470 46 470 -30 "
                    "C470 -122 386 -190 256 -190 C128 -190 44 -138 44 -68 C44 -10 96 46 186 90",
                    lc, {0: .7, 1: .76, 2: .9, 3: .92, 4: .97, 5: 1.0, 6: .95, 7: .56})
    sh.put('g', [g_bowl, g_ear, g_loop], 30, 6)


# ---------------------------------------------------------------- capitals

def upper(sh):
    uc = sh.uc
    s, h = uc.thick, uc.thin
    top, bot = CAP+OV-h/2, -OV+h/2
    ft, fb = CAP-h/2, h/2          # flat (non-overshooting) horizontals
    N, B = 88, 50
    put = lambda ch, parts, l, r, **kw: sh.put(ch, parts, l, r, uc, **kw)

    hw = 560
    put('H', [rect(0, 0, s, CAP), rect(hw-s, 0, hw, CAP), rect(s/2, 362-h*.47, hw-s/2, 362+h*.47)], N, N)
    iw = 236
    put('I', [rect(iw/2-s/2, 0, iw/2+s/2, CAP), rect(0, 0, iw, h*.88), rect(0, CAP-h*.88, iw, CAP)], 46, 46)
    put('E', [rect(0, 0, s, CAP), rect(s/2, CAP-h, 408, CAP), rect(s/2, 366-h*.47, 378, 366+h*.47), rect(s/2, 0, 420, h)], N, 34)
    put('F', [rect(0, 0, s, CAP), rect(s/2, CAP-h, 402, CAP), rect(s/2, 346-h*.47, 364, 346+h*.47)], N, 24)
    put('L', [rect(0, 0, s, CAP), rect(s/2, 0, 398, h)], N, 16)
    tw = 536
    put('T', [rect(tw/2-s/2, 0, tw/2+s/2, CAP), rect(0, CAP-h, tw, CAP)], 22, 22)

    ow = 706
    o_d = oval_d(s/2+1, bot, ow-s/2-1, top, K)
    o = ribbon(o_d, uc, {1: 1.03, 3: 1.03})
    put('O', o, B, B)
    put('Q', [o, bar((540, 124), (634, -122), s-2)], B, B-18)
    cw = 640
    c_d = (f"M606 548 C552 630 470 {top} 378 {top} C186 {top} {s/2+1} 546 {s/2+1} {CAP/2} "
           f"C{s/2+1} 154 186 {bot} 380 {bot} ")
    c = ribbon(c_d + "C474 28 554 76 614 152", uc, {0: 1.05, 4: 1.05})
    c = minus(minus(c, rect(598, CAP/2, 900, 900)), rect(606, -100, 900, CAP/2))
    put('C', c, B, 34)
    gx = 652
    g = ribbon(c_d + f"C502 {bot} {gx-s/2} 86 {gx-s/2} 206 L{gx-s/2} 352", uc, {0: 1.05})
    g = minus(g, rect(608, CAP/2+40, 900, 900))
    put('G', [g, rect(378, 352-h, gx-s/2, 352)], B, N-18)
    dw = 664
    put('D', [rect(0, 0, s, CAP), ribbon(f"M{s/2} {ft} L286 {ft} C500 {ft} {dw-s/2-1} 556 {dw-s/2-1} {CAP/2} "
                                         f"C{dw-s/2-1} 144 500 {fb} 286 {fb} L{s/2} {fb}", uc, {2: 1.03})], N, B)
    mid = 372
    put('B', [rect(0, 0, s, CAP),
              ribbon(f"M{s/2} {ft} L300 {ft} C424 {ft} 492 610 492 518 C492 428 424 {mid} 304 {mid} L{s/2} {mid}", uc, {2: 1.0, 3: .93, 4: .93}),
              ribbon(f"M{s/2} {mid} L322 {mid} C458 {mid} 532 314 532 204 C532 96 452 {fb} 316 {fb} L{s/2} {fb}", uc, {0: .93, 1: .93, 2: 1.02})],
        N, 40)
    pb = 300
    p_bowl = ribbon(f"M{s/2} {ft} L306 {ft} C452 {ft} 530 596 530 482 C530 368 452 {pb} 306 {pb} L{s/2} {pb}", uc, {2: 1.02})
    put('P', [rect(0, 0, s, CAP), p_bowl], N, 30)
    rb = 322
    r_bowl = ribbon(f"M{s/2} {ft} L300 {ft} C440 {ft} 514 602 514 492 C514 384 440 {rb} 300 {rb} L{s/2} {rb}", uc, {2: 1.02})
    put('R', [rect(0, 0, s, CAP), r_bowl, bar((306, rb+10), (536, 0), s, 'perp', 'h')], N, 14)

    aw = 648
    a = keep(union(bar((42, 0), (aw/2, CAP+8), h+6, 'h', 'h'), bar((aw-42, 0), (aw/2, CAP+8), s, 'h', 'h')), y1=CAP)
    put('A', [a, rect(142, 196, aw-142, 196+h*.9)], 10, 10)
    vw = 628
    put('V', keep(union(bar((44, CAP), (vw/2, -8), s, 'h', 'h'), bar((vw-44, CAP), (vw/2, -8), h+6, 'h', 'h')), y0=0), 10, 10)
    w = union(bar((42, CAP), (226, -8), s-3, 'h', 'h'), bar((444, CAP+8), (226, -8), h+3, 'h', 'h'),
              bar((444, CAP+8), (662, -8), s-3, 'h', 'h'), bar((846, CAP), (662, -8), h+3, 'h', 'h'))
    put('W', keep(w, y0=0, y1=CAP), 12, 12)
    mw = 760
    m = union(rect(0, 0, s-6, CAP), rect(mw-s+6, 0, mw, CAP),
              bar((48, CAP+10), (mw/2, -4), s-2, 'h', 'h'), bar((mw-48, CAP+10), (mw/2, -4), h+4, 'h', 'h'))
    put('M', keep(m, y0=0, y1=CAP), N-4, N-4)
    nw = 594
    n = union(rect(0, 0, s-6, CAP), rect(nw-s+6, 0, nw, CAP), bar((50, CAP+12), (nw-50, -12), s+2, 'h', 'h'))
    put('N', keep(n, y0=0, y1=CAP), N-2, N-2)
    put('K', [rect(0, 0, s, CAP), bar((s/2, 252), (522, CAP), h+7, 'perp', 'h'), bar((244, 428), (548, 0), s+1, 'perp', 'h')], N, 8)
    put('X', [bar((50, CAP), (566, 0), s, 'h', 'h'), bar((556, CAP), (38, 0), h+7, 'h', 'h')], 12, 12)
    yw = 584
    put('Y', [bar((44, CAP), (yw/2, 318), s-1, 'h', 'perp'), bar((yw-44, CAP), (yw/2, 318), h+7, 'h', 'perp'),
              rect(yw/2-s/2, 0, yw/2+s/2, 338)], 8, 8)
    put('Z', [rect(36, CAP-h, 520, CAP), rect(14, 0, 536, h), keep(bar((476, CAP+20), (62, -20), s, 'h', 'h'), y0=0, y1=CAP)], 34, 34)
    uw = 592
    put('U', ribbon(f"M{s/2} {CAP} L{s/2} 256 C{s/2} 112 140 {bot} {uw/2} {bot} C{uw-140} {bot} {uw-s/2} 112 {uw-s/2} 256 L{uw-s/2} {CAP}", uc), N-6, N-6)
    j = ribbon(f"M262 {CAP} L262 196 C262 86 204 {bot} 112 {bot} C72 {bot} 36 36 4 54", uc, {3: 1.05})
    put('J', minus(j, rect(-200, -100, 10, 200)), 14, N-8)
    s_d = (f"M478 574 C430 640 356 {top} 270 {top} C150 {top} 72 612 72 520 C72 440 132 402 256 364 "
           f"C392 322 468 284 468 182 C468 88 388 {bot} 266 {bot} C166 {bot} 92 62 36 136")
    sp = ribbon(s_d, uc, {0: 1.05, 2: .96, 3: 1.2, 4: .96, 6: 1.05})
    sp = minus(minus(sp, rect(468, CAP/2, 900, 900)), rect(-200, -100, 46, CAP/2))
    put('S', sp, 44, 44)


# ---------------------------------------------------------------- figures

def figures(sh):
    fg = sh.fig
    s, h = fg.thick, fg.thin
    top, bot = CAP+OV-h/2, -OV+h/2
    ADV = 572

    def put(ch, parts):
        path = soften(union(*parts) if isinstance(parts, (list, tuple)) else parts, fg)
        x0, _, x1, _ = path.bounds
        sh.glyphs[ch] = (ADV, move(path, (ADV-(x1-x0))/2-x0))

    zw = 478
    put('0', ribbon(oval_d(s/2, bot, zw-s/2, top, .565), fg, {1: 1.02, 3: 1.02}))
    put('1', [rect(196, 0, 196+s, CAP), keep(bar((50, 548), (262, CAP+34), h+4, 'perp', 'h'), y1=CAP, x1=260),
              rect(52, 0, 430, h*.9)])
    put('2', [keep(ribbon(f"M56 548 C92 630 160 {top} 248 {top} C350 {top} 416 612 416 522 C416 440 372 376 284 290 L46 46",
                           fg, {0: 1.05, 3: .98, 4: .96}), x0=30, y0=0), rect(30, 0, 446, h)])
    three = union(ribbon(f"M58 596 C108 648 170 {top} 244 {top} C344 {top} 404 622 404 538 C404 452 342 388 236 388 L190 388",
                         fg, {0: 1.05, 3: .92, 4: .92}),
                  ribbon(f"M190 388 L246 388 C366 388 436 320 436 212 C436 98 354 {bot} 232 {bot} C150 {bot} 86 54 30 108",
                         fg, {0: .92, 1: .92, 4: 1.05}))
    put('3', minus(minus(three, rect(-200, 520, 64, 800)), rect(-200, -100, 40, 180)))
    put('4', [rect(318, 0, 318+s, CAP), keep(bar((356, CAP+20), (40, 178), h+6, 'h', 'h'), y0=180, y1=CAP, x1=400),
              rect(8, 180, 492, 180+h*.94)])
    five = ribbon(f"M104 388 C150 420 202 434 260 434 C366 434 436 356 436 234 C436 106 352 {bot} 232 {bot} C150 {bot} 88 54 34 106",
                  fg, {0: .8, 3: 1.05})
    put('5', [minus(five, rect(-200, -100, 44, 180)), bar((120, CAP), (97, 338), s-6, 'h', 'h'), rect(100, CAP-h, 420, CAP)])
    six_bowl = ribbon(oval_d(18+s/2, bot, 460-s/2, 444-h/2, .57), fg, {1: 1.0, 3: 1.0})
    six_stroke = ribbon(f"M414 640 C380 662 344 {top} 302 {top} C150 {top} {18+s/2} 524 {18+s/2} 300 L{18+s/2} 210",
                        fg, {0: 1.05})
    six = union(six_bowl, minus(six_stroke, rect(404, 500, 800, 800)))
    put('6', six)
    put('9', rotate180(six, 239, CAP/2))
    put('7', [rect(18, CAP-h, 452, CAP), keep(bar((414, CAP+20), (176, -20), s-2, 'h', 'h'), y0=0, y1=CAP)])
    put('8', [ribbon(oval_d(42+s/2-2, 374, 418-s/2+2, top, .57), fg, {0: .96, 1: .95, 3: .95, 2: .9}),
              ribbon(oval_d(16+s/2, bot, 444-s/2, 374, .57), fg, {0: .9})])


# ---------------------------------------------------------------- punctuation and accents

def marks(sh):
    lc, uc, fg = sh.lc, sh.uc, sh.fig
    s, h = lc.thick, lc.thin
    wt = sh.weight
    flat = lambda w: Style(w*wt, w*wt, soft=lc.soft)
    put = sh.put
    R = 55*wt**.6                       # full-stop radius
    stop = oval(0, -5, 2*R, 2*R-5, .62)
    high = move(stop, 0, X-2*R+3)
    tail = ribbon("M64 50 C74 -8 60 -72 16 -124", flat(94), {0: 1.05, 1: .4})
    comma = union(stop, move(tail, R-56))
    put('.', stop, 62, 62)
    put(',', comma, 58, 62)
    put(':', [stop, high], 70, 70)
    put(';', [comma, high], 66, 70)
    put('·', move(oval(0, 0, 92*wt**.6, 92*wt**.6, .62), 0, 228), 66, 66)
    bang = poly((0, CAP), (94*wt, CAP), (76*wt, 214), (18*wt, 214))
    put('!', [bang, move(stop, 47*wt-R)], 82, 82, fg)
    q = ribbon(f"M28 548 C62 632 132 {CAP+OV-fg.thin/2} 214 {CAP+OV-fg.thin/2} C312 {CAP+OV-fg.thin/2} 376 620 376 540 "
               f"C376 474 342 434 290 396 C238 358 216 326 216 268 L216 214", fg, {0: 1.05, 3: .97})
    put('?', [minus(q, rect(-200, 400, 36, 800)), move(stop, 216-R)], 36, 44, fg)
    dash = 250-h*.52
    put('-', rect(0, dash, 262, dash+h*1.04), 52, 52)
    put('–', rect(0, dash, 500, dash+h*1.0), 40, 40)
    put('—', rect(0, dash, 880, dash+h*1.0), 30, 30)
    tick = poly((0, CAP+10), (88*wt, CAP+10), (70*wt, 456), (18*wt, 456))
    put("'", tick, 58, 58)
    put('"', [tick, move(tick, 88*wt+84)], 58, 58)
    raised = move(comma, 0, CAP+12-(2*R-5))
    turned = rotate180(raised, R, CAP+12-R+60)
    turned = move(turned, 0, CAP+12-turned.bounds[3])
    gap = 2*R+50
    put('’', raised, 50, 54)
    put('‘', turned, 54, 50)
    put('”', [raised, move(raised, gap)], 50, 54)
    put('“', [turned, move(turned, gap)], 54, 50)
    paren = ribbon("M190 790 C82 636 {0} 472 {0} 284 C{0} 96 82 -64 190 -218".format(s/2), lc, {0: .74, 1: .93, 2: .74})
    put('(', paren, 54, 20)
    put(')', flip_x(paren, 100), 20, 54)
    put('/', bar((36, -110), (330, 770), h+2, 'h', 'h'), 10, 10)
    amp = ribbon(f"M604 -6 L212 430 C166 482 144 524 144 572 C144 632 188 {CAP+OV-fg.thin/2} 252 {CAP+OV-fg.thin/2} "
                 f"C318 {CAP+OV-fg.thin/2} 360 632 360 574 C360 512 320 474 238 424 C116 350 {s/2+2} 286 {s/2+2} 192 "
                 f"C{s/2+2} 92 124 {-OV+fg.thin/2} 244 {-OV+fg.thin/2} C392 {-OV+fg.thin/2} 492 130 536 340",
                 fg, {2: .96, 4: .96, 5: .92, 8: 1.04})
    put('&', minus(amp, rect(400, -100, 900, 0)), 44, 6, fg)
    mh = h*1.0
    put('+', [rect(0, 350-mh/2, 424, 350+mh/2), rect(212-mh/2, 138, 212+mh/2, 562)], 74, 74, fg)
    put('=', [rect(0, 350+62, 424, 350+62+mh), rect(0, 350-62-mh, 424, 350-62)], 74, 74, fg)

    sh.glyphs[' '] = (252, pathops.Path())
    sh.glyphs['\u00a0'] = (252, pathops.Path())
    symbols(sh, stop, comma, tick, q, bang, R)
    extended(sh)


def symbols(sh, stop, comma, tick, q, bang, R):
    lc, uc, fg = sh.lc, sh.uc, sh.fig
    s, h = lc.thick, lc.thin
    wt = sh.weight
    flat = lambda w: Style(w*wt, w*wt, soft=lc.soft)
    put = sh.put
    top, bot = CAP+OV-fg.thin/2, -OV+fg.thin/2
    put('…', [stop, move(stop, 2*R+86), move(stop, 4*R+172)], 62, 62)
    put('•', oval(0, 190, 190, 380, .6), 60, 60)
    put('‚', comma, 58, 62)
    put('„', [comma, move(comma, 2*R+50)], 58, 62)
    put('¡', rotate180(union(bang, move(stop, 47*wt-R)), 47*wt, X/2), 82, 82, fg)
    put('¿', rotate180(union(minus(q, rect(-200, 400, 36, 800)), move(stop, 216-R)), 200, X/2), 44, 36, fg)
    cw = 62*wt
    guil = polyline([(150, 420), (0, 250), (150, 80)], cw)
    put('‹', guil, 50, 50)
    put('›', flip_x(guil, 75), 50, 50)
    put('«', [guil, move(guil, 150+cw*.6)], 50, 50)
    put('»', [flip_x(guil, 75), move(flip_x(guil, 75), 150+cw*.6)], 50, 50)
    put('<', polyline([(400, 580), (0, 350), (400, 120)], h), 80, 92, fg)
    put('>', polyline([(0, 580), (400, 350), (0, 120)], h), 92, 80, fg)
    put('^', polyline([(0, 380), (190, CAP), (380, 380)], h*.95), 60, 60, fg)
    put('_', rect(0, -130, 520, -130+h*.86), 0, 0)
    put('|', rect(0, -222, h*.95, 796), 110, 110)
    put('\\', bar((330, -110), (36, 770), h+2, 'h', 'h'), 10, 10)
    put('[', [rect(0, -200, h*1.02, 786), rect(0, 786-h*.9, 196, 786), rect(0, -200, 196, -200+h*.9)], 84, 22)
    put(']', [rect(196-h*1.02, -200, 196, 786), rect(0, 786-h*.9, 196, 786), rect(0, -200, 196, -200+h*.9)], 22, 84)
    half = "M214 {0} C138 {0} 112 726 112 664 L112 414 C112 338 84 293 14 293".format(786-h*.45)
    brace = union(ribbon(half, lc, {0: .9, 2: .92, 3: .9}), ribbon(xform(half, sy=-1, dy=586), lc, {0: .9, 2: .92, 3: .9}))
    put('{', brace, 34, 24)
    put('}', flip_x(brace, 100), 24, 34)
    put('~', ribbon("M0 310 C28 392 104 414 190 366 C276 318 352 318 392 402", flat(70), {0: .86, 1: 1.1, 2: .86}), 80, 80, fg)
    star = union(*[bar((0, 0), (0, 168), 60*wt).transform(c, sn, -sn, c, 0, 0)
                   for c, sn in ((1, 0), (.309, .951), (-.809, .588), (-.809, -.588), (.309, -.951))])
    put('*', move(star, 0, 556), 46, 46, fg)
    hash_ = union(bar((132, 0), (196, CAP), h*.9, 'h', 'h'), bar((352, 0), (416, CAP), h*.9, 'h', 'h'),
                  rect(34, 432, 548, 432+h*.86), rect(0, 204, 514, 204+h*.86))
    put('#', hash_, 36, 36, fg)
    ring = lambda x, y: ribbon(oval_d(x+34, y+31, x+252-34, y+336-31, .57), Style(70*wt, 62*wt, soft=lc.soft))
    put('%', [ring(0, 375), ring(430, -11), bar((148, -8), (534, 708), h*.86, 'h', 'h')], 44, 44, fg)
    put('°', ribbon(oval_d(30, 430+30, 270-30, CAP+OV-30, .57), flat(60)), 44, 44, fg)
    at = union(ribbon(f"M624 446 L624 172 C624 112 652 84 698 84 C776 84 826 176 826 304 C826 508 668 646 446 646 "
                      f"C206 646 54 486 54 246 C54 4 214 -150 456 -150 C548 -150 628 -130 700 -90",
                      Style(66*wt, 58*wt, soft=lc.soft), {7: 1.05}),
               ribbon(oval_d(286+33, 78+29, 660-33, 452-29, .58), Style(70*wt, 60*wt, soft=lc.soft)))
    put('@', at, 50, 50, fg)
    s_d = (f"M478 574 C430 640 356 {top} 270 {top} C150 {top} 72 612 72 520 C72 440 132 402 256 364 "
           f"C392 322 468 284 468 182 C468 88 388 {bot} 266 {bot} C166 {bot} 92 62 36 136")
    dollar = ribbon(xform(s_d, .9, .9, 0, 35), fg, {0: 1.05, 2: .96, 3: 1.2, 4: .96, 6: 1.05})
    dollar = minus(minus(dollar, rect(424, CAP/2, 900, 900)), rect(-200, -100, 40, CAP/2))
    put('$', [dollar, rect(243-h*.42, 600, 243+h*.42, 770), rect(243-h*.42, -70, 243+h*.42, 100)], 60, 60, fg)
    c_d = (f"M452 560 C414 630 356 {top} 286 {top} C166 {top} {96+fg.thick/2} 546 {96+fg.thick/2} {CAP/2} "
           f"C{96+fg.thick/2} 154 166 {bot} 288 {bot} C360 {bot} 420 66 462 142")
    euro = minus(minus(ribbon(c_d, fg, {0: 1.05, 4: 1.05}), rect(446, CAP/2, 900, 900)), rect(454, -100, 900, CAP/2))
    put('€', [euro, rect(20, 400, 372, 400+h*.8), rect(20, 262, 340, 262+h*.8)], 40, 50, fg)
    pound = ribbon(f"M428 588 C390 646 340 {top} 276 {top} C186 {top} 134 616 134 524 L134 210 C134 128 106 70 44 38",
                   fg, {0: 1.05, 4: .9})
    put('£', [minus(pound, rect(414, 500, 900, 900)), rect(28, 0, 450, h), rect(40, 318, 350, 318+h*.86)], 50, 50, fg)
    yw = 500
    put('¥', [bar((30, CAP), (yw/2, 330), fg.thick-2, 'h', 'perp'), bar((yw-30, CAP), (yw/2, 330), fg.thin+6, 'h', 'perp'),
              rect(yw/2-fg.thick/2, 0, yw/2+fg.thick/2, 350), rect(60, 300, yw-60, 300+h*.78), rect(60, 160, yw-60, 160+h*.78)],
        36, 36, fg)
    width, c = sh.glyphs['c']
    x0, _, x1, _ = c.bounds
    put('¢', [c, rect((x0+x1)/2+4-h*.4, -96, (x0+x1)/2+4+h*.4, X+96)], 60, 50)
    mh = h*1.0
    put('−', rect(0, 350-mh/2, 424, 350+mh/2), 74, 74, fg)
    put('×', [bar((36, 174), (388, 526), mh), bar((36, 526), (388, 174), mh)], 92, 92, fg)
    d = oval(212-50*wt**.6, 0, 212+50*wt**.6, 100*wt**.6, .62)
    put('÷', [rect(0, 350-mh/2, 424, 350+mh/2), move(d, 0, 500), move(d, 0, 100)], 74, 74, fg)
    put('±', [rect(0, 420-mh/2, 424, 420+mh/2), rect(212-mh/2, 230, 212+mh/2, 610), rect(0, 60, 424, 60+mh)], 74, 74, fg)
    put('`', soften(move(sh_grave(wt, lc), 60, X+64), lc), 80, 80)


def sh_grave(wt, lc):
    return flip_x(ribbon("M-36 6 L52 128", Style(80*wt, 80*wt, soft=lc.soft), {0: .6, 1: 1.0}), 0)


# ---------------------------------------------------------------- accented and special letters

MARKS = {0x300: 'grave', 0x301: 'acute', 0x302: 'circumflex', 0x303: 'tilde', 0x304: 'macron', 0x306: 'breve',
         0x307: 'dot', 0x308: 'dieresis', 0x30A: 'ring', 0x30B: 'hungar', 0x30C: 'caron', 0x327: 'cedilla',
         0x328: 'ogonek', 0x326: 'commabelow'}
BELOW = {'cedilla', 'ogonek', 'commabelow'}
RANGES = [(0xC0, 0x17F), (0x218, 0x21B), (0x1E80, 0x1E85), (0x1EF2, 0x1EF3)]


def extended(sh):
    import unicodedata
    lc, uc = sh.lc, sh.uc
    s, h, S = lc.thick, lc.thin, uc.thick
    wt = sh.weight
    flat = lambda w: Style(w*wt, w*wt, soft=lc.soft)
    g = sh.glyphs

    acute = ribbon("M-36 6 L52 128", flat(80), {0: .6, 1: 1.0})
    small_acute = ribbon("M-30 6 L44 128", flat(70), {0: .6, 1: 1.0})
    below = ribbon("M10 -62 C12 -102 -4 -140 -40 -178", flat(72), {0: 1.0, 1: .45})
    mark = dict(
        acute=acute, grave=flip_x(acute, 0),
        circumflex=polyline([(-108, 8), (0, 122), (108, 8)], 58*wt),
        caron=polyline([(-108, 126), (0, 12), (108, 126)], 58*wt),
        tilde=ribbon("M-146 26 C-122 96 -66 112 -8 74 C46 38 102 36 146 112", flat(62), {0: .82, 1: 1.12, 2: .82}),
        dieresis=union(oval(-146, 14, -54, 106, .62), oval(54, 14, 146, 106, .62)),
        dot=oval(-50, 12, 50, 112, .62),
        macron=rect(-118, 36, 118, 36+62*wt),
        breve=ribbon("M-110 128 C-110 56 -62 22 0 22 C62 22 110 56 110 128", flat(56), {0: .8, 1: 1.1, 2: .8}),
        ring=ribbon(oval_d(-70+26, 6+26, 70-26, 146-26, .57), flat(52)),
        hungar=union(move(small_acute, -62), move(small_acute, 66)),
        cedilla=union(bar((2, 14), (-14, -64), 40*wt),
                      ribbon("M-34 -64 C28 -58 62 -84 62 -122 C62 -170 2 -190 -62 -164", flat(52), {2: .9})),
        ogonek=ribbon("M-4 14 C-58 -22 -94 -62 -94 -110 C-94 -160 -46 -184 16 -164", flat(58), {0: 1.1, 2: .9}),
        commabelow=below,
    )
    turned = rotate180(below, 0, -120)                 # for g-cedilla
    apostrophe = poly((0, 0), (70*wt, 0), (46*wt, -176), (12*wt, -176))

    # Where a mark sits on its base, measured from the base's ink box.
    def anchor(base, kind, x0, x1):
        mid = (x0+x1)/2
        if kind == 'ogonek':
            return {'a': x1-34, 'e': mid+64, 'u': x1-30, 'A': x1-52, 'E': x1-70, 'U': mid+30}.get(base, mid)
        if kind in BELOW:
            return {'k': mid+10, 'K': mid+10, 'r': x0+s/2, 'l': x0+s/2, 't': x0+150, 'T': mid,
                    'L': mid+10, 'R': mid+6, 's': mid, 'S': mid}.get(base, mid)
        return {'a': mid+8, 'L': x0+S/2+26, 'l': x0+s/2, 'J': x1-S/2, 'h': x0+s/2, 'ȷ': x1-s/2,
                'r': mid-12, 'd': mid, 't': x0+150, 'g': mid-28, 'c': mid+10, 'C': mid+22, 'G': mid+16}.get(base, mid)

    def compose(ch, base, kind):
        if base in 'ij' and kind not in BELOW:
            base = 'ı' if base == 'i' else 'ȷ'
        if base not in g or kind not in mark:
            return
        width, path = g[base]
        x0, _, x1, y1 = path.bounds
        shape = mark[kind]
        if kind == 'caron' and base in 'dtlL':
            lift = ASC if base in 'dl' else CAP if base == 'L' else 690
            x = {'d': x1+22, 'l': x1+22, 'L': x0+S+34, 't': x0+222}[base]
            g[ch] = (width + (0 if base in 'tL' else 62), union(path, soften(move(apostrophe, x, lift), lc)))
            return
        if kind == 'cedilla' and base in 'gkKlLnNrRG':
            kind, shape = 'commabelow', below
            if base == 'g':
                g[ch] = (width, union(path, soften(move(turned, anchor('g', 'acute', x0, x1), X+312), lc)))
                return
        x = anchor(base, kind, x0, x1)
        if kind in BELOW:
            placed = move(shape, x, 0)
        elif y1 <= X+OV+12:
            placed = move(shape, x, X+62)
        else:
            flatter = shape.transform(1, 0, 0, .86, 0, 0)
            placed = move(flatter, x, (CAP if base.isupper() else ASC)+38)
        g[ch] = (width, union(path, soften(placed, lc)))
        sh.groups[ch] = base if base not in 'ıȷ' else {'ı': 'i', 'ȷ': 'j'}[base]

    for first, last in RANGES:
        for code in range(first, last+1):
            parts = unicodedata.decomposition(chr(code)).split()
            if len(parts) == 2 and not parts[0].startswith('<') and int(parts[1], 16) in MARKS:
                compose(chr(code), chr(int(parts[0], 16)), MARKS[int(parts[1], 16)])

    # Letters that are their own drawings.
    put = sh.put
    width, o = g['o']
    ob = o.bounds
    put('ø', [o, bar((ob[0]+34, -34), (ob[2]-34, X+34), h*.78, 'h', 'h')], 40, 40)
    width, O = g['O']
    Ob = O.bounds
    put('Ø', [O, bar((Ob[0]+40, -30), (Ob[2]-40, CAP+30), uc.thin*.8, 'h', 'h')], 50, 50, uc)
    _, e = g['e']
    eb = e.bounds
    put('œ', [o, move(e, ob[2]-eb[0]-s*.9)], 40, 38)
    _, a = g['a']
    ab = a.bounds
    put('æ', [a, move(e, ab[2]-eb[0]-s*.96)], 44, 38)
    _, E = g['E']
    Eb = E.bounds
    put('Œ', [O, move(E, Ob[2]-Eb[0]-S*.9)], 50, 34, uc)
    ae = [keep(bar((40, 0), (392, CAP+8), uc.thin+6, 'h', 'h'), y1=CAP), rect(160, 196, 420, 196+uc.thin*.9),
          rect(388, 0, 388+S, CAP), rect(340, CAP-uc.thin, 742, CAP), rect(400, 366-uc.thin*.47, 706, 366+uc.thin*.47),
          rect(400, 0, 754, uc.thin)]
    put('Æ', ae, 10, 34, uc)
    top = X+OV-h/2
    put('ß', ribbon(f"M{s/2} 0 L{s/2} 548 C{s/2} 660 108 {ASC+OV-h/2} 206 {ASC+OV-h/2} C296 {ASC+OV-h/2} 354 672 354 606 "
                    f"C354 548 326 516 280 478 C244 448 232 428 232 398 C232 360 262 338 310 306 C382 258 420 220 420 152 "
                    f"C420 74 362 {-OV+h/2} 282 {-OV+h/2} C238 {-OV+h/2} 200 36 168 54", lc, {2: .96, 9: 1.05}), 74, 40)
    bw = 494
    bowl_d = (f"M{s/2+3} {top-150} C{s/2+34} {top-58} 150 {top} 258 {top} C380 {top} {bw-s/2} 406 {bw-s/2} {X/2} "
              f"C{bw-s/2} 114 380 {-OV+h/2} 258 {-OV+h/2} C150 {-OV+h/2} {s/2+34} {-OV+h/2+58} {s/2+3} {-OV+h/2+150}")
    put('þ', [rect(0, DESC, s, ASC), ribbon(bowl_d, lc, {0: .52, 2: 1.02, 4: .52})], 74, 40)
    put('Þ', [rect(0, 0, S, CAP), ribbon(f"M{S/2} 560 L296 560 C430 560 504 500 504 396 C504 292 430 232 296 232 L{S/2} 232",
                                         uc, {2: 1.02})], 88, 30, uc)
    put('ð', [o, ribbon(f"M{ob[2]-ob[0]-s/2} 290 C{ob[2]-ob[0]-s/2} 480 350 630 170 726", lc, {0: 1.0, 1: .8}),
              bar((176, 596), (396, 694), h*.74)], 40, 40)
    for ch, base, x0, x1, y, style in [('đ', 'd', 250, 540, 612, lc), ('ħ', 'h', -52, 250, 612, lc),
                                       ('Đ', 'D', -40, 300, 366-uc.thin*.44, uc), ('Ð', 'D', -40, 300, 366-uc.thin*.44, uc),
                                       ('ŧ', 't', 60, 300, 250, lc), ('Ŧ', 'T', 120, 416, 330, uc), ('Ħ', 'H', -40, 600, 520, uc)]:
        width, path = g[base]
        bx = path.bounds[0]
        g[ch] = (width, union(path, soften(rect(bx+x0, y, bx+x1, y+style.thin*.8), style)))
    for ch, base, a, b, style in [('ł', 'l', (-62, 286), (178, 446), lc), ('Ł', 'L', (-62, 262), (236, 444), uc)]:
        width, path = g[base]
        bx = path.bounds[0]
        shifted = move(path, 40)
        g[ch] = (width+40, union(shifted, soften(bar((bx+40+a[0], a[1]), (bx+40+b[0], b[1]), style.thin*.86), style)))
