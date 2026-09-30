# SEIHouse Font Lab

Home of **SEIReader**, the reading font of SEIHouse Productions LLC. It is built for reading
hundreds of chapters on a phone: calm, soft, and distinctly SEIHouse.

Everything in the font is drawn from rules in code. There are no hand-drawn files to maintain, so
any change (weight, letter height, roundness, spacing) rebuilds the whole family consistently.

## What's inside

| Folder / file | What it is |
|---|---|
| `fonts/` | The finished fonts: 5 weights (Light, Regular, Medium, SemiBold, Bold), each upright and italic, as `.woff2` (web/apps) and `.otf` (computers) |
| `lab/index.html` | **The Lab**: the one page for testing and tuning the font (Reader Chamber, weights, languages, symbols, spacing tools, emoji comments demo) |
| `docs/HOW-TO-USE.txt` | Copy-paste instructions for a coding agent to add SEIReader to an app |
| `docs/HEALTH-CHECK.txt` | Results of Google's FontBakery checks, version by version |
| `settings.json` | The main settings: weights, letter height, roundness, spacing, reading setup |
| `engine.js` | The letter rules: every character, mark, and symbol is drawn here |
| `make_fonts.py` | Builds all 10 font files from the rules |
| `build_page.py` | Builds the Lab page with the current fonts inside it |
| `emoji_demo.py` | Original SEIHouse emoji art used in the comments demo |
| `kern_base.json`, `kern_auto.json` | Pair spacing: hand-set pairs and the automatic pass |
| `old/` | The 0.6 version, kept for side-by-side comparison in the Lab |

## Rebuilding

Needs Python 3 and:

```
pip install -r requirements.txt
python -m playwright install chromium
```

Then:

```
python make_fonts.py        # builds everything in fonts/
python build_page.py        # builds lab/index.html with the new fonts
```

To apply changes saved from the Lab (copied with "Copy instead of Save"), put them in a file and run
`python make_fonts.py my_changes.json`.

## What SEIReader has (version 0.25)

- 5 weights with real italics (handwriting-style italic letters, not a tilted copy)
- Thick and thin: horizontal strokes 12% thinner than vertical ones
- Tall lowercase letters exactly capital height
- Automatic pair spacing for capitals, punctuation, quotes, and brackets, plus hand-set pairs
- Joined `fi` and `fl`
- Screen tuning (alignment zones and Adobe autohinting) for crisp small text
- Languages: English, Spanish, French, Portuguese, German, Italian, Dutch, Catalan, Danish,
  Norwegian, Swedish, Finnish, Icelandic
- Web-novel and system-screen symbols, music marks, player controls, icons, and the SEIHouse `Ⓢ`
  brand mark, with private in-app codes (U+E000–E00F) so phones can't swap in color emoji
- FontBakery: 0 failures, 0 warnings on all 10 files

## Roadmap

- **Phase 2:** even-width numbers for stat screens, superscript numbers, fractions, smaller
  per-language files
- **Phase 3:** real-device testing (iPhone, Android, Windows, Mac) and full-chapter reading tests
- **Phase 4:** more languages: Central European, then Russian and Greek, then Vietnamese
- **Phase 5:** trademark check for the name, license decision, license info inside the files
- **Later:** a separate SEIHouse display font

## License

Not decided yet. Until a license is chosen, all rights are reserved by SEIHouse Productions LLC.
