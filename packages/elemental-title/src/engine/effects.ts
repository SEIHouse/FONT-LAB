import { lightning } from "./lightning";
import { testRipple } from "./test-ripple";
import type { ElementalEffect } from "./types";
import { water } from "./water";
import { poison } from "./poison";

/**
 * Elements rendered by the elemental engine. Elements missing here keep the older
 * CSS-only decoration until they are rebuilt on the same contract.
 */
const effects: Record<string, ElementalEffect | undefined> = {
  lightning,
  water,
  poison,
  // Test only: not a public element value. Delete with ./test-ripple.ts.
  [testRipple.id]: testRipple,
};

export function resolveElementalEffect(element: string): ElementalEffect | undefined {
  return Object.hasOwn(effects, element) ? effects[element] : undefined;
}

/** Every registered effect, for contract tests such as the tier invariant. */
export function registeredElementalEffects(): ElementalEffect[] {
  return Object.values(effects).filter((effect): effect is ElementalEffect => !!effect);
}
