"""Automatic pair kerning from the drawn outlines.

Each glyph gets a left and right edge profile. A pair is kerned so that its
weighted average gap matches the straight-to-straight rhythm of "nn" / "HH".
"""
from __future__ import annotations

import numpy as np

from pen import _contours, _cubic, bez

STEP = 8
Y0, Y1 = -240, 960
BANDS = np.arange(Y0, Y1, STEP) + STEP/2
OPEN = 300.0          # a gap wider than this reads as open space
POWER = -2.0          # weight nearer ink more strongly


def profile(path, advance):
    """(left gap, right gap) per band; inf where the glyph has no ink."""
    left = np.full(len(BANDS), np.inf)
    right = np.full(len(BANDS), np.inf)
    for contour in _contours(path):
        pts = np.concatenate([bez(_cubic(s), np.linspace(0, 1, 13))[:-1] for s in contour])
        a, b = pts, np.roll(pts, -1, axis=0)
        for i, y in enumerate(BANDS):
            lo, hi = np.minimum(a[:, 1], b[:, 1]), np.maximum(a[:, 1], b[:, 1])
            hit = (lo <= y) & (hi > y)
            if not hit.any():
                continue
            t = (y - a[hit, 1]) / (b[hit, 1] - a[hit, 1])
            xs = a[hit, 0] + t*(b[hit, 0] - a[hit, 0])
            left[i] = min(left[i], xs.min())
            right[i] = min(right[i], advance - xs.max())
    # Nearby heights count too, so a diagonal cannot slide into a neighbour.
    for arr in (left, right):
        src = arr.copy()
        for shift in (-3, -2, -1, 1, 2, 3):
            moved = np.roll(src, shift) + abs(shift)*STEP*.6
            if shift > 0:
                moved[:shift] = np.inf
            else:
                moved[shift:] = np.inf
            np.minimum(arr, moved, out=arr)
    return left, right


def measure(gap, k):
    g = np.clip(gap + k, 4, OPEN)
    return np.mean(g**POWER)**(1/POWER)


def pair_kern(right_of_a, left_of_b, target):
    both = np.isfinite(right_of_a) & np.isfinite(left_of_b)
    if both.sum() < 3:
        return 0
    gap = right_of_a[both] + left_of_b[both]
    lo, hi = -260.0, 120.0
    for _ in range(24):
        mid = (lo+hi)/2
        if measure(gap, mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


OVERHANG = 'TVWYFPKfrſ“”‘’\'"'


def kerning(glyphs, groups, skip='0123456789 \u00a0+=/&?!·#$%*@<>^_|\\~`°€£¥¢−×÷±•…¤¦§¨©ª¬®¯²³´¶¸¹º¼½¾', damp=.5, least=12,
            tightest=-76, loosest=32, clear=26):
    """-> (class pairs {(a, b): value} on base glyphs, exceptions {(a, composite): value})."""
    prof = {c: profile(p, w) for c, (w, p) in glyphs.items() if c not in skip}
    targets = {}
    for key, ref in (('lc', 'n'), ('uc', 'H')):
        gap = prof[ref][1] + prof[ref][0]
        targets[key] = measure(gap[np.isfinite(gap)], 0)

    def value(a, b):
        ra, lb = prof[a][1], prof[b][0]
        raw = pair_kern(ra, lb, targets['uc' if a.isupper() and b.isupper() else 'lc'])
        v = max(tightest, min(loosest, raw*damp))
        both = np.isfinite(ra) & np.isfinite(lb)
        if both.any():
            v = max(v, clear - float((ra[both] + lb[both]).min()))
        return int(round(v))

    bases = [c for c in prof if c not in groups]
    pairs = {}
    for a in bases:
        for b in bases:
            v = value(a, b)
            if abs(v) >= least:
                pairs[(a, b)] = v
    # An accent can meet an overhanging neighbour that its bare letter clears.
    exceptions = {}
    for a in OVERHANG:
        if a not in prof:
            continue
        for b, base in groups.items():
            if b in prof and base.islower():
                v = value(a, b)
                if abs(v - pairs.get((a, base), 0)) >= 8:
                    exceptions[(a, b)] = v
    # Any pair with an accented letter must also keep clear ink.
    def base(c):
        return groups.get(c, c)

    for a in prof:
        for b in prof:
            if (a in groups or b in groups) and (a, b) not in exceptions:
                ra, lb = prof[a][1], prof[b][0]
                both = np.isfinite(ra) & np.isfinite(lb)
                if not both.any():
                    continue
                current = pairs.get((base(a), base(b)), 0)
                need = int(np.ceil(clear - float((ra[both] + lb[both]).min())))
                if current < need:
                    exceptions[(a, b)] = need
    return pairs, exceptions
