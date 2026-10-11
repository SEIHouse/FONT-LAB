"""Builds the SEIHouse Display Lab: one page to shape display cuts live and save them."""
import json, os, glob, hashlib
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from display.title_spacing import spacing_settings
from display.living_build import engine_factory, profiles_for_lab
engine = open(os.path.join(HERE, '..', 'engine.js'), encoding='utf-8').read()
stroke_geometry = open(os.path.join(HERE, 'stroke_geometry.js'), encoding='utf-8').read()
spacing_helper = open(os.path.join(HERE, 'spacing.js'), encoding='utf-8').read()
draft_helper = open(os.path.join(HERE, '..', 'site', 'drafts.js'), encoding='utf-8').read()
presets = [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(os.path.join(HERE, 'cuts', '*.json')))]
order = ['Soft', 'Edge', 'Ink', 'Wide']
presets.sort(key=lambda c: order.index(c['name']) if c['name'] in order else 99)
spacing_dir = os.environ.get('SPACING_DIR', HERE)
def load_spacing(cut):
    """Load a cut's compiled snapshot and reject mismatched settings or OTF bytes."""
    slug = cut['name'].lower().replace(' ', '-')
    filename = 'SEIHouseDisplay-'+cut['name'].replace(' ', '')+'.otf'
    file = os.path.join(spacing_dir, 'spacing_'+slug+'.json')
    font = os.path.join(HERE, 'fonts', slug, filename)
    if spacing_dir != HERE:
        file = os.path.join(spacing_dir, slug, 'spacing_'+slug+'.json')
        font = os.path.join(spacing_dir, slug, filename)
    with open(file, encoding='utf-8') as source:
        record = json.load(source)
    with open(font, 'rb') as source:
        digest = hashlib.sha256(source.read()).hexdigest()
    if (record.get('schema') != 1 or record['settings'] != spacing_settings(cut) or record['otf_sha256'] != digest
            or record.get('built_alternates') != cut.get('alternates', {})):
        raise ValueError('Stale spacing export for '+cut['name']+'; rebuild the cut before its Lab')
    return record

spacing_exports = [load_spacing(cut) for cut in presets]

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>SEIHouse Display Lab</title>
<style>
:root{ box-sizing:border-box; padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px);
  --bg:#0d0f13; --panel:#151922; --line:#262c38; --ink:#eef1f6; --mute:#8d95a6; --accent:#8fa2ff; }
html{ scroll-padding-top:env(safe-area-inset-top,0px); }
*{ box-sizing:border-box; }
body{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }
.wrap{ display:grid; grid-template-columns:330px minmax(0,1fr); gap:18px; padding:18px; max-width:1500px; margin:0 auto; }
@media (max-width:900px){ .wrap{ grid-template-columns:minmax(0,1fr); padding:12px; } }
h1{ font-size:20px; margin:0 0 2px; } .sub{ color:var(--mute); font-size:13px; margin:0 0 14px; }
aside{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; min-width:0; align-self:start; position:sticky; top:12px; max-height:calc(100vh - 24px); overflow:auto; }
@media (max-width:900px){ aside{ position:static; max-height:none; overflow:visible; } }
.sec{ border-bottom:1px solid var(--line); padding:10px 0; display:grid; gap:9px; }
.sec:last-child{ border-bottom:0; }
.sec h2{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--mute); margin:0; }
.row{ display:flex; flex-wrap:wrap; gap:6px; }
.pill{ font:inherit; font-size:13px; padding:6px 11px; max-width:100%; overflow-wrap:anywhere; border-radius:999px; border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer; }
.pill[aria-pressed="true"]{ background:var(--ink); color:#0d0f13; border-color:var(--ink); }
.pill:disabled{opacity:.45;cursor:not-allowed}
.pill.primary{ background:var(--accent); color:#0d0f13; border-color:var(--accent); font-weight:600; }
.pill:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
label.ctl{ display:grid; gap:3px; min-width:0; font-size:13px; color:var(--mute); }
label.ctl span{ display:flex; justify-content:space-between; } label.ctl output{ color:var(--ink); }
input[type=range]{ width:100%; min-width:0; margin:0; accent-color:var(--accent); }
input[type=text], textarea, select{ width:100%; min-width:0; font:inherit; background:#0d0f13; color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:7px 9px; }
textarea{ min-height:84px; resize:vertical; }
.hint{ font-size:12px; color:var(--mute); }
main{ display:grid; gap:16px; min-width:0; }
.card{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; min-width:0; }
.card h2{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--mute); margin:0 0 10px; }
.covers{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:16px; }
@media (max-width:1100px){ .covers{ grid-template-columns:1fr; } }
.cover{ aspect-ratio:1/1; min-width:0; border-radius:12px; padding:7%; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; position:relative; }
.cover > div{ min-width:0; max-width:100%; }
.cover .mark{ align-self:flex-end; opacity:.9; }
.run{ display:flex; flex-wrap:wrap; align-items:flex-start; min-width:0; max-width:100%; } .run svg{ display:block; overflow:visible; flex:none; max-width:100%; height:auto; }
.tracks{ display:grid; gap:6px; }
.tracks .tr{ display:grid; grid-template-columns:2.2em minmax(0,1fr); align-items:start; color:var(--ink); }
.tracks .num{ color:var(--mute); font-size:14px; padding-top:6px; }
.all{ display:grid; gap:12px; } .all .hint{ margin-bottom:2px; }
.out{ font:12px/1.4 ui-monospace,Menlo,monospace; white-space:pre-wrap; overflow-wrap:anywhere; background:#0d0f13; border:1px solid var(--line); border-radius:8px; padding:8px; max-height:160px; overflow:auto; }
[hidden]{display:none!important}
.living-controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;min-width:0}
.living-controls>div,.living-axes{grid-column:1/-1;min-width:0}
.living-controls input[type=number],.living-controls input[type=file]{width:100%;min-width:0;max-width:100%;font:inherit;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px}
.living-controls input[type=color]{width:100%;height:36px;border:1px solid var(--line);background:transparent}
.living-axes{display:flex;flex-wrap:wrap;gap:12px;border:1px solid var(--line);border-radius:8px}
.living-stage{margin:16px 0;min-width:0;overflow:hidden;border:1px solid var(--line);border-radius:10px;background:repeating-conic-gradient(#252a34 0% 25%,#1b2029 0% 50%) 0/20px 20px}
.living-stage svg{display:block;width:100%;height:auto;max-height:420px}
.living-approval{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;display:grid;gap:8px}
.living-actions{margin:12px 0;align-items:center} #lt-progress{width:100%} #living-title a{color:var(--accent)}
.kind{display:inline-block;margin-left:8px;padding:2px 8px;border-radius:999px;font-size:11px;letter-spacing:.04em;text-transform:none;vertical-align:1px;border:1px solid}
.kind-static{color:#8fe3b0;border-color:#2f6b4a} .kind-live{color:#f2c46d;border-color:#6b5427} .kind-motion{color:#c9a8ff;border-color:#4f3a7a}
.kinds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0;padding:0;list-style:none}
@media (max-width:1100px){ .kinds{grid-template-columns:1fr; } }
.kinds li{border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:grid;gap:4px;align-content:start}
.kinds li .kind{margin-left:0;justify-self:start}
.static-sample{overflow-wrap:anywhere;min-width:0}
.lab-actions{margin:4px 0 10px} #job-status:empty{display:none} .downloads a{color:var(--accent)}
.static-sample .chap{font-size:30px;line-height:1.15;margin:4px 0 12px}
.static-sample .big{font-size:clamp(40px,7vw,84px);line-height:1.08}
.top{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding-bottom:6px}
.top h1{order:-1;margin:0} .back{color:var(--mute);font-size:13px;text-decoration:none} .back:hover{color:var(--ink)}
.ctls{display:grid;gap:9px}
details.sec>summary,details.fold>summary,details.legend>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
details>summary::-webkit-details-marker{display:none}
details.sec>summary{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);font-weight:600;min-height:28px}
details.sec>summary small{text-transform:none;letter-spacing:0;font-weight:400;opacity:.8}
details.sec>summary::after,details.fold>summary::after{content:"";margin-left:auto;width:7px;height:7px;border-right:2px solid var(--mute);border-bottom:2px solid var(--mute);transform:rotate(45deg);transition:transform .15s}
details[open].sec>summary::after,details[open].fold>summary::after{transform:rotate(-135deg)}
details.sec{display:block} details.sec>:not(summary){margin-top:9px}
details.fold>summary h2{margin:0} details.fold[open]>summary{margin-bottom:10px}
details>summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
.toolbar{display:flex;flex-wrap:wrap;align-items:end;gap:12px 16px}
.toolbar .title-field{flex:1 1 220px}
.toolbar .legend{flex:1 1 100%}
.toolbar .legend>summary .kind{margin-left:0}
.toolbar .legend[open]>summary{margin-bottom:10px}
.quick{display:none}
@media (max-width:900px){
  .quick{display:block;position:sticky;top:0;z-index:3;margin:0 -14px;padding:8px 14px;background:var(--panel);border-bottom:1px solid var(--line);overflow:hidden}
  .quick:not(.wrap) .run{flex-wrap:nowrap}
}
@media (prefers-reduced-motion:reduce){ details>summary::after{transition:none} }
</style>
<link rel="stylesheet" href="__DISPLAY_FONTS_CSS__"></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs id="clips"></defs></svg>
<div class="wrap">
<aside aria-label="Cut settings">
  <div class="top"><a class="back" href="../../index.html">← Font Lab</a><h1>Display Lab</h1></div>
  <div class="quick" id="quick" aria-hidden="true"></div>
  <div class="sec"><h2>Cut</h2>
    <div class="row" id="presets" role="group" aria-label="Starting cuts"></div>
    <div class="row" id="saved" role="group" aria-label="Saved cuts"></div>
    <div class="row"><button type="button" class="pill primary" id="save" disabled>Save cut</button><button type="button" class="pill" id="reset">Reset sliders</button></div>
    <div class="hint" id="savemsg" aria-live="polite">Loading drafts…</div>
    <p class="hint" id="draftwarning" hidden></p>
  </div>
  <details class="sec" open><summary>Shape</summary>
    <div class="row" role="group" aria-label="Corners"><button type="button" class="pill" data-k="corners" data-v="soft">Soft corners</button><button type="button" class="pill" data-k="corners" data-v="cut">Cut corners</button></div>
    <div class="row" role="group" aria-label="Ends"><button type="button" class="pill" data-k="ends" data-v="round">Round ends</button><button type="button" class="pill" data-k="ends" data-v="flat">Flat ends</button></div>
    <div class="row" role="group" aria-label="Joins"><button type="button" class="pill" data-k="joins" data-v="round">Round joins</button><button type="button" class="pill" data-k="joins" data-v="sharp">Sharp joins</button></div>
    <label><input type="checkbox" id="overshoot"> Overshoot (round letters dip slightly past the lines)</label>
    <div class="row" role="group" aria-label="Letter u"><button type="button" class="pill" data-k="uFoot" data-v="false">Plain u</button><button type="button" class="pill" data-k="uFoot" data-v="true">u with foot</button></div>
    <div id="ctl-shape" class="ctls"></div>
  </details>
  <details class="sec" open><summary>Pen</summary><div id="ctl-pen" class="ctls"></div>
    <div class="row" role="group" aria-label="Pen shape"><button type="button" class="pill" data-k="pen" data-v="oval">Oval pen</button><button type="button" class="pill" data-k="pen" data-v="nib">Flat nib</button></div>
    <p class="hint" id="pen-hint"></p>
    <div class="row" role="group" aria-label="Slanted letters"><button type="button" class="pill" data-k="italicForms" data-v="false">Tilted upright</button><button type="button" class="pill" data-k="italicForms" data-v="true">True italic</button></div>
    <p class="hint">True italic redraws d f h i m n u with pen exit strokes. Pair it with some slant.</p>
  </details>
  <details class="sec" open><summary>Spacing</summary><div id="ctl-space" class="ctls"></div>
    <label><input type="checkbox" id="cpsp"> Capital spacing (cpsp)</label>
    <p class="hint" id="spacing-status" aria-live="polite"></p>
  </details>
  <details class="sec"><summary>Letter designs <small>optional</small></summary><div id="ctl-alternates" class="ctls"></div>
    <p class="hint">Swap single forms like a/g, R, K or W. Every preset uses plain W/w; crossed W is the optional ss04 design.</p></details>
  <details class="sec"><summary>Artist &amp; tracks</summary>
    <label class="ctl"><span>Artist</span><input type="text" id="t-artist" value="SENSEI" maxlength="40"></label>
    <label class="ctl"><span>Tracks (one per line)</span><textarea id="t-tracks">Pavilion
Roots Through Ruin
Skybound
Oath (Interlude)
Bloom</textarea></label>
  </details>
  <details class="sec"><summary>Name &amp; export</summary>
    <label class="ctl"><span>Name of this cut</span><input type="text" id="cutname" maxlength="40" autocomplete="off"></label>
    <div class="row"><button type="button" class="pill" id="download">Download JSON</button><button type="button" class="pill" id="copy">Copy JSON</button></div>
    <p class="hint">Saved drafts stay in this browser. Download or copy the JSON to build a font or move your cut.</p>
    <div class="out" id="out" tabindex="0"></div>
  </details>
</aside>
<main>
  <div class="card toolbar">
    <label class="ctl title-field"><span>Title</span><input type="text" id="t-title" value="The Last Lotus" maxlength="60"></label>
    <div class="row" role="group" aria-label="Cover colors" id="palettes"></div>
    <details class="legend"><summary><span class="kind kind-static">Static font</span><span class="kind kind-live">Live drawing</span><span class="kind kind-motion">Animated</span> <span class="hint">What do these mean?</span></summary>
      <ul class="kinds">
        <li><span class="kind kind-static">Static font</span><strong>The built font file</strong><span class="hint">Fixed WOFF2/OTF. This is what the Reader loads for chapter titles. It changes only when the cut is rebuilt.</span></li>
        <li><span class="kind kind-live">Live drawing</span><strong>Your sliders, drawn now</strong><span class="hint">The engine draws your current settings. It becomes a font only after you download the JSON and build the cut.</span></li>
        <li><span class="kind kind-motion">Animated</span><strong>Living Title</strong><span class="hint">A separate player that redraws the title every frame. It is not a font file. The Reader does not run it yet.</span></li>
      </ul>
    </details>
  </div>
  <section class="card"><h2>Album cover <span class="kind kind-live">Live drawing</span></h2><div class="covers"><div class="cover" id="cover1"></div><div class="cover" id="cover2"></div></div></section>
  <section class="card" id="static-font" aria-labelledby="static-heading"><h2 id="static-heading">Built font file <span class="kind kind-static">Static font</span></h2>
    <p class="hint" id="static-status" aria-live="polite"></p>
    <div class="row lab-actions" id="lab-actions" hidden>
      <button type="button" class="pill primary" id="build-font">Build font from these sliders</button>
      <button type="button" class="pill" id="promote-cut" hidden></button>
    </div>
    <p class="hint" id="job-status" role="status" aria-live="polite"></p>
    <div class="static-sample" id="static-sample"></div>
  </section>
  <section class="card"><h2>Track list <span class="kind kind-live">Live drawing</span></h2><div class="tracks" id="tracks"></div></section>
  <section class="card"><h2>Poster line <span class="kind kind-live">Live drawing</span></h2><div id="poster"></div></section>
  <section class="card"><h2>All cuts side by side <span class="kind kind-live">Live drawing</span></h2><div class="all" id="all"></div></section>
  <details class="card fold" id="spec-card"><summary><h2>Every letter <span class="kind kind-live">Live drawing</span></h2></summary><div id="spec" style="display:grid;gap:8px"></div></details>
__LIVING_PANEL__
</main>
</div>
<script>
__ENGINE__
</script>
<script>
const PRESETS = __PRESETS__;
const SPACING_EXPORTS = __SPACING__;
const $ = id => document.getElementById(id);
const e_ = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const SLIDERS = {
  'ctl-shape': [
    ['weight', 'Thickness', 30, 220, 1], ['letterWidth', 'Width', 0.7, 1.7, 0.01], ['xHeight', 'Lowercase height', 400, 620, 1],
    ['capitalRoundness', 'Capital corners', 0, 320, 1], ['lowercaseRoundness', 'Lowercase roundness', 0, 1, 0.01],
    ['uprightStraightness', 'Straightness (lower = squarer)', 0.4, 1, 0.01], ['ascender', 'Ascender height (b d h k l)', 620, 800, 1]],
  'ctl-pen': [['contrast', 'Thick and thin', 1, 6, 0.01], ['penAngle', 'Pen angle', -60, 60, 1], ['slant', 'Slant', -6, 16, 0.5]],
  'ctl-space': [['spaceBetweenAllLetters', 'Space between letters', -30, 120, 1], ['wordSpace', 'Space between words', 120, 480, 1]],
};
const PALETTES = { Night:['#0f1115','#2b3140','#eef1f6'], Dawn:['#f6d7ad','#e7836a','#2a1714'], Jade:['#0b3a33','#2f8a6c','#eafff6'],
                   Ember:['#2a0d0b','#c2462b','#fff1e6'], Paper:['#f4efe6','#e6dccb','#1b1d22'], Violet:['#17112b','#6b54d6','#f2eeff'] };
let CUT = JSON.parse(JSON.stringify(PRESETS[0])), ORIGIN = JSON.stringify(PRESETS[0]), SAVED = Object.create(null), PAL = 'Night', PAL2 = 'Paper', db = null;

/** Apply the cut's geometry and validated letter choices to the shared drawing state. */
function applyToEngine(){
  CUT.alternates = displayChoices(CUT.alternates === undefined ? {} : CUT.alternates); P.alternates = CUT.alternates;
  P.base = CUT.weight; P.ws = CUT.letterWidth; P.xh = CUT.xHeight; P.contrast = displayContrast(CUT.weight, CUT.contrast, CUT.xHeight, CUT.ends); P.penAngle = CUT.penAngle || 0;
  P.caprx = CUT.capitalRoundness; P.round = CUT.lowercaseRoundness; P.straight = CUT.uprightStraightness || 1;
  P.corner = CUT.corners === 'cut' ? 'cut' : 'soft'; P.cap = CUT.ends; P.join = CUT.joins;
  P.os = CUT.overshoot === false ? 0 : 1; P.ufoot = CUT.uFoot ? 1 : 0; P.asc = CUT.ascender || 700; P.pen = CUT.pen === 'nib' ? 'nib' : 'oval';
  P.ital = CUT.italicForms ? 1 : 0; P.obliqueAngle = CUT.slant || 0; P.trk = CUT.spaceBetweenAllLetters;
  for(const k in cache) delete cache[k];
}
/* angled oval pen, drawn the same way the font builder does it */
const penBodies = new WeakMap();
function penBody(g){
  const key = [P.contrast,CUT.penAngle,CUT.slant,CUT.ends,CUT.joins,CUT.pen].join('|');
  const cached = penBodies.get(g);
  if(cached && cached.key === key) return cached.body;
  const body = displayPenBody(g, {...CUT, contrast:P.contrast});
  penBodies.set(g, {key,body});
  return body;
}
function drawWord(w, size){
  const sl = CUT.slant || 0, T = Math.tan(sl * Math.PI/180);
  const layout = titleLayout(w, CUT, spacingForCut(CUT, SPACING_EXPORTS), $('cpsp').checked);
  let parts = '';
  for(const {cluster,g,x} of layout.glyphs){
    const gx = x - (sl ? T * 330 : 0);
    parts += `<g transform="translate(${gx} 0)${sl ? ` skewX(${-sl})` : ''}"${CUT.ends === 'flat' || CUT.pen === 'nib' ? '' : ` clip-path="url(#${g.clipId})"`}>${penBody(g)}</g>`;
  }
  const W = Math.max(layout.width, 1);
  return `<svg viewBox="0 -1100 ${W} 1400" width="${W*size/1000}" height="${1.4*size}" aria-hidden="true">${parts}</svg>`;
}
function drawText(str, size, color, lh = 1.12){
  const tokens = String(str).match(/\S+|\s+/g) || [];
  const row = Math.max(0, size * (lh - 1.4));
  return `<div class="run" role="img" aria-label="${e_(str)}" style="color:${color || 'inherit'};row-gap:${row}px">${tokens.map(w => drawWord(w, size)).join('')}</div>`;
}
/* ---- controls ---- */
/** Populate accessible controls from the cut, retaining individual saved design choices. */
function buildControls(){
  if(CUT.ascender === undefined) CUT.ascender = 700;  // older drafts predate the ascender slider; 700 is what they drew with
  CUT.alternates = displayChoices(CUT.alternates === undefined ? {} : CUT.alternates);
  $('ctl-alternates').innerHTML = DISPLAY_SETS.map(set=>
    `<label class="ctl">${set.label} · ${set.tag}<select id="alt-${set.key}" aria-label="${set.label} design">${set.choices.map(choice=>
      `<option value="${choice}"${CUT.alternates[set.key]===choice ? ' selected' : ''}>${set.key==='W' ? (choice==='plain' ? 'Plain W (preset default)' : 'Crossed W (ss04)') : choice.replaceAll('-',' ')}</option>`).join('')}</select></label>`).join('');
  DISPLAY_SETS.forEach(set=>$('alt-'+set.key).addEventListener('change',event=>{
    CUT.alternates[set.key]=event.target.value; changed();
  }));
  for(const [box, list] of Object.entries(SLIDERS)){
    $(box).innerHTML = list.map(([k, label, mn, mx, st]) =>
      `<label class="ctl"><span>${label} <output id="o-${k}">${CUT[k]}</output></span><input type="range" id="r-${k}" min="${mn}" max="${mx}" step="${st}" value="${CUT[k]}" aria-label="${label}"></label>`).join('');
    list.forEach(([k]) => $('r-' + k).addEventListener('input', ev => { CUT[k] = +ev.target.value; $('o-' + k).textContent = CUT[k]; changed(); }));
  }
  // Older cuts omit these choices; show the values they were built with.
  const unset = {pen:'oval'};
  document.querySelectorAll('[data-k]').forEach(b => b.setAttribute('aria-pressed', String(String(CUT[b.dataset.k] ?? unset[b.dataset.k] ?? false) === b.dataset.v)));
  // The italic u always carries its own exit stroke, so the u choice applies only to upright forms.
  document.querySelectorAll('[data-k="uFoot"]').forEach(b => { b.disabled = !!CUT.italicForms; b.title = CUT.italicForms ? 'True italic draws its own u' : ''; });
  // A flat nib makes its own joins; its ends set the nib corners.
  const nib = CUT.pen === 'nib';
  document.querySelectorAll('[data-k="joins"]').forEach(b => { b.disabled = nib; b.title = nib ? 'The flat nib makes its own joins' : ''; });
  document.querySelector('[data-k="ends"][data-v="round"]').textContent = nib ? 'Soft nib corners' : 'Round ends';
  document.querySelector('[data-k="ends"][data-v="flat"]').textContent = nib ? 'Sharp chisel corners' : 'Flat ends';
  $('pen-hint').textContent = nib ? 'A flat nib makes thin strokes along its edge and full strokes across it, with ends cut at the pen angle. Try more thick-and-thin than with the oval.' : '';
  $('overshoot').checked = CUT.overshoot !== false;
  $('cutname').value = CUT.name;
}
document.querySelectorAll('[data-k]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.v; CUT[b.dataset.k] = v === 'true' ? true : v === 'false' ? false : v; buildControls(); changed(); }));
function renderPresets(){
  $('presets').innerHTML = PRESETS.map(p => `<button type="button" class="pill" data-p="${e_(p.name)}" aria-pressed="${p.name === CUT.name}">${e_(p.name)}</button>`).join('');
  $('presets').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { ORIGIN = JSON.stringify(PRESETS.find(p => p.name === b.dataset.p)); CUT = JSON.parse(ORIGIN); load(); }));
  const names = Object.keys(SAVED).sort();
  $('saved').innerHTML = names.length ? names.map(n => `<button type="button" class="pill" data-s="${e_(n)}" aria-pressed="${n === CUT.name}">${e_(n)}</button>`).join('') : '';
  $('saved').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { ORIGIN = JSON.stringify(SAVED[b.dataset.s]); CUT = JSON.parse(ORIGIN); load(); }));
}
function renderPalettes(){
  $('palettes').innerHTML = Object.keys(PALETTES).map(n => `<button type="button" class="pill" data-pal="${n}" aria-pressed="${n === PAL}">${n}</button>`).join('');
  $('palettes').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { PAL2 = PAL; PAL = b.dataset.pal; renderPalettes(); renderAll(); }));
}
$('cutname').addEventListener('input', ev => { CUT.name = ev.target.value.trim() || 'Untitled'; renderOut(); });
['t-title','t-artist','t-tracks'].forEach(id => $(id).addEventListener('input', () => renderAll()));
$('cpsp').addEventListener('change', () => renderAll());
$('overshoot').addEventListener('change', ev => { CUT.overshoot = ev.target.checked; changed(); });
/* ---- previews ---- */
function cover(el, pal){
  const [a, b, ink] = PALETTES[pal]; el.style.background = `linear-gradient(155deg, ${a}, ${b})`;
  const w = el.clientWidth || 420, title = $('t-title').value || ' ', artist = $('t-artist').value || ' ';
  el.innerHTML = `<div class="mark">${drawText('Ⓢ', w*0.07, ink)}</div><div style="display:grid;gap:${f1(w*0.02)}px">${drawText(title, w*0.13, ink, 1.02)}${drawText(artist.toUpperCase(), w*0.045, ink)}</div>`;
}
function renderAll(){
  if(typeof LivingTitleUI !== 'undefined') LivingTitleUI.update(CUT,$('t-title').value,$('cpsp').checked);
  applyToEngine();
  const exactSpacing = spacingForCut(CUT, SPACING_EXPORTS);
  $('cpsp').disabled = !exactSpacing;
  $('spacing-status').textContent = exactSpacing ? 'Final spacing from this built cut.'
    : 'Draft preview. Build this cut and rebuild the Lab for final title spacing.';
  renderQuick();
  cover($('cover1'), PAL); cover($('cover2'), PAL === 'Paper' ? 'Night' : 'Paper');
  const tracks = $('t-tracks').value.split('\n').map(s => s.trim()).filter(Boolean);
  const tw = $('tracks').clientWidth || 600;
  $('tracks').innerHTML = tracks.map((t, i) => `<div class="tr"><span class="num">${String(i + 1).padStart(2, '0')}</span>${drawText(t, Math.min(30, tw / 12))}</div>`).join('');
  const pw = $('poster').clientWidth || 600;
  $('poster').innerHTML = drawText(($('t-title').value || '').toUpperCase(), Math.min(64, pw / 5.5)) + drawText(($('t-artist').value || '') + ' · Live at the Celestial Library', Math.min(26, pw / 14));
  renderStatic(); renderAllCuts(); renderSpec(); renderOut();
}
/** Phones keep a one-line title pinned above the sliders; long titles shrink to fit, then wrap. */
function renderQuick(){
  const q = $('quick');
  if(!matchMedia('(max-width:900px)').matches){ q.textContent = ''; return; }
  const t = $('t-title').value || ' ';
  q.classList.remove('wrap'); q.innerHTML = drawText(t, 34);
  const run = q.firstElementChild, fit = 34 * run.clientWidth / Math.max(run.scrollWidth, 1);
  if(fit >= 34) return;
  q.classList.toggle('wrap', fit < 18);
  q.innerHTML = drawText(t, Math.max(18, Math.floor(fit * 0.98)));
}
/** The full character chart is long, so it is drawn only while its section is open. */
function renderSpec(){
  if(!$('spec-card').open) return;
  const sw = $('spec').clientWidth || 600;
  $('spec').innerHTML = ['ABCDEFG','HIJKLMN','OPQRSTU','VWXYZ','abcdefghijklm','nopqrstuvwxyz','0123456789',
    'ÀÁÂÃÄÅ ÆŒ Ø ÐÞß','ĀĂĄĆČĎ ĒĘĚĞ İıĽŁ','ŃŇŐŘŚȘŞ ŤŢȚŮŰŹŻŽ',
    'ƁƊƘƙƳƴɓɗ ḾṄỊỌỤ','ĈĊĜĠĢĤĨĮĴ ĶĹĻŅŖŜŨŲŴŶ',
    'ĐđĦħŦŧĸ ŊŋſĲĳĿŀŉ',
    'ΑΒΓΔΕΖΗΘΙΚΛΜΝ ΞΟΠΡΣΤΥΦΧΨΩ',
    'αβγδεζηθικλμν ξοπρσςτυφχψω',
    'АБВГДЕЁЖЗИЙКЛМН ОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
    'абвгдеёжзийклмн опрстуфхцчшщъыьэюя',
    'ҐґЄєЇїІіЂђЋћЉљЊњЏџ',
    'ĂăƠơƯư ẮắẦầỂểỘộỚớỰựỸỹ',
    'Tiếng Việt · Cộng hòa · Thượng Hải',
    'a\u0301\u0308 i\u0302\u0323 o\u031b\u0301',
    '¹²³⁴⁵⁶⁷⁸⁹⁰ ₁₂₃₄₅₆₇₈₉₀','½ ⅓ ⅔ ¼ ¾ ⅛ ⅜ ⅝ ⅞','& ! ? Ⓢ ♫ ☯ ⚡'].map(r => drawText(r, Math.min(46, sw / 8.5))).join('');
}
/* ---- built fonts: shipped files, plus drafts built by the local Lab server ---- */
const LAB = {token:null, busy:false, drafts:[]};
/** Show the real font file for these sliders: a fresh draft build, or the shipped cut. */
function renderStatic(){
  const built = spacingForCut(CUT, SPACING_EXPORTS);
  const draft = built && LAB.drafts.find(d => d.record === built);
  const exact = built && !draft && PRESETS.find(p => spacingForCut(p, [built]));
  const named = PRESETS.find(p => p.name.toLowerCase() === String(CUT.name).toLowerCase());
  const title = $('t-title').value || 'The Last Lotus';
  const local = !!LAB.token;
  $('lab-actions').hidden = !local;
  $('build-font').disabled = LAB.busy || !!draft || !!exact;
  const shipped = PRESETS.find(p => p.name === CUT.name);
  $('promote-cut').hidden = !local || !shipped || !!exact;
  $('promote-cut').textContent = shipped ? `Make these the shipped ${shipped.name}` : '';
  $('promote-cut').disabled = LAB.busy;
  let family, status;
  if(draft){
    family = draft.family;
    status = `Your draft font, built at ${draft.time} from exactly these sliders. The live drawings below now use its final spacing.`;
  } else if(exact){
    family = `"SEIHouse Display ${exact.name}", sans-serif`;
    status = `The real SEIHouse Display ${exact.name} file, typed by your browser. Your sliders match it, so the live drawings below look the same.`;
  } else if(named){
    family = `"SEIHouse Display ${named.name}", sans-serif`;
    status = `The shipped SEIHouse Display ${named.name} file. Your sliders have changed since it was built, so the live drawings below no longer match it.`
      + (local ? ' Build font to see your sliders as a real font.' : ' Rebuild the cut to update this file.');
  } else {
    status = local ? 'This cut has no font file yet. Build font to make one from your sliders.'
      : 'This cut has no font file yet. Download JSON and build it to get one; until then only the live drawing exists.';
  }
  $('static-status').textContent = status;
  $('static-sample').innerHTML = family
    ? `<div class="hint">Reader chapter title, 30px</div><div class="chap" style="font-family:${e_(family)}" lang="en">${e_(title)}</div>`
      + `<div class="big" style="font-family:${e_(family)}" lang="en">${e_(title)}</div>`
      + (draft ? `<p class="hint downloads">Download: <a href="${e_(draft.otf)}" download>OTF</a> · <a href="${e_(draft.woff2)}" download>WOFF2</a></p>` : '')
    : '';
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
/** Start a local Lab job and follow it until it finishes, showing its latest log line. */
async function runJob(kind, extra, label, target = 'job-status'){
  LAB.busy = true; renderStatic();
  const started = Date.now(), show = line => {
    $(target).textContent = `${label} · ${Math.round((Date.now()-started)/1000)} s${line ? ' · ' + line : ''}`;
  };
  try {
    show('');
    const response = await fetch('/api/jobs', {method:'POST', headers:{'Content-Type':'application/json', 'X-Lab-Token':LAB.token},
      body:JSON.stringify({kind, ...extra})});
    const start = await response.json();
    if(!response.ok) throw new Error(start.error || 'The job could not start');
    for(;;){
      await sleep(1500);
      const job = await (await fetch('/api/jobs/' + start.id, {cache:'no-store'})).json();
      show(job.log[job.log.length-1] || '');
      if(job.state !== 'running'){
        if(job.state === 'done') return job.result;
        throw new Error(job.result?.error || 'The job failed; see the Lab server window.');
      }
    }
  } finally { LAB.busy = false; renderStatic(); }
}
$('build-font').addEventListener('click', async () => {
  const cut = JSON.parse(JSON.stringify(CUT)), started = Date.now();
  try {
    const result = await runJob('build', {cut}, `Building ${cut.name}`);
    const record = await (await fetch(result.spacing, {cache:'no-store'})).json();
    // FontFace.family can come back already quoted, so keep the name we gave it.
    const name = `SEIHouse Lab Draft ${result.stamp}`;
    const face = new FontFace(name, `url("${result.woff2}") format("woff2")`);
    await face.load(); document.fonts.add(face);
    SPACING_EXPORTS.push(record);
    LAB.drafts.unshift({record, family:`"${name}", sans-serif`, otf:result.otf, woff2:result.woff2,
      time:new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})});
    $('job-status').textContent = `Built ${cut.name} in ${Math.round((Date.now()-started)/1000)} s.`;
    renderAll();
  } catch(error){ $('job-status').textContent = 'Build failed: ' + error.message; }
});
$('promote-cut').addEventListener('click', async () => {
  const cut = JSON.parse(JSON.stringify(CUT));
  if(!confirm(`Replace the shipped ${cut.name} with these settings?\n\nThis rewrites display/cuts/${cut.name.toLowerCase()}.json and rebuilds ${cut.name}'s font files in this repository. Git can undo it. Its Living Title will need motion approval again.`)) return;
  try {
    const result = await runJob('promote', {cut}, `Rebuilding the shipped ${cut.name}`);
    $('job-status').textContent = `${cut.name} is rebuilt (${result.changed.join(', ') || 'no setting changes'}). Reloading…`;
    await sleep(800); location.reload();
  } catch(error){ $('job-status').textContent = 'Promote failed: ' + error.message; }
});
/** Only the local Lab server answers /api/lab; the static website keeps these buttons hidden. */
(async () => {
  try {
    const response = await fetch('/api/lab', {cache:'no-store'});
    const info = response.ok && response.headers.get('Content-Type')?.includes('json') ? await response.json() : null;
    if(info?.local){ LAB.token = info.token; renderStatic(); window.dispatchEvent(new CustomEvent('lab-server', {detail:LAB})); }
  } catch {}
})();
function renderAllCuts(){
  const keep = CUT, title = $('t-title').value || 'The Last Lotus';
  const all = [...PRESETS, ...Object.values(SAVED).filter(s => !PRESETS.some(p => p.name === s.name))];
  $('all').innerHTML = all.map(c => { CUT = c; applyToEngine(); return `<div><div class="hint">${e_(c.name)}${c.note ? ' · ' + e_(c.note) : ''}</div>${drawText(title, Math.min(44, ($('all').clientWidth || 600) / 9))}</div>`; }).join('');
  CUT = keep; applyToEngine();
}
function renderOut(){ $('out').textContent = JSON.stringify(CUT, null, 2); }
let raf = 0;
function changed(){
  if(typeof LivingTitleUI !== 'undefined') LivingTitleUI.update(CUT,$('t-title').value,$('cpsp').checked);
  cancelAnimationFrame(raf); raf = requestAnimationFrame(renderAll); setMsg('Not saved yet');
}
function setMsg(t){ $('savemsg').textContent = t; }
function load(){ buildControls(); renderPresets(); renderAll(); setMsg(SAVED[CUT.name] ? 'Saved' : 'Not saved yet'); }
$('copy').addEventListener('click', async () => { try { await navigator.clipboard.writeText($('out').textContent); setMsg('Copied. Paste it to Claude with "build this cut".'); } catch(e){ setMsg('Copy failed: select the text and copy it.'); } });
$('download').addEventListener('click', () => SEIHouseDrafts.downloadJSON(CUT, slug(CUT.name) + '.json'));
/* ---- saving cuts ---- */
const slug = n => n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'untitled';
$('save').addEventListener('click', async () => {
  if(!db) return;
  const body = JSON.parse(JSON.stringify(CUT)); body.savedAt = Date.now();
  try { await db.doc('cuts/' + slug(CUT.name)).set(body); SAVED[CUT.name] = body; renderPresets(); renderAllCuts(); setMsg(db.local ? 'Saved in this browser. Download JSON to build or move this cut.' : 'Saved to the connected host. Download JSON to build locally.'); }
  catch(e){ setMsg((e && e.message === 'Invalid saved draft data' ? 'Invalid saved draft data. Existing drafts were kept.' : 'Save failed.') + ' Use Download JSON to keep a copy.'); }
});
(async () => {
  try { db = window.claude && typeof window.claude.use === 'function' ? await window.claude.use('db') : null; } catch(e){ db = null; }
  if(!db) db = SEIHouseDrafts.createLocalDB('seihouse.display.drafts.v1');
  $('save').disabled = false;
  try {
    const snap = await db.collection('cuts').get();
    let invalidAlternates=0;
    snap.docs.forEach(d => {
      const v=d.data(); if(!v || !v.name) return;
      try { v.alternates=displayChoices(v.alternates === undefined ? {} : v.alternates); SAVED[v.name]=v; }
      catch { invalidAlternates++; }
    });
    renderPresets(); renderAllCuts();
    if(snap.invalid || invalidAlternates){
      const warning = 'Invalid saved draft data: ' + ((snap.invalid || 0)+invalidAlternates) + ' unreadable record(s) were kept. Valid cuts are available below.';
      $('draftwarning').textContent = warning; $('draftwarning').hidden = false; setMsg(warning);
    } else setMsg(db.local ? 'Ready to save in this browser.' : 'Ready to save to the connected host.');
  } catch(e){ setMsg((e && e.message === 'Invalid saved draft data' ? 'Invalid saved draft data. Existing drafts were kept.' : 'Could not load drafts.') + ' Use Download JSON to keep a copy.'); }
})();
$('spec-card').addEventListener('toggle', renderSpec);
$('reset').addEventListener('click', () => { const name = CUT.name; CUT = JSON.parse(ORIGIN); CUT.name = name; load(); setMsg('Sliders reset'); });
renderPalettes(); load();
window.addEventListener('resize', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(renderAll); });
</script>
<script>__LIVING_FACTORY__
const MOTION_PROFILES=__MOTION_PROFILES__;
const LIVING_MEDIA_URL=__MEDIA_URL__;
__LIVING_CORE__
__LIVING_UI__
LivingTitleUI.update(CUT,$('t-title').value,$('cpsp').checked);
/* Preparing motion is heavy, so it waits until the Living title section is opened. */
if($('living-title').open) void LivingTitleUI.prepare();
else $('living-title').addEventListener('toggle', () => { if($('living-title').open && !LivingTitleUI.inspect().prepared) void LivingTitleUI.prepare(); });
</script></body></html>"""
out = os.environ.get('LAB_OUT', os.path.join(HERE, 'lab', 'index.html'))
media_url = os.path.relpath(os.path.join(HERE, 'lab', 'living-media.js'), os.path.dirname(os.path.abspath(out))).replace('\\', '/')
license_url = os.path.relpath(os.path.join(HERE, 'lab', 'living-media-LICENSE.txt'), os.path.dirname(os.path.abspath(out))).replace('\\', '/')
fonts_css = os.path.relpath(os.path.join(HERE, 'fonts.css'), os.path.dirname(os.path.abspath(out))).replace('\\', '/')
html = (HTML.replace('__DISPLAY_FONTS_CSS__', fonts_css).replace('__ENGINE__', draft_helper + '\n' + engine + '\n' + stroke_geometry + '\n' + spacing_helper)
        .replace('__PRESETS__', json.dumps(presets, ensure_ascii=False))
        .replace('__SPACING__', json.dumps(spacing_exports, ensure_ascii=False, separators=(',', ':')))
        .replace('__LIVING_PANEL__', open(os.path.join(HERE, 'living-panel.html'), encoding='utf-8').read().replace('living-media-LICENSE.txt', license_url))
        .replace('__LIVING_FACTORY__', engine_factory())
        .replace('__MOTION_PROFILES__', json.dumps(profiles_for_lab(), separators=(',', ':')))
        .replace('__MEDIA_URL__', json.dumps(media_url))
        .replace('__LIVING_CORE__', open(os.path.join(HERE, 'living.js'), encoding='utf-8').read())
        .replace('__LIVING_UI__', open(os.path.join(HERE, 'living-ui.js'), encoding='utf-8').read()))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print('display lab', len(html))
