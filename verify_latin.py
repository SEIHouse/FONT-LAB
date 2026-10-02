"""Audit the additive 0.33 Latin foundation against the preserved 0.32 family.

Checks old contours/metrics/spacing, canonical equivalence, zero-width marks,
attachment, stacks, dotless forms, joined-letter marks, and web delivery.
"""
from pathlib import Path
import hashlib
import io
import json
import unicodedata

import pathops
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from build_subsets import STYLES, SUBSETS, subset_groups, unicode_range
from verify_lowercase import recorded, bounds
from verify_spacing import WORDS

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT/'old/0.32'
MARKS = '\u0300\u0301\u0302\u0303\u0304\u0306\u0307\u0308\u0309\u030a\u030b\u030c\u031b\u0323\u0326\u0327\u0328'
ADDITIONS = MARKS+'‚„‛‟ʻʼ◌\u2009\u202f'
PROSE = WORDS+('“Mei’s,” Iñés said: “Entry 12? Wait… don’t!”',
               '0123456789 1,234.56 8.50% ½¼¾ ²₃ ☯⚡▲♥',
               'To AV P. “A office reflection affinity flame',
               'Áurea Éloi Iñés João Müller Søren Þóra')
CLUSTERS = ('x\u0301','n\u0304','m\u0300','g\u0303','x\u0323',
            'x\u0302\u0301','x\u0302\u0301\u0323','A\u0302\u0301',
            'a\u0302\u0301','i\u0304','j\u0301','i\u0323\u0304',
            'i\u0304\u0323','j\u0323\u0301','o\u031b','a\u0328',
            's\u0326','fl\u0301','fi\u0323','◌\u0307','◌\u0326')
LATIN_TEXTS = ('Café Iñés João Müller garçon',
               'Cafe\u0301 In\u0303e\u0301s Joa\u0303o Mu\u0308ller garc\u0327on',
               '„Lian sagt: ‚Warte!‘“ «\u202fIñés entre.\u202f» Meiʼs Hawaiʻi',
               *CLUSTERS)


def shape(font, text, **features):
    """Shape SFNT bytes with the real layout tables, retaining glyph positions."""
    if not text: return []
    if not hasattr(font,'_latin_shaper'):
        font.flavor = None
        output = io.BytesIO(); font.save(output)
        face = hb.Face(output.getvalue())
        font._latin_shaper = hb.Font(face)
        font._latin_shaper.scale = (face.upem,face.upem)
    buffer = hb.Buffer(); buffer.add_str(text); buffer.guess_segment_properties()
    hb.shape(font._latin_shaper,buffer,features)
    return [(font.getGlyphOrder()[info.codepoint],pos.x_advance,pos.x_offset,pos.y_offset)
            for info,pos in zip(buffer.glyph_infos,buffer.glyph_positions)]


def positioned_ink(font, text):
    """Build actual filled contours at shaped positions for collision/height checks."""
    glyphs = font.getGlyphSet()
    if not hasattr(font,'_latin_outlines'): font._latin_outlines = {}
    x = 0; ink = []
    for name,advance,dx,dy in shape(font,text):
        if name not in font._latin_outlines:
            path = pathops.Path(); glyphs[name].draw(path.getPen())
            font._latin_outlines[name] = path
        path = font._latin_outlines[name].transform(translateX=x+dx,translateY=dy)
        ink.append((name,path))
        x += advance
    return ink


def verify():
    previous = json.loads((BASELINE/'settings.json').read_text(encoding='utf-8'))
    current = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    assert current['version']=='0.33'
    previous.pop('version'); current.pop('version')
    assert current==previous, 'Nominal setting changed'
    for manifest,count in [('SHA256.json',10),('SUBSET-SHA256.json',30)]:
        hashes = json.loads((BASELINE/manifest).read_text(encoding='utf-8'))
        assert len(hashes)==count
        for filename,digest in hashes.items():
            assert hashlib.sha256((BASELINE/filename).read_bytes()).hexdigest()==digest, filename
    old_pairs = json.loads((BASELINE/'kern_styles.json').read_text(encoding='utf-8'))
    pairs = json.loads((ROOT/'kern_styles.json').read_text(encoding='utf-8'))
    css = (ROOT/'fonts.css').read_text(encoding='utf-8')
    assert css.count('@font-face')==30
    for style,weight,slant in STYLES:
        with TTFont(BASELINE/f'SEIReader-{style}.woff2') as before, TTFont(ROOT/'fonts'/f'SEIReader-{style}.otf') as after:
            old_cmap,cmap = before.getBestCmap(),after.getBestCmap()
            assert {c:cmap[c] for c in old_cmap}==old_cmap, (style,'existing Unicode changed')
            assert set(cmap)-set(old_cmap)==set(map(ord,ADDITIONS)), (style,'addition scope')
            for name in before.getGlyphOrder():
                assert recorded(before,name)==recorded(after,name), (style,name,'outline changed')
                assert before['hmtx'][name]==after['hmtx'][name], (style,name,'metric changed')
            old_codes = set(old_cmap)
            assert {p:v for p,v in pairs[style].items() if all(ord(c) in old_codes for c in p)}==old_pairs[style], (style,'existing pair changed')
            for pair in pairs[style]:
                if not any(ch in '‚„‛‟ʻʼ' for ch in pair): continue
                ink = positioned_ink(after,pair)
                if len(ink)==2:
                    overlap = pathops.op(ink[0][1],ink[1][1],pathops.PathOp.INTERSECTION)
                    assert abs(overlap.area)<.01, (style,pair,'new quote collision')
            for table,fields in {
                'head':['unitsPerEm'],'hhea':['ascent','descent','lineGap'],
                'post':['italicAngle'],
                'OS/2':['sxHeight','sCapHeight','usWeightClass','usWidthClass','sTypoAscender',
                        'sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent'],
            }.items():
                for field in fields:
                    assert getattr(before[table],field)==getattr(after[table],field), (style,table,field)
            for field in ('BlueValues','OtherBlues','StdVW','StdHW'):
                assert getattr(before['CFF '].cff.topDictIndex[0].Private,field)==getattr(after['CFF '].cff.topDictIndex[0].Private,field), (style,field)
            for text in PROSE:
                for liga in (True,False):
                    for kern in (True,False):
                        assert shape(before,text,kern=kern,liga=liga)==shape(after,text,kern=kern,liga=liga), (style,text,'old shaping changed')
            for ch in '0123456789':
                for feature in ('tnum','sups','subs'):
                    assert shape(before,ch,**{feature:1})==shape(after,ch,**{feature:1}), (style,ch,feature)
            assert shape(before,'12/34',frac=1)==shape(after,'12/34',frac=1), style
            gdef = after['GDEF'].table.GlyphClassDef.classDefs
            for ch in MARKS:
                name = cmap[ord(ch)]
                assert after['hmtx'][name][0]==0 and gdef[name]==3, (style,name,'mark width/class')
            for table,features in [('GSUB',{'ccmp'}),('GPOS',{'mark','mkmk'})]:
                actual = {r.FeatureTag for r in after[table].table.FeatureList.FeatureRecord}
                assert features<=actual, (style,table,actual)
            for ch in map(chr,old_cmap):
                if unicodedata.normalize('NFD',ch)!=ch:
                    assert shape(after,ch)==shape(after,unicodedata.normalize('NFD',ch)), (style,ch,'NFC/NFD mismatch')
            for text in CLUSTERS:
                assert shape(after,text)==shape(after,unicodedata.normalize('NFC',text)), (style,text,'canonical composition')
                assert shape(after,text)==shape(after,unicodedata.normalize('NFD',text)), (style,text,'canonical decomposition')
                result = shape(after,text)
                assert all(name!='.notdef' for name,_,_,_ in result), (style,text,'missing glyph')
                assert all(advance==0 for name,advance,_,_ in result if gdef.get(name)==3), (style,text,'mark added width')
                for name,path in positioned_ink(after,text):
                    if not path: continue
                    _,ymin,_,ymax = path.bounds
                    assert ymin>=-after['OS/2'].usWinDescent-1 and ymax<=after['OS/2'].usWinAscent+1, (style,text,name,'clipping',ymin,ymax)
            for text in ('x\u0301','n\u0304','m\u0300','g\u0303','x\u0323',
                         'x\u0302\u0301','x\u0302\u0301\u0323','A\u0302\u0301',
                         'i\u0304','j\u0301','i\u0323\u0304','j\u0323\u0301','fl\u0301'):
                ink = positioned_ink(after,text)
                for i,(_,a) in enumerate(ink):
                    for _,b in ink[i+1:]:
                        overlap = pathops.op(a,b,pathops.PathOp.INTERSECTION)
                        assert abs(overlap.area)<.01, (style,text,'base/mark or mark/mark collision')
            for text,base in [('i\u0304','i'),('j\u0301','j'),('i\u0323\u0304','i')]:
                result = shape(after,text)
                assert result[0][0]==base+'.dotless', (style,text,'dot not removed')
                assert sum(p[1] for p in result)==after['hmtx'][base][0], (style,text,'base width changed')
            for ch in 'ij':
                assert after['hmtx'][ch+'.dotless'][0]==after['hmtx'][ch][0]
                assert sum(op=='closePath' for op,_ in recorded(after,ch+'.dotless'))==sum(op=='closePath' for op,_ in recorded(after,ch))-1, (style,ch,'dotless contour')
            for text in ('nx\u0301a','ri\u0304v','fl\u0301a'):
                plain = ''.join(c for c in text if c not in MARKS)
                assert sum(p[1] for p in shape(after,text))==sum(p[1] for p in shape(after,plain)), (style,text,'kerning lost across mark')
            assert shape(after,'i\u0323\u0304')==shape(after,'i\u0304\u0323'), (style,'canonical mark order')
            assert shape(after,'x\u0302\u0301')!=shape(after,'x\u0302\u0301',mkmk=False), (style,'stack feature ineffective')
            assert shape(after,'x\u0301')!=shape(after,'x\u0301',mark=False), (style,'attachment feature ineffective')
            for text,code in [('fl\u0301',0xFB02),('fi\u0323',0xFB01)]:
                assert shape(after,text)[0][0]==cmap[code] and gdef[cmap[code]]==2, (style,text,'ligature class')
                assert shape(after,text)[1][2]>-after['hmtx'][cmap[code]][0]*.55, (style,text,'wrong ligature component')
            for new,old in [('ʻ','‘'),('ʼ','’')]:
                assert recorded(after,cmap[ord(new)])==recorded(after,cmap[ord(old)]), (style,new,'apostrophe drawing')
                assert after['hmtx'][cmap[ord(new)]]==after['hmtx'][cmap[ord(old)]], (style,new,'apostrophe width')
            for ch in '‚„':
                assert bounds(after,cmap[ord(ch)])[3]<after['OS/2'].sxHeight*.35, (style,ch,'low quote too high')
            for ch in '‛‟':
                assert bounds(after,cmap[ord(ch)])[3]>after['OS/2'].sCapHeight, (style,ch,'reversed quote too low')
            for ch in '\u2009\u202f':
                assert after['hmtx'][cmap[ord(ch)]][0]==240 and not recorded(after,cmap[ord(ch)]), (style,ch,'narrow space')
            groups = subset_groups(set(cmap))
            for subset_name in SUBSETS:
                path = ROOT/'fonts'/f'SEIReader-{style}.{subset_name}.woff2'
                with TTFont(path) as subset:
                    assert set(subset.getBestCmap())==groups[subset_name], (style,subset_name,'coverage')
                    texts = LATIN_TEXTS if subset_name=='latin-extended' else [''.join(c for c in t if ord(c) in groups[subset_name]) for t in PROSE]
                    for text in texts:
                        assert shape(after,text)==shape(subset,text), (style,subset_name,text,'subset shaping')
                block = next(b for b in css.split('@font-face')[1:] if f'SEIReader-{style}.{subset_name}.woff2' in b)
                assert f'font-weight: {weight};' in block and f'font-style: {slant};' in block
                assert f'unicode-range: {unicode_range(groups[subset_name])};' in block
            assert groups['latin-basic']<=groups['latin-extended']
            assert css.index(f'SEIReader-{style}.latin-extended.woff2')>css.index(f'SEIReader-{style}.latin-basic.woff2'), (style,'Latin face precedence')
            print(f'{style}: all 295 old outlines/metrics and pair values preserved; 26 additions; '
                  'canonical text, attachment, stacks, dotless, ligatures, and subsets pass')
    print('All ten styles pass the additive Latin-foundation audit.')


if __name__=='__main__':
    verify()
