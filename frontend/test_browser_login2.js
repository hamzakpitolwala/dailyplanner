import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  
  // Wait for input to be available
  await page.waitForSelector('input[placeholder="Email"]');
  await page.type('input[placeholder="Email"]', 'test_ui@example.com');
  await page.type('input[placeholder="Password"]', 'password');
  
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(e => console.log("Navigation timeout or error"))
  ]);

  await new Promise(r => setTimeout(r, 2000));
  
  const html = await page.content();
  console.log('HTML CONTENT AFTER LOGIN:', html.substring(0, 500));
  
  await browser.close();
})();
