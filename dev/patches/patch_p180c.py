#!/usr/bin/env python3
"""EVOLVE v0.18.0 part C: VFX overhaul. Additive light layer (cached glow sprites) over projectiles, novas, slashes, impacts,
lightning and ground zones; thick gradient shockwaves with a white core flash; filled crescent slashes; element ground
decals (scorch, frost, char, acid) that linger; a soft vignette so the light reads. Respects Options → reduce effects.
Usage: patch_p180c.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = json.load(open(src + '.en.json'))


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)


LIGHT = r"""
// ---------------- v0.18 light layer: additive glow, shockwaves, crescents, ground decals ----------------
const GLOW_CACHE = new Map();
function glowSprite(col) {   // 64×64 radial falloff, cached per colour
  let c = GLOW_CACHE.get(col); if (c) return c;
  c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, rgba(col, 1)); gr.addColorStop(0.22, rgba(col, 0.55)); gr.addColorStop(0.55, rgba(col, 0.16)); gr.addColorStop(1, rgba(col, 0));
  x.fillStyle = gr; x.fillRect(0, 0, 64, 64); GLOW_CACHE.set(col, c); return c;
}
let glowN = 0;
function glow(x, y, r, col, a) { if (glowN++ > 260 || r < 1 || a <= 0.01) return; ctx.globalAlpha = Math.min(1, a); ctx.drawImage(glowSprite(col), x - r, y - r, r * 2, r * 2); }
const DECAL = { fire: ['#1a0c06', '#ff6a2a'], cold: ['#bfe9ff', '#5ec8ff'], lightning: ['#20204a', '#b9a8ff'], poison: ['#12300c', '#8cff5a'], physical: ['#15121c', '#9fa8b8'] };
function addDecal(x, y, r, el, life) { const L = g._decals || (g._decals = []); if (L.length > 40) L.shift(); L.push({ x, y, r, el: DECAL[el] ? el : 'physical', t: 0, life: life || 3.2, seed: Math.random() * 99 }); }
function drawDecals(dt) {   // under enemies: scorched / frosted / acid ground that fades out
  const L = g._decals; if (!L || !L.length || opts.reduceFx) return;
  for (let i = L.length - 1; i >= 0; i--) { const d = L[i]; d.t += dt; if (d.t >= d.life) { L.splice(i, 1); continue; }
    const k = 1 - d.t / d.life, C = DECAL[d.el], cold = d.el === 'cold';
    ctx.globalAlpha = (cold ? 0.32 : 0.45) * k; ctx.fillStyle = C[0]; ctx.beginPath();
    for (let j = 0; j <= 14; j++) { const a = j / 14 * 6.283, rr = d.r * (0.72 + 0.28 * hsh(d.seed + j)); j ? ctx.lineTo(d.x + Math.cos(a) * rr, d.y + Math.sin(a) * rr * 0.8) : ctx.moveTo(d.x + Math.cos(a) * rr, d.y + Math.sin(a) * rr * 0.8); }
    ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 0.55 * k * k; ctx.strokeStyle = C[1]; ctx.lineWidth = 1; ctx.beginPath();   // cracks / frost lines
    for (let j = 0; j < 6; j++) { const a = d.seed + j * 1.047, r1 = d.r * (0.5 + 0.4 * hsh(d.seed * 3 + j)); ctx.moveTo(d.x + Math.cos(a) * 3, d.y + Math.sin(a) * 2.4); ctx.lineTo(d.x + Math.cos(a + 0.2) * r1 * 0.55, d.y + Math.sin(a + 0.2) * r1 * 0.44); ctx.lineTo(d.x + Math.cos(a - 0.1) * r1, d.y + Math.sin(a - 0.1) * r1 * 0.8); }
    ctx.stroke(); }
  ctx.globalAlpha = 1;
}
function shockRing(x, y, R, w, col, a) {   // thick ring: transparent → colour → white edge → colour → transparent
  if (R < 2 || a <= 0.01) return; const r0 = Math.max(0, R - w), gr = ctx.createRadialGradient(x, y, r0, x, y, R + w * 0.35);
  gr.addColorStop(0, rgba(col, 0)); gr.addColorStop(0.62, rgba(col, 0.5 * a)); gr.addColorStop(0.8, rgba('#ffffff', 0.85 * a)); gr.addColorStop(1, rgba(col, 0));
  ctx.globalAlpha = 1; ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, R + w * 0.35, 0, 6.283); ctx.fill();
}
function crescent(x, y, r, a0, a1, th, col, a) {   // filled moon-shaped blade: thick in the middle, sharp at both tips
  if (a <= 0.01 || a1 <= a0) return; const n = 14; ctx.globalAlpha = a; ctx.fillStyle = col; ctx.beginPath();
  for (let i = 0; i <= n; i++) { const t = i / n, an = a0 + (a1 - a0) * t; ctx.lineTo(x + Math.cos(an) * r, y + Math.sin(an) * r); }
  for (let i = n; i >= 0; i--) { const t = i / n, an = a0 + (a1 - a0) * t, rr = r - th * Math.sin(Math.PI * t); ctx.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr); }
  ctx.closePath(); ctx.fill();
}
function fxColor(f) { return f.color || (f.el && D.ELEMENTS[f.el] ? D.ELEMENTS[f.el].color : '#ffffff'); }
function lightLayer(now) {   // drawn after the normal fx with 'lighter' so colours add up into light
  if (opts.reduceFx) return; glowN = 0; ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const z of g.zones) if (!z.dead && z.r) { const col = z.kind === 'burning' ? '#ff6a2a' : (D.ELEMENTS[z.el] || D.ELEMENTS.physical).color; glow(z.x, z.y, z.r * 1.25, col, 0.16 + 0.05 * Math.sin(now * 5 + z.id)); }
  for (const pr of g.projectiles) { const col = (D.ELEMENTS[pr.el] || D.ELEMENTS.physical).color, sp = Math.hypot(pr.vx, pr.vy) || 1, ux = pr.vx / sp, uy = pr.vy / sp, big = (pr.r || 3) > 4 ? 1.4 : 1;
    glow(pr.x, pr.y, 13 * big, col, 0.55); glow(pr.x, pr.y, 4 * big, '#ffffff', 0.5);
    for (let i = 1; i <= 4; i++) glow(pr.x - ux * i * 5, pr.y - uy * i * 5, (9 - i * 1.4) * big, col, 0.3 - i * 0.06); }
  for (const f of g.fx) { const q = f.t / f.dur, col = fxColor(f);
    if (f.type === 'nova' && !f.danger) { const R = f.r * (0.3 + 0.7 * Math.pow(q, 0.6)), el = ELEM_BY_COLOR[f.color] || 'physical';
      if (!f._dec && f.skill && f.r >= 30) { f._dec = 1; addDecal(f.x, f.y, f.r * 0.6, el, 3.4); }
      if (q < 0.35) glow(f.x, f.y, f.r * (0.55 + q), '#ffffff', (0.35 - q) * 2.2);   // core flash
      glow(f.x, f.y, f.r * 1.1, col, (1 - q) * 0.45); ctx.globalCompositeOperation = 'lighter'; shockRing(f.x, f.y, R, Math.max(6, f.r * 0.22) * (1 - q * 0.5), col, 1 - q); }
    else if (f.type === 'impact') { const P = (f.crit ? 1.6 : 1) * (f.big ? 1.3 : 1); glow(f.x, f.y, 14 * P * (1 - q * 0.5), col, (1 - q) * 0.75); if (q < 0.4) glow(f.x, f.y, 6 * P, '#ffffff', 0.8 - q * 2); if (f.crit && q < 0.6) shockRing(f.x, f.y, 6 + q * 22, 5, col, 1 - q / 0.6); }
    else if (f.type === 'cleave') { const el = ELEM_BY_COLOR[f.color] || 'physical', a0 = f.ang - f.half, a1 = f.ang + f.half, sweep = a0 + (a1 - a0) * Math.min(1, q * 2.2), tail = Math.max(a0, sweep - (a1 - a0) * 0.75), th = Math.max(5, f.r * 0.32);
      crescent(f.x, f.y, f.r + 2, tail, sweep, th, rgba(EL_GLOW[el] === '#ffffff' ? (f.color || '#e8e8e8') : f.color || '#e8e8e8', 1), (1 - q) * 0.55);
      crescent(f.x, f.y, f.r + 1, Math.max(tail, sweep - 0.45), sweep, th * 0.45, '#ffffff', (1 - q) * 0.8);
      glow(f.x + Math.cos(sweep) * f.r * 0.85, f.y + Math.sin(sweep) * f.r * 0.85, 12, col, (1 - q) * 0.7); }
    else if (f.type === 'lightning' && f.pts && f.pts.length) { for (const pt of f.pts) glow(pt[0], pt[1], f.star ? 16 : 11, col, (1 - q) * 0.6); const e = f.pts[f.pts.length - 1]; if (!f._dec) { f._dec = 1; addDecal(e[0], e[1], 9, 'lightning', 1.6); } }
    else if (f.type === 'castflash') glow(f.x, f.y, (f.small ? 10 : 16) * (1 + q), col, (1 - q) * 0.6);
    else if (f.type === 'spark') glow(f.x, f.y, 7, col, (1 - q) * 0.5);
    else if (f.type === 'death' && f.elite) glow(f.x, f.y, 26, '#c77dff', (1 - q) * 0.6); }
  for (const m of g.minions || []) if (!m.dead) glow(m.x, m.y, 10, '#7dfcff', 0.18);
  if (g.player && g.player.invuln > 0) glow(g.player.x, g.player.y - 2, 14, '#7dfcff', 0.25);
  ctx.restore(); ctx.globalAlpha = 1;
}
let VIGNETTE = null, VIG_KEY = '';
function drawVignette() {   // in screen space: darker edges so the light layer pops
  if (opts.reduceFx) return; const key = VW + 'x' + VH;
  if (VIG_KEY !== key) { VIG_KEY = key; VIGNETTE = document.createElement('canvas'); VIGNETTE.width = 256; VIGNETTE.height = 256; const x = VIGNETTE.getContext('2d'), gr = x.createRadialGradient(128, 128, 60, 128, 128, 182);
    gr.addColorStop(0, 'rgba(4,3,10,0)'); gr.addColorStop(1, 'rgba(4,3,10,0.55)'); x.fillStyle = gr; x.fillRect(0, 0, 256, 256); }
  ctx.globalAlpha = 1; ctx.drawImage(VIGNETTE, 0, 0, VW, VH);
}
let lastDecalT = 0;
"""
rep("function render() {\n  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);", LIGHT + "function render() {\n  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);")
rep("  for (const h of g.hazards) drawHazard(h, now);\n  for (const k of g.pickups) if (!k.dead) drawPickup(k, now);",
    "  { const dt = Math.max(0, Math.min(0.1, now - lastDecalT)); lastDecalT = now; drawDecals(dt); }   // v0.18\n"
    "  for (const h of g.hazards) drawHazard(h, now);\n  for (const k of g.pickups) if (!k.dead) drawPickup(k, now);")
rep("  drawFx(now);\n  drawParts(now);   // v0.15.1\n",
    "  drawFx(now);\n  lightLayer(now);   // v0.18\n  drawParts(now);   // v0.15.1\n")
rep("  for (const h of g.hazards) if (h.kind === 'aimline' && h.owner && !h.owner.dead) drawExclaim(h.owner.x, h.owner.y - h.owner.r - 8, h.dur - h.t < 0.2);\n  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);",
    "  for (const h of g.hazards) if (h.kind === 'aimline' && h.owner && !h.owner.dead) drawExclaim(h.owner.x, h.owner.y - h.owner.r - 8, h.dur - h.t < 0.2);\n  ctx.setTransform(BASE, 0, 0, BASE, 0, 0);\n  drawVignette();   // v0.18")
# impact decals for heavy hits, plus a few extra heavier sparks
rep("function impactFx(f, q) {\n  if (!f._s) { f._s = 1;",
    "function impactFx(f, q) {\n  if (!f._s && (f.big || HEAVY[f.vis]) && Math.random() < 0.5) addDecal(f.x, f.y + 2, HEAVY[f.vis] ? 12 : 7, f.el, 2.2);   // v0.18\n  if (!f._s) { f._s = 1;")
rep("  openStash, stashSave, stRun, ST_OPS,", "  openStash, stashSave, stRun, ST_OPS, glowSprite, commitVillage, renderZones, get decals() { return g && g._decals; },")
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok C vfx', len(h))
