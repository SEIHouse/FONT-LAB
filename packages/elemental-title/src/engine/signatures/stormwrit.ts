import { anchorPoint, levelOf, sceneAnchors } from "../anchors";
import { cubic, type Point } from "../geometry";
import { between } from "../random";
import { burst, dissolveStroke, sceneCue, star, stroke, traveler } from "../scene";
import { signaturePriority } from "../program";
import { timeline } from "../timeline";
import type { ElementalCue, ElementalScenePrimitive, ElementalSceneStroke } from "../types";
import { defineSignature } from "./signature";

/** Quill's gold: bright in dark mode, deeper in light mode. */
const quillGold = "light-dark(#a8740a, #ffcf5c)";

/**
 * Stormwrit, Quill's first signature: "Quill signs your name."
 *
 * - Arrival: a spark ignites just before the first letter, slightly below the baseline.
 * - Act: it travels beneath the name like a pen nib, leaving a thin line of crackling
 *   electric ink behind it. The ink runs behind descenders; letter edges catch the light
 *   as the nib passes.
 * - Mark: past the last letter the ink sweeps up and back into a curling flourish (a fox's
 *   tail, a signature's last stroke) and ends in a small spark pop.
 * - Exit: the ink crackles away into fine fragments, start to end, and fades.
 *
 * A name that wraps is signed line by line: the nib lifts at the end of each line and
 * sets down again at the start of the next, and the flourish follows the last line.
 */
export const stormwrit = defineSignature({
  id: "quill/stormwrit",
  name: "Stormwrit",
  familiar: "quill",
  element: "lightning",
  accent: quillGold,
  timeline(stage, { random }) {
    const anchors = sceneAnchors(stage);
    if (!anchors) return null;
    const { em, lines } = anchors;
    // The ink runs just below the baseline: clear of resting letters, through descenders.
    const inkY = (line: (typeof lines)[number]) => levelOf(line, "baseline", em) + em * 0.14;
    const arrival = 0;
    const act = 240;
    const lift = 90;
    const writing = 980;
    const width = em * 0.038;

    // Arrival: the spark that becomes the nib.
    const nib = anchorPoint(anchors, stage, { at: "start", dx: -0.3, dy: 0.18 });
    const spark = star(
      {
        at: arrival,
        center: nib,
        radius: em * 0.26,
        part: "front",
        duration: 420,
        accent: true,
        keyframes: [
          { offset: 0, scale: 0.15, opacity: 0, flare: 0 },
          { offset: 0.22, scale: 1.2, opacity: 1, flare: 0.95, rotate: 12 },
          { offset: 0.5, scale: 0.8, opacity: 1, flare: 0.5, rotate: 30 },
          { offset: 1, scale: 0.2, opacity: 0, flare: 0, rotate: 60 },
        ],
      },
      anchors,
    );

    // Act: one ink line per line of the name, shared out by length.
    const spans = lines.map((line, index) => {
      const from = index ? line.start - em * 0.12 : nib.x + em * 0.08;
      return { line, from, to: line.end + em * 0.06 };
    });
    const total = spans.reduce((sum, span) => sum + (span.to - span.from), 0) || 1;
    const available = writing - lift * (spans.length - 1);
    let clock = act;
    const inks: ElementalSceneStroke[] = [];
    const cues: ElementalCue[] = [];
    const heads: ElementalScenePrimitive[] = [];
    for (const [index, span] of spans.entries()) {
      const duration = Math.max(160, (available * (span.to - span.from)) / total);
      const y = inkY(span.line);
      const phase = between(random, 0, Math.PI * 2);
      const steps = Math.max(6, Math.ceil((span.to - span.from) / (em * 0.3)));
      const path: Point[] = Array.from({ length: steps + 1 }, (_, step) => {
        const share = step / steps;
        return {
          x: span.from + (span.to - span.from) * share,
          // A hand-drawn line: a slight wave, rising a touch toward the end.
          y: y + Math.sin(phase + share * 5.2) * em * 0.018 - share * em * 0.025,
        };
      });
      const ink = stroke(
        {
          at: clock,
          path,
          width,
          taper: [index ? 0.04 : 0.08, 0.02],
          roughness: 0.2,
          detail: 2,
          gaps: 0.5,
          on: duration,
          hold: 0,
          off: 0,
          ease: index ? "linear" : "in",
          glow: width * 3.4,
          flicker: true,
          accent: true,
        },
        anchors,
        random,
      );
      inks.push(ink);
      heads.push(
        traveler(
          ink,
          {
            radius: em * 0.07,
            sparks: Math.max(2, Math.round(((span.to - span.from) / em) * 0.7)),
            part: "back",
          },
          anchors,
          random,
        ),
      );
      cues.push({
        type: "edge-light",
        at: clock,
        beat: "act",
        x: span.from,
        y: y - em * 0.08,
        to: { x: span.to, y: y - em * 0.08 },
        radius: em * 1.05,
        strength: 0.85,
        duration,
      });
      clock += duration + lift;
    }
    clock -= lift;

    // Mark: the flourish, a tail that sweeps up past the last letter and curls back.
    const mark = clock;
    const last = lines.at(-1)!;
    const end = last.end;
    const base = levelOf(last, "baseline", em);
    const start = inks.at(-1)!.spine.at(-1)!;
    const at = (dx: number, dy: number) => ({ x: end + dx * em, y: base + dy * em });
    const tail = [
      ...cubic(start, at(0.5, 0.17), at(0.7, -0.5), at(0.34, -0.74), 10),
      ...cubic(at(0.34, -0.74), at(0.06, -0.9), at(-0.12, -0.46), at(0.18, -0.36), 10).slice(1),
    ];
    const flourish = stroke(
      {
        at: mark,
        path: tail,
        width: width * 1.12,
        taper: [0.02, 0.5],
        roughness: 0.12,
        detail: 2,
        gaps: 0.3,
        // It sweeps up in front, then tucks the curl behind the last letter.
        front: [[0.08, 0.52]],
        on: 400,
        hold: 0,
        off: 0,
        ease: "out",
        glow: width * 3.4,
        flicker: true,
        accent: true,
      },
      anchors,
      random,
    );
    inks.push(flourish);
    heads.push(
      traveler(flourish, { radius: em * 0.07, sparks: 3, part: "front" }, anchors, random),
    );
    const tip = flourish.spine.at(-1)!;
    const pop = mark + 400;
    const popStar = star(
      {
        at: pop - 40,
        center: tip,
        radius: em * 0.22,
        part: "front",
        duration: 360,
        accent: true,
        keyframes: [
          { offset: 0, scale: 0.2, opacity: 0, flare: 0 },
          { offset: 0.2, scale: 1.25, opacity: 1, flare: 1, rotate: 20 },
          { offset: 1, scale: 0.1, opacity: 0, flare: 0, rotate: 70 },
        ],
      },
      anchors,
    );
    cues.push({
      type: "edge-light",
      at: mark + 120,
      beat: "mark",
      x: end - em * 0.1,
      y: base - em * 0.5,
      radius: em * 1.05,
      strength: 0.8,
      duration: 460,
    });

    // Exit: the ink crackles away from start to end.
    const exit = pop + 120;
    const erase = 380;
    const length = inks.reduce((sum, ink) => sum + ink.on, 0) || 1;
    let wipe = exit;
    const dust: ElementalScenePrimitive[] = [];
    for (const ink of inks) {
      const share = (erase * ink.on) / length;
      ink.hold = wipe - (ink.at + ink.on);
      ink.off = Math.max(80, share);
      dust.push(
        dissolveStroke(ink, { at: wipe, duration: ink.off, density: 1.5 }, anchors, random),
      );
      wipe += share;
    }
    cues.push(
      sceneCue("arrival", arrival, [
        spark,
        burst({ at: arrival + 60, center: nib, count: 4, reach: em * 0.3 }, anchors, random),
      ]),
      sceneCue("act", act, [...inks.slice(0, -1), ...heads.slice(0, -1)]),
      sceneCue("mark", mark, [
        flourish,
        heads.at(-1)!,
        popStar,
        burst({ at: pop, center: tip, count: 5, reach: em * 0.34 }, anchors, random),
      ]),
      sceneCue("exit", exit, dust),
    );
    return timeline("signature", signaturePriority, cues, [
      { label: "arrival", at: arrival },
      { label: "act", at: act },
      { label: "mark", at: mark },
      { label: "exit", at: exit },
    ]);
  },
});
