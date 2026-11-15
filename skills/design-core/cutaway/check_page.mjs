#!/usr/bin/env node
// design-core cutaway: the gate before a page is handed over. Drives a built cutaway page in headless Chromium the
// way a viewer would and fails (exit 1) unless the page is interactive by hand:
//
//   1. it loads with no page errors and the film plays (the scripted cursor is shown);
//   2. every part's pill is a button: a click enters manual mode, lights that pill and opens the part;
//   3. two parts stay open together (parts combine);
//   4. a drag orbits (azimuth changes), a scroll zooms (distance changes);
//   5. a number key toggles its part; clicking an open pill closes it;
//   6. while driving, the scripted cursor is hidden and the clock reads "Manual";
//   7. "Play film" hands back: manual off, cursor back, no page errors throughout.
//
//   node check_page.mjs <page.html> [--shots DIR]      (--shots: a screenshot per step, to read)
//   node check_page.mjs --help
//
// Playwright is resolved from the cutaway skill's node_modules: set CUTAWAY_DIR to the installed cutaway folder.
// macOS needs --use-angle=metal for WebGL in the headless shell; it is added here. Run it outside a sandboxed shell
// (the sandbox blocks the GPU).
import {createRequire} from 'node:module';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help')) {
  console.log('usage: CUTAWAY_DIR=<installed cutaway> node check_page.mjs <page.html> [--shots DIR]');
  process.exit(argv.includes('--help') ? 0 : 2);
}
const html = path.resolve(argv[0]);
const shots = argv.includes('--shots') ? path.resolve(argv[argv.indexOf('--shots') + 1]) : null;
const dir = process.env.CUTAWAY_DIR;
if (!dir) {
  console.error('set CUTAWAY_DIR to the installed cutaway skill folder (it has node_modules/playwright)');
  process.exit(2);
}
const {chromium} = createRequire(path.join(dir, 'node_modules', 'x.js'))('playwright');

const args = ['--ignore-gpu-blocklist', '--enable-webgl', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : process.platform === 'win32' ? ['--use-angle=d3d11'] : [])];
const browser = await chromium.launch({args});
const page = await browser.newPage({viewport: {width: 1600, height: 900}});
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
let failed = 0;
let step = 0;
const check = async (name, ok, detail = '') => {
  step++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${step}. ${name}${detail ? `  (${detail})` : ''}`);
  if (!ok) failed++;
  if (shots) await page.screenshot({path: path.join(shots, `check-${String(step).padStart(2, '0')}.png`)});
};
const read = () =>
  page.evaluate(() => {
    const m = window.CUTAWAY?.manual;
    const cur = document.querySelector('.vp svg.cur');
    return {
      wired: !!m,
      on: !!m?.isOn(),
      cam: m ? {az: m.m.cam.az, el: m.m.cam.el, d: m.m.cam.d} : null,
      parts: m?.parts ?? [],
      open: m ? Object.fromEntries(m.parts.map((k) => [k, m.isOpen(k)])) : {},
      lit: [...document.querySelectorAll('.vp .pill.on')].map((e) => e.dataset.p),
      cursor: !!cur && cur.style.display !== 'none',
      clock: document.querySelector('.vp [data-v="time"]')?.textContent ?? '',
    };
  });
const pill = (k) => page.locator(`.vp .pill[data-p="${k}"]`);
const wait = (ms) => page.waitForTimeout(ms);

try {
  await page.goto(pathToFileURL(html).href);
  await page.waitForFunction(() => window.SIM?.ready, null, {timeout: 60000});
  await wait(700);
  let s = await read();
  await check('page loads, film plays, manual mode is wired', s.wired && !s.on && s.cursor && s.parts.length > 0 && !errors.length, `${s.parts.length} parts`);
  if (!s.wired) throw new Error('window.CUTAWAY.manual missing: the page was not built with interactive.js');
  const parts = s.parts;

  let allOk = true;
  for (const k of parts) {
    if (!(await pill(k).count())) {
      allOk = false;
      console.log(`     no pill for part "${k}"`);
      continue;
    }
    await pill(k).click();
    await wait(900);
    s = await read();
    const ok = s.on && s.open[k] && s.lit.includes(k);
    if (!ok) allOk = false;
    if (shots) await page.screenshot({path: path.join(shots, `part-${k}.png`)});
    await pill(k).click(); // close it again
    await wait(700);
  }
  await check('every pill opens its part in manual mode', allOk);

  const [a, b] = parts;
  await pill(a).click();
  await wait(500);
  if (b) await pill(b).click();
  await wait(900);
  s = await read();
  await check('two parts stay open together', s.open[a] && (!b || s.open[b]) && s.lit.includes(a), `${a}${b ? ' + ' + b : ''}`);
  await check('scripted cursor hidden, clock reads Manual', !s.cursor && s.clock === 'Manual', s.clock);

  const before = s.cam;
  await page.mouse.move(800, 560);
  await page.mouse.down();
  await page.mouse.move(640, 520, {steps: 8});
  await page.mouse.up();
  await wait(200);
  s = await read();
  await check('drag orbits the camera', Math.abs(s.cam.az - before.az) > 10, `az ${before.az.toFixed(1)} -> ${s.cam.az.toFixed(1)}`);
  const d0 = s.cam.d;
  await page.mouse.wheel(0, 400);
  await wait(200);
  s = await read();
  await check('scroll zooms the camera', Math.abs(s.cam.d - d0) > 0.3, `d ${d0.toFixed(2)} -> ${s.cam.d.toFixed(2)}`);

  const last = parts.length;
  const lastK = parts[last - 1];
  const was = s.open[lastK];
  await page.keyboard.press(String(last));
  await wait(900);
  s = await read();
  await check(`key ${last} toggles "${lastK}"`, s.open[lastK] !== was);

  await page.getByRole('button', {name: 'Play film'}).click();
  await wait(800);
  s = await read();
  await check('"Play film" hands back to the film', !s.on && s.cursor && s.clock !== 'Manual');
  await check('no page errors', !errors.length, errors.join(' | '));
} catch (e) {
  failed++;
  console.log(`FAIL ${e.message}`);
}
await browser.close();
console.log(failed ? `\n${failed} check(s) failed: the page is not ready to hand over.` : '\nall checks passed: hand the page over, open.');
process.exit(failed ? 1 : 0);
