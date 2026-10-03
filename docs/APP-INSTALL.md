# Install SEIHouse Sans in an app

SEIHouse Sans 0.38 (formerly SEIReader) ships as static web fonts: five weights (300/400/500/600/700),
each with its real italic. The app needs WOFF2 files and CSS. It needs no Python,
font-building tools, JavaScript runtime library, or reference fonts.

## Recommended: the full web family

Use the `SEIReader-0.38-web-full.zip` from a successful **App distribution** GitHub
Actions run, or build it with `python build_distribution.py` in the font repository.
Actions retains these downloads for 30 days; its manual Run workflow button can
regenerate them from the current branch. This does not create a public npm release.
Extract the bundle into an app-owned, versioned asset directory such as
`public/seireader/0.38/`. Keep its `sans.css` next to its `fonts/` directory.
Asset/package names retain SEIReader for compatibility; the actual family is
SEIHouse Sans. Existing `fonts.css` / `"SEIReader"` integrations still work.

```text
public/seireader/0.38/
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
<link rel="stylesheet" href="/seireader/0.38/sans.css">
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
text uses. Do not preload all ten. A Regular-only page uses 63,624 font bytes;
Regular with its italic uses 130,052. Icons and all supported letters are in each
full file. Missing scripts, such as Chinese, still use the host's fallback fonts.

Set `lang` on the actual passage, for example `tr`, `ro`, `hu`, `ig`, `ku-Latn`, or
`uz-Latn`. Turkish/Romanian local forms and Hungarian capital spacing depend on
that language. Keep standard composition and mark features enabled. Optional
`font-variant-numeric: tabular-nums` selects tabular figures; `font-variant-position:
super` selects superscripts; `font-variant-numeric: diagonal-fractions` selects
fractions. Ordinary prose and numbers remain the defaults.

## Alternative: install the private npm tarball

The same Actions run includes `seihouse-seireader-0.38.0.tgz`. Copy it into the
app's `vendor/` folder and install it:

```sh
npm install ./vendor/seihouse-seireader-0.38.0.tgz
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

## First target: Development's NovelExpanded app

Inspected on 2026-10-02. This is a handoff plan; the Development repo was read,
and its app import-graph check was run. Its source and dependencies were not changed.
On the inspected Windows checkout, that baseline check fails at
`src/package/sen/inline-audio.ts` → `src/audio/InlineAudio.ts`. The component is
`InlineAudio.tsx`, alongside a different helper named `inlineAudio.ts`; extensionless
resolution encounters the helper's case-insensitive `.ts` path first. This is an
existing application/import-scanner issue, separate from the font package. Resolve
it in Development before claiming that its full integration/build gate passes.

The actual route is `/app/`, with `app/index.html` loading
`src/novel-expanded/main.tsx`. That entry imports `src/host/styles/theme.css`
and `@seihouse/sen/styles.css`. `NovelExpandedApp` reaches the reader through
Library `StoryPages` and the current `HarnessReaderSession`; it does not use
the older Reader Chamber settings screen.

Current chapter prose is the `TextHighlightEngine` root in
`src/components/harness-generation/development/HarnessReaderSession.tsx`:
`font-serif text-[1.075rem] leading-8`. At a 16px root this is 17.2px text / 32px
line height. The passage's article already sets `lang={locale}`. Its Reader
Settings currently holds Narration only. No new font preference schema is
needed for this initial trial.

For a host-only trial through the ZIP route:

1. Extract into `public/seireader/0.38/` and add the stylesheet link above to
   `app/index.html`.
2. Add `class="seireader-host"` to that HTML document's existing `<html>` tag.
3. Create `src/novel-expanded/seireader.css` with this scoped rule, then import
   it from `src/novel-expanded/main.tsx` after the existing style imports:

```css
.seireader-host [data-chapter-number] > .sen-text-highlight-root {
  font-family: "SEIHouse Sans", var(--font-serif, Georgia), serif;
  font-synthesis: none;
  font-kerning: normal;
}
```

For the npm route, use the CSS package import instead of the HTML stylesheet
link. Keep the host class and scoped rule. This selector follows the inspected
reader markup; revisit it if that markup changes.

The rule changes only chapter prose in the marked host. It preserves the
current UI fonts, titles, saved narration settings, and reader layout. It does
not add a SEIHouse font dependency to the portable SEN engine. The Workshop has
a separate `index.html`; mark and load that host explicitly if a comparison
there is wanted. The old Reader Chamber's font menu labels are not the active
NovelExpanded reader's font configuration.

After integration, run Development's `npm run check:app` and `npm run build`.
Inspect `/app/?story=<id>&read=1` in browser developer tools: font requests must
return WOFF2 bytes, and computed/rendered prose fonts must be SEIHouse Sans. Check
real italic, the actual language tags, unsupported-script fallback, and
13/15/17px Day/Night before changing typography preferences.

## Size and delivery choices

| Delivery | Font files | Font bytes | Intended use |
|---|---:|---:|---|
| Full family (default) | 10 | 658,048 (642.6 KiB) | All weights, languages and symbols in one face per style |
| Regular + italic only | 2 | 130,052 (127.0 KiB) | Explicit 400-only experiments; no other weights supplied |
| Six subsets, all styles | 60 | 1,911,336 (1866.5 KiB) | Opt-in Unicode delivery when actual usage makes it worthwhile |

The full family is 65.6% smaller than storing all 60 subset files. The
subsets intentionally overlap Latin letters and prose punctuation to preserve
Latin accent shaping; combining accents must not be split into separate faces.
For Regular, the preferred greek face alone is 41,112 bytes
and the full face is 63,624 bytes. The browser can request additional script
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
