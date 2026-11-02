// Rendered by figma_js.py (params injected as P); run the output as the `code` of use_figma / run_script.
// Turns absolutely positioned frames under P.root into auto layout, deepest first.
// A frame converts only when its children form one clean row or one clean column (no overlaps), the gaps
// between them are equal (auto layout has one itemSpacing) and they share one cross-axis alignment (start,
// center or end). Padding = distance from the frame edge. Anything else stays absolute and is listed: a column
// of header / content / footer with gaps 0 and 132 has no auto-layout equivalent, and forcing one moves layers.
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

// An imported svg is a frame of vector paths positioned by their geometry; stacking them as a row/column
// scrambles the icon (a rotated chevron becomes a dot). Icon art stays absolute.
const ART = new Set(['VECTOR', 'BOOLEAN_OPERATION', 'ELLIPSE', 'LINE', 'STAR', 'POLYGON', 'RECTANGLE', 'GROUP']);
const isArt = f => f.children.every(k => ART.has(k.type));
const frames = [root, ...root.findAllWithCriteria({ types: ['FRAME'] })]
  .filter(f => f.type === 'FRAME' && f.layoutMode === 'NONE' && f.children.length && !isArt(f));
const depth = n => { let d = 0; for (let p = n.parent; p; p = p.parent) d++; return d; };
frames.sort((a, b) => depth(b) - depth(a));

const out = { converted: [], skipped: [] };
for (const f of frames) {
  const kids = f.children.filter(k => k.visible);
  const [dir, order] = axisOf(kids);
  if (!dir) { out.skipped.push(f.id); continue; }
  const H = dir === 'HORIZONTAL';
  const gaps = order.slice(1).map((k, i) => H ? k.x - (order[i].x + order[i].width) : k.y - (order[i].y + order[i].height));
  if (gaps.length && Math.max(...gaps) - Math.min(...gaps) > tol) { out.skipped.push(f.id); continue; }
  const same = vals => Math.max(...vals) - Math.min(...vals) <= tol;
  const cs = k => H ? k.y : k.x, cl = k => H ? k.height : k.width, cross = H ? f.height : f.width;
  // a lone child centred in its box (a badge label, an icon in a button) keeps its centre, not its left edge
  // (never for a child larger than its box: that is a scroll container or a 0px wrapper, keep it at the start)
  const centred = (start, len, total) => len <= total && Math.abs(start - (total - start - len)) <= tol;
  const crossAlign = () => {
    if (kids.length === 1) return centred(cs(kids[0]), cl(kids[0]), cross) ? 'CENTER' : 'MIN';
    if (same(kids.map(cs))) return 'MIN';
    if (same(kids.map(k => cs(k) + cl(k) / 2))) return 'CENTER';
    if (same(kids.map(k => cs(k) + cl(k)))) return 'MAX';
    return null;
  };
  const align = crossAlign();
  if (!align) { out.skipped.push(f.id); continue; }
  const first = order[0], minCross = Math.min(...kids.map(k => H ? k.y : k.x));
  const maxEnd = Math.max(...kids.map(k => H ? k.x + k.width : k.y + k.height));
  const maxCrossEnd = Math.max(...kids.map(k => H ? k.y + k.height : k.x + k.width));
  const pad = H
    ? { l: first.x, r: f.width - maxEnd, t: minCross, b: f.height - maxCrossEnd }
    : { t: first.y, b: f.height - maxEnd, l: minCross, r: f.width - maxCrossEnd };
  // measured before layoutMode is set: switching it on moves the children
  const ps = k => H ? k.x : k.y, pl = k => H ? k.width : k.height, len = H ? f.width : f.height;
  const mainCentre = kids.length === 1 && centred(ps(kids[0]), pl(kids[0]), len);
  const mainPad = kids.length === 1 ? Math.max(0, Math.round(ps(kids[0]))) : 0;
  const crossMid = cs(kids[0]) + cl(kids[0]) / 2;
  const w = f.width, h = f.height;
  order.forEach((k, i) => f.insertChild(i, k));  // reading order = layout order
  f.layoutMode = dir;
  f.counterAxisAlignItems = align;
  f.itemSpacing = Math.max(0, Math.round(median(gaps)));
  f.paddingLeft = Math.max(0, Math.round(pad.l)); f.paddingRight = Math.max(0, Math.round(pad.r));
  f.paddingTop = Math.max(0, Math.round(pad.t)); f.paddingBottom = Math.max(0, Math.round(pad.b));
  if (mainCentre) {
    f.primaryAxisAlignItems = 'CENTER';
    if (H) { f.paddingLeft = f.paddingRight = mainPad; } else { f.paddingTop = f.paddingBottom = mainPad; }
  }
  // a one-line text that is centred / right-aligned by the layout may grow: Figma's metrics run wider than the
  // browser's, and an instance label longer than the sample ("Waiting" in a badge made from "Draft") must fit
  const mainAlign = mainCentre ? 'CENTER' : 'MIN';
  const hAlign = H ? mainAlign : align;
  if (hAlign !== 'MIN') for (const k of kids) {
    if (k.type !== 'TEXT' || k.textAutoResize === 'WIDTH_AND_HEIGHT' || k.fontSize === figma.mixed) continue;
    const lh = k.lineHeight !== figma.mixed && k.lineHeight.unit === 'PIXELS' ? k.lineHeight.value : k.fontSize * 1.2;
    if (k.height < lh * 1.5 && !k.characters.includes('\n')) {
      const fonts = k.fontName === figma.mixed ? k.getStyledTextSegments(['fontName']).map(s => s.fontName) : [k.fontName];
      await Promise.all(fonts.map(fn => figma.loadFontAsync(fn)));
      k.textAutoResize = 'WIDTH_AND_HEIGHT';
    }
  }
  if (align === 'CENTER') {  // keep the shared centre line m: auto layout centres at start + (cross - start - end) / 2
    const m = crossMid;
    const a = Math.max(0, Math.round(2 * m - cross)), b = Math.max(0, Math.round(cross - 2 * m));
    if (H) { f.paddingTop = a; f.paddingBottom = b; } else { f.paddingLeft = a; f.paddingRight = b; }
  }
  f.primaryAxisSizingMode = 'FIXED'; f.counterAxisSizingMode = 'FIXED';
  f.resize(w, h);  // keep the captured size; designers can switch to hug later
  out.converted.push(f.id);
}
return { mutatedNodeIds: out.converted, converted: out.converted.length, skipped: out.skipped.length, skippedIds: out.skipped.slice(0, 50) };
