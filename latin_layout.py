"""OpenType attachment and composition for SEIReader's additive Latin foundation."""
import unicodedata

def latin_features(records, origins, advances, cmap, scale, slant, center):
    """Use exported source anchors with the exact outline offset and italic shear."""
    def point(name, xy):
        x, y = xy
        return f'<anchor {round((x+origins[name]+slant*(y-center))*scale)} {round(y*scale)}>'

    classes = {kind:[] for kind in ('top','bottom','horn','ogonek')}
    for name, record in records.items():
        if record.get('mark'): classes[record['mark']].append(name)
    lines = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;',
             'languagesystem latn TRK;', 'languagesystem latn ROM;',
             'languagesystem latn HUN;']
    for kind, names in classes.items():
        lines.append(f'@{kind.upper()} = [{" ".join(names)}];')
        for name in names:
            lines.append(f'markClass {name} {point(name,records[name]["attach"])} @MC_{kind};')
    # An identical Turkish i stays dotted instead of disappearing into the fi join.
    # Romanian legacy cedilla text gets the modern comma forms only under lang=ro.
    lines += ['feature locl {', ' script latn;', ' language TRK;',
              ' sub i by i.loclTRK;', ' language ROM;']
    for old,new in zip('ŞşŢţ','ȘșȚț'):
        lines.append(f' sub {cmap[ord(old)]} by {cmap[ord(new)]};')
    lines.append('} locl;')
    # Existing precomposed drawings stay byte-for-byte equivalent after decomposition.
    lines.append('feature ccmp {')
    for code, name in cmap.items():
        chars = unicodedata.normalize('NFD',chr(code))
        if len(chars)==2 and all(ord(ch) in cmap for ch in chars):
            base, mark = (cmap[ord(ch)] for ch in chars)
            if records.get(mark,{}).get('mark'):
                lines.append(f' sub {base} {mark} by {name};')
                if base=='i': lines.append(f' sub i.loclTRK {mark} by {name};')
    lines += [' lookup Dotless {', '  lookupflag UseMarkFilteringSet @TOP;',
              '  sub i\' @TOP by i.dotless;', '  sub j\' @TOP by j.dotless;',
              '  sub i.loclTRK\' @TOP by i.dotless;',
              f'  sub {cmap[0x1ECB]}\' @TOP by i.below.dotless;',
              ' } Dotless;', '} ccmp;', 'feature mark {']
    ligatures = {cmap[code] for code in (0xFB01,0xFB02)}
    for name, record in records.items():
        if record.get('mark') or 'anchors' not in record: continue
        if name in ligatures: continue
        anchors = ' '.join(f'{point(name,xy)} mark @MC_{kind}' for kind,xy in record['anchors'].items())
        lines.append(f' pos base {name} {anchors};')
    # Marks on joined fi/fl can attach to either component instead of the next letter.
    for lig in sorted(ligatures):
        anchors = records[lig]['anchors']
        def component(x):
            return ' '.join(f'{point(lig,[x,xy[1]])} mark @MC_{kind}' for kind,xy in anchors.items())
        cut = advances['f']/scale
        first = cut/2-origins[lig]
        last = (cut+advances[lig]/scale)/2-origins[lig]
        lines.append(f' pos ligature {lig} {component(first)} ligComponent {component(last)};')
    lines += ['} mark;', 'feature mkmk {']
    # Filter other mark classes so above/below stacks remain independent.
    for kind in ('top','bottom'):
        lines += [f' lookup Stack_{kind} {{',f'  lookupflag MarkAttachmentType @{kind.upper()};']
        for name in classes[kind]:
            lines.append(f'  pos mark {name} {point(name,records[name]["anchors"][kind])} mark @MC_{kind};')
        lines.append(f' }} Stack_{kind};')
    lines.append('} mkmk;')
    return '\n'.join(lines)+'\n'
