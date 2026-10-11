// web_probe.mjs: the phone-profile measurements for game-prototype items 7 to 11, run in headless Chrome with touch events only.
//
//   node web_probe.mjs ROOT SPEC_JSON
//
// Hit points: the center and the middle of each edge, inset 4 px (a rounded or round button has no pixels at its corners).
// ROOT is the project directory (served statically; the page is /index.html). SPEC_JSON is {actions: {name: observable_attribute_value}, play: "#play"}.
// Prints one JSON object. The device profile is applied BEFORE navigation: applied after, a mobile page keeps a 980 px layout width.
// puppeteer-core is found through STUDIO_NODE_MODULES (a node_modules directory), and Chrome through STUDIO_CHROME or the puppeteer cache.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const [root, specPath] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const req = createRequire((process.env.STUDIO_NODE_MODULES || process.cwd() + '/node_modules') + '/x.js');
const puppeteer = req('puppeteer-core');

function chromePath() {
  if (process.env.STUDIO_CHROME) return process.env.STUDIO_CHROME;
  const base = path.join(process.env.HOME, '.cache/puppeteer/chrome-headless-shell');
  const v = fs.readdirSync(base)[0];
  return path.join(base, v, 'chrome-headless-shell-linux64/chrome-headless-shell');
}

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };
const server = http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, p);
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end('not found'); return; }
  r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(r);
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const url = `http://127.0.0.1:${server.address().port}/index.html`;

const UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36';
const PROFILES = [[390, 844], [844, 390], [1194, 834], [1280, 720]];
const KB = /\b(wasd|arrow keys?|right mouse|left mouse|mouse button|spacebar|space bar|press [a-z]\b|press (the )?(space|enter|shift|ctrl|esc)|scroll to zoom|click)\b/i;
const TOUCH = /\b(tap|taps|drag|swipe|pinch|hold|touch|joystick)\b/i;

const browser = await puppeteer.launch({ executablePath: chromePath(), args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const out = { url, profiles: {}, notes: [] };

async function open(w, h) {
  const page = await browser.newPage();
  await page.setUserAgent(UA);
  await page.setViewport({ width: w, height: h, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });   // before navigation
  await page.goto(url, { waitUntil: 'load', timeout: 20000 }).catch((e) => { out.notes.push('goto: ' + e.message); });
  await new Promise((r) => setTimeout(r, 400));
  return page;
}

// Finds the element for an action by data-control, then by accessible name (aria-label, or the text of a button / [role=button]).
const FIND = (name) => {
  const lc = name.toLowerCase();
  let el = document.querySelector(`[data-control="${name}"]`);
  if (!el) el = [...document.querySelectorAll('button,[role=button],a,[tabindex]')].find((e) => ((e.getAttribute('aria-label') || e.textContent || '').trim().toLowerCase() === lc));
  return el || null;
};

async function measureControls(page) {
  return page.evaluate((names, findSrc) => {
    const find = new Function('name', 'return (' + findSrc + ')(name)');
    return names.map((name) => {
      const el = find(name);
      if (!el) return { name, found: false };
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const shown = r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0';
      const vw = window.innerWidth, vh = window.innerHeight;
      const inside = r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh;
      const pts = [[0.5, 0.5, 0, 0], [0.5, 0, 0, 4], [0.5, 1, 0, -4], [0, 0.5, 4, 0], [1, 0.5, -4, 0]].map(([fx, fy, dx, dy]) => [r.left + fx * r.width + dx, r.top + fy * r.height + dy]);
      const covered = pts.filter(([x, y]) => { const hit = document.elementFromPoint(x, y); return !(hit && el.contains(hit)); }).length;
      return { name, found: true, shown, inside, w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, covered_points: shown ? covered : 5, rect: [r.left, r.top, r.right, r.bottom].map(Math.round) };
    });
  }, Object.keys(spec.actions), FIND.toString());
}

for (const [w, h] of PROFILES) {
  const page = await open(w, h);
  const key = `${w}x${h}`;
  out.profiles[key] = { coarse: await page.evaluate(() => matchMedia('(pointer: coarse)').matches), controls: await measureControls(page) };
  if (w === 390) {
    // item 7: tap each control with touch only; the observable is body[data-action-log]
    const taps = {};
    for (const [name, obs] of Object.entries(spec.actions)) {
      const c = out.profiles[key].controls.find((x) => x.name === name);
      if (!c || !c.found || !c.shown) { taps[name] = false; continue; }
      const [l, t, r, b] = c.rect;
      await page.touchscreen.tap((l + r) / 2, (t + b) / 2);
      await new Promise((ok) => setTimeout(ok, 150));
      taps[name] = await page.evaluate((o) => (document.body.dataset.actionLog || '').split(/\s+/).includes(o), obs);
    }
    out.taps = taps;
    // item 10: hints
    out.hints = await page.evaluate((kbSrc, touchSrc) => {
      const KB = new RegExp(kbSrc, 'i'), TOUCH = new RegExp(touchSrc, 'i');
      const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
      const text = (e) => (e ? ((e.getAttribute && e.getAttribute('aria-label')) || '') + ' ' + (e.innerText || '') : '');
      const bad = [];
      for (const e of document.body.querySelectorAll('*')) {
        if (!vis(e) && !(e.tagName === 'CANVAS')) continue;
        const own = text(e);
        if (e.children.length > 0 && e.tagName !== 'CANVAS' && ![...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
        if (!KB.test(own)) continue;
        const near = own + ' ' + text(e.previousElementSibling) + ' ' + text(e.nextElementSibling);
        if (!TOUCH.test(near)) bad.push(own.trim().slice(0, 80));
      }
      return bad;
    }, KB.source, TOUCH.source);
    // item 11: drag and pinch on the play surface
    const sel = spec.play || '#play';
    const box = await page.evaluate((s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }, sel);
    if (!box) out.page_stable = { error: 'no play surface ' + sel };
    else {
      const [l, t, bw, bh] = box;
      const cx = l + bw / 2, cy = t + bh / 2;
      const snap = () => page.evaluate(() => ({ x: scrollX, y: scrollY, s: visualViewport.scale, ox: visualViewport.offsetLeft, oy: visualViewport.offsetTop }));
      const before = await snap();
      const client = await page.createCDPSession();
      const ev = (type, pts) => client.send('Input.dispatchTouchEvent', { type, touchPoints: pts });
      await ev('touchStart', [{ x: cx, y: cy + 80 }]);
      for (let i = 1; i <= 8; i++) await ev('touchMove', [{ x: cx, y: cy + 80 - i * 20 }]);
      await ev('touchEnd', []);
      await new Promise((ok) => setTimeout(ok, 200));
      const afterDrag = await snap();
      await client.send('Input.synthesizePinchGesture', { x: cx, y: cy, scaleFactor: 2.0, relativeSpeed: 400, gestureSourceType: 'touch' }).catch((e) => out.notes.push('pinch: ' + e.message));
      await new Promise((ok) => setTimeout(ok, 300));
      const afterPinch = await snap();
      out.page_stable = { before, afterDrag, afterPinch };
    }
    out.viewport_meta = await page.evaluate(() => (document.querySelector('meta[name=viewport]') || {}).content || null);
  }
  if (w === 844) {
    // rotation without reload: swap the dimensions on the same page
    const page2 = await open(390, 844);
    const client = await page2.createCDPSession();
    await client.send('Emulation.setDeviceMetricsOverride', { width: 844, height: 390, deviceScaleFactor: 2, mobile: true });
    await new Promise((ok) => setTimeout(ok, 400));
    out.rotated = await measureControls(page2);
    await page2.close();
  }
  await page.close();
}
await browser.close();
server.close();
console.log(JSON.stringify(out));
