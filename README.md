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
| [`lab/comparison.html`](lab/comparison.html) | The reference preview: current candidate beside preserved 0.28, Literata, and Rubik, with focused lowercase samples, reading controls, and word-space trials |
| [`lab/reading-test.html`](lab/reading-test.html) | Three full chapters for sustained reading, with Day/Night and weight controls plus locally saved feedback |
| `docs/HOW-TO-USE.txt` | Copy-paste instructions for a coding agent to add SEIReader to an app |
| `docs/HEALTH-CHECK.txt` | Results of Google's FontBakery checks, version by version |
| [`docs/DEVICE-TEST.md`](docs/DEVICE-TEST.md) | Pass/fail checklist for iPhone, Android, Windows, and Mac browsers |
| `settings.json` | The main settings: weights, letter height, roundness, spacing, reading setup |
| `engine.js` | The letter rules: every character, mark, and symbol is drawn here |
| `make_fonts.py` | Builds all 10 styles from the rules as full OTF and WOFF2 files |
| `build_subsets.py` | Uses pyftsubset to split each style and writes `fonts.css` |
| `verify_phase2.py` | Shapes the optional figures/fractions and checks all 30 subset files |
| `verify_lowercase.py` | Checks the scope of the 0.29 curve pass against preserved 0.28: all advances, unchanged outlines, counters, heights, and settings |
| `build_page.py` | Builds the Lab page with the current fonts inside it |
| `build_comparison.py`, `comparison_template.html` | Rebuild the self-contained reference preview with embedded fonts; no network access needed |
| [`docs/DESIGN-GOALS.md`](docs/DESIGN-GOALS.md) | The approved design direction, reference measurements, and reading experiments |
| `references/` | Official Literata and Rubik fonts for comparison, with their OFL licenses and source hashes |
| `emoji_demo.py` | Original SEIHouse emoji art used in the comments demo |
| `kern_base.json`, `kern_auto.json` | Pair spacing: hand-set pairs and the automatic pass |
| `old/` | The 0.6 version for the Lab and all ten styles of both 0.27 and 0.28 as preserved baselines |

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
python verify_lowercase.py  # checks the 0.29 refinement scope against preserved 0.28
```

To apply changes saved from the Lab (copied with "Copy instead of Save"), put them in a file and run
`python make_fonts.py my_changes.json`.

## What SEIReader has (version 0.29)

- 5 weights with real italics (handwriting-style italic letters, not a tilted copy)
- Thick and thin: horizontal strokes 12% thinner than vertical ones
- Tall lowercase letters exactly capital height
- Automatic pair spacing for capitals, punctuation, quotes, brackets, and gently corrected
  lowercase pairs, plus hand-set pairs
- Rounder upright letters and slightly wider forms; raised straight and curly quotation marks
- Individual reading curves for `a`, `e`, `c`, and `s`; modestly narrower `a`/`e`, more side
  space for `i`, and a 0.220 em word space. Heights, weights, contrast, squared caps, and
  the handwriting-style italic construction carry forward from 0.27
- Related `h/n/m` shoulders, the `u` lower curve, and `b/d/p/q` bowls refined to sit
  consistently beside `a/e/c/s`. All advances and global settings carry forward from 0.28;
  real italics retain their lower branches and pen-like exits
- Joined `fi` and `fl`
- Optional tabular figures (`tnum`), superscript and subscript figures (`sups`, `subs`),
  and stacked fractions (`frac`); Unicode superscripts/subscripts and ½ ¼ ¾ are also included
- Three WOFF2 deliveries per style: Latin basic, Latin extended, and symbols/icons. The generated
  `fonts.css` registers all 30 with nonoverlapping `unicode-range` values
- Screen tuning (alignment zones and Adobe autohinting) for crisp small text
- Languages: English, Spanish, French, Portuguese, German, Italian, Dutch, Catalan, Danish,
  Norwegian, Swedish, Finnish, Icelandic
- Web-novel and system-screen symbols, music marks, player controls, icons, and the SEIHouse `Ⓢ`
  brand mark, with private in-app codes (U+E000–E00F) so phones can't swap in color emoji
- FontBakery: 0 failures and 0 warnings in OpenType and offline universal checks on all 10
  full OTF styles; online-only universal checks remain unverified in this session

## Roadmap

- **Phase 3:** the device checklist and full-chapter reading test are ready. Run the checklist on physical iPhone, Android, Windows, and Mac devices and record the results; no device results are claimed yet.
- **Phase 4:** more languages: Central European, then Russian and Greek, then Vietnamese
- **Phase 5:** trademark check for the name, license decision, license info inside the files
- **Later:** a separate SEIHouse display font

## License

Not decided yet. Until a license is chosen, all rights are reserved by SEIHouse Productions LLC.
The third-party reference fonts in `references/` are separately licensed under the SIL Open
Font License; their license texts are included in each family directory.
