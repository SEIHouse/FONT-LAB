import { between, type Random } from "./random";

export interface Point {
  x: number;
  y: number;
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const distance = (a: Point, b: Point) => Math.hypot(b.x - a.x, b.y - a.y);

export const lerpPoint = (a: Point, b: Point, t: number): Point => ({
  x: a.x + (b.x - a.x) * t,
  y: a.y + (b.y - a.y) * t,
});

export const rotate = (direction: Point, angle: number): Point => ({
  x: direction.x * Math.cos(angle) - direction.y * Math.sin(angle),
  y: direction.x * Math.sin(angle) + direction.y * Math.cos(angle),
});

export function normalize(direction: Point): Point {
  const length = Math.hypot(direction.x, direction.y) || 1;
  return { x: direction.x / length, y: direction.y / length };
}

export const clampPoint = (point: Point, bounds: Rect, inset = 0): Point => ({
  x: Math.min(bounds.x + bounds.width - inset, Math.max(bounds.x + inset, point.x)),
  y: Math.min(bounds.y + bounds.height - inset, Math.max(bounds.y + inset, point.y)),
});

/** Samples a quadratic curve through `control` into a short polyline (ends included). */
export function curve(start: Point, control: Point, end: Point, samples: number): Point[] {
  const points: Point[] = [];
  for (let index = 0; index <= samples; index += 1) {
    const t = index / samples;
    const inverse = 1 - t;
    points.push({
      x: inverse * inverse * start.x + 2 * inverse * t * control.x + t * t * end.x,
      y: inverse * inverse * start.y + 2 * inverse * t * control.y + t * t * end.y,
    });
  }
  return points;
}

/** Samples a cubic Bézier curve into a polyline (ends included). */
export function cubic(
  start: Point,
  first: Point,
  second: Point,
  end: Point,
  samples: number,
): Point[] {
  const points: Point[] = [];
  for (let index = 0; index <= samples; index += 1) {
    const t = index / samples;
    const u = 1 - t;
    const a = u * u * u;
    const b = 3 * u * u * t;
    const c = 3 * u * t * t;
    const d = t * t * t;
    points.push({
      x: a * start.x + b * first.x + c * second.x + d * end.x,
      y: a * start.y + b * first.y + c * second.y + d * end.y,
    });
  }
  return points;
}

/**
 * Samples an elliptical arc. Angles are in degrees, measured clockwise on screen from
 * east (0 = east, 90 = south, 180 = west, 270 = north); `to` may be below `from` to run
 * counterclockwise.
 */
export function ellipseArc(
  center: Point,
  rx: number,
  ry: number,
  from: number,
  to: number,
  samples: number,
): Point[] {
  const points: Point[] = [];
  for (let index = 0; index <= samples; index += 1) {
    const angle = ((from + ((to - from) * index) / samples) * Math.PI) / 180;
    points.push({ x: center.x + Math.cos(angle) * rx, y: center.y + Math.sin(angle) * ry });
  }
  return points;
}

export interface RoughenOptions {
  /** Subdivision passes; each pass doubles the segment count. */
  detail: number;
  /** Sideways displacement as a share of the segment length on the first pass. */
  roughness: number;
  /** How much each finer pass calms down relative to the previous one. */
  damping?: number;
}

/**
 * Fractal midpoint displacement. Every pass splits each segment near its middle and
 * pushes the new vertex sideways, giving the jagged, self-similar silhouette of an arc.
 */
export function roughen(base: Point[], random: Random, options: RoughenOptions): Point[] {
  const { detail, roughness, damping = 0.72 } = options;
  let points = base.slice();
  let amount = roughness;
  for (let pass = 0; pass < detail; pass += 1) {
    const next: Point[] = [points[0]];
    for (let index = 0; index < points.length - 1; index += 1) {
      const a = points[index];
      const b = points[index + 1];
      const length = distance(a, b);
      const middle = lerpPoint(a, b, between(random, 0.36, 0.64));
      const normalX = -(b.y - a.y) / (length || 1);
      const normalY = (b.x - a.x) / (length || 1);
      const shift = between(random, -1, 1) * amount * length;
      next.push({ x: middle.x + normalX * shift, y: middle.y + normalY * shift }, b);
    }
    points = next;
    amount *= damping;
  }
  return points;
}

export interface PolylineMeasure {
  total: number;
  cumulative: number[];
}

export function measurePolyline(points: Point[]): PolylineMeasure {
  const cumulative = [0];
  for (let index = 1; index < points.length; index += 1)
    cumulative.push(cumulative[index - 1] + distance(points[index - 1], points[index]));
  return { total: cumulative[cumulative.length - 1] ?? 0, cumulative };
}

export interface PolylineSample {
  point: Point;
  /** Unit tangent of the segment the sample lies on. */
  tangent: Point;
  /** Index of the segment start vertex. */
  index: number;
}

/** Point along a polyline at a distance from its start. */
export function sampleAt(points: Point[], measure: PolylineMeasure, along: number): PolylineSample {
  const target = Math.min(measure.total, Math.max(0, along));
  let index = 0;
  while (index < points.length - 2 && measure.cumulative[index + 1] < target) index += 1;
  const a = points[index];
  const b = points[index + 1] ?? a;
  const length = measure.cumulative[index + 1] - measure.cumulative[index] || 1;
  const t = (target - measure.cumulative[index]) / length;
  return { point: lerpPoint(a, b, t), tangent: normalize({ x: b.x - a.x, y: b.y - a.y }), index };
}

export interface Run {
  points: Point[];
  widths: number[];
}

/**
 * Cuts a polyline into runs, skipping the given [start, end] distance intervals.
 * Widths interpolate at the cut points so tapering continues across a gap.
 */
export function cutGaps(
  points: Point[],
  widths: number[],
  measure: PolylineMeasure,
  gaps: [number, number][],
): Run[] {
  if (points.length < 2) return [{ points, widths }];
  const sorted = gaps
    .map(([start, end]) => [Math.max(0, start), Math.min(measure.total, end)] as [number, number])
    .filter(([start, end]) => end > start)
    .sort((a, b) => a[0] - b[0]);
  const at = (along: number) => {
    const sample = sampleAt(points, measure, along);
    const index = sample.index;
    const length = measure.cumulative[index + 1] - measure.cumulative[index] || 1;
    const t = (along - measure.cumulative[index]) / length;
    const width = widths[index] + ((widths[index + 1] ?? widths[index]) - widths[index]) * t;
    return { point: sample.point, width };
  };
  const runs: Run[] = [];
  let cursor = 0;
  let vertex = 0;
  for (const [start, end] of [...sorted, [measure.total, measure.total] as [number, number]]) {
    if (start <= cursor) {
      cursor = Math.max(cursor, end);
      continue;
    }
    const run: Run = { points: [], widths: [] };
    const head = at(cursor);
    run.points.push(head.point);
    run.widths.push(head.width);
    while (vertex < points.length && measure.cumulative[vertex] <= cursor) vertex += 1;
    while (vertex < points.length && measure.cumulative[vertex] < start) {
      run.points.push(points[vertex]);
      run.widths.push(widths[vertex]);
      vertex += 1;
    }
    const tail = at(start);
    run.points.push(tail.point);
    run.widths.push(tail.width);
    if (run.points.length >= 2) runs.push(run);
    cursor = end;
  }
  return runs.length ? runs : [{ points, widths }];
}

const round = (value: number) => Math.round(value * 100) / 100;

export function polylinePath(points: Point[]): string {
  if (points.length < 2) return "";
  let path = `M${round(points[0].x)} ${round(points[0].y)}`;
  for (let index = 1; index < points.length; index += 1)
    path += `L${round(points[index].x)} ${round(points[index].y)}`;
  return path;
}

/**
 * A closed outline around a polyline with a width per vertex, so one filled path
 * can taper and bulge unevenly along its length the way a real arc does.
 */
export function ribbonPath(points: Point[], widths: number[]): string {
  if (points.length < 2) return "";
  const left: Point[] = [];
  const right: Point[] = [];
  for (let index = 0; index < points.length; index += 1) {
    const previous = points[index - 1] ?? points[index];
    const next = points[index + 1] ?? points[index];
    const incoming = normalize({
      x: points[index].x - previous.x,
      y: points[index].y - previous.y,
    });
    const outgoing = normalize({ x: next.x - points[index].x, y: next.y - points[index].y });
    const tangent = normalize({ x: incoming.x + outgoing.x, y: incoming.y + outgoing.y });
    // Sharp kinks would otherwise spike the miter; cap the widening.
    const cosine = Math.max(0.55, Math.abs(tangent.x * outgoing.x + tangent.y * outgoing.y) || 1);
    const half = (widths[index] / 2) * Math.min(1.5, 1 / cosine);
    const normalX = -tangent.y * half;
    const normalY = tangent.x * half;
    left.push({ x: points[index].x + normalX, y: points[index].y + normalY });
    right.push({ x: points[index].x - normalX, y: points[index].y - normalY });
  }
  let path = `M${round(left[0].x)} ${round(left[0].y)}`;
  for (let index = 1; index < left.length; index += 1)
    path += `L${round(left[index].x)} ${round(left[index].y)}`;
  for (let index = right.length - 1; index >= 0; index -= 1)
    path += `L${round(right[index].x)} ${round(right[index].y)}`;
  return `${path}Z`;
}
