import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const legacy = JSON.parse(readFileSync(new URL('fixtures/reader-curve-sources.json', import.meta.url), 'utf8'));

/** Restore only the three original definitions to audit the frozen historical exports. */
export function beforeReadingCurves(source) {
  for (const [ch, definition] of Object.entries(legacy.definitions)) {
    const start = source.indexOf(`def('${ch}',`);
    assert.ok(start >= 0, `Missing ${ch} definition`);
    const end = source.indexOf(';', start) + 1;
    assert.ok(end > start, `Unterminated ${ch} definition`);
    source = source.slice(0, start) + definition + source.slice(end);
  }
  return source;
}
