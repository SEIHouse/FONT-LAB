import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

test('private @seihouse/elemental-title artifact ships expected files, hashes, and zero mandatory dependencies', () => {
  const release = JSON.parse(
    readFileSync(new URL('../packages/elemental-title/releases/release.json', import.meta.url), 'utf8')
  );
  const bytes = readFileSync(
    new URL(`../packages/elemental-title/releases/${release.filename}`, import.meta.url)
  );
  assert.equal(createHash('sha256').update(bytes).digest('hex'), release.sha256);
  assert.equal(release.name, '@seihouse/elemental-title');
  assert.equal(release.version, '0.1.0');

  const mandatory = [
    'NOTICE.txt',
    'README.md',
    'package.json',
    'dist/index.js',
    'dist/index.d.ts',
    'dist/styles.css',
    'dist/provenance.json',
  ].sort();
  assert.deepEqual([...release.files].sort(), mandatory);
  assert.ok(release.files.every((f) => !/(mock|workbench|src\/|tests\/|\.test\.)/.test(f)));

  const manifest = JSON.parse(
    readFileSync(new URL('../packages/elemental-title/package.json', import.meta.url), 'utf8')
  );
  assert.equal(manifest.dependencies, undefined);
  assert.equal(manifest.private, true);
  assert.equal(manifest.peerDependencies.react, '>=18');
  assert.equal(manifest.exports['./styles.css'], './dist/styles.css');

  const builtJs = readFileSync(
    new URL('../packages/elemental-title/dist/index.js', import.meta.url),
    'utf8'
  );
  assert.ok(builtJs.startsWith('"use client";\n'), 'dist/index.js must retain "use client"; directive');

  const provenance = JSON.parse(
    readFileSync(new URL('../packages/elemental-title/dist/provenance.json', import.meta.url), 'utf8')
  );
  assert.deepEqual(provenance.signatures, ['quill/stormwrit', 'quill/true-north']);
  for (const [name, expectedSha] of Object.entries(provenance.outputs)) {
    const actualSha = createHash('sha256')
      .update(readFileSync(new URL(`../packages/elemental-title/dist/${name}`, import.meta.url)))
      .digest('hex');
    assert.equal(actualSha, expectedSha, `dist/${name} SHA-256 mismatch`);
  }
});
