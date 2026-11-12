import type { Point, Rect, Run } from "./geometry";
import type { Random } from "./random";
import type { LetterAnimation } from "./letters";

/** Visual rarity after legacy aliases are resolved. */
export type ElementalTier = "common" | "rare" | "epic" | "legendary";

/** A measured glyph in stage coordinates, with the estimated ink edges of the letter. */
export interface ElementalGlyph extends Rect {
  /** The character the box was measured for. */
  character: string;
  /** Estimated top of the visible letter (cap height, x-height or full em box). */
  inkTop: number;
  /** Estimated bottom of the visible letter, including a descender when present. */
  inkBottom: number;
  center: Point;
}

/**
 * Everything an effect needs to compose a frame: the overlay size in CSS pixels,
 * the font size, where the real text sits and where its letters are.
 */
export interface ElementalStage {
  width: number;
  height: number;
  /** Font size of the title in CSS pixels; effect geometry scales with it. */
  em: number;
  /** Overlay position relative to the ink box (negative: it overscans the text). */
  offset: Point;
  /** The ink box in stage coordinates. */
  text: Rect;
  glyphs: ElementalGlyph[];
  /** Tangent of the font's slant: 0 for upright text, about 0.2 for italic or oblique. */
  slant?: number;
}

/** Which schedule a frame belongs to; each slot keeps its own latest frame alive. */
export type ElementalSlot = "still" | "strike" | "crackle" | "drip" | "flow" | "wave";

export interface ElementalBolt {
  /** 0 = main arc, 1 = branch, 2 = twig. Finer tiers draw thinner and dimmer. */
  tier: 0 | 1 | 2;
  opacity: number;
  /** The whole centerline; the soft glow follows it across any gaps. */
  spine: Point[];
  /** Visible plasma and core runs, split where a dark gap breaks the arc. */
  runs: Run[];
}

export interface ElementalShard {
  x: number;
  y: number;
  /** Where the fragment drifts to over its life, relative to its origin. */
  dx: number;
  dy: number;
  /** Fragment length in pixels; zero draws a dot. */
  length: number;
  angle: number;
  width: number;
}

export interface ElementalLight {
  x: number;
  y: number;
  radius: number;
  strength: number;
}

export interface ElementalFrame {
  key: number;
  slot: ElementalSlot;
  /** Lifetime of the flash in milliseconds; the frame then rests at `rest` opacity. */
  life: number;
  /** Opacity the frame settles at so a paused view still shows the element. */
  rest: number;
  bolts: ElementalBolt[];
  shards: ElementalShard[];
  lights: ElementalLight[];
  /**
   * A still frame that stays under the element's moments instead of giving way to the
   * first one (poison's resting edge). Only a newer still frame replaces it.
   */
  persist?: boolean;
  /** Another element's material, drawn by its own renderer instead of arcs. */
  material?: ElementalMaterial;
  /** Set once a newer frame of the same slot exists; the frame then fades out. */
  stale?: boolean;
}

/* ---------------------------------------------------------------------------------------
 * Materials: elements that are not arcs draw their frames with their own renderer. Each
 * material is plain data in stage pixels, keyed by `type`, so a frame stays deterministic.
 * ------------------------------------------------------------------------------------- */

/** A band of poison along a contour: a ribbon that is thicker where gravity pools it. */
export interface ElementalPoisonBand {
  /** Centreline. A closed band repeats its first point at the end. */
  spine: Point[];
  widths: number[];
  closed: boolean;
  /** Stretch of the spine, as shares of its length, carrying the resting highlight. */
  highlight: [number, number];
}

/** A bead that gathers under the band, lets go and falls. */
export interface ElementalPoisonBead {
  /** Where it hangs from the band. */
  x: number;
  y: number;
  /** Bulb radius in px at full size. */
  radius: number;
  /** Start, gathering and falling times in ms. */
  delay: number;
  gather: number;
  fall: number;
  /** Fall distance in px. */
  drop: number;
  /** Hangs at this share of full size and never falls (resting frames). */
  hang?: number;
}

/** One highlight gliding along a band, and at higher tiers a current riding inside it. */
export interface ElementalPoisonFlow {
  spine: Point[];
  delay: number;
  duration: number;
  /** Share of the spine the glint covers. */
  length: number;
  /** Peak opacity of the glint, 0–1. */
  gain: number;
  reverse: boolean;
  /** Strength of the current (short dashes drifting with the glint), 0 for none. */
  current: number;
  /** Stroke width of the glint in px. */
  width: number;
}

export interface ElementalPoisonMaterial {
  type: "poison";
  bands: ElementalPoisonBand[];
  beads: ElementalPoisonBead[];
  flows: ElementalPoisonFlow[];
}

/** One traveling crest per visual line; coordinates and timing also drive its letters. */
export interface ElementalWave {
  left: number;
  right: number;
  baseline: number;
  from: number;
  to: number;
  em: number;
  height: number;
  curl: number;
  wake: number;
  delay: number;
  duration: number;
}

export interface ElementalWaterMaterial {
  type: "water";
  waves: ElementalWave[];
  still: boolean;
}

export type ElementalMaterial = ElementalPoisonMaterial | ElementalWaterMaterial;

/* ---------------------------------------------------------------------------------------
 * Choreography: a moment (strike, crackle, shine, ripple or a signature) is a timeline
 * of cues at millisecond offsets. Timelines are plain data, built by a pure function of the
 * measured stage, the tier and a seeded random stream; the conductor plays them.
 * ------------------------------------------------------------------------------------- */

/** A named moment an element can play, e.g. "strike". */
export type ElementalMomentId = string;

/** A labelled point in a multi-beat scene, e.g. "arrival", "act", "mark". */
export interface ElementalBeat {
  label: string;
  at: number;
}

interface CueBase {
  /** Offset from the start of the timeline, in milliseconds at normal speed. */
  at: number;
  /** Beat this cue belongs to, for authoring and inspection. */
  beat?: string;
}

/** Draws an overlay frame (arcs, fragments, lights). */
export interface ElementalFrameCue extends CueBase {
  type: "frame";
  frame: ElementalFrame;
}

/**
 * Moves letters. Every animation carries its own per-letter `delay` and optional
 * `origin`; the whole glyph set of a timeline is promoted once and released together.
 */
export interface ElementalLettersCue extends CueBase {
  type: "letters";
  animations: LetterAnimation[];
}

/** A rim of light around the letter edges near a point, on the title's flash layer. */
export interface ElementalEdgeLightCue extends CueBase {
  type: "edge-light";
  /** Centre of the light in stage coordinates. */
  x: number;
  y: number;
  /**
   * A passing light: the centre travels to this point over the cue's duration and the
   * rim fades in, holds and fades out, so letter edges catch the light as it passes.
   * Without it the rim flashes at its peak and decays (a strike).
   */
  to?: Point;
  /** Radius of the lit area in CSS pixels. */
  radius: number;
  /** Peak opacity of the rim, 0–1. */
  strength: number;
  duration: number;
  /** Glyphs whose own motion already carries light (a jolt's hot edge); the rim skips them. */
  exclude?: number[];
}

/** One soft band of light eased across the letters, in the title's own color. */
export interface ElementalShineCue extends CueBase {
  type: "shine";
  duration: number;
  /** Band angle in degrees. */
  angle: number;
  /** Sweep right-to-left instead of left-to-right. */
  reverse: boolean;
  /** Multiplies the title's CSS shine strength (`--et-energy-opacity`) for the peak. */
  gain: number;
  /** Keyframe offset where the band reaches its peak. */
  rise: number;
  /** Keyframe offset of the second, softer key. */
  hold: number;
  /** Opacity of the second key relative to the peak. */
  fade: number;
}

/* ---------------------------------------------------------------------------------------
 * Scenes: authored vector primitives drawn on the overlays, behind the letters (hidden by
 * their ink like the arcs) or in front of them. Primitives are an open set: a discriminated
 * union plus a renderer map in `scene-player.ts`. Geometry is plain data in stage pixels,
 * composed by pure builders in `scene.ts`, so a scene is deterministic per seed.
 * ------------------------------------------------------------------------------------- */

/** Behind the letters (their ink hides it, like the arcs) or in front of them. */
export type ElementalScenePart = "back" | "front";

/** A fine fragment or spark: a short line (or a dot) that drifts and fades. */
export interface ElementalSceneSpark {
  x: number;
  y: number;
  /** Drift over its life, relative to its origin. */
  dx: number;
  dy: number;
  /** Length in px; 0 draws a dot. */
  length: number;
  angle: number;
  width: number;
  /** Start, ms after the primitive's own start. */
  delay: number;
  /** Lifetime in ms. */
  life: number;
}

/**
 * A tapered path that draws on and off. It can be rough like an arc, break into dark gaps
 * and cross between back and front along its length.
 */
export interface ElementalSceneStroke {
  type: "stroke";
  at: number;
  /** The whole centerline; the glow follows it across dark gaps. */
  spine: Point[];
  /** Visible runs with tapered widths, split by part. */
  runs: Record<ElementalScenePart, Run[]>;
  /** Stretches of the centerline for the glow, split by part. */
  spines: Record<ElementalScenePart, Point[][]>;
  /** Draw-on schedule: [share of `on` time, share of length drawn], from [0, 0] to [1, 1]. */
  progress: [number, number][];
  /** Draw-on, hold and draw-off times in ms. */
  on: number;
  hold: number;
  off: number;
  /** Draw-off: `erase` wipes from the start toward the end, `retract` pulls back into the start. */
  exit: "erase" | "retract";
  /** Width of the soft glow in px behind the stroke; 0 for none. */
  glow: number;
  /** Crackles (flickers) while it holds. */
  flicker?: boolean;
  /** Carries the signature's accent edge. */
  accent?: boolean;
}

/** A bright head that rides a path, shedding sparks. */
export interface ElementalSceneTraveler {
  type: "traveler";
  at: number;
  part: ElementalScenePart;
  /** Positions over its ride: [share of duration, x, y]. */
  path: [number, number, number][];
  duration: number;
  /** Head radius in px. */
  radius: number;
  sparks: ElementalSceneSpark[];
}

/** A group keyframe of a shape, applied around the shape's centre. */
export interface ElementalSceneShapeKey {
  offset: number;
  /** Uniform scale. */
  scale: number;
  /** Extra length of the vertical points (1 = as authored). */
  stretch?: number;
  /** Degrees. */
  rotate?: number;
  opacity: number;
  /** Strength of the soft flare around the shape, 0–1. */
  flare?: number;
}

/** A small authored shape (a four-point star) that ignites, stretches, snaps back and winks out. */
export interface ElementalSceneShape {
  type: "shape";
  at: number;
  part: ElementalScenePart;
  shape: "star4";
  center: Point;
  /** Point length in px (centre to tip). */
  radius: number;
  /** Half-width of the star's waist in px. */
  waist: number;
  duration: number;
  keyframes: ElementalSceneShapeKey[];
  accent?: boolean;
}

/** Fine fragments released along a stroke or around a shape as it crackles away. */
export interface ElementalSceneDissolve {
  type: "dissolve";
  at: number;
  part: ElementalScenePart;
  fragments: ElementalSceneSpark[];
}

export type ElementalScenePrimitive =
  | ElementalSceneStroke
  | ElementalSceneTraveler
  | ElementalSceneShape
  | ElementalSceneDissolve;

/**
 * Plays authored primitives on the overlays. Every scene cue of a timeline shares one
 * build; later beats become Web Animation delays on the same nodes.
 */
export interface ElementalSceneCue extends CueBase {
  type: "scene";
  primitives: ElementalScenePrimitive[];
}

export type ElementalCue =
  | ElementalFrameCue
  | ElementalLettersCue
  | ElementalEdgeLightCue
  | ElementalShineCue
  | ElementalSceneCue;

export interface ElementalTimeline {
  moment: ElementalMomentId;
  /** Higher priority interrupts lower on shared layers and letters (signature > strike > crackle). */
  priority: number;
  /** Sorted by `at`. */
  cues: ElementalCue[];
  beats: ElementalBeat[];
  /** The signature this timeline plays, for signature moments. */
  signature?: { id: string; name: string };
}

/* ---------------------------------------------------------------------------------------
 * Tier programs: each effect declares, as data, which moments it schedules per bond tier,
 * how often (ambient and engaged) and with what parameters. Tiers never de-escalate.
 * ------------------------------------------------------------------------------------- */

export type ElementalRange = readonly [number, number];

export interface ElementalMomentCadence {
  /** Delay range between occurrences while the title runs ambiently; null: only on request. */
  ambient: ElementalRange | null;
  /** Delay range while hovered, focused or bursting; null: only on request. */
  engaged: ElementalRange | null;
  /** Delay before the first occurrence after (re)starting. Defaults to the cadence. */
  lead?: { ambient: ElementalRange; engaged: ElementalRange };
}

/** Tier parameters. Every value is "higher is stronger"; ranges compare at both ends. */
export type ElementalTierParams = Readonly<Record<string, number | ElementalRange>>;

export interface ElementalTierProgram {
  /** Moments scheduled at this tier. Moments missing here still play on request. */
  cadence: Readonly<Record<ElementalMomentId, ElementalMomentCadence>>;
  params: ElementalTierParams;
}

export interface ElementalTierPrograms {
  common: ElementalTierProgram;
  rare: ElementalTierProgram;
  epic: ElementalTierProgram;
  legendary: ElementalTierProgram;
}

/** What a timeline builder knows about the moment it builds. */
export interface ElementalMomentContext {
  tier: ElementalTier;
  params: ElementalTierParams;
  /** The title is live: running ambiently, or hovered, focused or bursting. */
  engaged: boolean;
  /** Engagement comes from the host (hover, focus or burst) rather than ambient motion. */
  interactive: boolean;
  /** Requested by the host through `playMoment` or `strikeKey`. */
  explicit: boolean;
  /** Seeded stream for this moment's composition. */
  random: Random;
  /** Unique, increasing per title; overlay frames use it as their key. */
  key: number;
  /** Stable hash of the title text, for derived per-moment streams. */
  textSeed: number;
}

export interface ElementalStillContext {
  tier: ElementalTier;
  params: ElementalTierParams;
  random: Random;
  key: number;
}

/** Overlay room around the ink box, in em. */
export interface ElementalOverscan {
  x: number;
  top: number;
  bottom: number;
}

/**
 * One element of the title system, registered as data plus choreography. The title
 * mounts only the layers an effect declares and hands them to the conductor.
 */
export interface ElementalEffect {
  id: string;
  /** Layers the effect draws on. */
  layers: {
    /** Vector frames behind and in front of the letters. */
    overlay?: boolean;
    /** Movable letters (the sparse letter engine). */
    letters?: boolean;
    /** The rim flash layer for edge-light cues. */
    edgeLight?: boolean;
  };
  /**
   * Room the overlay leaves around the ink box, in em. Elements that fall or rise further
   * than the defaults (0.8em beside, 1.4em above, 0.65em below) ask for their own.
   */
  overscan?: ElementalOverscan;
  /** Moments the effect can play, with their interrupt priority. */
  moments: Readonly<Record<ElementalMomentId, { priority: number }>>;
  program: ElementalTierPrograms;
  /** Deterministic resting overlay frame, shown paused, before hover and under reduced motion. */
  still?(stage: ElementalStage, context: ElementalStillContext): ElementalFrame;
  /** Pure: stage + tier + seeded random → timeline. Null when there is nothing to play. */
  timeline(
    moment: ElementalMomentId,
    stage: ElementalStage,
    context: ElementalMomentContext,
  ): ElementalTimeline | null;
}
