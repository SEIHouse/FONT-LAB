import { useEffect, useRef, useState } from "react";
import { ElementalTitle } from "../../../packages/elemental-title/src/index";
import { Block, Choice, engineElements, ranks } from "./shared";

type CrowdElement = (typeof engineElements)[number]["element"];

const names = [
  "Lantern Scribe",
  "Tidewater Sect",
  "Cloudgate Pavilion",
  "Starlit Ledger",
  "Ash Willow",
  "Jade Current Sect",
  "Kept Reading",
  "Nine Heavens Pavilion",
  "Ember Ledger",
  "Harbor Owl",
  "Moss & Ink",
  "Cinder Verse",
  "Quiet Lantern",
  "Wayfinder",
  "Silver Brush",
  "Thunder Gate",
  "Pale River",
  "Ink Sovereign",
  "Storm Archive",
  "Hollow Bell",
  "North Pavilion",
  "Paper Crane",
  "Last Chapter",
  "Night Heron",
];

/**
 * A crowded page: 24 legendary names of one element at once, like a busy comment feed or a
 * leaderboard. The page budget stretches every name's cadence evenly and shares a few
 * letter jolts, preferring names in view. Switch it off to compare.
 */
export function Crowd() {
  const [budget, setBudget] = useState<"on" | "off">("on");
  const [element, setElement] = useState<CrowdElement>("lightning");
  return (
    <Block
      title="A crowded page"
      testId="elemental-crowd"
      description="24 legendary names at once, like a busy comment feed or leaderboard. On a crowded page every name plays its moments a little less often, evenly, and only a few letters move at a time, so scrolling stays smooth. Switch the page budget off to compare."
      toolbar={
        <>
          <Choice
            label="Element"
            value={element}
            options={engineElements.map((entry) => entry.element)}
            onChange={setElement}
          />
          <Choice
            label="Page budget"
            value={budget}
            options={["on", "off"] as const}
            onChange={setBudget}
          />
        </>
      }
    >
      <CrowdGrid key={`${budget}-${element}`} budget={budget} element={element} />
    </Block>
  );
}

function CrowdGrid({ budget, element }: { budget: "on" | "off"; element: CrowdElement }) {
  const grid = useRef<HTMLDivElement>(null);
  return (
    <div className="lab-stack-sm">
      <div
        ref={grid}
        data-theme="dark"
        data-elemental-budget={budget}
        data-testid="elemental-crowd-grid"
        className="lab-theme-surface lab-crowd-grid"
      >
        {names.map((name, index) => (
          <ElementalTitle
            key={name}
            as="p"
            element={element}
            intensity="legendary"
            color={ranks[index % ranks.length].color}
            className="lab-title-voice lab-crowd-name"
          >
            {name}
          </ElementalTitle>
        ))}
      </div>
      <Rate target={grid} element={element} />
    </div>
  );
}

function Rate({
  target,
  element,
}: {
  target: React.RefObject<HTMLElement | null>;
  element: CrowdElement;
}) {
  const rate = useMomentRate(target);
  return (
    <p className="lab-meta-note" data-testid="elemental-crowd-rate">
      {engineElements.find((entry) => entry.element === element)?.label} moments per second on this
      grid: {rate === null ? "measuring…" : rate}
    </p>
  );
}

function useMomentRate(root: React.RefObject<HTMLElement | null>) {
  const [rate, setRate] = useState<number | null>(null);
  useEffect(() => {
    const element = root.current;
    if (!element || typeof MutationObserver === "undefined") return;
    const frame = ".elemental-title__arcs--back .et-frame:not([data-slot='still'])";
    let frames = 0;
    const observer = new MutationObserver((records) => {
      for (const record of records)
        for (const node of record.addedNodes)
          if (node instanceof Element)
            frames += (node.matches(frame) ? 1 : 0) + node.querySelectorAll(frame).length;
    });
    observer.observe(element, { childList: true, subtree: true });
    const timer = window.setInterval(() => {
      setRate(frames);
      frames = 0;
    }, 1000);
    return () => {
      observer.disconnect();
      window.clearInterval(timer);
    };
  }, [root]);
  return rate;
}
