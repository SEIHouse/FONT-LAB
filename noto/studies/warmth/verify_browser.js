async (page) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8767/');
  await page.evaluate(() => window.fontsReady);
  // CDP reports glyph usage only after the newly loaded font has been painted.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const fontStatus = await page.evaluate(() => [...document.fonts].map(face => ({family:face.family,status:face.status})));
  if (fontStatus.some(face => face.status !== 'loaded')) throw new Error('A specimen font did not load');
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const {root} = await cdp.send('DOM.getDocument');
  const actualFonts = {};
  for (const id of ['a','b','c']) {
    const {nodeId} = await cdp.send('DOM.querySelector',{nodeId:root.nodeId,selector:'.'+id+' .prose'});
    const {fonts} = await cdp.send('CSS.getPlatformFontsForNode',{nodeId});
    actualFonts[id] = fonts;
    if (!fonts.length || fonts.some(font => !font.isCustomFont || !font.familyName.includes('Study '+id.toUpperCase()))) {
      throw new Error('Unexpected fallback in study '+id+': '+JSON.stringify(fonts));
    }
  }
  const viewports = [];
  for (const width of [360,390,768,1024,1440]) {
    await page.setViewportSize({width,height:1100});
    for (const zoom of [false,true]) {
      if ((await page.locator('#zoom').getAttribute('aria-pressed')) !== String(zoom)) await page.locator('#zoom').click();
      const overflow = await page.evaluate(() => ({document:document.documentElement.scrollWidth > innerWidth, cards:[...document.querySelectorAll('.card')].filter(el=>el.scrollWidth>el.clientWidth+1).length}));
      if (overflow.document || overflow.cards) throw new Error('Overflow '+width+' zoom='+zoom+' '+JSON.stringify(overflow));
      viewports.push({width,view:zoom?'details':'reading',overflow:false});
    }
  }
  await page.locator('#zoom').click();
  await page.locator('#size').focus();
  await page.keyboard.press('End');
  if (await page.locator('#sizeValue').textContent() !== '28 px') throw new Error('Size control failed');
  if (await page.locator('.a .prose').evaluate(el=>getComputedStyle(el).fontSize) !== '28px') throw new Error('Size was not applied');
  await page.locator('#passage').fill('Warmth, light, and a quiet library.');
  if ((await page.locator('.prose').allTextContents()).some(text=>text!=='Warmth, light, and a quiet library.')) throw new Error('Passage sync failed');
  await page.locator('#passage').fill('Hello 漢');
  if (!(await page.locator('#status').textContent()).includes('Outside this study')) throw new Error('Missing-glyph disclosure failed');
  await page.getByRole('button',{name:'Reset passage'}).click();
  await page.locator('#size').focus();
  await page.keyboard.press('Home');
  for (let i=0;i<5;i++) await page.keyboard.press('ArrowRight');
  await page.locator('h1').click();
  await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:'output/playwright/noto-warmth-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Letter details'}).click();
  await page.screenshot({path:'output/playwright/noto-warmth-details.png',fullPage:true});
  await page.getByRole('button',{name:'Reading samples'}).click();
  await page.getByRole('button',{name:'View on dark'}).click();
  await page.screenshot({path:'output/playwright/noto-warmth-dark.png',fullPage:true});
  await page.setViewportSize({width:390,height:1000});
  await page.locator('.card.b').screenshot({path:'output/playwright/noto-warmth-mobile-b.png'});
  await page.getByRole('button',{name:'View on light'}).click();
  // Verify that the shareable file contains its fonts and works without font requests.
  const requests = [];
  const collect = request => requests.push(request.url());
  page.on('request',collect);
  await page.goto('http://127.0.0.1:8767/SEIHouse-Noto-Warmth-Studies.html');
  await page.evaluate(()=>window.fontsReady);
  const portable = await page.evaluate(()=>[...document.fonts].every(face=>face.status==='loaded'));
  page.off('request',collect);
  if (!portable || requests.some(url=>/\.(woff2|ttf)(\?|$)/.test(url))) throw new Error('Portable comparison depended on external fonts');
  if (errors.length) throw new Error(errors.join('\n'));
  await page.setViewportSize({width:1440,height:1100});
  return {fontStatus,actualFonts,viewports,controls:'passed',portable:'passed',pageErrors:errors};
}
