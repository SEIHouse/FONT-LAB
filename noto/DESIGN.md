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

## Evidence and boundaries

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
