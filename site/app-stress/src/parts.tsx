/** Shared building blocks: role wrappers, the living title, artist names and fallback marking. */
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { createTitlePlayer, createTitleScene, type CutName, type TitlePlayer } from "@seihouse/living-titles";
import {
  ElementalTitle,
  type ElementalTitleEffect,
  type ElementalTitleIntensity,
} from "../../../packages/elemental-title/src/index";
import type { Role } from "./data";

export interface Settings {
  theme: "day" | "night";
  scale: number;
  width: number;
  cut: CutName;
  living: boolean;
  element: ElementalTitleEffect;
  rarity: ElementalTitleIntensity;
  elementalFace: "noto" | "sans" | "display";
  metaFace: "seihouse" | "reference" | "system";
  roles: boolean;
}

export const SettingsContext = createContext<Settings | null>(null);
export const CharsetContext = createContext<Set<string> | null>(null);

export function useSettings(): Settings {
  const value = useContext(SettingsContext);
  if (!value) throw new Error("Settings missing");
  return value;
}

/** Text in one of the four type roles (plus the serif slot). */
export function R({ role, as: Tag = "span", className = "", children, title }: {
  role: Role; as?: "span" | "p" | "div" | "h1" | "h2" | "h3" | "li" | "button" | "strong" | "small";
  className?: string; children: ReactNode; title?: string;
}) {
  return <Tag className={`r-${role} ${className}`.trim()} data-role={role} title={title}>{children}</Tag>;
}

/** Marks characters SEIHouse Noto does not draw, so a fallback font is supplying them. */
export function Checked({ text }: { text: string }) {
  const charset = useContext(CharsetContext);
  const { metaFace } = useSettings();
  if (!charset || metaFace !== "seihouse") return <>{text}</>;
  const parts: ReactNode[] = [];
  let run = "";
  let key = 0;
  for (const ch of text) {
    if (ch === " " || charset.has(ch)) {
      run += ch;
      continue;
    }
    if (run) parts.push(run);
    run = "";
    parts.push(<mark key={key++} className="fb" title={`U+${ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")} falls back`}>{ch}</mark>);
  }
  if (run) parts.push(run);
  return <>{parts}</>;
}

/** An artist, author or reader name: Elemental Title on the chosen base face. */
export function Name({ children, element, rarity, size = "inherit", className = "" }: {
  children: string; element?: ElementalTitleEffect; rarity?: ElementalTitleIntensity;
  size?: "inherit" | "sm" | "md" | "lg" | "xl"; className?: string;
}) {
  const s = useSettings();
  return (
    <span className={`r-elemental base-${s.elementalFace} ${className}`.trim()} data-role="elemental">
      <ElementalTitle element={element ?? s.element} intensity={rarity ?? s.rarity} size={size}>
        {children}
      </ElementalTitle>
    </span>
  );
}

/** A title set by the Title Engine: animated Living Title, or the static Display cut. */
export function Title({ text, height, className = "" }: { text: string; height: number; className?: string }) {
  const s = useSettings();
  const art = useRef<HTMLDivElement>(null);
  const player = useRef<TitlePlayer | null>(null);
  const [state, setState] = useState<"static" | "preparing" | "live" | "error">("static");
  const color = s.theme === "night" ? "#f3e2b4" : "#3b2b12";

  useEffect(() => {
    if (!s.living) {
      setState("static");
      return;
    }
    const abort = new AbortController();
    setState("preparing");
    createTitleScene({ title: text, cut: s.cut, strength: 0.7, signal: abort.signal })
      .then((scene) => {
        if (abort.signal.aborted || !art.current) return;
        player.current = createTitlePlayer(art.current, scene, { color });
        setState("live");
      })
      .catch(() => {
        if (!abort.signal.aborted) setState("error");
      });
    return () => {
      abort.abort();
      player.current?.dispose();
      player.current = null;
      if (art.current) art.current.innerHTML = "";
    };
    // The colour is applied by the effect below, without rebuilding the scene.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, s.cut, s.living]);

  useEffect(() => {
    player.current?.setColor(color);
  }, [color]);

  return (
    <div className={`title-slot r-title ${className}`} data-role="title" style={{ height }} data-state={state}>
      <div ref={art} className="title-art" aria-hidden={state !== "live"} />
      {state !== "live" && (
        <h1 className={`title-text cut-${s.cut.toLowerCase()}`} style={{ fontSize: height * 0.72 }}>{text}</h1>
      )}
    </div>
  );
}

export function Phone({ label, children }: { label: string; children: ReactNode }) {
  return (
    <figure className="phone-wrap">
      <figcaption>{label}</figcaption>
      <div className="phone">
        <div className="status r-noto" data-role="noto">
          <span className="tnum">9:41</span>
          <span aria-hidden="true">▲ ◆ 87%</span>
        </div>
        {children}
      </div>
    </figure>
  );
}

export function Tabs({ active }: { active: string }) {
  const tabs = ["Home", "Albums", "Novels", "Library", "Profile"];
  return (
    <nav className="tabbar">
      {tabs.map((t) => (
        <R role="noto" key={t} className={t === active ? "on" : ""}>{t}</R>
      ))}
    </nav>
  );
}
