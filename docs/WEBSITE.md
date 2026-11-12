# Font Lab website

The repository has a workshop homepage at [`index.html`](../index.html) organized into two
clear studio sections—**01 / Regular & Reading Fonts** and **02 / The Title Engine**—plus a
dedicated **Version History & Side-by-Side Compare** page at [`site/versions/index.html`](../site/versions/index.html).

- **Section 01 — Regular & Reading Fonts:** Showcases the current **SEIHouse Sans 0.42**
  release with a live interactive specimen (weight, real italic, size, Night-mode optical
  grade status, and a Quick Compare dropdown for older milestones), workspace cards for the
  Reader Lab, 3-chapter reading test, Literata/Rubik benchmark, and version archive, plus a
  companion card for **SEIHouse Noto (`Balanced · Refinement 01`)** linking directly to
  `noto/studies/warmth/index.html`.
- **Section 02 — The Title Engine:** Showcases **SEIHouse Display 0.1**, **Living Titles 0.1.3**,
  and **Elemental Title 0.1.0** with interactive cut tabs (**Soft, Edge, Ink, Wide**), a live
  title tester, workspace cards for the Display Lab, Elemental Title Lab (`display/elemental/index.html`),
  finished cut gallery, and NovelExpanded living-title cover mock, plus direct `.otf` starter downloads.
- **Version History & Compare (`site/versions/index.html`):** Tracks and compares every
  preserved release across **SEIHouse Sans** (`0.6` through `0.42`, 17 versions),
  **Title Engine / Display** (7 milestones across Soft, Edge, Ink, and Wide), and
  **SEIHouse Noto** (Studies A, B, C, and `Balanced · Refinement 01`). Fonts are loaded on
  demand via `FontFace` so visitors only download the two versions they are actively comparing.

## Deploy to Vercel

1. Import `SEIHouse/seihouse-font-lab` in Vercel.
2. Leave **Root Directory** at the repository root (`.`).
3. Select **Other** for the framework preset. The checked-in `vercel.json` sets:
   - Install command: empty (no dependencies to install).
   - Build command: `node build_site.mjs`.
   - Output directory: `dist/site`.
4. Deploy. Use the branch containing these changes for a preview, or merge the PR
   into your production branch before deploying that branch.

Use Node.js 18 or newer. No environment variables, database, font compiler, or
Python installation are needed for the website build. The existing checked-in
Lab pages are copied, so commit rebuilt pages when changing a Lab template.

The configuration follows Vercel's [build settings](https://vercel.com/docs/builds/configure-a-build)
and [vercel.json reference](https://vercel.com/docs/project-configuration/vercel-json).
Only the output directory is served; the build copies an explicit Reader/site
allowlist, Display's production manifest inventory (`display/site_inventory.mjs`), and
the validated version-history WOFF2 inventory (`site/version_inventory.mjs` + `site/versions.json`).
This includes six web subsets per Display face, `display/fonts.css`, spacing exports, the
finished-cut specimen pages under `site/display/`, and the archived `.woff2` web fonts under
`old/` so the Version History & Compare page works on the deployed site.
`build_site.mjs` also verifies that `index.html` and `site/versions.json` match the active
version in `phase4.json`, preventing stale homepage version badges from shipping.
Regenerate the Display manifest and pages with `python -X utf8 display/build_all_cuts.py`
after changing cut settings, and run `python archive_version.py --sync` (or `--snapshot-sans` /
`--snapshot-display` before bumping a release) to keep the version archive and homepage badges in sync.
Historical `.otf` files, development scripts, and the source repository remain excluded from `dist/site`.
The dependency-free SEIReader npm/ZIP app packages remain completely separate and exclude `old/` and `site/`.

## Work on the hosted Labs

The [NovelExpanded title study](../display/novel-expanded/index.html) is a silent
homepage mock for comparing the four living cuts in their intended setting. Its
controls refine text, placement, colors, spacing and restrained motion; downloads
produce study JSON or a transparent animated wordmark SVG. Menu music and Reader
Chamber audio remain separate and unconnected. The mock has a caller-owned signal
seam for a future menu connection. It consumes the installable
[`@seihouse/living-titles`](../packages/living-titles/README.md) runtime. Rebuild its checked-in drawing bundle with
`python display/build_novel_mock.py` after changing shared engine/spacing inputs.

The [Elemental Title Lab](../display/elemental/index.html) lets you test every element
(Lightning, Water, provisional Poison, Fire, Frost, Celestial, Void), rank palette, bond tier,
page-wide crowd budget, and Quill familiar signature (*Stormwrit* and *True North*) across all
SEIHouse typefaces (`Display Edge`, `Soft`, `Ink`, `Wide`, `SEIHouse Sans 0.42`, and `SEIHouse Noto`).
It consumes [`@seihouse/elemental-title`](../packages/elemental-title/README.md); rebuild its checked-in
bundle after editing `packages/elemental-title/src/` or `display/elemental/src/` with `npm ci --prefix display`
and `node display/build_elemental_lab.mjs`.

- **Reader Lab:** change the live font settings, then **Save** to keep a browser draft.
  Reloading restores that saved draft.
- **Display Lab:** adjust and name a cut, then **Save cut**. Reloading lists saved
  cuts; choose one to continue working on it.
- **Both Labs:** **Download JSON** exports the current settings even if browser
  storage or clipboard access is blocked. Copy remains available.
- **Reading test:** chapter feedback continues to use its existing local storage
  and Copy All Feedback workflow.

Drafts belong to the current browser and site origin. Local files, localhost,
Vercel preview URLs, and your production domain do not share drafts. Download JSON
before moving between them, clearing browser data, or switching devices. Browser
Save does not update GitHub files or synchronize between devices. When opened in
the original Claude host, the Labs retain the existing host database integration.

The browser draws live previews. It does **not** run the Python font compiler.
Use the downloaded JSON locally to build the next font:

```sh
python make_fonts.py path/to/SEIReader-settings.json
python build_page.py
python build_comparison.py

python -X utf8 display/make_display.py path/to/my-cut.json
python -X utf8 display/build_display_page.py
```

## Preview locally

```sh
node build_site.mjs
python -m http.server 8000 --directory dist/site
```

Open `http://localhost:8000`. Building the website does not rebuild or alter fonts.
Opening the root `index.html` directly also works; saving depends on that browser's
local-file storage policy, and JSON downloads provide a portable copy.

The Display Lab's **Living title** workspace ships its locally bundled media
adapter and MPL notice with the generated page, plus the Step 6 animated proofs.
Local music clips stay on the device. Use localhost or HTTPS for audio/video
APIs. The site build copies these checked-in assets; rebuilding the media bundle
requires `npm ci --prefix display` and `node display/build_living_media.mjs` before rebuilding and
committing the Lab. The website deploy itself retains its dependency-free build.
See [Living Titles](DISPLAY-LIVING-TITLES-STEP6.md) for supported profiles, formats
and certification.

## Archiving a font release

Before building a new version over `fonts/` or `display/fonts/`, snapshot the outgoing
web fonts into `old/` and refresh `site/versions.json` + homepage version badges:

```sh
# Snapshot current Sans web faces into old/<version>/ before bumping phase4.json:
python archive_version.py --snapshot-sans

# Snapshot current Display cuts into old/display/<milestone-slug>/:
python archive_version.py --snapshot-display 0.1-step7

# After updating phase4.json and rebuilding fonts, sync site/versions.json & index.html:
python archive_version.py --sync
```

## Verification

```sh
node --test tests/site.test.mjs tests/site-production.test.mjs
node build_site.mjs
```

The draft tests cover reloads, storage isolation, interleaved tab saves, original
draft-format compatibility, failed writes, blocked/corrupt storage, and safe
document identifiers. Each draft has a separate storage key, so saving a cut does
not rewrite other cuts. Unreadable records are kept and reported; valid cuts still
load, while genuine storage-access errors remain errors. Existing app distribution checks remain
in place. Desktop/mobile browser checks should exercise theme and font controls,
navigation, Save/reload, JSON downloads, and chapter feedback against the built site.
