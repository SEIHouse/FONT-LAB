/** Deterministic random numbers so a still frame is reproducible and testable. */
export type Random = () => number;

/** FNV-1a: stable 32-bit hash for seeding a title from its text. */
export function hashString(text: string): number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

/** mulberry32: small, fast and good enough for decoration. Returns values in [0, 1). */
export function createRandom(seed: number): Random {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export const between = (random: Random, min: number, max: number) => min + random() * (max - min);

export const chance = (random: Random, probability: number) => random() < probability;

export function pick<T>(random: Random, items: readonly T[]): T {
  return items[Math.min(items.length - 1, Math.floor(random() * items.length))];
}

/** Integer in [min, max]. */
export const integer = (random: Random, min: number, max: number) =>
  Math.floor(between(random, min, max + 1));
