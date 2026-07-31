import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  
  // Click Register tab
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const registerBtn = buttons.find(b => b.textContent.includes('Register') && !b.textContent.includes('Sign in'));
    if (registerBtn) registerBtn.click();
  });
  
  await new Promise(r => setTimeout(r, 500));
  
  // Fill register form
  const email = `test_${Date.now()}@example.com`;
  await page.type('input[placeholder="Email"]', email);
  await page.type('input[placeholder="Username"]', 'testuser');
  await page.type('input[placeholder="Password"]', 'password');
  
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(e => console.log("Nav timeout"))
  ]);

  await new Promise(r => setTimeout(r, 2000));
  
  const html = await page.content();
  console.log('HTML CONTENT AFTER LOGIN:', html.substring(0, 500));
  
  await browser.close();
})();
