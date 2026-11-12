import { primitiveEnd } from "./scene";
import type { ElementalBeat, ElementalCue, ElementalTimeline } from "./types";

/** A timeline as the host sees it through `onMoment`: cues and beats without geometry. */
export interface ElementalMomentInfo {
  /** Moment id, e.g. "strike". */
  id: string;
  priority: number;
  /** Requested by the host rather than scheduled. */
  explicit: boolean;
  /** Length of the moment in milliseconds at normal speed. */
  duration: number;
  beats: ElementalBeat[];
  cues: {
    type: ElementalCue["type"];
    at: number;
    beat?: string;
    /** Glyph indices a letters cue moves. */
    glyphs?: number[];
    /** Primitive types a scene cue draws, in order. */
    primitives?: string[];
  }[];
  /** The signature that played, for signature moments. */
  signature?: { id: string; name: string };
}

/** When a cue's own work ends, in milliseconds from the start of the timeline. */
export function cueEnd(cue: ElementalCue): number {
  switch (cue.type) {
    case "frame":
      return cue.at + cue.frame.life;
    case "letters":
      return (
        cue.at +
        cue.animations.reduce(
          (end, animation) => Math.max(end, (animation.delay ?? 0) + animation.duration),
          0,
        )
      );
    case "scene":
      return cue.primitives.reduce(
        (end, primitive) => Math.max(end, cue.at + primitiveEnd(primitive)),
        cue.at,
      );
    default:
      return cue.at + cue.duration;
  }
}

export const timelineDuration = (timeline: ElementalTimeline) =>
  timeline.cues.reduce((end, cue) => Math.max(end, cueEnd(cue)), 0);

/** Assembles a timeline with its cues in play order (stable for equal offsets). */
export function timeline(
  moment: string,
  priority: number,
  cues: ElementalCue[],
  beats: ElementalBeat[] = [],
): ElementalTimeline {
  return {
    moment,
    priority,
    cues: cues
      .map((cue, index) => ({ cue, index }))
      .sort((a, b) => a.cue.at - b.cue.at || a.index - b.index)
      .map(({ cue }) => cue),
    beats: [...beats].sort((a, b) => a.at - b.at),
  };
}

export function describeTimeline(value: ElementalTimeline, explicit: boolean): ElementalMomentInfo {
  return {
    id: value.moment,
    priority: value.priority,
    explicit,
    duration: Math.round(timelineDuration(value)),
    beats: value.beats.map((beat) => ({ ...beat })),
    cues: value.cues.map((cue) => ({
      type: cue.type,
      at: cue.at,
      ...(cue.beat ? { beat: cue.beat } : {}),
      ...(cue.type === "letters"
        ? { glyphs: [...new Set(cue.animations.map((animation) => animation.glyph))] }
        : {}),
      ...(cue.type === "scene"
        ? { primitives: cue.primitives.map((primitive) => primitive.type) }
        : {}),
    })),
    ...(value.signature ? { signature: { ...value.signature } } : {}),
  };
}
