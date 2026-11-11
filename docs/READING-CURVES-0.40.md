# Reader curves — 0.40

The lowercase `g` now uses the same mirrored `b/d/p/q` bowl, with the existing
descending hook and a complete right stem. Capital `S` follows lowercase `s`'s
continuous curve rhythm. The question mark uses a continuous curved hook while
keeping its stem endpoint, dot, width and bearings.

The shared drawings carry into the accented forms `ĝğġģŚŜŞŠȘ`, Cyrillic `Ѕ`,
and italic `д`. No other Reader outlines change: 13 replacements per upright
face and 14 per italic face, including both Night grades. Global drawing settings,
all advances, every GPOS/GDEF/GSUB table, and line metrics are preserved. The
italic painted left bounds change with the outlines; their advances and placement
origins do not.

Automatic kerning previously retuned some inherited script pairs after an outline
change. `reading_curve_spacing.json` retains just the affected pairs and their
literal/class distinction from `5774a8a`, so rebuilding the default Reader keeps
the original positioning. Explicit pair overrides still work. Custom geometry
and Display cuts continue to calculate their own spacing.

The release is `@seihouse/seireader@0.40.0`. All twelve full faces and 84 subsets
are rebuilt. All four Display cuts inherit the shared refinements; their advances
remain fixed and their measured title spacing is regenerated. The updated static
Display fonts and shared runtime ship in `@seihouse/living-titles@0.1.2`.

## Proofs and preservation

- [Regular detail and paragraph comparison](proofs/reading-curves/regular-detail.png)
- [All twelve faces, Day](proofs/reading-curves/family-day.png)
- [All twelve faces, Night](proofs/reading-curves/family-night.png)
- [Actual-font preservation report](proofs/reading-curves/preservation.json)

These proofs use HarfBuzz positioning and FreeType rasterization of the actual
OTFs, at 17/20px for text and 45/130px for detail. They are native raster evidence,
not physical phone or Safari certification.

The original 0.35 and 0.39 fixtures are unchanged. New exact before/after outline
exceptions describe only the reviewed replacements; a new identity fixture gates
all 108 Reader deliveries, including Night. The engine regression restores only
the three original definitions to check historical hashes, and independently
compares every new width, bearing, dot, pair, alternate and unrelated path.

To repeat the real-font scope audit, preserve the original fonts from `5774a8a`,
then run:

```sh
python -X utf8 verify_reading_curves.py path/to/original/fonts --report dist/reading-curves.json
python -X utf8 render_reading_curves.py path/to/original/fonts
node --test tests/shared-engine.test.mjs
node verify_phase4_engine.mjs 5774a8a
python -X utf8 verify_shared_engine.py
```

Regular and Italic rebuilt through the final builder match every normalized table
and complete hint program in the shipped files. CI repeats the full Reader and
Display rebuild, plus construction, motion, package and website gates.
