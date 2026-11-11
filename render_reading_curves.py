"""Render actual before/after Reader fonts with HarfBuzz positioning and FreeType.

python -X utf8 render_reading_curves.py BASELINE --fonts fonts --output docs/proofs/reading-curves
Requires Pillow in addition to the normal font-build dependencies.
"""
import argparse
import io
import math
from pathlib import Path

import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

from build_subsets import ALL_STYLES as STYLES


class Face:
    """Shape the same glyph IDs that are rasterized, including real italics and kerning."""
    def __init__(self, path):
        data = path.read_bytes()
        self.hb = hb.Font(hb.Face(data))
        self.ft = freetype.Face(io.BytesIO(data))

    def shaped(self, text):
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self.hb, buffer)
        return list(zip(buffer.glyph_infos, buffer.glyph_positions))

    def width(self, text, size):
        return sum(p.x_advance for _, p in self.shaped(text))*size/self.hb.face.upem

    def draw(self, image, text, size, x, baseline, color):
        scale = size/self.hb.face.upem
        self.ft.set_pixel_sizes(0, size)
        for info, pos in self.shaped(text):
            self.ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
            glyph = self.ft.glyph
            bitmap = glyph.bitmap
            if bitmap.width and bitmap.rows:
                raw = bytes(bitmap.buffer)
                pixels = b''.join(raw[y*bitmap.pitch:y*bitmap.pitch+bitmap.width] for y in range(bitmap.rows))
                mask = Image.frombytes('L', (bitmap.width, bitmap.rows), pixels)
                point = (round(x+pos.x_offset*scale)+glyph.bitmap_left,
                         round(baseline-pos.y_offset*scale)-glyph.bitmap_top)
                image.paste(color, (*point, point[0]+bitmap.width, point[1]+bitmap.rows), mask)
            x += pos.x_advance*scale

    def paragraph(self, image, text, size, x, baseline, width, color):
        line = ''
        for word in text.split():
            candidate = (line+' '+word).strip()
            if line and self.width(candidate, size) > width:
                self.draw(image, line, size, x, baseline, color)
                baseline += math.ceil(size*1.5)
                line = word
            else:
                line = candidate
        self.draw(image, line, size, x, baseline, color)


def render(baseline, fonts, output):
    """Write Day/Night family proofs plus a compact Regular detail comparison."""
    output.mkdir(parents=True, exist_ok=True)
    label = ImageFont.load_default(size=17)
    faces = {(side, style): Face(folder/f'SEIReader-{style}.otf')
             for side, folder in [('Before', baseline), ('After', fonts)] for style, *_ in STYLES}
    for theme, background, ink, muted in [('day', '#f5f0e7', '#242c29', '#59655f'),
                                         ('night', '#17221d', '#deded4', '#b5c3b9')]:
        image = Image.new('RGB', (1320, 140+len(STYLES)*150), background)
        draw = ImageDraw.Draw(image)
        draw.text((32, 25), 'SEIHouse Sans · g / S / ? · actual font outlines', font=label, fill=muted)
        for side, x in [('Before', 32), ('After', 680)]:
            draw.text((x, 65), side, font=label, fill=muted)
            for i, (style, *_) in enumerate(STYLES):
                y = 110+i*150
                draw.text((x, y), style, font=label, fill=muted)
                face = faces[side, style]
                face.draw(image, 'g d b p q   S s   ?', 45, x, y+65, ink)
                face.draw(image, 'She crossed the bridge. Was the ledger signed?', 20, x, y+100, ink)
                face.draw(image, 'ginger · bright · digging · ŚŜŞŠȘ · ĝğġģ · Ѕд', 17, x, y+129, ink)
        image.save(output/f'family-{theme}.png')
    detail = Image.new('RGB', (1120, 760), '#f5f0e7')
    draw = ImageDraw.Draw(detail)
    for side, y in [('Before', 20), ('After', 390)]:
        draw.text((35, y), side+' · Regular', font=label, fill='#59655f')
        face = faces[side, 'Regular']
        face.draw(detail, 'g d q   S s   ?', 130, 35, y+165, '#242c29')
        face.paragraph(detail, 'She crossed the bridge. Was the ledger signed? '
                       'Ginger tea waited beside the bright window. She read the page again, '
                       'tracing each line until the story settled into a quiet rhythm.',
                       20, 35, y+230, 970, '#242c29')
    detail.save(output/'regular-detail.png')
    print(f'Rendered all {len(STYLES)} faces in Day/Night plus Regular detail -> {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--fonts', type=Path, default=Path('fonts'))
    parser.add_argument('--output', type=Path, default=Path('docs/proofs/reading-curves'))
    args = parser.parse_args()
    render(args.baseline, args.fonts, args.output)
