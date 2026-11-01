// Rendered by figma_js.py (params injected as P); run via run_script / use_figma. Read-only.
// Deterministic extraction of one page for design_graph.py: screens, labels, components, tokens, flows,
// and repeated-structure signatures (componentization candidates). No LLM, no guessing.
const P = __PARAMS__;
const page = await figma.getNodeByIdAsync(P.page);
await figma.setCurrentPageAsync(page);
const MIN_SCREEN_W = P.min_screen_w ?? 1000;
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
const fillKey = n => {
  const f = ('fills' in n && Array.isArray(n.fills)) ? n.fills.find(p => p.visible !== false) : null;
  if (!f) return 'none';
  if (f.type !== 'SOLID') return f.type;
  return f.boundVariables?.color?.id || hex(f.color);
};
const norm = t => (t === 'INSTANCE' || t === 'COMPONENT') ? 'FRAME' : t;
const geo = n => (n.findAll ? n.findAll(d => d.type === 'VECTOR') : []).map(v => (v.vectorPaths || []).map(p => p.data.length).join(';')).join('/');
const sig = n => [[n, ...(n.findAll ? n.findAll(() => true) : [])].map(d => norm(d.type)).join(','), Math.round(n.width / 4) * 4, Math.round(n.height / 4) * 4, fillKey(n), geo(n)].join('|');

const out = { page: { id: page.id, name: page.name }, screens: [], labels: [], components: [], connectors: [], dupes: {}, flows: [] };
const kids = page.children;

for (const n of kids) {
  if (n.type === 'CONNECTOR') {
    out.connectors.push({ id: n.id, from: n.connectorEnd?.endpointNodeId, to: n.connectorStart?.endpointNodeId, label: n.text?.characters || '' });
    continue;
  }
  if ((n.type === 'COMPONENT' || n.type === 'COMPONENT_SET')) out.components.push({ id: n.id, name: n.name, type: n.type, variants: n.type === 'COMPONENT_SET' ? n.children.map(c => ({ id: c.id, name: c.name })) : [] });
  if (n.type === 'SECTION') for (const c of n.findAll(d => d.type === 'COMPONENT_SET' || (d.type === 'COMPONENT' && d.parent.type !== 'COMPONENT_SET')))
    out.components.push({ id: c.id, name: c.name, type: c.type, section: n.name, variants: c.type === 'COMPONENT_SET' ? c.children.map(v => ({ id: v.id, name: v.name })) : [] });
  if (n.name.startsWith('Flow · ')) { out.flows.push({ id: n.id, name: n.name }); continue; }
  if (n.width < MIN_SCREEN_W && n.name.includes('▸')) { out.labels.push({ id: n.id, name: n.name, x: Math.round(n.x), y: Math.round(n.y) }); continue; }
  if (!(n.type === 'FRAME' || n.type === 'INSTANCE') || n.width < MIN_SCREEN_W || n.height < 400) continue;

  const s = { id: n.id, name: n.name, type: n.type, x: Math.round(n.x), y: Math.round(n.y), w: Math.round(n.width), h: Math.round(n.height),
    placeholder: n.type === 'INSTANCE' ? (n.componentProperties?.status?.value || 'instance') : null,
    instances: {}, variables: {}, textStyles: {}, rawPaints: 0, rawTexts: 0, layers: 0 };
  if (n.type === 'FRAME') {
    const all = n.findAll(() => true);
    s.layers = all.length;
    for (const d of all) {
      if (d.type === 'INSTANCE') { const m = await d.getMainComponentAsync(); if (m) { const key = m.parent?.type === 'COMPONENT_SET' ? m.parent.id : m.id; s.instances[key] = (s.instances[key] || 0) + 1; } }
      for (const k of ['fills', 'strokes']) if (k in d && Array.isArray(d[k])) for (const p of d[k]) if (p.type === 'SOLID' && p.opacity !== 0) {
        const id = p.boundVariables?.color?.id; if (id) s.variables[id] = (s.variables[id] || 0) + 1; else s.rawPaints++;
      }
      if (d.type === 'TEXT') { const ts = d.textStyleId; if (typeof ts === 'string' && ts) s.textStyles[ts] = (s.textStyles[ts] || 0) + 1; else if (ts !== figma.mixed) s.rawTexts++; }
      // repeated structures: small/medium frames that are not already instances
      if (d.type === 'FRAME' && d.children.length >= 2 && d.width <= (P.max_dupe_w ?? 700) && d.height <= (P.max_dupe_h ?? 400)) {
        let inInst = false; for (let p = d.parent; p && p !== n; p = p.parent) if (p.type === 'INSTANCE') { inInst = true; break; }
        if (inInst) continue;
        const k = sig(d);
        const e = out.dupes[k] || (out.dupes[k] = { count: 0, w: Math.round(d.width), h: Math.round(d.height), name: d.name, samples: [], screens: {} });
        e.count++; e.screens[n.id] = (e.screens[n.id] || 0) + 1; if (e.samples.length < 5) e.samples.push(d.id);
      }
    }
  }
  out.screens.push(s);
}
// keep only real repeats
for (const [k, v] of Object.entries(out.dupes)) if (v.count < (P.min_repeat ?? 3)) delete out.dupes[k];

const cols = await figma.variables.getLocalVariableCollectionsAsync();
out.variables = [];
for (const c of cols) for (const id of c.variableIds) { const v = await figma.variables.getVariableByIdAsync(id); out.variables.push({ id, name: v.name, collection: c.name, type: v.resolvedType }); }
out.textStyles = (await figma.getLocalTextStylesAsync()).map(t => ({ id: t.id, name: t.name, font: t.fontName.family + ' ' + t.fontName.style, size: t.fontSize }));
return out;
