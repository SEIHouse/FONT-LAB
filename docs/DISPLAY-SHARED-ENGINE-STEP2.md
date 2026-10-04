# Display Engine Step 2: one shared engine

Reader and Display use the root `engine.js` and `font_builder.py`. The forked
`display/engine.js` is deleted. All four Display cuts retain their JSON settings
and version 0.1 while inheriting the current Reader repertoire and layout.

## Shared construction

`make_fonts.py` loads Reader settings and builds the ten upright/italic styles
and their web subsets. `display/make_display.py` loads one cut and builds its
OTF/WOFF2 pair. Both call `FontBuilderCore`; export, metrics, spacing, alternate
construction, mark/local forms, OpenType features and hinting have one owner.
The core keeps build settings and kerning maps on each instance.

The Reader defaults remain soft corners, round ends, round joins and
`penAngle: 0`. Existing true italics retain their letter substitutions and
9-degree slant. Display settings expose `corners: soft|cut`, `ends: round|flat`,
`joins: round|sharp`, `penAngle` and `slant`. Explicit oblique slant shears the
upright letter forms without selecting italic substitutions.

The configured construction retains Step 1's perpendicular flat faces,
attached-terminal handling, miter limit of 2 with bevel fallback, and cleanup
after stroking, slant, fitting and integer rounding. Reader's unchanged default
path keeps the approved 0.35 overlap repair and curve fitting. Both Labs embed
the same root engine; the Display SVG helper supplies the configured pen's
terminal geometry for its live preview.

## Inherited repertoire and features

Each Display cut has 419 glyphs: 383 encoded engine entries, 34 unencoded
alternates, `.notdef` and space. Unicode and private-use aliases reuse existing
glyph IDs. The 17 combining marks keep zero advances, mark classification and
attachment; dotless forms support above accents without retaining the dots of
`i` and `j`.

The common layout includes canonical composition (`ccmp`), base and ligature
mark attachment (`mark`), stacked marks (`mkmk`), Turkish dotted-i and Romanian
comma forms (`locl`), and Hungarian capital digraph spacing. It also includes
fractions (`frac`), tabular figures (`tnum`), superscripts (`sups`), subscripts
(`subs`), and decimal period/comma spacing in proportional and tabular modes.

The Display audit shapes the ten pinned CLDR Latin inventories in
`languages.json`: Polish, Czech, Hungarian, Romanian, Turkish, Hausa, Kurdish
(Kurmanji, Latin), Māori, Igbo and Uzbek (Latin). It also checks the established
Latin foundation samples for English, Spanish, French, Portuguese, German,
Italian, Dutch, Catalan, Danish, Norwegian, Swedish, Finnish and Icelandic.
That is 23 language samples/inventories in this verification, with the same
encoded repertoire as Reader. Coverage and shaping checks do not constitute
native-reader certification.

## Display metrics inherited from Reader

Retiring the 0.25 fork also adopts Reader's existing 0.28 width and bearing
refinements. Twenty previously encoded glyph advances change in each cut:
`a` and its six accents, `e` and its four accents, `i` and its four accents,
`æ`, `œ` and `ﬁ`. These changes come from the inherited Reader construction;
cut JSON remains unchanged. Every other previous advance, every previous encoded
mapping and the vertical metrics are retained.

The table gives advance changes in font units at the 2,000-unit em. Cut width
scales the inherited `a`/`e` changes; the `i`/`ﬁ` bearing increase is 24 units.

| Glyph group | Glyphs | Soft | Edge | Ink | Wide |
|---|---:|---:|---:|---:|---:|
| `a à á â ã ä å` | 7 | −52 | −50 | −45 | −70 |
| `e è é ê ë` | 5 | −46 | −44 | −40 | −62 |
| `i ì í î ï` | 5 | +24 | +24 | +24 | +24 |
| `æ œ` | 2 | −46 | −44 | −40 | −62 |
| `ﬁ` | 1 | +24 | +24 | +24 | +24 |

[`display-step2-design.json`](../tests/fixtures/display-step2-design.json)
freezes all 419 current advances per cut and records the before/after value and
source reason for each of the twenty inherited changes. The design gate
requires those exact values, the original controls and aliases, the unchanged
vertical metrics, and Reader's unchanged shared skeleton source.

## Reader preservation and the byte-identity reason

The preservation baseline is commit
`bc61d90d25730f7768b92f51e190221045810e9a`, the current 0.36 release. Version
0.36 changed 0.35 family/licensing metadata; its geometry, metrics, hints and
layout retain 0.35. Keeping that current metadata avoids reverting the
SEIHouse Sans name or license as part of this engine change.

`tests/fixtures/reader-engine-0.35.json` fingerprints the complete engine
exports for all ten styles before consolidation: encoded glyphs, alternates,
kerning, base mappings and screen stroke weights. The Node regression compares
the shared engine's exports to that frozen fixture and requires exact equality.
It also checks option-sensitive glyph caching and oblique slant without
italic substitutions.

`tests/fixtures/reader-0.36-identity.json` fingerprints all 50 current font
deliveries: ten full OTFs, ten full WOFF2 files and thirty subsets.
`verify_shared_engine.py` compares every SFNT table, including the complete
CFF outline and hint programs, metrics, names and layout. Only
`head.created`, `head.modified` and `head.checkSumAdjustment` are normalized.
Rebuilding stamps new creation/modification times and consequently a new file
checksum; those bookkeeping values are the written reason for accepting
outline/metric identity instead of requiring whole-file byte identity.
No design, hint, name or layout field is omitted from the comparison.

The rebuilt delivery audit is recorded separately in
[reader-rebuilt.json](proofs/display-step2/reader-rebuilt.json). All 50 rebuilt
deliveries have identical normalized tables and CFF outline/hint programs,
and all 50 match the preserved 0.35 geometry, metrics and layout, with zero
preservation flags. The checked-in
Reader binaries are retained from the baseline, so shipping this refactor does
not change the existing Reader asset bytes; the rebuild audit proves that the
new core reproduces their contents apart from the timestamp bookkeeping above.

The optional `--reader-baseline` argument additionally compares the preserved
0.35 font directory's CFF programs, metrics and layout directly. The 0.35
reference used locally is an ignored build baseline, while the checked-in
fingerprints make the current-release preservation gate reproducible in CI.

## Evidence and historical proofs

Step 1's [construction report](DISPLAY-SHAPES-STEP1.md) and
[`proofs/display-step1/`](proofs/display-step1/after.json) remain frozen. They
describe the earlier 241-glyph cut builds: 964 outlines and 1,928 OTF/WOFF2
renders, with 474 baseline outline events reduced to zero.

Step 2's expanded builds have a fresh shape report and fresh proofs. The
shape thresholds remain the Step 1 thresholds at a 400px em, with every glyph
ID rasterized in both formats. The design gate retains the original cut JSON,
encoded mappings and vertical metrics while permitting inherited Reader
additions and the twenty documented advance refinements above. It freezes
every current advance and fingerprints the unchanged shared Reader skeleton
source because the old Display fork has been deleted.

The [shape report](proofs/display-step2/shapes.json) records **zero flags** for
all 1,676 glyph outlines and 3,352 OTF/WOFF2 renders. Both formats agree on
outlines, metrics, layout and raster output. The
[shared-engine report](proofs/display-step2/shared-engine.json) records zero
preservation/feature flags, all 50 shipped Reader files byte-identical to the
baseline, and 1,842 language shaping strings per cut across the 23 tested
language inventories/samples. Mark attachment/stacking, local forms, numeric
substitutions, feature ordering and decimal spacing pass the behavior checks.

FontBakery 1.1.0 checked every cut separately with no excluded check IDs. Each
Universal run used `--skip-network` and reported 75 PASS / 3 INFO / 49 SKIP;
each OpenType run reported 31 PASS / 22 SKIP. All four cuts have **0 FAIL /
0 WARN / 0 ERROR / 0 FATAL**. The
[FontBakery summary](proofs/display-step2/fontbakery.json) and shape report
identify the same final OTF hashes.

| Cut | Glyphs | OTF + WOFF2 renders | Shape flags | Universal PASS | OpenType PASS |
|---|---:|---:|---:|---:|---:|
| Soft | 419 | 838 | 0 | 75 | 31 |
| Edge | 419 | 838 | 0 | 75 | 31 |
| Ink | 419 | 838 | 0 | 75 | 31 |
| Wide | 419 | 838 | 0 | 75 | 31 |
| Total | 1,676 | 3,352 | 0 | 300 | 124 |

GitHub Actions also rebuilds all ten Reader styles and all four Display cuts
with the shared core, then gates the candidates against the frozen Reader
tables, inherited features and shape thresholds. The rebuild uses Windows
and the baseline tool versions for exact CFF/hint reproducibility; a separate
Linux job checks shipped fonts and construction regressions.

The final construction and preservation regressions pass: 24 Python tests and
20 Node tests. The existing Reader figure/subset, repaired-stroke, language,
license and distribution audits also pass. These checks protect the default
Reader path as well as the new option behavior.

The [Chromium Lab report](proofs/display-step2/lab.json) records all 383 encoded
engine entries at 300/400/800px in every live cut: 1,149 SVG instances per cut.
It also checks all preset buttons and the 390px layout, with zero page errors.
The separate Node regression constructs all 417 encoded/alternate live
drawings per cut and checks finite geometry.

Each proof sheet keeps the 400px em and paginates every glyph ID. The compact
comparisons use the original 0.1 fonts beside the final shared-engine builds;
the earlier Step 1 comparison remains available in its historical report.

![Ink original 0.1 and shared engine: R a y W k e s](proofs/display-step2/ink-before-after.png)

![Edge original 0.1 and shared engine: K R](proofs/display-step2/edge-before-after.png)

| Cut | Final 400px glyph sheets | Live 400px specimen |
|---|---|---|
| Soft | [1](proofs/display-step2/after/soft-01.png), [2](proofs/display-step2/after/soft-02.png), [3](proofs/display-step2/after/soft-03.png), [4](proofs/display-step2/after/soft-04.png), [5](proofs/display-step2/after/soft-05.png), [6](proofs/display-step2/after/soft-06.png), [7](proofs/display-step2/after/soft-07.png) | [Soft](proofs/display-step2/lab-soft-400.png) |
| Edge | [1](proofs/display-step2/after/edge-01.png), [2](proofs/display-step2/after/edge-02.png), [3](proofs/display-step2/after/edge-03.png), [4](proofs/display-step2/after/edge-04.png), [5](proofs/display-step2/after/edge-05.png), [6](proofs/display-step2/after/edge-06.png), [7](proofs/display-step2/after/edge-07.png) | [Edge](proofs/display-step2/lab-edge-400.png) |
| Ink | [1](proofs/display-step2/after/ink-01.png), [2](proofs/display-step2/after/ink-02.png), [3](proofs/display-step2/after/ink-03.png), [4](proofs/display-step2/after/ink-04.png), [5](proofs/display-step2/after/ink-05.png), [6](proofs/display-step2/after/ink-06.png), [7](proofs/display-step2/after/ink-07.png) | [Ink](proofs/display-step2/lab-ink-400.png) |
| Wide | [1](proofs/display-step2/after/wide-01.png), [2](proofs/display-step2/after/wide-02.png), [3](proofs/display-step2/after/wide-03.png), [4](proofs/display-step2/after/wide-04.png), [5](proofs/display-step2/after/wide-05.png), [6](proofs/display-step2/after/wide-06.png), [7](proofs/display-step2/after/wide-07.png) | [Wide](proofs/display-step2/lab-wide-400.png) |

## Reproduce

With `requirements.txt` installed, Playwright Chromium available and
`otfautohint` in the Python environment, run from the repository root:

```powershell
python -X utf8 make_fonts.py
foreach ($cut in 'soft','edge','ink','wide') {
  python -X utf8 display/make_display.py "display/cuts/$cut.json"
}
python -X utf8 display/build_display_page.py
node --test tests/shared-engine.test.mjs tests/display-strokes.test.mjs tests/site.test.mjs
python -X utf8 -m unittest discover -s tests -p test_display_shapes.py -v
python -X utf8 -m unittest discover -s tests -p test_shared_engine.py -v
python -X utf8 verify_shared_engine.py --report dist/shared-engine.json
python -X utf8 verify_display_shapes.py --proof-dir dist/display-step2-proofs --report dist/display-shapes.json
foreach ($cut in 'Soft','Edge','Ink','Wide') {
  $font = "display/fonts/$($cut.ToLower())/SEIHouseDisplay-$cut.otf"
  fontbakery check-universal --skip-network -n -C -e WARN $font
  fontbakery check-opentype -n -C -e WARN $font
}
```

To inspect the live Display Lab, serve the repository with
`python -m http.server 8766 --bind 127.0.0.1`, then run
`python -X utf8 display/verify_lab.py --proof-dir dist/display-lab-proofs` in
another terminal.
