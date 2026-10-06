# Font Lab website

The repository now has a homepage at [`index.html`](../index.html), with the actual
Reader and Display fonts, an editable specimen, and links to every workspace.

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
Only the output directory is served; the build copies an explicit list of 62
public files, including Display's six web subsets per cut and `display/fonts.css`.
Archived font versions, proof images, development scripts, and the
source repository are excluded. The dependency-free SEIReader npm package remains
separate and uses a 17-file allowlist, including the operative Sans license and
both canonical and legacy family stylesheets.

## Work on the hosted Labs

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

## Verification

```sh
node --test tests/site.test.mjs
node build_site.mjs
```

The draft tests cover reloads, storage isolation, interleaved tab saves, original
draft-format compatibility, failed writes, blocked/corrupt storage, and safe
document identifiers. Each draft has a separate storage key, so saving a cut does
not rewrite other cuts. Unreadable records are kept and reported; valid cuts still
load, while genuine storage-access errors remain errors. Existing app distribution checks remain
in place. Desktop/mobile browser checks should exercise theme and font controls,
navigation, Save/reload, JSON downloads, and chapter feedback against the built site.
