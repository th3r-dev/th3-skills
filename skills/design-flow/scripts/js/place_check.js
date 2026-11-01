// Rendered by figma_js.py (params injected as P). Placement check (stage 1): screens only. Overlaps between screens (incl. the title strip above each), and screens
// sitting on a section title. Read-only.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const T = P.title_strip ?? 120;
const scr = figma.currentPage.children.filter(n => n.type === 'FRAME' && n.width >= 1000 && n.height >= 600).map(n => ({ id: n.id, name: n.name, x: n.x, y: n.y - T, w: n.width, h: n.height + T }));
const titles = figma.currentPage.children.filter(n => n.type === 'INSTANCE' && n.width >= 2000).map(n => ({ id: n.id, x: n.x, y: n.y, w: n.width, h: n.height }));
const ov = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
const out = { screens: scr.length, overlaps: [], onTitle: [] };
const s = [...scr].sort((a, b) => a.x - b.x);
for (let i = 0; i < s.length; i++) for (let j = i + 1; j < s.length && s[j].x < s[i].x + s[i].w; j++) if (ov(s[i], s[j])) out.overlaps.push([s[i].name.slice(-40), s[j].name.slice(-40)]);
for (const a of scr) for (const t of titles) if (ov(a, t)) out.onTitle.push(a.name.slice(-40));
out.overlapCount = out.overlaps.length; out.overlaps = out.overlaps.slice(0, 8);
return out;
