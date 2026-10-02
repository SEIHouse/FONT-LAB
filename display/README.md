# SEIHouse Display Engine

One engine, a different display font ("cut") for every album or project. Same bones as SEIReader;
every cut sets its own personality.

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
| `engine.js` | Letter rules (SEIReader's, plus cut corners, flat ends, sharp joins, pen angle) |
| `make_display.py` | Builds one cut: `python make_display.py cuts/soft.json` |
| `build_display_page.py` | Builds the Lab page |

## Workflow
1. Shape a cut in the Lab, name it, and press **Save cut** to keep a browser draft
   (or save to the connected Claude host). Drafts stay on this browser and site.
2. **Download JSON** or **Copy** the settings. From the repo root, run
   `python -X utf8 display/make_display.py path/to/my-cut.json`.
3. Rebuild the Lab with `python -X utf8 display/build_display_page.py`.

The hosted Lab previews and saves settings; font compilation uses the local Python
tools. See the root [homepage](../index.html) and [website guide](../docs/WEBSITE.md).

## Version 0.1 notes
- Cuts with an angled pen and flat ends (Ink) still show a few small nicks at some stroke ends; cleanup planned.
- Live Lab spacing uses hand-set pairs only; built fonts also get the automatic pair pass.
