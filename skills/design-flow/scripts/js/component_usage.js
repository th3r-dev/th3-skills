// Rendered by figma_js.py (params injected as P); run via run_script / use_figma. Read-only.
// Rule check: a component exists to be used. Counts the instances of every local component (per variant) on the
// design pages and lists the ones nothing uses yet, so they get swapped in (swap.js) or removed, never left idle.
// P: pages? (ids to count instances on; default every page except the one holding the component), section? (only
//    components inside a section with this name), ignore? (regex on component names, e.g. "^\\.|^Flow/")
const P = __PARAMS__;
const ignore = P.ignore ? new RegExp(P.ignore) : null;
const pages = P.pages ? await Promise.all(P.pages.map(id => figma.getNodeByIdAsync(id))) : figma.root.children;
await figma.loadAllPagesAsync();
const owners = [];
for (const pg of figma.root.children) {
  for (const n of pg.findAllWithCriteria({ types: ['COMPONENT_SET', 'COMPONENT'] })) {
    if (n.type === 'COMPONENT' && n.parent.type === 'COMPONENT_SET') continue;
    if (ignore && ignore.test(n.name)) continue;
    if (P.section) { let s = n.parent; while (s && s.type !== 'SECTION') s = s.parent; if (!s || s.name !== P.section) continue; }
    owners.push({ node: n, page: pg.id });
  }
}
const pageIds = new Set(pages.filter(Boolean).map(p => p.id));
const count = {};
for (const pg of figma.root.children) {
  if (!pageIds.has(pg.id)) continue;
  for (const i of pg.findAllWithCriteria({ types: ['INSTANCE'] })) {
    const mc = await i.getMainComponentAsync(); if (!mc) continue;
    count[mc.id] = (count[mc.id] || 0) + 1;
  }
}
const out = { components: [], unused: [], unusedVariants: [] };
for (const { node, page } of owners) {
  const vs = node.type === 'COMPONENT_SET' ? node.children : [node];
  const per = Object.fromEntries(vs.map(v => [v.name, count[v.id] || 0]));
  const total = Object.values(per).reduce((a, b) => a + b, 0);
  out.components.push({ id: node.id, name: node.name, page, total, variants: per,
    variantIds: node.type === 'COMPONENT_SET' ? Object.fromEntries(vs.filter(v => !count[v.id]).map(v => [v.name, v.id])) : {} });
  if (!total) out.unused.push(`${node.name} (${node.id})`);
  else for (const [k, v] of Object.entries(per)) if (!v) out.unusedVariants.push(`${node.name} / ${k}`);
}
out.components.sort((a, b) => a.total - b.total);
return out;
