# Display Engine Step 3: title spacing

Display now measures capital-height title spacing separately from Reader's small
text spacing. All four cuts retain their design JSON, version 0.1, glyph drawings,
hint programs, advances and vertical metrics. Only their GPOS positioning table
changes. Reader's ninety delivered files remain byte-identical to 0.39.

## Cut-specific measurements

`display/title_spacing.py` owns Display's optical policy inside the existing
`FontBuilderCore`. A capital pass samples the 700-unit capital construction;
the mixed-case pass samples each cut's lowercase height. Both measure the empty
space between actual expanded outlines, including Ink's angled pen and oblique
slant. `HH` and `nn` supply the cut's reference rhythm and retain zero adjustment.
Open sides have a bounded optical depth. Closest-ink measurements limit tightening.

The four policies vary correction strength, open-side depth and minimum ink room
for the heavy round, angular flat, calligraphic and thin wide geometries. Policy
selection uses cut settings rather than its name: renaming a design retains its
spacing. This replaces Reader's automatic letter-pair assumptions and paragraph
correction pass for Display only. Mark/script clearance and explicit `pairSpace`
settings still run in the shared core.

Examples below are **source units per 1,000-unit em**, read independently from
HarfBuzz shaping before and after the change. Negative adjustments tighten the pair.
The complete requested-pair table is in [preservation.json](proofs/display-step3/preservation.json).

| Pair | Soft before → after | Edge before → after | Ink before → after | Wide before → after |
|---|---:|---:|---:|---:|
| LA | −42 → −47 | −43 → −64 | −44 → −50 | −51 → −111 |
| LY | −46 → −241 | −47 → −208 | −91 → −255 | −54 → −320 |
| TA | −30 → −194 | −32 → −167 | +20 → −101 | −40 → −319 |
| AV | −27 → −141 | −25 → −118 | −61 → −107 | −37 → −214 |
| RT | −34 → −137 | −41 → −160 | −57 → −111 | −43 → −217 |

## Capital spacing

Each cut includes the standard [`cpsp` capital-spacing feature](https://learn.microsoft.com/en-us/typography/opentype/spec/features_ae#tag-cpsp).
It adds room to capitals without changing their default hmtx advances. A GPOS
single adjustment places half the extra room on each side, with mark glyphs
ignored. Accented Latin, Greek and Cyrillic capitals receive the same adjustment;
lowercase, figures and combining marks receive none. It adds to normal kerning.

| Cut | Extra advance per capital | Extra advance in 2,000-unit font |
|---|---:|---:|
| Soft | 0.021 em | 42 units |
| Edge | 0.025 em | 50 units |
| Ink | 0.023 em | 46 units |
| Wide | 0.031 em | 62 units |

The extra amount is measured from each cut's `HH` rhythm, rather than inherited
from Reader. Enable **Capital spacing (cpsp)** in the Lab to preview it. For web
titles use `font-kerning: normal; font-feature-settings: "cpsp" 1;` with the cut's
font family. The feature is available separately from the default kerning pass.

## The Lab uses the final font spacing

Every Display build writes `spacing_<cut>.json` beside its spacing metadata.
The export reads final rounded hmtx advances and GPOS kerning from the finished
OTF. It retains compact class lookups, explicit zero exceptions, lookup order
and extension lookups. The Lab applies these values to its live SVG drawings,
including capital feature advances and placements. Canonical mark composition
precedes fi/fl ligatures; ordinary, thin, narrow no-break and repeated spaces
retain their own font advances.

The Lab generator verifies that each export matches both the preset settings
and the OTF hash. Geometry or spacing edits invalidate compiled spacing in the
live Lab; the draft remains editable and receives a visible draft-spacing label.
Rebuild that cut and then the Lab to supply its final spacing. Naming and note
edits do not invalidate it.
For a custom design, save its downloaded settings in `display/cuts/<slug>.json`
so the generator includes that cut and its compiled export. Build that JSON,
then rebuild the Lab. Names containing spaces use the same asset paths as the
font builder.

## Gates and proofs

[spacing.json](proofs/display-step3/spacing.json) records **888 actual DOM width
measurements**: 37 title/pair samples, four cuts, three sizes (48/96/192px), with
`cpsp` off and on. HarfBuzz independently shapes both OTF and decompressed WOFF2
fonts. The gate fails at a width difference of **0.5% or greater**.

| Cut | Measurements | Maximum Lab/font width difference |
|---|---:|---:|
| Soft | 222 | 0.0388% |
| Edge | 222 | 0.0365% |
| Ink | 222 | 0.0647% |
| Wide | 222 | 0.0334% |

There are zero width, feature, web-shaping or page-error flags. The sample set
includes every requested title pair, all-caps/mixed-case titles, fi/fl words,
canonical accents, Vietnamese, Greek, Cyrillic, decimal figures and special
spaces. The [preservation report](proofs/display-step3/preservation.json) compares
the fonts with commit `69b649433661166d143705cf43e64b2b96227d1a`: GPOS is the only
changed normalized table in every cut. Complete CFF programs/hints also match.
The [shape report](proofs/display-step3/shapes.json) retains Step 1's thresholds,
with zero flags across 2,928 glyphs and 5,856 OTF/WOFF2 renders at 400px.
The [FontBakery OpenType report](proofs/display-step3/fontbakery.json) records
31 PASS, 22 SKIP and zero FAIL/WARN per cut.

Each proof shows actual before/after fonts at 64px, kerning plus capital spacing,
and the corresponding live Lab SVG. Font shapes are the same throughout.

| Cut | All-caps proof | Mixed-case proof |
|---|---|---|
| Soft | [Before/after titles](proofs/display-step3/soft-all-caps.png) | [Before/after titles](proofs/display-step3/soft-mixed-case.png) |
| Edge | [Before/after titles](proofs/display-step3/edge-all-caps.png) | [Before/after titles](proofs/display-step3/edge-mixed-case.png) |
| Ink | [Before/after titles](proofs/display-step3/ink-all-caps.png) | [Before/after titles](proofs/display-step3/ink-mixed-case.png) |
| Wide | [Before/after titles](proofs/display-step3/wide-all-caps.png) | [Before/after titles](proofs/display-step3/wide-mixed-case.png) |

## Rebuild and verify

From the repository root, using the project Python environment:

```powershell
foreach ($cut in 'soft','edge','ink','wide') {
  .venv/Scripts/python.exe -X utf8 display/make_display.py "display/cuts/$cut.json"
}
.venv/Scripts/python.exe -X utf8 display/build_display_page.py
.venv/Scripts/python.exe -X utf8 verify_display_spacing.py --report dist/display-spacing.json
.venv/Scripts/python.exe -X utf8 verify_shared_engine.py
.venv/Scripts/python.exe -X utf8 verify_display_shapes.py
node --test tests/display-spacing.test.mjs
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p 'test_*.py'
```

GitHub Actions gates both checked-in deliveries and fonts rebuilt from the shared
core. Its rebuilt Lab loads spacing exports from the candidate directories and
compares its actual DOM widths against those candidate fonts.
