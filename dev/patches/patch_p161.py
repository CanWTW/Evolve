#!/usr/bin/env python3
"""EVOLVE v0.16.0 -> v0.16.1: feel pass.
- spell movement skills travel with animation (flame dash runs with a fire trail laid as you go; lightning warp / frostblink are a
  visible streak with departure / arrival effects), no more instant pop
- fusion: big banner when it awakens, charge-up ring before every burst, coloured screen flash, stronger damage, cd 6 → 5
- evolution: banner on each stage, kill assists count, thresholds 30/90 → 20/60
- resonance: stronger (+15% / +30%), an aura around the player, a HUD chip, and a resonance pulse every 4 s
  (same element: an element nova; trinity: a 3-element nova that sets up reactions)
Usage: patch_p161.py in.html out.html"""
import sys, json, re
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = {}


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)


# ---------------- version ----------------
rep("<title>PROJECT: EVOLVE — 原型 0.16.0</title>", "<title>PROJECT: EVOLVE — 原型 0.16.1</title>")
rep("瀏覽器原型 0.16.0（M0 + M1）", "瀏覽器原型 0.16.1（M0 + M1）", 2)
rep("Browser prototype 0.16.0 (M0 + M1)", "Browser prototype 0.16.1 (M0 + M1)")
rep("const VERSION = '0.16.0';", "const VERSION = '0.16.1';")

# ---------------- motion: options (hidden player, per-step callback, look) ----------------
rep("function startMotion(g, kind, ex, ey, dur, onEnd) {   // v0.12.1 player travels over time (invulnerable), onEnd fires on arrival\n"
    "  const p = g.player; p.motion = { kind, sx: p.x, sy: p.y, ex, ey, t: 0, dur, onEnd }; p.iframes = Math.max(p.iframes, dur + 0.08);",
    "function startMotion(g, kind, ex, ey, dur, onEnd, o) {   // v0.12.1 player travels over time (invulnerable), onEnd fires on arrival · v0.16.1 o = { vis, hide, onStep }\n"
    "  const p = g.player; p.motion = { kind, sx: p.x, sy: p.y, ex, ey, t: 0, dur, onEnd, vis: o && o.vis, hide: !!(o && o.hide), onStep: o && o.onStep }; p.iframes = Math.max(p.iframes, dur + 0.08);")
rep("  if (g.tick % 2 === 0) addFx(g, { type: 'after', x: p.x, y: p.y - (p.z || 0), dur: m.kind === 'dash' ? 0.18 : 0.12 });",
    "  if (m.onStep) { try { m.onStep(k); } catch (err) { /* ignore */ } }\n"
    "  if (g.tick % 2 === 0 && !m.hide) addFx(g, { type: 'after', x: p.x, y: p.y - (p.z || 0), dur: m.kind === 'dash' ? 0.18 : 0.12, vis: m.vis });")

# ---------------- blink: rewrite the travel part ----------------
a = h.index("  else if (sk.kind === 'blink') {")
b = h.index("  else if (sk.kind === 'chain') {", a)
BLINK = r"""  else if (sk.kind === 'blink') {   // v0.16 spell movement · v0.16.1 every one travels on screen
    if (origin.fromPlayer && !trig && p.motion) return false;
    const tgt = trig ? null : origin.dir ? aimTarget(g, ox, oy, sk.range, origin.dir) : nearestEnemy(g, ox, oy, sk.range, null); if (!tgt && !trig && !origin.dir) return false;
    const sx = origin.fromPlayer ? p.x : ox, sy = origin.fromPlayer ? p.y : oy;
    const a = tgt ? Math.atan2(tgt.y - sy, tgt.x - sx) : origin.dir ? Math.atan2(origin.dir[1], origin.dir[0]) : Math.atan2(p.faceY, p.faceX);
    let len = trig || !origin.fromPlayer ? 0 : tgt ? Math.min(sk.range, Math.hypot(tgt.x - sx, tgt.y - sy)) : sk.range;
    let ex = clamp(sx + Math.cos(a) * len, ARENA.wall + 6, ARENA.W - ARENA.wall - 6), ey = clamp(sy + Math.sin(a) * len, ARENA.wall + 6, ARENA.H - ARENA.wall - 6);
    for (let k = 0; k < 12 && len > 0 && inWall(g, ex, ey); k++) { len *= 0.8; ex = clamp(sx + Math.cos(a) * len, ARENA.wall + 6, ARENA.W - ARENA.wall - 6); ey = clamp(sy + Math.sin(a) * len, ARENA.wall + 6, ARENA.H - ARENA.wall - 6); }
    const R = sk.radius * M.area;
    const boom = (x, y, mul, big) => { addFx(g, { type: 'nova', x, y, r: R, dur: 0.35, color: elc, skill: true }); addFx(g, { type: 'blinkfx', x, y, r: R, dur: 0.45, vis: skillId, big: !!big });
      if (sk.element === 'lightning') addFx(g, { type: 'lightning', pts: [[x + 4, y - 70], [x - 5, y - 44], [x + 3, y - 20], [x, y]], dur: 0.25, color: elc, big: true });
      const HB = mul === 1 ? H : Object.assign({}, H, { dmg: H.dmg * mul }); forEnemiesIn(g, x, y, R, (e) => hitEnemy(g, e, HB, ctx)); };
    const trailZone = (x, y) => spawnZone(g, { kind: 'burning', skill: skillId, x, y, r: sk.trail.r * M.area, dur: sk.trail.dur * M.dur, tick: 0.5, H: Object.assign({}, H, { dmg: H.dmg * sk.trail.mul }), ctx });
    if (len > 0 && origin.fromPlayer) {
      if (sk.depart) boom(sx, sy, sk.depart);
      if (sk.warp) {   // lightning warp / frostblink: a short, visible streak (player hidden), arrival burst
        addFx(g, { type: 'streak', sx, sy, ex, ey, dur: 0.4, vis: skillId });
        if (sk.element === 'cold') addFx(g, { type: 'icestatue', x: sx, y: sy, dur: 0.6 });
        startMotion(g, 'warp', ex, ey, sk.element === 'lightning' ? 0.16 : 0.12, () => { if (sk.arrive) boom(ex, ey, sk.arrive, true); g.shake = Math.max(g.shake || 0, sk.element === 'lightning' ? 4 : 2); }, { vis: skillId, hide: true });
      } else {   // flame dash: run through as fire, burning ground laid as you go
        let laid = 0; const step = 26, n = Math.max(1, Math.floor(len / step));
        startMotion(g, 'dash', ex, ey, Math.max(0.22, len / 520), () => { while (laid <= n) { const t = laid / n; trailZone(sx + (ex - sx) * t, sy + (ey - sy) * t); laid++; } if (sk.arrive) boom(ex, ey, sk.arrive, true); },
          { vis: skillId, onStep: (k) => { while (laid <= n && laid / n <= k + 1e-6) { const t = laid / n; if (sk.trail) trailZone(sx + (ex - sx) * t, sy + (ey - sy) * t); laid++; } } });
      }
    } else { if (sk.depart) boom(ox, oy, sk.depart); if (sk.arrive) boom(ox, oy, sk.arrive); if (sk.trail) trailZone(ox, oy); }
    ok = true;
  }
"""
h = h[:a] + BLINK + h[b:]

# ---------------- evolution: assists, thresholds, banners ----------------
rep("const EVO_NEED = [30, 90];", "const EVO_NEED = [20, 60];   // v0.16.1: 30/90 → 20/60 (+ assists)")
rep("function evoKill(g, e, src) { const cred = src && g._autoSet && g._autoSet[src] ? src : e._la; if (cred) evoGain(g, cred, e.def.ai === 'boss' ? 25 : e.elite ? 5 : 1); }",
    "function evoKill(g, e, src) {   // v0.16.1: the killing auto skill gets the full value, every other auto skill that hit it gets half\n"
    "  const cred = src && g._autoSet && g._autoSet[src] ? src : e._la, v = e.def.ai === 'boss' ? 25 : e.elite ? 5 : 1;\n"
    "  if (cred) evoGain(g, cred, v); if (e._hb) for (const id in e._hb) if (id !== cred) evoGain(g, id, v * 0.5);\n}\n"
    "function banner(g, text, sub, col, big) { (g.banners || (g.banners = [])).push({ text, sub: sub || '', col: col || '#ffd23f', big: !!big }); if (g.banners.length > 4) g.banners.shift(); }")
rep("  if (g._autoSet && g._autoSet[H.src]) { e._la = H.src;", "  if (g._autoSet && g._autoSet[H.src]) { e._la = H.src; (e._hb || (e._hb = {}))[H.src] = 1;")
rep("    notice(g, SKILLS[id].name + tr(' 進化 ') + (st ? 'II' : 'I') + tr('：') + m.name, '#9dff7a');",
    "    banner(g, tr('進化 ') + (st ? 'II' : 'I') + ' · ' + m.name, SKILLS[id].name + tr('：') + m.desc, '#9dff7a', false);")

# ---------------- fusion: awaken banner, charge-up, flash, stronger ----------------
rep("const FUSION_CD = 6, FUSION_MUL = 2.2;", "const FUSION_CD = 5, FUSION_MUL = 2.5, FUSION_CHARGE = 0.8;   // v0.16.1: 6 s → 5 s, damage ×2.3, 0.8 s visible charge-up")
rep("  notice(g, tr('融合！') + SKILLS[a].name + ' ＋ ' + SKILLS[b].name + ' → ' + FUSIONS[key].name, '#ffd23f');\n"
    "  addFx(g, { type: 'nova', x: g.player.x, y: g.player.y, r: 90, dur: 0.7, color: '#ffd23f' });",
    "  banner(g, '✦ ' + FUSIONS[key].name + ' ✦', tr('融合覺醒：') + SKILLS[a].name + ' ＋ ' + SKILLS[b].name + tr(' · 每 ') + FUSION_CD + tr(' 秒自動爆發'), ELEMENTS[FUSIONS[key].els[0]].color, true);\n"
    "  addFx(g, { type: 'nova', x: g.player.x, y: g.player.y, r: 120, dur: 0.9, color: '#ffd23f' }); g.cflash = 0.5; g.cflashCol = ELEMENTS[FUSIONS[key].els[0]].color; g.shake = Math.max(g.shake || 0, 6); E0.fusT = 1.6;")
rep("  const base = ((E0.last[Fu.a] || 10) + (E0.last[Fu.b] || 10)) / 2 * FUSION_MUL,",
    "  const base = ((E0.last[Fu.a] || 10) + (E0.last[Fu.b] || 10)) * FUSION_MUL,")
rep("  addFx(g, { type: 'label', x: p.x, y: p.y - 28, text: '✦ ' + F.name, color: '#ffd23f', dur: 1.3 }); g.shake = Math.max(g.shake || 0, 3);",
    "  addFx(g, { type: 'label', x: p.x, y: p.y - 30, text: '✦ ' + F.name + ' ✦', color: '#ffd23f', dur: 1.4, big: true }); g.shake = Math.max(g.shake || 0, 6);\n"
    "  g.cflash = 0.28; g.cflashCol = col; addFx(g, { type: 'fusionburst', x: p.x, y: p.y, dur: 0.6, c1: col, c2: col2 });")
rep("  if (E0.fusion) { E0.fusT -= dt; if (E0.fusT <= 0) { if (nearestEnemy(g, g.player.x, g.player.y, 260, null)) { fireFusion(g); E0.fusT = FUSION_CD; } else E0.fusT = 0.3; } }",
    "  if (E0.fusion) { E0.fusT -= dt; if (E0.fusT <= FUSION_CHARGE && !nearestEnemy(g, g.player.x, g.player.y, 260, null)) E0.fusT = FUSION_CHARGE + 0.05;   // waits fully charged until enemies are near\n"
    "    if (E0.fusT <= 0) { fireFusion(g); E0.fusT = FUSION_CD; } }")

# ---------------- resonance: stronger + pulse ----------------
rep("  if (els.length === 3 && top === 1) return { kind: 'tri', react: 1.4 };\n  if (top >= 2) return { kind: 'same', el, n: top, dmg: top >= 3 ? 1.25 : 1.1 };",
    "  if (els.length === 3 && top === 1) return { kind: 'tri', react: 1.4, els: els.slice() };\n  if (top >= 2) return { kind: 'same', el, n: top, dmg: top >= 3 ? 1.3 : 1.15 };   // v0.16.1: +10/25% → +15/30%")
rep("function evoTick(g, dt) {\n  const A = autoSkillIds(g); g._autoSet = {}; for (const id of A) g._autoSet[id] = 1; g._reso = resonance(g);\n  const E0 = g.evo; if (!E0) return;",
    "const RESO_CD = 4;\n"
    "function resoPulse(g) {   // v0.16.1 共鳴脈衝: a beam to the nearest enemy and an element blast there (bigger with 3) / a 3-element blast (trinity, sets up reactions)\n"
    "  const R = g._reso, p = g.player; if (!R) return false; const t = nearestEnemy(g, p.x, p.y, 230, null); if (!t) return false; const E0 = evoState(g), A = autoSkillIds(g);\n"
    "  const avg = A.reduce((s, id) => s + (E0.last[id] || 8), 0) / Math.max(1, A.length), ctx = newChain(g, 'Cast', A[0]);\n"
    "  const r = R.kind === 'tri' ? 70 : R.n >= 3 ? 80 : 60, els = R.kind === 'tri' ? R.els : [R.el], mul = R.kind === 'tri' ? 0.9 : R.n >= 3 ? 2.2 : 1.4;\n"
    "  addFx(g, { type: 'resopulse', x: t.x, y: t.y, sx: p.x, sy: p.y - 4, r, dur: 0.6, els });\n"
    "  forEnemiesIn(g, t.x, t.y, r, (e) => { for (const el of els) if (!e.dead) hitEnemy(g, e, { dmg: avg * mul, element: el, src: 'reso.' + R.kind, ail: el === 'physical' ? 0 : 1, ailPow: 1, areaMul: 1, durMul: 1 }, ctx); });\n"
    "  g.stats.resoPulses = (g.stats.resoPulses || 0) + 1; return true;\n"
    "}\n"
    "function evoTick(g, dt) {\n  const A = autoSkillIds(g); g._autoSet = {}; for (const id of A) g._autoSet[id] = 1; const r0 = g._reso; g._reso = resonance(g);\n"
    "  if (g._reso && (!r0 || r0.kind !== g._reso.kind || r0.el !== g._reso.el || r0.n !== g._reso.n) && g.t > 0.5) { const R = g._reso; banner(g, R.kind === 'tri' ? tr('元素共鳴：三相') : tr('元素共鳴：') + ELEMENTS[R.el].name + ' ×' + R.n, R.kind === 'tri' ? tr('元素反應傷害 +40% · 每 4 秒三相脈衝') : tr('嗰種元素傷害 +') + Math.round((R.dmg - 1) * 100) + tr('% · 每 4 秒共鳴脈衝'), R.kind === 'tri' ? '#ff9ce6' : ELEMENTS[R.el].color, false); }\n"
    "  g.cflash = Math.max(0, (g.cflash || 0) - dt);\n"
    "  if (g._reso) { g._resoT = (g._resoT == null ? RESO_CD : g._resoT) - dt; if (g._resoT <= 0) g._resoT = resoPulse(g) ? RESO_CD : 0.2; } else g._resoT = null;\n"
    "  const E0 = g.evo; if (!E0) return;")
rep("  if (typeof id === 'string' && id.indexOf('fusion.') === 0 && FUSIONS[id.slice(7)])",
    "  if (id === 'reso.tri') return tr('共鳴脈衝：三相'); if (id === 'reso.same') return tr('共鳴脈衝');\n"
    "  if (typeof id === 'string' && id.indexOf('fusion.') === 0 && FUSIONS[id.slice(7)])")
rep("EVO_NEED, EVO_MUT, FUSIONS, FUSION_CD,", "EVO_NEED, EVO_MUT, FUSIONS, FUSION_CD, FUSION_CHARGE, RESO_CD, resoPulse,")

# ---------------- UI: player during motion, resonance aura, fusion charge ----------------
rep("  if (!blink || p.motion) ctx.drawImage(dollSprite(",
    "  drawMoveFx(p, now); drawResoAura(p, now);   // v0.16.1\n"
    "  if ((!blink || p.motion) && !(p.motion && p.motion.hide)) ctx.drawImage(dollSprite(")
UIFX = r"""
// ---------------- v0.16.1 movement / fusion / resonance visuals ----------------
function drawMoveFx(p, now) {
  const m = p.motion; if (!m || !m.vis) return; const x = p.x, y = p.y - 2, a = Math.atan2(m.ey - m.sy, m.ex - m.sx), ux = Math.cos(a), uy = Math.sin(a);
  if (m.vis === 'skill.flame_dash') {
    ctx.fillStyle = rgba('#ff6a2a', 0.35); ctx.beginPath(); ctx.arc(x, y, 11, 0, 6.283); ctx.fill();
    for (let i = 0; i < 4; i++) part(x + R01() * 8, y + R01() * 8, -ux * (60 + Math.random() * 60) + R01() * 40, -uy * (60 + Math.random() * 60) - 20 + R01() * 30, 0.4, Math.random() < 0.5 ? '#ff8a3c' : '#ffd23f', Math.random() < 0.3 ? 2 : 1, { dr: 3 });
    ctx.strokeStyle = '#ffd23f'; ctx.globalAlpha = 0.8; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x - ux * 22, y - uy * 22); ctx.lineTo(x, y); ctx.stroke(); ctx.globalAlpha = 1;
  } else if (m.vis === 'skill.lightning_warp') {
    ctx.fillStyle = rgba('#ffe14a', 0.4); ctx.beginPath(); ctx.arc(x, y, 9, 0, 6.283); ctx.fill(); ctx.fillStyle = '#ffffff'; ctx.fillRect(Math.round(x) - 2, Math.round(y) - 2, 5, 5);
    boltLine(m.sx, m.sy - 2, x, y, '#ffe14a', 2); for (let i = 0; i < 3; i++) part(x, y, R01() * 160, R01() * 160, 0.18, '#fff6a8', 1, { k: 1 });
  } else if (m.vis === 'skill.frostblink') {
    ctx.fillStyle = rgba('#9fe8ff', 0.45); ctx.beginPath(); ctx.arc(x, y, 8, 0, 6.283); ctx.fill(); ctx.fillStyle = '#ffffff'; ctx.fillRect(Math.round(x) - 1, Math.round(y) - 3, 3, 7); ctx.fillRect(Math.round(x) - 3, Math.round(y) - 1, 7, 3);
    for (let i = 0; i < 3; i++) part(x + R01() * 6, y + R01() * 6, -ux * 40 + R01() * 30, -uy * 40 + R01() * 30, 0.5, Math.random() < 0.5 ? '#e8fbff' : '#7dd8ff', 1, { dr: 3 });
  }
}
function drawResoAura(p, now) {
  const R = g && g._reso; if (!R || opts.reduceFx) return; const els = R.kind === 'tri' ? R.els : [R.el], n = R.kind === 'tri' ? 3 : R.n;
  const T = g._resoT == null ? C.RESO_CD : g._resoT, chg = 1 - Math.max(0, Math.min(1, T / C.RESO_CD)), rr = 16 + (1 - chg) * 4;
  for (let i = 0; i < n * 2; i++) { const a = now * 2.2 + i / (n * 2) * 6.283, col = D.ELEMENTS[els[i % els.length]].color; ctx.fillStyle = col; ctx.globalAlpha = 0.55 + 0.4 * chg; ctx.fillRect(Math.round(p.x + Math.cos(a) * rr) - 1, Math.round(p.y - 2 + Math.sin(a) * rr * 0.6) - 1, 2 + (chg > 0.85 ? 1 : 0), 2 + (chg > 0.85 ? 1 : 0)); }
  ctx.globalAlpha = 1;
  const E0 = g.evo; if (E0 && E0.fusion && E0.fusT <= C.FUSION_CHARGE) {   // fusion charge-up: two rings closing in + sparks pulled inward
    const F = C.FUSIONS[E0.fusion.key], c1 = D.ELEMENTS[F.els[0]].color, c2 = D.ELEMENTS[F.els[F.els.length - 1]].color, q = Math.max(0, E0.fusT / C.FUSION_CHARGE), r = 12 + q * 60;
    ctx.lineWidth = 2; ctx.strokeStyle = c1; ctx.globalAlpha = 0.9 - q * 0.5; ctx.beginPath(); ctx.arc(p.x, p.y - 2, r, now * 4, now * 4 + 4.5); ctx.stroke();
    ctx.strokeStyle = c2; ctx.beginPath(); ctx.arc(p.x, p.y - 2, r * 0.8, -now * 5, -now * 5 + 4.5); ctx.stroke(); ctx.globalAlpha = 1; ctx.lineWidth = 1;
    for (let i = 0; i < 2; i++) { const a = Math.random() * 6.283, d = 40 + Math.random() * 30; part(p.x + Math.cos(a) * d, p.y + Math.sin(a) * d, -Math.cos(a) * d * 2.5, -Math.sin(a) * d * 2.5, 0.35, i ? c1 : c2, 1, { dr: 0 }); }
  }
}
function drawFxV161(f, q, now) {   // returns true when handled
  if (f.type === 'streak') {
    const a = 1 - q; if (f.vis === 'skill.lightning_warp') { ctx.globalAlpha = a; boltLine(f.sx, f.sy - 2, f.ex, f.ey - 2, '#ffe14a', 3); boltLine(f.sx, f.sy - 2, f.ex, f.ey - 2, '#ffffff', 1); }
    else { ctx.globalAlpha = a * 0.9; ctx.strokeStyle = '#7dd8ff'; ctx.lineWidth = 4 * a + 1; ctx.beginPath(); ctx.moveTo(f.sx, f.sy - 2); ctx.lineTo(f.ex, f.ey - 2); ctx.stroke(); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.stroke();
      if (q < 0.3 && Math.random() < 0.7) { const t = Math.random(); part(f.sx + (f.ex - f.sx) * t, f.sy + (f.ey - f.sy) * t, R01() * 30, R01() * 30, 0.5, '#e8fbff', 1, { dr: 3 }); } }
    ctx.globalAlpha = 1; return true;
  }
  if (f.type === 'icestatue') {   // frostblink: an ice copy left behind that shatters
    const x = Math.round(f.x), y = Math.round(f.y);
    if (q < 0.75) { ctx.globalAlpha = 0.75; ctx.drawImage(SPR.player0, x - 6, y - 8); ctx.fillStyle = rgba('#9fe8ff', 0.55); ctx.fillRect(x - 6, y - 9, 13, 15); ctx.strokeStyle = '#e8fbff'; ctx.strokeRect(x - 6.5, y - 9.5, 14, 16); ctx.globalAlpha = 1; }
    else if (!f.done) { f.done = true; burst(f.x, f.y - 2, 18, '#cdf3ff', 90, 0.5, { dr: 3 }); }
    return true;
  }
  if (f.type === 'blinkfx') {
    const col = f.vis === 'skill.flame_dash' ? '#ff8a3c' : f.vis === 'skill.lightning_warp' ? '#ffe14a' : '#9fe8ff';
    if (!f.done) { f.done = true; burst(f.x, f.y, f.big ? 26 : 14, col, f.big ? 130 : 90, 0.5, { dr: 3 }); if (f.vis === 'skill.frostblink') for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; part(f.x, f.y, Math.cos(a) * 110, Math.sin(a) * 110, 0.4, '#ffffff', 1, { k: 1 }); } }
    ctx.globalAlpha = 1 - q; ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (0.4 + q * 0.8), 0, 6.283); ctx.stroke(); ctx.lineWidth = 1; ctx.globalAlpha = 1; return true;
  }
  if (f.type === 'fusionburst') {
    if (!f.done) { f.done = true; burst(f.x, f.y, 40, f.c1, 220, 0.7, { dr: 2 }); burst(f.x, f.y, 30, f.c2, 160, 0.8, { dr: 2 }); }
    ctx.globalAlpha = (1 - q) * 0.9; ctx.lineWidth = 3; ctx.strokeStyle = f.c1; ctx.beginPath(); ctx.arc(f.x, f.y, 20 + q * 150, 0, 6.283); ctx.stroke(); ctx.strokeStyle = f.c2; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(f.x, f.y, 10 + q * 110, 0, 6.283); ctx.stroke();
    ctx.lineWidth = 1; ctx.globalAlpha = 1; return true;
  }
  if (f.type === 'resopulse') {
    if (q < 0.35) f.els.forEach((el, i) => { const c = D.ELEMENTS[el].color; if (el === 'lightning') boltLine(f.sx, f.sy, f.x, f.y, c, 2); else { ctx.globalAlpha = Math.max(0, 0.9 - q * 2); ctx.strokeStyle = c; ctx.lineWidth = 3 - i; ctx.beginPath(); ctx.moveTo(f.sx, f.sy); ctx.lineTo(f.x, f.y); ctx.stroke(); } });
    ctx.globalAlpha = (1 - q) * 0.85; ctx.lineWidth = 2; f.els.forEach((el, i) => { ctx.strokeStyle = D.ELEMENTS[el].color; ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (0.25 + q * 0.75) - i * 4, 0, 6.283); ctx.stroke(); });
    if (!f.done) { f.done = true; f.els.forEach((el) => burst(f.x, f.y, 14, D.ELEMENTS[el].color, f.r * 2.2, 0.45, { dr: 3 })); }
    ctx.lineWidth = 1; ctx.globalAlpha = 1; return true;
  }
  return false;
}
"""
rep("function drawPlayer(p, now) {", UIFX + "function drawPlayer(p, now) {")
# hook into drawFx loop (first branch)
rep("    if (f.type === 'lightning') {", "    if (drawFxV161(f, q, now)) { /* v0.16.1 */ }\n    else if (f.type === 'lightning') {")
# coloured flash for fusions
rep("  if (g.flash > 0 && !opts.reduceFlash) { ctx.fillStyle = 'rgba(255,60,90,' + Math.min(0.35, g.flash) + ')'; ctx.fillRect(0, 0, VW, VH); }",
    "  if (g.cflash > 0 && !opts.reduceFlash) { ctx.fillStyle = rgba(g.cflashCol || '#ffd23f', Math.min(0.3, g.cflash * 0.8)); ctx.fillRect(0, 0, VW, VH); }   // v0.16.1 fusion flash\n"
    "  if (g.flash > 0 && !opts.reduceFlash) { ctx.fillStyle = 'rgba(255,60,90,' + Math.min(0.35, g.flash) + ')'; ctx.fillRect(0, 0, VW, VH); }")

# ---------------- banners (DOM) ----------------
rep('    <div id="toasts"></div>\n  </div>', '    <div id="toasts"></div>\n    <div id="banner" aria-live="polite"></div>\n  </div>')
rep("#toasts{position:absolute;", "#banner{position:absolute;left:5%;right:5%;top:28%;text-align:center;pointer-events:none;z-index:5}   /* v0.16.1 */\n"
    "#banner .bn{display:block;text-align:center;animation:bnIn 2.6s ease-out forwards;text-shadow:0 0 calc(var(--u)*3) currentColor,0 calc(var(--u)*0.6) 0 #000}#banner .bn b{display:block;font-size:calc(var(--u)*13);letter-spacing:.06em}#banner .bn.big b{font-size:calc(var(--u)*20)}\n"
    "#banner .bn small{display:block;color:#e8eef7;font-size:calc(var(--u)*5.5);text-shadow:0 calc(var(--u)*0.5) 0 #000;margin-top:calc(var(--u)*1)}\n"
    "@keyframes bnIn{0%{opacity:0;transform:scale(1.6)}12%{opacity:1;transform:scale(1)}80%{opacity:1}100%{opacity:0;transform:translateY(calc(var(--u)*-6))}}\n"
    "body.touch #banner{top:26%}#gemrow span.reso{border-style:solid;border-width:calc(var(--u)*0.5)}\n"
    "#toasts{position:absolute;")
rep("function drainNotices() {",
    "function drainBanners() {   // v0.16.1\n"
    "  if (!g || !g.banners || !g.banners.length) return; const box = $('banner'); const B = g.banners.shift(); g.banners.length = Math.min(g.banners.length, 1);\n"
    "  box.textContent = ''; const d = el('div', 'bn' + (B.big ? ' big' : '')); d.style.color = B.col; d.append(el('b', null, B.text)); if (B.sub) d.append(el('small', null, B.sub)); box.appendChild(d);\n"
    "  if (B.big) SFX.play('ancient', 400); else SFX.play('level', 300);\n"
    "  clearTimeout(drainBanners.t); drainBanners.t = setTimeout(() => { if (box.firstChild === d) d.remove(); }, 2700);\n"
    "}\n"
    "function drainNotices() {")
rep("  autosaveTick();\n  drainNotices();", "  autosaveTick();\n  drainNotices(); drainBanners();")
# fusion burst sound
rep("  if (now.dodges > pr.dodges) SFX.play('dodge', 100);",
    "  if (now.dodges > pr.dodges) SFX.play('dodge', 100);\n"
    "  if ((g.stats.fusionCasts || 0) > (sfxTick.fc || 0)) SFX.play('crit', 150); sfxTick.fc = g.stats.fusionCasts || 0;   // v0.16.1")
# HUD: resonance chip
rep("    if (g.evo && g.evo.fusion) { const F = C.FUSIONS[g.evo.fusion.key]; const sf = add('✦ ' + F.name, 'fus');",
    "    if (g._reso) { const R = g._reso; const sr = add(R.kind === 'tri' ? tr('共鳴：三相') : tr('共鳴：') + D.ELEMENTS[R.el].name + ' ×' + R.n, 'reso', R.kind === 'tri' ? '#ff9ce6' : D.ELEMENTS[R.el].color); sr.style.color = R.kind === 'tri' ? '#ffd0f3' : D.ELEMENTS[R.el].color; }   // v0.16.1\n"
    "    if (g.evo && g.evo.fusion) { const F = C.FUSIONS[g.evo.fusion.key]; const sf = add('✦ ' + F.name, 'fus');")
rep("const key = A.map((id) => id + ':' + ((E0 && E0.stage[id]) || 0)).join(',') + '|' + (E0 && E0.fusion ? E0.fusion.key : '');",
    "const key = A.map((id) => id + ':' + ((E0 && E0.stage[id]) || 0)).join(',') + '|' + (E0 && E0.fusion ? E0.fusion.key : '') + '|' + (g._reso ? g._reso.kind + (g._reso.el || '') + (g._reso.n || '') : '');")
# orb screen resonance text (numbers)
rep("tr('元素共鳴：2 招同元素 +10%、3 招同元素 +25%、3 種唔同元素＝三相（反應 +40%）')",
    "tr('元素共鳴：2 招同元素 +15%、3 招同元素 +30%、3 種唔同元素＝三相（反應 +40%）；仲會每 4 秒發出共鳴脈衝')")
rep("tr('元素共鳴：三相（元素反應傷害 +40%）')", "tr('元素共鳴：三相（元素反應傷害 +40%，每 4 秒三相脈衝）')")
rep("tr('（嗰種元素嘅自動技能傷害 +') + Math.round((R.dmg - 1) * 100) + '%）'", "tr('（嗰種元素嘅自動技能傷害 +') + Math.round((R.dmg - 1) * 100) + tr('%，每 4 秒共鳴脈衝）')")
rep("tr('（每 ') + C.FUSION_CD + tr(' 秒自動爆發）')", "tr('（每 ') + C.FUSION_CD + tr(' 秒自動爆發）')")

EN.update({
    '融合覺醒：': 'Fusion awakened: ', ' · 每 ': ' · bursts every ', ' 秒自動爆發': ' s', '進化 ': 'Evolution ',
    '元素共鳴：三相': 'Resonance: Trinity', '元素反應傷害 +40% · 每 4 秒三相脈衝': 'Reaction damage +40% · Trinity pulse every 4 s',
    '嗰種元素傷害 +': 'That element +', '% · 每 4 秒共鳴脈衝': '% damage · resonance pulse every 4 s',
    '共鳴脈衝：三相': 'Resonance pulse: Trinity', '共鳴脈衝': 'Resonance pulse', '共鳴：三相': 'Resonance: Trinity', '共鳴：': 'Resonance: ',
    '元素共鳴：2 招同元素 +15%、3 招同元素 +30%、3 種唔同元素＝三相（反應 +40%）；仲會每 4 秒發出共鳴脈衝': 'Resonance: 2 skills of one element +15%, 3 of one element +30%, 3 different elements = Trinity (reactions +40%); also a resonance pulse every 4 s',
    '元素共鳴：三相（元素反應傷害 +40%，每 4 秒三相脈衝）': 'Resonance: Trinity (reaction damage +40%, Trinity pulse every 4 s)',
    '%，每 4 秒共鳴脈衝）': '%, resonance pulse every 4 s)',
})
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();", "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.16.1\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")
open(dst, 'w', encoding='utf-8').write(h)
print('ok 0.16.1', len(h))
