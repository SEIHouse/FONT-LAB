# @seihouse/living-titles

Private, installable SEIHouse Living Titles runtime, version 0.1.0. Development
and SEA can consume this same package. Menu audio and Reader Chamber audio stay
separate; neither is included or connected. The runtime has zero mandatory
dependencies. Its optional React entry requires React 18 or newer.

## Install in Development

Copy `releases/seihouse-living-titles-0.1.0.tgz` into Development's `vendor/`
directory, then install the local artifact:

```sh
npm install ./vendor/seihouse-living-titles-0.1.0.tgz
```

Commit the tarball, package lock and `release.json` provenance with the consuming
change. The tarball contains built ESM, TypeScript declarations, four full Regular
WOFF2 fonts, CSS and existing notices. Consumers need no Python or font compiler.
This is a private artifact delivery, not an npm registry publication. Installing
the FONT-LAB repository root still installs the existing Reader font package.

## React

```tsx
import { LivingTitle } from '@seihouse/living-titles/react';

<LivingTitle title="NOVELEXPANDED" cut="Soft" strength={0.7}
  color="#e6cc87" style={{ display: 'block', width: '100%', height: 28 }} />
```

The host owns the fixed title container. A text fallback is shown during
preparation or after errors. Geometry preparation is cancellable on prop changes
and unmount; independent instances have unique SVG clips. React StrictMode is
supported. `onError` reports preparation or option errors. `playing={false}`
pauses the visual clock without changing any audio.

## Browser and future music input

```js
import { createTitleScene, createTitlePlayer } from '@seihouse/living-titles';

const scene = await createTitleScene({ title: 'NOVELEXPANDED', cut: 'Ink' });
const player = createTitlePlayer(document.querySelector('#title'), scene);
// Later: the menu owner can supply its own normalized, smoothed signal.
player.setSource({ sample: () => menuMusic.normalizedEnergy() });
// On removal:
player.dispose();
```

`menuMusic` above is illustrative; the package creates no audio owner. A
`MotionSource.sample(elapsedSeconds)` returns 0–1. The source may read its own
music clock instead of the visual elapsed time. Invalid/nonfinite samples and
exceptions show the resting title; finite samples are clamped. Use the exported
`smoothEnergy` helper for the existing 120 ms attack / 480 ms release response.
Actual channel-aware audio measurement belongs to the audio owner.

Without a supplied source, the player uses a silent 60 BPM/four-beat breathing
loop. `createBpmSource({bpm,beats})` prepares other 1–10 second loops. Live input
is continuous and has no ten-second playback limit. `play`, `pause`, `seek`,
`setSource`, `setScene`, `setColor`, `getState`, and idempotent `dispose` are
available. Players pause visual updates in hidden documents and show rest for
the reduced-motion preference. Pausing or disposing never touches audio.

## Rendering and exports

`createTitleScene` prepares 60 cached poses in yielding chunks. Provide an
`AbortSignal` and `onProgress` to expose preparation/cancellation. Titles are
limited to 60 UTF-16 code units. Only the four reviewed cuts are accepted; cut
JSON and font builds remain unchanged. `strength` is 0–1; `capitalSpacing`
defaults on, and `axes` can independently disable thickness/slant/pen angle.

`renderTitleSVG(scene,energy,{color,idPrefix})` returns deterministic static
vectors. For multiple inline SVGs supply distinct `idPrefix` values; the DOM and
React players do this automatically. `exportAnimatedSVG(scene,{bpm,beats,color})`
exports a transparent declarative breathing loop with a static reduced-motion
fallback. It does not record arbitrary external music. Both SVG functions accept
`longestEdge: 1080 | 1920` and six-digit hex colors.

The canvas covers the full reviewed motion range and never changes with energy.
Compiled origins, advances and kerning stay anchored. Ink retains its tighter
limits (+1% thickness, +1° slant, +0.25° pen); other cuts use +3%, +1°, +2°.
Saved studies are not cut JSON. Media import, Mediabunny, MP4/WebM encoders, the
Lab UI and the NovelExpanded mock are excluded from the installable archive.

Optional static usage:

```css
@import '@seihouse/living-titles/fonts.css';
.resting-title { font-family: 'SEIHouse Display Soft', sans-serif; }
```

Static fonts are full Regular faces with existing OpenType features, including
`cpsp` and stylistic sets. Live vectors use the shipped cut defaults. Runtime
frames are objects from their creating package instance; do not serialize a
scene and treat it as a font or a transferable compiled scene.

## Rebuild and validate in FONT-LAB

```sh
python display/build_novel_mock.py
node display/pack_living_package.mjs
node --test tests/living-package.test.mjs
node display/verify_living_package.mjs
python display/verify_novel_mock.py
```

The builder rejects stale motion certificates, cut settings or spacing/font
hashes. Packed-consumer validation installs the real archive and checks imports,
types, React bundling and browser lifecycle behavior. See `dist/provenance.json`
and `releases/release.json`. Preserve `NOTICE.txt` and `SANS-LICENSE.txt`; this
private package does not change the existing Display licensing scope or grants.
