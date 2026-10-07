# Display Engine Step 6: Living Titles

The [Display Lab](../display/lab/index.html) authors title artwork from the
shared engine, driven by a local music clip or a BPM loop. This phase covers
Lab authoring and SVG/video downloads. Motion settings are separate from saved
cuts, font builds and font package interfaces.

## Rendering and limits

The page generator embeds a private factory containing the exact shared engine
source, the shared stroke helper and compiled-spacing helper. Each instance owns
its parameters, frame-local glyph cache and clip definitions. It freezes the
starting cut's compiled origins, advances, kerning, alternate choices and `cpsp`.
Preview, SVG and video consume one prepared vector sequence and its timestamps.
The union of loop ink bounds plus conservative pen/miter padding sets a fixed
canvas for the whole loop. No font, script or external clip resource is needed
to play an exported SVG.

| Profile | Thickness | Slant | Pen angle |
|---|---:|---:|---:|
| Soft living-v1 | up to +3% | +1° | +2° |
| Edge living-v1 | up to +3% | +1° | +2° |
| Ink living-v1 | up to +1% | +1° | +0.25° |
| Wide living-v1 | up to +3% | +1° | +2° |

Strength scales offsets from zero to 100%; disabled axes keep their starting
values. These are positive offsets bounded by the agreed 3%/1°/2° caps. Ink's
smaller reviewed envelope preserves the six-pixel ordinal counter gate at
intermediate raster phases. Wide's circular pen is invariant under rotation.

BPM defaults are 120 BPM, four beats, two seconds and 30 FPS, paused. BPM/beat
combinations must yield 1–10 seconds. Local audio clips select a start time and
1–10 second length. Music is processed locally, including selected-range
decoding; channel RMS sums squares before averaging, retaining antiphase energy.
Attack is 120 ms, release is 480 ms; silence rests and both sampled loop edges
ease to the starting cut. Preparation yields every four frames, supports abort,
and publishes a sequence only after complete preparation. Scene edits stop and
invalidate it. AudioBufferSources, media inputs, encoders and temporary URLs are
released on cancellation/errors; navigation closes the audio context.

SVGs use discrete SMIL opacity changes, internal clip definitions, accessible
titles and a static `prefers-reduced-motion` fallback. This follows SVG's
[secure animated image processing mode](https://www.w3.org/TR/SVG/conform.html#secure-animated-mode).
Video probes actual dimensions and optional audio before encoding. It prefers
MP4/H.264 with AAC, then WebM/VP9 or VP8 with Opus, with the real extension shown
in the Lab. The local library's [codec support guide](https://mediabunny.dev/guide/supported-formats-and-codecs)
describes browser availability. Audio is optional and initially off. SVGs stay
transparent; video gets the chosen solid color. Output is 1080 or 1920 pixels
on the longest edge, with even video dimensions.

## Construction and reviewed witnesses

The flat-terminal helper rejects distant Beziers by their conservative control
boxes before sampling contact. Its successful existing output remains exact;
the regression compares all 815 encoded/alternate engine inputs per cut at
rest and maximum motion against the original contact algorithm.

Fractional motion weights exposed a Skia Boolean failure on almost coincident
Cyrillic stroke edges. The shared Display union now retries only a failed
operation, rounding controls by at most .001 of a 2000-UPM font unit—.0002 px
at the 400 px gate. It retains both inputs and throws if recovery fails.
Successful existing unions are unchanged. The frozen regression fails with
the original operation and passes with the shared retry. Reader construction
keeps its existing path.

The final CFF pen can also introduce a one-unit edge when it rounds cubic
controls after native cleanup. Display encoding now inspects the encoded
outline and applies the existing point cleanup only when that rounding leaves
an edge shorter than the shape gate's two-unit threshold. Clean charstring
programs remain exact; unresolved debris still raises an error. The frozen
Wide numerator-7 regression demonstrates the defect and its construction fix.

Motion fixtures live separately in `tests/fixtures/display-motion-topology/`.
The exploratory probe writes candidates only under `dist/`; the release gate
reads reviewed fixtures and cannot refresh them. Each cut covers all 815 engine
glyph inputs, including numeric, language and stylistic alternates, at rest,
all seven nonzero axis corners and 25/50/75% intermediate breaths. Native union,
final CFF outline debris/spikes/overlap and actual SVG raster clearance checks
remain active. Letters/numbers and unencoded alternates retain the Step 1
aperture policy; all other symbols retain construction and closed-counter
checks. Fixed resting white-space witnesses remain protected after applying
the slant delta, in addition to each state's reviewed topology.

Some small holes cross the raster's span-based “substantial counter” threshold
as weight changes. Reviewed state counts record that classification; fixed
resting witnesses still require the original hole to stay white and connected.
For example, Soft's ampersand retains both holes, with no filled-counter
exception. Dense ordinal tests additionally check 101 energies for each of
seven axis subsets (707 poses per cut). No glyph design or cut JSON is patched.

The certificate binds sources and the full immutable witness inventory. Any
failure or digest change disables exports until the profile is reviewed and
recertified. Resting vector frames must match the existing static Lab artwork
exactly, and frozen widths must match compiled spacing. Motion topology is
reviewed from that live SVG artwork separately from the static native-font
fixtures. Ordinary drafts remain static Lab drafts.

The two existing render paths have three baseline counter differences: Edge
Ƙ, Ink Ħ and Wide Æ have an additional enclosed white area in the live SVG
compared with their current fitted CFFs. Motion preserves the live artwork's
complete details and its separately reviewed witnesses. This phase preserves
the existing static font outputs and native fixtures; it does not claim native
font/SVG outline equivalence. Their resting title spacing remains subject to
the agreed 0.5% gate.

## Proofs and validation

[All-caps and mixed-case animated proofs](proofs/display-step6/index.html)
use the same prepared frame renderer as the Lab. They include every shipped
cut and transparent SVG downloads. The proof page also respects reduced motion.

```sh
npm ci --prefix display
node display/build_living_media.mjs
node --test tests/living-titles.test.mjs tests/display-terminal-bounds.test.mjs
python -X utf8 display/verify_motion.py
python -X utf8 display/build_display_page.py
python -X utf8 display/verify_living.py
python -X utf8 display/verify_lab.py
python -X utf8 verify_display_spacing.py
python -X utf8 verify_shared_engine.py
python -X utf8 verify_display_shapes.py
python -X utf8 verify_display_subsets.py
python -X utf8 display/verify_production.py
node build_site.mjs
```

Use the project's `.venv` on Windows. Motion/browser gates require the existing
fontTools, skia-pathops, FreeType, uharfbuzz and Playwright tools; install
Chromium with `python -m playwright install chromium`. The video timestamp gate
also requires `ffprobe` from FFmpeg. Mediabunny and esbuild are exact locked
development dependencies, and the local bundle carries Mediabunny's MPL notice.

`verify_motion.py --write-certificate` certifies passing sources only after
separate fixture review; it never rewrites those fixtures. CI recomputes this
gate, checks the local bundle and generated Lab for drift, and exercises actual
SVG/MP4/WebM playback, cancellation, audio clocks, codec rejection, corrupt audio
and 360–430 px layouts. Video bounds allow two pixels of codec tolerance,
decoded coverage allows 3%, and audio/video starts/ends must agree within one
frame. Resting-title widths retain the 0.5% built-font gate. The existing fresh
Reader preservation, static Display shape, license/subset and per-cut
FontBakery gates remain required at 0 FAIL / 0 WARN.

The initial Step 6 validation certified all four profiles with **0 flags**:
35,860 glyph/state constructions and SVG rasters, plus 2,828 dense ordinal
poses. The browser gate passed all four cuts, standalone/image SVG playback,
1080/1920 px video, MP4/AAC and WebM/Opus, lifecycle checks and ten phone states.
The terminal-helper regression retained exact SVG output for 6,520 inputs/poses.
The Python suite passed 89 tests.

A fresh Regular-only rebuild passed the existing static gate on 3,268 glyphs
and 6,536 renders, with 0 FAIL / 0 WARN from both FontBakery profiles per cut.
All 32 Display font deliveries retained their normalized font tables, and
latin-basic stayed below 25 KB. All ten Reader styles (20 full OTF/WOFF2
deliveries) retained their outline, metric, layout, name and hint tables; the
historical 0.35 preservation gate also passed. Rebuilds are table-identical
rather than byte-identical because the build writes new `head` timestamps and
derived checksums. Existing shipped font files remain unchanged. Resting title
widths passed all 888 samples with a maximum difference below 0.065%.
