# SEIHouse Sans 0.39: apparent weight across the app's reading sizes

Investigated on 2026-10-24. In the [0.35 Regular paragraph proof](proofs/0.35/paragraph-regular-day.png),
20px looks much darker than 17px although both are weight 400. This record measures
the current fonts at the NovelExpanded Reader's sizes, **15, 17.2, 18.5, 20 and 22px**.
No font file changes.

## Result

The jump **does not reproduce** with the 0.39 fonts in any browser available to CI.
Every size step stays within 8% in every browser, weight and screen scale tested.
In the 0.35 proof, Regular jumped **69%** from 17 to 20px. Because nothing here
reproduces the jump, nothing justifies changing hinting or stroke geometry yet.

| Browser and text rendering | Largest step, any weight and scale | Regular 17.2 → 20px at 100% |
|---|---|---|
| Windows Chromium 153, ClearType | −7.8% | +0.8% |
| Windows Chromium 153, grayscale | −7.8% | +0.5% |
| Windows Edge 155, ClearType and grayscale | −7.8% | +0.5% |
| macOS WebKit 26.6 (CoreText, as in iPhone Safari) | −2.7% | −0.7% |
| Linux Chromium 153 (FreeType, as in Android Chrome) | +1.6% | +0.6% |
| FreeType 2, Adobe CFF engine, hinted (direct) | +2.6% | +3.5% |

"Step" is the change between neighboring app sizes in ink per square pixel of text
size. Zero means a larger size looks equally dark. The usual difference between
neighboring weights is about 13%. For reference, at 100% Windows renders every size about
20% darker than macOS or Linux, but it does so evenly at every size.

## Why the 0.35 proof jumped

The shape of the 0.35 jump points to whole-pixel stem rounding.
Regular's standard vertical stem (`StdVW`) is 170/2000 em, which is 1.46px at 17.2px
and 1.57px at 18.5px. A rasterizer that rounds stems to whole pixels in the
horizontal direction changes them from 1px to 2px at about **17.6px**.
For Medium that happens at 15.5px, and for Light at 20.3px. The saved proofs match
all three points. After adjusting for size, the ink was Regular 37 → 63 at 17 → 20px,
Light 37 → 34 (no jump), and Medium 42 → 59 at 15 → 17px.

The 0.35 and 0.39 Regular fonts have identical hint values and lowercase
outlines, so the difference lies in how the proof machine rendered them. Its
screenshots were grayscale (no ClearType color fringes) from headless Chrome
154 on Windows. The script and machine settings that produced them are not in the
repository. On the CI Windows runner, grayscale text in Chromium and Edge does
not round stems that way.

The hinting test copies agree. Removing the vertical-stem hints (`no-vstem`) or all
hints (`unhinted`) leaves macOS and Linux unchanged. On Windows, removing all hints
only smooths a small wobble of under 8%: in shipped Regular at 100%, 18.5px and 22px
come out slightly lighter.

## Consequences for the Reader

- **Phones:** iPhones and most Android phones draw text at 2–3 device pixels per
  CSS pixel and do not round stems to whole pixels. The CI proxies for both are flat.
- **Desktop at 1280px and wider:** the Reader enlarges text by 1.12–1.32 times
  (`--reader-scale` in Development), so the 17.2px default draws at 19.3–22.7px.
  If a machine does round stems like the 0.35 proof machine, a 1280px or wider window
  is past Regular's 17.6px point while a narrower one is not. This is a possible
  effect, not one any tested browser shows.
- **The 18.5px default candidate** sits just past the same point. On a machine that
  renders like the 0.35 proof, 18.5px Regular would look heavier than 17.2px. That
  machine needs to compare them before a default change is judged there.

## How to repeat

`python verify_size_density.py <out> [--browser webkit] [--channel msedge] [--grayscale] [--dpr 1 1.25 1.5 2]`
renders the paragraph with the shipped fonts and both test copies. It writes a
JSON report and shipped-font screenshots. The **Size density** workflow runs it on
Windows (Chromium and Edge, ClearType and grayscale, 100/125/150/200%), macOS
WebKit and Linux Chromium for any change to the fonts or the tool.

On a physical device, open the [reading test](../lab/reading-test.html) and use
**App size steps**. Each line should look like the same weight at a larger size.
Record the result in the [device test](DEVICE-TEST.md). The most useful check is
the Windows PC that made the 0.35 proofs, in normal Chrome: if the 17.2 → 20px jump
appears there, the next step is a hinting-only candidate (for example, removing
vertical-stem hints) measured there, before any stroke change.
