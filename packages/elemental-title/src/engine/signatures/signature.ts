import { tiers } from "../program";
import type {
  ElementalMomentContext,
  ElementalStage,
  ElementalTier,
  ElementalTimeline,
} from "../types";

/**
 * When a signature plays. Signatures never play on their own: they answer a touch on the
 * name (a mouse or pen pointer entering it, a finger on it, keyboard focus), or the host
 * asks with `playMoment` (a shop preview, or an app action tied to the familiar), which
 * ignores cadence.
 */
export interface ElementalSignatureCadence {
  /**
   * Least time (ms) from the end of one play to a touch starting the next. 0: every touch
   * replays it once the last play has finished. Null: only when the host asks.
   */
  cooldown: number | null;
}

export const defaultSignatureCadence: ElementalSignatureCadence = {
  cooldown: 0,
};

/**
 * An official familiar's signature: an exclusive extra animation around the name, made of
 * its element's material. It suggests the familiar; it never illustrates it.
 */
export interface ElementalSignature {
  /** Stable official id, `"<familiar>/<signature>"`. */
  id: string;
  /** Display name, e.g. "Stormwrit". */
  name: string;
  /** The official familiar that owns it. */
  familiar: string;
  /** Plays only on titles of this element, and only while it runs on the elemental engine. */
  element: string;
  /** Lowest bond tier that plays it. */
  minimumTier: ElementalTier;
  cadence: ElementalSignatureCadence;
  /** Optional accent edge color for its primitives, e.g. `light-dark(#8f6200, #ffd166)`. */
  accent?: string;
  /** Pure: stage + seeded context → a timeline with labelled beats. Null when nothing fits. */
  timeline(stage: ElementalStage, context: ElementalMomentContext): ElementalTimeline | null;
}

type SignatureInput<Id extends string> = Omit<
  ElementalSignature,
  "id" | "minimumTier" | "cadence"
> & {
  id: Id;
  minimumTier?: ElementalTier;
  cadence?: Partial<ElementalSignatureCadence>;
};

/** Declares a signature with the defaults: legendary bond and the default cadence. */
export function defineSignature<Id extends string>(
  input: SignatureInput<Id>,
): ElementalSignature & { id: Id } {
  return {
    ...input,
    minimumTier: input.minimumTier ?? "legendary",
    cadence: { ...defaultSignatureCadence, ...input.cadence },
  };
}

/** Whether a title's tier meets a minimum tier. */
export const meetsTier = (tier: ElementalTier, minimum: ElementalTier) =>
  tiers.indexOf(tier) >= tiers.indexOf(minimum);
