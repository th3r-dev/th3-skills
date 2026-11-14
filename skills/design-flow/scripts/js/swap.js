// Rendered by figma_js.py (params injected as P); run the output as the `code` of use_figma / run_script (allowRemove).
// Replaces layers under P.roots that structurally match a variant of P.component with instances of it.
// Match = same descendant type sequence, same rounded height, corner radius and first fill (variable id or hex),
// plus an optional name filter. Width, position, sizing and every text are carried over; nothing else is guessed.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const set = await figma.getNodeByIdAsync(P.component);
if (!set) return { error: 'component not found: ' + P.component };
const variants = set.type === 'COMPONENT_SET' ? set.children : [set];
const tol = P.tolerance ?? 1; ``
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
const paintKey = ps => {
  const f = Array.isArray(ps) ? ps.find(p => p.visible !== false) : null;
  if (!f) return 'none';
  if (f.type !== 'SOLID') return f.type;
  return f.boundVariables?.color?.id || hex(f.color) + '@' + (f.opacity ?? 1);
};
// fill + stroke of the root and the colors of its icon vectors: an outline button (stroke only) or a recolored icon
// is a different variant, else blue and orange pager arrows collapse onto whichever variant was listed last
const fillKey = n => [n, ...(n.findAll ? n.findAll(d => d.type === 'VECTOR') : [])]
  .map(d => paintKey(d.fills) + '~' + paintKey(d.strokes)).join('/');
const norm = t => (t === 'INSTANCE' || t === 'COMPONENT') ? 'FRAME' : t;  // a variant root is a COMPONENT, its source a FRAME
const shape = n => [n, ...(n.findAll ? n.findAll(() => true) : [])].map(d => norm(d.type)).join(',');
// icons differ only in path data, so vectors contribute their geometry (else every card would get the first card's icon)
const geo = n => [n, ...(n.findAll ? n.findAll(d => d.type === 'VECTOR') : [])].filter(d => d.type === 'VECTOR')
  .map(v => (v.vectorPaths || []).map(p => p.data.length + ':' + p.data.slice(0, 24)).join(';')).join('/');
const sig = n => [shape(n), Math.round(n.height), typeof n.cornerRadius === 'number' ? Math.round(n.cornerRadius) : 'mix', fillKey(n), geo(n)].join('|');
const texts = n => n.findAllWithCriteria({ types: ['TEXT'] });

const owners = set.type === 'COMPONENT_SET' ? set : set;
const labelKey = Object.keys(owners.componentPropertyDefinitions || {}).find(k => k.startsWith('Label'));
const bySig = new Map(variants.map(v => [sig(v), v]));
const nameRe = P.name_match ? new RegExp(P.name_match) : null;

const out = { swapped: 0, byVariant: {}, createdNodeIds: [], errors: [] };
for (const rootId of P.roots) {
  const root = await figma.getNodeByIdAsync(rootId);
  if (!root) { out.errors.push('root missing ' + rootId); continue; }
  const cands = root.findAll(n => (n.type === 'FRAME') && (!nameRe || nameRe.test(n.name)) && bySig.has(sig(n)));
  for (const c of cands) {
    if (c.removed) continue;
    let inInstance = false; for (let p = c.parent; p; p = p.parent) if (p.type === 'INSTANCE') { inInstance = true; break; }
    if (inInstance) continue;
    const v = bySig.get(sig(c));
    try {
      const inst = v.createInstance();
      const parent = c.parent, idx = parent.children.indexOf(c);
      parent.insertChild(idx, inst);
      const auto = 'layoutMode' in parent && parent.layoutMode !== 'NONE';
      if (!auto || c.layoutPositioning === 'ABSOLUTE') { inst.x = c.x; inst.y = c.y; }
      if (c.layoutPositioning === 'ABSOLUTE') inst.layoutPositioning = 'ABSOLUTE';
      if (Math.abs(inst.width - c.width) > tol) inst.resize(c.width, inst.height);
      if (auto) { inst.layoutSizingHorizontal = c.layoutSizingHorizontal === 'HUG' ? 'HUG' : c.layoutSizingHorizontal; inst.layoutGrow = c.layoutGrow; }
      const src = texts(c), dst = texts(inst);
      for (let i = 0; i < Math.min(src.length, dst.length); i++) {
        const fonts = dst[i].fontName === figma.mixed ? dst[i].getStyledTextSegments(['fontName']).map(s => s.fontName) : [dst[i].fontName];
        for (const f of fonts) await figma.loadFontAsync(f);
        if (dst[i].characters !== src[i].characters) {
          if (i === 0 && labelKey) inst.setProperties({ [labelKey]: src[i].characters });
          else dst[i].characters = src[i].characters;
        }
        // the text's color is per copy too: a field holding a value is dark, the same field's placeholder is grey
        if (src[i].fills !== figma.mixed && JSON.stringify(src[i].fills) !== JSON.stringify(dst[i].fills)) dst[i].fills = src[i].fills;
      }
      inst.name = c.name;
      c.remove();
      out.swapped++; out.byVariant[v.name] = (out.byVariant[v.name] || 0) + 1;
      out.createdNodeIds.push(inst.id);
    } catch (e) { out.errors.push(c.id + ': ' + e.message); }
  }
}
out.createdNodeIds = out.createdNodeIds.slice(0, 200);
return out;
