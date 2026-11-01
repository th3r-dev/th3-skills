// Rendered by figma_js.py (params injected as P); run via run_script / use_figma. Read-only.
// Finds the layers that correspond to code components (by layer name: captures keep DOM-derived names such as
// "Button", "FormControl", "Badge"), groups them by structure (layer types + size), and splits every group by fill
// token. Each group is one Figma component; each fill inside it is one variant (e.g. Variant=primary / success).
// P: page, names {Component: "regex on layer name"}, min (copies needed to count as a duplicate, default 3)
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const vars = Object.fromEntries((await figma.variables.getLocalVariablesAsync('COLOR')).map(v => [v.id, v.name]));
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
const paintName = ps => {
  const f = Array.isArray(ps) ? ps.find(p => p.visible !== false && p.type === 'SOLID' && (p.opacity ?? 1) > 0) : null;
  if (!f) return 'none';
  return f.boundVariables?.color ? (vars[f.boundVariables.color.id] || 'var') : hex(f.color);
};
const norm = t => (t === 'INSTANCE' || t === 'COMPONENT') ? 'FRAME' : t;
const shape = n => [n, ...n.findAll(() => true)].map(d => norm(d.type)).join(',');
// icons differ only in path data: same color + different icon must be a different variant (swap matches geometry)
const geo = n => n.findAll(d => d.type === 'VECTOR').map(v => (v.vectorPaths || []).map(p => p.data.length).join(';')).join('/');
const screens = figma.currentPage.children.filter(n => n.type === 'FRAME' && n.width >= 1000 && n.height >= 600);
const out = {};
for (const [comp, re] of Object.entries(P.names)) {
  const rx = new RegExp(re);
  const groups = {};
  for (const s of screens) {
    for (const n of s.findAll(d => (d.type === 'FRAME' || d.type === 'INSTANCE') && rx.test(d.name))) {
      let inInst = false; for (let p = n.parent; p && p !== s; p = p.parent) if (p.type === 'INSTANCE') { inInst = true; break; }
      if (inInst || n.type === 'INSTANCE') continue;   // already a component instance
      const key = `${shape(n)}|${Math.round(n.height / 4) * 4}`;
      const g = groups[key] || (groups[key] = { count: 0, h: Math.round(n.height), w: Math.round(n.width), screens: new Set(), fills: {} });
      g.count++; g.screens.add(s.id);
      const f = `${paintName(n.fills)}~${paintName(n.strokes)}~${geo(n)}`;
      const fe = g.fills[f] || (g.fills[f] = { count: 0, sample: n.id, text: (n.findOne(t => t.type === 'TEXT')?.characters || '').slice(0, 20) });
      fe.count++;
    }
  }
  out[comp] = Object.values(groups).filter(g => g.count >= (P.min ?? 3)).sort((a, b) => b.count - a.count).slice(0, 4)
    .map(g => ({ count: g.count, screens: g.screens.size, w: g.w, h: g.h,
      fills: Object.entries(g.fills).sort((a, b) => b[1].count - a[1].count).slice(0, P.max_variants ?? 12).map(([k, v]) => ({ fill: k, ...v })) }));
}
return out;
