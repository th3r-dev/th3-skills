// LITHE LC-21 on the green page: the cell from cell.js in the piranha's studio, the film from tour.js. Frame 0 and the
// exit hold the hero pose and camera the still was approved in (posed like refs/R01).
// Build: node "$SKILL_DIR/sims/build.mjs" <this folder>   (the kit and the shared stage resolve through cutaway-kit/)
import {runSim} from 'cutaway-kit/runtime.js';
import {createConsole} from 'cutaway-kit/../green/console.js';
import {makeCursor, makeLabels, ORANGE_TO, PAPER_GREEN, retint, SHIFT} from 'cutaway-kit/../green/look.js';
import {createStage, PAPER} from 'cutaway-kit/../piranha-shared/stage.js';
import {buildCell, FLOOR_Y, PAL} from './cell.js';
import TL from './timeline.json';
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
  const fit = () => (app.style.transform = `scale(${Math.min(innerWidth / 1600, innerHeight / 900)})`);
  const resize = () => {
    fit();
    st.resize(1600, 900, capture ? devicePixelRatio || 1 : Math.min(devicePixelRatio || 1, 2));
  };
  resize();
  window.CELL = {st, cell, T};
  return {
    resize,
    render(t) {
      const s = T.stateAt(t);
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
        cursor: cursorAt(t),
      });
      return {};
    },
  };
});
