import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../site/drafts.js', import.meta.url), 'utf8');
/** Load the shared draft adapter with isolated storage instead of a user's browser data. */
function harness(storage) {
  const window = {localStorage:storage};
  vm.runInNewContext(source, {window});
  return window.SEIHouseDrafts;
}
/** Create a minimal storage double with the same get/set persistence contract. */
function storageMap() {
  const values = new Map();
  return {getItem:key => values.get(key) ?? null, setItem:(key,value) => values.set(key,value)};
}

test('Reader drafts survive a fresh page instance without sharing mutable settings', async () => {
  const storage = storageMap();
  const settings = {settings:{weight:97, pairSpace:{'7.':20}}, savedAt:123};
  await harness(storage).createLocalDB('reader').doc('seireader/settings').set(settings);
  settings.settings.weight = 150;
  const doc = await harness(storage).createLocalDB('reader').doc('seireader/settings').get();
  assert.equal(doc.exists, true);
  assert.equal(doc.data().settings.weight, 97);
  const draft = doc.data(); draft.settings.weight = 200;
  assert.equal(doc.data().settings.weight, 97);
});

test('Display cuts are isolated from Reader drafts and from other collections', async () => {
  const storage = storageMap();
  const db = harness(storage).createLocalDB('display');
  await db.doc('cuts/mei').set({name:'Mei', weight:115});
  await db.doc('cuts/lian').set({name:'Lian', weight:150});
  await db.doc('other/cut').set({name:'Other'});
  const cuts = await harness(storage).createLocalDB('display').collection('cuts').get();
  assert.deepEqual(cuts.docs.map(d => d.data().name).join(','), 'Mei,Lian');
  assert.equal((await harness(storage).createLocalDB('reader').doc('cuts/mei').get()).exists, false);
});

test('Blocked or corrupt storage rejects Save so the Lab can offer JSON download', async () => {
  const blocked = {getItem:() => {throw new Error('blocked');},setItem:() => {throw new Error('blocked');}};
  await assert.rejects(harness(blocked).createLocalDB('reader').doc('settings').set({weight:97}), /blocked/);
  const corrupt = storageMap(); corrupt.setItem('reader', '{broken');
  await assert.rejects(harness(corrupt).createLocalDB('reader').doc('settings').get());
  corrupt.setItem('reader', JSON.stringify({version:1, documents:[]}));
  await assert.rejects(harness(corrupt).createLocalDB('reader').doc('settings').get(), /Invalid/);
});

test('Failed writes do not replace the previous saved draft', async () => {
  const storage = storageMap();
  const db = harness(storage).createLocalDB('reader');
  await db.doc('settings').set({weight:97});
  storage.setItem = () => {throw new Error('quota');};
  await assert.rejects(db.doc('settings').set({weight:150}), /quota/);
  assert.equal((await db.doc('settings').get()).data().weight, 97);
});

test('Prototype-like document ids stay ordinary saved records', async () => {
  const db = harness(storageMap()).createLocalDB('reader');
  await db.doc('__proto__').set({name:'safe'});
  assert.equal((await db.doc('__proto__').get()).data().name, 'safe');
  assert.equal((await db.doc('toString').get()).exists, false);
});
