# SEIReader 0.33: a reliable Latin foundation

This is the first step of the multilingual expansion: combining accents, their placement,
and local quotation marks. It preserves the 0.32 reading design and adds layout support
that later encoded alphabets can use. It does not claim complete support for every Latin language.

## Accent inventory

All seventeen marks have zero advance. Base letters and accents keep their real weight,
contrast, and italic construction from `engine.js`; new marks use a lighter pen capped
at 58 source units. The standard `ccmp`, `mark`, and `mkmk` features apply automatically.

| Codepoint | Mark | Placement |
|---|---|---|
| U+0300 | Grave | Above |
| U+0301 | Acute | Above |
| U+0302 | Circumflex | Above |
| U+0303 | Tilde | Above |
| U+0304 | Macron | Above |
| U+0306 | Breve | Above |
| U+0307 | Dot above | Above |
| U+0308 | Diaeresis | Above |
| U+0309 | Hook above | Above |
| U+030A | Ring above | Above |
| U+030B | Double acute | Above |
| U+030C | Caron | Above |
| U+031B | Horn | Upper right |
| U+0323 | Dot below | Below |
| U+0326 | Comma below | Below |
| U+0327 | Cedilla | Below |
| U+0328 | Ogonek | Lower right connection |

The existing precomposed letters are retained through canonical composition. For example,
`Café` and `Café` shape identically. Remaining marks attach to the letter's actual ink
height, with independent above/below stacks. Dotless `i/j` alternates preserve their original
advance and pair classes. Marks on `fi/fl` can attach to either ligature component. The
dotted circle `◌` supports isolated-mark inspection.

The anchors are transformed through the same italic shear as the outlines. Pair kerning
ignores combining marks and remains active across them. Every old pair value is frozen
to 0.32 for unchanged design settings; custom design controls still remeasure their pairs.

## Local text punctuation

Added `‚ „ ‛ ‟`, lexical apostrophes `ʻ ʼ`, U+2009 thin space, and U+202F narrow nonbreaking
space. The two spaces are 0.120 em; the established ordinary space remains 0.220 em.
Existing high quotes, apostrophes, and guillemets retain their drawings and spacing.

| Convention / purpose | Example |
|---|---|
| German outer/nested dialogue | `„Lian sagt: ‚Warte!‘“` |
| Polish dialogue marks | `„Lian wraca.”` |
| French dialogue with narrow nonbreaking spaces | `« Iñés entre. »` |
| Lexical apostrophes | `Meiʼs`, `Hawaiʻi` |

These are punctuation examples, not full language-coverage claims. Content locale chooses
the convention; the font neither rewrites quotation marks nor decides linguistic spelling.

## Web delivery

Each style still has three WOFF2 subsets and the full WOFF2/OTF. Latin extended now
contains all 95 Latin-basic codepoints, the existing accented letters, seventeen marks,
dotted circle, and ordinary prose punctuation: 203 encoded codepoints. Symbols/icons
contains the other 104 codepoints. The full font has 307 codepoints and 323 glyphs.

The overlap is intentional. A base letter and its combining accent must be available in
the same face for OpenType attachment. Splitting plain letters, accents, and dialogue marks
among separate faces also loses some word/punctuation kerning. `fonts.css` declares Latin
extended last for each style so it is the preferred face for ordinary Latin prose. Keep the
generated order and all three files. Latin basic remains usable as a deliberate standalone
ASCII delivery, but is not the first face used by the generated stylesheet.

Regular's Latin extended is 25,524 bytes; symbols/icons is 13,728 bytes. Their combined
39,252 bytes exceed the full WOFF2's 36,932 bytes. Choose delivery using the chapter's real
character inventory and font-loading measurements. Full WOFF2 is a simple option for
prose with frequent system icons/fractions. Both deliveries preserve optional numeric features.

## Validation and limits

- Ten full styles and thirty WOFF2 subsets rebuilt and autohinted.
- `verify_latin.py`: all 295 old outlines and metrics, old cmap entries and pair values,
  nominal settings, vertical metrics, and hinting values match preserved 0.32. Existing
  prose/numeric shaping also matches with kerning and joins enabled/disabled.
- Existing canonical accented text has equivalent NFC/NFD shaping. New base+mark cases
  verify attachment, independent stacks, dotless forms, ligature components, zero advances,
  reserved clipping bounds, actual contour separation, and equivalent subset shaping.
- `verify_phase2.py` passes optional figures/fractions and all thirty subset ranges.
- FontBakery OpenType: 287 PASS / 171 SKIP / 0 FAIL / 0 WARN. Offline universal:
  705 PASS / 427 SKIP / 30 INFO / 0 FAIL / 0 WARN. Network checks remain unverified.
- Native Windows WPF Day/Night proofs cover 13/15/17px Light/Regular/Medium and all five
  weights at 20px, upright and italic. The renderer now follows WPF's positive-up vertical
  offsets. The 20px Latin proof uses 1.5 leading to separate its stacked-capital lines.
  Baseline 0.32's missing new glyphs appear as boxes in this renderer.

The comparison keeps the same four cards and all previous reading samples/controls.
The Lab includes live cluster drawing, the foundation row, and every new visible character.
The three-chapter page and its saved feedback are unchanged. Browser automation could
not connect in this session; physical browser/device and sustained-reading results are
deferred at the user's request. Native WPF evidence is separate from those checks.

Complete additional encoded alphabets come next. Missing precomposed codepoints can
trigger browser fallback even when their decomposed components shape successfully. Do
not claim new language coverage by converting all app text to NFD. This foundation tests
representative one/two above marks and one below mark; arbitrary stacks can exceed any
fixed vertical window. Compare 1.4/1.5 leading for passages with many stacked capitals.

Technical references: [OpenType GPOS attachment](https://learn.microsoft.com/en-us/typography/opentype/spec/gpos),
[canonical composition (`ccmp`)](https://learn.microsoft.com/en-us/typography/opentype/spec/features_ae#ccmp),
and [Unicode locale character/quotation data](https://unicode.org/reports/tr35/tr35-general.html#Character_Elements).
