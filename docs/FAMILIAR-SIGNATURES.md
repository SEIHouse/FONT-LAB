# Familiar signatures: design brief

Read this before designing or building a familiar signature for `ElementalTitle`.
It locks the **idea** of a signature and very little else. Everything about how one looks
and moves is open. The engine contract and API live in
[`packages/elemental-title/README.md`](../packages/elemental-title/README.md)
under "Familiar signatures".

Its guidance comes in three kinds, and they are not equally firm:

1. **Locked:** the founder's decisions. Don't change these without SENSEI.
2. **Starting points:** what worked for Quill's first two signatures. Change them when a
   new idea needs it, and say why in the pull request.
3. **What the engine does today:** current limits. Extend the engine when a design needs
   more; don't shrink the design to fit.

These rules come from two signatures, both lightning and both Quill's. Revisit the starting
points when the first signature for another element is built, and update this brief.

## Locked

> **A familiar signature is a fancy underline with a unique ending.** Something travels
> beneath the name and finishes with a mark beside it, like an exclamation point.

- **Beneath and beside.** The line runs under the name; the ending happens beside it. Nothing
  goes above the letters or through them: no line over the top, no ring around the name,
  no strike-through. The line may brush the feet of the letters and pass behind descenders
  (g, j, p, q, y). A unit test holds every registered signature to this on one-letter,
  40-letter and wrapped names (`tests/elemental-title.test.mjs`, "is a fancy underline").
- **The letters are left alone.** No letter motion, and no change to letter color, fill or
  background: rank sets the color. The name stays readable the whole time, so anything that
  passes in front of the letters is thin and brief.
- **It answers someone, every time.** A signature never plays on its own. It plays when
  someone touches the name (a mouse over it, a finger on it, keyboard focus), again on every
  touch once the last play has finished, or when the app asks: a shop preview, or an action
  tied to the familiar (finishing a chapter, a bond milestone, and so on). The engine
  handles this. A designer only decides what plays.
- **The element keeps going.** A signature plays on top of the element's own animation. The
  lightning (or any element) keeps running before, during and after it, touched or not.
- **It clears itself away.** Nothing lingers once it ends. That also keeps an underline from
  reading as a link.
- **It belongs to an official familiar** and is made of that familiar's element. It
  suggests the familiar without illustrating it. A user can own several.
- **Accessible.** No signature under reduced motion or forced colors. Every layer is
  decorative (`aria-hidden`, no pointer events). It stays brief (well under 5 seconds).

## Starting points (tuned on Quill)

Use these until an idea needs something else.

| What            | Quill's choice                                                                          | Feel free to                                                                 |
| --------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Length          | about 2–2.6s                                                                            | go shorter or longer (under 5s) if the motion needs time to read             |
| Beats           | arrival, act (the line), mark (the ending), exit                                        | use any labelled beats: two, three, five                                     |
| Ending          | one mark past the last letter, rising up to cap height and a little above               | end at the start of the name, end in two places, or rise higher              |
| Size            | ending about half an em; line about as thick as the element's own arcs                  | go bolder, finer or smaller if it still reads on a 20px name                 |
| Accent          | one extra color (Quill's gold), which hosts can switch off                              | use none, or pick the familiar's own                                         |
| Direction       | Stormwrit writes left to right; True North sweeps right to left                         | start in the middle, move in a broken rhythm, gather speed, rise from below  |
| Names that wrap | underline each line in turn (Stormwrit), or the last line across the block (True North) | do something else; just decide it and write it down in the file              |
| Replays         | every touch replays it once the last play ends; one signature on screen at a time       | set a minimum gap with `cadence.cooldown`, or `null` to play only on request |

Two signatures of the same element should differ in their idea (Stormwrit is writing, True
North is a compass), not only in color or timing.

## The open space

Everything about how the line and the ending look and move is open, per element and per
familiar:

- **The line's material and behavior:** ink written by a nib, a needle swinging, poison
  dripping, mist creeping, frost growing, embers smoldering, roots spreading, starlight
  threading, ripples on water.
- **The ending:** a flourish, a star flaring, a burst of mist, a black hole collapsing, a
  bloom, a crystal shattering, an ember rising, a page turning.

Some sketches to show the range. They are prompts, not specs, and apart from Quill's two
none is built. Don't copy them; beat them.

| Element                                | Line (beneath)                               | Ending (beside)                                                 |
| -------------------------------------- | -------------------------------------------- | --------------------------------------------------------------- |
| Lightning: Quill, Stormwrit (shipped)  | a pen nib writes crackling electric ink      | the ink sweeps up into a curling fox-tail flourish and pops     |
| Lightning: Quill, True North (shipped) | a compass needle sweeps from a star          | the needle snaps back into the star, which flares and winks out |
| Poison                                 | droplets gather and drip beneath the name    | the pool bursts into a ball of mist                             |
| Void                                   | a mysterious mist creeps underneath the name | the mist gathers into a small black hole that swallows itself   |

## What the engine does today

- **Lightning, Water, and provisional Poison run on the elemental engine.** A poison or void
  signature needs its material tokens wired into signature scene rendering (today scenes use
  `--et-arc-core`, `--et-arc-plasma`, `--et-arc-glow`, `--et-arc-haze`).
- **Primitives:** stroke, traveler, shape (a four-point star), dissolve and the edge-light
  cue. Drips, mist clouds and a vortex will each need a new primitive: a union member in
  `types.ts`, a builder in `scene.ts` and a renderer in `scene-player.ts`. The conductor
  and the title never change for a new signature.
- **Drawing space:** the overlay reaches about 0.8em to each side, 0.65em below and 1.4em
  above the name; anything outside is clipped. A design that needs more room (a long drip)
  can grow the overlay in `elemental-title.css`.
- **Phones:** each beat builds its own pieces when it starts. On constrained devices,
  primitives drop blur glow and half their fragments. Check frame timing at 4× CPU
  throttling.

## Building one

1. **One file, one line, one union entry.** Add
   `packages/elemental-title/src/engine/signatures/<name>.ts` using
   `defineSignature`. Add one line to `signatures/official.ts` and add its id
   (`"<familiar>/<name>"`) to `ElementalTitleSignature`.
2. **Compose from anchors and primitives.** `sceneAnchors(stage)` gives the name's start
   and end, its baseline, x-height and top, glyphs, and a bounding ellipse (offsets in
   em). Stormwrit (`stormwrit.ts`) and True North (`true-north.ts`) are worked examples,
   not templates.
3. **Review it the way Quill's were reviewed.** Put it side by side in the Elemental Title Lab
   (`display/elemental/index.html#signatures`) across rank colors, in dark and light, slowed to
   0.25×, with a wrapped name, and with the accent and constrained device toggled. Capture
   slowed frame strips and a real-speed GIF, and report frame timing. Say which starting points
   you changed and why.

## Handing it to another model

Give this brief plus a short prompt in this shape:

```text
Design a familiar signature for <familiar> (<element>), named "<Name>".
Idea: <the line> beneath the name, ending in <the ending> beside it.
Follow docs/FAMILIAR-SIGNATURES.md. The locked part is fixed: a fancy underline with a
unique ending, nothing above or through the letters, letters untouched, it clears itself
away. The starting points are yours to change if the idea needs it; say which and why.
Build it in packages/elemental-title/src/engine/signatures/, adding a primitive
if the motion needs one, register it, rebuild the package and lab, and show it in
display/elemental/index.html#signatures next to Quill's signatures with frame strips and timing.
```
