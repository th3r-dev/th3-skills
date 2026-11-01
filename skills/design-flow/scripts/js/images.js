// Rendered by figma_js.py (params injected as P); run the output as the `code` of use_figma / run_script.
// Fills the raster images capture.py split out of an html-figma import: every layer under P.root whose shared
// plugin data ("builder", "data") carries an `image` key gets an IMAGE fill from P.images[key] (base64).
// The importer can't do this itself: JSON can't carry the Uint8Array figma.createImage needs.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const root = await figma.getNodeByIdAsync(P.root);
if (!root) return { error: 'root not found: ' + P.root };
const hashes = {};
const out = { filled: 0, missing: [], mutatedNodeIds: [] };
for (const n of [root, ...root.findAll(n => 'fills' in n)]) {
  let d;
  try { d = JSON.parse(n.getSharedPluginData('builder', 'data') || '{}'); } catch (e) { continue; }
  if (!d || !d.image) continue;
  const img = P.images[d.image];
  if (!img) { out.missing.push(d.image); continue; }
  hashes[d.image] = hashes[d.image] || figma.createImage(figma.base64Decode(img.b64)).hash;
  n.fills = [{ type: 'IMAGE', scaleMode: img.scaleMode || 'FILL', imageHash: hashes[d.image] }];
  out.filled++;
  out.mutatedNodeIds.push(n.id);
}
return out;
