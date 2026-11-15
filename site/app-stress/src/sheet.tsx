/** Close-up checks for SEIHouse Noto in its "everywhere" job, beside its neighbours. */
import { useContext } from "react";
import { NAMES } from "./data";
import { CharsetContext, Checked, Name, R, useSettings } from "./parts";

const SIZES = [10, 11, 12, 13, 14, 16, 18];

export function Sheet({ world }: { world: "sea" | "sen" }) {
  const s = useSettings();
  const charset = useContext(CharsetContext);
  const meta = world === "sea"
    ? "Paper Lanterns · Mira Solace · 2026 · 8 songs, 28 min · 1,204,553 plays"
    : "The Quiet Library · Ilse Harrow · Ch. 128 · ★ 4.8 · 1.2M reads · 14 min";
  const missing = charset && s.metaFace === "seihouse"
    ? [...new Set([...NAMES.join("")].filter((c) => c !== " " && !charset.has(c)))]
    : [];

  return (
    <section className="sheet" aria-label="SEIHouse Noto close-up checks">
      <h2 className="sheet-h">SEIHouse Noto close-up</h2>
      <p className="sheet-note">
        The jobs the everywhere face carries alone. Sizes are CSS pixels × the text-size control
        ({Math.round(s.scale * 100)}%).
      </p>

      <div className="card">
        <h3>Size ladder: one metadata line, Regular and Medium</h3>
        {SIZES.map((px) => (
          <div className="ladder" key={px} style={{ fontSize: px * s.scale }}>
            <span className="px tnum">{px}</span>
            <R role="noto" className="ellipsis">{meta}</R>
            <R role="noto" className="ellipsis w5">{meta}</R>
          </div>
        ))}
      </div>

      <div className="grid2">
        <div className="card">
          <h3>Labels, badges and buttons</h3>
          <div className="caps-row">
            {["NOW PLAYING", "EXPLICIT", "NEW CHAPTER", "EXPANDED", "LOSSLESS", "UP NEXT"].map((t) => (
              <R role="noto" className="badge" key={t}>{t}</R>
            ))}
          </div>
          <div className="caps-row">
            <R role="noto" as="button" className="btn primary">Continue reading</R>
            <R role="noto" as="button" className="btn">Add to queue</R>
            <R role="noto" as="button" className="btn">Follow</R>
          </div>
          <R role="noto" as="p" className="overline">Settings · Audio · Downloads · Reading</R>
          <R role="noto" as="p" className="muted">Tab: Home · Albums · Novels · Library · Profile</R>
        </div>

        <div className="card">
          <h3>Numbers in their real jobs</h3>
          <table className="nums">
            <tbody>
              {[["Durations", "0:58  3:45  12:07  1:02:45"], ["Counts", "7  88  1,204  2,418,906  1.2M"],
                ["Chapters & dates", "Ch. 1 · Ch. 128 · Nov 14, 2026 · 11/14/26"], ["Prices & ratings", "$4.99 · €3,49 · £2 · ★ 4.8 · 97%"],
                ["Look-alikes", "Il1 | O0 | rn m | cl d | 5S | 8B"]].map(([k, v]) => (
                <tr key={k}><th>{k}</th><td><R role="noto" className="tnum">{v}</R></td></tr>
              ))}
            </tbody>
          </table>
          <R role="noto" as="p" className="muted">Track numbers and durations should stack in a column:</R>
          <div className="stack">
            {["1  0:58", "8  3:45", "11  12:07", "128  1:02:45"].map((v) => <R role="noto" key={v} className="tnum">{v}</R>)}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Names from distributors and readers, in many scripts</h3>
        <p className="sheet-note">
          {s.metaFace !== "seihouse"
            ? "Fallback marking is shown for SEIHouse Noto only."
            : missing.length
              ? <>Highlighted characters are not in SEIHouse Noto yet, so the browser borrows them from another font ({missing.length} distinct). This list is the coverage to-do.</>
              : <>Every character here is drawn by SEIHouse Noto.</>}
        </p>
        <div className="names">
          {NAMES.map((n) => <R role="noto" key={n}><Checked text={n} /></R>)}
        </div>
      </div>

      <div className="card">
        <h3>Do the faces sit together? Same size, same line</h3>
        <div className="harmony" style={{ fontSize: 22 * s.scale }}>
          <span className="guide" aria-hidden="true" />
          <R role="noto">Noto Hxg</R>
          <R role="sans">Sans Hxg</R>
          <R role="title" className={`static-cut cut-${s.cut.toLowerCase()}`}>Title Hxg</R>
          <Name>Elemental Hxg</Name>
          <R role="serif">Serif Hxg</R>
        </div>
        <p className="sheet-note">Capitals and x-heights should line up; differences jump out in mixed lines such as “Now playing: <i>title</i> by <i>artist</i>”.</p>
        <p className="mixed" style={{ fontSize: 15 * s.scale }}>
          <R role="noto">{world === "sea" ? "Now playing: " : "Continue reading "}</R>
          <R role="title" className={`static-cut cut-${s.cut.toLowerCase()}`}>{world === "sea" ? "Paper Lanterns" : "The Quiet Library"}</R>
          <R role="noto">{world === "sea" ? " by " : " by "}</R>
          <Name>{world === "sea" ? "Mira Solace" : "Ilse Harrow"}</Name>
          <R role="noto">{world === "sea" ? " · 1:24 / 3:45" : " · Ch. 127 · 14 min left"}</R>
        </p>
      </div>

      <div className="card">
        <h3>Long text in tight places</h3>
        {[300, 240, 180].map((w) => (
          <div className="trunc" key={w} style={{ width: w }}>
            <R role="noto" className="ellipsis tt">11:11 (Make a Wish, Then Make It Louder) [Expanded Edition]</R>
            <R role="noto" className="ellipsis tsub">Mira Solace, Søren Ålvik, Nguyễn Thảo Vy · 2026</R>
            <span className="px tnum">{w}px</span>
          </div>
        ))}
      </div>
    </section>
  );
}
