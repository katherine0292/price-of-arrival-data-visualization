// Deterministic frame-by-frame capture of the story HTML into H.264 chunks.
// usage: node render.js page.html outdir fps workers [stillTimes...]
//   with stillTimes given, writes PNG stills instead of video (for checking frames).
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const [html, outdir, fpsArg, workersArg, ...stills] = process.argv.slice(2);
const fps = +fpsArg || 30, workers = +workersArg || 4;
fs.mkdirSync(outdir, { recursive: true });
const url = 'file://' + path.resolve(html) + '?render=1';

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto(url, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => window.__READY === true, null, { timeout: 120000 });
  return page;
}

async function renderChunk(browser, idx, f0, f1) {
  const page = await openPage(browser);
  const out = path.join(outdir, `part_${String(idx).padStart(2, '0')}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-g', String(fps * 2), '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.render(t), f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93, caret: 'hide' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`[w${idx}] frame ${f - f0}/${f1 - f0}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await page.close();
  return out;
}

(async () => {
  const browser = await chromium.launch({ args: ['--disable-gpu', '--font-render-hinting=none'] });
  if (stills.length) {
    const page = await openPage(browser);
    for (const s of stills) {
      await page.evaluate(t => window.render(t), +s);
      await page.screenshot({ path: path.join(outdir, `still_${(+s).toFixed(2).padStart(7, '0')}.png`) });
    }
    await browser.close();
    return;
  }
  const total = await (await openPage(browser)).evaluate(() => window.TOTAL);
  const frames = Math.ceil(total * fps);
  const per = Math.ceil(frames / workers);
  console.log(`total ${total}s -> ${frames} frames, ${workers} workers`);
  const jobs = [];
  for (let i = 0; i < workers; i++) {
    const a = i * per, b = Math.min(frames, (i + 1) * per);
    if (a < b) jobs.push(renderChunk(browser, i, a, b));
  }
  const parts = await Promise.all(jobs);
  fs.writeFileSync(path.join(outdir, 'parts.txt'), parts.map(p => `file '${path.resolve(p)}'`).join('\n'));
  await browser.close();
  console.log('done');
})().catch(e => { console.error(e); process.exit(1); });
