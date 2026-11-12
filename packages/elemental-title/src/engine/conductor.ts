import { scaleFrame } from "./frames";
import {
  createStageCoordinator,
  drawSignature,
  noteSignature,
  type Contender,
  type SignatureKind,
  type StageCoordinator,
} from "./coordinator";
import { createLetterAnimator, type LetterAnimator, type LetterTrack } from "./letters";
import { cadenceFor, pickDelay, signaturePriority } from "./program";
import { createRandom } from "./random";
import { createSceneRun, type SceneRun } from "./scene-player";
import type { ElementalSignature } from "./signatures";
import { describeTimeline, timelineDuration, type ElementalMomentInfo } from "./timeline";
import type {
  ElementalCue,
  ElementalEdgeLightCue,
  ElementalEffect,
  ElementalFrame,
  ElementalLettersCue,
  ElementalMomentContext,
  ElementalMomentId,
  ElementalSceneCue,
  ElementalShineCue,
  ElementalStage,
  ElementalTier,
  ElementalTierProgram,
  ElementalTimeline,
} from "./types";

type Timer = ReturnType<typeof setTimeout>;

export interface ConductorLayers {
  /** The ink box: reads the tier's CSS shine strength once per shine. */
  ink: HTMLElement;
  /** The original text layers, masked while their letters move. */
  surface?: HTMLElement | null;
  /** The measured letter shells. */
  letters?: HTMLElement | null;
  /** The rim flash layer for edge-light cues. */
  flash?: HTMLElement | null;
  /** The shine band. */
  energy?: HTMLElement | null;
  /** Scene groups in the back and front overlays, for signature primitives. */
  sceneBack?: SVGGElement | null;
  sceneFront?: SVGGElement | null;
}

export interface ConductorOptions {
  effect: ElementalEffect;
  stage: ElementalStage;
  tier: ElementalTier;
  /** Running ambiently, or hovered, focused or bursting: recurring moments are scheduled. */
  engaged: boolean;
  /** Engagement comes from the host (hover, focus, burst) rather than ambient motion. */
  interactive: boolean;
  /** Session seed for composition and scheduling. */
  seed: number;
  /** Stable hash of the title text. */
  textSeed: number;
  /** Frame keys are shared with the title's still frame; each call returns a new key. */
  nextKey(): number;
  layers: ConductorLayers;
  /** Review aid: 0.25 plays every timer and animation at quarter speed. Default 1. */
  timeScale?: number;
  /** Most glyphs promoted at once; see `letterCap`. */
  letterCap?: number;
  /** Signatures the title may play (enabled, official and eligible), in the host's order. */
  signatures?: readonly ElementalSignature[];
  /** The page (or scope) budget. Defaults to a private one. */
  coordinator?: StageCoordinator;
  /** This title's key in the page memory (its text). */
  memoryKey?: string;
  /** Share of the title visible now, 0–1, which breaks ties between titles asking at once. Default 1. */
  visibility?(): number;
  /**
   * Constrained device: signature primitives render without blur glow and with half the
   * fragments. A function is read as each signature starts.
   */
  lite?: boolean | (() => boolean);
  /**
   * An ambient title's moments share the page budget: cadences stretch when the page is
   * crowded and single-letter jolts share a few slots. Requests, signatures and engaged
   * (hovered, focused, bursting) titles are never budgeted. Default true.
   */
  budget?: boolean;
  onFrame(frame: ElementalFrame): void;
  onMoment?(moment: ElementalMomentInfo): void;
  /** A signature started (its id) or ended (null). */
  onSignature?(signature: string | null): void;
}

export interface Conductor {
  /**
   * Schedules the tier program's recurring moments. Hover and burst titles start a fresh
   * conductor when touched, so their start also counts as a touch.
   */
  start(): void;
  /**
   * Plays a moment now. Returns the timeline, or null when nothing plays. Signatures go
   * through the page budget and start within a few milliseconds, so they return null;
   * `signature` asks for one of the title's signatures by id.
   */
  play(
    moment: ElementalMomentId,
    options?: { explicit?: boolean; signature?: string },
  ): ElementalTimeline | null;
  /**
   * Someone touched the name (a pointer entering it, a finger on it, keyboard focus): plays
   * the next signature unless one is already playing (or ended within its cooldown, if set).
   */
  touch(): void;
  /** Cancels every timer, animation, promoted letter, scene and flash. Nothing accumulates. */
  stop(): void;
}

function clearHoles(flash: HTMLElement) {
  delete flash.dataset.holes;
  flash.style.removeProperty("--et-rim-holes");
}

/** Rim envelope of a strike; the peak equals the cue's strength. */
const rim = [
  { opacity: 1 },
  { opacity: 0.45 / 0.95, offset: 0.12 },
  { opacity: 0.85 / 0.95, offset: 0.2 },
  { opacity: 0.5 / 0.95, offset: 0.45 },
  { opacity: 0 },
];

interface Playing {
  timeline: ElementalTimeline;
  timer?: Timer;
  track?: LetterTrack;
  lettersDone: boolean;
  /** Holds one of the page's letter-moment slots. */
  slot: boolean;
  /** Holds one of the page's ambient jolt slots. */
  jolt: boolean;
  explicit: boolean;
}

interface Owned {
  priority: number;
  animation: Animation;
}

interface Showing {
  entry: Playing;
  signature: ElementalSignature;
  kind: SignatureKind;
  scene?: SceneRun;
  end?: Timer;
}

/** Ambient moments per second a tier program plays, from the middle of each cadence. */
export function ambientRate(program: ElementalTierProgram): number {
  let rate = 0;
  for (const cadence of Object.values(program.cadence)) {
    const range = cadence.ambient;
    if (range) rate += 1000 / Math.max(1, (range[0] + range[1]) / 2);
  }
  return rate;
}

/** The shortest touch cooldown among a title's signatures; null when none answers a touch. */
function touchCooldown(signatures: readonly ElementalSignature[]): number | null {
  const cooldowns = signatures
    .map((signature) => signature.cadence.cooldown)
    .filter((value): value is number => value !== null);
  return cooldowns.length ? Math.min(...cooldowns) : null;
}

/**
 * Owns every timer and animation of one title. It schedules moments from the tier
 * program, plays signatures when the name is touched or the host asks, plays timelines
 * cue by cue, resolves priority
 * on shared layers and letters, asks the page budget before a signature or a whole-word
 * letter moment, and cancels everything on stop. The title creates one per running state
 * and stops it on pause, hidden document, reduced motion, forced colors, engagement change,
 * resize and unmount.
 */
export function createConductor(options: ConductorOptions): Conductor {
  const { effect, stage, tier, layers } = options;
  const scale =
    Number.isFinite(options.timeScale) && options.timeScale! > 0 ? options.timeScale! : 1;
  const random = createRandom(options.seed);
  const program = effect.program[tier];
  const plans = new Map<ElementalMomentId, Timer>();
  const playing = new Set<Playing>();
  const coordinator = options.coordinator ?? createStageCoordinator();
  const signatures = options.signatures ?? [];
  const cooldown = touchCooldown(signatures);
  const memory = signatures.length
    ? coordinator.memory(options.memoryKey ?? String(options.textSeed))
    : undefined;
  let animator: LetterAnimator | null | undefined;
  let edge: Owned | null = null;
  let shine: Owned | null = null;
  let showing: Showing | null = null;
  let stopped = false;
  let leaveAmbient: (() => void) | undefined;
  /** Ambient titles share the page budget; hovered, focused and bursting ones do not. */
  const budgeted = options.budget !== false && !options.interactive;
  const visibility = () => options.visibility?.() ?? 1;
  const lite = () => (typeof options.lite === "function" ? options.lite() : !!options.lite);

  const letters = () => {
    if (animator === undefined)
      animator =
        effect.layers.letters && layers.surface && layers.letters
          ? createLetterAnimator(layers.surface, layers.letters, stage, {
              cap: options.letterCap,
              timeScale: scale,
            })
          : null;
    return animator;
  };

  const context = (explicit: boolean): ElementalMomentContext => ({
    tier,
    params: program.params,
    engaged: options.engaged,
    interactive: options.interactive,
    explicit,
    random,
    key: options.nextKey(),
    textSeed: options.textSeed,
  });

  const releaseSlot = (entry: Playing) => {
    if (entry.jolt) {
      entry.jolt = false;
      coordinator.releaseJolt(entry);
    }
    if (!entry.slot) return;
    entry.slot = false;
    coordinator.releaseLetters(entry);
  };

  const playLetters = (entry: Playing, cue: ElementalLettersCue) => {
    const animator = letters();
    if (entry.lettersDone) return;
    entry.lettersDone = true;
    if (!animator) {
      releaseSlot(entry);
      return;
    }
    // Every letters cue of the timeline shares one promotion; later beats become delays.
    const cues = entry.timeline.cues.filter(
      (item): item is ElementalLettersCue => item.type === "letters",
    );
    const track = animator.claim(
      cues.flatMap((item) => item.animations.map((animation) => animation.glyph)),
      entry.timeline.priority,
      () => releaseSlot(entry),
    );
    entry.track = track;
    for (const item of cues)
      for (const animation of item.animations) track.animate(animation, item.at - cue.at);
    track.seal();
  };

  const playSceneCue = (entry: Playing, cue: ElementalSceneCue) => {
    if (!showing || showing.entry !== entry) return;
    // One run per signature; each beat builds its own primitives when it starts.
    showing.scene ??= createSceneRun({
      stage,
      hosts: { back: layers.sceneBack, front: layers.sceneFront },
      lite: lite(),
      timeScale: scale,
      accent: showing.signature.accent,
    });
    showing.scene.add(cue);
  };

  /** A soft elliptical hole around a glyph, in the flash layer's (ink box) coordinates. */
  const hole = (glyph: number) => {
    const box = stage.glyphs[glyph];
    const x = box.center.x - stage.text.x;
    const y = (box.inkTop + box.inkBottom) / 2 - stage.text.y;
    const rx = box.width * 0.8;
    const ry = (box.inkBottom - box.inkTop) * 0.8;
    return `radial-gradient(${rx.toFixed(1)}px ${ry.toFixed(1)}px at ${x.toFixed(1)}px ${y.toFixed(1)}px, transparent 55%, #000 100%)`;
  };

  const percent = (value: number, size: number) => `${((value / size) * 100).toFixed(1)}%`;

  const playEdge = (entry: Playing, cue: ElementalEdgeLightCue) => {
    const flash = layers.flash;
    if (!flash || typeof flash.animate !== "function") return;
    const priority = entry.timeline.priority;
    if (edge && edge.priority > priority) return;
    edge?.animation.cancel();
    const x = percent(cue.x - stage.text.x, stage.text.width);
    const y = percent(cue.y - stage.text.y, stage.text.height);
    flash.style.setProperty("--et-light-x", x);
    flash.style.setProperty("--et-light-y", y);
    flash.style.setProperty("--et-light-radius", `${cue.radius.toFixed(1)}px`);
    // A letter lit by its own hot edge gets a feathered hole in the rim, so it is never
    // lit twice and the glow keeps no hard edge.
    const lit = (cue.exclude ?? []).filter((glyph) => entry.track?.glyphs.has(glyph));
    if (lit.length) {
      flash.style.setProperty("--et-rim-holes", lit.map(hole).join(", "));
      flash.dataset.holes = "";
    } else clearHoles(flash);
    const keyframes: Keyframe[] = cue.to
      ? [
          // A passing light: the centre travels while the rim fades in, holds and fades out.
          { opacity: 0, "--et-light-x": x, "--et-light-y": y },
          { opacity: cue.strength, offset: 0.15 },
          { opacity: cue.strength, offset: 0.75 },
          {
            opacity: 0,
            "--et-light-x": percent(cue.to.x - stage.text.x, stage.text.width),
            "--et-light-y": percent(cue.to.y - stage.text.y, stage.text.height),
          },
        ]
      : rim.map((key) => ({ ...key, opacity: key.opacity * cue.strength }));
    const animation = flash.animate(keyframes, {
      duration: cue.duration,
      easing: cue.to ? "linear" : "ease-out",
    });
    animation.playbackRate = scale;
    const owned = { priority, animation };
    edge = owned;
    animation.onfinish = () => {
      if (edge !== owned) return;
      edge = null;
      clearHoles(flash);
    };
  };

  const playShine = (entry: Playing, cue: ElementalShineCue) => {
    const energy = layers.energy;
    if (!energy || typeof energy.animate !== "function") return;
    const priority = entry.timeline.priority;
    if (shine && shine.priority > priority) return;
    // A tier may set its shine strength to 0; only a missing or invalid value falls back.
    const parsed = parseFloat(getComputedStyle(layers.ink).getPropertyValue("--et-energy-opacity"));
    const strength = Number.isNaN(parsed) ? 0.5 : parsed;
    const peak = Math.min(0.85, strength * cue.gain);
    energy.style.setProperty("--et-shine-angle", `${cue.angle.toFixed(0)}deg`);
    shine?.animation.cancel();
    const animation = energy.animate(
      [
        { backgroundPosition: `${cue.reverse ? 0 : 100}% 0`, opacity: 0 },
        { opacity: peak, offset: cue.rise },
        { opacity: peak * cue.fade, offset: cue.hold },
        { backgroundPosition: `${cue.reverse ? 100 : 0}% 0`, opacity: 0 },
      ],
      { duration: cue.duration, easing: "cubic-bezier(0.42, 0.04, 0.3, 1)" },
    );
    animation.playbackRate = scale;
    const owned = { priority, animation };
    shine = owned;
    animation.onfinish = () => {
      if (shine === owned) shine = null;
    };
  };

  const dispatch = (entry: Playing, cue: ElementalCue) => {
    switch (cue.type) {
      case "frame":
        options.onFrame(scaleFrame(cue.frame, scale));
        break;
      case "letters":
        playLetters(entry, cue);
        break;
      case "edge-light":
        playEdge(entry, cue);
        break;
      case "shine":
        playShine(entry, cue);
        break;
      case "scene":
        playSceneCue(entry, cue);
        break;
    }
  };

  /** Dispatches cues whose time has come, then waits for the next offset (one timer). */
  const pump = (entry: Playing, index: number, now: number) => {
    const cues = entry.timeline.cues;
    while (index < cues.length && cues[index].at <= now) dispatch(entry, cues[index++]);
    if (index >= cues.length) {
      entry.timer = undefined;
      if (showing?.entry !== entry) playing.delete(entry);
      return;
    }
    const next = cues[index].at;
    entry.timer = setTimeout(() => pump(entry, index, next), (next - now) / scale);
  };

  const begin = (moment: ElementalMomentId, explicit: boolean) => {
    // The element keeps going while a signature plays; the signature wins shared layers.
    if (!effect.moments[moment]) return null;
    const timeline = effect.timeline(moment, stage, context(explicit));
    if (!timeline) return null;
    const entry: Playing = {
      timeline,
      lettersDone: false,
      slot: false,
      jolt: false,
      explicit,
    };
    // Moments that move several letters share the page's budget; explicit ones always play.
    const glyphs = new Set(
      timeline.cues.flatMap((cue) =>
        cue.type === "letters" ? cue.animations.map((animation) => animation.glyph) : [],
      ),
    );
    if (glyphs.size > 1) {
      if (!coordinator.acquireLetters(entry, explicit)) return null;
      entry.slot = true;
    } else if (glyphs.size && !explicit && budgeted) {
      // An ambient jolt takes one of the page's few jolt slots. Without one, the moment
      // still plays and its letter stays at rest.
      if (coordinator.acquireJolt(entry, visibility(), lite())) entry.jolt = true;
      else
        entry.timeline = {
          ...timeline,
          cues: timeline.cues.filter((cue) => cue.type !== "letters"),
        };
    }
    playing.add(entry);
    pump(entry, 0, 0);
    return entry.timeline;
  };

  const notify = (timeline: ElementalTimeline | null, explicit: boolean) => {
    if (timeline) options.onMoment?.(describeTimeline(timeline, explicit));
  };

  const plan = (moment: ElementalMomentId, first: boolean) => {
    const range = cadenceFor(program.cadence[moment], options.interactive, first);
    if (!range) return;
    // On a crowded page every ambient title stretches its cadence by the same factor, so
    // tiers keep their order.
    const stretch = budgeted ? coordinator.ambientStretch(visibility(), lite()) : 1;
    plans.set(
      moment,
      setTimeout(
        () => {
          // Plan the next occurrence before telling the host, so a throwing
          // listener can never end the schedule.
          const timeline = begin(moment, false);
          plan(moment, false);
          notify(timeline, false);
        },
        (pickDelay(random, range) * stretch) / scale,
      ),
    );
  };

  /* ---- Signatures ---------------------------------------------------------------- */

  const cancelSignature = () => {
    if (!showing) return;
    const current = showing;
    showing = null;
    clearTimeout(current.end);
    clearTimeout(current.entry.timer);
    playing.delete(current.entry);
    current.scene?.cancel();
    if (edge && edge.priority >= signaturePriority) {
      edge.animation.cancel();
      edge = null;
      if (layers.flash) clearHoles(layers.flash);
    }
    options.onSignature?.(null);
  };

  const finishSignature = () => {
    cancelSignature();
    coordinator.ended(contender);
  };

  const startSignature = (kind: SignatureKind, requested?: string): boolean => {
    if (stopped || !memory || showing) return false;
    const chosen = requested
      ? signatures.find((signature) => signature.id === requested)
      : undefined;
    if (requested && !chosen) return false;
    const id =
      chosen?.id ??
      drawSignature(
        memory.bag,
        signatures.map((s) => s.id),
        memory.random,
      );
    if (chosen) noteSignature(memory.bag, chosen.id);
    const signature = signatures.find((item) => item.id === id);
    if (!signature) return false;
    const built = signature.timeline(stage, context(kind === "explicit"));
    if (!built) return false;
    const timeline: ElementalTimeline = {
      ...built,
      moment: "signature",
      priority: Math.max(built.priority, signaturePriority),
      signature: { id: signature.id, name: signature.name },
    };
    const entry: Playing = {
      timeline,
      lettersDone: false,
      slot: false,
      jolt: false,
      explicit: kind === "explicit",
    };
    showing = { entry, signature, kind };
    playing.add(entry);
    options.onSignature?.(signature.id);
    // Composing the scene and drawing its first beat run as separate tasks, so neither
    // blocks the main thread for long on a slow device.
    entry.timer = setTimeout(() => pump(entry, 0, 0), 0);
    const current = showing;
    current.end = setTimeout(
      () => {
        if (showing === current) finishSignature();
      },
      (timelineDuration(timeline) + 20) / scale,
    );
    notify(timeline, kind === "explicit");
    return true;
  };

  const contender: Contender = {
    key: options.memoryKey ?? String(options.textSeed),
    ratio: visibility,
    begin: startSignature,
    preempt: cancelSignature,
  };

  const touch = () => {
    if (stopped || !memory || showing || cooldown === null) return;
    if (coordinator.now() - memory.lastEnd < cooldown) return;
    coordinator.request(contender, "engaged");
  };

  return {
    start() {
      // Starting twice never counts a title twice.
      leaveAmbient?.();
      leaveAmbient = undefined;
      if (options.engaged && budgeted) leaveAmbient = coordinator.joinAmbient(ambientRate(program));
      if (options.engaged) for (const moment of Object.keys(program.cadence)) plan(moment, true);
      if (options.interactive && options.engaged) touch();
    },
    touch,
    play(moment, { explicit = false, signature } = {}) {
      if (moment === "signature") {
        if (!memory || stopped) return null;
        if (signature && !signatures.some((item) => item.id === signature)) return null;
        if (showing) {
          // Never back to back. A request for a different signature replaces this one.
          if (!signature || signature === showing.signature.id) return null;
          cancelSignature();
          coordinator.ended(contender);
        }
        coordinator.request(contender, explicit ? "explicit" : "engaged", signature);
        return null;
      }
      const timeline = begin(moment, explicit);
      notify(timeline, explicit);
      return timeline;
    },
    stop() {
      stopped = true;
      leaveAmbient?.();
      leaveAmbient = undefined;
      for (const timer of plans.values()) clearTimeout(timer);
      plans.clear();
      cancelSignature();
      coordinator.withdraw(contender);
      for (const entry of playing) {
        clearTimeout(entry.timer);
        releaseSlot(entry);
      }
      playing.clear();
      edge?.animation.cancel();
      edge = null;
      if (layers.flash) clearHoles(layers.flash);
      shine?.animation.cancel();
      shine = null;
      animator?.cancelAll();
    },
  };
}
