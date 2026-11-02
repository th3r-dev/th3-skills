// Rendered by figma_js.py (params injected as P); run via run_script / use_figma.
// Builds a target "state" screen for UI → flow → UI:
//   mode "overlay": copy of P.base + scrim + the imported element P.overlay (e.g. a dialog) centered on it
//   mode "page":    the imported page P.overlay itself, optionally with the sidebar of P.sidebar_from moved in
// Position: P.x/P.y, or P.near {screen, dx, dy?, margin?} = first free slot right of that screen, sliding down
//                   (imports lose gradient/image shells; the accurate screen's sidebar replaces the blank one)
// P.max_height crops any state to that height (e.g. 1080: one viewport), top kept
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const ov = await figma.getNodeByIdAsync(P.overlay);
if (!ov) return { error: 'overlay/import not found ' + P.overlay };
const vars = await figma.variables.getLocalVariablesAsync('COLOR');
const paintOf = (name, opacity = 1) => { const v = vars.find(x => x.name === name); if (!v) return null; return figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 }, opacity }, 'color', v); };
const findSidebar = root => root.findOne(n => n.type === 'FRAME' && n.width >= 240 && n.width <= 300 && n.height >= 700 && Math.abs(n.absoluteBoundingBox.x - root.absoluteBoundingBox.x) < 30);

let screen;
if (P.mode === 'overlay') {
  const base = await figma.getNodeByIdAsync(P.base);
  screen = base.clone(); figma.currentPage.appendChild(screen);
  const abs = n => { if ('layoutMode' in screen && screen.layoutMode !== 'NONE') n.layoutPositioning = 'ABSOLUTE'; };
  const scrim = figma.createRectangle(); screen.appendChild(scrim); abs(scrim);
  scrim.resize(screen.width, screen.height); scrim.x = 0; scrim.y = 0; scrim.name = 'Scrim';
  const sp = paintOf(P.scrim_var || 'Color/Theme/Black'); if (sp) scrim.fills = [sp];
  scrim.opacity = P.scrim_opacity ?? 0.45;  // layer opacity: a bound paint drops its own opacity
  // html-figma keeps page coordinates, so a captured dialog sits offset inside its wrapper (and gets clipped):
  // shift the content to 0,0 and shrink the wrapper to it
  if ('children' in ov && ov.children.length && ov.layoutMode && ov.layoutMode !== 'NONE') {
    // after `autolayout` that offset is padding, and moving children does nothing: drop the padding, hug the content
    ov.paddingLeft = ov.paddingRight = ov.paddingTop = ov.paddingBottom = 0;
    ov.primaryAxisSizingMode = 'AUTO'; ov.counterAxisSizingMode = 'AUTO';
  } else if ('children' in ov && ov.children.length) {
    const bs = ov.children.map(c => c.absoluteBoundingBox), ob = ov.absoluteBoundingBox;
    const minX = Math.min(...bs.map(b => b.x)) - ob.x, minY = Math.min(...bs.map(b => b.y)) - ob.y;
    const maxX = Math.max(...bs.map(b => b.x + b.width)) - ob.x, maxY = Math.max(...bs.map(b => b.y + b.height)) - ob.y;
    for (const c of ov.children) { c.x -= minX; c.y -= minY; }
    ov.resizeWithoutConstraints(Math.max(1, maxX - minX), Math.max(1, maxY - minY));
  }
  screen.appendChild(ov); abs(ov);
  ov.x = Math.round((screen.width - ov.width) / 2); ov.y = P.overlay_y ?? 80;
  ov.name = P.overlay_name || 'Dialog';
} else {
  screen = ov;
  if (P.sidebar_from) {
    const from = await figma.getNodeByIdAsync(P.sidebar_from);
    const good = from && findSidebar(from), blank = findSidebar(screen);
    if (good) {
      const c = good.clone(); screen.appendChild(c);
      if ('layoutMode' in screen && screen.layoutMode !== 'NONE') c.layoutPositioning = 'ABSOLUTE';
      c.x = 0; c.y = blank ? blank.absoluteBoundingBox.y - screen.absoluteBoundingBox.y : 0;
      if (blank) blank.visible = false;
      c.name = 'Sidebar';
    }
  }
}
screen.name = P.name;
// keep the row tidy: a page state taller than its source (e.g. a long result table) is cropped to the source's
// height so it never runs into the next row; the top of the page, where the action happened, stays visible
if (P.clip_to && P.mode !== 'overlay') {
  const ref = await figma.getNodeByIdAsync(P.clip_to);
  if (ref && screen.height > ref.height + 1) { screen.clipsContent = true; screen.resizeWithoutConstraints(screen.width, Math.max(1080, ref.height)); }
}
// any state (overlay included) can be cropped to one viewport, so a band of states under a tall source stays one row
if (P.max_height && screen.height > P.max_height) {
  if (screen.layoutMode === 'VERTICAL') { screen.primaryAxisSizingMode = 'FIXED'; screen.primaryAxisAlignItems = 'MIN'; }  // keep the top
  if (screen.layoutMode === 'HORIZONTAL') screen.counterAxisSizingMode = 'FIXED';
  screen.clipsContent = true; screen.resizeWithoutConstraints(screen.width, P.max_height);
}
if (P.near) {
  // auto place: right of the source screen past its flow lane, first free slot going down (nothing overlaps)
  const src = await figma.getNodeByIdAsync(P.near.screen);
  const gapM = P.near.margin ?? 120, x = Math.round(src.x + src.width + (P.near.dx ?? 1600));
  const others = figma.currentPage.children.filter(n => n !== screen && n.type !== 'CONNECTOR' && n.visible)
    .map(n => n.absoluteBoundingBox).filter(Boolean);
  const hit = y => others.some(b => !(x >= b.x + b.width + gapM || x + screen.width + gapM <= b.x || y >= b.y + b.height + gapM || y + screen.height + gapM <= b.y));
  let y = Math.round(src.y + (P.near.dy ?? 0));
  for (let k = 0; k < 2000 && hit(y); k++) y += 40;
  screen.x = x; screen.y = y;
} else { screen.x = P.x; screen.y = P.y; }
return { screen: screen.id, w: Math.round(screen.width), h: Math.round(screen.height) };
