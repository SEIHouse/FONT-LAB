import { createRandom, hashString, pick, type Random } from "./random";

/*
 * The page budget. Every title of a page (or of an element marked `data-elemental-scope`)
 * shares one coordinator: at most one signature plays at a time, at most
 * `letterMomentLimit` moments that move several letters run at once, and the ambient
 * moments of all running titles share a rate and a few letter jolts, so a page full of
 * strong titles stays smooth. Idle titles cost nothing: the coordinator only holds a
 * timer while signature requests wait for a decision.
 */

/**
 * Why a signature wants to play: someone touched the name (`engaged`: a pointer, a finger or
 * keyboard focus), or the host asked (`explicit`: a preview, an app action). Signatures never
 * play on their own. Explicit requests beat touches.
 */
export type SignatureKind = "engaged" | "explicit";

const rank: Record<SignatureKind, number> = { engaged: 0, explicit: 1 };

/** Concurrent moments that move more than one letter, page-wide. Explicit requests are exempt. */
export const letterMomentLimit = 3;
/** Requests arriving within this window compete; the best one plays. */
export const decisionWindow = 40;
/**
 * Ambient element moments per second the page plays before cadences stretch (half on
 * constrained devices). About two legendary lightning titles fit without stretching; a
 * page of 24 runs about 7–10× smoother on a slow phone than without the budget.
 */
export const ambientMomentRate = 16;
/** Ambient single-letter jolts at once, page-wide (half on constrained devices). */
export const ambientJoltLimit = 4;
/** Titles less than this share visible are the first to thin out and the last to jolt. */
export const ambientVisibleShare = 0.5;

/**
 * A seeded "bag" of enabled signatures: every one plays before any repeats, and never
 * the same one twice in a row (unless only one is enabled).
 */
export interface SignatureBag {
  played: string[];
  last?: string;
}

export function drawSignature(
  bag: SignatureBag,
  enabled: readonly string[],
  random: Random,
): string | undefined {
  if (!enabled.length) return undefined;
  let pool = enabled.filter((id) => !bag.played.includes(id));
  if (!pool.length) {
    bag.played = [];
    pool = [...enabled];
  }
  const fresh = pool.filter((id) => id !== bag.last);
  const next = pick(random, fresh.length ? fresh : pool);
  noteSignature(bag, next);
  return next;
}

/** Records a signature that played by request, so the bag neither repeats it nor skips its turn. */
export function noteSignature(bag: SignatureBag, id: string) {
  if (!bag.played.includes(id)) bag.played.push(id);
  bag.last = id;
}

/** What a page remembers about one title (by its text) for this page load. */
export interface TitleMemory {
  /** When its last signature started and ended (ms, page clock); -Infinity if never. */
  lastStart: number;
  lastEnd: number;
  bag: SignatureBag;
  random: Random;
}

/** A title competing for the stage. */
export interface Contender {
  /** Memory key: the title text. */
  key: string;
  /** Share of the title currently visible (0–1). */
  ratio(): number;
  /** Starts the granted signature now. Returns false if it can no longer play. */
  begin(kind: SignatureKind, signature?: string): boolean;
  /** Another title's request took the stage: stop the signature now. */
  preempt(): void;
}

export interface StageCoordinator {
  /** The page clock (ms) used for cooldowns and rotation. */
  now(): number;
  memory(key: string): TitleMemory;
  /** Asks to play a signature. The decision follows within `decisionWindow` ms. */
  request(contender: Contender, kind: SignatureKind, signature?: string): void;
  /** The contender's signature ended (finished, cancelled or preempted). */
  ended(contender: Contender): void;
  /** Drops the contender's pending request and releases the stage if it holds it. */
  withdraw(contender: Contender): void;
  /** The contender playing now, if any. */
  readonly playing: Contender | null;
  /** Reserves a slot for a moment that moves several letters. Explicit ones always get one. */
  acquireLetters(owner: object, explicit: boolean): boolean;
  releaseLetters(owner: object): void;
  readonly letterMoments: number;
  /**
   * A title running its ambient program joins with its expected moment rate (per second).
   * Returns a function that leaves; paused, hidden and stopped titles have left.
   */
  joinAmbient(rate: number): () => void;
  /** The page's ambient moments per second if no cadence stretched. */
  readonly ambientLoad: number;
  /**
   * How much to stretch an ambient cadence now: 1 until the page's ambient load passes
   * its rate, then load ÷ rate, doubled for a title less than half visible.
   */
  ambientStretch(visible: number, lite: boolean): number;
  /**
   * Reserves one of the page's ambient jolt slots. A title less than half visible only
   * gets one while at least half the slots are free.
   */
  acquireJolt(owner: object, visible: number, lite: boolean): boolean;
  releaseJolt(owner: object): void;
  readonly jolts: number;
}

type AmbientKeys =
  | "joinAmbient"
  | "ambientLoad"
  | "ambientStretch"
  | "acquireJolt"
  | "releaseJolt"
  | "jolts";

export interface CoordinatorOptions {
  now?: () => number;
  window?: number;
  letterLimit?: number;
  ambientRate?: number;
  joltLimit?: number;
  /**
   * Shares this coordinator's ambient budget (load, stretch, jolts) with another one. A
   * scope keeps its own signature turns but always shares the page's ambient budget.
   */
  ambient?: StageCoordinator;
}

interface Pending {
  kind: SignatureKind;
  signature?: string;
  order: number;
}

export function createStageCoordinator({
  now = () => Date.now(),
  window = decisionWindow,
  letterLimit = letterMomentLimit,
  ambientRate = ambientMomentRate,
  joltLimit = ambientJoltLimit,
  ambient: shared,
}: CoordinatorOptions = {}): StageCoordinator {
  const memories = new Map<string, TitleMemory>();
  const pending = new Map<Contender, Pending>();
  const letters = new Set<object>();
  const jolts = new Set<object>();
  const ambient = new Set<{ rate: number }>();
  let load = 0;
  let current: { contender: Contender; kind: SignatureKind } | null = null;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let order = 0;

  const memory = (key: string) => {
    let entry = memories.get(key);
    if (!entry) {
      entry = {
        lastStart: -Infinity,
        lastEnd: -Infinity,
        bag: { played: [] },
        random: createRandom(hashString(key) ^ 0x5eed),
      };
      memories.set(key, entry);
    }
    return entry;
  };

  const release = (contender: Contender) => {
    if (current?.contender !== contender) return;
    current = null;
    memory(contender.key).lastEnd = now();
  };

  const decide = () => {
    timer = undefined;
    const requests = [...pending.entries()];
    pending.clear();
    // Explicit requests, then touches. Within a kind, the title that played least recently
    // on this page goes first, then the most visible one. The others lose: no backlog.
    requests.sort(([a, x], [b, y]) => {
      // Compared, not subtracted: two titles that never played are both -Infinity.
      const first = memory(a.key).lastStart;
      const second = memory(b.key).lastStart;
      const recency = first === second ? 0 : first < second ? -1 : 1;
      return rank[y.kind] - rank[x.kind] || recency || b.ratio() - a.ratio() || x.order - y.order;
    });
    let winner: Contender | undefined;
    for (const [contender, request] of requests) {
      if (winner) break;
      if (current) {
        if (current.contender === contender) continue;
        const outranks =
          rank[request.kind] > rank[current.kind] ||
          (request.kind === "explicit" && current.kind === "explicit");
        if (!outranks) continue;
      }
      // An explicit request takes the stage from a touch-started signature.
      const previous = current;
      if (previous) {
        release(previous.contender);
        previous.contender.preempt();
      }
      if (contender.begin(request.kind, request.signature)) {
        winner = contender;
        current = { contender, kind: request.kind };
        memory(contender.key).lastStart = now();
      }
    }
  };

  const coordinator: Omit<StageCoordinator, AmbientKeys> = {
    now,
    memory,
    request(contender, kind, signature) {
      const existing = pending.get(contender);
      if (!existing || rank[kind] >= rank[existing.kind])
        pending.set(contender, { kind, signature, order: (order += 1) });
      timer ??= setTimeout(decide, window);
    },
    ended: release,
    withdraw(contender) {
      pending.delete(contender);
      if (!pending.size && timer) {
        clearTimeout(timer);
        timer = undefined;
      }
      release(contender);
    },
    get playing() {
      return current?.contender ?? null;
    },
    acquireLetters(owner, explicit) {
      if (letters.has(owner)) return true;
      if (!explicit && letters.size >= letterLimit) return false;
      letters.add(owner);
      return true;
    },
    releaseLetters(owner) {
      letters.delete(owner);
    },
    get letterMoments() {
      return letters.size;
    },
  };
  // Copied as property descriptors, so the live getters (load, jolts) stay live.
  return Object.defineProperties(
    coordinator,
    Object.getOwnPropertyDescriptors(shared ? sharedAmbient(shared) : ownAmbient()),
  ) as StageCoordinator;

  function ownAmbient(): Pick<StageCoordinator, AmbientKeys> {
    return {
      joinAmbient(rate) {
        const member = { rate: Number.isFinite(rate) && rate > 0 ? rate : 0 };
        ambient.add(member);
        load += member.rate;
        return () => {
          if (!ambient.delete(member)) return;
          // An empty page starts from exactly zero, so rounding never accumulates.
          load = ambient.size ? Math.max(0, load - member.rate) : 0;
        };
      },
      get ambientLoad() {
        return load;
      },
      ambientStretch(visible, lite) {
        const stretch = Math.max(1, load / (lite ? ambientRate / 2 : ambientRate));
        return stretch > 1 && visible < ambientVisibleShare ? stretch * 2 : stretch;
      },
      acquireJolt(owner, visible, lite) {
        if (jolts.has(owner)) return true;
        const limit = lite ? Math.max(1, Math.floor(joltLimit / 2)) : joltLimit;
        if (jolts.size >= (visible < ambientVisibleShare ? limit / 2 : limit)) return false;
        jolts.add(owner);
        return true;
      },
      releaseJolt(owner) {
        jolts.delete(owner);
      },
      get jolts() {
        return jolts.size;
      },
    };
  }
}

/** Ambient methods that forward to another coordinator (a scope to its page). */
function sharedAmbient(target: StageCoordinator): Pick<StageCoordinator, AmbientKeys> {
  return {
    joinAmbient: (rate) => target.joinAmbient(rate),
    get ambientLoad() {
      return target.ambientLoad;
    },
    ambientStretch: (visible, lite) => target.ambientStretch(visible, lite),
    acquireJolt: (owner, visible, lite) => target.acquireJolt(owner, visible, lite),
    releaseJolt: (owner) => target.releaseJolt(owner),
    get jolts() {
      return target.jolts;
    },
  };
}

let page: StageCoordinator | undefined;
const scopes = new WeakMap<Element, StageCoordinator>();

/**
 * The coordinator for a title: its nearest `data-elemental-scope` ancestor's, or the
 * page's. A scope gives the titles inside it their own budget (a review grid that
 * replays several titles side by side); each scope still plays one signature at a time.
 */
export function coordinatorFor(element: Element | null): StageCoordinator {
  const scope = element?.closest("[data-elemental-scope]");
  const shared = (page ??= createStageCoordinator());
  if (!scope) return shared;
  let coordinator = scopes.get(scope);
  if (!coordinator) {
    coordinator = createStageCoordinator({ ambient: shared });
    scopes.set(scope, coordinator);
  }
  return coordinator;
}

/** Tests only: forget the page's coordinator and its memory. */
export function resetPageCoordinator() {
  page = undefined;
}

/**
 * Constrained devices render signatures lighter (no blur glow, half the fragments).
 * An ancestor's `data-elemental-performance="constrained"` or `"full"` decides; otherwise
 * the device does: four or fewer logical cores, or 4GB or less of memory.
 */
export function constrainedDevice(element: Element | null): boolean {
  const forced = element
    ?.closest("[data-elemental-performance]")
    ?.getAttribute("data-elemental-performance");
  if (forced === "constrained") return true;
  if (forced === "full") return false;
  if (typeof navigator === "undefined") return false;
  const { hardwareConcurrency } = navigator;
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
  return (!!hardwareConcurrency && hardwareConcurrency <= 4) || (!!memory && memory <= 4);
}

/**
 * Whether a title's ambient moments share the page budget. A review aid can switch it off
 * with `data-elemental-budget="off"` on an ancestor, to compare a crowded page with and
 * without the budget.
 */
export function ambientBudget(element: Element | null): boolean {
  const setting = element
    ?.closest("[data-elemental-budget]")
    ?.getAttribute("data-elemental-budget");
  return setting !== "off";
}
