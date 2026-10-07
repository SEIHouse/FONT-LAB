# NovelExpanded living wordmark study

Open `index.html` through the FONT-LAB website or a local HTTP server. This is a
visual mock for refining the homepage wordmark before porting it to Development.
The homepage treatment follows the owner's supplied mobile screenshot; its
SEIHouse emblem and landscape are copied from Development's host-owned public
assets. The serif comparison uses local Georgia as an approximation of the app's
Alegreya lettering. It is not a capture of the running application.

Select Soft, Edge, Ink or Wide, edit the wordmark/featured title, choose where
living lettering appears, and adjust color, capital spacing, motion axes,
strength and silent breathing tempo. Save the study as JSON or download an
animated transparent wordmark SVG. Study JSON is separate from cut JSON and is
not a font build input. This page does not persist or change shipped cut settings.

The mock generates 60 cached poses across the certified energy range using the
same isolated engine, compiled spacing and motion limits as the Display Lab.
The canvas covers every pose and stays fixed. Playback selects prepared poses;
reduced motion uses the resting pose, and hidden documents stop visual updates.

## Future menu music connection

Menu audio and Reader Chamber audio are separate systems. Neither is connected
here. The mock has no audio decoder, transport, AudioContext or audio dependency.
The page-local `NovelExpandedMock.setMotionSource({sample(seconds) {...}})` seam
accepts a normalized 0–1 motion value; the caller owns music, timing and smoothing.
Values outside the range are clamped; invalid values or thrown samples rest the
title. Passing `null` restores the silent breathing preview. For example:

```js
// Illustrative future adapter; there is no menuAudio implementation in this mock.
NovelExpandedMock.setMotionSource({ sample: () => menuAudio.smoothedEnergy() });
```

This seam is a mock interface, not a new published runtime contract. A future
menu adapter can read its own audio clock or energy without touching Reader
Chamber playback. External-source SVG export is disabled because an arbitrary
live signal is not a prepared reproducible loop. `dispose()` cancels preparation
and animation and releases the mock's signal reference.

## Build and verify

```powershell
.venv/Scripts/python.exe display/build_novel_mock.py
.venv/Scripts/python.exe display/verify_novel_mock.py
node build_site.mjs
```

`runtime/` is copied from the built `@seihouse/living-titles` package. The mock
uses its public core and browser player, including unique per-instance clips.
Rebuild with `build_novel_mock.py` when shared inputs or package source change;
stale certification/spacing blocks the build. Font production interfaces and
existing motion gates stay unchanged. The installable package and React entry
are documented in [packages/living-titles](../../packages/living-titles/README.md).

## History

- **2026-10-07** — Added the silent four-cut homepage study, serif comparison,
  prepared pose playback, separate future menu signal seam and responsive proofs.
