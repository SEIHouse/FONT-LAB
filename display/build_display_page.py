"""Builds the SEIHouse Display Lab: one page to shape display cuts live and save them."""
import json, os, glob, hashlib
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from display.title_spacing import spacing_settings
engine = open(os.path.join(HERE, '..', 'engine.js'), encoding='utf-8').read()
stroke_geometry = open(os.path.join(HERE, 'stroke_geometry.js'), encoding='utf-8').read()
spacing_helper = open(os.path.join(HERE, 'spacing.js'), encoding='utf-8').read()
draft_helper = open(os.path.join(HERE, '..', 'site', 'drafts.js'), encoding='utf-8').read()
presets = [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(os.path.join(HERE, 'cuts', '*.json')))]
order = ['Soft', 'Edge', 'Ink', 'Wide']
presets.sort(key=lambda c: order.index(c['name']) if c['name'] in order else 99)
spacing_dir = os.environ.get('SPACING_DIR', HERE)
def load_spacing(cut):
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
    if record.get('schema') != 1 or record['settings'] != spacing_settings(cut) or record['otf_sha256'] != digest:
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
@media (max-width:900px){ .wrap{ grid-template-columns:1fr; padding:12px; } }
h1{ font-size:20px; margin:0 0 2px; } .sub{ color:var(--mute); font-size:13px; margin:0 0 14px; }
aside{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; align-self:start; position:sticky; top:12px; max-height:calc(100vh - 24px); overflow:auto; }
@media (max-width:900px){ aside{ position:static; max-height:none; } }
.sec{ border-bottom:1px solid var(--line); padding:10px 0; display:grid; gap:9px; }
.sec:last-child{ border-bottom:0; }
.sec h2{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--mute); margin:0; }
.row{ display:flex; flex-wrap:wrap; gap:6px; }
.pill{ font:inherit; font-size:13px; padding:6px 11px; border-radius:999px; border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer; }
.pill[aria-pressed="true"]{ background:var(--ink); color:#0d0f13; border-color:var(--ink); }
.pill.primary{ background:var(--accent); color:#0d0f13; border-color:var(--accent); font-weight:600; }
.pill:focus-visible, input:focus-visible, textarea:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
label.ctl{ display:grid; gap:3px; font-size:13px; color:var(--mute); }
label.ctl span{ display:flex; justify-content:space-between; } label.ctl output{ color:var(--ink); }
input[type=range]{ width:100%; accent-color:var(--accent); }
input[type=text], textarea{ width:100%; font:inherit; background:#0d0f13; color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:7px 9px; }
textarea{ min-height:84px; resize:vertical; }
.hint{ font-size:12px; color:var(--mute); }
main{ display:grid; gap:16px; min-width:0; }
.card{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; min-width:0; }
.card h2{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--mute); margin:0 0 10px; }
.covers{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:16px; }
@media (max-width:1100px){ .covers{ grid-template-columns:1fr; } }
.cover{ aspect-ratio:1/1; border-radius:12px; padding:7%; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; position:relative; }
.cover .mark{ align-self:flex-end; opacity:.9; }
.run{ display:flex; flex-wrap:wrap; align-items:flex-start; } .run svg{ display:block; overflow:visible; flex:none; }
.tracks{ display:grid; gap:6px; }
.tracks .tr{ display:grid; grid-template-columns:2.2em minmax(0,1fr); align-items:start; color:var(--ink); }
.tracks .num{ color:var(--mute); font-size:14px; padding-top:6px; }
.all{ display:grid; gap:12px; } .all .hint{ margin-bottom:2px; }
.out{ font:12px/1.4 ui-monospace,Menlo,monospace; white-space:pre-wrap; background:#0d0f13; border:1px solid var(--line); border-radius:8px; padding:8px; max-height:160px; overflow:auto; }
</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs id="clips"></defs></svg>
<div class="wrap">
<aside aria-label="Cut settings">
  <a class="pill" href="../../index.html" style="display:inline-block;text-decoration:none">← Font Lab home</a>
  <h1>SEIHouse Display Lab</h1>
  <p class="sub">One engine, a different cut for every album or project.</p>
  <div class="sec"><h2>Cut</h2>
    <div class="row" id="presets" role="group" aria-label="Starting cuts"></div>
    <div class="row" id="saved" role="group" aria-label="Saved cuts"></div>
    <label class="ctl"><span>Name of this cut</span><input type="text" id="cutname" maxlength="40" autocomplete="off"></label>
    <div class="row"><button type="button" class="pill primary" id="save" disabled>Save cut</button><button type="button" class="pill" id="download">Download JSON</button></div>
    <div class="hint" id="savemsg" aria-live="polite">Loading drafts…</div>
    <p class="hint" id="draftwarning" hidden></p>
    <p class="hint">Browser drafts stay on this device and site. Download JSON to build a font or move your cut.</p>
  </div>
  <div class="sec"><h2>Shape</h2>
    <div class="row" role="group" aria-label="Corners"><button type="button" class="pill" data-k="corners" data-v="soft">Soft corners</button><button type="button" class="pill" data-k="corners" data-v="cut">Cut corners</button></div>
    <div class="row" role="group" aria-label="Ends"><button type="button" class="pill" data-k="ends" data-v="round">Round ends</button><button type="button" class="pill" data-k="ends" data-v="flat">Flat ends</button></div>
    <div class="row" role="group" aria-label="Joins"><button type="button" class="pill" data-k="joins" data-v="round">Round joins</button><button type="button" class="pill" data-k="joins" data-v="sharp">Sharp joins</button></div>
    <div id="ctl-shape" class="sec" style="border:0;padding:0"></div>
  </div>
  <div class="sec"><h2>Pen</h2><div id="ctl-pen" class="sec" style="border:0;padding:0"></div></div>
  <div class="sec"><h2>Spacing</h2><div id="ctl-space" class="sec" style="border:0;padding:0"></div>
    <label><input type="checkbox" id="cpsp"> Capital spacing (cpsp)</label>
    <p class="hint" id="spacing-status" aria-live="polite"></p>
  </div>
  <div class="sec"><h2>Your words</h2>
    <label class="ctl"><span>Title</span><input type="text" id="t-title" value="The Last Lotus" maxlength="60"></label>
    <label class="ctl"><span>Artist</span><input type="text" id="t-artist" value="SENSEI" maxlength="40"></label>
    <label class="ctl"><span>Tracks (one per line)</span><textarea id="t-tracks">Pavilion
Roots Through Ruin
Skybound
Oath (Interlude)
Bloom</textarea></label>
    <div class="row" role="group" aria-label="Cover colors" id="palettes"></div>
  </div>
  <div class="sec"><h2>Copy instead of Save</h2><div class="out" id="out" tabindex="0"></div><div class="row"><button type="button" class="pill" id="copy">Copy</button></div></div>
</aside>
<main>
  <section class="card"><h2>Album cover</h2><div class="covers"><div class="cover" id="cover1"></div><div class="cover" id="cover2"></div></div></section>
  <section class="card"><h2>Track list</h2><div class="tracks" id="tracks"></div></section>
  <section class="card"><h2>Poster line</h2><div id="poster"></div></section>
  <section class="card"><h2>Every letter</h2><div id="spec" style="display:grid;gap:8px"></div></section>
  <section class="card"><h2>All cuts side by side</h2><div class="all" id="all"></div></section>
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
    ['uprightStraightness', 'Straightness (lower = squarer)', 0.4, 1, 0.01]],
  'ctl-pen': [['contrast', 'Thick and thin', 1, 3.5, 0.01], ['penAngle', 'Pen angle', -60, 60, 1], ['slant', 'Slant', -6, 16, 0.5]],
  'ctl-space': [['spaceBetweenAllLetters', 'Space between letters', -30, 120, 1], ['wordSpace', 'Space between words', 120, 480, 1]],
};
const PALETTES = { Night:['#0f1115','#2b3140','#eef1f6'], Dawn:['#f6d7ad','#e7836a','#2a1714'], Jade:['#0b3a33','#2f8a6c','#eafff6'],
                   Ember:['#2a0d0b','#c2462b','#fff1e6'], Paper:['#f4efe6','#e6dccb','#1b1d22'], Violet:['#17112b','#6b54d6','#f2eeff'] };
let CUT = JSON.parse(JSON.stringify(PRESETS[0])), SAVED = Object.create(null), PAL = 'Night', PAL2 = 'Paper', db = null;

function applyToEngine(){
  P.base = CUT.weight; P.ws = CUT.letterWidth; P.xh = CUT.xHeight; P.contrast = displayContrast(CUT.weight, CUT.contrast, CUT.xHeight, CUT.ends); P.penAngle = CUT.penAngle || 0;
  P.caprx = CUT.capitalRoundness; P.round = CUT.lowercaseRoundness; P.straight = CUT.uprightStraightness || 1;
  P.corner = CUT.corners === 'cut' ? 'cut' : 'soft'; P.cap = CUT.ends; P.join = CUT.joins;
  P.os = CUT.overshoot === false ? 0 : 1; P.ufoot = CUT.uFoot ? 1 : 0; P.asc = CUT.ascender || 700;
  P.ital = 0; P.obliqueAngle = CUT.slant || 0; P.trk = CUT.spaceBetweenAllLetters;
  for(const k in cache) delete cache[k];
}
/* angled oval pen, drawn the same way the font builder does it */
const penBodies = new WeakMap();
function penBody(g){
  const key = [P.contrast,CUT.penAngle,CUT.slant,CUT.ends,CUT.joins].join('|');
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
    parts += `<g transform="translate(${gx} 0)${sl ? ` skewX(${-sl})` : ''}"${CUT.ends === 'flat' ? '' : ` clip-path="url(#${g.clipId})"`}>${penBody(g)}</g>`;
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
function buildControls(){
  for(const [box, list] of Object.entries(SLIDERS)){
    $(box).innerHTML = list.map(([k, label, mn, mx, st]) =>
      `<label class="ctl"><span>${label} <output id="o-${k}">${CUT[k]}</output></span><input type="range" id="r-${k}" min="${mn}" max="${mx}" step="${st}" value="${CUT[k]}" aria-label="${label}"></label>`).join('');
    list.forEach(([k]) => $('r-' + k).addEventListener('input', ev => { CUT[k] = +ev.target.value; $('o-' + k).textContent = CUT[k]; changed(); }));
  }
  document.querySelectorAll('[data-k]').forEach(b => b.setAttribute('aria-pressed', String(CUT[b.dataset.k] === b.dataset.v)));
  $('cutname').value = CUT.name;
}
document.querySelectorAll('[data-k]').forEach(b => b.addEventListener('click', () => { CUT[b.dataset.k] = b.dataset.v; buildControls(); changed(); }));
function renderPresets(){
  $('presets').innerHTML = PRESETS.map(p => `<button type="button" class="pill" data-p="${e_(p.name)}" aria-pressed="${p.name === CUT.name}">${e_(p.name)}</button>`).join('');
  $('presets').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { CUT = JSON.parse(JSON.stringify(PRESETS.find(p => p.name === b.dataset.p))); load(); }));
  const names = Object.keys(SAVED).sort();
  $('saved').innerHTML = names.length ? names.map(n => `<button type="button" class="pill" data-s="${e_(n)}" aria-pressed="${n === CUT.name}">${e_(n)}</button>`).join('') : '';
  $('saved').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { CUT = JSON.parse(JSON.stringify(SAVED[b.dataset.s])); load(); }));
}
function renderPalettes(){
  $('palettes').innerHTML = Object.keys(PALETTES).map(n => `<button type="button" class="pill" data-pal="${n}" aria-pressed="${n === PAL}">${n}</button>`).join('');
  $('palettes').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { PAL2 = PAL; PAL = b.dataset.pal; renderPalettes(); renderAll(); }));
}
$('cutname').addEventListener('input', ev => { CUT.name = ev.target.value.trim() || 'Untitled'; renderOut(); });
['t-title','t-artist','t-tracks'].forEach(id => $(id).addEventListener('input', () => renderAll()));
$('cpsp').addEventListener('change', () => renderAll());
/* ---- previews ---- */
function cover(el, pal){
  const [a, b, ink] = PALETTES[pal]; el.style.background = `linear-gradient(155deg, ${a}, ${b})`;
  const w = el.clientWidth || 420, title = $('t-title').value || ' ', artist = $('t-artist').value || ' ';
  el.innerHTML = `<div class="mark">${drawText('Ⓢ', w*0.07, ink)}</div><div style="display:grid;gap:${f1(w*0.02)}px">${drawText(title, w*0.13, ink, 1.02)}${drawText(artist.toUpperCase(), w*0.045, ink)}</div>`;
}
function renderAll(){
  applyToEngine();
  const exactSpacing = spacingForCut(CUT, SPACING_EXPORTS);
  $('cpsp').disabled = !exactSpacing;
  $('spacing-status').textContent = exactSpacing ? 'Final spacing from this built cut.'
    : 'Draft preview. Build this cut and rebuild the Lab for final title spacing.';
  cover($('cover1'), PAL); cover($('cover2'), PAL === 'Paper' ? 'Night' : 'Paper');
  const tracks = $('t-tracks').value.split('\n').map(s => s.trim()).filter(Boolean);
  const tw = $('tracks').clientWidth || 600;
  $('tracks').innerHTML = tracks.map((t, i) => `<div class="tr"><span class="num">${String(i + 1).padStart(2, '0')}</span>${drawText(t, Math.min(30, tw / 12))}</div>`).join('');
  const pw = $('poster').clientWidth || 600, sw = $('spec').clientWidth || 600;
  $('poster').innerHTML = drawText(($('t-title').value || '').toUpperCase(), Math.min(64, pw / 5.5)) + drawText(($('t-artist').value || '') + ' · Live at the Celestial Library', Math.min(26, pw / 14));
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
  renderAllCuts(); renderOut();
}
function renderAllCuts(){
  const keep = CUT, title = $('t-title').value || 'The Last Lotus';
  const all = [...PRESETS, ...Object.values(SAVED).filter(s => !PRESETS.some(p => p.name === s.name))];
  $('all').innerHTML = all.map(c => { CUT = c; applyToEngine(); return `<div><div class="hint">${e_(c.name)}${c.note ? ' · ' + e_(c.note) : ''}</div>${drawText(title, Math.min(44, ($('all').clientWidth || 600) / 9))}</div>`; }).join('');
  CUT = keep; applyToEngine();
}
function renderOut(){ $('out').textContent = JSON.stringify(CUT, null, 2); }
let raf = 0;
function changed(){ cancelAnimationFrame(raf); raf = requestAnimationFrame(renderAll); setMsg('Not saved yet'); }
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
    snap.docs.forEach(d => { const v = d.data(); if(v && v.name) SAVED[v.name] = v; });
    renderPresets(); renderAllCuts();
    if(snap.invalid){
      const warning = 'Invalid saved draft data: ' + snap.invalid + ' unreadable record(s) were kept. Valid cuts are available below.';
      $('draftwarning').textContent = warning; $('draftwarning').hidden = false; setMsg(warning);
    } else setMsg(db.local ? 'Ready to save in this browser.' : 'Ready to save to the connected host.');
  } catch(e){ setMsg((e && e.message === 'Invalid saved draft data' ? 'Invalid saved draft data. Existing drafts were kept.' : 'Could not load drafts.') + ' Use Download JSON to keep a copy.'); }
})();
renderPalettes(); load();
window.addEventListener('resize', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(renderAll); });
</script></body></html>"""
html = (HTML.replace('__ENGINE__', draft_helper + '\n' + engine + '\n' + stroke_geometry + '\n' + spacing_helper)
        .replace('__PRESETS__', json.dumps(presets, ensure_ascii=False))
        .replace('__SPACING__', json.dumps(spacing_exports, ensure_ascii=False, separators=(',', ':'))))
out = os.environ.get('LAB_OUT', os.path.join(HERE, 'lab', 'index.html'))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print('display lab', len(html))
