import { insideStage, type SceneAnchors } from "./anchors";
import {
  cutGaps,
  measurePolyline,
  normalize,
  roughen,
  rotate,
  sampleAt,
  type Point,
  type PolylineMeasure,
  type Run,
} from "./geometry";
import { between, chance, type Random } from "./random";
import type {
  ElementalSceneCue,
  ElementalSceneDissolve,
  ElementalScenePart,
  ElementalSceneShape,
  ElementalSceneShapeKey,
  ElementalSceneSpark,
  ElementalSceneStroke,
  ElementalSceneTraveler,
  ElementalScenePrimitive,
} from "./types";

/*
 * Pure builders for scene primitives. A signature composes its scene from these with the
 * measured anchors and a seeded random stream, so the same seed always builds the same
 * scene. Geometry stays inside the stage (the overlay's overscan).
 */

export type SceneEase = "linear" | "in" | "out" | "in-out";

export function ease(name: SceneEase, t: number): number {
  const x = Math.min(1, Math.max(0, t));
  switch (name) {
    case "in":
      return x * x;
    case "out":
      return 1 - (1 - x) * (1 - x);
    case "in-out":
      return x < 0.5 ? 2 * x * x : 1 - 2 * (1 - x) * (1 - x);
    default:
      return x;
  }
}

/** A draw schedule sampled from an ease: [share of time, share of length]. */
export function progressOf(name: SceneEase, samples = 16): [number, number][] {
  return Array.from({ length: samples + 1 }, (_, index) => {
    const t = index / samples;
    return [t, ease(name, t)];
  });
}

/** The share of time at which a schedule reaches a share of its length. */
export function timeAt(progress: [number, number][], share: number): number {
  for (let index = 1; index < progress.length; index += 1) {
    const [t0, s0] = progress[index - 1];
    const [t1, s1] = progress[index];
    if (share <= s1) return s1 === s0 ? t0 : t0 + ((share - s0) / (s1 - s0)) * (t1 - t0);
  }
  return 1;
}

/** Merged [start, end] intervals, clipped to [0, total]. */
function merged(intervals: [number, number][], total: number): [number, number][] {
  const sorted = intervals
    .map(([a, b]) => [Math.max(0, a), Math.min(total, b)] as [number, number])
    .filter(([a, b]) => b > a)
    .sort((a, b) => a[0] - b[0]);
  const out: [number, number][] = [];
  for (const interval of sorted) {
    const last = out.at(-1);
    if (last && interval[0] <= last[1]) last[1] = Math.max(last[1], interval[1]);
    else out.push([...interval]);
  }
  return out;
}

/** The runs left after removing intervals; empty when they cover the whole line. */
function runsWithout(
  points: Point[],
  widths: number[],
  measure: PolylineMeasure,
  excluded: [number, number][],
): Run[] {
  const cut = merged(excluded, measure.total);
  const covered = cut.reduce((sum, [a, b]) => sum + b - a, 0);
  if (covered >= measure.total - 0.01) return [];
  return cutGaps(points, widths, measure, cut);
}

function complement(intervals: [number, number][], total: number): [number, number][] {
  const out: [number, number][] = [];
  let cursor = 0;
  for (const [a, b] of merged(intervals, total)) {
    if (a > cursor) out.push([cursor, a]);
    cursor = b;
  }
  if (cursor < total) out.push([cursor, total]);
  return out;
}

export interface StrokeOptions {
  at: number;
  /** The authored path in stage px (sample curves densely enough to look smooth). */
  path: Point[];
  /** Core width in px at its widest; the plasma edge is drawn wider. */
  width: number;
  /** Shares of the length over which the start and end taper to a point. */
  taper?: [number, number];
  /** Lightning roughness (0 keeps the path smooth) and its detail passes. */
  roughness?: number;
  detail?: number;
  /** Expected number of dark gaps. */
  gaps?: number;
  /** Shares of the length drawn in front of the letters. */
  front?: [number, number][];
  on: number;
  hold: number;
  off: number;
  exit?: "erase" | "retract";
  ease?: SceneEase;
  /** Width of the soft glow in px; default four times the core width. */
  glow?: number;
  flicker?: boolean;
  accent?: boolean;
}

/** A tapered, optionally rough stroke that draws on, holds and draws off. */
export function stroke(
  options: StrokeOptions,
  anchors: SceneAnchors,
  random: Random,
): ElementalSceneStroke {
  const { em } = anchors;
  const inset = options.width * 2 + 1;
  let spine = options.path.map((point) => insideStage(anchors, point, inset));
  if (options.roughness)
    spine = roughen(spine, random, {
      detail: options.detail ?? 2,
      roughness: options.roughness,
    }).map((point) => insideStage(anchors, point, inset));
  const measure = measurePolyline(spine);
  const [head, tail] = options.taper ?? [0.12, 0.2];
  const widths = spine.map((_, index) => {
    const share = measure.total ? measure.cumulative[index] / measure.total : 0;
    const rise = head ? Math.min(1, 0.25 + (0.75 * share) / head) : 1;
    const fall = tail ? Math.min(1, 0.25 + (0.75 * (1 - share)) / tail) : 1;
    return options.width * Math.min(rise, fall) * between(random, 0.82, 1.15);
  });
  const expected = options.gaps ?? 0;
  const count = Math.floor(expected) + (chance(random, expected % 1) ? 1 : 0);
  const dark: [number, number][] = Array.from({ length: count }, () => {
    const start = between(random, 0.15, 0.85) * measure.total;
    return [start, start + Math.max(1.5, between(random, 0.04, 0.08) * em)];
  });
  const front = (options.front ?? []).map(
    ([a, b]) => [a * measure.total, b * measure.total] as [number, number],
  );
  const behind = complement(front, measure.total);
  const spinesOf = (excluded: [number, number][]) =>
    runsWithout(spine, widths, measure, excluded).map((run) => run.points);
  return {
    type: "stroke",
    at: options.at,
    spine,
    runs: {
      back: runsWithout(spine, widths, measure, [...dark, ...front]),
      front: runsWithout(spine, widths, measure, [...dark, ...behind]),
    },
    spines: { back: spinesOf(front), front: spinesOf(behind) },
    progress: progressOf(options.ease ?? "linear"),
    on: options.on,
    hold: options.hold,
    off: options.off,
    exit: options.exit ?? "erase",
    glow: options.glow ?? options.width * 4,
    ...(options.flicker ? { flicker: true } : {}),
    ...(options.accent ? { accent: true } : {}),
  };
}

/** A spark or fragment, kept inside the stage. */
function spark(
  anchors: SceneAnchors,
  random: Random,
  point: Point,
  direction: Point,
  { drift, delay, life, length }: { drift: number; delay: number; life: number; length?: number },
): ElementalSceneSpark {
  const { em } = anchors;
  const inside = insideStage(anchors, point, 2);
  const unit = normalize(direction);
  const dot = length === undefined ? chance(random, 0.3) : length === 0;
  const end = insideStage(
    anchors,
    { x: inside.x + unit.x * drift, y: inside.y + unit.y * drift },
    2,
  );
  return {
    x: inside.x,
    y: inside.y,
    dx: end.x - inside.x,
    dy: end.y - inside.y,
    length: dot ? 0 : (length ?? Math.max(0.8, between(random, 0.02, 0.06) * em)),
    angle: Math.atan2(unit.y, unit.x),
    width: Math.max(0.6, between(random, 0.45, 0.9) * (em / 24)),
    delay,
    life,
  };
}

export interface TravelerOptions {
  /** Head radius in px. */
  radius: number;
  /** Sparks shed along the ride. */
  sparks: number;
  part?: ElementalScenePart;
  /** Rides only part of the stroke: [from, to] shares of its length. Default the whole. */
  span?: [number, number];
}

/** A bright head that rides a stroke exactly as it draws on, shedding small sparks. */
export function traveler(
  line: ElementalSceneStroke,
  options: TravelerOptions,
  anchors: SceneAnchors,
  random: Random,
): ElementalSceneTraveler {
  const measure = measurePolyline(line.spine);
  const [from, to] = options.span ?? [0, 1];
  const t0 = timeAt(line.progress, from);
  const t1 = timeAt(line.progress, to);
  const duration = Math.max(1, (t1 - t0) * line.on);
  const steps = 24;
  const path: [number, number, number][] = [];
  for (let index = 0; index <= steps; index += 1) {
    const time = t0 + ((t1 - t0) * index) / steps;
    const share = sampleProgress(line.progress, time);
    const { point } = sampleAt(line.spine, measure, share * measure.total);
    path.push([index / steps, point.x, point.y]);
  }
  const sparks = Array.from({ length: options.sparks }, (_, index) => {
    const share = from + (to - from) * ((index + between(random, 0.1, 0.9)) / options.sparks);
    const sample = sampleAt(line.spine, measure, share * measure.total);
    const time = (timeAt(line.progress, share) - t0) * line.on;
    // Sparks fall away behind the nib: backwards along the path and a little down.
    const back = { x: -sample.tangent.x, y: -sample.tangent.y };
    const direction = rotate(back, between(random, -0.9, 0.9));
    return spark(
      anchors,
      random,
      sample.point,
      { x: direction.x, y: direction.y + between(random, 0.1, 0.5) },
      {
        drift: between(random, 0.1, 0.28) * anchors.em,
        delay: Math.max(0, time),
        life: between(random, 220, 380),
      },
    );
  });
  return {
    type: "traveler",
    at: line.at + t0 * line.on,
    part: options.part ?? "front",
    path,
    duration,
    radius: options.radius,
    sparks,
  };
}

/** Share of length drawn at a share of time. */
function sampleProgress(progress: [number, number][], time: number) {
  for (let index = 1; index < progress.length; index += 1) {
    const [t0, s0] = progress[index - 1];
    const [t1, s1] = progress[index];
    if (time <= t1) return t1 === t0 ? s1 : s0 + ((time - t0) / (t1 - t0)) * (s1 - s0);
  }
  return 1;
}

export interface StarOptions {
  at: number;
  center: Point;
  /** Point length in px; keep it at least a quarter em so the motif reads at 20px. */
  radius: number;
  /** Half-width of the waist; default 22% of the radius. */
  waist?: number;
  part?: ElementalScenePart;
  duration: number;
  keyframes: ElementalSceneShapeKey[];
  accent?: boolean;
}

/** A four-point star: ignite, stretch, snap back and wink out as authored keyframes. */
export function star(options: StarOptions, anchors: SceneAnchors): ElementalSceneShape {
  return {
    type: "shape",
    shape: "star4",
    at: options.at,
    part: options.part ?? "front",
    center: insideStage(anchors, options.center, options.radius * 0.6),
    radius: options.radius,
    waist: options.waist ?? options.radius * 0.22,
    duration: options.duration,
    keyframes: options.keyframes,
    ...(options.accent ? { accent: true } : {}),
  };
}

export interface DissolveOptions {
  at: number;
  /** Time over which fragments are released along the stroke. */
  duration: number;
  /** Fragments per em of stroke length. */
  density: number;
  part?: ElementalScenePart;
}

/**
 * The stroke crackles away: fine fragments are released along it in the direction it
 * draws off (start to end for `erase`, end to start for `retract`), drift and fade.
 */
export function dissolveStroke(
  line: ElementalSceneStroke,
  options: DissolveOptions,
  anchors: SceneAnchors,
  random: Random,
): ElementalSceneDissolve {
  const measure = measurePolyline(line.spine);
  const count = Math.max(2, Math.round((measure.total / anchors.em) * options.density));
  const fragments = Array.from({ length: count }, (_, index) => {
    const share = (index + between(random, 0.1, 0.9)) / count;
    const sample = sampleAt(line.spine, measure, share * measure.total);
    const side = chance(random, 0.5) ? -1 : 1;
    const normal = { x: -sample.tangent.y * side, y: sample.tangent.x * side };
    const direction = rotate(normal, between(random, -0.6, 0.6));
    const order = line.exit === "retract" ? 1 - share : share;
    return spark(anchors, random, sample.point, direction, {
      drift: between(random, 0.08, 0.26) * anchors.em,
      delay: order * options.duration,
      life: between(random, 260, 420),
    });
  });
  return { type: "dissolve", at: options.at, part: options.part ?? "front", fragments };
}

/** A few fragments thrown out from a point: a spark popping or a shape winking out. */
export function burst(
  options: { at: number; center: Point; count: number; reach: number; part?: ElementalScenePart },
  anchors: SceneAnchors,
  random: Random,
): ElementalSceneDissolve {
  const fragments = Array.from({ length: options.count }, (_, index) => {
    const angle = ((index + between(random, 0.2, 0.8)) / options.count) * Math.PI * 2;
    const direction = { x: Math.cos(angle), y: Math.sin(angle) };
    return spark(anchors, random, options.center, direction, {
      drift: options.reach * between(random, 0.6, 1),
      delay: between(random, 0, 40),
      life: between(random, 240, 360),
    });
  });
  return { type: "dissolve", at: options.at, part: options.part ?? "front", fragments };
}

/** When a primitive's own work ends, relative to its scene cue. */
export function primitiveEnd(primitive: ElementalScenePrimitive): number {
  const sparksEnd = (list: ElementalSceneSpark[]) =>
    list.reduce((end, item) => Math.max(end, item.delay + item.life), 0);
  switch (primitive.type) {
    case "stroke":
      return primitive.at + primitive.on + primitive.hold + primitive.off;
    case "traveler":
      return primitive.at + Math.max(primitive.duration, sparksEnd(primitive.sparks));
    case "shape":
      return primitive.at + primitive.duration;
    case "dissolve":
      return primitive.at + sparksEnd(primitive.fragments);
  }
}

/**
 * A scene cue for one beat. Builders place primitives on the timeline's clock; the cue
 * rebases them onto its own start.
 */
export function sceneCue(
  beat: string,
  at: number,
  primitives: ElementalScenePrimitive[],
): ElementalSceneCue {
  return {
    type: "scene",
    at,
    beat,
    primitives: primitives.map((primitive) => ({ ...primitive, at: primitive.at - at })),
  };
}
