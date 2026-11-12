# Elemental Title Lab

Interactive review workspace for [`@seihouse/elemental-title`](../../packages/elemental-title/README.md),
part of **Section 02: The Title Engine** in SEIHouse Font Lab.

Open `display/elemental/index.html` in the served Font Lab site (or visit `/display/elemental/`).
Use `#playground`, `#gallery`, `#moments`, `#signatures`, `#context`, or `#edge-cases` to deep-link
directly to any review tab.

## What You Can Test Here

1. **SEIHouse Typeface Switcher** — Switch every title in the lab live between **Display Edge**,
   **Display Soft**, **Display Ink**, **Display Wide**, **SEIHouse Sans 0.42**, and **SEIHouse Noto**.
2. **Playground** — Live title on Dark and Light surfaces side by side, with element, cultivator
   rank color, bond tier, motion mode, size, outline keyline, and Quill signatures.
3. **Elements & ranks** — Full palette gallery plus the Cultivator Rank × Bond Tier matrix at 20px.
4. **Moments** — Choreography lab firing `strike`, `crackle`, `wave`, `drip`, `flow`, `shine`, and
   `ripple` with `0.25×` slow motion and live timeline cue/beat readouts.
5. **Signatures** — Quill's *Stormwrit* and *True North* signatures across ranks, wrapped lines,
   gold accent toggle, constrained-device mode, Familiar Look, Signature Shop, and seeded rotation.
6. **In context** — Profile header, 10-reader comment feed sharing the 1-at-a-time signature
   coordinator, and a 24-name crowded page comparing `Page budget` `on` vs `off`.
7. **Edge cases** — Unbroken strings, mixed scripts (`読者 Éowyn — حارس المكتبة`), wrapped lines,
   plain inherited typography, and titles inside interactive buttons.

## Rebuild Commands

After editing `packages/elemental-title/src/` or `display/elemental/src/`:

```sh
node display/build_elemental_package.mjs
node display/pack_elemental_package.mjs
node display/build_elemental_lab.mjs
```
