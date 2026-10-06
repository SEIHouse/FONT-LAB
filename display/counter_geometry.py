"""Measure white counters and apertures in the actual exported raster."""
import math


def ink_rows(bitmap, padding=4):
    """Threshold coverage at its midpoint and pad with exterior white pixels."""
    width = bitmap['width'] + 2 * padding
    rows = [0] * padding
    for y in range(bitmap['height']):
        row = 0
        for x, value in enumerate(bitmap['pixels'][y*bitmap['width']:(y+1)*bitmap['width']]):
            if value >= 128:
                row |= 1 << (x + padding)
        rows.append(row)
    return width, rows + [0] * padding


def white_components(width, ink):
    """Label four-connected white runs, including the surrounding exterior.

    Run-length labels avoid a pixel-by-pixel flood fill for every glyph. Each
    result owns its row masks, area and whether it reaches the padded boundary.
    """
    mask = (1 << width) - 1
    parents, runs, exterior = [], [], []

    def root(index):
        """Find a white-run component owner and compress its union path."""
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    previous = []
    for y, row in enumerate(ink):
        bits, current = mask ^ row, []
        while bits:
            start = (bits & -bits).bit_length() - 1
            shifted = bits >> start
            count = ((shifted + 1) & ~shifted).bit_length() - 1
            end = start + count
            index = len(parents)
            parents.append(index)
            runs.append((y, start, end))
            exterior.append(start == 0 or end == width or y in (0, len(ink)-1))
            current.append((start, end, index))
            bits &= ~(((1 << count) - 1) << start)
        j = 0
        for start, end, index in current:
            while j < len(previous) and previous[j][1] <= start:
                j += 1
            k = j
            while k < len(previous) and previous[k][0] < end:
                other = root(previous[k][2])
                owner = root(index)
                if other != owner:
                    parents[other] = owner
                k += 1
        previous = current
    components = {}
    for index, (y, start, end) in enumerate(runs):
        component = components.setdefault(root(index), dict(area=0, exterior=False, rows={}))
        component['area'] += end - start
        component['exterior'] |= exterior[index]
        component['rows'][y] = component['rows'].get(y, 0) | (((1 << (end-start))-1) << start)
    return list(components.values())


def dilate(rows, width, radius):
    """Grow ink by a diamond pixel radius, used only for clearance measurement."""
    mask = (1 << width) - 1
    for _ in range(radius):
        rows = [((row | (row << 1) | (row >> 1)) |
                 (rows[y-1] if y else 0) |
                 (rows[y+1] if y+1 < len(rows) else 0)) & mask
                for y, row in enumerate(rows)]
    return rows


def substantial_counter(component, bitmap, min_area=24):
    """Exclude small enclosed details from the full-letter counter policy."""
    bits = 0
    for row in component['rows'].values():
        bits |= row
    span_x = bits.bit_length() - (bits & -bits).bit_length() + 1
    span_y = max(component['rows']) - min(component['rows']) + 1
    return component['area'] >= min_area and (
        span_x >= bitmap['width']*.2 or span_y >= bitmap['height']*.2)


def hull_rows(width, ink):
    """Rasterize the convex envelope of ink, to locate interior white basins."""
    points = []
    for y, bits in enumerate(ink):
        if bits:
            points.extend((((bits & -bits).bit_length() - .5, y+.5),
                           (bits.bit_length() - .5, y+.5)))
    points = sorted(set(points))
    if len(points) < 3:
        return [0]*len(ink)
    cross = lambda a, b, c: (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    halves = []
    for sequence in (points, reversed(points)):
        half = []
        for point in sequence:
            while len(half) >= 2 and cross(half[-2], half[-1], point) <= 0:
                half.pop()
            half.append(point)
        halves.append(half[:-1])
    hull = halves[0]+halves[1]
    result = []
    for y in range(len(ink)):
        scan, intersections = y+.5, []
        for a, b in zip(hull, hull[1:]+hull[:1]):
            if min(a[1], b[1]) <= scan < max(a[1], b[1]):
                intersections.append(a[0]+(scan-a[1])*(b[0]-a[0])/(b[1]-a[1]))
        if len(intersections) < 2:
            result.append(0)
        else:
            start = max(0, math.ceil(min(intersections)-.5))
            end = min(width, math.floor(max(intersections)-.5)+1)
            result.append(((1 << max(0, end-start))-1) << start)
    return result


def topology_snapshot(bitmap):
    """Capture approved counter counts and interior-white connectivity witnesses.

    Capture is for a reviewed immutable fixture, never an automatic gate update.
    Convex-envelope basins find open letter interiors as well as closed counters.
    Witnesses have at least three pixels of ink clearance and use glyph-space
    pixel coordinates, so changes to a raster's bounding box do not move them.
    """
    padding = 4
    width, ink = ink_rows(bitmap, padding)
    components = white_components(width, ink)
    closed = sum(not c['exterior'] and substantial_counter(c, bitmap) for c in components)
    envelope = hull_rows(width, ink)
    mask = (1 << width)-1
    basins = white_components(width, [bits | (mask ^ hull) for bits, hull in zip(ink, envelope)])
    grown = dilate(ink, width, 3)
    witnesses = []
    for basin in basins:
        candidates = {y: bits & ~grown[y] for y, bits in basin['rows'].items()}
        candidates = {y: bits for y, bits in candidates.items() if bits}
        if not candidates:
            continue
        all_bits = 0
        for bits in basin['rows'].values():
            all_bits |= bits
        cx = ((all_bits & -all_bits).bit_length()-1 + all_bits.bit_length()-1)/2
        cy = (min(basin['rows'])+max(basin['rows']))/2
        points = []
        for y, bits in candidates.items():
            left = bits & ((1 << (int(cx)+1))-1)
            right = bits & ~((1 << (int(cx)+1))-1)
            for x in (left.bit_length()-1 if left else None,
                      (right & -right).bit_length()-1 if right else None):
                if x is not None:
                    points.append(((x-cx)**2+(y-cy)**2, x, y))
        _, x, y = min(points)
        component = next(c for c in components if c['rows'].get(y, 0) & (1 << x))
        if component['exterior']:
            if basin['area'] < max(200, bitmap['width']*bitmap['height']*.02):
                continue
        elif not substantial_counter(component, bitmap):
            continue
        witnesses.append([bitmap.get('left', 0)+x-padding,
                          bitmap.get('top', bitmap['height'])-y+padding,
                          component['exterior']])
    return dict(closed_counters=closed, white_spaces=sorted(witnesses))


def topology_flags(bitmap, expected):
    """Reject filled counters and filled/sealed apertures against approved topology."""
    padding = 4
    width, ink = ink_rows(bitmap, padding)
    components = white_components(width, ink)
    closed = sum(not c['exterior'] and substantial_counter(c, bitmap) for c in components)
    found = []
    if closed != expected['closed_counters']:
        found.append(dict(kind='counter-topology', expected=expected['closed_counters'], actual=closed))
    for x, y, exterior in expected['white_spaces']:
        col = x-bitmap.get('left', 0)+padding
        row = bitmap.get('top', bitmap['height'])-y+padding
        component = next((c for c in components if 0 <= col < width and
                          c['rows'].get(row, 0) & (1 << col)), None)
        if component is None:
            found.append(dict(kind='filled-aperture' if exterior else 'filled-counter', point=[x, y]))
        elif component['exterior'] != exterior:
            found.append(dict(kind='sealed-aperture' if exterior else 'opened-counter', point=[x, y]))
    return found


def counter_flags(bitmap, radius=3, min_area=24, apertures=True):
    """Flag substantial counters with no room and apertures that pinch shut.

    At a 400px em, a three-pixel diamond tests a six-pixel opening. Small marks
    and enclosed details below 24px² or 20% of the glyph's span are excluded.
    Aperture basins must occupy at least 2% of the glyph box and 200px². This
    avoids treating the small spaces in attached hooks as letter counters.
    Tapered counter tips are allowed when the rest of their basin has room.
    """
    if not bitmap['width'] or not bitmap['height']:
        return []
    width, ink = ink_rows(bitmap, radius + 1)
    components = white_components(width, ink)
    grown = dilate(ink, width, radius)
    found = []
    holes = [item for item in components if not item['exterior']]
    for hole in holes:
        if substantial_counter(hole, bitmap, min_area) and not any(bits & ~grown[y] for y, bits in hole['rows'].items()):
            found.append(dict(kind='narrow-counter', area_px2=hole['area'], clearance_px=2*radius))
    if not apertures:
        return found
    exterior = {}
    for item in components:
        if item['exterior']:
            for y, bits in item['rows'].items():
                exterior[y] = exterior.get(y, 0) | bits
    for hole in white_components(width, grown):
        if not hole['exterior'] and hole['area'] >= max(min_area, 200, bitmap['width']*bitmap['height']*.02):
            # A sizeable basin formerly connected to the outside has become
            # enclosed: its entrance is narrower than the clearance threshold.
            if any(bits & exterior.get(y, 0) for y, bits in hole['rows'].items()):
                found.append(dict(kind='narrow-aperture', area_px2=hole['area'], clearance_px=2*radius))
    return found
