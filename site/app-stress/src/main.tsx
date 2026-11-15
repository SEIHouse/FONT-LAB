/** App-screen stress test: SEA and SEN screens set with the four SEIHouse type roles. */
import { StrictMode, useEffect, useMemo, useState, type CSSProperties } from "react";
import { createRoot } from "react-dom/client";
import { ROLES } from "./data";
import { CharsetContext, SettingsContext, type Settings } from "./parts";
import {
  AlbumScreen, ArtistScreen, NovelScreen, NowPlayingScreen, ProfileScreen, ReaderScreen, SearchScreen, WorldScreen,
} from "./screens";
import { Sheet } from "./sheet";

type World = "sea" | "sen";
const STORE = "seihouse-app-stress";
const DEFAULTS: Settings = {
  theme: "night", scale: 1, width: 390, cut: "Soft", living: true, element: "lightning",
  rarity: "rare", elementalFace: "noto", metaFace: "seihouse", roles: false,
};

function load(): Settings {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || "{}");
    return { ...DEFAULTS, ...saved };
  } catch {
    return DEFAULTS;
  }
}

function worldFromHash(): World {
  return location.hash === "#sen" ? "sen" : "sea";
}

function App() {
  const [s, setS] = useState<Settings>(load);
  const [world, setWorld] = useState<World>(worldFromHash);
  const [charset, setCharset] = useState<Set<string> | null>(null);
  const set = <K extends keyof Settings>(key: K, value: Settings[K]) => setS((prev) => ({ ...prev, [key]: value }));

  useEffect(() => {
    try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* storage is optional */ }
    document.documentElement.dataset.theme = s.theme;
  }, [s]);

  useEffect(() => {
    const onHash = () => setWorld(worldFromHash());
    addEventListener("hashchange", onHash);
    return () => removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    fetch("../../noto/studies/redraw/manifest.json")
      .then((r) => r.json())
      .then((m: { fonts: { characters: string }[] }) => setCharset(new Set([...m.fonts[0].characters])))
      .catch(() => setCharset(null));
  }, []);

  const night = s.theme === "night";
  const style = useMemo(() => ({
    "--s": String(s.scale),
    "--w": `${s.width}px`,
    "--noto": s.metaFace === "reference" ? '"Noto Sans Reference", sans-serif'
      : s.metaFace === "system" ? 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
      : night ? '"AS Noto Night", "AS Noto", sans-serif' : '"AS Noto", sans-serif',
    "--sans": night ? '"SEIHouse Sans Night", "SEIHouse Sans", sans-serif' : '"SEIHouse Sans", sans-serif',
    "--display": `"SEIHouse Display ${s.cut}", "SEIHouse Sans", sans-serif`,
  }) as CSSProperties, [s, night]);

  const go = (w: World) => { history.replaceState(null, "", `#${w}`); setWorld(w); };

  return (
    <SettingsContext.Provider value={s}>
      <CharsetContext.Provider value={charset}>
        <div className={`app world-${world} ${s.roles ? "show-roles" : ""}`} style={style}>
          <header className="head">
            <div className="head-top">
              <div>
                <p className="kicker">SEIHouse Font Lab · Stress test</p>
                <h1>The four faces, inside the app</h1>
              </div>
              <a className="back" href="../../index.html">← Font Lab</a>
            </div>
            <div className="worlds" role="group" aria-label="App">
              <button aria-pressed={world === "sea"} onClick={() => go("sea")}>
                <strong>SEA</strong><span>Expanded Albums · an album and its songs</span>
              </button>
              <button aria-pressed={world === "sen"} onClick={() => go("sen")}>
                <strong>SEN</strong><span>Expanded Novels · a novel and its world</span>
              </button>
            </div>
            <div className="controls">
              <Seg label="Theme" value={s.theme} options={[["day", "Day"], ["night", "Night"]]} onChange={(v) => set("theme", v)} />
              <Seg label="Text size" value={String(s.scale)} options={[["0.85", "85%"], ["1", "100%"], ["1.15", "115%"], ["1.3", "130%"]]} onChange={(v) => set("scale", Number(v))} />
              <Seg label="Phone width" value={String(s.width)} options={[["360", "360"], ["390", "390"], ["430", "430"]]} onChange={(v) => set("width", Number(v))} />
              <Seg label="Title cut" value={s.cut} options={[["Soft", "Soft"], ["Edge", "Edge"], ["Ink", "Ink"], ["Wide", "Wide"]]} onChange={(v) => set("cut", v)} />
              <Seg label="Title motion" value={s.living ? "on" : "off"} options={[["on", "Living"], ["off", "Still"]]} onChange={(v) => set("living", v === "on")} />
              <Pick label="Name element" value={s.element} options={["none", "lightning", "fire", "water", "frost", "poison", "celestial", "void"]} onChange={(v) => set("element", v)} />
              <Pick label="Name rarity" value={s.rarity} options={["common", "rare", "epic", "legendary"]} onChange={(v) => set("rarity", v)} />
              <Seg label="Name base face" value={s.elementalFace} options={[["noto", "Noto"], ["sans", "Sans"], ["display", "Title cut"]]} onChange={(v) => set("elementalFace", v)} />
              <Seg label="Everywhere face" value={s.metaFace} options={[["seihouse", "SEIHouse Noto"], ["reference", "Noto Sans"], ["system", "System UI"]]} onChange={(v) => set("metaFace", v)} />
              <Seg label="Show roles" value={s.roles ? "on" : "off"} options={[["off", "Off"], ["on", "On"]]} onChange={(v) => set("roles", v === "on")} />
            </div>
            <ul className="legend">
              {ROLES.map((r) => (
                <li key={r.id} className={`lg-${r.id}`}>
                  <span className="swatch" aria-hidden="true" />
                  <div><strong>{r.label}</strong> <span className="muted">— {r.face}</span><br />{r.job}</div>
                </li>
              ))}
            </ul>
            {s.metaFace !== "seihouse" && (
              <p className="notice">Comparison mode: everything in the SEIHouse Noto role is set in {s.metaFace === "reference" ? "Google Noto Sans" : "the system UI font"}. Switch back to judge SEIHouse Noto.</p>
            )}
          </header>

          <main>
            {world === "sea" ? (
              <div className="screens">
                <AlbumScreen />
                <NowPlayingScreen />
                <ArtistScreen />
                <SearchScreen />
              </div>
            ) : (
              <div className="screens">
                <NovelScreen />
                <ReaderScreen />
                <WorldScreen />
                <ProfileScreen />
              </div>
            )}
            <Sheet world={world} />
          </main>
          <footer className="foot">
            Fictional content. Fonts are the shipped Font Lab files: SEIHouse Noto Redraw 02, SEIHouse Sans,
            SEIHouse Display cuts through the Living Titles runtime, and the Elemental Title package. The serif is a stand-in.
          </footer>
        </div>
      </CharsetContext.Provider>
    </SettingsContext.Provider>
  );
}

function Seg<T extends string>({ label, value, options, onChange }: {
  label: string; value: string; options: [T, string][]; onChange: (value: T) => void;
}) {
  return (
    <fieldset className="seg">
      <legend>{label}</legend>
      <div>
        {options.map(([v, text]) => (
          <button key={v} aria-pressed={value === v} onClick={() => onChange(v)}>{text}</button>
        ))}
      </div>
    </fieldset>
  );
}

function Pick<T extends string>({ label, value, options, onChange }: {
  label: string; value: string; options: T[]; onChange: (value: T) => void;
}) {
  return (
    <label className="seg pick">
      <span className="legend-text">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value as T)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

createRoot(document.getElementById("app-stress-root")!).render(<StrictMode><App /></StrictMode>);
