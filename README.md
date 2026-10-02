# SEIHouse Font Lab

Home of **SEIReader**, the reading font of SEIHouse Productions LLC. It is built for reading
hundreds of chapters on a phone: calm, soft, and distinctly SEIHouse.

Everything in the font is drawn from rules in code. There are no hand-drawn files to maintain, so
any change (weight, letter height, roundness, spacing) rebuilds the whole family consistently.

## What's inside

| Folder / file | What it is |
|---|---|
| `fonts/` | The finished fonts: 5 weights (Light, Regular, Medium, SemiBold, Bold), each upright and italic, as full `.woff2` and `.otf` files plus three smaller WOFF2 subsets per style |
| `fonts.css` | Ready-to-use `@font-face` rules for the 30 Latin basic, Latin extended, and symbols/icons WOFF2 subsets |
| `lab/index.html` | **The Lab**: the one page for testing and tuning the font (Reader Chamber, weights, languages, symbols, spacing tools, emoji comments demo) |
| [`lab/comparison.html`](lab/comparison.html) | The same reference preview: 0.33 beside preserved 0.32, Literata, and Rubik, with composed/decomposed accents, stacks, local quotes, and the established reading samples |
| [`lab/reading-test.html`](lab/reading-test.html) | Three full chapters for sustained reading, with Day/Night and weight controls plus locally saved feedback |
| `docs/HOW-TO-USE.txt` | Copy-paste instructions for a coding agent to add SEIReader to an app |
| `docs/HEALTH-CHECK.txt` | Results of Google's FontBakery checks, version by version |
| [`docs/DEVICE-TEST.md`](docs/DEVICE-TEST.md) | Pass/fail checklist for iPhone, Android, Windows, and Mac browsers |
| `settings.json` | The main settings: weights, letter height, roundness, spacing, reading setup |
| `engine.js` | The letter rules: every character, mark, and symbol is drawn here |
| `make_fonts.py` | Builds all 10 styles from the rules as full OTF and WOFF2 files |
| `build_subsets.py` | Uses pyftsubset to split each style and writes `fonts.css` |
| `verify_phase2.py` | Shapes the optional figures/fractions and checks all 30 subset files |
| `latin_layout.py`, `verify_latin.py` | Build and audit Latin composition, base/mark/ligature attachment, stacking, dotless forms, and preserved 0.32 outlines/spacing |
| `verify_lowercase.py` | Checks the scope of the 0.29 curve pass against preserved 0.28: all advances, unchanged outlines, counters, heights, and settings |
| `verify_spacing.py` | Checks the 0.31 pass against preserved 0.30: every contour and metric, permitted pair changes, shaping, accent classes, joins, hints, subset spacing, and collisions |
| `verify_texture.py` | Checks 0.32 against preserved 0.31: permitted contours, stable advances and letter rhythm, figure counters, reading weights, hints, shaping, and collisions |
| `build_page.py` | Builds the Lab page with the current fonts inside it |
| `build_comparison.py`, `comparison_template.html` | Rebuild the self-contained reference preview with embedded fonts; no network access needed |
| [`docs/DESIGN-GOALS.md`](docs/DESIGN-GOALS.md) | The approved design direction, reference measurements, and reading experiments |
| [`docs/LATIN-FOUNDATION-0.33.md`](docs/LATIN-FOUNDATION-0.33.md) | The first multilingual expansion step: accent inventory, quotation conventions, delivery, validation, and coverage limits |
| `references/` | Official Literata and Rubik fonts for comparison, with their OFL licenses and source hashes |
| `emoji_demo.py` | Original SEIHouse emoji art used in the comments demo |
| `kern_base.json`, `kern_auto.json`, `kern_styles.json` | Pair spacing: hand-set pairs, the automatic pass, and the finished optical pairs for every weight/style used by the Lab |
| `render_small_text.py`, `render_windows.ps1` | Optional Windows WPF small-text proof renderer; uses HarfBuzz shaping and the actual glyph indices, with no font installation |
| `old/` | The 0.6 version for the Lab and all ten styles of 0.27 through 0.32 as preserved baselines; 0.31/0.32 also include their thirty subsets |

## Rebuilding

Needs Python 3 and:

```
pip install -r requirements.txt
python -m playwright install chromium
```

Then:

```
python make_fonts.py        # builds all 10 full styles, 30 subsets, and fonts.css
python build_page.py        # builds lab/index.html with the new fonts
python build_comparison.py  # builds lab/comparison.html with candidate, baseline, and references
python verify_phase2.py     # checks OpenType shaping and subset coverage
python verify_latin.py      # checks 0.33 additions and preservation against 0.32
python verify_texture.py old/0.32    # historical 0.32 texture/weight scope against 0.31
python verify_lowercase.py old/0.31  # historical curve preservation against 0.28
python verify_spacing.py old/0.31    # historical 0.31 spacing scope against 0.30
```

To apply changes saved from the Lab (copied with "Copy instead of Save"), put them in a file and run
`python make_fonts.py my_changes.json`.

Optional native Windows proof: `python render_small_text.py path/to/output 96 --latin`. This produces
Day/Night PNGs at 13/15/17px in Light, Regular, and Medium, including real italics. See the
checked-in [Day](docs/proofs/0.33/windows-day-96.png) and [Night](docs/proofs/0.33/windows-night-96.png)
proofs. Add `--full-family` to proof all five weights at 20px, upright and italic; see
the [family Day](docs/proofs/0.33/family/windows-day-96.png) and
[family Night](docs/proofs/0.33/family/windows-night-96.png) images. Use `--texture` for punctuation/figures,
or omit both flags for broader word-spacing samples. The Latin proof uses 1.5 leading with
at least 21px baseline separation. These are WPF
rasterization evidence; physical browser/device results remain deferred.

## What SEIReader has (version 0.33)

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
- Seventeen zero-width combining accents with automatic `ccmp`, `mark`, and `mkmk` layout.
  Existing accented text has identical NFC/NFD shaping; new combinations support above/below
  attachment, stacks, real italic placement, and dot removal under above accents on `i/j`
- Local low/reversed quotes `‚ „ ‛ ‟`, lexical apostrophes `ʻ ʼ`, a dotted circle `◌`,
  and U+2009 thin/U+202F narrow nonbreaking spaces. All 295 existing drawings, metrics,
  settings, and pair values are preserved from 0.32. See the [Latin foundation notes](docs/LATIN-FOUNDATION-0.33.md)
- Three WOFF2 deliveries per style: Latin basic, Latin extended, and symbols/icons. The generated
  `fonts.css` registers all 30. Latin extended deliberately also includes Latin basic and
  prose punctuation, and is declared last so base letters and combining accents shape together
- Screen tuning (alignment zones and Adobe autohinting) for crisp small text
- Languages: English, Spanish, French, Portuguese, German, Italian, Dutch, Catalan, Danish,
  Norwegian, Swedish, Finnish, Icelandic
- Web-novel and system-screen symbols, music marks, player controls, icons, and the SEIHouse `Ⓢ`
  brand mark, with private in-app codes (U+E000–E00F) so phones can't swap in color emoji
- FontBakery: 0 failures and 0 warnings in OpenType and offline universal checks on all 10
  full OTF styles; online-only universal checks remain unverified in this session

## Roadmap

- **Phase 3:** the device checklist and full-chapter reading test are ready. Run the checklist on physical iPhone, Android, Windows, and Mac devices and record the results; no device results are claimed yet.
- **Multilingual expansion:** Phase 1's Latin foundation is implemented. Next add complete
  encoded alphabets and language-specific refinements; combining marks alone do not certify
  Polish, Czech, Turkish, Vietnamese, or every Latin language. Cyrillic and Greek require later script work
- **Phase 5:** trademark check for the name, license decision, license info inside the files
- **Later:** a separate SEIHouse display font

## License

Not decided yet. Until a license is chosen, all rights are reserved by SEIHouse Productions LLC.
The third-party reference fonts in `references/` are separately licensed under the SIL Open
Font License; their license texts are included in each family directory.
