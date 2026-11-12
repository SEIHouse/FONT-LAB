(() => {
  const byId = id => document.getElementById(id);

  const DEFAULT_SAMPLES = {
    sans: 'The mountain was still asleep when Mei opened the gate.\n“Lian,” Iñés said—1,234.56 · One more chapter?',
    display: 'Make Your Mark.\nThe Nine Heavens',
    noto: 'A familiar warmth. The morning light settled gently over the quiet library.',
  };

  const state = {
    manifest: null,
    track: 'sans',
    leftVersion: '',
    rightVersion: '',
    cut: 'edge',
    weight: 400,
    size: 24,
    italic: false,
    allCaps: false,
    customTextEdited: false,
  };

  const loadedFaces = new Map();
  let renderSeq = 0;

  /** Apply Day or Night mode and persist in localStorage when available. */
  function setTheme(mode) {
    const day = mode === 'day';
    document.documentElement.dataset.theme = day ? 'day' : 'night';
    const btn = byId('theme');
    btn.textContent = day ? 'Night mode' : 'Day mode';
    btn.setAttribute('aria-pressed', String(day));
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = day ? '#f4f3ea' : '#141917';
  }

  /** Read initial state overrides from URL query parameters. */
  function readUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const track = params.get('track');
    if (track && ['sans', 'display', 'noto'].includes(track)) {
      state.track = track;
    }
    const cut = params.get('cut');
    if (cut && ['soft', 'edge', 'ink', 'wide'].includes(cut)) {
      state.cut = cut;
    }
    const left = params.get('left');
    const right = params.get('right');
    if (left) state.leftVersion = left;
    if (right) state.rightVersion = right;
  }

  /** Sync current track, version pair, and cut back to the URL bar cleanly. */
  function syncUrlParams() {
    if (!window.history?.replaceState) return;
    const params = new URLSearchParams();
    params.set('track', state.track);
    if (state.leftVersion) params.set('left', state.leftVersion);
    if (state.rightVersion) params.set('right', state.rightVersion);
    if (state.track === 'display') params.set('cut', state.cut);
    window.history.replaceState(null, '', `${window.location.pathname}?${params.toString()}`);
  }

  /** Ensure left/right version IDs belong to the active track. */
  function normalizeTrackSelection(resetDefaults = false) {
    const trackData = state.manifest.tracks[state.track];
    const versions = trackData.versions;
    const hasLeft = !resetDefaults && versions.some(v => v.version === state.leftVersion);
    const hasRight = !resetDefaults && versions.some(v => v.version === state.rightVersion);

    if (!hasLeft) {
      state.leftVersion = trackData.currentVersion || versions[0]?.version || '';
    }
    if (!hasRight) {
      state.rightVersion = trackData.defaultCompareVersion
        || versions.find(v => v.version !== state.leftVersion)?.version
        || versions[0]?.version
        || '';
    }
  }

  /** Populate the inline version selectors inside the Current and Compare cards. */
  function populateVersionSelects() {
    const trackData = state.manifest.tracks[state.track];
    const selects = [byId('left-version'), byId('right-version')];

    selects.forEach((selectEl, idx) => {
      selectEl.innerHTML = '';
      for (const entry of trackData.versions) {
        const opt = document.createElement('option');
        opt.value = entry.version;
        opt.textContent = `${entry.version} — ${entry.shortTitle}`;
        selectEl.append(opt);
      }
      selectEl.value = idx === 0 ? state.leftVersion : state.rightVersion;
    });
  }

  /** Resolve the exact WOFF2 face object for a version given current UI controls. */
  function selectFaceForEntry(entry) {
    if (state.track === 'display') {
      const faceObj = entry.faces.find(f => f.cut === state.cut) || entry.faces[0];
      return { faceObj, resolvedWeight: 400, resolvedItalic: false, useNight: false, fallbackNote: '' };
    }

    const caps = entry.capabilities || { weights: [400], italic: false, nightWeights: [] };
    const isNight = document.documentElement.dataset.theme !== 'day';
    const resolvedWeight = caps.weights.includes(Number(state.weight)) ? Number(state.weight) : 400;
    const resolvedItalic = Boolean(state.italic && caps.italic);
    const useNight = Boolean(isNight && (caps.nightWeights || []).includes(resolvedWeight));
    const styleStr = resolvedItalic ? 'italic' : 'normal';

    const faceObj = entry.faces.find(
      f => f.weight === resolvedWeight && f.style === styleStr && Boolean(f.night) === useNight
    ) || entry.faces[0];

    let fallbackNote = '';
    if (resolvedWeight !== Number(state.weight) || resolvedItalic !== state.italic) {
      fallbackNote = 'Regular upright only in this version.';
    } else if (isNight && state.track === 'sans' && [300, 400, 500].includes(Number(state.weight)) && !useNight) {
      fallbackNote = 'Predates Night grade for this weight.';
    }

    return { faceObj, resolvedWeight, resolvedItalic, useNight, fallbackNote };
  }

  /** Lazy-load a single WOFF2 file via the CSS Font Loading API and cache it. */
  async function loadFontFace(trackId, versionId, selection) {
    const { faceObj, useNight } = selection;
    const safeVer = versionId.replace(/[^a-zA-Z0-9]/g, '_');
    const cutPart = faceObj.cut ? `_${faceObj.cut}` : '';
    const nightPart = useNight ? '_Night' : '';
    const familyName = `VF_${trackId}_${safeVer}${cutPart}${nightPart}`;
    const cacheKey = `${familyName}:${faceObj.weight || 400}:${faceObj.style || 'normal'}:${faceObj.path}`;

    if (!loadedFaces.has(cacheKey) && typeof FontFace === 'function') {
      const promise = (async () => {
        const ff = new FontFace(familyName, `url("../../${faceObj.path}") format("woff2")`, {
          weight: String(faceObj.weight || 400),
          style: faceObj.style || 'normal',
          display: 'swap',
        });
        const loaded = await ff.load();
        document.fonts.add(loaded);
        return familyName;
      })();
      loadedFaces.set(cacheKey, promise);
    }

    if (loadedFaces.has(cacheKey)) {
      await loadedFaces.get(cacheKey);
    }
    return familyName;
  }

  /** Update track tabs, toolbar visibility, and workspace link for the active track. */
  function updateTrackChrome() {
    document.documentElement.dataset.track = state.track;
    const trackData = state.manifest.tracks[state.track];

    document.querySelectorAll('[role="tab"]').forEach(tab => {
      const active = tab.dataset.track === state.track;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active) byId('arena').setAttribute('aria-labelledby', tab.id);
    });

    const wsLink = byId('active-workspace-link');
    wsLink.href = trackData.workspaceUrl;
    wsLink.textContent = `${trackData.workspaceLabel} ↗`;

    const isDisplay = state.track === 'display';
    const isNoto = state.track === 'noto';

    byId('cut-field').hidden = !isDisplay;
    byId('all-caps').hidden = !isDisplay;
    byId('weight-field').hidden = isDisplay;
    byId('italic').hidden = isDisplay;

    const weightSelect = byId('weight');
    Array.from(weightSelect.options).forEach(opt => {
      opt.disabled = isNoto && opt.value !== '400';
    });
    if (isNoto && state.weight !== 400) {
      state.weight = 400;
      weightSelect.value = '400';
    }
    byId('italic').disabled = isNoto;
    if (isNoto && state.italic) state.italic = false;

    byId('size-value').textContent = `${state.size}px`;
    byId('size').value = String(state.size);
    byId('italic').setAttribute('aria-pressed', String(state.italic));
    byId('all-caps').setAttribute('aria-pressed', String(state.allCaps));
    byId('display-cut').value = state.cut;
    byId('weight').value = String(state.weight);
  }

  /** Render one compact card ('left' or 'right') in the comparison view. */
  function renderCard(side, entry, selection, familyName) {
    if (side === 'left') {
      const badgeEl = byId('badge-left');
      badgeEl.textContent = entry.current ? 'Current' : 'Base';
      badgeEl.className = entry.current ? 'pill accent-pill' : 'pill';
    }
    byId(`date-${side}`).textContent = entry.date || '';

    const passageEl = byId(`passage-${side}`);
    passageEl.textContent = byId('sample-input').value;
    passageEl.style.fontFamily = familyName ? `"${familyName}", sans-serif` : 'sans-serif';
    passageEl.style.fontWeight = String(selection.resolvedWeight || 400);
    passageEl.style.fontStyle = selection.resolvedItalic ? 'italic' : 'normal';
    passageEl.style.fontSize = `${state.size}px`;
    passageEl.style.lineHeight = state.track === 'display' ? '1.16' : '1.5';
    passageEl.style.textTransform = (state.track === 'display' && state.allCaps) ? 'uppercase' : 'none';
    passageEl.style.fontFeatureSettings = (state.track === 'display' && state.allCaps) ? '"cpsp" 1' : 'normal';

    // Keep the alternate card note extra concise so the card stays compact.
    const baseNote = side === 'right' ? `${entry.shortTitle}. ${entry.summary}` : entry.summary;
    byId(`summary-${side}`).textContent = selection.fallbackNote
      ? `${entry.shortTitle} — ${selection.fallbackNote}`
      : (side === 'right' ? entry.summary : baseNote);
  }

  /** Render compact single-line release rows below the comparison cards. */
  function renderTimeline() {
    const trackData = state.manifest.tracks[state.track];
    byId('timeline-count').textContent = `(${trackData.versions.length})`;
    const listEl = byId('timeline-list');
    listEl.innerHTML = '';

    for (const entry of trackData.versions) {
      const isCompared = entry.version === state.rightVersion;
      const isLeft = entry.version === state.leftVersion;

      const li = document.createElement('li');
      li.className = 'timeline-row';
      li.dataset.active = String(isCompared || isLeft);

      const pill = document.createElement('span');
      pill.className = entry.current ? 'pill accent-pill' : 'pill';
      pill.textContent = entry.current ? `★ ${entry.version}` : entry.version;

      const info = document.createElement('div');
      info.className = 'tl-info';

      const shortEl = document.createElement('span');
      shortEl.className = 'tl-short';
      shortEl.textContent = entry.shortTitle;

      const briefEl = document.createElement('span');
      briefEl.className = 'tl-brief';
      briefEl.textContent = entry.summary;

      info.append(shortEl, briefEl);

      const dateSpan = document.createElement('span');
      dateSpan.className = 'card-date';
      dateSpan.textContent = entry.date || '';

      const actionBtn = document.createElement('button');
      actionBtn.type = 'button';
      actionBtn.className = 'tl-compare-btn';

      if (entry.current && state.leftVersion === entry.version) {
        actionBtn.textContent = 'Current';
        actionBtn.disabled = true;
      } else if (isCompared) {
        actionBtn.textContent = 'Comparing';
        actionBtn.dataset.selected = 'true';
      } else {
        actionBtn.textContent = 'Compare ↑';
        actionBtn.addEventListener('click', () => {
          state.rightVersion = entry.version;
          byId('right-version').value = state.rightVersion;
          refreshArena();
          const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
          byId('arena').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
        });
      }

      li.append(pill, info, dateSpan, actionBtn);
      listEl.append(li);
    }
  }

  /** Load selected fonts on demand and refresh cards + compact release list. */
  async function refreshArena() {
    if (!state.manifest) return;
    const seq = ++renderSeq;
    updateTrackChrome();
    syncUrlParams();

    const trackData = state.manifest.tracks[state.track];
    const leftEntry = trackData.versions.find(v => v.version === state.leftVersion) || trackData.versions[0];
    const rightEntry = trackData.versions.find(v => v.version === state.rightVersion) || trackData.versions[0];

    const leftSel = selectFaceForEntry(leftEntry);
    const rightSel = selectFaceForEntry(rightEntry);

    renderCard('left', leftEntry, leftSel, '');
    renderCard('right', rightEntry, rightSel, '');
    renderTimeline();

    try {
      const [leftFamily, rightFamily] = await Promise.all([
        loadFontFace(state.track, leftEntry.version, leftSel),
        loadFontFace(state.track, rightEntry.version, rightSel),
      ]);
      if (seq !== renderSeq) return;
      renderCard('left', leftEntry, leftSel, leftFamily);
      renderCard('right', rightEntry, rightSel, rightFamily);
      const statusEl = byId('load-status');
      statusEl.textContent = `Comparing ${leftEntry.label} and ${rightEntry.label}.`;
      statusEl.className = 'sr-only';
    } catch {
      if (seq !== renderSeq) return;
      const statusEl = byId('load-status');
      statusEl.textContent = 'Could not load one of the archived font files. Displaying fallback font.';
      statusEl.className = 'load-error-visible';
    }
  }

  /** Switch to a new track ('sans', 'display', or 'noto'). */
  function switchTrack(nextTrack, focusTab = false) {
    if (!state.manifest || !state.manifest.tracks[nextTrack]) return;
    state.track = nextTrack;
    normalizeTrackSelection(true);
    populateVersionSelects();

    if (!state.customTextEdited) {
      byId('sample-input').value = DEFAULT_SAMPLES[nextTrack] || DEFAULT_SAMPLES.sans;
    }
    state.size = nextTrack === 'display' ? 38 : 24;

    if (focusTab) byId(`tab-${nextTrack}`)?.focus();
    refreshArena();
  }

  /** Wire up controls and keyboard navigation. */
  function bindEvents() {
    byId('theme').addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'day' ? 'night' : 'day';
      setTheme(next);
      try {
        localStorage.setItem('seihouse.home.theme', next);
      } catch { /* Works without storage. */ }
      refreshArena();
    });

    const tabOrder = ['sans', 'display', 'noto'];
    document.querySelectorAll('[role="tab"]').forEach(tab => {
      tab.addEventListener('click', () => switchTrack(tab.dataset.track, false));
      tab.addEventListener('keydown', event => {
        const idx = tabOrder.indexOf(state.track);
        let nextIdx = -1;
        if (event.key === 'ArrowRight') nextIdx = (idx + 1) % tabOrder.length;
        else if (event.key === 'ArrowLeft') nextIdx = (idx - 1 + tabOrder.length) % tabOrder.length;
        else if (event.key === 'Home') nextIdx = 0;
        else if (event.key === 'End') nextIdx = tabOrder.length - 1;
        if (nextIdx >= 0) {
          event.preventDefault();
          switchTrack(tabOrder[nextIdx], true);
        }
      });
    });

    byId('left-version').addEventListener('change', e => {
      state.leftVersion = e.target.value;
      refreshArena();
    });

    byId('right-version').addEventListener('change', e => {
      state.rightVersion = e.target.value;
      refreshArena();
    });

    byId('display-cut').addEventListener('change', e => {
      state.cut = e.target.value;
      refreshArena();
    });

    byId('weight').addEventListener('change', e => {
      state.weight = Number(e.target.value);
      refreshArena();
    });

    byId('size').addEventListener('input', e => {
      state.size = Number(e.target.value);
      byId('size-value').textContent = `${state.size}px`;
      byId('passage-left').style.fontSize = `${state.size}px`;
      byId('passage-right').style.fontSize = `${state.size}px`;
    });

    byId('italic').addEventListener('click', () => {
      state.italic = !state.italic;
      refreshArena();
    });

    byId('all-caps').addEventListener('click', () => {
      state.allCaps = !state.allCaps;
      refreshArena();
    });

    byId('sample-input').addEventListener('input', e => {
      state.customTextEdited = true;
      const val = e.target.value;
      byId('passage-left').textContent = val;
      byId('passage-right').textContent = val;
    });
  }

  /** Boot the simplified Past Versions viewer. */
  async function init() {
    try {
      setTheme(localStorage.getItem('seihouse.home.theme'));
    } catch {
      setTheme('night');
    }

    readUrlParams();
    state.size = state.track === 'display' ? 38 : 24;
    byId('sample-input').value = DEFAULT_SAMPLES[state.track] || DEFAULT_SAMPLES.sans;

    bindEvents();

    const response = await fetch('../versions.json');
    if (!response.ok) return;
    state.manifest = await response.json();

    normalizeTrackSelection(false);
    populateVersionSelects();
    await refreshArena();
  }

  init();
})();
