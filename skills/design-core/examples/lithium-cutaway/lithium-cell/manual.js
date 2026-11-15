// Manual mode for the live page: the viewer drives the cell instead of the film. Entered on the first pill click,
// drag or scroll. Each pill (or key 1-5) opens or closes its part and leaves it there, so parts combine; the camera
// eases to that part's view and then belongs to the viewer: drag to orbit, scroll to zoom, double-click to reset.
// This runs on wall-clock time, so it is live-only: capture never enters it and films the pure script.
import {CAM, LABELS, readouts, STATUS} from './tour.js';

export const PARTS = ['cap', 'sleeve', 'roll', 'mandrel', 'exploded'];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

/** canvas: where orbit and zoom are read; current(): the film's state this frame, to take over from. */
export function makeManual(canvas, current) {
  const m = {on: false, open: {}, target: {}, cam: {...CAM.intro}, camTo: null, last: 'intro', spin: 0, prev: 0};
  for (const k of PARTS) m.open[k] = m.target[k] = 0;

  /** Take over from the film at its current state, so nothing jumps. */
  const enter = (s) => {
    if (m.on) return;
    m.on = true;
    for (const k of PARTS) {
      m.open[k] = k === 'exploded' ? s.explode : s[k];
      m.target[k] = m.open[k] > 0.5 ? 1 : 0;
    }
    m.cam = {...s.cam};
    m.camTo = null;
    m.spin = s.spin;
    m.last = PARTS.includes(s.act) ? s.act : 'intro';
    m.prev = performance.now() / 1000;
  };
  const leave = () => (m.on = false);
  const lastOpen = () => [...PARTS].reverse().find((k) => m.target[k] > 0.5) ?? 'intro';
  const toggle = (k) => {
    enter(current());
    m.target[k] = m.target[k] > 0.5 ? 0 : 1;
    // the roll and the pin can't come out under a closed cap: closing the cap closes them too
    if (k === 'cap' && !m.target.cap) m.target.roll = m.target.mandrel = 0;
    m.last = m.target[k] ? k : lastOpen();
    m.camTo = {...CAM[m.last]};
  };

  // the camera: orbit, zoom, reset. The page overlay lets pointer events through to the canvas.
  let drag = null;
  canvas.style.cursor = 'grab';
  canvas.addEventListener('pointerdown', (e) => {
    enter(current());
    drag = {x: e.clientX, y: e.clientY};
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = 'grabbing';
    m.camTo = null;
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    m.cam.az -= (e.clientX - drag.x) * 0.35;
    m.cam.el = clamp(m.cam.el + (e.clientY - drag.y) * 0.3, -8, 75);
    drag = {x: e.clientX, y: e.clientY};
  });
  const up = () => {
    drag = null;
    canvas.style.cursor = 'grab';
  };
  canvas.addEventListener('pointerup', up);
  canvas.addEventListener('pointercancel', up);
  canvas.addEventListener(
    'wheel',
    (e) => {
      enter(current());
      e.preventDefault();
      m.camTo = null;
      m.cam.d = clamp(m.cam.d * Math.exp(e.deltaY * 0.0012), 3.5, 22);
    },
    {passive: false},
  );
  canvas.addEventListener('dblclick', () => (m.camTo = {...CAM[m.last]}));

  /** The state for this frame, in the same shape as the film's stateAt(t). */
  const state = (t) => {
    const now = performance.now() / 1000;
    const dt = Math.min(0.1, now - m.prev);
    m.prev = now;
    const kOpen = 1 - Math.exp(-dt / 0.22);
    for (const k of PARTS) m.open[k] += (m.target[k] - m.open[k]) * kOpen;
    if (m.camTo) {
      const kCam = 1 - Math.exp(-dt / 0.3);
      let far = 0;
      for (const key of Object.keys(m.camTo)) {
        m.cam[key] += (m.camTo[key] - m.cam[key]) * kCam;
        far = Math.max(far, Math.abs(m.camTo[key] - m.cam[key]));
      }
      if (far < 0.01) m.camTo = null;
    }
    const o = m.open;
    const apart = Math.max(...PARTS.map((k) => o[k]));
    return {
      t,
      spin: m.spin,
      axial: 0,
      explode: o.exploded,
      cap: Math.max(o.cap, o.roll, o.mandrel),
      sleeve: o.sleeve,
      roll: o.roll,
      mandrel: o.mandrel,
      act: m.last,
      view: m.last === 'intro' ? 'overview' : m.last,
      apart,
      cam: m.cam,
      labels: {set: LABELS[m.last] ?? [], o: m.last === 'intro' ? 0 : o[m.last]},
      status: m.last === 'intro' ? 'Exploring' : STATUS[m.last],
      ...readouts(t, apart, o.roll, o.exploded),
    };
  };
  return {m, enter, leave, toggle, state, isOn: () => m.on, isOpen: (k) => m.target[k] > 0.5};
}
