"""Builds the SEIReader Lab: live controls for every font setting, a Save button Claude can read,
the current font file and the 0.6 file for comparison."""
import base64, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emoji_demo import EMOJI
HERE = os.path.dirname(os.path.abspath(__file__))
settings = json.load(open(os.path.join(HERE, 'settings.json'), encoding='utf-8'))
VERSION = settings['version']
kern = json.load(open(os.path.join(HERE, 'kern_auto.json'), encoding='utf-8'))           # automatic pair spacing
kern.update(json.load(open(os.path.join(HERE, 'kern_base.json'), encoding='utf-8')))     # hand-set pairs win
style_kern = json.load(open(os.path.join(HERE, 'kern_styles.json'), encoding='utf-8'))
kern.update(style_kern['Regular'])
for k, v in settings.get('pairSpace', {}).items(): kern[k] = v
b64 = lambda p: base64.b64encode(open(os.path.join(HERE, p), 'rb').read()).decode()
WEIGHTS = dict(settings.get('weights', {})); WEIGHTS['Regular'] = settings['weight']
WORDER = [w for w in ['Light','Regular','Medium','SemiBold','Bold'] if w in WEIGHTS]
WCLASS = {'Light':300,'Regular':400,'Medium':500,'SemiBold':600,'Bold':700}
FONTLIST = [{'name':'SEIReader','weight':str(WCLASS[w]),'style':'normal','data':b64(f'fonts/SEIReader-{w}.woff2')} for w in WORDER]
FONTLIST += [{'name':'SEIReader','weight':str(WCLASS[w]),'style':'italic','data':b64('fonts/SEIReader-' + ('Italic' if w == 'Regular' else w + 'Italic') + '.woff2')} for w in WORDER]
OLD = b64('old/previous.woff2')
FONTLIST.append({'name':'SEIReader Previous','weight':'400','style':'normal','data':OLD})
ENGINE = open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
BAKED = {
  'weight': settings['weight'], 'xHeight': settings.get('xHeight', 520),
  'lowercaseRoundness': settings['lowercaseRoundness'], 'capitalRoundness': settings.get('capitalRoundness', 210),
  'letterWidth': settings.get('letterWidth', 1.0), 'spaceBetweenAllLetters': settings['spaceBetweenAllLetters'],
  'wordSpace': settings.get('wordSpace', 250),
  'weights': WEIGHTS,
  'uprightStraightness': settings.get('uprightStraightness', 1),
  'contrast': settings.get('contrast', 1),
  'ascender': settings.get('ascender', 770),
  'overshoot': settings.get('overshoot', True), 'uFoot': settings.get('uFoot', True),
  'letterSpace': settings.get('letterSpace', {}), 'pairSpace': settings.get('pairSpace', {}),
}
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉½¼¾⁄.,:;…!?'\"‘’“”-–—()[]/%+=&@#$*~_|\\{}<>★•·×÷±°→←∞«»‹›¥€£☯⚡☀☾☽⚔✦☆◆◇▲▼▶◀↑↓♥♡✓✗♪©®™−≤≥≠≈Ⓢ♩♫♬♭♮♯⏮⏸⏹⏺⏭🎧💻📖🔖🔍🔔⚙⌂🎤💿🔊ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝŸÆŒÐÞàáâãäåçèéêëìíîïñòóôõöøùúûüýÿæœßðþ¡¿ºª"
CHAPTER = [
  "The lantern burned low as the last gate opened—slowly, then all at once. Beyond it lay the hall of quiet books, thousands of them, and every shelf seemed to hum.",
  "“Don’t stop now,” Ren whispered. His voice came back to him twice, as if the room were deciding whether to answer.",
  "He had counted the steps on the way down: 312. Mei had counted 314. *Why does it matter?* he thought. Neither of them mentioned it again, but both of them kept counting on the way back.",
  "Nobody had walked here in a hundred years. Still, the floor was clean; the dust had been swept aside (carefully, in long even lines), as if something had been waiting for them. On the nearest shelf sat a copy of *The Nine Heavens*, open. *Crack!* Somewhere above, a seal broke.",
  "“Come in,” said a voice from somewhere above the shelves. “You’re late. You were supposed to arrive in the spring of the ninth year, and it is nearly winter.”",
]

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>SEIReader</title>
<meta name="color-scheme" content="light dark">
<style>
  :root{
    --bg:#eceff4; --panel:#fbfcfe; --ink:#151922; --mute:#5a6273; --line:#cdd3de; --accent:#3d52d5;
    box-sizing:border-box;
    padding-top:env(safe-area-inset-top,0px);
    padding-bottom:env(safe-area-inset-bottom,0px);
  }
  @media (prefers-color-scheme:dark){
    :root:not([data-theme="light"]){ --bg:#0e1117; --panel:#171b24; --ink:#e9edf5; --mute:#9aa3b5; --line:#2b3140; --accent:#8ea0ff; }
  }
  :root[data-theme="dark"]{ --bg:#0e1117; --panel:#171b24; --ink:#e9edf5; --mute:#9aa3b5; --line:#2b3140; --accent:#8ea0ff; }
  html{ scroll-padding-top:env(safe-area-inset-top,0px); }
  *{ box-sizing:border-box; }
  body{ margin:0; background:var(--bg); color:var(--ink); font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; line-height:1.5; }
  .wrap{ max-width:1240px; margin:0 auto; padding:24px 20px 72px; }
  h1{ margin:0; font-size:28px; font-weight:650; }
  h2{ font-size:15px; font-weight:650; margin:0 0 6px; }
  p{ margin:0; }
  .meta{ display:flex; flex-wrap:wrap; gap:8px 10px; align-items:center; margin-top:10px; }
  .badge{ font-size:12.5px; padding:4px 11px; border-radius:999px; border:1px solid var(--line); background:var(--panel); }
  .badge.bad{ color:#b3261e; border-color:#b3261e; }
  .note{ color:var(--mute); font-size:14px; max-width:70ch; margin-top:10px; }

  .layout{ display:grid; grid-template-columns:330px minmax(0,1fr); gap:22px; margin-top:20px; align-items:start; }
  .controls{ position:sticky; top:10px; max-height:calc(100vh - 20px); overflow:auto; background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; display:grid; gap:16px; }
  .grp{ display:grid; gap:10px; }
  .grp + .grp{ border-top:1px solid var(--line); padding-top:14px; }
  .ctl{ display:grid; gap:3px; }
  .cl{ font-size:13px; color:var(--mute); display:flex; justify-content:space-between; gap:8px; }
  .cl output{ color:var(--ink); font-variant-numeric:tabular-nums; }
  .hint{ font-size:12px; color:var(--mute); }
  input[type=range]{ width:100%; accent-color:var(--accent); }
  input[type=text]{ font:inherit; font-size:16px; padding:9px 12px; border:1px solid var(--line); border-radius:8px; background:var(--panel); color:var(--ink); width:100%; }
  input:focus-visible, button:focus-visible, summary:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
  .pill{ font:inherit; font-size:13px; padding:7px 13px; border-radius:999px; border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer; }
  .pill.primary{ background:var(--ink); color:var(--bg); border-color:var(--ink); }
  .pill[aria-pressed="true"]{ background:var(--ink); color:var(--bg); border-color:var(--ink); }
  .pill:disabled{ opacity:.45; cursor:default; }
  .row{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .savemsg{ font-size:12.5px; color:var(--mute); }
  .toggle-controls{ display:none; }

  @media (max-width:860px){
    .layout{ grid-template-columns:1fr; }
    .controls{ top:0; max-height:46vh; border-radius:0 0 14px 14px; z-index:8; }
    .controls.collapsed{ max-height:none; }
    .controls.collapsed .body{ display:none; }
    .toggle-controls{ display:inline-flex; }
  }
  .body{ display:grid; gap:10px; }
  .savebar{ display:grid; gap:6px; padding-bottom:12px; border-bottom:1px solid var(--line); }
  details.sec{ border-bottom:1px solid var(--line); padding-bottom:10px; }
  details.sec > summary{ cursor:pointer; font-size:14px; font-weight:650; color:var(--ink); padding:6px 0; list-style:none; display:flex; justify-content:space-between; align-items:center; }
  details.sec > summary::-webkit-details-marker{ display:none; }
  details.sec > summary::after{ content:"+"; color:var(--mute); font-weight:400; font-size:18px; }
  details.sec[open] > summary::after{ content:"–"; }
  .secbody{ display:grid; gap:10px; padding-top:4px; }
  .grp0{ display:grid; gap:10px; }
  .controls .letters button{ min-width:32px; height:34px; font-size:17px; padding:0 6px; }

  .main{ display:grid; gap:26px; min-width:0; }
  .card{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; min-width:0; }
  .sub{ color:var(--mute); font-size:13.5px; margin-bottom:10px; max-width:64ch; }

  /* text drawn live from the settings */
  .run{ display:flex; flex-wrap:wrap; align-items:flex-start; }
  .run.nw{ flex-wrap:nowrap; }
  .run svg{ flex:none; display:block; overflow:visible; }

  .chamber{ --r-bg:#fbf9f4; --r-ink:#1d1f24; --r-mute:#6b6f78; border-radius:20px; padding:clamp(20px,5vw,40px); background:var(--r-bg); color:var(--r-ink); border:1px solid var(--line); }
  .chamber.night{ --r-bg:#121418; --r-ink:#d9dde6; --r-mute:#8b92a1; }
  .chamber .inner{ max-width:var(--measure,62ch); margin:0 auto; font-size:var(--rsize,18px); }
  .chamber .clabel{ color:var(--r-mute); margin-bottom:6px; }
  .chamber .title{ margin-bottom:22px; }
  .chamber .para{ margin-bottom:1em; }
  .chamber .reviewtag{ color:var(--r-mute); font:12px/1.4 system-ui,sans-serif; letter-spacing:.04em; margin-bottom:5px; }
  .chamber .reviewline{ border-bottom:1px solid var(--line); padding-bottom:1em; }
  .chamber .cap{ color:var(--r-mute); margin-top:6px; }
  .filemode p{ margin:0 0 1em; line-height:var(--rlh,1.55); }
  .side{ display:grid; grid-template-columns:1fr 1fr; gap:28px; }
  .side .inner{ max-width:none; margin:0; }
  .sidelabel{ font:12px system-ui,sans-serif; color:var(--r-mute); margin-bottom:10px; letter-spacing:.02em; }
  @media (max-width:860px){ .side{ grid-template-columns:1fr; } }
  .f-new{ font-family:'SEIReader', system-ui, sans-serif; font-synthesis:none; }
  .f-old{ font-family:'SEIReader Previous', system-ui, sans-serif; font-synthesis:none; }

  .number-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(235px,1fr)); gap:12px; }
  .number-panel{ border:1px solid var(--line); border-radius:12px; background:var(--bg); padding:14px; }
  .number-panel h3{ margin:0 0 8px; font:600 12px/1.3 system-ui,sans-serif; color:var(--mute); }
  .stat-line{ display:flex; justify-content:space-between; gap:12px; align-items:baseline; padding:5px 0;
    font:20px/1.3 'SEIReader',system-ui,sans-serif; font-synthesis:none; }
  .stat-line + .stat-line{ border-top:1px solid var(--line); }
  .stat-line strong{ font-weight:400; font-size:26px; white-space:nowrap; }
  .number-panel.tabular .stat-line strong{ font-variant-numeric:tabular-nums; }
  .number-samples{ display:flex; flex-wrap:wrap; gap:12px 24px; margin-top:14px;
    font:26px/1.4 'SEIReader',system-ui,sans-serif; font-synthesis:none; }
  .number-samples > span{ white-space:nowrap; }
  .feature-sups{ font-feature-settings:'sups' 1; }
  .feature-subs{ font-feature-settings:'subs' 1; }
  .feature-frac{ font-feature-settings:'frac' 1; }

  .letters{ display:flex; flex-wrap:wrap; gap:6px; }
  .letters button{ font-family:'SEIReader', system-ui, sans-serif; font-synthesis:none; font-size:21px; line-height:1; background:var(--bg); border:1px solid var(--line); border-radius:8px; min-width:40px; height:42px; padding:0 8px; color:var(--ink); cursor:pointer; }
  .letters button[aria-pressed="true"]{ outline:2px solid var(--accent); outline-offset:1px; }
  .letters button.changed{ box-shadow:inset 0 -3px 0 var(--accent); }
  .pairin{ display:flex; gap:10px; flex-wrap:wrap; }
  .pairin label{ display:grid; gap:4px; font-size:13px; color:var(--mute); width:80px; }
  .pairin input{ text-align:center; font-size:20px; }
  /* comments + custom emojis demo */
  .cm-list{ display:grid; gap:14px; margin:12px 0 16px; }
  .cm{ display:grid; grid-template-columns:36px minmax(0,1fr); gap:10px; }
  .cm .av{ width:36px; height:36px; border-radius:50%; display:grid; place-items:center; font-weight:650; font-size:14px; color:#fff; }
  .cm .who{ font-size:12.5px; color:var(--mute); margin-bottom:2px; }
  .cm .who b{ color:var(--ink); font-weight:600; }
  .cm .txt{ font-family:'SEIReader', system-ui, sans-serif; font-synthesis:none; font-size:17px; line-height:1.5; overflow-wrap:anywhere; }
  .emo{ height:1.35em; width:auto; vertical-align:-0.32em; margin:0 .04em; }
  .cm .txt.jumbo .emo{ height:3em; vertical-align:middle; margin-right:.15em; }
  .compose{ display:grid; gap:8px; position:relative; }
  .compose textarea{ font-family:'SEIReader', system-ui, sans-serif; font-synthesis:none; font-size:17px; line-height:1.5; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:var(--bg); color:var(--ink); resize:vertical; min-height:70px; width:100%; }
  .compose textarea:focus-visible{ outline:2px solid var(--accent); outline-offset:1px; }
  .sugg{ display:flex; flex-wrap:wrap; gap:6px; }
  .sugg button, .picker button.e{ display:inline-flex; align-items:center; gap:6px; font:inherit; font-size:13px; padding:5px 10px; border-radius:999px; border:1px solid var(--line); background:var(--bg); color:var(--ink); cursor:pointer; }
  .sugg button img{ height:22px; }
  .picker{ border:1px solid var(--line); border-radius:12px; padding:10px; background:var(--bg); display:grid; gap:8px; }
  .picker .grid{ display:flex; flex-wrap:wrap; gap:6px; }
  .picker button.e{ padding:6px; border-radius:10px; }
  .picker button.e img{ height:34px; width:34px; }
  .picker[hidden]{ display:none; }
  .reg{ font-size:12px; white-space:pre; overflow:auto; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:10px; max-height:260px; margin-top:8px; }
  details summary{ cursor:pointer; font-size:13px; color:var(--mute); }
  .out{ white-space:pre-wrap; overflow-wrap:anywhere; font-size:12px; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:10px; max-height:180px; overflow:auto; margin-top:8px; }
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs id="clips"></defs></svg>
<div class="wrap">
  <h1>SEIReader</h1>
  <div class="meta">
    <span class="badge">Font file: version __VERSION__</span>
    <span class="badge" id="status" role="status">Loading…</span>
    <a class="badge" href="comparison.html">Compare __VERSION__, 0.29, Literata, and Rubik</a>
  </div>
  <p class="note">Move any slider and the text changes live, drawn from the exact rules the font file is built from. Press <b>Save</b> when you like it, then tell Claude “build it”. Claude reads your saved settings and makes the new font file. No copying needed.</p>

  <div class="layout">
    <aside class="controls" id="controls" aria-label="Font settings">
      <div class="row"><button type="button" class="pill toggle-controls" id="togglectl" aria-expanded="true">Hide settings</button></div>
      <div class="body">
        <div class="savebar">
          <div class="row">
            <button type="button" class="pill primary" id="save" disabled>Save</button>
            <button type="button" class="pill" id="reset">Back to font file</button>
          </div>
          <span class="savemsg" id="savemsg" aria-live="polite">Saving turns on once the page connects.</span>
        </div>

        <details class="sec" open>
          <summary>Letters</summary>
          <div class="secbody">
            <div id="fontctl" class="grp0"></div>
            <div class="row">
              <button type="button" class="pill" id="t-os" aria-pressed="true">Round letters a touch taller</button>
              <button type="button" class="pill" id="t-u" aria-pressed="true">u with foot</button>
            </div>
          </div>
        </details>

        <details class="sec" open>
          <summary>Weights</summary>
          <div class="secbody"><div id="weightctl" class="grp0"></div></div>
        </details>

        <details class="sec" open>
          <summary>Spacing</summary>
          <div class="secbody"><div id="spacectl" class="grp0"></div></div>
        </details>

        <details class="sec">
          <summary>One letter</summary>
          <div class="secbody">
            <p class="hint">Pick a letter, then change the space before and after it. A blue line means you changed it. The close-up is on the right.</p>
            <div class="letters" id="letters" role="group" aria-label="Choose a letter"></div>
            <div id="letterpanel" class="grp0"></div>
          </div>
        </details>

        <details class="sec">
          <summary>Two letters together</summary>
          <div class="secbody">
            <p class="hint">Type two letters and change the space between them. The close-up is on the right.</p>
            <div id="pairpanel" class="grp0"></div>
          </div>
        </details>

        <details class="sec">
          <summary>Reading setup</summary>
          <div class="secbody">
            <div class="row">
              <button type="button" class="pill" id="m-day" aria-pressed="true">Day</button>
              <button type="button" class="pill" id="m-night" aria-pressed="false">Night</button>
            </div>
            <div id="readctl" class="grp0"></div>
          </div>
        </details>

        <details class="sec">
          <summary>Compare</summary>
          <div class="secbody">
            <div class="row" role="group" aria-label="What the Reader Chamber shows">
              <button type="button" class="pill" id="v-live" aria-pressed="true">Your settings</button>
              <button type="button" class="pill" id="v-file" aria-pressed="false">Font file __VERSION__</button>
              <button type="button" class="pill" id="v-old" aria-pressed="false">0.6</button>
              <button type="button" class="pill" id="v-side" aria-pressed="false">Side by side with 0.6</button>
            </div>
            <p class="hint" style="margin-top:4px">Start from</p>
            <div class="row">
              <button type="button" class="pill" id="p-file">Font file __VERSION__</button>
              <button type="button" class="pill" id="p-06">0.6</button>
            </div>
            <div class="hint" id="diff" aria-live="polite"></div>
          </div>
        </details>

        <details class="sec">
          <summary>Copy instead of Save</summary>
          <div class="secbody">
            <div class="out" id="outtext" tabindex="0"></div>
            <button type="button" class="pill" id="copy">Copy</button>
          </div>
        </details>
      </div>
    </aside>

    <div class="main">
      <article class="chamber" id="chamber" aria-label="Reader Chamber sample chapter">
        <div class="inner" id="chamberInner"></div>
      </article>

      <section class="card" id="weightsCard">
        <h2>Weights</h2>
        <div id="weightrows" style="display:grid;gap:14px"></div>
      </section>

      <section class="card" id="numbersCard">
        <h2>Numbers on a stat screen</h2>
        <p class="sub">The same font file with proportional numbers (default) and tabular numbers (<code>tnum</code>). Tabular digits keep each column steady when values change.</p>
        <div class="number-grid">
          <div class="number-panel"><h3>tnum off · proportional</h3>
            <div class="stat-line"><span>Energy</span><strong>1,111</strong></div>
            <div class="stat-line"><span>Power</span><strong>8,888</strong></div>
            <div class="stat-line"><span>Health</span><strong>4,090</strong></div>
          </div>
          <div class="number-panel tabular"><h3>tnum on · equal-width figures</h3>
            <div class="stat-line"><span>Energy</span><strong>1,111</strong></div>
            <div class="stat-line"><span>Power</span><strong>8,888</strong></div>
            <div class="stat-line"><span>Health</span><strong>4,090</strong></div>
          </div>
        </div>
        <div class="number-samples" aria-label="Superscript, subscript, and fraction examples">
          <span>x<span class="feature-sups">2</span> · x²</span>
          <span>H<span class="feature-subs">2</span>O · H₂O</span>
          <span>½ · ¼ · ¾</span>
          <span class="feature-frac">1/2 · 12/34</span>
        </div>
      </section>

      <section class="card">
        <h2>Spacing close-up</h2>
        <div class="hint" id="lbiglabel" style="margin-bottom:4px"></div>
        <div id="lbig"></div>
        <div class="hint" id="pbiglabel" style="margin:14px 0 4px"></div>
        <div id="pbig"></div>
      </section>

      <section class="card">
        <h2>Every character</h2>
        <div id="allchars" style="display:grid;gap:8px"></div>
      </section>

      <section class="card" id="langCard">
        <h2>Languages</h2>
        <div id="langs" style="display:grid;gap:12px"></div>
      </section>

      <section class="card">
        <h2>Type anything</h2>
        <p class="sub" style="margin-bottom:8px">Put words between stars for italic, like *this*.</p>
        <input type="text" id="txt" value="Ⓢ SEIHouse · ♫ Now playing ⏮ ▶ ⏭ · 🎧 Listen · 📖 Read · ☯ Qi +120 ▲, *after the flying sword*" maxlength="120" autocomplete="off" spellcheck="false" aria-label="Test text">
        <div id="typed" style="display:grid;gap:8px;margin-top:12px"></div>
      </section>

      <section class="card" id="comments">
        <h2>Comments with custom emojis (demo)</h2>
        <p class="sub">Type <b>:</b> and a few letters (try <b>:cul</b> or <b>:fire</b>) or use the emoji button. The comment saves plain text like <b>:cultivator:</b>, and the app swaps it for the image when showing it. Comments here are just for trying it out and aren’t saved.</p>
        <div class="row" style="margin-bottom:4px">
          <button type="button" class="pill" id="anim" aria-pressed="true">Animated emojis</button>
          <span class="hint" style="margin-left:6px">Comment weight</span>
          <span class="row" id="cmw" role="group" aria-label="Comment text weight"></span>
        </div>
        <div class="cm-list" id="cmlist" aria-live="polite"></div>
        <div class="compose">
          <label for="cmbox" class="hint">Write a comment</label>
          <textarea id="cmbox" placeholder="That breakthrough scene :breakthrough:"></textarea>
          <div class="sugg" id="sugg" aria-label="Emoji suggestions"></div>
          <div class="row">
            <button type="button" class="pill" id="pickbtn" aria-expanded="false" aria-controls="picker">Emojis</button>
            <button type="button" class="pill primary" id="post">Post</button>
          </div>
          <div class="picker" id="picker" hidden></div>
        </div>
        <details style="margin-top:14px">
          <summary>The emoji list (what your app keeps for each emoji)</summary>
          <div class="reg" id="reg" tabindex="0"></div>
        </details>
      </section>
    </div>
  </div>
</div>
<script>
__ENGINE__
</script>
<script>
/* ---------------- page ---------------- */
const SR_BAKED = __BAKED__;
const SR_KERN = __KERN__;
const SR_STYLE_KERN = __STYLE_KERN__;
const SR_CHARS = [...__CHARS__];
const SR_CHAPTER = __CHAPTER__;
const SR_REVIEW = `“Lian,” Iñés said. "Entry" was written beside the blade; Mei's acquittal waited.`;
const SR_RHYTHM = `minimum · murmur · river · climate · parallel · everywhere. *minimum · murmur · river · climate · parallel · everywhere.*`;
const SR_TEXTURE = `“Mei’s,” Iñés said: “Entry 12? I counted 312 steps; you counted 314.” 0123456789 · 1,234.56 · 8.50% · ½ ¼ ¾. *“Wait… don’t!” Was it 6, 8, or 9?*`;
const SR_FONTS = __FONTLIST__;
const WORDER = __WORDER__;
const $ = id => document.getElementById(id);
const e_ = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));

/* current settings */
const S_ = {};
function loadInto(src){
  S_.weight = src.weight; S_.xHeight = src.xHeight; S_.lowercaseRoundness = src.lowercaseRoundness;
  S_.capitalRoundness = src.capitalRoundness; S_.letterWidth = src.letterWidth;
  S_.spaceBetweenAllLetters = src.spaceBetweenAllLetters; S_.wordSpace = src.wordSpace;
  S_.overshoot = src.overshoot !== false; S_.uFoot = src.uFoot !== false;
  S_.weights = Object.assign({}, SR_BAKED.weights, src.weights || {}); S_.weights.Regular = S_.weight;
  S_.letterSpace = JSON.parse(JSON.stringify(src.letterSpace || {}));
  S_.pairSpace = JSON.parse(JSON.stringify(src.pairSpace || {}));
}
loadInto(SR_BAKED);
const PRESET_06 = { weight:108, xHeight:550, lowercaseRoundness:0.5, capitalRoundness:210, letterWidth:1,
  spaceBetweenAllLetters:9.4, wordSpace:250, overshoot:false, uFoot:false, letterSpace:{}, pairSpace:{} };
PRESET_06.weights = Object.assign({}, SR_BAKED.weights, { Regular:108 });
const RD = Object.assign({ size:18, lh:1.55, measure:62, night:false, view:'live' }, __READER__);

const FONT_CTL = [
  { k:'xHeight',            label:'Lowercase height',        min:460, max:580, step:2,    fmt:v=>v },
  { k:'lowercaseRoundness', label:'Lowercase roundness',     min:0,   max:1,   step:0.05, fmt:v=>(+v).toFixed(2) },
  { k:'capitalRoundness',   label:'Capital corner roundness',min:80,  max:260, step:5,    fmt:v=>v },
  { k:'letterWidth',        label:'Letter width',            min:0.85,max:1.15,step:0.01, fmt:v=>Math.round(v*100)+'%' },
];
const SPACE_CTL = [
  { k:'spaceBetweenAllLetters', label:'Space between letters', min:-15, max:35,  step:0.2, fmt:v=>(+v).toFixed(1).replace(/\.0$/,'') },
  { k:'wordSpace',              label:'Space between words',   min:150, max:400, step:5, fmt:v=>v },
];
const READ_CTL = [
  { k:'size',    label:'Text size',     min:14,  max:24,  step:1,    fmt:v=>v+'px' },
  { k:'lh',      label:'Line spacing',  min:1.3, max:2.0, step:0.05, fmt:v=>(+v).toFixed(2) },
  { k:'measure', label:'Line length',   min:40,  max:80,  step:1,    fmt:v=>v+' letters' },
];

function slider(c, val, id){
  return `<label class="ctl"><span class="cl">${c.label} <output id="o-${id}">${c.fmt(val)}</output></span>
    <input type="range" id="r-${id}" min="${c.min}" max="${c.max}" step="${c.step}" value="${val}"></label>`;
}
function buildControls(){
  $('fontctl').innerHTML = FONT_CTL.map(c => slider(c, S_[c.k], c.k)).join('');
  $('spacectl').innerHTML = SPACE_CTL.map(c => slider(c, S_[c.k], c.k)).join('');
  $('readctl').innerHTML = READ_CTL.map(c => slider(c, RD[c.k], c.k)).join('');
  for(const c of [...FONT_CTL, ...SPACE_CTL]){ if(!$('r-'+c.k)) continue;
    $('r-'+c.k).addEventListener('input', ev => { S_[c.k] = +ev.target.value; $('o-'+c.k).textContent = c.fmt(S_[c.k]); if(c.k === 'weight'){ S_.weights.Regular = S_.weight; const rr = $('rw-Regular'); if(rr){ rr.value = S_.weight; $('ow-Regular').textContent = S_.weight; } } changed(true); });
  }
  for(const c of READ_CTL){
    $('r-'+c.k).addEventListener('input', ev => { RD[c.k] = +ev.target.value; $('o-'+c.k).textContent = c.fmt(RD[c.k]); changed(false); });
  }
}

/* push settings into the drawing rules */
let lastKey = '';
function applyToEngine(){
  const key = [S_.weight,S_.xHeight,S_.lowercaseRoundness,S_.capitalRoundness,S_.letterWidth,S_.overshoot,S_.uFoot].join('|');
  if(key !== lastKey){ for(const k in cache) delete cache[k]; lastKey = key; }
  P.base = S_.weight; P.round = S_.lowercaseRoundness; P.xh = S_.xHeight; P.caprx = S_.capitalRoundness; P.ws = S_.letterWidth; P.contrast = SR_BAKED.contrast; P.straight = SR_BAKED.uprightStraightness; P.asc = SR_BAKED.ascender; P.os = S_.overshoot ? 1 : 0; P.ufoot = S_.uFoot ? 1 : 0;
}
const bm = c => (ACC[c] ? ACC[c].base : c);
/** Resolve user overrides before the nearest baked weight and italic pair map. */
function pairVal(k, thick=S_.weight, italic=false){
  if(S_.pairSpace[k] !== undefined) return S_.pairSpace[k];
  const kb = [...k].map(bm).join('');
  if(S_.pairSpace[kb] !== undefined) return S_.pairSpace[kb];
  const name = Object.keys(SR_BAKED.weights).reduce((best, n) => Math.abs(SR_BAKED.weights[n]-thick) < Math.abs(SR_BAKED.weights[best]-thick) ? n : best);
  const style = italic ? (name === 'Regular' ? 'Italic' : name+'Italic') : name;
  return (SR_STYLE_KERN[style] || SR_KERN)[kb] || 0;
}

/* draw one word from the rules, spaced exactly like the font file will be */
/* thick and thin: draw each letter tall, then squash it back, so horizontal strokes come out thinner (same as the font build) */
function thickThin(g){
  const F = P.contrast || 1;
  if(F === 1) return g.body;
  if(g._tt && g._ttF === F) return g._tt;
  let body = g.body.replace(/ d="([^"]+)"/g, (m, d) => { let i = 0; return ' d="' + d.replace(/-?\d+(?:\.\d+)?/g, n => (i++ % 2 ? (+n * F).toFixed(1) : n)) + '"'; });
  body = body.replace(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g, (m, cx, cy, r) => `<ellipse cx="${cx}" cy="${(+cy * F).toFixed(1)}" rx="${r}" ry="${(+r * F).toFixed(1)}"`);
  g._tt = `<g transform="scale(1 ${(1/F).toFixed(5)})">${body}</g>`; g._ttF = F;
  return g._tt;
}
/** Draw one word with the selected real italic forms and per-style pair spacing. */
function drawWord(w, size, thick, ital){
  const Sw = thick || S_.weight, reg = S_.weights.Regular;
  const prevIt = P.ital; let itc = !!ital;
  const T9 = Math.tan(9 * Math.PI / 180);
  const tr = S_.spaceBetweenAllLetters + (Sw - reg) * (Sw > reg ? 0.25 : 0.1);
  let x = 0, parts = '', prev = '';
  w = w.replace(/fi/g, 'ﬁ').replace(/fl/g, 'ﬂ');     // joined fi / fl, like the font does
  for(const ch of w){
    if(ch === '\u2063'){ itc = !itc; continue; }   // italic on/off marker (made from a pair of *stars*)
    P.ital = itc ? 1 : 0;
    P.trk = tr + (itc ? 4 : 0);
    const g = glyph(ch, Sw);
    if(!g){ x += 420; prev = ''; continue; }
    const o = S_.letterSpace[ch] || S_.letterSpace[bm(ch)] || {};
    const before = o.before || 0, after = o.after || 0;
    x += pairVal(prev + ch, Sw, itc);
    const tri = tr + (itc ? 4 : 0);
    const gx = x + tri + g.sb0 + before - (itc ? T9 * 330 : 0);
    parts += `<g transform="translate(${f1(gx)} 0)${itc ? ' skewX(-9)' : ''}" clip-path="url(#${g.clipId})">${thickThin(g)}</g>`;
    x += tri + g.sb0 + before + g.w + Sw + g.sb1 + after + tri;
    prev = ch;
  }
  P.ital = prevIt;
  const W = Math.max(x, 1);
  return `<svg aria-hidden="true" focusable="false" viewBox="0 -900 ${f1(W)} 1160" width="${f1(W*size/1000)}" height="${f1(1.16*size)}">${parts}</svg>`;
}
function drawText(str, size, lh, thick){
  str = str.replace(/\*([^*\n]+?)\*/g, '\u2063$1\u2063');   // only a matched pair of stars means italic; a lone * stays an asterisk
  const words = []; let it = false;
  for(const w of str.split(/\s+/).filter(Boolean)){ words.push([w, it]); if((w.split('\u2063').length - 1) % 2) it = !it; }
  str = str.replace(/\u2063/g, '');
  const col = size * S_.wordSpace / 1000, row = Math.max(0, size * (lh - 1.16));
  return `<span class="run" role="img" aria-label="${e_(str)}" style="gap:${f1(row)}px ${f1(col)}px">${words.map(([w, i]) => drawWord(w, size, thick, i)).join('')}</span>`;
}

/* Reader Chamber */
/** Refresh the reader sample in the selected live or exported-font view. */
function renderChamber(){
  const ch = $('chamber'), inner = $('chamberInner');
  ch.classList.toggle('night', RD.night);
  inner.style.setProperty('--measure', RD.measure + 'ch');
  inner.style.setProperty('--rsize', RD.size + 'px');
  inner.style.setProperty('--rlh', RD.lh);
  const liveHTML = () =>
      `<div class="clabel">${drawText('Chapter 12', 13, 1.3)}</div>` +
      `<div class="title">${drawText('The Last Gate', 32, 1.25)}</div>` +
      `<div class="reviewtag">__VERSION__ REVIEW WORDS</div><div class="para reviewline">${drawText(SR_REVIEW, RD.size, RD.lh)}</div>` +
      `<div class="para reviewline">${drawText(SR_RHYTHM, RD.size, RD.lh)}</div>` +
      `<div class="para reviewline">${drawText(SR_TEXTURE, RD.size, RD.lh)}</div>` +
      SR_CHAPTER.map(p => `<div class="para">${drawText(p, RD.size, RD.lh)}</div>`).join('') +
      `<div class="cap">${drawText('4 minutes left in this chapter', 13, 1.3)}</div>`;
  const fileHTML = () => `<div class="clabel" style="font-size:13px">Chapter 12</div><div class="title" style="font-size:32px;line-height:1.25">The Last Gate</div>` +
      `<div class="reviewtag">__VERSION__ REVIEW WORDS</div><p class="reviewline" style="font-size:${RD.size}px">${e_(SR_REVIEW)}</p>` +
      `<p class="reviewline" style="font-size:${RD.size}px">${e_(SR_RHYTHM).replace(/\*([^*]+)\*/g, '<i>$1</i>')}</p>` +
      `<p class="reviewline" style="font-size:${RD.size}px">${e_(SR_TEXTURE).replace(/\*([^*]+)\*/g, '<i>$1</i>')}</p>` +
      SR_CHAPTER.map(p => `<p style="font-size:${RD.size}px">${e_(p).replace(/\*([^*]+)\*/g, '<i>$1</i>')}</p>`).join('') +
      `<div class="cap" style="font-size:13px">4 minutes left in this chapter</div>`;
  if(RD.view === 'side'){
    inner.className = 'inner side';
    inner.style.setProperty('--measure', 'none');
    inner.innerHTML = `<div><div class="sidelabel">YOUR SETTINGS</div>${liveHTML()}</div>` +
      `<div class="inner filemode f-old"><div class="sidelabel" style="font-family:system-ui,sans-serif">0.6 FONT FILE</div>${fileHTML()}</div>`;
  } else if(RD.view === 'live'){
    inner.className = 'inner';
    inner.innerHTML = liveHTML();
  } else {
    inner.className = 'inner filemode ' + (RD.view === 'old' ? 'f-old' : 'f-new');
    inner.innerHTML = fileHTML();
  }
}
function renderAllChars(){
  const rows = ['ABCDEFGHIJKLM NOPQRSTUVWXYZ','abcdefghijklm nopqrstuvwxyz','0123456789 Il1 O0o bd pq nu',". , : ; … ! ? ' \" ‘ ’ “ ” - – — ( ) [ ] / % + =",
    '⁰¹²³⁴⁵⁶⁷⁸⁹', '₀₁₂₃₄₅₆₇₈₉', '½ ¼ ¾ ⁄',
    "& @ # $ * ~ _ | \\ { } < >", '★ • · × ÷ ± ° → ← ∞ « » ‹ › ¥ € £',
    '☯ ⚡ ☀ ☾ ☽ ⚔ ✦ ☆ ◆ ◇ ▲ ▼ ▶ ◀ ↑ ↓', '♥ ♡ ✓ ✗ ♪ © ® ™ − ≤ ≥ ≠ ≈',
    'Ⓢ ♩ ♪ ♫ ♬ ♭ ♮ ♯ ⏮ ▶ ⏸ ⏹ ⏺ ⏭', '🎧 💻 📖 🔖 🔍 🔔 ⚙ ⌂ 🎤 💿 🔊',
    'ÀÁÂÃÄÅ Ç ÈÉÊË ÌÍÎÏ Ñ ÒÓÔÕÖØ ÙÚÛÜ ÝŸ ÆŒ ÐÞ', 'àáâãäå ç èéêë ìíîï ñ òóôõöø ùúûü ýÿ æœ ß ðþ ¡¿ ºª',
    '*àáâãäå ç èéêë ìíîï ñ òóôõöø ùúûü ýÿ æœ ß ðþ*',
    '*ABCDEFGHIJKLM NOPQRSTUVWXYZ*', '*abcdefghijklm nopqrstuvwxyz*', '*0123456789 . , : ; ! ? “ ” ( )*', '*& @ # $ ~ { } < > ★ • → ¥ € £*'];
  const sz = window.innerWidth > 700 ? 34 : 24;
  $('allchars').innerHTML = rows.map(r => drawText(r, sz, 1.3)).join('');
}
function renderTyped(){
  const t = $('txt').value.trim() || 'The Last Gate';
  $('typed').innerHTML = [40, 18, 14].map(s => drawText(t, s, 1.35)).join('');
}

/* one letter */
let sel = 'a';
function context(c){ if(/[A-Z0-9]/.test(c)) return `HH${c}HH OO${c}OO`; if(/[a-z]/.test(c)) return `nn${c}nn oo${c}oo`; return `n${c}n o${c}o`; }
function renderLetters(){
  $('letters').innerHTML = SR_CHARS.map(c => {
    const o = S_.letterSpace[c]; const ch = o && (o.before || o.after);
    return `<button type="button" data-ch="${e_(c)}" aria-label="Letter ${e_(c)}" aria-pressed="${c === sel}" class="${ch ? 'changed' : ''}">${e_(c)}</button>`;
  }).join('');
  $('letters').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { sel = b.dataset.ch; renderLetters(); renderLetterPanel(); }));
}
function renderLetterPanel(){
  const o = S_.letterSpace[sel] || { before:0, after:0 };
  $('letterpanel').innerHTML = `
    <div class="grp0">
      <label class="ctl"><span class="cl">Space before <output id="ol">${o.before||0}</output></span><input type="range" id="sl-l" min="-60" max="80" step="1" value="${o.before||0}"></label>
      <label class="ctl"><span class="cl">Space after <output id="or">${o.after||0}</output></span><input type="range" id="sl-r" min="-60" max="80" step="1" value="${o.after||0}"></label>
    </div>
    <div class="row"><button type="button" class="pill" id="resetletter">Reset this letter</button></div>`;
  const show = () => { $('lbiglabel').textContent = 'One letter: ' + sel; $('lbig').innerHTML = drawText(context(sel), window.innerWidth > 700 ? 64 : 40, 1.2); };
  show();
  const upd = () => {
    const b = +$('sl-l').value, a = +$('sl-r').value;
    if(b || a) S_.letterSpace[sel] = { before:b, after:a }; else delete S_.letterSpace[sel];
    $('ol').textContent = b; $('or').textContent = a; show(); markLetters(); changed(true, true);
  };
  $('sl-l').addEventListener('input', upd); $('sl-r').addEventListener('input', upd);
  $('resetletter').addEventListener('click', () => { delete S_.letterSpace[sel]; renderLetterPanel(); markLetters(); changed(true, true); });
}
function markLetters(){ document.querySelectorAll('#letters button').forEach(b => { const o = S_.letterSpace[b.dataset.ch]; b.classList.toggle('changed', !!(o && (o.before || o.after))); }); }

/* pairs */
let pa = 'r', pb = 'n';
function renderPairPanel(){
  const k = pa + pb;
  $('pairpanel').innerHTML = `
    <div class="pairin">
      <label>First<input type="text" id="pa" maxlength="2" value="${e_(pa)}" aria-label="First letter"></label>
      <label>Second<input type="text" id="pb" maxlength="2" value="${e_(pb)}" aria-label="Second letter"></label>
    </div>
    <label class="ctl"><span class="cl">Space between ${e_(pa)} and ${e_(pb)} <output id="pv">${pairVal(k)}</output></span>
      <input type="range" id="sl-p" min="-80" max="80" step="1" value="${pairVal(k)}"></label>
    <div class="row"><button type="button" class="pill" id="resetpair">Reset this pair</button></div>`;
  const show = () => { $('pbiglabel').textContent = 'Two letters: ' + k; $('pbig').innerHTML = drawText(`${k} ${k} n${k}n o${k}o`, window.innerWidth > 700 ? 56 : 36, 1.2); };
  show();
  $('pa').addEventListener('change', ev => { const v = [...ev.target.value].pop(); if(v){ pa = v; renderPairPanel(); } });
  $('pb').addEventListener('change', ev => { const v = [...ev.target.value].pop(); if(v){ pb = v; renderPairPanel(); } });
  $('pa').addEventListener('input', ev => { const v = [...ev.target.value].pop(); if(v && v !== pa){ pa = v; renderPairPanel(); $('pa').focus(); } });
  $('pb').addEventListener('input', ev => { const v = [...ev.target.value].pop(); if(v && v !== pb){ pb = v; renderPairPanel(); $('pb').focus(); } });
  $('sl-p').addEventListener('input', ev => {
    const v = +ev.target.value;
    if(v === (SR_KERN[k] || 0)) delete S_.pairSpace[k]; else S_.pairSpace[k] = v;
    $('pv').textContent = v; show(); changed(true, true);
  });
  $('resetpair').addEventListener('click', () => { delete S_.pairSpace[k]; renderPairPanel(); changed(true, true); });
}

/* switches and presets */
function syncToggles(){
  $('t-os').setAttribute('aria-pressed', String(S_.overshoot));
  $('t-u').setAttribute('aria-pressed', String(S_.uFoot));
}
$('t-os').addEventListener('click', () => { S_.overshoot = !S_.overshoot; syncToggles(); changed(true); });
$('t-u').addEventListener('click', () => { S_.uFoot = !S_.uFoot; syncToggles(); changed(true); });
function startFrom(src, label){
  loadInto(src); buildControls(); syncToggles(); renderWeightRows(); renderLetters(); renderLetterPanel(); renderPairPanel(); changed(true);
  setSaveMsg('Started from ' + label + '. Press Save to keep it.');
}
$('p-file').addEventListener('click', () => startFrom(SR_BAKED, 'the font file'));
$('p-06').addEventListener('click', () => startFrom(PRESET_06, '0.6'));
function renderDiff(){
  const d = [];
  const near = (a,b) => Math.abs(a-b) < 1e-6;
  if(!near(S_.weight, PRESET_06.weight)) d.push(`thickness ${S_.weight} (0.6: ${PRESET_06.weight})`);
  if(!near(S_.xHeight, PRESET_06.xHeight)) d.push(`lowercase height ${S_.xHeight} (0.6: ${PRESET_06.xHeight})`);
  if(!near(S_.lowercaseRoundness, PRESET_06.lowercaseRoundness)) d.push(`lowercase roundness ${S_.lowercaseRoundness} (0.6: 0.5)`);
  if(!near(S_.capitalRoundness, PRESET_06.capitalRoundness)) d.push(`capital corners ${S_.capitalRoundness} (0.6: 210)`);
  if(!near(S_.letterWidth, 1)) d.push(`letter width ${Math.round(S_.letterWidth*100)}% (0.6: 100%)`);
  if(Math.abs(S_.spaceBetweenAllLetters - 9.4) > 0.05) d.push(`space between letters ${S_.spaceBetweenAllLetters} (0.6: 9.4)`);
  if(!near(S_.wordSpace, 250)) d.push(`space between words ${S_.wordSpace} (0.6: 250)`);
  if(S_.overshoot) d.push('round letters a touch taller (0.6: off)');
  if(S_.uFoot) d.push('u with foot (0.6: off)');
  const n = Object.keys(S_.letterSpace).length + Object.keys(S_.pairSpace).length;
  if(n) d.push(`${n} letter or pair spacing changes`);
  $('diff').innerHTML = d.length ? '<b>Different from 0.6:</b> ' + d.map(e_).join('; ') + '.' : '<b>Same as 0.6.</b>';
}

/* what gets saved */
function payload(){
  return {
    weight:S_.weight, xHeight:S_.xHeight, lowercaseRoundness:S_.lowercaseRoundness, capitalRoundness:S_.capitalRoundness,
    weights:S_.weights,
    letterWidth:S_.letterWidth, spaceBetweenAllLetters:S_.spaceBetweenAllLetters, wordSpace:S_.wordSpace,
    overshoot:S_.overshoot, uFoot:S_.uFoot,
    letterSpace:S_.letterSpace, pairSpace:S_.pairSpace,
    reader:{ size:RD.size, lineSpacing:RD.lh, lineLength:RD.measure, night:RD.night }
  };
}
function renderOut(){ renderDiff(); $('outtext').textContent = 'SEIReader settings\n' + JSON.stringify(payload()); }

let raf = 0, dirty = false;
function changed(font, skipPanels){
  if(font){ dirty = true; setSaveMsg('Not saved yet'); if(RD.view === 'file' || RD.view === 'old') setView('live'); }
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(() => {
    applyToEngine();
    renderChamber();
    if(font){ renderAllChars(); renderTyped(); drawWeightSamples(); renderLangs(); if(typeof renderComments === 'function') renderComments(); if(!skipPanels){ renderLetterPanel(); renderPairPanel(); } }
    renderOut();
  });
}

/* view, mode */
function setView(v){
  RD.view = v;
  [['v-live','live'],['v-file','file'],['v-old','old'],['v-side','side']].forEach(([id,val]) => $(id).setAttribute('aria-pressed', String(v === val)));
  renderChamber();
}
$('v-live').addEventListener('click', () => setView('live'));
$('v-file').addEventListener('click', () => setView('file'));
$('v-old').addEventListener('click', () => setView('old'));
$('v-side').addEventListener('click', () => setView('side'));
$('m-day').addEventListener('click', () => { RD.night = false; $('m-day').setAttribute('aria-pressed','true'); $('m-night').setAttribute('aria-pressed','false'); changed(false); });
$('m-night').addEventListener('click', () => { RD.night = true; $('m-night').setAttribute('aria-pressed','true'); $('m-day').setAttribute('aria-pressed','false'); changed(false); });
$('txt').addEventListener('input', renderTyped);
$('togglectl').addEventListener('click', () => {
  const c = $('controls'), col = c.classList.toggle('collapsed');
  $('togglectl').textContent = col ? 'Show controls' : 'Hide controls';
  $('togglectl').setAttribute('aria-expanded', String(!col));
});
$('reset').addEventListener('click', () => {
  loadInto(SR_BAKED); buildControls(); syncToggles(); renderWeightRows(); renderLetters(); renderLetterPanel(); renderPairPanel(); changed(true);
  setSaveMsg('Back to the font file’s settings. Press Save to keep this.');
});
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('outtext').textContent); setSaveMsg('Copied. Paste it into the chat.'); }
  catch(e){ setSaveMsg('Could not copy automatically. Select the text and copy it.'); }
});
function setSaveMsg(t){ $('savemsg').textContent = t; }

/* saving, so Claude can read it */
let DB = null;
const DOC = 'seireader/settings';
async function connect(){
  try { DB = await claude.use('db'); } catch(e){ DB = null; }
  if(!DB){ setSaveMsg('Saving isn’t available here. Use “Copy instead of Save” in the settings.'); return; }
  $('save').disabled = false;
  try {
    const snap = await DB.doc(DOC).get();
    if(snap.exists){
      const d = snap.data();
      if(d && d.settings){
        loadInto({ ...SR_BAKED, ...d.settings });
        if(d.settings.reader){ const r = d.settings.reader; RD.size = r.size ?? RD.size; RD.lh = r.lineSpacing ?? RD.lh; RD.measure = r.lineLength ?? RD.measure; RD.night = !!r.night;
          $('m-night').setAttribute('aria-pressed', String(RD.night)); $('m-day').setAttribute('aria-pressed', String(!RD.night)); }
        buildControls(); syncToggles(); renderWeightRows(); renderLetters(); renderLetterPanel(); renderPairPanel(); changed(true);
        setSaveMsg('Loaded your saved settings' + (d.savedAt ? ' from ' + new Date(d.savedAt).toLocaleString() : '') + '.');
        dirty = false; return;
      }
    }
    setSaveMsg('Nothing saved yet.');
  } catch(e){ setSaveMsg('Could not load saved settings. You can still save.'); }
}
$('save').addEventListener('click', async () => {
  if(!DB) return;
  $('save').disabled = true; setSaveMsg('Saving…');
  try {
    await DB.doc(DOC).set({ settings: payload(), savedAt: Date.now(), fontFileVersion: '__VERSION__' });
    dirty = false; setSaveMsg('Saved. Tell Claude “build it”.');
  } catch(e){
    setSaveMsg('Save didn’t work (' + (e && e.code ? e.code : 'error') + '). Use “Copy instead of Save” in the settings.');
  }
  $('save').disabled = false;
});

/* ---------------- languages ---------------- */
const LANGS = [
  ['Español', '¿Dónde está el maestro? ¡Qué sorpresa! El niño comió piña con jalapeño.'],
  ['Français', 'Où est la bibliothèque ? L’élève a reçu un cœur plein de naïveté, déjà très âgé.'],
  ['Português', 'Não é fácil, mas a cultivação começa ao amanhecer. Ação, coração e maçã.'],
  ['Deutsch', 'Über die Straße läuft ein Bär. Größe, Übung und Schönheit für alle Jünger.'],
  ['Italiano', 'Perché è così difficile? La città più antica, però, è qui.'],
  ['Nederlands', 'Café, reünie, coördinatie en een ideeënrijk verhaal.'],
  ['Norsk · Svenska · Dansk', 'Blåbær og smørbrød på øya. Fältet är öppet. Æbler i København.'],
  ['Íslenska', 'Þetta er fræðibók um það.'],
];
function renderLangs(){
  const el = $('langs'); if(!el) return;
  el.innerHTML = LANGS.map(([n, t]) => `<div><div class="hint">${e_(n)}</div>${drawText(t, 18, 1.45)}</div>`).join('');
}

/* ---------------- weights ---------------- */
function renderWeightRows(){
  $('weightctl').innerHTML = WORDER.map(w => `
      <label class="ctl"><span class="cl"><span>${w}</span> <output id="ow-${w}">${S_.weights[w]}</output></span>
        <input type="range" id="rw-${w}" min="40" max="170" step="1" value="${S_.weights[w]}" aria-label="${w} thickness"></label>`).join('');
  $('weightrows').innerHTML = WORDER.map(w => `
    <div style="display:grid;gap:4px"><div class="hint">${w}</div><div id="dw-${w}"></div></div>`).join('');
  WORDER.forEach(w => $('rw-'+w).addEventListener('input', ev => {
    S_.weights[w] = +ev.target.value; $('ow-'+w).textContent = S_.weights[w];
    if(w === 'Regular'){ S_.weight = S_.weights.Regular; const r = $('r-weight'); if(r){ r.value = S_.weight; $('o-weight').textContent = S_.weight; } }
    changed(true);
  }));
  drawWeightSamples();
}
function drawWeightSamples(){
  WORDER.forEach(w => {
    const el = $('dw-'+w); if(!el) return;
    el.innerHTML = drawText('The Last Gate *The Last Gate*', 30, 1.2, S_.weights[w]) + drawText('Chapter 12 had me like that ending. *Why now, after a hundred years?*', 17, 1.4, S_.weights[w]);
  });
}

/* ---------------- comments + custom emojis demo ---------------- */
const EMOJI = __EMOJI__;
const EM = {}; EMOJI.forEach(e => { EM[e.name] = e; });
const svgURL = s => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s);
let animOn = !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
const emoSrc = e => svgURL(animOn ? e.anim : e.still);
const CM = [
  { who:'Mei', color:'#3fb28a', text:'Chapter 12 had me like :shock: :shock: that ending :fire:' },
  { who:'Ren', color:'#7c6cf0', text:':cultivator:' },
  { who:'Lin', color:'#c9861b', text:'Finally a real breakthrough :breakthrough: now drink the :elixir: and survive the :tribulation:' },
];
let cmWeight = WORDER.includes('Light') ? 'Light' : 'Regular';
const CM_SIZE = 17;
function renderComment(t){
  const only = t.trim().replace(/:([a-z0-9_]+):/g, (m, n) => EM[n] ? '' : m).trim() === '';
  const count = (t.match(/:([a-z0-9_]+):/g) || []).filter(m => EM[m.slice(1,-1)]).length;
  const jumbo = only && count > 0 && count <= 3;
  const eh = (jumbo ? 3 : 1.35) * CM_SIZE, thick = S_.weights[cmWeight];
  const items = [];
  for(const part of t.split(/(:[a-z0-9_]+:)/)){
    const m = part.match(/^:([a-z0-9_]+):$/);
    if(m && EM[m[1]]){ items.push(`<img class="emo" style="height:${eh}px;margin:${jumbo ? 0 : (1.16*CM_SIZE-eh)/2}px 0 0" src="${emoSrc(EM[m[1]])}" alt=":${m[1]}:" title=":${m[1]}:">`); continue; }
    for(const w of part.split(/\s+/).filter(Boolean)) items.push(drawWord(w, CM_SIZE, thick));
  }
  const col = CM_SIZE * S_.wordSpace / 1000, row = Math.max(0, CM_SIZE * (1.5 - 1.16));
  return { html: `<span class="run" role="img" aria-label="${e_(t)}" style="gap:${f1(row)}px ${f1(col)}px;align-items:${jumbo ? 'center' : 'flex-start'}">${items.join('')}</span>`, jumbo };
}
function renderCmWeights(){
  $('cmw').innerHTML = WORDER.map(w => `<button type="button" class="pill" data-w="${w}" aria-pressed="${w === cmWeight}">${w}</button>`).join('');
  $('cmw').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { cmWeight = b.dataset.w; renderCmWeights(); renderComments(); }));
}
function renderComments(){
  $('cmlist').innerHTML = CM.map(c => {
    const r = renderComment(c.text);
    return `<div class="cm"><div class="av" style="background:${c.color}" aria-hidden="true">${e_(c.who[0])}</div>
      <div><div class="who"><b>${e_(c.who)}</b> · just now</div><div class="txt${r.jumbo ? ' jumbo' : ''}">${r.html}</div></div></div>`;
  }).join('');
}
function renderPicker(){
  const packs = [...new Set(EMOJI.map(e => e.pack))];
  $('picker').innerHTML = packs.map(p => `<div><div class="hint" style="margin-bottom:6px">${e_(p)}</div><div class="grid">` +
    EMOJI.filter(e => e.pack === p).map(e => `<button type="button" class="e" data-n="${e.name}" aria-label=":${e.name}: ${e_(e.alt)}" title=":${e.name}:"><img src="${emoSrc(e)}" alt=""></button>`).join('') +
    `</div></div>`).join('');
  $('picker').querySelectorAll('button.e').forEach(b => b.addEventListener('click', () => insertEmoji(b.dataset.n, false)));
}
function insertEmoji(name, replacePartial){
  const box = $('cmbox'), pos = box.selectionStart, v = box.value;
  let start = pos;
  if(replacePartial){ const m = v.slice(0, pos).match(/:([a-z0-9_]*)$/); if(m) start = pos - m[0].length; }
  const ins = `:${name}: `;
  box.value = v.slice(0, start) + ins + v.slice(pos);
  const np = start + ins.length; box.focus(); box.setSelectionRange(np, np);
  renderSugg();
}
function renderSugg(){
  const box = $('cmbox'), m = box.value.slice(0, box.selectionStart).match(/:([a-z0-9_]{1,20})$/);
  if(!m){ $('sugg').innerHTML = ''; return; }
  const hits = EMOJI.filter(e => e.name.startsWith(m[1])).slice(0, 6);
  $('sugg').innerHTML = hits.map(e => `<button type="button" data-n="${e.name}"><img src="${svgURL(e.still)}" alt="">:${e.name}:</button>`).join('');
  $('sugg').querySelectorAll('button').forEach(b => b.addEventListener('click', () => insertEmoji(b.dataset.n, true)));
}
$('cmbox').addEventListener('input', renderSugg);
$('cmbox').addEventListener('click', renderSugg);
$('cmbox').addEventListener('keydown', ev => {
  if(ev.key === 'Tab'){ const f = $('sugg').querySelector('button'); if(f){ ev.preventDefault(); insertEmoji(f.dataset.n, true); } }
  if(ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)){ ev.preventDefault(); $('post').click(); }
});
$('post').addEventListener('click', () => {
  const t = $('cmbox').value.trim(); if(!t) return;
  CM.push({ who:'You', color:'#151922', text:t }); $('cmbox').value = ''; renderSugg(); renderComments();
});
$('pickbtn').addEventListener('click', () => {
  const p = $('picker'); p.hidden = !p.hidden; $('pickbtn').setAttribute('aria-expanded', String(!p.hidden));
});
$('anim').setAttribute('aria-pressed', String(animOn));
$('anim').addEventListener('click', () => { animOn = !animOn; $('anim').setAttribute('aria-pressed', String(animOn)); renderComments(); renderPicker(); });
renderCmWeights();
$('reg').textContent = JSON.stringify(EMOJI.map(e => ({ name:e.name, pack:e.pack, alt:e.alt, still:e.name + '.svg', animated:e.name + '-animated.svg', unlock:'free' })), null, 2);
renderComments(); renderPicker();

/* load fonts for the comparison views */
Promise.all(SR_FONTS.map(async f => {
  const face = new FontFace(f.name, `url(data:font/woff2;base64,${f.data})`, { weight:f.weight, style:f.style });
  await face.load(); document.fonts.add(face);
})).then(() => { $('status').textContent = 'Ready'; })
  .catch(() => { $('status').textContent = 'Font files did not load'; $('status').className = 'badge bad'; });

buildControls(); syncToggles(); renderLetters(); renderLetterPanel(); renderPairPanel();
applyToEngine(); renderWeightRows(); renderLangs(); renderChamber(); renderAllChars(); renderTyped(); renderOut();
if(window.claude && typeof window.claude.use === 'function') connect(); else setSaveMsg('Saving isn’t available here. Use “Copy instead of Save” in the settings.');
let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => changed(true), 200); });
</script>
</body>
</html>
'''
html = (html.replace('__ENGINE__', ENGINE)
            .replace('__BAKED__', json.dumps(BAKED, ensure_ascii=False))
            .replace('__KERN__', json.dumps(kern, ensure_ascii=False))
            .replace('__STYLE_KERN__', json.dumps(style_kern, ensure_ascii=False))
            .replace('__CHARS__', json.dumps(CHARS, ensure_ascii=False))
            .replace('__CHAPTER__', json.dumps(CHAPTER, ensure_ascii=False))
            .replace('__FONTLIST__', json.dumps(FONTLIST)).replace('__WORDER__', json.dumps(WORDER)).replace('__VERSION__', VERSION)
            .replace('__EMOJI__', json.dumps(EMOJI, ensure_ascii=False))
            .replace('__READER__', json.dumps({ 'size': settings.get('reader',{}).get('size',18), 'lh': settings.get('reader',{}).get('lineSpacing',1.55), 'measure': settings.get('reader',{}).get('lineLength',62), 'night': settings.get('reader',{}).get('night',False) })))
out = os.environ.get('LAB_OUT', os.path.join(HERE, 'lab', 'index.html'))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print('page', len(html))
