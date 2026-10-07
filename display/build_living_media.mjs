/** Bundle only the pinned media library and adapter; no font engine/public SDK. */
import {build} from 'esbuild';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const root = new URL('../',import.meta.url);
await build({entryPoints:[fileURLToPath(new URL('display/living-media.mjs',root))],
  outfile:fileURLToPath(new URL('display/lab/living-media.js',root)),bundle:true,
  format:'iife',globalName:'LivingMedia',target:'es2022',minify:true,legalComments:'eof',
  banner:{js:'/* Mediabunny 1.61.3 (MPL-2.0). See living-media-LICENSE.txt; source: https://github.com/Vanilagy/mediabunny/tree/v1.61.3 */'}});
writeFileSync(new URL('display/lab/living-media-LICENSE.txt',root),
  'Mediabunny 1.61.3\nCopyright (c) 2024-present Vanilagy\nSource: https://github.com/Vanilagy/mediabunny/tree/v1.61.3\nBundled without source changes using esbuild 0.28.2.\n\n'+
  readFileSync(new URL('display/node_modules/mediabunny/LICENSE',root),'utf8'));
