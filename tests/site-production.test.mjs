import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join, resolve, sep} from 'node:path';
import {createHash} from 'node:crypto';
import {displayInventory} from '../display/site_inventory.mjs';

function fixture(run) {
  const root = mkdtempSync(join(tmpdir(), 'fontlab-production-'));
  function write(file, text) {mkdirSync(dirname(join(root,file)),{recursive:true});writeFileSync(join(root,file),text);}
  const settings = {name:'New Cut', weight:55, production:{weights:{Light:.85},oblique:9}};
  write('display/cuts/new-cut.json',JSON.stringify(settings));
  const styles = ['Regular','Light','Oblique'].map(label => {
    const folder = 'display/fonts/new-cut/'+(label==='Regular'?'':label+'/');
    const path = folder+'SEIHouseDisplay-NewCut'+(label==='Regular'?'':'-'+label)+'.woff2';
    const bytes = Buffer.from(label+' font delivery'); write(path,bytes);
    return {label, assets:[{path,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')}]};
  });
  const manifest={version:1,cuts:[{name:'New Cut',slug:'new-cut',settings,styles,specimen:'site/display/new-cut/index.html'}]};
  function save() {write('display/production-manifest.json',JSON.stringify(manifest));}
  save();
  try {run({root,settings,manifest,save,write});}
  finally {
    const target=resolve(root), parent=resolve(tmpdir());
    if (!target.startsWith(parent+sep) || !target.slice(parent.length+1).startsWith('fontlab-production-')) throw new Error('Invalid test cleanup target');
    rmSync(target,{recursive:true,force:true});
  }
}

test('website discovers new cuts, optional styles and their native specimens',()=>fixture(({root})=>{
  const files=displayInventory(root);
  assert.ok(files.includes('site/display/new-cut/index.html'));
  assert.ok(files.includes('display/fonts/new-cut/Light/SEIHouseDisplay-NewCut-Light.woff2'));
  assert.ok(files.includes('display/fonts/new-cut/Oblique/SEIHouseDisplay-NewCut-Oblique.woff2'));
  assert.equal(new Set(files).size,files.length);
}));

test('stale cut settings or omitted declared styles cannot ship',()=>fixture(({root,settings,manifest,save,write})=>{
  write('display/cuts/new-cut.json',JSON.stringify({...settings,weight:65}));
  assert.throws(()=>displayInventory(root),/inventory is stale/);
  write('display/cuts/new-cut.json',JSON.stringify(settings));
  manifest.cuts[0].styles.pop();save();
  assert.throws(()=>displayInventory(root),/style inventory/);
}));

test('changed font bytes invalidate delivery even when JSON settings still match',()=>fixture(({root,write})=>{
  write('display/fonts/new-cut/SEIHouseDisplay-NewCut.woff2','stale font');
  assert.throws(()=>displayInventory(root),/Stale Display asset inventory/);
}));

test('manifest cannot expose source files or traverse outside the public inventory',()=>fixture(({root,manifest,save})=>{
  for (const path of ['font_builder.py','display/fonts/../../engine.js','C:/other/font.otf']) {
    manifest.cuts[0].styles[0].assets[0].path=path;save();
    assert.throws(()=>displayInventory(root),/Invalid Display website asset/);
  }
}));
