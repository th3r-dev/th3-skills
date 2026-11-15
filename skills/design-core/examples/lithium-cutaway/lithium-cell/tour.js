// The cell's film as functions of time: each act's open amount, the explode, the turntable, one camera per beat,
// the labels and the card values. Pure: stateAt(t) reads only t and the timeline. No close body among the upstream
// examples (a cylinder with no limbs), so the beat timing follows the method's numbers rather than a ported film:
// a part opens in 1 s, holds, closes in 0.5 s, a new beat every 2.5 s, then the explode, a fast reassembly, the exit.

const sm = (x) => {
  const u = Math.min(1, Math.max(0, x));
  return u * u * u * (u * (u * 6 - 15) + 10);
};
const lerp = (a, b, k) => a + (b - a) * k;

// one camera per beat: its own side, height and distance, aimed at its part (degrees, world units)
const CAM = {
  intro: {tx: 0, ty: -0.22, tz: 0, az: 6, el: 16, d: 9.2},
  cap: {tx: 0, ty: 1.15, tz: 0, az: 24, el: 40, d: 5.4}, // from above, the stack lifting off
  sleeve: {tx: -0.3, ty: 0.55, tz: 0, az: -58, el: 8, d: 11.5}, // low from the left, the wrap sliding off
  roll: {tx: 0.1, ty: 0.75, tz: 0.1, az: 46, el: 22, d: 8.4}, // into the cut, the layers telescoping
  mandrel: {tx: 0, ty: 1.0, tz: 0, az: -24, el: 28, d: 6.2}, // the pin drawn up through the open cap
  exploded: {tx: 0, ty: -0.2, tz: 0, az: 4, el: 13, d: 11.5},
  assemble: {tx: 0, ty: -0.2, tz: 0, az: 6, el: 15, d: 10.0},
  hero: {tx: 0, ty: -0.22, tz: 0, az: 10, el: 17, d: 8.4},
};
const LABELS = {
  cap: [['cap', 'POSITIVE CAP', 'button · ptc ring · vent disc'], ['vent', 'VENT', 'opens at overpressure']],
  sleeve: [['sleeve', 'WRAP', 'printed sleeve over the steel can'], ['base', 'NEGATIVE CUP', 'the can is the minus pole']],
  roll: [['roll', 'JELLY ROLL', 'anode · separator · cathode'], ['tabs', 'POSITIVE TAB', 'aluminium, up to the cap']],
  mandrel: [['mandrel', 'MANDREL', 'steel pin the roll is wound on']],
  exploded: [['cap', 'CAP STACK', '5 parts'], ['roll', 'JELLY ROLL', '18 layers'], ['base', 'CAN AND WRAP', 'steel under a printed sleeve']],
};
const STATUS = {intro: 'Idle', cap: 'Cap off', sleeve: 'Wrap off', roll: 'Roll open', mandrel: 'Pin out', exploded: 'Teardown', assemble: 'Reassembly', hero: 'Sealed'};

export function makeTour(TL) {
  const SCRIPT = [...TL.script].sort((a, b) => a.t - b.t);
  const END = TL.duration;
  const next = (i) => SCRIPT[i + 1]?.t ?? END;
  const actAt = (t) => {
    let i = -1;
    SCRIPT.forEach((e, j) => t >= e.t && (i = j));
    return i;
  };
  // an act's open amount: 1 s out, hold, 0.5 s back before the next beat
  const open = (act, t) => {
    let w = 0;
    SCRIPT.forEach((e, i) => {
      if (e.act !== act) return;
      w = Math.max(w, sm((t - e.t) / 1.0) * (1 - sm((t - (next(i) - 0.6)) / 0.5)));
    });
    return w;
  };
  const tEx = SCRIPT.find((e) => e.act === 'exploded')?.t ?? END;
  const tAs = SCRIPT.find((e) => e.act === 'assemble')?.t ?? END;

  const camAt = (t) => {
    // each beat's camera is reached in 1.1 s from the one before, then pushes in 6% while the part hangs open
    let cur = CAM.intro;
    let from = CAM.intro;
    let k = 1;
    let since = t;
    const i = actAt(t);
    if (i >= 0) {
      cur = CAM[SCRIPT[i].act];
      from = i > 0 ? CAM[SCRIPT[i - 1].act] : CAM.intro;
      since = t - SCRIPT[i].t;
      k = sm(since / 1.1);
    }
    const c = Object.fromEntries(Object.keys(cur).map((key) => [key, lerp(from[key], cur[key], k)]));
    c.d *= 1 - 0.06 * sm((since - 0.6) / 2);
    return c;
  };

  const stateAt = (t) => {
    const explode = sm((t - tEx - 0.1) / 1.6) * (1 - sm((t - tAs) / 1.0));
    // a slow turntable drift; through the explode the cell, lying down, turns once on its own axis and lands home
    const spin = -18 + 18 * sm(t / 2.4) + 6 * Math.sin(t * 0.7);
    const axial = 360 * sm((t - tEx - 0.4) / (tAs + 0.6 - tEx));
    const i = actAt(t);
    const act = i < 0 ? 'intro' : SCRIPT[i].act;
    const s = {
      t,
      spin,
      axial,
      explode,
      cap: Math.max(open('cap', t), open('roll', t), open('mandrel', t)),
      sleeve: open('sleeve', t),
      roll: open('roll', t),
      mandrel: open('mandrel', t),
    };
    const view = act === 'assemble' ? 'exploded' : act === 'intro' || act === 'hero' ? 'overview' : act;
    const labelO = act === 'exploded' ? sm((t - tEx - 1.2) / 0.5) * (1 - sm((t - tAs + 0.4) / 0.3)) : act in LABELS ? open(act, t) : 0;
    const apart = Math.max(s.explode, s.cap, s.sleeve, s.roll, s.mandrel);
    return {
      ...s,
      act,
      view,
      apart,
      cam: camAt(t),
      labels: {set: LABELS[act === 'assemble' ? 'exploded' : act] ?? [], o: labelO},
      status: STATUS[act],
      // the cards: a cell that sags as it is opened, a layer per bar, warming a touch under the lights
      volts: 3.68 - 0.25 * apart + 0.015 * Math.sin(t * 5),
      charge: 0.82 - 0.06 * apart,
      bars: Array.from({length: 6}, (_, j) => 0.35 + 0.45 * Math.max(s.roll, explode) * (1 - j / 7) + 0.08 * Math.sin(t * 2.3 + j)),
      temp: 24 + 3 * apart,
    };
  };
  return {SCRIPT, stateAt};
}
