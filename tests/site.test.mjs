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
  return {getItem:key => values.get(key) ?? null, setItem:(key,value) => values.set(key,value),
    get length() { return values.size; }, key:index => [...values.keys()][index] ?? null};
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

test('Interleaved saves in different tabs preserve both cuts', async () => {
  const storage = storageMap();
  const first = harness(storage).createLocalDB('display');
  const second = harness(storage).createLocalDB('display');
  const originalSet = storage.setItem;
  let interleaved = false, otherSave;
  storage.setItem = (key, value) => {
    if (!interleaved) {
      interleaved = true;
      otherSave = second.doc('cuts/second').set({name:'Second'});
    }
    originalSet(key, value);
  };
  await first.doc('cuts/first').set({name:'First'});
  await otherSave;
  const cuts = await first.collection('cuts').get();
  assert.equal(cuts.docs.map(doc => doc.data().name).sort().join(','), 'First,Second');
});

test('Original map-format drafts remain readable and update without replacing other cuts', async () => {
  const storage = storageMap();
  const original = JSON.stringify({version:1,documents:{'cuts/soft':{name:'Soft',weight:150},'cuts/edge':{name:'Edge',weight:115}}});
  storage.setItem('display', original);
  const db = harness(storage).createLocalDB('display');
  assert.equal((await db.doc('cuts/soft').get()).data().weight, 150);
  await db.doc('cuts/soft').set({name:'Soft',weight:155});
  assert.equal((await db.doc('cuts/soft').get()).data().weight, 155);
  assert.equal((await db.doc('cuts/edge').get()).data().weight, 115);
  assert.equal((await db.collection('cuts').get()).docs.length, 2);
  assert.equal(storage.getItem('display'), original);
});

test('Corrupt per-document records are reported without erasing them or another cut', async () => {
  const storage = storageMap();
  const db = harness(storage).createLocalDB('display');
  await db.doc('cuts/good').set({name:'Good'});
  const brokenKey = 'display:doc:' + encodeURIComponent('cuts/broken');
  storage.setItem(brokenKey, '{broken');
  await assert.rejects(db.doc('cuts/broken').get(), /Invalid saved draft data/);
  await assert.rejects(db.doc('cuts/broken').set({name:'Broken'}), /Invalid saved draft data/);
  assert.equal(storage.getItem(brokenKey), '{broken');
  assert.equal((await db.doc('cuts/good').get()).data().name, 'Good');
  const cuts = await db.collection('cuts').get();
  assert.equal(cuts.invalid, 1);
  assert.equal(cuts.docs.map(doc => doc.data().name).join(','), 'Good');
});

test('Valid per-document cuts remain available with corrupt legacy data or malformed keys', async () => {
  const storage = storageMap();
  const db = harness(storage).createLocalDB('display');
  await db.doc('cuts/good').set({name:'Good'});
  storage.setItem('display', '{broken');
  storage.setItem('display:doc:%ZZ', '{broken-key');
  const cuts = await db.collection('cuts').get();
  assert.equal(cuts.invalid, 2);
  assert.equal(cuts.docs.map(doc => doc.data().name).join(','), 'Good');
  assert.equal(storage.getItem('display'), '{broken');
  assert.equal(storage.getItem('display:doc:%ZZ'), '{broken-key');
});

test('Collection loading still rejects genuine storage-access failures', async () => {
  const broken = {getItem:() => {throw new Error('storage unavailable');}};
  await assert.rejects(harness(broken).createLocalDB('display').collection('cuts').get(), /storage unavailable/);
});
