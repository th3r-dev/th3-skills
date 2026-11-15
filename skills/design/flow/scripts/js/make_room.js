// Rendered by figma_js.py (params injected as P); run via run_script / use_figma.
// Make horizontal room for UI → flow → UI inside a section: move every top-level node whose left edge is at or
// right of P.from_x by P.dx (connectors follow their endpoints, so they're skipped), and widen the section label
// P.label by P.dx. Nothing is deleted; relative layouts inside moved sections stay intact.
// Pages laid out in rows (a label at the left, screens to its right) take P.y_from / P.y_to: only nodes whose
// top edge is inside that band move, so the other rows keep their place.
// Vertical room (P.from_y + P.dy): every top-level node whose top edge is at or below P.from_y moves down by P.dy,
// e.g. a band of result-state screens under a row; the rows below shift together and keep their spacing.
const P = __PARAMS__;
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(P.page));
const moved = [], skipped = [];
const vertical = P.dy != null;
for (const n of figma.currentPage.children) {
  if (vertical ? n.y < P.from_y : n.x < P.from_x) continue;
  if (!vertical && ((P.y_from != null && n.y < P.y_from) || (P.y_to != null && n.y >= P.y_to))) continue;
  if (n.type === 'CONNECTOR') { skipped.push(n.id); continue; }
  if (vertical) n.y += P.dy; else n.x += P.dx;
  moved.push(n.id);
}
let label = null;
if (P.label && !vertical) {
  label = await figma.getNodeByIdAsync(P.label);
  if (label) label.resize(label.width + P.dx, label.height);
}
// connectors keep their stored elbow route when glued layers move through the Plugin API, so the moved ones go stale:
// run `figma_js.py redraw-connectors` right after this
return { moved: moved.length, connectorsFollowing: skipped.length, labelWidth: label ? Math.round(label.width) : null,
  next: skipped.length ? 'run redraw-connectors: moved connectors keep their old route' : null };
