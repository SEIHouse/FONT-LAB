import type { ElementalGlyph, ElementalStage } from "./types";

/** A line of the name, left to right. */
export interface Line {
  glyphs: ElementalGlyph[];
  left: number;
  right: number;
}

/** Reading order breaks into a new line wherever a glyph sits clearly lower or higher. */
export function linesOf(stage: ElementalStage): Line[] {
  const lines: Line[] = [];
  for (const glyph of stage.glyphs) {
    const line = lines.at(-1);
    if (line && Math.abs(line.glyphs[0].center.y - glyph.center.y) < stage.em * 0.5)
      line.glyphs.push(glyph);
    else lines.push({ glyphs: [glyph], left: 0, right: 0 });
  }
  for (const line of lines) {
    line.glyphs.sort((a, b) => a.x - b.x);
    line.left = Math.min(...line.glyphs.map((glyph) => glyph.x));
    line.right = Math.max(...line.glyphs.map((glyph) => glyph.x + glyph.width));
  }
  return lines;
}
