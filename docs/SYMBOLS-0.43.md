# Studio Symbol Refinement — 0.43

SEIHouse Sans `0.43` and SEIHouse Display `0.1` (`@seihouse/living-titles@0.1.4`) replace the original placeholder symbol drawings across all 44 monochrome brand, cultivation, web-novel, player, and music icons with custom studio-crafted silhouettes built for both **16px reading** and **400px Display** scale.

## Scope & Priority Highlights

All 44 refined symbols keep their exact historical cell widths (`w`), vertical alignment classes (`cap`), and sidebearings (`sb`), guaranteeing **zero text reflow** across existing chapters, menus, and covers:

`★ ☯ ⚡ ☀ ☾ ☽ ⚔ ✦ ☆ ◆ ◇ ▲ ▼ ▶ ◀ ♥ ♡ ♪ © ® ™ Ⓢ ♩ ♫ ♬ ♭ ♮ ♯ ⏸ ⏹ ⏺ ⏭ ⏮ 🎧 💻 📖 🔖 🔍 🔔 ⚙ ⌂ 🎤 💿 🔊`

(Along with their Private Use Area mirrors `U+E000`–`U+E00F`, which inherit the refined shapes automatically so mobile browsers never substitute color system emoji.)

Key architectural upgrades in `engine.js` and `font_builder.py`:

- **True-Space Geometric Projection (`iconSpace`):** Circular and geometric symbols now project through an inverse width/height normalizer around each glyph's cap center, keeping `Ⓢ`, `☯`, `💿`, `⏺`, `🔍`, `©`, `®`, and `⚙` true `1:1` circles across every weight, Night grade, and Display width cut (eliminating the `1.52:1` horizontal oval distortion previously seen in `Display Wide`).
- **`Ⓢ` Brand Mark (`U+24C8`):** Combines a true, non-squished outer ring with SEIHouse Sans's smooth continuous `0.40` cubic `S` spine, scaled with balanced interior breathing room across Light, Regular, Bold, and Display Soft/Wide.
- **Cultivation, Rating & Quest Icons (`☯`, `⚡`, `⚔`, `★`, `☆`, `✦`, `♥`, `♡`, `☀`, `☾`, `☽`):**
  - `☯` uses tangent-joined inner Yin/Yang teardrops with optically balanced dark/light eyes that stay crisp at 16px Day & Night and razor-smooth at 400px.
  - `⚡` features a sharper, fuller high-voltage bolt silhouette; `⚔` replaces crossed sticks with tapered pointed blades, compact crossguards, and pommel caps.
  - `☆` and `◇` use clean even-odd hollow contours with weight-aware wall thickness rather than heavy single strokes that plugged interior counters in bold cuts; `♥` and `♡` use warm, full cubic Bezier lobes; `☾` and `☽` use tangent-continuous rounded horn tips; `✦` uses smooth concave cubic arcs.
- **Expanded Albums Music, Player & Studio Utility Suite (`🎧`, `🎤`, `💿`, `🔊`, `🔔`, `⚙`, `♩`, `♪`, `♫`, `♬`, `♭`, `♮`, `♯`, `⏸`, `⏹`, `⏺`, `⏭`, `⏮`, `💻`, `📖`, `🔖`, `🔍`, `⌂`):**
  - `🎧` joins a padded headband arch seamlessly into cushioned earcup shells; `🎤` separates the condenser capsule cleanly inside its U-cradle and stand; `💿` pairs a crisp outer disc and unpluggable spindle hub with two delicate opposing sheen arcs; `🔊` separates the flared speaker horn from two concentric wave arcs so heavy cuts never merge; `🔔` pairs a crowned bell dome and overhanging rim lip with a tucked clapper; `⚙` uses an 8-tooth involute-style profile with an enlarged center bore that reads clearly at 16px.
  - `♩`, `♪`, `♫`, and `♬` replace detached circular dot noteheads with tilted elliptical cubic noteheads anchored directly to stems and slanted beams across every weight and width.

Punctuation bullets (`•`, `·`, including Catalan `L·l`), directional arrows (`↑`, `↓`, `→`, `←`), check/cross marks (`✓`, `✗`), and math operators (`−`, `≤`, `≥`, `≠`, `≈`, `×`, `÷`, `±`) remain completely untouched.

## Visual Proofs & Preservation Gates

- [Priority 12 Studio Icons — Before (0.42) vs After (0.43)](proofs/symbols-0.43/priority-12.png)
- [Remaining 32 Symbols (Part 1/2) — Before (0.42) vs After (0.43)](proofs/symbols-0.43/remaining-part-1.png)
- [Remaining 32 Symbols (Part 2/2) — Before (0.42) vs After (0.43)](proofs/symbols-0.43/remaining-part-2.png)

Preservation & quality verification:
- **100% of letters, figures, punctuation, alternates, advance widths (`hmtx`), kerning (`GPOS`), and layout tables (`GSUB`, `GDEF`)** across all 16 Reader faces (112 subsets) and 4 Display cuts (24 subsets) are preserved unchanged.
- All 44 refined symbols pass `verify_display_shapes.py` at 400px (`0` outline, reversal, tiny-segment, or counter flags across Soft, Edge, Ink, Wide, and flat-nib mode), `display/verify_motion.py`, and FontBakery (`check-opentype` and `check-universal --skip-network`).
