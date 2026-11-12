# @seihouse/elemental-title

Private, installable SEIHouse Elemental Title runtime, version 0.1.0. Renders
semantic, readable name lettering with optional lightning, water, poison, fire,
frost, celestial, or void illumination, page-wide choreography budgeting, and
official familiar signatures (Quill: *Stormwrit* and *True North*) for any
SEIHouse surface. Zero mandatory runtime dependencies; requires React 18 or newer.

## Install in Development

Copy `releases/seihouse-elemental-title-0.1.0.tgz` into `development/vendor/`,
then install the local artifact:

```sh
npm install ./vendor/seihouse-elemental-title-0.1.0.tgz
```

Commit the tarball, package lock, and `release.json` provenance with the
consuming change. Import the stylesheet once in your app root, then render
`<ElementalTitle>`:

```tsx
import "@seihouse/elemental-title/styles.css";
import { ElementalTitle } from "@seihouse/elemental-title";

<ElementalTitle
  as="h2"
  element="lightning"
  color="light-dark(#8a5a12, #f6cf7f)"
  intensity="legendary"
  shadow="outlined"
  signatures={["quill/stormwrit", "quill/true-north"]}
>
  {readerName}
</ElementalTitle>;
```

String children are escaped by React. `as` supports `span` (default), `p`, and
`h1`–`h6`; choose a heading level appropriate to the document. Native attributes,
events, styles, and a DOM ref are forwarded. `element="none"` (default) preserves
the original plain text contract. `element` chooses the effect shape while `color`
chooses the CSS text color independently, including for plain text. Without `color`,
existing element palettes remain the default. Choose a color with enough contrast
against the host surface; CSS `light-dark()` can supply separate light/dark colors.
Font family, weight, line height and size inherit from the host profile. Consumer
classes override the low-specificity defaults.

| Prop         | Values                                                           | Default                               |
| ------------ | ---------------------------------------------------------------- | ------------------------------------- |
| `element`    | `none`, `water`, `poison`, `fire`, `lightning`, `frost`, `celestial`, `void`        | `none`                                |
| `color`      | CSS color value                                                  | element palette                       |
| `intensity`  | `common`, `rare`, `epic`, `legendary`; legacy `subtle`, `active` | `active`                              |
| `motion`     | `ambient`, `hover`, `burst`                                      | `ambient`                             |
| `size`       | `inherit`, `sm`, `md`, `lg`, `xl` (responsive)                   | `inherit`                             |
| `shadow`     | `none`, `soft`, `outlined`                                       | `outlined` for lightning/water/poison, else `soft` |
| `signatures` | official signature ids the user owns and enabled                 | none                                  |
| `playMoment` | `{ id: string; key: number; signature? }`                        | none                                  |
| `strikeKey`  | number (alias of `playMoment={{ id: "strike", key }}`)           | none                                  |
| `onMoment`   | `(moment: ElementalTitleMoment) => void`                         | none                                  |
| `timeScale`  | positive number; review aid only                                 | `1`                                   |

Rarity changes the glow, moving fill, outline, and particle count: common is
quietest and legendary is strongest. Hover or focus strengthens the selected
rarity, including in a containing button or link. Existing `active` intensity
remains available for current consumers.

Ambient motion runs while visible. Hover motion also responds to keyboard focus
on a containing button or link. Burst plays once (1.6 seconds) on pointer entry,
press, or focus; repeated input during the burst does not restart it. The title
never adds a tab stop or intercepts an action. The host owns interactive semantics.

Real text supplies the accessible name and layout. Decorative copies are hidden
from assistive technology and ignore pointer input. Fire has a moving letter fill
and scattered embers, anchored to at most eight measured glyphs (four visible on
mobile). The real text is never split, preserving shaping and wrapping. No Canvas,
video, animation dependency, or font request is added.

## Lightning and the elemental engine

Rank sets color; the familiar sets the element; bond tier sets strength. Effects
never change the name's color.

Lightning is the first effect built on the package's elemental engine
(`engine/`). The engine measures the title's letters once, then composes
frames of vector geometry into an SVG that overscans the ink box by about one em,
so arcs occupy the space around and between the letters without changing layout.

A lightning frame has a near-white core, a plasma edge, a tight glow and a wide
haze, drawn from separate `--et-arc-*` tokens. Every arc, twig and fragment
draws behind the letters (see [Depth](#depth-the-letters-are-the-front-plane)).
Most strikes lead with an arc that threads through
the letters' own ink band, emerging from one edge and heading into the next,
so the storm reads as part of the word rather than decoration floating near
it; strikes also jump between neighbouring letters, crawl under the baseline,
dive through the gap between two letters, strike down from above or lash off
the first or last letter. They taper unevenly, branch toward nearby letter
edges into thinner twigs, break into dark gaps and throw off fine fragments
that drift away. Strikes flash at full power, flicker, then rest at a
rarity-scaled opacity until the next strike replaces them, so a paused frame
still reads as one electric image. Between strikes, short crackles keep the
letters alive. Each strike also lights the edges of the letters near its
impact with a brief rim of arc light (see edge light below).

The letters keep a soft, rarity-scaled glow of their own, applied to the text
layer only so it never blurs the arcs. A soft band of light in the title's color
sweeps across them at irregular intervals, and each pass varies in speed, angle,
strength and sometimes direction, so the shine never settles into a visible loop.

A custom `color` keeps the letters exactly that color: the arc tokens are never
overridden by it. Lightning's `shadow="outlined"` draws a rank-tinted keyline,
mixed 58% toward black in dark mode and very faint in light mode. With no `color`
prop, it derives from the inherited text color. Its width is 0.035em capped at
0.85px, underneath the fill and above back arcs. **The keyline is lightning's
default when `shadow` is unset**; `soft` and `none` remain explicit choices, and
every legacy element keeps `soft` as its default. The keyline moves with the
letter. Forced colors remove it and all decoration.

### Depth: the letters are the front plane

The name is always the frontmost, sharpest thing. Every element draws behind it, so
its motion reads as a layer beneath the letters instead of competing with them at
the same depth:

- **Behind, never across.** The element's overlay sits under the real text (z-index 0
  under 1), and opaque letter ink swallows whatever falls under a stroke. Lightning's
  arcs, branches, twigs and fragments all live there; fire, frost, celestial and void
  embers rise from behind the letters.
- **Dimmer behind a letter.** A soft shade over each letter takes 60% of the light from
  whatever passes behind it and fades out about 0.2em past its ink, so an arc dims as it
  slips behind a letter and brightens again beside it. The shade is a luminance mask,
  so it only lowers the element's alpha: it works on any surface, never touches the
  letters, and is the same for every tier, so bond tiers keep their order.
- **In front is only the name itself.** Letter moments (a jolt, the ripple) move the
  letters, and the rim light and shine belong to the letters. Familiar signatures
  keep their own layer in front, because they run beneath the name and finish beside
  it without crossing it.

Drawing each frame once, behind the text, also halves the overlay's work: on the
crowded 24-name page, frames went from 20–22 to 28–30 per second with the page budget
on (390px, 4× CPU throttling).

### Recipes and tier programs

Props resolve internally into a recipe: `{ elements, tier, signature? }`. The type
allows several elements so custom familiars can combine them later, but **only
single-element recipes render in this phase**; a recipe with zero or several
elements resolves to no effect. `none` has no elements, and fire, frost, celestial
and void keep their CSS-only decoration because they are not in the registry.

Each registered effect declares a **tier program** as data: for every bond tier,
the moments it schedules, their cadence (delay ranges while ambient and while
engaged by hover, focus or burst, plus an optional lead before the first one) and
its tier parameters. Lightning's program holds what used to be hard-coded: arc
counts, branching, fragments, detail, resting opacity, flash life, arc weight,
jolt probability, rim strength, crackle splitting and the shine gaps. Ambient
titles keep the engaged pace lightning has always used (the original per-tier
ranges × 0.45).

Tiers never de-escalate. A higher tier never schedules fewer moments, never has a
slower cadence and never has a weaker parameter than the tier below it; every
parameter is "higher is stronger". A unit test checks this for every registered
effect. Signatures belong to familiars, not elements, so they are not part of a
tier program (see Familiar signatures below).

### Moments are timelines

A moment (strike, crackle, shine or a signature) is a **timeline**: cues at
millisecond offsets, built by a pure function of the measured stage, the tier and a
seeded random stream, so it is deterministic per seed and testable without a DOM.
Cue types:

- `frame`: an overlay frame (arcs, fragments, lights).
- `letters`: `LetterAnimation`s — `{ glyph, keyframes, duration, delay?, origin?, easing?, edge? }`.
  `delay` staggers each letter through Web Animations (no per-letter timers);
  `origin` pivots it around its own glyph box, e.g. `"50% 100%"` to grow, melt or
  hop from its foot. Keyframes accept only `transform`, `opacity`, `offset` and `easing`.
- `edge-light`: a rim of light around letter edges near a point, with a radius,
  strength and duration, on the title's `__flash` layer. It animates opacity only
  and never changes letter fill. Letters that carry their own light (a jolt's hot
  edge) get a feathered hole in the rim, so they are never lit twice.
- `shine`: one soft band of light across the letters.
- `scene`: authored vector primitives drawn on the overlays (see Familiar signatures).

Timelines may label beats (`{ label, at }`, e.g. "arrival", "act", "mark") so
multi-beat scenes can be authored and inspected. Every letters cue of a timeline
shares one promotion; later beats become Web Animation delays on the same copies.

### The conductor

A **conductor** owns every timer and animation of a title. It schedules moments
from the tier program, plays timelines cue by cue (one timer per timeline at a
time), and cancels everything on stop. The title only mounts the layers the
effect declares and hands them to the conductor. It stops the conductor (and
starts a fresh one if the title is still running) on pause offscreen, hidden
document, reduced motion, forced colors, engagement change, resize, text change
and unmount. Animations never accumulate: a newer rim light or shine replaces the
previous one, and finished letters are released.

Moments have a **priority** (signature > strike > crackle > shine). A higher or
equal priority moment takes over a shared layer or letter from a lower one; a
lower one cannot interrupt a higher one there. Each letter is owned by exactly one
letter track at a time.

### Moment requests and readouts

`playMoment={{ id, key }}` plays the named moment whenever `key` changes after
mount; unknown moments are ignored. Lightning plays `"strike"`, `"crackle"` and
`"shine"`. `strikeKey={n}` is an alias of `playMoment={{ id: "strike", key: n }}`.
Requests respect visibility, document state, reduced motion and forced colors and
never start an idle title's recurring schedule; requested strikes always jolt a
letter. `playMoment={{ id: "signature", key, signature? }}` plays one of the title's
signatures (see below).

`onMoment(moment)` is called when a moment starts, with its id, priority, whether
it was requested, its length, beat labels and cues (type, offset, beat, the letters
a letters cue moves and the primitive types a scene cue draws), without geometry.
Signature moments also report which signature played: `signature: { id, name }`.
Use it for review readouts or to sync sound.

### Time scale (review aid)

`timeScale` scales every moment's timers, overlay frame lives and Web Animations
together (0.25 plays at quarter speed). It exists for workbench review; leave it
unset in product UI. Changing it restarts the title's conductor.

### The letter engine

`stage.ts` measures every non-space grapheme using `Intl.Segmenter` and DOM ranges,
including wrapped lines, combining marks and joined emoji. Lightning still samples
at most 40 of these for its arc geometry. Measurement runs on text, font loading
and resize, never on animation frames. Empty names render plain text.

The real string remains the single layout and accessibility source. The
`aria-hidden` letter layer holds measured, empty glyph shells at rest. A moment
**promotes its whole glyph set at once**: one style snapshot and one mask update at
the start, one mask update when its letters are released together at the end.
Each moving copy contains the **whole browser-shaped text run**, sits at the ink box
origin exactly where the original text paints, and is clipped to its glyph's
slice; the matching region of the original is hidden only while the moment plays.
This preserves kerning, bidi, wrapping and continuous `background-clip: text`
gradients. CSS-animated layers (aura flicker, moving fill) continue in phase; the
lightning shine is sampled once per moment. In a ligature or connected script, a
movable piece is a slice of the shared shaped ink and can separate at the slice
boundary while it moves. Resting typography is always the original rendering.

- **Promotion cap:** at most **32 glyphs per title** are promoted at once. That
  covers typical names completely (DAO names run 10–25 letters). On a longer name,
  glyphs over the cap keep their resting ink for that moment instead of stuttering.
- **Slices:** slices tile the stage exactly, so resting copies look identical
  whichever layer draws a pixel. Each line splits into three bands — above the
  x-height, the x-height, and below baseline letters' overshoot and soft shadow.
  Above and below, a letter with no ink there lends its half to a neighbour that
  has some, so T and W arms, f hooks and g, j, y tails travel with their own letter
  under a 0.25em lift, an 8° lean or a 0.85–1.1 scale. Italic boundaries step along
  the slant in short steps (about 0.12em, at most 16 per band). Inner edges snap to the device pixel grid,
  read once per promotion, so copies and the masked original meet without a seam.
- **Compositor:** letters animate `transform` and `opacity` only, on the copies
  themselves, with pivots baked into the keyframes. While a letter animates, the
  browser rasterizes it on the compositor; at a fractional page position or under a
  drop-shadow halo this can shift its anti-aliasing by up to one device pixel for
  the moment's duration. At rest the title is always the original text.

### Lightning on the engine

Strike, crackle and shine are timelines driven by lightning's tier program; the
arcs, still frames and cadence are unchanged. A strike carries its overlay frame,
an edge light at its first impact (a 1.9em rim at 95% peak, as before the letter
engine) and, sometimes, one 180–260ms letter jolt: the letter nearest the impact
shakes, rotates slightly and settles exactly to rest, with an opacity-only white
edge beneath the rank fill. Ambient jolt probabilities are 12%, 30%, 55% and 80%
from common to legendary; engaged and requested strikes always jolt. The jolted
letter gets a feathered hole in the rim light. The jolt decision uses its own
seeded stream, so it never perturbs arc composition. Geometry is deterministic per
title text for the resting frame and seeded per session for strikes.

The Elemental Title Lab (`display/elemental/index.html`) is split into
tabs, and only the open tab runs its titles; `#<tab>` links straight to one:

- **Playground:** a live title in the dark and light themes side by side, with every
  prop, rank color swatches and a bond-tier strip. It turns the page budget off, so it
  always shows a title's own cadence.
- **Elements & ranks:** every element in both themes, and the rank × bond-tier grid at
  20px (one element and theme at a time: lightning, water or poison) comparing the default
  keyline with no outline.
- **Moments:** the choreography lab fires each moment on lightning, water, provisional poison and the test
  ripple at every tier (14–22px and 36px, dark and light, plus a name that wraps), with 0.25× slow
  motion and a readout of the last timeline's cues and beats.
- **Signatures:** Quill's review grid, shop, Familiar Look and rotation.
- **In context:** a profile header and comment list of Quill owners, and a crowded page
  of 24 legendary names (lightning, water or poison) with the page budget switchable on and off
  and a live count of moments per second.
- **Edge cases:** long unbroken names, mixed scripts, a wrapped name, inherited
  typography and a title inside a button.

### Water

Water is a **translucent wave passing through the name**. Its shoulder gathers,
the thin lip overturns, and its return current and broken reflections deform
independently as it travels. Layered transmission gradients leave clear areas
between the teal folds; titles at 24px and above add bounded SVG surface lighting.
Below 24px, the body, inner fold, reflections and wake retain the same geometry,
with nine poses and at most four animated paths; subpixel foam, spray and extra
surface layers are omitted along with the lighting filter. It travels across
one measured line at a time (wrapped lines each get a crest), behind the ink and
under the common depth mask. It never traces the letter outlines or hangs drops.
Its material colors are independent of the rank-colored text.

`playMoment={{ id: "wave", key }}` plays the wave. Material translation and letter
buoyancy use the same start, end and duration. Each letter rises as the crest
reaches it, leans with the slope, then dips and settles. Only transform changes;
the real text remains the layout and accessibility source. Seventeen compatible
Bézier poses are shared per material profile in a bounded immutable cache and
interpolated by native path animation (every other pose for small names),
with no per-frame measurement, JavaScript loop or React updates. Each moment
starts its own interval, including replays long after the title mounted. Browsers
with CSS path interpolation use Web Animations on the letter clock; WebKit's
fallback uses SVG animation. Both are cancelled when the material unmounts.
Material morphing, translation and buoyancy all respect the review time scale.

| Bond tier | Water behavior |
| --- | --- |
| Common | A low, broad ripple at the baseline; barely lifts the letters. |
| Rare | A rising, unbroken swell over twice Common's height, with a clear lift and lean. |
| Epic | A tall breaking curl with an open fold, low trailing current and fuller buoyancy. |
| Legendary | A towering double surge: a second breaking crest follows the first and lifts the letters again. |

The palette stays the same across tiers. Geometry, buoyancy and cadence provide
the progression. The four silhouettes remain distinct below 24px: Legendary's
second crest and its reflection use the existing wake and glint paths, so the
compact renderer keeps its four-path budget. Larger Epic and Legendary titles
also shed fine spray, with broken foam on Legendary. A static crest is shown initially and for reduced motion;
a live wave passes out of the name and rests between moments. The still frame
contains no SVG animation or spray. Existing page
budget and 32-glyph promotion limits still apply: long names keep their excess
letters at rest. Forced colors hide all decoration.

### Poison (provisional)

The original Water contour and droplets now belong to `element="poison"`.
Poison has a viscous green body, olive shadows, acid-green rims and pale green
highlights. It retains the same surface-tension geometry, hanging beads,
gather/release/drop timing, higher-tier pours and the weighted letter that sinks
as a bead grows and springs back when it falls. `drip`, `flow` and `shine` are its
moments. Common and Rare keep letters still; Epic and Legendary can pull a letter.

This is an intentionally provisional reassignment, not a finished Poison design.
A later Poison pass can refine viscosity, breakup and its own tier identity.
The droplet pull/release is retained as the starting point.

Both materials use engine frame slots behind the letters. Poison's resting edge
persists under drips; Water's static crest gives way to a traveling wave. Review
`timeScale` now scales material times as well as frame life and letter animation,
so slow-motion inspection preserves crest/lift and drop/release synchronization.

### The test ripple (test only)

`engine/test-ripple.ts` is a throwaway effect that proves the plug-in
model: a two-beat ripple (the wave, then a small settle overshoot) that lifts every
letter in reading order, wrapped lines included. It registers through the registry
and a tier program only, with no title code. It is **not a public `element` value
and not exported**; the workbench reaches it through the internal id
`"test-ripple"` with an explicit cast. Delete the file, its test and its
registration in `effects.ts` (and the lab row) to remove it.

### How to add an element

1. Create `engine/<element>.ts` exporting an `ElementalEffect`: its `id`,
   the `layers` it draws (`overlay`, `letters`, `edgeLight`), its `moments` with
   priorities, a `program` for all four tiers, an optional `still` frame, and
   `timeline(moment, stage, context)`.
2. Keep `timeline` pure: read only the stage, `context.params` and
   `context.random`. Return `null` for moments it does not play.
3. Use only `transform` and `opacity` in letter keyframes; start and end every
   letter at rest; give whole-word behaviors per-letter `delay` and `origin`.
   Everything else the element draws goes in its overlay frames, behind the letters
   and under the depth shade (see
   [Depth](#depth-the-letters-are-the-front-plane)); nothing crosses in front of them.
   An element that is not arcs gives its frames a `material` and a renderer (as water
   does); its own frame slots keep separate moments from replacing each other, and a
   still frame that should stay under every moment sets `persist`.
   An element that needs more room around the name than the default overscan sets
   `overscan` instead of growing it for every element.
4. Make every tier at least as strong as the one below (more moments, faster
   cadence, higher parameters). Signatures belong to familiars, not elements.
5. Register the effect in `effects.ts`. Add its id to `ElementalTitleEffect`
   only when it is ready to be public, with palette tokens under
   `[data-element="<element>"]` in `elemental-title.css`.
6. Add a lab row, unit tests (determinism, the tier invariant runs automatically)
   and screenshots in both themes; check reduced motion and forced colors.

## Familiar signatures

At a qualifying bond, each **official** SEIHouse familiar can add an exclusive extra
animation around the name, made from its element's material. A signature briefly
_suggests_ the familiar; it never illustrates it, and it never moves or recolors the
letters. A familiar can own several signatures: they are a customization product that
users earn or buy one by one. Custom familiars (which may mix elements) can never get or
create one.

**Signatures are fancy underlines with a unique ending.** The motion runs beneath the
name and finishes with a mark beside it (a flourish, a star): a small exclamation point to
the side of the name. Nothing crosses above or through the letters. A unit test holds every
registered signature to this on one-letter, 40-letter and wrapped names. The design
brief, [`docs/FAMILIAR-SIGNATURES.md`](../../docs/FAMILIAR-SIGNATURES.md), locks this idea,
lists Quill's choices as starting points rather than rules, and leaves each element's
material and motion open; hand it to anyone (or any model) designing a new signature.

```tsx
<ElementalTitle
  element="lightning"
  intensity="legendary"
  color={rankColor}
  signatures={["quill/stormwrit", "quill/true-north"]}
  playMoment={
    previewKey ? { id: "signature", key: previewKey, signature: "quill/true-north" } : undefined
  }
>
  {readerName}
</ElementalTitle>
```

- **`signatures`** (additive prop) lists the signatures this user owns and has enabled.
  `ElementalTitleSignature` is the union of official ids, today
  `"quill/stormwrit" | "quill/true-north"`. **The host app decides which ids a user may
  pass** (earned, purchased, enabled); the package has no registration API, so no one can
  add a signature at runtime.
- A signature plays only if the title's bond tier meets the signature's **minimum tier**
  (both of Quill's are legendary) and the title's `element` is the signature's element
  **and** runs on the elemental engine. Other ids are ignored, with a development-only
  console warning that says why.
- **Selection.** When a signature plays with several enabled, the title draws from
  a seeded "bag": every enabled signature plays before any repeats, and never the same one
  twice in a row. With one enabled, it always plays that one.
- **Requests.** `playMoment={{ id: "signature", key }}` plays the next signature from the
  bag: use it for an app action tied to the familiar (finishing a chapter, a bond
  milestone). `signature: "quill/true-north"` asks for a specific one (a "Preview" button
  in a shop or on the Familiar screen). A shop previews what it sells by passing that id in
  `signatures` for its preview title. Requests for ids the title cannot play are ignored
  with a development warning.
- `onMoment` reports `signature: { id, name }` for signature moments.

### When a signature plays

**Never on its own.** A signature plays in two ways, whatever the title's `motion`:

- **Someone touches the name:** a mouse or pen pointer enters it, a finger lands on it, or
  it (or a containing link or button) takes keyboard focus. **Every touch plays it again**
  once the previous play has finished.
- **The app asks** with `playMoment`: a shop or Familiar screen preview, or an action tied
  to the familiar. Requests take the stage from a touch-started signature elsewhere on the
  page.

Only while the title is visible and running (not under reduced motion or forced colors),
and never on top of itself: a touch while it plays is ignored. Once started, a signature
plays to its end: moving the pointer away or lifting the finger does not cut it short (a
`hover` or `burst` title stays engaged until it finishes). A signature may set a minimum
gap between plays with `cadence.cooldown` (default 0), or `null` so only the app can play
it.

**The element keeps going.** A signature plays on top of the element's own animation: the
lightning keeps striking, crackling and shining on its usual schedule, before, during and
after the signature, whether or not the name is touched. Where both use the rim light, the
signature's takes priority while it plays.

### Page budget

All titles of a page share one coordinator:

- **At most one signature plays at a time.** Requests arriving within 40ms compete: the
  app's requests beat touches. Among equals, **the title that played least recently on
  this page goes next** (never played counts as least recent), then the most visible. The
  others lose; there is no backlog, so a name touched while another signs simply doesn't
  sign (touch it again once that one ends). A request preempts a touch-started signature
  already on screen.
- **Whole-word letter moments** (moments that move more than one letter, such as the test
  ripple) are capped at **3 at once** page-wide. Explicit requests always play (they count
  toward the cap); single-letter accents such as a lightning jolt never count.
- **Constrained devices** (4 or fewer logical cores, or 4GB or less of device memory)
  render signatures lighter: no blur glow on primitives and half the fragments.
- **Ambient moments share the page** so a page full of strong names stays smooth.
  Every running ambient title joins with its expected moment rate. Once the page passes
  16 ambient moments a second (8 on constrained devices; about two legendary lightning
  titles), every ambient cadence stretches by the same factor, so tiers keep their
  order. Titles less than half visible stretch twice as much. Single-letter jolts share
  4 slots (2 on constrained devices), and the last half go only to titles in view; a
  strike without a slot still plays, with its letter at rest. Requests (`playMoment`),
  signatures and hovered, focused or bursting titles are never budgeted, and reduced
  motion and forced colors behave as before.
- Idle titles do no work: the coordinator holds a timer only while requests wait for a
  decision, and an untouched title holds none for its signatures.

Three host hooks, read from the nearest ancestor:

- `data-elemental-performance="constrained"` or `"full"` forces the rendering tier (a
  battery saver setting, or a design review).
- `data-elemental-scope` gives the titles inside an element their own signature turns.
  Each scope still plays one signature at a time, and the ambient budget stays
  page-wide. The workbench review grid uses one scope per title so candidates replay
  side by side; product pages normally need none.
- `data-elemental-budget="off"` switches the ambient budget off (a review aid; the
  workbench playground and the crowded-page comparison use it).

Styling hook: `--et-signature-accent` overrides a signature's accent color, or turns it
off with `none`.

Frame timing, measured in the workbench at 390px with 4× CPU throttling, no pointer over
the page and the lightning running as usual:

- A signature on a shop-sized page plays at 49–56fps with no long tasks, full or
  constrained. On the whole Signatures tab (about 20 other legendary titles, sharing the
  page budget) it plays at 52–58fps with no long tasks.
- A crowded page of 24 legendary lightning names runs at about 25fps with the budget and
  under 4fps without it (13 against 93 lightning moments a second).

The Playwright checks fail on any long task over 50ms during a signature on the
shop-sized page, and unless the crowded page runs at least 3× smoother with the budget.

### Scenes and primitives

A signature is a timeline like any other moment. Its `scene` cues play authored vector
primitives on the title's overlays: **back** (behind the letters, hidden by their ink like
the arcs) or **front** (in front of them; kept thin so the name is never hidden for more
than a moment). Primitives paint with the element's material tokens (for lightning
`--et-arc-core`, `--et-arc-plasma`, `--et-arc-glow`, `--et-arc-haze`) plus an optional
signature accent edge. They never touch letter color, fill or background, and each
beat's primitives are built when that beat starts, so the work is spread across the
scene. Every signature layer is `aria-hidden` with `pointer-events: none`, stays inside
the overlay's overscan (about 0.8em to each side, 1.4em above, 0.65em below) and is
removed when the scene ends or stops. Ancestors with `overflow: hidden` clip it.

**Anchors** (`anchors.ts`) turn the measured stage into positions, with offsets in em:
the name's `start` (first line) and `end` (last line); levels `top` (cap height),
`x-height`, `middle`, `baseline` and `bottom` (descenders) of any line; a glyph (`first`,
`last` or an index, clamped) and a point across its box; and a bounding ellipse around the
name. Lines come from the glyph boxes, so one-letter, 40-letter and wrapped names all
resolve.

**Wrapped names.** Scenes treat the name as a block of lines and choose deliberately:
Stormwrit signs each line in turn, lifting the pen between lines, and puts its flourish
after the last line; True North sweeps beneath the last line, across the width of the
whole block, with its star after the last word.

| Primitive      | What it does                                                                                                                                                                                                                                                                                 | Built with                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **Stroke**     | An anchored path that draws on, holds and draws off (`erase` from its start or `retract` into it). Tapered, with optional lightning roughness and dark gaps (`geometry.ts`), and it can cross between back and front along its length (`front` intervals). Optional flicker and accent edge. | `stroke()`                    |
| **Traveler**   | A bright head that rides a stroke exactly as it draws, shedding small sparks (shard rendering).                                                                                                                                                                                              | `traveler()`                  |
| **Shape**      | A small authored shape (a four-point star) with group keyframes around its centre: ignite, stretch its points, snap back, flare and wink out, scaled and rotated.                                                                                                                            | `star()`                      |
| **Dissolve**   | Fine fragments released along a stroke (in the direction it draws off) or thrown from a point, drifting and fading.                                                                                                                                                                          | `dissolveStroke()`, `burst()` |
| **Edge light** | The existing `edge-light` cue: letter edges catch the light near a point. With `to`, the light travels and fades in and out as something passes. No letter motion.                                                                                                                           | `edge-light` cue              |

Primitives are an **open set**: a discriminated union (`ElementalScenePrimitive` in
`types.ts`) plus a renderer map (`sceneRenderers` in `scene-player.ts`). A new primitive
(a particle formation, flipping pages, freezing the element's own effects for a beat)
adds a union member, a builder in `scene.ts` and a renderer; the conductor and the title
do not change. Renderers receive the overlays themselves, so a primitive can also act on
the element's own drawing.

### Quill's signatures

Quill, the default familiar ("an indigo celestial archive fox who pairs a novelist's
imagination with a reviewer's precision"), ships two lightning signatures, both at
legendary bond with Quill's gold accent (gold in dark mode, deeper gold in light mode):

- **Stormwrit** (`quill/stormwrit`), "Quill signs your name", about 2.5s. _Arrival_: a
  spark ignites just before the first letter, below the baseline. _Act_: it travels
  beneath the name like a pen nib, leaving a thin line of crackling electric ink that runs
  behind descenders while letter edges catch the light. _Mark_: past the last letter the
  ink sweeps up and back into a curling flourish (a fox's tail, a signature's last stroke)
  and ends in a spark pop. _Exit_: the ink crackles away into fragments, start to end.
- **True North** (`quill/true-north`), a compass star, about 2.6s. _Arrival_: a tiny
  four-point star ignites just past the end of the name. _Act_: its lower point stretches
  into a thin needle that sweeps beneath the whole name, right to left, like a compass
  needle swinging, while letter edges catch its light. _Mark_: the needle snaps back into
  the star, which flares. _Exit_: it winks out with a few fragments.

### How to add a familiar signature

Start from the design brief, [`docs/FAMILIAR-SIGNATURES.md`](../../docs/FAMILIAR-SIGNATURES.md).

1. Create `engine/signatures/<name>.ts` exporting `defineSignature(...)` with
   its `id` (`"<familiar>/<name>"`), `name`, `familiar`, `element`, and optionally
   `accent`, `minimumTier`, `cadence`. Then write its `timeline`. The id is permanent; the
   name is what users see.
2. Compose `timeline(stage, context)` from `sceneAnchors(stage)` and the builders in
   `scene.ts`. Keep it pure (stage, `context.random`), label its beats and keep it brief
   (under 5s). Put each beat's primitives in its own `sceneCue(beat, at, primitives)`.
3. Make it a fancy underline with a unique ending: motion beneath the name, the ending
   beside it, nothing above or through the letters, parts in front of the letters thin,
   and no letter motion or color. Quill's timing, beats, sizes and accent are starting
   points, not rules (see the brief). Stay inside the overscan, or grow it. Decide how
   wrapped names behave and say so in the file.
4. Add one line to `signatures/official.ts` and the id to `ElementalTitleSignature`.
   Retiring a signature removes the same file, line and union entry.
5. Need a new kind of motion? Add a primitive (union member, builder, renderer) instead
   of special-casing the conductor.
6. Check it in the Elemental Title Lab's Signatures tab (`display/elemental/index.html#signatures`) (side by side, slow
   motion, accent off, constrained device, both themes, a wrapped name) and run the
   signature unit tests, which hold every registered signature to the locked rules
   automatically (Quill's own tuning is tested separately).

Element and engine code (`engine/*.ts`) never names a familiar; a unit test
enforces it.

### Future signatures

How five planned signatures map onto primitives. "New" primitives are not built yet.
Each will follow the underline rule: it moves beneath the name and keeps its motif for
the ending beside it. For example, Timekeeper's ring becomes a sweep under the name that
freezes the element's particles at its end, and Stargazer's constellation gathers past
the last letter.

| Familiar — signature            | Scene                                                                                            | Existing primitives                                               | New primitives                                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------- |
| Galaxy Octopus — Stargazer      | stars gather into a constellation, then drift away; a bigger moment forms a tiny rotating galaxy | shape (stars), stroke (constellation lines), dissolve, edge light | particle formation (gather/disperse), rotating particle field |
| Celestial Guardian — Timekeeper | a luminous ring passes behind the name while nearby particles freeze, then catch up              | stroke (ring, back/front), traveler, edge light                   | freeze the element's own effects for a beat                   |
| Phoenix — Rekindled             | an ember travels beneath the name and rises into a brief wing shape                              | traveler (ember), stroke (rising trail), dissolve                 | particle formation (wing)                                     |
| Living Grimoire — Spellbound    | small glyphs turn like pages at the name's edges, then dissolve into ink                         | dissolve, edge light                                              | flipping symbol (page turn)                                   |
| Nine-tailed Fox — Moonveil      | wisps curl from the final letters into the suggestion of several tails before fading             | stroke (tapered curls, several at once), dissolve, edge light     | none (a fan of strokes from one anchor)                       |

Effects pause offscreen and when the document is hidden. Reduced motion keeps static
illuminated lettering: fire drops its particles and lightning keeps a single still
frame of arcs with no animation, no moments and no signatures. Forced colors use native readable
text and hide every decorative layer. Before hydration or without browser observers,
text is still readable and lightning draws nothing until the letters are measured.
Palettes follow the host's `color-scheme` via the UI `data-theme` / `.sh-theme-*`
scopes. Long names wrap without truncation. Animation and decoration do not change
geometry; changing the text itself can naturally change its height. The host owns
any space reservation required for asynchronously loaded text, and any
`overflow: hidden` ancestor will clip arcs that reach beyond the title's line box.
