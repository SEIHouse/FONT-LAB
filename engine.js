/* ---------- SEIHouse Soft, refinement 2: glyph engine ----------
   Units: 1000 per em. Baseline 0, capitals 700, x-height XH, ascenders ASC, descenders -200.
   Letters are centre-line strokes. Coordinates in the tables below use the OLD scale
   (x-height 500, ascender 740); the mapping function stretches lowercase to the new x-height. */

const XH = 520, ASC = 770;
const OVS = new Set([...'oceasOCGQS0']);
const OSV = 10;
const WIDE = new Set([...'mwMWOCGDQ']);   // these get back 60% of the width the slider takes away

const o = p => ({ z:0, p });
const c = p => ({ z:1, p });
const R = (x0,y0,x1,y1,m) => ({ z:1, p:[[x0,y0,m],[x1,y0,m],[x1,y1,m],[x0,y1,m]] });
const RAW = r => ({ raw:r });
const FILL = p => ({ fill:p });
const THIN = (shape, k) => Object.assign({}, shape, { sw:k });   // this part uses a thinner line than the letters
const arcPts = (cx, cy, r, a0, a1, n = 48) => { const o = []; for(let i = 0; i <= n; i++){ const a = (a0 + (a1 - a0) * i / n) * Math.PI/180; o.push([cx + r*Math.cos(a), cy + r*Math.sin(a)]); } return o; };
const circ = (cx, cy, r) => { const k = 0.5522847498 * r;
  return [['M', cx + r, cy], ['C', cx + r, cy + k, cx + k, cy + r, cx, cy + r], ['C', cx - k, cy + r, cx - r, cy + k, cx - r, cy],
          ['C', cx - r, cy - k, cx - k, cy - r, cx, cy - r], ['C', cx + k, cy - r, cx + r, cy - k, cx + r, cy]]; };
const LN = (x0,y0,x1,y1) => ['C', x0+(x1-x0)/3, y0+(y1-y0)/3, x0+2*(x1-x0)/3, y0+2*(y1-y0)/3, x1, y1];
function cCurve(W, H, x0){
  /* one continuous curve; the ends stop partway round the corner at an angle, so there is no hard drop */
  const R = Math.min(P.caprx, W/2, H/2), END = 38 * Math.PI/180, PI = Math.PI;
  const arc = (cx, cy, a0, a1) => {
    const k = 4/3 * Math.tan((a1 - a0)/4);
    const p0 = [cx + R*Math.cos(a0), cy + R*Math.sin(a0)], p3 = [cx + R*Math.cos(a1), cy + R*Math.sin(a1)];
    return ['C', p0[0] - k*R*Math.sin(a0), p0[1] + k*R*Math.cos(a0), p3[0] + k*R*Math.sin(a1), p3[1] - k*R*Math.cos(a1), p3[0], p3[1]];
  };
  const c1 = [x0+W-R, H-R], c2 = [x0+R, H-R], c3 = [x0+R, R], c4 = [x0+W-R, R];
  return [['M', c1[0] + R*Math.cos(END), c1[1] + R*Math.sin(END)],
    arc(c1[0], c1[1], END, PI/2), LN(x0+W-R, H, x0+R, H),
    arc(c2[0], c2[1], PI/2, PI), LN(x0, H-R, x0, R),
    arc(c3[0], c3[1], PI, 1.5*PI), LN(x0+R, 0, x0+W-R, 0),
    arc(c4[0], c4[1], 1.5*PI, 2*PI - END)];
}

const G = {};
const def = (ch, w, kind, shapes, dots = [], sb = [62,62]) => { G[ch] = { w, kind, shapes, dots, sb }; };

/* 0.29: shared shoulder and bowl construction for the related lowercase.
   Tangents meet the straight stems smoothly; short upright sides retain the
   softly squared rhythm. Widths and bearings stay in the glyph definitions. */
/** Build a smooth lowercase shoulder, optionally ending in an italic exit foot. */
function shoulder(x, w, branch = 280, foot = 0){
  const end = x + w;
  const path = [['M',x,branch],
    ['C',x,branch + (500-branch)*0.64,x+w*0.22,500,x+w*0.51,500],
    ['C',x+w*0.83,500,end,424,end,280]];
  if(foot){
    path.push(LN(end,280,end,65),['C',end,18,end+foot*0.4,0,end+foot,0]);
  } else path.push(LN(end,280,end,0));
  return RAW(path);
}
/** Build the shared b/p bowl or mirror it onto the right stem for d/q. */
function bowlOnStem(w, right = false){
  const path = [['M',0,370],['C',0,458,w*0.26,500,w*0.505,500],
    ['C',w*0.825,500,w,422,w,277],LN(w,277,w,223),
    ['C',w,78,w*0.825,0,w*0.505,0],['C',w*0.26,0,0,48,0,132]];
  return RAW(right ? path.map(seg => seg.map((v,i) => i && i%2 ? w-v : v)) : path);
}
/** Build the shared u bowl, optionally leaving its right stem to the caller. */
function uBowl(full = true){
  const path = [['M',0,500],LN(0,500,0,220),
    ['C',0,76,84,0,198,0],['C',316,0,400,76,400,220]];
  if(full) path.push(LN(400,220,400,500));
  return RAW(path);
}

/* ----- capitals (squared curves, unchanged in spirit) ----- */
def('A',540,'cap',[o([[0,0],[270,700],[540,0]]),o([[115,230],[425,230]])],[],[15,15]);
def('B',440,'cap',[c([[0,350,0],[0,700,0],[400,700],[400,350]]),c([[0,0,0],[0,350,0],[440,350],[440,0]])],[],[66,52]);
def('C',480,'cap',[{ fn: () => cCurve(480, 700, 0) }],[],[52,44]);
def('D',500,'cap',[c([[0,0,0],[0,700,0],[500,700,1.6],[500,0,1.6]])],[],[66,52]);
def('E',480,'cap',[o([[480,700],[0,700],[0,0],[480,0]]),o([[0,350],[400,350]])],[],[66,40]);
def('F',480,'cap',[o([[480,700],[0,700],[0,0]]),o([[0,350],[400,350]])],[],[66,35]);
def('G',500,'cap',[o([[500,540],[500,700],[0,700],[0,0],[500,0],[500,320],[270,320]])],[],[52,62]);
def('H',480,'cap',[o([[0,0],[0,700]]),o([[480,0],[480,700]]),o([[0,350],[480,350]])],[],[66,66]);
def('I',240,'cap',[o([[0,700],[240,700]]),o([[120,700],[120,0]]),o([[0,0],[240,0]])],[],[56,56]);
def('J',440,'cap',[o([[440,700],[440,0],[0,0],[0,200]])],[],[40,66]);
def('K',490,'cap',[o([[0,0],[0,700]]),o([[470,700],[0,215]]),o([[130,340],[490,0]])],[],[66,20]);
def('L',420,'cap',[o([[0,700],[0,0],[420,0]])],[],[66,30]);
def('M',580,'cap',[o([[0,0],[0,700],[290,240],[580,700],[580,0]])],[],[66,66]);
def('N',500,'cap',[o([[0,0],[0,700],[500,0],[500,700]])],[],[66,66]);
def('O',560,'cap',[R(0,0,560,700)],[],[52,52]);
def('P',430,'cap',[o([[0,0],[0,700,0],[430,700],[430,300],[0,300,0]])],[],[66,40]);
def('Q',560,'cap',[R(0,0,560,700),o([[340,190],[590,-60]])],[],[52,52]);
def('R',450,'cap',[o([[0,0],[0,700,0],[430,700],[430,300],[0,300,0]]),o([[220,300],[450,0]])],[],[66,40]);
def('S',480,'cap',[o([[480,560],[480,700],[0,700],[0,350],[480,350],[480,0],[0,0],[0,140]])],[],[50,50]);
def('T',500,'cap',[o([[0,700],[500,700]]),o([[250,700],[250,0]])],[],[10,10]);
def('U',480,'cap',[o([[0,700],[0,0],[480,0],[480,700]])],[],[66,66]);
def('V',520,'cap',[o([[0,700],[260,0],[520,700]])],[],[15,15]);
def('W',700,'cap',[o([[0,700],[175,0],[350,520],[525,0],[700,700]])],[],[15,15]);
def('X',500,'cap',[o([[0,700],[500,0]]),o([[500,700],[0,0]])],[],[25,25]);
def('Y',500,'cap',[o([[0,700],[250,340],[500,700]]),o([[250,340],[250,0]])],[],[15,15]);
def('Z',480,'cap',[o([[0,700],[480,700],[0,0],[480,0]])],[],[50,50]);

/* ----- lowercase (calmer: rounder bowls, straight stems, open counters) ----- */
/* 0.28: individual reading curves retain the soft squared family rhythm.
   The double-storey a has a smaller bowl; e has a level crossbar and an open exit;
   c and s use continuous strokes so their terminals flow into the bowls. */
def('a',395,'low',[
  RAW([['M',35,433],['C',49,489,121,500,210,500],['C',327,500,395,463,395,350],LN(395,350,395,0)]),
  RAW([['M',395,284],['C',300,294,270,300,180,300],['C',65,300,0,262,0,155],
       ['C',0,59,64,0,172,0],['C',272,0,352,36,395,111]])
],[],[46,66]);
def('b',420,'low',[o([[0,740],[0,0]]),bowlOnStem(420)],[],[66,50]);
def('c',420,'low',[RAW([['M',414,402],['C',361,483,320,500,231,500],
  ['C',88,500,0,437,0,277],LN(0,277,0,219),['C',0,59,101,0,231,0],
  ['C',320,0,367,25,412,82]])],[],[50,40]);
def('d',420,'low',[o([[420,740],[420,0]]),bowlOnStem(420,true)],[],[50,66]);
def('e',398,'low',[o([[5,255],[398,255]]),RAW([['M',398,255],
  ['C',398,405,338,500,206,500],['C',79,500,0,440,0,260],
  ['C',0,74,74,0,213,0],['C',294,0,342,6,372,20]])],[],[50,50]);
def('f',350,'low',[o([[375,740],[150,740,1],[150,0]]),o([[0,500],[340,500]])],[],[30,14]);
def('g',420,'low',[o([[420,200],[420,-195,1],[75,-195,0.8],[75,-125]]),o([[420,200],[420,500],[0,500],[0,0],[420,0]])],[],[50,66]);
def('h',400,'low',[o([[0,0],[0,740]]),shoulder(0,400)],[],[66,66]);
def('i',0,'low',[o([[0,0],[0,500]])],[[0,720]],[72,72]);
def('j',160,'low',[o([[160,500],[160,-205,0.5],[0,-205,0.5],[0,-110]])],[[160,720]],[30,66]);
def('k',420,'low',[o([[0,0],[0,740]]),o([[415,500],[0,185]]),o([[165,309],[425,0]])],[],[66,20]);
def('l',95,'low',[o([[0,740],[0,0,0.55],[95,0]])],[],[66,40]);
def('m',640,'low',[o([[0,0],[0,500]]),shoulder(0,320),shoulder(320,320)],[],[66,66]);
def('n',400,'low',[o([[0,0],[0,500]]),shoulder(0,400)],[],[66,66]);
def('o',420,'low',[R(0,0,420,500)],[],[50,50]);
def('p',420,'low',[o([[0,500],[0,-200]]),bowlOnStem(420)],[],[66,50]);
def('q',420,'low',[o([[420,500],[420,-200]]),bowlOnStem(420,true)],[],[50,66]);
def('r',300,'low',[o([[0,0],[0,500]]),o([[0,320],[0,500],[300,500],[300,440]])],[],[66,30]);
def('s',420,'low',[RAW([['M',405,428],['C',356,484,292,500,210,500],
  ['C',90,500,0,433,0,370],['C',0,300,65,270,209,255],
  ['C',337,242,420,198,420,131],['C',420,47,286,0,197,0],
  ['C',114,0,38,33,13,70]])],[],[46,46]);
def('t',350,'low',[o([[150,710],[150,0,1.15],[360,0]]),o([[0,500],[350,500]])],[],[30,22]);
def('u',400,'low',[uBowl()],[],[66,66]);
const U_PLAIN = G['u'];
def('u',400,'low',[o([[400,500],[400,0,0.5],[465,0]]),uBowl(false)],[],[66,12]);
const U_FOOT = G['u'];
const A_UP = G['a'], F_UP = G['f'];
def('a',410,'low',[o([[410,500],[410,0,0.6],[465,0]]),o([[410,500],[0,500],[0,0],[410,0]])],[],[48,28]);
const A_IT = G['a'];
def('f',350,'low',[o([[375,740],[150,740,1],[150,-195,1],[-40,-195]]),o([[0,500],[340,500]])],[],[30,14]);
const F_IT = G['f'];
G['a'] = A_UP; G['f'] = F_UP;
/* the rest of the italic letters: lower-branching arches and small exit strokes, like a pen moving fast */
const IT = {};
{
  const keep = {};
  for(const ch of 'dhimnu') keep[ch] = G[ch];
  def('d',420,'low',[o([[420,740],[420,0,0.6],[475,0]]),bowlOnStem(420,true)],[],[50,28]);
  def('h',400,'low',[o([[0,0],[0,740]]),shoulder(0,400,210,55)],[],[66,28]);
  def('i',45,'low',[o([[0,500],[0,0,0.6],[55,0]])],[[0,720]],[72,38]);
  def('m',640,'low',[o([[0,0],[0,500]]),shoulder(0,320,210),shoulder(320,320,210,55)],[],[66,28]);
  def('n',400,'low',[o([[0,0],[0,500]]),shoulder(0,400,210,55)],[],[66,28]);
  def('u',400,'low',[o([[400,500],[400,0,0.6],[455,0]]),uBowl(false)],[],[66,28]);
  for(const ch of 'dhimnu'){ IT[ch] = G[ch]; G[ch] = keep[ch]; }
}
def('v',420,'low',[o([[0,500],[210,0],[420,500]])],[],[15,15]);
def('w',640,'low',[o([[0,500],[160,0],[320,400],[480,0],[640,500]])],[],[15,15]);
def('x',420,'low',[o([[0,500],[420,0]]),o([[420,500],[0,0]])],[],[20,20]);
def('y',420,'low',[o([[0,500],[210,0]]),RAW([['M',420,500],['C',341.7,313.3,263.3,126.7,185,-60],['C',156.8,-127.2,115,-195,50,-195]])],[],[15,15]);
def('z',400,'low',[o([[0,500],[400,500],[0,0],[400,0]])],[],[50,50]);

/* ----- numerals ----- */
/* 0.32: continuous bowls and terminals soften the figure texture. The existing
   widths, heights, and angular 1/4/7 keep the family recognizable. */
def('0',360,'cap',[R(0,0,360,700)],[],[56,56]);
def('1',300,'cap',[o([[0,520],[150,700],[150,0]]),o([[0,0],[300,0]])],[],[40,40]);
def('2',400,'cap',[RAW([['M',0,546],['C',0,648,71,700,191,700],
  ['C',318,700,400,640,400,538],['C',400,456,342,396,261,324],
  LN(261,324,0,0),LN(0,0,400,0)])]);
def('3',420,'cap',[RAW([['M',0,592],['C',46,670,111,700,207,700],
  ['C',325,700,380,633,380,536],['C',380,433,308,360,188,350],
  ['C',329,349,420,284,420,175],['C',420,65,329,0,208,0],
  ['C',116,0,44,28,0,108]])]);
def('4',420,'cap',[o([[320,0],[320,700],[0,200],[420,200]])],[],[30,40]);
def('5',400,'cap',[RAW([['M',400,700],LN(400,700,0,700),LN(0,700,0,384),
  ['C',100,395,186,402,247,389],['C',350,367,400,299,400,188],
  ['C',400,71,325,0,201,0],['C',108,0,42,34,0,108]])]);
const SIX_FIGURE = [
  [['M',375,700],['C',276,700,178,681,100,610],['C',24,540,0,401,0,179]],
  [['M',206,358],['C',83,358,0,287,0,179],['C',0,71,83,0,206,0],
   ['C',329,0,400,71,400,179],['C',400,287,329,358,206,358],['Z']]
];
def('6',400,'cap',SIX_FIGURE.map(RAW));
def('7',400,'cap',[o([[0,700],[400,700],[120,0]])],[],[40,20]);
def('8',420,'cap',[RAW([['M',210,350],['C',88,350,20,419,20,521],
  ['C',20,632,86,700,210,700],['C',334,700,400,632,400,521],
  ['C',400,419,332,350,210,350],['Z']]),
  RAW([['M',210,350],['C',74,350,0,277,0,175],
  ['C',0,70,77,0,210,0],['C',343,0,420,70,420,175],
  ['C',420,277,346,350,210,350],['Z']])]);
def('9',400,'cap',SIX_FIGURE.map(path => RAW(path.map(seg => seg.map((v,i) => i ? (i%2 ? 400-v : 700-v) : v)))));

/* Numeric alternates keep the original digit drawings as their source. The font builder
   measures the finished outlines for the exact shared advances and optical centering. */
const DIGITS = '0123456789';
const DIGIT_NAMES = ['zero','one','two','three','four','five','six','seven','eight','nine'];
const SUPERS = '⁰¹²³⁴⁵⁶⁷⁸⁹', SUBS = '₀₁₂₃₄₅₆₇₈₉';
const NUMERIC_VARIANTS = {};
for(let i = 0; i < 10; i++){
  NUMERIC_VARIANTS[DIGIT_NAMES[i] + '.tf'] = { digit:DIGITS[i], type:'tf' };
  NUMERIC_VARIANTS[DIGIT_NAMES[i] + '.numr'] = { digit:DIGITS[i], type:'numr' };
  NUMERIC_VARIANTS[DIGIT_NAMES[i] + '.dnom'] = { digit:DIGITS[i], type:'dnom' };
  NUMERIC_VARIANTS[SUPERS[i]] = { digit:DIGITS[i], type:'sup' };
  NUMERIC_VARIANTS[SUBS[i]] = { digit:DIGITS[i], type:'sub' };
  G[SUPERS[i]] = G[SUBS[i]] = { comp:true, w:0, kind:'cap', shapes:[], dots:[], sb:[0,0] };
}
const FRACTION_PARTS = { '½':['1','2'], '¼':['1','4'], '¾':['3','4'] };
for(const ch of Object.keys(FRACTION_PARTS)) G[ch] = { comp:true, w:0, kind:'cap', shapes:[], dots:[], sb:[0,0] };

/* ----- punctuation ----- */
/* Quotes sit just above the cap line so they read clearly at chapter size. */
const QUOTE_RISE = 60;
const qy = y => y + QUOTE_RISE;
def('.',0,'cap',[],[[0,0]],[50,50]);
const COMMA_TAIL = RAW([['M',80,20],['C',83,-42,45,-110,10,-150]]);
def(',',80,'cap',[COMMA_TAIL],[[80,20]],[36,40]);
def(':',0,'low',[],[[0,0],[0,470]],[50,50]);
def(';',80,'low',[COMMA_TAIL],[[80,20],[80,470]],[36,40]);
def('…',480,'cap',[],[[0,0],[240,0],[480,0]],[40,40]);
def('!',0,'cap',[o([[0,700],[0,230]])],[[0,0]],[56,56]);
def('?',380,'cap',[o([[0,560],[0,700],[380,700],[380,420],[190,420],[190,240]])],[[190,0]],[50,50]);
def("'",0,'cap',[o([[0,qy(700)],[0,qy(510)]])],[],[50,50]);
def('"',200,'cap',[o([[0,qy(700)],[0,qy(510)]]),o([[200,qy(700)],[200,qy(510)]])],[],[50,50]);
/** Draw a lighter curved quote while retaining the established raised endpoints. */
function curvedQuote(opening, dx = 0){
  return RAW(opening
    ? [['M',10+dx,qy(520)],['C',10+dx,qy(582),43+dx,qy(644),80+dx,qy(690)]]
    : [['M',80+dx,qy(650)],['C',80+dx,qy(588),47+dx,qy(533),10+dx,qy(490)]]);
}
def('’',80,'cap',[curvedQuote(false)],[[80,qy(650)]],[40,40]);
def('‘',80,'cap',[curvedQuote(true)],[[10,qy(520)]],[40,40]);
def('”',270,'cap',[curvedQuote(false),curvedQuote(false,190)],[[80,qy(650)],[270,qy(650)]],[40,40]);
def('“',270,'cap',[curvedQuote(true),curvedQuote(true,190)],[[10,qy(520)],[200,qy(520)]],[40,40]);
/** Place a curved local opening quote below the baseline at a horizontal offset. */
const lowQuote = dx => RAW([['M',80+dx,20],['C',80+dx,-42,47+dx,-97,10+dx,-140]]);
/** Reverse the raised quote curve for local reversed quotation forms. */
const reverseQuote = dx => RAW([['M',10+dx,qy(650)],['C',10+dx,qy(588),43+dx,qy(533),80+dx,qy(490)]]);
def('‚',80,'cap',[lowQuote(0)],[[80,20]],[40,40]);
def('„',270,'cap',[lowQuote(0),lowQuote(190)],[[80,20],[270,20]],[40,40]);
def('‛',80,'cap',[reverseQuote(0)],[[10,qy(650)]],[40,40]);
def('‟',270,'cap',[reverseQuote(0),reverseQuote(190)],[[10,qy(650)],[200,qy(650)]],[40,40]);
def('-',240,'low',[o([[0,265],[240,265]])],[],[50,50]);
def('–',480,'low',[o([[0,265],[480,265]])],[],[40,40]);
def('—',860,'low',[o([[0,265],[860,265]])],[],[24,24]);
def('/',300,'low',[o([[0,-90],[300,760]])],[],[10,10]);
def('⁄',170,'cap',[THIN(o([[0,-180],[170,760]]),0.68)],[],[5,5]);
def('\\',300,'low',[o([[0,760],[300,-90]])],[],[10,10]);
/* common symbols */
def('&',480,'cap',[RAW([['M',470,10], LN(470,10,150,420), ['C',90,500,100,700,250,700], ['C',390,700,410,560,300,480],
    LN(300,480,120,340), ['C',20,260,30,0,210,0], ['C',330,0,410,80,470,230]])],[],[40,30]);
def('@',640,'cap',[R(180,130,440,450), o([[440,450],[440,130,0.6],[640,130],[640,640],[0,640],[0,-80],[520,-80]])],[],[40,40]);
def('#',520,'cap',[o([[150,30],[210,670]]), o([[330,30],[390,670]]), o([[40,460],[520,460]]), o([[0,230],[480,230]])],[],[30,30]);
def('$',420,'cap',[o([[420,520],[420,630],[0,630],[0,340],[420,340],[420,60],[0,60],[0,170]]), o([[210,-70],[210,770]])],[],[45,45]);
def('*',300,'cap',[o([[150,380],[150,680]]), o([[20,455],[280,605]]), o([[20,605],[280,455]])],[],[30,30]);
def('~',500,'cap',[RAW([['M',0,260],['C',90,380,170,380,250,310],['C',330,240,410,240,500,360]])],[],[40,40]);
def('_',520,'cap',[o([[0,-140],[520,-140]])],[],[10,10]);
def('|',0,'cap',[o([[0,-180],[0,880]])],[],[80,80]);
def('{',200,'low',[RAW([['M',200,760],['C',110,760,90,720,90,640], LN(90,640,90,390), ['C',90,320,70,290,0,290],
    ['C',70,290,90,260,90,190], LN(90,190,90,-60), ['C',90,-140,110,-180,200,-180]])],[],[40,30]);
def('}',200,'low',[RAW([['M',0,760],['C',90,760,110,720,110,640], LN(110,640,110,390), ['C',110,320,130,290,200,290],
    ['C',130,290,110,260,110,190], LN(110,190,110,-60), ['C',110,-140,90,-180,0,-180]])],[],[30,40]);
def('<',420,'cap',[o([[420,560],[0,320],[420,80]])],[],[50,50]);
def('>',420,'cap',[o([[0,560],[420,320],[0,80]])],[],[50,50]);
/* novel and system-screen symbols */
{ const pts = []; for(let i = 0; i < 10; i++){ const a = (90 + i*36) * Math.PI/180, r = i % 2 ? 135 : 330; pts.push([320 + r*Math.cos(a), 310 + r*Math.sin(a)]); }
  def('★',640,'cap',[FILL(pts)],[],[30,30]); }
def('•',220,'low',[],[[110,250,1.8]],[40,40]);
def('·',0,'low',[],[[0,260]],[60,60]);
/* cultivation */
{ const R = 320, cx = 320, cy = 330, hole = 50;
  const dark = [...arcPts(cx, cy, R, 90, 270, 64), ...arcPts(cx, cy - R/2, R/2, -90, 90, 32), ...arcPts(cx, cy + R/2, R/2, -90, -270, 32)];
  def('☯',640,'cap',[{ fill:[dark, arcPts(cx, cy - R/2, hole + 42, 0, 360, 32)], nostroke:true }, RAW(circ(cx, cy, R))],[[cx, cy + R/2, 0.95]],[40,40]); }
def('⚡',380,'cap',[FILL([[240,700],[30,300],[190,300],[110,-40],[370,400],[210,400],[320,700]])],[],[40,40]);
def('☀',680,'cap',[FILL(arcPts(340, 320, 60, 0, 360, 40)),
    ...[0,45,90,135,180,225,270,315].map(a => { const r = a*Math.PI/180; return o([[340 + 235*Math.cos(r), 320 + 235*Math.sin(r)], [340 + 335*Math.cos(r), 320 + 335*Math.sin(r)]]); })],[],[40,40]);
{ const cx = 320, cy = 330, R = 310;
  const moon = sgn => [...arcPts(cx, cy, R, 60*sgn + (sgn < 0 ? 180 : 0), sgn < 0 ? 180 + 300 : 300, 48)];
  const outerL = arcPts(cx, cy, R, 60, 300, 48), innerL = arcPts(cx + 155, cy, Math.hypot(0, R*Math.sin(Math.PI/3)), 270, 90, 48);
  const outerR = arcPts(cx, cy, R, 120, -120, 48), innerR = arcPts(cx - 155, cy, Math.hypot(0, R*Math.sin(Math.PI/3)), -90, 90, 48);
  def('☾',600,'cap',[FILL([...outerL, ...innerL])],[],[30,30]);
  def('☽',600,'cap',[FILL([...outerR, ...innerR])],[],[30,30]); }
def('⚔',640,'cap',[o([[60,20],[560,620]]), o([[580,20],[80,620]]), o([[20,150],[180,10]]), o([[620,150],[460,10]])],[],[30,30]);
/* scene breaks, ratings, bullets */
def('✦',400,'cap',[FILL([[200,660],[250,370],[400,320],[250,270],[200,-20],[150,270],[0,320],[150,370]])],[],[40,40]);
{ const pts = []; for(let i = 0; i < 10; i++){ const a = (90 + i*36) * Math.PI/180, r = i % 2 ? 135 : 330; pts.push([320 + r*Math.cos(a), 310 + r*Math.sin(a)]); }
  def('☆',640,'cap',[c(pts.map(p => [p[0], p[1], 0]))],[],[30,30]); }
def('◆',440,'cap',[FILL([[220,560],[440,320],[220,80],[0,320]])],[],[40,40]);
def('◇',440,'cap',[c([[220,560,0],[440,320,0],[220,80,0],[0,320,0]])],[],[40,40]);
/* stat screens */
def('▲',480,'cap',[FILL([[0,40],[480,40],[240,480]])],[],[40,40]);
def('▼',480,'cap',[FILL([[0,480],[480,480],[240,40]])],[],[40,40]);
def('▶',440,'cap',[FILL([[0,20],[0,500],[440,260]])],[],[40,40]);
def('◀',440,'cap',[FILL([[440,20],[440,500],[0,260]])],[],[40,40]);
def('↑',400,'cap',[o([[200,0],[200,680]]), o([[20,500],[200,680],[380,500]])],[],[40,40]);
def('↓',400,'cap',[o([[200,680],[200,0]]), o([[20,180],[200,0],[380,180]])],[],[40,40]);
def('−',420,'cap',[o([[30,300],[390,300]])],[],[50,50]);
def('≤',420,'cap',[o([[420,620],[0,420],[420,220]]), o([[0,40],[420,40]])],[],[50,50]);
def('≥',420,'cap',[o([[0,620],[420,420],[0,220]]), o([[0,40],[420,40]])],[],[50,50]);
def('≠',420,'cap',[o([[30,220],[390,220]]), o([[30,400],[390,400]]), o([[90,40],[330,580]])],[],[50,50]);
def('≈',420,'cap',[RAW([['M',10,380],['C',90,480,160,480,210,420],['C',260,360,330,360,410,460]]),
                    RAW([['M',10,170],['C',90,270,160,270,210,210],['C',260,150,330,150,410,250]])],[],[50,50]);
/* hearts and quests */
{ const heart = []; for(let i = 0; i < 72; i++){ const t = i/72 * 2*Math.PI;
    heart.push([280 + 17.5*16*Math.pow(Math.sin(t),3), 330 + 17.5*(13*Math.cos(t) - 5*Math.cos(2*t) - 2*Math.cos(3*t) - Math.cos(4*t))]); }
  def('♥',560,'cap',[FILL(heart)],[],[30,30]);
  def('♡',560,'cap',[c(heart.map(p => [p[0], p[1], 0]))],[],[30,30]); }
def('✓',460,'cap',[o([[0,300],[160,80],[460,620]])],[],[40,40]);
def('✗',440,'cap',[o([[0,560],[440,40]]), o([[40,40],[440,580]])],[],[40,40]);
/* music, for SEA */
def('♪',400,'cap',[o([[260,120],[260,700],[400,560]])],[[130,120,2.2]],[40,40]);
/* brand */
def('©',640,'cap',[{ fn: () => circ(320, 320, 320), swFn: true }, { swFn: true, fn: () => cCurve(260, 330, 190).map(seg => seg[0] === 'M' ? ['M', seg[1], seg[2] + 155] : ['C', seg[1], seg[2] + 155, seg[3], seg[4] + 155, seg[5], seg[6] + 155]) }],[],[40,40]);
def('®',640,'cap',[{ fn: () => circ(320, 320, 320), swFn: true }, Object.assign(o([[210,160],[210,490],[420,490,0.5],[420,330,0.5],[210,330]]), { swFn:true }), Object.assign(o([[320,330],[430,160]]), { swFn:true })],[],[40,40]);
def('™',560,'cap',[o([[0,700],[220,700]]), o([[110,700],[110,440]]), o([[300,440],[300,700],[430,540],[560,700],[560,440]])],[],[40,40]);
/* languages: letters with their own shapes */
{ const sh = (shapes, dx) => shapes.map(s => s.p ? Object.assign({}, s, { p: s.p.map(q => [q[0] + dx, q[1], q[2]]) })
                                   : s.raw ? { raw: s.raw.map(seg => seg[0] === 'M' ? ['M', seg[1] + dx, seg[2]] : ['C', seg[1] + dx, seg[2], seg[3] + dx, seg[4], seg[5] + dx, seg[6]]) } : s);
  def('Ø',560,'cap',[R(0,0,560,700), o([[-10,-30],[570,730]])],[],[52,52]);
  def('ø',420,'low',[R(0,0,420,500), o([[-10,-40],[430,540]])],[],[50,50]);
  def('ß',420,'low',[o([[0,0],[0,740],[360,740],[360,420],[190,420]]), o([[190,420],[420,420],[420,0],[170,0]])],[],[66,40]);
  def('æ',380+G['e'].w,'low',[...A_UP.shapes, ...sh(G['e'].shapes, 380)],[],[46,50]);
  def('œ',380+G['e'].w,'low',[...G['o'].shapes, ...sh(G['e'].shapes, 380)],[],[50,50]);
  def('Æ',720,'cap',[o([[0,0],[330,700],[720,700]]), o([[330,700],[330,0],[720,0]]), o([[330,350],[660,350]]), o([[110,230],[330,230]])],[],[15,40]);
  def('Œ',720,'cap',[o([[720,700],[0,700],[0,0],[720,0]]), o([[390,700],[390,0]]), o([[390,350],[660,350]])],[],[52,40]);
  def('Ð',500,'cap',[...G['D'].shapes, o([[-50,350],[170,350]])],[],[100,52]);
  def('ð',420,'low',[R(0,0,420,500), o([[420,250],[420,560],[240,760]]), o([[170,660],[420,740]])],[],[50,50]);
  def('Þ',430,'cap',[o([[0,0],[0,700]]), o([[0,540],[430,540],[430,160],[0,160]])],[],[66,40]);
  def('þ',410,'low',[o([[0,740],[0,-200]]), o([[0,500],[410,500],[410,0],[0,0]])],[],[66,48]);
  def('¡',0,'cap',[o([[0,330],[0,-190]])],[[0,510]],[56,56]);
  def('¿',380,'cap',[o([[190,340],[190,160],[0,160],[0,-120],[380,-120],[380,20]])],[[190,510]],[50,50]);
  def('º',240,'cap',[R(0,400,240,700), o([[0,300],[240,300]])],[],[40,40]);
  def('ª',240,'cap',[R(0,400,240,600), o([[240,700],[240,400]]), o([[0,700],[240,700]]), o([[0,300],[240,300]])],[],[40,40]); }
/* SEIHouse brand mark: circled S, drawn with SEIReader's own S */
def('Ⓢ',660,'cap',[{ fn: () => circ(330, 320, 330), swFn: true },
    { p: [[480,560],[480,700],[0,700],[0,350],[480,350],[480,0],[0,0],[0,140]].map(p => [196 + p[0]*0.56, 124 + p[1]*0.56, 0.55]), z: 0, swFn: true }],[],[40,40]);
/* music */
def('♩',300,'cap',[o([[260,120],[260,700]])],[[130,120,2.2]],[40,40]);
def('♫',620,'cap',[o([[240,80],[240,640],[580,720],[580,160]])],[[110,80,2.2],[450,160,2.2]],[40,40]);
def('♬',620,'cap',[o([[240,80],[240,640],[580,720],[580,160]]), o([[240,520],[580,600]])],[[110,80,2.2],[450,160,2.2]],[40,40]);
def('♭',260,'cap',[o([[0,0],[0,720]]), RAW([['M',0,320],['C',120,420,260,380,260,260],['C',260,150,120,60,0,0]])],[],[50,40]);
def('♮',260,'cap',[o([[0,700],[0,180],[260,230]]), o([[260,0],[260,520],[0,470]])],[],[50,50]);
def('♯',360,'cap',[o([[100,-40],[100,660]]), o([[260,0],[260,700]]), o([[0,420],[360,480]]), o([[0,200],[360,260]])],[],[40,40]);
/* player controls (SEA / SAP) */
def('⏸',440,'cap',[o([[80,40],[80,600]]), o([[360,40],[360,600]])],[],[50,50]);
def('⏹',500,'cap',[FILL([[0,40],[500,40],[500,540],[0,540]])],[],[50,50]);
def('⏺',500,'cap',[FILL(arcPts(250, 290, 250, 0, 360, 48))],[],[50,50]);
def('⏭',480,'cap',[FILL([[0,40],[0,560],[370,300]]), o([[480,40],[480,560]])],[],[40,40]);
def('⏮',480,'cap',[FILL([[480,40],[480,560],[110,300]]), o([[0,40],[0,560]])],[],[40,40]);
/* utilities */
def('🎧',640,'cap',[RAW([['M',70,300],['C',70,520,180,660,320,660],['C',460,660,570,520,570,300]]),
    FILL([[20,30],[190,30],[190,330],[20,330]]), FILL([[450,30],[620,30],[620,330],[450,330]])],[],[40,40]);
def('💻',680,'cap',[c([[100,230,0.25],[580,230,0.25],[580,660,0.25],[100,660,0.25]]), o([[0,70],[680,70]])],[],[30,30]);
def('📖',660,'cap',[RAW([['M',330,90],['C',250,150,130,150,20,120], LN(20,120,20,610), ['C',130,640,250,640,330,580]]),
    RAW([['M',330,90],['C',410,150,530,150,640,120], LN(640,120,640,610), ['C',530,640,410,640,330,580]]), o([[330,90],[330,580]])],[],[30,30]);
def('🔖',400,'cap',[c([[0,700,0.3],[400,700,0.3],[400,-40,0],[200,140,0],[0,-40,0]])],[],[60,60]);
def('🔍',620,'cap',[{ fn: () => circ(250, 410, 220), swFn: true }, o([[410,250],[600,40]])],[],[40,40]);
def('🔔',600,'cap',[RAW([['M',70,150],['C',110,210,120,290,120,380],['C',120,540,210,650,300,650],['C',390,650,480,540,480,380],['C',480,290,490,210,530,150]]),
    o([[20,150],[580,150]])],[[300,40,1.3]],[40,40]);
def('⚙',640,'cap',[{ fn: () => circ(320, 320, 205), swFn: true }, { fn: () => circ(320, 320, 70), swFn: true },
    ...[0,45,90,135,180,225,270,315].map(a => { const r = a*Math.PI/180; return Object.assign(o([[320 + 240*Math.cos(r), 320 + 240*Math.sin(r)], [320 + 315*Math.cos(r), 320 + 315*Math.sin(r)]]), { swFn:true }); })],[],[40,40]);
def('⌂',600,'cap',[o([[20,300],[300,620],[580,300]]), o([[90,350],[90,0],[510,0],[510,350]])],[],[40,40]);
def('🎤',520,'cap',[c([[150,330],[370,330],[370,720],[150,720]]),
    RAW([['M',50,470],['C',50,290,150,200,260,200],['C',370,200,470,290,470,470]]), o([[260,200],[260,20]]), o([[120,20],[400,20]])],[],[40,40]);
def('💿',640,'cap',[{ fn: () => circ(320, 320, 320), swFn: true }, { fn: () => circ(320, 320, 80), swFn: true }],[],[40,40]);
def('🔊',640,'cap',[FILL([[0,210],[130,210],[300,50],[300,590],[130,430],[0,430]]),
    o(arcPts(320, 320, 150, -45, 45, 16).map(p => [p[0], p[1], 0])), o(arcPts(320, 320, 280, -50, 50, 24).map(p => [p[0], p[1], 0]))],[],[30,30]);
def('×',420,'cap',[o([[20,110],[400,490]]), o([[20,490],[400,110]])],[],[50,50]);
def('÷',420,'cap',[o([[0,300],[420,300]])],[[210,510],[210,90]],[50,50]);
def('±',420,'cap',[o([[0,400],[420,400]]), o([[210,220],[210,580]]), o([[0,60],[420,60]])],[],[50,50]);
def('°',200,'cap',[R(0,470,200,700)],[],[40,40]);
def('→',580,'cap',[o([[0,300],[580,300]]), o([[400,480],[580,300],[400,120]])],[],[40,40]);
def('←',580,'cap',[o([[0,300],[580,300]]), o([[180,480],[0,300],[180,120]])],[],[40,40]);
def('∞',520,'cap',[RAW([['M',260,300],['C',340,440,520,440,520,300],['C',520,160,340,160,260,300],
    ['C',180,440,0,440,0,300],['C',0,160,180,160,260,300]])],[],[40,40]);
def('‹',170,'low',[o([[170,430],[0,250],[170,70]])],[],[40,40]);
def('›',170,'low',[o([[0,430],[170,250],[0,70]])],[],[40,40]);
def('«',370,'low',[o([[170,430],[0,250],[170,70]]), o([[370,430],[200,250],[370,70]])],[],[40,40]);
def('»',370,'low',[o([[0,430],[170,250],[0,70]]), o([[200,430],[370,250],[200,70]])],[],[40,40]);
/* money */
def('¥',500,'cap',[o([[0,700],[250,380],[500,700]]), o([[250,380],[250,0]]), o([[80,320],[420,320]]), o([[80,170],[420,170]])],[],[15,15]);
def('€',530,'cap',[{ fn: () => cCurve(460, 700, 70) }, o([[0,420],[380,420]]), o([[0,270],[380,270]])],[],[30,30]);
def('£',480,'cap',[RAW([['M',470,560],['C',450,660,390,700,300,700],['C',190,700,140,630,140,520], LN(140,520,140,100),
    ['C',140,40,110,10,40,0]]), o([[40,0],[480,0]]), o([[20,350],[340,350]])],[],[40,30]);
def('[',150,'low',[o([[150,760],[0,760,0.3],[0,-180,0.3],[150,-180]])],[],[46,36]);
def(']',150,'low',[o([[0,760],[150,760,0.3],[150,-180,0.3],[0,-180]])],[],[36,46]);
def('+',420,'cap',[o([[30,300],[390,300]]),o([[210,120],[210,480]])],[],[50,50]);
def('=',420,'cap',[o([[30,220],[390,220]]),o([[30,400],[390,400]])],[],[50,50]);
def('%',560,'cap',[R(0,430,210,700),R(350,0,560,270),o([[500,700],[60,0]])],[],[36,36]);
def('(',150,'low',[RAW([['M',150,760],['C',-20,560,-20,20,150,-180]])],[],[46,36]);
def(')',150,'low',[RAW([['M',0,760],['C',170,560,170,20,0,-180]])],[],[36,46]);

/* ----- pair spacing (added after the first letter of each pair, in font units) ----- */
const KERN = {
  'Th':30,'Te':-35,'To':-35,'Ta':-35,'Tr':-20,'Ty':-30,'Tu':-20,'Tw':-25,
  'Yo':-40,'Ye':-40,'Ya':-40,'Wa':-20,'Wo':-25,'Va':-25,'Vo':-25,'Av':-20,'Aw':-20,'Ay':-20,
  'rn':26,'rm':26,'rh':10,'ri':8,'ll':6,'oo':-6,'te':-8,'er':-14,'re':-6,'rt':-8,'ry':-20,
  'ov':-10,'ow':-10,'ev':-10,'ew':-10,'vo':-10,'wo':-10,'yo':-8,
  'T.':-40,'T,':-40,'F.':-40,'F,':-40,'P.':-45,'P,':-45,'r.':-30,'r,':-30,'y.':-30,'y,':-30,
  '“T':-10,'“A':-30,'‘T':-10
};
/* Keep decimal/thousands separators readable instead of tucking them into digits.
   This also supplies the font builder's explicit numeric override after auto spacing. */
for(const digit of DIGITS) for(const separator of '.,'){
  KERN[digit + separator] = 24;
  KERN[separator + digit] = 24;
}

/* ---------- settings the sliders control ---------- */
const P = { base:108, boost:0, round:0.5, track:9, size:17, contrast:1, xh:520, ws:1, caprx:210, space:250, os:1, ufoot:1, ital:0, slant:9, straight:1, asc:770,
  corner:'soft', cap:'round', join:'round', penAngle:0, obliqueAngle:0, alternates:null };
const DEFAULTS = { base:108, boost:0, round:0.5, track:9, size:17, contrast:1 };

/* Display designs are opt-in. The Reader retains its original skeletons and
   italic substitutions when P.alternates is null. Related designs share a set,
   while a saved cut can choose each member independently. */
const DISPLAY_SETS = [
  {key:'a', tag:'ss01', label:'a', choices:['double','single']},
  {key:'g', tag:'ss01', label:'g', choices:['single','double']},
  {key:'R', tag:'ss02', label:'R leg', choices:['straight','curved']},
  {key:'K', tag:'ss03', label:'K / k arms', choices:['branched','joined']},
  {key:'M', tag:'ss04', label:'M stems', choices:['vertical','splayed']},
  {key:'W', tag:'ss04', label:'W strokes', choices:['plain','crossed']},
  {key:'y', tag:'ss05', label:'y tail', choices:['curved','straight']},
  {key:'G', tag:'ss06', label:'G spur', choices:['no-spur','spur']},
  {key:'Q', tag:'ss07', label:'Q tail', choices:['diagonal','long']},
  {key:'four', tag:'ss08', label:'4', choices:['closed','open']},
  {key:'sixNine', tag:'ss08', label:'6 / 9', choices:['closed','open']},
];
/** Validate saved choices and fill legacy drafts with the original upright forms. */
function displayChoices(choices={}){
  const result={};
  if(!choices || typeof choices!=='object' || Array.isArray(choices)) throw new Error('Invalid alternate choices');
  for(const key of Object.keys(choices)) if(!DISPLAY_SETS.some(set=>set.key===key)) throw new Error('Unknown alternate: '+key);
  for(const set of DISPLAY_SETS){
    const choice=choices[set.key] ?? set.choices[0];
    if(!set.choices.includes(choice)) throw new Error('Invalid alternate '+set.key+': '+choice);
    result[set.key]=choice;
  }
  return result;
}
/** Copy the approved metrics while replacing only a letter's centre-line drawing. */
const displayDesign=(ch, shapes)=>({...G[ch],shapes});
const OPEN_SIX = [RAW([['M',375,700],['C',276,700,178,681,100,610],
  ['C',24,540,0,401,0,179],['C',0,71,83,0,206,0],
  ['C',329,0,400,71,400,179],['C',400,287,329,358,250,358]])];
const DISPLAY_DESIGNS = {
  a:{double:G.a,single:displayDesign('a',[o([[395,500],[395,0]]),bowlOnStem(395,true)])},
  g:{single:G.g,double:displayDesign('g',[R(20,200,400,500),R(0,-220,420,40),
    o([[340,200],[80,40]]),o([[400,500],[465,500]])])},
  R:{straight:G.R,curved:displayDesign('R',[G.R.shapes[0],
    RAW([['M',220,300],['C',220,195,320,100,450,0]])])},
  K:{branched:G.K,joined:displayDesign('K',[G.K.shapes[0],o([[470,700],[0,350],[490,0]])])},
  k:{branched:G.k,joined:displayDesign('k',[G.k.shapes[0],o([[415,500],[0,250],[425,0]])])},
  M:{vertical:G.M,splayed:displayDesign('M',[o([[0,0],[60,700],[290,240],[520,700],[580,0]])])},
  W:{plain:G.W,crossed:displayDesign('W',[o([[0,700],[200,0],[500,700]]),o([[200,700],[500,0],[700,700]])])},
  y:{curved:G.y,straight:displayDesign('y',[o([[0,500],[210,0]]),o([[420,500],[125,-200]])])},
  G:{'no-spur':G.G,spur:displayDesign('G',[o([[500,620],[500,700],[0,700],[0,0],[500,0],[500,390]]),o([[270,320],[540,320]])])},
  Q:{diagonal:G.Q,long:displayDesign('Q',[G.Q.shapes[0],
    RAW([['M',320,160],['C',440,5,495,-160,650,-160]])])},
  '4':{closed:G['4'],open:displayDesign('4',[o([[320,700],[320,0]]),o([[160,550],[0,200],[420,200]])])},
  '6':{closed:G['6'],open:displayDesign('6',OPEN_SIX)},
  '9':{closed:G['9'],open:displayDesign('9',OPEN_SIX.map(shape=>RAW(shape.raw.map(seg=>seg.map((v,i)=>i ? (i%2 ? 400-v : 700-v) : v)))))},
};
const DISPLAY_VARIANTS = {};
/** Resolve accented letters, script reuse and numeric derivatives to a design family. */
function displayFamily(ch){
  const base=NUMERIC_VARIANTS[ch]?.digit || (FRACTION_PARTS[ch]?.includes('4') ? '4' : latinBase(ch));
  const key=base==='k' ? 'K' : base==='4' ? 'four' : ['6','9'].includes(base) ? 'sixNine' : base;
  return DISPLAY_SETS.find(set=>set.key===key);
}
/** Describe the alternate opposite each cut default, including accented and small figures. */
function displayManifest(){
  if(!P.alternates) return {};
  const defaults=displayChoices(P.alternates), result={};
  const sources=Object.keys(G).concat(Object.keys(NUMERIC_VARIANTS).filter(ch=>ch.includes('.')));
  for(const ch of sources){
    const set=displayFamily(ch); if(!set) continue;
    const choice=set.choices.find(value=>value!==defaults[set.key]);
    const stem=[...ch].length===1 ? 'alt'+ch.codePointAt(0).toString(16).toUpperCase().padStart(4,'0') : ch;
    const name=stem+'.'+set.tag+'.'+choice.replaceAll('-','_');
    DISPLAY_VARIANTS[name]={source:ch,key:set.key,choice,letter:!['four','sixNine'].includes(set.key)};
    result[ch]={key:set.key,tag:set.tag,default:defaults[set.key],choices:{[defaults[set.key]]:ch,[choice]:name}};
  }
  return result;
}

const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
const weightFor = size => P.base + P.boost * clamp((28 - size) / 15, 0, 1);

/* ---------- drawing ---------- */
const f1 = v => (+v).toFixed(1);

/** Preserve vertical counter room in heavy Display masters without reducing stem weight.
 * Lowercase mapping reserves a pen radius at both height limits. An unmodulated
 * heavy pen then consumes that room again between stacked bowls and terminals.
 * Bound its horizontal diameter to 20% of x-height (15% with extended flat
 * terminals); lighter/contrasting pens
 * retain their requested ratio. Reader does not opt into this compensation.
 */
function displayContrast(weight, contrast, xHeight, ends='round'){
  return Math.max(contrast, weight / (xHeight * (ends === 'flat' ? .15 : .20)));
}

/** Support radii of the shared oval pen; the unrotated branch retains Reader arithmetic. */
function penHalf(S){
  if(!P.penAngle) return {hx:S/2,hy:S/(2*P.contrast)};
  const a=S/2,b=S/(2*P.contrast),t=P.penAngle*Math.PI/180;
  return {hx:Math.sqrt((a*Math.cos(t))**2+(b*Math.sin(t))**2),
    hy:Math.sqrt((a*Math.sin(t))**2+(b*Math.cos(t))**2)};
}

/** All shared strokes honor cut terminals and bounded sharp joins. */
function strokePath(d,width){
  const cap=P.cap==='flat' ? 'butt' : 'round',join=P.join==='sharp' ? 'miter' : 'round';
  return `<path d="${d}" fill="none" stroke="currentColor" stroke-width="${f1(width)}" stroke-linecap="${cap}" stroke-linejoin="${join}"${join==='miter' ? ' stroke-miterlimit="2"' : ''}/>`;
}

function radii(kind){
  if(kind === 'low'){
    if(P.ital){ const v = 0.6; return { rx:210, ry:210 + 60*v, k:0.667 - 0.115*v }; }   // italic curves are locked
    const v = P.round; return { rx:(210 + 50*v) * P.straight, ry:(210 + 60*v) * P.straight, k:0.667 - 0.115*v };
  }
  return { rx:P.caprx, ry:P.caprx, k:0.667 };
}

function pathFrom(pts, closed, kind){
  const n = pts.length, cmds = [], rr = radii(kind);
  const corner = i => {
    const p = pts[i], prev = pts[(i-1+n)%n], next = pts[(i+1)%n];
    const m = p[2] === undefined ? 1 : p[2];
    const ax = p[0]-prev[0], ay = p[1]-prev[1], bx = next[0]-p[0], by = next[1]-p[1];
    const l1 = Math.hypot(ax,ay), l2 = Math.hypot(bx,by);
    const axis = (Math.abs(ax)<0.01 || Math.abs(ay)<0.01) && (Math.abs(bx)<0.01 || Math.abs(by)<0.01);
    const perp = Math.abs(ax*bx + ay*by) < 1e-3*l1*l2;
    if(!axis || !perp || m === 0) return [['L',p]];
    const er = (vx,vy) => Math.abs(vy) < 0.01 ? rr.rx : rr.ry;
    const r1 = Math.min(er(ax,ay)*m, l1/2), r2 = Math.min(er(bx,by)*m, l2/2);
    if(r1 < 3 || r2 < 3) return [['L',p]];
    const p1 = [p[0]-ax/l1*r1, p[1]-ay/l1*r1];
    const p2 = [p[0]+bx/l2*r2, p[1]+by/l2*r2];
    if(P.corner === 'cut') return [['L',p1],['L',p2]];
    const c1 = [p1[0]+(p[0]-p1[0])*rr.k, p1[1]+(p[1]-p1[1])*rr.k];
    const c2 = [p2[0]+(p[0]-p2[0])*rr.k, p2[1]+(p[1]-p2[1])*rr.k];
    return [['L',p1],['C',c1,c2,p2]];
  };
  if(closed){ for(let i=0;i<n;i++) cmds.push(...corner(i)); }
  else {
    cmds.push(['L',pts[0]]);
    for(let i=1;i<n-1;i++) cmds.push(...corner(i));
    cmds.push(['L',pts[n-1]]);
  }
  const Pt = q => `${f1(q[0])} ${f1(-q[1])}`;
  let d = '';
  cmds.forEach((cm,i) => {
    if(i === 0){ d += `M${Pt(cm[1])}`; return; }
    d += cm[0] === 'L' ? `L${Pt(cm[1])}` : `C${Pt(cm[1])} ${Pt(cm[2])} ${Pt(cm[3])}`;
  });
  return d + (closed ? 'Z' : '');
}

const clipDone = {};
function ensureClip(top, bot){
  const id = `c${top}_${bot < 0 ? 'n'+(-bot) : bot}`;
  if(!clipDone[id]){
    clipDone[id] = 1;
    document.getElementById('clips').insertAdjacentHTML('beforeend',
      `<clipPath id="${id}" clipPathUnits="userSpaceOnUse"><rect x="-500" y="${-top}" width="6000" height="${top-bot}"/></clipPath>`);
  }
  return id;
}

const cache = {};
/** Select an opt-in Display design or the Reader's established upright/italic form. */
function pickBase(ch){
  if(P.alternates && DISPLAY_DESIGNS[ch]) return DISPLAY_DESIGNS[ch][displayChoices(P.alternates)[displayFamily(ch).key]];
  if(P.alternates && ['Ƙ','ƙ','ƴ','ĸ'].includes(ch)){
    const base=LANGUAGE_SPECIALS[ch], choice=displayChoices(P.alternates)[displayFamily(ch).key];
    const shapes=DISPLAY_DESIGNS[base][choice].shapes;
    return {...G[ch],shapes:ch==='ĸ' ? [G[ch].shapes[0],...shapes.slice(1)]
      : [...shapes,...G[ch].shapes.slice(G[base].shapes.length)]};
  }
  return ch === 'u' ? (P.ital ? IT.u : P.ufoot ? U_FOOT : U_PLAIN)
       : (P.ital && ch === 'a') ? A_IT : (P.ital && ch === 'f') ? F_IT : (P.ital && IT[ch]) ? IT[ch] : G[ch];
}
/* ---------- languages: accent marks, drawn in SEIReader's style ---------- */
const MARK = {
  acute:   (cx, y0) => ({ shapes:[o([[cx-45,y0],[cx+55,y0+110]])] }),
  grave:   (cx, y0) => ({ shapes:[o([[cx+45,y0],[cx-55,y0+110]])] }),
  circ:    (cx, y0) => ({ shapes:[o([[cx-95,y0],[cx,y0+105],[cx+95,y0]])] }),
  tilde:   (cx, y0) => ({ shapes:[RAW([['M',cx-115,y0+25],['C',cx-80,y0+105,cx-35,y0+105,cx,y0+60],['C',cx+35,y0+15,cx+80,y0+15,cx+115,y0+95]])] }),
  dier:    (cx, y0) => ({ dots:[[cx-100,y0+55],[cx+100,y0+55]] }),
  ring:    (cx, y0) => ({ shapes:[RAW(circ(cx, y0+65, 58))] }),
  cedilla: (cx)     => ({ shapes:[RAW([['M',cx,5], LN(cx,5,cx+15,-70), ['C',cx+30,-130,cx-20,-175,cx-80,-160]])] }),
  /** Draw a centered horizontal macron above the attachment point. */
  macron:  (cx,y) => ({ shapes:[o([[cx-100,y+30],[cx+100,y+30]])] }),
  /** Draw a shallow rounded breve with smooth symmetric ends. */
  breve:   (cx,y) => ({ shapes:[RAW([['M',cx-100,y+100],['C',cx-80,y-15,cx+80,y-15,cx+100,y+100]])] }),
  /** Place a single above-dot for dotted letters and combining accents. */
  dot:     (cx,y) => ({ dots:[[cx,y+40]] }),
  /** Draw a compact hook above for the shared combining-mark repertoire. */
  hook:    (cx,y) => ({ shapes:[RAW([['M',cx-30,y+100],['C',cx+75,y+140,cx+90,y+45,cx+10,y]])] }),
  /** Draw parallel acute strokes for Hungarian double-acute vowels. */
  double:  (cx,y) => ({ shapes:[o([[cx-100,y],[cx-10,y+110]]),o([[cx+30,y],[cx+120,y+110]])] }),
  /** Draw a centered caron with two symmetric diagonal strokes. */
  caron:   (cx,y) => ({ shapes:[o([[cx-95,y+105],[cx,y],[cx+95,y+105]])] }),
  /** Draw a right-side horn that can attach beside the base's upper bowl. */
  horn:    (cx,y) => ({ shapes:[RAW([['M',cx,y],['C',cx+105,y,cx+130,y+65,cx+105,y+130]])] }),
  /** Place a below-dot for Igbo vowels and combining sequences. */
  below:   (cx) => ({ dots:[[cx,-45]] }),
  /** Draw a compact below-comma for Romanian and combining accents. */
  comma:   (cx) => ({ shapes:[RAW([['M',cx+15,-15],['C',cx+30,-55,cx+10,-95,cx-25,-110]])] }),
  /** Draw an attached ogonek that curves left and returns toward its anchor. */
  ogonek:  (cx) => ({ shapes:[RAW([['M',cx,0],['C',cx-80,-55,cx-80,-125,cx+5,-110]])] }),
};
// Compact, light marks leave room for two levels inside the existing line metrics.
const COMBINING = Object.fromEntries([
  ['\u0300','grave','top'],['\u0301','acute','top'],['\u0302','circ','top'],
  ['\u0303','tilde','top'],['\u0304','macron','top'],['\u0306','breve','top'],
  ['\u0307','dot','top'],['\u0308','dier','top'],['\u0309','hook','top'],
  ['\u030a','ring','top'],['\u030b','double','top'],['\u030c','caron','top'],
  ['\u031b','horn','horn'],['\u0323','below','bottom'],['\u0326','comma','bottom'],
  ['\u0327','cedilla','bottom'],['\u0328','ogonek','ogonek'],
].map(([ch,mark,place]) => [ch,{mark,place}]));
for(const ch of Object.keys(COMBINING)) G[ch] = { comp:true };
const DOTLESS = { 'i.dotless':'i', 'j.dotless':'j' };
def('◌',440,'low',[],Array.from({length:12},(_,i) => {
  const t=i*Math.PI/6; return [220+190*Math.cos(t),250+190*Math.sin(t),.24];
}),[38,38]);
// Lexical apostrophes keep the established apostrophe drawing and advance.
G['ʻ'] = { comp:true }; G['ʼ'] = { comp:true };
G['\u2009'] = G['\u202f'] = { comp:true };
const ACC = {};
function acc(chars, base, marks, opt = {}){ [...chars].forEach((ch, i) => { ACC[ch] = Object.assign({ base, mark: marks[i] }, opt); G[ch] = { comp:true, w:0, kind:'low', shapes:[], dots:[], sb:[0,0] }; }); }
const M6 = ['grave','acute','circ','tilde','dier','ring'], M4 = ['grave','acute','circ','dier'], M5 = ['grave','acute','circ','tilde','dier'];
acc('ÀÁÂÃÄÅ', 'A', M6); acc('àáâãäå', 'a', M6);
acc('ÈÉÊË', 'E', M4);    acc('èéêë', 'e', M4);
acc('ÌÍÎÏ', 'I', M4);    acc('ìíîï', 'i', M4, { nodot:true });
acc('ÒÓÔÕÖ', 'O', M5);   acc('òóôõö', 'o', M5);
acc('ÙÚÛÜ', 'U', M4);    acc('ùúûü', 'u', M4);
acc('Ñ', 'N', ['tilde']); acc('ñ', 'n', ['tilde']);
acc('Ç', 'C', ['cedilla']); acc('ç', 'c', ['cedilla']);
acc('ÝŸ', 'Y', ['acute','dier']); acc('ýÿ', 'y', ['acute','dier']);
/* 0.34: encoded alphabets reuse the 0.33 attachment construction. These are
   precisely the missing letters in the ten pinned CLDR exemplar inventories. */
const LANGUAGE_COMPOSED = Object.fromEntries([...`ĀāĂăĄąĆćČčĎďĒēĔĕĘęĚěĞğĪīĬĭİĽľŃńŇňŌōŎŏŐőŔŕŘřŚśŞşŠšŢţŤťŪūŬŭŮůŰűŹźŻżŽžǸǹȘșȚțḾḿṄṅỊịỌọỤụ`]
  .map(ch => { const [base,...marks]=ch.normalize('NFD'); return [ch,{base,marks}]; }));
const LANGUAGE_SPECIALS = { 'ı':'i','Ł':'L','ł':'l','Ɓ':'B','Ɗ':'D','Ƙ':'K','ƙ':'k','Ƴ':'Y','ƴ':'y','ɓ':'b','ɗ':'d' };
for(const ch of Object.keys(LANGUAGE_COMPOSED)) G[ch]={comp:true};
G['ı']={comp:true};
/** Add only the distinctive stroke, retaining the family's existing skeleton. */
function hooked(ch,base,shape,before=0,after=0){
  const g=G[base];
  def(ch,g.w,g.kind,[...g.shapes,RAW(shape)],g.dots,[g.sb[0]+before,g.sb[1]+after]);
}
hooked('Ł','L',[['M',-70,285],LN(-70,285,195,465)],70);
hooked('ł','l',[['M',-70,285],LN(-70,285,145,415)],70,50);
const capHook=[['M',-155,565],['C',-175,650,-110,700,-55,700],['C',-20,700,0,675,0,625]];
hooked('Ɓ','B',capHook,175);
hooked('Ɗ','D',capHook,175);
hooked('Ƙ','K',[['M',0,570],['C',0,660,30,700,100,700],['C',165,700,185,640,150,600]]);
hooked('ƙ','k',[['M',0,620],['C',0,715,30,740,100,740],['C',165,740,185,685,150,650]]);
hooked('Ƴ','Y',[['M',500,700],['C',575,700,605,635,560,585]],0,100);
hooked('ƴ','y',[['M',420,500],['C',490,545,570,505,535,435]],0,155);
hooked('ɓ','b',[['M',0,630],['C',0,715,45,740,105,740],['C',170,740,195,680,160,645]]);
hooked('ɗ','d',[['M',420,630],['C',420,715,375,740,315,740],['C',250,740,225,680,260,645]]);
// Real italic d has its established exit foot; the hook follows that skeleton.
IT['ɗ']={...G['ɗ'],shapes:[...IT.d.shapes,G['ɗ'].shapes.at(-1)],sb:[...IT.d.sb]};
/* Phase 4, step 1: add the remaining Extended-A composites through ACC.
   Existing accent recipes and the fixed-gap, light-mark construction stay intact. */
acc('Ĉ','C',['circ'],{additive:true,marks:["\u0302"]});
acc('ĉ','c',['circ'],{additive:true,marks:["\u0302"]});
acc('Ċ','C',['dot'],{additive:true,marks:["\u0307"]});
acc('ċ','c',['dot'],{additive:true,marks:["\u0307"]});
acc('Ė','E',['dot'],{additive:true,marks:["\u0307"]});
acc('ė','e',['dot'],{additive:true,marks:["\u0307"]});
acc('Ĝ','G',['circ'],{additive:true,marks:["\u0302"]});
acc('ĝ','g',['circ'],{additive:true,marks:["\u0302"]});
acc('Ġ','G',['dot'],{additive:true,marks:["\u0307"]});
acc('ġ','g',['dot'],{additive:true,marks:["\u0307"]});
acc('Ģ','G',['cedilla'],{additive:true,marks:["\u0327"]});
acc('ģ','g',['cedilla'],{additive:true,marks:["\u0327"]});
acc('Ĥ','H',['circ'],{additive:true,marks:["\u0302"]});
acc('ĥ','h',['circ'],{additive:true,marks:["\u0302"]});
acc('Ĩ','I',['tilde'],{additive:true,marks:["\u0303"]});
acc('ĩ','i',['tilde'],{additive:true,marks:["\u0303"]});
acc('Į','I',['ogonek'],{additive:true,marks:["\u0328"]});
acc('į','i',['ogonek'],{additive:true,marks:["\u0328"]});
acc('Ĵ','J',['circ'],{additive:true,marks:["\u0302"]});
acc('ĵ','j',['circ'],{additive:true,marks:["\u0302"]});
acc('Ķ','K',['cedilla'],{additive:true,marks:["\u0327"]});
acc('ķ','k',['cedilla'],{additive:true,marks:["\u0327"]});
acc('Ĺ','L',['acute'],{additive:true,marks:["\u0301"]});
acc('ĺ','l',['acute'],{additive:true,marks:["\u0301"]});
acc('Ļ','L',['cedilla'],{additive:true,marks:["\u0327"]});
acc('ļ','l',['cedilla'],{additive:true,marks:["\u0327"]});
acc('Ņ','N',['cedilla'],{additive:true,marks:["\u0327"]});
acc('ņ','n',['cedilla'],{additive:true,marks:["\u0327"]});
acc('Ŗ','R',['cedilla'],{additive:true,marks:["\u0327"]});
acc('ŗ','r',['cedilla'],{additive:true,marks:["\u0327"]});
acc('Ŝ','S',['circ'],{additive:true,marks:["\u0302"]});
acc('ŝ','s',['circ'],{additive:true,marks:["\u0302"]});
acc('Ũ','U',['tilde'],{additive:true,marks:["\u0303"]});
acc('ũ','u',['tilde'],{additive:true,marks:["\u0303"]});
acc('Ų','U',['ogonek'],{additive:true,marks:["\u0328"]});
acc('ų','u',['ogonek'],{additive:true,marks:["\u0328"]});
acc('Ŵ','W',['circ'],{additive:true,marks:["\u0302"]});
acc('ŵ','w',['circ'],{additive:true,marks:["\u0302"]});
acc('Ŷ','Y',['circ'],{additive:true,marks:["\u0302"]});
acc('ŷ','y',['circ'],{additive:true,marks:["\u0302"]});
// Latvian small g uses the turned comma above its bowl, clear of the descender.
MARK.commaAbove=(cx,y)=>({shapes:[RAW([['M',cx-15,y],['C',cx-30,y+40,cx-10,y+80,cx+25,y+95]])]});
COMBINING['\u0312']={mark:'commaAbove',place:'top'}; G['\u0312']={comp:true};
ACC['ģ'].mark='commaAbove'; ACC['ģ'].marks=['\u0312'];
for(const ch of 'ĢĶķĻļŅņŖŗ'){ ACC[ch].mark='comma'; ACC[ch].marks=['\u0326']; }
const PHASE4_SPECIALS = {'Đ':'D','đ':'d','Ħ':'H','ħ':'h','Ŧ':'T','ŧ':'t','ĸ':'k','Ŋ':'N','ŋ':'n','ſ':'f','Ĳ':'I','ĳ':'i','Ŀ':'L','ŀ':'l','ŉ':'n'};
hooked('Đ','D',[['M',-50,350],LN(-50,350,170,350)],50);
hooked('đ','d',[['M',250,630],LN(250,630,560,630)],0,90);
IT['đ']={...G['đ'],shapes:[...IT.d.shapes,G['đ'].shapes.at(-1)],sb:[IT.d.sb[0],IT.d.sb[1]+90]};
hooked('Ħ','H',[['M',-55,540],LN(-55,540,535,540)],55,55);
hooked('ħ','h',[['M',-55,620],LN(-55,620,185,620)],55);
IT['ħ']={...G['ħ'],shapes:[...IT.h.shapes,G['ħ'].shapes.at(-1)],sb:[IT.h.sb[0]+55,IT.h.sb[1]]};
hooked('Ŧ','T',[['M',80,360],LN(80,360,420,360)]);
hooked('ŧ','t',[['M',25,270],LN(25,270,310,270)]);
def('ĸ',420,'low',[o([[0,0],[0,500]]),o([[415,500],[0,185]]),o([[165,309],[425,0]])],[],[66,20]);
hooked('Ŋ','N',[['M',500,0],['C',500,-125,455,-195,350,-195]],0,20);
def('ŋ',400,'low',[o([[0,0],[0,500]]),shoulder(0,400),RAW([['M',400,0],['C',400,-140,360,-200,260,-200]])],[],[66,66]);
IT['ŋ']={...G['ŋ'],shapes:[o([[0,0],[0,500]]),shoulder(0,400,250),G['ŋ'].shapes.at(-1)]};
def('ſ',350,'low',[o([[375,740],[150,740,1],[150,0]])],[],[30,14]);
const PHASE4_JOINED={'Ĳ':['I','J'],'ĳ':['i','j'],'Ŀ':['L','·'],'ŀ':['l','·'],'ŉ':['ʼ','n']};
for(const ch of Object.keys(PHASE4_JOINED)) G[ch]={comp:true};
/** Join new special letters from existing drawings, retaining each component's metrics. */
function phase4Joined(ch,S){
  const parts=PHASE4_JOINED[ch].map(base=>glyph(base,S));
  const first=parts[0],second=parts[1],dx=first.w+S+first.sb1+second.sb0;
  const body=first.body+moveNumericBody(second.body,1,dx,0,1);
  return {...first,body,w:dx+second.w,sb1:second.sb1,clipId:ensureClip(1250,-500),ink:undefined};
}
Object.assign(LANGUAGE_SPECIALS,PHASE4_SPECIALS);
const PHASE4_LETTERS=Object.keys(PHASE4_SPECIALS);
const LANGUAGE_ALTERNATES={'i.loclTRK':'i','i.below.dotless':'ị'};
/** Map new derivatives to the approved optical pair and letter-space classes. */
function latinBase(ch){
  const source=DOTLESS[ch] || LANGUAGE_ALTERNATES[ch] || scriptReuse(ch) || ch;
  const base=LANGUAGE_COMPOSED[source]?.base || LANGUAGE_SPECIALS[source] || ACC[source]?.base || source;
  return base===source ? source : latinBase(base);
}
/** Return base-letter mappings for accented and language-specific glyphs. */
window.getBaseMap = () => Object.fromEntries([...Object.keys(ACC),...Object.keys(LANGUAGE_COMPOSED),...Object.keys(LANGUAGE_SPECIALS),...PHASE4_SCRIPT]
  .map(ch=>[ch,latinBase(ch)]).filter(([ch,base])=>ch!==base));

/* Keep nominal widths and weight controls stable. Optical stroke calibration
   gives Light more substance and Medium more counter room at reading sizes.
   These are static masters: the correction also applies at larger sizes. */
const READING_LETTERS = new Set([...('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÆŒÐÞØæœßðþøﬁﬂ')]);
const TEXT_MARKS = new Set([...`.,:;…!?'"‘’“”‚„‛‟-–—()[]¡¿`]);
const QUIET_MARKS = new Set([...`'"‘’“”‚„‛‟-–—`]);
/* Phase 4, step 2: original Cyrillic and monotonic Greek constructions.
   Identical skeletons resolve directly to existing Latin drawings in every master. */
const SCRIPT_REUSE={
  'А':'A','В':'B','Е':'E','К':'K','М':'M','Н':'H','О':'O','Р':'P','С':'C','Т':'T','Х':'X',
  'а':'a','е':'e','о':'o','р':'p','с':'c','х':'x','у':'y',
  'І':'I','і':'i','Ј':'J','ј':'j','Ѕ':'S','ѕ':'s','Ё':'Ë','ё':'ë','Ї':'Ï','ї':'ï',
  'Α':'A','Β':'B','Ε':'E','Ζ':'Z','Η':'H','Ι':'I','Κ':'K','Μ':'M','Ν':'N','Ο':'O','Ρ':'P','Τ':'T','Υ':'Y','Χ':'X',
  'ο':'o','ρ':'p','ν':'v','Γ':'Г','Π':'П','Φ':'Ф','φ':'ф','κ':'к','Ϊ':'Ï','Ϋ':'Ÿ',';':';','·':'·'
};
const SCRIPT_ITALIC_REUSE={'д':'g','и':'u','п':'n','т':'m'};
for(const ch of Object.keys(SCRIPT_REUSE)) G[ch]={comp:true};
// Capitals retain the family's 700-unit cap construction and softened corners.
def('Б',440,'cap',[o([[430,700],[0,700],[0,0]]),o([[0,360],[440,360],[440,0],[0,0]])],[],[66,52]);
def('Г',450,'cap',[o([[0,0],[0,700],[450,700]])],[],[66,30]);
def('Д',590,'cap',[o([[0,0],[120,180],[180,700],[460,700],[460,0]]),o([[0,-110],[0,0],[590,0],[590,-110]])],[],[45,45]);
def('Ж',700,'cap',[o([[350,0],[350,700]]),o([[0,700],[350,350],[0,0]]),o([[700,700],[350,350],[700,0]])],[],[25,25]);
def('З',470,'cap',[o([[0,600],[0,700],[440,700],[440,350],[160,350]]),o([[160,350],[470,350],[470,0],[0,0],[0,100]])],[],[50,50]);
def('И',500,'cap',[o([[0,700],[0,0],[500,700],[500,0]])],[],[66,66]);
def('Л',510,'cap',[o([[0,0],[95,70],[180,700],[510,700],[510,0]])],[],[30,66]);
def('П',480,'cap',[o([[0,0],[0,700],[480,700],[480,0]])],[],[66,66]);
def('У',500,'cap',[o([[0,700],[265,280],[500,700]]),o([[265,280],[120,0],[10,0]])],[],[25,25]);
def('Ф',650,'cap',[R(0,130,650,570),o([[325,0],[325,700]])],[],[52,52]);
def('Ц',480,'cap',[o([[0,700],[0,0],[480,0],[480,700]]),o([[480,0],[560,0],[560,-110]])],[],[66,45]);
def('Ч',480,'cap',[o([[0,700],[0,320],[480,320]]),o([[480,700],[480,0]])],[],[66,66]);
def('Ш',720,'cap',[o([[0,700],[0,0],[720,0],[720,700]]),o([[360,0],[360,700]])],[],[66,66]);
def('Щ',720,'cap',[...G['Ш'].shapes,o([[720,0],[800,0],[800,-110]])],[],[66,45]);
def('Ъ',530,'cap',[o([[-110,700],[0,700],[0,0]]),o([[0,360],[530,360],[530,0],[0,0]])],[],[140,52]);
def('Ь',440,'cap',[o([[0,700],[0,0]]),o([[0,360],[440,360],[440,0],[0,0]])],[],[66,52]);
def('Ы',680,'cap',[...G['Ь'].shapes,o([[680,700],[680,0]])],[],[66,66]);
def('Э',500,'cap',[o([[0,560],[0,700],[500,700],[500,0],[0,0],[0,140]]),o([[500,350],[170,350]])],[],[50,52]);
def('Ю',760,'cap',[o([[0,700],[0,0]]),o([[0,350],[210,350]]),R(210,0,760,700)],[],[66,52]);
def('Я',450,'cap',[o([[450,0],[450,700,0],[20,700],[20,320],[450,320,0]]),o([[240,320],[0,0]])],[],[40,66]);
// Lowercase: the same bowls and shoulders, at the existing x-height.
def('б',420,'low',[R(0,0,420,500),RAW([['M',0,240],LN(0,240,0,520),['C',0,675,120,740,255,740],['C',330,740,395,750,435,775]])],[],[50,50]);
def('в',390,'low',[c([[0,245,0],[0,500,0],[350,500],[350,245]]),c([[0,0,0],[0,245,0],[390,245],[390,0]])],[],[66,50]);
def('г',370,'low',[o([[0,0],[0,500],[370,500]])],[],[66,30]);
def('д',530,'low',[o([[0,0],[90,100],[155,500],[420,500],[420,0]]),o([[0,-110],[0,0],[530,0],[530,-110]])],[],[45,45]);
def('ж',620,'low',[o([[310,0],[310,500]]),o([[0,500],[310,250],[0,0]]),o([[620,500],[310,250],[620,0]])],[],[25,25]);
def('з',420,'low',[o([[0,410],[0,500],[390,500],[390,250],[135,250]]),o([[135,250],[420,250],[420,0],[0,0],[0,80]])],[],[46,46]);
def('и',400,'low',[o([[0,500],[0,0],[400,500],[400,0]])],[],[66,66]);
def('к',420,'low',[o([[0,0],[0,500]]),o([[415,500],[0,185]]),o([[165,309],[425,0]])],[],[66,20]);
def('л',450,'low',[o([[0,0],[80,60],[160,500],[450,500],[450,0]])],[],[30,66]);
def('м',530,'low',[o([[0,0],[0,500],[265,140],[530,500],[530,0]])],[],[66,66]);
def('н',400,'low',[o([[0,0],[0,500]]),o([[400,0],[400,500]]),o([[0,250],[400,250]])],[],[66,66]);
def('п',400,'low',[o([[0,0],[0,500],[400,500],[400,0]])],[],[66,66]);
def('т',450,'low',[o([[0,500],[450,500]]),o([[225,500],[225,0]])],[],[10,10]);
def('ф',560,'low',[R(0,0,560,500),o([[280,740],[280,-200]])],[],[50,50]);
def('ц',400,'low',[o([[0,500],[0,0],[400,0],[400,500]]),o([[400,0],[475,0],[475,-110]])],[],[66,45]);
def('ч',400,'low',[o([[0,500],[0,230],[400,230]]),o([[400,500],[400,0]])],[],[66,66]);
def('ш',640,'low',[o([[0,500],[0,0],[640,0],[640,500]]),o([[320,0],[320,500]])],[],[66,66]);
def('щ',640,'low',[...G['ш'].shapes,o([[640,0],[715,0],[715,-110]])],[],[66,45]);
def('ъ',470,'low',[o([[-95,500],[0,500],[0,0]]),o([[0,280],[470,280],[470,0],[0,0]])],[],[125,50]);
def('ь',390,'low',[o([[0,500],[0,0]]),o([[0,280],[390,280],[390,0],[0,0]])],[],[66,50]);
def('ы',600,'low',[...G['ь'].shapes,o([[600,500],[600,0]])],[],[66,66]);
def('э',420,'low',[o([[0,400],[0,500],[420,500],[420,0],[0,0],[0,100]]),o([[420,250],[135,250]])],[],[46,50]);
def('ю',650,'low',[o([[0,500],[0,0]]),o([[0,250],[210,250]]),R(210,0,650,500)],[],[66,50]);
def('я',400,'low',[o([[400,0],[400,500,0],[15,500],[15,245],[400,245,0]]),o([[220,245],[0,0]])],[],[40,66]);
// Russian cursive forms are drawn before the shared italic shear.
IT['б']={...G['б'],shapes:[bowlOnStem(420),RAW([['M',0,270],['C',0,555,55,700,250,740],['C',325,755,395,750,445,715]])]};
IT['в']={...G['в'],w:400,shapes:[RAW([['M',0,0],LN(0,0,0,560),['C',0,700,80,740,155,740],['C',290,740,300,550,130,420],['C',60,368,0,335,0,275],['C',0,500,400,500,400,250],['C',400,80,260,0,0,0]])]};
IT['г']={...G['г'],shapes:[RAW([['M',10,420],['C',100,535,375,535,375,425],['C',375,320,0,200,0,90],['C',0,-20,250,-20,385,75]])]};
// Additional common Slavic letters, including Ukrainian and Serbian/Macedonian.
def('Ґ',450,'cap',[o([[0,0],[0,700],[450,700],[450,790]])],[],[66,30]);
def('ґ',370,'low',[o([[0,0],[0,500],[370,500],[370,620]])],[],[66,30]);
def('Є',500,'cap',[...G['C'].shapes,o([[0,350],[330,350]])],[],[52,44]);
def('є',420,'low',[...G['c'].shapes,o([[0,250],[280,250]])],[],[50,40]);
def('Џ',480,'cap',[...G['Ц'].shapes.slice(0,1),o([[240,0],[240,-110]])],[],[66,66]);
def('џ',400,'low',[...G['ц'].shapes.slice(0,1),o([[200,0],[200,-110]])],[],[66,66]);
def('Ћ',480,'cap',[o([[0,0],[0,700]]),o([[-80,520],[400,520]]),o([[0,280],[480,280],[480,0]])],[],[110,66]);
def('ћ',400,'low',[o([[0,0],[0,740]]),o([[-70,590],[280,590]]),shoulder(0,400)],[],[100,66]);
def('Ђ',480,'cap',[...G['Ћ'].shapes,RAW([['M',480,0],['C',480,-130,440,-195,315,-195]])],[],[110,66]);
def('ђ',400,'low',[o([[0,0],[0,740]]),o([[-70,590],[280,590]]),shoulder(0,400),RAW([['M',400,0],['C',400,-130,360,-195,255,-195]])],[],[100,66]);
/** Translate shared source shapes when a Slavic digraph needs a joined bowl. */
function scriptShift(shapes,dx){
  return shapes.map(s=>s.p ? {...s,p:s.p.map(q=>[q[0]+dx,q[1],q[2]])}
    : s.raw ? {...s,raw:s.raw.map(seg=>seg.map((v,i)=>i && i%2 ? v+dx : v))} : s);
}
def('Љ',800,'cap',[...G['Л'].shapes,o([[510,360],[800,360],[800,0],[510,0]])],[],[30,52]);
def('љ',690,'low',[...G['л'].shapes,o([[450,280],[690,280],[690,0],[450,0]])],[],[30,50]);
def('Њ',780,'cap',[...G['H'].shapes,o([[480,360],[780,360],[780,0],[480,0]])],[],[66,52]);
def('њ',650,'low',[...G['н'].shapes,o([[400,280],[650,280],[650,0],[400,0]])],[],[66,50]);
// Greek capitals reuse Latin only when the shape really is identical.
def('Γ',450,'cap',[o([[0,0],[0,700],[450,700]])],[],[66,30]);
def('Δ',540,'cap',[c([[0,0,0],[270,700,0],[540,0,0]])],[],[15,15]);
def('Θ',560,'cap',[R(0,0,560,700),o([[0,350],[560,350]])],[],[52,52]);
def('Λ',540,'cap',[o([[0,0],[270,700],[540,0]])],[],[15,15]);
def('Ξ',480,'cap',[o([[0,700],[480,700]]),o([[40,350],[440,350]]),o([[0,0],[480,0]])],[],[50,50]);
def('Π',480,'cap',[o([[0,0],[0,700],[480,700],[480,0]])],[],[66,66]);
def('Σ',480,'cap',[o([[480,700],[0,700],[265,350],[0,0],[480,0]])],[],[50,50]);
def('Φ',650,'cap',[...G['Ф'].shapes],[],[52,52]);
def('Ψ',650,'cap',[o([[0,700],[0,220],[650,220],[650,700]]),o([[325,700],[325,0]])],[],[66,66]);
def('Ω',560,'cap',[o([[0,0],[160,0],[160,100],[0,220],[0,700],[560,700],[560,220],[400,100],[400,0],[560,0]])],[],[52,52]);
def('α',410,'low',[...A_IT.shapes],[],[48,28]);
def('β',400,'low',[RAW([['M',0,-200],LN(0,-200,0,555),['C',0,675,65,740,175,740],['C',330,740,385,620,340,520],['C',315,460,240,400,95,350],['C',270,410,400,310,400,180],['C',400,65,315,0,180,0],['C',80,0,0,45,0,150]])],[],[66,50]);
def('γ',420,'low',[RAW([['M',0,500],['C',115,500,190,335,215,100],['C',230,-40,245,-145,210,-200]]),RAW([['M',420,500],['C',350,340,280,180,215,100]])],[],[30,30]);
def('δ',420,'low',[R(0,0,420,500),RAW([['M',420,245],['C',420,525,85,555,85,675],['C',85,740,220,765,360,710]])],[],[50,50]);
def('ε',400,'low',[RAW([['M',390,430],['C',345,485,295,500,210,500],['C',85,500,0,450,0,380],['C',0,305,70,250,190,250],['C',75,250,0,205,0,130],['C',0,55,90,0,215,0],['C',300,0,355,20,400,75]]),o([[190,250],[330,250]])],[],[50,40]);
def('ζ',400,'low',[RAW([['M',0,500],LN(0,500,400,500),['C',270,380,0,260,0,115],['C',0,25,140,0,300,0],['C',390,0,390,-110,300,-150]])],[],[46,46]);
def('η',400,'low',[o([[0,0],[0,500]]),shoulder(0,400),o([[400,0],[400,-200]])],[],[66,66]);
def('θ',420,'low',[R(0,0,420,740),o([[0,365],[420,365]])],[],[50,50]);
def('ι',95,'low',[o([[0,500],[0,0,.55],[95,0]])],[],[66,40]);
def('κ',420,'low',[...G['ĸ'].shapes],[],[66,20]);
def('λ',450,'low',[RAW([['M',100,740],['C',220,740,225,520,270,400],LN(270,400,450,0)]),o([[270,400],[0,0]])],[],[25,25]);
def('μ',465,'low',[...U_FOOT.shapes,o([[0,220],[0,-200]])],[],[66,40]);
def('ξ',400,'low',[RAW([['M',0,740],['C',90,695,280,695,390,740],['C',315,600,0,560,0,420],['C',0,340,160,330,335,340],['C',160,325,0,255,0,115],['C',0,20,150,0,300,0],['C',385,0,390,-105,300,-150]])],[],[46,46]);
def('π',480,'low',[o([[-20,500],[500,500]]),o([[70,500],[70,0]]),o([[420,500],[420,0,.55],[480,0]])],[],[50,40]);
def('σ',490,'low',[R(0,0,420,500),o([[210,500],[490,500]])],[],[50,35]);
def('ς',400,'low',[RAW([['M',400,500],['C',190,530,0,440,0,235],['C',0,75,125,35,285,0],['C',410,-25,405,-115,290,-170]])],[],[50,45]);
def('τ',370,'low',[o([[0,500],[370,500]]),o([[170,500],[170,0,.6],[255,0]])],[],[30,30]);
def('υ',400,'low',[...U_PLAIN.shapes],[],[66,66]);
def('φ',560,'low',[R(0,0,560,500),o([[280,740],[280,-200]])],[],[50,50]);
def('χ',420,'low',[o([[0,500],[420,-200]]),o([[420,500],[0,-200]])],[],[25,25]);
def('ψ',500,'low',[o([[0,500],[0,100],[500,100],[500,500]]),o([[250,500],[250,-200]])],[],[66,66]);
def('ω',560,'low',[RAW([['M',0,500],LN(0,500,0,220),['C',0,75,40,0,135,0],['C',220,0,280,65,280,220],LN(280,220,280,320),LN(280,320,280,220),['C',280,65,340,0,425,0],['C',520,0,560,75,560,220],LN(560,220,560,500)])],[],[50,50]);
const PHASE4_SCRIPT=new Set([...Object.keys(SCRIPT_REUSE),...Object.keys(SCRIPT_ITALIC_REUSE),
  ...'БГДЖЗИЛПУФЦЧШЩЪЫЬЭЮЯбвгджзиклмнптфцчшщъыьэюяҐґЄєЏџЋћЂђЉљЊњΓΔΘΛΞΠΣΦΨΩαβγδεζηθικλμξπσςτυφχψω']);
for(const ch of PHASE4_SCRIPT) READING_LETTERS.add(ch);
for(const ch of 'бвзфэюβδεθσςφωФЭЮΘΦΩ') OVS.add(ch);
for(const ch of 'ЖШЩЫЮжмшщыюЉљЊњΦΩφω') WIDE.add(ch);
acc('Ѐ','Е',['grave'],{additive:true,marks:["\u0300"]});
PHASE4_SCRIPT.add('Ѐ');
acc('Ё','Е',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('Ё');
acc('Ѓ','Г',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ѓ');
acc('Ї','І',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('Ї');
acc('Ќ','К',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ќ');
acc('Ѝ','И',['grave'],{additive:true,marks:["\u0300"]});
PHASE4_SCRIPT.add('Ѝ');
acc('Ў','У',['breve'],{additive:true,marks:["\u0306"]});
PHASE4_SCRIPT.add('Ў');
acc('Й','И',['breve'],{additive:true,marks:["\u0306"]});
PHASE4_SCRIPT.add('Й');
acc('й','и',['breve'],{additive:true,marks:["\u0306"]});
PHASE4_SCRIPT.add('й');
acc('ѐ','е',['grave'],{additive:true,marks:["\u0300"]});
PHASE4_SCRIPT.add('ѐ');
acc('ё','е',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('ё');
acc('ѓ','г',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ѓ');
acc('ї','і',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('ї');
acc('ќ','к',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ќ');
acc('ѝ','и',['grave'],{additive:true,marks:["\u0300"]});
PHASE4_SCRIPT.add('ѝ');
acc('ў','у',['breve'],{additive:true,marks:["\u0306"]});
PHASE4_SCRIPT.add('ў');
acc('Ά','Α',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ά');
acc('Έ','Ε',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Έ');
acc('Ή','Η',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ή');
acc('Ί','Ι',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ί');
acc('Ό','Ο',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ό');
acc('Ύ','Υ',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ύ');
acc('Ώ','Ω',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('Ώ');
acc('ά','α',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ά');
acc('έ','ε',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('έ');
acc('ή','η',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ή');
acc('ί','ι',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ί');
acc('ό','ο',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ό');
acc('ύ','υ',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ύ');
acc('ώ','ω',['acute'],{additive:true,marks:["\u0301"]});
PHASE4_SCRIPT.add('ώ');
acc('Ϊ','Ι',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('Ϊ');
acc('Ϋ','Υ',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('Ϋ');
acc('ϊ','ι',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('ϊ');
acc('ϋ','υ',['dier'],{additive:true,marks:["\u0308"]});
PHASE4_SCRIPT.add('ϋ');
acc('ΐ','ι',['dier','acute'],{additive:true,marks:["\u0308", "\u0301"]});
PHASE4_SCRIPT.add('ΐ');
acc('ΰ','υ',['dier','acute'],{additive:true,marks:["\u0308", "\u0301"]});
PHASE4_SCRIPT.add('ΰ');
Object.assign(LANGUAGE_SPECIALS,SCRIPT_REUSE);
/* Phase 4, step 3: Vietnamese structural vowels and all encoded tones.
   Reuse the existing circumflex/breve parents, then attach a light tone with
   the established fixed gap. The existing mark and vowel outlines stay intact. */
acc("Ơ","O",["horn"],{additive:true,marks:["\u031b"]});
acc("ơ","o",["horn"],{additive:true,marks:["\u031b"]});
acc("Ư","U",["horn"],{additive:true,marks:["\u031b"]});
acc("ư","u",["horn"],{additive:true,marks:["\u031b"]});
acc("Ạ","A",["below"],{additive:true,marks:["\u0323"]});
acc("ạ","a",["below"],{additive:true,marks:["\u0323"]});
acc("Ả","A",["hook"],{additive:true,marks:["\u0309"]});
acc("ả","a",["hook"],{additive:true,marks:["\u0309"]});
acc("Ấ","Â",["acute"],{additive:true,marks:["\u0301"]});
acc("ấ","â",["acute"],{additive:true,marks:["\u0301"]});
acc("Ầ","Â",["grave"],{additive:true,marks:["\u0300"]});
acc("ầ","â",["grave"],{additive:true,marks:["\u0300"]});
acc("Ẩ","Â",["hook"],{additive:true,marks:["\u0309"]});
acc("ẩ","â",["hook"],{additive:true,marks:["\u0309"]});
acc("Ẫ","Â",["tilde"],{additive:true,marks:["\u0303"]});
acc("ẫ","â",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ậ","Â",["below"],{additive:true,marks:["\u0323"]});
acc("ậ","â",["below"],{additive:true,marks:["\u0323"]});
acc("Ắ","Ă",["acute"],{additive:true,marks:["\u0301"]});
acc("ắ","ă",["acute"],{additive:true,marks:["\u0301"]});
acc("Ằ","Ă",["grave"],{additive:true,marks:["\u0300"]});
acc("ằ","ă",["grave"],{additive:true,marks:["\u0300"]});
acc("Ẳ","Ă",["hook"],{additive:true,marks:["\u0309"]});
acc("ẳ","ă",["hook"],{additive:true,marks:["\u0309"]});
acc("Ẵ","Ă",["tilde"],{additive:true,marks:["\u0303"]});
acc("ẵ","ă",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ặ","Ă",["below"],{additive:true,marks:["\u0323"]});
acc("ặ","ă",["below"],{additive:true,marks:["\u0323"]});
acc("Ẹ","E",["below"],{additive:true,marks:["\u0323"]});
acc("ẹ","e",["below"],{additive:true,marks:["\u0323"]});
acc("Ẻ","E",["hook"],{additive:true,marks:["\u0309"]});
acc("ẻ","e",["hook"],{additive:true,marks:["\u0309"]});
acc("Ẽ","E",["tilde"],{additive:true,marks:["\u0303"]});
acc("ẽ","e",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ế","Ê",["acute"],{additive:true,marks:["\u0301"]});
acc("ế","ê",["acute"],{additive:true,marks:["\u0301"]});
acc("Ề","Ê",["grave"],{additive:true,marks:["\u0300"]});
acc("ề","ê",["grave"],{additive:true,marks:["\u0300"]});
acc("Ể","Ê",["hook"],{additive:true,marks:["\u0309"]});
acc("ể","ê",["hook"],{additive:true,marks:["\u0309"]});
acc("Ễ","Ê",["tilde"],{additive:true,marks:["\u0303"]});
acc("ễ","ê",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ệ","Ê",["below"],{additive:true,marks:["\u0323"]});
acc("ệ","ê",["below"],{additive:true,marks:["\u0323"]});
acc("Ỉ","I",["hook"],{additive:true,marks:["\u0309"]});
acc("ỉ","i",["hook"],{additive:true,marks:["\u0309"]});
acc("Ỏ","O",["hook"],{additive:true,marks:["\u0309"]});
acc("ỏ","o",["hook"],{additive:true,marks:["\u0309"]});
acc("Ố","Ô",["acute"],{additive:true,marks:["\u0301"]});
acc("ố","ô",["acute"],{additive:true,marks:["\u0301"]});
acc("Ồ","Ô",["grave"],{additive:true,marks:["\u0300"]});
acc("ồ","ô",["grave"],{additive:true,marks:["\u0300"]});
acc("Ổ","Ô",["hook"],{additive:true,marks:["\u0309"]});
acc("ổ","ô",["hook"],{additive:true,marks:["\u0309"]});
acc("Ỗ","Ô",["tilde"],{additive:true,marks:["\u0303"]});
acc("ỗ","ô",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ộ","Ô",["below"],{additive:true,marks:["\u0323"]});
acc("ộ","ô",["below"],{additive:true,marks:["\u0323"]});
acc("Ớ","Ơ",["acute"],{additive:true,marks:["\u0301"]});
acc("ớ","ơ",["acute"],{additive:true,marks:["\u0301"]});
acc("Ờ","Ơ",["grave"],{additive:true,marks:["\u0300"]});
acc("ờ","ơ",["grave"],{additive:true,marks:["\u0300"]});
acc("Ở","Ơ",["hook"],{additive:true,marks:["\u0309"]});
acc("ở","ơ",["hook"],{additive:true,marks:["\u0309"]});
acc("Ỡ","Ơ",["tilde"],{additive:true,marks:["\u0303"]});
acc("ỡ","ơ",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ợ","Ơ",["below"],{additive:true,marks:["\u0323"]});
acc("ợ","ơ",["below"],{additive:true,marks:["\u0323"]});
acc("Ủ","U",["hook"],{additive:true,marks:["\u0309"]});
acc("ủ","u",["hook"],{additive:true,marks:["\u0309"]});
acc("Ứ","Ư",["acute"],{additive:true,marks:["\u0301"]});
acc("ứ","ư",["acute"],{additive:true,marks:["\u0301"]});
acc("Ừ","Ư",["grave"],{additive:true,marks:["\u0300"]});
acc("ừ","ư",["grave"],{additive:true,marks:["\u0300"]});
acc("Ử","Ư",["hook"],{additive:true,marks:["\u0309"]});
acc("ử","ư",["hook"],{additive:true,marks:["\u0309"]});
acc("Ữ","Ư",["tilde"],{additive:true,marks:["\u0303"]});
acc("ữ","ư",["tilde"],{additive:true,marks:["\u0303"]});
acc("Ự","Ư",["below"],{additive:true,marks:["\u0323"]});
acc("ự","ư",["below"],{additive:true,marks:["\u0323"]});
acc("Ỳ","Y",["grave"],{additive:true,marks:["\u0300"]});
acc("ỳ","y",["grave"],{additive:true,marks:["\u0300"]});
acc("Ỵ","Y",["below"],{additive:true,marks:["\u0323"]});
acc("ỵ","y",["below"],{additive:true,marks:["\u0323"]});
acc("Ỷ","Y",["hook"],{additive:true,marks:["\u0309"]});
acc("ỷ","y",["hook"],{additive:true,marks:["\u0309"]});
acc("Ỹ","Y",["tilde"],{additive:true,marks:["\u0303"]});
acc("ỹ","y",["tilde"],{additive:true,marks:["\u0303"]});
const VIETNAMESE_ADDED=new Set([..."ƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ"]);
/** Choose the established cursive skeleton before applying the family's italic shear. */
function scriptReuse(ch){ return (P.ital && SCRIPT_ITALIC_REUSE[ch]) || SCRIPT_REUSE[ch]; }
window.getScriptChars=()=>[...PHASE4_SCRIPT].filter(ch=>G[ch] && !ACC[ch] && latinBase(ch)===ch).join('');

/** Interpolate stroke corrections without changing any glyph advance. */
function readingStroke(S){
  const anchors = [[40,0],[70,4],[85,0],[100,-3],[115,0]];
  if(S <= 40 || S >= 115) return S;
  for(let i=1; i<anchors.length; i++){
    const [x0,d0] = anchors[i-1], [x1,d1] = anchors[i];
    if(S <= x1) return S + d0 + (d1-d0)*(S-x0)/(x1-x0);
  }
  return S;
}

/* ---------- joined letters: fi and fl ---------- */
const LIG = { 'ﬁ':'i', 'ﬂ':'l' };
for(const ch in LIG) G[ch] = { comp:true, w:0, kind:'low', shapes:[], dots:[], sb:[0,0] };
function buildLig(ch, S){
  const fb = pickBase('f'), sec = pickBase(LIG[ch]);
  const ws0 = P.ws * (P.ital ? 0.94 : 1), trk = P.trk || 0;
  const D = fb.w*ws0 + S + fb.sb[1] + 2*trk + sec.sb[0];      // distance from the f to the next letter, as normally spaced
  const dx = D / ws0;
  const shift = shapes => shapes.map(sh => sh.p ? Object.assign({}, sh, { p: sh.p.map(q => [q[0] + dx, q[1], q[2]]) }) : sh);
  const fsh = fb.shapes[0];
  let shapes;
  if(ch === 'ﬁ'){        // the f's arm reaches over the i and takes the place of its dot
    const p = fsh.p.map((q, i) => i === 0 ? [dx, q[1], q[2]] : q);
    shapes = [Object.assign({}, fsh, { p }), ...fb.shapes.slice(1), ...shift(sec.shapes)];
  } else {               // the f's arm flows into the top of the l as one stroke
    const lp = sec.shapes[0].p.map(q => [q[0] + dx, q[1], q[2]]).reverse();
    lp[lp.length - 1] = [lp[lp.length - 1][0], lp[lp.length - 1][1], 0.8];
    shapes = [Object.assign({}, fsh, { p: [...lp, ...fsh.p.slice(1)] }), ...fb.shapes.slice(1), ...shift(sec.shapes.slice(1))];
  }
  const wFinal = fb.w*ws0 + fb.sb[1] + 2*trk + sec.sb[0] + sec.w*ws0 + S;
  return { w: wFinal / ws0, kind:'low', sb:[fb.sb[0], sec.sb[1]], shapes, dots:[] };
}

function moveNumericBody(body, scale, dx, dy, strokeScale = scale){
  const n = v => f1(+v);
  return body.replace(/d="([^"]+)"/g, (all, d) => {
    let coordinate = 0;
    return `d="${d.replace(/-?\d+(?:\.\d+)?/g, value => n((+value) * scale + (coordinate++ % 2 ? dy : dx)))}"`;
  }).replace(/stroke-width="([^"]+)"/g, (all, width) => `stroke-width="${n((+width) * strokeScale)}"`)
    .replace(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g,
      (all, x, y, r) => `<circle cx="${n((+x)*scale+dx)}" cy="${n((+y)*scale+dy)}" r="${n((+r)*strokeScale)}"`);
}

function numericVariant(spec, S){
  const base = glyph(spec.digit, S);
  const widest = Math.max(...[...DIGITS].map(d => { const g = glyph(d, S); return g.sb0 + g.w + S + g.sb1; }));
  if(spec.type === 'tf'){
    const dx = (widest - (base.w + S)) / 2;
    return { body:moveNumericBody(base.body, 1, dx, 0), clipId:base.clipId,
      sb0:0, sb1:0, w:widest - S };
  }
  const scale = 0.60, advance = Math.round(widest * scale + 22);
  const rise = { sup:380, sub:-190, numr:300, dnom:-190 }[spec.type];
  const dx = (advance - (base.w + S) * scale) / 2;
  const lighterStroke = Math.min(readingStroke(S) * 0.52, 70) / (readingStroke(S) * 0.96);
  return { body:moveNumericBody(base.body, scale, dx, -rise, lighterStroke),
    clipId:ensureClip(900, -310), sb0:0, sb1:0, w:advance - S };
}

function composedFraction(parts, S){
  const numerator = numericVariant({digit:parts[0], type:'numr'}, S);
  const denominator = numericVariant({digit:parts[1], type:'dnom'}, S);
  const slash = glyph('⁄', S);
  const nAdvance = numerator.w + S, slashAdvance = slash.sb0 + slash.w + S + slash.sb1;
  return { body:numerator.body + moveNumericBody(slash.body, 1, nAdvance, 0, 1)
      + moveNumericBody(denominator.body, 1, nAdvance + slashAdvance, 0, 1),
    clipId:ensureClip(900, -310), sb0:0, sb1:0,
    w:nAdvance + slashAdvance + denominator.w };
}

/** Measure SVG ink, including cubic extrema and the same oval pen as the font. */
function inkBounds(g){
  if(g.ink) return g.ink;
  const box=[Infinity,Infinity,-Infinity,-Infinity];
  /** Expand the ink box by a point and its horizontal and vertical pen radii. */
  const add=(x,y,rx=0,ry=0) => { box[0]=Math.min(box[0],x-rx); box[1]=Math.min(box[1],y-ry); box[2]=Math.max(box[2],x+rx); box[3]=Math.max(box[3],y+ry); };
  /** Evaluate one coordinate of a cubic Bezier at parameter t. */
  const at=(p,t) => (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3];
  /** Return derivative roots; the caller limits them to the curve segment. */
  const extrema=p => {
    const a=-p[0]+3*p[1]-3*p[2]+p[3], b=2*(p[0]-2*p[1]+p[2]), c=p[1]-p[0];
    if(Math.abs(a)<1e-9) return Math.abs(b)<1e-9 ? [] : [-c/b];
    const d=b*b-4*a*c; return d<0 ? [] : [(-b+Math.sqrt(d))/(2*a),(-b-Math.sqrt(d))/(2*a)];
  };
  for(const el of g.body.matchAll(/<path\b[^>]*>/g)){
    const d=el[0].match(/\bd="([^"]+)"/)[1], sw=+(el[0].match(/stroke-width="([^"]+)"/)?.[1] || 0);
    const tok=d.match(/[MLCZ]|-?\d+(?:\.\d+)?/g) || []; let i=0,pt=[0,0];
    while(i<tok.length){
      const op=tok[i++]; if(op==='Z') continue;
      /** Read the next SVG point and restore the font's upward y axis. */
      const end=() => [+tok[i++],-tok[i++]];
      if(op==='M'||op==='L'){pt=end();const h=penHalf(sw);add(...pt,h.hx,h.hy);}
      else if(op==='C'){
        const p1=end(),p2=end(),p3=end(),xs=[pt[0],p1[0],p2[0],p3[0]],ys=[pt[1],p1[1],p2[1],p3[1]];
        const h=penHalf(sw);
        for(const t of [0,1,...extrema(xs),...extrema(ys)].filter(t=>t>=0&&t<=1)) add(at(xs,t),at(ys,t),h.hx,h.hy);
        pt=p3;
      }
    }
  }
  for(const m of g.body.matchAll(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g)) add(+m[1],-m[2],+m[3],+m[3]);
  return (g.ink=Number.isFinite(box[0]) ? box : [0,0,0,0]);
}

/** Build a zero-advance mark from shared accent shapes, with lighter strokes. */
function combiningGlyph(ch,S){
  const spec=COMBINING[ch], mk=MARK[spec.mark](0,0), scale=.72, sw=Math.min(readingStroke(S)*.72,58);
  let body='';
  /** Scale a mark point into SVG coordinates without altering its advance. */
  const point=(x,y) => `${f1(x*scale)} ${f1(-y*scale)}`;
  for(const shape of mk.shapes || []){
    const d=shape.raw ? shape.raw.map(seg => seg[0]+' '+seg.slice(1).map((v,i)=>f1(v*scale*(i%2 ? -1 : 1))).join(' ')).join(' ')
      : shape.p.map((p,i)=>(i?'L':'M')+point(p[0],p[1])).join(' ');
    body+=strokePath(d,sw);
  }
  for(const dot of mk.dots || []) body+=`<circle cx="${f1(dot[0]*scale)}" cy="${f1(-dot[1]*scale)}" r="${f1(sw*.46)}" fill="currentColor"/>`;
  const g={body,sb0:0,sb1:0,w:-S,clipId:ensureClip(300,-300)},b=inkBounds(g);
  g.mark=spec.place;
  g.attach=spec.place==='top' ? [0,b[1]] : spec.place==='bottom' ? [0,b[3]] : [0,0];
  g.anchors={top:[0,b[3]+20],bottom:[0,b[1]-20],horn:[0,b[3]+20],ogonek:[0,b[1]-20]};
  return g;
}

/** Optical attachment points in the source coordinates, before italic shear. */
function latinAnchors(ch,S){
  const g=glyph(ch,S); if(g.anchors) return g.anchors;
  const b=inkBounds(g),cx=penHalf(S).hx+g.w/2;
  const topGap=ACC[ch] && ACC[ch].mark!=='cedilla' ? 20 : 60;
  return {top:[cx,b[3]+topGap],bottom:[cx,b[1]-38],horn:[b[2]-S*.18,b[3]-S*.7],ogonek:[b[2]-S*.3,b[1]+S*.1]};
}

/** Keep existing precomposed letters; attach only the remaining combining marks. */
function latinClusters(text){
  const clusters=[];
  /** Return the canonical combining class for the supported mark repertoire. */
  const ccc=ch=>COMBINING[ch].place==='horn' ? 216 : ['\u0327','\u0328'].includes(ch) ? 202 : COMBINING[ch].place==='bottom' ? 220 : 230;
  for(const ch of text.normalize('NFD')){
    if(COMBINING[ch]){
      if(!clusters.length) clusters.push({base:'◌',marks:[]});
      const c=clusters.at(-1), composed=(c.base+ch).normalize('NFC');
      const blocked=c.marks.length && ccc(c.marks.at(-1))>=ccc(ch);
      if(!blocked && [...composed].length===1 && G[composed]) c.base=composed;
      else c.marks.push(ch);
    } else clusters.push({base:ch,marks:[]});
  }
  return clusters.map(c=>{
    if(['i','j'].includes(c.base) && c.marks.some(ch=>COMBINING[ch].place==='top')) c.base+='.dotless';
    if(c.base==='ị' && c.marks.some(ch=>COMBINING[ch].place==='top')) c.base='i.below.dotless';
    return c;
  });
}

/** Mirror language-specific OpenType forms in the Lab's live SVG construction. */
function languageClusters(text,locale=''){
  if(locale==='ro') text=text.replace(/[ŞşŢţ]/g,ch=>'ȘșȚț'['ŞşŢţ'.indexOf(ch)]);
  const clusters=latinClusters(text);
  if(locale==='tr') for(const c of clusters) if(c.base==='i') c.base='i.loclTRK';
  return clusters;
}

/** Overlay accents without adding width or interrupting the word's pair rhythm. */
function clusterGlyph(cluster,S){
  const g=glyph(cluster.base,S); if(!g || !cluster.marks.length) return g;
  const anchors=Object.fromEntries(Object.entries(latinAnchors(cluster.base,S)).map(([k,v])=>[k,[...v]]));
  if(LIG[cluster.base] && cluster.component!==undefined){
    const first=glyph('f',S),cut=2*P.trk+first.sb0+first.w+S+first.sb1;
    const advance=2*P.trk+g.sb0+g.w+S+g.sb1;
    const cx=(cluster.component ? cut+advance : cut)/2-P.trk-g.sb0;
    for(const a of Object.values(anchors)) a[0]=cx;
  }
  let body=g.body;
  for(const ch of cluster.marks){
    const m=glyph(ch,S),kind=COMBINING[ch].place,a=anchors[kind],dx=a[0]-m.attach[0],dy=a[1]-m.attach[1];
    body+=moveNumericBody(m.body,1,dx,-dy,1);
    if(kind==='top') anchors.top=[dx+m.anchors.top[0],dy+m.anchors.top[1]];
    else if(kind==='bottom'||kind==='ogonek') anchors.bottom=[dx+m.anchors.bottom[0],dy+m.anchors.bottom[1]];
  }
  const result={...g,body,anchors,clipId:ensureClip(1250,-500)};
  delete result.ink;
  delete result._tt; delete result._ttF;
  return result;
}

/** Compose new encoded letters without redrawing any 0.33 outline or advance. */
function languageGlyph(ch,S,removeDot=false){
  const spec=LANGUAGE_COMPOSED[ch] || ACC[ch];
  const top=spec.marks.some(mark=>COMBINING[mark].place==='top');
  const dotBase=scriptReuse(spec.base) || spec.base;
  const base=['i','j'].includes(dotBase) && (top||removeDot) ? dotBase+'.dotless' : spec.base;
  if(!['ď','ť','ľ','Ľ'].includes(ch)) return clusterGlyph({base,marks:spec.marks},S);
  // Czech/Slovak tall stems use a compact side caron, not a floating accent.
  const g=glyph(base,S),b=inkBounds(g),ws=P.ws*(P.ital ? 0.94 : 1);
  const stem=(ch==='ď'?420:ch==='ť'?150:0)*ws+penHalf(S).hx;
  const cx=stem+96,y=b[3]+12,sw=Math.min(readingStroke(S)*.66,58);
  const d=`M${f1(cx+15)} ${f1(-y-10)}C${f1(cx+37)} ${f1(-y+25)} ${f1(cx+25)} ${f1(-y+65)} ${f1(cx-8)} ${f1(-y+82)}`;
  const body=g.body+strokePath(d,sw);
  const extra=ch==='ď'?90:ch==='ľ'?55:0;
  const result={...g,body,sb1:g.sb1+extra,clipId:ensureClip(1100,-320)};
  // A copied cached base must not retain its old cached ink bounds.
  delete result.ink;
  delete result._tt; delete result._ttF;
  const actual=inkBounds(result),anchors=latinAnchors(base,S);
  return {...result,anchors:{...anchors,top:[anchors.top[0],actual[3]+20]}};
}

/** Resolve a character or alternate into its cached SVG drawing and horizontal metrics. */
function glyph(ch, S){
  const ck = `${ch}|${S}|${P.round}|${P.contrast}|${P.xh}|${P.ws}|${P.caprx}|${P.os}|${P.ufoot}|${P.ital}|${P.straight}|${P.asc}|${P.corner}|${P.cap}|${P.join}|${P.penAngle}${LIG[ch] ? '|' + P.trk : ''}${P.alternates ? '|'+JSON.stringify(displayChoices(P.alternates)) : ''}`;
  if(cache[ck] !== undefined) return cache[ck];
  if(P.alternates && DISPLAY_VARIANTS[ch]){
    const spec=DISPLAY_VARIANTS[ch], keep=P.alternates;
    try {
      P.alternates={...displayChoices(keep),[spec.key]:spec.choice};
      const g=glyph(spec.source,S);
      return (cache[ck]={...g,...(spec.letter ? {anchors:latinAnchors(spec.source,S)} : {})});
    } finally { P.alternates=keep; }
  }
  if(scriptReuse(ch)) return (cache[ck]=glyph(scriptReuse(ch),S));
  if(PHASE4_JOINED[ch]) return (cache[ck]=phase4Joined(ch,S));
  if(LANGUAGE_COMPOSED[ch] || ACC[ch]?.additive) return (cache[ck]=languageGlyph(ch,S));
  if(ch==='ı') return (cache[ck]=glyph('i.dotless',S));
  if(ch==='i.loclTRK') return (cache[ck]=glyph('i',S));
  if(ch==='i.below.dotless') return (cache[ck]=languageGlyph('ị',S,true));
  if(COMBINING[ch]) return (cache[ck] = combiningGlyph(ch,S));
  if(ch === 'ʻ' || ch === 'ʼ') return (cache[ck] = glyph(ch === 'ʻ' ? '‘' : '’',S));
  if(ch === '\u2009' || ch === '\u202f') return (cache[ck] = { body:'',clipId:ensureClip(700,0),sb0:0,sb1:0,w:120-S });
  if(NUMERIC_VARIANTS[ch]) return (cache[ck] = numericVariant(NUMERIC_VARIANTS[ch], S));
  if(FRACTION_PARTS[ch]) return (cache[ck] = composedFraction(FRACTION_PARTS[ch], S));
  let g = DOTLESS[ch] ? Object.assign({},pickBase(DOTLESS[ch]),{dots:[]}) : LIG[ch] ? buildLig(ch, S) : pickBase(ch);
  const bch = latinBase(ch);
  const isFigure = DIGITS.includes(ch), isMark = TEXT_MARKS.has(ch);
  const drawS = READING_LETTERS.has(bch) || isFigure || isMark ? readingStroke(S) : S;
  const strokeS = isFigure ? drawS*0.96
    : isMark ? Math.min(drawS*(QUIET_MARKS.has(ch) ? 0.86 : 0.92),100) : drawS;
  if(ACC[ch]){                                   // accented letter = base letter + mark
    const a = ACC[ch], b = pickBase(a.base);
    if(!b) return (cache[ck] = null);
    const cx = a.cx !== undefined ? a.cx : b.w / 2;
    /* put the mark a fixed gap above the letter's real top edge, at any weight */
    const hy0 = penHalf(drawS).hy, os0 = (P.os && OVS.has(a.base)) ? OSV : 0, markW = Math.min(drawS,80);
    const GAP = 60, lift = GAP + markW / 2;
    let y0;
    if(b.kind === 'cap'){ const target = 700 + os0 + lift; y0 = (target - hy0 + os0) * 700 / (700 - 2*hy0 + 2*os0); }
    else { const target = P.xh + os0 + lift; y0 = 500 + (target - (P.xh - hy0)) * 240 / (P.asc - P.xh); }
    const mk = MARK[a.mark](cx, y0);
    const markShapes = (mk.shapes || []).map(m => Object.assign({}, m, { swFn:true }));   // marks get lighter as weight goes up
    g = { w:b.w, kind:b.kind, sb:b.sb, shapes:[...b.shapes, ...markShapes], dots:[...(a.nodot ? [] : b.dots), ...(mk.dots || []).map(d => [d[0], d[1], 0.85])] };
  }
  if(!g) return (cache[ck] = null);
  const h = penHalf(S).hx, kind = g.kind;
  /* Normalize raised quotes with their lighter pen too, keeping even Bold
     closing quotes above the cap line after their dot is reduced. */
  const hy = penHalf(isFigure || `'"‘’“”‛‟`.includes(ch) ? strokeS : drawS).hy;
  const os = (P.os && OVS.has(bch)) ? OSV : 0;
  const ws = (WIDE.has(bch) ? 1 - (1 - P.ws) * 0.4 : P.ws) * (P.ital ? 0.94 : 1);
  const mx = x => h + x*ws;
  const my = y => kind === 'cap'
    ? hy - os + y*(700 - 2*hy + 2*os)/700
    : (y < 0 ? hy + y
      : y <= 500 ? hy - os + y*(P.xh - 2*hy + 2*os)/500
      : y <= 740 ? (P.xh-hy) + (y-500)*(P.asc-P.xh)/240
      : (P.asc-hy) + (y-740));
  let body = '', topO = -1e9, botO = 1e9;
  const seeY = yy => { topO = Math.max(topO, yy + strokeS/2); botO = Math.min(botO, yy - strokeS/2); };
  const stroke = (d, k = 1) => strokePath(d,strokeS*k);
  for(let s of g.shapes){
    if(s.swFn) s = Object.assign({}, s, { sw: Math.min(1, 80 / drawS) });
    if(s.fn) s = Object.assign({ raw: s.fn() }, s.sw ? { sw: s.sw } : {});
    if(s.fill){
      const parts = Array.isArray(s.fill[0][0]) ? s.fill : [s.fill];      // several outlines = shape with holes
      const d = parts.map(pp => pp.map((q, i) => { const yy = my(q[1]); seeY(yy); return `${i ? 'L' : 'M'}${f1(mx(q[0]))} ${f1(-yy)}`; }).join('') + 'Z').join('');
      const sw = s.nostroke ? 0 : strokeS;
      body += `<path data-fill="1" d="${d}" fill="currentColor" fill-rule="evenodd" stroke="currentColor" stroke-width="${f1(sw)}" stroke-linejoin="round"/>`;
      continue;
    }
    if(s.raw){
      let d = '';
      for(const seg of s.raw){
        const pt = (x,y) => `${f1(mx(x))} ${f1(-my(y))}`;
        if(seg[0] === 'M'){ d += `M${pt(seg[1],seg[2])}`; seeY(my(seg[2])); }
        else if(seg[0] === 'Z'){ d += 'Z'; }
        else { d += `C${pt(seg[1],seg[2])} ${pt(seg[3],seg[4])} ${pt(seg[5],seg[6])}`; seeY(my(seg[6])); }
      }
      body += stroke(d, s.sw || 1);
    } else {
      const pts = s.p.map(q => { const yy = my(q[1]); seeY(yy); return [mx(q[0]), yy, q[2]]; });
      body += stroke(pathFrom(pts, s.z, kind), s.sw || 1);
    }
  }
  for(const dp of g.dots){
    const yy = my(dp[1]);
    const dot = isMark ? Math.min(drawS*(QUIET_MARKS.has(ch) ? 0.46 : 0.49), QUIET_MARKS.has(ch) ? 52 : 62)
      : drawS*0.58;
    const rr = dot*(dp[2] || 1);
    botO = Math.min(botO, yy - rr - 2); topO = Math.max(topO, yy + rr + 2);
    body += `<circle cx="${f1(mx(dp[0]))}" cy="${f1(-yy)}" r="${f1(rr)}" fill="currentColor"/>`;
  }
  const hasDot = g.dots.length > 0;
  const top = hasDot ? 1000 : Math.round(topO);
  const bot = Math.round(Math.min(0, botO)) - (hasDot ? 30 : 0);
  if(ch === '⁄'){
    const advance = 190;
    return (cache[ck] = { body:moveNumericBody(body, 1, (advance - (g.w*ws + S)) / 2, 0, 1),
      clipId:ensureClip(top, bot), sb0:0, sb1:0, w:advance-S });
  }
  return (cache[ck] = { body, clipId: ensureClip(top, bot), sb0:g.sb[0], sb1:g.sb[1], w:g.w*ws });
}

/** Render accent clusters and approved pair spacing as one scaled SVG word. */
function word(w, size, ui){
  const S = weightFor(size);
  const extra = P.track + 0.3*(S - P.base);
  let x = 0, parts = '', prev = '';
  const clusters=latinClusters(w);
  for(const cluster of clusters){
    const ch=cluster.base, g = clusterGlyph(cluster, S);
    if(!g){ x += 380; prev = ''; continue; }
    if(ch==='\u2009'||ch==='\u202f'){ x+=120; prev=''; continue; }
    x += (KERN[(DOTLESS[prev] || prev) + (DOTLESS[ch] || ch)] || 0);
    const shear=P.obliqueAngle ? ` skewX(${-P.obliqueAngle})` : '';
    const center=P.obliqueAngle ? Math.tan(P.obliqueAngle*Math.PI/180)*330 : 0;
    parts += `<g transform="translate(${f1(x + extra + g.sb0-center)} 0)${shear}" clip-path="url(#${g.clipId})">${g.body}</g>`;
    x += extra + g.sb0 + g.w + S + g.sb1 + extra;
    prev = ch;
  }
  const W = Math.max(x, 1);
  const marked=clusters.some(c=>c.marks.length);
  const vb = marked ? `0 -1120 ${f1(W)} 1440` : ui ? `0 -700 ${f1(W)} 700` : `0 -840 ${f1(W)} 1100`;
  const hgt = (marked ? 1.44 : ui ? 0.7 : 1.1) * size;
  const overflow=clusters.some(c=>VIETNAMESE_ADDED.has(c.base)) ? ' overflow="visible"' : '';
  return `<svg${overflow} aria-hidden="true" focusable="false" viewBox="${vb}" width="${f1(W*size/1000)}" height="${f1(hgt)}">${parts}</svg>`;
}

const esc = s => s.replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));

/** Wrap SVG words in an accessible text run with the requested row and column gaps. */
function T(str, size, opt = {}){
  const words = str.split(/\s+/).filter(Boolean);
  const colGap = size*0.25, rowGap = opt.ui ? 0 : size*(opt.rowGap ?? 0.28);
  return `<span class="run${opt.nw ? ' nw' : ''}" role="img" aria-label="${esc(str)}" style="gap:${f1(rowGap)}px ${f1(colGap)}px">${
    words.map(w => word(w, size, !!opt.ui)).join('')
  }</span>`;
}
