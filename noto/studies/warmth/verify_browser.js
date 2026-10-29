async (page) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8768/noto/studies/warmth/');
  await page.evaluate(() => window.fontsReady);
  // CDP reports glyph usage only after the newly loaded font has been painted.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const fontStatus = await page.evaluate(() => [...document.fonts].map(face => ({family:face.family,status:face.status})));
  if (fontStatus.some(face => face.status !== 'loaded')) throw new Error('A specimen font did not load');
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  async function renderedFonts() {
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const {root} = await cdp.send('DOM.getDocument');
    const actualFonts = {};
    for (const [id, family] of [['refined','SEIHouse Noto Balanced'], ['baseline','SEIHouse Noto Study B']]) {
      const {nodeId} = await cdp.send('DOM.querySelector',{nodeId:root.nodeId,selector:'.'+id+' .prose'});
      const {fonts} = await cdp.send('CSS.getPlatformFontsForNode',{nodeId});
      actualFonts[id] = fonts;
      if (!fonts.length || fonts.some(font => !font.isCustomFont || font.familyName !== family)) {
        throw new Error('Unexpected fallback in study '+id+': '+JSON.stringify(fonts));
      }
    }
    return actualFonts;
  }
  const actualFonts = await renderedFonts();
  const viewports = [];
  for (const width of [360,390,768,1024,1440]) {
    await page.setViewportSize({width,height:1100});
    for (const zoom of [false,true]) {
      if ((await page.locator('#zoom').getAttribute('aria-pressed')) !== String(zoom)) await page.locator('#zoom').click();
      for (const view of ['refined','original','compare']) {
        await page.locator('#view').selectOption(view);
        const expectedCards = view === 'compare' ? 2 : 1;
        if (await page.locator('.card:visible').count() !== expectedCards) throw new Error('View selector failed: '+view);
        const overflow = await page.evaluate(() => ({document:document.documentElement.scrollWidth > innerWidth, cards:[...document.querySelectorAll('.card')].filter(el=>el.clientWidth && el.scrollWidth>el.clientWidth+1).length}));
        if (overflow.document || overflow.cards) throw new Error('Overflow '+width+' zoom='+zoom+' '+JSON.stringify(overflow));
        viewports.push({width,view,detail:zoom,overflow:false});
      }
    }
  }
  await page.locator('#zoom').click();
  await page.locator('#size').focus();
  await page.keyboard.press('End');
  if (await page.locator('#sizeValue').textContent() !== '28 px') throw new Error('Size control failed');
  if (await page.locator('.refined .prose').evaluate(el=>getComputedStyle(el).fontSize) !== '28px') throw new Error('Size was not applied');
  await page.locator('#passage').fill('Warmth, light, and a quiet library.');
  if ((await page.locator('.prose').allTextContents()).some(text=>text!=='Warmth, light, and a quiet library.')) throw new Error('Passage sync failed');
  await page.locator('#passage').fill('');
  if ((await page.locator('.prose').allTextContents()).some(text=>text!=='')) throw new Error('Empty passage was not preserved');
  await page.locator('#passage').fill('Hello 漢');
  if (!(await page.locator('#status').textContent()).includes('Outside this study')) throw new Error('Missing-glyph disclosure failed');
  await page.getByRole('button',{name:'Reset passage'}).click();
  await page.locator('#size').focus();
  await page.keyboard.press('Home');
  for (let i=0;i<5;i++) await page.keyboard.press('ArrowRight');
  await page.locator('h1').click();
  await page.evaluate(()=>scrollTo(0,0));
  await page.getByRole('button',{name:'View on dark'}).click();
  if (!await page.locator('body').evaluate(el=>el.classList.contains('dark'))) throw new Error('Theme toggle failed');
  await page.getByRole('button',{name:'View on light'}).click();
  // Verify that the shareable file contains its fonts and works without font requests.
  const requests = [];
  const collect = request => requests.push(request.url());
  page.on('request',collect);
  await page.goto('http://127.0.0.1:8768/noto/studies/warmth/SEIHouse-Noto-Warmth-Studies.html');
  await page.evaluate(()=>window.fontsReady);
  const portableFonts = await renderedFonts();
  const portable = await page.evaluate(()=>[...document.fonts].every(face=>face.status==='loaded'));
  page.off('request',collect);
  if (!portable || requests.some(url=>/\.(woff2|ttf)(\?|$)/.test(url))) throw new Error('Portable comparison depended on external fonts');
  if (await page.getByRole('link',{name:'Back to Font Lab'}).getAttribute('href') !== 'https://fontlab.seihouse.world/') throw new Error('Portable home link depends on local files');
  const localLinks = await page.locator('a').evaluateAll(links=>links.map(link=>link.getAttribute('href')).filter(href=>!href.startsWith('#') && !href.startsWith('https://')));
  if (localLinks.length) throw new Error('Portable navigation depends on local files: '+localLinks);
  await page.goto('http://127.0.0.1:8768/');
  await page.getByRole('link',{name:'Noto test',exact:true}).click();
  await page.getByRole('link',{name:'First three studies'}).click();
  await page.evaluate(()=>window.fontsReady);
  if (await page.getByRole('heading',{name:'Balanced',exact:true}).count() !== 1) throw new Error('Original study archive failed');
  await page.getByRole('link',{name:'Back to Font Lab'}).click();
  await page.getByRole('link',{name:'Open Noto test page'}).click();
  if (errors.length) throw new Error(errors.join('\n'));
  await page.setViewportSize({width:1440,height:1100});
  return {fontStatus,actualFonts,portableFonts,viewports,controls:'passed',portable:'passed',pageErrors:errors};
}
