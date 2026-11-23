# SEIHouse Noto — chosen design direction

## Owner decision — 2026-10-28

**Balanced (study B) is the base.** The owner's direction is “a warmer version of
Google Noto Sans.” This is a new, original SEIHouse family. Its long-term goals
remain broad Unicode script support and an unmistakable SEIHouse identity.

The choice approves Balanced's character; it does not approve every subsequent
refinement or establish production readiness. Keep the original B available for
comparison. A and C are historical studies, not competing current directions.

## Preserve the chosen character

- Moderate terminal softness, full curves, and an upright, welcoming sans voice.
- The double-storey a and g, hooked lowercase l, and distinct I / l / 1 forms.
- Original construction independent of SEIHouse Sans, Display, and external fonts.
- Comfortable text first; details must survive actual paragraph sizes.

The Latin scaffold retains B's 74-unit construction stroke, 14-unit terminal
softness, .585 bowl fullness parameter, and 1.025 horizontal factor. These are
working parameters for this drawing, not universal geometry for other scripts.

## Refinement 01 — candidate, not a new owner decision

Source: `studies/warmth/build_samples.py`, `REFINEMENT` and `refine_balanced()`.
Output: `SEIHouseNotoBalanced-Regular.otf` / `.woff2`, version 0.002.

- Redraw a/c/e/g/s and the b/d/p/q bowls with smoother continuous curves.
- Coordinate the n/h/m/r shoulders and u so stems and arches have a steadier rhythm.
- Use 68-unit strokes for the e/f/t crossbars while retaining 74-unit main strokes.
- Bring flat lowercase stems to the baseline; align inherited capitals to the
  working cap height with small vertical corrections and round overshoots.
- Space straight and round forms by sidebearing groups, then apply limited
  pair kerning. Existing accented lowercase letters share their base's pairs.
- Preserve all original A/B/C font bytes. The approved B WOFF2 hash is checked
  by `tests/test_noto_balanced.py`, alongside reproducibility of the refinement.
- Unite independently drawn filled parts before exporting the refinement. This
  removes unintended winding holes where the comma/semicolon dots meet their tails.

Compare using the same size, weight, colors, and passage. Review both full paragraphs
and enlarged letter details. The comparison is the default Noto test page in the
Font Lab navigation; the first three studies remain accessible from its footer.

## Redraw 02 — candidate, not a new owner decision

On 2026-11-12 the owner asked for SEIHouse Noto to be reimagined: more professional,
keeping its flavour. Source and outputs: `studies/redraw/` (version 0.011).

- New construction: stroke thickness follows direction (88 upright / 74 horizontal
  at Regular) and tapers where arches and bowls meet a stem. The constant 74-unit
  line of the earlier drawings is retired in this candidate.
- Regular carries a text weight. Light is close to the earlier colour; Medium and
  Bold come from the same rules, with lighter horizontal crossbars and opened inner
  loops in heavier weights (`a, e, g, s, B, 8`), plus a reading-size polish to
  `a`, `e`, `g`, and `s` (replacing `g`'s wide flat loop shelf with a compact
  curved neck and rounded lower loop under the upper bowl, calming `s`'s mid-spine,
  and tuning `a` and `e` counter openness) so paragraphs keep an even colour at
  14–18 px.
- Kept from Balanced: the softness (one corner radius, 13 units at Regular), the
  .585 full curve, two-storey a and g, hooked l, distinct I / l / 1.
- Changed from Balanced: vertical proportions (x-height 520, capitals 700,
  ascender 744), the 1.025 horizontal factor (letters are drawn to width instead),
  and all spacing, which is now shape-based with automatic kerning.
- 363 characters (`367` glyphs): complete printable Basic Latin, Latin-1 Supplement and
  Latin Extended-A (including `¤ ¦ § ¨ © ª ¬ ® ¯ ² ³ ´ µ ¶ ¸ ¹ º ¼ ½ ¾` and
  `ĸ Ĳ ĳ Ŀ ŀ ŉ Ŋ ŋ ſ`), everyday typography symbols, Romanian comma-below
  (`Ș ș Ț ț`), Welsh accents (`Ẁ ẁ Ẃ ẃ Ẅ ẅ Ỳ ỳ`), dotted circle (`◌`), and all 19
  Latin combining marks (`U+0300–U+0304`, `U+0306–U+030C`, `U+0312`, `U+031B`,
  `U+0323`, `U+0326–U+0328`, `U+0331`) with `GDEF`, `ccmp` canonical composition and
  dotless substitution (including `u012F.dotless`), Romanian/Moldovan `locl`, `mark`
  attachment anchors, independent above/below `mkmk` stacking, `IgnoreMarks` kerning,
  separated `Š`/`Č`/`ť` carons, and `STAT` / `OS/2` / `CFF` stem metadata.
- Night optical grade (`NIGHT_GRADE = -4`): `Light Night`, `Regular Night`,
  `Medium Night`, `Light Italic Night`, `Italic Night`, and `Medium Italic Night`
  thin strokes by 4 upright units to counter dark-mode halation while keeping
  exact Day advance widths and `GPOS` kerning so Day/Night toggles never reflow.
- Skim pass, measured on blurred 16 px prose against Google Noto Sans: the hooked
  `l` keeps its foot but tucked closer (it left a light hole after every l), and the
  two-storey `a` meets its stem more lightly (it was a dark knot). Texture now matches
  Noto Sans (0.110). Next candidates: the `g` (darkest letter) and slightly wide `o e c`.
- Rhythm pass (`RHYTHM` in `letters.py`): letters with one protruding part (`t`, `l`,
  `v w y`, `A V X Y Z`) are spaced by their bodies, not their tips, and open-sided capitals
  (`E L P R Q`) get a little more room. Measured as white area between real pairs against
  Google Noto Sans as a yardstick: prose gap difference 7.1% → 4.7% at Regular. `t` and `y`
  fade toward Bold. Next candidates: `ry`/`re`, `ow`, `ll`, Bold capitals `N S W Z`.
- Optical spacing pass (`optical.py`) on top of the automatic kerning, from an
  eye review of real words at every weight: W follows V with lowercase (`Wa`, `We`,
  `Wo`), the f terminal gets air above the x-height (`fi`, `fl`, `fí`, `f”`), and
  tucked descenders (`gj`, `qj`) only need clearance. `T` and `Y` pairs were
  reviewed and left unchanged.

The owner has not yet compared or approved it. Until then Balanced is the approved
direction and Refinement 01 the last reviewed drawing. See
[the study notes](studies/redraw/README.md) for limits.

## Evidence and boundaries (Refinement 01)

This pass has 94 encoded characters / 95 glyphs including .notdef: Latin letters,
digits, selected punctuation and nine precomposed accented letters. It adds no new
script coverage. Combining-mark support, a complete Latin repertoire, additional
weights, hinting, and native/script-specialist testing remain future work.
The OS/2 Latin code-page bit is a compatibility classification for this functional
Latin prose specimen, not a claim of complete Windows-1252 coverage. Exact support
is recorded in the manifest and cmap. OpenType leaves functional code-page
classification to the designer ([OS/2 specification](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#ulcodepagerange1-bits-0-31)).

The regression checks cover preserved B bytes, reproducible output, every glyph's
outline bounds and fragments, key counter topology, baseline alignment, and real
HarfBuzz shaping/kerning. Browser checks cover actual font selection, responsive
views, controls, navigation and portable-font embedding. Automated evidence is not
a substitute for reading comfort or future native-script review.

Conceptual references: [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths/)
on curve continuity; [Glyphs: sketching](https://glyphsapp.com/learn/sketching)
on optical alignment; [Glyphs: kerning](https://www.handbook.glyphsapp.com/kerning/)
on spacing before pair adjustments. No third-party outlines or metrics are used.

The broader research reference is [the Noto handbook](../docs/SEIHOUSE-NOTO-HANDBOOK.md).
This file records the actual owner choice and current drawing, rather than treating
all handbook recommendations as already approved or implemented.
