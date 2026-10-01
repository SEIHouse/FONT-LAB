# Comparison references

These fonts are used only by `build_comparison.py` and the reference preview. They do not
contribute glyph outlines or spacing data to SEIReader.

- Literata 3.103: official `Literata[opsz,wght].ttf` and italic from Google Fonts.
- Rubik 2.300: official `Rubik[wght].ttf` and italic from Google Fonts.

`Regular.woff2` and `Italic.woff2` retain the full original variable fonts, converted with
fontTools using lossless WOFF2 compression. The preview explicitly selects the weight and
pins Literata's optical size to 20. `MANIFEST.json` records source URLs, versions, original
file hashes, and WOFF2 asset hashes. Both families' OFL texts are included in their folders.

The preview embeds these files and SEIReader's candidate/baseline styles, so opening it
requires no font downloads or external services.
