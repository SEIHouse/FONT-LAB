import * as official from "./official";
import { meetsTier, type ElementalSignature } from "./signature";
import type { ElementalTier } from "../types";

export { defaultSignatureCadence, defineSignature, meetsTier } from "./signature";
export type { ElementalSignature, ElementalSignatureCadence } from "./signature";

/** Official signature ids, as declared by their files. */
export type OfficialSignatureId = (typeof official)[keyof typeof official]["id"];

/**
 * The closed registry: every official signature, by id. There is no registration API;
 * users can build custom familiars but can never get or create a signature.
 */
const signatures: ReadonlyMap<string, ElementalSignature> = new Map(
  Object.values(official).map((signature) => [signature.id, Object.freeze(signature)]),
);

/** Official familiars and their signatures, in registry order. */
export const familiarSignatures: Readonly<Record<string, readonly ElementalSignature[]>> =
  Object.freeze(
    [...signatures.values()].reduce<Record<string, ElementalSignature[]>>((map, signature) => {
      (map[signature.familiar] ??= []).push(signature);
      return map;
    }, {}),
  );

export function officialSignature(id: string): ElementalSignature | undefined {
  return signatures.get(id);
}

export function officialSignatures(): ElementalSignature[] {
  return [...signatures.values()];
}

export interface SignatureTitle {
  /** The title's single element, or undefined for none or a combination. */
  element: string | undefined;
  tier: ElementalTier;
  /** The element runs on the elemental engine. */
  engine: boolean;
}

export interface ResolvedSignatures {
  /** Signatures that can play on this title, in the order given, without duplicates. */
  eligible: ElementalSignature[];
  /** Why each other id is ignored (for development warnings). */
  ignored: { id: string; reason: string }[];
}

/**
 * Filters a title's enabled signatures to those that can play: official, of the title's
 * element (which runs on the engine), at or above their minimum bond tier.
 */
export function resolveSignatures(
  ids: readonly string[] | undefined,
  title: SignatureTitle,
  lookup: (id: string) => ElementalSignature | undefined = officialSignature,
): ResolvedSignatures {
  const eligible: ElementalSignature[] = [];
  const ignored: { id: string; reason: string }[] = [];
  for (const id of new Set(ids ?? [])) {
    const signature = lookup(id);
    let reason: string | undefined;
    if (!signature) reason = "it is not an official signature";
    else if (title.element !== signature.element)
      reason = `it needs the ${signature.element} element`;
    else if (!title.engine) reason = `${signature.element} does not run on the elemental engine`;
    else if (!meetsTier(title.tier, signature.minimumTier))
      reason = `it needs a ${signature.minimumTier} bond (this title is ${title.tier})`;
    if (reason) ignored.push({ id, reason });
    else eligible.push(signature!);
  }
  return { eligible, ignored };
}
