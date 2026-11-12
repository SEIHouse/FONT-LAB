(() => {
  const byId = id => document.getElementById(id);
  const themeBtn = byId('theme');

  const displayCuts = {
    soft: {
      family: 'DisplaySoft',
      name: 'Soft',
      note: 'Rounded, welcoming strokes with warm terminals—built for lyrical covers and gentle chapter openings.',
    },
    edge: {
      family: 'DisplayEdge',
      name: 'Edge',
      note: 'Crisp flat terminals and decisive corners—built for sharp fantasy titles and bold posters.',
    },
    ink: {
      family: 'DisplayInk',
      name: 'Ink',
      note: 'High-contrast calligraphic energy—built for literary covers and expressive signatures.',
    },
    wide: {
      family: 'DisplayWide',
      name: 'Wide',
      note: 'Expansive, cinematic proportions—built for widescreen headers, album art, and emblems.',
    },
  };

  let sansItalic = false;
  let activeCut = 'edge';
  let displayAllCaps = false;
  let versionsCache = null;
  let sansUpdateSeq = 0;
  const loadedFaces = new Map();

  /** Fit a resizable textarea cleanly to its wrapped lines up to maxPx. */
  function fitTextarea(el, maxPx) {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight + 4, maxPx) + 'px';
  }

  /** Fetch site/versions.json once when needed for quick historical comparison. */
  async function loadManifest() {
    if (versionsCache) return versionsCache;
    const response = await fetch('./site/versions.json');
    if (!response.ok) throw new Error('Could not load version manifest');
    versionsCache = await response.json();
    return versionsCache;
  }

  /** Dynamically register a single historical WOFF2 face on demand. */
  async function ensureHistoricalFace(versionEntry, weight, italic, nightMode) {
    const caps = versionEntry.capabilities || { weights: [400], italic: false, nightWeights: [] };
    const resolvedWeight = caps.weights.includes(Number(weight)) ? Number(weight) : 400;
    const resolvedItalic = Boolean(italic && caps.italic);
    const useNight = Boolean(nightMode && (caps.nightWeights || []).includes(resolvedWeight));
    const styleStr = resolvedItalic ? 'italic' : 'normal';

    const faceObj = versionEntry.faces.find(
      f => f.weight === resolvedWeight && f.style === styleStr && Boolean(f.night) === useNight
    ) || versionEntry.faces[0];

    const familyName = `ArchiveSans_${versionEntry.version.replace(/[^a-zA-Z0-9]/g, '_')}_${useNight ? 'N' : 'D'}`;
    const cacheKey = `${familyName}:${faceObj.weight}:${faceObj.style}`;

    if (!loadedFaces.has(cacheKey) && typeof FontFace === 'function') {
      const loader = (async () => {
        const ff = new FontFace(familyName, `url("./${faceObj.path}") format("woff2")`, {
          weight: String(faceObj.weight),
          style: faceObj.style,
          display: 'swap',
        });
        const loaded = await ff.load();
        document.fonts.add(loaded);
        return familyName;
      })();
      loadedFaces.set(cacheKey, loader);
    }
    if (loadedFaces.has(cacheKey)) {
      await loadedFaces.get(cacheKey);
    }
    return { familyName, resolvedWeight, resolvedItalic, useNight };
  }

  /** Update the SEIHouse Sans live specimen and optional quick side-by-side comparison. */
  async function updateSansSpecimen() {
    const seq = ++sansUpdateSeq;
    const sample = byId('specimen');
    const weight = byId('sans-weight').value;
    const size = byId('sans-size').value;
    const compareVer = byId('sans-compare').value;
    const isNight = document.documentElement.dataset.theme !== 'day';
    const hasNightGrade = isNight && ['300', '400', '500'].includes(weight);

    sample.style.fontFamily = (hasNightGrade ? '"SEIReader Night", SEIReader' : 'SEIReader') + ', sans-serif';
    sample.style.fontSize = size + 'px';
    sample.style.fontWeight = weight;
    sample.style.fontStyle = sansItalic ? 'italic' : 'normal';

    byId('sans-italic').setAttribute('aria-pressed', String(sansItalic));
    byId('sans-size-value').textContent = size + 'px';
    byId('sans-grade-note').textContent = isNight
      ? (hasNightGrade ? 'Night optical grade active (-4 units, zero reflow)' : 'Day stroke weight (Night grade applies to 300–500)')
      : 'Day mode stroke weight';

    const wrap = byId('sans-compare-wrap');
    const oldCol = byId('sans-old-column');
    const oldPreview = byId('sans-old-preview');

    if (!compareVer) {
      wrap.dataset.comparing = 'false';
      oldCol.hidden = true;
      fitTextarea(sample, 416);
      return;
    }

    wrap.dataset.comparing = 'true';
    oldCol.hidden = false;
    oldPreview.textContent = sample.value;
    oldPreview.style.fontSize = Math.max(14, Math.round(Number(size) * 0.9)) + 'px';
    byId('sans-full-compare-link').href = `./site/versions/index.html?track=sans&left=0.42&right=${encodeURIComponent(compareVer)}`;
    fitTextarea(sample, 416);

    try {
      const manifest = await loadManifest();
      if (seq !== sansUpdateSeq) return;
      const entry = manifest.tracks.sans.versions.find(v => v.version === compareVer);
      if (!entry) return;
      byId('sans-old-label').textContent = `${entry.version} · ${entry.shortTitle}`;
      const loaded = await ensureHistoricalFace(entry, weight, sansItalic, isNight);
      if (seq !== sansUpdateSeq) return;
      oldPreview.style.fontFamily = `"${loaded.familyName}", sans-serif`;
      oldPreview.style.fontWeight = String(loaded.resolvedWeight);
      oldPreview.style.fontStyle = loaded.resolvedItalic ? 'italic' : 'normal';

      const notes = [entry.shortTitle + '.'];
      if (loaded.resolvedWeight !== Number(weight) || loaded.resolvedItalic !== sansItalic) {
        notes.push('Regular upright only.');
      } else if (isNight && hasNightGrade && !loaded.useNight) {
        notes.push(`Predates Night grade for ${weight}.`);
      }
      byId('sans-old-note').textContent = notes.join(' ');
    } catch {
      byId('sans-old-note').textContent = 'Open Past versions to compare archived fonts.';
    }
  }

  /** Update the Title Engine live specimen across Soft, Edge, Ink, and Wide. */
  function updateDisplaySpecimen() {
    const cut = displayCuts[activeCut] || displayCuts.edge;
    const sample = byId('display-specimen');
    const size = byId('display-size').value;

    sample.style.fontFamily = `"${cut.family}", sans-serif`;
    sample.style.fontSize = size + 'px';
    sample.style.textTransform = displayAllCaps ? 'uppercase' : 'none';
    sample.style.fontFeatureSettings = displayAllCaps ? '"cpsp" 1' : 'normal';

    byId('display-size-value').textContent = size + 'px';
    byId('display-caps').setAttribute('aria-pressed', String(displayAllCaps));

    const noteEl = byId('display-cut-note');
    noteEl.innerHTML = '';
    const strong = document.createElement('strong');
    strong.textContent = `${cut.name}: `;
    noteEl.append(strong, document.createTextNode(cut.note));

    document.querySelectorAll('.cut-tab').forEach(btn => {
      btn.setAttribute('aria-pressed', String(btn.dataset.cut === activeCut));
    });
    fitTextarea(sample, 384);
  }

  /** Apply Day or Night mode and reflect it in browser chrome and specimens. */
  function setTheme(value) {
    const day = value === 'day';
    document.documentElement.dataset.theme = day ? 'day' : 'night';
    themeBtn.textContent = day ? 'Night mode' : 'Day mode';
    themeBtn.setAttribute('aria-pressed', String(day));
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = day ? '#f4f3ea' : '#141917';
  }

  try {
    setTheme(localStorage.getItem('seihouse.home.theme'));
  } catch {
    setTheme('night');
  }

  themeBtn.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'day' ? 'night' : 'day';
    setTheme(next);
    updateSansSpecimen();
    try {
      localStorage.setItem('seihouse.home.theme', next);
    } catch { /* Theme works without storage. */ }
  });

  ['sans-weight', 'sans-size', 'sans-compare'].forEach(id => {
    byId(id).addEventListener('input', updateSansSpecimen);
    byId(id).addEventListener('change', updateSansSpecimen);
  });

  byId('sans-italic').addEventListener('click', () => {
    sansItalic = !sansItalic;
    updateSansSpecimen();
  });

  byId('specimen').addEventListener('input', () => {
    fitTextarea(byId('specimen'), 416);
    const oldPreview = byId('sans-old-preview');
    if (oldPreview && !byId('sans-old-column').hidden) {
      oldPreview.textContent = byId('specimen').value;
    }
  });

  document.querySelectorAll('.cut-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      activeCut = btn.dataset.cut;
      updateDisplaySpecimen();
    });
  });

  byId('display-size').addEventListener('input', updateDisplaySpecimen);
  byId('display-caps').addEventListener('click', () => {
    displayAllCaps = !displayAllCaps;
    updateDisplaySpecimen();
  });
  byId('display-specimen').addEventListener('input', () => fitTextarea(byId('display-specimen'), 384));

  window.addEventListener('resize', () => {
    fitTextarea(byId('specimen'), 416);
    fitTextarea(byId('display-specimen'), 384);
  });

  if (document.fonts?.ready) {
    document.fonts.ready.then(() => {
      fitTextarea(byId('specimen'), 416);
      fitTextarea(byId('display-specimen'), 384);
    });
  }

  updateSansSpecimen();
  updateDisplaySpecimen();
})();
