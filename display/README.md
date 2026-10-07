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
- **Letters:** single/double-story a/g, R leg, K/k arms, M stems, W strokes,
  y tail, G spur, Q tail, open/closed 4 and 6/9. Eleven individual Lab controls
  persist in each cut's `alternates` JSON object. Eight named OpenType sets
  (`ss01`–`ss08`) select the other forms.

All four presets use **plain W/w**. Crossed uppercase W and its accented form
are opt-in through `ss04`; lowercase w stays plain. The Lab labels both W
choices and starts every preset with Plain W. `ss04` also switches M.

## Files

| File | What it is |
|---|---|
| `cuts/*.json` | One file per cut (Soft, Edge, Ink, Wide to start) |
| `fonts/<cut>/` | Full OTF/WOFF2 and six web subsets, family "SEIHouse Display <Cut>" |
| `fonts.css` | Per-cut web faces with exact `unicode-range`, relative to this directory |
| `lab/index.html` | The Display Lab: shape cuts live on an album cover, track list, poster and alphabet |
| `../engine.js` | Shared letter, mark, symbol and numeric rules, with Reader defaults and Display options |
| `../font_builder.py` | `FontBuilderCore`: shared export, outlines, spacing, hinting and OpenType layout |
| `make_display.py` | Thin cut loader using the same core as `../make_fonts.py` |
| `build_all_cuts.py` | Discovers every cut JSON and builds its declared production styles, subsets and specimens |
| `production.py` / `production-manifest.json` | Validated cut/style plans and the final delivery inventory with byte counts and SHA-256 hashes |
| `verify_production.py` | Shape/topology, inherited features, compiled spacing, subset/license and FontBakery gates for every built face |
| `specimens.py` / `specimen.css` / `specimen.js` | Generates native-font album cover, track list, poster and alphabet pages into `../site/display/` |
| `verify_specimens.py` | WOFF2 versus built-OTF native widths, style/feature controls and 360–430px layouts |
| `build_subsets.py` | Six Display deliveries using the Reader's subset routine and coverage policy |
| `build_display_page.py` | Builds the Lab page |
| `stroke_geometry.js` | Live oval-pen caps and joins, including perpendicular faces after slant |
| `title_spacing.py` | Capital-height and mixed-case optical spacing, plus final-font GPOS/metric exports |
| `letter_alternates.py` | Stylistic sets and measured alternate pair classes |
| `spacing.js` | Applies compiled kerning classes, rounded advances and capital spacing in the Lab |
| `spacing_<cut>.json` | Final spacing data from each OTF, verified against its settings and font hash |
| `outline_cleanup.py` | Resolves overlaps and removes contour/point/spike debris before export |
| `../verify_display_shapes.py` | Renders every glyph at 400px and gates shapes, design preservation and web delivery |
| `../verify_shared_engine.py` | Gates Reader preservation and Display repertoire, language, mark and numeric shaping |
| `../verify_display_subsets.py` | Gates license parity, subset outlines/metrics/shaping, CSS and the 25 KB basic limit |
| `verify_lab.py` | All live glyphs and phone overflow at 360, 375, 390, 414 and 430px |

## Workflow

1. Shape a cut in the Lab, name it, and press **Save cut** to keep a browser draft
   (or save to the connected Claude host). Drafts stay on this browser and site.
2. **Download JSON** or **Copy** the settings into `display/cuts/my-cut.json`
   (or replace the corresponding preset JSON). From the repo root, run
   `python -X utf8 display/make_display.py display/cuts/my-cut.json`.
3. Rebuild the Lab with `python -X utf8 display/build_display_page.py`.

For production, build the complete collection from the repository root:

```sh
python -X utf8 display/build_all_cuts.py
python -X utf8 display/verify_production.py
python -X utf8 display/verify_specimens.py
python -X utf8 display/build_display_page.py
node build_site.mjs
```

The batch discovers **every `cuts/*.json`**, with no fixed cut list. Current
Soft/Edge/Ink/Wide settings stay Regular-only. Each cut gets a finished-font
specimen in [`site/display/`](../site/display/index.html), with downloads,
capital spacing and all eight stylistic-set controls. These pages use the native
font's actual kerning and metrics, with font synthesis disabled.

`--output-dir dist/display-production` writes a self-contained candidate bundle
with `display/fonts/`, `display/fonts.css`, the manifest, `site/display/`, and
both license files. Candidate spacing lives next to its font. Serve that bundle
as a website root to inspect the specimens; it leaves committed fonts and Lab
spacing untouched. `--specimens-only` refreshes pages, inventory and CSS from
existing fonts without rebuilding outlines. Cut names use ASCII letters/digits,
single spaces or hyphens; duplicate slugs or PostScript identities fail before
building.

### Opt-in extra weights and Oblique

Add a `production` object to the individual cut JSON. For example, a Wide
variation can request:

```json
"production": {
  "weights": {"Light": 0.85, "Bold": 1.03},
  "oblique": 9
}
```

Weight values multiply **that cut's thickness**; all other drawing and alternate
settings stay the same. Weight names use the Reader's static weight classes
(Light 300, Medium 500, SemiBold 600, Bold 700, etc.). Lighter names require a
multiplier below 1; heavier names require one above 1. The accepted 0.5–1.5 range
is an input bound, and every result must still pass the shape gate.
`oblique` adds degrees to the cut's existing slant (the reviewed Ink example adds
3° to its 8° slant, giving 11°).
It retains upright letter skeletons and sets proper Oblique names, slope/caret
metadata, OS/2 oblique flags and a `slnt` STAT value. It does not select Reader
italic letter substitutions. The total angle is limited to 25°.

Extra fonts, subsets and spacing exports live in `fonts/<cut>/<Style>/`; CSS
uses their real weight and oblique angle. Regular paths stay compatible.
To experiment without changing committed defaults, copy the cut JSON files to
another directory, add production choices there, and pass `--cuts <directory>`
with a separate `--output-dir`. Each cut explicitly chooses its extra styles.

### CI and release gates

The **App distribution** GitHub Action runs the batch on pushes to `main`, pull
requests and manual runs. Every rebuilt face passes the shape gate, inherited
language/numeric/alternate features, final spacing, license and six-subset
checks, then FontBakery **OpenType + offline Universal**, with any WARN, FAIL,
ERROR or unfinished run blocking delivery. Every Latin-basic face stays strictly
under 25,000 bytes. The job also rebuilds Reader and checks its preserved tables,
outlines and metrics, plus the rebuilt Lab's title/alternate/phone gates.

Successful runs upload **`seihouse-display-fonts`** (fonts, web CSS, manifest,
native specimens and licenses), retained for 30 days. Validation reports and
FontBakery logs are in **`shared-builder-evidence`**, including failed runs.
Automatic and manual runs honor each cut JSON. Current files declare no extras.

Regular retains Step 1's immutable metrics, skeletons and topology witnesses.
Each extra style needs separately reviewed 400px topology at
`tests/fixtures/display-production-topology/<slug>-<style>.json`; a new cut's
Regular uses `<slug>.json`. The fixture records the exact drawing `settings`,
built spacing `variants`, `size_px`, and each glyph's fixed counter/witness
coordinates. A changed recipe requires new review. Every glyph still passes
outline, overlap, 6px counter/aperture clearance and OTF/WOFF2 raster checks.
The production gate reads fixed fixtures and never captures a candidate baseline.
Reviewed opt-in example JSONs and proofs are linked in
[Step 5 pipeline evidence](../docs/DISPLAY-PRODUCTION-STEP5.md).

Each cut build also writes `latin-basic`, `latin-extended`, `cyrillic`, `greek`,
`vietnamese` and `symbols` WOFF2 files. Default builds refresh the subsets for
every OTF included in `display/fonts.css` before writing that stylesheet, so it
cannot reference another cut's missing or stale subsets.
`--output-dir` keeps candidate fonts, subsets, spacing and CSS together without
changing shipped metadata. To regenerate subsets/CSS from the current OTFs,
run `python -X utf8 display/build_subsets.py`.

The hosted Lab previews and saves settings; font compilation uses the local Python
tools. See the root [homepage](../index.html) and [website guide](../docs/WEBSITE.md).

## License and web delivery

Every full font and web subset embeds the **SEIHouse Sans Ecosystem License,
version 1.0**, using exactly the Reader's name records: copyright (0), trademark
(7), manufacturer (8), designer (9), vendor/designer URLs (11/12), license
description (13) and license URL (14). `OS/2.fsType` is `0` and the vendor is
`SEIH`, matching Reader. The operative terms are in [LICENSE](../LICENSE);
installable document embedding follows those terms. Display family/style names
remain distinct from Reader.

Keep `fonts.css` next to the `fonts/` directory and include it in your site:

```html
<link rel="stylesheet" href="/display/fonts.css">
```

```css
.title {
  font-family: "SEIHouse Display Soft", sans-serif;
  font-weight: 400;
  font-kerning: normal;
  font-feature-settings: "cpsp" 1;
}
```

Like Reader, extended and script faces overlap Latin/mark coverage to preserve
complete grapheme clusters and title kerning. Later matching faces take browser
priority. A project requiring only basic Latin can use its cut's `latin-basic`
face block alone; all four basic files are strictly below **25,000 bytes**
(Soft 22,156; Edge 17,264; Ink 22,416; Wide 22,140). Subsets retain applicable
stylistic, numeric, local-form and mark features, including a visible `.notdef`.

The Lab fits long SVG words proportionally inside their containers on phones.
Its gate checks all four presets at five widths from 360–430px, with default
and long titles, crossed W and `cpsp`. It rejects both document overflow and
individual elements outside the viewport. Run `python -X utf8 display/verify_lab.py`;
`--lab` checks a candidate HTML file and `--url` checks
a served page. See the [pre-Step-5 fixes and current proofs](../docs/DISPLAY-PRE-STEP5.md).

## Shared engine and clean shapes

The forked `display/engine.js` has been removed. Both Labs and both builders use
the root engine. Reader defaults keep soft corners, round ends and joins, an
unrotated pen, and the existing true italic behavior. Cut settings select cut
corners, flat ends, sharp joins, pen angle and oblique slant; oblique slant keeps
upright letter forms.

Step 2's four cuts passed the 400px shape gate: **732 glyphs per cut, 2,928 outlines
and 5,856 OTF/WOFF2 renders, 0 flags**. Each cut passes FontBakery OpenType
and offline Universal with **0 FAIL / 0 WARN**. Step 4 expands each cut to 817
glyphs: **3,268 outlines and 6,536 renders, 0 flags**. Its separate proof reports
cover the new designs; both FontBakery profiles still pass with zero FAIL/WARN.
All ninety shipped Reader
files retain their latest 0.39 bytes; all ninety rebuilt deliveries match
normalized current tables and CFF outlines/hints. The ten styles also retain
every original 0.35 glyph outline and metric.

The shape gate also measures substantial white counters and letter/number
apertures. An immutable approved topology baseline rejects missing counters and
filled or sealed interiors, including cases that pass clearance-only analysis.
Heavy Display pens use shared counter compensation: vertical stems
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

- Each cut has its own default letter designs and includes 85 alternate glyphs,
  including accents, shared script forms and numeric derivatives. Built sets
  combine with mark attachment, `cpsp` and numeric features. The Lab uses their
  compiled spacing, so switching a design preserves final width agreement.
  See the [Step 4 defaults, feature mapping, gates and native title proofs](../docs/DISPLAY-ALTERNATES-STEP4.md).

- Titles use each cut's capital-height spacing pass and optional `cpsp` capital
  spacing. The Lab reads the final OTF's kerning and advances; all 888 measured
  title widths differ by less than 0.065%. Unbuilt edits receive a draft-spacing
  label until their font and Lab are rebuilt. See the [Step 3 title proofs,
  spacing behavior and width gate](../docs/DISPLAY-TITLE-SPACING-STEP3.md).
