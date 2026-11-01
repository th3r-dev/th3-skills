# Flow conventions

## Conventions

Use the file's own kit when it has one. These defaults describe a common kit, and they are
what this skill falls back on when a file has none.

| Element | Node | Style |
|---|---|---|
| Process / action step | `SHAPE_WITH_TEXT`, `shapeType: 'SQUARE'` | white fill, grey stroke |
| Alert / error step | `SHAPE_WITH_TEXT`, `SQUARE` | light red fill (`#f8aaa7`) |
| Decision | `SHAPE_WITH_TEXT`, `shapeType: 'DIAMOND'` | white fill, square bounds (336 × 336) |
| Navigation edge (menu → screen) | `CONNECTOR`, elbowed, 4 px | dark (`#002538`), no label |
| Decision edge | `CONNECTOR`, elbowed, 4 px | dark, labeled `True` / `False` |
| Highlighted edge | `CONNECTOR` | blue (`#4394e5`) |
| Kit variants | `CONNECTOR` | red (`#ef4840`) and green (`#43b55e`) exist for failure and success paths |
| Note | frame with Header + body | one per business rule that the flow can't show |

Text: the file's body font at 18 px. Process steps are 336 × 122.

**Arrow direction.** In the kit this skill was built from, the arrowhead sits on the
**start** cap (`connectorStartStrokeCap: 'ARROW_LINES'`, end `NONE`). So
`connectorStart` is the **target** and `connectorEnd` is the source. Check the caps
before you read edges or draw new ones. A flipped edge reads as the reverse flow.

## Read the flow

This is a read-only script for one page. Run it once per page, in parallel across pages.

```js
const page = await figma.getNodeByIdAsync('PAGE_ID');
await figma.setCurrentPageAsync(page);
const hex = p => p && p.type === 'SOLID'
  ? '#' + [p.color.r, p.color.g, p.color.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('')
  : null;
const nameOf = async id => { const n = id && await figma.getNodeByIdAsync(id); return n ? n.name : null; };
const edges = [];
for (const c of page.findAllWithCriteria({ types: ['CONNECTOR'] })) {
  const arrowAtStart = c.connectorStartStrokeCap !== 'NONE';
  const a = await nameOf(c.connectorStart.endpointNodeId);
  const b = await nameOf(c.connectorEnd.endpointNodeId);
  edges.push({ id: c.id, label: c.text.characters, color: hex(c.strokes[0]),
               from: arrowAtStart ? b : a, to: arrowAtStart ? a : b });
}
const steps = page.findAllWithCriteria({ types: ['SHAPE_WITH_TEXT'] })
  .map(s => ({ id: s.id, shape: s.shapeType, fill: hex(s.fills[0]), text: s.text.characters }));
return { steps, edges };
```

## Build from the kit

Design mode blocks creating shapes and connectors, so clone the kit nodes. The IDs
come from your own read of the kit. Never hard-code them in this skill.

```js
const page = await figma.getNodeByIdAsync('TARGET_PAGE_ID');
await figma.setCurrentPageAsync(page);
const kitDecision = await figma.getNodeByIdAsync('KIT_DECISION_ID');
const kitConnector = await figma.getNodeByIdAsync('KIT_CONNECTOR_ID');
const screen = await figma.getNodeByIdAsync('SCREEN_ID');

const d = kitDecision.clone();
page.appendChild(d);
await figma.loadFontAsync(d.text.fontName);
d.text.characters = 'Has permission?';
d.x = screen.x + screen.width + 200; d.y = screen.y;

const e = kitConnector.clone();
page.appendChild(e);
e.connectorStart = { endpointNodeId: d.id, magnet: 'AUTO' };     // arrow end = target
e.connectorEnd = { endpointNodeId: screen.id, magnet: 'AUTO' };  // source
return { createdNodeIds: [d.id, e.id] };
```

If `clone()` throws in design mode, stop and report it. The fallback is to build the
flow in a FigJam board (`figma-use-figjam`) and link to it from the screen, which is
the user's call.

## Mock labels

Examples, test runs, and anything published use these and never real names from a
user's file:

| Slot | English mock | Thai mock |
|---|---|---|
| Role | `Role A`, `Role B` | `บทบาท ก`, `บทบาท ข` |
| Menu | `Menu 1`, `Menu 2` | `เมนู 1`, `เมนู 2` |
| Screen | `Screen 1.1` | `หน้าจอ 1.1` |
| Breadcrumb | `Role A ▸ Menu 1 ▸ Screen 1.1` | `บทบาท ก ▸ เมนู 1 ▸ หน้าจอ 1.1` |
| Decision | `Has permission?`, `Login ok?` | `มีสิทธิ์หรือไม่`, `เข้าสู่ระบบสำเร็จ?` |
| Alert | `Alert: no access` | `แจ้งเตือน: ไม่มีสิทธิ์` |
| Person in data | follow `thai-mock-naming` | follow `thai-mock-naming` |
