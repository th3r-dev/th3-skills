// Rendered by figma_js.py (params injected as P); run the output as the `code` of use_figma / run_script.
// Turns absolutely positioned frames under P.root into auto layout, deepest first.
// A frame converts only when its children form one clean row or one clean column (no overlaps);
// gap = median spacing, padding = distance from the frame edge. Anything else is left as is and listed.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const root = await figma.getNodeByIdAsync(P.root);
const tol = P.tolerance ?? 2;
const median = a => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.floor(s.length / 2)] : 0; };

function axisOf(kids) {
  const byX = [...kids].sort((a, b) => a.x - b.x), byY = [...kids].sort((a, b) => a.y - b.y);
  const row = byX.every((k, i) => i === 0 || k.x >= byX[i - 1].x + byX[i - 1].width - tol);
  const col = byY.every((k, i) => i === 0 || k.y >= byY[i - 1].y + byY[i - 1].height - tol);
  if (row && !col) return ['HORIZONTAL', byX];
  if (col && !row) return ['VERTICAL', byY];
  if (row && col) return kids.length === 1 ? ['VERTICAL', byY] : [null, null];  // diagonal: ambiguous
  return [null, null];
}

const frames = [root, ...root.findAllWithCriteria({ types: ['FRAME'] })]
  .filter(f => f.type === 'FRAME' && f.layoutMode === 'NONE' && f.children.length);
const depth = n => { let d = 0; for (let p = n.parent; p; p = p.parent) d++; return d; };
frames.sort((a, b) => depth(b) - depth(a));

const out = { converted: [], skipped: [] };
for (const f of frames) {
  const kids = f.children.filter(k => k.visible);
  const [dir, order] = axisOf(kids);
  if (!dir) { out.skipped.push(f.id); continue; }
  const H = dir === 'HORIZONTAL';
  const gaps = order.slice(1).map((k, i) => H ? k.x - (order[i].x + order[i].width) : k.y - (order[i].y + order[i].height));
  const first = order[0], minCross = Math.min(...kids.map(k => H ? k.y : k.x));
  const maxEnd = Math.max(...kids.map(k => H ? k.x + k.width : k.y + k.height));
  const maxCrossEnd = Math.max(...kids.map(k => H ? k.y + k.height : k.x + k.width));
  const pad = H
    ? { l: first.x, r: f.width - maxEnd, t: minCross, b: f.height - maxCrossEnd }
    : { t: first.y, b: f.height - maxEnd, l: minCross, r: f.width - maxCrossEnd };
  const w = f.width, h = f.height;
  order.forEach((k, i) => f.insertChild(i, k));  // reading order = layout order
  f.layoutMode = dir;
  f.itemSpacing = Math.max(0, Math.round(median(gaps)));
  f.paddingLeft = Math.max(0, Math.round(pad.l)); f.paddingRight = Math.max(0, Math.round(pad.r));
  f.paddingTop = Math.max(0, Math.round(pad.t)); f.paddingBottom = Math.max(0, Math.round(pad.b));
  f.primaryAxisSizingMode = 'FIXED'; f.counterAxisSizingMode = 'FIXED';
  f.resize(w, h);  // keep the captured size; designers can switch to hug later
  out.converted.push(f.id);
}
return { mutatedNodeIds: out.converted, converted: out.converted.length, skipped: out.skipped.length, skippedIds: out.skipped.slice(0, 50) };
