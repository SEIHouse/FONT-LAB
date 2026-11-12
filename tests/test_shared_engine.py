"""Independent regressions for immutable output and inherited feature gates."""
import json
import copy
from pathlib import Path
import shutil
import tempfile
import unittest

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from verify_shared_engine import (FIXTURE, LEGACY_FIXTURE, CURVE_CHANGES, ROOT, audit_features,
                                  reader_flags, legacy_flags)
from verify_display_shapes import (DESIGN, SHARED_DESIGN, SHARED_REFERENCE, design_flags,
                                   validate_design_reference, web_flags,
                                   blank_flags, outline)


class ReaderIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.filename = 'SEIReader-Regular.otf'
        self.fixture['files'] = {self.filename: self.fixture['files'][self.filename]}
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)/self.filename
        shutil.copyfile(ROOT/'fonts'/self.filename, self.path)

    def failures(self):
        return reader_flags(self.path.parent, self.fixture)[0]

    def save(self, font):
        font.save(self.path)
        font.close()

    def test_complete_current_reader_matches_frozen_reference(self):
        self.assertEqual(self.failures(), [])

    def test_curve_refinement_preserves_every_original_positioning_table(self):
        """The 0.40 drawing fixture cannot bless kerning or mark-placement changes."""
        original = json.loads((ROOT/'tests/fixtures/reader-0.39-identity.json').read_text(encoding='utf-8'))
        current = json.loads((ROOT/'tests/fixtures/reader-curves-identity.json').read_text(encoding='utf-8'))
        night = json.loads(CURVE_CHANGES.read_text(encoding='utf-8'))['night_layout_before']
        self.assertTrue(set(original['files']) <= set(current['files']))
        for filename, new in current['files'].items():
            old_tables = night[filename] if 'Night' in filename else original['files'][filename]['tables']
            for tag in ('GPOS', 'GDEF', 'GSUB'):
                self.assertEqual(new['tables'].get(tag), old_tables.get(tag),
                                 f'{filename}/{tag}')

    def test_night_grade_release_only_restamps_the_version_of_every_0_41_delivery(self):
        """Adding Light and Medium Night faces cannot redraw, rehint or respace an existing font."""
        previous = json.loads((ROOT/'tests/fixtures/reader-0.41-identity.json').read_text(encoding='utf-8'))
        current = json.loads((ROOT/'tests/fixtures/reader-0.42-identity.json').read_text(encoding='utf-8'))
        self.assertTrue(set(previous['files']) < set(current['files']))
        self.assertEqual(current['cmap'], previous['cmap'])
        for filename, old in previous['files'].items():
            new = current['files'][filename]
            changed = {tag for tag in set(old['tables']) | set(new['tables'])
                       if old['tables'].get(tag) != new['tables'].get(tag)}
            # The release number lives in the name table, CFF top dictionary and head.fontRevision.
            self.assertEqual(changed, {'CFF ', 'head', 'name'}, filename)
            for part in ('glyphs', 'subroutines', 'private_dict'):
                self.assertEqual(new['programs'][part], old['programs'][part], f'{filename}/{part}')

    def test_043_symbol_refinement_preserves_every_layout_table_and_cmap(self):
        """Refining the 44 symbols in 0.43 cannot alter GPOS, GSUB, GDEF, cmap, OS/2, hhea, or STAT."""
        previous = json.loads((ROOT/'tests/fixtures/reader-0.42-identity.json').read_text(encoding='utf-8'))
        current = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertEqual(set(previous['files']), set(current['files']))
        self.assertEqual(current['cmap'], previous['cmap'])
        for filename, old in previous['files'].items():
            new = current['files'][filename]
            self.assertEqual(new['glyphs'], old['glyphs'], filename)
            for tag in ('GPOS', 'GSUB', 'GDEF', 'cmap', 'OS/2', 'hhea', 'post', 'STAT', 'maxp'):
                if tag in old['tables'] or tag in new['tables']:
                    self.assertEqual(new['tables'].get(tag), old['tables'].get(tag), f'{filename}/{tag}')

    def test_build_timestamps_are_the_only_ignored_fields(self):
        font = TTFont(self.path, recalcTimestamp=False)
        font['head'].created += 60
        font['head'].modified += 60
        self.save(font)
        self.assertEqual(self.failures(), [])

    def test_advance_change_fails(self):
        font = TTFont(self.path)
        advance, bearing = font['hmtx']['R']
        font['hmtx']['R'] = advance+1, bearing
        self.save(font)
        failures = self.failures()
        self.assertTrue(any('hmtx' in flag.get('tables', []) for flag in failures))

    def test_outline_or_hint_change_fails(self):
        font = TTFont(self.path)
        char = font['CFF '].cff.topDictIndex[0].CharStrings['R']
        char.decompile()
        first_number = next(i for i, value in enumerate(char.program) if isinstance(value, (int, float)))
        char.program[first_number] += 1
        self.save(font)
        failures = self.failures()
        self.assertTrue(any(flag['kind']=='reader-outline-or-hint-identity' for flag in failures))
        self.assertTrue(any('CFF ' in flag.get('tables', []) for flag in failures))

    def test_name_and_layout_are_also_protected(self):
        font = TTFont(self.path)
        font['name'].setName('Changed family', 1, 3, 1, 0x409)
        self.save(font)
        self.assertTrue(any('name' in flag.get('tables', []) for flag in self.failures()))


class DisplayInheritanceTests(unittest.TestCase):
    def test_full_shared_reader_features_work_before_reuse(self):
        with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as font:
            failures, report = audit_features(font)
        self.assertEqual(failures, [])
        self.assertEqual(report['pinned_cldr_locales'], 148)
        self.assertEqual(report['languages'], 161)
        self.assertGreater(report['language_strings'], 17000)

    def test_041_additions_preserve_all_040_outlines_and_metrics(self):
        """Every 0.40 non-symbol glyph keeps identical outlines/hmtx; refined 0.43 symbols keep advances."""
        from build_subsets import ALL_STYLES
        fixture_file = ROOT / 'tests/fixtures/reader-0.40-original-glyphs.json'
        baseline = json.loads(fixture_file.read_text(encoding='utf-8'))['styles']
        refined_chars = '★☯⚡☀☾☽⚔✦☆◆◇▲▼▶◀♥♡♪©®™Ⓢ♩♫♬♭♮♯⏸⏹⏺⏭⏮🎧💻📖🔖🔍🔔⚙⌂🎤💿🔊'
        self.assertTrue(set(baseline) <= {style for style, *_ in ALL_STYLES})
        for style, old_id in baseline.items():
            with self.subTest(style=style), TTFont(ROOT/'fonts'/f'SEIReader-{style}.otf') as after:
                cmap = after.getBestCmap()
                allowed_symbols = {cmap[ord(ch)] for ch in refined_chars}
                self.assertEqual(legacy_flags(after, old_id), [])
                for gname, old_row in old_id['glyphs'].items():
                    self.assertEqual(after['hmtx'][gname][0], old_row['hmtx'][0], f'{style}/{gname}')
                    if gname not in allowed_symbols:
                        self.assertEqual(list(after['hmtx'][gname]), old_row['hmtx'], f'{style}/{gname}')
                for code, gname in old_id['cmap'].items():
                    self.assertEqual(cmap.get(int(code)), gname)

    def test_missing_mark_feature_fails_the_behavior_gate(self):
        with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as font:
            features = font['GPOS'].table.FeatureList
            features.FeatureRecord = [record for record in features.FeatureRecord if record.FeatureTag!='mark']
            features.FeatureCount = len(features.FeatureRecord)
            failures, _ = audit_features(font)
        self.assertTrue(any(flag['kind']=='display-features' and 'mark' in flag['missing'] for flag in failures))

    def test_phase4_additions_preserve_original_035_contours_and_metrics(self):
        """Allow only reviewed curves and bearings in every historical Reader style."""
        legacy = json.loads(LEGACY_FIXTURE.read_text(encoding='utf-8'))
        for name,expected in legacy['styles'].items():
            with self.subTest(style=name), TTFont(ROOT/'fonts'/f'{name}.otf') as font:
                self.assertEqual(legacy_flags(font,expected), [])

    def test_approved_italic_curve_does_not_allow_unreviewed_metrics(self):
        """An allowed drawing still rejects either a changed advance or bearing."""
        legacy = json.loads(LEGACY_FIXTURE.read_text(encoding='utf-8'))
        with TTFont(ROOT/'fonts/SEIReader-Italic.otf') as font:
            expected=legacy['styles']['SEIReader-Italic']
            original=font['hmtx']['g']
            for index in (0,1):
                changed=list(original); changed[index]+=1
                font['hmtx']['g']=tuple(changed)
                self.assertIn(dict(kind='reader-035-hmtx',glyph='g'),legacy_flags(font,expected))

    def test_original_metric_mutation_fails_even_with_additive_repertoire(self):
        legacy = json.loads(LEGACY_FIXTURE.read_text(encoding='utf-8'))
        with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as font:
            advance, bearing = font['hmtx']['R']
            font['hmtx']['R'] = advance+1, bearing
            failures = legacy_flags(font, legacy['styles']['SEIReader-Regular'])
        self.assertTrue(any(flag['kind']=='reader-035-hmtx' and flag['glyph']=='R' for flag in failures))


class DisplayDesignTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads(DESIGN.read_text(encoding='utf-8'))
        self.shared = json.loads(SHARED_DESIGN.read_text(encoding='utf-8'))
        self.reader = json.loads(SHARED_REFERENCE.read_text(encoding='utf-8'))
        self.font = TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf')
        self.addCleanup(self.font.close)

    def failures(self):
        variants=json.loads((ROOT/'display/spacing_soft.json').read_text(encoding='utf-8'))['variants']
        return design_flags(self.font, 'soft', self.original, self.shared, variants)

    def test_reviewed_inheritance_preserves_all_controls_and_final_metrics(self):
        validate_design_reference(self.original, self.shared, self.reader)
        self.assertEqual(self.failures(), [])
        self.assertEqual(len(self.shared['fonts']['soft']['previous_advance_changes']), 20)

    def test_approved_changed_old_glyph_is_still_gated_exactly(self):
        advance, bearing = self.font['hmtx']['a']
        self.font['hmtx']['a'] = advance+1, bearing
        self.assertTrue(any(flag['kind']=='advance-width' and flag['glyph']=='a' for flag in self.failures()))

    def test_new_combining_mark_advance_is_gated(self):
        name = self.font.getBestCmap()[0x301]
        advance, bearing = self.font['hmtx'][name]
        self.font['hmtx'][name] = advance+1, bearing
        self.assertTrue(any(flag['kind']=='advance-width' and flag['glyph']==name for flag in self.failures()))

    def test_original_vertical_metrics_are_gated(self):
        self.font['OS/2'].usWinAscent += 1
        self.assertTrue(any(flag['kind']=='line-metric' for flag in self.failures()))

    def test_edge_clipping_exception_is_exact_and_does_not_allow_other_changes(self):
        for cut, table, field in (('edge', 'OS/2', 'usWinAscent'),
                                  ('soft', 'OS/2', 'usWinAscent'),
                                  ('edge', 'hhea', 'ascent')):
            with self.subTest(cut=cut, table=table, field=field):
                changed = copy.deepcopy(self.shared)
                before = self.original['fonts'][cut]['metrics'][table][field]
                after = changed['fonts'][cut]['metrics'][table][field]+1
                changed['fonts'][cut]['metrics'][table][field] = after
                changed['fonts'][cut]['previous_metric_changes'][f'{table}.{field}'] = dict(
                    table=table, field=field, before=before, after=after,
                    delta=after-before, reason='phase4-edge-vietnamese-clipping')
                with self.assertRaisesRegex(ValueError, 'unapproved clipping'):
                    validate_design_reference(self.original, changed, self.reader)

    def test_unlisted_old_metric_change_cannot_be_blessed_by_fixture(self):
        changed = copy.deepcopy(self.shared)
        changed['fonts']['soft']['advances']['R'] += 1
        with self.assertRaisesRegex(ValueError, 'listed explicitly'):
            validate_design_reference(self.original, changed, self.reader)

    def test_browser_vertical_metrics_cannot_drift(self):
        for table, field in (('OS/2', 'usWinAscent'), ('hhea', 'ascent')):
            with self.subTest(table=table), TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.woff2') as web:
                setattr(web[table], field, getattr(web[table], field)+1)
                failures = web_flags(self.font, web)
                self.assertTrue(any(flag['kind']=='web-table' and flag['table']==table for flag in failures))

    def test_blank_letter_fails_even_with_valid_glyph_inventory(self):
        char = self.font['CFF '].cff.topDictIndex[0].CharStrings['R']
        char.decompile()
        char.program = ['endchar']
        self.assertIn('R', self.font.getGlyphOrder())
        self.assertIn('R', self.font.getBestCmap().values())
        path = outline(self.font, 'R')
        self.assertFalse(path)
        self.assertEqual(blank_flags('R', path), [dict(kind='empty-glyph')])

    def test_only_explicit_space_glyphs_may_have_no_ink(self):
        for name in ('space', 'uni2009', 'uni202F'):
            self.assertEqual(blank_flags(name, outline(self.font, name)), [])


class NightGradeTests(unittest.TestCase):
    def test_night_grades_thin_light_regular_medium_strokes_with_zero_reflow_metrics(self):
        samples = [
            ('The gate will remain closed until morning, Iñés said. Lian placed Mei’s entry beside the lamp and read it again.', None),
            ('“Entry 12?” — 312, 314; 1,234.56 · 8.50% · ½ ¼ ¾ · office reflection', None),
            ('İpek · Işık · fikir · fi · fı', 'tr'),
            ('Ștefan · țară · ş ţ · ș ț', 'ro'),
            ('Őrző · tűz · TY TTY · gyűrű', 'hu'),
            ('Άγγελος · Αθήνα · Σωκράτης · Ήλιος', 'el'),
            ('Москва · Санкт-Петербург · їжак · ґанок', 'uk'),
            ('Tiếng Việt · Nguyễn · đường phố · trường học', 'vi'),
        ]
        # Hinted stem widths are twice the drawn reading stroke: Light 74 -> 70, Regular 85 -> 81, Medium 97 -> 93.
        for day_style, night_style, day_stem, night_stem in (
                ('Light', 'LightNight', 148, 140), ('LightItalic', 'LightItalicNight', 148, 140),
                ('Regular', 'RegularNight', 170, 162), ('Italic', 'ItalicNight', 170, 162),
                ('Medium', 'MediumNight', 194, 186), ('MediumItalic', 'MediumItalicNight', 194, 186)):
            day_path = ROOT/'fonts'/f'SEIReader-{day_style}.otf'
            night_path = ROOT/'fonts'/f'SEIReader-{night_style}.otf'
            with TTFont(day_path) as day_font, TTFont(night_path) as night_font:
                day_priv = day_font['CFF '].cff.topDictIndex[0].Private
                night_priv = night_font['CFF '].cff.topDictIndex[0].Private
                self.assertEqual(day_priv.StdVW, day_stem, day_style)
                self.assertEqual(night_priv.StdVW, night_stem, night_style)
                self.assertEqual(night_font['OS/2'].usWeightClass, day_font['OS/2'].usWeightClass, night_style)
                self.assertEqual(night_font['name'].getDebugName(16), 'SEIHouse Sans', night_style)
                weight_name = (day_font['name'].getDebugName(17) or '').removesuffix('Italic').strip()
                self.assertEqual(night_font['name'].getDebugName(1),
                                 'SEIHouse Sans Night' if weight_name in ('', 'Regular') else f'SEIHouse Sans {weight_name} Night')
                self.assertEqual(night_font.getGlyphOrder(), day_font.getGlyphOrder())
                for table in ('GSUB', 'GDEF'):
                    self.assertEqual(
                        night_font[table].compile(night_font),
                        day_font[table].compile(day_font),
                        f'{night_style} {table} table mismatch',
                    )
                from fontTools.misc.xmlWriter import XMLWriter
                from io import BytesIO
                kern_indices = {idx for rec in day_font['GPOS'].table.FeatureList.FeatureRecord
                                if rec.FeatureTag in ('kern', 'cpsp') for idx in rec.Feature.LookupListIndex}
                for idx in sorted(kern_indices):
                    b_night, b_day = BytesIO(), BytesIO()
                    night_font['GPOS'].table.LookupList.Lookup[idx].toXML(XMLWriter(b_night), night_font)
                    day_font['GPOS'].table.LookupList.Lookup[idx].toXML(XMLWriter(b_day), day_font)
                    self.assertEqual(b_night.getvalue(), b_day.getvalue(), f'{night_style} GPOS lookup {idx} mismatch')
                for glyph in day_font.getGlyphOrder():
                    self.assertEqual(
                        night_font['hmtx'][glyph][0],
                        day_font['hmtx'][glyph][0],
                        f'{night_style} advance mismatch on {glyph}',
                    )
                failures, _ = audit_features(night_font)
                self.assertEqual(failures, [])
            day_shaper = hb.Font(hb.Face(day_path.read_bytes()))
            night_shaper = hb.Font(hb.Face(night_path.read_bytes()))
            for text, lang in samples:
                for features in ({'kern': True, 'liga': True}, {'kern': True, 'liga': True, 'tnum': True}):
                    buf_day = hb.Buffer()
                    buf_day.add_str(text)
                    buf_day.guess_segment_properties()
                    if lang:
                        buf_day.language = lang
                    hb.shape(day_shaper, buf_day, features)

                    buf_night = hb.Buffer()
                    buf_night.add_str(text)
                    buf_night.guess_segment_properties()
                    if lang:
                        buf_night.language = lang
                    hb.shape(night_shaper, buf_night, features)

                    self.assertEqual(
                        [info.codepoint for info in buf_night.glyph_infos],
                        [info.codepoint for info in buf_day.glyph_infos],
                    )
                    self.assertEqual(
                        [(pos.x_advance, pos.y_advance) for pos in buf_night.glyph_positions],
                        [(pos.x_advance, pos.y_advance) for pos in buf_day.glyph_positions],
                    )


if __name__ == '__main__':
    unittest.main()
