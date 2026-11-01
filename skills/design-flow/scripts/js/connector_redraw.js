// Rendered by figma_js.py (params injected as P); run via run_script / use_figma.
// Repairs connectors whose elbow route went stale. Figma stores an elbowed connector's route as fixed points, and
// moving the glued layers through the Plugin API (or a large canvas move) doesn't recompute it, so the line
// stretches back to the old position. Design mode can't create, clone or re-route connectors, so each stale
// connector is redrawn as a vector with the same ends, magnets, stroke (variable bindings kept), weight, dashes,
// caps and label, and the original is hidden (not deleted), so the change is reversible.
// P: page, ids? (connector ids; default = every stale connector), slack? (px a route may extend past its ends, 400)
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const SLACK = P.slack ?? 400, J = P.jetty ?? 32;
const all = figma.currentPage.children.filter(n => n.type === 'CONNECTOR' && n.visible);
const endBox = async e => {
  if (e.endpointNodeId) { const n = await figma.getNodeByIdAsync(e.endpointNodeId); return n ? n.absoluteBoundingBox : null; }
  return e.position ? { x: e.position.x, y: e.position.y, width: 0, height: 0 } : null;
};
async function isStale(c) {
  const a = await endBox(c.connectorStart), b = await endBox(c.connectorEnd), r = c.absoluteBoundingBox;
  if (!a || !b || !r) return false;
  const x0 = Math.min(a.x, b.x), x1 = Math.max(a.x + a.width, b.x + b.width), y0 = Math.min(a.y, b.y), y1 = Math.max(a.y + a.height, b.y + b.height);
  return Math.max(x0 - r.x, r.x + r.width - x1, y0 - r.y, r.y + r.height - y1) > SLACK;
}
const targets = [];
for (const c of all) if (P.ids ? P.ids.includes(c.id) : await isStale(c)) targets.push(c);

const DIR = { LEFT: [-1, 0], RIGHT: [1, 0], TOP: [0, -1], BOTTOM: [0, 1] };
function port(b, magnet, other) {
  let m = magnet;
  if (!DIR[m]) {   // AUTO / CENTER / NONE: the side facing the other end
    const cx = b.x + b.width / 2, cy = b.y + b.height / 2, dx = other[0] - cx, dy = other[1] - cy;
    m = Math.abs(dx) >= Math.abs(dy) ? (dx >= 0 ? 'RIGHT' : 'LEFT') : (dy >= 0 ? 'BOTTOM' : 'TOP');
  }
  const p = { LEFT: [b.x, b.y + b.height / 2], RIGHT: [b.x + b.width, b.y + b.height / 2], TOP: [b.x + b.width / 2, b.y], BOTTOM: [b.x + b.width / 2, b.y + b.height] }[m];
  return { p: p.map(Math.round), d: DIR[m] };
}
// orthogonal elbow between two ports, each leaving its side with a straight jetty (like an elbowed connector)
function elbow(s, e) {
  const a = [s.p[0] + s.d[0] * J, s.p[1] + s.d[1] * J], b = [e.p[0] + e.d[0] * J, e.p[1] + e.d[1] * J];
  const hs = s.d[1] === 0, he = e.d[1] === 0;
  let mid;
  if (hs && he) {
    const facing = s.d[0] !== e.d[0] && Math.sign(b[0] - a[0]) === s.d[0];
    const mx = facing ? (a[0] + b[0]) / 2 : (s.d[0] > 0 ? Math.max(a[0], b[0]) : Math.min(a[0], b[0]));
    mid = [[mx, a[1]], [mx, b[1]]];
  } else if (!hs && !he) {
    const facing = s.d[1] !== e.d[1] && Math.sign(b[1] - a[1]) === s.d[1];
    const my = facing ? (a[1] + b[1]) / 2 : (s.d[1] > 0 ? Math.max(a[1], b[1]) : Math.min(a[1], b[1]));
    mid = [[a[0], my], [b[0], my]];
  } else if (hs) {   // horizontal out, vertical in: one corner if it lies ahead of both jetties
    const ok = Math.sign(b[0] - a[0]) !== -s.d[0] && Math.sign(a[1] - b[1]) !== -e.d[1];
    mid = ok ? [[b[0], a[1]]] : [[a[0], b[1]]];
  } else {
    const ok = Math.sign(b[1] - a[1]) !== -s.d[1] && Math.sign(a[0] - b[0]) !== -e.d[0];
    mid = ok ? [[a[0], b[1]]] : [[b[0], a[1]]];
  }
  const pts = [s.p, a, ...mid, b, e.p].map(p => p.map(Math.round));
  return pts.filter((p, i) => i === 0 || p[0] !== pts[i - 1][0] || p[1] !== pts[i - 1][1])
    .filter((p, i, arr) => i === 0 || i === arr.length - 1 || !((arr[i - 1][0] === p[0] && p[0] === arr[i + 1][0]) || (arr[i - 1][1] === p[1] && p[1] === arr[i + 1][1])));
}

const made = [], fixed = [], skipped = [];
for (const c of targets) {
  const A = await endBox(c.connectorStart), B = await endBox(c.connectorEnd);
  if (!A || !B) { skipped.push(c.id); continue; }
  const ca = [A.x + A.width / 2, A.y + A.height / 2], cb = [B.x + B.width / 2, B.y + B.height / 2];
  const s = c.connectorStart.endpointNodeId ? port(A, c.connectorStart.magnet, cb) : { p: [Math.round(A.x), Math.round(A.y)], d: [Math.sign(cb[0] - A.x) || 1, 0] };
  const e = c.connectorEnd.endpointNodeId ? port(B, c.connectorEnd.magnet, ca) : { p: [Math.round(B.x), Math.round(B.y)], d: [Math.sign(ca[0] - B.x) || -1, 0] };
  const pts = elbow(s, e);
  const minX = Math.min(...pts.map(p => p[0])), minY = Math.min(...pts.map(p => p[1]));
  const v = figma.createVector(); figma.currentPage.appendChild(v);
  const capS = c.connectorStartStrokeCap, capE = c.connectorEndStrokeCap;
  await v.setVectorNetworkAsync({
    vertices: pts.map(([x, y], i) => ({ x: x - minX, y: y - minY,
      ...(i === 0 && capS !== 'NONE' ? { strokeCap: capS } : {}), ...(i === pts.length - 1 && capE !== 'NONE' ? { strokeCap: capE } : {}) })),
    segments: pts.slice(1).map((_, i) => ({ start: i, end: i + 1 })),
  });
  v.x = minX; v.y = minY; v.fills = [];
  v.strokes = JSON.parse(JSON.stringify(c.strokes));   // keeps boundVariables on the paints
  v.strokeWeight = c.strokeWeight; v.strokeJoin = 'ROUND';
  if (c.dashPattern && c.dashPattern.length) v.dashPattern = c.dashPattern;
  v.name = `${c.name} · redrawn ${c.id}`;
  made.push(v);
  const label = c.text && c.text.characters.trim();
  if (label) {   // label centered on the longest run, same font and fill as the connector's own label
    let best = -1, at = pts[0];
    for (let i = 1; i < pts.length; i++) { const L = Math.abs(pts[i][0] - pts[i - 1][0]) + Math.abs(pts[i][1] - pts[i - 1][1]); if (L > best) { best = L; at = [(pts[i][0] + pts[i - 1][0]) / 2, (pts[i][1] + pts[i - 1][1]) / 2]; } }
    const t = figma.createText();
    const font = c.text.fontName === figma.mixed ? c.text.getRangeFontName(0, 1) : c.text.fontName;
    await figma.loadFontAsync(font); t.fontName = font;
    t.fontSize = c.text.fontSize === figma.mixed ? 16 : c.text.fontSize;
    t.characters = label; t.fills = JSON.parse(JSON.stringify(c.text.fills));
    figma.currentPage.appendChild(t); t.x = at[0] - t.width / 2; t.y = at[1] - t.height / 2 - (pts.some((p, i) => i && p[1] === pts[i - 1][1] && Math.abs(p[1] - at[1]) < 1) ? t.height / 2 + 4 : 0);
    t.name = `${c.name} · label ${c.id}`;
    made.push(t);
  }
  c.visible = false;   // keep the original for undo
  fixed.push(c.id);
}
return { stale: targets.length, fixed, skipped, createdNodeIds: made.map(n => n.id) };
