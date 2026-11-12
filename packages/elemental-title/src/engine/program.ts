import type {
  ElementalMomentCadence,
  ElementalRange,
  ElementalTier,
  ElementalTierProgram,
  ElementalTierPrograms,
} from "./types";

export const tiers: readonly ElementalTier[] = ["common", "rare", "epic", "legendary"];

/** Priority of a signature scene: above every regular moment. */
export const signaturePriority = 100;

/** Seeded pick from a delay range; a fixed range consumes no random draw. */
export const pickDelay = (random: () => number, [min, max]: ElementalRange) =>
  min === max ? min : min + random() * (max - min);

function slower(higher: ElementalRange | null, lower: ElementalRange | null) {
  if (!lower) return false;
  return !higher || higher[0] > lower[0] || higher[1] > lower[1];
}

function cadenceViolations(
  name: string,
  higher: ElementalMomentCadence,
  lower: ElementalMomentCadence,
): string[] {
  const found: string[] = [];
  for (const mode of ["ambient", "engaged"] as const) {
    if (slower(higher[mode], lower[mode])) found.push(`${name} ${mode} cadence is slower`);
    if (lower.lead && (!higher.lead || slower(higher.lead[mode], lower.lead[mode])))
      found.push(`${name} ${mode} lead is slower`);
  }
  return found;
}

/**
 * Tiers never de-escalate: compared with the tier below, a tier has every moment it
 * schedules, cadences at least as fast and parameters at least as strong. Returns a
 * description of each violation (empty when the program holds).
 */
export function tierProgramViolations(program: ElementalTierPrograms): string[] {
  const found: string[] = [];
  for (const [index, tier] of tiers.entries()) {
    const current: ElementalTierProgram = program[tier];
    if (!index) continue;
    const below = tiers[index - 1];
    const lower: ElementalTierProgram = program[below];
    const prefix = `${tier} vs ${below}:`;
    for (const [moment, cadence] of Object.entries(lower.cadence)) {
      const higher = current.cadence[moment];
      if (!higher) found.push(`${prefix} drops ${moment}`);
      else found.push(...cadenceViolations(moment, higher, cadence).map((v) => `${prefix} ${v}`));
    }
    for (const [name, value] of Object.entries(lower.params)) {
      const higher = current.params[name];
      if (higher === undefined) {
        found.push(`${prefix} drops parameter ${name}`);
        continue;
      }
      const [lowMin, lowMax] = typeof value === "number" ? [value, value] : value;
      const [highMin, highMax] = typeof higher === "number" ? [higher, higher] : higher;
      if (highMin < lowMin || highMax < lowMax) found.push(`${prefix} ${name} is weaker`);
    }
  }
  return found;
}

/** The delay range for the next occurrence of a scheduled moment, or null. */
export function cadenceFor(
  cadence: ElementalMomentCadence | undefined,
  interactive: boolean,
  first: boolean,
): ElementalRange | null {
  if (!cadence) return null;
  const mode = interactive ? "engaged" : "ambient";
  const range = cadence[mode];
  if (!range) return null;
  return first ? (cadence.lead?.[mode] ?? range) : range;
}
