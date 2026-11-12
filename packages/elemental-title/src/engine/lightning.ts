import {
  clampPoint,
  curve,
  cutGaps,
  distance,
  measurePolyline,
  normalize,
  rotate,
  roughen,
  sampleAt,
  type Point,
  type Rect,
} from "./geometry";
import type { LetterAnimation } from "./letters";
import { between, chance, createRandom, integer, pick, type Random } from "./random";
import { timeline } from "./timeline";
import type {
  ElementalBolt,
  ElementalCue,
  ElementalEffect,
  ElementalFrame,
  ElementalGlyph,
  ElementalLight,
  ElementalRange,
  ElementalShard,
  ElementalSlot,
  ElementalStage,
  ElementalTier,
  ElementalTierPrograms,
} from "./types";

/** Lightning's parameters per bond tier. Every value is "higher is stronger". */
type LightningParams = {
  /** Main arcs per strike. */
  bolts: ElementalRange;
  /** Expected branches per main arc. */
  branches: number;
  shards: ElementalRange;
  /** Roughening passes; more detail reads as a hotter arc. */
  detail: number;
  /** Resting opacity once a strike has faded. */
  rest: number;
  /** Lifetime of a strike's flash in ms. */
  life: number;
  /** Multiplies arc width; higher familiar bond tiers carry a heavier charge. */
  weight: number;
  /** Chance an ambient strike jolts the letter nearest its impact. */
  jolt: number;
  /** Peak strength of the strike's rim light on nearby letter edges. */
  rim: number;
  /** Chance a crackle splits into two arcs. */
  split: number;
};

const params: Record<ElementalTier, LightningParams> = {
  common: {
    bolts: [1, 1],
    branches: 0.6,
    shards: [2, 5],
    detail: 3,
    rest: 0.26,
    life: 420,
    weight: 0.95,
    jolt: 0.12,
    rim: 0.95,
    split: 0,
  },
  rare: {
    bolts: [1, 2],
    branches: 1,
    shards: [3, 7],
    detail: 3,
    rest: 0.34,
    life: 460,
    weight: 1.05,
    jolt: 0.3,
    rim: 0.95,
    split: 0,
  },
  epic: {
    bolts: [1, 2],
    branches: 1.6,
    shards: [5, 10],
    detail: 4,
    rest: 0.42,
    life: 500,
    weight: 1.16,
    jolt: 0.55,
    rim: 0.95,
    split: 0,
  },
  legendary: {
    bolts: [2, 3],
    branches: 2.3,
    shards: [7, 14],
    detail: 4,
    rest: 0.5,
    life: 560,
    weight: 1.32,
    jolt: 0.8,
    rim: 0.95,
    split: 0.4,
  },
};

/** A strike leads soon after (re)starting; hover, focus and burst answer almost at once. */
const strikeLead = { ambient: [150, 700], engaged: [40, 40] } as const;
/** The first shine waits a little; engaged titles catch the light sooner. */
const shineLead = { ambient: [600, 2800], engaged: [120, 420] } as const;

/**
 * Lightning's tier program. Delays are in ms. Ambient-running titles use the engaged
 * pace, as they always have: the numbers are the original per-tier strike and crackle
 * ranges × 0.45. The shine's irregular gaps never settle into a metronome.
 */
const program: ElementalTierPrograms = {
  common: {
    cadence: {
      strike: { ambient: [1440, 2790], engaged: [1440, 2790], lead: strikeLead },
      crackle: { ambient: [450, 945], engaged: [450, 945] },
      shine: { ambient: [7000, 13000], engaged: [7000, 13000], lead: shineLead },
    },
    params: params.common,
  },
  rare: {
    cadence: {
      strike: { ambient: [855, 1620], engaged: [855, 1620], lead: strikeLead },
      crackle: { ambient: [292.5, 585], engaged: [292.5, 585] },
      shine: { ambient: [5500, 10500], engaged: [5500, 10500], lead: shineLead },
    },
    params: params.rare,
  },
  epic: {
    cadence: {
      strike: { ambient: [540, 1035], engaged: [540, 1035], lead: strikeLead },
      crackle: { ambient: [189, 382.5], engaged: [189, 382.5] },
      shine: { ambient: [4500, 8500], engaged: [4500, 8500], lead: shineLead },
    },
    params: params.epic,
  },
  legendary: {
    cadence: {
      strike: { ambient: [315, 630], engaged: [315, 630], lead: strikeLead },
      crackle: { ambient: [126, 252], engaged: [126, 252] },
      shine: { ambient: [3500, 7000], engaged: [3500, 7000], lead: shineLead },
    },
    params: params.legendary,
  },
};

type Strategy = "crown" | "jump" | "crawl" | "gap" | "lash" | "weave";

interface Composition {
  base: Point[];
  width: number;
  roughness: number;
  lights: ElementalLight[];
}

const bounds = (stage: ElementalStage): Rect => ({
  x: 0,
  y: 0,
  width: stage.width,
  height: stage.height,
});

/** Letters that can pair for a jump or crawl: neighbours on the same line. */
function neighbour(
  glyphs: ElementalGlyph[],
  index: number,
  random: Random,
  em: number,
): number | undefined {
  const step = pick(random, [1, 2, 2, 3, 3, 4]);
  for (let reach = Math.min(step, glyphs.length - 1 - index); reach >= 1; reach -= 1) {
    const candidate = glyphs[index + reach];
    if (Math.abs(candidate.center.y - glyphs[index].center.y) < em * 0.6) return index + reach;
  }
  return undefined;
}

/** A close neighbour, biased toward the very next letter — a weave stays legible. */
function adjacent(
  glyphs: ElementalGlyph[],
  index: number,
  random: Random,
  em: number,
): number | undefined {
  const step = pick(random, [1, 1, 1, 2]);
  for (let reach = Math.min(step, glyphs.length - 1 - index); reach >= 1; reach -= 1) {
    const candidate = glyphs[index + reach];
    if (Math.abs(candidate.center.y - glyphs[index].center.y) < em * 0.6) return index + reach;
  }
  return undefined;
}

/**
 * The nearest point on a nearby glyph's edge, within `reach`. Lets a branch visibly
 * terminate at a specific letter — reaching into it rather than trailing into empty air.
 */
function nearestGlyphEdge(stage: ElementalStage, from: Point, reach: number): Point | undefined {
  let best: { point: Point; distance: number } | undefined;
  for (const glyph of stage.glyphs) {
    const midY = (glyph.inkTop + glyph.inkBottom) / 2;
    const midX = glyph.x + glyph.width / 2;
    const candidates: Point[] = [
      { x: glyph.x, y: midY },
      { x: glyph.x + glyph.width, y: midY },
      { x: midX, y: glyph.inkTop },
      { x: midX, y: glyph.inkBottom },
    ];
    for (const point of candidates) {
      const away = distance(from, point);
      if (away <= reach && away > 1 && (!best || away < best.distance))
        best = { point, distance: away };
    }
  }
  return best?.point;
}

function composeStrategy(
  strategy: Strategy,
  stage: ElementalStage,
  random: Random,
): Composition | undefined {
  const { em, glyphs } = stage;
  const stageBounds = bounds(stage);
  const index = integer(random, 0, glyphs.length - 1);
  const glyph = glyphs[index];
  const spot = (target: ElementalGlyph, low = 0.15, high = 0.85) =>
    target.x + target.width * between(random, low, high);
  switch (strategy) {
    case "crown": {
      const impact = { x: spot(glyph), y: glyph.inkTop + between(random, -0.02, 0.05) * em };
      const origin = clampPoint(
        {
          x: impact.x + between(random, -0.45, 0.45) * em,
          y: impact.y - between(random, 0.4, 0.7) * em,
        },
        stageBounds,
        1,
      );
      const base = [origin, impact];
      // Half the strikes skid along the letter after impact instead of stopping dead.
      if (chance(random, 0.5))
        base.push(
          clampPoint(
            {
              x: impact.x + between(random, 0.12, 0.3) * em * (chance(random, 0.5) ? -1 : 1),
              y: impact.y + between(random, 0, 0.08) * em,
            },
            stageBounds,
            1,
          ),
        );
      return {
        base,
        width: 0.062 * em,
        roughness: 0.34,
        lights: [
          { ...impact, radius: between(random, 0.42, 0.62) * em, strength: 1 },
          { ...origin, radius: between(random, 0.22, 0.34) * em, strength: 0.45 },
        ],
      };
    }
    case "jump": {
      const partner = adjacent(glyphs, index, random, em);
      if (partner === undefined) return undefined;
      const other = glyphs[partner];
      const start = { x: spot(glyph, 0.3, 0.9), y: glyph.inkTop };
      const end = { x: spot(other, 0.1, 0.7), y: other.inkTop };
      const lift = between(random, 0.16, 0.34) * em;
      const control = {
        x: (start.x + end.x) / 2 + between(random, -0.15, 0.15) * em,
        y: Math.min(start.y, end.y) - lift * 2,
      };
      return {
        base: curve(start, control, end, 3),
        width: 0.052 * em,
        roughness: 0.3,
        lights: [
          { ...start, radius: between(random, 0.26, 0.4) * em, strength: 0.7 },
          { ...end, radius: between(random, 0.26, 0.4) * em, strength: 0.7 },
        ],
      };
    }
    case "crawl": {
      const partner = neighbour(glyphs, index, random, em);
      if (partner === undefined) return undefined;
      const other = glyphs[partner];
      const start = { x: spot(glyph, 0.3, 0.9), y: glyph.inkBottom };
      const end = { x: spot(other, 0.1, 0.7), y: other.inkBottom };
      const sag = between(random, 0.14, 0.38) * em;
      const control = {
        x: (start.x + end.x) / 2 + between(random, -0.15, 0.15) * em,
        y: Math.max(start.y, end.y) + sag * 2,
      };
      return {
        base: curve(start, control, end, 3),
        width: 0.048 * em,
        roughness: 0.3,
        lights: [
          { ...start, radius: between(random, 0.22, 0.34) * em, strength: 0.55 },
          { ...end, radius: between(random, 0.22, 0.34) * em, strength: 0.55 },
        ],
      };
    }
    case "gap": {
      if (index >= glyphs.length - 1) return undefined;
      const next = glyphs[index + 1];
      if (Math.abs(next.center.y - glyph.center.y) > em * 0.6) return undefined;
      const seam = (glyph.x + glyph.width + next.x) / 2;
      const top = Math.min(glyph.inkTop, next.inkTop);
      const bottom = Math.max(glyph.inkBottom, next.inkBottom);
      const start = {
        x: seam + between(random, -0.12, 0.12) * em,
        y: top - between(random, 0.12, 0.42) * em,
      };
      const end = {
        x: seam + between(random, -0.16, 0.16) * em,
        y: bottom + between(random, 0.08, 0.32) * em,
      };
      const middle = { x: seam + between(random, -0.06, 0.06) * em, y: (top + bottom) / 2 };
      return {
        base: [clampPoint(start, stageBounds, 1), middle, clampPoint(end, stageBounds, 1)],
        width: 0.048 * em,
        roughness: 0.26,
        lights: [{ ...middle, radius: between(random, 0.3, 0.44) * em, strength: 0.7 }],
      };
    }
    case "lash": {
      const last = chance(random, 0.5);
      const edge = last ? glyphs[glyphs.length - 1] : glyphs[0];
      const fromTop = chance(random, 0.6);
      const start = {
        x: last
          ? edge.x + edge.width * between(random, 0.7, 1)
          : edge.x + edge.width * between(random, 0, 0.3),
        y: fromTop
          ? edge.inkTop + between(random, 0, 0.2) * em
          : edge.inkBottom - between(random, 0, 0.2) * em,
      };
      const end = clampPoint(
        {
          x: start.x + between(random, 0.45, 0.9) * em * (last ? 1 : -1),
          y: start.y + between(random, -0.4, 0.4) * em,
        },
        stageBounds,
        1,
      );
      return {
        base: [start, end],
        width: 0.052 * em,
        roughness: 0.36,
        lights: [{ ...start, radius: between(random, 0.26, 0.4) * em, strength: 0.6 }],
      };
    }
    case "weave": {
      const partner = adjacent(glyphs, index, random, em);
      if (partner === undefined) return undefined;
      const other = glyphs[partner];
      // Threads through the letters' own ink band — cap-height to baseline, biased toward
      // the x-height counters — emerging from one edge and heading into the next, so the
      // back layer lets real letter ink swallow it wherever it crosses a stroke.
      const band = (target: ElementalGlyph) =>
        target.inkTop + (target.inkBottom - target.inkTop) * between(random, 0.3, 0.72);
      const start = { x: glyph.x + glyph.width * between(random, 0.55, 0.96), y: band(glyph) };
      const end = { x: other.x + other.width * between(random, 0.04, 0.45), y: band(other) };
      const control = {
        x: (start.x + end.x) / 2,
        y: (start.y + end.y) / 2 + between(random, -0.14, 0.14) * em,
      };
      return {
        base: curve(start, control, end, 3),
        width: 0.05 * em,
        roughness: 0.22,
        lights: [
          { ...start, radius: between(random, 0.18, 0.28) * em, strength: 0.45 },
          { ...end, radius: between(random, 0.18, 0.28) * em, strength: 0.45 },
        ],
      };
    }
  }
}

/**
 * Every strike leads with one of these, so the electricity always reads as touching the
 * letters. Weave dominates the pool so the word's own ink band — not the space above it —
 * carries most of the visible structure; crown and lash stay a minority accent.
 */
const connectedStrategies: Strategy[] = ["weave", "weave", "weave", "gap", "crawl", "jump"];
const strategies: Strategy[] = [
  ...connectedStrategies,
  "weave",
  "weave",
  "gap",
  "crawl",
  "crown",
  "lash",
];

/** Per-vertex widths: tapered toward the tip and never perfectly even. */
function widthsFor(points: Point[], width: number, random: Random): number[] {
  const measure = measurePolyline(points);
  return points.map((_, index) => {
    const t = measure.total ? measure.cumulative[index] / measure.total : 0;
    const taper = 1 - 0.68 * Math.pow(t, 0.85);
    return width * taper * between(random, 0.72, 1.28);
  });
}

function gapsFor(
  points: Point[],
  em: number,
  random: Random,
  expected: number,
): [number, number][] {
  const measure = measurePolyline(points);
  const count = Math.floor(expected) + (chance(random, expected % 1) ? 1 : 0);
  const gaps: [number, number][] = [];
  for (let index = 0; index < count; index += 1) {
    const start = between(random, 0.2, 0.82) * measure.total;
    const length = Math.max(1.5, between(random, 0.05, 0.13) * em);
    gaps.push([start, start + length]);
  }
  return gaps;
}

function buildBolt(
  spine: Point[],
  width: number,
  tier: 0 | 1 | 2,
  opacity: number,
  random: Random,
  em: number,
  gapBudget: number,
): ElementalBolt {
  const widths = widthsFor(spine, width, random);
  const runs = cutGaps(
    spine,
    widths,
    measurePolyline(spine),
    gapsFor(spine, em, random, gapBudget),
  );
  return { tier, opacity, spine, runs };
}

/** Grows branches off a spine; the arc splits where the charge finds an easier path. */
function branch(
  parent: ElementalBolt,
  width: number,
  random: Random,
  stage: ElementalStage,
  profile: LightningParams,
  budget: number,
  output: ElementalBolt[],
) {
  if (parent.tier >= 2 || parent.spine.length < 5) return;
  const count = Math.floor(budget) + (chance(random, budget % 1) ? 1 : 0);
  const measure = measurePolyline(parent.spine);
  for (let index = 0; index < count; index += 1) {
    const along = between(random, 0.18, 0.8) * measure.total;
    const sample = sampleAt(parent.spine, measure, along);
    const remaining = measure.total - along;
    const length = Math.max(stage.em * 0.16, remaining * between(random, 0.35, 0.75));
    const angle = between(random, 0.4, 1.05) * (chance(random, 0.5) ? -1 : 1);
    const direction = rotate(sample.tangent, angle);
    // Branches often reach for a nearby letter edge instead of open air, so the tree
    // looks grown out of the word rather than merely decorating the space around it.
    const targeted = chance(random, 0.5)
      ? nearestGlyphEdge(stage, sample.point, length * 1.6)
      : undefined;
    const end = clampPoint(
      targeted ?? {
        x: sample.point.x + direction.x * length,
        y: sample.point.y + direction.y * length,
      },
      bounds(stage),
      1,
    );
    const spine = roughen([sample.point, end], random, {
      detail: Math.max(2, profile.detail - 1),
      roughness: 0.36,
    });
    const tier = (parent.tier + 1) as 1 | 2;
    const bolt = buildBolt(
      spine,
      width * between(random, 0.48, 0.62),
      tier,
      parent.opacity * 0.82,
      random,
      stage.em,
      tier === 1 ? 0.35 : 0,
    );
    output.push(bolt);
    if (tier < 2 && chance(random, 0.45))
      branch(bolt, width * 0.55, random, stage, profile, 1, output);
  }
}

function shardsFor(
  bolts: ElementalBolt[],
  count: number,
  random: Random,
  em: number,
): ElementalShard[] {
  const shards: ElementalShard[] = [];
  const sources = bolts.filter((bolt) => bolt.spine.length >= 2);
  if (!sources.length) return shards;
  for (let index = 0; index < count; index += 1) {
    const bolt = chance(random, 0.65) ? sources[0] : pick(random, sources);
    const measure = measurePolyline(bolt.spine);
    const sample = sampleAt(bolt.spine, measure, between(random, 0.08, 0.95) * measure.total);
    const side = chance(random, 0.5) ? -1 : 1;
    const normal = { x: -sample.tangent.y * side, y: sample.tangent.x * side };
    const offset = between(random, 0.05, 0.22) * em;
    const direction = normalize(rotate(normal, between(random, -0.7, 0.7)));
    const drift = between(random, 0.08, 0.3) * em;
    const dot = chance(random, 0.35);
    shards.push({
      x: sample.point.x + normal.x * offset,
      y: sample.point.y + normal.y * offset,
      dx: direction.x * drift,
      dy: direction.y * drift,
      length: dot ? 0 : Math.max(0.8, between(random, 0.02, 0.08) * em),
      angle: Math.atan2(direction.y, direction.x),
      width: Math.max(0.6, between(random, 0.5, 1.1) * (em / 24)),
    });
  }
  return shards;
}

/** A short, low-energy arc that keeps the letters alive between strikes. */
function crackle(stage: ElementalStage, random: Random, em: number): ElementalBolt | undefined {
  if (!stage.glyphs.length) return undefined;
  const glyph = pick(random, stage.glyphs);
  const top = chance(random, 0.6);
  const start = {
    x: glyph.x + glyph.width * between(random, 0, 1),
    y: top
      ? glyph.inkTop - between(random, 0, 0.08) * em
      : glyph.inkBottom + between(random, 0, 0.08) * em,
  };
  const direction = normalize({
    x: between(random, -1, 1),
    y: (top ? -1 : 1) * between(random, 0.05, 0.5),
  });
  const length = between(random, 0.22, 0.48) * em;
  const end = clampPoint(
    { x: start.x + direction.x * length, y: start.y + direction.y * length },
    bounds(stage),
    1,
  );
  const spine = roughen([start, end], random, { detail: 2, roughness: 0.36 });
  return buildBolt(spine, 0.03 * em, 1, 0.85, random, em, 0.3);
}

const empty = (key: number, slot: ElementalFrame["slot"], rest: number): ElementalFrame => ({
  key,
  slot,
  life: 1,
  rest,
  bolts: [],
  shards: [],
  lights: [],
});

export interface LightningComposeOptions {
  slot: ElementalSlot;
  tier: ElementalTier;
  /** Hovered, focused, bursting or running ambiently: the strike can afford more energy. */
  engaged: boolean;
  random: Random;
  key: number;
}

/** Composes one lightning frame: the still frame, a strike or a crackle. */
export function composeLightning(
  stage: ElementalStage,
  options: LightningComposeOptions,
): ElementalFrame {
  // Keep the existing bounded storm (including its seeded still frame) even
  // though the letter engine now measures the entire name.
  if (stage.glyphs.length > 40) {
    const glyphs = stage.glyphs;
    stage = {
      ...stage,
      glyphs: Array.from(
        { length: 40 },
        (_, index) => glyphs[Math.floor((index * glyphs.length) / 40)],
      ),
    };
  }
  const { random, tier, slot, engaged, key } = options;
  const profile = params[tier];
  const em = stage.em;
  if (!stage.glyphs.length || !em) return empty(key, slot, profile.rest);

  if (slot === "crackle") {
    const bolts: ElementalBolt[] = [];
    const count = profile.split > 0 && chance(random, profile.split) ? 2 : 1;
    for (let index = 0; index < count; index += 1) {
      const bolt = crackle(stage, random, em);
      if (bolt) bolts.push(bolt);
    }
    return {
      key,
      slot,
      life: 220,
      rest: profile.rest * 0.55,
      bolts,
      shards: shardsFor(bolts, integer(random, 0, 2), random, em),
      lights: [],
    };
  }

  const bolts: ElementalBolt[] = [];
  const lights: ElementalLight[] = [];
  const wanted =
    slot === "still"
      ? tier === "common" || tier === "rare"
        ? 1
        : 2
      : integer(random, profile.bolts[0], profile.bolts[1]) + (engaged ? 1 : 0);
  let attempts = 0;
  while (bolts.filter((bolt) => bolt.tier === 0).length < wanted && attempts < wanted * 4) {
    attempts += 1;
    const isFirst = bolts.filter((bolt) => bolt.tier === 0).length === 0;
    const strategy =
      stage.glyphs.length > 1 && attempts <= wanted * 2
        ? pick(random, isFirst ? connectedStrategies : strategies)
        : pick(random, ["crown", "lash"] as Strategy[]);
    const composition = composeStrategy(strategy, stage, random);
    if (!composition) continue;
    const spine = roughen(composition.base, random, {
      detail: profile.detail,
      roughness: composition.roughness,
    });
    const width = composition.width * profile.weight;
    const main = buildBolt(spine, width, 0, 1, random, em, 0.9);
    bolts.push(main);
    lights.push(...composition.lights);
    branch(main, width, random, stage, profile, profile.branches, bolts);
  }
  const shardCount = Math.round(
    integer(random, profile.shards[0], profile.shards[1]) * (engaged ? 1.4 : 1),
  );
  return {
    key,
    slot,
    life: profile.life,
    rest: profile.rest,
    bolts,
    shards: shardsFor(bolts, shardCount, random, em),
    lights,
  };
}

/**
 * At most one 180–260ms jolt of the letter nearest a strike's first impact light (or
 * main bolt endpoint). Crackles and still frames never jolt. Engaged and explicit
 * strikes always jolt; ambient ones use the tier's probability.
 */
export function lightningJolt(
  stage: ElementalStage,
  frame: ElementalFrame,
  { tier, engaged, random }: { tier: ElementalTier; engaged: boolean; random: Random },
): LetterAnimation[] {
  if (
    frame.slot !== "strike" ||
    !stage.glyphs.length ||
    !chance(random, engaged ? 1 : params[tier].jolt)
  )
    return [];
  const bolt = frame.bolts.find((bolt) => bolt.tier === 0);
  const impact = frame.lights[0] ?? bolt?.spine.at(-1);
  if (!impact) return [];
  let glyph = 0;
  let nearest = Infinity;
  stage.glyphs.forEach((candidate, index) => {
    const away = distance(impact, clampPoint(impact, candidate));
    if (away < nearest) {
      nearest = away;
      glyph = index;
    }
  });
  const direction = chance(random, 0.5) ? 1 : -1;
  const shift = Math.min(1.5, stage.em * 0.055) * direction;
  return [
    {
      glyph,
      edge: true,
      duration: between(random, 180, 260),
      keyframes: [
        { transform: "translate(0, 0) rotate(0deg)" },
        {
          transform: `translate(${shift}px, -0.7px) rotate(${direction * 1.2}deg)`,
          offset: 0.15,
        },
        {
          transform: `translate(${-shift * 0.55}px, 0.35px) rotate(${-direction * 0.6}deg)`,
          offset: 0.4,
        },
        { transform: "translate(0, 0) rotate(0deg)" },
      ],
    },
  ];
}

/**
 * Lightning: hot-cored, branching arcs that jump between and around the letters,
 * break into dark gaps and throw off fine fragments. Its moments are timelines:
 * a strike (arcs, the rim light on nearby letter edges and sometimes a letter jolt),
 * a crackle (a short faint arc) and the shine (a soft band of light).
 */
export const lightning: ElementalEffect = {
  id: "lightning",
  layers: { overlay: true, letters: true, edgeLight: true },
  moments: { strike: { priority: 2 }, crackle: { priority: 1 }, shine: { priority: 0 } },
  program,
  still: (stage, { tier, random, key }) =>
    composeLightning(stage, { slot: "still", tier, engaged: false, random, key }),
  timeline(moment, stage, context) {
    const { tier, random, key } = context;
    const profile = context.params as LightningParams;
    switch (moment) {
      case "strike": {
        const frame = composeLightning(stage, {
          slot: "strike",
          tier,
          engaged: context.engaged,
          random,
          key,
        });
        // The jolt draws from its own stream, so it never perturbs arc composition.
        const jolts = lightningJolt(stage, frame, {
          tier,
          engaged: context.explicit || (context.engaged && context.interactive),
          random: createRandom(context.textSeed ^ frame.key),
        });
        const impact = frame.lights[0];
        const cues: ElementalCue[] = [{ type: "frame", at: 0, frame }];
        if (jolts.length) cues.push({ type: "letters", at: 0, animations: jolts });
        if (impact)
          cues.push({
            type: "edge-light",
            at: 0,
            x: impact.x,
            y: impact.y,
            radius: stage.em * 1.9,
            strength: profile.rim,
            duration: Math.max(frame.life, 420),
            exclude: jolts.map((jolt) => jolt.glyph),
          });
        return timeline("strike", lightning.moments.strike.priority, cues);
      }
      case "crackle":
        return timeline("crackle", lightning.moments.crackle.priority, [
          {
            type: "frame",
            at: 0,
            frame: composeLightning(stage, {
              slot: "crackle",
              tier,
              engaged: context.engaged,
              random,
              key,
            }),
          },
        ]);
      case "shine": {
        // Each pass draws its own speed, angle, strength and sometimes direction, so it
        // reads as light catching the letters rather than a looping stripe.
        const gain = between(random, 0.9, 1.35);
        const reverse = random() < 0.25;
        const angle = between(random, 100, 122);
        const rise = between(random, 0.18, 0.28);
        const fade = between(random, 0.7, 0.95);
        const hold = between(random, 0.62, 0.74);
        const duration =
          between(random, 1300, 2300) * (context.engaged && context.interactive ? 0.8 : 1);
        return timeline("shine", lightning.moments.shine.priority, [
          { type: "shine", at: 0, duration, angle, reverse, gain, rise, hold, fade },
        ]);
      }
      default:
        return null;
    }
  },
};
