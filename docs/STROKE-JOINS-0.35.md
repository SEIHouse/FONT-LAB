# SEIReader 0.35: solid stroke joins

The homepage's 68px specimen exposed missing ink at the turns of `v/V/w/W`,
`2/3/4/5`, and related smaller figures. These were unintended export defects.

## Cause and repair

The stroke expander can produce a contour that overlaps itself at a tight turn.
The builder already united different shapes within a glyph, but a glyph with
only one path bypassed that operation. Self-intersections survived CFF export
and hinting. Chromium's font rasterizer displayed those overlaps as holes.
The same contours appeared solid when rendered as SVG with nonzero winding,
which explains why the live engine drawing could look correct.

`make_fonts.py` now resolves overlaps and contour winding on every finished
outline before curve fitting, CFF encoding and auto-hinting. The fix also
reaches tabular figures, superscripts, subscripts, fractions, combining marks
and symbols. The Display engine is separate and is unchanged in this repair.

This keeps the original centerline drawings, round joins, contrast, configured
weights, advance widths, kerning, language behavior and line metrics. Cleanup
can change curve segmentation, with small differences from fitting and rounding
to whole font units. It does not intentionally redesign a letter or number.

## Verification

Run `python verify_stroke_joins.py` after rebuilding. It compares the full family
with preserved `old/0.34` fonts and checks:

- Every glyph's actual CFF ink agrees under nonzero and even/odd fill rules.
- The archived v/V/w/W/2/3/4/5 reproduce the original ambiguity in all ten styles.
- Repaired silhouettes match the original intended filled outline within
  subpixel fitting tolerances; counters and empty glyphs remain intact.
- Horizontal metrics and GPOS/GSUB/GDEF tables match byte for byte.
- Design settings, per-style pairs, language pairs and line metrics are preserved.
- All ten language inventories, NFC/NFD forms and numeric feature layouts match.
- Full WOFF2 fonts and all thirty web subsets preserve the repaired outlines,
  metrics, coverage and shaping.

FontBakery profiles and Chromium rendering are separate checks. A FontBakery
pass alone did not catch the original missing patches; the fill-rule regression
audit now covers that failure directly. See `HEALTH-CHECK.txt` for final results.

The comparison page now shows 0.35 alongside the archived 0.34, Literata and
Rubik. Refresh the local homepage or comparison page to load the rebuilt fonts.
