/** Assemble only the public website assets; font builders and npm metadata stay separate. */
import {copyFileSync, existsSync, lstatSync, mkdirSync, realpathSync, rmSync, statSync} from 'node:fs';
import {dirname, join, relative, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {displayInventory} from './display/site_inventory.mjs';

const root = dirname(fileURLToPath(import.meta.url));
const output = join(root, 'dist', 'site');
const pages = [
  'index.html', 'site/home.css', 'site/home.js', 'site/favicon.svg',
  'fonts-full.css', 'fonts-sans.css', 'LICENSE', 'FONT-LICENSE.txt',
  'lab/index.html', 'lab/comparison.html', 'lab/reading-test.html',
  'display/lab/index.html', 'display/README.md', 'display/fonts.css',
  'display/lab/living-media.js', 'display/lab/living-media-LICENSE.txt',
  'display/novel-expanded/index.html', 'display/novel-expanded/mock.css',
  'display/novel-expanded/mock.js',
  ...['engine.js','index.js','player.js'].map(name => `display/novel-expanded/runtime/${name}`),
  'display/novel-expanded/assets/emblem.jpg', 'display/novel-expanded/assets/immortal-land.jpg',
  'display/novel-expanded/README.md',
  'packages/living-titles/README.md',
  'docs/DISPLAY-LIVING-TITLES-STEP6.md', 'docs/proofs/display-step6/index.html',
  ...['soft','edge','ink','wide'].flatMap(cut => ['caps','mixed'].map(kind => `docs/proofs/display-step6/${cut}-${kind}.svg`)),
  'docs/APP-INSTALL.md', 'docs/HOW-TO-USE.txt', 'docs/DEVICE-TEST.md',
  'docs/HEALTH-CHECK.txt', 'docs/DESIGN-GOALS.md', 'docs/WEBSITE.md',
];
const styles = ['Light','LightItalic','Regular','Italic','Medium','MediumItalic','SemiBold','SemiBoldItalic','Bold','BoldItalic'];
const displayFiles = displayInventory(root);
const files = [...pages, ...styles.map(style => `fonts/SEIReader-${style}.woff2`),
  ...new Set(displayFiles)];

// Validate all inputs before replacing the fixed, generated output directory.
for (const file of files) {
  if (!statSync(join(root, file)).isFile()) throw new Error(`Missing website asset: ${file}`);
}
mkdirSync(join(root, 'dist'), {recursive:true});
if (realpathSync(join(root, 'dist')) !== join(realpathSync(root), 'dist') ||
    relative(root, resolve(output)) !== join('dist', 'site') ||
    (existsSync(output) && lstatSync(output).isSymbolicLink())) {
  throw new Error('Website output must be the local dist/site directory');
}
rmSync(output, {recursive:true, force:true});
let bytes = 0;
for (const file of files) {
  const destination = join(output, file);
  mkdirSync(dirname(destination), {recursive:true});
  copyFileSync(join(root, file), destination);
  bytes += statSync(destination).size;
}
console.log(`Website: ${files.length} public files, ${(bytes/1024/1024).toFixed(2)} MiB -> dist${sep}site`);
