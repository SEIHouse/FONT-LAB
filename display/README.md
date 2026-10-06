# SEIHouse Display Engine

The shared Reader/Display engine builds a different display font ("cut") for
every album or project. Each cut keeps its own settings while inheriting the
current Reader letter rules, Latin/Vietnamese/Cyrillic/Greek repertoire and
OpenType features.

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

All four cuts pass the 400px shape gate: **732 glyphs per cut, 2,928 outlines
and 5,856 OTF/WOFF2 renders, 0 flags**. Each cut passes FontBakery OpenType
and offline Universal with **0 FAIL / 0 WARN**. All ninety shipped Reader
files retain their latest 0.39 bytes; all ninety rebuilt deliveries match
normalized current tables and CFF outlines/hints. The ten styles also retain
every original 0.35 glyph outline and metric.

The shape gate also measures substantial white counters and letter/number
apertures. Heavy Display pens use shared counter compensation: vertical stems
keep the selected thickness, while horizontal diameter is bounded by x-height
(20% for round ends, 15% for extended flat ends). Both the live Lab and exported
fonts use the same calculation. Soft and Edge gain room in `Aa`, accented `a`,
`æ`, `e`, `g`, Greek epsilon and stacked symbols; Ink and Wide keep their pen
ratios. Saved cut JSON and the shared letter skeletons remain unchanged.
See the [counter repair and before/after proofs](../docs/DISPLAY-COUNTER-REPAIR.md).

All four cuts inherit combining marks and `mark`/`mkmk`/`ccmp`, Turkish and
Romanian `locl`, the complete Latin Extended-A additions, modern Cyrillic and
monotonic Greek, Vietnamese tone stacks, decimal separator spacing and
`frac`/`tnum`/`sups`/`subs`. The shared 0.39 inventory contains 732 font glyphs:
696 encoded engine entries, 34 alternates, `.notdef` and space. Unicode/PUA
aliases reuse glyph IDs.

Adopting Reader's existing `a`/`e` widths and `i` bearings also updates twenty
old advances per cut. Cut JSON, every other old advance, encoded aliases and
typographic line spacing are retained. Edge's Windows clipping ascent grows
20 font units to fit the new Vietnamese tone stacks. The
[Step 2 notes](../docs/DISPLAY-SHARED-ENGINE-STEP2.md) record each inherited
change and its exact metric gate.

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
