# SEIHouse Display Engine

The shared Reader/Display engine builds a different display font ("cut") for
every album or project. Each cut keeps its own settings while inheriting the
current Reader letter rules, Latin repertoire and OpenType features.

## Settings a cut controls

- **Shape:** thickness, width, lowercase height, capital corners, lowercase roundness, straightness;
  soft or cut corners; round or flat ends; round or sharp joins
- **Pen:** thick and thin (contrast), pen angle (where the thick and thin fall), slant
- **Spacing:** space between letters and words

## Files

| File | What it is |
|---|---|
| `cuts/*.json` | One file per cut (Soft, Edge, Ink, Wide to start) |
| `fonts/<cut>/` | The built font for each cut (`.otf` + `.woff2`), family "SEIHouse Display <Cut>" |
| `lab/index.html` | The Display Lab: shape cuts live on an album cover, track list, poster and alphabet |
| `../engine.js` | Shared letter, mark, symbol and numeric rules, with Reader defaults and Display options |
| `../font_builder.py` | `FontBuilderCore`: shared export, outlines, spacing, hinting and OpenType layout |
| `make_display.py` | Thin cut loader using the same core as `../make_fonts.py` |
| `build_display_page.py` | Builds the Lab page |
| `stroke_geometry.js` | Live oval-pen caps and joins, including perpendicular faces after slant |
| `outline_cleanup.py` | Resolves overlaps and removes contour/point/spike debris before export |
| `../verify_display_shapes.py` | Renders every glyph at 400px and gates shapes, design preservation and web delivery |
| `../verify_shared_engine.py` | Gates Reader preservation and Display repertoire, language, mark and numeric shaping |

## Workflow

1. Shape a cut in the Lab, name it, and press **Save cut** to keep a browser draft
   (or save to the connected Claude host). Drafts stay on this browser and site.
2. **Download JSON** or **Copy** the settings. From the repo root, run
   `python -X utf8 display/make_display.py path/to/my-cut.json`.
3. Rebuild the Lab with `python -X utf8 display/build_display_page.py`.

The hosted Lab previews and saves settings; font compilation uses the local Python
tools. See the root [homepage](../index.html) and [website guide](../docs/WEBSITE.md).

## Shared engine and clean shapes

The forked `display/engine.js` has been removed. Both Labs and both builders use
the root engine. Reader defaults keep soft corners, round ends and joins, an
unrotated pen, and the existing true italic behavior. Cut settings select cut
corners, flat ends, sharp joins, pen angle and oblique slant; oblique slant keeps
upright letter forms.

The final shared builds pass the 400px shape gate: **419 glyphs per cut,
1,676 outlines and 3,352 OTF/WOFF2 renders, 0 flags**. Each cut passes
FontBakery OpenType and offline Universal with **0 FAIL / 0 WARN**. All 50
shipped Reader files retain their baseline bytes; rebuilding through the
new core preserves every table after normalizing build timestamps/checksum.

All four cuts inherit combining marks and `mark`/`mkmk`/`ccmp`, Turkish and
Romanian `locl`, Latin language additions, decimal separator spacing and
`frac`/`tnum`/`sups`/`subs`. Each cut now has 419 font glyphs: the shared engine's
383 encoded entries, 34 alternates, `.notdef` and space. Unicode/PUA aliases
reuse glyph IDs.

Adopting Reader's existing `a`/`e` widths and `i` bearings also updates twenty
old advances per cut. Cut JSON, every other old advance, encoded aliases and
vertical metrics are retained; the [Step 2 notes](../docs/DISPLAY-SHARED-ENGINE-STEP2.md)
record each inherited change and its exact metric gate.

Flat faces end perpendicular to the stroke, including an angled pen and slant.
Attached terminals receive joins rather than protruding caps; sharp joins use
a bounded miter with bevel fallback. The automatic cleanup pass removes
micro-contours, near-duplicate points, spurs/notches and unresolved overlaps.
The live Lab uses the repaired terminal construction as well.

Run `python -X utf8 verify_display_shapes.py` and
`python -X utf8 verify_shared_engine.py` from the repo root; any flag fails.
Add `--proof-dir path/to/proofs --report path/to/report.json` to save every
400px glyph sheet and its results from the shape gate. The same gates run in
GitHub Actions. See the [shared engine and preservation evidence](../docs/DISPLAY-SHARED-ENGINE-STEP2.md).

[Step 1's construction details and before/after proofs](../docs/DISPLAY-SHAPES-STEP1.md)
record the earlier 241-glyph inventory, its 964 clean outlines and per-cut
FontBakery results. Those reports remain a frozen record of that build; Step 2
reports cover the expanded shared inventory.

## Version 0.1 notes

- Live Lab spacing uses hand-set pairs only; built fonts also get the automatic pair pass.
