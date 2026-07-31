import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  const html = await page.content();
  console.log('HTML CONTENT:', html);
  
  await browser.close();
})();
