"""OpenType sets and outline-derived spacing for opt-in Display letter designs."""

SET_NAMES = {
    'ss01': 'Alternate a and g', 'ss02': 'Alternate R leg',
    'ss03': 'Alternate K and k arms', 'ss04': 'Alternate M and W',
    'ss05': 'Alternate y tail', 'ss06': 'Alternate G spur',
    'ss07': 'Alternate Q tail', 'ss08': 'Alternate 4, 6 and 9',
}


def stylistic_features(designs, gname):
    """Each set selects the opposite of this cut's defaults, including derivatives."""
    lines = []
    for tag, label in SET_NAMES.items():
        lines += [f'feature {tag} {{', f' featureNames {{ name "{label}"; }};']
        for source, spec in designs.items():
            if spec['tag'] != tag:
                continue
            original = gname(source) if len(source) == 1 else source
            alternate = next(name for choice, name in spec['choices'].items() if choice != spec['default'])
            lines.append(f' sub {original} by {alternate};')
        lines.append(f'}} {tag};')
    return '\n'.join(lines)+'\n'


def alternate_kerning(policy, designs, basemap, paths, advances, gname,
                      scale, left_groups, right_groups):
    """Measure alternate outlines and inherit their pair classes through accents/scripts."""
    groups = {}
    for source, spec in designs.items():
        if len(source) != 1 or not source.isalpha():
            continue
        base = basemap.get(source, source)
        if base not in policy.profiles:
            continue
        name = next(name for choice, name in spec['choices'].items() if choice != spec['default'])
        groups.setdefault(base, []).append(name)
    roots = {}
    for base in groups:
        if base not in designs:
            continue
        name = next(name for choice, name in designs[base]['choices'].items() if choice != designs[base]['default'])
        policy.add_profile(name, paths[name], advances[name])
        roots[name] = base
    ordinary = [ch for ch in policy.profiles if len(ch) == 1]
    left_groups.update(ordinary)
    right_groups.update(ordinary)
    classes = [f'@ALT_{gname(base)} = [{" ".join(names)}];' for base, names in sorted(groups.items()) if base in roots.values()]
    lines = []
    for a in [*ordinary, *roots]:
        for b in [*ordinary, *roots]:
            if a not in roots and b not in roots:
                continue
            first, second = roots.get(a, a), roots.get(b, b)
            letters = first.isalpha() and second.isalpha()
            overrides = policy.builder.settings.get('pairSpace', {})
            if letters and 'j' in (first, second) and first+second not in overrides:
                continue  # Keep the default pass's descender exclusion.
            if not letters and not (
                first.isalpha() and second in '.,\'"‘’“”)' or
                first in '\'"‘’“”(' and second.isalpha()):
                continue
            zone = 'cap' if ((first.isupper() and second.isupper()) or
                (not letters and (first.isupper() or second.isupper()))) else 'body'
            value = round(overrides.get(first+second,
                policy.adjustment(a, b, zone))*scale)
            lclass = '@ALT_'+gname(first) if a in roots else '@L_'+gname(first)
            rclass = '@ALT_'+gname(second) if b in roots else '@R_'+gname(second)
            lines.append(f' pos {lclass} {rclass} {value};')
    return lines, classes
