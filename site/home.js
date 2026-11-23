(() => {
  const byId = id => document.getElementById(id);

  const VIEWS = ['fonts', 'lab', 'download'];
  const FONT_SUBTABS = ['normal', 'title', 'special'];
  const DL_SUBTABS = ['current', 'legacy'];
  const DL_FONTS = ['sans', 'noto', 'display'];

  const VIEW_LABELS = {
    fonts: 'Fonts',
    lab: 'Lab',
    download: 'Download',
  };

  const TRACK_META = {
    sans: {
      label: 'SEIHouse Sans',
      accent: 'var(--fl-sans)',
      badgeClass: 'sei-badge sei-badge--sans',
      legacyCountFallback: 17,
    },
    noto: {
      label: 'SEIHouse Noto',
      accent: 'var(--fl-noto)',
      badgeClass: 'sei-badge sei-badge--noto',
      legacyCountFallback: 4,
    },
    display: {
      label: 'SEIHouse Display',
      accent: 'var(--fl-display)',
      badgeClass: 'sei-badge sei-badge--display',
      legacyCountFallback: 7,
    },
  };

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

  const elementalPresets = {
    lightning: { kicker: 'LIGHTNING · STORMWRIT SIGNATURE', word: 'Stormwrit' },
    water: { kicker: 'WATER · TIDECALLER SIGNATURE', word: 'Tidecaller' },
    celestial: { kicker: 'CELESTIAL · TRUE NORTH SIGNATURE', word: 'True North' },
    fire: { kicker: 'FIRE · EMBERBLADE SIGNATURE', word: 'Emberblade' },
  };

  let activeView = 'fonts';
  let activeFontTab = 'normal';
  let activeDlTab = 'current';
  let activeDlFont = 'sans';

  let sansItalic = false;
  let notoItalic = false;
  let activeCut = 'edge';
  let displayAllCaps = false;

  let versionsCache = null;
  let versionsPromise = null;
  let sansUpdateSeq = 0;
  const loadedFaces = new Map();

  /** Fit a resizable textarea cleanly to its wrapped lines up to maxPx. */
  function fitTextarea(el, maxPx) {
    if (!el || el.offsetParent === null) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight + 4, maxPx) + 'px';
  }

  function fitVisibleTextareas() {
    fitTextarea(byId('specimen'), 352);
    fitTextarea(byId('noto-specimen'), 300);
    fitTextarea(byId('display-specimen'), 384);
  }

  /** Fetch site/versions.json once (shared by Quick Compare and Legacy Downloads). */
  async function loadManifest() {
    if (versionsCache) return versionsCache;
    if (!versionsPromise) {
      versionsPromise = fetch('./site/versions.json').then(res => {
        if (!res.ok) throw new Error('Could not load version manifest');
        return res.json();
      }).then(data => {
        versionsCache = data;
        return data;
      }).catch(err => {
        versionsPromise = null;
        throw err;
      });
    }
    return versionsPromise;
  }

  /* ========================================================================
     Navigation & Routing (Bottom Bar + Subtabs + Hash Sync)
     ======================================================================== */

  function updateHash() {
    let hash = `#${activeView}`;
    if (activeView === 'fonts' && activeFontTab !== 'normal') {
      hash = `#fonts/${activeFontTab}`;
    } else if (activeView === 'download') {
      if (activeDlFont !== 'sans' || activeDlTab !== 'current') {
        hash = `#download/${activeDlFont}/${activeDlTab}`;
      }
    }
    if (window.location.hash !== hash) {
      history.replaceState(null, '', hash);
    }
  }

  function setView(view, { scrollTop = false, syncHash = true } = {}) {
    if (!VIEWS.includes(view)) view = 'fonts';
    activeView = view;

    for (const v of VIEWS) {
      const section = byId(`view-${v}`);
      if (section) section.hidden = v !== view;
    }

    document.querySelectorAll('[data-slot="bottom-nav-tab"]').forEach(btn => {
      const isCurrent = btn.dataset.nav === view;
      if (isCurrent) {
        btn.setAttribute('aria-current', 'page');
        btn.dataset.selected = 'true';
      } else {
        btn.removeAttribute('aria-current');
        delete btn.dataset.selected;
      }
    });

    const ctx = byId('header-context-label');
    if (ctx) ctx.textContent = VIEW_LABELS[view] || 'Fonts';

    if (view === 'download') {
      updateDownloadUI();
    }

    if (syncHash) updateHash();
    if (scrollTop) {
      try {
        window.scrollTo({ top: 0, behavior: 'instant' });
      } catch {
        window.scrollTo(0, 0);
      }
    }

    requestAnimationFrame(fitVisibleTextareas);
  }

  function setFontSubtab(subtab, { syncHash = true } = {}) {
    if (!FONT_SUBTABS.includes(subtab)) subtab = 'normal';
    activeFontTab = subtab;

    document.querySelectorAll('[data-tablist="fonts"] [role="tab"]').forEach(tab => {
      const selected = tab.dataset.subtab === subtab;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });

    for (const t of FONT_SUBTABS) {
      const panel = byId(`panel-fonts-${t}`);
      if (panel) panel.hidden = t !== subtab;
    }

    if (syncHash) updateHash();
    requestAnimationFrame(fitVisibleTextareas);
  }

  function setDownloadSubtab(subtab, { syncHash = true } = {}) {
    if (!DL_SUBTABS.includes(subtab)) subtab = 'current';
    activeDlTab = subtab;

    document.querySelectorAll('[data-tablist="download"] [role="tab"]').forEach(tab => {
      const selected = tab.dataset.subtab === subtab;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });

    for (const t of DL_SUBTABS) {
      const panel = byId(`panel-dl-${t}`);
      if (panel) panel.hidden = t !== subtab;
    }

    if (subtab === 'legacy') {
      renderLegacyDownloads();
    }

    if (syncHash) updateHash();
  }

  function setDownloadFont(fontId, { syncHash = true } = {}) {
    if (!DL_FONTS.includes(fontId)) fontId = 'sans';
    activeDlFont = fontId;

    document.querySelectorAll('.font-pick-chip').forEach(chip => {
      const checked = chip.dataset.dlFont === fontId;
      chip.setAttribute('aria-checked', String(checked));
      chip.tabIndex = checked ? 0 : -1;
    });

    document.querySelectorAll('[data-current-font]').forEach(card => {
      card.hidden = card.dataset.currentFont !== fontId;
    });

    updateDownloadUI();
    if (syncHash) updateHash();
  }

  function updateDownloadUI() {
    const meta = TRACK_META[activeDlFont] || TRACK_META.sans;
    const countBadge = byId('legacy-count-badge');
    if (countBadge) {
      const manifestCount = versionsCache?.tracks?.[activeDlFont]?.versions?.filter(v => !v.current).length;
      countBadge.textContent = String(manifestCount ?? meta.legacyCountFallback);
    }
    if (activeDlTab === 'legacy') {
      renderLegacyDownloads();
    }
  }

  /** Apply initial or changed URL hash (including backwards-compatible legacy anchors). */
  function applyHashRoute() {
    const raw = window.location.hash.replace(/^#/, '').trim().toLowerCase();
    if (!raw) {
      setView('fonts', { syncHash: false });
      setFontSubtab('normal', { syncHash: false });
      return;
    }

    // Legacy homepage anchors remain gracefully supported.
    if (raw === 'reading-fonts') {
      setView('fonts', { syncHash: false });
      setFontSubtab('normal', { syncHash: false });
      return;
    }
    if (raw === 'title-engine') {
      setView('fonts', { syncHash: false });
      setFontSubtab('title', { syncHash: false });
      return;
    }
    if (raw === 'resources') {
      setView('download', { syncHash: false });
      return;
    }

    const parts = raw.split('/').filter(Boolean);
    const top = parts[0];
    if (top === 'fonts') {
      setView('fonts', { syncHash: false });
      if (FONT_SUBTABS.includes(parts[1])) {
        setFontSubtab(parts[1], { syncHash: false });
      }
    } else if (top === 'lab') {
      setView('lab', { syncHash: false });
    } else if (top === 'download') {
      if (DL_FONTS.includes(parts[1])) {
        setDownloadFont(parts[1], { syncHash: false });
      }
      if (DL_SUBTABS.includes(parts[2])) {
        setDownloadSubtab(parts[2], { syncHash: false });
      } else if (DL_SUBTABS.includes(parts[1])) {
        setDownloadSubtab(parts[1], { syncHash: false });
      }
      setView('download', { syncHash: false });
    }
  }

  /** Shared roving keyboard handler for horizontal tablists and radio groups. */
  function bindHorizontalKeys(container, itemSelector, onActivate) {
    if (!container) return;
    container.addEventListener('keydown', event => {
      const items = [...container.querySelectorAll(itemSelector)];
      if (!items.length) return;
      const idx = items.indexOf(document.activeElement);
      if (idx === -1) return;

      let next = -1;
      if (event.key === 'ArrowRight') next = (idx + 1) % items.length;
      else if (event.key === 'ArrowLeft') next = (idx - 1 + items.length) % items.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = items.length - 1;
      else return;

      event.preventDefault();
      items[next].focus();
      onActivate(items[next]);
    });
  }

  /* ========================================================================
     Legacy Downloads Renderer (from site/versions.json)
     ======================================================================== */

  function formatFaceLabel(face) {
    const raw = face.styleName || face.path.split('/').pop().replace(/\.woff2$/i, '');
    return raw.replace(/([a-z])([A-Z])/g, '$1 $2');
  }

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) return '';
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  function createFaceDownloadLink(face) {
    const a = document.createElement('a');
    a.className = 'legacy-file-link';
    a.href = `./${face.path}`;
    a.setAttribute('download', '');
    const nameSpan = document.createElement('span');
    nameSpan.textContent = formatFaceLabel(face);
    const metaSpan = document.createElement('span');
    metaSpan.className = 'dl-ext';
    const kb = formatBytes(face.bytes);
    metaSpan.textContent = kb ? `${kb} ↓` : '↓';
    a.append(nameSpan, metaSpan);
    return a;
  }

  async function renderLegacyDownloads() {
    const listEl = byId('legacy-list');
    const legacyCard = byId('legacy-card');
    const badgeEl = byId('legacy-track-badge');
    const headingEl = byId('legacy-heading');
    const compareAllEl = byId('legacy-compare-all');
    if (!listEl) return;

    const trackId = activeDlFont;
    const meta = TRACK_META[trackId] || TRACK_META.sans;

    if (legacyCard) legacyCard.style.setProperty('--sh-card-accent', meta.accent);
    if (badgeEl) {
      badgeEl.className = meta.badgeClass;
      badgeEl.textContent = meta.label;
    }
    if (headingEl) headingEl.textContent = `${meta.label} · Legacy`;
    if (compareAllEl) compareAllEl.href = `./site/versions/index.html?track=${encodeURIComponent(trackId)}`;

    try {
      const manifest = await loadManifest();
      if (trackId !== activeDlFont) return;

      const track = manifest?.tracks?.[trackId];
      const legacyVersions = (track?.versions || []).filter(v => !v.current);

      const countBadge = byId('legacy-count-badge');
      if (countBadge) countBadge.textContent = String(legacyVersions.length);

      listEl.textContent = '';

      if (!legacyVersions.length) {
        const empty = document.createElement('p');
        empty.className = 'legacy-loading';
        empty.textContent = 'No archived older versions for this font yet.';
        listEl.append(empty);
        return;
      }

      for (const entry of legacyVersions) {
        const row = document.createElement('article');
        row.className = 'legacy-row';

        const top = document.createElement('div');
        top.className = 'legacy-row-top';

        const idGroup = document.createElement('div');
        idGroup.className = 'legacy-row-id';

        const verTag = document.createElement('span');
        verTag.className = 'legacy-ver-tag';
        verTag.textContent = entry.version;

        const verTitle = document.createElement('span');
        verTitle.className = 'legacy-ver-title';
        verTitle.textContent = entry.shortTitle || entry.label || '';

        idGroup.append(verTag, verTitle);

        if (entry.date) {
          const verDate = document.createElement('span');
          verDate.className = 'legacy-ver-date';
          verDate.textContent = entry.date;
          idGroup.append(verDate);
        }

        const actions = document.createElement('div');
        actions.className = 'legacy-row-actions';

        const compareLink = document.createElement('a');
        compareLink.className = 'sei-button sei-button--sm sei-button--ghost';
        compareLink.href = `./site/versions/index.html?track=${encodeURIComponent(trackId)}&right=${encodeURIComponent(entry.version)}`;
        compareLink.textContent = 'Compare ↗';
        actions.append(compareLink);

        top.append(idGroup, actions);
        row.append(top);

        const faces = entry.faces || [];
        const filesWrap = document.createElement('div');
        filesWrap.className = 'legacy-files';

        const MAX_INLINE = 4;
        let primaryFaces = faces;
        let extraFaces = [];

        if (faces.length > MAX_INLINE) {
          const preferred = ['Regular', 'Italic', 'Bold', 'RegularNight', 'Edge', 'Soft', 'Ink', 'Wide'];
          const picked = [];
          for (const key of preferred) {
            const match = faces.find(f => f.styleName === key && !picked.includes(f));
            if (match && picked.length < MAX_INLINE) picked.push(match);
          }
          for (const f of faces) {
            if (picked.length >= MAX_INLINE) break;
            if (!picked.includes(f)) picked.push(f);
          }
          primaryFaces = picked;
          extraFaces = faces.filter(f => !picked.includes(f));
        }

        for (const face of primaryFaces) {
          filesWrap.append(createFaceDownloadLink(face));
        }

        if (extraFaces.length) {
          const extraLinks = extraFaces.map(face => {
            const link = createFaceDownloadLink(face);
            link.hidden = true;
            return link;
          });
          const toggleBtn = document.createElement('button');
          toggleBtn.type = 'button';
          toggleBtn.className = 'legacy-more-btn';
          toggleBtn.setAttribute('aria-expanded', 'false');
          toggleBtn.textContent = `+${extraFaces.length} more files`;
          toggleBtn.addEventListener('click', () => {
            const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
            const next = !expanded;
            toggleBtn.setAttribute('aria-expanded', String(next));
            toggleBtn.textContent = next ? 'Show fewer' : `+${extraFaces.length} more files`;
            for (const link of extraLinks) link.hidden = !next;
          });
          filesWrap.append(...extraLinks, toggleBtn);
        }

        row.append(filesWrap);
        listEl.append(row);
      }
    } catch {
      listEl.textContent = '';
      const fallback = document.createElement('p');
      fallback.className = 'legacy-loading';
      fallback.textContent = 'Could not load version history here. Open Version Compare to browse all archived releases.';
      listEl.append(fallback);
    }
  }

  /* ========================================================================
     Live Font Specimens (Sans, Noto, Display, Special)
     ======================================================================== */

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

  async function updateSansSpecimen() {
    const seq = ++sansUpdateSeq;
    const sample = byId('specimen');
    if (!sample) return;

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
      fitTextarea(sample, 352);
      return;
    }

    wrap.dataset.comparing = 'true';
    oldCol.hidden = false;
    oldPreview.textContent = sample.value;
    oldPreview.style.fontSize = Math.max(14, Math.round(Number(size) * 0.9)) + 'px';
    byId('sans-full-compare-link').href = `./site/versions/index.html?track=sans&right=${encodeURIComponent(compareVer)}`;
    fitTextarea(sample, 352);

    try {
      const manifest = await loadManifest();
      if (seq !== sansUpdateSeq) return;
      const baseVer = manifest?.tracks?.sans?.currentVersion;
      if (baseVer) {
        byId('sans-full-compare-link').href = `./site/versions/index.html?track=sans&left=${encodeURIComponent(baseVer)}&right=${encodeURIComponent(compareVer)}`;
      }
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
      byId('sans-old-note').textContent = 'Open Version Compare to inspect archived fonts.';
    }
  }

  function updateNotoSpecimen() {
    const sample = byId('noto-specimen');
    if (!sample) return;

    const weight = byId('noto-weight').value;
    const size = byId('noto-size').value;
    const isNight = document.documentElement.dataset.theme !== 'day';
    const hasNightGrade = isNight && ['300', '400', '500'].includes(weight);

    sample.style.fontFamily = (hasNightGrade ? '"SEIHouseNotoNight", "SEIHouseNotoBalanced"' : '"SEIHouseNotoBalanced"') + ', sans-serif';
    sample.style.fontSize = size + 'px';
    sample.style.fontWeight = weight;
    sample.style.fontStyle = notoItalic ? 'italic' : 'normal';

    byId('noto-italic').setAttribute('aria-pressed', String(notoItalic));
    byId('noto-size-value').textContent = size + 'px';
    byId('noto-grade-note').textContent = isNight
      ? (hasNightGrade ? 'Night optical grade active (zero reflow)' : 'Day stroke weight (Night grade applies to 300–500)')
      : 'Day mode stroke weight';

    fitTextarea(sample, 300);
  }

  function updateDisplaySpecimen() {
    const cut = displayCuts[activeCut] || displayCuts.edge;
    const sample = byId('display-specimen');
    if (!sample) return;

    const size = byId('display-size').value;

    sample.style.fontFamily = `"${cut.family}", sans-serif`;
    sample.style.fontSize = size + 'px';
    sample.style.textTransform = displayAllCaps ? 'uppercase' : 'none';
    sample.style.fontFeatureSettings = displayAllCaps ? '"cpsp" 1' : 'normal';

    byId('display-size-value').textContent = size + 'px';
    byId('display-caps').setAttribute('aria-pressed', String(displayAllCaps));

    const noteEl = byId('display-cut-note');
    noteEl.textContent = '';
    const strong = document.createElement('strong');
    strong.textContent = `${cut.name}: `;
    noteEl.append(strong, document.createTextNode(cut.note));

    document.querySelectorAll('.cut-tab').forEach(btn => {
      btn.setAttribute('aria-pressed', String(btn.dataset.cut === activeCut));
    });
    fitTextarea(sample, 384);
  }

  /* ========================================================================
     Theme Toggle (Day / Night + Multi-tab storage sync)
     ======================================================================== */

  function setTheme(value) {
    const day = value === 'day';
    document.documentElement.dataset.theme = day ? 'day' : 'night';

    const themeBtn = byId('theme');
    const themeIcon = byId('theme-icon');
    const themeLabel = byId('theme-label');
    if (themeBtn) themeBtn.setAttribute('aria-pressed', String(day));
    if (themeIcon) themeIcon.textContent = day ? '☾' : '☀';
    if (themeLabel) themeLabel.textContent = day ? 'Night' : 'Day';

    const metaScheme = document.querySelector('meta[name="color-scheme"]');
    if (metaScheme) metaScheme.content = day ? 'light' : 'dark';

    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = day ? '#f5f4ec' : '#0f1311';
  }

  /* ========================================================================
     Event Wiring
     ======================================================================== */

  // Theme initialization & toggle
  try {
    setTheme(localStorage.getItem('seihouse.home.theme'));
  } catch {
    setTheme('night');
  }

  byId('theme')?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'day' ? 'night' : 'day';
    setTheme(next);
    updateSansSpecimen();
    updateNotoSpecimen();
    try {
      localStorage.setItem('seihouse.home.theme', next);
    } catch { /* Theme still applies without storage. */ }
  });

  window.addEventListener('storage', event => {
    if (event.key === 'seihouse.home.theme') {
      setTheme(event.newValue);
      updateSansSpecimen();
      updateNotoSpecimen();
    }
  });

  // Brand logo resets to Fonts -> Normal
  byId('brand-home')?.addEventListener('click', event => {
    event.preventDefault();
    setFontSubtab('normal', { syncHash: false });
    setView('fonts', { scrollTop: true });
  });

  // Bottom Navigation Bar
  document.querySelectorAll('[data-slot="bottom-nav-tab"]').forEach(btn => {
    btn.addEventListener('click', () => {
      setView(btn.dataset.nav, { scrollTop: true });
    });
  });

  // Fonts sub-category tabs (Normal / Title / Special)
  document.querySelectorAll('[data-tablist="fonts"] [role="tab"]').forEach(tab => {
    tab.addEventListener('click', () => setFontSubtab(tab.dataset.subtab));
  });
  bindHorizontalKeys(
    document.querySelector('[data-tablist="fonts"]'),
    '[role="tab"]',
    tab => setFontSubtab(tab.dataset.subtab)
  );

  // Download font picker (Sans / Noto / Display)
  document.querySelectorAll('.font-pick-chip').forEach(chip => {
    chip.addEventListener('click', () => setDownloadFont(chip.dataset.dlFont));
  });
  bindHorizontalKeys(
    document.querySelector('.font-picker'),
    '[role="radio"]',
    chip => setDownloadFont(chip.dataset.dlFont)
  );

  // Download sub-category tabs (Current / Legacy)
  document.querySelectorAll('[data-tablist="download"] [role="tab"]').forEach(tab => {
    tab.addEventListener('click', () => setDownloadSubtab(tab.dataset.subtab));
  });
  bindHorizontalKeys(
    document.querySelector('[data-tablist="download"]'),
    '[role="tab"]',
    tab => setDownloadSubtab(tab.dataset.subtab)
  );

  // Quick jump buttons from Font cards -> Download Current for that font
  document.querySelectorAll('[data-jump-download]').forEach(btn => {
    btn.addEventListener('click', () => {
      setDownloadFont(btn.dataset.jumpDownload, { syncHash: false });
      setDownloadSubtab('current', { syncHash: false });
      setView('download', { scrollTop: true });
    });
  });

  // Sans controls
  ['sans-weight', 'sans-size', 'sans-compare'].forEach(id => {
    byId(id)?.addEventListener('input', updateSansSpecimen);
    byId(id)?.addEventListener('change', updateSansSpecimen);
  });

  byId('sans-italic')?.addEventListener('click', () => {
    sansItalic = !sansItalic;
    updateSansSpecimen();
  });

  byId('specimen')?.addEventListener('input', () => {
    fitTextarea(byId('specimen'), 352);
    const oldPreview = byId('sans-old-preview');
    if (oldPreview && !byId('sans-old-column').hidden) {
      oldPreview.textContent = byId('specimen').value;
    }
  });

  // Noto controls
  ['noto-weight', 'noto-size'].forEach(id => {
    byId(id)?.addEventListener('input', updateNotoSpecimen);
    byId(id)?.addEventListener('change', updateNotoSpecimen);
  });

  byId('noto-italic')?.addEventListener('click', () => {
    notoItalic = !notoItalic;
    updateNotoSpecimen();
  });

  byId('noto-specimen')?.addEventListener('input', () => fitTextarea(byId('noto-specimen'), 300));

  // Display controls
  document.querySelectorAll('.cut-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      activeCut = btn.dataset.cut;
      updateDisplaySpecimen();
    });
  });

  byId('display-size')?.addEventListener('input', updateDisplaySpecimen);
  byId('display-caps')?.addEventListener('click', () => {
    displayAllCaps = !displayAllCaps;
    updateDisplaySpecimen();
  });
  byId('display-specimen')?.addEventListener('input', () => fitTextarea(byId('display-specimen'), 384));

  // Special view: Living Title cut preview
  document.querySelectorAll('[data-living-cut]').forEach(btn => {
    btn.addEventListener('click', () => {
      const cut = displayCuts[btn.dataset.livingCut] || displayCuts.edge;
      const word = byId('living-preview-word');
      if (word) word.style.fontFamily = `"${cut.family}", sans-serif`;
      document.querySelectorAll('[data-living-cut]').forEach(b => {
        b.setAttribute('aria-pressed', String(b === btn));
      });
    });
  });

  // Special view: Elemental preset preview
  document.querySelectorAll('[data-element-preset]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.elementPreset;
      const preset = elementalPresets[key] || elementalPresets.lightning;
      const stage = byId('elemental-stage');
      const kicker = byId('elemental-kicker');
      const word = byId('elemental-preview-word');
      if (stage) stage.dataset.element = key;
      if (kicker) kicker.textContent = preset.kicker;
      if (word) word.textContent = preset.word;
      document.querySelectorAll('[data-element-preset]').forEach(b => {
        b.setAttribute('aria-pressed', String(b === btn));
      });
    });
  });

  window.addEventListener('hashchange', applyHashRoute);
  window.addEventListener('resize', fitVisibleTextareas);

  if (document.fonts?.ready) {
    document.fonts.ready.then(fitVisibleTextareas);
  }

  // Initial render
  applyHashRoute();
  updateSansSpecimen();
  updateNotoSpecimen();
  updateDisplaySpecimen();
})();
