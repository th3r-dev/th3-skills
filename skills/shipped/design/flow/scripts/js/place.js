// Rendered by figma_js.py (params injected as P); run the output as the `code` of a use_figma call.
// Puts a new screen (P.capture) where P.target is:
//   - target is a placeholder instance (main component name matches P.placeholder_match) -> replace it
//   - target is a real design -> versioning: new takes its place, a version card goes above it,
//     the old one moves right by P.gap at opacity 0.5 and gets "(old version)" in its name. Nothing is deleted.
// Card colors/text come only from the file's variables and text styles; a missing one is reported, not invented.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const cap = await figma.getNodeByIdAsync(P.capture);
const target = await figma.getNodeByIdAsync(P.target);
if (!cap || !target) return { error: 'capture or target not found', capture: !!cap, target: !!target };

const gap = P.gap ?? 200;
const main = target.type === 'INSTANCE' ? await target.getMainComponentAsync() : null;
const placeholderName = main ? (main.parent?.type === 'COMPONENT_SET' ? main.parent.name : main.name) : '';
const isPlaceholder = !!main && new RegExp(P.placeholder_match || 'placeholder', 'i').test(placeholderName);

const at = { x: target.x, y: target.y };
cap.x = at.x; cap.y = at.y;
cap.name = P.name || target.name;

if (isPlaceholder) {
  target.remove();
  return { mode: 'replaced-placeholder', mutatedNodeIds: [cap.id], removed: [P.target], at };
}

// --- versioning ---
const missing = [];
const vars = await figma.variables.getLocalVariablesAsync('COLOR');
const cols = Object.fromEntries((await figma.variables.getLocalVariableCollectionsAsync()).map(c => [c.id, c.name]));
const findVar = name => {
  const hits = vars.filter(v => v.name === name);
  const v = hits.find(v => cols[v.variableCollectionId] === P.prefer_collection) || hits[0];
  if (!v) missing.push('variable ' + name);
  return v;
};
const styles = await figma.getLocalTextStylesAsync();
const findStyle = name => { const s = styles.find(s => s.name === name); if (!s) missing.push('text style ' + name); return s; };
const solid = v => [figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', v)];

const fillVar = findVar(P.card_fill_var), textVar = findVar(P.card_text_var);
const titleStyle = findStyle(P.title_style), bodyStyle = findStyle(P.body_style);
if (missing.length) return { mode: 'blocked', missing, hint: 'ask the user whether to add these to the design system' };

const card = figma.createFrame(); card.name = `Version card · ${cap.name}`;  // plain Plugin API, works on every backend
card.layoutMode = 'VERTICAL'; card.primaryAxisSizingMode = 'AUTO'; card.counterAxisSizingMode = 'AUTO'; card.itemSpacing = 16;
card.paddingTop = card.paddingBottom = 64; card.paddingLeft = card.paddingRight = 80;
card.cornerRadius = 32;
card.fills = solid(fillVar);
const line = async (chars, style) => {
  const t = figma.createText();
  await figma.loadFontAsync(style.fontName);
  await t.setTextStyleIdAsync(style.id);
  t.characters = chars;
  t.fills = solid(textVar);
  card.appendChild(t);
  return t;
};
await line(P.title || 'New version', titleStyle);
await line([P.version, P.date].filter(Boolean).join(' · '), bodyStyle);
if (P.note) await line(P.note, bodyStyle);
figma.currentPage.appendChild(card);
card.resize(cap.width, card.height);  // resize() fixes both axes, so let height hug again
card.primaryAxisSizingMode = 'AUTO';
card.x = at.x; card.y = at.y - card.height - 80;

target.x = at.x + cap.width + gap;
target.opacity = 0.5;
if (P.old_version && !target.name.includes(`(${P.old_version})`)) target.name = `${target.name} (${P.old_version})`;
return { mode: 'versioned', mutatedNodeIds: [cap.id, target.id], createdNodeIds: [card.id], at };
