import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const legacy = JSON.parse(readFileSync(new URL('fixtures/reader-curve-sources.json', import.meta.url), 'utf8'));
const symbols043 = JSON.parse(readFileSync(new URL('fixtures/reader-symbol-sources-0.43.json', import.meta.url), 'utf8'));

export const REFINED_SYMBOLS_043 = symbols043.refined_symbols;

/** Restore the 0.42 symbol definitions while keeping all 0.43 engine plumbing intact. */
export function beforeSymbols043(source) {
  const normalized = source.replace(/\r\n/g, '\n');
  const start = normalized.indexOf(symbols043.start_marker);
  if (start < 0) return source;
  const end = normalized.indexOf(symbols043.end_anchor, start);
  assert.ok(end > start, 'Missing end anchor for 0.43 symbol block');
  return normalized.slice(0, start) + symbols043.block_042 + normalized.slice(end);
}

/** Restore only the three original definitions (and pre-0.43 symbols) to audit frozen historical exports. */
export function beforeReadingCurves(source) {
  source = beforeSymbols043(source);
  for (const [ch, definition] of Object.entries(legacy.definitions)) {
    const start = source.indexOf(`def('${ch}',`);
    assert.ok(start >= 0, `Missing ${ch} definition`);
    const end = source.indexOf(';', start) + 1;
    assert.ok(end > start, `Unterminated ${ch} definition`);
    source = source.slice(0, start) + definition + source.slice(end);
  }
  return source;
}
