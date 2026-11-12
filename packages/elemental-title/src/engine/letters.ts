import { descentShare } from "./stage";
import type { ElementalStage } from "./types";

/** Effects may change only compositor properties. No layout or paint keyframes. */
export type LetterKeyframe = {
  transform?: string;
  opacity?: number;
  offset?: number;
  easing?: string;
};
export interface LetterAnimation {
  glyph: number;
  keyframes: LetterKeyframe[];
  duration: number;
  /** Start after this many milliseconds (relative to the letters cue), via Web Animations. */
  delay?: number;
  /** CSS transform-origin for this letter, e.g. "50% 100%" to grow, melt or hop from its foot. */
  origin?: string;
  /** Timing function for the whole animation; defaults to ease-out. */
  easing?: string;
  /** Optional white edge, animated by opacity only. */
  edge?: boolean;
}

/**
 * Most glyphs one title promotes at once. Covers typical names completely (DAO names
 * run 10–25 letters); on a longer name, glyphs over the cap keep their resting ink for
 * that moment instead of stuttering.
 */
export const letterCap = 32;

/** One horizontal band of a slice, in ink-box coordinates. */
export interface SliceBand {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

/**
 * The device pixel grid in ink-box coordinates: device pixel edges lie where
 * `(value + x) * scale` is a whole number.
 */
export interface PixelGrid {
  x: number;
  y: number;
  scale: number;
}

/** The ink box's device pixel grid, read once when a moment promotes its letters. */
export function pixelGrid(ink: Element): PixelGrid {
  const box = ink.getBoundingClientRect();
  const scale = (typeof window !== "undefined" && window.devicePixelRatio) || 1;
  const phase = (value: number) => {
    const device = value * scale;
    return Math.round((device - Math.floor(device)) * 64) / 64 / scale;
  };
  return { x: phase(box.left), y: phase(box.top), scale };
}

/** A glyph's region: a stack of bands whose edges can step around neighbouring ink. */
export interface LetterSlice {
  x: number;
  y: number;
  width: number;
  height: number;
  bands: SliceBand[];
}

/** Lowercase letters with no ink above the x-height. Anything else is treated as tall. */
const short = /^[acegmnopqrsuvwxyz]$/;
/** Letters and digits with no ink below the baseline. Anything else is treated as deep. */
const shallow = /^[A-IK-PR-Zabcdefhik-oruvwxz0-9]$/;

/**
 * Non-overlapping visual slices, preserving the full browser-shaped run inside each.
 *
 * Each line splits into three bands: above the x-height, the x-height itself and below
 * the baseline. In the middle band neighbours meet halfway between their boxes. Above
 * and below it, a letter with no ink there lends its half to a neighbour that has some,
 * so T and W arms, f hooks and g, j, y tails travel with their own letter. Italic
 * boundaries step along the slant. Inner edges sit on the device pixel grid, so a
 * resting copy and the masked original meet without an anti-aliased seam. The slices
 * still tile the stage exactly, so the resting picture is unchanged whichever layer
 * draws each pixel.
 */
export function letterSlices(
  stage: ElementalStage,
  grid: PixelGrid = { x: 0, y: 0, scale: 1 },
): LetterSlice[] {
  const ordered = stage.glyphs
    .map((glyph, index) => ({ ...glyph, index }))
    .sort((a, b) => a.y - b.y || a.x - b.x);
  const lines: { glyphs: typeof ordered; top: number; bottom: number }[] = [];
  for (const glyph of ordered) {
    const line = lines.at(-1);
    // Fallback emoji fonts can have different vertical metrics on the same line.
    const overlap = line
      ? Math.min(line.bottom, glyph.y + glyph.height) - Math.max(line.top, glyph.y)
      : 0;
    if (line && overlap > Math.min(line.bottom - line.top, glyph.height) * 0.5) {
      line.glyphs.push(glyph);
      line.top = Math.min(line.top, glyph.y);
      line.bottom = Math.max(line.bottom, glyph.y + glyph.height);
    } else lines.push({ glyphs: [glyph], top: glyph.y, bottom: glyph.y + glyph.height });
  }
  const slant = stage.slant ?? 0;
  const deep = (character: string) => !shallow.test(character) || (slant > 0 && character === "f");
  const slices = new Array<LetterSlice>(ordered.length);
  lines.forEach((line, row) => {
    line.glyphs.sort((a, b) => a.x - b.x);
    // Inner edges snap to device pixels; the stage's own edges stay where they are.
    const snapY = (value: number) =>
      Math.round((value + stage.offset.y + grid.y) * grid.scale) / grid.scale -
      grid.y -
      stage.offset.y;
    const snapX = (value: number) =>
      Math.round((value + stage.offset.x + grid.x) * grid.scale) / grid.scale -
      grid.x -
      stage.offset.x;
    const top = row ? snapY((lines[row - 1].bottom + line.top) / 2) : 0;
    const bottom =
      row < lines.length - 1 ? snapY((lines[row + 1].top + line.bottom) / 2) : stage.height;
    const baselines = line.glyphs
      .map((glyph) => glyph.y + glyph.height * (1 - descentShare))
      .sort((a, b) => a - b);
    const baseline = baselines[Math.floor(baselines.length / 2)];
    const clamp = (value: number) => Math.min(bottom, Math.max(top, value));
    // Above most fonts' x-heights; below baseline letters' overshoot and soft shadow, so
    // only descender tails reach into the lower band.
    const cuts = [
      top,
      clamp(snapY(baseline - stage.em * 0.58)),
      clamp(snapY(baseline + Math.max(stage.em * 0.1, stage.em * 0.02 + 2.5))),
      bottom,
    ];
    const inked = [(character: string) => !short.test(character), () => true, deep];
    // Slanted text steps along its lean in short sub-bands; upright text keeps one per band.
    const steps: { top: number; bottom: number; hasInk: (character: string) => boolean }[] = [];
    inked.forEach((hasInk, band) => {
      const height = cuts[band + 1] - cuts[band];
      if (height <= 0) return;
      // Bounded, so a tiny font under a tall line height never explodes the slice outline.
      const count = slant ? Math.min(16, Math.max(1, Math.ceil(height / (stage.em * 0.12)))) : 1;
      let from = cuts[band];
      for (let step = 1; step <= count; step += 1) {
        const to = step === count ? cuts[band + 1] : snapY(cuts[band] + (height * step) / count);
        if (to > from) steps.push({ top: from, bottom: to, hasInk });
        from = Math.max(from, to);
      }
    });
    // boundaries[step][column]: the edge between column and column + 1.
    const boundaries = steps.map(({ top: from, bottom: to, hasInk }) => {
      const shift = (baseline - (from + to) / 2) * slant;
      return line.glyphs.slice(0, -1).map((glyph, column) => {
        const next = line.glyphs[column + 1];
        const left = glyph.x + glyph.width / 2;
        const right = next.x + next.width / 2;
        const a = hasInk(glyph.character);
        const b = hasInk(next.character);
        const edge = a && !b ? right : b && !a ? left : (glyph.x + glyph.width + next.x) / 2;
        return snapX(Math.min(right + shift, Math.max(left + shift, edge + shift)));
      });
    });
    line.glyphs.forEach((glyph, column) => {
      const bands: SliceBand[] = steps.map((step, index) => ({
        top: step.top + stage.offset.y,
        bottom: step.bottom + stage.offset.y,
        left: (column ? boundaries[index][column - 1] : 0) + stage.offset.x,
        right:
          (column < line.glyphs.length - 1 ? boundaries[index][column] : stage.width) +
          stage.offset.x,
      }));
      const x = Math.min(...bands.map((band) => band.left));
      slices[glyph.index] = {
        x,
        y: top + stage.offset.y,
        width: Math.max(...bands.map((band) => band.right)) - x,
        height: bottom - top,
        bands,
      };
    });
  });
  return slices;
}

const fixed = (value: number) => Number(value.toFixed(3));

/** The slice outline: down the right edges, back up the left ones. */
function outline(slice: LetterSlice): [number, number][] {
  const points: [number, number][] = [];
  for (const band of slice.bands)
    points.push([fixed(band.right), fixed(band.top)], [fixed(band.right), fixed(band.bottom)]);
  for (const band of [...slice.bands].reverse())
    points.push([fixed(band.left), fixed(band.bottom)], [fixed(band.left), fixed(band.top)]);
  return points;
}

const pathOf = (points: [number, number][]) => `M${points.map(([x, y]) => `${x} ${y}`).join("L")}Z`;

export interface LetterTrack {
  /** Glyphs this track owns now: without those over the cap or held by a higher priority. */
  readonly glyphs: ReadonlySet<number>;
  /** Starts one letter's animation; `offset` is added to its delay. Unowned glyphs are skipped. */
  animate(request: LetterAnimation, offset?: number): void;
  /** No more animations follow; the glyphs are released together once all have finished. */
  seal(): void;
  /** Stops every animation of the track and releases its glyphs now. */
  release(): void;
}

export interface LetterAnimator {
  /**
   * Promotes a timeline's whole glyph set at once: one style snapshot, one mask update.
   * A glyph held by a lower or equal priority track is taken over; a higher one keeps it.
   */
  claim(glyphs: Iterable<number>, priority: number, onRelease?: () => void): LetterTrack;
  /** `path(evenodd, …)` that cuts these slices out of the stage; "" for none. */
  holes(glyphs: Iterable<number>): string;
  /** Releases copies, clipping and animations. */
  cancelAll(): void;
  /** Number of glyphs currently promoted. */
  readonly promoted: number;
}

interface TrackState {
  priority: number;
  glyphs: Set<number>;
  pending: number;
  sealed: boolean;
  released: boolean;
  onRelease?: () => void;
}

interface Entry {
  /** The moving ink: a clipped copy of the whole shaped run, at the ink box origin. */
  copy: HTMLElement;
  owner: TrackState;
  animations: Animation[];
  hot?: HTMLElement;
}

const keywords: Record<string, string> = {
  left: "0%",
  top: "0%",
  center: "50%",
  right: "100%",
  bottom: "100%",
};

/**
 * Resolves a transform-origin given for a glyph's box ("50% 100%", "center bottom",
 * "4px 12px") into the copy's coordinates, which span the whole ink box.
 */
export function glyphOrigin(
  stage: ElementalStage,
  glyph: number,
  origin = "50% 50%",
): { x: number; y: number } {
  const box = stage.glyphs[glyph];
  let [x = "50%", y = "50%"] = origin.trim().split(/\s+/);
  if (x === "top" || x === "bottom" || y === "left" || y === "right") [x, y] = [y, x];
  if (origin.trim() === "center") y = "50%";
  const resolve = (value: string, size: number) => {
    const token = keywords[value] ?? value;
    return token.endsWith("%") ? (parseFloat(token) / 100) * size : parseFloat(token) || 0;
  };
  return {
    x: fixed(box.x + stage.offset.x + resolve(x, box.width)),
    y: fixed(box.y + stage.offset.y + resolve(y, box.height)),
  };
}

/**
 * Pivots transform keyframes around a point by wrapping them in translations, which is
 * exactly what transform-origin does. The copy never carries a transform-origin style: at
 * rest, any transform-related property can change how an ancestor's filter rasterizes.
 */
export function pivot(keyframes: LetterKeyframe[], { x, y }: { x: number; y: number }) {
  return keyframes.map((keyframe) =>
    keyframe.transform === undefined
      ? keyframe
      : {
          ...keyframe,
          transform: `translate(${x}px, ${y}px) ${
            keyframe.transform === "none" ? "" : `${keyframe.transform} `
          }translate(${-x}px, ${-y}px)`,
        },
  );
}

const hotKeyframes = [
  { opacity: 0 },
  { opacity: 1, offset: 0.12 },
  { opacity: 0.65, offset: 0.3 },
  { opacity: 0 },
];

/**
 * Sparse letter renderer: idle uses the original shaped text; only moving slices get an
 * ink copy. A timeline promotes its glyph set once, reuses the copies across its beats and
 * releases them together. No RAF, timers or layout reads during playback: per-letter delays
 * and origins run through Web Animations, and all coordinates were measured beforehand.
 *
 * Each copy sits at the ink box origin, exactly where the original text paints, and moves
 * itself; its transform origin is resolved around its glyph. Nothing between the copy and
 * the ink box is offset, so a resting copy rasterizes identically at any page position and
 * pixel density.
 */
export function createLetterAnimator(
  surface: HTMLElement,
  layer: HTMLElement,
  stage: ElementalStage,
  { cap = letterCap, timeScale = 1 }: { cap?: number; timeScale?: number } = {},
): LetterAnimator {
  // One pixel grid per promotion cycle: every promoted slice and hole share it.
  let slices: LetterSlice[] | undefined;
  const entries = new Map<number, Entry>();
  const outer = pathOf([
    [fixed(stage.offset.x), fixed(stage.offset.y)],
    [fixed(stage.offset.x + stage.width), fixed(stage.offset.y)],
    [fixed(stage.offset.x + stage.width), fixed(stage.offset.y + stage.height)],
    [fixed(stage.offset.x), fixed(stage.offset.y + stage.height)],
  ]);
  const sliceOf = (glyph: number) => (slices ??= letterSlices(stage, pixelGrid(surface)))[glyph];
  const holes = (glyphs: Iterable<number>) => {
    const cut = [...glyphs].map((glyph) => pathOf(outline(sliceOf(glyph)))).join("");
    // Even-odd holes remove only the animated ink. The real text stays accessible.
    return cut ? `path(evenodd, "${outer}${cut}")` : "";
  };
  const mask = () => {
    surface.style.clipPath = holes(entries.keys());
    // Re-read the pixel grid for the next promotion; the title may have moved since.
    if (!entries.size) slices = undefined;
  };
  const stopMotion = (entry: Entry) => {
    for (const animation of entry.animations) {
      animation.onfinish = null;
      animation.cancel();
    }
    const stopped = entry.animations.length;
    entry.animations = [];
    return stopped;
  };
  const drop = (glyph: number, entry: Entry) => {
    stopMotion(entry);
    entry.copy.remove();
    entries.delete(glyph);
  };
  const release = (track: TrackState) => {
    if (track.released) return;
    track.released = true;
    track.onRelease?.();
    let removed = false;
    for (const glyph of track.glyphs) {
      const entry = entries.get(glyph);
      if (entry?.owner !== track) continue;
      drop(glyph, entry);
      removed = true;
    }
    track.glyphs.clear();
    if (removed) mask();
  };
  /** One style snapshot per promotion: every copy in the batch clones this template. */
  const template = () => {
    const copy = surface.cloneNode(true) as HTMLElement;
    copy.removeAttribute("style");
    copy.className = "elemental-title__letter-copy";
    // Copies have their own class names so the original semantic nodes stay unique.
    [...copy.children].forEach((node, index) => {
      const source = surface.children[index] as HTMLElement | undefined;
      const target = node as HTMLElement;
      if (source) {
        const style = getComputedStyle(source);
        target.style.opacity = style.opacity;
        target.style.backgroundPosition = style.backgroundPosition;
        // A CSS-animated layer (aura flicker, moving fill) keeps running in phase.
        const css = source.getAnimations?.().find((animation) => "animationName" in animation);
        if (typeof css?.currentTime === "number")
          target.style.animationDelay = `${-css.currentTime}ms`;
      }
      target.className = target.className.replace(/__([a-z]+)/g, "__letter-$1");
    });
    return copy;
  };
  const handle = (track: TrackState): LetterTrack => ({
    glyphs: track.glyphs,
    animate(request, offset = 0) {
      const entry = entries.get(request.glyph);
      if (!entry || entry.owner !== track || track.released) return;
      const delay = offset + (request.delay ?? 0);
      const keyframes = pivot(request.keyframes, glyphOrigin(stage, request.glyph, request.origin));
      const animations = [
        entry.copy.animate(keyframes, {
          duration: request.duration,
          delay,
          easing: request.easing ?? "ease-out",
        }),
      ];
      if (request.edge) {
        if (!entry.hot) {
          const edge = entry.copy
            .querySelector(".elemental-title__letter-edge")
            ?.cloneNode(true) as HTMLElement | undefined;
          if (edge) {
            edge.className = "elemental-title__letter-hot";
            edge.style.opacity = "0";
            entry.copy.append(edge);
            entry.hot = edge;
          }
        }
        if (entry.hot)
          animations.push(entry.hot.animate(hotKeyframes, { duration: request.duration, delay }));
      }
      for (const animation of animations) {
        animation.playbackRate = timeScale;
        entry.animations.push(animation);
        track.pending += 1;
        animation.onfinish = () => {
          entry.animations = entry.animations.filter((item) => item !== animation);
          track.pending -= 1;
          if (track.sealed && !track.pending) release(track);
        };
      }
    },
    seal() {
      track.sealed = true;
      if (!track.pending) release(track);
    },
    release() {
      release(track);
    },
  });
  return {
    claim(glyphs, priority, onRelease) {
      const track: TrackState = {
        priority,
        glyphs: new Set(),
        pending: 0,
        sealed: false,
        released: false,
        onRelease,
      };
      const fresh = new Set<number>();
      for (const glyph of glyphs) {
        if (track.glyphs.has(glyph) || fresh.has(glyph)) continue;
        if (!stage.glyphs[glyph] || typeof surface.animate !== "function") continue;
        const entry = entries.get(glyph);
        if (entry) {
          if (entry.owner.priority > priority) continue;
          // Each letter has one owner: the previous track's motion on it stops here.
          const previous = entry.owner;
          previous.pending -= stopMotion(entry);
          previous.glyphs.delete(glyph);
          entry.owner = track;
          track.glyphs.add(glyph);
          if (previous.sealed && !previous.pending) release(previous);
        } else if (entries.size + fresh.size < cap) fresh.add(glyph);
      }
      if (fresh.size) {
        const base = template();
        for (const glyph of fresh) {
          const copy = base.cloneNode(true) as HTMLElement;
          const points = outline(sliceOf(glyph))
            .map(([x, y]) => `${x}px ${y}px`)
            .join(",");
          // Keep full-run inline shaping, line breaks, bidi, gradients and glow.
          Object.assign(copy.style, {
            left: "0px",
            top: "0px",
            width: `${stage.text.width}px`,
            height: `${stage.text.height}px`,
            clipPath: `polygon(${points})`,
          });
          copy.dataset.letter = String(glyph);
          layer.append(copy);
          entries.set(glyph, { copy, owner: track, animations: [] });
          track.glyphs.add(glyph);
        }
        mask();
      }
      return handle(track);
    },
    holes,
    cancelAll() {
      if (!entries.size) return;
      for (const [glyph, entry] of [...entries]) {
        if (!entry.owner.released) {
          entry.owner.released = true;
          entry.owner.onRelease?.();
        }
        drop(glyph, entry);
      }
      mask();
    },
    get promoted() {
      return entries.size;
    },
  };
}
