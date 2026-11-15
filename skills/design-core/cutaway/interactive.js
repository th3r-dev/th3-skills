// design-core cutaway: wires manual.js into the green page (upstream's green/console.js). Makes every part's pill a
// real button (click, Enter, space, its number key), adds the hint bar with "Play film", and keeps the page honest
// while the viewer drives: every open part's pill lit, the scripted cursor hidden, the film clock reading "Manual".
// Exposes window.CUTAWAY = {manual} for check_page.mjs. Live-only: call it under `if (!capture)`.
//
//   const page = attachManual({ui, canvas, manual, acts});   // acts: [[part, label], ...] as the pills were made
//   ...in render(t): const s = page.state(t, filmStateAt); ui.update({...cursor: page.cursor(cursorAt(t))}); page.after();

const GREEN = '#16b364';
const CSS = `.vp .manual-bar{position:absolute;left:50%;transform:translateX(-50%);top:802px;display:flex;align-items:center;gap:12px;padding:4px 4px 4px 14px;border:1px solid #e8edf3;border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 4px 14px rgba(15,23,42,.06);font:500 12.5px/1 'Inter',sans-serif;color:#475569;white-space:nowrap}
.vp .manual-bar button[hidden]{display:none}
.vp .manual-bar button{pointer-events:auto;cursor:pointer;height:28px;padding:0 14px;border:1px solid ${GREEN};border-radius:14px;background:#effbf4;color:#0b7a43;font:600 12.5px/1 'Inter',sans-serif}
.vp .manual-bar button:focus-visible,.vp .pill:focus-visible{outline:2px solid ${GREEN};outline-offset:2px}`;
const HINT_FILM = 'Click a part to open it · drag to orbit · scroll to zoom';
const HINT_MANUAL = 'Drag to orbit · scroll to zoom · double-click to reset the view';

export function attachManual({ui, canvas, manual, acts}) {
  const css = document.createElement('style');
  css.textContent = CSS;
  document.head.appendChild(css);
  const bar = document.createElement('div');
  bar.className = 'manual-bar';
  bar.innerHTML = `<span data-hint>${HINT_FILM}</span><button type="button" data-play hidden>Play film</button>`;
  ui.root.appendChild(bar);
  const play = bar.querySelector('[data-play]');
  const hint = bar.querySelector('[data-hint]');
  const timeEl = ui.root.querySelector('[data-v="time"]');
  const progEl = ui.root.querySelector('[data-v="prog"]');
  const sync = () => {
    play.hidden = !manual.isOn();
    hint.textContent = manual.isOn() ? HINT_MANUAL : HINT_FILM;
  };
  const toggle = (k) => {
    manual.toggle(k);
    sync();
  };
  for (const [k] of acts) {
    const el = ui.pills[k];
    if (!el) continue;
    Object.assign(el.style, {pointerEvents: 'auto', cursor: 'pointer'});
    el.setAttribute('role', 'button');
    el.tabIndex = 0;
    el.addEventListener('click', () => toggle(k));
    el.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      e.stopPropagation(); // the runtime's space would pause the film
      toggle(k);
    });
  }
  addEventListener('keydown', (e) => {
    const i = Number(e.key) - 1;
    if (Number.isInteger(i) && i >= 0 && i < manual.parts.length) toggle(manual.parts[i]);
  });
  canvas.addEventListener('pointerdown', sync);
  canvas.addEventListener('wheel', sync);
  play.addEventListener('click', () => {
    manual.leave();
    dispatchEvent(new KeyboardEvent('keydown', {key: 'r'})); // the runtime restarts the film from 0
    sync();
  });
  window.CUTAWAY = {manual};

  let film = null;
  return {
    /** The frame's state: the viewer's while they drive, else the film's (kept as the take-over point). */
    state: (t, stateAt) => (manual.isOn() ? manual.state(t) : (film = stateAt(t))),
    film: () => film,
    /** The scripted cursor only while the film runs. */
    cursor: (c) => (manual.isOn() ? null : c),
    /** After ui.update: light every open part's pill, and the clock reads Manual. */
    after() {
      if (!manual.isOn()) return;
      for (const [k, el] of Object.entries(ui.pills)) el.classList.toggle('on', manual.isOpen(k));
      timeEl.textContent = 'Manual';
      progEl.style.width = '0%';
    },
  };
}
