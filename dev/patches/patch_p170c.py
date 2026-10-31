#!/usr/bin/env python3
"""EVOLVE v0.17.0 part C: looks — gear materials by item level (doll + icons), legendary sparkle, per-skill VFX for the skills
that only had generic effects, per-skill cast sounds. Usage: patch_p170c.py in.html out.html"""
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


# ---------------- materials by item level ----------------
MAT = r"""
// v0.17 gear materials by item level: 1 iron / leather · 2 bronze · 3 frost silver · 4 void · 5 ancient gold · 6 primal crimson
const TIER_MAT = { 2: '#d08a48', 3: '#9fe0ff', 4: '#a678ff', 5: '#ffd23f', 6: '#ff4a6e' };
const TIER_NAME = { 1: tr('鐵'), 2: tr('青銅'), 3: tr('霜銀'), 4: tr('虛空'), 5: tr('遠古'), 6: tr('太古') };
function hexMix(a, b, t) { const p = (h) => { h = h.replace('#', ''); if (h.length === 3) h = h.split('').map((c) => c + c).join(''); const n = parseInt(h, 16); return [n >> 16, (n >> 8) & 255, n & 255]; };
  if (!/^#/.test(a) || !/^#/.test(b)) return a; const A = p(a), B = p(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); }
function tierTint(col, tier, amt) { const m = TIER_MAT[tier]; return m && col && col[0] === '#' ? hexMix(col, m, amt == null ? 0.45 : amt) : col; }
"""
rep("function itemIconURL(baseId, rarity, variant) {", MAT + "function itemIconURL(baseId, rarity, variant) {")
# icons: tint every non-outline colour by the tier, add a tier pip row; variant now always carries the item level
rep("    const [uq, gr] = variant.split('|'); if (uq) { const U = D.UNIQUES[uq]; pal.g = U && U.set ? '#5ef2a0' : uniqueAccent(uq); if (U && !U.set) pal.c = '#fff6c0'; }",
    "    const [uq, gr] = variant.split('|'); if (uq) { const U = D.UNIQUES[uq]; pal.g = U && U.set ? '#5ef2a0' : uniqueAccent(uq); if (U && !U.set) pal.c = '#fff6c0'; }\n"
    "    const tier = +gr || 1; if (tier >= 2) for (const k in pal) if (k !== 'k' && k !== 'g' && k !== 'c') pal[k] = tierTint(pal[k], tier, 0.5);   // v0.17 material")
rep("    if (gr === '5' || gr === '6') { x.fillStyle = gr === '6' ? '#ff4a6e' : '#ffd23f';",
    "    if (tier >= 2 && tier <= 4) { x.fillStyle = TIER_MAT[tier]; for (let i = 0; i < tier - 1; i++) x.fillRect(11, 11 - i * 2, 1, 1); }   // tier pips\n"
    "    if (gr === '5' || gr === '6') { x.fillStyle = gr === '6' ? '#ff4a6e' : '#ffd23f';")
rep("function itemVariant(it) { return (it.unique || '') + '|' + (it.ilvl >= 5 ? it.ilvl : ''); }",
    "function itemVariant(it) { return (it.unique || '') + '|' + (it.ilvl > 1 ? it.ilvl : ''); }   // v0.17: every item level has its own look")
# doll: key includes item level + unique, colours tinted by tier, extra pieces from tier 3 / legendary glow
rep("function dollKey(eq) { const b = (s) => (eq && eq[s] ? (C.baseOf(eq[s]) || {}).id + ':' + eq[s].rarity : '-');",
    "function dollKey(eq) { const b = (s) => (eq && eq[s] ? (C.baseOf(eq[s]) || {}).id + ':' + eq[s].rarity + ':' + (eq[s].ilvl || 1) + ':' + (eq[s].unique || '') : '-');")
rep("  const look = DOLL_BODYLOOK[bid('body')] || DOLL_BODYLOOK.none;",
    "  const tl = (s) => (eq && eq[s] ? Math.min(6, eq[s].ilvl || 1) : 1), uqc = (s) => (eq && eq[s] && eq[s].unique ? (D.UNIQUES[eq[s].unique] && D.UNIQUES[eq[s].unique].set ? '#5ef2a0' : uniqueAccent(eq[s].unique)) : null);   // v0.17\n"
    "  const look0 = DOLL_BODYLOOK[bid('body')] || DOLL_BODYLOOK.none, tb = tl('body'); const look = {}; for (const k in look0) look[k] = tierTint(look0[k], tb, 0.4);")
rep("    G: DOLL_HANDS[bid('hands')] || '#f2c9a0', K: DOLL_FEET[bid('feet')] || '#2a2030',",
    "    G: DOLL_HANDS[bid('hands')] ? tierTint(DOLL_HANDS[bid('hands')], tl('hands')) : '#f2c9a0', K: DOLL_FEET[bid('feet')] ? tierTint(DOLL_FEET[bid('feet')], tl('feet')) : '#2a2030',")
rep("  const hd = DOLL_HEAD[bid('head')]; if (hd) put(hd[0], 3, 1, Object.assign({ g: rc('head') || '#ff5ad1' }, hd[1]));",
    "  const hd = DOLL_HEAD[bid('head')]; if (hd) { const hx = {}; for (const k in hd[1]) hx[k] = tierTint(hd[1][k], tl('head'), 0.5); put(hd[0], 3, 1, Object.assign({ g: uqc('head') || rc('head') || '#ff5ad1' }, hx));\n"
    "    if (tl('head') >= 3 && !white) { x.fillStyle = TIER_MAT[tl('head')]; x.fillRect(8, 0, 2, 1); if (tl('head') >= 5) { x.fillRect(6, 1, 1, 1); x.fillRect(11, 1, 1, 1); } } }   // crest / horns\n"
    "  if (bid('body') && tb >= 3 && !white) { x.fillStyle = TIER_MAT[tb]; x.fillRect(4, 7, 2, 1); x.fillRect(12, 7, 2, 1); if (tb >= 5) { x.fillRect(4, 8, 1, 1); x.fillRect(13, 8, 1, 1); } }   // shoulder plates\n"
    "  if (uqc('body') && !white) { x.fillStyle = uqc('body'); x.fillRect(8, 9, 2, 1); }")
rep("  const wp = DOLL_WEAPON[bid('weapon')]; if (wp) put(wp, 13, frame ? 1 : 0, { g: rc('weapon') || '#5ef2ff', w: '#e8eef7', a: '#9fa8b8' });",
    "  const wp = DOLL_WEAPON[bid('weapon')], tw = tl('weapon'); if (wp) put(wp, 13, frame ? 1 : 0, { g: uqc('weapon') || rc('weapon') || '#5ef2ff', w: tierTint('#e8eef7', tw, 0.55), a: tierTint('#9fa8b8', tw, 0.6), b: tierTint('#a8743c', tw, 0.3) });")
rep("  const off = DOLL_OFFHAND[bid('offhand')]; if (off) put(off, 0, frame && bid('offhand') === 'base.focus_orb' ? 1 : 0, { g: rc('offhand') || '#b35cff', G: '#6a2aa8', a: '#4b6cc8' });",
    "  const off = DOLL_OFFHAND[bid('offhand')]; if (off) put(off, 0, frame && bid('offhand') === 'base.focus_orb' ? 1 : 0, { g: uqc('offhand') || rc('offhand') || '#b35cff', G: '#6a2aa8', a: tierTint('#4b6cc8', tl('offhand'), 0.55) });")
# legendary sparkle + high-tier weapon glow around the player in a run
rep("  drawMoveFx(p, now); drawResoAura(p, now);   // v0.16.1",
    "  drawMoveFx(p, now); drawResoAura(p, now);   // v0.16.1\n"
    "  if (!opts.reduceFx && Math.random() < 0.25) { const E = p.equip || {}; const u = ['weapon', 'body', 'head', 'amulet', 'offhand'].map((k) => E[k]).find((it) => it && it.unique); const w = E.weapon;   // v0.17 gear shine\n"
    "    if (u) part(p.x + R01() * 14, p.y - 4 + R01() * 14, R01() * 8, -14 - Math.random() * 10, 0.6, D.UNIQUES[u.unique] && D.UNIQUES[u.unique].set ? '#5ef2a0' : uniqueAccent(u.unique), 1, { dr: 1 });\n"
    "    else if (w && (w.ilvl || 1) >= 4) part(p.x + 7 + R01() * 4, p.y - 6 + R01() * 8, 0, -10, 0.5, TIER_MAT[Math.min(6, w.ilvl)], 1, { dr: 1 }); }")
# item names: material prefix for common / magic items of tier 2–4 (ancient / primal already show)

# ---------------- per-skill VFX ----------------
rep("    addFx(g, { type: 'nova', x: ox, y: oy, r, dur: 0.32, color: elc, skill: true });\n    forEnemiesIn(g, ox, oy, r, (e) => hitEnemy(g, e, H, ctx));",
    "    addFx(g, { type: 'nova', x: ox, y: oy, r, dur: 0.32, color: elc, skill: true, vis: skillId });\n    forEnemiesIn(g, ox, oy, r, (e) => hitEnemy(g, e, H, ctx));")
rep("    if (drawFxV161(f, q, now)) { /* v0.16.1 */ }",
    "    if (drawFxV161(f, q, now)) { /* v0.16.1 */ }\n    else if (f.type === 'nova' && f.vis && NOVA_VFX[f.vis] && !opts.reduceFx) NOVA_VFX[f.vis](f, q, now);   // v0.17")
VFX = r"""
// v0.17 per-skill visuals for skills that used generic effects
const NOVA_VFX = {
  'skill.frost_nova': (f, q, now) => {   // ice spikes burst out of the ground, frost floor
    const R = f.r * (0.35 + 0.65 * Math.min(1, q * 1.6)); ctx.fillStyle = rgba('#bfe8ff', (1 - q) * 0.22); ctx.beginPath(); ctx.arc(f.x, f.y, R, 0, 6.283); ctx.fill();
    ctx.globalAlpha = 1 - q; for (let i = 0; i < 14; i++) { const a = i * 0.449 + f.x * 0.02, rr = R * (0.55 + (i % 3) * 0.17); iceShard(f.x + Math.cos(a) * rr, f.y + Math.sin(a) * rr, a, 5 + (i % 2) * 3); }
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(f.x, f.y, R, 0, 6.283); ctx.stroke(); snowflake(f.x, f.y, 3, '#ffffff');
    if (!f._p) { f._p = 1; burst(f.x, f.y, 22, '#e8fbff', f.r * 2.2, 0.5, { dr: 3 }); } ctx.globalAlpha = 1; },
  'skill.static_nova': (f, q, now) => {   // electric dome with arcs crawling out
    const R = f.r * (0.5 + 0.5 * q); ctx.fillStyle = rgba('#ffe14a', (1 - q) * 0.14); ctx.beginPath(); ctx.arc(f.x, f.y, R, 0, 6.283); ctx.fill();
    ctx.globalAlpha = 1 - q; ctx.strokeStyle = '#fff6a8'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(f.x, f.y, R, 0, 6.283); ctx.stroke();
    for (let i = 0; i < 6; i++) { const a = Math.random() * 6.283; boltLine(f.x, f.y, f.x + Math.cos(a) * R, f.y + Math.sin(a) * R, '#ffe14a', 1); }
    if (!f._p) { f._p = 1; for (let i = 0; i < 16; i++) { const a = Math.random() * 6.283; part(f.x, f.y, Math.cos(a) * 160, Math.sin(a) * 160, 0.25, '#ffffff', 1, { k: 1 }); } } ctx.globalAlpha = 1; },
};
Object.assign(PROJ_VFX, {
  'skill.power_shot': (pr, x, y, ux, uy) => { shaft(pr, ux, uy, 14, '#d8c8a8', '#ffffff'); ctx.strokeStyle = rgba('#ffffff', 0.5); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pr.x - ux * 26 - uy * 3, pr.y - uy * 26 + ux * 3); ctx.lineTo(pr.x - ux * 8, pr.y - uy * 8); ctx.moveTo(pr.x - ux * 26 + uy * 3, pr.y - uy * 26 - ux * 3); ctx.lineTo(pr.x - ux * 8, pr.y - uy * 8); ctx.stroke(); },
  'skill.quick_shot': (pr, x, y, ux, uy) => { ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pr.x - ux * 12, pr.y - uy * 12); ctx.lineTo(pr.x, pr.y); ctx.stroke(); ctx.fillStyle = '#ffffff'; ctx.fillRect(x - 1, y - 1, 2, 2); },
  'skill.dart_fan': (pr, x, y, ux, uy, now) => { const a = now * 30 + pr.id; ctx.strokeStyle = '#d8dce8'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pr.x + Math.cos(a) * 3, pr.y + Math.sin(a) * 3); ctx.lineTo(pr.x - Math.cos(a) * 3, pr.y - Math.sin(a) * 3); ctx.moveTo(pr.x - Math.sin(a) * 3, pr.y + Math.cos(a) * 3); ctx.lineTo(pr.x + Math.sin(a) * 3, pr.y - Math.cos(a) * 3); ctx.stroke(); ctx.fillStyle = '#ffffff'; ctx.fillRect(x, y, 1, 1); },
  'skill.ice_shards': (pr, x, y, ux, uy) => { ctx.fillStyle = '#7dd8ff'; ctx.beginPath(); ctx.moveTo(pr.x + ux * 4, pr.y + uy * 4); ctx.lineTo(pr.x - uy * 2, pr.y + ux * 2); ctx.lineTo(pr.x - ux * 3, pr.y - uy * 3); ctx.lineTo(pr.x + uy * 2, pr.y - ux * 2); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.fillRect(x, y, 1, 1); if (Math.random() < 0.4) part(pr.x, pr.y, R01() * 20, R01() * 20, 0.3, '#e8fbff', 1, { dr: 3 }); },
  'evowave': (pr, x, y, ux, uy) => { ctx.globalAlpha = 0.8; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(pr.x - ux * 4, pr.y - uy * 4, 7, Math.atan2(uy, ux) - 1, Math.atan2(uy, ux) + 1); ctx.stroke(); ctx.globalAlpha = 1; },
});
Object.assign(CLEAVE_VFX, {
  'skill.lightning_strike': (f, q) => { const half = f.half || 0.7; ctx.globalAlpha = 1 - q; ctx.strokeStyle = '#ffe14a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (0.6 + 0.4 * q), f.ang - half, f.ang + half); ctx.stroke();
    for (let i = 0; i < 3; i++) { const a = f.ang - half + (i + 0.5) * half * 2 / 3; boltLine(f.x + Math.cos(a) * 6, f.y + Math.sin(a) * 6, f.x + Math.cos(a) * f.r, f.y + Math.sin(a) * f.r, '#fff6a8', 1); } ctx.globalAlpha = 1; return true; },
});
"""
# insert after CLEAVE_VFX definition block: find its end (first "\n};\n" after the const)
ci = h.index("const CLEAVE_VFX = {")
ce = h.index("\n};\n", ci) + 4
h = h[:ce] + VFX + h[ce:]
# contagion telegraph: a green plague cloud instead of the cracking ground
rep("    if (z.skill === 'skill.meteor') {",
    "    if (z.skill === 'skill.contagion') { ctx.globalAlpha = 0.5 + 0.4 * pr; for (let i = 0; i < 7; i++) { const a = now * 2 + i * 0.9, rr = z.r * (0.3 + 0.12 * (i % 3)); bubble(z.x + Math.cos(a) * rr, z.y + Math.sin(a) * rr * 0.7, 2 + (i % 2), rgba('#9dff6a', 0.9)); } ctx.fillStyle = '#d8ffb8'; ctx.fillRect(Math.round(z.x) - 2, Math.round(z.y) - 3, 5, 4); ctx.fillStyle = '#1a2a10'; ctx.fillRect(Math.round(z.x) - 1, Math.round(z.y) - 2, 1, 1); ctx.fillRect(Math.round(z.x) + 1, Math.round(z.y) - 2, 1, 1); ctx.globalAlpha = 1; return; }   // v0.17\n"
    "    if (z.skill === 'skill.meteor') {")

# ---------------- per-skill sounds ----------------
SND = r"""
    // v0.17 per-skill cast sounds (fall back to the element sound)
    'sk:skill.arc_spark': () => { noise(0.07, 0.06, { hp: vary(4500, 0.2) }); tone(vary(1900), 0.05, 'square', 0.025, { f2: 600, lp: 5000 }); },
    'sk:skill.fireball': () => { noise(0.22, 0.07, { lp: 700, sweep: 2200 }); tone(vary(140), 0.2, 'triangle', 0.05, { f2: 70 }); },
    'sk:skill.ice_spear': () => { noise(0.1, 0.05, { hp: 5000, sweep: 9000 }); tone(vary(2800), 0.12, 'sine', 0.04, { f2: 4200 }); },
    'sk:skill.ice_shards': () => { for (let i = 0; i < 3; i++) tone(vary(3200, 0.2), 0.05, 'triangle', 0.025, { delay: i * 0.025 }); },
    'sk:skill.frost_nova': () => { noise(0.3, 0.08, { bp: 3000, sweep: 800, q: 0.8 }); for (let i = 0; i < 4; i++) tone(vary(2600, 0.3), 0.1, 'triangle', 0.025, { delay: 0.04 + i * 0.03 }); },
    'sk:skill.static_nova': () => { noise(0.18, 0.08, { hp: 3000 }); tone(vary(120), 0.25, 'sawtooth', 0.05, { f2: 60, lp: 1200 }); },
    'sk:skill.chain_lightning': () => { for (let i = 0; i < 3; i++) noise(0.05, 0.06, { hp: vary(4000, 0.3), delay: i * 0.04 }); tone(vary(900), 0.15, 'sawtooth', 0.03, { f2: 2400, lp: 5000 }); },
    'sk:skill.meteor': () => { tone(1800, 0.6, 'sine', 0.035, { f2: 300 }); noise(0.6, 0.03, { bp: 1500, sweep: 400 }); },
    'sk:skill.poison_pool': () => { for (let i = 0; i < 3; i++) tone(vary(300, 0.3), 0.08, 'sine', 0.05, { f2: 520, delay: i * 0.05 }); },
    'sk:skill.contagion': () => { noise(0.3, 0.05, { bp: 900, q: 2 }); tone(vary(180), 0.3, 'sine', 0.05, { f2: 260 }); },
    'sk:skill.flame_field': () => { noise(0.35, 0.07, { lp: 600, sweep: 1600 }); },
    'sk:skill.searing_aura': () => { noise(0.4, 0.05, { lp: 500, sweep: 1200 }); tone(110, 0.4, 'sawtooth', 0.03, { lp: 600 }); },
    'sk:skill.storm_turret': () => { tone(vary(320), 0.06, 'square', 0.04, { lp: 2000 }); noise(0.05, 0.05, { hp: 3500, delay: 0.05 }); },
    'sk:skill.blade_vortex': () => { for (let i = 0; i < 3; i++) tone(vary(3600, 0.2), 0.12, 'sine', 0.02, { delay: i * 0.04 }); noise(0.2, 0.04, { bp: 2500, q: 3 }); },
    'sk:skill.frost_mine': () => { tone(1200, 0.03, 'square', 0.04, { lp: 3000 }); tone(2400, 0.1, 'sine', 0.03, { delay: 0.04 }); },
    'sk:skill.whirl_cleave': () => noise(0.12, 0.08, { bp: 900, sweep: 2600, q: 0.9 }),
    'sk:skill.cyclone': () => noise(0.08, 0.05, { bp: 1600, sweep: 2600, q: 1 }),
    'sk:skill.double_strike': () => { noise(0.06, 0.07, { bp: 2200, sweep: 3800, q: 1 }); noise(0.06, 0.07, { bp: 2400, sweep: 4200, q: 1, delay: 0.07 }); },
    'sk:skill.heavy_strike': () => { noise(0.1, 0.08, { bp: 700, sweep: 1400, q: 1 }); tone(90, 0.18, 'sine', 0.12, { f2: 45, delay: 0.05 }); },
    'sk:skill.ground_slam': () => { tone(70, 0.3, 'sine', 0.14, { f2: 35 }); noise(0.25, 0.08, { lp: 600, sweep: 120 }); },
    'sk:skill.earthquake': () => { tone(55, 0.5, 'sine', 0.14, { f2: 30 }); noise(0.45, 0.07, { lp: 400, sweep: 80 }); },
    'sk:skill.leap_slam': () => { noise(0.15, 0.05, { bp: 800, sweep: 2400 }); tone(80, 0.25, 'sine', 0.13, { f2: 40, delay: 0.2 }); },
    'sk:skill.dash_strike': () => noise(0.14, 0.08, { bp: 1500, sweep: 5000, q: 0.8 }),
    'sk:skill.venom_slash': () => { noise(0.08, 0.06, { bp: 2000, sweep: 3600, q: 1 }); tone(vary(260), 0.1, 'sine', 0.04, { f2: 420, delay: 0.05 }); },
    'sk:skill.frost_blades': () => { noise(0.08, 0.06, { bp: 2200, sweep: 3800 }); tone(vary(2600), 0.12, 'sine', 0.035, { f2: 3400, delay: 0.04 }); },
    'sk:skill.infernal_blow': () => { noise(0.08, 0.06, { bp: 1800, sweep: 3000 }); noise(0.25, 0.07, { lp: 900, sweep: 250, delay: 0.06 }); },
    'sk:skill.lightning_strike': () => { noise(0.08, 0.06, { bp: 2200, sweep: 3800 }); noise(0.08, 0.06, { hp: 4500, delay: 0.05 }); },
    'sk:skill.power_shot': () => { tone(vary(180), 0.1, 'triangle', 0.08, { f2: 90 }); noise(0.15, 0.05, { bp: 1800, sweep: 600, delay: 0.02 }); },
    'sk:skill.split_arrow': () => { tone(vary(220), 0.08, 'triangle', 0.06, { f2: 120 }); noise(0.12, 0.05, { bp: 2400, sweep: 900 }); },
    'sk:skill.tornado_shot': () => { tone(vary(200), 0.08, 'triangle', 0.06, { f2: 110 }); noise(0.3, 0.05, { bp: 1200, sweep: 3000, q: 2 }); },
    'sk:skill.lightning_arrow': () => { tone(vary(200), 0.08, 'triangle', 0.06, { f2: 110 }); noise(0.07, 0.06, { hp: 4500, delay: 0.04 }); },
    'sk:skill.caustic_arrow': () => { tone(vary(200), 0.08, 'triangle', 0.06, { f2: 110 }); tone(vary(320), 0.1, 'sine', 0.04, { f2: 500, delay: 0.05 }); },
    'sk:skill.explosive_arrow': () => { tone(vary(200), 0.08, 'triangle', 0.06, { f2: 110 }); noise(0.18, 0.07, { lp: 900, delay: 0.06 }); },
    'sk:skill.rain_arrows': () => { for (let i = 0; i < 4; i++) noise(0.1, 0.03, { bp: vary(3000, 0.3), sweep: 900, delay: i * 0.05 }); },
    'sk:skill.dart_fan': () => { for (let i = 0; i < 3; i++) noise(0.05, 0.04, { bp: vary(3500, 0.2), delay: i * 0.02 }); },
    'sk:skill.cluster_darts': () => { for (let i = 0; i < 4; i++) noise(0.04, 0.04, { bp: vary(3800, 0.2), delay: i * 0.018 }); },
    'sk:skill.ricochet_blades': () => { tone(vary(3000, 0.1), 0.15, 'sine', 0.03, { f2: 2200 }); noise(0.06, 0.04, { bp: 3200 }); },
    'sk:skill.quick_shot': () => { noise(0.06, 0.1, { bp: 1500, q: 0.8 }); tone(140, 0.06, 'square', 0.05, { f2: 70, lp: 1000 }); },
    'sk:skill.scattershot': () => { noise(0.14, 0.13, { lp: 2200, sweep: 500 }); tone(90, 0.12, 'square', 0.07, { f2: 45, lp: 700 }); },
    'sk:skill.deadeye_shot': () => { noise(0.1, 0.12, { bp: 1100, q: 0.7 }); tone(110, 0.25, 'sine', 0.1, { f2: 50 }); noise(0.3, 0.03, { hp: 4000, delay: 0.08 }); },
    'sk:skill.frost_rounds': () => { noise(0.06, 0.09, { bp: 1500, q: 0.8 }); tone(vary(2800), 0.08, 'sine', 0.03, { delay: 0.03 }); },
    'sk:skill.summon_skeletons': () => { for (let i = 0; i < 4; i++) tone(vary(700, 0.4), 0.03, 'square', 0.035, { delay: i * 0.035, lp: 2500 }); },
    'sk:skill.flame_spirits': () => { arp([392, 523, 659], 0.05, 0.2, 'triangle', 0.05, { send: 0.4 }); noise(0.2, 0.03, { lp: 900 }); },
    'sk:skill.frost_wolf': () => { tone(330, 0.4, 'sawtooth', 0.04, { f2: 520, lp: 1400, attack: 0.08 }); },
    'sk:skill.summon_spiders': () => { for (let i = 0; i < 5; i++) noise(0.02, 0.04, { bp: vary(4000, 0.3), delay: i * 0.025 }); },
    'sk:skill.flame_dash': () => { noise(0.3, 0.09, { lp: 800, sweep: 3000 }); tone(120, 0.25, 'sawtooth', 0.04, { f2: 60, lp: 900 }); },
    'sk:skill.lightning_warp': () => { noise(0.12, 0.08, { hp: 3000 }); tone(2400, 0.12, 'sawtooth', 0.04, { f2: 300, lp: 5000 }); },
    'sk:skill.frostblink': () => { tone(2200, 0.15, 'sine', 0.05, { f2: 3600 }); noise(0.2, 0.04, { hp: 6000, sweep: 9000 }); },
    fusion: () => { tone(110, 0.6, 'sawtooth', 0.08, { f2: 55, lp: 900 }); noise(0.6, 0.1, { lp: 1600, sweep: 120 }); arp([523, 784, 1047], 0.04, 0.4, 'triangle', 0.05, { send: 0.6 }); },
    reso: () => { arp([659, 988], 0.05, 0.25, 'sine', 0.05, { send: 0.5 }); },
"""
rep("    // elements (casts) + reactions\n", SND + "    // elements (casts) + reactions\n")
rep("  return { play, music, unlock, apply, get key() { return musicKey; }, get names() { return Object.keys(BANK); }, get moods() { return Object.keys(MOODS); } };\n})();",
    "  return { play, music, unlock, apply, has: (n) => !!BANK[n], get key() { return musicKey; }, get names() { return Object.keys(BANK); }, get moods() { return Object.keys(MOODS); } };\n})();")
rep("  for (const k in now.casts) if (now.casts[k] > (pr.casts[k] || 0) && D.SKILLS[k]) SFX.play(D.SKILLS[k].element, 90);",
    "  for (const k in now.casts) if (now.casts[k] > (pr.casts[k] || 0) && D.SKILLS[k]) SFX.play(SFX.has('sk:' + k) ? 'sk:' + k : D.SKILLS[k].element, 90);   // v0.17 per-skill sounds")
rep("  if ((g.stats.fusionCasts || 0) > (sfxTick.fc || 0)) SFX.play('crit', 150); sfxTick.fc = g.stats.fusionCasts || 0;   // v0.16.1",
    "  if ((g.stats.fusionCasts || 0) > (sfxTick.fc || 0)) SFX.play('fusion', 150); sfxTick.fc = g.stats.fusionCasts || 0;   // v0.16.1 · v0.17 own sound\n"
    "  if ((g.stats.resoPulses || 0) > (sfxTick.rp || 0)) SFX.play('reso', 300); sfxTick.rp = g.stats.resoPulses || 0;")
EN.update({'鐵': 'Iron', '青銅': 'Bronze', '霜銀': 'Frost-silver', '虛空': 'Void'})
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok C looks', len(h))
