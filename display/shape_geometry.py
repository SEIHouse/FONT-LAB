"""Curve-preserving outline utilities in font units (no cut or glyph exceptions)."""
import math

import pathops


def contours(path):
    """Return closed contours as [start, verb, controls..., end] segments."""
    result = []
    for contour in path.contours:
        segments = []
        first = current = None
        for verb, points in contour.segments:
            if verb == 'moveTo':
                first = current = points[0]
            elif verb in ('lineTo', 'qCurveTo', 'curveTo'):
                segments.append([current, verb, *points])
                current = points[-1]
            elif verb == 'closePath' and current != first:
                segments.append([current, 'lineTo', first])
        if segments:
            result.append(segments)
    return result


def from_contours(items):
    """Write native line/quadratic/cubic segments without flattening curves."""
    result = pathops.Path()
    pen = result.getPen()
    for segments in items:
        if not segments:
            continue
        pen.moveTo(segments[0][0])
        for segment in segments:
            getattr(pen, segment[1])(*segment[2:])
        pen.closePath()
    return result


def length(segment):
    """Conservative curve length from its control polygon."""
    points = [segment[0], *segment[2:]]
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def tangent(segment, at_end=False):
    """Find a nonzero endpoint tangent, including repeated cubic controls."""
    points = [segment[0], *segment[2:]]
    if at_end:
        points.reverse()
    anchor = points[0]
    for point in points[1:]:
        delta = (point[0] - anchor[0], point[1] - anchor[1])
        if math.hypot(*delta) > 1e-7:
            return (-delta[0], -delta[1]) if at_end else delta
    return (0, 0)


def turn(before, after):
    """Signed tangent turn at a segment boundary, in degrees."""
    a, b = tangent(before, True), tangent(after)
    return math.degrees(math.atan2(a[0]*b[1] - a[1]*b[0],
                                  a[0]*b[0] + a[1]*b[1]))


def sample(segment, t):
    """Evaluate a native Bezier with de Casteljau interpolation."""
    points = [segment[0], *segment[2:]]
    while len(points) > 1:
        points = [(a[0]*(1-t) + b[0]*t, a[1]*(1-t) + b[1]*t)
                  for a, b in zip(points, points[1:])]
    return points[0]


def chord_turn(before, after, distance):
    """Measure a corner at a visible distance, ignoring subunit control noise."""
    end = before[-1]
    a = sample(before, max(0, 1-distance/max(length(before), 1e-7)))
    b = sample(after, min(1, distance/max(length(after), 1e-7)))
    incoming = (end[0]-a[0], end[1]-a[1])
    outgoing = (b[0]-end[0], b[1]-end[1])
    return math.degrees(math.atan2(incoming[0]*outgoing[1] - incoming[1]*outgoing[0],
                                  incoming[0]*outgoing[0] + incoming[1]*outgoing[1]))
