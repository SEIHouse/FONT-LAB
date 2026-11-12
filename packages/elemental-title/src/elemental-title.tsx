"use client";

import {
  forwardRef,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type HTMLAttributes,
  type Ref,
} from "react";
const cn = (...classes: Array<string | false | null | undefined>) =>
  classes.filter(Boolean).join(" ");
import { createConductor, type Conductor } from "./engine/conductor";
import { ambientBudget, constrainedDevice, coordinatorFor } from "./engine/coordinator";
import { ElementalOverlay } from "./engine/ElementalOverlay";
import { LetterLayer } from "./engine/LetterLayer";
import {
  ignoredSignatures,
  resolveRecipe,
  resolveRecipeEffect,
  resolveRecipeSignatures,
} from "./engine/recipe";
import { createRandom, hashString } from "./engine/random";
import { pushFrame } from "./engine/frames";
import { measureStage, sameStage } from "./engine/stage";
import type { ElementalMomentInfo } from "./engine/timeline";
import type { ElementalFrame, ElementalStage } from "./engine/types";

export type ElementalTitleElement = "span" | "p" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
export type ElementalTitleEffect =
  | "none"
  | "fire"
  | "lightning"
  | "water"
  | "poison"
  | "frost"
  | "celestial"
  | "void";
export type ElementalTitleIntensity =
  | "subtle"
  | "active"
  | "common"
  | "rare"
  | "epic"
  | "legendary";
export type ElementalTitleMotion = "ambient" | "hover" | "burst";
export type ElementalTitleSize = "inherit" | "sm" | "md" | "lg" | "xl";
export type ElementalTitleShadow = "none" | "soft" | "outlined";
/**
 * Official familiar signatures: exclusive animations around the name, `"<familiar>/<name>"`.
 * The host decides which ids a user may pass (earned, purchased and enabled).
 */
export type ElementalTitleSignature = "quill/stormwrit" | "quill/true-north";
/** A host request to play a named moment, e.g. `{ id: "strike", key: n }`. */
export interface ElementalTitleMomentRequest {
  /** Moment id. Lightning plays "strike", "crackle" and "shine"; any title with signatures plays "signature". */
  id: string;
  /** Change this value to play the moment again. */
  key: number;
  /**
   * With `id: "signature"`: play this one of the title's `signatures` (a shop or Familiar
   * screen preview) instead of the next one in its rotation. Leave it out to play the next
   * one, for example when the app marks an action tied to the familiar.
   */
  signature?: ElementalTitleSignature;
}
/** A moment that started playing: its cues and beat labels, without geometry. */
export type ElementalTitleMoment = Omit<ElementalMomentInfo, "signature"> & {
  /** The signature that played, for `"signature"` moments. */
  signature?: { id: ElementalTitleSignature; name: string };
};

export interface ElementalTitleProps extends Omit<
  HTMLAttributes<HTMLElement>,
  "children" | "dangerouslySetInnerHTML"
> {
  /** Plain text, escaped by React. No markup or decorative children. */
  children: string;
  /** Match the host document outline; inline text by default. */
  as?: ElementalTitleElement;
  /** Opt in to elemental lettering; existing consumers stay plain by default. */
  element?: ElementalTitleEffect;
  /** Optional CSS text color, independent of the selected elemental effect. */
  color?: string;
  /** Familiar bond tier controls strength independently of rank color. Legacy aliases remain supported. */
  intensity?: ElementalTitleIntensity;
  /** Burst plays once on pointer entry, press, or focus, including a containing control. */
  motion?: ElementalTitleMotion;
  /** Inherit preserves the host profile's typography. Other sizes scale responsively. */
  size?: ElementalTitleSize;
  /** Letter edge treatment. Lightning, water and poison default to the rank keyline (`outlined`), others to `soft`. */
  shadow?: ElementalTitleShadow;
  /** Change this value to request a strike. Alias of `playMoment={{ id: "strike", key }}`. */
  strikeKey?: number;
  /**
   * Official signatures this user owns and has enabled. They never play on their own: one
   * plays when someone touches the name (a pointer entering it, a finger on it, keyboard
   * focus), again on every touch once the last play has finished, or when the host asks with
   * `playMoment`. The element keeps animating while it plays. Each plays only
   * when the title's bond tier meets the signature's minimum and its element matches; others
   * are ignored (with a development warning). With several, each plays before any repeats.
   */
  signatures?: readonly ElementalTitleSignature[];
  /**
   * Plays the named moment whenever `key` changes after mount. Unknown moments are ignored.
   * Respects visibility, document state, reduced motion and forced colors, and does not
   * start an idle title's recurring schedule.
   */
  playMoment?: ElementalTitleMomentRequest;
  /** Called when a moment starts, with its cues and beat labels (review readouts, sound sync). */
  onMoment?: (moment: ElementalTitleMoment) => void;
  /**
   * Review aid only: scales the speed of every moment's timers and animations together
   * (0.25 = quarter speed). Leave unset in product UI. Defaults to 1.
   */
  timeScale?: number;
  ref?: Ref<HTMLElement>;
}

type Anchor = { x: number; y: number };
const particleCounts = {
  subtle: 3,
  active: 6,
  common: 2,
  rare: 3,
  epic: 6,
  legendary: 8,
} as const;
const burstDuration = 1800;
/** Engine elements draw behind the letters; a rank-tinted keyline keeps the letters in front. */
const keylineElements = new Set<ElementalTitleEffect>(["lightning", "water", "poison"]);
/** Legacy CSS particles: a bounded set of glyph-anchored points. */
function measureAnchors(ink: HTMLElement, text: Text, value: string, count: number): Anchor[] {
  const box = ink.getBoundingClientRect();
  if (!box.width || !box.height) return [];
  // Preserve the legacy particle placement; only the letter engine changes to graphemes.
  const offsets: { start: number; end: number }[] = [];
  let start = 0;
  for (const character of value) {
    if (!/\s/u.test(character)) offsets.push({ start, end: start + character.length });
    start += character.length;
  }
  const range = document.createRange();
  return Array.from({ length: Math.min(count, offsets.length) }, (_, index) => {
    // Spread the first four anchors across the name as well as the full desktop set.
    const position = offsets[Math.floor(((0.13 + index * 0.61803398875) % 1) * offsets.length)];
    range.setStart(text, position.start);
    range.setEnd(text, position.end);
    const glyph = range.getBoundingClientRect();
    return {
      x: ((glyph.left + glyph.width / 2 - box.left) / box.width) * 100,
      y: ((glyph.top + glyph.height * (index % 2 ? 0.78 : 0.22) - box.top) / box.height) * 100,
    };
  });
}

type MomentPlayer = (moment: string, signature?: string) => void;

/** Plays a moment when `key` changes after mount (not on the first render). */
function useMomentRequest(
  play: { current: MomentPlayer | null },
  id: string | undefined,
  key: number | undefined,
  signature?: string,
) {
  const previous = useRef(key);
  useEffect(() => {
    if (previous.current === key) return;
    previous.current = key;
    if (id) play.current?.(id, signature);
  }, [id, key, play, signature]);
}

declare const process: { env?: { NODE_ENV?: string } } | undefined;

/** Development builds only: bundlers replace `process.env.NODE_ENV`; plain browsers have no `process`. */
function developing() {
  try {
    return typeof process !== "undefined" && process?.env?.NODE_ENV !== "production";
  } catch {
    return false;
  }
}

const warn = (message: string) => {
  if (developing()) console.warn(`ElementalTitle: ${message}`);
};

/** Measures decoration without splitting the real layout or accessible text. */
function ElementalLettering({
  children,
  element,
  intensity,
  motion,
  strikeKey,
  signatures: enabled,
  playMoment,
  onMoment,
  timeScale = 1,
}: {
  children: string;
  element: ElementalTitleEffect;
  intensity: ElementalTitleIntensity;
  motion: ElementalTitleMotion;
  strikeKey?: number;
  signatures?: readonly ElementalTitleSignature[];
  playMoment?: ElementalTitleMomentRequest;
  onMoment?: (moment: ElementalTitleMoment) => void;
  timeScale?: number;
}) {
  const inkRef = useRef<HTMLSpanElement>(null);
  const textRef = useRef<HTMLSpanElement>(null);
  const flashRef = useRef<HTMLSpanElement>(null);
  const energyRef = useRef<HTMLSpanElement>(null);
  const surfaceRef = useRef<HTMLSpanElement>(null);
  const letterRef = useRef<HTMLSpanElement>(null);
  const sceneBackRef = useRef<SVGGElement>(null);
  const sceneFrontRef = useRef<SVGGElement>(null);
  const request = useRef<MomentPlayer | null>(null);
  const conductorRef = useRef<Conductor | null>(null);
  const ratio = useRef(0);
  const signing = useRef<string | null>(null);
  const releaseHold = useRef<(() => void) | null>(null);
  const listener = useRef(onMoment);
  const counter = useRef(0);
  const requested = (enabled ?? []).join(",");
  const recipe = resolveRecipe(element, intensity, enabled);
  const effect = resolveRecipeEffect(recipe);
  const { tier } = recipe;
  const signatureKey = recipe.signatures.join(",");
  // Keyed by the eligible ids, so an inline array prop never restarts the title.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const signatures = useMemo(() => resolveRecipeSignatures(recipe), [signatureKey, tier, element]);
  const touchable = signatures.length > 0;
  const overlay = !!effect && (!!effect.layers.overlay || touchable);
  const [running, setRunning] = useState(false);
  const [burst, setBurst] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [anchors, setAnchors] = useState<Anchor[]>([]);
  const [stage, setStage] = useState<ElementalStage | null>(null);
  const [frames, setFrames] = useState<ElementalFrame[]>([]);
  const engaged = motion === "ambient" ? running : motion === "hover" ? hovered : burst;

  useEffect(() => {
    const ink = inkRef.current;
    if (!ink) return;
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const forced = window.matchMedia?.("(forced-colors: active)");
    let visible = typeof IntersectionObserver === "undefined";
    if (visible) ratio.current = 1;
    const sync = () =>
      setRunning(visible && !document.hidden && !media?.matches && !forced?.matches);
    const observer =
      typeof IntersectionObserver === "undefined"
        ? undefined
        : new IntersectionObserver(
            ([entry]) => {
              visible = entry.isIntersecting;
              // The share in view breaks ties between titles asking to sign at once.
              ratio.current = entry.isIntersecting ? (entry.intersectionRatio ?? 1) : 0;
              sync();
            },
            { threshold: [0, 0.25, 0.5, 0.75, 1] },
          );
    observer?.observe(ink);
    media?.addEventListener("change", sync);
    forced?.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    sync();
    return () => {
      observer?.disconnect();
      media?.removeEventListener("change", sync);
      forced?.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
    };
  }, []);

  useEffect(() => {
    const ink = inkRef.current;
    const text = textRef.current?.firstChild;
    if (!children.trim() || !ink || !text || text.nodeType !== Node.TEXT_NODE) return;
    // Overlay effects also measure while paused so a still frame exists; legacy particles only run live.
    if (!effect && !running) return;
    let cancelled = false;
    const measure = () => {
      // A queued font/resize callback can arrive after a text commit and before effect cleanup.
      if (cancelled || !text.isConnected || text.textContent !== children) return;
      if (effect) {
        const next = measureStage(ink, text as Text, children, Infinity, effect.overscan);
        if (next) setStage((previous) => (sameStage(previous, next) ? previous : next));
      } else {
        setAnchors(measureAnchors(ink, text as Text, children, particleCounts[intensity]));
      }
    };
    measure();
    const observer =
      typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(measure);
    observer?.observe(ink);
    window.addEventListener("resize", measure);
    void document.fonts?.ready.then(measure);
    document.fonts?.addEventListener("loadingdone", measure);
    return () => {
      cancelled = true;
      observer?.disconnect();
      window.removeEventListener("resize", measure);
      document.fonts?.removeEventListener("loadingdone", measure);
    };
  }, [children, effect, intensity, running]);

  // What touching the name does. A touch is a mouse or pen pointer entering the name, a
  // finger on it, or keyboard focus, including on a containing control.
  useEffect(() => {
    const root = inkRef.current?.parentElement;
    if (motion === "ambient" || !running || !root) {
      setBurst(false);
      setHovered(false);
    }
    if (!running || !root || (motion === "ambient" && !touchable)) return;
    const trigger = root.closest("button, a[href], [role='button']") ?? root;
    const listen = (listeners: Record<string, (event: Event) => void>) => {
      const entries = Object.entries(listeners);
      for (const [type, listener] of entries) trigger.addEventListener(type, listener);
      return () => {
        for (const [type, listener] of entries) trigger.removeEventListener(type, listener);
      };
    };
    if (motion === "ambient") {
      // The element keeps running on its own; a touch plays a signature.
      const touch = () => conductorRef.current?.touch();
      return listen({ pointerenter: touch, pointerdown: touch, focusin: touch });
    }
    let timer: ReturnType<typeof setTimeout> | undefined;
    // A signature that started with the engagement finishes before the engagement ends.
    const hold = (release: () => void) => {
      if (!signing.current) return release();
      releaseHold.current = () => {
        releaseHold.current = null;
        release();
      };
    };
    const after = (delay: number, release: () => void) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        timer = undefined;
        hold(release);
      }, delay);
    };
    let unlisten: () => void;
    if (motion === "hover") {
      const enter = () => {
        clearTimeout(timer);
        timer = undefined;
        releaseHold.current = null;
        setHovered(true);
      };
      const leave = (event: Event) => {
        const next = (event as FocusEvent).relatedTarget;
        const still =
          event.type === "focusout"
            ? (next instanceof Node && trigger.contains(next)) || trigger.matches(":hover")
            : trigger.matches(":focus-within");
        if (still) return;
        // A finger leaves as soon as it lifts, so its touch lasts as long as a burst.
        if ((event as PointerEvent).pointerType === "touch")
          after(burstDuration, () => setHovered(false));
        else hold(() => setHovered(false));
      };
      unlisten = listen({
        pointerenter: enter,
        focusin: enter,
        pointerleave: leave,
        focusout: leave,
      });
      setHovered(trigger.matches(":hover, :focus-within"));
    } else {
      const play = () => {
        if (timer) return;
        releaseHold.current = null;
        setBurst(true);
        after(burstDuration, () => setBurst(false));
      };
      unlisten = listen({ pointerenter: play, pointerdown: play, focusin: play });
    }
    return () => {
      releaseHold.current = null;
      clearTimeout(timer);
      unlisten();
    };
  }, [motion, running, touchable]);

  // A deterministic still frame is composed as soon as the letters are measured, so a
  // paused, reduced-motion or not-yet-hovered title already reads as its element.
  // Restore it on running-state changes: transient materials may have already exited.
  useEffect(() => {
    if (!effect?.still || !stage) {
      setFrames((previous) => (previous.length ? [] : previous));
      return;
    }
    counter.current += 1;
    setFrames([
      effect.still(stage, {
        tier,
        params: effect.program[tier].params,
        random: createRandom(hashString(children)),
        key: counter.current,
      }),
    ]);
  }, [children, effect, stage, tier, running]);

  useEffect(() => {
    listener.current = onMoment;
  }, [onMoment]);

  useEffect(() => {
    for (const { id, reason } of ignoredSignatures(
      element,
      intensity,
      requested ? requested.split(",") : [],
    ))
      warn(`signature "${id}" is ignored: ${reason}.`);
  }, [element, intensity, requested]);

  // The conductor owns every timer and animation. Any change of running state,
  // engagement, measurement, tier or speed stops it and starts a fresh one.
  useEffect(() => {
    const ink = inkRef.current;
    if (!effect || !stage || !running || !ink) return;
    const conductor = createConductor({
      effect,
      stage,
      tier,
      signatures,
      coordinator: coordinatorFor(ink),
      memoryKey: children,
      visibility: () => ratio.current,
      lite: () => constrainedDevice(ink),
      budget: ambientBudget(ink),
      engaged,
      interactive: motion !== "ambient",
      seed: (hashString(children) ^ (Date.now() >>> 0)) >>> 0,
      textSeed: hashString(children),
      nextKey: () => (counter.current += 1),
      layers: {
        ink,
        surface: surfaceRef.current,
        letters: letterRef.current,
        flash: flashRef.current,
        energy: energyRef.current,
        sceneBack: sceneBackRef.current,
        sceneFront: sceneFrontRef.current,
      },
      timeScale,
      onFrame: (frame) => setFrames((previous) => pushFrame(previous, frame)),
      onMoment: (moment) => listener.current?.(moment as ElementalTitleMoment),
      onSignature: (id) => {
        signing.current = id;
        if (id) ink.dataset.signature = id;
        else {
          delete ink.dataset.signature;
          releaseHold.current?.();
        }
      },
    });
    conductorRef.current = conductor;
    conductor.start();
    request.current = (moment, signature) => {
      if (signature && !signatures.some((item) => item.id === signature))
        warn(`signature "${signature}" was requested but is not enabled and eligible here.`);
      conductor.play(moment, { explicit: true, signature });
    };
    return () => {
      request.current = null;
      conductorRef.current = null;
      conductor.stop();
    };
  }, [children, effect, engaged, motion, running, signatures, stage, tier, timeScale]);

  useMomentRequest(request, "strike", strikeKey);
  useMomentRequest(request, playMoment?.id, playMoment?.key, playMoment?.signature);

  const textLayers = (
    <>
      <span aria-hidden="true" className="elemental-title__aura">
        {children}
      </span>
      <span aria-hidden="true" className="elemental-title__edge">
        {children}
      </span>
      <span ref={textRef} className="elemental-title__text">
        {children}
      </span>
      <span ref={energyRef} aria-hidden="true" className="elemental-title__energy">
        {children}
      </span>
    </>
  );

  return (
    <span ref={inkRef} className="elemental-title__ink" data-running={running} data-burst={burst}>
      {overlay && (
        <span aria-hidden="true" className="elemental-title__arcs elemental-title__arcs--back">
          {stage ? (
            <ElementalOverlay stage={stage} frames={frames} part="back" sceneRef={sceneBackRef} />
          ) : null}
        </span>
      )}
      {effect?.layers.letters ? (
        <span ref={surfaceRef} className="elemental-title__surface">
          {textLayers}
        </span>
      ) : (
        textLayers
      )}
      {effect?.layers.letters && stage && <LetterLayer stage={stage} layerRef={letterRef} />}
      {effect?.layers.edgeLight && (
        <span ref={flashRef} aria-hidden="true" className="elemental-title__flash">
          {children}
        </span>
      )}
      {effect ? (
        // The element draws only behind the letters; in front sit signature scenes alone.
        touchable && (
          <span aria-hidden="true" className="elemental-title__arcs elemental-title__arcs--front">
            {stage ? (
              <ElementalOverlay stage={stage} part="front" sceneRef={sceneFrontRef} />
            ) : null}
          </span>
        )
      ) : (
        <span aria-hidden="true" className="elemental-title__particles">
          {anchors.map(({ x, y }, index) => (
            <span
              key={index}
              className="elemental-title__particle"
              style={
                {
                  left: `${x}%`,
                  top: `${y}%`,
                  "--et-delay": `${-index * 0.73}s`,
                  "--et-duration": `${2.6 + (index % 3) * 0.9}s`,
                  "--et-drift": `${index % 2 ? -0.3 : 0.28}em`,
                  "--et-turn": `${index % 2 ? -32 : 24}deg`,
                } as CSSProperties
              }
            />
          ))}
        </span>
      )}
    </span>
  );
}

/** Readable semantic text with optional, non-interactive elemental decoration. */
export const ElementalTitle = forwardRef<HTMLElement, ElementalTitleProps>(function ElementalTitle(
  {
    as: Tag = "span",
    children,
    className,
    element = "none",
    color,
    intensity = "active",
    motion = "ambient",
    size = "inherit",
    shadow = keylineElements.has(element) ? "outlined" : "soft",
    strikeKey,
    signatures,
    playMoment,
    onMoment,
    timeScale,
    style,
    ...props
  }: ElementalTitleProps,
  ref: Ref<HTMLElement>
) {
  const titleStyle = color
    ? ({ ...style, color, "--et-custom-color": color } as CSSProperties)
    : style;
  return (
    <Tag
      {...props}
      ref={ref as any}
      className={cn("elemental-title", className)}
      style={titleStyle}
      data-element={element}
      data-color={color ? "custom" : "default"}
      data-intensity={intensity}
      data-motion={motion}
      data-size={size}
      data-shadow={shadow}
    >
      {element === "none" || !children.trim() ? (
        children
      ) : (
        <ElementalLettering
          key={
            resolveRecipeEffect(resolveRecipe(element, intensity))?.layers.letters
              ? children
              : undefined
          }
          element={element}
          intensity={intensity}
          motion={motion}
          strikeKey={strikeKey}
          signatures={signatures}
          playMoment={playMoment}
          onMoment={onMoment}
          timeScale={timeScale}
        >
          {children}
        </ElementalLettering>
      )}
    </Tag>
  );
});

ElementalTitle.displayName = "ElementalTitle";
