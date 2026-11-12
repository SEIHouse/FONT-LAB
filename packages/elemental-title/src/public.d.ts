import type {
  ForwardRefExoticComponent,
  HTMLAttributes,
  JSX,
  Ref,
  RefAttributes,
} from "react";

export type ElementalTitleElement = "span" | "p" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
export type ElementalTitleEffect =
  | "none"
  | "fire"
  | "lightning"
  | "water"
  | "poison"
  | "frost"
  | "celestial"
  | "void";
export type ElementalTitleIntensity =
  | "subtle"
  | "active"
  | "common"
  | "rare"
  | "epic"
  | "legendary";
export type ElementalTitleMotion = "ambient" | "hover" | "burst";
export type ElementalTitleSize = "inherit" | "sm" | "md" | "lg" | "xl";
export type ElementalTitleShadow = "none" | "soft" | "outlined";

/**
 * Official familiar signatures: exclusive animations around the name, `"<familiar>/<name>"`.
 * The host decides which ids a user may pass (earned, purchased and enabled).
 */
export type ElementalTitleSignature = "quill/stormwrit" | "quill/true-north";

/** A host request to play a named moment, e.g. `{ id: "strike", key: n }`. */
export interface ElementalTitleMomentRequest {
  /** Moment id. Lightning plays "strike", "crackle" and "shine"; Water plays "wave"; Poison plays "drip", "flow" and "shine"; any title with signatures plays "signature". */
  id: string;
  /** Change this value to play the moment again. */
  key: number;
  /**
   * With `id: "signature"`: play this one of the title's `signatures` (a shop or Familiar
   * screen preview) instead of the next one in its rotation. Leave it out to play the next
   * one, for example when the app marks an action tied to the familiar.
   */
  signature?: ElementalTitleSignature;
}

/** A moment that started playing: its cues and beat labels, without geometry. */
export interface ElementalTitleMoment {
  /** Moment id, e.g. "strike". */
  id: string;
  priority: number;
  /** Requested by the host rather than scheduled. */
  explicit: boolean;
  /** Length of the moment in milliseconds at normal speed. */
  duration: number;
  beats: { label: string; at: number }[];
  cues: {
    type: "frame" | "letters" | "edge-light" | "shine" | "scene";
    at: number;
    beat?: string;
    glyphs?: number[];
    primitives?: string[];
  }[];
  /** The signature that played, for `"signature"` moments. */
  signature?: { id: ElementalTitleSignature; name: string };
}

export interface ElementalTitleProps extends Omit<
  HTMLAttributes<HTMLElement>,
  "children" | "dangerouslySetInnerHTML"
> {
  /** Plain text, escaped by React. No markup or decorative children. */
  children: string;
  /** Match the host document outline; inline text by default. */
  as?: ElementalTitleElement;
  /** Opt in to elemental lettering; existing consumers stay plain by default. */
  element?: ElementalTitleEffect;
  /** Optional CSS text color, independent of the selected elemental effect. */
  color?: string;
  /** Familiar bond tier controls strength independently of rank color. Legacy aliases remain supported. */
  intensity?: ElementalTitleIntensity;
  /** Burst plays once on pointer entry, press, or focus, including a containing control. */
  motion?: ElementalTitleMotion;
  /** Inherit preserves the host profile's typography. Other sizes scale responsively. */
  size?: ElementalTitleSize;
  /** Letter edge treatment. Lightning, water and poison default to the rank keyline (`outlined`), others to `soft`. */
  shadow?: ElementalTitleShadow;
  /** Change this value to request a strike. Alias of `playMoment={{ id: "strike", key }}`. */
  strikeKey?: number;
  /** Official signatures this user owns and has enabled. */
  signatures?: readonly ElementalTitleSignature[];
  /** Plays the named moment whenever `key` changes after mount. */
  playMoment?: ElementalTitleMomentRequest;
  /** Called when a moment starts, with its cues and beat labels (review readouts, sound sync). */
  onMoment?: (moment: ElementalTitleMoment) => void;
  /** Review aid only: scales the speed of every moment's timers and animations together. Defaults to 1. */
  timeScale?: number;
  ref?: Ref<HTMLElement>;
}

/** Readable semantic text with optional, non-interactive elemental decoration. */
export declare const ElementalTitle: ForwardRefExoticComponent<
  ElementalTitleProps & RefAttributes<HTMLElement>
>;
