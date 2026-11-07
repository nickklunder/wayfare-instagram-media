// usage: node render.js stills 1,5,8  |  node render.js video
const puppeteer = require('/opt/npm-tools/node_modules/puppeteer');
const fs = require('fs'), path = require('path');
(async () => {
  const mode = process.argv[2] || 'stills';
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new',
    args: ['--no-sandbox', '--allow-file-access-from-files', '--disable-web-security'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920 });
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, process.env.PAGE||'template.html') + (process.env.TT?'?tiktok=1':process.env.REEL?'?reel=1':''));
  const dur = await page.evaluate(() => window.ready);
  console.log('duration', dur);
  const grab = async (t) => {
    const d = await page.evaluate(t => { window.draw(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, t);
    return Buffer.from(d.split(',')[1], 'base64');
  };
  if (mode === 'stills') {
    const SD=process.env.TT?'stills_tt':process.env.REEL?'stills_reel':'stills';fs.mkdirSync(SD, { recursive: true });
    for (const t of (process.argv[3] || '1').split(',').map(Number)) fs.writeFileSync(`${SD}/t${t}.jpg`, await grab(t));
  } else {
    const FD=process.env.TT?'frames_tt':process.env.REEL?'frames_reel':'frames';fs.mkdirSync(FD, { recursive: true });
    const n = Math.ceil(dur * 30);
    for (let i = 0; i < n; i++) { fs.writeFileSync(`${FD}/f${String(i).padStart(5, '0')}.jpg`, await grab(i / 30)); if (i % 100 == 0) console.log(i, '/', n); }
  }
  await browser.close();
})();
