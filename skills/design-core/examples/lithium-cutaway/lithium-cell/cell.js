// LITHE LC-21, a lithium-ion cell rebuilt from refs/R01 (the cutaway bench in design-core). Everything is built along
// local +x (the cell's axis) inside `body`, which is turned so +x points up. sweepX angles: 0 at local +y, 90° at +z;
// with body turned 90° about z, the cut quarter (90°..180°) faces the camera's front right, as in the picture.
// Parts that come apart are their own groups with named anchors: sleeve, can, cap, insulators, roll, mandrel, tabs.
import * as THREE from 'three';
import {makeMaterials, PAL, put, rbox, ring, V3} from 'cutaway-kit/../piranha-shared/parts.js';

export const FLOOR_Y = -1.28;
const R = 0.5; // can radius; the can runs x -1..1
const CUT = [Math.PI, Math.PI * 2.5]; // the solid arc; the missing quarter is the window
const WIN = [-0.93, 0.78]; // the window's height on the axis
const D2R = Math.PI / 180;

export function buildCell() {
  const M = makeMaterials();
  M.copper = new THREE.MeshStandardMaterial({color: '#b87333', roughness: 0.32, metalness: 0.85});
  M.sep = new THREE.MeshPhysicalMaterial({color: '#eceff1', roughness: 0.55, metalness: 0, clearcoat: 0.3});
  M.coat = new THREE.MeshStandardMaterial({color: '#1c1f23', roughness: 0.72, metalness: 0.15});
  M.capGrey = new THREE.MeshPhysicalMaterial({color: '#c9cfcb', roughness: 0.4, metalness: 0.3, clearcoat: 0.6});
  M.green = M.orange; // PAL.orange is set to the page green before the build

  // root (turntable) -> tilt (lays the cell down for the explode, pivot at its centre) -> body (built along +x)
  const root = new THREE.Group();
  const tilt = new THREE.Group();
  tilt.position.y = FLOOR_Y + 1.05;
  root.add(tilt);
  const body = new THREE.Group();
  body.scale.x = 1.05; // round 2: h/w measured 2.12 against R01's 2.26
  tilt.add(body);
  const group = (name) => {
    const g = new THREE.Group();
    g.name = name;
    body.add(g);
    return g;
  };
  const anchors = {};
  const anchor = (key, obj, x, y, z) => (anchors[key] = {obj, at: new V3(x, y, z)});
  const arc = {a0: CUT[0], a1: CUT[1], segs: 96};
  const full = {segs: 96};

  // ---- the steel can: a wall cut by the window, the crimped rim on top, the negative cup below
  const can = group('can');
  put(can, ring(WIN[0], WIN[1], R - 0.026, R - 0.012, 0.002, arc), M.steel);
  put(can, ring(WIN[1], 0.97, R - 0.026, R - 0.012, 0.002, full), M.steel);
  put(can, ring(0.955, 1.0, 0.36, R + 0.004, 0.018, full), M.shell); // the crimp, the light rim seen from above
  put(can, ring(-1.0, WIN[0], 0, R + 0.006, 0.03, full), M.black); // the negative cup
  anchor('base', can, -0.97, 0, R);

  // ---- the sleeve: gloss white wrap over the can, two green bands, the green edge of the cut, the bolt
  const sleeve = group('sleeve');
  put(sleeve, ring(WIN[0], WIN[1], R - 0.012, R, 0.002, arc), M.shell);
  put(sleeve, ring(WIN[1], 0.955, R - 0.012, R, 0.004, full), M.shell);
  put(sleeve, ring(0.8, 0.875, R - 0.004, R + 0.004, 0.003, full), M.green);
  put(sleeve, ring(-0.905, -0.885, R - 0.004, R + 0.004, 0.003, arc), M.green);
  put(sleeve, ring(WIN[1] - 0.025, WIN[1], 0.06, R + 0.004, 0.002, {a0: Math.PI / 2, a1: Math.PI, segs: 32}), M.green);
  put(sleeve, boltGeo(), M.orangeFilm); // double-sided: the bent shape's winding faces either way
  anchor('sleeve', sleeve, 0.1, R * Math.cos(62 * D2R), R * Math.sin(62 * D2R));

  // ---- the jelly roll: concentric layers in the cut, dark coating between copper, separator and aluminium foils.
  // ponytail: concentric rings, not a true spiral; reads the same in section, swap for a spiral if a shot looks down it
  const roll = group('roll');
  const layers = [];
  const FOIL = [M.copper, M.sep, M.gunmetal];
  let r = 0.05;
  for (let i = 0; r < R - 0.04; i++) {
    const coatT = 0.017;
    const foilT = i % 3 === 1 ? 0.008 : 0.006;
    const lay = new THREE.Group();
    put(lay, ring(-0.9, WIN[1] - 0.02, r, r + coatT, 0.001, arc), M.coat);
    put(lay, ring(-0.9 + 0.012, WIN[1] - 0.014, r + coatT, r + coatT + foilT, 0.001, arc), FOIL[i % 3]);
    r += coatT + foilT;
    roll.add(lay);
    layers.push(lay);
  }
  put(roll, ring(-0.9, WIN[1] - 0.02, r, R - 0.026, 0.001, arc), M.coat); // the outer wrap of separator-coat
  anchor('roll', roll, 0.1, -0.24, 0.12);
  const mandrel = group('mandrel');
  put(mandrel, ring(-0.92, 0.9, 0, 0.032, 0.006, {segs: 24}), M.steel);
  anchor('mandrel', mandrel, 0.5, 0, 0.032);

  // ---- tabs: the aluminium positive tab up to the cap, the nickel negative tab down to the cup
  const tabs = group('tabs');
  put(tabs, rbox(0.16, 0.012, 0.07, 0.004), M.steel, WIN[1] + 0.07, -0.2, 0.05);
  put(tabs, rbox(0.1, 0.012, 0.07, 0.004), M.copper, -0.93, 0.2, 0.05);
  anchor('tabs', tabs, WIN[1] + 0.07, -0.2, 0.09);

  // ---- insulators: pale discs at both ends of the roll
  const insTop = group('insTop');
  put(insTop, ring(0.83, 0.85, 0.06, R - 0.03, 0.004, full), M.sep);
  const insBot = group('insBot');
  put(insBot, ring(-0.925, -0.91, 0.06, R - 0.03, 0.004, full), M.coat); // dark, so the window stays dark to the cup

  // ---- the cap stack: CID disc, PTC ring, recessed cap with 4 vents, green gasket, the positive button
  const cap = group('cap');
  put(cap, ring(0.88, 0.9, 0, R - 0.035, 0.004, full), M.steel); // CID disc
  put(cap, ring(0.905, 0.925, 0.2, R - 0.06, 0.004, full), M.graphite); // PTC ring
  put(cap, ring(0.93, 0.975, 0, 0.42, 0.006, full), M.capGrey);
  for (let k = 0; k < 4; k++) {
    const a = (k * 90 + 45) * D2R;
    put(cap, ring(0.972, 0.979, 0, 0.05, 0.003, {segs: 24}), M.black, 0, 0.27 * Math.cos(a), 0.27 * Math.sin(a));
  }
  const gasket = put(cap, new THREE.TorusGeometry(0.455, 0.016, 12, 96), M.green, 1.0); // on the rim, not in it
  gasket.rotation.y = Math.PI / 2;
  put(cap, ring(0.975, 1.08, 0, 0.185, 0.022, full), M.steel); // the positive button
  anchor('cap', cap, 1.08, 0, 0.1);
  anchor('vent', cap, 0.979, 0.27 * Math.cos(135 * D2R), 0.27 * Math.sin(135 * D2R));

  const G = {can, sleeve, roll, mandrel, tabs, insTop, insBot, cap};
  const HOME = Object.fromEntries(Object.entries(G).map(([k, g]) => [k, g.position.clone()]));

  /** One moment of the cell. s: {spin, axial (deg), explode, cap, sleeve, roll, mandrel}, amounts 0..1.
   *  Every move runs along the cell's axis, so no part passes through another: the explode lays the cell on its
   *  side in the air and spreads the stack along the axis, the can and cup staying at one end. */
  const pose = (s = {}) => {
    const e = s.explode ?? 0;
    const c = s.cap ?? 0;
    for (const [k, g] of Object.entries(G)) {
      g.position.copy(HOME[k]);
      g.scale.set(1, 1, 1);
    }
    root.rotation.y = (s.spin ?? 0) * D2R;
    tilt.rotation.z = -(Math.PI / 2) * e;
    body.rotation.set(0, 0, Math.PI / 2);
    body.rotateX((s.axial ?? 0) * D2R);
    body.position.set(0, 0, 0);
    body.translateX(-1.85 * e); // the exploded stack's middle (-1.05 .. 4.6 after the 1.05 stretch) on the pivot
    const up = (k, x) => (G[k].position.x += x);
    // acts: the cap stack lifts (and stays up while the roll or the pin come out); the wrap loosens and rides up
    up('cap', 1.0 * c * (1 - e) + 3.3 * e);
    up('insTop', 0.5 * c * (1 - e) + 2.6 * e);
    up('roll', 2.0 * e);
    up('tabs', 2.15 * e);
    up('mandrel', 0.9 * (s.mandrel ?? 0) * (1 - e) + 3.0 * e);
    const w = Math.max(s.sleeve ?? 0, e);
    G.sleeve.scale.set(1, 1 + 0.07 * sm01(w * 3), 1 + 0.07 * sm01(w * 3));
    up('sleeve', 1.2 * (s.sleeve ?? 0) * (1 - e) + 0.25 * e);
    // the roll telescopes: layer i rises by a share of the open amount, inner first
    const t = Math.max(e * 0.5, s.roll ?? 0);
    layers.forEach((l, i) => (l.position.x = t * 0.5 * (1 - i / layers.length)));
  };

  const clear = [];
  const anchorAt = (key, out = new V3()) => {
    const a = anchors[key];
    a.obj.updateWorldMatrix(true, false);
    return a.obj.localToWorld(out.copy(a.at));
  };
  return {root, tilt, body, pose, clear, M, anchors, anchorAt, layers, groups: G};
}

// the bolt from R01, in picture px (can 320 px wide = 1.0, 600 px tall = 2.0), bent onto the sleeve
function boltGeo() {
  const P = [[430, 420], [382, 560], [424, 560], [398, 680], [468, 520], [428, 520], [456, 420]];
  const s = new THREE.Shape(P.map(([x, y]) => new THREE.Vector2((x - 425) / 300, -(y - 550) / 300)));
  const g = new THREE.ShapeGeometry(s);
  const p = g.attributes.position;
  const rr = R + 0.0035;
  const phiC = 62 * D2R; // left of the front, as in the picture (90° is dead front)
  const xC = 1.0 - (550 - 230) / 300;
  for (let i = 0; i < p.count; i++) {
    const u = p.getX(i);
    const v = p.getY(i);
    const phi = phiC + u / R;
    p.setXYZ(i, xC + v, rr * Math.cos(phi), rr * Math.sin(phi));
  }
  g.computeVertexNormals();
  return g;
}

const sm01 = (x) => Math.min(1, Math.max(0, x));

export {PAL};
