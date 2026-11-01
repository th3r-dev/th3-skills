// Rendered by figma_js.py (params injected as P); run via run_script / use_figma (allowRemove when re-rendering).
// UI → flow → UI. An arrow leaves the real element on the source screen, runs through flow-kit nodes placed in the
// free corridor to the screen's right, and lands on the target screen (another page, or a copy in the resulting
// state). Nodes sit on a layered grid (columns = steps, rows center-aligned, 10px snap). Lines never run over other
// objects: every edge is routed with A* on an orthogonal grid built from the edges of nearby obstacles (Hanan grid)
// plus offset lanes beside earlier lines; cost = length + bends + per-px penalty for running on/near an earlier
// line + crossings. Ports keep a straight jetty; ends sharing one side of a box get slots sorted by where their
// lines go. Only flow-kit components + the file's variables/text styles are used. Returns `qa` (measured quality).
// Spec: screen, components{node,decision}, tokens{edge,edge_true,edge_false,label_text,chip},
//       anchors[{id, find? (visible text), name? (layer-name regex), component?/state? (instance of a component, in a
//       variant state: survives swaps), node? (exact id: breaks when the layer is swapped), within? (ancestor-name regex),
//       nth? (0-based match index), side? (right|left|top|bottom|auto)}],
//       nodes[{id,type,text}], screens[{id,node}], edges[{from,to,label,tone}], gap?, col?, row?, margin?, region?,
//       lane?, jetty?, bend_cost?, share_rate?, near_rate?, cross_cost?, inner_cross_cost?, label_inline?
const P = __PARAMS__;
const T0 = Date.now();
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const src = await figma.getNodeByIdAsync(P.screen);
if (!src) return { error: 'screen not found ' + P.screen };
const C = { node: await figma.getNodeByIdAsync(P.components.node), decision: await figma.getNodeByIdAsync(P.components.decision) };
const vars = await figma.variables.getLocalVariablesAsync('COLOR');
const styles = await figma.getLocalTextStylesAsync();
const missing = [];
const V = n => { const v = vars.find(x => x.name === n); if (!v) missing.push('variable ' + n); return v; };
const tone = { base: V(P.tokens.edge), true: V(P.tokens.edge_true), false: V(P.tokens.edge_false) };
const chipFill = V(P.tokens.chip);
const labelStyle = styles.find(s => s.name === P.tokens.label_text); if (!labelStyle) missing.push('text style ' + P.tokens.label_text);
if (!C.node || !C.decision) missing.push('flow kit components');
if (missing.length) return { blocked: missing };
const paint = v => figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', v);
const variantOf = (set, type) => set.type === 'COMPONENT_SET' ? (set.children.find(c => c.name.toLowerCase() === `type=${type}`) || set.defaultVariant) : set;
const setLabel = (inst, val) => { const k = Object.keys(inst.componentProperties).find(p => p.startsWith('Label')); if (k) inst.setProperties({ [k]: val }); };
const box = n => { const b = n.absoluteBoundingBox; return { x: b.x, y: b.y, w: b.width, h: b.height }; };
const ctr = b => [b.x + b.w / 2, b.y + b.h / 2];
const M = P.margin ?? 28;                       // clearance kept around every obstacle

// re-render: drop this screen's previous flow (deterministic name)
const tag = `Flow · ${src.name}`;
const removed = [];
for (const n of figma.currentPage.children.filter(n => n.name === tag)) { removed.push(n.id); n.remove(); }

// ---------- obstacles: every top-level object near the flow (screens, labels, other flows' nodes) ----------
const S0 = box(src);
const targets = []; for (const t of P.screens || []) { const n = await figma.getNodeByIdAsync(t.node); if (n?.absoluteBoundingBox) targets.push(box(n)); }
// the search region: right of the source screen, grown to take in every target screen (a flow that lands on a
// screen to its left must still see that screen, its flow and its lines)
const region = P.region || (() => { let x1 = S0.x - 600, y1 = S0.y - 1600, x2 = x1 + 16000, y2 = y1 + Math.max(S0.h, 4000) + 4000;
  for (const b of targets) { x1 = Math.min(x1, b.x - 600); y1 = Math.min(y1, b.y - 600); x2 = Math.max(x2, b.x + b.w + 600); y2 = Math.max(y2, b.y + b.h + 600); }
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 }; })();
const inR = b => !(b.x > region.x + region.w || b.x + b.w < region.x || b.y > region.y + region.h || b.y + b.h < region.y);
const obstacles = [], lines = [];   // lines: other flows' arrows, kept apart from like this flow's own
const addObs = (b, id) => { if (b.w > 0 && b.h > 0 && inR(b)) obstacles.push({ ...b, id }); };
for (const n of figma.currentPage.children) {
  if (n.type === 'CONNECTOR' || n.type === 'VECTOR' || n.type === 'SECTION' || !n.visible) continue;
  if (n.type === 'GROUP') { for (const c of n.children) if (c.type === 'VECTOR') { if (n.name.startsWith('Flow · ')) lines.push(c); } else if (c.visible) addObs(box(c), c.id); continue; }
  addObs(box(n), n.id);
  // the frame's name is drawn on the canvas right above it (the screen title): keep lines off that strip too
  if (n.type === 'FRAME' && n.width >= 1000) { const b = box(n), T = P.title_strip ?? 120; addObs({ x: b.x, y: b.y - T, w: Math.min(b.w, 1600), h: T - 2 }, n.id + ':title'); }
}
const overlaps = (a, b, m = 0) => !(a.x >= b.x + b.w + m || a.x + a.w + m <= b.x || a.y >= b.y + b.h + m || a.y + a.h + m <= b.y);
const isFree = b => !obstacles.some(o => overlaps(b, o, M));

// ---------- anchors (real elements on the source screen) and target screens ----------
// An anchor is picked by visible text (`find`: exact match first, then substring), layer name (`name` regex),
// exact `node` id, optionally only under an ancestor whose name matches `within`; `nth` picks among the matches
// (document order). A matched text is lifted to its nearest filled/stroked container (the button, not the label).
const at = {}, notFound = [], clipped = [], resolved = {};
const spec = Object.fromEntries(P.nodes.map(n => [n.id, n]));
// what is actually visible of a node: cut by every ancestor that clips its content. An element clipped out
// entirely is pulled to the nearest visible spot of the clipping frame (and reported) so its line starts on screen.
const visibleBox = n => {
  let b = box(n), hid = false;
  for (let p = n.parent; p && p.type !== 'PAGE'; p = p.parent) {
    if (!p.clipsContent || !p.absoluteBoundingBox) continue;
    const c = box(p), x1 = Math.max(b.x, c.x), y1 = Math.max(b.y, c.y), x2 = Math.min(b.x + b.w, c.x + c.w), y2 = Math.min(b.y + b.h, c.y + c.h);
    if (x2 > x1 && y2 > y1) b = { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
    else { hid = true; const w = Math.min(b.w, c.w), h = Math.min(b.h, c.h); b = { x: Math.min(Math.max(b.x, c.x), c.x + c.w - w), y: Math.min(Math.max(b.y, c.y), c.y + c.h - h), w, h }; }
  }
  return { b, hid };
};
const pick = async a => {
  if (a.node) { const n = await figma.getNodeByIdAsync(a.node); return n ? [n] : []; }
  // by component (+ state): survives swaps and rebuilds, unlike a node id. `component` is a regex on the component
  // (set) name, `state` a regex on the variant value, e.g. {component: "^Pager Arrow$", state: "^next"}
  if (a.component) {
    const cre = new RegExp(a.component), sre = a.state ? new RegExp(a.state) : null, hits = [];
    for (const i of src.findAllWithCriteria({ types: ['INSTANCE'] })) {
      if (!i.visible) continue;
      const mc = await i.getMainComponentAsync(); if (!mc) continue;
      const set = mc.parent?.type === 'COMPONENT_SET' ? mc.parent : mc;
      if (cre.test(set.name) && (!sre || sre.test(mc.name.split('=').slice(1).join('=')))) hits.push(i);
    }
    return hits;
  }
  const nameRe = a.name ? new RegExp(a.name) : null, withinRe = a.within ? new RegExp(a.within) : null;
  const under = n => { if (!withinRe) return true; for (let p = n.parent; p && p !== src; p = p.parent) if (withinRe.test(p.name)) return true; return false; };
  const pool = src.findAll(n => n.visible && (!a.find || n.type === 'TEXT') && (!nameRe || nameRe.test(n.name)) && under(n));
  if (!a.find) return pool;
  return [...pool.filter(t => t.characters.trim() === a.find), ...pool.filter(t => t.characters.trim() !== a.find && t.characters.includes(a.find))];
};
for (const a of P.anchors) {
  const t = (await pick(a))[a.nth ?? 0];
  if (!t) { notFound.push(a.id); continue; }
  let el = t;
  if (t.type === 'TEXT') for (let p = t.parent; p && p !== src && p.width < 700; p = p.parent) { el = p; if (p.type === 'FRAME' && (p.fills?.length || p.strokes?.length)) break; }
  const v = visibleBox(el); if (v.hid) clipped.push(a.id);
  at[a.id] = { box: v.b, kind: 'anchor', host: S0, side: a.side && a.side !== 'auto' ? a.side : null };
  resolved[a.id] = el.id;
}
// fan-in merge: anchors whose lines go to exactly the same places (e.g. every filter field → "result hidden", or
// Excel/PDF → the same export check) become one line leaving the box around all of them, so a screen shows one
// straight line per action instead of a bundle of parallel ones. Off with merge_fanin: false.
const merged = {};
if (P.merge_fanin !== false) {
  const sig = id => P.edges.filter(e => e.from === id).map(e => `${e.to}|${e.label || ''}|${e.tone || ''}`).sort().join(';');
  const groups = {};
  for (const a of P.anchors) if (at[a.id] && sig(a.id)) (groups[sig(a.id)] ||= []).push(a.id);
  for (const ids of Object.values(groups)) {
    if (ids.length < 2) continue;
    const bs = ids.map(id => at[id].box), x = Math.min(...bs.map(b => b.x)), y = Math.min(...bs.map(b => b.y));
    const head = ids[0];
    at[head] = { ...at[head], box: { x, y, w: Math.max(...bs.map(b => b.x + b.w)) - x, h: Math.max(...bs.map(b => b.y + b.h)) - y } };
    for (const id of ids.slice(1)) { delete at[id]; merged[id] = head; }
  }
  P.edges = P.edges.filter(e => !merged[e.from]);
}
for (const s of P.screens || []) { const n = await figma.getNodeByIdAsync(s.node); if (n) at[s.id] = { box: box(n), kind: 'screen', id: n.id }; else notFound.push(s.id); }
// on-page connectors (flowchart convention): a target screen with another screen between it and this flow is
// "far". Instead of a long line looping past those screens (and crossing everything on the way), the chain ends in
// a lettered marker, and the same letter sits right before the target with a short arrow in. One letter per target
// screen on the page (`Marker · <screen id>`), shared by every flow that goes there. Off with markers: false.
const markersPlaced = [];
if (P.markers !== false && P.components.marker) {
  const MK = await figma.getNodeByIdAsync(P.components.marker);
  const scr = figma.currentPage.children.filter(n => n.type === 'FRAME' && n.width >= 1000 && n.height >= 600 && n.id !== src.id);
  const far = T => scr.some(n => { const b = box(n); return n.id !== T.id && b.x >= S0.x + S0.w - 1 && b.x + b.w <= T.box.x + 1 && b.y < T.box.y + T.box.h && b.y + b.h > T.box.y; });
  const letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  const setNum = (m, v) => { const k = Object.keys(m.componentProperties).find(p => p.startsWith('Number')); if (k) m.setProperties({ [k]: v }); };
  const rewritten = [];
  for (const [ei, e] of P.edges.entries()) {
    const T = at[e.to];
    if (!T || T.kind !== 'screen' || !MK || !far(T)) { rewritten.push(e); continue; }
    // the marker in front of the target: reuse it, or make one with the next free letter in this band of the page
    let pre = figma.currentPage.children.find(n => n.name === `Marker · ${T.id}`);
    if (!pre) {
      const near = figma.currentPage.children.filter(n => n.name.startsWith('Marker · ') && Math.abs(n.y - T.box.y) < 3000);
      const used = new Set(near.map(n => n.getPluginData('label')));
      const L = [...letters].find(c => !used.has(c)) || String(near.length + 1);
      const m = MK.createInstance(); figma.currentPage.appendChild(m); setNum(m, L);
      m.x = Math.round(T.box.x - 120 - m.width); m.y = Math.round(T.box.y + 200 - m.height / 2);
      const cy = Math.round(m.y + m.height / 2), x1 = m.x + m.width, v = figma.createVector(); figma.currentPage.appendChild(v);
      await v.setVectorNetworkAsync({ vertices: [{ x: 0, y: 0 }, { x: T.box.x - x1, y: 0, strokeCap: 'ARROW_LINES' }], segments: [{ start: 0, end: 1 }] });
      v.x = x1; v.y = cy; v.fills = []; v.strokes = [paint(tone.base)]; v.strokeWeight = 3;
      // marker + its arrow into the screen live together, outside any flow: made once, shared by every flow
      pre = figma.group([m, v], figma.currentPage); pre.name = `Marker · ${T.id}`; pre.setPluginData('label', L);
    }
    const L = pre.getPluginData('label');
    const mId = `m_${e.to}_${ei}`;
    spec[mId] = { id: mId, type: 'marker', text: L };
    if (!obstacles.some(o => o.id === pre.id)) obstacles.push({ ...box(pre), id: pre.id });
    P.nodes.push({ id: mId, type: 'marker', text: L });
    markersPlaced.push(`${e.from}→${e.to} via ${L}`);
    rewritten.push({ ...e, to: mId });
  }
  P.edges = rewritten;
  C.marker = MK;
}

// elements inside the source screen (leaves and cards, not page-wide containers): an anchor's first run should
// not cut through its neighbours, and running through another anchor's element counts three times
const J = P.jetty ?? M + 12;   // straight run outside every port before the first bend (room for the arrowhead)
const LANE = P.lane ?? 40, BEND = P.bend_cost ?? 260, SHARE = P.share_rate ?? 4, NEAR = P.near_rate ?? 2, CROSS = P.cross_cost ?? 600;
const XIN = P.inner_cross_cost ?? 1000, JOG = 16;
const DIR = { right: 0, left: 1, bottom: 2, top: 3 }, ENTER = { left: 0, right: 1, top: 2, bottom: 3 };
const VEC = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const across = side => side === 'left' || side === 'right' ? 1 : 0;   // coordinate that varies along a side
// ports: drawio practice — leave/enter on the side facing the peer, keep a straight jetty J outside the port, and
// spread several lines on one side of a box into separate slots. `off` shifts a box's port along its side;
// diamonds keep their single vertex per side.
const portOf = (X, side, off = 0) => {
  const b = X.box, c = ctr(b);
  const p = { right: [b.x + b.w, c[1]], left: [b.x, c[1]], top: [c[0], b.y], bottom: [c[0], b.y + b.h] }[side];
  if (off && X.kind === 'node') { const ax = across(side), half = (ax ? b.h : b.w) / 2 - 12; p[ax] += Math.max(-half, Math.min(half, off)); }
  const v = VEC[DIR[side]], q = p.map(Math.round);
  return { p: q, stub: [q[0] + v[0] * J, q[1] + v[1] * J], side };
};
const innerBoxes = src.findAllWithCriteria({ types: ['TEXT', 'INSTANCE', 'VECTOR', 'RECTANGLE', 'ELLIPSE', 'FRAME'] })
  .filter(n => n.visible && n.absoluteBoundingBox && (n.type !== 'FRAME' || n.fills?.length || n.strokes?.length)).map(box).filter(b => b.w < S0.w / 2 && b.h < S0.h / 3);
const anchorBoxes = Object.values(at).filter(x => x.kind === 'anchor').map(x => x.box);
const segHits = (p, q) => { const h = p[1] === q[1], c = h ? p[1] : p[0], a = Math.min(h ? p[0] : p[1], h ? q[0] : q[1]), z = Math.max(h ? p[0] : p[1], h ? q[0] : q[1]);
  return b => h ? c > b.y + 1 && c < b.y + b.h - 1 && z > b.x + 1 && a < b.x + b.w - 1 : c > b.x + 1 && c < b.x + b.w - 1 && z > b.y + 1 && a < b.y + b.h - 1; };
// elements a polyline inside the screen runs through (a line within 1px of an element's edge does not count); a card and its
// texts count once (only the outermost crossed boxes)
const crossCount = (ab, pts) => {
  const segs = pts.slice(1).map((q, i) => segHits(pts[i], q)), hit = b => !overlaps(b, ab) && segs.some(f => f(b));
  const inside = (b, o) => b !== o && b.x >= o.x - 1 && b.y >= o.y - 1 && b.x + b.w <= o.x + o.w + 1 && b.y + b.h <= o.y + o.h + 1;
  const hits = innerBoxes.filter(hit);
  return hits.filter(b => !hits.some(o => inside(b, o))).length + 2 * anchorBoxes.filter(hit).length;
};
// an anchor's first run, per side: straight out to the screen edge, or out JOG px and over into a channel along the
// edge of a nearby element (a row divider, the gap between a toolbar and a table) when that crosses less. Cost =
// XIN per crossed element + length + BEND per bend; the cheapest per side is offered to the router.
const headCache = {};
const headFor = (A, side) => headCache[`${A.box.x},${A.box.y}:${side}`] ??= (() => {
  const H = A.host, pe = portOf(A, side).p, ax = across(side), sg = side === 'right' || side === 'bottom' ? 1 : -1;
  const edge = side === 'right' ? H.x + H.w + J : side === 'left' ? H.x - J : side === 'bottom' ? H.y + H.h + J : H.y - J;
  const lo = ax ? H.y + 8 : H.x + 8, hi = ax ? H.y + H.h - 8 : H.x + H.w - 8;
  const chans = new Set([pe[ax]]);
  for (const b of innerBoxes) for (const v of ax ? [b.y, b.y + b.h] : [b.x, b.x + b.w]) if (Math.abs(v - pe[ax]) < 200 && v > lo && v < hi) chans.add(Math.round(v));
  let best = null;
  for (const ch of [...chans].sort((p, q) => Math.abs(p - pe[ax]) - Math.abs(q - pe[ax]) || p - q)) {
    let pts;
    if (ch === pe[ax]) pts = [pe, ax ? [edge, pe[1]] : [pe[0], edge]];
    else { const j = ax ? [pe[0] + sg * JOG, pe[1]] : [pe[0], pe[1] + sg * JOG]; pts = [pe, j, ax ? [j[0], ch] : [ch, j[1]], ax ? [edge, ch] : [ch, edge]]; }
    const cl = anchorBoxes.filter(o => o !== A.box && Math.abs(ctr(o)[ax] - ch) < LANE && (ax ? (sg > 0 ? o.x > pe[0] : o.x < pe[0]) : (sg > 0 ? o.y > pe[1] : o.y < pe[1]))).length;   // keep a lane from another element's own line
    const n = crossCount(A.box, pts) + cl, cost = n * XIN + pts.slice(1).reduce((t, q, i) => t + Math.abs(q[0] - pts[i][0]) + Math.abs(q[1] - pts[i][1]), 0) + (pts.length - 2) * BEND;
    if (!best || cost < best.cost) best = { head: pts.slice(0, -1), s: pts[pts.length - 1].map(Math.round), side, n, cost, extra: n * XIN + (pts.length - 2) * BEND };
  }
  return best;
})();
// the side an anchor's line will most likely leave by: cheapest first run plus a rough trip to the flow column
// (one more bend from top/bottom, around the screen from the left); the side facing right first on ties
const likelySide = A => {
  const H = A.host, xc = H.x + H.w + J, est = sd => { const hd = headFor(A, sd), s = hd.s;
    return hd.cost + Math.abs(xc - s[0]) + (sd === 'top' || sd === 'bottom' ? BEND : sd === 'left' ? 2 * BEND + 2 * Math.min(s[1] - H.y, H.y + H.h - s[1]) : 0); };
  return ['right', 'top', 'bottom', 'left'].reduce((b, sd) => est(sd) < est(b) ? sd : b, 'right');
};

// ---------- place flow nodes: layered grid, one band of rows per anchor ----------
// Column = steps from the anchor; column and row centers snap to a 10px grid and every row is aligned on its
// center, so a diamond and a box in the same row meet with one straight line. A node's first new child continues
// on its row (the main path). A decision's 2nd branch drops to a free row in the decision's own column, right
// under its bottom vertex, and its 3rd branch rises to the row right above its top vertex (one straight vertical
// line each); other extra children open a free row one column on.
// Row 0 sits at the anchor's height so the first line runs straight out of the element when there is room.
// Bands are stacked in the order their lines leave the screen, clockwise from the top-left corner (top side
// left→right, right side top→bottom, bottom side right→left): Sugiyama-style ordering by port position, so lines
// from neighbouring elements nest instead of crossing.
const out = new Map(); for (const e of P.edges) { if (!out.has(e.from)) out.set(e.from, []); out.get(e.from).push(e); }
for (const n of P.nodes) spec[n.id] ??= n;
const gap = P.gap ?? 260, colW = P.col ?? 480, rowH = P.row ?? 300, VGAP = Math.max(80, rowH - 200);
const x0 = S0.x + S0.w + gap;
const snap = v => Math.round(v / 10) * 10;
const made = [], bands = [], inst = {}, wide = [];
for (const a of P.anchors) {
  if (!at[a.id]) continue;
  const rows = {}, cell = new Set();
  // the state screen this anchor's chain leads to (first one reached): its steps line up with that screen, so
  // the step sits right before the page it opens and the last run goes straight in
  let target = null;
  { const q0 = [a.id], seen0 = new Set(q0); while (q0.length && !target) { const id = q0.shift();
      for (const e of out.get(id) || []) { if (at[e.to]?.kind === 'screen') { target = at[e.to].box; break; }
        if (spec[e.to] && !seen0.has(e.to)) { seen0.add(e.to); q0.push(e.to); } } } }
  bands.push({ a, rows, side: at[a.id].side || likelySide(at[a.id]), target });
  const freeRow = (r0, c) => { let r = r0 + 1; while (cell.has(`${r},${c}`)) r++; return r; };   // first free row below r0
  const q = [[a.id, 0, 0]], seen = new Set([a.id]);
  while (q.length) {
    const [id, col, row] = q.shift();
    const isDec = spec[id]?.type === 'decision';
    let kids = 0;
    (out.get(id) || []).forEach((e, ei) => {
      if (seen.has(e.to) || at[e.to] || !spec[e.to]) return; seen.add(e.to);
      let c = col + 1, r = row;
      if (isDec && ei === 1 && !cell.has(`${row + 1},${col}`)) { c = col; r = row + 1; }        // straight down from the bottom vertex
      else if (isDec && ei === 2 && !cell.has(`${row - 1},${col}`)) { c = col; r = row - 1; }   // straight up from the top vertex
      else if ((isDec ? ei > 0 : kids > 0) || cell.has(`${r},${c}`)) r = freeRow(row, c);
      kids++; cell.add(`${r},${c}`);
      const s = spec[e.to];
      const n = inst[e.to] = (s.type === 'decision' ? C.decision : s.type === 'marker' ? C.marker : variantOf(C.node, s.type)).createInstance();
      figma.currentPage.appendChild(n);
      if (s.type === 'marker') { const k = Object.keys(n.componentProperties).find(p => p.startsWith('Number')); if (k) n.setProperties({ [k]: s.text }); n.name = `Marker → ${s.text}`; }
      else { setLabel(n, s.text); n.name = s.text.slice(0, 60); }
      (rows[r] ||= []).push({ inst: n, col: c, id: e.to, kind: s.type === 'decision' ? 'decision' : 'node' }); made.push(n);
      if (e.label && inst[id] && r === row && c === col + 1) wide.push({ col: c, label: e.label, w: (inst[id].width + n.width) / 2 });
      q.push([e.to, c, r]);
    });
  }
}
const perim = (A, side) => { const s = headFor(A, side).s, cx = s[0], cy = s[1]; return { top: cx - S0.x, right: S0.w + cy - S0.y, bottom: 2 * S0.w + S0.h + S0.x - cx, left: 3 * S0.w + 2 * S0.h + S0.y - cy }[side]; };
bands.sort((p, q) => perim(at[p.a.id], p.side) - perim(at[q.a.id], q.side));
// a labeled straight run between two columns must fit its chip plus the jetty (drawio: shorten or make room for a
// label wider than its corridor), so widen that column gap when it doesn't
const font = labelStyle.fontName; await figma.loadFontAsync(font);
const labelW = async str => { const t = figma.createText(); t.fontName = font; await t.setTextStyleIdAsync(labelStyle.id); t.characters = str; const w = t.width + 16; t.remove(); return w; };
const extra = [];
for (const x of wide) extra[x.col] = Math.max(extra[x.col] || 0, (await labelW(x.label)) + 24 + J - (colW - 80 - x.w));
let xoff = 0;   // bands that would spill below the screen start a new column of bands to the right (see placeBands)
const colX = col => { let x = x0 + xoff + (col - 1) * colW + (colW - 80) / 2; for (let k = 1; k <= col; k++) x += Math.max(0, extra[k] || 0); return snap(x); };   // column center
const obsBase = obstacles.length;
function placeBands() {
obstacles.length = obsBase;
let floor = S0.y; xoff = 0;
const bottomOK = S0.y + S0.h;   // a flow stays beside its own screen: never runs down beside the next one
for (const { a, rows, side, target } of bands) {
  const keys = Object.keys(rows).map(Number).sort((p, q) => p - q);
  const est = keys.reduce((t, r) => t + Math.max(...rows[r].map(n => n.inst.height)) + VGAP, 0);
  if (P.wrap !== false && floor > S0.y + 1 && floor + est > bottomOK) {
    const maxCol = Math.max(1, ...bands.flatMap(b => Object.values(b.rows).flat().map(n => n.col)));
    xoff += maxCol * colW; floor = S0.y;   // next column of bands, back at the top
  }
  const hOf = r => Math.max(...rows[r].map(n => n.inst.height));
  const fits = (list, cc) => list.every(n => isFree({ x: colX(n.col) - n.inst.width / 2, y: cc - n.inst.height / 2, w: n.inst.width, h: n.inst.height }));
  const put = (list, cc) => { for (const n of list) {
    n.inst.x = colX(n.col) - n.inst.width / 2; n.inst.y = cc - n.inst.height / 2;
    const b = box(n.inst); obstacles.push({ ...b, id: n.inst.id });
    at[n.id] = { box: b, kind: n.kind, id: n.inst.id };
  } };
  const above = keys.filter(r => r < 0).reduce((s, r) => s + hOf(r) + VGAP, 0);   // room kept for rows over row 0
  let prevBottom = null, top0 = null;
  for (const r of keys.filter(r => r >= 0)) {
    const list = rows[r], hMax = hOf(r);
    let c;
    if (prevBottom === null) {   // at the anchor's height, or just below its screen when the line will leave downward
      const ab = at[a.id].box;
      c = side === 'bottom' ? Math.round(S0.y + S0.h + J) : side === 'right' || side === 'left' ? headFor(at[a.id], side).s[1] : Math.round(ab.y + ab.h / 2);
      if (target && P.align_to_target !== false) c = snap(target.y + Math.min(240, target.h / 2));   // beside the screen it opens
      if (c - hMax / 2 < floor + above) c = snap(floor + above + hMax / 2);
    }
    else c = snap(prevBottom + VGAP + hMax / 2);
    while (!fits(list, c)) c += 20;   // slide the whole row down to the first free slot, keeping it aligned
    put(list, c);
    top0 ??= c - hMax / 2; prevBottom = c + hMax / 2;
  }
  let prevTop = top0;
  for (const r of keys.filter(r => r < 0).reverse()) {   // rows over row 0 (a decision's 3rd branch), bottom-up
    const list = rows[r], hMax = hOf(r);
    let c = snap(prevTop - VGAP - hMax / 2);
    for (let k = 0; k < 100 && !fits(list, c); k++) c -= 20;   // ponytail: slides up only; a blocked 3rd branch lands where it can
    put(list, c); prevTop = c - hMax / 2;
  }
  if (prevBottom !== null) floor = prevBottom + M;   // bands keep their order; isFree keeps the clearance
}
}
placeBands();

// ---------- A* orthogonal router on a Hanan grid ----------
// Directions 0 → 1 ← 2 ↓ 3 ↑. Cost = length + BEND per turn + per-px penalties for running on (SHARE) or within a
// lane (NEAR) of an earlier line + CROSS per crossing. The grid also gets lines LANE and 2·LANE beside every earlier
// run, so a later line can run parallel at a clean offset instead of on top of it or far away. `limit` stops the
// search once no path can beat a cost already found (branch and bound across port candidates).
const runsOf = pts => pts.slice(1).map((p, i) => { const q = pts[i]; return q[1] === p[1] ? { h: true, c: p[1], a: Math.min(q[0], p[0]), b: Math.max(q[0], p[0]) } : { h: false, c: p[0], a: Math.min(q[1], p[1]), b: Math.max(q[1], p[1]) }; });
const used = [];               // runs of lines already drawn (other flows' first): { h, c (fixed coord), a, b (range) }
for (const v of lines) {
  const tx = v.absoluteTransform[0][2], ty = v.absoluteTransform[1][2], vn = v.vectorNetwork;
  for (const sg of vn.segments) {
    const q = vn.vertices[sg.start], p = vn.vertices[sg.end], a = [tx + q.x, ty + q.y], b = [tx + p.x, ty + p.y];
    if (Math.abs(a[1] - b[1]) < 0.5 || Math.abs(a[0] - b[0]) < 0.5) used.push(...runsOf([a.map(Math.round), b.map(Math.round)]).filter(r => inR({ x: r.h ? r.a : r.c, y: r.h ? r.c : r.a, w: 1, h: 1 })).map(r => ({ ...r, name: v.name })));
  }
}
const otherRuns = used.slice();
const OPP = [1, 0, 3, 2];
const simplify = pts => {
  const d = pts.filter((p, i) => i === 0 || p[0] !== pts[i - 1][0] || p[1] !== pts[i - 1][1]);
  const s = [d[0]];
  for (let k = 1; k < d.length - 1; k++) { const a = s[s.length - 1], b = d[k], c = d[k + 1]; if (!((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1]))) s.push(b); }
  if (d.length > 1) s.push(d[d.length - 1]);
  return s;
};
const lower = (arr, v) => { let a = 0, b = arr.length; while (a < b) { const m = (a + b) >> 1; if (arr[m] < v) a = m + 1; else b = m; } return a; };
let RM = null;   // router clearance override (a tighter retry before an edge is forced)
function route(p0, sdir, p1, edir, ignore, limit = Infinity) {
  const lo = { x: Math.min(p0[0], p1[0]) - 1500, y: Math.min(p0[1], p1[1]) - 1500 }, hi = { x: Math.max(p0[0], p1[0]) + 1500, y: Math.max(p0[1], p1[1]) + 1500 };
  const m = RM ?? M;
  const near = obstacles.filter(o => !ignore.has(o.id)).map(o => ({ x1: o.x - m, y1: o.y - m, x2: o.x + o.w + m, y2: o.y + o.h + m }))
    .filter(o => !(o.x1 > hi.x || o.x2 < lo.x || o.y1 > hi.y || o.y2 < lo.y));
  const lanes = (h) => used.filter(u => u.h === h).flatMap(u => [u.c - 2 * LANE, u.c - LANE, u.c + LANE, u.c + 2 * LANE]);
  const xs = [...new Set([p0[0], p1[0], lo.x, hi.x, ...near.flatMap(o => [o.x1, o.x2]), ...lanes(false)])].filter(x => x >= lo.x && x <= hi.x).sort((a, b) => a - b);
  const ys = [...new Set([p0[1], p1[1], lo.y, hi.y, ...near.flatMap(o => [o.y1, o.y2]), ...lanes(true)])].filter(y => y >= lo.y && y <= hi.y).sort((a, b) => a - b);
  const NX = xs.length, NY = ys.length, idx = (i, j) => j * NX + i;
  const blocked = new Uint8Array(NX * NY), hBlk = new Uint8Array(NX * NY), vBlk = new Uint8Array(NX * NY);
  for (const o of near) {
    const i1 = lower(xs, o.x1), j1 = lower(ys, o.y1);
    for (let j = j1; j < NY && ys[j] <= o.y2; j++) for (let i = i1; i < NX && xs[i] <= o.x2; i++) {
      const ix = xs[i] > o.x1 && xs[i] < o.x2, iy = ys[j] > o.y1 && ys[j] < o.y2;
      if (ix && iy) blocked[idx(i, j)] = 1;
      if (iy && i + 1 < NX && xs[i] >= o.x1 && xs[i + 1] <= o.x2) hBlk[idx(i, j)] = 1;   // run i→i+1 on row j cuts the interior
      if (ix && j + 1 < NY && ys[j] >= o.y1 && ys[j + 1] <= o.y2) vBlk[idx(i, j)] = 1;   // run j→j+1 on column i cuts the interior
    }
  }
  // penalties from earlier lines: hPen = run i→i+1 on row j, vPen = run j→j+1 on column i
  const hPen = new Float64Array(NX * NY), vPen = new Float64Array(NX * NY);
  for (const u of used) {
    const C1 = u.h ? ys : xs, C2 = u.h ? xs : ys, N1 = C1.length, N2 = C2.length, pen = u.h ? hPen : vPen, cross = u.h ? vPen : hPen;
    const at2 = (k1, k2) => u.h ? idx(k2, k1) : idx(k1, k2);
    for (let k1 = lower(C1, u.c - LANE + 1); k1 < N1 && C1[k1] < u.c + LANE; k1++) {      // parallel and close
      const rate = C1[k1] === u.c ? SHARE : NEAR;
      for (let k2 = Math.max(0, lower(C2, u.a) - 1); k2 + 1 < N2 && C2[k2] < u.b; k2++) {
        const ov = Math.min(C2[k2 + 1], u.b) - Math.max(C2[k2], u.a); if (ov > 0) pen[at2(k1, k2)] += ov * rate;
      }
    }
    // perpendicular runs that cross it or touch it (a line ending on another line reads as a merge)
    for (let k1 = Math.max(0, lower(C1, u.c) - 1); k1 + 1 < N1 && C1[k1] <= u.c; k1++) if (C1[k1 + 1] >= u.c)
      for (let k2 = lower(C2, u.a); k2 < N2 && C2[k2] <= u.b; k2++) cross[u.h ? idx(k2, k1) : idx(k1, k2)] += CROSS;
  }
  const si = xs.indexOf(p0[0]), sj = ys.indexOf(p0[1]), ti = xs.indexOf(p1[0]), tj = ys.indexOf(p1[1]);
  const N = NX * NY * 4, g = new Float64Array(N).fill(Infinity), prev = new Int32Array(N).fill(-1);
  const heap = [];
  const push = (f, s) => { heap.push([f, s]); let c = heap.length - 1; while (c > 0) { const p = (c - 1) >> 1; if (heap[p][0] <= heap[c][0]) break; [heap[p], heap[c]] = [heap[c], heap[p]]; c = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let c = 0; for (;;) { const l = 2 * c + 1, r = l + 1; let m = c; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === c) break; [heap[m], heap[c]] = [heap[c], heap[m]]; c = m; } } return top; };
  const h = (i, j) => Math.abs(xs[i] - xs[ti]) + Math.abs(ys[j] - ys[tj]);
  for (let d = 0; d < 4; d++) { if (d === OPP[sdir]) continue; const s = idx(si, sj) * 4 + d; g[s] = d === sdir ? 0 : BEND; push(g[s] + h(si, sj), s); }   // leave the stub in the port's direction
  const DX = [1, -1, 0, 0], DY = [0, 0, 1, -1];
  let goal = -1;
  while (heap.length) {
    const [f, s] = pop(); const node = s >> 2, d = s & 3, i = node % NX, j = (node / NX) | 0;
    if (f - h(i, j) > g[s] + 1e-6) continue;   // stale heap entry
    if (f >= limit) break;                      // nothing left can beat the best candidate so far
    if (i === ti && j === tj) { goal = s; break; }
    for (let nd = 0; nd < 4; nd++) {
      if (nd === OPP[d]) continue;
      const ni = i + DX[nd], nj = j + DY[nd]; if (ni < 0 || nj < 0 || ni >= NX || nj >= NY) continue;
      const end = ni === ti && nj === tj;
      if (blocked[idx(ni, nj)] && !end) continue;
      if (end && nd === OPP[edir]) continue;
      const k = nd < 2 ? idx(Math.min(i, ni), j) : idx(i, Math.min(j, nj));
      if (nd < 2 ? hBlk[k] : vBlk[k]) continue;
      const len = Math.abs(xs[ni] - xs[i]) + Math.abs(ys[nj] - ys[j]);
      const ns = idx(ni, nj) * 4 + nd, cost = g[s] + len + (nd !== d ? BEND : 0) + (nd < 2 ? hPen[k] : vPen[k]) + (end && nd !== edir ? BEND : 0);
      if (cost < g[ns]) { g[ns] = cost; prev[ns] = s; push(cost + h(ni, nj), ns); }
    }
  }
  if (goal < 0) return null;
  const pts = []; for (let s = goal; s >= 0; s = prev[s]) { const n = s >> 2; pts.push([xs[n % NX], ys[(n / NX) | 0]]); }
  return { pts: simplify(pts.reverse()), cost: g[goal] };
}

// ---------- route every edge: two passes ----------
// Pass 1 picks each edge's sides: every candidate pair is ordered by a Manhattan lower bound and routed only while
// it can still win. Pass 2 sorts the ends that share one side of a box by where their lines head (drawio edgeports:
// order by the far end, so lines keep their order instead of swapping at the box), spaces them a lane apart around
// the one that runs straight, and re-routes every edge on its chosen sides. Only pass 2 is drawn.
// an anchor's first run is drawn straight, outside the router: charge it the router's share/near/cross penalties
const headPen = (a, b) => runsOf([a, b]).reduce((t, r) => t + used.reduce((s, u) => {
  if (u.h === r.h) { const ov = Math.min(u.b, r.b) - Math.max(u.a, r.a), d = Math.abs(u.c - r.c); return s + (ov > 0 && d < LANE ? ov * (d ? NEAR : SHARE) : 0); }
  return s + (u.c >= r.a && u.c <= r.b && r.c >= u.a && r.c <= u.b ? CROSS : 0);
}, 0), 0);
const dist = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
// decisions keep the house convention: 1st outgoing edge right, 2nd bottom, 3rd top
const decSide = {}, decN = {};
P.edges.forEach((e, ei) => { if (at[e.from]?.kind === 'decision' && at[e.to]) decSide[ei] = ['right', 'bottom', 'top'][Math.min(decN[e.from] = (decN[e.from] ?? -1) + 1, 2)]; });
const failed = [], exits = {};
function routeOne(e, ei, fx, st8) {
  const A = at[e.from], B = at[e.to];
  const toward = ctr(B.box), from = ctr(A.box);
  const seqOff = (X, side, far) => { const k = st8.cnt[`${X.id}:${side}`] || 0, ax = across(side); return k ? Math.sign(far[ax] - ctr(X.box)[ax] || 1) * k * LANE : 0; };
  // exit candidates: anchors leave on any side by that side's cheapest first run (headFor); boxes may leave
  // right/bottom/top
  let starts;
  if (A.kind === 'anchor') {
    const face = B.box.x + B.box.w < A.host.x ? 'left' : 'right';
    const sides = fx ? [fx.sa] : A.side ? [A.side] : [face, 'top', 'bottom', face === 'right' ? 'left' : 'right'];
    // leaving on the back side (away from the flow) wraps the line around its own screen: only when nothing else works
    const back = face === 'right' ? 'left' : 'right';
    starts = sides.map(side => { const hd = headFor(A, side); return { head: hd.head, s: hd.s, side, extra: sides.length > 1 ? hd.extra + (side === back ? (P.back_side_cost ?? 2500) : 0) : 0 }; });
  } else {
    // a decision prefers its conventional side; the others stay possible (at a price) so a branch is never dropped
    const pref = A.kind === 'decision' ? decSide[ei] : null;
    const sides = fx ? [fx.sa] : pref ? [pref, ...['right', 'bottom', 'top'].filter(x => x !== pref)] : ['right', 'bottom', 'top'];
    starts = sides.map(side => { const pt = portOf(A, side, fx ? fx.offA : seqOff(A, side, toward)); return { head: [pt.p], s: pt.stub, side, extra: pref && side !== pref ? (P.off_convention_cost ?? 3000) : 0 }; });
  }
  // entry candidates: boxes from left/top/bottom; screens on the side facing the source, at the source's height
  // when it fits, moved down a lane at a time while another line already lands there
  let ends;
  if (B.kind === 'screen') {
    // also taken: heights where any line (this flow's or another's) already leaves or enters this screen's edges,
    // otherwise the fixed jetty into the screen can sit right on top of it
    const L0 = B.box.x - J - LANE, L1 = B.box.x, R0 = B.box.x + B.box.w, R1 = R0 + J + LANE;
    const taken = [...(st8.screenY[e.to] || []),
      ...used.filter(r => r.h && r.c > B.box.y && r.c < B.box.y + B.box.h && ((r.a <= L1 && r.b >= L0) || (r.a <= R1 && r.b >= R0))).map(r => r.c)];
    let y = Math.round(Math.min(Math.max(starts[0].s[1], B.box.y + 80), B.box.y + B.box.h - 80));
    while (taken.some(t => Math.abs(t - y) < LANE)) y += LANE;
    const bx = Math.round(B.box.x + Math.min(B.box.w - 120, 160 + (st8.screenY[e.to] || []).length * LANE));   // returns land near the top-left, staggered
    ends = [{ p: [Math.round(B.box.x), y], stub: [Math.round(B.box.x - J), y], side: 'left' }, { p: [Math.round(B.box.x + B.box.w), y], stub: [Math.round(B.box.x + B.box.w + J), y], side: 'right' },
      { p: [bx, Math.round(B.box.y)], stub: [bx, Math.round(B.box.y - J)], side: 'top', extra: P.screen_vertical_cost ?? 400 },
      { p: [bx, Math.round(B.box.y + B.box.h)], stub: [bx, Math.round(B.box.y + B.box.h + J)], side: 'bottom', extra: P.screen_vertical_cost ?? 400 }]
      .filter(en => !fx || en.side === fx.sb);
  } else ends = (fx ? [fx.sb] : ['left', 'top', 'bottom']).map(sd => portOf(B, sd, fx ? fx.offB : seqOff(B, sd, from)));
  const ignore = new Set([A.id, B.id].filter(Boolean));
  const combos = [];
  for (const st of starts) for (const en of ends) {
    const hp = [...st.head, st.s], pre = (st.extra || 0) + (en.extra || 0) + hp.slice(1).reduce((t, q, i) => t + dist(hp[i], q) + headPen(hp[i], q), 0);
    combos.push({ st, en, pre, lb: pre + dist(st.s, en.stub) });
  }
  combos.sort((p, q) => p.lb - q.lb);
  let best = null;
  for (const { st, en, pre, lb } of combos) {
    if (best && lb >= best.c) break;
    const r = route(st.s, DIR[st.side], en.stub, ENTER[en.side], ignore, best ? best.c - pre : Infinity);
    if (r && (!best || r.cost + pre < best.c)) best = { c: r.cost + pre, st, en, mid: r.pts };
  }
  if (!best) return null;
  const pts = simplify([...best.st.head, ...best.mid, best.en.p]);
  return { e, ei, A, B, sa: best.st.side, sb: best.en.side, pts, runs: runsOf(pts), headN: A.kind === 'anchor' ? best.st.head.length : 0, headPts: [...best.st.head, best.st.s] };
}
// short edges first, long ones (to a remote screen) last: a long line has room to detour, so it should be the
// one that pays for crossings, not the short lines it would otherwise block (libavoid-style ordering)
const order = P.edges.map((e, ei) => ei).filter(ei => at[P.edges[ei].from] && at[P.edges[ei].to])
  .sort((p, q) => dist(ctr(at[P.edges[p].from].box), ctr(at[P.edges[p].to].box)) - dist(ctr(at[P.edges[q].from].box), ctr(at[P.edges[q].to].box)) || p - q);
function routeAll(plan) {
  used.length = 0; used.push(...otherRuns);
  const st8 = { cnt: {}, screenY: {} }, res = [];
  for (const ei of order) {
    const e = P.edges[ei];
    const r = routeOne(e, ei, plan?.[ei], st8) || (plan && routeOne(e, ei, null, st8));
    if (!r) { if (!plan) failed.push(`${e.from}→${e.to}`); continue; }
    for (const [X, sd] of [[r.A, r.sa], [r.B, r.sb]]) if (X.id) st8.cnt[`${X.id}:${sd}`] = (st8.cnt[`${X.id}:${sd}`] || 0) + 1;
    if (r.B.kind === 'screen') (st8.screenY[e.to] ||= []).push(r.pts[r.pts.length - 1][1]);
    used.push(...r.runs); res.push(r);
  }
  return res;
}
function routeBoth() {
failed.length = 0;
const pass1 = routeAll(null);
const plan = {}, ends = {};
for (const r of pass1) {
  plan[r.ei] = { sa: r.sa, sb: r.sb, offA: 0, offB: 0 };
  for (const [X, sd, seq, key] of [[r.A, r.sa, r.pts, 'offA'], [r.B, r.sb, [...r.pts].reverse(), 'offB']]) {
    if (X.kind !== 'node') continue;
    const ax = across(sd), p = seq[0], q = seq.find(v => Math.abs(v[ax] - p[ax]) > 1);
    (ends[`${X.id}:${sd}`] ||= []).push({ ei: r.ei, key, far: q ? q[ax] : p[ax], c: ctr(X.box)[ax], half: (ax ? X.box.h : X.box.w) / 2 - 12 });
  }
}
for (const g of Object.values(ends)) {
  g.sort((p, q) => p.far - q.far || p.ei - q.ei);
  const m = g.reduce((bi, x, i) => Math.abs(x.far - x.c) < Math.abs(g[bi].far - g[bi].c) ? i : bi, 0);   // the straightest keeps the middle
  const sp = Math.min(LANE, g[0].half / Math.max(1, m, g.length - 1 - m));
  g.forEach((x, i) => { plan[x.ei][x.key] = (i - m) * sp; });
}
return routeAll(plan);
}
const crossOf = rs => { let n = 0; rs.forEach((r, i) => rs.slice(i + 1).forEach(q => r.runs.forEach(a => q.runs.forEach(b => {
  if (a.h !== b.h && b.c > a.a && b.c < a.b && a.c > b.a && a.c < b.b) n++; })))); return n; };
let routed = routeBoth();
// no line may cross another: when this flow's own lines cross, stack the bands in the order their lines actually
// cross the screen's right edge (top to bottom) and route again; keep whichever crosses less
if (P.reorder !== false && crossOf(routed) > 0 && bands.length > 1) {
  const X = S0.x + S0.w, before = bands.slice();
  const exitY = b => { const r = routed.find(q => q.e.from === b.a.id); if (!r) return Infinity;
    const u = r.runs.find(q => q.h && q.a <= X && q.b >= X); return u ? u.c : r.pts[r.pts.length - 1][1]; };
  const ys = new Map(bands.map(b => [b, exitY(b)]));
  bands.sort((p, q) => ys.get(p) - ys.get(q));
  placeBands(); const alt = routeBoth();
  if (crossOf(alt) < crossOf(routed)) routed = alt;
  else { bands.splice(0, bands.length, ...before); placeBands(); routed = routeBoth(); }
}
// every edge is drawn: one the router can't place gets a plain elbow between its ports (flagged `forced` for review)
// instead of leaving its nodes floating. A floating node reads as a broken flow; a forced line reads as "check me".
const forced = [];
{
  const done = new Set(routed.map(r => r.ei));
  const st8r = { cnt: {}, screenY: {} };
  P.edges.forEach((e, ei) => {
    if (done.has(ei) || !at[e.from] || !at[e.to]) return;
    RM = 8; const tight = routeOne(e, ei, null, st8r); RM = null;   // squeeze through with a small clearance first
    if (tight) { routed.push(tight); used.push(...tight.runs); return; }
    const A = at[e.from], B = at[e.to];
    const sa = A.kind === 'decision' ? (decSide[ei] || 'right') : 'right';
    const s0 = portOf(A, sa, 0), t0 = B.kind === 'screen' ? { p: [Math.round(B.box.x), Math.round(B.box.y + 80)], stub: [Math.round(B.box.x - J), Math.round(B.box.y + 80)] } : portOf(B, 'left', 0);
    const a = s0.stub, b = t0.stub, mx = Math.round(Math.max(a[0], (a[0] + b[0]) / 2));
    const pts = simplify(sa === 'right' ? [s0.p, a, [mx, a[1]], [mx, b[1]], b, t0.p] : [s0.p, a, [a[0], b[1]], b, t0.p]);
    routed.push({ e, ei, A, B, sa, sb: 'left', pts, runs: runsOf(pts), headN: 0, headPts: [], forced: true });
    forced.push(`${e.from}→${e.to}`);
  });
}

// ---------- draw: lines, then labels in free space clear of every line ----------
const arrows = [], chips = [], drawn = [];
for (const { e, A, sa, pts } of routed) {
  if (A.kind === 'anchor') exits[e.from] = sa;
  const minX = Math.min(...pts.map(p => p[0])), minY = Math.min(...pts.map(p => p[1]));
  const v = figma.createVector(); figma.currentPage.appendChild(v);
  await v.setVectorNetworkAsync({
    vertices: pts.map(([x, y], i) => ({ x: x - minX, y: y - minY, ...(i === pts.length - 1 ? { strokeCap: 'ARROW_LINES' } : {}) })),
    segments: pts.slice(1).map((_, i) => ({ start: i, end: i + 1 })),
  });
  v.x = minX; v.y = minY; v.fills = []; v.strokes = [paint(tone[e.tone] || tone.base)]; v.strokeWeight = 3; v.strokeJoin = 'ROUND';
  v.name = `${e.from} → ${e.to}`; made.push(v); arrows.push(v.id);
}
for (const [k, r] of routed.entries()) {
  const { e, A, B, pts } = r;
  let chipBox = null;
  if (e.label) {
    // label just after the branch point: the first run (from the source) with room and free space. Short labels
    // (True/False) sit on the line; longer ones sit beside it so the chip never severs the line or hides a bend.
    const chip = figma.createFrame(); chip.name = 'Label'; chip.layoutMode = 'HORIZONTAL';
    chip.primaryAxisSizingMode = 'AUTO'; chip.counterAxisSizingMode = 'AUTO';
    chip.paddingLeft = chip.paddingRight = 8; chip.paddingTop = chip.paddingBottom = 2; chip.cornerRadius = 4; chip.fills = [paint(chipFill)];
    const t = figma.createText(); await t.setTextStyleIdAsync(labelStyle.id);
    t.characters = e.label; t.fills = [paint(tone[e.tone] || tone.base)]; chip.appendChild(t);
    figma.currentPage.appendChild(chip);
    const w = chip.width, hh = chip.height, onLine = w <= (P.label_inline ?? 64), G = 12;
    const lineBoxes = used.filter(u => !(onLine && r.runs.includes(u))).map(u => u.h ? { x: u.a, y: u.c - 2, w: u.b - u.a, h: 4 } : { x: u.c - 2, y: u.a, w: 4, h: u.b - u.a });
    const free = q => !obstacles.some(o => overlaps(q, o, 4)) && !chips.some(o => overlaps(q, o, 6)) && !lineBoxes.some(o => overlaps(q, o, 2));
    let spot = null;
    const runs = pts.slice(1).map((p, i) => [pts[i], p]);
    for (let i = 1; i < pts.length && !spot; i++) {
      const q = pts[i - 1], p = pts[i], hz = q[1] === p[1], L = dist(q, p), need = (hz ? w : hh) + 2 * G;
      if (L < need + (i === pts.length - 1 ? J : 0)) continue;
      const sg = Math.sign(hz ? p[0] - q[0] : p[1] - q[1]);
      for (const cand of onLine ? [0] : [-1, 1]) {   // on the line, else above/below (left/right of a vertical run)
        const cx = hz ? q[0] + sg * (G + w / 2) : q[0] + cand * (w / 2 + 8), cy = hz ? q[1] + cand * (hh / 2 + 6) : q[1] + sg * (G + hh / 2);
        const sq = { x: cx - w / 2, y: cy - hh / 2, w, h: hh };
        if (free(sq)) { spot = sq; break; }
      }
    }
    for (const [q, p] of [...runs].sort((a, b) => dist(...b) - dist(...a))) {   // else centered beside a run, longest first
      if (spot) break;
      const hz = q[1] === p[1], m = [(q[0] + p[0]) / 2, (q[1] + p[1]) / 2];
      for (const cand of [-1, 1]) {
        const sq = { x: m[0] - w / 2 + (hz ? 0 : cand * (w / 2 + 8)), y: m[1] - hh / 2 + (hz ? cand * (hh / 2 + 6) : 0), w, h: hh };
        if (free(sq)) { spot = sq; break; }
      }
    }
    if (!spot) {   // last resort: on the middle of the longest run
      let bl = -1; for (let i = 1; i < pts.length; i++) { const L = dist(pts[i - 1], pts[i]); if (L > bl) { bl = L; spot = { x: (pts[i][0] + pts[i - 1][0]) / 2 - w / 2, y: (pts[i][1] + pts[i - 1][1]) / 2 - hh / 2, w, h: hh }; } }
    }
    chip.x = Math.round(spot.x); chip.y = Math.round(spot.y); made.push(chip);
    chipBox = { ...spot, id: chip.id, onLine };
    chips.push(chipBox); obstacles.push(chipBox);
  }
  drawn.push({ name: `${e.from} → ${e.to}`, pts, runs: r.runs, headN: r.headN, headPts: r.headPts, A, B, chip: chipBox });
}
const grp = made.length ? figma.group(made, figma.currentPage) : null;
if (grp) grp.name = tag;
// the graph as actually drawn (Design → State → graph JSON), for inspection: what is connected, what was forced,
// what reads backwards (right-to-left or bottom-to-top), and which steps ended up orphaned
const drawnSet = new Set(routed.map(r => `${r.e.from}→${r.e.to}`));
const cx = b => [b.x + b.w / 2, b.y + b.h / 2];
const graph = {
  screen: src.id,
  nodes: [...P.anchors.filter(a => at[a.id]).map(a => ({ id: a.id, kind: 'anchor', layer: resolved[a.id], box: at[a.id].box })),
          ...P.nodes.filter(n => at[n.id]).map(n => ({ id: n.id, kind: n.type, text: n.text, layer: at[n.id].id, box: at[n.id].box })),
          ...(P.screens || []).filter(t => at[t.id]).map(t => ({ id: t.id, kind: 'screen', layer: at[t.id].id, box: at[t.id].box }))],
  edges: P.edges.map(e => {
    const r = routed.find(x => x.e === e), A = at[e.from], B = at[e.to];
    const d = A && B ? [cx(B.box)[0] - cx(A.box)[0], cx(B.box)[1] - cx(A.box)[1]] : null;
    return { from: e.from, to: e.to, label: e.label || null, drawn: !!r, forced: !!(r && r.forced),
      bends: r ? r.pts.length - 2 : null, back: !!(d && B.kind !== 'screen' && (d[0] < -40 || (Math.abs(d[0]) <= 40 && d[1] < -40))) };
  }),
};
const touched = new Set(graph.edges.filter(e => e.drawn).flatMap(e => [e.from, e.to]));
graph.orphans = P.nodes.filter(n => at[n.id] && !touched.has(n.id)).map(n => n.id);
graph.missing = graph.edges.filter(e => !e.drawn).map(e => `${e.from}→${e.to}`);
graph.backward = graph.edges.filter(e => e.back).map(e => `${e.from}→${e.to}`);
graph.forced = forced;
const inside = (a, b) => a.x >= b.x - 1 && a.y >= b.y - 1 && a.x + a.w <= b.x + b.w + 1 && a.y + a.h <= b.y + b.h + 1;
const anc = P.anchors.filter(a => at[a.id] && at[a.id].kind === 'anchor');
graph.nested = anc.flatMap((a, i) => anc.slice(i + 1).filter(b => resolved[a.id] !== resolved[b.id] && (inside(at[a.id].box, at[b.id].box) || inside(at[b.id].box, at[a.id].box))).map(b => `${a.id}⊂${b.id}`));
return { markers: markersPlaced, flow: grp?.id, graph, nodes: made.filter(n => n.type === 'INSTANCE').length, arrows: arrows.length, failed, merged, exits, anchors: resolved, clipped, notFound, removed, obstacles: obstacles.length, qa: qa(), ms: Date.now() - T0 };

// ---------- QA: measured, not eyeballed (drawio validate.py: through-vertex + crossings, plus spacing/labels) ----------
// crossings: proper crossings between this flow's lines (crossOther: with other flows' lines). lineOverObjects:
// runs through any box but the edge's own ends (an element's first run may cross its own screen; headInner counts
// the elements it passes inside that screen, another anchor's element three times). minParallelGap: closest pair of overlapping parallel runs of
// different lines. labelOverlaps: chips touching a line (their own, unless they sit on it), a box or another chip.
function qa() {
  const cross = (r, u) => r.h !== u.h && u.c > r.a && u.c < r.b && r.c > u.a && r.c < u.b;
  const thin = r => r.h ? { x: r.a, y: r.c - 1, w: r.b - r.a, h: 2 } : { x: r.c - 1, y: r.a, w: 2, h: r.b - r.a };
  const through = (r, o) => r.h ? r.c > o.y + 1 && r.c < o.y + o.h - 1 && r.b > o.x + 1 && r.a < o.x + o.w - 1 : r.c > o.x + 1 && r.c < o.x + o.w - 1 && r.b > o.y + 1 && r.a < o.y + o.h - 1;
  const par = (r, u) => r.h === u.h && Math.min(r.b, u.b) - Math.max(r.a, u.a) > 0 ? Math.abs(r.c - u.c) : Infinity;
  let crossings = 0, crossOther = 0, gap = Infinity, gapAt = null, labelOverlaps = 0, bends = 0, length = 0, headInner = 0;
  const over = [], pairs = [];
  const near = (g, what) => { if (g < gap) { gap = g; gapAt = what; } };   // remember which pair is closest
  drawn.forEach((d, k) => {
    bends += d.pts.length - 2; length += d.runs.reduce((s, r) => s + r.b - r.a, 0);
    d.runs.forEach((r, i) => {
      for (const o of obstacles) {
        if (o.id === d.A.id || o.id === d.B.id || o.id === d.chip?.id) continue;
        if (o.id === src.id && i < d.headN) continue;   // an element's first run leaves its own screen
        if (through(r, o)) over.push(`${d.name} × ${o.id}`);
      }
      for (const d2 of drawn.slice(k + 1)) for (const u of d2.runs) {
        if (cross(r, u)) { crossings++; pairs.push(`${d.name} × ${d2.name}`); }
        near(par(r, u), `${d.name} ∥ ${d2.name}`);
      }
      for (const u of otherRuns) { if (cross(r, u)) crossOther++; near(par(r, u), `${d.name} ∥ ${u.name || 'other flow'} @${r.h ? 'y' : 'x'}=${Math.round(r.c)}`); }
    });
    if (d.headN) headInner += crossCount(d.A.box, d.headPts);
    const c = d.chip;
    if (c && (obstacles.some(o => o.id !== c.id && overlaps(c, o)) || drawn.some(x => (x !== d || !c.onLine) && x.runs.some(r => overlaps(c, thin(r)))) || otherRuns.some(r => overlaps(c, thin(r))))) labelOverlaps++;
  });
  return { crossings, crossOther, lineOverObjects: over.length, minParallelGap: gap === Infinity ? null : gap, minParallelAt: gapAt, labelOverlaps, bends, length, headInner, over: over.slice(0, 12), pairs: pairs.slice(0, 12) };
}
