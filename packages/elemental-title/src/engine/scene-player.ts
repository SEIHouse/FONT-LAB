import { polylinePath, ribbonPath } from "./geometry";
import type {
  ElementalSceneCue,
  ElementalSceneDissolve,
  ElementalScenePart,
  ElementalScenePrimitive,
  ElementalSceneShape,
  ElementalSceneSpark,
  ElementalSceneStroke,
  ElementalSceneTraveler,
  ElementalStage,
} from "./types";

const svg = "http://www.w3.org/2000/svg";

/** What a primitive renderer can use. */
export interface SceneRenderContext {
  stage: ElementalStage;
  /** Constrained device: no blur glow, half the fragments. */
  lite: boolean;
  /** Draw accent edges (the signature has an accent and the host did not turn it off). */
  accent: boolean;
  /** Creates an SVG node in the back or front host for this scene. */
  node<K extends keyof SVGElementTagNameMap>(
    part: ElementalScenePart | SVGElement,
    tag: K,
    attributes?: Record<string, string | number>,
  ): SVGElementTagNameMap[K];
  /** Starts a Web Animation that the scene owns (scaled, tracked, cancelled on stop). */
  animate(target: Element, keyframes: Keyframe[], options: KeyframeAnimationOptions): Animation;
  /** Id of an overlay filter (`glow`, or `haze` behind the letters), when present. */
  filter(part: ElementalScenePart, name: "glow" | "haze"): string | undefined;
  /** A unique id for masks and gradients. */
  id(prefix: string): string;
  /** The overlays themselves, for primitives that act on the element's own drawing. */
  overlays: Record<ElementalScenePart, SVGSVGElement | null>;
}

/** Draws one primitive, `delay` ms after the scene starts. */
export type SceneRenderer<P extends ElementalScenePrimitive> = (
  primitive: P,
  delay: number,
  context: SceneRenderContext,
) => void;

const fixed = (value: number) => Number(value.toFixed(2));

/** Fragments and sparks: a short line (or dot) that drifts and fades. Halved on lite. */
function sparks(
  list: ElementalSceneSpark[],
  part: ElementalScenePart,
  delay: number,
  context: SceneRenderContext,
) {
  list.forEach((item, index) => {
    if (context.lite && index % 2) return;
    const line = context.node(part, "path", {
      class: "et-scene-spark",
      d: `M${fixed(item.x)} ${fixed(item.y)}l${fixed(Math.cos(item.angle) * item.length) || 0.01} ${fixed(Math.sin(item.angle) * item.length)}`,
      "stroke-width": fixed(item.width),
    });
    context.animate(
      line,
      [
        // Hidden until its own start (the backwards fill), then it flicks on and drifts away.
        { opacity: 0, transform: "translate(0px, 0px)" },
        { opacity: 1, offset: 0.04 },
        { opacity: 0.8, offset: 0.6 },
        { opacity: 0, transform: `translate(${fixed(item.dx)}px, ${fixed(item.dy)}px)` },
      ],
      { duration: item.life, delay: delay + item.delay, easing: "ease-out", fill: "both" },
    );
  });
}

const renderStroke: SceneRenderer<ElementalSceneStroke> = (line, delay, context) => {
  const widest = Math.max(1, ...line.runs.back.flatMap((run) => run.widths), 1);
  const reveal = Math.max(widest * 2.2 + line.glow * 1.6, context.stage.em * 0.4);
  const coreFloor = Math.max(1.1, context.stage.em * 0.03);
  for (const part of ["back", "front"] as const) {
    const runs = line.runs[part];
    if (!runs.length) continue;
    // A dash along the whole centerline reveals the stroke as it draws, in both parts at once.
    const maskId = context.id("et-scene-mask");
    const mask = context.node(part, "mask", {
      id: maskId,
      maskUnits: "userSpaceOnUse",
      x: 0,
      y: 0,
      width: context.stage.width,
      height: context.stage.height,
    });
    const dash = context.node(mask, "path", {
      d: polylinePath(line.spine),
      pathLength: 1,
      fill: "none",
      stroke: "#fff",
      "stroke-width": fixed(reveal),
      "stroke-linejoin": "round",
      "stroke-dasharray": "1 1",
      "stroke-dashoffset": 1,
    });
    context.animate(
      dash,
      line.progress.map(([t, s]) => ({ offset: t, strokeDashoffset: `${fixed(1 - s)}` })),
      { duration: line.on, delay: delay + line.at, fill: "both" },
    );
    if (line.off)
      context.animate(
        dash,
        [{ strokeDashoffset: "0" }, { strokeDashoffset: line.exit === "retract" ? "1" : "-1" }],
        {
          duration: line.off,
          delay: delay + line.at + line.on + line.hold,
          easing: line.exit === "retract" ? "cubic-bezier(0.5, 0, 0.9, 0.6)" : "ease-in",
          fill: "forwards",
        },
      );
    const group = context.node(part, "g", {
      class: "et-scene-stroke",
      "data-part": part,
      mask: `url(#${maskId})`,
    });
    const glow = context.filter(part, "glow");
    if (!context.lite && line.glow && glow)
      for (const points of line.spines[part])
        context.node(group, "path", {
          class: "et-scene-glow",
          d: polylinePath(points),
          "stroke-width": fixed(part === "front" ? line.glow * 0.5 : line.glow),
          filter: `url(#${glow})`,
        });
    if (context.accent && line.accent)
      context.node(group, "path", {
        class: "et-scene-accent",
        d: runs
          .map((run) =>
            ribbonPath(
              run.points,
              run.widths.map((width) => Math.max(coreFloor * 2, width * 1.7 + 0.5) + 1.1),
            ),
          )
          .join(""),
      });
    const body = context.node(group, "g", { class: "et-scene-body" });
    context.node(body, "path", {
      class: "et-scene-plasma",
      d: runs
        .map((run) =>
          ribbonPath(
            run.points,
            run.widths.map((width) => Math.max(coreFloor * 2, width * 1.7 + 0.5)),
          ),
        )
        .join(""),
    });
    context.node(body, "path", {
      class: "et-scene-core",
      d: runs
        .map((run) =>
          ribbonPath(
            run.points,
            run.widths.map((width) => Math.max(coreFloor, width)),
          ),
        )
        .join(""),
    });
    if (line.flicker && line.hold > 80)
      context.animate(
        body,
        [
          { opacity: 1 },
          { opacity: 0.62, offset: 0.18 },
          { opacity: 1, offset: 0.32 },
          { opacity: 0.8, offset: 0.58 },
          { opacity: 1, offset: 0.7 },
          { opacity: 0.7, offset: 0.86 },
          { opacity: 1 },
        ],
        { duration: Math.max(1, line.hold), delay: delay + line.at + line.on },
      );
    // While it draws off, what remains of the stroke cools and dims.
    if (line.off)
      context.animate(group, [{ opacity: 1 }, { opacity: 0.35 }], {
        duration: line.off,
        delay: delay + line.at + line.on + line.hold,
        easing: "ease-in",
        fill: "forwards",
      });
  }
};

const renderTraveler: SceneRenderer<ElementalSceneTraveler> = (item, delay, context) => {
  const head = context.node(item.part, "g", { class: "et-scene-head" });
  const glow = context.filter(item.part, "glow");
  if (!context.lite && glow)
    context.node(head, "circle", {
      class: "et-scene-head-glow",
      r: fixed(item.radius * 2.6),
      filter: `url(#${glow})`,
    });
  context.node(head, "circle", { class: "et-scene-head-plasma", r: fixed(item.radius * 1.5) });
  context.node(head, "circle", { class: "et-scene-head-core", r: fixed(item.radius) });
  const last = item.path.length - 1;
  context.animate(
    head,
    item.path.map(([offset, x, y], index) => ({
      offset,
      transform: `translate(${fixed(x)}px, ${fixed(y)}px)`,
      opacity: index === 0 || index === last ? 0 : 1,
    })),
    { duration: item.duration, delay: delay + item.at, fill: "both" },
  );
  sparks(item.sparks, item.part, delay + item.at, context);
};

/** A four-point star as one path: long vertical points, shorter horizontal ones. */
function starPath(center: { x: number; y: number }, radius: number, waist: number) {
  const { x, y } = center;
  const side = radius * 0.72;
  const points = [
    [x, y - radius],
    [x + waist, y - waist],
    [x + side, y],
    [x + waist, y + waist],
    [x, y + radius],
    [x - waist, y + waist],
    [x - side, y],
    [x - waist, y - waist],
  ];
  return `M${points.map(([px, py]) => `${fixed(px)} ${fixed(py)}`).join("L")}Z`;
}

const renderShape: SceneRenderer<ElementalSceneShape> = (shape, delay, context) => {
  const { center, radius, waist } = shape;
  const group = context.node(shape.part, "g", { class: "et-scene-shape" });
  const glow = context.filter(shape.part, "glow");
  const flare = context.node(group, "circle", {
    class: "et-scene-flare",
    cx: fixed(center.x),
    cy: fixed(center.y),
    r: fixed(radius * (context.lite ? 0.9 : 1.3)),
    ...(!context.lite && glow ? { filter: `url(#${glow})` } : {}),
  });
  if (context.accent && shape.accent)
    context.node(group, "path", {
      class: "et-scene-accent-line",
      d: starPath(center, radius + 1.2, waist + 0.9),
      "stroke-width": fixed(Math.max(0.8, context.stage.em * 0.035)),
    });
  context.node(group, "path", {
    class: "et-scene-plasma",
    d: starPath(center, radius + 0.8, waist + 0.7),
  });
  context.node(group, "path", { class: "et-scene-core", d: starPath(center, radius, waist) });
  const pivot = (key: ElementalSceneShape["keyframes"][number]) =>
    `translate(${fixed(center.x)}px, ${fixed(center.y)}px) rotate(${key.rotate ?? 0}deg) scale(${key.scale}, ${fixed(key.scale * (key.stretch ?? 1))}) translate(${fixed(-center.x)}px, ${fixed(-center.y)}px)`;
  context.animate(
    group,
    shape.keyframes.map((key) => ({
      offset: key.offset,
      transform: pivot(key),
      opacity: key.opacity,
    })),
    { duration: shape.duration, delay: delay + shape.at, fill: "both" },
  );
  context.animate(
    flare,
    shape.keyframes.map((key) => ({ offset: key.offset, opacity: key.flare ?? 0 })),
    { duration: shape.duration, delay: delay + shape.at, fill: "both" },
  );
};

const renderDissolve: SceneRenderer<ElementalSceneDissolve> = (item, delay, context) => {
  sparks(item.fragments, item.part, delay + item.at, context);
};

/**
 * Renderers by primitive type. Adding a primitive means adding it to the union in
 * `types.ts`, a builder in `scene.ts` and a renderer here; the conductor and the title
 * never change.
 */
export const sceneRenderers: {
  [K in ElementalScenePrimitive["type"]]: SceneRenderer<
    Extract<ElementalScenePrimitive, { type: K }>
  >;
} = {
  stroke: renderStroke,
  traveler: renderTraveler,
  shape: renderShape,
  dissolve: renderDissolve,
};

export interface ScenePlayerOptions {
  stage: ElementalStage;
  /** Scene groups inside the back and front overlays. */
  hosts: Record<ElementalScenePart, SVGGElement | null | undefined>;
  lite: boolean;
  timeScale: number;
  /** The signature's accent color, or undefined for none. */
  accent?: string;
}

export interface SceneRun {
  /** Builds one scene cue's primitives now; their animations run from this moment. */
  add(cue: ElementalSceneCue): void;
  /** Removes every node and cancels every animation now. */
  cancel(): void;
}

let sequence = 0;

/**
 * Plays a timeline's scene cues with Web Animations. Each cue builds its primitives when
 * its beat starts, so the work is spread across the scene; no timers or layout reads run
 * during playback. The conductor cancels the run when the timeline ends or stops, which
 * removes every node at once.
 */
export function createSceneRun({
  stage,
  hosts,
  lite,
  timeScale,
  accent,
}: ScenePlayerOptions): SceneRun {
  const nodes: Element[] = [];
  const animations: Animation[] = [];
  let cancelled = false;
  const containers: Partial<Record<ElementalScenePart, SVGGElement>> = {};
  const container = (part: ElementalScenePart) => {
    const host = hosts[part];
    if (!host) return null;
    if (!containers[part]) {
      const group = document.createElementNS(svg, "g");
      group.setAttribute("class", "et-scene-run");
      // The signature's accent is the default; hosts may override or disable it with
      // --et-signature-accent (a color, or none).
      if (accent) group.style.setProperty("--et-accent-default", accent);
      host.append(group);
      nodes.push(group);
      containers[part] = group;
    }
    return containers[part]!;
  };
  const filterIn = (part: ElementalScenePart, name: string) =>
    hosts[part]?.ownerSVGElement?.querySelector(`filter[data-filter="${name}"]`)?.id;
  const context: SceneRenderContext = {
    stage,
    lite,
    accent: !!accent,
    node(parent, tag, attributes = {}) {
      const element = document.createElementNS(svg, tag);
      for (const [name, value] of Object.entries(attributes))
        element.setAttribute(name, String(value));
      const target = typeof parent === "string" ? container(parent) : parent;
      target?.append(element);
      return element;
    },
    animate(target, keyframes, options) {
      const animation = target.animate(keyframes, options);
      animation.playbackRate = timeScale;
      animations.push(animation);
      return animation;
    },
    filter: (part, name) => filterIn(part, name),
    id: (prefix) => `${prefix}-${(sequence += 1)}`,
    overlays: {
      back: hosts.back?.ownerSVGElement ?? null,
      front: hosts.front?.ownerSVGElement ?? null,
    },
  };
  const animatable =
    typeof SVGElement !== "undefined" && typeof SVGElement.prototype.animate === "function";
  return {
    add(cue) {
      if (cancelled || !animatable) return;
      for (const primitive of cue.primitives)
        (sceneRenderers[primitive.type] as SceneRenderer<ElementalScenePrimitive>)(
          primitive,
          0,
          context,
        );
    },
    cancel() {
      if (cancelled) return;
      cancelled = true;
      for (const animation of animations) animation.cancel();
      for (const node of nodes) node.remove();
      animations.length = 0;
      nodes.length = 0;
    },
  };
}
