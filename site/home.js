(() => {
  const families = {reader:'SEIReader',soft:'DisplaySoft',edge:'DisplayEdge',ink:'DisplayInk',wide:'DisplayWide'};
  const byId = id => document.getElementById(id);
  const theme = byId('theme');
  let italic = false;
  /** Fit the editable sample to its wrapped text, keeping very large samples scrollable. */
  function fitSample() {
    const sample = byId('specimen');
    sample.style.height = 'auto';
    sample.style.height = Math.min(sample.scrollHeight + 2, 500) + 'px';
  }
  /** Update the live specimen with actual font files and supported style controls. */
  function updateSpecimen() {
    const isReader = byId('family').value === 'reader';
    const sample = byId('specimen');
    sample.style.fontFamily = families[byId('family').value] + ', sans-serif';
    sample.style.fontSize = byId('size').value + 'px';
    sample.style.fontWeight = isReader ? byId('weight').value : '400';
    sample.style.fontStyle = isReader && italic ? 'italic' : 'normal';
    byId('weight').disabled = !isReader;
    byId('italic').disabled = !isReader;
    byId('italic').setAttribute('aria-pressed', String(isReader && italic));
    byId('size-value').textContent = byId('size').value + 'px';
    byId('tester-hint').textContent = isReader
      ? 'Type your own words. Open a Lab below to change the letter shapes and spacing.'
      : 'This is the supplied display cut. Open the Display Lab to explore weight, slant, and shape.';
    fitSample();
  }
  /** Apply Day or Night mode and reflect it in the toggle and browser chrome. */
  function setTheme(value) {
    const day = value === 'day';
    document.documentElement.dataset.theme = day ? 'day' : 'night';
    theme.textContent = day ? 'Night mode' : 'Day mode';
    theme.setAttribute('aria-pressed', String(day));
    document.querySelector('meta[name="theme-color"]').content = day ? '#f4f3e9' : '#151917';
  }
  try { setTheme(localStorage.getItem('seihouse.home.theme')); } catch { setTheme('night'); }
  theme.addEventListener('click', () => {
    const value = document.documentElement.dataset.theme === 'day' ? 'night' : 'day';
    setTheme(value);
    try { localStorage.setItem('seihouse.home.theme', value); } catch { /* Theme works without storage. */ }
  });
  ['family','weight','size'].forEach(id => byId(id).addEventListener('input', updateSpecimen));
  byId('italic').addEventListener('click', () => { italic = !italic; updateSpecimen(); });
  byId('specimen').addEventListener('input', fitSample);
  window.addEventListener('resize', fitSample);
  document.fonts.ready.then(fitSample);
  updateSpecimen();
})();
