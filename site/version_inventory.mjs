/** Public version-history inventory & release-sync validation shared by build_site.mjs and tests. */
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';

const SAFE_VERSION_WOFF2 = /^(?:fonts\/SEIReader-[A-Za-z0-9-]+\.woff2|old\/(?:previous\.woff2|[0-9]+\.[0-9]+\/SEIReader-[A-Za-z0-9-]+\.woff2|display\/[a-z0-9.-]+\/SEIHouseDisplay-[A-Za-z0-9-]+\.woff2)|display\/fonts\/[a-z0-9-]+\/(?:[A-Za-z]+\/)?SEIHouseDisplay-[A-Za-z0-9-]+\.woff2|noto\/studies\/warmth\/fonts\/SEIHouseNoto[A-Za-z0-9-]+\.woff2)$/;

/**
 * Validate `site/versions.json`, `phase4.json`, and `index.html` version badges,
 * then return the deduplicated list of public version-history files to deploy.
 */
export function versionInventory(root) {
  const phase4Path = join(root, 'phase4.json');
  const manifestPath = join(root, 'site/versions.json');
  const homePath = join(root, 'index.html');

  if (!existsSync(phase4Path) || !existsSync(manifestPath) || !existsSync(homePath)) {
    throw new Error('Missing phase4.json, site/versions.json, or index.html for version validation');
  }

  const phase4 = JSON.parse(readFileSync(phase4Path, 'utf8'));
  const expectedSansVersion = String(phase4.version || '').trim();
  if (!expectedSansVersion) {
    throw new Error('Missing version in phase4.json');
  }

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.schema !== 1 || !manifest.tracks) {
    throw new Error('Invalid site/versions.json schema');
  }

  for (const requiredTrack of ['sans', 'display', 'noto']) {
    if (!manifest.tracks[requiredTrack]?.versions?.length) {
      throw new Error(`Missing version track "${requiredTrack}" in site/versions.json`);
    }
  }

  const sansTrack = manifest.tracks.sans;
  if (sansTrack.currentVersion !== expectedSansVersion ||
      sansTrack.versions[0].version !== expectedSansVersion ||
      sansTrack.versions[0].current !== true) {
    throw new Error(
      `Stale SEIHouse Sans version in site/versions.json (${sansTrack.currentVersion} !== ${expectedSansVersion}); run python archive_version.py --sync`
    );
  }

  const homeHtml = readFileSync(homePath, 'utf8');
  const badgeMatches = [...homeHtml.matchAll(/<([a-z0-9]+)\b[^>]*\bdata-sans-version\b[^>]*>([^<]+)<\/\1>/gi)];
  if (!badgeMatches.length) {
    throw new Error('Homepage index.html is missing data-sans-version badges');
  }
  for (const [, , rawText] of badgeMatches) {
    const text = rawText.trim();
    if (text !== expectedSansVersion && text !== `SEIHouse Sans ${expectedSansVersion}`) {
      throw new Error(
        `Stale SEIHouse Sans version badge "${text}" in index.html (expected ${expectedSansVersion}); run python archive_version.py --sync`
      );
    }
  }

  if (!homeHtml.includes(`Current · SEIHouse Sans ${expectedSansVersion}`)) {
    throw new Error(
      `Homepage specimen label in index.html does not match current Sans version ${expectedSansVersion}`
    );
  }

  const woff2Files = [];
  for (const [trackId, track] of Object.entries(manifest.tracks)) {
    for (const entry of track.versions) {
      if (!entry.version || !entry.faces?.length) {
        throw new Error(`Incomplete version entry in track "${trackId}"`);
      }
      for (const face of entry.faces) {
        const relPath = face.path;
        if (typeof relPath !== 'string' ||
            relPath.includes('\\') ||
            resolve(root, relPath) !== join(root, relPath) ||
            !SAFE_VERSION_WOFF2.test(relPath)) {
          throw new Error(`Invalid version website asset: ${relPath}`);
        }
        const diskPath = join(root, relPath);
        if (!existsSync(diskPath)) {
          throw new Error(`Missing archived font file: ${relPath}`);
        }
        const bytes = readFileSync(diskPath);
        if (bytes.length < 4 || bytes.subarray(0, 4).toString('ascii') !== 'wOF2') {
          throw new Error(`Corrupt WOFF2 header in archived font: ${relPath}`);
        }
        const digest = createHash('sha256').update(bytes).digest('hex');
        if (bytes.length !== face.bytes || digest !== face.sha256) {
          throw new Error(`Stale version asset inventory: ${relPath}; run python archive_version.py --sync`);
        }
        woff2Files.push(relPath);
      }
    }
  }

  return [...new Set([
    'site/versions.json',
    'site/versions/index.html',
    'site/versions/versions.css',
    'site/versions/versions.js',
    ...woff2Files,
  ])];
}
