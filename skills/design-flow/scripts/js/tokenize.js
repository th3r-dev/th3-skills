// use_figma body: swap raw values under ROOT_ID for the file's own design system.
// Rendered by figma_js.py (params injected as P); run the output as the `code` of a use_figma call.
//   - text: fallback font families -> FONT_MAP, then the local text style with the same family, weight and size
//     (a Regular style is never forced onto a Medium/Bold text: that text is reported instead)
//   - SOLID fills/strokes: the COLOR variable with the exact same hex (PREFER_COLLECTION first)
// Returns counts and every raw value it could not match, so the agent can report gaps instead of inventing tokens.
const P = __PARAMS__;
const ROOT_ID = P.root, PAGE_ID = P.page;
const PREFER_COLLECTION = P.prefer_collection || '';  // '' = any collection
const FONT_MAP = P.font_map || {};                    // captured fallback family -> real family

await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(PAGE_ID));
const root = await figma.getNodeByIdAsync(ROOT_ID);
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');

// colour index: hex (opaque) or hex@alpha (translucent) -> variable (preferred collection wins)
const byHex = {};
const key = (c, a) => hex(c) + ((a ?? 1) < 1 ? '@' + Math.round(a * 100) / 100 : '');
for (const col of await figma.variables.getLocalVariableCollectionsAsync()) {
  const mode = col.defaultModeId;
  for (const id of col.variableIds) {
    const v = await figma.variables.getVariableByIdAsync(id);
    if (v.resolvedType !== 'COLOR') continue;
    const val = v.valuesByMode[mode];
    if (!val || val.type === 'VARIABLE_ALIAS') continue;
    const k = key(val, val.a);
    if (!byHex[k] || col.name === PREFER_COLLECTION) byHex[k] = v;
  }
}
const styles = await figma.getLocalTextStylesAsync();
const fonts = await figma.listAvailableFontsAsync();
const hasFont = (family, style) => fonts.some(f => f.fontName.family === family && f.fontName.style === style);
const styleFix = s => s.replace(/Semi Bold/i, 'SemiBold').replace(/Extra Bold/i, 'ExtraBold');

const out = { boundPaints: 0, styledTexts: 0, fontsRemapped: 0, unmatchedColors: {}, unmatchedText: {}, errors: [] };
const nodes = [root, ...(root.findAll ? root.findAll(() => true) : [])];

for (const n of nodes) {
  for (const prop of ['fills', 'strokes']) {
    if (!(prop in n) || !Array.isArray(n[prop]) || !n[prop].length) continue;
    let changed = false;
    const paints = n[prop].map(p => {
      if (p.type !== 'SOLID' || (p.boundVariables && p.boundVariables.color) || p.opacity === 0) return p;  // keep transparent paints raw
      // Figma takes a bound paint's opacity from the variable's alpha, so an 8% black tint only binds to a variable
      // that is itself black at 8% (key hex@0.08); binding it to opaque black would make it solid
      const k = key(p.color, p.opacity);
      const v = byHex[k];
      if (!v) { out.unmatchedColors[k] = (out.unmatchedColors[k] || 0) + 1; return p; }
      changed = true; out.boundPaints++;
      return figma.variables.setBoundVariableForPaint(p, 'color', v);
    });
    if (changed) n[prop] = paints;
  }
  if (n.type !== 'TEXT' || (typeof n.textStyleId === 'string' && n.textStyleId)) continue;
  if (n.fontName === figma.mixed || n.fontSize === figma.mixed || n.textStyleId === figma.mixed) {
    // mixed runs (e.g. Thai 11px + Latin 9px): style each run on its own
    try {
      for (const seg of n.getStyledTextSegments(['fontName', 'fontSize', 'textStyleId'])) {
        if (seg.textStyleId) continue;
        await figma.loadFontAsync(seg.fontName);
        let { family, style } = seg.fontName;
        if (FONT_MAP[family]) {
          family = FONT_MAP[family]; style = [style, styleFix(style), 'Regular'].find(x => hasFont(family, x));
          await figma.loadFontAsync({ family, style });
          n.setRangeFontName(seg.start, seg.end, { family, style }); out.fontsRemapped++;
        }
        const ts = styles.find(t => Math.abs(t.fontSize - seg.fontSize) < 0.05 && t.fontName.family === family && t.fontName.style === style);
        if (!ts) { const k = `${family} ${style} ${seg.fontSize}`; out.unmatchedText[k] = (out.unmatchedText[k] || 0) + 1; continue; }
        await n.setRangeTextStyleIdAsync(seg.start, seg.end, ts.id);
        out.styledTexts++;
      }
    } catch (e) { out.errors.push(n.id + ': ' + e.message); }
    continue;
  }
  try {
    if (!n.hasMissingFont) await figma.loadFontAsync(n.fontName);  // captured fallback families are often missing
    let { family, style } = n.fontName;
    const target = FONT_MAP[family];
    if (target) {
      const s = [style, styleFix(style), 'Regular'].find(x => hasFont(target, x));
      family = target; style = s;
      await figma.loadFontAsync({ family, style });
      n.fontName = { family, style };
      out.fontsRemapped++;
    }
    const ts = styles.find(t => Math.abs(t.fontSize - n.fontSize) < 0.05 && t.fontName.family === family && t.fontName.style === style);
    if (!ts) { const k = `${family} ${style} ${n.fontSize}`; out.unmatchedText[k] = (out.unmatchedText[k] || 0) + 1; continue; }
    await figma.loadFontAsync(ts.fontName);
    await n.setTextStyleIdAsync(ts.id);
    out.styledTexts++;
  } catch (e) { out.errors.push(n.id + ': ' + e.message); }
}
out.mutatedRoot = ROOT_ID;
return out;
