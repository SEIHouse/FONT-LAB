/** Fictional app content for the stress page. Names are invented; they exercise real character sets. */

export type Role = "title" | "elemental" | "sans" | "noto" | "serif";

export const ROLES: { id: Role; label: string; face: string; job: string }[] = [
  { id: "title", label: "Title Engine", face: "Living Titles on SEIHouse Display (Soft · Edge · Ink · Wide)",
    job: "Album and novel titles. Users will customise the cut and motion." },
  { id: "elemental", label: "Elemental Title", face: "Elemental effects on the base face you choose",
    job: "Artist, author and reader names. Effects grow later (hearts, notes, …)." },
  { id: "noto", label: "SEIHouse Noto", face: "SEIHouse Noto Redraw 02 (Day and Night grades)",
    job: "Everything else: navigation, track lists, metadata, numbers, buttons, settings." },
  { id: "sans", label: "SEIHouse Sans", face: "SEIHouse Sans 0.43 (Day and Night grades)",
    job: "Reading text: chapters, lyrics, synopses." },
  { id: "serif", label: "Future serif", face: "Stand-in: the system serif (Georgia). Not a SEIHouse font yet.",
    job: "Editorial: liner notes, editor's notes, features." },
];

export const ALBUM = {
  title: "Paper Lanterns",
  artist: "Mira Solace",
  year: 2026,
  label: "SEIHouse Productions",
  tracks: [
    { n: 1, title: "Paper Lanterns", feat: "", time: "3:45", plays: "1,204,553", explicit: false, expanded: true },
    { n: 2, title: "Ivy on the Overpass", feat: "Søren Ålvik", time: "4:02", plays: "887,210", explicit: false, expanded: true },
    { n: 3, title: "11:11 (Make a Wish, Then Make It Louder)", feat: "", time: "3:11", plays: "2,418,906", explicit: true, expanded: false },
    { n: 4, title: "Quiet Library", feat: "Nguyễn Thảo Vy", time: "5:27", plays: "301,448", explicit: false, expanded: true },
    { n: 5, title: "Wolves Wait Where Water Was", feat: "", time: "2:58", plays: "96,071", explicit: false, expanded: false },
    { n: 6, title: "Façade / Ça Va", feat: "Zoë Brontë-Ïsle", time: "4:40", plays: "1,010,001", explicit: false, expanded: false },
    { n: 7, title: "Gjallar", feat: "Łucja Wróbel", time: "3:33", plays: "58,912", explicit: true, expanded: true },
    { n: 8, title: "Twenty-Two Degrees (Interlude)", feat: "", time: "1:12", plays: "44,780", explicit: false, expanded: false },
  ],
  minutes: "28 min",
  liner:
    "Recorded over four winters in a converted library, Paper Lanterns trades the glare of her debut for something closer: tape hiss, a borrowed upright piano, and songs that read like letters left on a windowsill.",
};

export const LYRICS = [
  "We folded every promise into paper,",
  "set it floating where the river bends —",
  "if the light goes out before it reaches you,",
  "know that I was counting to the end.",
];

export const NOVEL = {
  title: "The Quiet Library",
  author: "Ilse Harrow",
  rating: "4.8",
  reads: "1.2M",
  chapters: 128,
  status: "Ongoing · Updates Fridays",
  synopsis:
    "When the last librarian of Wyrmhollow inherits a key that opens every book but her own, she discovers the stories have been rewriting their readers. Now the library is waking up, and it remembers everyone who ever borrowed from it.",
  editor:
    "A patient, lantern-lit fantasy that rewards the reader who lingers. Our pick for the long winter.",
  list: [
    { n: 128, name: "The Key That Would Not Turn", date: "2 days ago", mins: "14 min", isNew: true },
    { n: 127, name: "Wyrmhollow, After Midnight", date: "Nov 6", mins: "12 min", isNew: false },
    { n: 126, name: "Ink, Ash & the Fifth Floor", date: "Oct 30", mins: "17 min", isNew: false },
    { n: 125, name: "To Whom It May Concern", date: "Oct 23", mins: "9 min", isNew: false },
  ],
};

export const CHAPTER = {
  number: 128,
  name: "The Key That Would Not Turn",
  body: [
    "The morning light settled gently over the quiet library. Wren set the key on the reading table and waited, the way you wait for a kettle you are sure you never filled.",
    "“Good evening,” said the book nearest her elbow — although it was, by every clock in Wyrmhollow, a little after nine in the morning.",
    "She did not answer. Fifty years of rules said you did not answer a book that spoke first.",
  ],
  comments: [
    { name: "Quillwright", el: "lightning", rank: "legendary", text: "The kettle line!! 😭 Chapter 128 and it still gets me.", time: "2h", likes: "1.4k" },
    { name: "Ελένη Ρόδου", el: "frost", rank: "epic", text: "Rule 1 of Wyrmhollow: never answer first. Noted.", time: "5h", likes: "312" },
    { name: "Şebnem Yıldız", el: "fire", rank: "rare", text: "Is the fifth floor coming back? Asking for a friend.", time: "1d", likes: "88" },
  ],
};

export const LIBRARY = [
  { title: "Midnight Orchard", who: "Nguyễn Thảo Vy", kind: "Album · 2025" },
  { title: "Ålesund Nights", who: "Søren Ålvik", kind: "Single · 2026" },
  { title: "Земля и небо", who: "Злата Миронова", kind: "Album · 2024" },
  { title: "Ψίθυροι", who: "Ελένη Ρόδου", kind: "EP · 2026" },
  { title: "光の庭", who: "坂本 光", kind: "Album · 2023" },
  { title: "하늘 아래", who: "이하늘", kind: "Single · 2026" },
  { title: "ليالي", who: "ليلى حداد", kind: "Album · 2025" },
  { title: "Đêm Hà Nội (Live at the Old Quarter, Remastered 2026 Deluxe Edition)", who: "Đỗ Minh Quân", kind: "Live album · 2026" },
];

/** Names that a music app receives from distributors, in many scripts. */
export const NAMES = [
  "Zoë Brontë-Ïsle", "Renée Faÿ", "Søren Ålvik", "Łucja Wróbel", "Şebnem Yıldız",
  "Đỗ Minh Quân", "Nguyễn Thảo Vy", "Ðorđe Ćirić", "Ελένη Ρόδου", "Злата Миронова",
  "坂本 光", "이하늘", "ليلى حداد",
];

export const SETTINGS = [
  { label: "Audio quality", value: "Lossless · 24-bit / 96 kHz" },
  { label: "Download over cellular", value: "Off" },
  { label: "Reading font size", value: "18 px" },
  { label: "Storage used", value: "3.42 GB of 64 GB" },
  { label: "Version", value: "0.43.0 (build 2611)" },
];
