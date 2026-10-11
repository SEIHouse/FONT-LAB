import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const context = vm.createContext({document:{getElementById:()=>({insertAdjacentHTML(){}})}});
context.window = context;
vm.runInContext(readFileSync(new URL('engine.js', root), 'utf8')+'\n'+
  readFileSync(new URL('display/stroke_geometry.js', root), 'utf8'), context);
const evaluate = code => vm.runInContext(code, context);
const ellipse = (a,b) => { const h = ((a-b)/(a+b))**2; return Math.PI*(a+b)*(1+3*h/(10+Math.sqrt(4-3*h))); };

test('the flat nib keeps the oval pen perimeter, so switching pens keeps the stroke color', () => {
  for(const k of [1, 2.6, 5]){
    const sharp = evaluate(`nibShape(100, ${k}, 32, false)`), soft = evaluate(`nibShape(100, ${k}, 32, true)`);
    assert.ok(Math.abs(2*(sharp.length+sharp.thick) - ellipse(50, 50/k)) < 1e-9);
    assert.ok(Math.abs(2*(soft.length-soft.thick) + Math.PI*soft.thick - ellipse(50, 50/k)) < 1e-9);
    assert.ok(Math.abs(sharp.length/sharp.thick - k) < 1e-9);
  }
  // At contrast 1 the soft nib is exactly the round pen.
  const round = evaluate('nibShape(100, 1, 30, true)');
  assert.ok(Math.abs(round.length-100) < 1e-9 && Math.abs(round.thick-100) < 1e-9);
});

test('curves split exactly where their tangent runs along the nib', () => {
  const pieces = evaluate(`displayNibSplit([[0,0],[55,0],[100,45],[100,100]], [1,1])`);
  assert.equal(pieces.length, 2);
  const joint = pieces[0][3], before = pieces[0][2], after = pieces[1][1];
  assert.deepEqual(joint, pieces[1][0]);
  for(const control of [before, after]){
    const tangent = [joint[0]-control[0], joint[1]-control[1]];
    assert.ok(Math.abs(tangent[0]-tangent[1]) < 1e-9, 'the tangent at the split is parallel to the nib');
  }
  assert.equal(evaluate(`displayNibSplit([[0,0],[100,0]], [1,1])`).length, 1);
});

test('a sharp nib sweeps a straight stem into its exact rectangle', () => {
  const box = evaluate(`(() => {
    const {contours, nib} = displayNibContours(displaySegments('M0 0L0 -700'), 100, {contrast:4, penAngle:0, ends:'flat'});
    const points = contours.flat(2);
    return {nib, box:[Math.min(...points.map(p=>p[0])), Math.min(...points.map(p=>p[1])),
                      Math.max(...points.map(p=>p[0])), Math.max(...points.map(p=>p[1]))]};
  })()`);
  const {length, thick} = box.nib, expected = [-length/2, -700-thick/2, length/2, thick/2];
  box.box.forEach((value, i) => assert.ok(Math.abs(value-expected[i]) < 1e-9, `edge ${i}`));
});

test('the engine spaces and aligns letters with the nib footprint', () => {
  const half = evaluate(`(() => { Object.assign(P, {pen:'nib', contrast:4, penAngle:30, cap:'flat'});
    const result = penHalf(100); Object.assign(P, {pen:'oval', contrast:1, penAngle:0, cap:'round'}); return result; })()`);
  const n = evaluate('nibShape(100, 4, 30, false)'), c = Math.cos(Math.PI/6), s = Math.sin(Math.PI/6);
  assert.ok(Math.abs(half.hx - (n.length/2*c + n.thick/2*s)) < 1e-9);
  assert.ok(Math.abs(half.hy - (n.length/2*s + n.thick/2*c)) < 1e-9);
  // The Reader's unrotated oval branch is unchanged.
  assert.deepEqual(JSON.parse(evaluate('JSON.stringify(penHalf(100))')), {hx:50, hy:50});
});

test('nib bodies are one nonzero fill without caps; a soft nib adds its round edge', () => {
  const body = cut => evaluate(`displayPenBody({body:'<path d="M0 0L0 -700" fill="none" stroke="currentColor" stroke-width="100"/>'+
    '<circle cx="0" cy="-900" r="50" fill="currentColor"/>'}, ${JSON.stringify(cut)})`);
  const sharp = body({pen:'nib', contrast:4, penAngle:30, ends:'flat', joins:'round'});
  assert.equal([...sharp.matchAll(/<path /g)].length, 1);
  assert.match(sharp, /fill-rule="nonzero"\/>/);
  assert.match(sharp, /<circle /);
  const soft = body({pen:'nib', contrast:4, penAngle:30, ends:'round', joins:'round'});
  const thick = evaluate('nibShape(100, 4, 30, true)').thick;
  assert.match(soft, new RegExp(`stroke-width="${thick.toFixed(5)}" stroke-linejoin="round"`));
});
