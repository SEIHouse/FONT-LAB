import type { ElementalGlyph, ElementalOverscan, ElementalStage } from "./types";

/** Room the overlay leaves around the ink box, in em, unless an element asks for its own. */
export const defaultOverscan: ElementalOverscan = { x: 0.8, top: 1.4, bottom: 0.65 };

const upright = /[\p{Lu}\p{N}bdfhklt]/u;
const lowercase = /\p{Ll}/u;
const descending = /[gjpqyçşţ]/u;
const european = /[\p{Script=Latin}\p{Script=Greek}\p{Script=Cyrillic}\p{P}\p{S}]/u;

/** Share of a text run's content box that hangs below the baseline in typical fonts. */
export const descentShare = 0.21;

/** Tangent of the slant of italic or oblique text; 0 when upright. */
function slantOf(fontStyle: string): number {
  const angle = /oblique\s+(-?[\d.]+)deg/.exec(fontStyle);
  if (angle) return Math.tan((parseFloat(angle[1]) * Math.PI) / 180);
  return /italic|oblique/.test(fontStyle) ? Math.tan((12 * Math.PI) / 180) : 0;
}

/** Estimated ink edges of a glyph from its character class; a letter's box is not its shape. */
function inkEdges(character: string, baseline: number, em: number) {
  if (!european.test(character)) return { top: baseline - em * 0.76, bottom: baseline + em * 0.14 };
  const top = upright.test(character) ? 0.7 : lowercase.test(character) ? 0.47 : 0.6;
  return {
    top: baseline - em * top,
    bottom: baseline + em * (descending.test(character) ? 0.21 : 0.02),
  };
}

/** Non-space graphemes with UTF-16 offsets (combining marks and ZWJ emoji stay whole). */
export function glyphOffsets(text: string): { character: string; start: number; end: number }[] {
  return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text))
    .filter(({ segment }) => !/^\s+$/u.test(segment))
    .map(({ segment, index }) => ({
      character: segment,
      start: index,
      end: index + segment.length,
    }));
}

/**
 * Measures the ink box and its graphemes into overlay coordinates. Effects may
 * sample these for bounded geometry; letters always need the complete run.
 * Returns null while the text has no size (hidden, detached, or not yet laid out).
 */
export function measureStage(
  ink: HTMLElement,
  text: Text,
  value: string,
  limit = Infinity,
  overscan: ElementalOverscan = defaultOverscan,
): ElementalStage | null {
  const box = ink.getBoundingClientRect();
  if (!box.width || !box.height) return null;
  const style = getComputedStyle(ink);
  const em = parseFloat(style.fontSize) || 16;
  const padX = em * overscan.x;
  const padTop = em * overscan.top;
  const padBottom = em * overscan.bottom;
  const offsets = glyphOffsets(value);
  const step = Math.max(1, offsets.length / limit);
  const range = document.createRange();
  const glyphs: ElementalGlyph[] = [];
  for (let index = 0; index < Math.min(limit, offsets.length); index += 1) {
    const position = offsets[Math.floor(index * step)];
    range.setStart(text, position.start);
    range.setEnd(text, position.end);
    const rect = range.getBoundingClientRect();
    if (!rect.width || !rect.height) continue;
    const x = rect.left - box.left + padX;
    const y = rect.top - box.top + padTop;
    const baseline = y + rect.height * (1 - descentShare);
    const edges = inkEdges(position.character, baseline, em);
    glyphs.push({
      character: position.character,
      x,
      y,
      width: rect.width,
      height: rect.height,
      inkTop: Math.max(y, edges.top),
      inkBottom: Math.min(y + rect.height, edges.bottom),
      center: { x: x + rect.width / 2, y: y + rect.height / 2 },
    });
  }
  return {
    width: box.width + padX * 2,
    height: box.height + padTop + padBottom,
    em,
    offset: { x: -padX, y: -padTop },
    text: { x: padX, y: padTop, width: box.width, height: box.height },
    glyphs,
    slant: slantOf(style.fontStyle ?? ""),
  };
}

/** Whether two measurements would compose the same picture. */
export function sameStage(a: ElementalStage | null, b: ElementalStage): boolean {
  if (!a) return false;
  if (
    a.width !== b.width ||
    a.height !== b.height ||
    a.em !== b.em ||
    (a.slant ?? 0) !== (b.slant ?? 0) ||
    a.glyphs.length !== b.glyphs.length
  )
    return false;
  return a.glyphs.every((glyph, index) => {
    const other = b.glyphs[index];
    return (
      glyph.character === other.character &&
      glyph.x === other.x &&
      glyph.y === other.y &&
      glyph.width === other.width &&
      glyph.height === other.height
    );
  });
}
