# SEIReader 0.34: the first Latin language batch

Multilingual Phase 2 completes ten Latin alphabet inventories from the reader app's
glossary locales. It adds 94 encoded letters and two unencoded language/mark alternates,
while retaining all 323 glyph outlines and metrics from 0.33, every approved old pair
value, and all design settings except the version. The family remains five weights,
each with its real italic. No global spacing or weight changes are part of this phase.

## What is covered

The audit uses **CLDR 48 main, auxiliary, and index exemplars**, their uppercase,
lowercase/titlecase variants, and NFC/NFD forms. Auxiliary exemplars include letters
used in foreign names and borrowed words. Digraphs remain ordinary text sequences;
they are not forced into decorative ligatures.

| Locale | Alphabet scope | Notable additions / cases |
|---|---|---|
| `pl` | Polish | `Ąą Ćć Ęę Łł Ńń Śś Źź Żż`; connected ogoneks have their own punctuation clearance |
| `cs` | Czech | `Čč Ďď Ěě Ňň Řř Šš Ťť Ůů Žž`; auxiliary `Ľľ Ŕŕ Łł` and macron/breve vowels |
| `hu` | Hungarian | `Őő Űű`, with clearly paired acute strokes; ordinary digraph spelling is retained |
| `ro` | Romanian | `Ăă Șș Țț`; legacy `Şş Ţţ` display as comma forms only for Romanian text |
| `tr` | Turkish | `Ğğ İ ı Şş`, with separate dotted/dotless letters and a visible dot in `fi` words |
| `ha` | Hausa (Latin/Boko) | Dedicated `ƁƊƘƳ ɓɗƙƴ` hooks, lexical `ʼ`, and auxiliary `r̃` |
| `ku-Latn` | Kurdish: Kurmanji in Latin script | `Şş`, alongside existing `Çç Êê Îî Ûû` and auxiliary vowels |
| `mi` | Māori | `Āā Ēē Īī Ōō Ūū`; dot removed under above accents on `i` |
| `ig` | Igbo | `Ịị Ọọ Ụụ Ṅṅ`, tone sequences above dot-below vowels, and auxiliary `Ḿḿ Ńń Ǹǹ` |
| `uz-Latn` | Uzbek in Latin script | `oʻ gʻ ʼ`, regular digraphs, and the completed auxiliary accented-letter inventory |

Kurdish in Arabic script and Uzbek in Cyrillic are separate script deliveries. This
batch's coverage claim is the recorded alphabet inventory and shaping behavior. It
does not certify every spelling tradition, transliteration, specialist symbol, or the
comfort of a native reader on an actual device.

The full font has **401 encoded codepoints / 419 glyphs**. Latin extended contains
**298 codepoints**, including all 95 Latin-basic codepoints, complete tested Latin
clusters, prose punctuation, and the middle-dot word separator `·`. The latter also
remains in symbols/icons, which retains its 104-codepoint inventory.
There are still ten full OTF/WOFF2 styles and thirty WOFF2 subset files.

## Construction and local behavior

- New composed letters use the existing base drawings and the 0.33 lighter combining
  marks. Their positions, stroke weight, contrast, and italic shear follow the engine.
- Czech `ď/ť` and auxiliary `ľ/Ľ` use compact side carons beside their tall stems.
  Their new bearings provide room for the added stroke.
- Polish barred letters and Hausa hooks reuse the family's skeleton and rounded pen.
  New hooked/barred forms have their own advances where their ink needs more room.
- Above marks on Igbo `ị` remove the dot of the underlying `i` while keeping its
  dot-below and advance. Above/below attachment stacks remain independent.
- Standard `locl` behavior reads the text language. Turkish uses an identical dotted
  `i` alternate so `fi` stays separated and readable; `fl` still joins. Other languages
  retain the established `fi/fl` joins. Romanian maps legacy cedillas to comma forms.
- New ogonek/punctuation pairs are measured separately. A comma must not collide
  with a connected tail; all pre-existing letter/punctuation pair values stay intact.
- Hungarian uppercase `TY/TTY` digraphs get extra clearance through a language-specific
  `kern` lookup under `lang="hu"`. Default capital spacing stays exactly as in 0.33.

## Using it in the reader

Use the full family or the generated `fonts.css`; both contain the complete tested
inventories. Preserve the stylesheet's face order so letters, accents, and punctuation
shape in the same Latin extended face. A missing codepoint outside the inventory can
still fall back to another font. Keep the actual chapter text; no blanket NFD rewrite
is needed to obtain this batch's coverage.

```html
<article lang="pl" class="chapter">„Łucja ćwiczy cierpliwość.”</article>
<article lang="tr" class="chapter">İpek · Işık · fikir · fi · fı</article>
<article lang="ro" class="chapter">Ștefan · țară · ş ţ</article>
<article lang="ig" class="chapter">ị́ · ọ̀ · ụ́ · Ị́ · Ọ̀ · Ụ́</article>
<article lang="ku-Latn" class="chapter">çiya · şev · rê</article>
<article lang="uz-Latn" class="chapter">oʻqish · gʻoya</article>
```

```css
@import url('/fonts.css');
.chapter {
  font-family: 'SEIReader', sans-serif;
  font-weight: 400;
  font-synthesis: none;
  font-kerning: normal;
  font-variant-ligatures: common-ligatures;
  font-size: 20px;
  line-height: 1.4;
  max-width: 60ch;
}
```

`locl`, `ccmp`, `mark`, and `mkmk` apply automatically in a shaping-aware browser.
Setting `lang` on the actual passage is necessary for Turkish/Romanian behavior.
Do not globally disable these features. Locale-aware case conversion is the app's
responsibility; a font does not convert or correct stored language text.

## Inspection and evidence

The same four-card [reference preview](../lab/comparison.html) compares 0.34, preserved
0.33, Literata, and Rubik. Its language selector changes only the language rows; all
earlier prose, punctuation, spacing, numeric, and foundation samples remain. New
fixed-size rows cover the alphabets in 13/15/17px Light/Regular/Medium. The Lab has the
new language rows in upright/italic and all 94 additions in Every character.

`verify_languages.py` independently checks the full fonts and Latin extended subsets:
encoded main/auxiliary/index coverage and casing, NFC/NFD shaping, actual local forms,
zero-width marks, contour collisions/clipping, and preservation of 0.33 geometry,
metrics, old prose/numeric shaping, pair values, line metrics, and hint parameters.
`verify_phase2.py` continues to audit figures/fractions and all thirty subset ranges.
`verify_latin.py old/0.33` audits the archived foundation against preserved 0.32.

Native Windows WPF proofs are supplemental rasterization evidence. Browser controls,
physical browser/device results, native-speaker proofreading, and sustained-reading
comfort are separate checks; see [DEVICE-TEST.md](DEVICE-TEST.md). Baseline 0.33 lacks
the new encoded letters, so its corresponding rows may show boxes or browser fallback.

Completed local checks for this build:

- All ten styles pass **18,290 language strings**, with identical Latin extended
  subset shaping. Figures/fractions and all thirty subset deliveries also pass.
- FontBakery 1.1.0 on all ten full OTF files: **0 FAIL / 0 WARN** for OpenType
  (287 PASS, 171 SKIP) and offline universal (705 PASS, 427 SKIP, 30 INFO).
  Network checks remain unverified.
- Independent script checks pass the comparison controls, all ten locale selections,
  and **2,010 Lab word widths** against HarfBuzz. The live drawing check also covers
  newly added accents after a base-letter contrast drawing has been cached.
- The inspected [Day](proofs/0.34/windows-day-96.png) and
  [Night](proofs/0.34/windows-night-96.png) proofs cover 13/15/17px in
  Light/Regular/Medium; [family Day](proofs/0.34/family/windows-day-96.png) and
  [family Night](proofs/0.34/family/windows-night-96.png) cover all weights at 20px.
  Every proof includes real italics. Browser automation could not connect, so these
  results do not establish an actual browser or phone pass.

## Data sources and later work

[languages.json](../languages.json) records the ten official CLDR source URLs, source
SHA-256 hashes, and extracted exemplar strings. [language_coverage.py](../language_coverage.py)
expands that pinned inventory offline. The data is covered by the
[Unicode license](../references/cldr/LICENSE.txt), independently of SEIReader's pending
font license. Source character shapes are original SEIReader rules, not extracted
from the reference fonts or Unicode code charts.

References: [Unicode locale character data](https://unicode.org/reports/tr35/tr35-general.html#Character_Elements),
[CLDR 48 locale sources](https://github.com/unicode-org/cldr/tree/release-48/common/main),
and [OpenType localized forms](https://learn.microsoft.com/en-us/typography/opentype/spec/features_ko#locl).

Later Latin batches can add Vietnamese's full encoded repertoire and the open-vowel,
stroke, and tone letters required by more African languages. Cyrillic, Greek, and
other scripts need separate design/shaping work. No support for those remaining
inventories is implied by this batch.
