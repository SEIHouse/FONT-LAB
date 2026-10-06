"""Measure white counters and apertures in the actual exported raster."""


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
        bits = 0
        for row in hole['rows'].values():
            bits |= row
        span_x = bits.bit_length() - (bits & -bits).bit_length() + 1
        span_y = max(hole['rows']) - min(hole['rows']) + 1
        substantial = span_x >= bitmap['width']*.2 or span_y >= bitmap['height']*.2
        if substantial and hole['area'] >= min_area and not any(bits & ~grown[y] for y, bits in hole['rows'].items()):
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
