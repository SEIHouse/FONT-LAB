/** The SEA (music) and SEN (novel) app screens, each set with the same four type roles. */
import { ALBUM, CHAPTER, LIBRARY, LYRICS, NOVEL, SETTINGS } from "./data";
import { Checked, Name, Phone, R, Tabs, Title, useSettings } from "./parts";

/* ───────────────────────── SEA · SEIHouse Expanded Albums ───────────────────────── */

export function AlbumScreen() {
  return (
    <Phone label="SEA · Album">
      <div className="topbar"><R role="noto">‹ Albums</R><R role="noto" className="pill">Expanded</R></div>
      <div className="cover sea-cover" aria-hidden="true"><span className="cover-mark">✦</span></div>
      <Title text={ALBUM.title} height={46} className="center" />
      <div className="center byline"><Name size="md">{ALBUM.artist}</Name></div>
      <R role="noto" as="p" className="meta center">Album · {ALBUM.year} · {ALBUM.tracks.length} songs, {ALBUM.minutes}</R>
      <div className="actions">
        <R role="noto" as="button" className="btn primary">▶ Play</R>
        <R role="noto" as="button" className="btn">⤮ Shuffle</R>
        <R role="noto" as="button" className="btn icon" title="Save">♡</R>
      </div>
      <ol className="tracks">
        {ALBUM.tracks.map((t) => (
          <li key={t.n} className={t.n === 1 ? "playing" : ""}>
            <R role="noto" className="tn tnum">{t.n === 1 ? "♪" : t.n}</R>
            <div className="tbody">
              <R role="noto" className="tt ellipsis">{t.title}</R>
              <div className="tsub ellipsis">
                {t.explicit && <R role="noto" className="badge">E</R>}
                {t.expanded && <R role="noto" className="badge exp">EXPANDED</R>}
                <Name size="inherit" rarity="common">{ALBUM.artist}</Name>
                {t.feat && <><R role="noto"> feat. </R><Name rarity="common">{t.feat}</Name></>}
              </div>
            </div>
            <R role="noto" className="tdur tnum">{t.time}</R>
          </li>
        ))}
      </ol>
      <R role="noto" as="p" className="fine">℗ {ALBUM.year} {ALBUM.label} · Released November 14, {ALBUM.year}</R>
      <section className="liner">
        <R role="noto" as="h3" className="overline">Liner notes</R>
        <R role="serif" as="p">{ALBUM.liner}</R>
      </section>
      <Tabs active="Albums" />
    </Phone>
  );
}

export function NowPlayingScreen() {
  const t = ALBUM.tracks[0];
  return (
    <Phone label="SEA · Now playing">
      <div className="topbar"><R role="noto">⌄</R><R role="noto" className="overline">Playing from album</R><R role="noto">⋯</R></div>
      <div className="cover sea-cover big" aria-hidden="true"><span className="cover-mark">✦</span></div>
      <div className="np-head">
        <div>
          <R role="noto" as="h2" className="np-title">{t.title}</R>
          <Name size="md">{ALBUM.artist}</Name>
        </div>
        <R role="noto" className="btn icon" title="Save">♥</R>
      </div>
      <div className="progress"><span style={{ width: "37%" }} /></div>
      <div className="times"><R role="noto" className="tnum">1:24</R><R role="noto" className="tnum">−2:21</R></div>
      <div className="transport" aria-hidden="true"><span>⤮</span><span>⏮</span><span className="big">⏸</span><span>⏭</span><span>↻</span></div>
      <div className="np-tags">
        <R role="noto" className="badge exp">EXPANDED</R><R role="noto" className="badge">LOSSLESS</R><R role="noto" className="badge">24-BIT · 96 kHz</R>
      </div>
      <section className="lyrics">
        <R role="noto" as="h3" className="overline">Lyrics</R>
        {LYRICS.map((line, i) => (
          <R role="sans" as="p" key={i} className={i === 1 ? "lyric now" : "lyric"}>{line}</R>
        ))}
      </section>
    </Phone>
  );
}

export function ArtistScreen() {
  return (
    <Phone label="SEA · Artist">
      <div className="artist-hero sea-cover" aria-hidden="true" />
      <div className="artist-head">
        <Name size="xl" rarity="legendary">{ALBUM.artist}</Name>
        <R role="noto" as="p" className="meta">2,847,301 monthly listeners · ✓ Verified</R>
        <div className="actions left">
          <R role="noto" as="button" className="btn primary">Follow</R>
          <R role="noto" as="button" className="btn icon">▶</R>
        </div>
      </div>
      <R role="noto" as="h3" className="section-h">Popular</R>
      <ol className="tracks compact">
        {ALBUM.tracks.slice(0, 4).map((t, i) => (
          <li key={t.n}>
            <R role="noto" className="tn tnum">{i + 1}</R>
            <div className="tbody">
              <R role="noto" className="tt ellipsis">{t.title}</R>
              <R role="noto" className="tsub tnum">{t.plays} plays</R>
            </div>
            <R role="noto" className="tdur tnum">{t.time}</R>
          </li>
        ))}
      </ol>
      <R role="noto" as="h3" className="section-h">Discography</R>
      <div className="shelf">
        {[["Paper Lanterns", "2026 · Album"], ["Ivy on the Overpass", "2025 · Single"], ["Wolves Wait", "2023 · EP"]].map(([n, k]) => (
          <div className="shelf-item" key={n}>
            <div className="cover sea-cover small" aria-hidden="true" />
            <R role="noto" className="ellipsis st">{n}</R>
            <R role="noto" className="ellipsis sk">{k}</R>
          </div>
        ))}
      </div>
      <Tabs active="Albums" />
    </Phone>
  );
}

export function SearchScreen() {
  return (
    <Phone label="SEA · Search & library">
      <div className="search r-noto" data-role="noto"><span aria-hidden="true">⌕</span> Search artists, songs, albums</div>
      <div className="chips">
        {["All", "Albums", "Singles", "Expanded", "Downloaded ✓"].map((c, i) => (
          <R role="noto" key={c} className={i === 0 ? "chip on" : "chip"}>{c}</R>
        ))}
      </div>
      <ul className="lib">
        {LIBRARY.map((item) => (
          <li key={item.title}>
            <div className="cover sea-cover tiny" aria-hidden="true" />
            <div className="tbody">
              <R role="noto" className="tt ellipsis"><Checked text={item.title} /></R>
              <div className="tsub ellipsis">
                <R role="noto">{item.kind} · </R>
                <Name rarity="common">{item.who}</Name>
              </div>
            </div>
          </li>
        ))}
      </ul>
      <div className="toast r-noto" data-role="noto">✓ Added “Paper Lanterns” to Library</div>
      <Tabs active="Library" />
    </Phone>
  );
}

/* ───────────────────────── SEN · SEIHouse Expanded Novels ───────────────────────── */

export function NovelScreen() {
  return (
    <Phone label="SEN · Novel">
      <div className="topbar"><R role="noto">‹ Novels</R><R role="noto">⋯</R></div>
      <div className="book-row">
        <div className="cover sen-cover book" aria-hidden="true"><span className="cover-mark">❦</span></div>
        <div className="book-meta">
          <R role="noto" className="badge">FANTASY</R>
          <R role="noto" as="p" className="meta">{NOVEL.status}</R>
          <R role="noto" as="p" className="stats tnum">★ {NOVEL.rating} · {NOVEL.reads} reads · {NOVEL.chapters} ch.</R>
        </div>
      </div>
      <Title text={NOVEL.title} height={44} className="center" />
      <div className="center byline"><R role="noto" className="by">by </R><Name size="md" element="celestial">{NOVEL.author}</Name></div>
      <div className="actions">
        <R role="noto" as="button" className="btn primary">Continue · Ch. 127</R>
        <R role="noto" as="button" className="btn icon">＋</R>
      </div>
      <R role="sans" as="p" className="synopsis">{NOVEL.synopsis}</R>
      <section className="liner">
        <R role="noto" as="h3" className="overline">Editor’s note</R>
        <R role="serif" as="p">{NOVEL.editor}</R>
      </section>
      <div className="list-head"><R role="noto" as="h3" className="section-h">Chapters</R><R role="noto" className="muted">Newest ⇅</R></div>
      <ul className="chapters">
        {NOVEL.list.map((c) => (
          <li key={c.n}>
            <R role="noto" className="cn tnum">{c.n}</R>
            <div className="tbody">
              <R role="noto" className="tt ellipsis">{c.name}</R>
              <R role="noto" className="tsub">{c.date} · {c.mins}{c.isNew && <span className="badge new">NEW</span>}</R>
            </div>
          </li>
        ))}
      </ul>
      <Tabs active="Novels" />
    </Phone>
  );
}

export function ReaderScreen() {
  return (
    <Phone label="SEN · Reading a chapter">
      <div className="topbar reader-bar"><R role="noto">‹</R><R role="noto" className="ellipsis">The Quiet Library</R><R role="noto">Aa</R></div>
      <R role="noto" as="p" className="overline center">Chapter {CHAPTER.number}</R>
      <R role="noto" as="h2" className="ch-title center">{CHAPTER.name}</R>
      <article className="chapter">
        {CHAPTER.body.map((p, i) => <R role="sans" as="p" key={i}>{p}</R>)}
      </article>
      <div className="reader-progress"><R role="noto" className="tnum">p. 3 of 11</R><div className="progress"><span style={{ width: "27%" }} /></div><R role="noto" className="tnum">27%</R></div>
      <div className="list-head"><R role="noto" as="h3" className="section-h">Comments <span className="muted tnum">· 2,318</span></R><R role="noto" className="muted">Top ▾</R></div>
      <ul className="comments">
        {CHAPTER.comments.map((c) => (
          <li key={c.name}>
            <div className="avatar" aria-hidden="true">{c.name.slice(0, 1)}</div>
            <div className="tbody">
              <div className="c-head"><Name element={c.el as never} rarity={c.rank as never}>{c.name}</Name><R role="noto" className="muted tnum"> · {c.time}</R></div>
              <R role="noto" as="p" className="c-text">{c.text}</R>
              <R role="noto" className="c-act tnum">♡ {c.likes} · Reply</R>
            </div>
          </li>
        ))}
      </ul>
    </Phone>
  );
}

export function WorldScreen() {
  const places = [
    ["Wyrmhollow", "The library-city. Seven floors above ground, none below — officially."],
    ["The Fifth Floor", "Sealed since the Year of Ash (Y.A. 412). Do not borrow."],
    ["Lantern Quay", "Where unread letters are set afloat at dusk."],
  ];
  const people = [
    { name: "Wren Ashby", role: "Last librarian", el: "frost" },
    { name: "Ilse Harrow", role: "Author · Narrator", el: "celestial" },
    { name: "The Bookbinder", role: "Unknown", el: "void" },
  ];
  return (
    <Phone label="SEN · Novel world">
      <div className="world-hero sen-cover" aria-hidden="true"><span className="cover-mark">❦</span></div>
      <R role="noto" as="p" className="overline center">World guide</R>
      <Title text="Wyrmhollow" height={40} className="center" />
      <div className="stat-row">
        {[["128", "Chapters"], ["46", "Characters"], ["412", "Years of lore"]].map(([n, l]) => (
          <div key={l}><R role="noto" className="big-num tnum">{n}</R><R role="noto" className="muted">{l}</R></div>
        ))}
      </div>
      <R role="noto" as="h3" className="section-h">Characters</R>
      <ul className="people">
        {people.map((p) => (
          <li key={p.name}>
            <div className="avatar" aria-hidden="true">{p.name.slice(0, 1)}</div>
            <div className="tbody"><Name element={p.el as never} rarity="epic">{p.name}</Name><R role="noto" className="tsub">{p.role}</R></div>
          </li>
        ))}
      </ul>
      <R role="noto" as="h3" className="section-h">Places</R>
      <dl className="places">
        {places.map(([n, d]) => (
          <div key={n}><R role="noto" as="strong">{n}</R><R role="sans" as="p">{d}</R></div>
        ))}
      </dl>
      <R role="noto" as="h3" className="section-h">Timeline</R>
      <ol className="timeline">
        {[["Y.A. 1", "The first book is shelved."], ["Y.A. 412", "Fire on the Fifth Floor."], ["Y.A. 1,019", "Wren inherits the key."]].map(([y, e]) => (
          <li key={y}><R role="noto" className="tnum year">{y}</R><R role="noto">{e}</R></li>
        ))}
      </ol>
      <Tabs active="Novels" />
    </Phone>
  );
}

export function ProfileScreen() {
  const s = useSettings();
  return (
    <Phone label="SEN · Profile & settings">
      <div className="profile-head">
        <div className="avatar big" aria-hidden="true">Q</div>
        <Name size="lg" element="lightning" rarity="legendary">Quillwright</Name>
        <R role="noto" as="p" className="meta">Legendary reader · Bond tier III</R>
      </div>
      <div className="stat-row">
        {[["1,204", "Chapters read"], ["86h", "Listening"], ["37", "Day streak"]].map(([n, l]) => (
          <div key={l}><R role="noto" className="big-num tnum">{n}</R><R role="noto" className="muted">{l}</R></div>
        ))}
      </div>
      <ul className="settings">
        {SETTINGS.map((row) => (
          <li key={row.label}><R role="noto">{row.label}</R><R role="noto" className="muted tnum">{row.value} ›</R></li>
        ))}
        <li><R role="noto">Night reading grade</R><span className={`switch ${s.theme === "night" ? "on" : ""}`} aria-hidden="true" /></li>
      </ul>
      <label className="field">
        <R role="noto" className="overline">Display name</R>
        <span className="input r-noto" data-role="noto">Quillwright_Of_The_Fifth_Floor_2026</span>
        <R role="noto" className="error">Use 3–24 characters: letters, numbers or _</R>
      </label>
      <Tabs active="Profile" />
    </Phone>
  );
}
