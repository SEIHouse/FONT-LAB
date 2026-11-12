import type { ElementalWave } from "./types";

const n = (value: number) => Number(value.toFixed(3));
const point = (x: number, y: number) => `${n(x)} ${n(y)}`;
const ease = (value: number) => {
  const t = Math.max(0, Math.min(1, value));
  return t * t * (3 - 2 * t);
};

/** Shared by the liquid and letter track: the crest gathers, spills, then relaxes. */
export function waterEnvelope(t: number) {
  return 0.76 + 0.24 * Math.sin(Math.PI * t);
}

/** An unbroken surface: Common ripples gently; Rare gathers into a steep swell. */
function unbrokenSurface(curl: number, t: number) {
  const phase = t * Math.PI * 2;
  const h = waterEnvelope(t) * (0.88 + 0.04 * Math.sin(phase));
  const crown = -0.12 + 0.08 * Math.sin(phase - 0.6);
  const front = curl === 0 ? 0.85 : 0.38;
  const slip = Math.sin(phase + 0.8) * 0.14;
  const tailY = 0.105 + 0.015 * Math.sin(phase);
  const top = `M-2.8 ${n(tailY)} C-2.05 .08 -1.35 ${n(-h * 0.38)} -.78 ${n(-h * 0.7)} C${point(crown - 0.35, -h)} ${point(crown - 0.18, -h)} ${point(crown, -h)} C${point(crown + front, -h)} ${point(front, -h * 0.2)} 1.12 .12`;
  const body = `${top} C.22 .24 -1.85 .18 -2.8 ${n(tailY)}Z`;
  const face = `M${point(crown, -h + 0.08)} C${point(crown + front * 0.8, -h + 0.05)} ${point(front - 0.05, -h * 0.15)} 1.12 .12 C.3 .2 -.56 .15 -1.1 .13 C-.35 .02 ${point(crown - 0.18, -h * 0.54)} ${point(crown, -h + 0.08)}Z`;
  const back = `${top} C.25 .17 -.7 .08 -1.15 ${n(-h * 0.32)} C-1.7 .08 -2.3 .12 -2.8 ${n(tailY)}Z`;
  const glints = `M${point(-2.32 + slip, 0.08)} Q-1.7 ${n(-h * 0.16)} ${point(-1.23 + slip, -h * 0.44)} M${point(-0.8 + slip, -h * 0.72)} Q${point(crown - 0.15, -h + 0.04)} ${point(crown + front * 0.3, -h + 0.06)} M.05 .12 Q.48 .1 .77 .13`;
  const caustics = `M-1.72 .1 Q-.91 ${n(-h * 0.45)} -.41 ${n(-h * 0.48)} M-.45 .13 Q.04 ${n(-h * 0.23)} .55 .12`;
  // Keep the material contract uniform; these parts are not drawn for an unbroken swell.
  return {
    body,
    back,
    face,
    glints,
    caustics,
    lip: glints,
    wake: "M0 0",
    wakeEdge: "M0 0",
    foam: "M0 0",
    spray: "M0 0",
  };
}

/**
 * Compatible Bézier poses in em. The shoulder, lip, return current and reflections
 * deform independently. Sampled once per wave, then interpolated natively by SVG.
 */
export function waterSurface(wave: Pick<ElementalWave, "curl" | "wake">, t: number) {
  if (wave.curl < 2) return unbrokenSurface(wave.curl, t);
  const phase = t * Math.PI * 2;
  const spill = ease((t - 0.18) / 0.36) * (1 - ease((t - 0.65) / 0.35));
  const h = waterEnvelope(t) * (0.88 + 0.04 * Math.sin(phase));
  const crown = -0.12 + 0.08 * Math.sin(phase - 0.6);
  const fold = Math.min(1.35, 1 + (wave.curl - 2) * 0.35);
  const tip = crown + 0.18 + fold * (0.12 + spill * 0.3);
  const tipY = -h + 0.08 + fold * (0.05 + spill * 0.34);
  const shoulder = -1.05 - 0.18 * Math.sin(phase + 0.5);
  const toe = 0.94 + spill * 0.18;
  const tailY = 0.105 + 0.015 * Math.sin(phase);
  const top = `M-3.2 ${n(tailY)} C-2.3 ${n(tailY - 0.025)} ${point(shoulder - 0.28, -0.05)} ${point(shoulder, -h * 0.36)} C${point(-0.58, -h * 0.78)} ${point(crown - 0.35, -h - 0.06)} ${point(crown, -h)} C${point(crown + 0.22, -h + 0.015)} ${point(tip + 0.12, tipY - 0.16)} ${point(tip, tipY)}`;
  const innerX = tip - 0.12 - spill * 0.1;
  const innerY = tipY - 0.12;
  const face = `M${point(crown - 0.23, -h + 0.1)} C${point(crown - 0.05, -h + 0.19)} ${point(innerX - 0.14, innerY - 0.11)} ${point(innerX, innerY)} C${point(tip - 0.17, tipY + 0.24)} ${point(0.28, 0.05)} ${point(toe, 0.13)} C0.28 0.2 -0.58 0.14 -1.38 0.13 C-0.55 0.03 -0.63 ${n(-h * 0.52)} ${point(crown - 0.23, -h + 0.1)}Z`;
  const body = `${top} C${point(tip - 0.09, tipY + 0.09)} ${point(innerX - 0.08, innerY + 0.04)} ${point(innerX, innerY)} C${point(crown - 0.17, -h + 0.16)} ${point(crown - 0.29, -h * 0.38)} -0.08 -0.12 C0.18 0.045 ${point(toe - 0.28, 0.045)} ${point(toe, 0.13)} C0.34 0.25 -0.65 0.205 -1.28 0.17 C-2.03 0.145 -2.72 0.15 -3.2 ${n(tailY)}Z`;
  const back = `${top} C${point(tip - 0.04, tipY - 0.12)} ${point(crown + 0.02, -h + 0.11)} ${point(crown - 0.18, -h + 0.13)} C${point(-0.75, -h * 0.52)} -1.16 0.12 -3.2 ${n(tailY)}Z`;
  const lip = `M${point(crown - 0.37, -h + 0.045)} C${point(crown - 0.04, -h - 0.12)} ${point(tip + 0.19, tipY - 0.23)} ${point(tip, tipY)} C${point(tip - 0.09, tipY + 0.09)} ${point(innerX - 0.08, innerY + 0.04)} ${point(innerX, innerY)} C${point(tip + 0.03, tipY - 0.11)} ${point(crown + 0.03, -h + 0.03)} ${point(crown - 0.37, -h + 0.045)}Z`;
  // Broken narrow reflections slide over the shoulder instead of tracing its outline.
  const slip = Math.sin(phase + 0.8) * 0.14;
  let glints = `M${point(-2.62 + slip, 0.095)} C-1.98 0.073 -1.6 0.018 ${point(-1.32 + slip, -h * 0.15)} M${point(-1.11 + slip, -h * 0.28)} C${point(-0.84 + slip, -h * 0.52)} ${point(crown - 0.4, -h * 0.89)} ${point(crown - 0.23, -h + 0.065)} M${point(crown + 0.02, -h + 0.06)} Q${point(tip + 0.05, tipY - 0.18)} ${point(tip - 0.01, tipY - 0.045)} M-0.65 0.125 Q-0.04 ${n(0.06 + spill * 0.06)} ${point(0.51 + slip, 0.14)}`;
  const caustics = `M-2.12 0.13 C-1.59 0.07 -1.14 ${n(-h * 0.14)} -0.91 ${n(-h * 0.32)} M-1.56 0.155 Q-0.94 ${n(-0.08 - spill * 0.08)} -0.55 -0.11 M${point(crown - 0.14, -h + 0.26)} Q${point(-0.38, -h * 0.31)} 0.22 0.11`;
  const wakeHeight = wave.wake > 1 ? h * 0.72 : 0.14 * (0.65 + 0.35 * Math.sin(phase - 0.8));
  // Legendary's second crest is part of the existing fourth path, including at 14px.
  // It breaks after the lead crest and gives the name a second buoyant lift.
  const wakeTip = -1.88 + spill * 0.1;
  const wake =
    wave.wake > 1
      ? `M-3.2 .11 C-2.85 .08 -2.65 ${n(-wakeHeight * 0.88)} -2.15 ${n(-wakeHeight)} C-1.93 ${n(-wakeHeight - 0.06)} ${point(wakeTip + 0.17, -wakeHeight * 0.64)} ${point(wakeTip, -wakeHeight * 0.47)} C${point(wakeTip - 0.19, -wakeHeight * 0.36)} -2.12 ${n(-wakeHeight * 0.64)} -2.2 ${n(-wakeHeight * 0.6)} C-2.16 -.08 -1.73 .04 -1.32 .14 C-1.96 .22 -2.67 .17 -3.2 .11Z`
      : `M-3.05 .11 C-2.71 .08 -2.42 ${n(-wakeHeight)} -2.13 ${n(-wakeHeight * 0.8)} C-1.87 ${n(-wakeHeight * 0.58)} -1.92 .07 -1.41 .12 C-1.01 .15 -.77 .12 -.48 .15 C-1.6 .22 -2.37 .15 -3.05 .11Z`;
  const wakeEdge =
    wave.wake > 1
      ? `M-2.88 .035 C-2.62 ${n(-wakeHeight * 0.5)} -2.45 ${n(-wakeHeight * 0.88)} -2.15 ${n(-wakeHeight + 0.04)} M-2.08 ${n(-wakeHeight + 0.035)} Q${point(wakeTip + 0.14, -wakeHeight * 0.82)} ${point(wakeTip, -wakeHeight * 0.5)}`
      : `M-2.76 .08 Q-2.31 ${n(-wakeHeight * 1.13)} -2.1 ${n(-wakeHeight * 0.72)} M-1.94 .09 Q-1.54 .18 -1.12 .145`;
  if (wave.wake > 1) glints += ` ${wakeEdge}`;
  const foam = `M${point(crown - 0.25, -h + 0.025)} Q${point(crown - 0.08, -h - 0.04)} ${point(crown + 0.02, -h + 0.025)} M${point(tip - 0.06, tipY - 0.17)} Q${point(tip + 0.06, tipY - 0.08)} ${point(tip, tipY)} M-1.77 .12 Q-1.52 .16 -1.39 .135`;
  const spray = Array.from({ length: wave.wake > 1 ? 3 : 2 }, (_, index) => {
    const flight = Math.max(0, Math.min(1, (t - 0.28 - index * 0.035) / 0.46));
    const radius = Math.sin(Math.PI * flight) * (0.018 - index * 0.003);
    const x = 0.18 + flight * (0.63 + index * 0.2);
    const y = -0.88 - Math.sin(Math.PI * flight) * (0.2 + index * 0.055) + flight * 0.46;
    return `M${point(x - radius, y)} a${n(radius)} ${n(radius * 1.7)} 0 1 0 ${n(radius * 2)} 0 a${n(radius)} ${n(radius * 1.7)} 0 1 0 ${n(-radius * 2)} 0`;
  }).join(" ");
  return { body, back, face, lip, glints, caustics, wake, wakeEdge, foam, spray };
}

export type WaterSurface = ReturnType<typeof waterSurface>;
const poseCache = new Map<string, readonly Readonly<WaterSurface>[]>();
/** Bounded geometry budget, independent of font size or name length. */
export function waterPoses(wave: Pick<ElementalWave, "curl" | "wake">) {
  const key = `${wave.curl}:${wave.wake}`;
  let poses = poseCache.get(key);
  if (!poses) {
    poses = Object.freeze(
      Array.from({ length: 17 }, (_, index) => Object.freeze(waterSurface(wave, index / 16))),
    );
    // Four standard tiers share these immutable shapes across names and replays.
    // Bound the cache as well when a host supplies custom material parameters.
    if (poseCache.size >= 8) poseCache.delete(poseCache.keys().next().value!);
    poseCache.set(key, poses);
  }
  return poses;
}
