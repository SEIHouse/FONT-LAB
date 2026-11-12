import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import {dirname, join, resolve, sep} from 'node:path';
import {createHash} from 'node:crypto';
import {displayInventory} from '../display/site_inventory.mjs';
import {versionInventory} from '../site/version_inventory.mjs';

test('built homepage reaches the Noto comparison and ships its linked assets', () => {
  const repo = fileURLToPath(new URL('../', import.meta.url));
  execFileSync(process.execPath, ['build_site.mjs'], {cwd:repo});
  const output = join(repo, 'dist', 'site');
  const home = readFileSync(join(output, 'index.html'), 'utf8');
  const entry = [...home.matchAll(/href="([^"]+)"/g)].map(match=>match[1]).find(href=>href.includes('/noto/'));
  assert.ok(entry, 'Noto must be reachable from the homepage');
  const pagePath = resolve(output, entry);
  const page = readFileSync(pagePath, 'utf8');
  assert.match(page, /Back to Font Lab/);
  const refs = [...page.matchAll(/(?:href=|src=)["']([^"']+)["']|url\(['"]?([^)'"\s]+)['"]?\)/g)]
    .map(match=>match[1] || match[2]).filter(ref=>!ref.startsWith('data:') && !ref.startsWith('#'));
  assert.ok(refs.some(ref=>ref.endsWith('.woff2')), 'The comparison must load its study fonts');
  for (const ref of refs) {
    assert.ok(existsSync(resolve(dirname(pagePath), ref)), `Missing deployed comparison asset: ${ref}`);
  }
});

/** Exercise public inventory validation in a disposable collection with a new cut and three styles. */
function fixture(run) {
  const root = mkdtempSync(join(tmpdir(), 'fontlab-production-'));
  /** Write a fixture asset inside the isolated temporary collection. */
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
  /** Publish the current fixture inventory before checking a deliberate regression. */
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

test('built homepage separates Reading Fonts & Title Engine, showcases 0.42, and deploys full version history', () => {
  const repo = fileURLToPath(new URL('../', import.meta.url));
  execFileSync(process.execPath, ['build_site.mjs'], {cwd:repo});
  const output = join(repo, 'dist', 'site');
  const phase4 = JSON.parse(readFileSync(join(repo, 'phase4.json'), 'utf8'));
  const home = readFileSync(join(output, 'index.html'), 'utf8');

  assert.match(home, /id="reading-fonts"/, 'Homepage must have the Reading Fonts section');
  assert.match(home, /id="title-engine"/, 'Homepage must have the Title Engine section');
  assert.match(home, new RegExp(`SEIHouse Sans ${phase4.version.replace('.', '\\.')}`), 'Homepage must showcase current Sans version');
  assert.doesNotMatch(home, /Current · SEIHouse Sans 0\.39/, 'Homepage must not label 0.39 as current');

  // Verify every local link and script/stylesheet reference on index.html resolves inside dist/site.
  const homeRefs = [...home.matchAll(/(?:href|src)="([^"]+)"/g)]
    .map(m => m[1])
    .filter(ref => !ref.startsWith('#') && !ref.startsWith('data:') && !/^https?:/i.test(ref));
  assert.ok(homeRefs.includes('./display/elemental/index.html'), 'Homepage must link to Elemental Title Lab');
  assert.ok(homeRefs.includes('./packages/elemental-title/README.md'), 'Homepage must link to Elemental Title package guide');
  assert.ok(homeRefs.includes('./docs/FAMILIAR-SIGNATURES.md'), 'Homepage must link to Familiar Signatures brief');
  for (const ref of homeRefs) {
    const cleanRef = ref.split('?')[0].split('#')[0];
    assert.ok(existsSync(resolve(output, cleanRef)), `Missing deployed homepage target: ${ref}`);
  }

  // Verify Elemental Title Lab deploys with its CSS/JS assets while keeping package source & tarballs out of dist/site.
  const elementalLabPath = join(output, 'display', 'elemental', 'index.html');
  assert.ok(existsSync(elementalLabPath), 'Elemental Title Lab must be deployed');
  assert.ok(existsSync(join(output, 'display', 'elemental', 'lab.js')), 'Elemental Title Lab bundle must be deployed');
  assert.ok(existsSync(join(output, 'display', 'elemental', 'lab.css')), 'Elemental Title Lab stylesheet must be deployed');
  assert.ok(!existsSync(join(output, 'packages', 'elemental-title', 'src')), 'Elemental Title source must stay excluded from public site');
  assert.ok(!existsSync(join(output, 'packages', 'elemental-title', 'releases')), 'Elemental Title release tarballs must stay excluded from public site');
  const elementalHtml = readFileSync(elementalLabPath, 'utf8');
  const elementalRefs = [...elementalHtml.matchAll(/(?:href|src)="([^"]+)"/g)]
    .map(m => m[1])
    .filter(ref => !ref.startsWith('#') && !ref.startsWith('data:') && !/^https?:/i.test(ref));
  for (const ref of elementalRefs) {
    const cleanRef = ref.split('?')[0].split('#')[0];
    assert.ok(existsSync(resolve(dirname(elementalLabPath), cleanRef)), `Missing Elemental Lab asset: ${ref}`);
  }

  // Verify the Version History & Compare page and manifest ship all archived WOFF2 files.
  const versionsPagePath = join(output, 'site', 'versions', 'index.html');
  assert.ok(existsSync(versionsPagePath), 'Version history page must be deployed');
  const versionsPage = readFileSync(versionsPagePath, 'utf8');
  const verRefs = [...versionsPage.matchAll(/(?:href|src)="([^"]+)"/g)]
    .map(m => m[1])
    .filter(ref => !ref.startsWith('#') && !ref.startsWith('data:') && !/^https?:/i.test(ref));
  for (const ref of verRefs) {
    const cleanRef = ref.split('?')[0].split('#')[0];
    assert.ok(existsSync(resolve(dirname(versionsPagePath), cleanRef)), `Missing version page asset: ${ref}`);
  }

  const manifest = JSON.parse(readFileSync(join(output, 'site', 'versions.json'), 'utf8'));
  assert.equal(manifest.tracks.sans.currentVersion, phase4.version);
  assert.ok(manifest.tracks.sans.versions.length >= 17, 'All 17 Sans versions (0.6 -> 0.42) must be tracked');
  assert.ok(manifest.tracks.display.versions.length >= 7, 'All 7 Display milestones must be tracked');
  assert.ok(manifest.tracks.noto.versions.length >= 4, 'All 4 Noto warmth studies must be tracked');

  for (const track of Object.values(manifest.tracks)) {
    for (const entry of track.versions) {
      for (const face of entry.faces) {
        const deployedFont = join(output, face.path);
        assert.ok(existsSync(deployedFont), `Missing deployed version font: ${face.path}`);
        const bytes = readFileSync(deployedFont);
        assert.equal(bytes.subarray(0, 4).toString('ascii'), 'wOF2');
        assert.equal(bytes.length, face.bytes);
        assert.equal(createHash('sha256').update(bytes).digest('hex'), face.sha256);
      }
    }
  }
});

/** Exercise versionInventory validation in an isolated disposable fixture. */
function versionFixture(run) {
  const root = mkdtempSync(join(tmpdir(), 'fontlab-versions-'));
  function write(file, data) {
    mkdirSync(dirname(join(root, file)), {recursive:true});
    writeFileSync(join(root, file), data);
  }
  const woff2Bytes = Buffer.concat([Buffer.from('wOF2'), Buffer.from('fixture-font-payload')]);
  const sha = createHash('sha256').update(woff2Bytes).digest('hex');

  write('fonts/SEIReader-Regular.woff2', woff2Bytes);
  write('old/0.41/SEIReader-Regular.woff2', woff2Bytes);
  write('display/fonts/edge/SEIHouseDisplay-Edge.woff2', woff2Bytes);
  write('noto/studies/warmth/fonts/SEIHouseNotoBalanced-Regular.woff2', woff2Bytes);
  write('site/versions/index.html', '<!doctype html><title>Versions</title>');
  write('site/versions/versions.css', 'body {}');
  write('site/versions/versions.js', '');
  write('phase4.json', JSON.stringify({schema:1, version:'0.42'}));
  write('index.html', '<span data-sans-version>SEIHouse Sans 0.42</span><span>Current · SEIHouse Sans 0.42</span>');

  const manifest = {
    schema: 1,
    tracks: {
      sans: {
        currentVersion: '0.42',
        versions: [
          {version:'0.42', current:true, faces:[{path:'fonts/SEIReader-Regular.woff2', bytes:woff2Bytes.length, sha256:sha}]},
          {version:'0.41', current:false, faces:[{path:'old/0.41/SEIReader-Regular.woff2', bytes:woff2Bytes.length, sha256:sha}]},
        ],
      },
      display: {
        currentVersion: '0.1',
        versions: [
          {version:'0.1', current:true, faces:[{path:'display/fonts/edge/SEIHouseDisplay-Edge.woff2', bytes:woff2Bytes.length, sha256:sha}]},
        ],
      },
      noto: {
        currentVersion: 'Refinement 01',
        versions: [
          {version:'Refinement 01', current:true, faces:[{path:'noto/studies/warmth/fonts/SEIHouseNotoBalanced-Regular.woff2', bytes:woff2Bytes.length, sha256:sha}]},
        ],
      },
    },
  };
  function saveManifest() {
    write('site/versions.json', JSON.stringify(manifest));
  }
  saveManifest();

  try {
    run({root, write, manifest, saveManifest, woff2Bytes});
  } finally {
    const target = resolve(root), parent = resolve(tmpdir());
    if (!target.startsWith(parent + sep) || !target.slice(parent.length + 1).startsWith('fontlab-versions-')) {
      throw new Error('Invalid test cleanup target');
    }
    rmSync(target, {recursive:true, force:true});
  }
}

test('versionInventory rejects stale homepage badges, stale manifest versions, bad hashes, and unsafe paths', () => versionFixture(({root, write, manifest, saveManifest}) => {
  const validFiles = versionInventory(root);
  assert.ok(validFiles.includes('old/0.41/SEIReader-Regular.woff2'));

  // Stale homepage badge (e.g., 0.39 while phase4.json is 0.42) must fail build validation.
  write('index.html', '<span data-sans-version>SEIHouse Sans 0.39</span><span>Current · SEIHouse Sans 0.39</span>');
  assert.throws(() => versionInventory(root), /Stale SEIHouse Sans version badge/);

  // Restore homepage, then test stale manifest version.
  write('index.html', '<span data-sans-version>SEIHouse Sans 0.42</span><span>Current · SEIHouse Sans 0.42</span>');
  manifest.tracks.sans.currentVersion = '0.39';
  saveManifest();
  assert.throws(() => versionInventory(root), /Stale SEIHouse Sans version in site\/versions\.json/);

  // Restore manifest version, then test modified font bytes.
  manifest.tracks.sans.currentVersion = '0.42';
  saveManifest();
  write('old/0.41/SEIReader-Regular.woff2', Buffer.from('wOF2tampered'));
  assert.throws(() => versionInventory(root), /Stale version asset inventory/);

  // Test unsafe / non-public paths.
  for (const unsafePath of ['archive_version.py', 'old/../phase4.json', 'C:/Windows/Fonts/arial.woff2']) {
    manifest.tracks.sans.versions[1].faces[0].path = unsafePath;
    saveManifest();
    assert.throws(() => versionInventory(root), /Invalid version website asset/);
  }
}));
