// ---------- cloth physics core (position-based dynamics; no THREE dependency) ----------
// Units: mm, seconds, grams. GL frame: x right, y up, z front. Body = mannequin; shirt = particle grid.
const PHYS = { g: 9810, damping: 0.985, substeps: 2, iters: 6, kStruct: 1.0, kShear: 0.85, kBend: 0.22,
  fabricGsm: 160, BODYK: 0.95, friction: { compression: 0.85, regular: 0.55, loose: 0.3 }, fitScale: { compression: 0.965, regular: 1.05, loose: 1.14 } };
const CNTH = 96, CNZ = 44, SNA = 32, SNT = 12;     // torso columns x rows; sleeve angles x rings
function bodyA(z){ return z > BNP ? 58 : interp(z, TA) * PHYS.BODYK; }
function bodyB(z){ return z > BNP ? 52 : interp(z, TB) * PHYS.BODYK; }
const ARM = { joint: (side) => [side * 168, 560, 0], len: 300, r: 48 };

function makeCloth(fit){
  const k = PHYS.fitScale[fit];
  const nT = CNTH * CNZ, nS = 2 * SNA * SNT, n = nT + nS;
  const C = { fit, n, nT, pos: new Float32Array(n * 3), prev: new Float32Array(n * 3), rest: new Float32Array(n * 3),
    w: new Float32Array(n), w0: new Float32Array(n), sz: new Float32Array(nT * 2), sl: new Float32Array(nS * 3), noBody: new Uint8Array(n),
    cons: [], grab: -1, grabT: [0, 0, 0], gap: new Float32Array(n) };
  // torso rest shape = body x fit scale (circumferential), body surface + 1 mm offset where tighter than body
  for (let i = 0; i < CNTH; i++) { const th = -Math.PI / 2 + 2 * Math.PI * i / CNTH;
    for (let j = 0; j < CNZ; j++) { const z = BNP * j / (CNZ - 1), id = i * CNZ + j;
      const c = Math.cos(th), s = Math.sin(th), e = 2 / NEXP;
      const ux = Math.sign(c) * Math.pow(Math.abs(c), e), uy = Math.sign(s) * Math.pow(Math.abs(s), e);
      const restScale = k, initScale = Math.max(k, 1.0) + 0.006;
      C.rest.set([bodyA(z) * restScale * ux, z, bodyB(z) * restScale * uy], id * 3);
      C.pos.set([bodyA(z) * initScale * ux, z, bodyB(z) * initScale * uy], id * 3);
      C.sz[id * 2] = thToS(th, z); C.sz[id * 2 + 1] = z; } }
  // sleeves (attached to torso by the first ring)
  const d = SL.droop;
  for (let si = 0; si < 2; si++) { const side = si === 0 ? 1 : -1;
    const ax = [side * Math.cos(d), -Math.sin(d), 0], up = [side * Math.sin(d), Math.cos(d), 0], fw = [0, 0, 1];
    for (let a = 0; a < SNA; a++) { const ang = 2 * Math.PI * a / SNA;
      for (let t = 0; t < SNT; t++) { const tt = t / (SNT - 1), id = nT + (si * SNA + a) * SNT + t;
        const rT = SL.r0 + (SL.r1 - SL.r0) * tt, hug = fit === 'compression' ? Math.min(1, tt / 0.35) : 0, hs = hug * hug * (3 - 2 * hug);   // compression sleeve tapers onto the arm
        const r = fit === 'compression' ? rT * (1 - hs) + ARM.r * 0.97 * hs : rT * Math.max(1, Math.min(1.1, k)), L = tt * SL.len;
        const nx = Math.cos(ang) * up[0] + Math.sin(ang) * fw[0], ny = Math.cos(ang) * up[1] + Math.sin(ang) * fw[1], nz = Math.cos(ang) * up[2] + Math.sin(ang) * fw[2];
        const rx = fit === 'compression' ? SL.rootX * (1 - hs) + ARM.joint(1)[0] * hs : SL.rootX; const p = [side * rx + ax[0] * L + r * nx, SL.rootZ + ax[1] * L + r * ny, ax[2] * L + r * nz];
        C.rest.set(p, id * 3); C.pos.set(p, id * 3); C.sl.set([side, tt, ang], (id - nT) * 3); if (t < 2) C.noBody[id] = 1; } } }
  C.prev.set(C.pos);
  // masses: fabric areal density spread per particle
  const pm = PHYS.fabricGsm * 1e-6 * (2 * Math.PI * 160 / CNTH) * (BNP / (CNZ - 1));   // g per particle (~0.06 g)
  for (let p = 0; p < n; p++) { C.w0[p] = 1 / pm; C.w[p] = C.w0[p]; }
  // constraints
  const add = (a, b, kk) => { const dx = C.rest[a*3]-C.rest[b*3], dy = C.rest[a*3+1]-C.rest[b*3+1], dz = C.rest[a*3+2]-C.rest[b*3+2]; C.cons.push(a, b, Math.hypot(dx, dy, dz), kk); };
  const T = (i, j) => ((i + CNTH) % CNTH) * CNZ + j;
  for (let i = 0; i < CNTH; i++) for (let j = 0; j < CNZ; j++) {
    if (j + 1 < CNZ) add(T(i, j), T(i, j + 1), PHYS.kStruct);
    add(T(i, j), T(i + 1, j), PHYS.kStruct);
    if (j + 1 < CNZ) { add(T(i, j), T(i + 1, j + 1), PHYS.kShear); add(T(i + 1, j), T(i, j + 1), PHYS.kShear); }
    if (j + 2 < CNZ) add(T(i, j), T(i, j + 2), PHYS.kBend);
    add(T(i, j), T(i + 2, j), PHYS.kBend); }
  for (let si = 0; si < 2; si++) { const S = (a, t) => nT + (si * SNA + ((a + SNA) % SNA)) * SNT + t;
    for (let a = 0; a < SNA; a++) for (let t = 0; t < SNT; t++) {
      if (t + 1 < SNT) { add(S(a, t), S(a, t + 1), PHYS.kStruct); add(S(a, t), S(a + 1, t + 1), PHYS.kShear); }
      add(S(a, t), S(a + 1, t), PHYS.kStruct); if (t + 2 < SNT) add(S(a, t), S(a, t + 2), PHYS.kBend); }
    // attach first ring to nearest torso particles
    for (let a = 0; a < SNA; a++) { const p = S(a, 0); let best = -1, bd = 1e9;
      for (let q = 0; q < nT; q++) { const dd = (C.rest[q*3]-C.rest[p*3])**2 + (C.rest[q*3+1]-C.rest[p*3+1])**2 + (C.rest[q*3+2]-C.rest[p*3+2])**2; if (dd < bd) { bd = dd; best = q; } }
      add(p, best, 1.0); C.cons[C.cons.length - 2] = Math.min(C.cons[C.cons.length - 2], 4); } }
  C.cons = Float64Array.from(C.cons);
  // shoulder support: yoke rows (z >= 640) rest on the body's shoulders; anchor = body surface point (body-local)
  const anc = [];
  for (let i = 0; i < CNTH; i++) for (let j = 0; j < CNZ; j++) { const z = BNP * j / (CNZ - 1); if (z < 640) continue;
    const id = i * CNZ + j, th = -Math.PI / 2 + 2 * Math.PI * i / CNTH, c = Math.cos(th), s = Math.sin(th), e = 2 / NEXP;
    const ux = Math.sign(c) * Math.pow(Math.abs(c), e), uy = Math.sign(s) * Math.pow(Math.abs(s), e);
    anc.push(id, bodyA(z) * ux * 1.004 + ux * 0.8, z, bodyB(z) * uy * 1.004 + uy * 0.8, z >= 680 ? 0.5 : 0.25); }
  C.anchor = Float64Array.from(anc);
  // long-range attachments: no particle may hang further than 3% beyond its rest distance from its column's yoke row / sleeve root ring
  const teth = [], jTop = Math.ceil(640 / BNP * (CNZ - 1)), rd = (a, b) => Math.hypot(C.rest[a*3]-C.rest[b*3], C.rest[a*3+1]-C.rest[b*3+1], C.rest[a*3+2]-C.rest[b*3+2]);
  for (let i = 0; i < CNTH; i++) for (let j = 0; j < jTop; j++) { const p = i * CNZ + j, q = i * CNZ + jTop; let L = 0; for (let jj = j; jj < jTop; jj++) L += rd(i * CNZ + jj, i * CNZ + jj + 1); teth.push(p, q, L * 1.03); }
  for (let si = 0; si < 2; si++) for (let a = 0; a < SNA; a++) { const q = nT + (si * SNA + a) * SNT; for (let t = 2; t < SNT; t++) { const p = q + t; let L = 0; for (let tt = 0; tt < t; tt++) L += rd(q + tt, q + tt + 1); teth.push(p, q, L * 1.03); } }
  C.teth = Float64Array.from(teth);
  return C;
}

// body pose: translation, yaw (about y) and arm swing angles, plus previous pose for surface velocity
function bodyPose(t, motion){
  if (motion === 'walk') { const f = 0.9, w = 2 * Math.PI * f; return { tx: 0, ty: 7 * Math.abs(Math.sin(w * t)) - 3.5, tz: 0, yaw: 0.05 * Math.sin(w * t), roll: 0.02 * Math.sin(w * t), swing: [0.33 * Math.sin(w * t), -0.33 * Math.sin(w * t)] }; }
  if (motion === 'run') { const f = 1.35, w = 2 * Math.PI * f; return { tx: 0, ty: 28 * Math.abs(Math.sin(w * t)) - 14, tz: 0, yaw: 0.09 * Math.sin(w * t), roll: 0.03 * Math.sin(w * t), swing: [0.65 * Math.sin(w * t), -0.65 * Math.sin(w * t)] }; }
  return { tx: 0, ty: 0, tz: 0, yaw: 0, roll: 0, swing: [0, 0] };
}
function toLocal(P, p){ // world -> body local (inverse yaw/roll, translation)
  let x = p[0] - P.tx, y = p[1] - P.ty - 430, z = p[2] - P.tz;
  const cy = Math.cos(-P.yaw), sy = Math.sin(-P.yaw); let x1 = cy * x + sy * z, z1 = -sy * x + cy * z;
  const cr = Math.cos(-P.roll), sr = Math.sin(-P.roll); let x2 = cr * x1 - sr * y, y2 = sr * x1 + cr * y;
  return [x2, y2 + 430, z1]; }
function toWorld(P, q){
  let x = q[0], y = q[1] - 430, z = q[2];
  const cr = Math.cos(P.roll), sr = Math.sin(P.roll); let x1 = cr * x - sr * y, y1 = sr * x + cr * y;
  const cy = Math.cos(P.yaw), sy = Math.sin(P.yaw); let x2 = cy * x1 + sy * z, z2 = -sy * x1 + cy * z;
  return [x2 + P.tx, y1 + 430 + P.ty, z2 + P.tz]; }
function armSeg(P, side){ // world-space segment of the arm capsule
  const si = side > 0 ? 0 : 1, j = ARM.joint(side), d = SL.droop, sw = P.swing[si];
  const dir = [side * Math.cos(d), -Math.sin(d) * Math.cos(sw), -Math.sin(d) * Math.sin(sw)];
  const a = toWorld(P, j), b = toWorld(P, [j[0] + dir[0] * ARM.len, j[1] + dir[1] * ARM.len, j[2] + dir[2] * ARM.len]); return [a, b]; }

// body surface query in body-local coords (y up): returns gap (+ outside) and outward unit normal (implicit-surface gradient)
const _S = { gap: 0, nx: 0, ny: 0, nz: 0 };
function bodyQuery(x, y, z){
  const yy = Math.max(0, y), a = bodyA(yy), b = bodyB(yy), da = (bodyA(yy + 2) - bodyA(yy - 2)) / 4, db = (bodyB(yy + 2) - bodyB(yy - 2)) / 4;
  const ux = Math.abs(x / a), uz = Math.abs(z / b), px = Math.pow(ux, NEXP), pz = Math.pow(uz, NEXP), F = px + pz;
  const r = Math.sqrt(x * x + z * z) || 1e-6, k = Math.pow(F || 1e-9, -1 / NEXP);
  let gx = NEXP * px / (x || 1e-9), gz = NEXP * pz / (z || 1e-9), gy = y > 0 ? -NEXP * (px * da / a + pz * db / b) : 0;
  const gl = Math.sqrt(gx * gx + gy * gy + gz * gz) || 1e-9; gx /= gl; gy /= gl; gz /= gl;
  const cosr = (gx * x + gz * z) / r;                      // radial vs normal
  _S.gap = (r - r * k) * Math.max(0.2, cosr); _S.nx = gx; _S.ny = gy; _S.nz = gz; return _S;
}
const GRIP = { compression: [0.9, 0.6], regular: [0.6, 0.3], loose: [0.35, 0.12] };   // [kinetic factor, static threshold mm]
function collide(C, P, Pp, measure){
  const pos = C.pos, prev = C.prev, n = C.n, [muK, muS] = GRIP[C.fit];
  const cy = Math.cos(P.yaw), sy = Math.sin(P.yaw), cr = Math.cos(P.roll), sr = Math.sin(P.roll);
  const cyp = Math.cos(Pp.yaw), syp = Math.sin(Pp.yaw), crp = Math.cos(Pp.roll), srp = Math.sin(Pp.roll);
  const arms = [armSeg(P, 1), armSeg(P, -1)];
  for (let p = 0; p < n; p++) { if (C.w[p] === 0) continue; const i = p * 3;
    if (measure) C.gap[p] = 1e9;
    if (!C.noBody[p]) {
      // world -> local
      let x = pos[i] - P.tx, y = pos[i+1] - P.ty - 430, z = pos[i+2] - P.tz;
      let x1 = cy * x - sy * z, z1 = sy * x + cy * z; let lx = cr * x1 + sr * y, ly = -sr * x1 + cr * y + 430, lz = z1;
      if (ly > -20 && ly < BNP + 120) { const S = bodyQuery(lx, ly, lz); if (measure) C.gap[p] = S.gap;
        if (S.gap < 0.6) { const d = 0.6 - S.gap; lx += S.nx * d; ly += S.ny * d; lz += S.nz * d;
          // local -> world (current and previous pose) for surface velocity
          let yy = ly - 430, X1 = cr * lx - sr * yy, Y1 = sr * lx + cr * yy;
          const wx = cy * X1 + sy * lz + P.tx, wy = Y1 + 430 + P.ty, wz = -sy * X1 + cy * lz + P.tz;
          X1 = crp * lx - srp * yy; Y1 = srp * lx + crp * yy;
          const bx = wx - (cyp * X1 + syp * lz + Pp.tx), by = wy - (Y1 + 430 + Pp.ty), bz = wz - (-syp * X1 + cyp * lz + Pp.tz);
          pos[i] = wx; pos[i+1] = wy; pos[i+2] = wz;
          // friction (position based): tangential motion relative to the body this substep
          const nwx = cy * (cr * S.nx - sr * S.ny) + sy * S.nz, nwy = sr * S.nx + cr * S.ny, nwz = -sy * (cr * S.nx - sr * S.ny) + cy * S.nz;
          let dx = pos[i] - prev[i] - bx, dy = pos[i+1] - prev[i+1] - by, dz = pos[i+2] - prev[i+2] - bz; const dn = dx * nwx + dy * nwy + dz * nwz;
          dx -= dn * nwx; dy -= dn * nwy; dz -= dn * nwz; const dt = Math.sqrt(dx * dx + dy * dy + dz * dz);
          const f = dt < muS ? 1 : muK; pos[i] -= dx * f; pos[i+1] -= dy * f; pos[i+2] -= dz * f; } } }
    if (p >= C.nT) { for (const [A, B] of arms) { const abx = B[0]-A[0], aby = B[1]-A[1], abz = B[2]-A[2];
      let u = ((pos[i]-A[0])*abx + (pos[i+1]-A[1])*aby + (pos[i+2]-A[2])*abz) / (abx*abx + aby*aby + abz*abz); u = Math.max(0, Math.min(1, u));
      const cx = A[0] + abx*u, cy2 = A[1] + aby*u, cz = A[2] + abz*u, dx = pos[i]-cx, dy = pos[i+1]-cy2, dz = pos[i+2]-cz, dd = Math.sqrt(dx*dx+dy*dy+dz*dz) || 1e-6;
      if (measure && u > 0.02) C.gap[p] = Math.min(C.gap[p], dd - ARM.r);
      if (dd < ARM.r + 0.6) { const s = (ARM.r + 0.6) / dd; pos[i] = cx + dx*s; pos[i+1] = cy2 + dy*s; pos[i+2] = cz + dz*s; } } } }
}

function stepCloth(C, t, dt, motion, wind){
  const h = dt / PHYS.substeps, g = PHYS.g * h * h, n = C.n, pos = C.pos, prev = C.prev;
  let P = bodyPose(t, motion);
  for (let ss = 0; ss < PHYS.substeps; ss++) {
    const tt = t - dt + (ss + 1) * h; P = bodyPose(tt, motion); const Pp = bodyPose(tt - h, motion);
    const windF = wind ? (2500 + 1800 * Math.sin(tt * 2.3) + 900 * Math.sin(tt * 7.1)) * h * h : 0;
    for (let p = 0; p < n; p++) { if (C.w[p] === 0) continue; const i = p * 3;
      const vx = (pos[i] - prev[i]) * PHYS.damping, vy = (pos[i+1] - prev[i+1]) * PHYS.damping, vz = (pos[i+2] - prev[i+2]) * PHYS.damping;
      prev[i] = pos[i]; prev[i+1] = pos[i+1]; prev[i+2] = pos[i+2];
      pos[i] += vx; pos[i+1] += vy - g; pos[i+2] += vz - windF * (0.6 + 0.4 * Math.sin(p * 0.37)); }
    const cons = C.cons, m = cons.length, w = C.w;
    for (let it = 0; it < PHYS.iters; it++) {
      if (C.grab >= 0) { const i = C.grab * 3; pos[i] = C.grabT[0]; pos[i+1] = C.grabT[1]; pos[i+2] = C.grabT[2]; }
      for (let c = 0; c < m; c += 4) { const ia = cons[c], ib = cons[c+1], wa = w[ia], wb = w[ib], ws = wa + wb; if (ws === 0) continue;
        const a = ia * 3, b = ib * 3, dx = pos[b] - pos[a], dy = pos[b+1] - pos[a+1], dz = pos[b+2] - pos[a+2], d = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1e-6;
        const s = cons[c+3] * (d - cons[c+2]) / (d * ws);
        pos[a] += dx * s * wa; pos[a+1] += dy * s * wa; pos[a+2] += dz * s * wa;
        pos[b] -= dx * s * wb; pos[b+1] -= dy * s * wb; pos[b+2] -= dz * s * wb; }
      { const T = C.teth, w = C.w; for (let c = 0; c < T.length; c += 3) { const p = T[c], q = T[c+1]; if (w[p] === 0) continue; const a = p * 3, b = q * 3;
          const dx = pos[a] - pos[b], dy = pos[a+1] - pos[b+1], dz = pos[a+2] - pos[b+2], d = Math.sqrt(dx*dx + dy*dy + dz*dz); if (d > T[c+2]) { const s = T[c+2] / d; pos[a] = pos[b] + dx * s; pos[a+1] = pos[b+1] + dy * s; pos[a+2] = pos[b+2] + dz * s; } } }
      { const A = C.anchor, cyA = Math.cos(P.yaw), syA = Math.sin(P.yaw), crA = Math.cos(P.roll), srA = Math.sin(P.roll);
        for (let q = 0; q < A.length; q += 5) { const p = A[q], i = p * 3; if (w[p] === 0) continue; const k = A[q+4];
          const lx = A[q+1], yy = A[q+2] - 430, lz = A[q+3], X1 = crA * lx - srA * yy, Y1 = srA * lx + crA * yy;
          const tx = cyA * X1 + syA * lz + P.tx, ty = Y1 + 430 + P.ty, tz = -syA * X1 + cyA * lz + P.tz;
          pos[i] += (tx - pos[i]) * k; pos[i+1] += (ty - pos[i+1]) * k; pos[i+2] += (tz - pos[i+2]) * k; } }
      if (it === (PHYS.iters >> 1) || it === PHYS.iters - 1) collide(C, P, Pp, it === PHYS.iters - 1 && ss === PHYS.substeps - 1);
    }
  }
  return P;
}
// module mass: spread over the footprint particles (rest s,z within the module rectangle)
function footprint(C, s0, z0, w, h){ const out = []; for (let p = 0; p < C.nT; p++) { let ds = C.sz[p*2] - s0; const Cc = arc(C.sz[p*2+1]).C; if (ds > Cc/2) ds -= Cc; if (ds < -Cc/2) ds += Cc;
  if (Math.abs(ds) <= w / 2 + 6 && Math.abs(C.sz[p*2+1] - z0) <= h / 2 + 6) out.push(p); } return out; }
function sleeveFootprint(C, side, t, ang){ const out = []; for (let p = C.nT; p < C.n; p++) { const q = (p - C.nT) * 3; if (C.sl[q] !== side) continue;
  let da = C.sl[q+2] - ang; da = Math.atan2(Math.sin(da), Math.cos(da)); if (Math.abs(C.sl[q+1] - t) < 0.12 && Math.abs(da) < 0.45) out.push(p); } return out; }
function applyMasses(C, items){ C.w.set(C.w0); for (const it of items) { if (!it.idx.length) continue; const add = it.mass / it.idx.length;
  for (const p of it.idx) C.w[p] = 1 / (1 / C.w0[p] + add); } }
