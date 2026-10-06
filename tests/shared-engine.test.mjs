import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const source = readFileSync(new URL('engine.js', root), 'utf8');
const tail = readFileSync(new URL('export_tail.js', root), 'utf8');
const settings = JSON.parse(readFileSync(new URL('settings.json', root), 'utf8'));
const historicalFixture = JSON.parse(readFileSync(new URL('tests/fixtures/reader-engine-0.35.json', root), 'utf8'));
const historicalInventory = JSON.parse(readFileSync(new URL('tests/fixtures/reader-engine-0.35-inventory.json', root), 'utf8'));
const currentFixture = JSON.parse(readFileSync(new URL('tests/fixtures/reader-engine-0.39.json', root), 'utf8'));
/** Evaluate drawing and export code without a browser or persistent glyph cache. */
function engine(code = source, options = {}) {
  const document = {getElementById:() => ({insertAdjacentHTML(){}})};
  const context = vm.createContext({document});
  context.window = context;
  vm.runInContext(code + '\n' + tail, context);
  vm.runInContext(`Object.assign(P, ${JSON.stringify(options)})`, context);
  return expression => vm.runInContext(expression, context);
}
/** Capture all encoded and alternate exports for the ten published Reader styles. */
function readerExports(code, inventory = null) {
  const styles = {};
  for(const italic of [false, true]) for(const [style, weight] of Object.entries(settings.weights)) {
    const options = {round:settings.lowercaseRoundness, contrast:settings.contrast,
      xh:settings.xHeight, caprx:settings.capitalRoundness, ws:settings.letterWidth,
      base:weight, os:+settings.overshoot, ufoot:+settings.uFoot, ital:+italic,
      straight:settings.uprightStraightness, asc:settings.ascender,
      trk:settings.spaceBetweenAllLetters + (weight-settings.weight)*(weight>settings.weight ? .25 : .1) + (italic ? 4 : 0)};
    const evaluate = engine(code, options);
    let result = evaluate(`JSON.stringify({glyphs:exportGlyphs(${weight}), alternates:exportAlternates(${weight}),
      kern:getKern(), basemap:getBaseMap(), screenStroke:readingStroke(${weight})})`);
    const record = JSON.parse(result), name = italic ? style==='Regular' ? 'Italic' : style+'Italic' : style;
    if(inventory) {
      for(const [field, keys] of Object.entries(inventory.fields)) {
        record[field] = Object.fromEntries(keys.map(key => [key,record[field][key]]));
      }
      result = JSON.stringify(record);
    }
    styles[name] = {glyphs:Object.keys(record.glyphs).length, alternates:Object.keys(record.alternates).length,
      sha256:createHash('sha256').update(result).digest('hex')};
  }
  return styles;
}

test('all ten Reader styles retain their historical 0.35 glyph exports and metrics', () => {
  assert.deepEqual(settings, historicalFixture.settings, 'Reader settings must remain unchanged');
  assert.deepEqual(readerExports(source, historicalInventory), historicalFixture.styles);
});

test('all ten Reader styles retain complete current 0.39 engine exports', () => {
  assert.deepEqual(settings, currentFixture.settings, 'Reader settings must remain unchanged');
  assert.deepEqual(readerExports(source), currentFixture.styles);
});

test('Display shape options change construction and remain in the glyph cache key', () => {
  const evaluate = engine(source, {caprx:240, contrast:2.6, base:135});
  const round = evaluate('glyph("E",135).body');
  evaluate('P.corner="cut";P.cap="flat";P.join="sharp";P.penAngle=32');
  const cut = evaluate('glyph("E",135).body');
  assert.notEqual(cut, round);
  assert.ok(cut.includes('stroke-linecap="butt"'));
  assert.ok(cut.includes('stroke-linejoin="miter" stroke-miterlimit="2"'));
  evaluate('P.corner="soft";P.cap="round";P.join="round";P.penAngle=0');
  assert.equal(evaluate('glyph("E",135).body'), round);
});

test('oblique slant retains upright letter skeletons and metrics', () => {
  const evaluate = engine(source, {ital:0, obliqueAngle:0});
  const upright = evaluate('JSON.stringify(exportGlyphs(135))');
  const word = evaluate('word("afuy",400,false)');
  evaluate('P.obliqueAngle=8');
  assert.equal(evaluate('JSON.stringify(exportGlyphs(135))'), upright);
  assert.notEqual(evaluate('word("afuy",400,false)'), word);
  assert.ok(evaluate('word("afuy",400,false)').includes('skewX(-8)'));
  assert.equal(evaluate('P.ital'), 0);
});

test('late language marks and alternates inherit Display ends and joins', () => {
  const evaluate = engine(source, {cap:'flat',join:'sharp',penAngle:32,contrast:2.6});
  for(const ch of ['\u0301','\u0312','ď','Ű','ị','ģ','Ж','Ά','Ự','i.dotless','zero.tf','zero.numr']) {
    const body = evaluate(`glyph(${JSON.stringify(ch)},135).body`);
    assert.ok(body.includes('stroke-linecap="butt"'), ch);
    assert.ok(body.includes('stroke-miterlimit="2"'), ch);
  }
  assert.equal(evaluate('Object.keys(exportGlyphs(135)).length'), currentFixture.styles.Regular.glyphs);
  assert.equal(evaluate('Object.keys(exportAlternates(135)).length'), currentFixture.styles.Regular.alternates);
  assert.equal(evaluate('glyph("\\u0301",135).w'), -135);
});

test('all four Display cuts construct every encoded and alternate live outline', () => {
  const helper = readFileSync(new URL('display/stroke_geometry.js', root), 'utf8');
  for(const name of ['soft','edge','ink','wide']) {
    const cut = JSON.parse(readFileSync(new URL(`display/cuts/${name}.json`, root), 'utf8'));
    const options = {base:cut.weight, round:cut.lowercaseRoundness, contrast:cut.contrast,
      xh:cut.xHeight, caprx:cut.capitalRoundness, ws:cut.letterWidth, os:+cut.overshoot,
      ufoot:+cut.uFoot, straight:cut.uprightStraightness, asc:cut.ascender,
      trk:cut.spaceBetweenAllLetters, ital:0, corner:cut.corners, cap:cut.ends,
      join:cut.joins, penAngle:cut.penAngle, obliqueAngle:cut.slant};
    const evaluate = engine(source+'\n'+helper, options);
    evaluate(`P.contrast=displayContrast(${cut.weight},${cut.contrast},${cut.xHeight},${JSON.stringify(cut.ends)})`);
    const result = evaluate(`(() => {
      const cut=${JSON.stringify(cut)}, names=Object.keys(G).concat(Object.keys(exportAlternates(${cut.weight})));
      cut.contrast=P.contrast;
      return names.map(ch => [ch, displayPenBody(glyph(ch,${cut.weight}), cut)]);
    })()`);
    assert.equal(result.length, currentFixture.styles.Regular.glyphs+currentFixture.styles.Regular.alternates, name);
    for(const [ch, body] of result) assert.ok(!/NaN|Infinity|undefined/.test(body), name+' '+ch);
  }
});

test('Display counter compensation retains stem weight and respects existing thin pens', () => {
  const evaluate = engine();
  assert.equal(evaluate('displayContrast(150,1,520)'), 150/104);
  assert.equal(evaluate('displayContrast(115,1,520,"flat")'), 115/78);
  assert.equal(evaluate('displayContrast(135,2.6,520,"flat")'), 2.6);
  assert.equal(evaluate('displayContrast(55,1,470)'), 1);
  evaluate('P.contrast=displayContrast(150,1,520);P.xh=520;P.ws=1.05');
  const glyph = JSON.parse(evaluate('JSON.stringify(exportGlyphs(150).a)'));
  assert.ok(glyph.paths.every(path => path.w === 150), 'full vertical stem thickness retained');
  assert.equal(glyph.w, 395*1.05, 'skeleton width retained');
});

test('live accent clusters do not reuse the cached base letter preview', () => {
  const helper = readFileSync(new URL('display/stroke_geometry.js', root), 'utf8');
  const template = readFileSync(new URL('display/build_display_page.py', root), 'utf8');
  const cacheCode = template.split('const penBodies =')[1].split('function drawWord(')[0];
  const evaluate = engine(source+'\n'+helper+'\nconst penBodies ='+cacheCode,
    {base:135, contrast:2.6, cap:'flat', join:'round', penAngle:32});
  evaluate('var CUT={contrast:2.6,penAngle:32,slant:8,ends:"flat",joins:"round"}');
  const base = evaluate('penBody(glyph("a",135))');
  const marked = evaluate('penBody(clusterGlyph({base:"a",marks:["\\u0301","\\u0308"]},135))');
  assert.notEqual(marked, base);
  assert.ok((marked.match(/<circle/g) || []).length === 2);
  assert.equal(evaluate('penBody(glyph("a",135))'), base);
});
