/** Install the packed artifact in a clean consumer; compile and bundle its public APIs. */
import {spawnSync} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {build} from './node_modules/esbuild/lib/main.js';
import {npm} from './package_tools.mjs';
const root=dirname(dirname(fileURLToPath(import.meta.url))),tools=join(root,'display/node_modules');
const release=JSON.parse(readFileSync(join(root,'packages/living-titles/releases/release.json'),'utf8'));
const temporary=mkdtempSync(join(tmpdir(),'living-title-consumer-'));
// Only this freshly-created directory may be removed on Windows or any other host.
if(dirname(resolve(temporary))!==resolve(tmpdir()) || !temporary.startsWith(join(tmpdir(),'living-title-consumer-')))throw Error('Invalid consumer temporary directory');
function run(cmd,args){const r=spawnSync(cmd,args,{cwd:temporary,encoding:'utf8'});if(r.status!==0)throw Error(r.stdout+r.stderr+(r.error?.message || ''));return r.stdout;}
try{
  writeFileSync(join(temporary,'package.json'),JSON.stringify({name:'living-title-packed-consumer',private:true,type:'module'}));
  npm(['install','--ignore-scripts','--legacy-peer-deps','--no-audit','--no-fund',join(root,'packages/living-titles/releases',release.filename)],temporary);
  writeFileSync(join(temporary,'headless.mjs'),`import {cuts,createTitleScene,renderTitleSVG} from '@seihouse/living-titles';
    const scene=await createTitleScene({title:'SEN'});if(cuts.length!==4 || !renderTitleSVG(scene).includes('<svg'))throw Error('Packed import failed');
    const p=JSON.parse(await (await import('node:fs/promises')).readFile('node_modules/@seihouse/living-titles/package.json','utf8'));
    if(p.dependencies)throw Error('Unexpected mandatory dependencies');console.log('Packed headless import: pass');`);
  run(process.execPath,['headless.mjs']);
  // Test tools are local locked dev dependencies; they do not enter the runtime archive.
  writeFileSync(join(temporary,'consumer.tsx'),`import {createTitleScene,createTitlePlayer,createBpmSource,smoothEnergy,exportAnimatedSVG} from '@seihouse/living-titles';
    import {LivingTitle} from '@seihouse/living-titles/react';
    const scene=await createTitleScene({title:'SEN',cut:'Ink',axes:{weight:false}});
    const player=createTitlePlayer(document.createElement('div'),scene,{source:createBpmSource()});
    player.setSource({sample:seconds=>smoothEnergy(0,seconds,.03)});player.dispose();exportAnimatedSVG(scene);
    const component=<LivingTitle title="SEN" cut="Soft" playing={false} style={{height:28}} onError={error=>console.log(error.message)} />;
    export {component};`);
  writeFileSync(join(temporary,'tsconfig.json'),JSON.stringify({compilerOptions:{target:'ES2022',module:'NodeNext',moduleResolution:'NodeNext',strict:true,noEmit:true,
    jsx:'react-jsx',lib:['ES2022','DOM'],paths:{react:[join(tools,'@types/react/index.d.ts')],
    'react/jsx-runtime':[join(tools,'@types/react/jsx-runtime.d.ts')]}},include:['consumer.tsx']}));
  run(process.execPath,[join(tools,'typescript/bin/tsc'),'--project','tsconfig.json']);
  const browserEntry=`import React from 'react';import {createRoot} from 'react-dom/client';
    import {LivingTitle} from '@seihouse/living-titles/react';
    import {createTitleScene,createTitlePlayer,createBpmSource} from '@seihouse/living-titles';
    window.api={createTitleScene,createTitlePlayer,createBpmSource};window.errors=[];
    const root=createRoot(document.getElementById('react'));
    window.setTitle=(title,color='#e6cc87')=>root.render(React.createElement(React.StrictMode,null,React.createElement(LivingTitle,{title,cut:'Soft',color,onError:e=>window.errors.push(e.message),style:{width:300,height:40}})));
    window.unmount=()=>root.unmount();window.setTitle('SEN');`;
  await build({stdin:{contents:browserEntry,resolveDir:temporary,loader:'js'},bundle:true,format:'esm',platform:'browser',nodePaths:[tools],outfile:join(temporary,'consumer.js')});
  writeFileSync(join(temporary,'index.html'),'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><div id="react"></div><div id="one" style="width:300px;height:40px"></div><div id="two" style="width:300px;height:40px"></div><script type="module" src="consumer.js"></script>');
  const python=process.platform==='win32'?join(root,'.venv/Scripts/python.exe'):'python';
  console.log(run(python,[join(root,'display/verify_package_browser.py'),temporary]));
  mkdirSync(join(root,'dist'),{recursive:true});
  writeFileSync(join(root,'dist/living-package-consumer.json'),JSON.stringify({artifact:release.filename,sha256:release.sha256,
    checks:['clean archive install','headless import without React','strict public TypeScript','React browser bundle','DOM/React lifecycle browser gates'],flags:[]},null,2)+'\n');
  console.log('Packed consumer: install, types, React bundle and browser lifecycle passed');
}finally{rmSync(temporary,{recursive:true,force:true});}
