"use client";

import { memo, useId, useMemo, type CSSProperties, type Ref } from "react";
import { polylinePath, ribbonPath } from "./geometry";
import type { ElementalBolt, ElementalFrame, ElementalStage } from "./types";
import { WaterMaterial } from "./WaterMaterial";
import { PoisonMaterial } from "./PoisonMaterial";

/** Main arc, branch and twig: each finer tier draws thinner and a little dimmer. */
const tierScale = [1, 0.62, 0.44] as const;
const tierOpacity = [1, 0.82, 0.66] as const;
/**
 * The letters are the front plane. Every frame draws behind them, and a soft shade over
 * each letter takes this share of the light from whatever passes behind it (an arc behind
 * a letter keeps 40%), so the element reads as a layer beneath the name rather than on it.
 * It changes alpha only, so it works on any surface, and it is uniform, so bond tiers keep
 * their order.
 */
export const depthShade = 0.6;
/** How far past a letter's ink the shade fades out, in em. */
const depthReach = 0.2;
/** Share of the shade's radius at full strength; a typical letter's ink edge falls near it. */
const depthPlateau = 0.55;

interface TierLayer {
  tier: number;
  spines: string;
  plasma: string;
  core: string;
}

function layersFor(bolts: ElementalBolt[], em: number): TierLayer[] {
  const coreFloor = Math.max(1.1, em * 0.03);
  const layers = new Map<number, TierLayer>();
  for (const bolt of bolts) {
    const layer = layers.get(bolt.tier) ?? { tier: bolt.tier, spines: "", plasma: "", core: "" };
    layer.spines += polylinePath(bolt.spine);
    for (const run of bolt.runs) {
      layer.core += ribbonPath(
        run.points,
        run.widths.map((width) => Math.max(coreFloor, width)),
      );
      layer.plasma += ribbonPath(
        run.points,
        run.widths.map((width) => Math.max(coreFloor * 2, width * 1.7 + 0.5)),
      );
    }
    layers.set(bolt.tier, layer);
  }
  return [...layers.values()].sort((a, b) => b.tier - a.tier);
}

const Frame = memo(function Frame({
  frame,
  em,
  glowId,
  hazeId,
  lightId,
}: {
  frame: ElementalFrame;
  em: number;
  glowId: string;
  hazeId: string;
  lightId: string;
}) {
  const layers = useMemo(() => layersFor(frame.bolts, em), [frame, em]);
  const style = { "--et-life": `${frame.life}ms`, "--et-rest": frame.rest } as CSSProperties;
  if (frame.material)
    return (
      <g
        className="et-frame"
        data-slot={frame.slot}
        data-material={frame.material.type}
        data-stale={frame.stale ? "true" : undefined}
        style={style}
      >
        {frame.material.type === "water" ? (
          <WaterMaterial material={frame.material} />
        ) : (
          <PoisonMaterial material={frame.material} />
        )}
      </g>
    );
  return (
    <g
      className="et-frame"
      data-slot={frame.slot}
      data-stale={frame.stale ? "true" : undefined}
      style={style}
    >
      <g className="et-haze" filter={`url(#${hazeId})`}>
        {layers.map((layer) => (
          <path
            key={layer.tier}
            d={layer.spines}
            strokeWidth={Math.max(6, em * 0.3 * tierScale[layer.tier])}
            opacity={tierOpacity[layer.tier]}
          />
        ))}
      </g>
      <g className="et-lights">
        {frame.lights.map((light, index) => (
          <circle
            key={index}
            cx={light.x}
            cy={light.y}
            r={light.radius}
            fill={`url(#${lightId})`}
            opacity={light.strength}
          />
        ))}
      </g>
      <g className="et-glow" filter={`url(#${glowId})`}>
        {layers.map((layer) => (
          <path
            key={layer.tier}
            d={layer.spines}
            strokeWidth={Math.max(2.4, em * 0.12 * tierScale[layer.tier])}
            opacity={tierOpacity[layer.tier]}
          />
        ))}
      </g>
      <g className="et-plasma">
        {layers.map((layer) => (
          <path key={layer.tier} d={layer.plasma} opacity={tierOpacity[layer.tier]} />
        ))}
      </g>
      <g className="et-core">
        {layers.map((layer) => (
          <path key={layer.tier} d={layer.core} opacity={tierOpacity[layer.tier]} />
        ))}
      </g>
      <g className="et-shards">
        {frame.shards.map((shard, index) => (
          <g
            key={index}
            className="et-shard"
            style={{ "--et-sx": `${shard.dx}px`, "--et-sy": `${shard.dy}px` } as CSSProperties}
          >
            <path
              d={`M${shard.x} ${shard.y}l${(Math.cos(shard.angle) * shard.length || 0.01).toFixed(2)} ${(Math.sin(shard.angle) * shard.length).toFixed(2)}`}
              strokeWidth={shard.width}
            />
          </g>
        ))}
      </g>
    </g>
  );
});

/**
 * A luminance mask over the stage: white everywhere, with a soft shade over each letter's
 * ink that fades out just past its edges. Shades that overlap merge in one group before
 * the group's opacity applies, so neighbouring letters never shade twice.
 */
const DepthMask = memo(function DepthMask({
  stage,
  id,
  fadeId,
}: {
  stage: ElementalStage;
  id: string;
  fadeId: string;
}) {
  const reach = stage.em * depthReach;
  const skew = stage.slant ? (Math.atan(stage.slant) * 180) / Math.PI : 0;
  return (
    <>
      <radialGradient id={fadeId}>
        <stop offset={depthPlateau} stopColor="black" />
        <stop offset="1" stopColor="black" stopOpacity="0" />
      </radialGradient>
      <mask
        id={id}
        data-mask="depth"
        maskUnits="userSpaceOnUse"
        x="0"
        y="0"
        width={stage.width}
        height={stage.height}
      >
        <rect width={stage.width} height={stage.height} fill="white" />
        <g className="et-depth" opacity={depthShade}>
          {stage.glyphs.map((glyph, index) => {
            const cx = glyph.x + glyph.width / 2;
            const cy = (glyph.inkTop + glyph.inkBottom) / 2;
            // Italic ink leans right as it rises; the shade leans with it about the baseline.
            const lean = skew
              ? `translate(0 ${glyph.inkBottom}) skewX(${-skew}) translate(0 ${-glyph.inkBottom})`
              : undefined;
            return (
              <ellipse
                key={index}
                cx={cx}
                cy={cy}
                rx={glyph.width / 2 + reach}
                ry={(glyph.inkBottom - glyph.inkTop) / 2 + reach}
                transform={lean}
                fill={`url(#${fadeId})`}
              />
            );
          })}
        </g>
      </mask>
    </>
  );
});

/**
 * Draws effect frames around the title in an SVG that overscans the ink box. Callers render
 * it behind the real text (`part="back"`), so the letters stay the front plane: opaque ink,
 * clipped to the exact glyph shapes by the text layer's own CSS, swallows whatever part of
 * an arc falls under a stroke, and a soft depth shade dims what shows between strokes.
 * Titles with signatures also render a `part="front"` overlay, which holds only signature
 * scenes (they run beneath the name and never cross it). Geometry arrives in CSS pixels,
 * so the picture stays crisp at any pixel density.
 */
export function ElementalOverlay({
  stage,
  frames,
  part,
  sceneRef,
}: {
  stage: ElementalStage;
  /** The element's frames; only the back overlay draws them. */
  frames?: readonly ElementalFrame[];
  part: "back" | "front";
  /** Receives the group where signature scenes draw, above this overlay's frames. */
  sceneRef?: Ref<SVGGElement>;
}) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const glowId = `et-glow-${id}`;
  const hazeId = `et-haze-${id}`;
  const lightId = `et-light-${id}`;
  const depthId = `et-depth-${id}`;
  const depthFadeId = `et-depth-fade-${id}`;
  return (
    <svg
      className="elemental-title__stage"
      data-part={part}
      width={stage.width}
      height={stage.height}
      viewBox={`0 0 ${stage.width} ${stage.height}`}
      style={{ left: stage.offset.x, top: stage.offset.y }}
      focusable="false"
    >
      <defs>
        <filter
          id={glowId}
          data-filter="glow"
          filterUnits="userSpaceOnUse"
          x="0"
          y="0"
          width={stage.width}
          height={stage.height}
        >
          <feGaussianBlur stdDeviation={Math.max(1, stage.em * 0.036)} />
        </filter>
        {part === "back" && (
          <>
            <filter
              id={hazeId}
              data-filter="haze"
              filterUnits="userSpaceOnUse"
              x="0"
              y="0"
              width={stage.width}
              height={stage.height}
            >
              <feGaussianBlur stdDeviation={Math.max(2.6, stage.em * 0.13)} />
            </filter>
            <radialGradient id={lightId}>
              <stop offset="0" className="et-light-core" />
              <stop offset="0.38" className="et-light-mid" />
              <stop offset="1" className="et-light-edge" />
            </radialGradient>
            <DepthMask stage={stage} id={depthId} fadeId={depthFadeId} />
          </>
        )}
      </defs>
      {part === "back" && (
        <g className="et-frames" mask={`url(#${depthId})`}>
          {frames?.map((frame) => (
            <Frame
              key={frame.key}
              frame={frame}
              em={stage.em}
              glowId={glowId}
              hazeId={hazeId}
              lightId={lightId}
            />
          ))}
        </g>
      )}
      {/* Scene primitives are added and removed here by the conductor, never by React. */}
      <g ref={sceneRef} className="et-scene" data-part={part} />
    </svg>
  );
}
