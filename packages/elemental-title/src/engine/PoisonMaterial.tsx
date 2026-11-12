"use client";

import { memo, useMemo, type CSSProperties } from "react";
import { measurePolyline, polylinePath, type Point } from "./geometry";
import { tangentsOf } from "./poison";
import type { ElementalPoisonBand, ElementalPoisonBead, ElementalPoisonMaterial } from "./types";

const round = (value: number) => Math.round(value * 100) / 100;

/**
 * A filled ribbon along a spine, optionally shifted toward the outside (positive) or the
 * letters (negative). A closed spine wraps its tangents around the seam, so the band has
 * no kink where it starts; its outline is two loops, which the nonzero fill turns into a ring.
 */
export function bandPath(
  spine: Point[],
  widths: number[],
  closed: boolean,
  shift: (index: number) => number = () => 0,
): string {
  if (spine.length < 2) return "";
  const tangents = tangentsOf(spine, closed);
  const outer: Point[] = [];
  const inner: Point[] = [];
  spine.forEach((point, index) => {
    // Outward normal: the loop runs left along the top, so outward is (-ty, tx).
    const normal = { x: -tangents[index].y, y: tangents[index].x };
    const centre = shift(index);
    const half = widths[index] / 2;
    outer.push({
      x: point.x + normal.x * (centre + half),
      y: point.y + normal.y * (centre + half),
    });
    inner.push({
      x: point.x + normal.x * (centre - half),
      y: point.y + normal.y * (centre - half),
    });
  });
  // Where the poison thins to nothing the band breaks, rather than leaving a hairline where
  // its two edges meet.
  const drawn = widths.map((width) => width > hairline);
  if (closed && drawn.every(Boolean)) {
    let path = `M${round(outer[0].x)} ${round(outer[0].y)}`;
    for (let index = 1; index < outer.length; index += 1)
      path += `L${round(outer[index].x)} ${round(outer[index].y)}`;
    path += `ZM${round(inner.at(-1)!.x)} ${round(inner.at(-1)!.y)}`;
    for (let index = inner.length - 2; index >= 0; index -= 1)
      path += `L${round(inner[index].x)} ${round(inner[index].y)}`;
    return `${path}Z`;
  }
  // A closed band starts its runs at a break, so no run is cut in two at the seam.
  const count = closed ? spine.length - 1 : spine.length;
  const start = closed ? drawn.indexOf(false) : 0;
  const order = Array.from(
    { length: count + (closed ? 1 : 0) },
    (_, step) => (start + step) % count,
  );
  let path = "";
  let run: number[] = [];
  const flush = () => {
    if (run.length >= 2) {
      path += `M${round(outer[run[0]].x)} ${round(outer[run[0]].y)}`;
      for (const index of run.slice(1))
        path += `L${round(outer[index].x)} ${round(outer[index].y)}`;
      for (const index of run.slice().reverse())
        path += `L${round(inner[index].x)} ${round(inner[index].y)}`;
      path += "Z";
    }
    run = [];
  };
  for (const index of order) {
    if (drawn[index]) run.push(index);
    else {
      // Each run ends on the break point, so it tapers into it.
      if (run.length) run.push(index);
      flush();
      run = [index];
    }
  }
  flush();
  return path;
}

/** Narrower than this, a band is not drawn at all. */
const hairline = 0.3;

/** The stretch of a band between two shares of its length, with widths tapering to points. */
function highlightOf(band: ElementalPoisonBand): { spine: Point[]; widths: number[] } {
  const measure = measurePolyline(band.spine);
  const [from, to] = band.highlight;
  const spine: Point[] = [];
  const widths: number[] = [];
  band.spine.forEach((point, index) => {
    const share = measure.total ? measure.cumulative[index] / measure.total : 0;
    if (share < from || share > to) return;
    const t = (share - from) / (to - from);
    spine.push(point);
    widths.push(band.widths[index] * 0.42 * Math.sin(Math.PI * t));
  });
  return { spine, widths };
}

function Band({ band }: { band: ElementalPoisonBand }) {
  const paths = useMemo(() => {
    const { spine, widths, closed } = band;
    const highlight = highlightOf(band);
    return {
      body: bandPath(spine, widths, closed),
      // The deep poison pools along the outer, lower edge; the rim catches light on the
      // side facing the letters.
      deep: bandPath(
        spine,
        widths.map((width) => width * 0.5),
        closed,
        (index) => widths[index] * 0.22,
      ),
      rim: bandPath(
        spine,
        widths.map((width) => width * 0.22),
        closed,
        (index) => -widths[index] * 0.32,
      ),
      glint: bandPath(
        highlight.spine,
        highlight.widths,
        false,
        (index) => -highlight.widths[index] * 0.25,
      ),
    };
  }, [band]);
  return (
    <g className="pt-band">
      <path className="pt-body" d={paths.body} />
      <path className="pt-deep" d={paths.deep} />
      <path className="pt-rim" d={paths.rim} />
      <path className="pt-glint" d={paths.glint} />
    </g>
  );
}

/** A pendant drop hanging from (0, 0): a neck from the band into a round bulb. */
function Drop({ radius: r }: { radius: number }) {
  const h = r * 1.25;
  const neck = r * 0.42;
  const top = -r * 0.3;
  return (
    <>
      <path
        className="pt-drop"
        d={`M${round(-neck)} ${round(top)}C${round(-neck)} ${round(h * 0.35)} ${round(-r)} ${round(h - r * 0.7)} ${round(-r)} ${round(h)}A${round(r)} ${round(r)} 0 0 0 ${round(r)} ${round(h)}C${round(r)} ${round(h - r * 0.7)} ${round(neck)} ${round(h * 0.35)} ${round(neck)} ${round(top)}Z`}
      />
      <path
        className="pt-drop-deep"
        d={`M${round(-r * 0.86)} ${round(h + r * 0.2)}A${round(r)} ${round(r)} 0 0 0 ${round(r * 0.86)} ${round(h + r * 0.2)}A${round(r * 1.05)} ${round(r * 0.7)} 0 0 1 ${round(-r * 0.86)} ${round(h + r * 0.2)}Z`}
      />
      <ellipse
        className="pt-drop-glint"
        cx={round(-r * 0.36)}
        cy={round(h - r * 0.32)}
        rx={round(r * 0.24)}
        ry={round(r * 0.34)}
        transform={`rotate(-24 ${round(-r * 0.36)} ${round(h - r * 0.32)})`}
      />
    </>
  );
}

function Bead({ bead }: { bead: ElementalPoisonBead }) {
  const position = `translate(${round(bead.x)} ${round(bead.y)})`;
  if (bead.hang !== undefined)
    return (
      <g className="pt-bead" data-resting="" transform={position}>
        <g transform={`scale(${round(bead.hang)})`}>
          <Drop radius={bead.radius} />
        </g>
      </g>
    );
  const release = bead.delay + bead.gather;
  const style = {
    "--pt-delay": `${bead.delay}ms`,
    "--pt-gather": `${bead.gather}ms`,
    "--pt-release": `${release}ms`,
    "--pt-fall": `${bead.fall}ms`,
    "--pt-retract": `${bead.fall * (380 / 520)}ms`,
    "--pt-drop": `${round(bead.drop)}px`,
  } as CSSProperties;
  return (
    <g className="pt-bead" transform={position} style={style}>
      {/* What stays behind on the band when the bead lets go, then draws back in. */}
      <ellipse
        className="pt-remnant"
        cx="0"
        cy="0"
        rx={round(bead.radius * 0.5)}
        ry={round(bead.radius * 0.36)}
      />
      <g className="pt-fall">
        <g className="pt-grow">
          <Drop radius={bead.radius} />
        </g>
      </g>
    </g>
  );
}

/**
 * Draws a poison frame: the resting edge and hanging beads (still), a gathering and falling
 * bead or pour (drip), or a highlight gliding along the edge with its current (flow).
 * Motion is CSS on transform, opacity and dash offset; nothing is measured while it plays.
 */
export const PoisonMaterial = memo(function PoisonMaterial({
  material,
}: {
  material: ElementalPoisonMaterial;
}) {
  return (
    <>
      {material.bands.length > 0 && (
        <g className="pt-bands">
          {material.bands.map((band, index) => (
            <Band key={index} band={band} />
          ))}
        </g>
      )}
      {material.flows.map((flow, index) => {
        const d = polylinePath(flow.spine);
        const length = round(flow.length * 100);
        const style = {
          "--pt-delay": `${flow.delay}ms`,
          "--pt-duration": `${flow.duration}ms`,
          "--pt-gain": flow.gain,
          "--pt-from": flow.reverse ? "-100" : `${length}`,
          "--pt-to": flow.reverse ? `${length}` : "-100",
          strokeDasharray: `${length} 200`,
          strokeWidth: flow.width,
        } as CSSProperties;
        return (
          <g key={index} className="pt-flows">
            {flow.current > 0 && (
              <path
                className="pt-current"
                d={d}
                pathLength={100}
                style={
                  {
                    "--pt-delay": `${flow.delay}ms`,
                    "--pt-duration": `${flow.duration}ms`,
                    "--pt-gain": round(flow.current * 0.55),
                    "--pt-shift": flow.reverse ? "21" : "-21",
                    strokeWidth: round(flow.width * 0.55),
                  } as CSSProperties
                }
              />
            )}
            <path className="pt-flow" d={d} pathLength={100} style={style} />
          </g>
        );
      })}
      {material.beads.map((bead, index) => (
        <Bead key={index} bead={bead} />
      ))}
    </>
  );
});
