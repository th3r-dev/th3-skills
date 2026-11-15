// LITHE LC-21 on the green page: the cell from cell.js in the piranha's studio, the film from tour.js. Frame 0 and the
// exit hold the hero pose and camera the still was approved in (posed like refs/R01).
// Build: node "$SKILL_DIR/sims/build.mjs" <this folder>   (the kit and the shared stage resolve through cutaway-kit/)
import {runSim} from 'cutaway-kit/runtime.js';
import {createConsole} from 'cutaway-kit/../green/console.js';
import {makeCursor, makeLabels, ORANGE_TO, PAPER_GREEN, retint, SHIFT} from 'cutaway-kit/../green/look.js';
import {createStage, PAPER} from 'cutaway-kit/../piranha-shared/stage.js';
import {buildCell, FLOOR_Y, PAL} from './cell.js';
import TL from './timeline.json';
import {makeManual, PARTS} from './manual.js';
import {makeTour} from './tour.js';

// the shell a cool white like R01's; retint() on the lights only: R01 keeps its copper foil, and every accent is
// built green already
Object.assign(PAL, {orange: ORANGE_TO, white: '#f3f6f4'});
Object.assign(PAPER, PAPER_GREEN);
const D2R = Math.PI / 180;

const ACTS = [['cap', 'Cap stack'], ['sleeve', 'Wrap'], ['roll', 'Jelly roll'], ['mandrel', 'Mandrel'], ['exploded', 'Teardown']];
const PAGE = {
  name: 'Lithe',
  code: 'LC-21',
  title: 'Lithium-ion Cell, Taken Apart',
  date: '2026-11-15',
  sub: {
    overview: ['Cylindrical cell, 21 x 70', 'A quarter cut away'],
    cap: ['Button, PTC, vent disc', 'Green gasket seals it'],
    sleeve: ['Printed wrap over steel', 'The can is the negative'],
    roll: ['Anode, separator, cathode', 'Wound round a pin'],
    mandrel: ['Steel pin on the axis', 'Holds the roll round'],
    exploded: ['Every part apart', 'One turn on its axis'],
  },
  cards: [{k: 'Voltage', kind: 'wave', unit: 'V'}, {k: 'Charge', kind: 'bar', unit: '%'}, {k: 'Layer load', kind: 'bars', n: 6}, {k: 'Temperature', kind: 'bar', unit: '°C'}],
};
runSim({duration: TL.duration, fps: 60, theme: 'light', hud: {enabled: false, title: 'lithium-cutaway', subtitle: ''}, director: {enabled: false}, watermark: ''}, async ({canvas, capture}) => {
  const app = document.getElementById('app');
  const st = createStage({canvas, floorY: FLOOR_Y, span: 2.6});
  const cell = buildCell();
  cell.pose();
  st.addBody(cell);
  st.scene.traverse((o) => o.isLight && retint(o));
  const T = makeTour(TL);
  const ui = createConsole(app, {...PAGE, nav: [['overview', 'Overview'], ...ACTS], pills: ACTS});
  const cursorAt = makeCursor(ui, T.SCRIPT);
  const labels = makeLabels(st, cell.anchors);
  // live page: the film plays until the viewer takes over (a pill, keys 1-5, a drag or a scroll on the cell); from
  // then on manual.js drives it until "Play film". Capture never takes this path and films the pure script.
  let film = null;
  const manual = makeManual(canvas, () => film ?? T.stateAt(0));
  if (!capture) {
    const bar = document.createElement('div');
    bar.className = 'manual-bar';
    bar.innerHTML = `<span data-hint>Click a part to open it · drag to orbit · scroll to zoom</span><button type="button" data-play hidden>Play film</button>`;
    const css = document.createElement('style');
    css.textContent = `.vp .manual-bar{position:absolute;left:50%;transform:translateX(-50%);top:802px;display:flex;align-items:center;gap:12px;padding:4px 4px 4px 14px;border:1px solid #e8edf3;border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 4px 14px rgba(15,23,42,.06);font:500 12.5px/1 'Inter',sans-serif;color:#475569;white-space:nowrap}
.vp .manual-bar button[hidden]{display:none}
.vp .manual-bar button{pointer-events:auto;cursor:pointer;height:28px;padding:0 14px;border:1px solid #16b364;border-radius:14px;background:#effbf4;color:#0b7a43;font:600 12.5px/1 'Inter',sans-serif}
.vp .manual-bar button:focus-visible,.vp .pill:focus-visible{outline:2px solid #16b364;outline-offset:2px}`;
    document.head.appendChild(css);
    ui.root.appendChild(bar);
    const play = bar.querySelector('[data-play]');
    const hint = bar.querySelector('[data-hint]');
    const sync = () => {
      play.hidden = !manual.isOn();
      hint.textContent = manual.isOn() ? 'Drag to orbit · scroll to zoom · double-click to reset the view' : 'Click a part to open it · drag to orbit · scroll to zoom';
    };
    const toggle = (k) => {
      manual.toggle(k);
      sync();
    };
    ACTS.forEach(([k]) => {
      const el = ui.pills[k];
      Object.assign(el.style, {pointerEvents: 'auto', cursor: 'pointer'});
      el.setAttribute('role', 'button');
      el.tabIndex = 0;
      el.addEventListener('click', () => toggle(k));
      el.addEventListener('keydown', (e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), e.stopPropagation(), toggle(k)));
    });
    addEventListener('keydown', (e) => /^[1-5]$/.test(e.key) && toggle(PARTS[+e.key - 1]));
    canvas.addEventListener('pointerdown', sync);
    canvas.addEventListener('wheel', sync);
    play.addEventListener('click', () => {
      manual.leave();
      dispatchEvent(new KeyboardEvent('keydown', {key: 'r'})); // the runtime restarts the film from 0
      sync();
    });
  }
  const fit = () => (app.style.transform = `scale(${Math.min(innerWidth / 1600, innerHeight / 900)})`);
  const resize = () => {
    fit();
    st.resize(1600, 900, capture ? devicePixelRatio || 1 : Math.min(devicePixelRatio || 1, 2));
  };
  resize();
  const timeEl = ui.root.querySelector('[data-v="time"]');
  const progEl = ui.root.querySelector('[data-v="prog"]');
  window.CELL = {st, cell, T, manual};
  return {
    resize,
    render(t) {
      // live manual mode reads wall-clock time in manual.state; the film (and every capture) stays a pure function of t
      const s = manual.isOn() ? manual.state(t) : (film = T.stateAt(t));
      cell.pose(s);
      const c = s.cam;
      st.frame({...c, az: c.az * D2R, el: c.el * D2R, sx: SHIFT[0], sy: SHIFT[1]}, {guides: 0});
      ui.update({
        time: t,
        dur: TL.duration,
        status: s.status,
        cards: [
          {v: s.volts.toFixed(2), wave: Array.from({length: 24}, (_, i) => Math.sin(i / 3 + t * 3) * (0.25 + 0.5 * s.apart))},
          {v: Math.round(s.charge * 100), bar: s.charge},
          {bars: s.bars},
          {v: Math.round(s.temp), bar: (s.temp - 15) / 30},
        ],
        apart: Math.round(s.apart * 100),
        view: s.view,
        callouts: labels(s.labels),
        cursor: manual.isOn() ? null : cursorAt(t),
      });
      // in manual mode several parts can be open at once: light every open part's pill
      if (manual.isOn()) {
        for (const [k, el] of Object.entries(ui.pills)) el.classList.toggle('on', manual.isOpen(k));
        // the film's clock means nothing while the viewer drives: the time reads Manual, the track sits empty
        timeEl.textContent = 'Manual';
        progEl.style.width = '0%';
      }
      return {};
    },
  };
});
