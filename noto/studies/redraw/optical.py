"""Optical spacing pass, applied on top of the automatic outline kerning in spacing.py.

The automatic system balances the *measured* gap of each pair. The eye is not a ruler,
so a few situations read differently in sentences than they measure. Each rule below
came from reviewing real words (To, Te, Wa, Yo, italic ff, fi, gj ...) at every weight
and names what the eye sees. Rules are relative to the weight being built (stem, the
automatic V value), so Light, Regular, Medium, Bold and their italics stay consistent.

Reviewed and left unchanged: T and Y with lowercase (To, Te, Ta, Tr, Ty, Yo, Ya, Ye)
already read evenly; ff keeps its shared crossbar rhythm.
"""
from __future__ import annotations

import numpy as np

# 1. The eye reads a word's rhythm above the baseline. Between two letters,
#    descenders that tuck toward each other (g j, j j, q j) only need clearance,
#    and a smaller one, because contact below the baseline does not clot the
#    word's texture. This only ever tightens: a pair whose descenders are open
#    (p q, y y) keeps its measured value. Punctuation keeps the full measure.
DESCENDER_CLEAR = 12
DESCENDER_ZONE = -40      # below the overshoots and the profile's neighbour blur

# 2. W is lighter and more open than V, so with the same neighbour it looks
#    looser at the same measured gap. W follows at least this share of V's kern.
W_FOLLOWS_V = .75

# 3. An f terminal crowds an i dot, an accent, an ascender or a quote that sits
#    under it (fi, fí, fl, fb, f”), most visibly in italic. Above the x-height
#    the f gets about one stem of air, opened by at most AIR_LIMIT stems.
AIR_STEMS = 1.0
AIR_LIMIT = .16
TERMINALS = 'fſ'          # letters whose terminal overhangs the next letter
SHARED_BAR = 'fſ'         # followers that share the f crossbar rhythm (off, buffet)


def letters_only(a, b):
    return a.isalpha() and b.isalpha()


def reading_zone(bands, a, b, right_of_a, left_of_b):
    """A letter pair's profiles without the descender zone, when both letters reach into it."""
    if not letters_only(a, b):
        return right_of_a, left_of_b
    above = bands >= DESCENDER_ZONE
    both = np.isfinite(right_of_a) & np.isfinite(left_of_b)
    if (both & ~above).any() and (both & above).sum() >= 3:
        return np.where(above, right_of_a, np.inf), np.where(above, left_of_b, np.inf)
    return right_of_a, left_of_b


def clearance(bands, a, b, right_of_a, left_of_b, clear):
    """Least kern that keeps clear ink; between letters, descenders need less."""
    gap = right_of_a + left_of_b
    need = -np.inf
    below = DESCENDER_CLEAR if letters_only(a, b) else clear
    for zone, floor in ((bands >= DESCENDER_ZONE, clear), (bands < DESCENDER_ZONE, below)):
        sel = zone & np.isfinite(gap)
        if sel.any():
            need = max(need, floor - float(gap[sel].min()))
    return need


def stem_width(bands, profile, advance, x_height):
    """Stem of the weight being built, measured across dotless ı at half the x-height."""
    left, right = profile
    i = int(np.argmin(abs(bands - x_height/2)))
    return advance - left[i] - right[i]


def terminal_air(bands, a, b, right_of_a, left_of_b, x_height, stem):
    """Least kern that gives an f terminal its air above the x-height (or -inf)."""
    if a not in TERMINALS or b in SHARED_BAR:
        return -np.inf
    gap = right_of_a + left_of_b
    sel = (bands > x_height) & np.isfinite(gap)
    if not sel.any():
        return -np.inf
    need = AIR_STEMS*stem - float(gap[sel].min())
    return min(need, AIR_LIMIT*stem) if need > 0 else -np.inf


def w_follows_v(a, b, value, v_value):
    """W with a lowercase neighbour kerns at least W_FOLLOWS_V of V's value."""
    if a == 'W' and b.islower() and v_value < 0:
        return min(value, W_FOLLOWS_V*v_value)
    return value
