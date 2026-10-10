# Install SEIHouse Sans in an app

SEIHouse Sans 0.39 (formerly SEIReader) ships as static web fonts: five weights (300/400/500/600/700),
each with its real italic. The app needs WOFF2 files and CSS. It needs no Python,
font-building tools, JavaScript runtime library, or reference fonts.

## Recommended: the full web family

Use the `SEIReader-0.39-web-full.zip` from a successful **App distribution** GitHub
Actions run, or build it with `python build_distribution.py` in the font repository.
Actions retains these downloads for 30 days; its manual Run workflow button can
regenerate them from the current branch. This does not create a public npm release.
Extract the bundle into an app-owned, versioned asset directory such as
`public/seireader/0.39/`. Keep its `sans.css` next to its `fonts/` directory.
Asset/package names retain SEIReader for compatibility; the actual family is
SEIHouse Sans. Existing `fonts.css` / `"SEIReader"` integrations still work.

```text
public/seireader/0.39/
  fonts.css
  sans.css
  fonts/SEIReader-Regular.woff2
  fonts/SEIReader-Italic.woff2
  ...the other eight styles
  README.md
  FONT-LICENSE.txt
  LICENSE
  manifest.json
```

In a Vite app hosted at the domain root, load the CSS from its HTML head:

```html
<link rel="stylesheet" href="/seireader/0.39/sans.css">
```

The URL starts at the site root, including from `/app/` or its query-string
routes. A deployment under a path prefix must include that prefix in the link.
Keep the versioned directory when caching; a new font version gets a new URL.

Apply the face to the intended prose:

```css
.chapter-prose {
  font-family: "SEIHouse Sans", system-ui, sans-serif;
  font-synthesis: none;
  font-kerning: normal;
}
```

Keep the app's existing size, line height, spacing, and width for its first trial.
An italic needs `font-style: italic`; use `font-weight: 700` for actual Bold.
The CSS registers all styles, but the browser requests the faces that rendered
text uses. Do not preload all ten. A Regular-only page uses 69,192 font bytes;
Regular with its italic uses 141,632. Icons and all supported letters are in each
full file. Missing scripts, such as Chinese, still use the host's fallback fonts.

Set `lang` on the actual passage, for example `tr`, `ro`, `hu`, `ig`, `ku-Latn`, or
`uz-Latn`. Turkish/Romanian local forms and Hungarian capital spacing depend on
that language. Keep standard composition and mark features enabled. Optional
`font-variant-numeric: tabular-nums` selects tabular figures; `font-variant-position:
super` selects superscripts; `font-variant-numeric: diagonal-fractions` selects
fractions. Ordinary prose and numbers remain the defaults.

## Alternative: install the private npm tarball

The same Actions run includes `seihouse-seireader-0.39.0.tgz`. Copy it into the
app's `vendor/` folder and install it:

```sh
npm install ./vendor/seihouse-seireader-0.39.0.tgz
```

Import its CSS from the host entry point, before the host's prose overrides:

```ts
import '@seihouse/seireader/sans.css';
```

Vite processes the relative CSS font URLs and emits the font assets. Use either
this install route or the static ZIP route in an app, so the same faces are not
registered twice. The package has zero dependencies and no installation scripts.
It is marked private with `SEE LICENSE IN LICENSE`. Both the operative ecosystem
license and its short notice ship with it; this workflow does not publish to npm.
Existing imports of `@seihouse/seireader/styles.css` continue to register the
legacy `"SEIReader"` alias. Use one family stylesheet per integration.

## Installed in Development (NovelExpanded and the Workshop)

Installed on 2026-10-10 by Development PR #353, from this repository at
`93954df`. Development uses the npm tarball route for both families:

| Package | Tarball in Development's `vendor/` | Family names it uses |
|---|---|---|
| `@seihouse/seireader@0.39.0` | `seihouse-seireader-0.39.0.tgz` (`npm pack --ignore-scripts` at this repository's root) | `"SEIHouse Sans"` |
| `@seihouse/living-titles@0.1.0` | `seihouse-living-titles-0.1.0.tgz`, copied unchanged with its `release.json` | `"SEIHouse Display Soft"`, `"… Edge"`, `"… Ink"`, `"… Wide"` |

Development records each tarball's source commit and SHA-512 integrity in
`vendor/font-artifacts.json`, and describes them in `vendor/README.md`. Both are
`file:vendor/…` dependencies in its `package.json`.

**Where the faces load.** The shared host theme, `src/host/styles/theme.css`,
imports both stylesheets, so the `/app/` NovelExpanded app and the Workshop
register the same faces:

```css
@import "@seihouse/seireader/sans.css";
@import "@seihouse/living-titles/fonts.css";
```

Vite fingerprints the WOFF2 files into `dist/assets`, so new font bytes get new
URLs without a manual version directory. Development uses only Living Titles'
`fonts.css`; its runtime and React entry are not imported. The portable SEN
engine has no font dependency.

**Where the faces are chosen.** The Library names the fonts. SEN stays
brand-neutral. `src/library/stories/readerFonts.ts` (`LIBRARY_READER_FONTS`)
lists the choices, first one default:

- chapter text: SEIHouse Sans, then Noto Serif;
- chapter titles: SEIHouse Display Ink, then Soft, Edge, Wide, then Alegreya.

Each stack falls back to the theme's fonts for scripts SEIHouse does not cover,
for example `"SEIHouse Sans", var(--font-sans, system-ui), sans-serif`.

**How the Reader applies them.** The chapter body sets the reader's choices on
the chapter's `<article data-chapter-number>`: `font-family`, `font-size`,
`font-weight`, `font-synthesis: none`, `font-kerning: normal`, and the line
height through `--sen-text-line-height`. The title uses the chosen title font.
The article keeps `lang` set to the story's language. A reader changes these in
Reader Settings → Text:

- **Sizes:** 15, 17.2 (default), 18.5, 20 and 22px, set in rem.
- **Line spacing:** 1.5, 1.85 (default) and 2.15.
- **Weights:** 300, 400 (default) and 500.

The choices are kept on the device as `novelexpanded-reader-text-settings`. The
prose column is `34em` wide, measured in `em` rather than `ch` so every font gets
the same width. No host class or scoped CSS rule is needed; the 2026-10-02
`.seireader-host` handoff plan is superseded.

**What a release must keep.** Development depends on these. A release that
changes any of them needs a matching Development change:

- the family names above;
- the stylesheet paths `@seihouse/seireader/sans.css` and
  `@seihouse/living-titles/fonts.css`;
- weights 300, 400 and 500 with real italics, because the Reader offers all three;
- the four cut names. A new cut also needs an entry in `LIBRARY_READER_FONTS`.

### Updating the fonts in Development

When a font is refined, release it here first, then replace the tarball in
Development. Do not edit font files inside Development.

1. **Here: build and audit.**
   - SEIHouse Sans: bump the version, then run `python build_distribution.py`,
     `npm pack --ignore-scripts`, and
     `python verify_distribution.py <the web ZIP> --npm <the tarball>`.
   - Display: rebuild and validate Living Titles with the "Rebuild and validate
     in FONT-LAB" steps in `packages/living-titles/README.md`.
     Use the new tarball and `release.json` from `packages/living-titles/releases/`.
2. **Development: swap the tarballs.** Copy each new tarball into `vendor/`
   (and Living Titles' `release.json` as `<tarball name>.release.json`). Delete
   the old ones, and point the `file:vendor/…` dependencies in `package.json` at
   the new files.
3. **Development: refresh the lockfile.** Run `npm install`, then `npm ci` to
   confirm the lockfile installs cleanly.
4. **Development: record provenance.**
   - In `vendor/font-artifacts.json`, update `sourceCommit`, each `version`,
     `file` and `integrity` (the `integrity` npm records in `package-lock.json`).
   - In `vendor/README.md`, update the "SEIHouse fonts" section and add a dated
     history line.
5. **Development: verify.**
   - Run `npm run verify` and `npm run build`. Then confirm `dist/assets` holds
     the new `SEIReader-*.woff2` and `SEIHouseDisplay-*.woff2` files and no old ones.
   - With `npm run dev` running, run
     `node scripts/verifyNovelExpandedApp.browser.mjs`. It checks that the prose
     renders in a loaded SEIHouse Sans and that a Display cut restyles the title.
   - Look at a chapter at phone and laptop widths. A font whose widths changed
     can move line breaks and the Read Aloud highlight.

Ship the tarballs, lockfile and provenance together in one Development pull
request.

## Size and delivery choices

| Delivery | Font files | Font bytes | Intended use |
|---|---:|---:|---|
| Full family (default) | 10 | 712,464 (695.8 KiB) | All weights, languages and symbols in one face per style |
| Regular + italic only | 2 | 141,632 (138.3 KiB) | Explicit 400-only experiments; no other weights supplied |
| Seven subsets, all styles | 70 | 2,511,836 (2453.0 KiB) | Opt-in Unicode delivery when actual usage makes it worthwhile |

The full family is 71.6% smaller than storing all 70 subset files. The
subsets intentionally overlap Latin letters and prose punctuation to preserve
Latin accent shaping; combining accents must not be split into separate faces.
For Regular, the preferred vietnamese face alone is 38,500 bytes
and the full face is 69,192 bytes. The browser can request additional script
faces for mixed-language passages. Measure actual reading content before
choosing subsets.

For a controlled smaller ZIP: `python build_distribution.py --weights 400`
includes only Regular and Italic. Select `--weights 400 700` if bold prose is
also needed. A reduced bundle cannot supply omitted weights; choose the full
family when the app offers a weight switcher. Optional subsets use
`python build_distribution.py --delivery subsets` and retain their CSS order.

The ZIP manifest records every file's byte count and SHA-256. Distribution
checks reject extra source/history/reference files, wrong mappings, stale CSS,
missing faces, and font bytes that differ from the checked-in build. Generated
archives and npm caches stay in ignored `dist/`; they are not committed again.

The application bundle excludes OTF desktop files, old versions, Lab pages,
proof images, reference fonts, Python dependencies, and build/audit scripts.
Keep those in the development repo for comparisons and engineering checks.

## Permission and customization

The included `LICENSE` permits ecosystem users to customize the font and use it
in personal/commercial creative projects and embedded creative documents without
fees or user-count limits. Authorized SEIHouse products may ship it. Independent
app/product embedding and standalone font redistribution require written
permission. Distribute `LICENSE` and `FONT-LICENSE.txt` alongside the font assets.
The license covers Sans; Display and reference fonts/data retain their own notices.
