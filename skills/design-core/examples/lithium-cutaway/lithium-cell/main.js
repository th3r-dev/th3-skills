// LITHE LC-21 on the green page: the cell from cell.js in the piranha's studio. This round is the still gate only:
// the hero pose and camera, posed like refs/R01. The film's tour is added after the still is approved.
// Build: node "$SKILL_DIR/sims/build.mjs" <this folder>   (the kit and the shared stage resolve through cutaway-kit/)
import {runSim} from 'cutaway-kit/runtime.js';
import {createConsole} from 'cutaway-kit/../green/console.js';
import {ORANGE_TO, PAPER_GREEN, SHIFT} from 'cutaway-kit/../green/look.js';
import {createStage, PAPER} from 'cutaway-kit/../piranha-shared/stage.js';
import {buildCell, FLOOR_Y, PAL} from './cell.js';
import TL from './timeline.json';

// the shell a cool white like R01's; no retint(): R01 keeps its copper foil, and every accent is built green already
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
    exploded: ['Every part apart', 'Turntable 300°'],
  },
  cards: [{k: 'Voltage', kind: 'wave', unit: 'V'}, {k: 'Charge', kind: 'bar', unit: '%'}, {k: 'Layer load', kind: 'bars', n: 6}, {k: 'Temperature', kind: 'bar', unit: '°C'}],
};
// the hero camera: front 3/4, about 12° above, as R01 is drawn
export const HERO = {tx: 0, ty: -0.22, tz: 0, az: 6, el: 16, d: 9.2};

runSim({duration: TL.duration, fps: 60, theme: 'light', hud: {enabled: false, title: 'lithium-cutaway', subtitle: ''}, director: {enabled: false}, watermark: ''}, async ({canvas, capture}) => {
  const app = document.getElementById('app');
  const st = createStage({canvas, floorY: FLOOR_Y, span: 2.6});
  const cell = buildCell();
  cell.pose();
  st.addBody(cell);
  const ui = createConsole(app, {...PAGE, nav: [['overview', 'Overview'], ...ACTS], pills: ACTS});
  const fit = () => (app.style.transform = `scale(${Math.min(innerWidth / 1600, innerHeight / 900)})`);
  const resize = () => {
    fit();
    st.resize(1600, 900, capture ? devicePixelRatio || 1 : Math.min(devicePixelRatio || 1, 2));
  };
  resize();
  window.CELL = {st, cell};
  return {
    resize,
    render(t) {
      cell.pose({spin: 0});
      const c = HERO;
      st.frame({...c, az: c.az * D2R, el: c.el * D2R, sx: SHIFT[0], sy: SHIFT[1]}, {guides: 0});
      const v = 3.62 + 0.04 * Math.sin(t * 2);
      ui.update({
        time: t,
        dur: TL.duration,
        status: 'Idle',
        cards: [{v: v.toFixed(2), wave: Array.from({length: 24}, (_, i) => Math.sin(i / 3 + t * 3) * 0.4)}, {v: 82, bar: 0.82}, {bars: [0.4, 0.5, 0.45, 0.55, 0.5, 0.42]}, {v: 24, bar: 0.24}],
        apart: 0,
        view: 'overview',
        callouts: [],
        cursor: null,
      });
      return {};
    },
  };
});
