import type { LetterAnimation } from "./letters";
import { linesOf } from "./lines";
import { timeline } from "./timeline";
import { waterEnvelope } from "./water-surface";
import type {
  ElementalEffect,
  ElementalFrame,
  ElementalStage,
  ElementalTier,
  ElementalTierPrograms,
  ElementalWave,
} from "./types";

type WaterParams = { height: number; curl: number; wake: number; lift: number };
const profiles: Record<ElementalTier, WaterParams> = {
  common: { height: 0.32, curl: 0, wake: 0, lift: 0.035 },
  rare: { height: 0.7, curl: 1, wake: 0, lift: 0.09 },
  epic: { height: 1.1, curl: 2, wake: 1, lift: 0.17 },
  legendary: { height: 1.6, curl: 3, wake: 2, lift: 0.29 },
};

const program = Object.fromEntries(
  Object.entries(profiles).map(([tier, params], index) => [
    tier,
    {
      params,
      cadence: {
        wave: {
          ambient: [6500 - index * 650, 8500 - index * 800],
          engaged: [5500 - index * 500, 7000 - index * 650],
          lead: { ambient: [400, 1500], engaged: [100, 180] },
        },
      },
    },
  ]),
) as unknown as ElementalTierPrograms;

/** A smooth compact swell. Outside its footprint letters are exactly at rest. */
function swell(distance: number, width: number) {
  return Math.abs(distance) >= width ? 0 : (1 + Math.cos((distance / width) * Math.PI)) / 2;
}

/** Same crest position as the renderer's linear transport, sampled once per moment. */
export function waveLetters(
  stage: ElementalStage,
  wave: ElementalWave,
  glyphs: ElementalStage["glyphs"],
  lift: number,
): LetterAnimation[] {
  return glyphs.map((glyph) => ({
    glyph: stage.glyphs.indexOf(glyph),
    delay: wave.delay,
    duration: wave.duration,
    origin: "50% 85%",
    easing: "linear",
    keyframes: Array.from({ length: 81 }, (_, index) => {
      const t = index / 80;
      const crest = wave.from + (wave.to - wave.from) * t;
      const d = (glyph.center.x - crest) / wave.em;
      const main = swell(d, 0.95);
      const trail = swell(d + 1.2, 0.7);
      const roll = waterEnvelope(t);
      const follower = wave.wake > 1 ? swell(d + 2.15, 0.7) * roll * 0.62 : 0;
      const y = -lift * (main * roll + follower) + lift * 0.23 * trail;
      const lean = main * Math.sin((d / 0.95) * Math.PI) * (1 + wave.height * 5);
      const bend = -lean * 0.6;
      return {
        offset: t,
        transform:
          index === 0 || index === 80
            ? "translate(0px, 0px) rotate(0deg) skewX(0deg)"
            : `translate(${(main * wave.em * 0.035).toFixed(3)}px, ${(y * wave.em).toFixed(3)}px) rotate(${lean.toFixed(3)}deg) skewX(${bend.toFixed(3)}deg)`,
      };
    }),
  }));
}

function wavesOf(stage: ElementalStage, profile: WaterParams): ElementalWave[] {
  return linesOf(stage).map((line) => ({
    left: line.left - stage.em * 0.28,
    right: line.right + stage.em * 0.28,
    baseline: Math.max(...line.glyphs.map((glyph) => glyph.inkBottom)) - stage.em * 0.04,
    from: line.left - stage.em * 1.1,
    to: line.right + stage.em * 3.2,
    em: stage.em,
    height: profile.height,
    curl: profile.curl,
    wake: profile.wake,
    delay: 0,
    duration: Math.min(3200, 1800 + ((line.right - line.left) / stage.em) * 95),
  }));
}

function frameOf(waves: ElementalWave[], key: number, still = false): ElementalFrame {
  return {
    key,
    slot: still ? "still" : "wave",
    life: Math.max(1, ...waves.map((wave) => wave.delay + wave.duration)),
    rest: 1,
    bolts: [],
    shards: [],
    lights: [],
    material: { type: "water", waves, still },
  };
}

/** A body of water crossing the ink band, with buoyancy tied to the passing crest. */
export const water: ElementalEffect = {
  id: "water",
  layers: { overlay: true, letters: true },
  overscan: { x: 0.7, top: 0.8, bottom: 0.6 },
  moments: { wave: { priority: 2 } },
  program,
  still: (stage, context) =>
    frameOf(wavesOf(stage, context.params as WaterParams), context.key, true),
  timeline(moment, stage, context) {
    if (moment !== "wave" || !stage.glyphs.length || !stage.em) return null;
    const profile = context.params as WaterParams;
    const waves = wavesOf(stage, profile);
    const lines = linesOf(stage);
    return timeline("wave", 2, [
      { type: "frame", at: 0, beat: "arrival", frame: frameOf(waves, context.key) },
      {
        type: "letters",
        at: 0,
        beat: "buoyancy",
        animations: waves.flatMap((wave, index) =>
          waveLetters(stage, wave, lines[index].glyphs, profile.lift),
        ),
      },
    ]);
  },
};
