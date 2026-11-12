import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import {
  ElementalTitle,
  type ElementalTitleEffect,
  type ElementalTitleIntensity,
  type ElementalTitleMomentRequest,
  type ElementalTitleMotion,
  type ElementalTitleShadow,
  type ElementalTitleSignature,
  type ElementalTitleSize,
} from "../../../packages/elemental-title/src/index";
import { ChoreographyLab } from "./choreography-lab";
import { Crowd } from "./crowd";
import { QuillInContext, QuillSignatureLab } from "./quill-signature-lab";
import {
  Block,
  Choice,
  elementSample,
  elements,
  engineElements,
  fontFaces,
  ranks,
  tiers,
  type FontFaceId,
} from "./shared";

const sections = [
  { id: "playground", label: "Playground" },
  { id: "gallery", label: "Elements & ranks" },
  { id: "moments", label: "Moments" },
  { id: "signatures", label: "Signatures" },
  { id: "context", label: "In context" },
  { id: "edge-cases", label: "Edge cases" },
] as const;

type Section = (typeof sections)[number]["id"];
const isSection = (value: string): value is Section => sections.some(({ id }) => id === value);

interface Settings {
  text: string;
  element: ElementalTitleEffect;
  color: string;
  intensity: ElementalTitleIntensity;
  motion: ElementalTitleMotion;
  size: ElementalTitleSize;
  shadow: ElementalTitleShadow;
  signatures: ElementalTitleSignature[];
}

const quill = [
  { id: "quill/stormwrit", name: "Stormwrit" },
  { id: "quill/true-north", name: "True North" },
] as const;

let requestKey = 0;
type GridElement = (typeof engineElements)[number]["element"];

export function App() {
  const [pageTheme, setPageTheme] = useState<"night" | "day">(() => {
    try {
      return localStorage.getItem("seihouse-theme") === "day" ? "day" : "night";
    } catch {
      return "night";
    }
  });
  const [fontId, setFontId] = useState<FontFaceId>("display-edge");
  const [section, setSection] = useState<Section>("playground");
  const [count, setCount] = useState(0);
  const [settings, setSettings] = useState<Settings>({
    text: "Kept Reading",
    element: "lightning",
    color: "",
    intensity: "legendary",
    motion: "ambient",
    size: "xl",
    shadow: "outlined",
    signatures: ["quill/stormwrit", "quill/true-north"],
  });
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const update = (patch: Partial<Settings>) => setSettings((value) => ({ ...value, ...patch }));
  const read = () => setCount((value) => value + 1);

  useEffect(() => {
    document.documentElement.dataset.pageTheme = pageTheme;
    try {
      localStorage.setItem("seihouse-theme", pageTheme);
    } catch {
      /* ignore storage errors */
    }
  }, [pageTheme]);

  useEffect(() => {
    const follow = () => {
      const hash = window.location.hash.slice(1);
      if (isSection(hash)) setSection(hash);
    };
    follow();
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  const openSection = (next: Section, focusTab = false) => {
    setSection(next);
    window.history.replaceState(null, "", `#${next}`);
    const btn = tabRefs.current[next];
    if (btn) {
      btn.scrollIntoView({ block: "nearest", inline: "nearest" });
      if (focusTab) btn.focus();
    }
  };

  const onTabKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const idx = sections.findIndex((item) => item.id === section);
    if (idx < 0) return;
    let nextIdx = -1;
    if (event.key === "ArrowRight") nextIdx = (idx + 1) % sections.length;
    else if (event.key === "ArrowLeft") nextIdx = (idx - 1 + sections.length) % sections.length;
    else if (event.key === "Home") nextIdx = 0;
    else if (event.key === "End") nextIdx = sections.length - 1;
    if (nextIdx >= 0) {
      event.preventDefault();
      openSection(sections[nextIdx].id, true);
    }
  };

  const activeFont = fontFaces.find((entry) => entry.id === fontId) ?? fontFaces[0];

  return (
    <div
      data-testid="elemental-title-preview"
      className="lab-shell"
      style={{ "--lab-title-font": activeFont.stack } as CSSProperties}
    >
      <header className="lab-topbar">
        <div className="lab-topbar-left">
          <a href="../../index.html" className="lab-brand" aria-label="SEIHouse Font Lab Home">
            <span className="lab-brand-mark" aria-hidden="true">
              S.
            </span>
            <span className="lab-brand-text">
              <strong>SEIHOUSE</strong>
              <span>FONT LAB</span>
            </span>
          </a>
          <a href="../../index.html#title-engine" className="lab-back-link">
            ← Back to Font Lab
          </a>
        </div>
        <nav className="lab-topbar-nav" aria-label="Title Engine workspaces">
          <a href="../lab/index.html">Display &amp; Living Lab ↗</a>
          <a href="../../site/display/index.html">Cuts Gallery ↗</a>
          <a href="../../packages/elemental-title/README.md">Package Guide ↗</a>
          <button
            type="button"
            className="lab-theme-toggle"
            onClick={() => setPageTheme((t) => (t === "night" ? "day" : "night"))}
          >
            {pageTheme === "night" ? "Day mode" : "Night mode"}
          </button>
        </nav>
      </header>

      <main className="lab-main">
        <section className="lab-hero">
          <div className="lab-hero-copy">
            <p className="lab-eyebrow">
              02 / THE TITLE ENGINE · <code>@seihouse/elemental-title</code> 0.1.0
            </p>
            <h1 className="lab-h1">Elemental Title Lab</h1>
            <p className="lab-lead">
              Name lettering with an element. Rank sets the color, the familiar sets the element,
              and bond tier sets the strength. Every element draws behind the letters so the name
              stays sharp in front.
            </p>
          </div>

          <div className="lab-font-bar" role="group" aria-label="SEIHouse typeface voice">
            <div className="lab-font-bar-head">
              <span className="lab-font-bar-label">SEIHouse typeface</span>
              <span className="lab-font-bar-note">{activeFont.note}</span>
            </div>
            <div className="lab-font-pills">
              {fontFaces.map((face) => (
                <button
                  key={face.id}
                  type="button"
                  aria-pressed={fontId === face.id}
                  onClick={() => setFontId(face.id)}
                  className="lab-font-pill"
                  data-font-choice={face.id}
                >
                  {face.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        <div className="lab-tabs-wrap">
          <div
            role="tablist"
            aria-label="Elemental Title sections"
            className="lab-tablist"
            onKeyDown={onTabKeyDown}
          >
            {sections.map(({ id, label }) => {
              const selected = section === id;
              return (
                <button
                  key={id}
                  ref={(node) => {
                    tabRefs.current[id] = node;
                  }}
                  type="button"
                  role="tab"
                  id={`tab-${id}`}
                  data-section={id}
                  aria-selected={selected}
                  tabIndex={selected ? 0 : -1}
                  className="lab-tab"
                  onClick={() => openSection(id)}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {sections.map(({ id }) => {
            const active = section === id;
            return (
              <div
                key={id}
                role="tabpanel"
                id={`panel-${id}`}
                aria-labelledby={`tab-${id}`}
                hidden={!active}
              >
                {active ? (
                  <div className="lab-tabpanel-inner">
                    {id === "playground" && (
                      <Playground
                        settings={settings}
                        update={update}
                        count={count}
                        onRead={read}
                        fontId={fontId}
                        onFontChange={setFontId}
                      />
                    )}
                    {id === "gallery" && <Gallery />}
                    {id === "moments" && <ChoreographyLab />}
                    {id === "signatures" && <QuillSignatureLab />}
                    {id === "context" && (
                      <div className="lab-stack-lg">
                        <QuillInContext />
                        <Crowd />
                      </div>
                    )}
                    {id === "edge-cases" && (
                      <EdgeCases settings={settings} count={count} onRead={read} />
                    )}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}

function Playground({
  settings,
  update,
  count,
  onRead,
  fontId,
  onFontChange,
}: {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  count: number;
  onRead: () => void;
  fontId: FontFaceId;
  onFontChange: (id: FontFaceId) => void;
}) {
  const [pickerColor, setPickerColor] = useState("#f6cf7f");
  const [strikeKey, setStrikeKey] = useState(0);
  const [request, setRequest] = useState<ElementalTitleMomentRequest>();
  const { text, element, color, intensity, motion, size, shadow, signatures } = settings;
  const lightning = element === "lightning";
  const headline = engineElements.find((entry) => entry.element === element);
  const signing = lightning && intensity === "legendary" && signatures.length > 0;
  const title = {
    element,
    color: color || undefined,
    intensity,
    motion,
    shadow,
    signatures: lightning ? signatures : undefined,
  };
  const toggleSignature = (id: ElementalTitleSignature, on: boolean) =>
    update({
      signatures: on
        ? quill.map((item) => item.id).filter((item) => item === id || signatures.includes(item))
        : signatures.filter((item) => item !== id),
    });

  return (
    <div className="lab-playground" data-elemental-budget="off">
      <div className="lab-playground-grid">
        <div className="lab-stage-column">
          <div className="lab-hero-canvases">
            <section
              aria-label="dark lettering"
              data-theme="dark"
              className="lab-theme-surface lab-hero-canvas lab-hero-canvas--dark"
            >
              <span className="lab-canvas-badge">Dark surface</span>
              <div className="lab-hero-title-box lab-title-voice">
                <ElementalTitle
                  as="h2"
                  {...title}
                  size={size}
                  strikeKey={strikeKey}
                  playMoment={request}
                  data-testid="elemental-hero"
                >
                  {text}
                </ElementalTitle>
              </div>
              <button type="button" className="lab-subtle-action" onClick={onRead}>
                Continue reading ({count})
              </button>
            </section>

            <section
              aria-label="light lettering"
              data-theme="light"
              className="lab-theme-surface lab-hero-canvas lab-hero-canvas--light"
            >
              <span className="lab-canvas-badge">Light surface</span>
              <div className="lab-hero-title-box lab-title-voice">
                <ElementalTitle
                  as="h2"
                  {...title}
                  size={size}
                  playMoment={element === "water" ? request : undefined}
                >
                  {text}
                </ElementalTitle>
              </div>
            </section>
          </div>

          <div className="lab-button-row lab-button-row--center">
            <button
              type="button"
              className="lab-btn"
              disabled={!headline}
              onClick={() => {
                if (!headline) return;
                if (lightning) setStrikeKey((key) => key + 1);
                else setRequest({ id: headline.moment, key: (requestKey += 1) });
              }}
            >
              Trigger {headline?.moment ?? "strike"}
            </button>
            <button
              type="button"
              className="lab-btn"
              disabled={!signing}
              title={
                signing ? undefined : "Signatures need lightning, legendary bond and one enabled"
              }
              onClick={() => setRequest({ id: "signature", key: (requestKey += 1) })}
            >
              Play signature
            </button>
          </div>

          <section
            aria-label="Bond tiers"
            data-theme="dark"
            className="lab-theme-surface lab-tier-strip"
          >
            {tiers.map((tier) => (
              <button
                key={tier}
                type="button"
                aria-pressed={intensity === tier}
                onClick={() => update({ intensity: tier })}
                className="lab-tier-card"
              >
                <span className="lab-tier-label">{tier}</span>
                <ElementalTitle
                  element={element}
                  color={color || undefined}
                  intensity={tier}
                  shadow="outlined"
                  motion={element === "water" ? motion : undefined}
                  playMoment={element === "water" ? request : undefined}
                  className="lab-title-voice lab-tier-sample"
                  aria-hidden="true"
                >
                  {text || "Kept Reading"}
                </ElementalTitle>
              </button>
            ))}
          </section>
        </div>

        <form
          aria-label="Playground controls"
          className="lab-panel-card lab-controls-form"
          onSubmit={(event) => event.preventDefault()}
        >
          <label className="lab-field">
            <span>Title text</span>
            <input
              className="lab-input"
              value={text}
              onChange={(event) => update({ text: event.target.value })}
            />
          </label>

          <label className="lab-field">
            <span>Typeface</span>
            <select
              className="lab-input"
              value={fontId}
              onChange={(event) => onFontChange(event.target.value as FontFaceId)}
            >
              {fontFaces.map((face) => (
                <option key={face.id} value={face.id}>
                  {face.label} — {face.note}
                </option>
              ))}
            </select>
          </label>

          <div className="lab-form-two-col">
            <label className="lab-field">
              <span>Element</span>
              <select
                className="lab-input"
                value={element}
                onChange={(event) =>
                  update({ element: event.target.value as ElementalTitleEffect })
                }
              >
                {elements.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label className="lab-field">
              <span>Bond tier</span>
              <select
                className="lab-input"
                value={intensity}
                onChange={(event) =>
                  update({ intensity: event.target.value as ElementalTitleIntensity })
                }
              >
                {tiers.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <fieldset className="lab-fieldset">
            <legend>Rank color</legend>
            <div className="lab-swatch-row">
              <button
                type="button"
                aria-pressed={!color}
                className="lab-chip"
                onClick={() => update({ color: "" })}
              >
                Element palette
              </button>
              {ranks.map((entry) => (
                <button
                  key={entry.rank}
                  type="button"
                  aria-pressed={color === entry.color}
                  className="lab-chip lab-swatch-chip"
                  onClick={() => update({ color: entry.color })}
                >
                  <span
                    aria-hidden="true"
                    className="lab-swatch-dot"
                    style={{ background: entry.color } as CSSProperties}
                  />
                  {entry.rank}
                </button>
              ))}
            </div>
            <div className="lab-color-custom-row">
              <label className="lab-field">
                <span>Title color (CSS)</span>
                <input
                  className="lab-input"
                  value={color}
                  placeholder="Element palette (default)"
                  onChange={(event) => update({ color: event.target.value })}
                />
              </label>
              <div className="lab-color-tools">
                <label htmlFor="elemental-color-picker" className="sr-only">
                  Pick title color
                </label>
                <input
                  id="elemental-color-picker"
                  type="color"
                  value={/^#[0-9a-f]{6}$/i.test(color) ? color : pickerColor}
                  className="lab-color-picker"
                  onChange={(event) => {
                    setPickerColor(event.target.value);
                    update({ color: event.target.value });
                  }}
                />
                <button
                  type="button"
                  className="lab-subtle-action"
                  onClick={() => update({ color: "" })}
                >
                  Reset
                </button>
              </div>
            </div>
          </fieldset>

          <div className="lab-form-three-col">
            <label className="lab-field">
              <span>Motion</span>
              <select
                className="lab-input"
                value={motion}
                onChange={(event) => update({ motion: event.target.value as ElementalTitleMotion })}
              >
                {["ambient", "hover", "burst"].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label className="lab-field">
              <span>Size</span>
              <select
                className="lab-input"
                value={size}
                onChange={(event) => update({ size: event.target.value as ElementalTitleSize })}
              >
                {["inherit", "sm", "md", "lg", "xl"].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label className="lab-field lab-field-span-mobile">
              <span>Shadow</span>
              <select
                className="lab-input"
                value={shadow}
                onChange={(event) => update({ shadow: event.target.value as ElementalTitleShadow })}
              >
                {["none", "soft", "outlined"].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {lightning ? (
            <fieldset className="lab-fieldset">
              <legend>Quill signatures (legendary bond)</legend>
              <div className="lab-check-row">
                {quill.map(({ id, name }) => (
                  <label key={id} className="lab-check-label">
                    <input
                      type="checkbox"
                      checked={signatures.includes(id)}
                      onChange={(event) => toggleSignature(id, event.target.checked)}
                    />
                    <span>{name}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ) : null}

          <p className="lab-meta-note">
            Touch the name to play a signature. Each bond tier grows brighter on hover or focus;
            reduced motion keeps the lettering still.
          </p>
        </form>
      </div>
    </div>
  );
}

function Gallery() {
  const [paletteTier, setPaletteTier] = useState<(typeof tiers)[number]>("rare");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [gridElement, setGridElement] = useState<GridElement>("lightning");
  const [strikeKey, setStrikeKey] = useState(0);
  const [momentKey, setMomentKey] = useState(0);
  const engine = engineElements.find((entry) => entry.element === gridElement)!;
  const lightningGrid = gridElement === "lightning";

  return (
    <div className="lab-stack-lg">
      <Block
        title="Elements"
        description="Each element in the dark and light themes, with its own palette."
        toolbar={
          <Choice label="Bond tier" value={paletteTier} options={tiers} onChange={setPaletteTier} />
        }
      >
        <div aria-label="Element palette" role="region" className="lab-palette-grid">
          {elements.map((value) => (
            <div key={value} className="lab-palette-pair">
              {(["dark", "light"] as const).map((scheme) => (
                <div
                  key={scheme}
                  data-theme={scheme}
                  className="lab-theme-surface lab-palette-cell"
                >
                  <p className="lab-micro-label">
                    {value} · {scheme}
                  </p>
                  <ElementalTitle
                    as="p"
                    element={value}
                    intensity={paletteTier}
                    shadow="outlined"
                    className="lab-title-voice lab-palette-sample"
                  >
                    {elementSample[value]}
                  </ElementalTitle>
                </div>
              ))}
            </div>
          ))}
        </div>
      </Block>

      <Block
        title="Ranks × bond tiers"
        testId="elemental-ranks"
        description={`${engine.label} at 20px. Rank sets the color, bond tier sets the strength. Each cell compares the default rank keyline with no outline; swipe across on narrow screens.`}
        toolbar={
          <>
            <Choice
              label="Element"
              value={gridElement}
              options={engineElements.map((entry) => entry.element)}
              onChange={setGridElement}
            />
            <Choice
              label="Theme"
              value={theme}
              options={["dark", "light"] as const}
              onChange={setTheme}
            />
            <button
              type="button"
              aria-label={`Trigger ${engine.moment} in ${theme} grid`}
              onClick={() =>
                lightningGrid ? setStrikeKey((key) => key + 1) : setMomentKey((key) => key + 1)
              }
              className="lab-btn"
            >
              Trigger {engine.moment}
            </button>
          </>
        }
      >
        <div
          data-theme={theme}
          data-testid={`elemental-phone-${theme}`}
          className="lab-theme-surface"
        >
          <div
            className="lab-table-wrap"
            role="region"
            aria-label={`${theme} rank by bond tier`}
            tabIndex={0}
          >
            <table className="lab-matrix lab-matrix--wide" data-testid={`elemental-grid-${theme}`}>
              <caption className="sr-only">
                Cultivator rank colors by familiar bond tier, {gridElement}, 20px. Each cell
                compares the default rank keyline with no outline.
              </caption>
              <thead>
                <tr>
                  <th scope="col" className="lab-matrix-rowhead">
                    Rank / bond tier
                  </th>
                  {tiers.map((tier) => (
                    <th key={tier} scope="col">
                      {tier}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ranks.map((entry) => (
                  <tr key={entry.rank} data-rank={entry.rank}>
                    <th scope="row" className="lab-matrix-rowhead">
                      {entry.rank}
                    </th>
                    {tiers.map((tier) => (
                      <td key={tier} data-tier={tier}>
                        <div className="lab-keyline-pair">
                          {(["outlined", "none"] as const).map((shadow) => (
                            <div key={shadow} className="lab-keyline-cell">
                              <p className="lab-micro-sub">
                                {shadow === "outlined" ? "Keyline" : "No outline"}
                              </p>
                              <ElementalTitle
                                as="p"
                                element={gridElement}
                                color={entry.color}
                                intensity={tier}
                                motion="hover"
                                shadow={shadow === "outlined" ? undefined : shadow}
                                strikeKey={lightningGrid ? strikeKey : undefined}
                                playMoment={
                                  !lightningGrid && momentKey
                                    ? { id: engine.moment, key: momentKey }
                                    : undefined
                                }
                                className="lab-title-voice"
                                style={{ fontSize: 20 }}
                              >
                                {entry.name}
                              </ElementalTitle>
                            </div>
                          ))}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Block>
    </div>
  );
}

function EdgeCases({
  settings,
  count,
  onRead,
}: {
  settings: Settings;
  count: number;
  onRead: () => void;
}) {
  const { element, motion } = settings;
  return (
    <Block
      title="Long names & inherited typography"
      description="These follow the playground's element, motion, and active SEIHouse typeface."
    >
      <div
        data-theme="dark"
        className="lab-theme-surface lab-edge-box lab-title-voice"
        data-testid="elemental-long-names"
      >
        <ElementalTitle as="p" element={element} motion={motion}>
          {"VeryLongUnbrokenReaderName".repeat(4)}
        </ElementalTitle>
        <ElementalTitle as="p" element={element} dir="auto">
          読者 Éowyn — حارس المكتبة
        </ElementalTitle>
        <div className="lab-wrapped-cell">
          <ElementalTitle as="p" element={element} motion={motion} intensity="legendary">
            Wayfinder of the Jagged Fjord
          </ElementalTitle>
        </div>
        <ElementalTitle as="p" data-testid="elemental-inherited">
          Plain inherited profile typography
        </ElementalTitle>
        <div>
          <button type="button" className="lab-btn" onClick={onRead}>
            <ElementalTitle element={element} motion={motion}>
              Read next
            </ElementalTitle>
          </button>
        </div>
        <p className="lab-meta-note lab-sans-reset">Chapters read: {count}</p>
      </div>
    </Block>
  );
}
