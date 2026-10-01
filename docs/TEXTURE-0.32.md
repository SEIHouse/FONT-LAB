# SEIReader 0.32: punctuation, figures, and reading weights

The approved direction remains **Literata + Rubik + SEIHouse = SEIReader**.
This pass combines punctuation/number texture and small-size weight balance.

## Inspection and changes

The native 13/15/17px proofs showed dark punctuation clusters beside the refined
lowercase, and several figures retained more rigid corners than the surrounding
letters. Quotes and commas now use curved tails. Dots are smaller, while quotes,
dashes, and other reading punctuation use a lighter, capped stroke. Quotes keep
the raised endpoints introduced in 0.27.

Continuous curves soften `2/3/5/6/8/9`; `0` retains its softly squared form, and
`1/4/7` retain their angular construction. Full-size figures use a 4% lighter
stroke than the calibrated letter stroke. Tabular figures reuse the finished
digit outlines. Superscripts, subscripts, numerator/denominator sets, and fractions
inherit the new curves with their separately lighter strokes. Proportional figures
remain the default. All figure advances and opt-in features remain unchanged.

| Weight | Nominal control | Letter stroke in 0.31 | Letter stroke in 0.32 |
|---|---:|---:|---:|
| Light | 70 | 70 | 74 |
| Regular | 85 | 85 | 85 |
| Medium | 100 | 100 | 97 |
| SemiBold | 115 | 115 | 115 |
| Bold | 140 | 140 | 140 |

Values are source units per 1000/em. Light gains substance; Medium gains counter
room. Nominal controls still determine character advances and tracking. Letter
stroke corrections interpolate for intermediate Lab weights and apply at every
size. These fonts are static masters with no optical-size axis. Regular remains
the default body-text reference; the two other reading weights remain distinct.

The built `n` has about 5% more ink in Light and 2.6% less in Medium, upright and
italic. Its ink area remains identical in the other weights. This is an outline
measurement, not a rating of readability on a particular device.

## Scope and spacing

- Every one of the 295 character/alternate advances matches 0.31.
- Nominal weights, word space, tracking, x-height, cap height, vertical metrics,
  contrast, and italic angle match 0.31. Only the version setting changes.
- Regular, SemiBold, and Bold letter outlines and bearings match 0.31 exactly.
  Light/Medium letter outlines, dots, accent derivatives, and joins follow the
  calibrated stroke. Counter structure and tall-letter alignment remain intact.
- Symbols/icons, private-code aliases, compact ordinal marks, and fraction slash
  preserve their existing contours and metrics at every weight.
- Default builds retain every approved letter-to-letter pair from 0.31. Custom
  design settings remeasure those pairs. Explicit `pairSpace` overrides still win.
- Pairs involving marks/figures are remeasured. A 35-unit minimum sampled ink
  clearance covers their full height and accented class members. Finished
  outlines are also checked for intersections. This protects overhanging letters
  beside brackets and raised quotes beside accents.
- CFF alignment zones are unchanged. Standard stem hints use the calibrated
  letter stroke, and all ten fonts are autohinted again.

The counter audit caught an open 6/9 bowl in the first candidate. A shared closed
bowl now gives each digit one real counter. Compact `ª/º` keep their earlier
drawings so body-letter calibration cannot alter their small topology.

## Preview and evidence

The [same four-card preview](../lab/comparison.html) compares 0.32, preserved 0.31,
Literata, and Rubik. All fonts are embedded. Dialogue punctuation, chapter numbers,
decimals, proportional/tabular figures, and fractions sit beside the earlier
spacing samples. The fixed matrix covers Light/Regular/Medium, upright and real
italic, at 13/15/17px in both themes. The original Lab Reader Chamber includes
the same new reading cases; saved chapter feedback remains untouched.

Native Windows WPF grayscale proofs use HarfBuzz-shaped real glyph indices,
without font installation or simulated bold/italic:

- [Small-text Day](proofs/0.32/windows-day-96.png) and [Night](proofs/0.32/windows-night-96.png).
- [All-weight 20px Day](proofs/0.32/family/windows-day-96.png) and
  [Night](proofs/0.32/family/windows-night-96.png).
- [Broader-word Day](proofs/0.32/rhythm/windows-day-96.png) and
  [Night](proofs/0.32/rhythm/windows-night-96.png).

`verify_texture.py` checks the current family against the exact 0.31 archive.
`verify_phase2.py` checks numeric shaping and all thirty subsets. Historical
curve/spacing audits can run against `old/0.31/`, which preserves its full fonts,
subsets, settings, engine, and pair maps with SHA-256 manifests.

These proofs support local outline, shaping, and rasterization inspection.
Physical browser/device and sustained-reading comfort checks remain deferred at
the user's request. Online-only FontBakery checks remain unverified. See
[HEALTH-CHECK.txt](HEALTH-CHECK.txt) for the completed automated results.
