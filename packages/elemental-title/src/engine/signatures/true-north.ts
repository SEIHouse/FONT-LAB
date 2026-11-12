import { levelOf, sceneAnchors } from "../anchors";
import { cubic } from "../geometry";
import { burst, sceneCue, star, stroke, traveler } from "../scene";
import { signaturePriority } from "../program";
import { timeline } from "../timeline";
import type { ElementalCue } from "../types";
import { defineSignature } from "./signature";

/** Quill's gold: bright in dark mode, deeper in light mode. */
const quillGold = "light-dark(#a8740a, #ffcf5c)";

/**
 * True North, Quill's compass star. Like every signature, it is a fancy underline with a
 * unique ending: the motion runs beneath the name, the mark sits beside it, and nothing
 * crosses above the letters.
 *
 * - Arrival: a tiny four-point lightning star ignites just past the end of the name.
 * - Act: its lower point stretches into a thin needle that sweeps beneath the whole name,
 *   right to left, like a compass needle swinging; letter edges catch its light.
 * - Mark: the needle snaps back into the star, which flares.
 * - Exit: it winks out with a few fragments.
 *
 * A name that wraps is swept beneath its last line, across the width of the whole block,
 * with the star after the last word.
 */
export const trueNorth = defineSignature({
  id: "quill/true-north",
  name: "True North",
  familiar: "quill",
  element: "lightning",
  accent: quillGold,
  timeline(stage, { random }) {
    const anchors = sceneAnchors(stage);
    if (!anchors) return null;
    const { em, lines, box } = anchors;
    const last = lines.at(-1)!;
    const base = levelOf(last, "baseline", em);
    const radius = em * 0.3;
    const north = { x: last.end + em * 0.42, y: levelOf(last, "middle", em) };
    const width = em * 0.044;

    const arrival = 0;
    const act = 300;
    const sweep = 860;
    const mark = act + sweep + 110;
    const snap = 190;
    const exit = mark + snap + 420;
    const end = exit + 420;
    const at = (time: number) => time / end;

    const compass = star(
      {
        at: arrival,
        center: north,
        radius,
        waist: em * 0.06,
        part: "front",
        duration: end,
        accent: true,
        keyframes: [
          { offset: 0, scale: 0.1, opacity: 0, flare: 0 },
          { offset: at(130), scale: 1.25, opacity: 1, flare: 1 },
          { offset: at(260), scale: 1, opacity: 1, flare: 0.45 },
          // The points stretch as the needle leaves them, then relax while it sweeps.
          { offset: at(act + 120), scale: 1, stretch: 1.8, opacity: 1, flare: 0.6 },
          { offset: at(act + sweep - 100), scale: 0.9, stretch: 1.15, opacity: 1, flare: 0.3 },
          // Snap back and flare.
          { offset: at(mark + snap), scale: 0.8, stretch: 0.85, opacity: 1, flare: 0.5 },
          { offset: at(mark + snap + 90), scale: 1.6, opacity: 1, flare: 1 },
          { offset: at(exit), scale: 1, opacity: 1, flare: 0.4 },
          { offset: 1, scale: 0, rotate: 45, opacity: 0, flare: 0 },
        ],
      },
      anchors,
    );

    // One needle leaves the star's lower point and sweeps beneath the name, clear of the
    // descenders in the middle and rising to the baseline at its far end.
    const tip = { x: north.x, y: north.y + radius * 0.9 };
    const far = { x: box.x - em * 0.3, y: base + em * 0.02 };
    const span = tip.x - far.x;
    const depth = base + em * 0.36;
    const path = cubic(
      tip,
      { x: tip.x - span * 0.2, y: depth },
      { x: far.x + span * 0.3, y: depth },
      far,
      Math.max(12, Math.ceil(span / (em * 0.3))),
    );
    const needle = stroke(
      {
        at: act,
        path,
        width,
        taper: [0.04, 0.3],
        roughness: 0.14,
        detail: 2,
        gaps: 0.5,
        on: sweep,
        hold: mark - (act + sweep),
        off: snap,
        exit: "retract",
        ease: "in-out",
        glow: width * 3.4,
        accent: true,
      },
      anchors,
      random,
    );
    const head = traveler(needle, { radius: em * 0.065, sparks: 4, part: "back" }, anchors, random);

    const cues: ElementalCue[] = [
      sceneCue("arrival", arrival, [compass]),
      sceneCue("act", act, [needle, head]),
      sceneCue("exit", exit + 300, [
        burst({ at: exit + 300, center: north, count: 5, reach: em * 0.34 }, anchors, random),
      ]),
      {
        // Letter feet catch the light as the needle passes beneath them.
        type: "edge-light",
        at: act + 60,
        beat: "act",
        x: last.end,
        y: base - em * 0.02,
        to: { x: box.x, y: base - em * 0.02 },
        radius: em * 1.05,
        strength: 0.8,
        duration: sweep - 120,
      },
      {
        type: "edge-light",
        at: mark + snap,
        beat: "mark",
        x: north.x - em * 0.35,
        y: north.y,
        radius: em * 1.2,
        strength: 0.9,
        duration: 440,
      },
    ];
    return timeline("signature", signaturePriority, cues, [
      { label: "arrival", at: arrival },
      { label: "act", at: act },
      { label: "mark", at: mark },
      { label: "exit", at: exit },
    ]);
  },
});
