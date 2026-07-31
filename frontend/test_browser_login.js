import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  
  await page.type('input[type="text"]', 'test_ui@example.com');
  await page.type('input[type="password"]', 'password');
  
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {})
  ]);

  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
})();
