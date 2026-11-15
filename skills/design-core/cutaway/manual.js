// design-core cutaway: manual mode for any cutaway page. The live page plays its film until the viewer takes over
// (a part's pill, its number key, a drag or a scroll on the object); from then on the viewer drives it. Each part
// opens or closes and stays so, parts combine, the camera eases to the part's beat camera and then belongs to the
// viewer (drag orbits, scroll zooms, double-click resets). Live-only: it runs on wall-clock time, so capture never
// enters it and the film's render(t) stays pure. Wire it to the page with interactive.js.
//
//   const manual = makeManual(canvas, () => filmStateNow, {
//     parts: ['cap', 'sleeve', 'roll', 'exploded'],        // pill order = keys 1..n
//     cams: {intro: {...}, cap: {...}, ...},                // the film's beat cameras {tx, ty, tz, az, el, d}
//     labels: {cap: [[anchor, NAME, sub], ...], ...},       // shown for the part opened last
//     status: {cap: 'Cap off', ...},
//     closes: {cap: ['roll']},                              // closing cap closes roll: what can't stay out alone
//     fromFilm: (s) => ({cap: s.cap, exploded: s.explode}), // the film state's open amount per part
//     toState: (o, t, apart, keep) => ({...pose fields, ...cards}), // open amounts -> the object's pose and cards
//   });
//
// state(t) returns the film's state shape: {act, view, apart, cam, labels, status, ...toState(...)}.

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

export function makeManual(canvas, current, cfg) {
  const {parts, cams, labels = {}, status = {}, closes = {}, toState} = cfg;
  const fromFilm = cfg.fromFilm ?? ((s) => Object.fromEntries(parts.map((k) => [k, s[k] ?? 0])));
  const m = {on: false, open: {}, target: {}, cam: {...cams.intro}, camTo: null, last: 'intro', keep: {}, prev: 0};
  for (const k of parts) m.open[k] = m.target[k] = 0;

  /** Take over from the film at its current state, so nothing jumps. keep: film fields to hold (a turntable angle). */
  const enter = (s = current()) => {
    if (m.on) return;
    m.on = true;
    const f = fromFilm(s);
    for (const k of parts) {
      m.open[k] = f[k] ?? 0;
      m.target[k] = m.open[k] > 0.5 ? 1 : 0;
    }
    m.cam = {...s.cam};
    m.camTo = null;
    m.keep = s;
    m.last = parts.includes(s.act) ? s.act : 'intro';
    m.prev = performance.now() / 1000;
  };
  const leave = () => (m.on = false);
  const lastOpen = () => [...parts].reverse().find((k) => m.target[k] > 0.5) ?? 'intro';
  const toggle = (k) => {
    enter();
    m.target[k] = m.target[k] > 0.5 ? 0 : 1;
    if (!m.target[k]) for (const c of closes[k] ?? []) m.target[c] = 0;
    m.last = m.target[k] ? k : lastOpen();
    m.camTo = {...(cams[m.last] ?? cams.intro)};
  };

  // orbit, zoom, reset on the canvas (the page overlay lets pointer events through)
  let drag = null;
  canvas.style.cursor = 'grab';
  canvas.style.touchAction = 'none';
  canvas.addEventListener('pointerdown', (e) => {
    enter();
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
      enter();
      e.preventDefault();
      m.camTo = null;
      m.cam.d = clamp(m.cam.d * Math.exp(e.deltaY * 0.0012), (cfg.zoom ?? [3.5, 22])[0], (cfg.zoom ?? [3.5, 22])[1]);
    },
    {passive: false},
  );
  canvas.addEventListener('dblclick', () => (m.camTo = {...(cams[m.last] ?? cams.intro)}));

  /** This frame's state, in the film's shape. Eases open amounts and the camera on wall-clock time. */
  const state = (t) => {
    const now = performance.now() / 1000;
    const dt = Math.min(0.1, now - m.prev);
    m.prev = now;
    const kOpen = 1 - Math.exp(-dt / 0.22);
    for (const k of parts) m.open[k] += (m.target[k] - m.open[k]) * kOpen;
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
    const apart = Math.max(...parts.map((k) => o[k]));
    return {
      t,
      act: m.last,
      view: m.last === 'intro' ? 'overview' : m.last,
      apart,
      cam: m.cam,
      labels: {set: labels[m.last] ?? [], o: m.last === 'intro' ? 0 : o[m.last]},
      status: status[m.last] ?? 'Exploring',
      ...toState(o, t, apart, m.keep),
    };
  };
  return {m, parts, enter, leave, toggle, state, isOn: () => m.on, isOpen: (k) => m.target[k] > 0.5};
}
