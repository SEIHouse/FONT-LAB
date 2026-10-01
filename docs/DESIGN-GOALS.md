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

The first candidate keeps the overall height and the deliberate alignment of tall lowercase
with caps. It targets `a`/`e` widths, the side space of `i`, and individual curves and openings
for `a`, `e`, `c`, and `s`. Raised quotes carry forward; apostrophe placement should be reviewed
in `Mei's`. Weight and contrast stay at the 0.27 values while Regular and Medium are compared.

## Reading experiments

Use [the reference preview](../lab/comparison.html) for matched samples, then
[the chapter test](../lab/reading-test.html) for sustained reading. Preserve the 0.27 baseline
and use the same text, physical column width, color, and selected weight when comparing.

- Inspect `Lian`, `Iñés`, `blade`, `Entry`, `Mei's`, and italic `acquittal`.
- Compare 20px at line heights 1.4 and 1.5, then 13/15/17px at Regular and Medium.
- Compare word spaces 0.205, 0.220, and 0.230 em; the 0.28 font uses the middle value.
- Check Light comments, real italics, `fi`/`fl`, accents, punctuation, and symbols on phones.
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
