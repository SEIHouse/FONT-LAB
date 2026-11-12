import { useState } from "react";
import {
  ElementalTitle,
  type ElementalTitleEffect,
  type ElementalTitleMoment,
  type ElementalTitleMomentRequest,
} from "../../../packages/elemental-title/src/index";

const tiers = ["common", "rare", "epic", "legendary"] as const;
const sizes = [14, 16, 18, 20, 22, 36] as const;
const moments = ["strike", "crackle", "wave", "drip", "flow", "shine", "ripple"] as const;

/** Each subject keeps a rank color; the element only supplies the motion. */
const subjects: {
  id: string;
  label: string;
  element: ElementalTitleEffect;
  name: string;
  color: string;
}[] = [
  {
    id: "lightning",
    label: "Lightning",
    element: "lightning",
    name: "Kept Reading",
    color: "light-dark(#8a5a12, #f6cf7f)",
  },
  {
    id: "water",
    label: "Water",
    element: "water",
    name: "Kept Reading",
    color: "light-dark(#8a5a12, #f6cf7f)",
  },
  {
    id: "poison",
    label: "Poison (provisional)",
    element: "poison",
    name: "Kept Reading",
    color: "light-dark(#8a5a12, #f6cf7f)",
  },
  {
    id: "test-ripple",
    label: "Test ripple",
    element: "test-ripple" as ElementalTitleEffect,
    name: "Jade Current Sect",
    color: "light-dark(#1f7a4d, #86e3ae)",
  },
];

/** Wraps to two lines and carries overhanging ink: W, y, f, J, g, j. */
const longName = "Wayfinder of the Jagged Fjord";

interface Played {
  subject: string;
  moment: ElementalTitleMoment;
}

/** Review aid: fire each moment, slow it down, and read its timeline. */
export function ChoreographyLab() {
  const [request, setRequest] = useState<ElementalTitleMomentRequest>();
  const [slow, setSlow] = useState(false);
  const [size, setSize] = useState<(typeof sizes)[number]>(20);
  const [played, setPlayed] = useState<Played>();
  const listen = (subject: string) => (moment: ElementalTitleMoment) =>
    setPlayed({ subject, moment });
  const timeScale = slow ? 0.25 : 1;

  return (
    <section
      aria-labelledby="choreography-lab-title"
      data-testid="choreography-lab"
      className="lab-panel-card lab-stack"
    >
      <div className="lab-block-copy">
        <h2 id="choreography-lab-title" className="lab-h2">
          Choreography lab
        </h2>
        <p className="lab-desc">
          Fire each moment on every title below. Titles ignore moments their element does not have.
          Slow motion scales timers, SVG paths, and letter animations together.
        </p>
      </div>
      <div className="lab-button-row" role="group" aria-label="Moments">
        {moments.map((id) => (
          <button
            key={id}
            type="button"
            className="lab-btn"
            onClick={() => setRequest((previous) => ({ id, key: (previous?.key ?? 0) + 1 }))}
          >
            Play {id}
          </button>
        ))}
        <button
          type="button"
          className="lab-btn"
          aria-pressed={slow}
          onClick={() => setSlow((value) => !value)}
        >
          Slow motion 0.25×
        </button>
      </div>
      <div className="lab-button-row" role="group" aria-label="Name size">
        {sizes.map((value) => (
          <button
            key={value}
            type="button"
            className="lab-chip"
            aria-pressed={size === value}
            onClick={() => setSize(value)}
          >
            {value}px
          </button>
        ))}
      </div>
      {(["dark", "light"] as const).map((theme) => (
        <div
          key={theme}
          data-theme={theme}
          data-testid={`choreography-${theme}`}
          className="lab-theme-surface lab-stack"
        >
          <div
            className="lab-table-wrap"
            role="region"
            aria-label={`${theme} choreography by bond tier`}
            tabIndex={0}
          >
            <table
              className="lab-matrix"
              style={{ minWidth: size > 22 ? 1050 : 720 }}
            >
              <caption className="lab-matrix-caption">
                {theme} · {size}px names
              </caption>
              <thead>
                <tr>
                  <th scope="col" className="lab-matrix-rowhead">
                    Element / bond tier
                  </th>
                  {tiers.map((tier) => (
                    <th key={tier} scope="col">
                      {tier}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {subjects.map((subject) => (
                  <tr key={subject.id} data-subject={subject.id}>
                    <th scope="row" className="lab-matrix-rowhead">
                      {subject.label}
                    </th>
                    {tiers.map((tier) => (
                      <td key={tier} data-tier={tier}>
                        <ElementalTitle
                          as="p"
                          element={subject.element}
                          color={subject.color}
                          intensity={tier}
                          motion="hover"
                          playMoment={request}
                          timeScale={timeScale}
                          onMoment={listen(`${subject.label} · ${tier} · ${theme}`)}
                          className="lab-title-voice"
                          style={{ fontSize: size }}
                        >
                          {subject.name}
                        </ElementalTitle>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="lab-wrapped-grid" data-testid={`choreography-wrapped-${theme}`}>
            {subjects.map((subject) => (
              <div key={subject.id} className="lab-wrapped-cell">
                <p className="lab-micro-label">{subject.label} · legendary · wraps</p>
                <ElementalTitle
                  as="p"
                  element={subject.element}
                  color={subject.color}
                  intensity="legendary"
                  motion="hover"
                  playMoment={request}
                  timeScale={timeScale}
                  onMoment={listen(`${subject.label} · wrapped · ${theme}`)}
                  className="lab-title-voice"
                  style={{ fontSize: size }}
                >
                  {longName}
                </ElementalTitle>
              </div>
            ))}
          </div>
        </div>
      ))}
      <div data-testid="choreography-readout" className="lab-readout">
        <h3 className="lab-readout-title">Last timeline</h3>
        {played ? (
          <>
            <p data-testid="choreography-readout-moment">
              {played.moment.id} · {played.subject} · priority {played.moment.priority} ·{" "}
              {played.moment.duration}ms{played.moment.explicit ? " · requested" : ""}
            </p>
            <p data-testid="choreography-readout-beats">
              Beats:{" "}
              {played.moment.beats.length
                ? played.moment.beats.map((beat) => `${beat.label} @${beat.at}ms`).join(", ")
                : "none"}
            </p>
            <ol className="lab-readout-list" data-testid="choreography-readout-cues">
              {played.moment.cues.map((cue, index) => (
                <li key={index}>
                  {cue.type} @{Math.round(cue.at)}ms
                  {cue.beat ? ` (${cue.beat})` : ""}
                  {cue.glyphs ? ` · ${cue.glyphs.length} letters` : ""}
                </li>
              ))}
            </ol>
          </>
        ) : (
          <p>No moment yet. Play one above.</p>
        )}
      </div>
    </section>
  );
}
