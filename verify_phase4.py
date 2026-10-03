"""Audit additive Phase 4 coverage, old glyphs/spacing, canonical shaping and delivery.

python verify_phase4.py [--baseline PREVIOUS_STEP_COMMIT]
The baseline is read from Git without switching or modifying any checkout.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import unicodedata

import pathops
from fontTools.ttLib import TTFont
from build_subsets import STYLES, SUBSETS, subset_groups, unicode_range
from language_coverage import inventory, required_characters, test_strings
from verify_latin import shape, PROSE
from verify_lowercase import recorded, bounds
from verify_stroke_joins import missing_ink, outline

ROOT = Path(__file__).resolve().parent

def historical(ref, file):
    """Read a committed file without disturbing another agent's branch."""
    return subprocess.check_output(['git','show',f'{ref}:{file}'],cwd=ROOT)

def check_ink(font, text, language=None):
    """Check real positioned contours for inter-glyph collisions and clipping."""
    x=0; ink=[]
    for name,advance,dx,dy in shape(font,text,language=language):
        if not hasattr(font,'_phase4_ink'): font._phase4_ink={}
        if name not in font._phase4_ink: font._phase4_ink[name]=outline(font,name)
        path=font._phase4_ink[name].transform(translateX=x+dx,translateY=dy)
        x+=advance
        if not path: continue
        assert path.bounds[1]>=-font['OS/2'].usWinDescent-1 and path.bounds[3]<=font['OS/2'].usWinAscent+1,(text,name,'clipping',path.bounds)
        for other,b in ink:
            if path.bounds[0]>b.bounds[2] or b.bounds[0]>path.bounds[2]: continue
            assert abs(pathops.op(path,b,pathops.PathOp.INTERSECTION).area)<1,(text,other,name,'collision')
        ink.append((name,path))

def verify(baseline=None):
    """Require exact preservation and validate every addition in all ten masters."""
    release=json.loads((ROOT/'phase4.json').read_text(encoding='utf-8'))
    ref=baseline or release['baseline_commit']
    assert json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))==json.loads(historical(ref,'settings.json')),'Existing settings changed'
    previous_pairs=json.loads(historical(ref,'kern_styles.json'))
    current_pairs=json.loads((ROOT/'kern_styles.json').read_text(encoding='utf-8'))
    previous_locales=json.loads(historical(ref,'languages.json'))['locales']
    required=set(map(ord,required_characters()))|set(range(0x100,0x180))
    if release['step']>=2:
        required.update(range(0x400,0x460));required.update([0x490,0x491])
        required.update(map(ord,'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρσςτυφχψωΆΈΉΊΌΎΏάέήίόύώΪΫϊϋΐΰ'))
    css=(ROOT/'fonts.css').read_text(encoding='utf-8');total=0
    for style,weight,slant in STYLES:
        before=TTFont(io.BytesIO(historical(ref,f'fonts/SEIReader-{style}.woff2')))
        font=TTFont(ROOT/'fonts'/f'SEIReader-{style}.otf')
        old_cmap,cmap=before.getBestCmap(),font.getBestCmap()
        assert required<=set(cmap),(style,'missing coverage',[hex(c) for c in sorted(required-set(cmap))])
        assert all(cmap[c]==name for c,name in old_cmap.items()),(style,'old cmap changed')
        for name in before.getGlyphOrder():
            assert recorded(before,name)==recorded(font,name),(style,name,'existing outline changed')
            assert before['hmtx'][name]==font['hmtx'][name],(style,name,'existing metrics changed')
        assert all(current_pairs[style].get(pair,0)==value for pair,value in previous_pairs[style].items()),(style,'existing pairs changed')
        assert not any(pair not in previous_pairs[style] and all(ord(c) in old_cmap for c in pair) for pair in current_pairs[style]),(style,'new old-character pair')
        for table,fields in {'head':['unitsPerEm'],'hhea':['ascent','descent','lineGap'],'post':['italicAngle'],
            'OS/2':['sxHeight','sCapHeight','usWeightClass','usWidthClass','sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent']}.items():
            for field in fields: assert getattr(before[table],field)==getattr(font[table],field),(style,table,field)
        for field in ('BlueValues','OtherBlues','StdVW','StdHW'):
            assert getattr(before['CFF '].cff.topDictIndex[0].Private,field)==getattr(font['CFF '].cff.topDictIndex[0].Private,field),(style,field)
        texts=list(PROSE)+[pair for pair in previous_pairs[style]]
        for text in texts:
            assert shape(before,text)==shape(font,text),(style,text,'existing shaping changed')
        for code,row in previous_locales.items():
            assert shape(before,row['sample'],language=code)==shape(font,row['sample'],language=code),(style,code,'existing local shaping changed')
        for feature,text in [('tnum','0123456789'),('sups','123'),('subs','456'),('frac','12/34')]:
            assert shape(before,text,**{feature:1})==shape(font,text,**{feature:1}),(style,feature)
        additions=set(cmap)-set(old_cmap)
        for code in additions:
            name=cmap[code];b=bounds(font,name)
            assert b is not None,(style,hex(code),'empty addition')
            assert b[1]>=-font['OS/2'].usWinDescent-1 and b[3]<=font['OS/2'].usWinAscent+1,(style,hex(code),'glyph clipping',b)
            assert missing_ink(outline(font,name))<1,(style,name,'ambiguous outline')
            nfd=unicodedata.normalize('NFD',chr(code))
            if all(ord(c) in cmap for c in nfd):
                assert shape(font,chr(code))==shape(font,nfd),(style,chr(code),'canonical composition')
            if not unicodedata.combining(chr(code)):
                for neighbor in ('a','n','i','l','.',',','’','“'):
                    check_ink(font,chr(code)+neighbor);check_ink(font,neighbor+chr(code))
        gdef=font['GDEF'].table.GlyphClassDef.classDefs
        for code,name in cmap.items():
            if unicodedata.combining(chr(code)):
                assert font['hmtx'][name][0]==0 and gdef.get(name)==3,(style,hex(code),'mark class/advance')
        groups=subset_groups(set(cmap))
        with TTFont(ROOT/'fonts'/f'SEIReader-{style}.woff2') as full_web:
            for table in ('CFF ','hmtx','GPOS','GSUB','GDEF'):
                assert font[table].compile(font)==full_web[table].compile(full_web),(style,table,'OTF/web mismatch')
        for name in SUBSETS:
            with TTFont(ROOT/'fonts'/f'SEIReader-{style}.{name}.woff2') as web:
                assert set(web.getBestCmap())==groups[name],(style,name,'subset cmap')
                for glyph in web.getGlyphOrder():
                    assert web['hmtx'][glyph]==font['hmtx'][glyph],(style,name,glyph,'subset metrics')
                    if glyph!='.notdef':
                        assert recorded(web,glyph)==recorded(font,glyph),(style,name,glyph,'subset outline')
            block=next(b for b in css.split('@font-face')[1:] if f'SEIReader-{style}.{name}.woff2' in b)
            assert f'font-weight: {weight};' in block and f'font-style: {slant};' in block
            assert f'unicode-range: {unicode_range(groups[name])};' in block
        for code,row in inventory()['locales'].items():
            delivery={'Latn':'vietnamese' if code=='vi' else 'latin-ext-2','Cyrl':'cyrillic','Grek':'greek'}[row['script']]
            with TTFont(ROOT/'fonts'/f'SEIReader-{style}.{delivery}.woff2') as web:
                for text in [*test_strings(row),row['sample']]:
                    shaped=shape(font,text,language=code)
                    assert all(name!='.notdef' for name,_,_,_ in shaped),(style,code,text,'fallback')
                    assert shaped==shape(font,unicodedata.normalize('NFD',text),language=code),(style,code,text,'NFD mismatch')
                    assert shaped==shape(web,text,language=code),(style,code,text,'subset shaping')
                    check_ink(font,text,code);total+=1
        before.close();font.close()
        print(f'{style}: {len(before.getGlyphOrder())} previous glyphs/metrics, old pairs/layout preserved; {len(additions)} additions and {len(SUBSETS)} deliveries pass',flush=True)
    print(f'Phase 4 step {release["step"]}: all ten styles; {total:,} language strings; unchanged settings and old design.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline')
    verify(parser.parse_args().baseline)
