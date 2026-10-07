import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {dirname,join} from 'node:path';
/** Run npm's JavaScript CLI directly, without Windows shell argument interpolation. */
export function npm(args,cwd){
  const directory=dirname(process.execPath);
  const cli=[process.env.npm_execpath,join(directory,'node_modules/npm/bin/npm-cli.js'),
    join(directory,'../lib/node_modules/npm/bin/npm-cli.js')].find(path=>path && existsSync(path));
  if(!cli)throw Error('Cannot locate the npm CLI beside Node; run this check with a standard Node/npm installation.');
  const result=spawnSync(process.execPath,[cli,...args],{cwd,encoding:'utf8'});
  if(result.status!==0)throw Error(result.stderr || result.stdout || result.error?.message);
  return result.stdout;
}
