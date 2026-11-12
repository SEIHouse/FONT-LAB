import type { ElementalFrame } from "./types";

/** Keep material transport and the conductor's letter animations on the same clock. */
export function scaleFrame(frame: ElementalFrame, speed: number): ElementalFrame {
  if (speed === 1) return frame;
  const material = frame.material;
  return {
    ...frame,
    life: frame.life / speed,
    material:
      material?.type === "water"
        ? {
            ...material,
            waves: material.waves.map((wave) => ({
              ...wave,
              delay: wave.delay / speed,
              duration: wave.duration / speed,
            })),
          }
        : material?.type === "poison"
          ? {
              ...material,
              beads: material.beads.map((bead) => ({
                ...bead,
                delay: bead.delay / speed,
                gather: bead.gather / speed,
                fall: bead.fall / speed,
              })),
              flows: material.flows.map((flow) => ({
                ...flow,
                delay: flow.delay / speed,
                duration: flow.duration / speed,
              })),
            }
          : material,
  };
}

/**
 * The newest frame of a slot replaces the previous one, which fades out before it is dropped.
 * The first moment also retires the still frame, unless that frame persists under moments.
 */
export function pushFrame(frames: ElementalFrame[], frame: ElementalFrame): ElementalFrame[] {
  const next: ElementalFrame[] = [];
  for (const existing of frames) {
    const replaced =
      existing.slot === frame.slot || (existing.slot === "still" && !existing.persist);
    if (!replaced) next.push(existing);
    else if (!existing.stale) next.push({ ...existing, stale: true });
  }
  next.push(frame);
  return next;
}
