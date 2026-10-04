# Changelog

Newest first.

- **Display Engine Step 2** Consolidated Reader and Display into the root
  `engine.js` and one `FontBuilderCore` used by both Python entry points.
  Removed the forked Display engine and rebuilt its Lab from the shared source.
  Display options are explicit settings for soft/cut corners, round/flat ends,
  round/sharp joins, rotated pens and oblique slant without italic form swaps;
  default Reader construction remains unchanged. Display inherits current
  overlap repair, Latin letters and combining marks, `mark`/`mkmk`/`ccmp`,
  `locl`, decimal spacing and `frac`/`tnum`/`sups`/`subs`. Cut settings and
  version 0.1 are retained; twenty old advances per cut adopt Reader 0.28's
  existing `a`/`e` width and `i` bearing refinements, with each delta documented
  and all current advances gated. Added frozen ten-style drawing exports and all-fifty
  Reader delivery fingerprints, with a gate that normalizes only build-time
  `head` timestamps and checksum bookkeeping. See the shared-engine notes for
  rebuild validation, expanded Display proofs and the Reader identity reason.
  All 50 shipped Reader files remain byte-identical; all 50 regenerated files
  match normalized tables and 0.35 geometry/hints/metrics/layout. Soft, Edge,
  Ink and Wide now each have 419 glyphs, passing the shape gate with 0 flags
  across 1,676 outlines and 3,352 OTF/WOFF2 renders. Each cut passes FontBakery
  OpenType/offline Universal with 0 FAIL / 0 WARN. Added complete 400px proofs
  and inherited-language/numeric/mark behavior checks; all local regressions
  and Reader distribution checks pass.

- **Display Engine Step 1** Repaired flat-cap construction for rotated/slanted
  oval pens, terminal attachments and coincident joins. Bounded sharp miters
  with clean bevel fallback; removed global cuts through angled terminals.
  Added curve-preserving outline cleanup after stroking and before CFF export,
  including fitting/rounding debris and self-overlap winding. Updated the live
  Lab's cap/join construction and rebuilt Soft, Edge, Ink and Wide OTF/WOFF2.
  Preserved all cut settings, letter skeletons, inventories, advances and line
  metrics; recalculated automatic pairs from the repaired ink profiles.
  Added the 400px all-glyph shape/delivery gate, construction regressions,
  Actions gate and complete before/after proof sheets. All 964 glyph outlines
  pass with 0 flags; each cut passes FontBakery OpenType/offline Universal with
  0 FAIL / 0 WARN. The Display cut version remains 0.1.

- **0.36** Renamed the current family to SEIHouse Sans and added the SEIHouse
  Sans Ecosystem License 1.0: broad ecosystem creative use and customization,
  authorized SEIHouse app/web distribution, and document embedding without fees
  or user-count limits. Unrelated app/product embedding and standalone font
  redistribution require permission. Added all requested name-table legal/owner
  fields and retained installable document embedding with vendor ID SEIH.
  Kept SEIReader filenames, npm identity, and legacy CSS working; added canonical
  Sans CSS and shipped the operative license in ZIP/npm/site deliveries.
  Rebuilt ten full styles and thirty subsets without changing drawings or spacing.

- **0.35 paragraph inspection** Inspected sentence endings, straight/curly
  apostrophes and narrow-letter runs in full paragraphs across all ten styles.
  Added the exact samples to the existing comparison and recorded measured
  geometry, shaping checks and Day/Night browser proofs. No demonstrated spacing
  defect was found; font bytes, spacing settings and the version remain unchanged.

- **0.35** Fixed missing ink at sharp joins in v/V/w/W and figures by resolving
  self-overlapping stroke outlines before CFF export and hinting. Applied the
  same repair to numeric alternates, accents and symbols through the shared
  builder. Drawing rules, weight controls, advances, kerning and OpenType layout
  remain unchanged. Preserved the ten 0.34 full web fonts for comparison and
  added an audit for rasterizer fill-rule agreement and design preservation.

- **Font Lab website** Added a real homepage with an actual-font specimen,
  Day/Night mode, Reader/Display workspaces, comparison/chapter links, and resource
  downloads. Added a dependency-free static build and Vercel configuration with an
  explicit public-file allowlist. Both Labs now save browser-local drafts and
  download portable JSON while retaining the original host database integration.
  Added Home links and website deployment/use documentation. Font drawings,
  settings, kerning and binaries are unchanged; the Reader npm package stays separate.

- **Display 0.1 import** Added the supplied SEIHouse Display Engine under `display/`:
  Soft, Edge, Ink, and Wide cut settings, source/build tools, live Lab, kerning maps,
  and each design's OTF/WOFF2 fonts. The 24 supplied files retain their design rules,
  settings, and font bytes; normalized one extra export-tail blank line and added
  explicit UTF-8 file I/O to both Python builders for Windows portability. Documented
  all engine/builder functions without changing executable drawing/build logic and
  rebuilt the Lab to include the engine comments.
  Added repository links and Windows UTF-8 build instructions; documented the original
  local Copy workflow and prototype limitations. SEIReader source/fonts/settings and
  its app distribution scope are unchanged. Corrected the app-install guide's
  Regular-plus-italic font-size count to 86,932 bytes.

- **0.34** Multilingual Phase 2: the first ten Latin language inventories. Added 94
  encoded letters for Polish, Czech, Hungarian, Romanian, Turkish, Hausa, Kurdish
  (Kurmanji, Latin), Māori, Igbo, and Uzbek (Latin), including CLDR main/auxiliary/index
  exemplars and both cases. Dedicated side carons, barred letters, and hooked Hausa
  forms; Igbo dot removal under tones above dot-below i; Turkish dotted-i and Romanian
  comma forms through `locl`, and Hungarian-only uppercase digraph spacing. New ogonek
  punctuation clearance preserves every old nonnumeric pair value. All 323 old outlines/metrics
  and design settings match 0.33. Preserved
  its ten full fonts/thirty subsets; rebuilt the family and web delivery. Added a
  pinned alphabet inventory, independent coverage/shaping/collision audit, native
  Windows proofs, and a language selector in the same comparison; Lab language and
  Every character rows include the additions. All ten styles pass 18,290 language
  strings, and OpenType/offline universal FontBakery remain at 0 FAIL / 0 WARN.
  Native-reader/device certification and the remaining alphabet/script batches are
  separate follow-up work.
  Added a runtime-only distribution: ten full WOFF2 files, relative app CSS, installation
  guidance, integrity manifest, and a private npm tarball with zero dependencies/scripts.
  Full-family font data is 31.3% smaller than all thirty overlapping subsets. Optional
  explicit weight/subset ZIPs, shipped-payload audits, and an Actions artifact build
  keep engineering files out of application installs. Documented the actual NovelExpanded
  HARNESS reader and a scoped host integration without altering its source or font bytes.
  Corrected user-reported crowded decimal points: explicit 24-unit separation on both
  sides of numeric periods and commas replaces automatic tightening, in all ten styles
  and both figure modes. Tabular adjustments are uniform to retain column alignment.
  Added price/percentage/decimal-comma Lab samples and an independent numeric-clearance,
  alignment, unchanged-outline/metric, and full/subset shaping regression check.
- **0.33** Multilingual Phase 1: an additive Latin foundation. Seventeen zero-width combining
  marks, canonical composition, above/below and ligature attachment, mark stacking, and
  unencoded dotless `i/j` forms. Added low/reversed quotes `‚ „ ‛ ‟`, lexical apostrophes
  `ʻ ʼ`, dotted circle `◌`, thin space, and narrow nonbreaking space. Every existing contour,
  metric, design setting, and per-style pair value matches 0.32. Latin extended now includes
  basic Latin and prose punctuation and is preferred in `fonts.css` so accent sequences
  stay in one face. Preserved the ten 0.32 full fonts/thirty subsets; rebuilt all ten styles
  and thirty subsets. Updated the same comparison/Lab with NFC/NFD, stacks, and quotation
  samples; added preservation, shaping, collision, and delivery audits plus Windows proofs.
  Corrected the proof renderer's vertical offset direction and row sizing for combining marks.
  OpenType and offline universal FontBakery profiles remain at 0 FAIL / 0 WARN. Complete
  additional language alphabets and physical browser/device checks remain future work.
- **0.32** Punctuation, figure texture, and reading-weight balance together: lighter dots,
  quotes, commas, and dashes; curved comma/quote tails; continuous `2/3/5/6/8/9` curves
  and slightly lighter figure strokes. Tabular, small figures, and fractions follow their
  source digits. Light's letter stroke increases from 70 to 74 source units and Medium's
  decreases from 100 to 97, with nominal controls and all character advances unchanged.
  Regular/SemiBold/Bold letter drawings, symbols/icons, vertical metrics, word space, and
  approved letter-pair rhythm remain unchanged. Static weight adjustments apply at all
  sizes. Preserved all ten 0.31 styles and thirty subsets; rebuilt the full family and
  delivery. Updated the same preview and Lab with dialogue, decimals, proportional/tabular
  figures, and small-size comparisons; added scope, weight, counter, and collision audits.
- **0.31** Broader spacing rhythm: inspected `minimum`, `murmur`, `river`, `climate`,
  `parallel`, and `everywhere`, with supporting `r/v/w/y` and narrow-letter words, upright
  and italic at all five weights. Balance `ll` and protect `yw/tw` and italic `ur/um`
  separation. Small residuals keep their existing spacing unless ink separation needs
  correction. All 295 contours, bearings, advances, design settings, earlier focused
  pairs, and ligature construction match 0.30. Preserved the ten merged 0.30 styles and
  all per-style pair maps; rebuilt ten full styles and thirty subsets. Updated the same
  reference preview and Lab, plus fixed small-size and all-weight Windows proofs.
- **0.30** Optical spacing pass: measured, limited corrections for `Lian`, `Iñés`, `blade`,
  `Entry`, `Mei’s`, `acquittal`, and `ri/rn/cl/li`, separately for upright and real italic
  at every weight. Joined `fi/fl` now receive pair spacing beside neighboring letters;
  crowded `tt/ry` pairs keep more room at small sizes. Every glyph contour, bearing,
  advance, weight, height, contrast, and word space matches 0.29. The Lab uses the finished
  per-style pairs. Preserved all ten 0.29 styles, rebuilt ten full styles and 30 subsets,
  and added contour/shaping/collision audits. Updated the same comparison preview with
  a fixed 13/15/17px Light/Regular/Medium matrix and native Windows Day/Night proofs.
  Physical phone/browser checks are deferred at the user's request.
- **0.29** Lowercase consistency pass: continuous shoulders for `h/n/m`, a smoother
  `u` lower curve, and shared `b/d/p/q` bowls with smooth stem joins and softly squared
  sides. Italics retain lower branches and pen-like exits; `ñ/ù/ú/û/ü` follow their bases.
  All advances and all settings except the version number match 0.28. Preserved all ten
  0.28 styles and updated the reference preview with focused letters and word samples.
  Rebuilt all ten styles and 30 subsets; added an audit that checks every unchanged
  outline, advance, counter count, and vertical alignment against 0.28.
- **0.28** Literata/Rubik reference refinement: individual continuous curves for the upright
  `a` and shared `e`/`c`/`s`, modestly narrower `a`/`e`, slightly more side space for `i`, and
  word space raised from 0.205 to 0.220 em. Accent and joined-letter derivatives follow the
  updated source rules, and pair spacing is recalculated for every style. Preserved all ten
  0.27 styles and added the same reference preview layout with 0.28, 0.27, Literata, and Rubik;
  Day/Night, 13/15/17/20px, weights, 1.4/1.5/1.6 line height, and 0.205/0.220/0.230 word-space
  trials. The default chapter line height remains 1.4 for comparison.
- **0.27** Phase 3 reading feedback pass: rounder, slightly wider upright forms; conservative
  lowercase pair spacing to smooth long words; straight and curly quotes raised, with
  apostrophes tucked closer to adjacent lowercase letters. Rebuilt the full family and web
  subsets, with the reported snag words in the original Lab Reader Chamber. Also added a
  six-browser device checklist and three-chapter reading page with locally saved feedback.
- **0.26** Phase 2: optional tabular figures (`tnum`), superscript/subscript digits (`sups`,
  `subs`), fractions (`frac`, ½ ¼ ¾, U+2044), and three pyftsubset WOFF2 deliveries per style
  with generated `fonts.css`. Added numeric demos in the Lab.
- **0.25** Phase 1: Light raised to 70; automatic pair spacing (about 1,800 pairs per style);
  joined fi / fl with cursor positions; screen tuning (alignment zones + Adobe otfautohint).
- **0.24** Tall lowercase letters (l b d h k f) set to exactly capital height.
- **0.23** Western European languages: 70 accented and special letters, marks placed a fixed gap
  above each letter at every weight and lighter in heavier weights. Languages section in the Lab.
- **0.22** Thick and thin (horizontals 12% thinner). Carved joins tried and switched off.
- **0.21** SEIHouse `Ⓢ` brand mark, music marks, player controls, icons, private in-app codes.
- **0.20** ☯ ⚡ ☀ ☾ ☽ and 26 more symbols; shapes now merged one at a time.
- **0.19** Common, novel, and money symbols; first FontBakery run, all findings fixed.
- **0.18** Capital C redrawn as one continuous curve with angled ends.
- **0.17** Upright letters a little straighter; italic curves locked.
- **0.16** Handwriting-style italic (exit strokes, lower arches, rounder curves).
- **0.15** Italic for all 5 weights; saved settings applied.
- **0.14** Wide letters keep more width; spacing grows with weight; softer g, y, f, t.
- **0.13** Default weights Light 55 / Regular 85 / Medium 100 / SemiBold 115 / Bold 140; tidy Lab layout.
- **0.12** Five weights.
- **0.11** Built from settings saved in the Lab.
- **0.10** More space between letters and words.
- **0.9** / **0.8** Back to the 0.6 look with the smaller lowercase.
- **0.7** "SEIReader" reading font (research-based pass; most of it later reverted by preference).
- **0.6 and earlier** SEIHouse Soft: the original soft, squared-curve design.
