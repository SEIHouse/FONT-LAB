# Display fixes before Step 5

All four rebuilt presets now use plain W/w, carry the Reader's ecosystem license
metadata, fit phone viewports and include six web subsets. Cut version 0.1 and
all other cut settings remain unchanged. Crossed uppercase W stays available
through `ss04`, which also switches M; lowercase w remains plain in either mode.
The Lab identifies Plain W as the preset default and Crossed W as the optional
set design. Explicit saved design choices continue to load and save.

## Current specimens

The native title sheets compare each built WOFF2 row with the matching Lab SVG,
including plain W/w defaults, `ss04` with crossed W, accented forms and titles.
The phone sheets show each preset at a 390px viewport.

| Cut | Native font and Lab | Phone Lab | Latin-basic bytes |
|---|---|---|---:|
| Soft | [Letters and titles](proofs/display-pre-step5/soft-alternates-titles.png) | [390px](proofs/display-pre-step5/lab-soft-390.png) | 22,156 |
| Edge | [Letters and titles](proofs/display-pre-step5/edge-alternates-titles.png) | [390px](proofs/display-pre-step5/lab-edge-390.png) | 17,264 |
| Ink | [Letters and titles](proofs/display-pre-step5/ink-alternates-titles.png) | [390px](proofs/display-pre-step5/lab-ink-390.png) | 22,416 |
| Wide | [Letters and titles](proofs/display-pre-step5/wide-alternates-titles.png) | [390px](proofs/display-pre-step5/lab-wide-390.png) | 22,140 |

Edge and Ink already contained approved plain W and W-circumflex outlines as
alternates. This change makes those forms their defaults and moves the crossed
forms into the unencoded `ss04` glyphs. Soft and Wide already defaulted to plain
W. The topology fixture rekeys only the two default/alternate pairs in Edge and
Ink, copying their existing counter counts and white-space witnesses exactly.
No other topology record is measured again or changed; the original Step 1/2
metrics and Step 3 outline fingerprints remain frozen. The fixture records the
authorized default revision separately from its original Step 4 provenance.

## Embedded license

The Display branch of `FontBuilderCore` previously stripped the shared legal
records and left only an owner string. It now retains the exact Reader records:

| Name ID | Record |
|---:|---|
| 0 | Copyright 2026 SEIHouse Productions LLC; rights subject to the license |
| 7 | Reader's family-name/trademark notice; no registration claimed |
| 8, 9 | Manufacturer and designer: SEIHouse Productions LLC |
| 11, 12 | Reader's project/vendor and designer URLs |
| 13 | SEIHouse Sans Ecosystem License 1.0 description and terms URL |
| 14 | Reader's license URL |

The gate compares every platform/language record to the actual Reader font,
including the existing project URL spelling. It also requires `fsType=0` and
vendor `SEIH`. All 32 Display font files pass, while Display family/style names
remain distinct. [LICENSE](../LICENSE) contains the operative terms.

## Web subsets and phone layout

Every cut build produces `latin-basic`, `latin-extended`, `cyrillic`, `greek`,
`vietnamese` and `symbols` WOFF2 siblings, plus the shared
[`display/fonts.css`](../display/fonts.css). Reader's atomic subset writer keeps
all applicable layout features and name records. Display also retains the
`.notdef` outline. Its extended delivery combines the Reader's historical Latin
faces into one complete repertoire. Script faces retain surrounding Latin,
punctuation and combining marks so text can shape as a complete run.

The stylesheet uses each actual cut family at weight 400, normal style, and exact
`unicode-range` values from the subset cmap. As in Reader, later matching script
faces take priority over overlapping Latin ranges. For a basic-Latin-only project
needing a single small request, use that cut's Latin-basic face block alone.
The gate enforces a strict **25,000-byte** Latin-basic limit for every cut.
The public website includes the stylesheet and all 24 subset files.

The old Lab's document was 580px wide at a 390px viewport. A
[baseline run](proofs/display-pre-step5/mobile-before.json) proves the new gate
rejects it. The fix bounds grid tracks, controls and SVG words instead of hiding
horizontal page overflow. Long unbroken SVG words scale proportionally to their
container; their viewBox, glyph outlines and compiled spacing stay intact.
The gate checks both document widths and visible element bounds at 360, 375,
390, 414 and 430px for every preset, with ordinary titles, long titles and
crossed W plus `cpsp`: **60 layouts, zero overflow flags or page errors**.

## Validation

- [Shape gate](proofs/display-pre-step5/shapes.json): 3,268 full-font outlines and
  6,536 OTF/WOFF2 renders at 400px; zero flags, including every stylistic design.
- [Previous-cut preservation](proofs/display-pre-step5/preservation.json): all
  3,268 prior outlines and complete horizontal metrics remain exact under the
  explicit Edge/Ink default/alternate W swaps; zero flags.
- [Shared engine](proofs/display-pre-step5/shared-engine.json): all 90 Reader
  deliveries remain byte-identical; each Display cut passes 3,339 shaping strings
  across 34 languages. The ten Reader styles retain original 0.35 outlines/metrics.
- [Reader subset rebuild](proofs/display-pre-step5/reader-subsets.json): all 70
  subsets rebuilt with the factored shared writer remain byte-identical.
- [License/subsets](proofs/display-pre-step5/subsets-license.json): 32 licensed
  files, 24 subsets, exact retained outlines/metrics and CSS coverage, and 48,724
  native language/feature comparisons; zero flags. Canonical comparisons require
  the text and its NFC form to be covered by the selected subset.
- [Built-site web CSS](proofs/display-pre-step5/web.json): 120 actual browser
  widths across four cuts, ten Latin/script/mark/numeric/symbol samples and three
  feature modes match the full WOFF2 exactly; zero page errors or flags.
- [Alternate spacing](proofs/display-pre-step5/alternates.json): 1,920 Lab DOM/native
  font width comparisons, eleven controls per cut and Save/Download/Reload; zero
  flags, with maximum width difference 0.0361% against the strict 0.5% limit.
- [Existing title spacing](proofs/display-pre-step5/spacing.json): 888 comparisons,
  maximum difference 0.0647%; zero flags.
- [Live Lab](proofs/display-pre-step5/lab.json): 8,352 glyph instances at
  300/400/800px and all 60 phone layouts; zero flags.
- [FontBakery 1.1.0](proofs/display-pre-step5/fontbakery.json): each full cut passes
  OpenType (31 PASS, 22 SKIP) and offline Universal (75 PASS, 3 INFO, 49 SKIP), with
  **0 FAIL / 0 WARN / 0 ERROR / 0 FATAL**. Network checks are skipped.
- 73 Python tests, 29 Node tests, whitespace checks and the 62-file public website
  build pass. CI gates checked-in and fresh Display deliveries, rebuilt Reader
  identity, subset/license/CSS parity, mobile layout and per-cut FontBakery.

From the repo root:

```powershell
foreach ($cut in 'soft','edge','ink','wide') {
  python -X utf8 display/make_display.py "display/cuts/$cut.json"
}
python -X utf8 display/build_display_page.py
python -X utf8 verify_shared_engine.py
python -X utf8 verify_display_shapes.py
python -X utf8 verify_display_spacing.py
python -X utf8 verify_display_alternates.py
python -X utf8 verify_display_subsets.py
python -X utf8 display/verify_lab.py
```
