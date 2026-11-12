/** Build @seihouse/elemental-title into packages/elemental-title/dist with strict TS verification. */
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from './node_modules/esbuild/lib/main.js';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const tools = join(root, 'display/node_modules');
const pkg = join(root, 'packages/elemental-title');
const srcDir = join(pkg, 'src');
const outDir = join(pkg, 'dist');

function walkFiles(dir) {
  const results = [];
  if (!existsSync(dir)) return results;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    const stat = lstatSync(full);
    if (stat.isSymbolicLink()) {
      throw new Error(`Symbolic links are not allowed in package tree: ${full}`);
    }
    if (stat.isDirectory()) {
      results.push(...walkFiles(full));
    } else if (stat.isFile()) {
      results.push(full);
    }
  }
  return results.sort();
}

// Typecheck src/index.ts and assert public.d.ts contract parity using locked TypeScript in display/node_modules
const checkTmp = mkdtempSync(join(tmpdir(), 'elemental-title-typecheck-'));
try {
  writeFileSync(
    join(checkTmp, 'contract-check.ts'),
    `import * as impl from ${JSON.stringify(join(srcDir, 'index.ts'))};\n` +
      `import type * as pub from ${JSON.stringify(join(srcDir, 'public.d.ts'))};\n` +
      `type AssertAssignable<A extends B, B> = true;\n` +
      `type _Forward = AssertAssignable<typeof impl.ElementalTitle, typeof pub.ElementalTitle>;\n` +
      `type _Backward = AssertAssignable<typeof pub.ElementalTitle, typeof impl.ElementalTitle>;\n` +
      `type _PropsF = AssertAssignable<impl.ElementalTitleProps, pub.ElementalTitleProps>;\n` +
      `type _PropsB = AssertAssignable<pub.ElementalTitleProps, impl.ElementalTitleProps>;\n` +
      `type _SigF = AssertAssignable<impl.ElementalTitleSignature, pub.ElementalTitleSignature>;\n` +
      `type _SigB = AssertAssignable<pub.ElementalTitleSignature, impl.ElementalTitleSignature>;\n` +
      `export const verified: [_Forward, _Backward, _PropsF, _PropsB, _SigF, _SigB] = [true, true, true, true, true, true];\n`
  );
  writeFileSync(
    join(checkTmp, 'tsconfig.json'),
    JSON.stringify({
      compilerOptions: {
        target: 'ES2022',
        module: 'ESNext',
        moduleResolution: 'bundler',
        allowImportingTsExtensions: true,
        strict: true,
        noEmit: true,
        jsx: 'react-jsx',
        lib: ['ES2022', 'DOM', 'DOM.Iterable'],
        paths: {
          react: [join(tools, '@types/react/index.d.ts')],
          'react/jsx-runtime': [join(tools, '@types/react/jsx-runtime.d.ts')],
        },
      },
      include: [
        join(checkTmp, 'contract-check.ts').replace(/\\/g, '/'),
        join(srcDir, '**/*.ts').replace(/\\/g, '/'),
        join(srcDir, '**/*.tsx').replace(/\\/g, '/'),
      ],
    })
  );
  const tsc = spawnSync(
    process.execPath,
    [join(tools, 'typescript/bin/tsc'), '--project', join(checkTmp, 'tsconfig.json')],
    { encoding: 'utf8' }
  );
  if (tsc.status !== 0) {
    throw new Error(`Elemental Title TypeScript check failed:\n${tsc.stdout}${tsc.stderr}`);
  }
} finally {
  rmSync(checkTmp, { recursive: true, force: true });
}

// Clean previous dist payload files without deleting OneDrive-backed folder handles
const resolvedOut = resolve(outDir);
if (dirname(resolvedOut) !== resolve(pkg)) {
  throw new Error('Package output must stay inside packages/elemental-title/dist');
}
for (const oldFile of walkFiles(outDir)) {
  if (!resolve(oldFile).startsWith(resolvedOut)) {
    throw new Error('Previous package files must stay inside dist');
  }
  unlinkSync(oldFile);
}
mkdirSync(outDir, { recursive: true });

const built = await build({
  entryPoints: [join(srcDir, 'index.ts')],
  bundle: true,
  format: 'esm',
  platform: 'neutral',
  mainFields: ['browser', 'module', 'main'],
  target: ['es2022'],
  jsx: 'automatic',
  external: ['react', 'react/jsx-runtime'],
  write: false,
});

let code = built.outputFiles[0].text.replace(/\r\n/g, '\n');
// Guarantee "use client"; directive sits on line 1 for Next.js App Router consumers
code = code.replace(/^"use client";\n?/m, '');
code = `"use client";\n${code}`;
writeFileSync(join(outDir, 'index.js'), code, 'utf8');

const dts = readFileSync(join(srcDir, 'public.d.ts'), 'utf8').replace(/\r\n/g, '\n');
writeFileSync(join(outDir, 'index.d.ts'), dts, 'utf8');

const css = readFileSync(join(srcDir, 'elemental-title.css'), 'utf8').replace(/\r\n/g, '\n');
writeFileSync(join(outDir, 'styles.css'), css, 'utf8');

const sourceHashes = {};
for (const file of walkFiles(srcDir)) {
  const rel = relative(srcDir, file).replace(/\\/g, '/');
  sourceHashes[rel] = createHash('sha256').update(readFileSync(file)).digest('hex');
}

const provenance = {
  schema: 1,
  package: '@seihouse/elemental-title',
  elements: ['lightning', 'water', 'poison', 'fire', 'frost', 'celestial', 'void', 'none'],
  engineElements: ['lightning', 'water', 'poison'],
  signatures: ['quill/stormwrit', 'quill/true-north'],
  sources: sourceHashes,
  outputs: {
    'index.js': createHash('sha256').update(readFileSync(join(outDir, 'index.js'))).digest('hex'),
    'index.d.ts': createHash('sha256').update(readFileSync(join(outDir, 'index.d.ts'))).digest('hex'),
    'styles.css': createHash('sha256').update(readFileSync(join(outDir, 'styles.css'))).digest('hex'),
  },
};
writeFileSync(join(outDir, 'provenance.json'), JSON.stringify(provenance, null, 2) + '\n', 'utf8');

console.log(
  `Elemental Title package: ${Object.keys(sourceHashes).length} sources compiled -> packages/elemental-title/dist`
);
