# Display Engine Step 5: production pipeline

The production inventory comes from every `display/cuts/*.json`. One shared
builder makes Regular and any cut-specific extra styles, then writes full
OTF/WOFF2, six subsets, native specimens and a manifest of final byte counts
and SHA-256 hashes. Reader and Display continue to share `engine.js` and
`font_builder.py`; this step adds delivery/style orchestration.

## Building and using a collection

```sh
python -X utf8 display/build_all_cuts.py --output-dir dist/display-production
python -X utf8 display/verify_production.py --manifest dist/display-production/display/production-manifest.json
python -X utf8 display/verify_specimens.py --manifest dist/display-production/display/production-manifest.json
python -m http.server 8000 --directory dist/display-production
```

Open `http://localhost:8000/site/display/index.html`. Keep the bundle's directory
structure when hosting it so specimen font/download links and the web stylesheet
resolve correctly. `display/fonts.css` describes every included style with
actual weight, slope and Unicode coverage.

Default builds contain Soft, Edge, Ink and Wide **Regular only**. Add a
`production` object to an individual JSON to request more styles; the
[Display README](../display/README.md#opt-in-extra-weights-and-oblique) gives
the schema. Extra weights alter only thickness; Oblique adds slant without
italic letter substitutions. Alternate choices, pen, corners, ends, joins and
proportions stay inherited from the cut. Styles have separate output/spacing
directories, so extra builds cannot replace Regular's metrics or the Lab export.
For a separate experiment, copy the JSONs into another directory and pass
`--cuts <directory>` with a separate output bundle. No global extra-style
defaults change the committed cuts.

## Specimens

Each page contains an album cover, track list, poster and alphabet, rendered
from the full built web font. Style choices list only built files. Capital
spacing and `ss01`–`ss08` use native OpenType features. Synthesis is disabled.
The specimen gate compares browser WOFF2 rendering to an independently loaded
OTF reference in the same browser, with separate expected feature settings.
This keeps Windows CFF grid fitting consistent. Raw GPOS, rounded hmtx advances
and native HarfBuzz feature/subset shaping are checked by the production gate;
the existing SVG Lab/HarfBuzz width gate remains independent.

| Cut | Generated page | Native proof |
| --- | --- | --- |
| Soft | [Soft specimen](../site/display/soft/index.html) | [Soft](proofs/display-step5/soft.png) |
| Edge | [Edge specimen](../site/display/edge/index.html) | [Edge](proofs/display-step5/edge.png) |
| Ink | [Ink specimen](../site/display/ink/index.html) | [Ink](proofs/display-step5/ink.png) |
| Wide | [Wide specimen](../site/display/wide/index.html) | [Wide](proofs/display-step5/wide.png) |

## Gates and artifacts

The App distribution Action's Windows job uses the preservation baseline's
pinned build tools, rebuilds Reader and the Display collection, and checks
Reader identity, the rebuilt Lab, and every manifest face. It runs FontBakery
1.1.0 OpenType and offline Universal on each full OTF; WARN/FAIL/ERROR/FATAL
or unfinished results block delivery. Existing Linux jobs also verify committed
fonts, construction regressions, the website and Reader app packaging.

Automatic and manual builds honor individual cut settings. On
success, `seihouse-display-fonts` contains fonts/subsets, CSS, manifest,
specimens and the operative license files. `shared-builder-evidence` contains
reports and FontBakery logs, including failures. Artifacts are retained 30 days.

All styles reuse Reader's SEIHouse Sans Ecosystem License 1.0 metadata: name
IDs 0/7/8/9/11/12/13/14, `fsType=0` and vendor `SEIH`. No license text or
permissions change in this phase.

Regular's immutable design/advance/line-metric and fixed topology-witness
checks remain intact. Thickness and slant alter raster coordinates, so each
optional face has a separately reviewed fixed 400px topology fixture, keyed
to its exact drawing settings and alternate inventory. A changed recipe or
new cut requires review before it can pass. The gate never captures or updates
these fixtures. Every glyph also passes contour/segment/spike/overlap checks,
6px counter/aperture clearance, and OTF/WOFF2 raster parity at 400px.

## Reviewed opt-in examples

The JSONs in [opt-in-cuts](proofs/display-step5/opt-in-cuts/) keep the four
committed defaults intact. Soft, Edge and Wide add 9° Oblique; Ink adds 3°
(11° total). Wide also includes Light at 0.85× thickness and Bold at 1.03×.
Ink's larger trial angle pinched the sharp-s aperture below the 6px gate;
the smaller angle preserves clearance. These recipes demonstrate opt-in
support; arbitrary multipliers and angles still require their own shape review.

```sh
python -X utf8 display/build_all_cuts.py --cuts docs/proofs/display-step5/opt-in-cuts --output-dir dist/display-opt-in
python -X utf8 display/verify_production.py --manifest dist/display-opt-in/display/production-manifest.json
python -X utf8 display/verify_specimens.py --manifest dist/display-opt-in/display/production-manifest.json
```

The [style proofs](proofs/display-step5/styles/) show the reviewed defaults,
counter-sensitive letters, non-Latin forms and core stylistic alternatives.
Six fixtures in `tests/fixtures/display-production-topology/` preserve the
reviewed optional faces' 675 letter/number/alternate topology records each.

## Validation

The checked-in Regular specimen collection passes **96 native title-width
comparisons and 60 phone layouts** at 360, 375, 390, 414 and 430px. Native OTF
and WOFF2 title widths match exactly. Production and optional-style reports
are recorded alongside these proofs.

The ten-face opt-in collection passes **240 native width comparisons and 150
phone layouts**, also with exact OTF/WOFF2 width agreement. The rebuilt SVG Lab
passes 888 title measurements (maximum difference **0.0647%**, below 0.5%),
1,920 alternate measurements, 8,352 glyph instances and 60 phone layouts.

All 90 committed Reader deliveries remain byte-identical. Fresh builds of all
ten Reader styles (20 full OTF/WOFF2 files) match every normalized SFNT table,
including complete CFF outlines/hints, names, metrics and layout. The written
normalization reason is build-time `head.created`, `head.modified` and the
resulting `head.checkSumAdjustment`; no drawing or metric exception is used.
All 32 freshly built Regular Display deliveries likewise retain their
normalized tables. The production regressions pass **83 Python tests and 33
Node tests**; the website builds 74 public assets and passes the native specimen
gate from its assembled output.

The fresh ten-face production gate checks **8,170 glyphs and 16,340 renders**,
with zero flags. All four cut families pass FontBakery OpenType and offline
Universal with **0 FAIL / 0 WARN / 0 ERROR**. Latin-basic ranges up to **23,372
bytes**, below the 25,000-byte limit. The compact
[validation report](proofs/display-step5/validation.json) records cut/style
counts, profile results, native widths, Lab parity and Reader preservation.
