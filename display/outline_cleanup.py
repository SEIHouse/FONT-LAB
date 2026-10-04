"""Remove stroke/Boolean debris while retaining the cut's native Bezier curves."""
from display.shape_geometry import contours, from_contours, length, chord_turn

# At 400px/2000 UPM: .6px point tolerance, 1px² debris, 8px needle shoulders.
# These are construction tolerances, shared by every glyph and cut.
POINT_EPSILON = 3.0
MIN_AREA = 25.0
SPIKE_SHOULDER = 40.0


def split(segment, t):
    """Split a native Bezier without approximating the remaining curve."""
    level = [segment[0], *segment[2:]]
    left, right = [level[0]], [level[-1]]
    while len(level) > 1:
        level = [(a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t)
                 for a, b in zip(level, level[1:])]
        left.append(level[0])
        right.append(level[-1])
    right.reverse()
    return ([left[0], segment[1], *left[1:]],
            [right[0], segment[1], *right[1:]])


def move_end(segment, point):
    """Move an endpoint and its adjacent control together to preserve its tangent."""
    delta = (point[0]-segment[-1][0], point[1]-segment[-1][1])
    if len(segment) > 3:
        segment[-2] = (segment[-2][0]+delta[0], segment[-2][1]+delta[1])
    segment[-1] = point


def move_start(segment, point):
    """Move a start and its first control together to preserve its tangent."""
    delta = (point[0]-segment[0][0], point[1]-segment[0][1])
    if len(segment) > 3:
        segment[2] = (segment[2][0]+delta[0], segment[2][1]+delta[1])
    segment[0] = point


def tidy(segments):
    """Collapse tiny edges and bevel short needle excursions, never full-size tips."""
    segments = [list(segment) for segment in segments]
    # Every edit either removes an edge or removes one needle corner. Revisit
    # neighbors because Boolean operations often leave several tiny edges in a row.
    for _ in range(len(segments)*3):
        changed = False
        for i, before in enumerate(segments):
            after = segments[(i+1) % len(segments)]
            if length(before) < POINT_EPSILON:
                if len(segments) <= 2:
                    return []
                point = ((before[0][0]+before[-1][0])/2,
                         (before[0][1]+before[-1][1])/2)
                move_end(segments[i-1], point)
                move_start(after, point)
                segments.pop(i)
                changed = True
                break
            short = min(length(before), length(after))
            angle = chord_turn(before, after, 10)
            previous = chord_turn(segments[i-1], before, 10)
            following = chord_turn(after, segments[(i+2) % len(segments)], 10)
            # A small out-and-back triangle on an otherwise continuous wall is
            # also debris, even when its tip is wider than a needle. Opposing
            # root turns distinguish it from a deliberate letter/symbol corner.
            if (60 < abs(angle) <= 150 and short < 80 and
                    max(length(before), length(after)) < 120 and
                    angle*previous < 0 and angle*following < 0 and
                    abs(previous) > 10 and abs(following) > 10 and
                    abs(previous+angle+following) < 15):
                replacement = [[before[0], 'lineTo', after[-1]]]
                segments = replacement + segments[i+2:] + segments[:i] if i < len(segments)-1 else replacement + segments[1:i]
                changed = True
                break
            if short < SPIKE_SHOULDER and abs(chord_turn(before, after, 10)) > 150:
                # Cut at the root of the shorter shoulder. Leave exact Bezier
                # subdivisions on both sides and bridge them with a clean bevel.
                a, _ = split(before, max(0, 1-short/length(before)))
                _, b = split(after, min(1, short/length(after)))
                replacement = []
                if length(a) >= POINT_EPSILON:
                    replacement.append(a)
                replacement.append([a[-1], 'lineTo', b[0]])
                if length(b) >= POINT_EPSILON:
                    replacement.append(b)
                # Rotate so a corner across the contour seam is handled identically.
                segments = replacement + segments[i+2:] + segments[:i] if i < len(segments)-1 else replacement + segments[1:i]
                changed = True
                break
        if not changed or not segments:
            break
    return segments


def cleanup(path):
    """Resolve overlaps, remove micro-contours and clean points after stroking."""
    if not path:
        return path
    result = path.transform()
    result.simplify(fix_winding=True)
    result.convertConicsToQuads(.02)
    kept = []
    for contour in result.contours:
        if abs(contour.area) < MIN_AREA:
            continue
        for segments in contours(contour):
            cleaned = tidy(segments)
            if cleaned:
                kept.append(cleaned)
    result = from_contours(kept)
    result.simplify(fix_winding=True)
    result.convertConicsToQuads(.02)
    return result
