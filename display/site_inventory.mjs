/** Public Display inventory validation, shared by the website build and its regressions. */
import {readFileSync, readdirSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {isDeepStrictEqual} from 'node:util';
import {createHash} from 'node:crypto';

export function displayInventory(root) {
  const manifest = JSON.parse(readFileSync(join(root, 'display/production-manifest.json'), 'utf8'));
  if (manifest.version !== 1 || !manifest.cuts?.length) throw new Error('Missing Display production inventory');
  const settings = readdirSync(join(root, 'display/cuts')).filter(file => file.endsWith('.json'))
    .map(file => JSON.parse(readFileSync(join(root, 'display/cuts', file), 'utf8')));
  if (settings.length !== manifest.cuts.length || settings.some(cut =>
      !manifest.cuts.some(row => isDeepStrictEqual(row.settings, cut)))) {
    throw new Error('Display inventory is stale; run display/build_all_cuts.py');
  }
  const displayFiles = ['display/production-manifest.json', 'site/display/index.html',
    'site/display/specimen.css', 'site/display/specimen.js',
    ...manifest.cuts.flatMap(cut => [cut.specimen, ...cut.styles.flatMap(face => face.assets.map(asset => asset.path))])];
  for (const cut of manifest.cuts) {
    const labels = ['Regular', ...Object.keys(cut.settings.production?.weights ?? {})];
    if (cut.settings.production?.oblique !== undefined) labels.push('Oblique');
    if (cut.styles.length !== labels.length || new Set(cut.styles.map(face => face.label)).size !== labels.length ||
        labels.some(label => !cut.styles.some(face => face.label === label))) {
      throw new Error('Stale Display style inventory for '+cut.name+'; run display/build_all_cuts.py');
    }
  }
  for (const file of displayFiles) {
    if (typeof file !== 'string' || file.includes('\\') || resolve(root, file) !== join(root, file) ||
        !/^(display\/(fonts\/[a-z0-9-]+\/(?:[A-Za-z]+\/)?(?:SEIHouseDisplay-[A-Za-z0-9-]+(?:\.[a-z-]+)?\.(?:otf|woff2)|spacing_[a-z0-9-]+\.json)|spacing_[a-z0-9-]+\.json|production-manifest\.json)|site\/display\/(?:[a-z0-9-]+\/)?(?:index\.html|specimen\.(?:css|js)))$/.test(file)) {
      throw new Error('Invalid Display website asset: '+file);
    }
  }
  for (const cut of manifest.cuts) for (const face of cut.styles) for (const asset of face.assets) {
    const bytes = readFileSync(join(root, asset.path));
    if (bytes.length !== asset.bytes || createHash('sha256').update(bytes).digest('hex') !== asset.sha256) {
      throw new Error('Stale Display asset inventory: '+asset.path+'; run display/build_all_cuts.py');
    }
  }
  return [...new Set(displayFiles)];
}
