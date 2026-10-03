# SEIReader 0.35: final paragraph-spacing inspection

Inspected **“said. Lian,” “Mei’s entry,” “minimum,” and “parallel”** in whole
paragraphs on 2026-10-03. No demonstrated spacing defect was found in these
candidates, so the existing font files, drawings, advances, kerning, word space,
settings and version are retained. This is an inspection record, not a font release.

## Paragraph and conditions

> The gate will remain closed until morning, Iñés said. Lian placed Mei’s entry
> beside the lamp and read it again. The note asked for a minimum of three
> witnesses before anyone opened the inner court. Two parallel paths followed
> the river, where willow branches moved in the wind. He listened for the murmur
> beneath the bridge, then turned back to the ledger.

The same paragraph was also inspected with `Mei's entry`, upright and real italic.
The [reference preview](../lab/comparison.html) now contains these exact paragraphs
in each of its four cards, under **Paragraph spacing**. Open that disclosure and
use the existing size, weight, line-height, Day/Night and kerning controls.
The paragraph language remains English when the separate language sample changes.
Rebuild the preview with `python build_comparison.py`.

The browser proofs use the shipped full WOFF2 fonts in headless Chrome 154 on
Windows, at device scale 1 and 100% zoom. All five weights and their real italics
were inspected at **13, 15, 17 and 20px**, in Day and Night, at 1.4 line height and
a 1280px viewport. Regular/Italic were also inspected at 1.5 line height and at a
390px viewport. Kerning and common ligatures were enabled, with no added letter
or word spacing and no synthetic styles.

## Findings

| Candidate | Observation | Decision |
|---|---|---|
| `said. Lian` | The period remains distinct from the preceding word; the following sentence has a clear word boundary. The period-to-`L` horizontal ink gap is 0.3355–0.4159 em across the ten styles. | Retain punctuation pairs and the 0.220 em word space. |
| `Mei’s entry` / `Mei's entry` | Both apostrophes remain recognizable in paragraph context, with no outline intersection or lost boundary before `entry`. | Retain apostrophe drawings and pair values. |
| `minimum` | Upright gaps are closely matched. In Regular, adjacent horizontal bounding-box gaps are 0.1330–0.1375 em. Italic exits produce smaller bounding-box gaps, while the actual contours remain separate. | Retain the approved narrow-letter rhythm. |
| `parallel` | The two `l` stems remain separate without a conspicuous opening between them. Regular's `ll` horizontal bounding-box gap is 0.1001 em. | Retain the existing `ll` correction. |

Small italic text and heavier weights still look denser. That appearance did not
establish a local spacing error in these phrases. The inspection does not justify
opening every narrow pair, adding sentence-specific space, or changing global tracking.

## Measurements and validation

The [measurement record](proofs/0.35/paragraph-spacing.json) identifies the source
commit and SHA-256 of every inspected full OTF/WOFF2. HarfBuzz shaped the five
candidate strings and both complete paragraphs. Actual saved CFF paths were then
placed at the shaped advances and offsets; neighboring filled outlines, including
neighbors across a space, had no intersections above 0.01 square font units.
All characters were present in the actual font, without `.notdef`.

Full OTF, full WOFF2 and Latin extended shaping agree for all seven strings in
every style. Latin basic agrees for the four candidate strings it fully covers;
the curly-apostrophe phrase and the paragraphs containing `Iñés` require Latin
extended or the full font. All ten browser faces loaded with their proper weight
and style. Fifty browser kerning-on/off deltas at a 2000px diagnostic size match
HarfBuzz exactly. This checks applied pair positioning; it does not claim that
small-size hinted browser advances equal unhinted outline measurements.

The reported gaps are distances between positioned horizontal ink bounding boxes,
divided by 2000 units per em. The sentence gap runs from the period's right ink
edge to `L`'s left ink edge across the intervening space. Word gaps run between
adjacent glyph boxes. They describe geometry, not a readability threshold, and
can understate the visible separation of slanted or vertically disjoint contours.
Collision checks and normal-size screenshots were evaluated separately.

## Saved browser proofs

Each desktop proof contains upright and real italic, four sizes, and both
apostrophe variants. The mobile proofs are desktop Chrome at a narrow viewport.

| Weight / condition | Day | Night |
|---|---|---|
| Light | [Proof](proofs/0.35/paragraph-light-day.png) | [Proof](proofs/0.35/paragraph-light-night.png) |
| Regular | [Proof](proofs/0.35/paragraph-regular-day.png) | [Proof](proofs/0.35/paragraph-regular-night.png) |
| Medium | [Proof](proofs/0.35/paragraph-medium-day.png) | [Proof](proofs/0.35/paragraph-medium-night.png) |
| SemiBold | [Proof](proofs/0.35/paragraph-semibold-day.png) | [Proof](proofs/0.35/paragraph-semibold-night.png) |
| Bold | [Proof](proofs/0.35/paragraph-bold-day.png) | [Proof](proofs/0.35/paragraph-bold-night.png) |
| Regular, 390px viewport | [Proof](proofs/0.35/paragraph-mobile-day.png) | [Proof](proofs/0.35/paragraph-mobile-night.png) |
| Regular, 1.5 line height | [Proof](proofs/0.35/paragraph-regular-leading-15.png) | — |

This is evidence for these samples and this desktop browser. Physical iPhone,
Android, Safari and sustained chapter-reading comfort remain unverified; the
390px screenshots do not certify a phone. No new FontBakery result is claimed
because this inspection changes no font bytes.
