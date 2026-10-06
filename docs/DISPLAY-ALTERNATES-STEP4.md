# Display Engine Step 4: letter designs

The shared engine now contains two designs for each requested letter group.
Each cut chooses its default forms in an `alternates` object. Eight named
OpenType stylistic sets select the opposite designs; the Lab offers eleven
individual controls so a saved cut can combine them freely.

| Set | Designs | JSON keys |
|---|---|---|
| `ss01` | Single/double-story a and g | `a`, `g` |
| `ss02` | Straight/curved R leg | `R` |
| `ss03` | Branched/joined K and k arms | `K` |
| `ss04` | Vertical/splayed M; plain/crossed W | `M`, `W` |
| `ss05` | Curved/straight y tail | `y` |
| `ss06` | G without/with a spur | `G` |
| `ss07` | Diagonal/long curved Q tail | `Q` |
| `ss08` | Closed/open 4 and 6/9 | `four`, `sixNine` |

Sets are relative to the cut defaults. Enabling `ss01` in Soft selects a
double-story a and g. Enabling it in Edge selects single-story a and g. `ss04`
switches both M and W; `ss08` switches all three figures. All eight sets can
be combined. The original g is already single-story; the new double-story
design has two enclosed bowls and a connecting link.

The G with a spur has an upright projection above its crossbar; the other
form keeps the original continuous G. The long Q tail curves below the bowl
and extends to the right. Open 6/9 connect their counters to the exterior;
closed forms retain enclosed bowls. Open 4 reserves sufficient aperture room
in its smaller superscript, subscript and fraction forms too.

## Cut defaults

| Design | Soft | Edge | Ink | Wide |
|---|---|---|---|---|
| a | single | double | single | double |
| g | single | double | single | double |
| R | curved | straight | curved | straight |
| K/k | branched | joined | branched | joined |
| M | vertical | splayed | vertical | splayed |
| W | plain | plain | plain | plain |
| y | curved | straight | curved | straight |
| G | no spur | spur | no spur | spur |
| Q | long | diagonal | long | long |
| 4 | open | closed | open | open |
| 6/9 | closed | open | open | closed |

These are the current defaults after the [pre-Step-5 fixes](DISPLAY-PRE-STEP5.md).
Edge and Ink now use their already-built plain W designs by default; crossed W
remains available through `ss04` in every cut. Lowercase w stays plain.

Weights, pen/corner settings, advances, encoded character maps and line metrics
retain the previous cut values. Only the chosen default drawings and their
derived optical kerning change. The new forms remain Display options: Reader
settings, original upright skeletons and true italic swaps are unchanged.
Older cut JSON without `alternates` resolves to the original upright designs.

All ninety shipped Reader files remain byte-identical to the frozen 0.39
release, and all ten styles retain the original 0.35 outlines and metrics.
Fresh OTF/WOFF2 rebuilds of all ten styles also match every normalized SFNT
table and the complete CFF outline/hint programs. Those twenty rebuilt files
have new `head.created`/`head.modified` timestamps and consequently a new
`head.checkSumAdjustment`; these three bookkeeping fields are the only
normalization allowed. No names, metrics, layout tables, outlines or hints
are excluded. See the [shipped-file identity report](proofs/display-step4/shared-engine.json)
and [fresh Reader build report](proofs/display-step4/reader-rebuild.json).

## Accents, figures and spacing

Each cut includes 85 additional glyphs, covering the base letters, their
encoded accents and applicable shared Cyrillic/Greek forms, hooked K/k/y,
and small/tabular/fraction derivatives of 4/6/9. Both forms have native mark
anchors. Canonical NFC/NFD composition, remaining mark attachment and stacked
marks work before and after stylistic substitution. Numeric sets combine with
`tnum`, `sups`, `subs` and `frac`, including direct Unicode figures and fractions.

Alternate letter pairs receive the same cut-specific capital/body measurement
policy as the defaults, measured from their actual expanded outlines. GPOS
classes inherit through accented and shared script forms. Alternate capitals
also receive `cpsp` when enabled. The final-font spacing export includes every
alternate's rounded advance, origin, capital classification and compiled pair
lookups. Changing a Lab design selects those compiled metrics and kerning.
Geometry or manual spacing edits continue to show the draft-spacing label.

The Lab's individual design choices persist in Save cut, Copy and Download
JSON. Rebuilding a cut makes those choices its encoded defaults; its stylistic
sets then select the opposite choices. Standard font apps enable a whole set,
so an independent a/g or M/W combination is chosen through the cut JSON.

```css
.display-title {
  font-family: "SEIHouse Display Soft";
  font-kerning: normal;
  font-feature-settings: "ss01" 1, "ss07" 1, "cpsp" 1;
}
```

## Verification and proofs

The Step 1 shape thresholds cover every encoded and unencoded final glyph in
OTF and WOFF2, including all 85 alternates per cut. The original approved
counter topology remains frozen. A separate reviewed Step 4 fixture supplies
counter counts and white-space witnesses only for alternate-covered forms;
verification never regenerates either fixture. An immutable Step 3 outline
fingerprint rejects changes to unrelated original drawings. All original
advances and vertical metrics still use the Step 2 preservation fixture.

The native title proofs show each default and set, the corresponding Lab SVG,
and all-caps/mixed-case titles with all sets enabled:

The following table records the original Step 4 build. The [current proofs](DISPLAY-PRE-STEP5.md)
show plain W/w defaults and optional crossed W for all four cuts.

| Cut | Letter designs and title proof | Measured widths | Maximum Lab/font difference |
|---|---|---:|---:|
| Soft | [Native font and Lab](proofs/display-step4/soft-alternates-titles.png) | 480 | 0.0287% |
| Edge | [Native font and Lab](proofs/display-step4/edge-alternates-titles.png) | 480 | 0.0285% |
| Ink | [Native font and Lab](proofs/display-step4/ink-alternates-titles.png) | 480 | 0.0361% |
| Wide | [Native font and Lab](proofs/display-step4/wide-alternates-titles.png) | 480 | 0.0118% |

[alternates.json](proofs/display-step4/alternates.json) records all 1,920 actual
DOM/native title widths, eleven control checks per cut, and Save/Download/Reload
checks with zero flags. The [existing title gate](proofs/display-step4/spacing.json)
also passes all 888 measurements, with a maximum difference below 0.065%.
[shapes.json](proofs/display-step4/shapes.json) covers **3,268 outlines and 6,536
OTF/WOFF2 renders at 400px, with zero flags**. Every cut passes FontBakery
OpenType and offline Universal with **zero FAIL/WARN**, recorded in
[fontbakery.json](proofs/display-step4/fontbakery.json). The
[live Lab check](proofs/display-step4/lab.json) covers all encoded drawings at
300/400/800px and the 390px mobile view, with no page errors. The focused native,
geometry, preservation and persistence suites pass 62 Python and 28 Node tests.

Rebuild and check from the repo root:

```powershell
foreach ($cut in 'soft','edge','ink','wide') {
  python -X utf8 display/make_display.py "display/cuts/$cut.json"
}
python -X utf8 display/build_display_page.py
node --test tests/display-alternates.test.mjs tests/shared-engine.test.mjs
python -X utf8 verify_display_shapes.py --report dist/display-shapes.json
python -X utf8 verify_shared_engine.py --report dist/shared-engine.json
python -X utf8 verify_display_spacing.py --report dist/display-spacing.json
python -X utf8 verify_display_alternates.py --report dist/display-alternates.json --proof-dir docs/proofs/display-step4
```

Actions run these gates against both the checked-in fonts/Lab and fresh shared
builder output. The alternate verifier compares actual Lab DOM widths with
independent HarfBuzz shaping of OTF and decompressed WOFF2 at 48/96/192px,
for each set individually and all sets together, with `cpsp` off/on. Differences
of 0.5% or greater fail. It also exercises every individual Lab control, its
JSON persistence, native substitutions and canonical accent equivalence.
