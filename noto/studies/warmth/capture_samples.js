async (page) => {
  const context = await page.context().browser().newContext({viewport:{width:1440,height:1100},deviceScaleFactor:2});
  const proof = await context.newPage();
  await proof.goto('http://127.0.0.1:8767/');
  await proof.evaluate(()=>window.fontsReady);
  await proof.screenshot({path:'output/playwright/noto-warmth-desktop.png',fullPage:true,scale:'device'});
  await proof.getByRole('button',{name:'Letter details'}).click();
  await proof.screenshot({path:'output/playwright/noto-warmth-details.png',fullPage:true,scale:'device'});
  await proof.getByRole('button',{name:'Reading samples'}).click();
  await proof.getByRole('button',{name:'View on dark'}).click();
  // Wait for the short theme transition to finish before capturing colors.
  await proof.evaluate(()=>Promise.all(document.getAnimations().map(animation=>animation.finished)));
  await proof.screenshot({path:'output/playwright/noto-warmth-dark.png',fullPage:true,scale:'device'});
  await proof.setViewportSize({width:390,height:1000});
  await proof.locator('.card.b').screenshot({path:'output/playwright/noto-warmth-mobile-b.png',scale:'device'});
  await context.close();
  return 'Four samples captured at 2x pixel density.';
}
