# SEIReader design goals

The approved direction is **Literata + Rubik + SEIHouse = SEIReader**.

1. Keep a distinctive look. Preserve the softness, softly squared construction, recognizable
   caps and terminals, handwriting-style italics, and SEIHouse symbols already established.
2. Bring the consistency and polish of the references to reading text. Refine individual
   proportions, open counters and terminals, and optical spacing across the full family.

Use Literata as a reference for sustained reading rhythm and differentiated letters, and
Rubik as a reference for friendly, softly squared construction. SEIReader remains an original
design drawn from its own code rules. Reference outlines are used only in comparison assets.

## The 0.27 measurements

Regular / 400; Literata explicitly set to optical size 20; dimensions normalized to an em.

| Proportion | SEIReader 0.27 | Literata 3.103 | Rubik 2.300 |
|---|---:|---:|---:|
| x-height | 0.510 | 0.508 | 0.520 |
| Capital height | 0.700 | 0.703 | 0.700 |
| Word space | 0.205 | 0.200 | 0.245 |
| `a` advance | 0.602 | 0.538 | 0.552 |
| `e` advance | 0.590 | 0.518 | 0.560 |
| `i` advance | 0.223 | 0.332 | 0.242 |

The 0.28 candidate keeps the overall height and the deliberate alignment of tall lowercase
with caps. It targets `a`/`e` widths, the side space of `i`, and individual curves and openings
for `a`, `e`, `c`, and `s`. Raised quotes carry forward; apostrophe placement should be reviewed
in `Mei's`. Weight and contrast stay at the 0.27 values while Regular and Medium are compared.

## The 0.29 lowercase consistency pass

Refine the shoulders of `h/n/m`, the lower curve of `u`, and the bowls of `b/d/p/q`
beside the established `a/e/c/s`. Shared continuous curves give related letters smooth
stem joins and balanced inner spaces, with short straight sides retaining the softly
squared character. Italics keep their lower branches and small pen-like exits.

The 0.29 comparison used preserved 0.28 as its immediate baseline. All ten 0.27 styles
remain under `old/0.27/`. Every advance and every setting except the version number
matches 0.28. The existing automatic pair-spacing pass measures the new outlines;
this iteration does not change its rules. `ñ/ù/ú/û/ü` follow their updated base curves.
`verify_lowercase.py` audits these limits against all ten preserved 0.28 fonts.

## The 0.30 optical spacing pass

Preserve every 0.29 contour, bearing, and advance. Measure the central lowercase band
for the reported word/pair cases, limit how far open edges affect the calculation,
and retain room between the closest ink. Upright and italic have separate correction
limits and every weight is measured independently. `rn/rm` retain a separation cushion;
`tt/ry` receive room at their crowded edges. Joined `fi/fl` participate in surrounding
pair spacing, with their internal construction unchanged. Accented letters inherit
the same pair classes as their bases. The Lab uses the resulting per-style pairs.

The 0.30 preview compared the candidate with preserved 0.29 and the references. Its fixed
13/15/17px matrix covers Light, Regular, and Medium, upright/italic, with accents and
joins on/off. Native Windows WPF grayscale proofs at 96 dpi supplement the font audits.
Physical iPhone/Android and browser checks are deferred at the user's request; they
remain required evidence before making device-specific readability claims.

## The 0.31 broader spacing rhythm pass

Preserve every 0.30 contour, bearing, advance, and design setting. Inspect `minimum`,
`murmur`, `river`, `climate`, `parallel`, and `everywhere`, with supporting `rival`,
`arrival`, `vivid`, `willow`, `weary`, `yearly`, and `twilight`. Use the established
central-band measurement and minimum ink separation separately at every weight and italic.
Keep the earlier focused pairs and ligature-neighbor corrections unchanged.

Balance `ll`, protect `yw/tw` where the outlines come close, and give italic `ur/um`
enough separation. New residuals below five source units retain their current spacing
unless the minimum ink gap requires correction. This avoids adjusting already balanced
words merely to make every sample different. See [the inspection notes](SPACING-0.31.md).

The same four-card preview compares 0.31 with preserved 0.30, Literata, and Rubik. It
includes the broader words in prose and upright/italic word lines, plus the fixed-size
matrix. Native Windows proofs cover 13/15/17px Light/Regular/Medium and all five weights
at 20px in Day/Night. Device and sustained-reading comfort results remain deferred.

## The 0.32 punctuation, figures, and reading-weight pass

Refine these two areas together so marks and figures sit comfortably in the prose.
Smooth the continuous curves of `2/3/5/6/8/9`, keep the characteristic angular `1/4/7`,
and give full-size figures a 4% lighter stroke. Numeric alternates inherit the new
curves, with small figures retaining their separately lighter stroke. Quotes, commas,
dots, and dashes make quieter marks while quotes keep their raised position.

Calibrate letter strokes to 74 source units in Light and 97 in Medium, with 85 unchanged
in Regular. Keep the nominal 70/85/100 controls so all advances and the established
letter-pair spacing remain stable. These are static master refinements at every size,
not an optical-size axis. Other weights keep their letter drawings. Symbols/icons,
word space, contrast, italic angle, tall-letter alignment, and vertical metrics stay
as in 0.31. Custom design settings can still remeasure the letter-pair spacing.

The same preview uses preserved 0.31 as its baseline and retains Literata/Rubik, the
earlier word samples, and all reading controls. It adds dialogue punctuation, decimals,
proportional/tabular figures, and fractions to the fixed small-size matrix. See
[the inspection notes](TEXTURE-0.32.md). Native Windows proofs supplement the outline
and shaping audits; physical browser/device and sustained-reading results remain deferred.

## The 0.33 Latin foundation

Add reliable combining accents and local quotation marks while keeping the 0.32 reader
design intact. Preserve every old outline, bearing, advance, pair value, nominal weight,
height, contrast, and italic angle. New marks use lighter strokes, optical base attachment,
above/below stacking, and italic shear shared with the letter drawing. Canonical forms
of the existing accented text must shape identically; above accents on i/j remove the dot.

Keep complete Latin clusters and prose in the same web face. The generated Latin extended
subset includes basic Latin and is preferred in fonts.css. Complete encoded alphabets,
locale-specific letter refinements, and new scripts belong to later expansion steps.
See [the foundation notes](LATIN-FOUNDATION-0.33.md).

The same four-card preview uses preserved 0.32 and retains Literata/Rubik and the earlier
controls/samples. New rows compare NFC/NFD, stacked marks, and local dialogue punctuation.
Baseline rows may use fallback for additions. Physical device and sustained-reading
comfort results remain deferred.

## Reading experiments

Use [the reference preview](../lab/comparison.html) for matched samples, then
[the chapter test](../lab/reading-test.html) for sustained reading. Preserve the 0.32 baseline
and use the same text, physical column width, color, and selected weight when comparing.

- Inspect `Lian`, `Iñés`, `blade`, `Entry`, `Mei's`, and italic `acquittal`.
- Inspect `“Mei’s,”`, `“Entry 12?”`, `312/314`, `1,234.56`, `8.50%`, and `6089`, upright
  and italic. Compare both figure sets and watch commas, dots, and quote tails at 13/15/17px.
- Inspect `minimum`, `murmur`, `river`, `climate`, `parallel`, and `everywhere`, upright
  and italic. Include `rival`, `arrival`, `vivid`, `willow`, `weary`, `yearly`, and `twilight`.
- Inspect `human`, `minimum`, `humming`, `bud`, `dawn`, `people`, and `quiet`, upright
  and italic. Compare both arches of `m`, the `u` bottom, and `b/d/p/q` counters at
  Light and Bold as well as the main reading weights.
- Compare 20px at line heights 1.4 and 1.5, then 13/15/17px at Regular and Medium.
- Compare word spaces 0.205, 0.220, and 0.230 em; versions 0.28 through 0.30 use the middle value.
- Check Light comments, real italics, `fi`/`fl`, accents, punctuation, and symbols on phones.
- Check NFC/NFD pairs, `n̄ m̀ x̣ g̃ ī j́ Ấ`, stacked above/below marks, and local quotes,
  in full-font and subset delivery. Compare 1.4/1.5 leading for stacked capitals.
- Record tiring spots, snag words, and comfort after a chapter. Measurements and automated
  font checks cannot establish sustained reading comfort.

## Research and reference delivery

- [How type influences readability](https://fonts.google.com/knowledge/readability_and_accessibility/how_type_influences_readability)
  informs the attention to crowding, letter recognition, and differences between readers.
- [Material 3: Applying type](https://m3.material.io/styles/typography/applying-type)
  recommends around 1.5 line height for body text and tabular figures for changing values.
- [Using web fonts](https://fonts.google.com/knowledge/using_type/using_web_fonts#optimizing-font-loading)
  informs the explicit weight/style mapping and `font-display: swap` delivery.

The preview bundles official [Literata](https://github.com/google/fonts/tree/main/ofl/literata)
and [Rubik](https://github.com/google/fonts/tree/main/ofl/rubik) references locally. Their OFL
licenses, exact versions, source hashes, and lossless WOFF2 conversion are recorded in
`references/`. This material is separate from the SEIReader build and never contributes
outlines to the candidate. The preview makes no network font requests.
