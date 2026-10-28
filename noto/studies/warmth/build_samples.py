"""Original, limited Latin warmth studies. No existing font supplies outline data.

Run from the repository with .venv/Scripts/python.exe noto/studies/warmth/build_samples.py.
The separately licensed, unchanged Noto reference is used only by the specimen HTML.
"""
from __future__ import annotations

import hashlib
import base64
import html
import json
import math
from pathlib import Path
import urllib.request

import pathops
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.svgLib.path import parse_path
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ROOT = Path(__file__).resolve().parent
UPM = 1000
STROKE = 74
REFERENCE_COMMIT = "9862abc066c9b83bf84c3e8ed1fc2d8d48f9bbf0"
STUDIES = [
    dict(id="A", name="Subtle", cap=3, fullness=.545, width=1.0),
    dict(id="B", name="Balanced", cap=14, fullness=.585, width=1.025),
    dict(id="C", name="Pronounced", cap=29, fullness=.625, width=1.05),
]


def outline(d):
    p = pathops.Path()
    parse_path(d, p.getPen())
    return p


def ellipse(x0, y0, x1, y1, k=.55228475):
    cx, cy = (x0+x1)/2, (y0+y1)/2
    rx, ry = (x1-x0)/2, (y1-y0)/2
    p = pathops.Path()
    p.moveTo(cx, y1)
    p.cubicTo(cx+k*rx, y1, x1, cy+k*ry, x1, cy)
    p.cubicTo(x1, cy-k*ry, cx+k*rx, y0, cx, y0)
    p.cubicTo(cx-k*rx, y0, x0, cy-k*ry, x0, cy)
    p.cubicTo(x0, cy+k*ry, cx-k*rx, y1, cx, y1)
    p.close()
    return p


def soft_cap(point, outward, radius):
    """Round the two corners of a flat terminal, independently of stroke thickness."""
    h = STROKE/2
    r = radius
    p = outline(f"M0 {-h} Q{r} {-h} {r} {-h+r} L{r} {h-r} Q{r} {h} 0 {h} Z")
    dx, dy = outward
    length = math.hypot(dx, dy)
    if not length:
        return pathops.Path()
    ux, uy = dx/length, dy/length
    return p.transform(ux, uy, -uy, ux, *point)


class Drawing:
    def __init__(self, study):
        self.study = study
        self.p = pathops.Path()

    def stroke(self, d):
        p = outline(d)
        record = RecordingPen()
        parse_path(d, record)
        commands = record.value
        p.stroke(STROKE, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 2)
        self.p.addPath(p)
        # Each call is one continuous path, with separate caps for open contours.
        if commands[-1][0] != "closePath":
            segments = [(op, pts) for op, pts in commands if op not in ("endPath", "closePath")]
            first = segments[0][1][0]
            nxt = segments[1][1][0]
            last = segments[-1][1][-1]
            prev = segments[-1][1][-2] if len(segments[-1][1]) > 1 else segments[-2][1][-1]
            self.p.addPath(soft_cap(first, (first[0]-nxt[0], first[1]-nxt[1]), self.study["cap"]))
            self.p.addPath(soft_cap(last, (last[0]-prev[0], last[1]-prev[1]), self.study["cap"]))
        return self

    def bowl(self, x0, y0, x1, y1):
        p = ellipse(x0, y0, x1, y1, self.study["fullness"])
        p.stroke(STROKE, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 2)
        self.p.addPath(p)
        return self

    def dot(self, x, y, size=42):
        self.p.addPath(ellipse(x-size, y-size, x+size, y+size, self.study["fullness"]))
        return self


def draw_alphabet(study):
    g = {}
    def put(ch, width, paths=(), bowls=(), dots=()):
        d = Drawing(study)
        for path in paths: d.stroke(path)
        for box in bowls: d.bowl(*box)
        for dot in dots: d.dot(*dot)
        g[ch] = (width, d.p)

    # Original centerlines and cubic contours, independently drawn for these studies.
    put('a', 535, ["M117 444 C178 516 343 524 405 451 C432 417 428 365 428 320 L428 36",
                   "M428 281 C337 297 87 282 87 155 C87 45 201 12 306 44 C369 63 408 104 428 155"])
    put('b', 555, ["M101 710 L101 36", "M101 380 C148 492 251 530 345 485 C464 434 486 166 393 78 C299 -16 157 43 101 150"])
    put('c', 500, ["M418 446 C333 530 187 522 114 416 C48 320 58 157 130 82 C205 6 339 18 425 91"])
    put('d', 555, ["M448 710 L448 36", "M448 380 C401 492 298 530 204 485 C85 434 63 166 156 78 C250 -16 392 43 448 150"])
    put('e', 530, ["M86 278 L439 278 C446 407 374 506 269 506 C153 507 79 400 79 269 C79 101 165 30 287 30 C345 30 405 52 446 87"])
    put('f', 338, ["M139 36 L139 565 C139 680 188 734 293 706", "M56 491 L294 491"])
    put('g', 559, ["M408 455 C443 507 485 509 514 493", "M166 238 C97 178 129 123 220 104"], [(101,236,427,499),(98,-180,454,103)])
    put('h', 557, ["M100 710 L100 36", "M100 367 C161 493 272 531 363 478 C418 447 450 382 450 291 L450 36"])
    put('i', 246, ["M123 493 L123 36"], dots=[(123,674,44)])
    put('j', 267, ["M162 493 L162 -55 C162 -164 111 -198 25 -175"], dots=[(162,674,44)])
    put('k', 510, ["M101 710 L101 36", "M442 492 L102 205", "M262 341 L454 36"])
    put('l', 263, ["M116 710 L116 104 C116 46 140 27 201 37"])
    put('m', 842, ["M100 493 L100 36", "M100 366 C150 481 244 525 324 481 C387 448 403 383 403 296 L403 36", "M403 366 C454 482 548 526 628 481 C690 447 735 392 735 296 L735 36"])
    put('n', 557, ["M100 493 L100 36", "M100 367 C161 493 272 531 363 478 C418 447 450 382 450 291 L450 36"])
    put('o', 550, bowls=[(84,30,466,506)])
    put('p', 555, ["M101 493 L101 -185", "M101 380 C148 492 251 530 345 485 C464 434 486 166 393 78 C299 -16 157 43 101 150"])
    put('q', 555, ["M448 493 L448 -185", "M448 380 C401 492 298 530 204 485 C85 434 63 166 156 78 C250 -16 392 43 448 150"])
    put('r', 371, ["M101 493 L101 36", "M101 358 C150 471 232 526 327 491"])
    put('s', 475, ["M393 443 C319 516 190 529 119 458 C59 396 104 316 231 278 C362 239 417 184 384 107 C350 16 185 2 86 83"])
    put('t', 352, ["M148 646 L148 152 C148 57 183 16 296 47", "M56 491 L297 491"])
    put('u', 557, ["M100 493 L100 228 C100 137 132 72 187 41 C278 -12 389 26 450 152", "M450 493 L450 36"])
    put('v', 487, ["M66 491 L244 39 L422 491"])
    put('w', 752, ["M65 492 L205 40 L376 476 L547 40 L687 492"])
    put('x', 487, ["M74 491 L413 36", "M413 491 L74 36"])
    put('y', 494, ["M66 491 L249 47", "M430 491 L213 -49 C179 -144 140 -193 54 -172"])
    put('z', 469, ["M82 493 L389 493 L80 36 L399 36"])

    put('A', 652, ["M65 36 L324 680 L586 36", "M157 264 L494 264"])
    put('B', 622, ["M110 36 L110 680 L310 680 C590 680 591 374 316 374 L110 374", "M316 374 C615 374 623 36 314 36 L110 36"])
    put('C', 656, ["M566 602 C453 724 239 731 126 563 C28 422 59 173 185 74 C287 -5 470 5 575 117"])
    put('D', 672, ["M111 36 L111 680 L282 680 C488 680 581 553 581 358 C581 160 488 36 282 36 Z"])
    put('E', 560, ["M477 680 L111 680 L111 36 L487 36", "M111 370 L434 370"])
    put('F', 538, ["M477 680 L111 680 L111 36", "M111 370 L426 370"])
    put('G', 704, ["M596 604 C475 729 259 725 140 566 C34 420 65 168 190 75 C304 -9 502 8 596 105 L596 319 L406 319"])
    put('H', 702, ["M111 680 L111 36", "M591 680 L591 36", "M111 363 L591 363"])
    put('I', 325, ["M77 680 L248 680", "M162 680 L162 36", "M77 36 L248 36"])
    put('J', 435, ["M328 680 L328 203 C328 35 229 -11 76 61"])
    put('K', 625, ["M111 680 L111 36", "M546 680 L111 262", "M311 454 L566 36"])
    put('L', 527, ["M111 680 L111 36 L464 36"])
    put('M', 840, ["M111 36 L111 680 L420 147 L729 680 L729 36"])
    put('N', 706, ["M111 36 L111 680 L595 36 L595 680"])
    put('O', 711, bowls=[(82,30,629,686)])
    put('P', 604, ["M111 36 L111 680 L313 680 C582 680 579 349 313 349 L111 349"])
    put('Q', 711, ["M431 189 L639 -72"], [(82,30,629,686)])
    put('R', 626, ["M111 36 L111 680 L313 680 C582 680 579 349 313 349 L111 349", "M326 349 L561 36"])
    put('S', 588, ["M493 606 C409 701 230 724 134 630 C51 546 98 415 270 360 C449 305 530 226 467 111 C406 1 219 -4 90 100"])
    put('T', 587, ["M52 680 L535 680", "M293 680 L293 36"])
    put('U', 695, ["M105 680 L105 251 C105 -44 590 -44 590 251 L590 680"])
    put('V', 640, ["M65 680 L320 36 L575 680"])
    put('W', 921, ["M65 680 L250 36 L461 635 L671 36 L856 680"])
    put('X', 616, ["M77 680 L539 36", "M539 680 L77 36"])
    put('Y', 620, ["M64 680 L310 361 L556 680", "M310 361 L310 36"])
    put('Z', 599, ["M88 680 L511 680 L85 36 L514 36"])

    put('0', 557, bowls=[(97,30,460,686)])
    put('1', 557, ["M118 544 L292 680 L292 36", "M128 36 L456 36"])
    put('2', 557, ["M97 552 C110 734 441 735 451 557 C462 425 347 353 104 36 L465 36"])
    put('3', 557, ["M100 609 C230 749 457 690 450 542 C444 407 347 365 253 365", "M254 365 C508 389 524 144 412 60 C313 -13 180 21 91 99"])
    put('4', 557, ["M377 36 L377 680 L76 226 L486 226"])
    put('5', 557, ["M443 680 L145 680 L120 397 C237 458 419 417 451 271 C504 29 222 -33 92 101"])
    put('6', 557, ["M423 639 C289 757 109 611 99 345 L99 232", "M99 241 C99 481 460 481 460 241 C460 -42 99 -42 99 241 Z"])
    put('7', 557, ["M89 680 L465 680 L217 36"])
    put('8', 557, bowls=[(105,374,452,686),(90,30,467,374)])
    put('9', 557, ["M134 77 C268 -41 448 105 458 371 L458 484", "M458 475 C458 235 97 235 97 475 C97 758 458 758 458 475 Z"])
    put(' ', 255)
    put('.', 238, dots=[(119,41,42)])
    put(',', 238, ["M139 44 C141 -16 121 -56 82 -88"], dots=[(132,44,38)])
    put(':', 238, dots=[(119,41,42),(119,395,42)])
    put(';', 238, ["M139 44 C141 -16 121 -56 82 -88"], dots=[(132,44,38),(119,395,42)])
    put('!', 252, ["M126 680 L126 206"], dots=[(126,41,42)])
    put('?', 478, ["M78 595 C150 727 366 712 392 586 C419 462 241 424 241 279 L241 205"], dots=[(241,41,42)])
    put('-', 370, ["M78 260 L292 260"])
    put('–', 590, ["M65 260 L525 260"])
    put('—', 900, ["M65 260 L835 260"])
    put("'", 218, ["M109 680 L99 548"])
    put('’', 218, ["M129 680 C145 622 121 568 81 536"])
    put('‘', 218, ["M137 695 C96 658 75 602 91 548"])
    put('“', 382, ["M140 695 C99 658 78 602 94 548", "M304 695 C263 658 242 602 258 548"])
    put('”', 382, ["M129 680 C145 622 121 568 81 536", "M293 680 C309 622 285 568 245 536"])
    put('"', 382, ["M109 680 L99 548", "M273 680 L263 548"])
    put('(', 295, ["M222 746 C18 512 18 141 222 -93"])
    put(')', 295, ["M73 746 C277 512 277 141 73 -93"])
    put('/', 425, ["M70 -25 L355 716"])
    put('&', 683, ["M576 325 C530 116 385 1 221 42 C84 72 54 186 142 292 L364 526 C474 651 302 759 206 662 C88 544 355 284 596 42"])
    put('+', 557, ["M96 320 L461 320", "M278 503 L278 137"])
    put('=', 557, ["M96 410 L461 410", "M96 230 L461 230"])
    put('·', 238, dots=[(119,267,35)])
    # Small accent inventory for the specimen, not a language-coverage claim.
    accents = {'é':('e','acute'), 'á':('a','acute'), 'í':('i','acute'),
               'ó':('o','acute'), 'ú':('u','acute'), 'ö':('o','diaeresis'),
               'ü':('u','diaeresis'), 'ñ':('n','tilde'), 'è':('e','grave')}
    for ch, (base, accent) in accents.items():
        width, original = g[base]
        p = pathops.Path()
        if base == 'i':
            base_d = Drawing(study).stroke("M123 493 L123 36")
            p.addPath(base_d.p)
        else: p.addPath(original)
        d = Drawing(study)
        mid = width/2
        if accent == 'acute': d.stroke(f"M{mid-38} 626 L{mid+60} 729")
        elif accent == 'grave': d.stroke(f"M{mid+38} 626 L{mid-60} 729")
        elif accent == 'diaeresis':
            d.dot(mid-90,668,35).dot(mid+90,668,35)
        else: d.stroke(f"M{mid-118} 644 C{mid-56} 756 {mid+29} 586 {mid+118} 695")
        p.addPath(d.p)
        g[ch] = (width,p)
    return g


def build_font(study):
    source = draw_alphabet(study)
    glyphs = {'.notdef': (600, Drawing(study).stroke('M90 30 L90 680 L510 680 L510 30 Z').p)}
    cmap = {}
    for char, (width, path) in source.items():
        name = 'space' if char == ' ' else f'u{ord(char):04X}'
        cmap[ord(char)] = name
        glyphs[name] = (round(width*study['width']), path.transform(study['width'],0,0,1,0,0))
    order = list(glyphs)
    metrics, charstrings = {}, {}
    for name, (width,path) in glyphs.items():
        if list(path.verbs):
            path.convertConicsToQuads(0.01)
            path.simplify(fix_winding=True)
            path.convertConicsToQuads(0.01)
        pen = T2CharStringPen(width, None)
        path.draw(pen)
        charstrings[name] = pen.getCharString(private=None, globalSubrs=None)
        metrics[name] = (width, round(path.bounds[0]) if list(path.verbs) else 0)
    family = f"SEIHouse Noto Study {study['id']}"
    psname = f"SEIHouseNotoStudy{study['id']}-Regular"
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=950, descent=-270)
    fb.setupNameTable(dict(familyName=family, styleName='Regular', uniqueFontIdentifier=psname+'-0.001',
        fullName=family+' Regular', psName=psname, version='Version 0.001',
        copyright='Original study drawings for SEIHouse Productions LLC, 2026. Reference font is separate.',
        description='Limited Latin design study. Not a production or multilingual release.'))
    fb.setupOS2(version=4,sTypoAscender=950,sTypoDescender=-270,sTypoLineGap=0,usWinAscent=1000,usWinDescent=300,
                sxHeight=537,sCapHeight=717,usWeightClass=400,fsSelection=0xC0,achVendID='SEIH')
    fb.setupPost()
    fb.setupCFF(psname, dict(FullName=family+' Regular',FamilyName=family,Weight='Regular'),charstrings,{})
    pairs = [('T','a',-24),('T','o',-30),('T','e',-28),('T','r',-14),('V','a',-24),
             ('V','o',-26),('W','a',-18),('Y','o',-36),('Y','a',-34),('A','V',-30),
             ('A','W',-20),('A','T',-28),('L','T',-28),('L','Y',-26),('F','o',-18),
             ('P','a',-15),('r','.',-26),('r',',',-26)]
    features = 'languagesystem DFLT dflt; languagesystem latn dflt; feature kern {\n'
    features += '\n'.join(f'pos {cmap[ord(a)]} {cmap[ord(b)]} {v};' for a,b,v in pairs)
    features += '\n} kern;'
    addOpenTypeFeaturesFromString(fb.font,features)
    fb.font['head'].created = fb.font['head'].modified = 3875990400
    out = ROOT/'fonts'
    out.mkdir(exist_ok=True)
    fb.save(out/f'{psname}.otf')
    fb.font.flavor = 'woff2'
    fb.save(out/f'{psname}.woff2')
    return dict(**study,glyphs=len(order),characters=''.join(source),
                sha256=hashlib.sha256((out/f'{psname}.woff2').read_bytes()).hexdigest())


def fetch_reference():
    ref = ROOT/'reference'
    ref.mkdir(exist_ok=True)
    records = []
    for remote,local in [('NotoSans%5Bwdth,wght%5D.ttf','NotoSans-Reference.ttf'),('OFL.txt','OFL.txt')]:
        url=f'https://raw.githubusercontent.com/google/fonts/{REFERENCE_COMMIT}/ofl/notosans/{remote}'
        target=ref/local
        if not target.exists():
            with urllib.request.urlopen(url,timeout=30) as response: target.write_bytes(response.read())
        records.append(dict(file=local,url=url,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (ref/'provenance.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')


def portable_comparison():
    page=(ROOT/'index.html').read_text(encoding='utf-8')
    for study in STUDIES:
        relative=f"fonts/SEIHouseNotoStudy{study['id']}-Regular.woff2"
        data=base64.b64encode((ROOT/relative).read_bytes()).decode('ascii')
        page=page.replace(relative,'data:font/woff2;base64,'+data)
    reference=base64.b64encode((ROOT/'reference/NotoSans-Reference.ttf').read_bytes()).decode('ascii')
    page=page.replace('reference/NotoSans-Reference.ttf','data:font/ttf;base64,'+reference)
    page=page.replace('href="reference/OFL.txt"','href="#reference-license"').replace('href="README.md"','href="#study-scope"')
    license_text=html.escape((ROOT/'reference/OFL.txt').read_text(encoding='utf-8'))
    page=page.replace('</main>',f'<details id="reference-license" style="margin-top:24px"><summary>Google Noto Sans reference license</summary><pre style="white-space:pre-wrap;font:12px/1.5 monospace">{license_text}</pre></details></main>')
    (ROOT/'SEIHouse-Noto-Warmth-Studies.html').write_text(page,encoding='utf-8')


if __name__=='__main__':
    fetch_reference()
    reports=[build_font(s) for s in STUDIES]
    (ROOT/'manifest.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    portable_comparison()
    print(json.dumps([{k:r[k] for k in ('id','name','glyphs','sha256')} for r in reports],indent=2))
