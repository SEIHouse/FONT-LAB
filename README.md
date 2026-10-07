# SEIHouse Font Lab

Home of **SEIHouse Sans** (formerly SEIReader), the reading font of SEIHouse Productions LLC. It is built for reading
hundreds of chapters on a phone: calm, soft, and distinctly SEIHouse.

The **SEIHouse Display Engine** is a version 0.1 workshop for album covers,
posters, chapter titles, and other large text. It shares the Reader drawing
engine and builder core; its four cut settings, live Lab and prebuilt fonts are
under [`display/`](display/README.md).

## Font Lab homepage & Vercel

Open [`index.html`](index.html) for the workshop homepage: an editable specimen
using the actual font files, Reader/Display workspaces, comparisons, chapter
reading tests, and downloads. Both Labs can save browser drafts and download JSON
settings on a normal website.

Import this repository into Vercel with **Other** as the framework and the repo
root as the Root Directory. `vercel.json` builds the website with
`node build_site.mjs` and serves only `dist/site`. There are no website dependencies
or environment variables to configure. See [website setup and draft usage](docs/WEBSITE.md).

Local preview: `node build_site.mjs`, then
`python -m http.server 8000 --directory dist/site` and open `http://localhost:8000`.

Everything in the font is drawn from rules in code. There are no hand-drawn files to maintain, so
any change (weight, letter height, roundness, spacing) rebuilds the whole family consistently.

## Installing in an app

Use the **App distribution** Actions run's `seireader-app-packages` download, or build
the packages locally with `python build_distribution.py` and
`npm pack --ignore-scripts --pack-destination dist`. No font-building dependencies
are needed to package the checked-in fonts.

- **Static assets:** extract `SEIReader-0.39-web-full.zip` into your app's public assets
  and load its `sans.css` for `font-family: "SEIHouse Sans"`.
- **Vite/npm:** install `seihouse-seireader-0.39.0.tgz` and import
  `@seihouse/seireader/sans.css`. This private package has zero dependencies and
  no installation scripts; it is not published to the npm registry.

The default uses ten full WOFF2 files: **712,464 font bytes (695.8 KiB)** for all
five weights and their real italics. That is **71.6% less** than storing all seventy
overlapping subsets. Regular plus italic uses **141,632 bytes**; the browser requests
the styles used by rendered text. The package includes no old versions, Lab, OTFs,
reference fonts, proof images, or font engineering tools.

See [APP-INSTALL.md](docs/APP-INSTALL.md) for both installation routes, explicit
weight-only bundles, and the inspected Development/NovelExpanded host handoff.
The developer sections below describe the full source repository.

## Display font Lab

Open [`display/lab/index.html`](display/lab/index.html) to explore **Soft, Edge, Ink,
and Wide**. Each design has its own OTF and WOFF2 files under `display/fonts/<cut>/`.
Reader and Display now use the root `engine.js` and `font_builder.py`.
Display cuts inherit the current Reader Latin, Vietnamese, Cyrillic and Greek
repertoire, combining mark/local forms and numeric features while retaining
their cut settings. Display fonts
remain excluded from the SEIReader app ZIP/npm package. See the
[shared engine and Reader preservation gate](docs/DISPLAY-SHARED-ENGINE-STEP2.md)
and [clean-shape construction and proofs](docs/DISPLAY-SHAPES-STEP1.md).
Titles use per-cut capital-height kerning and optional `cpsp` capital spacing.
The Lab reads each built font's final spacing; see the
[title spacing gate and before/after proofs](docs/DISPLAY-TITLE-SPACING-STEP3.md).
Each cut now chooses its own letter designs. The Lab has individual controls
for a/g, R, K/k, M/W, y, G, Q and open/closed 4/6/9; built fonts include the
other forms through `ss01`–`ss08`. See the [alternate mapping, cut defaults and
native title proofs](docs/DISPLAY-ALTERNATES-STEP4.md).
All four presets default to plain W/w; crossed W is optional in `ss04`.
Display embeds the Reader's ecosystem license metadata and includes six web
subsets per cut through `display/fonts.css`, with every Latin-basic file below
25 KB. The phone Lab gates overflow at 360–430px. See the
[pre-Step-5 fixes, current specimens and delivery checks](docs/DISPLAY-PRE-STEP5.md).
The [production pipeline](docs/DISPLAY-PRODUCTION-STEP5.md) discovers every cut
JSON, supports opt-in extra weights and Oblique, and generates a
[finished-font specimen collection](site/display/index.html). The App
distribution Action rebuilds and gates every declared face before uploading
`seihouse-display-fonts`, including OTF/WOFF2, subsets, CSS, specimens and licenses.
Current cut defaults remain Regular-only.
Its **Save cut** button uses browser-local drafts on a normal website and retains
the original database integration in the Claude host. Use **Download JSON** or
**Copy** to bring a cut back to the font builder. Drafts stay on this browser/site.

To rebuild with the Python dependencies described below, run from the repository root:

```sh
python -X utf8 display/make_display.py display/cuts/soft.json
python -X utf8 display/build_display_page.py
```

For the entire collection, run `python -X utf8 display/build_all_cuts.py`.
Use `--output-dir dist/display-production` for a separate candidate bundle;
per-cut `production.weights` and `production.oblique` settings opt into styles.
See [Display build options and gates](display/README.md).

Choose `edge.json`, `ink.json`, or `wide.json` for another design. The builder uses
Chromium and `otfautohint`; run it in the environment where those dependencies are
installed. The explicit UTF-8 mode supports the supplied Unicode sources on Windows.
The Lab generator checks the cut settings and font hash against its spacing
export. Unbuilt geometry edits receive a draft-spacing label until rebuilt.
Run `python -X utf8 verify_display_shapes.py` and
`python -X utf8 verify_shared_engine.py` to gate all four rebuilt cuts and Reader
preservation, and `python -X utf8 verify_display_spacing.py` to gate Lab/font
title widths at a difference below 0.5%.

## What's inside

For application integration, [`@seihouse/living-titles`](packages/living-titles/README.md)
is a separate private runtime package with a ready-to-install tarball, ESM/TypeScript
interfaces, a browser player, an optional React component and four static Display
faces. The [NovelExpanded mock](display/novel-expanded/index.html) consumes that same
runtime. Audio remains caller-owned; menu and Reader Chamber systems stay separate.
The existing Reader font package and font build interfaces remain unchanged.

| Folder / file | What it is |
|---|---|
| `index.html`, `site/`, `build_site.mjs`, `vercel.json` | Workshop homepage, browser draft/download helpers, and an explicit static website build for Vercel |
| [`display/`](display/README.md) | SEIHouse Display 0.1: four cut settings, live Lab, shared-core entry point, kerning maps and OTF/WOFF2 fonts |
| `fonts/` | The finished fonts: 5 weights (Light, Regular, Medium, SemiBold, Bold), each upright and italic, as full `.woff2` and `.otf` files plus seven WOFF2 subset deliveries per style |
| `fonts.css` | Ready-to-use `@font-face` rules for all 70 Latin and script WOFF2 subsets |
| `fonts-full.css` | Recommended app stylesheet for the ten full web fonts; no Unicode face splitting |
| `package.json`, `build_distribution.py`, `verify_distribution.py` | Runtime allowlist, deterministic ZIP delivery, dependency-free npm package, and actual shipped-payload audits |
| [`docs/APP-INSTALL.md`](docs/APP-INSTALL.md) | App installation, measured sizes, and the current Development/NovelExpanded reader integration points |
| `lab/index.html` | **The Lab**: the one page for testing and tuning the font (Reader Chamber, weights, languages, symbols, spacing tools, emoji comments demo) |
| [`lab/comparison.html`](lab/comparison.html) | The same reference preview: 0.39 beside preserved 0.34, Literata, and Rubik, with the expanded language selector, NFC/NFD alphabets, local forms, and the established reading samples |
| [`lab/reading-test.html`](lab/reading-test.html) | Three full chapters for sustained reading, with Day/Night and weight controls plus locally saved feedback |
| `docs/HOW-TO-USE.txt` | Copy-paste instructions for a coding agent to add SEIReader to an app |
| `docs/HEALTH-CHECK.txt` | Results of Google's FontBakery checks, version by version |
| [`docs/DEVICE-TEST.md`](docs/DEVICE-TEST.md) | Pass/fail checklist for iPhone, Android, Windows, and Mac browsers |
| `settings.json` | The main settings: weights, letter height, roundness, spacing, reading setup |
| `phase4.json`, `phase4_support.py` | Current additive release metadata and web-face order, kept separate from design settings |
| `engine.js` | Shared Reader/Display rules for every character, mark, alternate and symbol |
| `font_builder.py` | Shared outline, spacing, OpenType layout and hinting core |
| `make_fonts.py` | Thin Reader entry point: builds all 10 styles as full OTF and WOFF2 files |
| `verify_shared_engine.py`, `verify_display_shapes.py` | Reader preservation, Display shaping and all-glyph 400px shape/delivery gates |
| `build_subsets.py` | Uses pyftsubset to split each style and writes `fonts.css` |
| `verify_phase2.py` | Shapes the optional figures/fractions and checks all current subset files |
| `latin_layout.py`, `verify_latin.py` | Build and audit Latin composition, base/mark/ligature attachment, stacking, dotless forms, and preserved 0.32 outlines/spacing |
| `languages.json`, `language_coverage.py`, `verify_phase4.py`, `verify_phase4_engine.mjs` | Pinned CLDR inventories, modern script scope, and additive coverage, composition, collision, preservation and web delivery audits |
| `verify_lowercase.py` | Checks the scope of the 0.29 curve pass against preserved 0.28: all advances, unchanged outlines, counters, heights, and settings |
| `verify_spacing.py` | Checks the 0.31 pass against preserved 0.30: every contour and metric, permitted pair changes, shaping, accent classes, joins, hints, subset spacing, and collisions |
| `verify_texture.py` | Checks 0.32 against preserved 0.31: permitted contours, stable advances and letter rhythm, figure counters, reading weights, hints, shaping, and collisions |
| `build_page.py` | Builds the Lab page with the current fonts inside it |
| `build_comparison.py`, `comparison_template.html` | Rebuild the self-contained reference preview with embedded fonts; no network access needed |
| [`docs/DESIGN-GOALS.md`](docs/DESIGN-GOALS.md) | The approved design direction, reference measurements, and reading experiments |
| [`docs/LATIN-FOUNDATION-0.33.md`](docs/LATIN-FOUNDATION-0.33.md) | The first multilingual expansion step: accent inventory, quotation conventions, delivery, validation, and coverage limits |
| [`docs/LANGUAGES-0.34.md`](docs/LANGUAGES-0.34.md) | The first language batch: scope per locale, 94 additions, local behavior, usage, inspection, data provenance, and remaining work |
| `references/` | Official Literata/Rubik comparison fonts with OFL licenses and source hashes, plus the separate Unicode license for CLDR locale data |
| `emoji_demo.py` | Original SEIHouse emoji art used in the comments demo |
| `kern_base.json`, `kern_auto.json`, `kern_styles.json`, `kern_languages.json` | Pair spacing: hand-set pairs, automatic and finished per-style maps, and Hungarian-only capital adjustments used by the Lab |
| `render_small_text.py`, `render_windows.ps1` | Optional Windows WPF small-text proof renderer; uses HarfBuzz shaping and the actual glyph indices, with no font installation |
| `old/` | The 0.6 version for the Lab and all ten styles of 0.27 through 0.33 as preserved baselines; 0.31 through 0.33 also include their thirty subsets |

## Rebuilding

Needs Python 3 and:

```
pip install -r requirements.txt
python -m playwright install chromium
```

Then:

```
python make_fonts.py        # builds all 10 full styles, 70 subsets, and fonts.css
python build_page.py        # builds lab/index.html with the new fonts
python build_comparison.py  # builds lab/comparison.html with candidate, baseline, and references
python verify_phase2.py     # checks OpenType shaping and subset coverage
python verify_phase4.py     # checks all additions and exact preservation against the Phase 4 starting commit
node verify_phase4_engine.mjs # checks old SVG output across weights, italics and contrast
python verify_phase4.py --custom-spacing # optional real-font Lab override regression
python verify_latin.py old/0.33 # historical foundation audit against preserved 0.32
python verify_texture.py old/0.32    # historical 0.32 texture/weight scope against 0.31
python verify_lowercase.py old/0.31  # historical curve preservation against 0.28
python verify_spacing.py old/0.31    # historical 0.31 spacing scope against 0.30
python build_distribution.py       # runtime-only app ZIP; standard library only
npm pack --ignore-scripts --pack-destination dist # private, dependency-free npm tarball
python verify_distribution.py --npm dist/seihouse-seireader-0.39.0.tgz
python verify_license.py           # legal metadata in all current full/subset fonts
```

The historical scope audits target their recorded releases; the current additive gate is
`verify_phase4.py`. The 0.35 stroke-join audit requires that release's original font set.

To apply changes saved from the Lab (copied with "Copy instead of Save"), put them in a file and run
`python make_fonts.py my_changes.json`.

Optional native Windows proof: `python render_small_text.py path/to/output 96 --languages`. This produces
Day/Night PNGs at 13/15/17px in Light, Regular, and Medium, including real italics. See the
checked-in [Day](docs/proofs/0.34/windows-day-96.png) and [Night](docs/proofs/0.34/windows-night-96.png)
proofs. Add `--full-family` to proof all five weights at 20px, upright and italic; see
the [family Day](docs/proofs/0.34/family/windows-day-96.png) and
[family Night](docs/proofs/0.34/family/windows-night-96.png) images. Use `--latin` for foundation marks,
`--texture` for punctuation/figures, or omit the flags for broader word-spacing samples. The language proof uses 1.5 leading with
at least 21px baseline separation. These are WPF
rasterization evidence; physical browser/device results remain deferred.

For the 0.35 export repair, see [stroke-join notes](docs/STROKE-JOINS-0.35.md) and
the Chromium [Day](docs/proofs/0.35/stroke-joins-day.png) /
[Night](docs/proofs/0.35/stroke-joins-night.png) proofs.

The [final paragraph-spacing inspection](docs/PARAGRAPH-SPACING-0.35.md) records
the sentence-ending, apostrophe and narrow-letter candidates in full paragraphs,
with Day/Night proofs across all ten styles. It found no demonstrated spacing
defect and preserves the 0.35 fonts. Open **Paragraph spacing** in each reference
preview card to inspect the exact text with the existing reading controls.

## What SEIHouse Sans has (version 0.39)

- 5 weights with real italics (handwriting-style italic letters, not a tilted copy)
- Thick and thin: horizontal strokes 12% thinner than vertical ones
- Tall lowercase letters exactly capital height
- Automatic pair spacing for capitals, punctuation, quotes, brackets, and gently corrected
  lowercase pairs, plus hand-set pairs
- Rounder upright letters and slightly wider forms; raised straight and curly quotation marks
- Individual reading curves for `a`, `e`, `c`, and `s`; modestly narrower `a`/`e`, more side
  space for `i`, and a 0.220 em word space. Heights, nominal weights, contrast, squared caps, and
  the handwriting-style italic construction carry forward from 0.27
- Related `h/n/m` shoulders, the `u` lower curve, and `b/d/p/q` bowls refined to sit
  consistently beside `a/e/c/s`. All advances and global settings carry forward from 0.28;
  real italics retain their lower branches and pen-like exits
- Joined `fi` and `fl`
- Focused optical spacing for the reported snag words and `ri/rn/cl/li`, measured separately
  for every weight and italic. Joined `fi/fl` receive spacing beside neighbors; all glyph
  advances carry forward, with extra separation at crowded `tt/ry` pairs
- Broader rhythm inspection for `minimum`, `murmur`, `river`, `climate`, `parallel`, and
  `everywhere`, plus supporting `r/v/w/y` and narrow-letter cases. Balance `ll`, protect
  `yw/tw` separation, and open crowded italic `ur/um`. All earlier focused pairs and all
  character advances are preserved. See the [inspection notes](docs/SPACING-0.31.md)
- Quieter punctuation and smoother figures, including updated tabular/small figures and
  fractions. Raised quotes stay raised; mark/figure pairs retain minimum ink separation,
  including accented letter classes. See the [texture notes](docs/TEXTURE-0.32.md)
- Firmer Light and slightly lighter Medium letter strokes for small reading sizes, with
  Regular/SemiBold/Bold letter drawings, symbols/icons, nominal controls, and all advances
  unchanged. These are static refinements at every size, with no optical-size axis
- Optional tabular figures (`tnum`), superscript and subscript figures (`sups`, `subs`),
  and stacked fractions (`frac`); Unicode superscripts/subscripts and ½ ¼ ¾ are also included
- Eighteen zero-width combining accents with automatic `ccmp`, `mark`, and `mkmk` layout.
  Existing accented text has identical NFC/NFD shaping; new combinations support above/below
  attachment, stacks, real italic placement, and dot removal under above accents on `i/j`
- Local low/reversed quotes `‚ „ ‛ ‟`, lexical apostrophes `ʻ ʼ`, a dotted circle `◌`,
  and U+2009 thin/U+202F narrow nonbreaking spaces. All 295 existing drawings, metrics,
  settings, and pair values are preserved from 0.32. See the [Latin foundation notes](docs/LATIN-FOUNDATION-0.33.md)
- Ninety-four additional encoded letters complete the pinned CLDR main/auxiliary/index
  inventories and case variants for Polish, Czech, Hungarian, Romanian, Turkish, Hausa,
  Kurdish (Kurmanji, Latin), Māori, Igbo, and Uzbek (Latin). New side carons, hooks, barred
  letters, Igbo tone stacks, Turkish dotted `fi`, Romanian comma forms, and Hungarian
  capital digraph spacing follow the existing design. All 323 old outlines/metrics and
  nonnumeric pair values match 0.33. Numeric periods/commas have explicit separation
  on both sides, including equal adjustments for tabular figures; digit drawings,
  advances, and digit-to-digit spacing stay unchanged. See the [language notes](docs/LANGUAGES-0.34.md)
- Seven WOFF2 deliveries per style: Latin basic, legacy Latin extended, symbols/icons,
  `latin-ext-2`, `cyrillic`, `greek`, and `vietnamese`. The generated `fonts.css`
  registers all 70; preferred script faces include complete Latin text, punctuation and combining marks
- Screen tuning (alignment zones and Adobe autohinting) for crisp small text
- Established Latin coverage: English, Spanish, French, Portuguese, German, Italian,
  Dutch, Catalan, Danish, Norwegian, Swedish, Finnish, Icelandic. Additional audited
  inventories: the ten locales above, Slovak, Croatian, Slovenian, the six Cyrillic
  locales, monotonic Greek and Vietnamese in Phase 4. Alphabet coverage is separate from native-reader
  and physical device certification; other scripts/spelling traditions may need fallback
- Web-novel and system-screen symbols, music marks, player controls, icons, and the SEIHouse `Ⓢ`
  brand mark, with private in-app codes (U+E000–E00F) so phones can't swap in color emoji
- FontBakery: 0 failures and 0 warnings in OpenType and offline universal checks on all 10
  full OTF styles; online-only universal checks remain unverified in this session

## Phase 4: additive language expansion

Step 1 (0.37) completes all 128 Latin Extended-A characters. Polish, Czech, Slovak,
Hungarian, Romanian, Croatian, Slovenian, and Turkish are covered, including
`İ ı Ğ ğ Ş ş Đ đ Ĺ ĺ` and the established apostrophe-style carons on `ď ľ ť Ľ`.
The Lab adds Slovak, Croatian, and Slovenian samples to the existing ten-language
inventory. New accents use ACC/MARK and the existing fixed-gap, lighter-mark
attachment. `ģ` uses a turned comma above; new ogoneks receive their own
punctuation clearance without changing approved pairs.

Step 2 (0.38) adds the Russian alphabet and common Slavic Cyrillic set (U+0400–045F
plus Ukrainian Ґ/ґ), with pinned Russian, Ukrainian, Belarusian, Bulgarian, Serbian
and Macedonian samples. It also adds the modern monotonic Greek alphabet, tonos,
diaeresis, combined dialytika/tonos, final sigma and Greek punctuation. Identical
shapes reuse existing glyph construction; new shapes use the same stroke, contrast,
roundness and italic rules. Cyrillic italic `б в г д и п т` uses cursive forms.
New script classes receive automatic pair measurements and separate clearance
exceptions; existing Latin pairs remain unchanged. Historical Bulgarian yat/yus
and Greek polytonic auxiliary letters are outside this batch.

Step 3 (0.39) completes Vietnamese: all U+1EA0–1EF9 letters and the four
Ơ/ơ/Ư/ư horn bases are encoded. Eighty-eight missing letters use ACC recipes
built from existing vowels, circumflex/breve parents and lighter tone marks.
Canonical composition handles both stacked accents and structural vowel plus
tone input. Horn and tone clearance uses literal pairs for new glyphs; prior
letter outlines, advances, weights and spacing remain unchanged. The Lab adds
a pinned Vietnamese inventory/sample and every new letter. The `vietnamese`
subset includes complete Latin text, all encoded vowels and their combining
ingredients together. All 21 recorded locale inventories pass the declared
scope; frequent capital stacks can use 1.5 line height after checking the app.

`phase4.json` records release metadata separately from unchanged `settings.json`.
Run `python verify_phase4.py` to compare all old glyphs, advances, settings,
spacing and shaping with the starting commit. FontBakery results are in
[the health check](docs/HEALTH-CHECK.txt). Alphabet coverage does not certify
sustained reading on a physical device.

## Roadmap

- **Phase 3:** the device checklist and full-chapter reading test are ready. Run the checklist on physical iPhone, Android, Windows, and Mac devices and record the results; no device results are claimed yet.
- **Multilingual expansion:** Phase 1's Latin foundation and Phase 2's first ten Latin
  inventories are implemented. Phase 4 completes Latin Extended-A and supplies common
  Cyrillic, monotonic Greek and full Vietnamese. Further African
  open-vowel/stroke/tone letters and other scripts remain candidates. Device/native-reader
  evaluation remains separate
- **Phase 5 completed:** recorded name screening, selected ecosystem license, and embedded legal metadata in all styles and subsets. Name screening is preliminary; no registered-trademark claim is made.
- **Later:** a separate SEIHouse display font

## License

SEIHouse Sans is owned by **SEIHouse Productions LLC, Ohio**, and uses the
[SEIHouse Sans Ecosystem License 1.0](LICENSE). Ecosystem users may install,
customize, and use it for personal or commercial creative work, including PDF/EPUB
document embedding, without fees or user-count limits. Authorized SEIHouse apps,
websites, SEA/SEN tools, and official font deliveries may distribute it.
Independent app/product embedding and standalone font redistribution require
written permission. See the full license for collaboration, notices, and scope.

The font's current family name is **SEIHouse Sans**. Existing `SEIReader-*` asset
paths, `@seihouse/seireader`, and its `styles.css` / `font-family: "SEIReader"`
alias continue working. New integrations can use `sans.css` / `"SEIHouse Sans"`.
The license is shipped in every runtime ZIP and npm package. Font metadata carries
the owner, studio designer credit, project/license URLs, and license summary.
`fsType=0` permits installable document embedding subject to this EULA; it does
not grant unrestricted standalone redistribution. Vendor ID `SEIH` is a project
identifier; no Microsoft vendor registration or SEIHouse Sans trademark registration
is claimed. The [name screen](docs/NAME-CHECK.md) records its limited scope.

The separate Display prototype and archived earlier releases are outside this
license's scope and retain their existing permissions.
The third-party reference fonts in `references/` are separately licensed under the SIL Open
Font License; their license texts are included in each family directory.
The pinned CLDR locale data is separately covered by the [Unicode license](references/cldr/LICENSE.txt).
