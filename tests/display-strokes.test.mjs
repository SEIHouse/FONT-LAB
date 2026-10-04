import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../display/stroke_geometry.js', import.meta.url), 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context);
const evaluate = code => vm.runInContext(code, context);

test('live Ink caps remain perpendicular after pen rotation and slant', () => {
  for(const angle of [0,30,75,90,145]){
    const error = evaluate(`(() => {
      const angle = ${angle}*Math.PI/180, inward = [Math.cos(angle),Math.sin(angle)];
      const shear = -Math.tan(8*Math.PI/180), M = displayPen(2.6,32);
      const p = displayCap([200,300],inward,135,M.out,shear);
      const face = [p[2][0]-p[1][0]+shear*(p[2][1]-p[1][1]),p[2][1]-p[1][1]];
      const tangent = [inward[0]+shear*inward[1],inward[1]];
      return Math.abs(face[0]*tangent[0]+face[1]*tangent[1]);
    })()`);
    assert.ok(error < 1e-8, `angle ${angle}: perpendicular face required`);
  }
});

test('live attached branch has three exposed caps and no fourth cap at the stem', () => {
  const body = evaluate(`displayPenBody({body:
    '<path d="M0 0L0 -700" fill="none" stroke="currentColor" stroke-width="115"/>'+
    '<path d="M470 -700L0 -215" fill="none" stroke="currentColor" stroke-width="115"/>'},
    {contrast:1,penAngle:0,slant:0,ends:'flat',joins:'sharp'})`);
  assert.equal([...body.matchAll(/fill="currentColor"/g)].length, 3);
  assert.ok(!body.includes('stroke-linecap="square"'));
});

test('live coincident terminal rays use a join with only two exposed caps', () => {
  const body = evaluate(`displayPenBody({body:
    '<path d="M0 -700L0 0" fill="none" stroke="currentColor" stroke-width="115"/>'+
    '<path d="M0 0L400 0" fill="none" stroke="currentColor" stroke-width="115"/>'},
    {contrast:1,penAngle:0,slant:0,ends:'flat',joins:'sharp'})`);
  assert.equal([...body.matchAll(/fill="currentColor"/g)].length, 2);
  assert.equal([...body.matchAll(/stroke-width="115"/g)].length, 3);
});

test('closed native circles have joins and no terminal cap polygons', () => {
  const body = evaluate(`displayPenBody({body:
    '<path d="M100 0C100 55 55 100 0 100C-55 100 -100 55 -100 0C-100 -55 -55 -100 0 -100C55 -100 100 -55 100 0" fill="none" stroke="currentColor" stroke-width="55"/>'},
    {contrast:1,penAngle:0,slant:0,ends:'flat',joins:'sharp'})`);
  assert.equal([...body.matchAll(/fill="currentColor"/g)].length, 0);
  assert.ok(body.includes('Z"'));
});
