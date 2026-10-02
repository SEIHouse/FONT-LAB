"""Audit SEIReader 0.34's ten Latin alphabet inventories against preserved 0.33.

Check complete encoded coverage and canonical shaping, real language-specific
forms, mark placement, preserved old geometry/spacing, and all web subsets.
"""
from pathlib import Path
import hashlib
import json
import unicodedata

import pathops
from fontTools.ttLib import TTFont

from build_subsets import STYLES, SUBSETS, subset_groups, unicode_range
from language_coverage import inventory, required_characters, test_strings
from verify_latin import shape, positioned_ink, PROSE, MARKS
from verify_lowercase import recorded

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT/'old/0.33'


def no_collisions(font,text,language=None):
    """Compare actual positioned filled contours, including language substitutions."""
    if language is None:
        ink=positioned_ink(font,text)
    else:
        ink=[];x=0;glyphs=font.getGlyphSet()
        for name,advance,dx,dy in shape(font,text,language=language):
            path=pathops.Path();glyphs[name].draw(path.getPen())
            ink.append((name,path.transform(translateX=x+dx,translateY=dy)))
            x+=advance
    for i,(name,a) in enumerate(ink):
        if not a: continue
        _,ymin,_,ymax=a.bounds
        assert ymin>=-font['OS/2'].usWinDescent-1 and ymax<=font['OS/2'].usWinAscent+1,(text,name,'clipping',ymin,ymax)
        for other,b in ink[i+1:]:
            if not b: continue
            intersection=pathops.op(a,b,pathops.PathOp.INTERSECTION)
            assert abs(intersection.area)<.01,(text,name,other,'ink collision')


def verify():
    """Validate real full fonts and their independent subset layout tables."""
    data=inventory();assert len(data['locales'])==10
    current=json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    old=json.loads((BASELINE/'settings.json').read_text(encoding='utf-8'))
    assert current.pop('version')==data['version']=='0.34'
    old.pop('version');assert current==old,'Design settings changed'
    required=set(map(ord,required_characters()))
    old_pairs=json.loads((BASELINE/'kern_styles.json').read_text(encoding='utf-8'))
    pairs=json.loads((ROOT/'kern_styles.json').read_text(encoding='utf-8'))
    language_pairs=json.loads((ROOT/'kern_languages.json').read_text(encoding='utf-8'))
    css=(ROOT/'fonts.css').read_text(encoding='utf-8')
    for manifest,count in [('SHA256.json',10),('SUBSET-SHA256.json',30)]:
        hashes=json.loads((BASELINE/manifest).read_text(encoding='utf-8'))
        assert len(hashes)==count
        for name,digest in hashes.items():
            assert hashlib.sha256((BASELINE/name).read_bytes()).hexdigest()==digest,name
    total=0
    for style,weight,slant in STYLES:
        with TTFont(BASELINE/f'SEIReader-{style}.woff2') as before, TTFont(ROOT/'fonts'/f'SEIReader-{style}.otf') as font:
            old_cmap,cmap=before.getBestCmap(),font.getBestCmap()
            additions=required-set(old_cmap)
            assert len(additions)==94
            assert set(cmap)==set(old_cmap)|required,(style,'encoded inventory scope')
            assert all(cmap[c]==name for c,name in old_cmap.items()),(style,'old cmap')
            assert set(font.getGlyphOrder())-set(before.getGlyphOrder())=={cmap[c] for c in additions}|{'i.loclTRK','i.below.dotless'},(style,'glyph scope')
            for name in before.getGlyphOrder():
                assert recorded(before,name)==recorded(font,name),(style,name,'old outline')
                assert before['hmtx'][name]==font['hmtx'][name],(style,name,'old metrics')
            numeric_pairs = {a+b for a in '0123456789' for b in '.,'} | {a+b for a in '.,' for b in '0123456789'}
            assert {p:v for p,v in pairs[style].items() if all(ord(ch) in old_cmap for ch in p) and p not in numeric_pairs}=={p:v for p,v in old_pairs[style].items() if p not in numeric_pairs},(style,'old nonnumeric pair values')
            assert all(pairs[style][p] == 24 for p in numeric_pairs),(style,'numeric separator spacing')
            for table,fields in {'head':['unitsPerEm'],'hhea':['ascent','descent','lineGap'],
                                 'post':['italicAngle'],'OS/2':['sxHeight','sCapHeight','usWeightClass','usWidthClass','sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent']}.items():
                for field in fields:
                    assert getattr(before[table],field)==getattr(font[table],field),(style,table,field)
            for field in ('BlueValues','OtherBlues','StdVW','StdHW'):
                assert getattr(before['CFF '].cff.topDictIndex[0].Private,field)==getattr(font['CFF '].cff.topDictIndex[0].Private,field),(style,field)
            for text in PROSE:
                for kern in (True,False):
                    for liga in (True,False):
                        expected = shape(before,text,kern=kern,liga=liga)
                        # Keep all old prose positions except the approved decimal correction.
                        if kern:
                            by_name = {(old_cmap[ord(a)],old_cmap[ord(b)]):a+b for a,b in numeric_pairs}
                            adjusted = []
                            for i,(name,advance,dx,dy) in enumerate(expected):
                                pair = by_name.get((name,expected[i+1][0])) if i+1 < len(expected) else None
                                if pair: advance += 48-round(old_pairs[style].get(pair,0)*2)
                                adjusted.append((name,advance,dx,dy))
                            expected = adjusted
                        assert expected==shape(font,text,kern=kern,liga=liga),(style,text,'old prose')
            for feature,text in [('tnum','0123456789'),('sups','123'),('subs','456'),('frac','12/34')]:
                assert shape(before,text,**{feature:1})==shape(font,text,**{feature:1}),(style,feature)
            for code in additions:
                ch=chr(code)
                nfd=unicodedata.normalize('NFD',ch)
                assert shape(font,ch)==shape(font,nfd),(style,ch,'new canonical composition')
                assert font['hmtx'][cmap[code]][0]>0,(style,ch,'empty advance')
                assert recorded(font,cmap[code]),(style,ch,'empty outline')
                for neighbor in ('a','n','r','i','l','v','w','y','.',',','’','“'):
                    no_collisions(font,ch+neighbor)
                    no_collisions(font,neighbor+ch)
            gdef=font['GDEF'].table.GlyphClassDef.classDefs
            for mark in MARKS:
                name=cmap[ord(mark)]
                assert font['hmtx'][name][0]==0 and gdef[name]==3,(style,mark,'mark advance/class')
            for text in ('ị́','ị̀','Ị́','Ị̀','ọ́','ọ̀','Ọ́','ụ́','Ụ̀','r̃','R̃','m̀','M̀'):
                no_collisions(font,text)
                assert shape(font,text)==shape(font,unicodedata.normalize('NFD',text)),(style,text,'stack canonical form')
            assert shape(font,'ị́')[0][0]=='i.below.dotless',(style,'Igbo dot removal')
            assert font['hmtx']['i.below.dotless'][0]==font['hmtx']['i'][0]
            assert recorded(font,'i.loclTRK')==recorded(font,'i') and font['hmtx']['i.loclTRK']==font['hmtx']['i']
            assert recorded(font,cmap[0x131])==recorded(font,'i.dotless')
            assert shape(font,'fi')[0][0]==cmap[0xFB01],(style,'default fi join')
            assert [r[0] for r in shape(font,'fi',language='tr')]==['f','i.loclTRK'],(style,'Turkish dot lost')
            assert shape(font,'fl',language='tr')[0][0]==cmap[0xFB02],(style,'Turkish fl join')
            assert shape(font,'ŞşŢţ',language='ro')==shape(font,'ȘșȚț',language='ro'),(style,'Romanian local forms')
            assert shape(font,'ŞşŢţ',language='tr')!=shape(font,'ȘșȚț',language='tr'),(style,'Turkish cedilla lost')
            for pair in ('TT','TY'):
                delta=language_pairs[style]['hu'].get(pair,0)
                assert sum(r[1] for r in shape(font,pair,language='hu'))==sum(r[1] for r in shape(font,pair))+delta*2,(style,pair,'Hungarian local spacing')
                assert shape(font,pair)==shape(before,pair),(style,pair,'default caps changed')
            assert 'locl' in {r.FeatureTag for r in font['GSUB'].table.FeatureList.FeatureRecord}
            for code,row in data['locales'].items():
                for text in [*test_strings(row),row['sample']]:
                    assert all(ord(ch) in cmap for ch in text),(style,code,text,'missing encoded character')
                    shaped=shape(font,text,language=code)
                    assert all(name!='.notdef' for name,_,_,_ in shaped),(style,code,text,'fallback needed')
                    assert shaped==shape(font,unicodedata.normalize('NFC',text),language=code)
                    assert shaped==shape(font,unicodedata.normalize('NFD',text),language=code),(style,code,text,'canonical mismatch')
                    no_collisions(font,text,code)
                    total+=1
            groups=subset_groups(set(cmap));assert required<=groups['latin-extended']
            for subset_name in SUBSETS:
                with TTFont(ROOT/'fonts'/f'SEIReader-{style}.{subset_name}.woff2') as subset:
                    assert set(subset.getBestCmap())==groups[subset_name],(style,subset_name,'subset coverage')
                    if subset_name=='latin-extended':
                        for code,row in data['locales'].items():
                            for text in [*test_strings(row),row['sample']]:
                                assert shape(font,text,language=code)==shape(subset,text,language=code),(style,subset_name,code,text,'subset shaping')
                block=next(b for b in css.split('@font-face')[1:] if f'SEIReader-{style}.{subset_name}.woff2' in b)
                assert f'font-weight: {weight};' in block and f'font-style: {slant};' in block
                assert f'unicode-range: {unicode_range(groups[subset_name])};' in block
            assert css.index(f'SEIReader-{style}.latin-extended.woff2')>css.index(f'SEIReader-{style}.latin-basic.woff2')
            print(f'{style}: 323 old glyphs/metrics and nonnumeric pairs preserved; decimal fix; 94 letters; all ten alphabets, casing, canonical shaping, local forms, ink clearance, and subsets pass')
    print(f'All ten styles pass; {total} full-font language strings audited with matching Latin-extended shaping.')


if __name__=='__main__':
    verify()
