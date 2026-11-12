import { npm } from './package_tools.mjs';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const pkg = join(root, 'packages/elemental-title');
const target = join(pkg, 'releases');
mkdirSync(target, { recursive: true });

const provenance = JSON.parse(readFileSync(join(pkg, 'dist/provenance.json'), 'utf8'));
const distFiles = ['index.js', 'index.d.ts', 'styles.css', 'provenance.json'];
const expected = [
  'NOTICE.txt',
  'README.md',
  'package.json',
  ...distFiles.map((f) => `dist/${f}`),
].sort();

for (const file of expected) {
  if (!existsSync(join(pkg, file))) {
    throw new Error(`Incomplete Elemental Title package build: ${file}`);
  }
}

for (const [name, expectedSha] of Object.entries(provenance.outputs)) {
  const actualSha = createHash('sha256')
    .update(readFileSync(join(pkg, 'dist', name)))
    .digest('hex');
  if (actualSha !== expectedSha) {
    throw new Error(`Stale Elemental Title dist output: ${name}`);
  }
}

const record = JSON.parse(
  npm(['pack', '--json', '--ignore-scripts', '--pack-destination', target], pkg)
)[0];
const bytes = readFileSync(join(target, record.filename));

const packedPaths = record.files.map((f) => f.path).sort();
if (JSON.stringify(packedPaths) !== JSON.stringify(expected)) {
  throw new Error(
    `Unexpected Elemental Title package payload: ${JSON.stringify(packedPaths)} vs ${JSON.stringify(expected)}`
  );
}

writeFileSync(
  join(target, 'release.json'),
  JSON.stringify(
    {
      name: record.name,
      version: record.version,
      filename: record.filename,
      bytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'),
      integrity: record.integrity,
      provenance,
      files: record.files.map((f) => f.path),
    },
    null,
    2
  ) + '\n',
  'utf8'
);

console.log(
  `${record.name}@${record.version}: ${(bytes.length / 1024).toFixed(1)} KB archive -> packages/elemental-title/releases/${record.filename}`
);
