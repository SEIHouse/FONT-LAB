"""Audit 0.32 marks, figures, and reading weights against preserved 0.31.

Check every advance, permitted contour/pair changes, counter survival, weight
order, hinting, accent inheritance, subset shaping, and actual ink separation.
Pass old/0.32 to audit that archived build after later additive work.
"""
from pathlib import Path
import hashlib
import json
import sys

import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

from build_subsets import STYLES
from verify_lowercase import recorded, bounds
from verify_spacing import WORDS, shaped, adjustment

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT/'old/0.31'
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÆŒÐÞØæœßðþøﬁﬂ'
ACCENTS = 'ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝŸàáâãäåçèéêëìíîïñòóôõöùúûüýÿ'
ACCENT_BASE = {accent:base for base,group in {
    'A':'ÀÁÂÃÄÅ','C':'Ç','E':'ÈÉÊË','I':'ÌÍÎÏ','N':'Ñ','O':'ÒÓÔÕÖ',
    'U':'ÙÚÛÜ','Y':'ÝŸ','a':'àáâãäå','c':'ç','e':'èéêë','i':'ìíîï',
    'n':'ñ','o':'òóôõö','u':'ùúûü','y':'ýÿ',
}.items() for accent in group}
MARKS = '.,:;…!?\'"‘’“”-–—()[]¡¿'
FIGURES = '0123456789⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉½¼¾'
TEXTS = WORDS + (
    '“Mei’s,”', '‘Lian,’', '"Iñés"', "don't!", 'Why?', '(Chapter 12);',
    '3:14—5:09…', '1,234.56', '8.50%', '0123456789', '6089', '½¼¾',
    'To AV P. “A', 'Áurea Éloi Iñés João Müller Søren Þóra',
)


def area(font, name):
    """Measure filled ink area independently of hint instructions and translations."""
    glyphs = font.getGlyphSet()
    pen = AreaPen(glyphs)
    glyphs[name].draw(pen)
    return abs(pen.value)


def separated(font, text, liga):
    """Reject intersections between adjacent shaped outlines, including punctuation."""
    glyphs = font.getGlyphSet()
    if not hasattr(font, '_texture_outlines'): font._texture_outlines = {}
    outlines = font._texture_outlines
    x, previous = 0, None
    for name, advance, dx, dy in shaped(font, text, liga=liga):
        if name not in outlines:
            outline = pathops.Path()
            glyphs[name].draw(outline.getPen())
            outlines[name] = outline
        ink = outlines[name].transform(translateX=x+dx, translateY=dy)
        if previous is not None:
            overlap = pathops.op(previous, ink, pathops.PathOp.INTERSECTION)
            assert abs(overlap.area) < .01, (text, name, liga, 'ink collision')
        previous = ink
        x += advance


def verify(candidate=None):
    """Check the finished family, stable reading layout, and intended weight changes."""
    candidate = Path(candidate).resolve() if candidate else ROOT/'fonts'
    metadata = candidate if (candidate/'settings.json').exists() else candidate.parent
    previous_settings = json.loads((BASELINE/'settings.json').read_text(encoding='utf-8'))
    settings = json.loads((metadata/'settings.json').read_text(encoding='utf-8'))
    previous_settings.pop('version'); settings.pop('version')
    assert previous_settings == settings, 'A nominal design setting changed'
    for manifest, count in [('SHA256.json', 10), ('SUBSET-SHA256.json', 30)]:
        hashes = json.loads((BASELINE/manifest).read_text(encoding='utf-8'))
        assert len(hashes) == count
        for filename, digest in hashes.items():
            assert hashlib.sha256((BASELINE/filename).read_bytes()).hexdigest() == digest, filename
    old_pairs = json.loads((BASELINE/'kern_styles.json').read_text(encoding='utf-8'))
    pairs = json.loads((metadata/'kern_styles.json').read_text(encoding='utf-8'))
    assert old_pairs.keys() == pairs.keys() and len(pairs) == 10
    mass = {}
    for style, _, _ in STYLES:
        candidate_path = candidate/f'SEIReader-{style}.otf'
        if not candidate_path.exists(): candidate_path = candidate/f'SEIReader-{style}.woff2'
        with TTFont(BASELINE/f'SEIReader-{style}.woff2') as before, TTFont(candidate_path) as after:
            assert before.getBestCmap() == after.getBestCmap(), style
            assert before.getGlyphOrder() == after.getGlyphOrder(), style
            cmap = after.getBestCmap()
            adjusted_weight = style.startswith(('Light', 'Medium'))
            numeric = {cmap[ord(ch)] for ch in FIGURES}
            numeric.update(name for name in after.getGlyphOrder() if name.endswith(('.tf','.numr','.dnom')))
            marks = {cmap[ord(ch)] for ch in MARKS}
            letters = {cmap[ord(ch)] for ch in LETTERS+ACCENTS}
            allowed = numeric | marks | (letters if adjusted_weight else set())
            changed = set()
            for name in after.getGlyphOrder():
                assert before['hmtx'][name][0] == after['hmtx'][name][0], (style, name, 'advance changed')
                if recorded(before, name) != recorded(after, name): changed.add(name)
                if name not in allowed:
                    assert recorded(before, name) == recorded(after, name), (style, name, 'unexpected contour change')
                    assert before['hmtx'][name] == after['hmtx'][name], (style, name, 'unexpected bearing change')
            assert numeric <= changed and marks <= changed, (style, 'refinement missing')
            if adjusted_weight: assert letters <= changed, (style, 'weight refinement missing')
            for ch in LETTERS:
                name = cmap[ord(ch)]
                assert sum(op == 'closePath' for op, _ in recorded(before,name)) == sum(op == 'closePath' for op, _ in recorded(after,name)), (style, ch, 'letter counter changed')
            for ch, count in [('0',2),('6',2),('8',3),('9',2)]:
                assert sum(op == 'closePath' for op, _ in recorded(after,cmap[ord(ch)])) == count, (style, ch, 'figure counter closed')
            for ch,name,count in [('⁰','zero',2),('⁶','six',2),('⁸','eight',3),('⁹','nine',2),
                                  ('₀','zero',2),('₆','six',2),('₈','eight',3),('₉','nine',2)]:
                for glyph in (cmap[ord(ch)],name+'.tf',name+'.numr',name+'.dnom'):
                    assert sum(op == 'closePath' for op,_ in recorded(after,glyph)) == count, (style,glyph,'alternate counter closed')
            for ch in 'hbd':
                assert abs(bounds(after,cmap[ord(ch)])[3]-after['OS/2'].sCapHeight) <= 1, (style, ch, 'cap alignment')
            for ch in 'nmupq':
                assert abs(bounds(after,cmap[ord(ch)])[3]-after['OS/2'].sxHeight) <= 1, (style, ch, 'x-height alignment')
            for ch in '\'"‘’“”':
                assert bounds(after,cmap[ord(ch)])[3] > after['OS/2'].sCapHeight, (style, ch, 'quote lost raised position')
            for table, fields in {
                'head':['unitsPerEm'], 'hhea':['ascent','descent','lineGap'], 'post':['italicAngle'],
                'OS/2':['sxHeight','sCapHeight','usWeightClass','usWidthClass','sTypoAscender',
                        'sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent'],
            }.items():
                for field in fields:
                    assert getattr(before[table],field) == getattr(after[table],field), (style,table,field)
            private = after['CFF '].cff.topDictIndex[0].Private
            old_private = before['CFF '].cff.topDictIndex[0].Private
            for field in ('BlueValues','OtherBlues'):
                assert getattr(private,field) == getattr(old_private,field), (style,field)
            expected_stem = 148 if style.startswith('Light') else 194 if style.startswith('Medium') else old_private.StdVW
            assert private.StdVW == expected_stem, (style,'hint stem',private.StdVW)
            for ch in ('n','0'):
                charstring = after['CFF '].cff.topDictIndex[0].CharStrings[cmap[ord(ch)]]
                charstring.decompile()
                assert any(token in charstring.program for token in ('hstem','hstemhm','vstem','vstemhm')), (style,ch,'hints missing')
            changed_pairs = {p for p in old_pairs[style].keys() | pairs[style].keys() if old_pairs[style].get(p,0) != pairs[style].get(p,0)}
            assert changed_pairs and all(any(ch in MARKS+'0123456789' for ch in p) for p in changed_pairs), (style,'unrelated pair changed')
            for pair in changed_pairs:
                separated(after,pair,False)
                for accent,base in ACCENT_BASE.items():
                    if base in pair: separated(after,pair.replace(base,accent),False)
            for word in WORDS:
                if all(ch in LETTERS+ACCENTS for ch in word):
                    assert shaped(before,word) == shaped(after,word), (style,word,'letter rhythm changed')
            for text in TEXTS:
                assert shaped(before,text,kern=False) == shaped(after,text,kern=False), (style,text,'unspaced layout changed')
                for liga in (True,False): separated(after,text,liga)
            for base,accent in [('ar','ár'),('ur','ür'),('va','và'),('ev','év'),('ly','lý'),('ne','ñé')]:
                assert adjustment(after,base) == adjustment(after,accent), (style,base,accent)
            for pair,value in pairs[style].items():
                if len(pair) == 2 and all(ord(ch) in cmap for ch in pair):
                    assert adjustment(after,pair)[0] == round(value*2), (style,pair,'Lab pair mismatch')
            for subset_name,texts in {
                'latin-basic':['"Entry 12?"',"don't!",'1,234.56','office reflection'],
                'latin-extended':['Áurea Éloi Iñés João Müller Søren Þóra'],
                'symbols-icons':['“Mei’s,” ½ ¼ ¾ · ² ₃ · ☯ ⚡ ▲ ♥'],
            }.items():
                with TTFont(candidate/f'SEIReader-{style}.{subset_name}.woff2') as subset:
                    for text in texts:
                        # Each CSS subset can contain shaping closure but only its own encoded range.
                        codes = subset.getBestCmap()
                        local = ''.join(ch for ch in text if ord(ch) in codes)
                        assert shaped(after,local) == shaped(subset,local), (style,subset_name,local)
            ratio = area(after,cmap[ord('n')])/area(before,cmap[ord('n')])
            if style.startswith('Light'): assert 1.03 < ratio < 1.08, (style,'Light ink',ratio)
            elif style.startswith('Medium'): assert .94 < ratio < .99, (style,'Medium ink',ratio)
            else: assert ratio == 1, (style,'letter weight changed')
            assert area(after,cmap[ord('.')]) < area(before,cmap[ord('.')]), (style,'dot texture')
            if not adjusted_weight:
                assert area(after,cmap[ord('0')]) < area(before,cmap[ord('0')]), (style,'figure texture')
            mass[style] = area(after,cmap[ord('n')])
            print(f'{style}: {len(changed)} intended contours; {len(changed_pairs)} mark/figure pairs; '
                  f'all 295 advances preserved; n ink {100*(ratio-1):+.2f}%; counters, hints, shaping, separation pass')
    for suffix in ('','Italic'):
        keys = ['Light'+suffix,'Italic' if suffix else 'Regular','Medium'+suffix,'SemiBold'+suffix,'Bold'+suffix]
        assert all(mass[a] < mass[b] for a,b in zip(keys,keys[1:])), ('weight order',keys)
    print('All ten styles pass the 0.32 texture and reading-weight audit.')


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv)>1 else None)
