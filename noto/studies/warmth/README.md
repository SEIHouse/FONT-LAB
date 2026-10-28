# SEIHouse Noto — Balanced, refinement 01

Owner brief: **a warmer version of Google Noto Sans**, as an original new family.

**Owner choice, 2026-10-28: Balanced (B) is the base.**
The [active design record](../../DESIGN.md) distinguishes that approval from the
new refinement candidate. The app's **Noto test** page opens the refinement beside
the unchanged B. Use **View** to show either version alone or compare both.

The refinement redraws the a/c/e/g/s curves and b/d/p/q bowls, coordinates n/h/m/r/u,
lightens the e/f/t crossbars, aligns flat stems/capitals, and tunes sidebearings and
selected kerning pairs. It preserves the moderate softness and full curves of B.

## View the samples on GitHub

These images open directly on GitHub, including on a phone. No local files or
font installation are needed.

![Balanced refinement compared with original B](proofs/balanced-refinement.png)

[Enlarged letter comparison](proofs/balanced-details.png) ·
[Dark comparison](proofs/balanced-dark.png) ·
[Refinement at phone width](proofs/balanced-mobile.png) ·
[Every encoded glyph](proofs/balanced-glyphs.svg)

The downloadable `SEIHouse-Noto-Warmth-Studies.html` also embeds the comparison fonts
and the reference license for an interactive, offline comparison. GitHub displays
HTML source rather than running this page; use the images above for immediate viewing.

## Interactive study

Open `index.html` through a local web server. Refinement 01 is delivered as
`fonts/SEIHouseNotoBalanced-Regular.otf` and `.woff2` (version 0.002). The original
A/B/C fonts remain byte-for-byte unchanged and are available in `warmth-01.html`.
Their original design parameters were:

| Study | Terminal corner radius | Curve fullness | Width factor |
|---|---:|---:|---:|
| A — Subtle | 3 source units | .545 | 1.000 |
| B — Balanced | 14 source units | .585 | 1.025 |
| C — Pronounced | 29 source units | .625 | 1.050 |

All three use a 74-unit construction stroke on a 1000-unit em. These are exploratory
parameters, not settled rules for other scripts. The source is `build_samples.py`:
independently authored paths, bowls, terminal construction, and spacing. No Sans,
Display, or external font outlines, metrics, anchors, or kerning were imported.
The builder uses generic fontTools and PathOps libraries.

## Scope

Limited Latin samples: upper/lowercase, digits, selected punctuation, and a few
accented letters. The page reports characters outside this repertoire. There are
no Arabic, Indic, East Asian, or other script-support claims, no certified reading
metrics, and no production release. The custom outlines need further refinement
and native/script-specific design studies as the selected direction develops.

## Reference and provenance

`reference/NotoSans-Reference.ttf` is the unchanged Google Noto Sans variable font,
used only by the labeled reference row at weight 400. Its upstream OFL is preserved
in `reference/OFL.txt`. Download URLs are pinned to Google Fonts commit
`9862abc066c9b83bf84c3e8ed1fc2d8d48f9bbf0`; exact source hashes are in
`reference/provenance.json`. The reference file is never opened by the original
font construction functions. Original output hashes and character sets are in
`manifest.json`.

## Rebuild

From the repository root:

```powershell
.\.venv\Scripts\python.exe noto/studies/warmth/build_samples.py
```

Generated assets stay inside this study folder. Existing fonts and release
pipelines are unaffected. No font installation is required to view the page.

## Verification and proof capture

Chromium checks confirm that each study renders with its own custom font, the
controls work, and reading/detail views fit widths of 360, 390, 768, 1024, and
1440 pixels. The standalone HTML loads its embedded fonts without external font
requests. These checks do not establish native iPhone rendering or reading comfort.

Run `node build_site.mjs` and serve `dist/site` on port 8768, then run `verify_browser.js` through Playwright
CLI's `run-code --filename` option. Run `capture_samples.js` afterward to capture
the four screenshots at 2x pixel density under `output/playwright/`; copy those
images into `proofs/` when updating the reviewed samples.

Run `python -m unittest discover -s tests -p "test_noto_*.py"` from the repository
root for approved-base preservation, deterministic rebuild, all-glyph geometry,
counter/baseline checks, shaping, kerning, and reference integrity. The SVG glyph
sheet is drawn from the final OTF in `build_samples.py` rather than from a mock font.

Historical proofs: [first three studies](proofs/noto-warmth-desktop.png) and
[original letter comparison](proofs/noto-warmth-details.png).
