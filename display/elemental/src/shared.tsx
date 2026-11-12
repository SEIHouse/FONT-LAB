import type { ReactNode } from "react";
import type {
  ElementalTitleEffect,
  ElementalTitleIntensity,
} from "../../../packages/elemental-title/src/index";

export const elements = [
  "lightning",
  "water",
  "poison",
  "fire",
  "frost",
  "celestial",
  "void",
  "none",
] as const;

/** Elements that run on the engine, with their headline moment for review buttons. */
export const engineElements = [
  { element: "lightning", label: "Lightning", moment: "strike" },
  { element: "water", label: "Water", moment: "wave" },
  { element: "poison", label: "Poison (provisional)", moment: "drip" },
] as const;

export const tiers = ["common", "rare", "epic", "legendary"] as const satisfies readonly Exclude<
  ElementalTitleIntensity,
  "subtle" | "active"
>[];

/** SEIHouse typefaces available in Font Lab for testing Elemental Title across voices. */
export const fontFaces = [
  {
    id: "display-edge",
    label: "Display Edge",
    note: "Sharp faceted display",
    stack: '"SEIHouse Display Edge", "SEIHouse Sans", sans-serif',
  },
  {
    id: "display-soft",
    label: "Display Soft",
    note: "Warm rounded display",
    stack: '"SEIHouse Display Soft", "SEIHouse Sans", sans-serif',
  },
  {
    id: "display-ink",
    label: "Display Ink",
    note: "High-contrast notched ink",
    stack: '"SEIHouse Display Ink", "SEIHouse Sans", sans-serif',
  },
  {
    id: "display-wide",
    label: "Display Wide",
    note: "Extended banner display",
    stack: '"SEIHouse Display Wide", "SEIHouse Sans", sans-serif',
  },
  {
    id: "sans",
    label: "SEIHouse Sans 0.42",
    note: "Reader & UI humanist sans",
    stack: '"SEIHouse Sans", sans-serif',
  },
  {
    id: "noto",
    label: "SEIHouse Noto",
    note: "Balanced reading study",
    stack: '"SEIHouse Noto Balanced", "SEIHouse Sans", sans-serif',
  },
] as const;

export type FontFaceId = (typeof fontFaces)[number]["id"];

/** A name that reads well in each element, for galleries. */
export const elementSample: Record<ElementalTitleEffect, string> = {
  lightning: "Leader",
  water: "Still Waters",
  poison: "Nightshade",
  fire: "Kept Reading",
  frost: "Winter Sage",
  celestial: "Starlight",
  void: "Nightfall",
  none: "Reader",
};

/** DAO names keep their Cultivator Rank color; the element only supplies the effect. */
export const ranks = [
  { rank: "Mortal", name: "Ash Willow", color: "light-dark(#4b5563, #c9d1d9)" },
  { rank: "Qi Condensation", name: "Jade Current Sect", color: "light-dark(#1f7a4d, #86e3ae)" },
  { rank: "Core Formation", name: "Kept Reading", color: "light-dark(#8a5a12, #f6cf7f)" },
  { rank: "Nascent Soul", name: "Nine Heavens Pavilion", color: "light-dark(#6b3fb5, #d5b8ff)" },
] as const;

/** A small labelled group of toggle buttons for one choice. */
export function Choice<T extends string>({
  label,
  value,
  options,
  onChange,
  render = (option) => option,
}: {
  label: string;
  value: T;
  options: readonly T[];
  onChange: (value: T) => void;
  render?: (option: T) => ReactNode;
}) {
  return (
    <div role="group" aria-label={label} className="lab-choice-group">
      <span className="lab-choice-label">{label}</span>
      {options.map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={value === option}
          onClick={() => onChange(option)}
          className="lab-chip"
        >
          {render(option)}
        </button>
      ))}
    </div>
  );
}

/** A titled block inside a tab, with an optional toolbar on the right. */
export function Block({
  title,
  description,
  toolbar,
  children,
  testId,
}: {
  title: string;
  description?: ReactNode;
  toolbar?: ReactNode;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <section aria-label={title} data-testid={testId} className="lab-block">
      <div className="lab-block-head">
        <div className="lab-block-copy">
          <h2 className="lab-h2">{title}</h2>
          {description ? <p className="lab-desc">{description}</p> : null}
        </div>
        {toolbar ? <div className="lab-toolbar">{toolbar}</div> : null}
      </div>
      {children}
    </section>
  );
}
