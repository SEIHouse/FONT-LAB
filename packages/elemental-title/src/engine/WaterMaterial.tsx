"use client";

import { memo, useId, useLayoutEffect, useMemo, useRef, type CSSProperties } from "react";
import type { ElementalWaterMaterial, ElementalWave } from "./types";
import { waterPoses, waterSurface, type WaterSurface } from "./water-surface";

/** Transparent water sheets and moving reflections, behind the name's depth mask. */
function Wave({ wave, still }: { wave: ElementalWave; still: boolean }) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const lineRef = useRef<SVGGElement>(null);
  const { left, right, baseline, em, height, curl, wake } = wave;
  const detailed = em >= 24;
  const cssPaths = typeof CSS !== "undefined" && CSS.supports?.("d", 'path("M0 0L1 1")');
  const poses = useMemo(() => {
    if (still) return [waterSurface({ curl, wake }, 0.42)];
    const samples = waterPoses({ curl, wake });
    // Subpixel surface detail is expensive to animate in a crowd of small names.
    return detailed ? samples : samples.filter((_, index) => index % 2 === 0);
  }, [curl, wake, still, detailed]);
  useLayoutEffect(() => {
    if (still) return;
    if (cssPaths) {
      // Use the same browser clock as the letters. In Chromium, dynamically mounted
      // SMIL paths can freeze at their first sample inside a CSS-animated group.
      const animations = Array.from(
        lineRef.current?.querySelectorAll<SVGPathElement>("path[data-water-shape]") ?? [],
        (path) => {
          const part = path.dataset.waterShape as keyof WaterSurface;
          return path.animate(
            poses.map((pose) => ({ d: `path("${pose[part]}")` })),
            {
              duration: wave.duration,
              delay: wave.delay,
              easing: "linear",
              fill: "forwards",
            },
          );
        },
      );
      return () => animations.forEach((animation) => animation.cancel());
    }
    // WebKit without CSS path interpolation uses native SVG instead. Start this
    // moment explicitly because the parent SVG's clock may already be minutes old.
    const animations = lineRef.current?.querySelectorAll<SVGAnimateElement>("animate");
    animations?.forEach((animation) => animation.beginElementAt?.(wave.delay / 1000));
    return () => animations?.forEach((animation) => animation.endElement?.());
  }, [cssPaths, poses, still, wave.delay, wave.duration]);
  const morph = (part: keyof WaterSurface) =>
    !still &&
    !cssPaths && (
      <animate
        attributeName="d"
        values={poses.map((pose) => pose[part]).join(";")}
        begin="indefinite"
        dur={`${wave.duration}ms`}
        fill="freeze"
      />
    );
  const style = {
    "--wv-from": `${wave.from}px`,
    "--wv-to": `${wave.to}px`,
    "--wv-rest": `${(left + right) / 2 + em * 0.45}px`,
    "--wv-duration": `${wave.duration}ms`,
    "--wv-delay": `${wave.delay}ms`,
  } as CSSProperties;
  return (
    <g ref={lineRef} className="wv-line" data-still={still ? "" : undefined} style={style}>
      <defs>
        {detailed && (
          <filter
            id={`${id}-surface`}
            x="-3.3"
            y="-1.3"
            width="4.7"
            height="1.7"
            filterUnits="userSpaceOnUse"
            colorInterpolationFilters="sRGB"
          >
            <feTurbulence
              type="fractalNoise"
              baseFrequency="2.4 5.5"
              numOctaves="2"
              seed="7"
              result="ripples"
            />
            <feGaussianBlur in="SourceAlpha" stdDeviation="0.025" result="thickness" />
            <feComposite in="ripples" in2="thickness" operator="in" result="height" />
            <feSpecularLighting
              in="height"
              surfaceScale="0.1"
              specularConstant="0.65"
              specularExponent="24"
              lightingColor="#dfffff"
              result="reflection"
            >
              <feDistantLight azimuth="235" elevation="55" />
            </feSpecularLighting>
            <feComposite in="reflection" in2="SourceAlpha" operator="in" result="clipped" />
            <feMerge>
              <feMergeNode in="SourceGraphic" />
              <feMergeNode in="clipped" />
            </feMerge>
          </filter>
        )}
        <linearGradient id={`${id}-body`} x1="0.15" y1="0" x2="0.4" y2="1">
          <stop offset="0" stopColor="var(--et-water-rim)" stopOpacity="0.76" />
          <stop offset="0.22" stopColor="var(--et-water-body)" stopOpacity="0.42" />
          <stop offset="0.5" stopColor="var(--et-water-mid)" stopOpacity="0.12" />
          <stop offset="0.8" stopColor="var(--et-water-deep)" stopOpacity="0.58" />
          <stop offset="1" stopColor="var(--et-water-body)" stopOpacity="0.06" />
        </linearGradient>
        <linearGradient id={`${id}-face`} x1="0" y1="0" x2="0.8" y2="0.9">
          <stop stopColor="var(--et-water-deep)" stopOpacity="0.08" />
          <stop offset="0.55" stopColor="var(--et-water-deep)" stopOpacity="0.58" />
          <stop offset="0.8" stopColor="var(--et-water-mid)" stopOpacity="0.18" />
          <stop offset="1" stopColor="var(--et-water-body)" stopOpacity="0" />
        </linearGradient>
        <linearGradient id={`${id}-glass`} x1="0" y1="0" x2="0.3" y2="1">
          <stop stopColor="var(--et-water-rim)" stopOpacity="0.88" />
          <stop offset="0.3" stopColor="var(--et-water-body)" stopOpacity="0.16" />
          <stop offset="0.6" stopColor="var(--et-water-rim)" stopOpacity="0.36" />
          <stop offset="1" stopColor="var(--et-water-body)" stopOpacity="0" />
        </linearGradient>
        <linearGradient id={`${id}-edge`}>
          <stop offset="0" stopColor="white" stopOpacity="0" />
          <stop offset="0.08" stopColor="white" />
          <stop offset="0.92" stopColor="white" />
          <stop offset="1" stopColor="white" stopOpacity="0" />
        </linearGradient>
        <mask
          id={`${id}-mask`}
          maskUnits="userSpaceOnUse"
          x={left}
          y={baseline - em * 1.8}
          width={right - left}
          height={em * 2.3}
        >
          <rect
            x={left}
            y={baseline - em * 1.8}
            width={right - left}
            height={em * 2.3}
            fill={`url(#${id}-edge)`}
          />
        </mask>
      </defs>
      <g mask={`url(#${id}-mask)`}>
        <g transform={`translate(0 ${baseline})`}>
          <g className="wv-travel">
            <g transform={`scale(${em} ${em * height})`}>
              <g filter={detailed ? `url(#${id}-surface)` : undefined}>
                <path
                  className="wv-body"
                  data-water-shape="body"
                  d={poses[0].body}
                  fill={`url(#${id}-body)`}
                >
                  {morph("body")}
                </path>
                {detailed && (
                  <path
                    className="wv-back"
                    data-water-shape="back"
                    d={poses[0].back}
                    fill={`url(#${id}-glass)`}
                  >
                    {morph("back")}
                  </path>
                )}
                <path
                  className="wv-fold"
                  data-water-shape="face"
                  d={poses[0].face}
                  fill={`url(#${id}-face)`}
                >
                  {morph("face")}
                </path>
              </g>
              {detailed && (
                <path className="wv-caustic" data-water-shape="caustics" d={poses[0].caustics}>
                  {morph("caustics")}
                </path>
              )}
              {detailed && curl >= 2 && (
                <path
                  className="wv-lip"
                  data-water-shape="lip"
                  d={poses[0].lip}
                  fill={`url(#${id}-glass)`}
                >
                  {morph("lip")}
                </path>
              )}
              {wake > 0 && (
                <>
                  <path
                    className="wv-undertow"
                    data-water-shape="wake"
                    d={poses[0].wake}
                    fill={`url(#${id}-body)`}
                  >
                    {morph("wake")}
                  </path>
                  {detailed && wake === 1 && (
                    <path
                      className="wv-reflection wv-wake-edge"
                      data-water-shape="wakeEdge"
                      d={poses[0].wakeEdge}
                    >
                      {morph("wakeEdge")}
                    </path>
                  )}
                  {detailed && !still && (
                    <path className="wv-spray" data-water-shape="spray" d={poses[0].spray}>
                      {morph("spray")}
                    </path>
                  )}
                </>
              )}
              <path className="wv-reflection" data-water-shape="glints" d={poses[0].glints}>
                {morph("glints")}
              </path>
              {detailed && wake > 1 && (
                <path className="wv-foam" data-water-shape="foam" d={poses[0].foam}>
                  {morph("foam")}
                </path>
              )}
            </g>
          </g>
        </g>
      </g>
    </g>
  );
}

export const WaterMaterial = memo(function WaterMaterial({
  material,
}: {
  material: ElementalWaterMaterial;
}) {
  return (
    <>
      {material.waves.map((wave, index) => (
        <Wave key={index} wave={wave} still={material.still} />
      ))}
    </>
  );
});
