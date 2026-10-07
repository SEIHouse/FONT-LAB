import {npm} from './package_tools.mjs';
import {createHash} from 'node:crypto';
import {existsSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url))),pkg=join(root,'packages/living-titles');
const target=join(pkg,'releases');mkdirSync(target,{recursive:true});
const provenance=JSON.parse(readFileSync(join(pkg,'dist/provenance.json'),'utf8'));
const fonts=['Soft','Edge','Ink','Wide'].map(c=>`SEIHouseDisplay-${c}.woff2`);
const expected=['NOTICE.txt','README.md','SANS-LICENSE.txt','package.json',
  ...['engine.js','index.js','player.js','react.js','index.d.ts','react.d.ts','fonts.css','provenance.json'].map(f=>`dist/${f}`),
  ...fonts.map(f=>`dist/fonts/${f}`)].sort();
for(const file of expected)if(!existsSync(join(pkg,file)))throw Error(`Incomplete package build: ${file}`);
for(const font of fonts)if(createHash('sha256').update(readFileSync(join(pkg,'dist/fonts',font))).digest('hex')!==provenance.fonts[font])throw Error(`Invalid package font: ${font}`);
const record=JSON.parse(npm(['pack','--json','--ignore-scripts','--pack-destination',target],pkg))[0],bytes=readFileSync(join(target,record.filename));
if(JSON.stringify(record.files.map(f=>f.path).sort())!==JSON.stringify(expected))throw Error('Unexpected package payload; rebuild before delivery');
writeFileSync(join(target,'release.json'),JSON.stringify({name:record.name,version:record.version,
  filename:record.filename,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),
  integrity:record.integrity,provenance,files:record.files.map(f=>f.path)},null,2)+'\n');
console.log(`${record.name}@${record.version}: ${(bytes.length/1024).toFixed(1)} KB archive -> packages/living-titles/releases/${record.filename}`);
