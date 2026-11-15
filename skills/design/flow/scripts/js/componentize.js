// Rendered by figma_js.py (params injected as P); run via run_script / use_figma. Idempotent per component name.
// Turns a repeated UI element into a component with SIMPLE controls, so a state changes with one switch:
//   variant  `State`  = one variant per sample (e.g. Default / Active / Disabled), copies that differ only in color
//   text     `Label`, `Value`, `Hint`, … (P.text_names, in reading order) bound to the element's texts
//   boolean  `Icon`   shows/hides the element's icon (first child that holds vectors), when it has one
// Samples are cloned (the originals stay put; swap.js replaces them with instances afterwards). Colors keep
// whatever variables the samples were bound to (tokenize first), so the component is on the design system.
// P: page, section ("Components"), name ("Sidebar/Menu Item"), samples [{id, state}], text_names? ["Label", …]
const P = __PARAMS__;
const page = await figma.getNodeByIdAsync(P.page);
await figma.setCurrentPageAsync(page);
let sec = page.children.find(n => n.type === 'SECTION' && n.name === (P.section || 'Components'));
if (!sec) {
  sec = figma.createSection(); sec.name = P.section || 'Components';
  const others = page.children.filter(n => n !== sec);
  // Read Top, Work Down: a title band (an instance whose only text is the section name, e.g. a titleInfo
  // "Components") owns the area below it until the next band; put the section there, right of what's already in it
  const isTitle = n => n.type === 'INSTANCE' && n.width >= 2000 && n.findAll(d => d.type === 'TEXT').length === 1;
  const titles = others.filter(isTitle).sort((a, b) => a.y - b.y);
  const t = titles.find(n => n.findOne(d => d.type === 'TEXT').characters.trim().toLowerCase() === sec.name.toLowerCase());
  if (t) {
    const bottom = (titles.find(n => n.y > t.y) || { y: Infinity }).y;
    const inBand = others.filter(n => n !== t && n.y >= t.y + t.height && n.y < bottom && n.x < t.x + t.width);
    sec.x = inBand.length ? Math.max(...inBand.map(n => n.x + n.width)) + 240 : t.x;
    sec.y = t.y + t.height + 240;
  } else {   // no band for it: say so in the result, park it right of the page content
    sec.x = Math.max(...others.map(n => n.x + n.width)) + 400; sec.y = Math.min(...others.map(n => n.y));
  }
  sec.setPluginData('band', t ? t.id : '');
}
// design system first: if the component already exists anywhere on the page, extend it with the missing variants
// (same property names) instead of making a second one
const existing = page.findOne(n => (n.type === 'COMPONENT_SET' || n.type === 'COMPONENT') && n.name === P.name);
if (existing) {
  if (existing.type !== 'COMPONENT_SET') {
    // a single component: keep it as State=default and add the samples beside it as a variant set
    // (its instances stay linked; combineAsVariants keeps the node)
    if (existing.parent.type === 'COMPONENT_SET' || !P.samples.length) return { exists: true, id: existing.id, extended: [] };
    const parent = existing.parent, x = existing.x, y = existing.y;
    const comps = [existing];
    existing.name = 'State=default';
    for (const smp of P.samples) {
      if ((smp.state || 'default').toLowerCase() === 'default') continue;
      const src = await figma.getNodeByIdAsync(smp.id); if (!src) continue;
      const c = figma.createComponentFromNode(src.clone()); parent.appendChild(c); c.name = `State=${smp.state}`; comps.push(c);
    }
    const set = figma.combineAsVariants(comps, parent);
    set.name = P.name; set.x = x; set.y = y;
    let cx = 24; for (const v of set.children) { v.x = cx; v.y = 24; cx += v.width + 24; }
    set.resizeWithoutConstraints(cx, Math.max(...set.children.map(v => v.height)) + 48);
    return { exists: true, id: set.id, extended: comps.slice(1).map(c => c.name) };
  }
  const axis = (existing.children[0]?.name.split('=')[0] || 'State').trim();   // keep the set's own axis name
  const have = new Set(existing.children.map(v => v.name.split('=').slice(1).join('=').trim().toLowerCase()));
  const added = [];
  const defs = existing.componentPropertyDefinitions;
  for (const smp of P.samples) {
    const val = smp.state || 'Default', vname = `${axis}=${val}`;
    if (have.has(val.toLowerCase())) continue;
    const src = await figma.getNodeByIdAsync(smp.id); if (!src) continue;
    const c = figma.createComponentFromNode(src.clone()); existing.appendChild(c); c.name = vname;
    const ts = c.findAll(d => d.type === 'TEXT');
    for (const t of ts) { const f = t.fontName === figma.mixed ? t.getRangeFontName(0, 1) : t.fontName; await figma.loadFontAsync(f); }
    const textKeys = Object.keys(defs).filter(k => defs[k].type === 'TEXT');
    textKeys.forEach((k, i) => { if (ts[i]) ts[i].componentPropertyReferences = { characters: k }; });
    added.push(vname);
  }
  let x = 24; for (const v of existing.children) { v.x = x; v.y = 24; x += v.width + 24; }
  existing.resizeWithoutConstraints(x, Math.max(...existing.children.map(v => v.height)) + 48);
  return { exists: true, id: existing.id, extended: added };
}

const texts = n => n.findAll(d => d.type === 'TEXT');
const iconOf = n => n.children?.find(c => c.type === 'VECTOR' || (('findAll' in c) && c.findAll(d => d.type === 'VECTOR').length && !texts(c).length));
const comps = [];
for (const smp of P.samples) {
  const src = await figma.getNodeByIdAsync(smp.id);
  if (!src) return { error: 'sample not found ' + smp.id };
  const c = figma.createComponentFromNode(src.clone());
  sec.appendChild(c);
  c.name = P.samples.length > 1 ? `State=${smp.state || 'Default'}` : P.name;
  comps.push(c);
}
const owner = comps.length > 1 ? figma.combineAsVariants(comps, sec) : comps[0];
if (comps.length > 1) {
  owner.name = P.name;
  let x = 24; for (const v of owner.children) { v.x = x; v.y = 24; x += v.width + 24; }
  owner.resizeWithoutConstraints(x, Math.max(...owner.children.map(v => v.height)) + 48);
}
// text + boolean properties live on the set and are bound in every variant, in reading order
const names = P.text_names || ['Label', 'Value', 'Hint', 'Meta', 'Note'];
const first = comps[0], nText = Math.min(texts(first).length, names.length);
const fonts = new Set();
for (const v of comps) for (const t of texts(v)) { const f = t.fontName === figma.mixed ? t.getRangeFontName(0, 1) : t.fontName; const k = JSON.stringify(f); if (!fonts.has(k)) { fonts.add(k); await figma.loadFontAsync(f); } }
const props = {};
for (let i = 0; i < nText; i++) {
  const key = owner.addComponentProperty(names[i], 'TEXT', texts(first)[i].characters);
  props[names[i]] = key;
  for (const v of comps) { const t = texts(v)[i]; if (t) t.componentPropertyReferences = { ...(t.componentPropertyReferences || {}), characters: key }; }
}
if (iconOf(first)) {
  const key = owner.addComponentProperty('Icon', 'BOOLEAN', true);
  props.Icon = key;
  for (const v of comps) { const ic = iconOf(v); if (ic) ic.componentPropertyReferences = { ...(ic.componentPropertyReferences || {}), visible: key }; }
}
if (P.description) owner.description = P.description;
const maxX = Math.max(...sec.children.map(n => n.x + n.width)), maxY = Math.max(...sec.children.map(n => n.y + n.height));
if (owner.y + owner.height + 80 > sec.height || owner.x + owner.width + 80 > sec.width) sec.resizeWithoutConstraints(Math.max(sec.width, maxX + 80), Math.max(sec.height, maxY + 80));
// stack new components down the section, top to bottom
const others = sec.children.filter(n => n !== owner);
owner.x = 80; owner.y = others.length ? Math.max(...others.map(n => n.y + n.height)) + 120 : 80;
sec.resizeWithoutConstraints(Math.max(sec.width, owner.x + owner.width + 80), Math.max(sec.height, owner.y + owner.height + 80));
return { id: owner.id, type: owner.type, variants: comps.map(c => c.name), props: Object.keys(props), band: sec.getPluginData('band') || 'none: add a title band named like the section' };
