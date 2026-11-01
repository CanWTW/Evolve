#!/usr/bin/env python3
"""EVOLVE v0.18.1: physical skill effects instead of glow (the v0.18 light layer + vignette are gone):
 - real ground fissures (tapered dark cracks with a lit lip, side branches, lifted slabs, craters, lava for meteor) that grow and linger
 - rock debris with height + shadow + bounce, dust clouds
 - wind funnels for Cyclone / Whirl Cleave / Tornado Shot (layered tapered wind ribbons, ground dust skirt, swirling grit)
 - scorch / frost-crystal / acid ground marks for elemental bursts
 - set pieces roll 3 random affixes (other legendaries 2) on top of their fixed lines; existing items are topped up on load
Usage: patch_p181.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = {}


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)


# ---------------- remove the glow layer ----------------
rep("  drawFx(now);\n  lightLayer(now);   // v0.18\n", "  drawFx(now);\n  groundTop(now);   // v0.18.1 rocks + dust over the fx\n")
rep("  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);\n  drawVignette();   // v0.18", "  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);")
rep("  { const dt = Math.max(0, Math.min(0.1, now - lastDecalT)); lastDecalT = now; drawDecals(dt); }   // v0.18\n",
    "  { const dt = Math.max(0, Math.min(0.1, now - lastDecalT)); lastDecalT = now; drawScars(dt, now); }   // v0.18.1\n")
rep("  if (!f._s && (f.big || HEAVY[f.vis]) && Math.random() < 0.5) addDecal(f.x, f.y + 2, HEAVY[f.vis] ? 12 : 7, f.el, 2.2);   // v0.18\n", "")
# the delayed explosion tells the drawer which skill it was (meteor / aftershock / contagion)
rep("const c = forkChain(g, z.ctx, 'Zone'); addFx(g, { type: 'nova', x: z.x, y: z.y, r: z.r, dur: 0.35, color: ELEMENTS[z.el].color, skill: true });",
    "const c = forkChain(g, z.ctx, 'Zone'); addFx(g, { type: 'nova', x: z.x, y: z.y, r: z.r, dur: 0.35, color: ELEMENTS[z.el].color, skill: true, vis: z.skill, after: true });")
rep("      addFx(g, { type: 'nova', x: cx, y: cy, r, dur: 0.25, color: '#c8a070' });",
    "      addFx(g, { type: 'nova', x: cx, y: cy, r, dur: 0.25, color: '#c8a070', ground: skillId });")

GROUND = r"""
// ---------------- v0.18.1 physical effects: fissures, craters, rocks, dust, wind, elemental ground marks ----------------
const PUFF = new Map();
function puffSprite(col) { let c = PUFF.get(col); if (c) return c; c = document.createElement('canvas'); c.width = c.height = 32; const x = c.getContext('2d'), gr = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  gr.addColorStop(0, rgba(col, 0.9)); gr.addColorStop(0.5, rgba(col, 0.5)); gr.addColorStop(1, rgba(col, 0)); x.fillStyle = gr; x.fillRect(0, 0, 32, 32); PUFF.set(col, c); return c; }
const GFX = { scars: [], rocks: [], dust: [], g: null };
function gfxReset() { if (GFX.g !== g) { GFX.g = g; GFX.scars.length = 0; GFX.rocks.length = 0; GFX.dust.length = 0; } }
const RND = () => Math.random();
function crackBranch(x, y, ang, L, w, bend) { const pts = [[x, y]]; let cx = x, cy = y, a = ang; const seg = Math.max(2, Math.round(L / 11));
  for (let s = 1; s <= seg; s++) { a = ang + (RND() - 0.5) * (bend || 0.55) * 1.6; cx += Math.cos(a) * L / seg; cy += Math.sin(a) * L / seg * 0.82; pts.push([cx, cy]); } return { pts, w, a }; }
function mkFissure(x, y, R, o) {   // o: { a0, a1, n, w, lava, crater, slabs, life }
  o = o || {}; const n = o.n || 7, br = [];
  for (let i = 0; i < n; i++) {
    const a = o.a0 != null ? o.a0 + (o.a1 - o.a0) * (n > 1 ? i / (n - 1) : 0.5) + (RND() - 0.5) * 0.25 : i / n * 6.283 + RND() * 0.6;
    const b = crackBranch(x + Math.cos(a) * (o.crater ? R * 0.18 : 2), y + Math.sin(a) * (o.crater ? R * 0.15 : 2), a, R * (0.55 + 0.5 * RND()), (o.w || 4) * (0.7 + 0.6 * RND())); br.push(b);
    const k = 1 + Math.floor(RND() * (b.pts.length - 2));   // side branches
    if (RND() < 0.45) { const p0 = b.pts[k]; br.push(crackBranch(p0[0], p0[1], a + (RND() < 0.5 ? 1 : -1) * (0.45 + RND() * 0.4), R * (0.18 + 0.2 * RND()), b.w * 0.5, 0.5)); }
  }
  const slabs = []; for (let i = 0; i < (o.slabs || 0); i++) { const a = RND() * 6.283, d = R * (0.2 + 0.3 * RND()), s = 3 + RND() * 4, t = RND() * 6.283;
    slabs.push({ x: x + Math.cos(a) * d, y: y + Math.sin(a) * d * 0.82, pts: [0, 1, 2, 3].map((j) => { const q = t + j * 1.571 + (RND() - 0.5) * 0.6, r = s * (0.7 + 0.5 * RND()); return [Math.cos(q) * r, Math.sin(q) * r * 0.75]; }), lift: 1 + RND() * 2 }); }
  return { kind: 'fissure', x, y, R, br, slabs, t: 0, life: o.life || 3.6, grow: o.grow || 0.14, lava: !!o.lava, crater: o.crater || 0 };
}
function addScar(s) { gfxReset(); if (GFX.scars.length > 26) GFX.scars.shift(); GFX.scars.push(s); return s; }
function addRocks(x, y, n, R, cols, up) { if (opts.reduceFx) return; gfxReset(); for (let i = 0; i < n && GFX.rocks.length < 140; i++) { const a = RND() * 6.283, sp = (R || 60) * (0.5 + RND());
  GFX.rocks.push({ x: x + Math.cos(a) * 4, y: y + Math.sin(a) * 3, z: 2, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp * 0.8, vz: (up || 120) * (0.6 + 0.7 * RND()), r: 1.4 + RND() * 2.4, rot: RND() * 6.283, vr: (RND() - 0.5) * 14, col: cols[i % cols.length], t: 0, life: 1.6 + RND() * 0.8, b: 0, seed: RND() }); } }
function addDust(x, y, n, R, col, o) { if (opts.reduceFx) return; gfxReset(); o = o || {}; for (let i = 0; i < n && GFX.dust.length < 160; i++) { const a = o.ang != null ? o.ang + (RND() - 0.5) * (o.spread || 1) : RND() * 6.283, d = (o.ring ? R : R * 0.3 * RND()), sp = (o.sp || 40) * (0.5 + RND());
  GFX.dust.push({ x: x + Math.cos(a) * d, y: y + Math.sin(a) * d * 0.8, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp * 0.7 - (o.rise || 6), r: (o.r || 6) * (0.7 + 0.6 * RND()), gr: (o.r || 6) * 1.6, t: 0, life: (o.life || 0.9) * (0.7 + 0.6 * RND()), col: col || '#8a7a68', a: o.a || 0.45 }); } }
function taper(pts, w, upto) {   // polygon around a polyline, thick at the start, sharp at the tip
  const n = pts.length, m = Math.max(2, Math.min(n, upto)); const L = [], Rr = [];
  for (let i = 0; i < m; i++) { const p = pts[i], q = pts[Math.min(n - 1, i + 1)], o = pts[Math.max(0, i - 1)]; let dx = q[0] - o[0], dy = q[1] - o[1]; const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
    const ww = w * Math.pow(1 - i / (n - 1), 0.75) * (i === 0 ? 0.8 : 1) / 2; L.push([p[0] - dy * ww, p[1] + dx * ww]); Rr.push([p[0] + dy * ww, p[1] - dx * ww]); }
  return { L, R: Rr };
}
function drawFissure(s, now) {
  const k = Math.min(1, s.t / s.grow), fade = Math.min(1, (s.life - s.t) / 0.9);
  if (s.crater) {   // dished crater: dark bowl, lit lower rim, shadowed upper rim
    const cr = s.crater * (0.6 + 0.4 * k); ctx.globalAlpha = 0.75 * fade; const gr = ctx.createRadialGradient(s.x, s.y + 1, 0, s.x, s.y, cr);
    gr.addColorStop(0, s.lava ? '#3a1408' : '#0b0807'); gr.addColorStop(0.7, s.lava ? 'rgba(40,14,6,0.7)' : 'rgba(14,10,9,0.65)'); gr.addColorStop(1, 'rgba(14,10,9,0)');
    ctx.fillStyle = gr; ctx.beginPath(); ctx.ellipse(s.x, s.y, cr, cr * 0.72, 0, 0, 6.283); ctx.fill();
    ctx.lineWidth = 1.5; ctx.strokeStyle = rgba('#8c7a64', 0.7 * fade); ctx.beginPath(); ctx.ellipse(s.x, s.y, cr * 0.8, cr * 0.58, 0, 0.2, 2.94); ctx.stroke();
    ctx.strokeStyle = rgba('#000000', 0.55 * fade); ctx.beginPath(); ctx.ellipse(s.x, s.y, cr * 0.8, cr * 0.58, 0, 3.34, 6.08); ctx.stroke();
  }
  for (const b of s.br) { const upto = Math.ceil(b.pts.length * k); if (upto < 2) continue; const T = taper(b.pts, b.w, upto);
    ctx.globalAlpha = 0.9 * fade; ctx.fillStyle = '#070505'; ctx.beginPath(); T.L.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); for (let i = T.R.length - 1; i >= 0; i--) ctx.lineTo(T.R[i][0], T.R[i][1]); ctx.closePath(); ctx.fill();
    ctx.lineWidth = 1; ctx.strokeStyle = rgba('#9a8770', 0.55 * fade); ctx.beginPath(); T.R.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1] + 0.8) : ctx.moveTo(p[0], p[1] + 0.8))); ctx.stroke();   // lit lip
    if (s.lava) { const pul = 0.55 + 0.35 * Math.sin(now * 7 + b.w * 3); ctx.strokeStyle = rgba('#ff5a1a', pul * fade); ctx.lineWidth = Math.max(1, b.w * 0.35); ctx.beginPath(); b.pts.slice(0, upto).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
      ctx.strokeStyle = rgba('#ffd23f', pul * 0.7 * fade); ctx.lineWidth = 1; ctx.stroke(); }
  }
  for (const sl of s.slabs) { const lift = sl.lift * Math.min(1, s.t / 0.12) * Math.max(0, 1 - s.t / 1.6);   // chunks of floor kicked up, then settling
    ctx.globalAlpha = 0.85 * fade; ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.beginPath(); sl.pts.forEach((p, i) => (i ? ctx.lineTo(sl.x + p[0] + 1.5, sl.y + p[1] + 1.5) : ctx.moveTo(sl.x + p[0] + 1.5, sl.y + p[1] + 1.5))); ctx.fill();
    ctx.fillStyle = '#3a3242'; ctx.beginPath(); sl.pts.forEach((p, i) => (i ? ctx.lineTo(sl.x + p[0], sl.y + p[1] - lift) : ctx.moveTo(sl.x + p[0], sl.y + p[1] - lift))); ctx.fill();
    ctx.strokeStyle = '#5c5266'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(sl.x + sl.pts[2][0], sl.y + sl.pts[2][1] - lift); ctx.lineTo(sl.x + sl.pts[3][0], sl.y + sl.pts[3][1] - lift); ctx.stroke(); }
}
function crystal(x, y, h, w, lean, a) {   // faceted ice spike: lit left face, dark right face
  const tx = x + lean, ty = y - h; ctx.globalAlpha = a;
  ctx.fillStyle = '#d8f4ff'; ctx.beginPath(); ctx.moveTo(x - w, y); ctx.lineTo(tx, ty); ctx.lineTo(x, y + 1); ctx.fill();
  ctx.fillStyle = '#4aa8e8'; ctx.beginPath(); ctx.moveTo(x + w, y); ctx.lineTo(tx, ty); ctx.lineTo(x, y + 1); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 0.6; ctx.beginPath(); ctx.moveTo(x, y + 1); ctx.lineTo(tx, ty); ctx.stroke();
}
function mkPatch(kind, x, y, R, life) { const pts = []; for (let j = 0; j < 12; j++) pts.push(0.7 + 0.3 * RND()); const items = []; for (let i = 0; i < (kind === 'frost' ? 7 : 6); i++) { const a = RND() * 6.283, d = R * (0.25 + 0.6 * RND()); items.push({ x: x + Math.cos(a) * d, y: y + Math.sin(a) * d * 0.75, s: 0.6 + 0.6 * RND(), p: RND() * 6 }); }
  return { kind, x, y, R, pts, items, t: 0, life: life || 3 }; }
function drawPatch(s, now) {
  const fade = Math.min(1, (s.life - s.t) / 0.8), grow = Math.min(1, s.t / 0.12);
  const blob = (r, col, a) => { ctx.globalAlpha = a; ctx.fillStyle = col; ctx.beginPath(); s.pts.forEach((m, j) => { const q = j / s.pts.length * 6.283; const X = s.x + Math.cos(q) * r * m, Y = s.y + Math.sin(q) * r * m * 0.72; j ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); }); ctx.closePath(); ctx.fill(); };
  if (s.kind === 'scorch') { blob(s.R * grow, '#120806', 0.55 * fade); blob(s.R * 0.6 * grow, '#050302', 0.4 * fade);
    for (const it of s.items) { const on = Math.sin(now * 9 + it.p) > -0.2 && s.t < s.life * 0.7; if (!on) continue; ctx.globalAlpha = fade * (1 - s.t / s.life); ctx.fillStyle = it.p > 3 ? '#ff8a3c' : '#ffd23f'; ctx.fillRect(Math.round(it.x), Math.round(it.y), 1, 1); }
    if (s.t < 1.4 && RND() < 0.25 && !opts.reduceFx) addDust(s.x + (RND() - 0.5) * s.R, s.y + (RND() - 0.5) * s.R * 0.6, 1, 0, '#3a3236', { sp: 4, rise: 14, r: 4, life: 1.2, a: 0.35 }); }
  else if (s.kind === 'frost') { const melt = s.t > s.life - 1 ? (s.life - s.t) : 1; blob(s.R * grow, '#cfefff', 0.16 * fade); blob(s.R * 0.7 * grow, '#ffffff', 0.12 * fade); for (const it of s.items) { ctx.globalAlpha = 0.7 * fade; ctx.fillStyle = '#ffffff'; ctx.fillRect(Math.round(it.x + 4), Math.round(it.y + 2), 1, 1); ctx.fillRect(Math.round(it.x - 3), Math.round(it.y - 1), 1, 1); }
    for (const it of s.items) crystal(it.x, it.y, 9 * it.s * grow * melt, 2.4 * it.s, (it.p - 3) * 0.8, 0.95 * fade); }
  else if (s.kind === 'acid') { blob(s.R * grow, '#1f5a14', 0.5 * fade); blob(s.R * 0.8 * grow, '#4fbf2a', 0.25 * fade);
    for (const it of s.items) { const ph = (now * 1.3 + it.p) % 1; ctx.globalAlpha = (1 - ph) * fade; ctx.strokeStyle = '#b8ff8a'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(it.x, it.y, 1 + ph * 3 * it.s, 0, 6.283); ctx.stroke(); } }
}
function drawScars(dt, now) {   // under enemies
  gfxReset(); const S = GFX.scars;
  for (let i = S.length - 1; i >= 0; i--) { const s = S[i]; s.t += dt; if (s.t >= s.life) S.splice(i, 1); }
  for (const s of S) { if (s.kind === 'fissure') drawFissure(s, now); else drawPatch(s, now); }
  for (const z of g.zones) if (!z.dead && z.kind === 'delayed' && z.skill === 'skill.earthquake') {   // aftershock telegraph: the ground splits open bit by bit
    if (!z._fis) z._fis = mkFissure(z.x, z.y, z.r, { n: 6, w: 3, life: 99, grow: 1 }); const pr = Math.min(1, z.t / (z.delay || 1)); z._fis.t = pr * 0.8; drawFissure(z._fis, now); }
  ctx.globalAlpha = 1;
}
function groundTop(now) {   // rocks (with height + shadow) and dust, over everything on the ground
  gfxReset(); const dt = Math.max(0, Math.min(0.05, now - (GFX.lt == null ? now : GFX.lt))); GFX.lt = now;
  if (g._vortex && g.t < g._vortex.until && !opts.reduceFx) { const V = g._vortex, p = g.player; windFunnel(p.x, p.y + V.r * 0.3, V.r * 1.1, now, Math.min(1, (V.until - g.t) / 0.15), 6); }
  const Rk = GFX.rocks; for (let i = Rk.length - 1; i >= 0; i--) { const r = Rk[i]; r.t += dt; if (r.t >= r.life) { Rk.splice(i, 1); continue; }
    if (r.b < 3) { r.vz -= 520 * dt; r.z += r.vz * dt; r.x += r.vx * dt; r.y += r.vy * dt; r.rot += r.vr * dt; if (r.z <= 0) { r.z = 0; r.b++; r.vz = -r.vz * 0.32; r.vx *= 0.5; r.vy *= 0.5; r.vr *= 0.5; if (r.b >= 3) r.vz = 0; } }
    const a = Math.min(1, (r.life - r.t) / 0.5); ctx.globalAlpha = 0.35 * a; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(r.x, r.y + 1, r.r * (1 - Math.min(0.6, r.z / 60)), r.r * 0.45, 0, 0, 6.283); ctx.fill();
    ctx.globalAlpha = a; ctx.save(); ctx.translate(r.x, r.y - r.z); ctx.rotate(r.rot); ctx.fillStyle = r.col; ctx.beginPath(); ctx.moveTo(-r.r, -r.r * 0.3); ctx.lineTo(-r.r * 0.2, -r.r); ctx.lineTo(r.r, -r.r * 0.4); ctx.lineTo(r.r * 0.7, r.r * 0.8); ctx.lineTo(-r.r * 0.6, r.r * 0.7); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.beginPath(); ctx.moveTo(-r.r, -r.r * 0.3); ctx.lineTo(-r.r * 0.2, -r.r); ctx.lineTo(r.r * 0.2, -r.r * 0.2); ctx.closePath(); ctx.fill(); ctx.restore(); }
  const Du = GFX.dust; for (let i = Du.length - 1; i >= 0; i--) { const d = Du[i]; d.t += dt; if (d.t >= d.life) { Du.splice(i, 1); continue; }
    const q = d.t / d.life; d.x += d.vx * dt; d.y += d.vy * dt; d.vx *= 1 - 2.5 * dt; d.vy *= 1 - 2.5 * dt; const r = d.r + (d.gr - d.r) * q;
    ctx.globalAlpha = d.a * (1 - q) * Math.min(1, d.t / 0.06); ctx.drawImage(puffSprite(d.col), d.x - r, d.y - r, r * 2, r * 2); }
  ctx.globalAlpha = 1;
}
function windRibbon(x, y, rx, ry, a0, span, th, col, al) {   // a tapered band of wind following an ellipse
  const n = 12; ctx.globalAlpha = al; ctx.fillStyle = col; ctx.beginPath();
  for (let i = 0; i <= n; i++) { const t = i / n, a = a0 + span * t; ctx.lineTo(x + Math.cos(a) * rx, y + Math.sin(a) * ry); }
  for (let i = n; i >= 0; i--) { const t = i / n, a = a0 + span * t, w = th * Math.sin(Math.PI * t); ctx.lineTo(x + Math.cos(a) * (rx - w), y + Math.sin(a) * (ry - w * 0.4) - w * 0.35); }
  ctx.closePath(); ctx.fill();
}
function windFunnel(x, y, r, now, a, layers, tint) {   // a whirlwind: ground dust skirt, stacked spinning wind bands widening upward, grit pulled up
  if (a <= 0.01) return; const col = tint || '#e6edf7';
  for (let i = 0; i < 9; i++) { const q = now * 6.5 + i * 0.698, X = x + Math.cos(q) * r * 0.92, Y = y + Math.sin(q) * r * 0.32; ctx.globalAlpha = 0.28 * a; ctx.drawImage(puffSprite('#8a7a68'), X - 7, Y - 5, 14, 10); }
  for (let k = 0; k < layers; k++) { const hgt = k * r * 0.22, rx = r * (0.42 + 0.15 * k), ry = rx * 0.34, sp = 11 - k * 1.3;
    for (let j = 0; j < 2; j++) { const a0 = -now * sp + j * Math.PI + k * 0.9, mid = Math.sin(a0 + 1.2), front = mid > 0;
      windRibbon(x, y - hgt, rx, ry, a0, 2.3, 2.6 + k * 0.8, j ? '#ffffff' : col, a * (front ? 0.7 : 0.3) * (1 - k / (layers + 3))); } }
  for (let i = 0; i < 14; i++) { const ph = (now * 0.9 + hsh(i * 17 + 3)) % 1, q = -now * (8 + (i % 3)) + i * 1.7, rad = r * (0.35 + 0.75 * ph);
    const X = x + Math.cos(q) * rad, Y = y + Math.sin(q) * rad * 0.34 - ph * r * 0.85; ctx.globalAlpha = a * (1 - ph) * 0.9; ctx.fillStyle = i % 3 === 0 ? '#c8a070' : i % 3 === 1 ? '#6e8a4a' : '#d8dce8'; ctx.fillRect(Math.round(X), Math.round(Y), i % 2 ? 2 : 1, 1); }
  for (let i = 0; i < 3; i++) { const q = -now * 13 + i * 2.09; ctx.globalAlpha = 0.6 * a; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(x, y - r * 0.3, r * 1.02, r * 0.38, 0, q, q + 0.6); ctx.stroke(); }
  ctx.globalAlpha = 1;
}
const ROCK_COLS = ['#5a4a3a', '#7a6650', '#3e342c', '#8a7860'];
function groundHook(f) {   // runs once per fx: spawns the physical leftovers of a skill
  if (f._gh) return; f._gh = 1; if (opts.reduceFx) return; const v = f.vis;
  if (f.type === 'cleave') {
    if (v === 'skill.earthquake') { addScar(mkFissure(f.x, f.y, f.r * 1.15, { n: 6, w: 7, crater: f.r * 0.45, slabs: 6 })); addRocks(f.x, f.y, 10, 70, ROCK_COLS, 140); addDust(f.x, f.y, 12, f.r * 0.7, '#8a7a68', { ring: 1, sp: 50, r: 7, life: 1.1 }); g.shake = Math.max(g.shake || 0, 3); }
    else if (v === 'skill.ground_slam') { addScar(mkFissure(f.x, f.y, f.r * 1.2, { a0: f.ang - f.half * 0.8, a1: f.ang + f.half * 0.8, n: 5, w: 5, slabs: 4 })); const cx = f.x + Math.cos(f.ang) * f.r * 0.5, cy = f.y + Math.sin(f.ang) * f.r * 0.5;
      addRocks(cx, cy, 9, 80, ROCK_COLS, 120); addDust(cx, cy, 10, f.r * 0.4, '#8a7a68', { ang: f.ang, spread: f.half * 2, sp: 70, r: 7 }); }
    else if (v === 'skill.leap_slam') { addScar(mkFissure(f.x, f.y, f.r, { n: 7, w: 4, crater: f.r * 0.5, slabs: 5 })); addRocks(f.x, f.y, 8, 60, ROCK_COLS, 130); addDust(f.x, f.y, 14, f.r * 0.8, '#8a7a68', { ring: 1, sp: 60, r: 7 }); }
    else if (v === 'skill.heavy_strike') { const cx = f.x + Math.cos(f.ang) * f.r * 0.6, cy = f.y + Math.sin(f.ang) * f.r * 0.6; addScar(mkFissure(cx, cy, 16, { n: 4, w: 3, crater: 7, life: 2.4 })); addRocks(cx, cy, 5, 50, ROCK_COLS, 100); addDust(cx, cy, 5, 4, '#8a7a68', { sp: 30, r: 5 }); }
    else if (v === 'skill.infernal_blow') { const cx = f.x + Math.cos(f.ang) * f.r * 0.6, cy = f.y + Math.sin(f.ang) * f.r * 0.6; addScar(mkPatch('scorch', cx, cy, f.r * 0.5, 2.6)); addDust(cx, cy, 6, 6, '#3a3236', { sp: 20, rise: 20, r: 6, life: 1.2, a: 0.4 }); }
    else if (v === 'skill.cyclone') { g._vortex = { until: g.t + 0.32, r: f.r }; }
    else if (v === 'skill.frost_blades' || v === 'skill.venom_slash') { /* blade skills keep their swing */ }
  } else if (f.type === 'nova') {
    if (f.ground) { addDust(f.x, f.y, 12, f.r * 0.85, '#8a7a68', { ring: 1, sp: 45, r: 7, life: 0.9 }); }
    else if (v === 'skill.earthquake' && f.after) { addScar(mkFissure(f.x, f.y, f.r * 1.1, { n: 8, w: 9, crater: f.r * 0.35, slabs: 9, life: 4.5 })); addRocks(f.x, f.y, 16, 90, ROCK_COLS, 170); addDust(f.x, f.y, 18, f.r * 0.8, '#8a7a68', { ring: 1, sp: 60, r: 9, life: 1.3 }); g.shake = Math.max(g.shake || 0, 5); }
    else if (v === 'skill.meteor') { addScar(mkFissure(f.x, f.y, f.r * 0.95, { n: 7, w: 4, crater: f.r * 0.55, lava: true, slabs: 4, life: 4 })); addScar(mkPatch('scorch', f.x, f.y, f.r * 0.8, 4)); addRocks(f.x, f.y, 12, 90, ['#2a1c14', '#5a2a14', '#ff6a2a'], 160); addDust(f.x, f.y, 14, f.r * 0.6, '#2e2628', { ring: 1, sp: 40, rise: 18, r: 9, life: 1.6, a: 0.5 }); }
    else if (f.skill && !f.danger) { const el = ELEM_BY_COLOR[f.color]; if (f.r < 24) return;
      if (el === 'fire') { addScar(mkPatch('scorch', f.x, f.y, f.r * 0.6, 2.8)); addDust(f.x, f.y, 6, f.r * 0.3, '#3a3236', { sp: 20, rise: 18, r: 7, life: 1.2, a: 0.4 }); }
      else if (el === 'cold') addScar(mkPatch('frost', f.x, f.y, f.r * 0.7, 2.6));
      else if (el === 'poison') addScar(mkPatch('acid', f.x, f.y, f.r * 0.6, 3)); }
  }
}
"""
rep("function drawFx(now) {\n  let labels = [];\n  for (const f of g.fx) {\n    const q = f.t / f.dur;\n",
    GROUND + "function drawFx(now) {\n  let labels = [];\n  for (const f of g.fx) {\n    const q = f.t / f.dur;\n    groundHook(f);   // v0.18.1\n    if (f.type === 'nova' && (f.ground || (f.after && f.vis === 'skill.earthquake')) && !opts.reduceFx) continue;   // v0.18.1 the landing ring is now dust\n")
# per-skill swings that were just line patterns: let the ground do the talking, keep a short weapon arc
rep("  'skill.cyclone': (f, q, now) => {", "  'skill.cyclone': (f, q, now) => { return true; },   // v0.18.1 the whirlwind is drawn around the player (groundTop)\n  'skill.cyclone_old': (f, q, now) => {")
rep("  'skill.earthquake': (f, q) => {", "  'skill.earthquake': (f, q) => { ctx.globalAlpha = 1 - q; ctx.strokeStyle = '#e8dcc8'; ctx.lineWidth = 3 * (1 - q); ctx.beginPath(); ctx.ellipse(f.x, f.y - 6 + q * 6, 10, 4, 0, 3.4, 6.0); ctx.stroke(); ctx.globalAlpha = 1; return true; },   // v0.18.1 weapon impact only; fissure in groundHook\n  'skill.earthquake_old': (f, q) => {")
rep("  'skill.leap_slam': (f, q) => {", "  'skill.leap_slam': (f, q) => { return true; },   // v0.18.1\n  'skill.leap_slam_old': (f, q) => {")
rep("  'skill.ground_slam': (f, q) => {", "  'skill.ground_slam': (f, q) => { return true; },   // v0.18.1\n  'skill.ground_slam_old': (f, q) => {")
rep("  'skill.whirl_cleave': (f, q) => {",
    "  'skill.whirl_cleave': (f, q, now) => { windFunnel(f.x, f.y + 2, f.r * 0.95, now, 1 - q, 3); const sw = -6.283 * Math.min(1, q * 1.6); for (let i = 0; i < 2; i++) windRibbon(f.x, f.y - 3, f.r, f.r * 0.42, sw - 1.6 + i * 3.14, 1.6, 4, '#ffffff', (1 - q) * 0.8); ctx.globalAlpha = 1; return true; },   // v0.18.1 a single spinning gust\n  'skill.whirl_cleave_old': (f, q) => {")
# tornado shot: a small travelling whirlwind
rep("Object.assign(PROJ_VFX, {\n  'skill.power_shot':",
    "Object.assign(PROJ_VFX, {\n  'skill.tornado_shot': (pr, x, y, ux, uy, now) => { windFunnel(pr.x, pr.y + 4, 12, now + pr.id, 1, 5, '#dfe8f2'); return true; },   // v0.18.1\n  'skill.power_shot':")

rep("  if (z.kind === 'delayed') {   // v0.8.1 telegraph + falling meteor / cracking ground\n",
    "  if (z.kind === 'delayed' && z.skill === 'skill.earthquake' && !opts.reduceFx) { const pr = Math.min(1, z.t / (z.delay || 1)); ctx.globalAlpha = 0.18 + 0.2 * pr; ctx.strokeStyle = '#c8a070'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(z.x, z.y, z.r, z.r * 0.8, 0, 0, 6.283); ctx.stroke(); ctx.globalAlpha = 1;   // v0.18.1 fissure drawn in drawScars\n"
    "    if (Math.random() < 0.3) addDust(z.x + (Math.random() - 0.5) * z.r * 1.4, z.y + (Math.random() - 0.5) * z.r, 1, 0, '#8a7a68', { sp: 6, rise: 4, r: 4, life: 0.6, a: 0.35 }); return; }\n"
    "  if (z.kind === 'delayed') {   // v0.8.1 telegraph + falling meteor / cracking ground\n")
rep("  'skill.frost_nova': (f, q, now) => {   // ice spikes burst out of the ground, frost floor\n",
    "  'skill.frost_nova': (f, q, now) => {   // v0.18.1 a wave of ice crystals erupts outward, cold mist rolls off\n"
    "    if (!f._c) { f._c = []; for (let i = 0; i < 26; i++) f._c.push({ a: Math.random() * 6.283, d: 0.25 + 0.75 * Math.random(), s: 0.6 + 0.7 * Math.random() }); addDust(f.x, f.y, 14, f.r * 0.8, '#dff4ff', { ring: 1, sp: 30, rise: 3, r: 8, life: 0.9, a: 0.4 }); }\n"
    "    const R = f.r * Math.min(1, q * 1.8); for (const c of f._c) { const dd = c.d * f.r; if (dd > R) continue; const age = (R - dd) / f.r; crystal(f.x + Math.cos(c.a) * dd, f.y + Math.sin(c.a) * dd * 0.78, 13 * c.s * Math.min(1, age * 5) * (1 - q * 0.5), 2.8 * c.s, Math.cos(c.a) * 3, 1 - q * 0.4); }\n"
    "    ctx.globalAlpha = 1; },\n  'skill.frost_nova_old': (f, q, now) => {\n")

# ---------------- set pieces / legendaries get random affixes ----------------
rep("  legendary: { id: 'legendary', name: tr('傳奇'), en: 'Legendary', affixes: [1, 1], color: '#ff8a1f' },",
    "  legendary: { id: 'legendary', name: tr('傳奇'), en: 'Legendary', affixes: [2, 3], color: '#ff8a1f' },   // v0.18.1: set pieces roll 3, other legendaries 2 (plus their fixed lines)")
rep("  const n = Math.min(rng.int(rr.affixes[0], rr.affixes[1]), rr.affixes[1]);",
    "  const n = rarity === 'legendary' ? (uq && uq.set ? 3 : 2) : Math.min(rng.int(rr.affixes[0], rr.affixes[1]), rr.affixes[1]);   // v0.18.1")
TOPUP = r"""
function topUpLegendaries(s, at) {   // v0.18.1: older legendaries had 1 random line; give set pieces 3 and other legendaries 2 (deterministic per item, mid-high rolls)
  const ch = s && s.character; if (!isObj(ch)) return 0; const D0 = C.DATA, AF = D0.AFFIXES, U = D0.UNIQUES; let n = 0;
  const hs = (str) => { let x = 2166136261; for (let i = 0; i < str.length; i++) { x ^= str.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return () => { x = (Math.imul(x ^ (x >>> 15), 2246822519) + 0x9e3779b9) >>> 0; return (x % 100000) / 100000; }; };
  const fix = (it) => { if (!isObj(it) || it.rarity !== 'legendary' || !it.unique || !U[it.unique] || !Array.isArray(it.affixes)) return; const want = U[it.unique].set ? 3 : 2; if (it.affixes.length >= want) return;
    const T = Math.min(6, Math.max(1, Number.isInteger(it.ilvl) ? it.ilvl : 1)), r = hs(String(it.uid || it.unique)); const have = new Set(it.affixes.map((a) => a && a.id));
    const pool = AF.filter((a) => a.slots.indexOf(it.slot) >= 0 && (!a.minTier || T >= a.minTier) && !have.has(a.id) && !a.rareRoll); let guard = 0;
    while (it.affixes.length < want && pool.length && guard++ < 20) { const a = pool.splice(Math.floor(r() * pool.length), 1)[0]; const [lo, hi] = C.affixRange(a, T); let v = lo + (hi - lo) * (0.45 + 0.4 * r()); v = a.int ? Math.round(v) : Math.round(v * 100) / 100; it.affixes.push({ id: a.id, stat: a.stat, value: v }); n++; } };
  (isObj(ch.inventory) && Array.isArray(ch.inventory.items) ? ch.inventory.items : []).forEach(fix); if (isObj(ch.equipment)) Object.values(ch.equipment).forEach(fix);
  if (isObj(s.stash) && Array.isArray(s.stash.items)) s.stash.items.forEach(fix); if (isObj(s.progress) && isObj(s.progress.collection)) Object.values(s.progress.collection).forEach(fix);
  if (n) s.migrationLog = (Array.isArray(s.migrationLog) ? s.migrationLog : []).concat([{ at: at || null, kind: 'legendary-affixes-added', count: n, gold: 0 }]); return n;
}
"""
rep("function repairAffixRanges(s, at) {", TOPUP + "function repairAffixRanges(s, at) {")
rep("    try { if (validateSave(d).length) repairAffixRanges(d, at || now()); } catch (e) { /* validation below decides */ }",
    "    try { if (validateSave(d).length) repairAffixRanges(d, at || now()); } catch (e) { /* validation below decides */ }\n    try { topUpLegendaries(d, at || now()); } catch (e) { /* ignore */ }   // v0.18.1")

# ---------------- version ----------------
rep("<title>PROJECT: EVOLVE — 原型 0.18.0</title>", "<title>PROJECT: EVOLVE — 原型 0.18.1</title>")
rep("瀏覽器測試版 0.18.0 — 持續更新中", "瀏覽器測試版 0.18.1 — 持續更新中", 5)
rep("Browser beta 0.18.0", "Browser beta 0.18.1", 4)
rep("const VERSION = '0.18.0';", "const VERSION = '0.18.1';")
EN['瀏覽器測試版 0.18.1 — 持續更新中'] = 'Browser beta 0.18.1 — updated often'
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();", "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.18.1\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")
rep("  openStash, stashSave, stRun, ST_OPS,", "  openStash, stashSave, stRun, ST_OPS, get gfx() { return GFX; },")
open(dst, 'w', encoding='utf-8').write(h)
print('ok 181', len(h))
