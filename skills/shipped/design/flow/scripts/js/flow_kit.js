// Rendered by figma_js.py (params injected as P); run via run_script / use_figma. Idempotent.
// Design-mode flow kit as real components (FigJam shape/connector nodes can't be created or cloned in design files):
//   Flow/Node (Type=Process|Alert|Success|End) · Flow/Decision · Flow/Marker · Flow/Element Row
// Every color/text comes from the file's variables and text styles named in P; a missing one blocks the build.
const P = __PARAMS__;
const page = await figma.getNodeByIdAsync(P.page);
await figma.setCurrentPageAsync(page);
const vars = await figma.variables.getLocalVariablesAsync('COLOR');
const styles = await figma.getLocalTextStylesAsync();
const missing = [];
const V = n => { const v = vars.find(x => x.name === n); if (!v) missing.push('variable ' + n); return v; };
const S = n => { const s = styles.find(x => x.name === n); if (!s) missing.push('text style ' + n); return s; };
const T = P.tokens;
const tok = { ink: V(T.ink), line: V(T.line), paper: V(T.paper), alert: V(T.alert), success: V(T.success), accent: V(T.accent), onAccent: V(T.on_accent), muted: V(T.muted) };
const st = { node: S(T.node_text), small: S(T.small_text), marker: S(T.marker_text) };
if (missing.length) return { blocked: missing };
const paint = v => figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', v);

let sec = page.children.find(n => n.type === 'SECTION' && n.name === 'Flow Kit');
if (sec && sec.children.length) return { exists: true, section: sec.id, components: Object.fromEntries(sec.children.map(c => [c.name, c.id])) };
if (!sec) {
  sec = figma.createSection(); sec.name = 'Flow Kit';
  const others = page.children.filter(n => n !== sec);
  sec.x = Math.max(...others.map(n => n.x + n.width)) + 400; sec.y = Math.min(...others.map(n => n.y));
}
const text = async (chars, style, fill) => {
  const t = figma.createText(); await figma.loadFontAsync(style.fontName); await t.setTextStyleIdAsync(style.id);
  t.characters = chars; t.fills = [paint(fill)]; return t;
};
const out = {};

// Flow/Node
const nodeVariant = async (type, fill, stroke, textFill) => {
  const c = figma.createComponent(); c.name = `Type=${type}`;
  c.layoutMode = 'HORIZONTAL'; c.primaryAxisAlignItems = 'CENTER'; c.counterAxisAlignItems = 'CENTER';
  c.paddingLeft = c.paddingRight = 24; c.paddingTop = c.paddingBottom = 20; c.cornerRadius = 16;
  c.resize(336, 122); c.primaryAxisSizingMode = 'FIXED'; c.counterAxisSizingMode = 'FIXED';
  c.fills = [paint(fill)]; c.strokes = [paint(stroke)]; c.strokeWeight = 2;
  const t = await text('Step', st.node, textFill); t.textAlignHorizontal = 'CENTER'; t.textAutoResize = 'HEIGHT';
  c.appendChild(t); t.layoutSizingHorizontal = 'FILL';
  const k = c.addComponentProperty('Label', 'TEXT', 'Step'); t.componentPropertyReferences = { characters: k };
  sec.appendChild(c); return c;
};
const nodes = [await nodeVariant('Process', tok.paper, tok.line, tok.ink), await nodeVariant('Alert', tok.alert, tok.alert, tok.ink),
  await nodeVariant('Success', tok.success, tok.success, tok.onAccent), await nodeVariant('End', tok.ink, tok.ink, tok.onAccent)];
const nodeSet = figma.combineAsVariants(nodes, sec); nodeSet.name = 'Flow/Node';
nodeSet.children.forEach((c, i) => { c.x = 24 + i * 360; c.y = 24; });
nodeSet.resizeWithoutConstraints(24 + nodes.length * 360, 170); nodeSet.x = 80; nodeSet.y = 80;
out['Flow/Node'] = nodeSet.id;

// Flow/Decision: diamond drawn as a vector (rhombus) behind a centered label
const dec = figma.createComponent(); dec.name = 'Flow/Decision'; dec.resize(260, 260); dec.fills = [];
const dia = figma.createVector();
await dia.setVectorNetworkAsync({ vertices: [{ x: 130, y: 0 }, { x: 260, y: 130 }, { x: 130, y: 260 }, { x: 0, y: 130 }],
  segments: [{ start: 0, end: 1 }, { start: 1, end: 2 }, { start: 2, end: 3 }, { start: 3, end: 0 }], regions: [{ windingRule: 'NONZERO', loops: [[0, 1, 2, 3]] }] });
dia.fills = [paint(tok.paper)]; dia.strokes = [paint(tok.line)]; dia.strokeWeight = 2; dia.name = 'Shape';
dec.appendChild(dia); dia.x = 0; dia.y = 0;
const dt = await text('Condition?', st.node, tok.ink); dt.textAlignHorizontal = 'CENTER'; dt.textAlignVertical = 'CENTER';
dt.textAutoResize = 'NONE'; dt.resize(160, 120); dec.appendChild(dt); dt.x = 50; dt.y = 70;
const dk = dec.addComponentProperty('Label', 'TEXT', 'Condition?'); dt.componentPropertyReferences = { characters: dk };
sec.appendChild(dec); dec.x = 80; dec.y = 300; out['Flow/Decision'] = dec.id;

// Flow/Marker: numbered pin placed on the screen over the element
const mk = figma.createComponent(); mk.name = 'Flow/Marker';
mk.layoutMode = 'HORIZONTAL'; mk.primaryAxisAlignItems = 'CENTER'; mk.counterAxisAlignItems = 'CENTER';
mk.resize(40, 40); mk.primaryAxisSizingMode = 'FIXED'; mk.counterAxisSizingMode = 'FIXED'; mk.cornerRadius = 20;
mk.fills = [paint(tok.accent)]; mk.strokes = [paint(tok.paper)]; mk.strokeWeight = 3;
const mt = await text('1', st.marker, tok.onAccent); mk.appendChild(mt);
const mkk = mk.addComponentProperty('Number', 'TEXT', '1'); mt.componentPropertyReferences = { characters: mkk };
sec.appendChild(mk); mk.x = 400; mk.y = 300; out['Flow/Marker'] = mk.id;

// Flow/Element Row: marker + label + kind, one per interactive element in the side panel
const row = figma.createComponent(); row.name = 'Flow/Element Row';
row.layoutMode = 'HORIZONTAL'; row.counterAxisAlignItems = 'CENTER'; row.itemSpacing = 16;
row.paddingLeft = row.paddingRight = 20; row.paddingTop = row.paddingBottom = 14; row.cornerRadius = 12;
row.fills = [paint(tok.paper)]; row.strokes = [paint(tok.line)]; row.strokeWeight = 1;
const ri = mk.createInstance(); row.appendChild(ri);
const rl = await text('Element', st.node, tok.ink); row.appendChild(rl);
const rk = await text('button', st.small, tok.muted); row.appendChild(rk);
row.resize(560, 68); row.primaryAxisSizingMode = 'FIXED'; row.counterAxisSizingMode = 'AUTO'; rl.layoutGrow = 1;
const k1 = row.addComponentProperty('Label', 'TEXT', 'Element'); rl.componentPropertyReferences = { characters: k1 };
const k2 = row.addComponentProperty('Kind', 'TEXT', 'button'); rk.componentPropertyReferences = { characters: k2 };
sec.appendChild(row); row.x = 520; row.y = 300; out['Flow/Element Row'] = row.id;

sec.resizeWithoutConstraints(Math.max(...sec.children.map(n => n.x + n.width)) + 80, Math.max(...sec.children.map(n => n.y + n.height)) + 80);
return { section: sec.id, components: out };
