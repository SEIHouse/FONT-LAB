/** Install packed @seihouse/elemental-title in a clean consumer; typecheck, bundle, and run browser gates. */
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from './node_modules/esbuild/lib/main.js';
import { npm } from './package_tools.mjs';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const tools = join(root, 'display/node_modules');
const release = JSON.parse(
  readFileSync(join(root, 'packages/elemental-title/releases/release.json'), 'utf8')
);
const temporary = mkdtempSync(join(tmpdir(), 'elemental-title-consumer-'));
if (
  dirname(resolve(temporary)) !== resolve(tmpdir()) ||
  !temporary.startsWith(join(tmpdir(), 'elemental-title-consumer-'))
) {
  throw new Error('Invalid consumer temporary directory');
}

function run(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: temporary, encoding: 'utf8' });
  if (r.status !== 0) {
    throw new Error(r.stdout + r.stderr + (r.error?.message || ''));
  }
  return r.stdout;
}

try {
  writeFileSync(
    join(temporary, 'package.json'),
    JSON.stringify({ name: 'elemental-title-packed-consumer', private: true, type: 'module' })
  );
  npm(
    [
      'install',
      '--ignore-scripts',
      '--legacy-peer-deps',
      '--no-audit',
      '--no-fund',
      join(root, 'packages/elemental-title/releases', release.filename),
    ],
    temporary
  );

  // Verify manifest & Next.js "use client" directive
  const installedPkg = JSON.parse(
    readFileSync(join(temporary, 'node_modules/@seihouse/elemental-title/package.json'), 'utf8')
  );
  if (installedPkg.dependencies) {
    throw new Error('Unexpected mandatory dependencies in @seihouse/elemental-title');
  }
  const installedJs = readFileSync(
    join(temporary, 'node_modules/@seihouse/elemental-title/dist/index.js'),
    'utf8'
  );
  if (!installedJs.startsWith('"use client";')) {
    throw new Error('Packed dist/index.js is missing leading "use client"; directive');
  }

  // Strict TypeScript consumer check
  writeFileSync(
    join(temporary, 'consumer.tsx'),
    `import { ElementalTitle, type ElementalTitleMoment, type ElementalTitleSignature } from '@seihouse/elemental-title';\n` +
      `const sigs: readonly ElementalTitleSignature[] = ['quill/stormwrit', 'quill/true-north'];\n` +
      `export const view = (\n` +
      `  <ElementalTitle\n` +
      `    as="h2"\n` +
      `    element="lightning"\n` +
      `    color="light-dark(#8a5a12, #f6cf7f)"\n` +
      `    intensity="legendary"\n` +
      `    shadow="outlined"\n` +
      `    signatures={sigs}\n` +
      `    onMoment={(m: ElementalTitleMoment) => void m.id}\n` +
      `  >\n` +
      `    Kept Reading\n` +
      `  </ElementalTitle>\n` +
      `);\n`
  );
  writeFileSync(
    join(temporary, 'tsconfig.json'),
    JSON.stringify({
      compilerOptions: {
        target: 'ES2022',
        module: 'NodeNext',
        moduleResolution: 'NodeNext',
        strict: true,
        noEmit: true,
        jsx: 'react-jsx',
        lib: ['ES2022', 'DOM'],
        paths: {
          react: [join(tools, '@types/react/index.d.ts')],
          'react/jsx-runtime': [join(tools, '@types/react/jsx-runtime.d.ts')],
        },
      },
      include: ['consumer.tsx'],
    })
  );
  run(process.execPath, [join(tools, 'typescript/bin/tsc'), '--project', 'tsconfig.json']);

  // Bundle React 19 browser test app
  copyFileSync(
    join(temporary, 'node_modules/@seihouse/elemental-title/dist/styles.css'),
    join(temporary, 'elemental-title.css')
  );
  const browserEntry = `
    import React, { useState } from 'react';
    import { createRoot } from 'react-dom/client';
    import { ElementalTitle } from '@seihouse/elemental-title';

    window.moments = [];
    let nextKey = 0;

    function App() {
      const [moment, setMoment] = useState(undefined);
      window.playStrike = () => setMoment({ id: 'strike', key: ++nextKey });
      window.playSignature = (signature) => setMoment({ id: 'signature', key: ++nextKey, signature });
      return React.createElement(
        'div',
        { style: { padding: '32px', background: '#0b1018', color: '#f6cf7f', colorScheme: 'dark' } },
        React.createElement(
          'div',
          { id: 'lightning' },
          React.createElement(
            ElementalTitle,
            {
              as: 'h2',
              element: 'lightning',
              intensity: 'legendary',
              color: '#f6cf7f',
              signatures: ['quill/stormwrit', 'quill/true-north'],
              playMoment: moment,
              onMoment: (m) => window.moments.push(m),
              style: { fontSize: '32px' },
            },
            'Kept Reading'
          )
        ),
        React.createElement(
          'div',
          { id: 'water', style: { marginTop: '24px' } },
          React.createElement(
            ElementalTitle,
            {
              as: 'h2',
              element: 'water',
              intensity: 'legendary',
              color: '#86e3ae',
              style: { fontSize: '28px' },
            },
            'Still Waters'
          )
        )
      );
    }

    const root = createRoot(document.getElementById('root'));
    root.render(React.createElement(React.StrictMode, null, React.createElement(App)));
    window.unmount = () => root.unmount();
  `;
  await build({
    stdin: { contents: browserEntry, resolveDir: temporary, loader: 'js' },
    bundle: true,
    format: 'esm',
    platform: 'browser',
    nodePaths: [tools],
    outfile: join(temporary, 'consumer.js'),
  });
  writeFileSync(
    join(temporary, 'index.html'),
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<link rel="stylesheet" href="elemental-title.css">' +
      '<div id="root"></div><script type="module" src="consumer.js"></script>'
  );

  const python =
    process.platform === 'win32' ? join(root, '.venv/Scripts/python.exe') : 'python';
  console.log(run(python, [join(root, 'display/verify_elemental_browser.py'), temporary]));

  mkdirSync(join(root, 'dist'), { recursive: true });
  writeFileSync(
    join(root, 'dist/elemental-package-consumer.json'),
    JSON.stringify(
      {
        artifact: release.filename,
        sha256: release.sha256,
        checks: [
          'clean archive install',
          'zero mandatory runtime dependencies',
          'Next.js use client directive',
          'strict public TypeScript',
          'React 19 browser bundle',
          'Lightning/Water stage, strike, Quill Stormwrit signature, reduced motion & disposal gates',
        ],
        flags: [],
      },
      null,
      2
    ) + '\n',
    'utf8'
  );
  console.log(
    'Elemental Title packed consumer: install, types, React bundle and browser lifecycle passed'
  );
} finally {
  rmSync(temporary, { recursive: true, force: true });
}
