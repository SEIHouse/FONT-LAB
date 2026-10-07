import {npm} from './package_tools.mjs';
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url))),pkg=join(root,'packages/living-titles');
const target=join(pkg,'releases');mkdirSync(target,{recursive:true});
const record=JSON.parse(npm(['pack','--json','--ignore-scripts','--pack-destination',target],pkg))[0],bytes=readFileSync(join(target,record.filename));
const provenance=JSON.parse(readFileSync(join(pkg,'dist/provenance.json'),'utf8'));
writeFileSync(join(target,'release.json'),JSON.stringify({name:record.name,version:record.version,
  filename:record.filename,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),
  integrity:record.integrity,provenance,files:record.files.map(f=>f.path)},null,2)+'\n');
console.log(`${record.name}@${record.version}: ${(bytes.length/1024).toFixed(1)} KB archive -> packages/living-titles/releases/${record.filename}`);
