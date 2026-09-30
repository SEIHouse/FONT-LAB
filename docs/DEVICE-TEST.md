# SEIReader device test

Use [the reading test](../lab/reading-test.html) for sustained reading and [the Lab](../lab/index.html) for isolated characters. Open the files through the same delivery method the app will use, with the SEIReader WOFF2 files available. Record the browser and OS versions, device, screen scale, font file or subset delivery, and date. A pass means the face is legible and consistent at normal zoom without fallback, clipping, or unexpected shifts. Mark an item **Fail** and describe the exact text, size, theme, and screenshot when it differs. Leave untested items blank; this document is a test plan, not a record of completed device tests.

## Test sessions

| Device / browser | Device, OS and browser version | Date / tester | Delivery (full or subsets) | Overall |
|---|---|---|---|---|
| iPhone / Safari | | | | ☐ Pass ☐ Fail |
| Android / Chrome | | | | ☐ Pass ☐ Fail |
| Windows / Chrome | | | | ☐ Pass ☐ Fail |
| Windows / Edge | | | | ☐ Pass ☐ Fail |
| Mac / Safari | | | | ☐ Pass ☐ Fail |
| Mac / Chrome | | | | ☐ Pass ☐ Fail |

## Run on every device and browser above

Record **P** (pass), **F** (fail), or **—** (not run) in each session column. Use 100% browser zoom, normal display scaling, and a loaded web font. Repeat a failed item at normal and increased text size to distinguish a font issue from a browser zoom issue. Check Light (300) in the comments sample as well as the reading weight selected for the chapter.

| Check | iPhone Safari | Android Chrome | Win Chrome | Win Edge | Mac Safari | Mac Chrome |
|---|---|---|---|---|---|---|
| 13px: sharp, open counters; no broken strokes or merged letters | | | | | | |
| 15px: sharp, open counters; no uneven stems or blur | | | | | | |
| 17px: sharp, comfortable punctuation and accents | | | | | | |
| 20px: sustained chapter text stays clear | | | | | | |
| Night: body, italics, accents and symbols remain clear on dark background | | | | | | |
| Day: same checks on light background; no halo or low contrast | | | | | | |
| Light (300) in comments: readable in both themes, including punctuation | | | | | | |
| Real italics: visible distinction; no clipping or synthetic slant | | | | | | |
| `fi` and `fl`: joins form cleanly, remain readable, and do not collide with neighbors | | | | | | |
| Kerning: `To`, `AV`, `P.`, `“A` look balanced, with no collision or obvious gap | | | | | | |
| Tall lowercase `l b d h k f` align with caps in `Hlbdfk` | | | | | | |
| Accents: `Áurea`, `Éloi`, `Iñés`, `João`, `Müller`, `Søren`, `Þóra` render and clear preceding lines | | | | | | |
| Common symbols/icons `☯ ⚡ ▲ ♥ Ⓢ` match SEIReader strokes rather than color emoji | | | | | | |
| Same symbols with `font-variant-emoji: text` still use SEIReader | | | | | | |
| Private icons U+E000–E00F all render as the intended monochrome SEIReader icons | | | | | | |
| No missing glyph boxes or color emoji in chapter system messages and comments | | | | | | |
| Line height stays consistent through accents, italics, system messages and icon lines | | | | | | |
| No horizontal scrolling, clipped controls, or covered feedback fields in portrait/narrow view | | | | | | |

## How to inspect the glyph cases

1. In the reading page's quick glyph check, compare the 13/15/17/20px samples at the same weight in Day and Night. Include the Light-weight comment. Look at stem edges and small counters, not only whole-word readability.
2. Inspect the italic passage and `office`, `flame`, `affinity`, `reflection` for `fi`/`fl`; inspect `To AV P. “A` at normal reading size. Compare `Hlbdfk` against the capital height.
3. Read accented names in each chapter and inspect the language and every-character sections in the Lab. Check for displaced marks and line collisions.
4. Compare the two labeled symbol lines in the reading page's quick glyph check. The first has normal emoji CSS; the second uses `font-variant-emoji: text`. Both include `☯ ⚡ ▲ ♥ Ⓢ` and U+E000–E00F (the private codes bypass phone emoji substitution). Confirm the symbols are monochrome, recognizable, and sized with the text. Use the Lab's symbols section for a closer look at any failure.
5. Read at least one full chapter in each theme and selected weight. Note the first line where leading, paragraph spacing, or a symbol changes the apparent line rhythm. Submit its chapter feedback before switching devices.

## Failures and evidence

| Session / item | Exact text and size | Theme / weight / emoji setting | Expected vs observed | Screenshot or issue link | Recheck |
|---|---|---|---|---|---|
| | | | | | |

Keep a device result open until the same browser and delivery method have been retested. The reading page stores feedback only in that browser's local storage; use **Copy All Feedback** to collect one shareable block.
