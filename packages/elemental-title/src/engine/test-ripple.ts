import { timeline } from "./timeline";
import type { ElementalEffect, ElementalRange, ElementalTierProgram } from "./types";

/**
 * TEST ONLY: not an element, not art, not exported. A throwaway effect that proves new
 * behaviors plug in as data plus choreography: it registers through the registry and a
 * tier program, with no title code. Every letter rises and falls in reading order across
 * the whole name (wrapped lines included), then settles with a small overshoot. It also
 * pressure-tests slices with bigger motion: up to 0.25em lift, 8° lean and 0.85–1.1 scale.
 *
 * Remove it by deleting this file and its registration in `effects.ts`.
 */
type RippleParams = {
  /** Peak lift in em. */
  lift: number;
  /** Peak lean in degrees. */
  lean: number;
  /** Peak growth; 0.1 is 110%. */
  swell: number;
  /** Settle overshoot below rest, in em. */
  dip: number;
  /** Settle squash; 0.15 is 85% tall. */
  squash: number;
};

const tier = (
  params: RippleParams,
  ambient: ElementalRange,
  engaged: ElementalRange,
): ElementalTierProgram => ({
  cadence: { ripple: { ambient, engaged, lead: { ambient: [900, 1800], engaged: [60, 60] } } },
  params,
});

const rest = "translateY(0px) rotate(0deg) scale(1, 1)";
const stagger = 45;
const rise = 520;
const settle = 260;

export const testRipple: ElementalEffect = {
  id: "test-ripple",
  layers: { letters: true },
  moments: { ripple: { priority: 2 } },
  program: {
    common: tier(
      { lift: 0.08, lean: 0, swell: 0.02, dip: 0.02, squash: 0.03 },
      [9000, 14000],
      [5000, 8000],
    ),
    rare: tier(
      { lift: 0.13, lean: 2, swell: 0.04, dip: 0.03, squash: 0.06 },
      [7000, 11000],
      [4000, 6500],
    ),
    epic: tier(
      { lift: 0.19, lean: 5, swell: 0.07, dip: 0.04, squash: 0.1 },
      [5500, 9000],
      [3200, 5000],
    ),
    legendary: tier(
      { lift: 0.25, lean: 8, swell: 0.1, dip: 0.05, squash: 0.15 },
      [4500, 7500],
      [2600, 4200],
    ),
  },
  timeline(moment, stage, { params, random }) {
    if (moment !== "ripple" || !stage.glyphs.length) return null;
    const { lift, lean, swell, dip, squash } = params as RippleParams;
    const tilt = lean * (random() < 0.5 ? -1 : 1);
    const letters = stage.glyphs.map((_, glyph) => glyph);
    return timeline(
      "ripple",
      testRipple.moments.ripple.priority,
      [
        {
          type: "letters",
          at: 0,
          beat: "wave",
          animations: letters.map((glyph) => ({
            glyph,
            delay: glyph * stagger,
            duration: rise,
            origin: "50% 79%",
            easing: "ease-in-out",
            keyframes: [
              { transform: rest },
              {
                transform: `translateY(${(-lift * stage.em).toFixed(2)}px) rotate(${tilt}deg) scale(${1 + swell}, ${1 + swell})`,
                offset: 0.45,
              },
              { transform: rest },
            ],
          })),
        },
        {
          // Each letter settles the moment its own wave ends.
          type: "letters",
          at: rise,
          beat: "settle",
          animations: letters.map((glyph) => ({
            glyph,
            delay: glyph * stagger,
            duration: settle,
            origin: "50% 79%",
            keyframes: [
              { transform: rest },
              {
                transform: `translateY(${(dip * stage.em).toFixed(2)}px) rotate(0deg) scale(1, ${1 - squash})`,
                offset: 0.4,
              },
              { transform: rest },
            ],
          })),
        },
      ],
      [
        { label: "wave", at: 0 },
        { label: "settle", at: rise },
      ],
    );
  },
};
