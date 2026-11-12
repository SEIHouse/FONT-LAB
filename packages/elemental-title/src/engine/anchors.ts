import { clampPoint, type Point, type Rect } from "./geometry";
import { descentShare } from "./stage";
import type { ElementalGlyph, ElementalStage } from "./types";

/**
 * Vertical reference lines of a line of text, measured from its baseline in em:
 * `top` is cap height, `x-height` the top of lowercase letters, `middle` the middle of
 * the x-height band, `bottom` the depth of descenders.
 */
export type AnchorLevel = "top" | "x-height" | "middle" | "baseline" | "bottom";

const levels: Record<AnchorLevel, number> = {
  top: -0.7,
  "x-height": -0.47,
  middle: -0.24,
  baseline: 0,
  bottom: 0.21,
};

/** One line of the name, left to right on screen. */
export interface AnchorLine {
  /** Glyph indices on this line, left to right. */
  glyphs: number[];
  /** Left edge of the line's first glyph box. */
  start: number;
  /** Right edge of the line's last glyph box. */
  end: number;
  baseline: number;
}

/** Where a scene can attach, measured once from the stage. All values are stage pixels. */
export interface SceneAnchors {
  em: number;
  /** Lines in reading order, top to bottom. A name that wraps has several. */
  lines: AnchorLine[];
  /** The name's box: every line's glyph boxes from cap height to descender depth. */
  box: Rect;
  /**
   * A bounding ellipse around the name: centred on its box and as wide as the overscan
   * allows (about half an em past each end).
   */
  ellipse: { center: Point; rx: number; ry: number };
  /** The overlay (the stage), which every primitive stays inside. */
  bounds: Rect;
}

/** Groups glyphs into lines by their boxes, as the letter engine does. */
function linesOf(stage: ElementalStage): AnchorLine[] {
  const ordered = stage.glyphs
    .map((glyph, index) => ({ glyph, index }))
    .sort((a, b) => a.glyph.y - b.glyph.y || a.glyph.x - b.glyph.x);
  const groups: { items: typeof ordered; top: number; bottom: number }[] = [];
  for (const item of ordered) {
    const group = groups.at(-1);
    const { y, height } = item.glyph;
    const overlap = group ? Math.min(group.bottom, y + height) - Math.max(group.top, y) : 0;
    if (group && overlap > Math.min(group.bottom - group.top, height) * 0.5) {
      group.items.push(item);
      group.top = Math.min(group.top, y);
      group.bottom = Math.max(group.bottom, y + height);
    } else groups.push({ items: [item], top: y, bottom: y + height });
  }
  return groups.map(({ items }) => {
    items.sort((a, b) => a.glyph.x - b.glyph.x);
    const baselines = items
      .map(({ glyph }) => glyph.y + glyph.height * (1 - descentShare))
      .sort((a, b) => a - b);
    return {
      glyphs: items.map(({ index }) => index),
      start: Math.min(...items.map(({ glyph }) => glyph.x)),
      end: Math.max(...items.map(({ glyph }) => glyph.x + glyph.width)),
      baseline: baselines[Math.floor(baselines.length / 2)],
    };
  });
}

/** The y of a level on a line. */
export const levelOf = (line: AnchorLine, level: AnchorLevel, em: number) =>
  line.baseline + levels[level] * em;

/** Measures the anchors of a stage; null when the name has no glyphs. */
export function sceneAnchors(stage: ElementalStage): SceneAnchors | null {
  const lines = linesOf(stage);
  if (!lines.length) return null;
  const { em } = stage;
  const first = lines[0];
  const last = lines.at(-1)!;
  const left = Math.min(...lines.map((line) => line.start));
  const right = Math.max(...lines.map((line) => line.end));
  const top = levelOf(first, "top", em);
  const bottom = levelOf(last, "bottom", em);
  const box = { x: left, y: top, width: right - left, height: bottom - top };
  const center = { x: left + box.width / 2, y: (top + levelOf(last, "baseline", em)) / 2 };
  const room = Math.max(0, Math.min(center.x, stage.width - center.x) - em * 0.12);
  return {
    em,
    lines,
    box,
    ellipse: {
      center,
      rx: Math.min(box.width / 2 + em * 0.45, room),
      ry: (levelOf(last, "baseline", em) - top) / 2 + em * 0.2,
    },
    bounds: { x: 0, y: 0, width: stage.width, height: stage.height },
  };
}

/** What a point attaches to. */
export type AnchorTarget =
  | "start"
  | "end"
  | { glyph: "first" | "last" | number; x?: number }
  | { ellipse: number };

export interface AnchorSpec {
  /**
   * `start`: where the name begins (first line); `end`: where it ends (last line);
   * a glyph (first, last or by index; `x` 0–1 across its box, default 0.5); or a point
   * on the bounding ellipse at an angle in degrees (0 east, 90 south, clockwise).
   */
  at: AnchorTarget;
  /** Height on the target's line. Ignored on the ellipse. Default baseline. */
  level?: AnchorLevel;
  /** Offsets in em. */
  dx?: number;
  dy?: number;
}

function glyphLine(anchors: SceneAnchors, glyph: number) {
  return anchors.lines.find((line) => line.glyphs.includes(glyph)) ?? anchors.lines[0];
}

/** Resolves an anchor to a stage point. Glyph indices past either end clamp to it. */
export function anchorPoint(
  anchors: SceneAnchors,
  stage: ElementalStage,
  { at, level = "baseline", dx = 0, dy = 0 }: AnchorSpec,
): Point {
  const { em, lines } = anchors;
  let point: Point;
  if (at === "start") point = { x: lines[0].start, y: levelOf(lines[0], level, em) };
  else if (at === "end") {
    const line = lines.at(-1)!;
    point = { x: line.end, y: levelOf(line, level, em) };
  } else if ("ellipse" in at) {
    const angle = (at.ellipse * Math.PI) / 180;
    const { center, rx, ry } = anchors.ellipse;
    point = { x: center.x + Math.cos(angle) * rx, y: center.y + Math.sin(angle) * ry };
  } else {
    const count = stage.glyphs.length;
    const index =
      at.glyph === "first"
        ? lines[0].glyphs[0]
        : at.glyph === "last"
          ? lines.at(-1)!.glyphs.at(-1)!
          : Math.min(count - 1, Math.max(0, Math.round(at.glyph)));
    const glyph: ElementalGlyph = stage.glyphs[index];
    point = {
      x: glyph.x + glyph.width * (at.x ?? 0.5),
      y: levelOf(glyphLine(anchors, index), level, em),
    };
  }
  return { x: point.x + dx * em, y: point.y + dy * em };
}

/** Keeps a point inside the stage, `inset` px from its edges. */
export const insideStage = (anchors: SceneAnchors, point: Point, inset = 1) =>
  clampPoint(point, anchors.bounds, inset);
