import { memo, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import {
  ElementalTitle,
  type ElementalTitleMoment,
  type ElementalTitleMomentRequest,
  type ElementalTitleSignature,
} from "../../../packages/elemental-title/src/index";
import { ranks } from "./shared";

/** Quill's official signatures, with the copy a shop or the Familiar screen would show. */
const quillSignatures: {
  id: ElementalTitleSignature;
  name: string;
  line: string;
}[] = [
  {
    id: "quill/stormwrit",
    name: "Stormwrit",
    line: "Quill signs your name in crackling electric ink, ending in a fox-tail flourish.",
  },
  {
    id: "quill/true-north",
    name: "True North",
    line: "A compass star sweeps its needle beneath your name, then flares.",
  },
];

const wrappedName = "Wayfinder of the Jagged Fjord";

const comments: {
  name: string;
  color: string;
  size: number;
  element: "lightning" | "fire" | "none";
  intensity: "rare" | "epic" | "legendary";
  signatures?: ElementalTitleSignature[];
  text: string;
}[] = [
  {
    name: "Lantern Scribe",
    color: ranks[2].color,
    size: 18,
    element: "lightning",
    intensity: "legendary",
    signatures: ["quill/stormwrit", "quill/true-north"],
    text: "Chapter nine's storm scene gave me chills.",
  },
  {
    name: "Ash Willow",
    color: ranks[0].color,
    size: 16,
    element: "none",
    intensity: "rare",
    text: "Bookmarking this for the weekend.",
  },
  {
    name: "Tidewater Sect",
    color: ranks[1].color,
    size: 17,
    element: "lightning",
    intensity: "legendary",
    signatures: ["quill/true-north"],
    text: "The reviewer in me has notes, the reader in me has none.",
  },
  {
    name: "Ember Ledger",
    color: ranks[2].color,
    size: 16,
    element: "fire",
    intensity: "epic",
    text: "Who else reread the prologue after the twist?",
  },
  {
    name: "Cloudgate Pavilion",
    color: ranks[3].color,
    size: 18,
    element: "lightning",
    intensity: "legendary",
    signatures: ["quill/stormwrit"],
    text: "Signed, sealed, and waiting for the next arc.",
  },
  {
    name: "Quiet Lantern",
    color: ranks[0].color,
    size: 16,
    element: "lightning",
    intensity: "epic",
    signatures: ["quill/stormwrit"],
    text: "Epic bond, so no signature yet. Soon.",
  },
  {
    name: "Starlit Ledger",
    color: ranks[3].color,
    size: 17,
    element: "lightning",
    intensity: "legendary",
    signatures: ["quill/stormwrit", "quill/true-north"],
    text: "Quill would approve of this pacing.",
  },
  {
    name: "Moss & Ink",
    color: ranks[1].color,
    size: 16,
    element: "none",
    intensity: "rare",
    text: "Lovely prose in the tavern chapter.",
  },
  {
    name: "Harbor Owl",
    color: ranks[0].color,
    size: 17,
    element: "lightning",
    intensity: "rare",
    text: "Rare bond crew, checking in.",
  },
  {
    name: "Cinder Verse",
    color: ranks[2].color,
    size: 16,
    element: "fire",
    intensity: "legendary",
    text: "Fire familiar, still here for the lightning.",
  },
];

type Request = ElementalTitleMomentRequest | undefined;
interface Played {
  where: string;
  moment: ElementalTitleMoment;
}

function createBus() {
  const listeners = new Set<(played: Played) => void>();
  return {
    emit: (played: Played) => listeners.forEach((listener) => listener(played)),
    listen(listener: (played: Played) => void) {
      listeners.add(listener);
      return () => void listeners.delete(listener);
    },
  };
}
type Bus = ReturnType<typeof createBus>;

let requestKey = 0;
const nextRequest = (signature?: ElementalTitleSignature): ElementalTitleMomentRequest => ({
  id: "signature",
  key: (requestKey += 1),
  ...(signature ? { signature } : {}),
});

const report = (bus: Bus, where: string) => (moment: ElementalTitleMoment) => {
  if (moment.id === "signature") bus.emit({ where, moment });
};

function Readout({
  testId,
  bus,
  filter,
  children,
}: {
  testId: string;
  bus: Bus;
  filter?: (played: Played) => boolean;
  children?: (played: Played[]) => ReactNode;
}) {
  const [played, setPlayed] = useState<Played[]>([]);
  const accept = useRef(filter);
  useEffect(() => {
    accept.current = filter;
  });
  useEffect(
    () =>
      bus.listen((item) => {
        if (!accept.current || accept.current(item))
          setPlayed((previous) => [...previous.slice(-11), item]);
      }),
    [bus],
  );
  const last = played.at(-1);
  return (
    <div data-testid={testId} className="lab-readout">
      {last ? (
        <>
          <p data-testid={`${testId}-signature`}>
            {last.moment.signature?.name ?? last.moment.id} · {last.where} · {last.moment.duration}
            ms{last.moment.explicit ? " · requested" : ""}
          </p>
          <p data-testid={`${testId}-beats`}>
            Beats: {last.moment.beats.map((beat) => `${beat.label} @${beat.at}ms`).join(", ")}
          </p>
          <p>
            Cues:{" "}
            {last.moment.cues
              .map(
                (cue) =>
                  `${cue.type}${cue.beat ? ` (${cue.beat})` : ""} @${Math.round(cue.at)}ms${
                    cue.primitives ? ` [${cue.primitives.join(", ")}]` : ""
                  }`,
              )
              .join(" · ")}
          </p>
        </>
      ) : (
        <p>No signature yet.</p>
      )}
      {children?.(played)}
    </div>
  );
}

const ReviewTitle = memo(function ReviewTitle({
  id,
  name,
  color,
  where,
  request,
  timeScale,
  bus,
}: {
  id: ElementalTitleSignature;
  name: string;
  color: string;
  where: string;
  request: Request;
  timeScale: number;
  bus: Bus;
}) {
  return (
    <div data-elemental-scope="" data-signature-cell={id}>
      <ElementalTitle
        as="p"
        element="lightning"
        color={color}
        intensity="legendary"
        signatures={[id]}
        playMoment={request}
        timeScale={timeScale}
        onMoment={report(bus, where)}
        className="lab-title-voice"
        style={{ fontSize: 20 }}
      >
        {name}
      </ElementalTitle>
    </div>
  );
});

function Review({
  replay,
  timeScale,
  bus,
}: {
  replay: Record<ElementalTitleSignature, Request>;
  timeScale: number;
  bus: Bus;
}) {
  return (
    <>
      {(["dark", "light"] as const).map((theme) => (
        <div
          key={theme}
          data-theme={theme}
          data-testid={`quill-review-${theme}`}
          className="lab-theme-surface lab-stack"
        >
          <p className="lab-surface-eyebrow">{theme} · 20px names · legendary bond</p>
          <ul className="lab-rank-list" aria-label={`${theme} Quill signatures by rank`}>
            {ranks.map((entry) => (
              <li key={entry.rank} data-rank={entry.rank} className="lab-rank-row">
                <p className="lab-micro-label">{entry.rank}</p>
                <div className="lab-two-col-sm">
                  {quillSignatures.map(({ id, name }) => (
                    <div key={id} className="lab-sig-cell">
                      <p className="lab-micro-sub">{name}</p>
                      <ReviewTitle
                        id={id}
                        name={entry.name}
                        color={entry.color}
                        where={`${name} · ${entry.rank} · ${theme}`}
                        request={replay[id]}
                        timeScale={timeScale}
                        bus={bus}
                      />
                    </div>
                  ))}
                </div>
              </li>
            ))}
          </ul>
          <div className="lab-two-col-sm" data-testid={`quill-wrapped-${theme}`}>
            {quillSignatures.map(({ id, name }) => (
              <div key={id} className="lab-wrapped-cell">
                <p className="lab-micro-label">{name} · wraps</p>
                <ReviewTitle
                  id={id}
                  name={wrappedName}
                  color={ranks[2].color}
                  where={`${name} · wrapped · ${theme}`}
                  request={replay[id]}
                  timeScale={timeScale}
                  bus={bus}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}

function Profile({ timeScale, bus }: { timeScale: number; bus: Bus }) {
  const [request, setRequest] = useState<Request>();
  return (
    <article
      data-testid="quill-profile"
      data-theme="dark"
      aria-label="Profile header"
      className="lab-profile-card"
    >
      <span aria-hidden="true" className="lab-avatar">
        K
      </span>
      <div className="lab-profile-copy">
        <ElementalTitle
          as="h3"
          element="lightning"
          color={ranks[2].color}
          intensity="legendary"
          signatures={["quill/stormwrit", "quill/true-north"]}
          playMoment={request}
          timeScale={timeScale}
          onMoment={report(bus, "Profile")}
          className="lab-title-voice"
          style={{ fontSize: 28 }}
        >
          Kept Reading
        </ElementalTitle>
        <p className="lab-meta-note">Core Formation · Quill, legendary bond</p>
      </div>
      <button
        type="button"
        className="lab-btn lab-profile-action"
        onClick={() => setRequest(nextRequest())}
      >
        Finish a chapter with Quill
      </button>
    </article>
  );
}

function Look({ timeScale, bus }: { timeScale: number; bus: Bus }) {
  const [enabled, setEnabled] = useState<ElementalTitleSignature[]>([
    "quill/stormwrit",
    "quill/true-north",
  ]);
  const [request, setRequest] = useState<Request>();
  return (
    <article
      data-testid="quill-look"
      aria-label="Familiar look preview"
      className="lab-panel-card lab-stack-sm"
    >
      <h4 className="lab-h3">Familiar · Look</h4>
      <p className="lab-desc">Quill, an indigo celestial archive fox. Lightning, legendary bond.</p>
      <div data-theme="dark" className="lab-theme-surface lab-stage-well">
        <ElementalTitle
          as="p"
          element="lightning"
          color={ranks[3].color}
          intensity="legendary"
          signatures={enabled}
          playMoment={request}
          timeScale={timeScale}
          onMoment={report(bus, "Look")}
          className="lab-title-voice"
          style={{ fontSize: 22 }}
        >
          Nine Heavens Pavilion
        </ElementalTitle>
      </div>
      <div className="lab-button-row" role="group" aria-label="Enabled signatures">
        {quillSignatures.map(({ id, name }) => (
          <button
            key={id}
            type="button"
            className="lab-chip"
            aria-pressed={enabled.includes(id)}
            onClick={() =>
              setEnabled((previous) =>
                previous.includes(id)
                  ? previous.filter((item) => item !== id)
                  : quillSignatures
                      .map((item) => item.id)
                      .filter((item) => item === id || previous.includes(item)),
              )
            }
          >
            {name} enabled
          </button>
        ))}
        <button type="button" className="lab-btn" onClick={() => setRequest(nextRequest())}>
          Preview signature
        </button>
      </div>
    </article>
  );
}

function Shop({ timeScale, bus }: { timeScale: number; bus: Bus }) {
  const [request, setRequest] = useState<Request>();
  return (
    <article
      data-testid="quill-shop"
      aria-label="Signature shop"
      className="lab-panel-card lab-stack-sm"
    >
      <h4 className="lab-h3">Signature shop · Quill</h4>
      <div data-theme="dark" className="lab-theme-surface lab-stage-well">
        <ElementalTitle
          as="p"
          element="lightning"
          color={ranks[1].color}
          intensity="legendary"
          signatures={["quill/stormwrit", "quill/true-north"]}
          playMoment={request}
          timeScale={timeScale}
          onMoment={report(bus, "Shop")}
          className="lab-title-voice"
          style={{ fontSize: 22 }}
        >
          Jade Current Sect
        </ElementalTitle>
      </div>
      <ul className="lab-shop-list">
        {quillSignatures.map(({ id, name, line }) => (
          <li key={id} className="lab-shop-item">
            <span className="lab-shop-copy">
              <strong>{name}</strong>
              <span>{line} Legendary bond.</span>
            </span>
            <button
              type="button"
              className="lab-btn"
              aria-label={`Preview ${name}`}
              onClick={() => setRequest(nextRequest(id))}
            >
              Preview
            </button>
          </li>
        ))}
      </ul>
    </article>
  );
}

function Rotation({ timeScale, bus }: { timeScale: number; bus: Bus }) {
  const [request, setRequest] = useState<Request>();
  return (
    <article
      data-testid="quill-rotation"
      aria-label="Signature rotation"
      className="lab-panel-card lab-stack-sm"
    >
      <h4 className="lab-h3">Rotation · both signatures enabled</h4>
      <p className="lab-desc">
        Each press plays the next signature from a seeded bag: every enabled signature plays before
        any repeats, and never the same one twice in a row.
      </p>
      <div data-theme="dark" className="lab-theme-surface lab-rotation-bar">
        <ElementalTitle
          as="p"
          element="lightning"
          color={ranks[2].color}
          intensity="legendary"
          signatures={["quill/stormwrit", "quill/true-north"]}
          playMoment={request}
          timeScale={timeScale}
          onMoment={report(bus, "Rotation")}
          className="lab-title-voice"
          style={{ fontSize: 20 }}
        >
          Starlit Archive
        </ElementalTitle>
        <button type="button" className="lab-btn" onClick={() => setRequest(nextRequest())}>
          Play next signature
        </button>
      </div>
      <Readout
        testId="quill-rotation-readout"
        bus={bus}
        filter={(item) => item.where === "Rotation"}
      >
        {(played) => (
          <ol data-testid="quill-rotation-order" className="lab-readout-list">
            {played.map((item, index) => (
              <li key={index}>{item.moment.signature?.name}</li>
            ))}
          </ol>
        )}
      </Readout>
    </article>
  );
}

function Comments({ timeScale, bus }: { timeScale: number; bus: Bus }) {
  const [request, setRequest] = useState<Request>();
  return (
    <article
      data-testid="quill-comments"
      aria-label="Comments"
      className="lab-panel-card lab-stack-sm"
    >
      <div className="lab-block-head">
        <h4 className="lab-h3">Comments · 10 readers, 4 legendary Quill owners</h4>
        <button type="button" className="lab-btn" onClick={() => setRequest(nextRequest())}>
          Every Quill owner requests at once
        </button>
      </div>
      <p className="lab-desc">
        Touch a name to see its signature. The button stands in for an app action shared by every
        Quill owner at once: only one signs, and the next press goes to whoever signed least
        recently.
      </p>
      <ul data-theme="dark" className="lab-theme-surface lab-comment-list">
        {comments.map((comment) => (
          <li key={comment.name} className="lab-comment-item" data-commenter={comment.name}>
            <ElementalTitle
              as="p"
              element={comment.element}
              color={comment.color}
              intensity={comment.intensity}
              signatures={comment.signatures}
              playMoment={comment.signatures ? request : undefined}
              timeScale={timeScale}
              onMoment={report(bus, comment.name)}
              className="lab-title-voice"
              style={{ fontSize: comment.size }}
            >
              {comment.name}
            </ElementalTitle>
            <p className="lab-comment-body">{comment.text}</p>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function QuillSignatureLab() {
  const [bus] = useState(createBus);
  const [slow, setSlow] = useState(false);
  const [accent, setAccent] = useState(true);
  const [constrained, setConstrained] = useState(false);
  const [replay, setReplay] = useState<Record<ElementalTitleSignature, Request>>({
    "quill/stormwrit": undefined,
    "quill/true-north": undefined,
  });
  const timeScale = slow ? 0.25 : 1;
  const replayAll = (ids: ElementalTitleSignature[]) =>
    setReplay((previous) => {
      const updated = { ...previous };
      for (const id of ids) updated[id] = nextRequest();
      return updated;
    });
  const inReview = (item: Played) => / · (dark|light)$/.test(item.where);

  return (
    <section
      aria-labelledby="quill-signature-title"
      data-testid="quill-signature-lab"
      data-elemental-performance={constrained ? "constrained" : "full"}
      className="lab-stack"
      style={accent ? undefined : ({ "--et-signature-accent": "none" } as CSSProperties)}
    >
      <div className="lab-block-copy">
        <h2 id="quill-signature-title" className="lab-h2">
          Quill familiar signatures
        </h2>
        <p className="lab-desc">
          Quill&apos;s two official signatures at legendary bond: <strong>Stormwrit</strong> (Quill
          signs your name) and <strong>True North</strong> (a compass star). Touch a name (hover,
          tap, or keyboard focus) to play it, or use the buttons below. The lightning keeps running
          underneath. See{" "}
          <a href="../../docs/FAMILIAR-SIGNATURES.md" className="lab-inline-link">
            Familiar Signatures design brief ↗
          </a>
          .
        </p>
      </div>
      <div className="lab-toolbar">
        <div className="lab-button-row" role="group" aria-label="Replay">
          <button
            type="button"
            className="lab-btn"
            onClick={() => replayAll(["quill/stormwrit", "quill/true-north"])}
          >
            Replay both
          </button>
          {quillSignatures.map(({ id, name }) => (
            <button key={id} type="button" className="lab-btn" onClick={() => replayAll([id])}>
              Replay {name}
            </button>
          ))}
        </div>
        <div className="lab-button-row" role="group" aria-label="Review options">
          <button
            type="button"
            className="lab-chip"
            aria-pressed={slow}
            onClick={() => setSlow((value) => !value)}
          >
            Slow motion 0.25×
          </button>
          <button
            type="button"
            className="lab-chip"
            aria-pressed={accent}
            onClick={() => setAccent((value) => !value)}
          >
            Gold accent
          </button>
          <button
            type="button"
            className="lab-chip"
            aria-pressed={constrained}
            title="No blur glow and half the fragments, matching 4-core / 4GB mobile devices"
            onClick={() => setConstrained((value) => !value)}
          >
            Constrained device
          </button>
        </div>
      </div>
      <div className="lab-two-col-xl">
        <Review replay={replay} timeScale={timeScale} bus={bus} />
      </div>
      <Readout testId="quill-review-readout" bus={bus} filter={inReview} />
      <div className="lab-two-col-lg">
        <Look timeScale={timeScale} bus={bus} />
        <Shop timeScale={timeScale} bus={bus} />
        <div className="lab-span-full">
          <Rotation timeScale={timeScale} bus={bus} />
        </div>
      </div>
    </section>
  );
}

export function QuillInContext() {
  const [bus] = useState(createBus);
  return (
    <section
      aria-labelledby="quill-context-title"
      data-testid="quill-in-context"
      className="lab-stack"
    >
      <div className="lab-block-copy">
        <h2 id="quill-context-title" className="lab-h2">
          Quill owners in context
        </h2>
        <p className="lab-desc">
          One signature on screen at a time. It plays when someone touches a name or when the app
          asks (an action tied to Quill, such as finishing a chapter); the app&apos;s requests win,
          and among names asking at once the one that signed least recently goes next.
        </p>
      </div>
      <Profile timeScale={1} bus={bus} />
      <Comments timeScale={1} bus={bus} />
      <Readout testId="quill-page-readout" bus={bus}>
        {(played) => (
          <p data-testid="quill-page-turns">
            Turns: {played.map((item) => item.where).join(" → ") || "none"}
          </p>
        )}
      </Readout>
    </section>
  );
}
