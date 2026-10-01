# SEIReader 0.31: broader spacing inspection

Inspect the rhythm of **minimum, murmur, river, climate, parallel, everywhere**,
upright and italic at all five weights. Supporting cases are **rival, arrival,
vivid, willow, weary, yearly, twilight**, covering both sides of `r/v/w/y` and
the narrow `i/l/t` forms.

## Findings and changes

- `ll` left more apparent space than its neighbors in `parallel` and `willow`.
  It receives a modest tightening at every weight, with separate italic values.
- `yw` in `everywhere` and `tw` in `twilight` had close upper outlines. They
  receive more separation, with the minimum ink gap taking precedence over the
  usual adjustment limit where necessary.
- Italic `ur/um` bring the exit of `u` close to the next stem. Their spacing
  opens, particularly in Light and Regular. Other measured italic cases include
  `ev/iv`, `ar`, and the gaps beside `l`.
- Many upright gaps in `minimum`, `murmur`, and `river` were already balanced.
  New corrections below five source units are omitted when the minimum ink gap
  is already satisfied. Balanced gaps retain their prior values.

The pass changes **9–12 pairs per upright style** and **25–29 per italic style**.
These are pair adjustments; every glyph contour, bearing, advance, weight, height,
contrast, word space, and all earlier focused/ligature-neighbor pairs match 0.30.

### Representative pair values

Values are adjustments in the source scale of 1,000 units per em. Positive values
add space; negative values remove space. They are not measurements of the visible
gap itself. The finished 2,000-unit fonts store twice these values.

| Pair | Regular: 0.30 → 0.31 | Italic: 0.30 → 0.31 |
|---|---:|---:|
| `ll` | +6 → −12 | +6 → −19 |
| `yw` | 0 → +45 | −22 → +37 |
| `tw` | 0 → +38 | −30 → +30 |
| `ur` | 0 → 0 | 0 → +22 |
| `um` | 0 → 0 | 0 → +22 |
| `ev` | −10 → −10 | −10 → −35 |

## Evidence and limits

- [The same four-card preview](../lab/comparison.html) compares 0.31, preserved
  0.30, Literata, and Rubik, with the broader words in prose and upright/italic
  samples. Its original reading controls and Day/Night setup remain available.
- Native Windows WPF [Day](proofs/0.31/windows-day-96.png) and
  [Night](proofs/0.31/windows-night-96.png) proofs cover 13/15/17px in Light,
  Regular, and Medium. [Family Day](proofs/0.31/family/windows-day-96.png) and
  [Family Night](proofs/0.31/family/windows-night-96.png) cover all five weights
  and real italics at 20px. Both comparison columns use actual HarfBuzz-shaped
  glyph indices at 96 dpi, without synthetic styles or font installation.
- `verify_spacing.py` checks all 295 outlines and metrics against exact archived
  0.30 files, restricts every changed pair to the inspected cases, and verifies
  accent inheritance, hints, full/subset shaping, and actual outline collisions.
- FontBakery OpenType and offline universal checks have zero failures and
  warnings. Physical phone/browser rendering and sustained-reading comfort
  remain unverified; the native proofs do not establish those results.
