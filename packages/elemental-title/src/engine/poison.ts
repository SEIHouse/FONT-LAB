import { linesOf, type Line } from "./lines";
import { measurePolyline, normalize, type Point } from "./geometry";
import type { LetterAnimation } from "./letters";
import { between, chance, createRandom, integer, pick, type Random } from "./random";
import { timeline } from "./timeline";
import type {
  ElementalCue,
  ElementalEffect,
  ElementalFrame,
  ElementalGlyph,
  ElementalRange,
  ElementalStage,
  ElementalTierPrograms,
  ElementalPoisonBand,
  ElementalPoisonBead,
  ElementalPoisonFlow,
  ElementalPoisonMaterial,
} from "./types";

/** Poison's parameters per bond tier. Every value is "higher is stronger". */
export type PoisonParams = {
  /** Share of the contour around each line the band covers, centred under the word. */
  wrap: number;
  /** Multiplies the band's thickness. */
  weight: number;
  /** Beads per drip; above one, the rest follow the first from the same point (a pour). */
  beads: ElementalRange;
  /** Multiplies bead size. */
  size: number;
  /** Chance a drip weighs the letters above it down and lets them spring back. */
  swell: number;
  /** Strength of the current riding inside the band as its highlight flows. */
  current: number;
  /** Peak opacity of the flowing highlight. */
  glint: number;
  /** Beads hanging from the band at rest. */
  rest: number;
};

const params: Record<"common" | "rare" | "epic" | "legendary", PoisonParams> = {
  common: {
    wrap: 0.42,
    weight: 0.85,
    beads: [1, 1],
    size: 0.9,
    swell: 0,
    current: 0,
    glint: 0.55,
    rest: 1,
  },
  rare: {
    wrap: 0.66,
    weight: 0.95,
    beads: [1, 1],
    size: 1,
    swell: 0,
    current: 0,
    glint: 0.7,
    rest: 1,
  },
  epic: {
    wrap: 1,
    weight: 1.08,
    beads: [1, 2],
    size: 1.08,
    swell: 0.6,
    current: 0.35,
    glint: 0.85,
    rest: 1,
  },
  legendary: {
    wrap: 1,
    weight: 1.22,
    beads: [1, 3],
    size: 1.18,
    swell: 0.85,
    current: 1,
    glint: 1,
    rest: 2,
  },
};

const dripLead = { ambient: [900, 2600], engaged: [120, 120] } as const;
const flowLead = { ambient: [1600, 4000], engaged: [300, 300] } as const;
const shineLead = { ambient: [3000, 7000], engaged: [600, 600] } as const;

/**
 * Poison's tier program, in ms. Drips never come faster than a whole bead cycle (the
 * longest pour ends in about 2.4s), so a new drip never cuts a falling bead short.
 */
const program: ElementalTierPrograms = {
  common: {
    cadence: {
      drip: { ambient: [7000, 11500], engaged: [4500, 7500], lead: dripLead },
      flow: { ambient: [8000, 14000], engaged: [5000, 8000], lead: flowLead },
      shine: { ambient: [12000, 20000], engaged: [8000, 13000], lead: shineLead },
    },
    params: params.common,
  },
  rare: {
    cadence: {
      drip: { ambient: [5200, 8800], engaged: [3600, 6000], lead: dripLead },
      flow: { ambient: [6500, 11000], engaged: [4200, 6800], lead: flowLead },
      shine: { ambient: [10000, 17000], engaged: [7000, 11000], lead: shineLead },
    },
    params: params.rare,
  },
  epic: {
    cadence: {
      drip: { ambient: [4000, 6800], engaged: [3100, 5200], lead: dripLead },
      flow: { ambient: [5000, 8500], engaged: [3400, 5600], lead: flowLead },
      shine: { ambient: [8500, 14000], engaged: [6000, 9500], lead: shineLead },
    },
    params: params.epic,
  },
  legendary: {
    cadence: {
      drip: { ambient: [3000, 5200], engaged: [2900, 4600], lead: dripLead },
      flow: { ambient: [4000, 6800], engaged: [2800, 4600], lead: flowLead },
      shine: { ambient: [7000, 12000], engaged: [5000, 8000], lead: shineLead },
    },
    params: params.legendary,
  },
};

/* ---- Geometry ------------------------------------------------------------------------ */

/* A liquid outline: every letter is a soft rounded block, and blocks melt into each other
   (a smooth union) the way poison held by surface tension bridges the gap between two
   letters and pinches where a word ends. The edge is one level of that field, traced with
   marching squares, so it bends into every gap instead of boxing the word. */

/** Signed distance to a rounded box. */
function roundedBox(px: number, py: number, box: Box): number {
  const qx = Math.abs(px - box.cx) - box.hx + box.r;
  const qy = Math.abs(py - box.cy) - box.hy + box.r;
  const outside = Math.hypot(Math.max(qx, 0), Math.max(qy, 0));
  return outside + Math.min(Math.max(qx, qy), 0) - box.r;
}

/** Polynomial smooth minimum: blends two fields over a distance `k`. */
function smoothMin(a: number, b: number, k: number): number {
  const h = Math.max(k - Math.abs(a - b), 0) / k;
  return Math.min(a, b) - h * h * k * 0.25;
}

interface Box {
  cx: number;
  cy: number;
  hx: number;
  hy: number;
  r: number;
}

/** A lowest point of the band where beads gather. */
export interface PoisonSite {
  x: number;
  y: number;
  /** Index of the line it hangs under. */
  line: number;
  /** Depth ranking value: lower on screen gathers first. */
  depth: number;
}

/**
 * Traces the level set `field = 0` over a grid with marching squares and chains the
 * segments into closed loops (first point repeated at the end).
 */
function traceLoops(
  field: (x: number, y: number) => number,
  left: number,
  top: number,
  cols: number,
  rows: number,
  cell: number,
): Point[][] {
  const values = new Float64Array((cols + 1) * (rows + 1));
  for (let j = 0; j <= rows; j += 1)
    for (let i = 0; i <= cols; i += 1)
      values[j * (cols + 1) + i] = field(left + i * cell, top + j * cell);
  const value = (i: number, j: number) => values[j * (cols + 1) + i];
  // Edge ids: horizontal edge (i, j) → i, j; vertical edge (i, j) → offset.
  const vertical = (cols + 1) * (rows + 1);
  const horizontalId = (i: number, j: number) => j * (cols + 1) + i;
  const verticalId = (i: number, j: number) => vertical + j * (cols + 1) + i;
  const points = new Map<number, Point>();
  const crossing = (
    id: number,
    ax: number,
    ay: number,
    a: number,
    bx: number,
    by: number,
    b: number,
  ) => {
    if (!points.has(id)) {
      const t = a / (a - b);
      points.set(id, {
        x: left + (ax + (bx - ax) * t) * cell,
        y: top + (ay + (by - ay) * t) * cell,
      });
    }
    return id;
  };
  const links = new Map<number, number[]>();
  const link = (a: number, b: number) => {
    links.set(a, [...(links.get(a) ?? []), b]);
    links.set(b, [...(links.get(b) ?? []), a]);
  };
  for (let j = 0; j < rows; j += 1)
    for (let i = 0; i < cols; i += 1) {
      const a = value(i, j);
      const b = value(i + 1, j);
      const c = value(i + 1, j + 1);
      const d = value(i, j + 1);
      const inside = [a < 0, b < 0, c < 0, d < 0];
      const edges: number[] = [];
      if (inside[0] !== inside[1]) edges.push(crossing(horizontalId(i, j), i, j, a, i + 1, j, b));
      if (inside[1] !== inside[2])
        edges.push(crossing(verticalId(i + 1, j), i + 1, j, b, i + 1, j + 1, c));
      if (inside[2] !== inside[3])
        edges.push(crossing(horizontalId(i, j + 1), i + 1, j + 1, c, i, j + 1, d));
      if (inside[3] !== inside[0]) edges.push(crossing(verticalId(i, j), i, j + 1, d, i, j, a));
      if (edges.length === 2) link(edges[0], edges[1]);
      else if (edges.length === 4) {
        // A saddle: the centre decides which corners connect.
        const centre = (a + b + c + d) / 4 < 0;
        if (centre === inside[0]) {
          link(edges[0], edges[1]);
          link(edges[2], edges[3]);
        } else {
          link(edges[0], edges[3]);
          link(edges[1], edges[2]);
        }
      }
    }
  const loops: Point[][] = [];
  const seen = new Set<number>();
  for (const start of links.keys()) {
    if (seen.has(start)) continue;
    const loop: Point[] = [];
    let previous = -1;
    let current = start;
    while (!seen.has(current)) {
      seen.add(current);
      loop.push(points.get(current)!);
      const next = (links.get(current) ?? []).find((id) => id !== previous && !seen.has(id));
      if (next === undefined) break;
      previous = current;
      current = next;
    }
    if (loop.length > 8) loops.push([...loop, loop[0]]);
  }
  return loops;
}

/** Twice the signed area on screen; negative runs the way the bands expect. */
function signedArea(loop: Point[]): number {
  let area = 0;
  for (let index = 0; index < loop.length - 1; index += 1)
    area += loop[index].x * loop[index + 1].y - loop[index + 1].x * loop[index].y;
  return area;
}

/** Laplacian smoothing on a closed loop: removes the grid's stair steps. */
function relax(loop: Point[], passes: number): Point[] {
  let ring = loop.slice(0, -1);
  for (let pass = 0; pass < passes; pass += 1)
    ring = ring.map((point, index) => {
      const previous = ring[(index - 1 + ring.length) % ring.length];
      const next = ring[(index + 1) % ring.length];
      return {
        x: (previous.x + point.x * 2 + next.x) / 4,
        y: (previous.y + point.y * 2 + next.y) / 4,
      };
    });
  return [...ring, ring[0]];
}

/** Rotates a closed loop to start at its top centre, running left along the top. */
function fromTop(loop: Point[]): Point[] {
  const ring = signedArea(loop) > 0 ? loop.slice(0, -1).reverse() : loop.slice(0, -1);
  const xs = ring.map((point) => point.x);
  const centre = (Math.min(...xs) + Math.max(...xs)) / 2;
  let best = 0;
  ring.forEach((point, index) => {
    const score = Math.abs(point.x - centre) + point.y * 4;
    const current = Math.abs(ring[best].x - centre) + ring[best].y * 4;
    if (score < current) best = index;
  });
  const rotated = [...ring.slice(best), ...ring.slice(0, best)];
  return [...rotated, rotated[0]];
}

interface LiquidLoop {
  /** Closed loop from the top centre, running left along the top. */
  loop: Point[];
  /** Arc length of the loop's bottom centre. */
  bottomCentre: number;
  line: number;
}

/** The liquid outline of one line: one loop per pool (words far apart become separate pools). */
function liquidLoops(line: Line, index: number, em: number, weight: number): LiquidLoop[] {
  const boxes: Box[] = line.glyphs.map((glyph) => {
    const hx = Math.max(em * 0.06, glyph.width * 0.42);
    const hy = Math.max(em * 0.08, (glyph.inkBottom - glyph.inkTop) / 2);
    return {
      cx: glyph.x + glyph.width / 2,
      cy: (glyph.inkTop + glyph.inkBottom) / 2,
      hx,
      hy,
      r: Math.min(hx, hy, em * 0.12),
    };
  });
  const top = Math.min(...line.glyphs.map((glyph) => glyph.inkTop));
  const bottom = Math.max(...line.glyphs.map((glyph) => glyph.inkBottom));
  const middle = (top + bottom) / 2;
  const blend = em * 0.2;
  const reach = em * 0.07;
  // Gravity: the liquid hangs lower and heavier beneath the letters than above them.
  const pool = em * 0.09 * weight;
  const field = (x: number, y: number) => {
    let distance = Infinity;
    for (const box of boxes) {
      if (Math.abs(x - box.cx) > box.hx + em) continue;
      const next = roundedBox(x, y, box);
      distance = distance === Infinity ? next : smoothMin(distance, next, blend);
    }
    const sag = Math.min(1, Math.max(0, (y - middle) / (bottom - middle + em * 0.25)));
    return distance - reach - pool * sag * sag;
  };
  const margin = em * 0.5;
  let cell = Math.max(0.6, em * 0.05);
  const width = line.right - line.left + margin * 2;
  const height = bottom - top + margin * 2;
  // Keep the grid bounded on very long names.
  while ((width / cell) * (height / cell) > 60000) cell *= 1.25;
  const cols = Math.ceil(width / cell);
  const rows = Math.ceil(height / cell);
  return traceLoops(field, line.left - margin, top - margin, cols, rows, cell)
    .filter((loop) => signedArea(loop) !== 0)
    .map((loop) => fromTop(relax(loop, 3)))
    .filter((loop, _, all) => {
      // Drop holes: loops lying inside another loop's bounds.
      const box = bounds(loop);
      return !all.some((other) => {
        if (other === loop) return false;
        const outer = bounds(other);
        return (
          outer.left < box.left &&
          outer.right > box.right &&
          outer.top < box.top &&
          outer.bottom > box.bottom
        );
      });
    })
    .map((loop) => {
      const measure = measurePolyline(loop);
      const box = bounds(loop);
      const centre = (box.left + box.right) / 2;
      let best = 0;
      loop.forEach((point, at) => {
        const score = Math.abs(point.x - centre) - point.y * 4;
        const current = Math.abs(loop[best].x - centre) - loop[best].y * 4;
        if (score < current) best = at;
      });
      return { loop, bottomCentre: measure.cumulative[best], line: index };
    });
}

function bounds(points: Point[]) {
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  return {
    left: Math.min(...xs),
    right: Math.max(...xs),
    top: Math.min(...ys),
    bottom: Math.max(...ys),
  };
}

/** The part of a closed loop within [start, end] of its length, as an open polyline. */
function stretchOf(loop: Point[], start: number, end: number): Point[] {
  const measure = measurePolyline(loop);
  const points: Point[] = [];
  const at = (along: number) => {
    let index = 0;
    while (index < loop.length - 2 && measure.cumulative[index + 1] < along) index += 1;
    const a = loop[index];
    const b = loop[index + 1] ?? a;
    const length = measure.cumulative[index + 1] - measure.cumulative[index] || 1;
    const t = Math.min(1, Math.max(0, (along - measure.cumulative[index]) / length));
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  };
  points.push(at(start));
  loop.forEach((point, index) => {
    if (measure.cumulative[index] > start && measure.cumulative[index] < end) points.push(point);
  });
  points.push(at(end));
  return points;
}

const smoothstep = (edge: number, value: number) => {
  const t = Math.min(1, Math.max(0, value / edge));
  return t * t * (3 - 2 * t);
};

/** Unit tangents along a spine; a closed spine wraps around its seam. */
export function tangentsOf(spine: Point[], closed: boolean): Point[] {
  const count = spine.length;
  return spine.map((point, index) => {
    const previous = spine[index - 1] ?? (closed ? spine[count - 2] : point);
    const next = spine[index + 1] ?? (closed ? spine[1] : point);
    return normalize({ x: next.x - previous.x, y: next.y - previous.y });
  });
}

export interface PoisonGeometry {
  bands: ElementalPoisonBand[];
  /** Where beads gather, deepest first. */
  sites: PoisonSite[];
  /** Other points along the undersides, about 0.3em apart, where a drip can form too. */
  underside: PoisonSite[];
}

/** Low points on a band's underside: where the outline turns from falling to rising. */
function sitesOn(band: ElementalPoisonBand, line: number, em: number): PoisonSite[] {
  const { spine, closed } = band;
  const tangents = tangentsOf(spine, closed);
  const reach = Math.max(2, Math.round((em * 0.25) / Math.max(0.6, em * 0.05)));
  const found: PoisonSite[] = [];
  spine.forEach((point, index) => {
    // Only the underside (outward normal pointing down) gathers beads.
    if (tangents[index].x < 0.75) return;
    for (let offset = -reach; offset <= reach; offset += 1) {
      const other = spine[index + offset];
      if (other && other.y > point.y) return;
    }
    found.push({ x: point.x, y: point.y, line, depth: point.y });
  });
  return found;
}

const geometryCache = new WeakMap<ElementalStage, Map<string, PoisonGeometry>>();

/**
 * The flowing edge around every line of the name, and the points under it where beads
 * gather. Pure and cached per measured stage.
 */
export function poisonGeometry(
  stage: ElementalStage,
  wrap: number,
  weight: number,
): PoisonGeometry {
  const key = `${wrap}:${weight}`;
  const cached = geometryCache.get(stage)?.get(key);
  if (cached) return cached;
  const em = stage.em;
  const loops = linesOf(stage).flatMap((line, index) => liquidLoops(line, index, em, weight));
  const bands = loops.map(({ loop, bottomCentre }): ElementalPoisonBand => {
    const closed = wrap >= 1;
    const total = measurePolyline(loop).total;
    const spine = closed
      ? loop
      : stretchOf(
          loop,
          Math.max(0, bottomCentre - (wrap * total) / 2),
          Math.min(total, bottomCentre + (wrap * total) / 2),
        );
    const measure = measurePolyline(spine);
    const tangents = tangentsOf(spine, closed);
    const widths = spine.map((_, index) => {
      // Outward normal is (-ty, tx), so its downward share is the tangent's x.
      const down = Math.min(1, Math.max(0, (tangents[index].x + 1) / 2));
      const along = measure.total ? measure.cumulative[index] / measure.total : 0;
      // Gravity pools the poison underneath; a slow swell keeps that width from ever
      // looking drawn with a pen. Above, only a thin film clings, and it breaks into
      // fragments the way a film of poison beads up instead of drawing an outline.
      const swell =
        1 + 0.16 * Math.sin(along * Math.PI * 2 * Math.max(1, measure.total / (em * 2.2)));
      const film = Math.pow(
        Math.max(0, Math.sin(along * Math.PI * 2 * Math.max(2, measure.total / (em * 0.9)) + 0.7)),
        1.5,
      );
      const width =
        em *
        weight *
        (0.09 * Math.pow(Math.max(0, (down - 0.56) / 0.44), 1.3) * swell +
          0.024 * film * Math.min(1, Math.max(0, (0.42 - down) / 0.3)));
      if (closed) return width;
      return width * smoothstep(0.16, along) * smoothstep(0.16, 1 - along);
    });
    return { spine, widths, closed, highlight: closed ? [0.06, 0.2] : [0.3, 0.44] };
  });
  const sites: PoisonSite[] = [];
  bands.forEach((band, index) => sites.push(...sitesOn(band, loops[index].line, em)));
  const ranked = sites.sort((a, b) => b.depth - a.depth || a.x - b.x);
  const spaced: PoisonSite[] = [];
  for (const site of ranked)
    if (spaced.every((other) => other.line !== site.line || Math.abs(other.x - site.x) >= em * 0.6))
      spaced.push({
        ...site,
        // Hang from the band's outer edge, overlapping it so the bead grows out of it.
        y: site.y + em * 0.035 * weight,
      });
  const underside: PoisonSite[] = [];
  bands.forEach((band, index) => {
    const tangents = tangentsOf(band.spine, band.closed);
    let last = -Infinity;
    band.spine.forEach((point, at) => {
      // Only where the underside runs level and the poison is thick enough to hold a bead.
      if (tangents[at].x < 0.9 || band.widths[at] < em * 0.04 || point.x - last < em * 0.3) return;
      last = point.x;
      underside.push({
        x: point.x,
        y: point.y + em * 0.035 * weight,
        line: loops[index].line,
        depth: point.y,
      });
    });
  });
  const geometry = { bands, sites: spaced, underside };
  let byStage = geometryCache.get(stage);
  if (!byStage) geometryCache.set(stage, (byStage = new Map()));
  byStage.set(key, geometry);
  return geometry;
}

/* ---- Frames -------------------------------------------------------------------------- */

const material = (
  bands: ElementalPoisonBand[],
  beads: ElementalPoisonBead[],
  flows: ElementalPoisonFlow[],
): ElementalPoisonMaterial => ({ type: "poison", bands, beads, flows });

/** Beads stay readable on a phone: never smaller than about 2px across the bulb's radius. */
const beadRadius = (em: number, size: number, random: Random) =>
  Math.max(1.9, em * between(random, 0.09, 0.115) * size);

/** The resting edge with beads hanging at its lowest points: poison in a single frame. */
export function poisonStill(
  stage: ElementalStage,
  profile: PoisonParams,
  key: number,
  random: Random,
) {
  const { bands, sites } = poisonGeometry(stage, profile.wrap, profile.weight);
  const beads = sites.slice(0, profile.rest).map(
    (site): ElementalPoisonBead => ({
      x: site.x,
      y: site.y,
      radius: beadRadius(stage.em, profile.size, random),
      delay: 0,
      gather: 0,
      fall: 0,
      drop: 0,
      hang: between(random, 0.62, 0.78),
    }),
  );
  return {
    key,
    slot: "still",
    life: 1,
    rest: 1,
    persist: true,
    bolts: [],
    shards: [],
    lights: [],
    material: material(bands, beads, []),
  } satisfies ElementalFrame;
}

/**
 * In a pour, each bead starts gathering the moment the one before it lets go, smaller and
 * quicker. A lone drip takes its time; a pour's first bead is a little faster, so even a
 * three-bead pour (about 2.8s) ends before the fastest next drip.
 */
const pourGather: ElementalRange = [380, 520];

export function poisonDrip(
  stage: ElementalStage,
  profile: PoisonParams,
  key: number,
  random: Random,
): { frame: ElementalFrame; site?: PoisonSite; release: number } {
  const { sites, underside } = poisonGeometry(stage, profile.wrap, profile.weight);
  // Resting beads keep their points. Drips favour the other low points, and otherwise form
  // anywhere along a level underside, away from the hanging beads.
  const resting = sites.slice(0, profile.rest);
  const clear = (site: PoisonSite) =>
    resting.every(
      (other) => other.line !== site.line || Math.abs(other.x - site.x) >= stage.em * 0.6,
    );
  const deep = sites.slice(profile.rest, profile.rest + 3);
  const open = underside.filter(clear);
  const site =
    deep.length && (!open.length || chance(random, 0.6))
      ? pick(random, deep)
      : open.length
        ? pick(random, open)
        : sites[0];
  const beads: ElementalPoisonBead[] = [];
  let release = 0;
  if (site) {
    const count = integer(random, profile.beads[0], profile.beads[1]);
    let delay = 0;
    for (let index = 0; index < count; index += 1) {
      const first = index === 0;
      const gather = first
        ? between(random, 900, count > 1 ? 1200 : 1500)
        : between(random, pourGather[0], pourGather[1]);
      const bead: ElementalPoisonBead = {
        x: site.x,
        y: site.y,
        radius: beadRadius(stage.em, profile.size, random) * (first ? 1 : 0.8),
        delay,
        gather,
        fall: 520,
        drop: stage.em * between(random, 0.42, 0.58),
      };
      if (first) release = gather;
      beads.push(bead);
      delay += gather;
    }
  }
  const life = beads.reduce((end, bead) => Math.max(end, bead.delay + bead.gather + bead.fall), 1);
  return {
    frame: {
      key,
      slot: "drip",
      life,
      rest: 1,
      bolts: [],
      shards: [],
      lights: [],
      material: material([], beads, []),
    },
    site,
    release,
  };
}

/**
 * A weighted letter: as a bead gathers beneath it, the letter above sinks a hair under
 * its weight; when the bead lets go it springs back past rest and settles. The nearest
 * neighbour follows at half strength. Transform only, starting and ending at rest.
 */
export function poisonSwell(
  stage: ElementalStage,
  site: PoisonSite,
  release: number,
  strength: number,
): LetterAnimation[] {
  const line = linesOf(stage)[site.line];
  if (!line) return [];
  const ranked = line.glyphs
    .map((glyph) => ({ glyph, away: Math.abs(glyph.center.x - site.x) }))
    .sort((a, b) => a.away - b.away);
  const duration = release + 560;
  const at = release / duration;
  const sink = stage.em * (0.03 + 0.03 * strength);
  const animation = (glyph: ElementalGlyph, share: number, delay: number): LetterAnimation => ({
    glyph: stage.glyphs.indexOf(glyph),
    delay,
    duration,
    origin: "50% 100%",
    easing: "linear",
    keyframes: [
      { transform: "translateY(0px)", easing: "cubic-bezier(0.45, 0, 0.55, 1)" },
      {
        transform: `translateY(${(sink * share).toFixed(2)}px)`,
        offset: at,
        easing: "cubic-bezier(0.2, 0.9, 0.3, 1)",
      },
      {
        transform: `translateY(${(-sink * share * 0.4).toFixed(2)}px)`,
        offset: at + (1 - at) * 0.38,
        easing: "cubic-bezier(0.4, 0, 0.3, 1)",
      },
      { transform: "translateY(0px)" },
    ],
  });
  const result = [animation(ranked[0].glyph, 1, 0)];
  const neighbour = ranked[1];
  if (neighbour && neighbour.away < stage.em)
    result.push({ ...animation(neighbour.glyph, 0.5, 0), delay: 60 });
  return result.filter((item) => item.glyph >= 0);
}

export function poisonFlow(
  stage: ElementalStage,
  profile: PoisonParams,
  key: number,
  random: Random,
  quick: boolean,
): ElementalFrame {
  const { bands } = poisonGeometry(stage, profile.wrap, profile.weight);
  const flows = bands.map(
    (band, index): ElementalPoisonFlow => ({
      spine: band.spine,
      delay: index * 140,
      duration: between(random, 2200, 3200) * (quick ? 0.8 : 1),
      length: band.closed ? 0.14 : 0.22,
      gain: profile.glint * between(random, 0.85, 1),
      reverse: chance(random, 0.35),
      current: profile.current,
      width: Math.max(0.7, stage.em * 0.034),
    }),
  );
  const life = flows.reduce((end, flow) => Math.max(end, flow.delay + flow.duration), 1);
  return {
    key,
    slot: "flow",
    life,
    rest: 0,
    bolts: [],
    shards: [],
    lights: [],
    material: material([], [], flows),
  };
}

/**
 * Poison: a smooth, weighty edge that clings around the lettering from behind, heavier
 * where gravity pools it, with beads that slowly gather at its lowest points, let go and
 * fall. A highlight flows along the edge now and then, and at higher bond tiers a letter
 * sinks a hair under a gathering bead and springs back when it drops. No sparkle.
 */
export const poison: ElementalEffect = {
  id: "poison",
  layers: { overlay: true, letters: true },
  // Beads fall below the name; the band hugs the letters, so less room is needed above.
  overscan: { x: 0.7, top: 0.7, bottom: 1.15 },
  moments: { drip: { priority: 2 }, flow: { priority: 1 }, shine: { priority: 0 } },
  program,
  still: (stage, { params: tierParams, random, key }) =>
    poisonStill(stage, tierParams as PoisonParams, key, random),
  timeline(moment, stage, context) {
    if (!stage.glyphs.length || !stage.em) return null;
    const { random, key } = context;
    const profile = context.params as PoisonParams;
    const quick = context.engaged && context.interactive;
    switch (moment) {
      case "drip": {
        const { frame, site, release } = poisonDrip(stage, profile, key, random);
        const cues: ElementalCue[] = [{ type: "frame", at: 0, beat: "gather", frame }];
        if (site && profile.swell > 0) {
          // Its own stream, so the letter decision never changes the bead.
          const letters = createRandom(context.textSeed ^ frame.key);
          if (context.explicit || chance(letters, profile.swell)) {
            const animations = poisonSwell(stage, site, release, profile.swell);
            if (animations.length)
              cues.push({ type: "letters", at: 0, beat: "gather", animations });
          }
        }
        return timeline("drip", poison.moments.drip.priority, cues, [
          { label: "gather", at: 0 },
          { label: "release", at: Math.round(release) },
        ]);
      }
      case "flow":
        return timeline("flow", poison.moments.flow.priority, [
          { type: "frame", at: 0, frame: poisonFlow(stage, profile, key, random, quick) },
        ]);
      case "shine": {
        // A slow, broad sheen: light moving across wet letters, never a glint.
        const duration = between(random, 2200, 3200) * (quick ? 0.85 : 1);
        return timeline("shine", poison.moments.shine.priority, [
          {
            type: "shine",
            at: 0,
            duration,
            angle: between(random, 100, 116),
            reverse: random() < 0.3,
            gain: between(random, 0.7, 1),
            rise: between(random, 0.3, 0.38),
            hold: between(random, 0.6, 0.7),
            fade: between(random, 0.75, 0.9),
          },
        ]);
      }
      default:
        return null;
    }
  },
};
