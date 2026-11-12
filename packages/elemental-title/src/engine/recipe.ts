import { resolveElementalEffect } from "./effects";
import { resolveSignatures, type ElementalSignature } from "./signatures";
import type { ElementalEffect, ElementalTier } from "./types";

/** An element in the registry, e.g. "lightning". */
export type ElementId = string;

/**
 * What a title plays: the familiar's elements, its bond tier, and the official
 * signatures the user owns, has enabled and can play here. The type allows several
 * elements so custom familiars can combine them later, but only single-element recipes
 * render in this phase: a recipe with zero or several elements resolves to no effect.
 */
export interface ElementalRecipe {
  elements: ElementId[];
  tier: ElementalTier;
  /** Eligible signature ids, in the order given (the tier and element fit). */
  signatures: string[];
}

/** Legacy `subtle`/`active` intensities map onto the rarity ladder. */
export function resolveTier(intensity: string): ElementalTier {
  switch (intensity) {
    case "common":
    case "rare":
    case "epic":
    case "legendary":
      return intensity;
    case "subtle":
      return "rare";
    default:
      return "epic";
  }
}

function titleOf(element: string, intensity: string) {
  const elements = element === "none" ? [] : [element];
  const tier = resolveTier(intensity);
  const single = elements.length === 1 ? elements[0] : undefined;
  return { elements, tier, single, engine: !!single && !!resolveElementalEffect(single) };
}

/** Resolves today's props into a recipe. `none` means no element. */
export function resolveRecipe(
  element: string,
  intensity: string,
  signatures?: readonly string[],
): ElementalRecipe {
  const { elements, tier, single, engine } = titleOf(element, intensity);
  const { eligible } = resolveSignatures(signatures, { element: single, tier, engine });
  return { elements, tier, signatures: eligible.map((signature) => signature.id) };
}

/** Why each ignored signature id cannot play with these props (for development warnings). */
export function ignoredSignatures(
  element: string,
  intensity: string,
  signatures?: readonly string[],
): { id: string; reason: string }[] {
  const { tier, single, engine } = titleOf(element, intensity);
  return resolveSignatures(signatures, { element: single, tier, engine }).ignored;
}

/** The effect a recipe renders with, or undefined (none, legacy CSS-only, or a combination). */
export function resolveRecipeEffect(recipe: ElementalRecipe): ElementalEffect | undefined {
  return recipe.elements.length === 1 ? resolveElementalEffect(recipe.elements[0]) : undefined;
}

/** The recipe's signature definitions, in order. */
export function resolveRecipeSignatures(recipe: ElementalRecipe): ElementalSignature[] {
  return resolveSignatures(recipe.signatures, {
    element: recipe.elements.length === 1 ? recipe.elements[0] : undefined,
    tier: recipe.tier,
    engine: !!resolveRecipeEffect(recipe),
  }).eligible;
}
