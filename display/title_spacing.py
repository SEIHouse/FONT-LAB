"""Display-size optical spacing and the compiled font's Lab spacing contract.

All distances here use the builder's source units (1,000 per em). Reader never
calls this policy. The Lab export is read back from final GPOS/hmtx tables, so
class kerning, zero exceptions and rounded advances have one authoritative owner.
"""
import hashlib
import json
import math
from pathlib import Path

from fontTools.ttLib import TTFont

POLICIES = {
    'soft': dict(cap_strength=.94, body_strength=.78, depth=200, clearance=18),
    'edge': dict(cap_strength=.90, body_strength=.76, depth=190, clearance=20),
    'ink': dict(cap_strength=.92, body_strength=.80, depth=210, clearance=12),
    'wide': dict(cap_strength=.84, body_strength=.72, depth=230, clearance=24),
}
SPACING_DEFAULTS = dict(weight=135, contrast=1, penAngle=0, slant=0,
    corners='soft', ends='round', joins='round', lowercaseRoundness=.5,
    capitalRoundness=210, letterWidth=1, xHeight=520, wordSpace=250,
    spaceBetweenAllLetters=0, overshoot=True, uFoot=False,
    uprightStraightness=1, ascender=700, letterSpace={}, pairSpace={})


def spacing_settings(settings):
    """Names, notes and save timestamps do not change a cut's spacing identity."""
    return {key: settings.get(key, value) for key, value in SPACING_DEFAULTS.items()}


def policy_for(settings):
    """Select the cut's optical policy from its geometry, also for renamed drafts."""
    if settings.get('penAngle', 0) or settings['contrast'] >= 2:
        return 'ink'
    if settings.get('ends') == 'flat' and settings.get('corners') == 'cut':
        return 'edge'
    if settings.get('letterWidth', 1) >= 1.2 and settings['weight'] < 100:
        return 'wide'
    return 'soft'


class DisplaySpacing:
    """Measure cap-height titles and mixed-case words against this cut's H/n rhythm."""
    def __init__(self, builder, paths, advances, cmap, chars):
        """Sample expanded outlines in cap/body bands and establish this cut's H/n targets."""
        self.scale = scale = 2
        self.policy_name = policy_for(builder.settings)
        self.policy = policy = POLICIES[self.policy_name]
        self.depth = policy['depth'] * builder.WS * scale
        self.clearance = policy['clearance'] * scale
        self.profiles = {}
        zones = dict(cap=range(28*scale, 673*scale, 5*scale),
                     body=range(round(builder.XHT*.06)*scale,
                                round(builder.XHT*.95)*scale, 5*scale),
                     full=range(0, 701*scale, 4*scale))
        for ch in dict.fromkeys(chars):
            name = cmap.get(ord(ch))
            if name is None or paths.get(name) is None:
                continue
            bands = {zone: builder.profiles(paths[name], ys) for zone, ys in zones.items()}
            left, right = bands['full']
            if not any(value is not None for value in left):
                continue
            self.profiles[ch] = dict(advance=advances[name], bands=bands,
                left=min(value for value in left if value is not None),
                right=max(value for value in right if value is not None))
        self.targets = {zone: self.gap(ch, ch, zone)[0]
                        for zone, ch in (('cap', 'H'), ('body', 'n'))}
        self.capital_space = max(6, min(36, round(self.targets['cap']/scale*.14)))

    def gap(self, a, b, zone):
        """Return optical whitespace and the closest real ink, before kerning."""
        first, second = self.profiles[a], self.profiles[b]
        depth = self.depth if zone == 'cap' else self.depth*.48
        gaps = [first['advance'] - max(r if r is not None else -1e9, first['right']-depth)
                + min(l if l is not None else 1e9, second['left']+depth)
                for r, l in zip(first['bands'][zone][1], second['bands'][zone][0])]
        closest = [first['advance']-r+l for r, l in
                   zip(first['bands']['full'][1], second['bands']['full'][0])
                   if r is not None and l is not None]
        return sum(gaps)/len(gaps), min(closest) if closest else math.inf

    def adjustment(self, a, b, zone):
        """Return a source-unit pair correction bounded by optical depth and ink room."""
        gap, closest = self.gap(a, b, zone)
        strength = self.policy['cap_strength' if zone == 'cap' else 'body_strength']
        value = strength * (self.targets[zone]-gap)
        lower = -320*self.scale if zone == 'cap' else -110*self.scale
        value = max(lower, min(65*self.scale, value))
        value = max(value, self.clearance-closest)
        return math.ceil(value/self.scale) if value == self.clearance-closest else round(value/self.scale)

    def title_pairs(self):
        """A dedicated full capital-height pass, inherited by accented capital classes."""
        capitals = [ch for ch in self.profiles if ch.isupper()]
        return {a+b: self.adjustment(a, b, 'cap') for a in capitals for b in capitals}

    def auto_pairs(self):
        """Display-size body/mixed-case corrections with smaller ink cushions than Reader."""
        result = {}
        letters = {ch for ch in self.profiles if ch.isalpha()}
        for a in self.profiles:
            for b in self.profiles:
                if a.isupper() and b.isupper():
                    continue  # The title pass owns these pairs.
                if a in letters and b in letters and 'j' not in (a, b):
                    result[a+b] = self.adjustment(a, b, 'body')
                elif ((a in letters and b in '.,') or
                      (a in '\'"‘’“”(' and b in letters) or
                      (a in letters and b in '\'"‘’“”)')):
                    zone = 'cap' if a.isupper() or b.isupper() else 'body'
                    result[a+b] = self.adjustment(a, b, zone)
        return result


def default_lookups(font, feature):
    """Use DFLT's feature plan; language-specific Hungarian spacing stays separate."""
    table = font['GPOS'].table
    script = next(record.Script for record in table.ScriptList.ScriptRecord
                  if record.ScriptTag == 'DFLT')
    indices = []
    for index in script.DefaultLangSys.FeatureIndex:
        record = table.FeatureList.FeatureRecord[index]
        if record.FeatureTag == feature:
            indices.extend(record.Feature.LookupListIndex)
    return [table.LookupList.Lookup[index] for index in dict.fromkeys(indices)]


def compiled_kerning(font):
    """Keep compiled class lookups compact; the Lab follows their matching order."""
    def value(record):
        """Read the first glyph's advance-only adjustment in source units."""
        first, other = record.Value1, record.Value2
        if other or (first and any(getattr(first, field, 0) for field in
                                  ('XPlacement', 'YPlacement', 'YAdvance'))):
            raise ValueError('Unsupported non-advance title kerning')
        return (getattr(first, 'XAdvance', 0) if first else 0)/2

    result = []
    for lookup in default_lookups(font, 'kern'):
        if lookup.LookupType == 9:
            if any(subtable.ExtensionLookupType != 2 for subtable in lookup.SubTable):
                raise ValueError('Lab export requires pair-positioning kerning')
            source_tables = [subtable.ExtSubTable for subtable in lookup.SubTable]
        elif lookup.LookupType == 2:
            source_tables = lookup.SubTable
        else:
            raise ValueError('Lab export requires pair-positioning kerning')
        subtables = []
        for subtable in source_tables:
            if subtable.ValueFormat1 & ~4 or subtable.ValueFormat2:
                raise ValueError('Unsupported non-advance title kerning')
            if subtable.Format == 1:
                pairs = {first: {record.SecondGlyph: value(record)
                         for record in subtable.PairSet[i].PairValueRecord}
                         for i, first in enumerate(subtable.Coverage.glyphs)}
                subtables.append(dict(format=1, pairs=pairs))
            elif subtable.Format == 2:
                subtables.append(dict(format=2, coverage=subtable.Coverage.glyphs,
                    left=subtable.ClassDef1.classDefs, right=subtable.ClassDef2.classDefs,
                    values=[[value(record) for record in row.Class2Record]
                            for row in subtable.Class1Record]))
            else:
                raise ValueError('Unsupported pair-positioning format')
        result.append(subtables)
    return result


def export_spacing(font_path, settings, origins, policy):
    """Publish final rounded metrics and resolved GPOS values for the live SVG Lab."""
    font_path = Path(font_path)
    with TTFont(font_path) as font:
        cmap = font.getBestCmap()
        characters = {chr(code): name for code, name in cmap.items()}
        characters.update({name: name for name in font.getGlyphOrder() if '.' in name})
        capitals = sorted({name for code, name in cmap.items() if chr(code).isupper()})
        return dict(schema=1, settings=spacing_settings(settings),
            otf_sha256=hashlib.sha256(font_path.read_bytes()).hexdigest(),
            policy=policy.policy_name, capitalSpace=policy.capital_space,
            capitals=capitals, glyphs={ch:dict(name=name, advance=font['hmtx'][name][0]/2,
                origin=origins.get(name, 0)) for ch, name in characters.items()},
            kern=compiled_kerning(font))


def write_spacing(font_path, settings, origins, policy, directory):
    """Save the compiled spacing snapshot using the cut builder's asset slug."""
    slug = settings['name'].lower().replace(' ', '-')
    output = Path(directory)/f'spacing_{slug}.json'
    output.write_text(json.dumps(export_spacing(font_path, settings, origins, policy),
                                  ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
