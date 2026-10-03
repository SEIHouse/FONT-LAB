/** Assemble only the public website assets; font builders and npm metadata stay separate. */
import {copyFileSync, existsSync, lstatSync, mkdirSync, realpathSync, rmSync, statSync} from 'node:fs';
import {dirname, join, relative, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const output = join(root, 'dist', 'site');
const pages = [
  'index.html', 'site/home.css', 'site/home.js', 'site/favicon.svg',
  'fonts-full.css', 'fonts-sans.css', 'LICENSE', 'FONT-LICENSE.txt',
  'lab/index.html', 'lab/comparison.html', 'lab/reading-test.html',
  'display/lab/index.html', 'display/README.md',
  'docs/APP-INSTALL.md', 'docs/HOW-TO-USE.txt', 'docs/DEVICE-TEST.md',
  'docs/HEALTH-CHECK.txt', 'docs/DESIGN-GOALS.md', 'docs/WEBSITE.md',
];
const styles = ['Light','LightItalic','Regular','Italic','Medium','MediumItalic','SemiBold','SemiBoldItalic','Bold','BoldItalic'];
const cuts = ['soft','edge','ink','wide'];
const files = [...pages, ...styles.map(style => `fonts/SEIReader-${style}.woff2`),
  ...cuts.flatMap(cut => ['otf','woff2'].map(format => `display/fonts/${cut}/SEIHouseDisplay-${cut[0].toUpperCase()+cut.slice(1)}.${format}`))];

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
