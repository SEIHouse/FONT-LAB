"use client";

import { memo, type Ref } from "react";
import type { ElementalStage } from "./types";

/**
 * Measured, empty glyph shells mark where each letter rests. They cost no paint; the
 * animator adds moving ink copies beside them, at the ink box origin, only during a moment.
 */
export const LetterLayer = memo(function LetterLayer({
  stage,
  layerRef,
}: {
  stage: ElementalStage;
  layerRef: Ref<HTMLSpanElement>;
}) {
  return (
    <span ref={layerRef} className="elemental-title__letters" aria-hidden="true">
      {stage.glyphs.map((glyph, index) => (
        <span
          key={index}
          data-glyph={index}
          className="elemental-title__letter"
          style={{
            left: `${glyph.x + stage.offset.x}px`,
            top: `${glyph.y + stage.offset.y}px`,
            width: `${glyph.width}px`,
            height: `${glyph.height}px`,
          }}
        />
      ))}
    </span>
  );
});
