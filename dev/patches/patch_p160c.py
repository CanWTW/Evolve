#!/usr/bin/env python3
"""EVOLVE v0.16.0 part D: skill evolution (paths picked in the village, stages earned in the run), fusion ultimates,
elemental resonance, fusion codex. Usage: patch_p160c.py in.html out.html"""
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


# ---------------- data ----------------
MUT = {
    'proj': [[('split', '分裂', 'Split', '命中後分裂成 2 粒（×0.6）；傷害 +10%', 'Splits into 2 on hit (×0.6); +10% damage', "fork: 2, dmg: 1.1"),
              ('giant', '巨大化', 'Giant', '投射物大 60%、傷害 ×1.4，飛行速度 −25%', 'Projectiles 60% bigger, ×1.4 damage, 25% slower', "dmg: 1.4, size: 1.6, pspd: 0.75")],
             [('homing', '追蹤', 'Homing', '投射物會轉彎追蹤敵人，貫穿 +1', 'Projectiles curve towards enemies; +1 pierce', "homing: true, pierce: 1"),
              ('volley', '連射', 'Volley', '+2 投射物，每粒傷害 ×0.85', '+2 projectiles, ×0.85 damage each', "proj: 2, dmg: 0.85")]],
    'melee': [[('wave', '劍氣', 'Blade Wave', '每次揮擊向前射出一道劍氣（60%，貫穿）', 'Every swing sends a piercing wave forward (60%)', "wave: 0.6"),
               ('spin', '旋斬', 'Spin', '揮擊變成 360°，範圍 +25%', 'Swings hit all around you; +25% area', "full: true, area: 1.25")],
              [('combo', '連擊', 'Combo', '每次命中再補多一下（50%）', 'Every hit lands a follow-up (50%)', "extraHit: 0.5"),
               ('crush', '重擊', 'Crush', '傷害 ×1.25、暴擊率 +10%，攻速 −10%', '×1.25 damage, +10% crit chance, 10% slower', "dmg: 1.25, crit: 0.1, spd: 0.9")]],
    'area': [[('echo', '二次脈衝', 'Echo', '0.5 秒後喺同一位置再施放一次（60%）', 'Repeats 0.5 s later in the same place (60%)', "echo: 0.6"),
              ('spread', '擴散', 'Spread', '範圍 +40%', '+40% area', "area: 1.4")],
             [('erode', '侵蝕', 'Erosion', '傷害 ×1.2、異常機率 +25%', '×1.2 damage, +25% ailment chance', "dmg: 1.2, ail: 0.25"),
              ('rapid', '急速', 'Rapid', '施放速度 +30%', '+30% cast speed', "spd: 1.3")]],
    'minion': [[('legion', '軍團', 'Legion', '每次多召喚 1 隻、上限 +50%，每隻傷害 −15%', '+1 summoned per cast, +50% max, −15% damage each', "perCast: 1, maxMul: 1.5, dmg: 0.85"),
                ('titan', '巨型化', 'Titan', '每隻傷害 ×1.6，上限 −1', '×1.6 damage each, −1 max', "dmg: 1.6, maxAdd: -1")],
               [('frenzy', '狂暴', 'Frenzy', '召喚物速度 +30%', 'Minions 30% faster', "mspd: 1.3"),
                ('burst', '爆裂', 'Burst', '召喚物消失時爆炸（150%，範圍 40）', 'Minions explode when they expire (150%, radius 40)', "burst: 1.5")]],
}
FUS = [  # key, zh, en, desc zh, desc en, ops
    ('cold+fire', '蒸氣爆裂', 'Steam Burst', '3 個敵人位置延遲大爆炸（範圍 64）', 'Delayed blasts on 3 enemies (radius 64)', "[['blasts', 3, 64, 2.4, 0.35]]"),
    ('fire+lightning', '等離子風暴', 'Plasma Storm', '8 道雷火轟落附近敵人', '8 fire-lightning bolts on nearby enemies', "[['bolts', 8, 28, 1.6]]"),
    ('fire+poison', '毒焰風暴', 'Toxic Inferno', '敵人腳下燃起毒焰地面 4 秒（範圍 90）', 'A burning toxic field under enemies for 4 s (radius 90)', "[['field', 90, 4, 0.7]]"),
    ('fire+physical', '熔岩隕落', 'Magma Fall', '4 粒熔岩隕石砸落敵人（範圍 56）', '4 magma meteors on enemies (radius 56)', "[['blasts', 4, 56, 2.0, 0.6]]"),
    ('cold+lightning', '超導冰暴', 'Superconductor', '身邊冰雷爆發（範圍 120），再連鎖 6 個敵人', 'An ice-lightning nova (radius 120), then chains to 6 enemies', "[['nova', 120, 2.0], ['chain', 6, 1.0]]"),
    ('cold+poison', '冰毒結晶', 'Venom Frost', '冰毒新星（範圍 70）＋留低毒霜地面 3 秒', 'A venom-frost nova (radius 70) plus a frozen poison field for 3 s', "[['nova', 70, 1.4], ['field', 80, 3, 0.7]]"),
    ('cold+physical', '冰川碎裂', 'Glacial Shatter', '向四周射出 14 塊冰川碎片（貫穿 3）', '14 glacier shards in every direction (pierce 3)', "[['ring', 14, 1.0, 3]]"),
    ('lightning+poison', '腐蝕電網', 'Corrosive Grid', '腐蝕閃電連鎖 10 個敵人', 'Corrosive lightning chains through 10 enemies', "[['chain', 10, 1.3]]"),
    ('lightning+physical', '雷鳴千斬', 'Thunder Blades', '身邊雷斬（範圍 90）＋5 道落雷', 'A thunder slash around you (radius 90) plus 5 bolts', "[['nova', 90, 1.6], ['bolts', 5, 24, 1.2]]"),
    ('physical+poison', '劇毒鋼刃', 'Venom Steel', '16 把毒刃四散（貫穿 2）＋毒池', '16 venom blades in every direction (pierce 2) plus a poison pool', "[['ring', 16, 0.9, 2], ['field', 60, 3, 0.4]]"),
    ('fire+fire', '煉獄', 'Inferno', '純火焰大爆發（範圍 130）', 'A pure fire explosion (radius 130)', "[['nova', 130, 2.6]]"),
    ('cold+cold', '絕對零度', 'Absolute Zero', '冰封新星（範圍 140），必定冰緩', 'A freezing nova (radius 140) that always chills', "[['nova', 140, 1.8]]"),
    ('lightning+lightning', '雷神之怒', "Thunder God's Wrath", '12 道落雷', '12 lightning bolts', "[['bolts', 12, 30, 1.5]]"),
    ('poison+poison', '萬毒歸宗', 'Plaguelands', '巨大毒沼 5 秒（範圍 120）', 'A huge poison swamp for 5 s (radius 120)', "[['field', 120, 5, 0.6]]"),
    ('physical+physical', '千刃風暴', 'Thousand Blades', '24 把刀刃四散（貫穿 4）', '24 blades in every direction (pierce 4)', "[['ring', 24, 1.1, 4]]"),
]
mut_js = '{ ' + ', '.join("%s: [%s]" % (g, ', '.join('[' + ', '.join("{ id: '%s', name: tr('%s'), en: '%s', desc: tr('%s'), %s }" % (i, zh, en, dz, f) for (i, zh, en, dz, de, f) in stage) + ']' for stage in st)) for g, st in MUT.items()) + ' }'
fus_js = '{ ' + ', '.join("'%s': { key: '%s', name: tr('%s'), en: \"%s\", desc: tr('%s'), els: %s, ops: %s }" % (k, k, zh, en, dz, json.dumps(k.split('+')[:1] if k.split('+')[0] == k.split('+')[1] else k.split('+')), ops) for (k, zh, en, dz, de, ops) in FUS) + ' }'
for g_, st in MUT.items():
    for stage in st:
        for (i, zh, en, dz, de, f) in stage:
            EN[zh] = en; EN[dz] = de
for (k, zh, en, dz, de, ops) in FUS:
    EN[zh] = en; EN[dz] = de

CORE = r"""
// ---------------- v0.16 skill evolution · fusion · resonance ----------------
// Paths are part of the build (picked in the village, save.progress.evoPaths[skillId] = [stage I choice, stage II choice]); stages are
// earned in the run by the skill's own kills (+ damage to elites / bosses) — no random choices, so leaderboards stay about the build.
const EVO_NEED = [40, 120];   // cumulative evolution points for stage I / II
const EVO_MUT = %MUT%;
const FUSIONS = %FUS%;
const FUSION_CD = 6, FUSION_MUL = 2.2;
function evoGroup(sk) { return !sk ? 'area' : sk.kind === 'summon' ? 'minion' : sk.kind === 'projectile' ? 'proj' : (sk.kind === 'melee' || sk.kind === 'leap' || sk.kind === 'dash') ? 'melee' : 'area'; }
function evoState(g) { return g.evo || (g.evo = { pts: {}, stage: {}, last: {}, el: {}, q: [], fusion: null, fusT: 0 }); }
function evoPick(g, id) { const v = g.evoPaths && g.evoPaths[id]; return Array.isArray(v) ? [v[0] ? 1 : 0, v[1] ? 1 : 0] : [0, 0]; }
function evoMutation(g, id, k) { return EVO_MUT[evoGroup(SKILLS[id])][k][evoPick(g, id)[k]]; }
const EVO_MULF = ['dmg', 'area', 'spd', 'size', 'pspd', 'maxMul', 'mspd'];
function evoMods(g, id) {
  const st = g.evo ? g.evo.stage[id] || 0 : 0; if (!st) return null;
  const R = { dmg: 1, area: 1, spd: 1, size: 1, pspd: 1, maxMul: 1, mspd: 1, fork: 0, pierce: 0, proj: 0, crit: 0, ail: 0, perCast: 0, maxAdd: 0, echo: 0, wave: 0, extraHit: 0, burst: 0, full: false, homing: false };
  for (let k = 0; k < st; k++) { const m = evoMutation(g, id, k); for (const f in m) { if (f === 'id' || f === 'name' || f === 'en' || f === 'desc') continue; const v = m[f]; if (typeof v === 'boolean') R[f] = R[f] || v; else if (EVO_MULF.indexOf(f) >= 0) R[f] *= v; else R[f] += v; } }
  return R;
}
function evoGain(g, id, v) {
  if (!g._autoSet || !g._autoSet[id] || !(v > 0)) return; const E0 = evoState(g), st = E0.stage[id] || 0; if (st >= 2) return;
  E0.pts[id] = (E0.pts[id] || 0) + v;
  if (E0.pts[id] >= EVO_NEED[st]) {
    E0.stage[id] = st + 1; const m = evoMutation(g, id, st), p = g.player;
    notice(g, SKILLS[id].name + tr(' 進化 ') + (st ? 'II' : 'I') + tr('：') + m.name, '#9dff7a');
    addFx(g, { type: 'nova', x: p.x, y: p.y, r: 46, dur: 0.5, color: '#9dff7a' }); addFx(g, { type: 'label', x: p.x, y: p.y - 22, text: '⬆ ' + m.name, color: '#9dff7a', dur: 1.1 });
    g.stats.evolutions = (g.stats.evolutions || 0) + 1; checkFusion(g);
  }
}
function evoKill(g, e, src) { const cred = src && g._autoSet && g._autoSet[src] ? src : e._la; if (cred) evoGain(g, cred, e.def.ai === 'boss' ? 25 : e.elite ? 5 : 1); }
function skillEl(g, id) { return (g.evo && g.evo.el[id]) || SKILLS[id].element; }
function checkFusion(g) {
  const E0 = evoState(g); if (E0.fusion) return;
  const ready = AUTO_ROWS.map((i) => g.player.build.mains[i]).map((M) => (M ? gemId(g, M.skill) : null)).filter((id) => id && (E0.stage[id] || 0) >= 2);
  if (ready.length < 2) return;
  const a = ready[0], b = ready[1], key = [skillEl(g, a), skillEl(g, b)].sort().join('+'); if (!FUSIONS[key]) return;
  E0.fusion = { key, a, b }; E0.fusT = 1.2; g.stats.fusion = key;
  notice(g, tr('融合！') + SKILLS[a].name + ' ＋ ' + SKILLS[b].name + ' → ' + FUSIONS[key].name, '#ffd23f');
  addFx(g, { type: 'nova', x: g.player.x, y: g.player.y, r: 90, dur: 0.7, color: '#ffd23f' });
}
function resonance(g) {   // 元素共鳴 from the auto skills' elements
  const els = autoSkillIds(g).map((id) => skillEl(g, id)); const cnt = {}; for (const x of els) cnt[x] = (cnt[x] || 0) + 1;
  const top = Math.max(0, ...Object.values(cnt)), el = Object.keys(cnt).find((k) => cnt[k] === top) || null;
  if (els.length === 3 && top === 1) return { kind: 'tri', react: 1.4 };
  if (top >= 2) return { kind: 'same', el, n: top, dmg: top >= 3 ? 1.25 : 1.1 };
  return null;
}
function evoTick(g, dt) {
  const A = autoSkillIds(g); g._autoSet = {}; for (const id of A) g._autoSet[id] = 1; g._reso = resonance(g);
  const E0 = g.evo; if (!E0) return;
  if (E0.q.length) { const due = E0.q.filter((q) => q.t <= g.t); if (due.length) { E0.q = E0.q.filter((q) => q.t > g.t); for (const q of due) castSkill(g, q.id, q.inst, { x: q.x, y: q.y, fromPlayer: false, triggered: false, echo: q.mul }, newChain(g, 'Cast', q.id)); } }
  if (E0.fusion) { E0.fusT -= dt; if (E0.fusT <= 0) { if (nearestEnemy(g, g.player.x, g.player.y, 260, null)) { fireFusion(g); E0.fusT = FUSION_CD; } else E0.fusT = 0.3; } }
}
function fireFusion(g) {
  const E0 = g.evo, Fu = E0.fusion, F = FUSIONS[Fu.key], p = g.player; if (!F) return;
  const base = ((E0.last[Fu.a] || 10) + (E0.last[Fu.b] || 10)) / 2 * FUSION_MUL, src = 'fusion.' + Fu.key, ctx = newChain(g, 'Cast', Fu.a);
  const els = F.els, col = ELEMENTS[els[0]].color, col2 = ELEMENTS[els[els.length - 1]].color;
  const pk = (mul, i) => ({ dmg: base * mul, element: els[(i || 0) % els.length], src, ail: 0.6, ailPow: 1, areaMul: 1, durMul: 1 });
  const hitAll = (e, mul) => { for (let i = 0; i < els.length; i++) if (!e.dead) hitEnemy(g, e, pk(mul / els.length, i), ctx); };
  const near = (r) => g.enemies.filter((e) => !e.dead && Math.hypot(e.x - p.x, e.y - p.y) < r).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
  addFx(g, { type: 'label', x: p.x, y: p.y - 28, text: '✦ ' + F.name, color: '#ffd23f', dur: 1.3 }); g.shake = Math.max(g.shake || 0, 3);
  for (const op of F.ops) {
    const k = op[0];
    if (k === 'nova') { addFx(g, { type: 'nova', x: p.x, y: p.y, r: op[1], dur: 0.5, color: col, skill: true }); addFx(g, { type: 'nova', x: p.x, y: p.y, r: op[1] * 0.65, dur: 0.4, color: col2 }); forEnemiesIn(g, p.x, p.y, op[1], (e) => hitAll(e, op[2])); }
    else if (k === 'bolts') { const pool = near(240); for (let i = 0; i < op[1] && pool.length; i++) { const e = pool[(i * 3) % pool.length]; const x = e.x, y = e.y; addFx(g, { type: 'lightning', pts: [[x + 3, y - 52], [x - 3, y - 24], [x, y]], dur: 0.22, color: i % 2 ? col2 : col, big: true }); addFx(g, { type: 'nova', x, y, r: op[2], dur: 0.25, color: col2 }); forEnemiesIn(g, x, y, op[2], (o) => hitAll(o, op[3])); } }
    else if (k === 'blasts') { const pool = near(260); for (let i = 0; i < op[1] && pool.length; i++) { const e = pool[i % pool.length], off = i >= pool.length ? (i * 17 % 40) - 20 : 0; const z = spawnZone(g, { kind: 'delayed', skill: Fu.a, x: e.x + off, y: e.y - off, r: op[2], dur: op[4] + 0.05, tick: 99, H: pk(op[3], i), ctx }); if (z) { z.delay = op[4]; z.tickT = 99; } } }
    else if (k === 'ring') { for (let i = 0; i < op[1]; i++) spawnProjectile(g, { x: p.x, y: p.y, ang: i / op[1] * Math.PI * 2, speed: 270, life: 0.95, r: 3, H: pk(op[2], i), pierce: op[3], ctx, vis: 'fusion' }); }
    else if (k === 'field') { const t = near(240)[0]; spawnZone(g, { kind: els.indexOf('fire') >= 0 ? 'burning' : 'pool', skill: Fu.a, x: t ? t.x : p.x, y: t ? t.y : p.y, r: op[1], dur: op[2], tick: 0.5, H: pk(op[3], els.length - 1), ctx }); }
    else if (k === 'chain') { let cur = near(240)[0], px = p.x, py = p.y; const hit = []; for (let i = 0; i < op[1] && cur; i++) { addFx(g, { type: 'lightning', pts: [[px, py], [cur.x, cur.y]], dur: 0.2, color: i % 2 ? col2 : col, big: true }); hit.push(cur.id); px = cur.x; py = cur.y; hitAll(cur, op[2]); cur = nearestEnemy(g, px, py, 130, hit); } }
  }
  g.stats.fusionCasts = (g.stats.fusionCasts || 0) + 1;
}
function minionBurst(g, m) { const r = 40; addFx(g, { type: 'nova', x: m.x, y: m.y, r, dur: 0.3, color: ELEMENTS[m.H.element].color }); const HB = Object.assign({}, m.H, { dmg: m.H.dmg * m.burst }); forEnemiesIn(g, m.x, m.y, r, (e) => hitEnemy(g, e, HB, m.ctx)); }
""".replace('%MUT%', mut_js).replace('%FUS%', fus_js)
rep("function supportOk(supId, skillId, rowIds) {", CORE + "function supportOk(supId, skillId, rowIds) {")

# ---------------- hooks ----------------
# per tick: auto set, resonance, echoes, fusion
rep("function castMains(g, dt) {\n  const p = g.player, s = p.stats;", "function castMains(g, dt) {\n  const p = g.player, s = p.stats; evoTick(g, dt);   // v0.16")
# evolution speed mutation on the cast interval
rep("    const W2 = sk.attack ? attackWeapon(g, sk) : null; const baseCd = W2 ? sk.speedMod / W2.aps : sk.cooldown;   // v0.7: attacks run at the weapon's speed",
    "    { const EVs = g._autoSet && g._autoSet[id] ? evoMods(g, id) : null; if (EVs) cs *= EVs.spd; }   // v0.16 evolution\n"
    "    const W2 = sk.attack ? attackWeapon(g, sk) : null; const baseCd = W2 ? sk.speedMod / W2.aps : sk.cooldown;   // v0.7: attacks run at the weapon's speed")
# cast: evolution mods, resonance, last hit damage for fusions
rep("  if (sk.spread) H.spread = sk.spread;   // v0.16 contagion",
    "  if (sk.spread) H.spread = sk.spread;   // v0.16 contagion\n"
    "  const isAuto = !!(g._autoSet && g._autoSet[skillId]);\n"
    "  const EV = isAuto && !trig && !origin.echo ? evoMods(g, skillId) : null;   // v0.16 evolution\n"
    "  if (isAuto && g._reso && g._reso.kind === 'same' && g._reso.el === M.element) H.dmg *= g._reso.dmg;   // 元素共鳴\n"
    "  if (isAuto && !trig) { const E0 = evoState(g); E0.last[skillId] = H.dmg; E0.el[skillId] = M.element; }\n"
    "  if (origin.echo) H.dmg *= origin.echo;\n"
    "  if (EV) { H.dmg *= EV.dmg; M.area *= EV.area; H.areaMul = M.area; M.fork += EV.fork; M.pierce += EV.pierce; M.extraProj += EV.proj; if (EV.crit) H.critAdd = (H.critAdd || 0) + EV.crit; if (EV.ail && H.ail > 0) H.ail = Math.min(1, H.ail + EV.ail); }")
rep("spawnProjectile(g, { x: ox, y: oy, ang: base + (i - (n - 1) / 2) * spread, speed: sk.projSpeed * s.projSpeedMul, life: sk.projLife, r: sk.r, H: HH,",
    "spawnProjectile(g, { x: ox, y: oy, ang: base + (i - (n - 1) / 2) * spread, speed: sk.projSpeed * s.projSpeedMul * (EV ? EV.pspd : 1), life: sk.projLife * (EV && EV.pspd < 1 ? 1 / EV.pspd : 1), r: (sk.r || 2.5) * (EV ? EV.size : 1), H: HH, homing: !!(EV && EV.homing),")
rep("forked: !!o.forked,", "forked: !!o.forked, homing: !!o.homing,")
rep("    pr.x += pr.vx * dt; pr.y += pr.vy * dt; pr.life -= dt;",
    "    if (pr.homing && (g.tick + pr.id) % 3 === 0) { const t = nearestEnemy(g, pr.x, pr.y, 150, pr.hit); if (t) { const sp = Math.hypot(pr.vx, pr.vy), a0 = Math.atan2(pr.vy, pr.vx); let da = Math.atan2(t.y - pr.y, t.x - pr.x) - a0; while (da > Math.PI) da -= 2 * Math.PI; while (da < -Math.PI) da += 2 * Math.PI; const a1 = a0 + clamp(da, -0.35, 0.35); pr.vx = Math.cos(a1) * sp; pr.vy = Math.sin(a1) * sp; } }   // v0.16 evolution: homing\n"
    "    pr.x += pr.vx * dt; pr.y += pr.vy * dt; pr.life -= dt;")
# melee mutations
rep("    const full = trig || !!sk.full; const ang = tgt ? Math.atan2(tgt.y - oy, tgt.x - ox) : 0;",
    "    const full = trig || !!sk.full || !!(EV && EV.full); const ang = tgt ? Math.atan2(tgt.y - oy, tgt.x - ox) : 0;")
rep("      for (let hn = 0; hn < (sk.hits || 1) && !e.dead; hn++) hitEnemy(g, e, H, ctx);   // v0.8.2 double strike",
    "      for (let hn = 0; hn < (sk.hits || 1) && !e.dead; hn++) hitEnemy(g, e, H, ctx);   // v0.8.2 double strike\n"
    "      if (EV && EV.extraHit && !e.dead) hitEnemy(g, e, Object.assign({}, H, { dmg: H.dmg * EV.extraHit }), ctx);   // v0.16 combo")
rep("    if (M.scorched && tgt) maybeScorch(g, tgt.x, tgt.y, H, ctx);\n    ok = true;\n  }\n  else if (sk.kind === 'summon') {",
    "    if (M.scorched && tgt) maybeScorch(g, tgt.x, tgt.y, H, ctx);\n"
    "    if (EV && EV.wave && (tgt || trig)) spawnProjectile(g, { x: ox, y: oy, ang, speed: 290, life: 0.7, r: 5, H: Object.assign({}, H, { dmg: H.dmg * EV.wave }), pierce: 4, ctx, vis: 'evowave' });   // v0.16 blade wave\n"
    "    ok = true;\n  }\n  else if (sk.kind === 'summon') {")
# leap / dash / slam: combo + crush already through dmg; summon mutations
rep("    const n = Math.max(1, sk.perCast + (M.extraProj > 0 ? 0 : 0));",
    "    const n = Math.max(1, sk.perCast + (EV ? EV.perCast : 0));   // v0.16 legion")
rep("      if (mine.length >= sk.maxAlive + (s.flags.minionPlus ? 1 : 0)) { const old = mine.shift(); old.dead = true; }",
    "      if (mine.length >= Math.max(1, Math.round((sk.maxAlive + (EV ? EV.maxAdd : 0)) * (EV ? EV.maxMul : 1))) + (s.flags.minionPlus ? 1 : 0)) { const old = mine.shift(); old.dead = true; }")
rep("        speed: sk.mSpeed * (M.mSpd || 1), hitEvery: sk.mHit / (M.mSpd || 1), range: sk.mRange, r: sk.mR, face: 1, dead: false, ofs: g.rng() * 6.28 };",
    "        speed: sk.mSpeed * (M.mSpd || 1) * (EV ? EV.mspd : 1), hitEvery: sk.mHit / ((M.mSpd || 1) * (EV ? EV.mspd : 1)), range: sk.mRange, r: sk.mR, face: 1, dead: false, ofs: g.rng() * 6.28, burst: EV ? EV.burst : 0 };")
rep("    m.t += dt; if (m.t >= m.dur) { m.dead = true; continue; }", "    m.t += dt; if (m.t >= m.dur) { m.dead = true; if (m.burst) minionBurst(g, m); continue; }")
# echo queue after a successful cast
rep("  if (ok) {\n    g.stats.casts[skillId] = (g.stats.casts[skillId] || 0) + 1;",
    "  if (ok && EV && EV.echo) { const E0 = evoState(g); if (E0.q.length < 24) E0.q.push({ t: g.t + 0.5, id: skillId, inst, x: ox, y: oy, mul: EV.echo }); }   // v0.16 echo\n"
    "  if (ok) {\n    g.stats.casts[skillId] = (g.stats.casts[skillId] || 0) + 1;")
# credit: last auto skill to hit an enemy; elites / bosses also feed evolution by damage
rep("  g.stats.dmgBySource[H.src] = (g.stats.dmgBySource[H.src] || 0) + total;",
    "  g.stats.dmgBySource[H.src] = (g.stats.dmgBySource[H.src] || 0) + total;\n"
    "  if (g._autoSet && g._autoSet[H.src]) { e._la = H.src; if ((e.elite || e.def.ai === 'boss') && total > 0) evoGain(g, H.src, total / e.maxHp * (e.def.ai === 'boss' ? 30 : 4)); }   // v0.16 evolution credit")
rep("    forEnemiesIn(g, e.x, e.y, sp.r, (o) => { if (o !== e && !o.dead) hitEnemy(g, o, HS, S.ctx); });\n  }",
    "    forEnemiesIn(g, e.x, e.y, sp.r, (o) => { if (o !== e && !o.dead) hitEnemy(g, o, HS, S.ctx); });\n  }\n  evoKill(g, e, src);   // v0.16")
# three different elements → reactions +40%
rep("  if (REACTION_SRC[H.src]) amt *= s.reactionMul;   // P4 reactor passive (reaction damage)",
    "  if (REACTION_SRC[H.src]) amt *= s.reactionMul * (g._reso && g._reso.kind === 'tri' ? g._reso.react : 1);   // P4 reactor passive (reaction damage) · v0.16 三相共鳴")
# names for the damage breakdown
rep("  if (SKILLS[id]) return SKILLS[id].name + ' ' + SKILLS[id].en;", "  if (SKILLS[id]) return SKILLS[id].name + ' ' + SKILLS[id].en;\n  if (typeof id === 'string' && id.indexOf('fusion.') === 0 && FUSIONS[id.slice(7)]) return tr('融合：') + FUSIONS[id.slice(7)].name + ' ' + FUSIONS[id.slice(7)].en;   // v0.16")
rep("supportOk, supportBlock, socketOk, supportDead, autoSkillIds, AUTO_ROWS,", "supportOk, supportBlock, socketOk, supportDead, autoSkillIds, AUTO_ROWS, EVO_NEED, EVO_MUT, FUSIONS, FUSION_CD, evoGroup, evoMods, evoState, resonance, fireFusion, checkFusion,")

# ---------------- UI ----------------
# evo paths into the run
rep("  villageMode = false; lastAutoT = 0; lastWriteT = -1e9;",
    "  g.evoPaths = cur && cur.progress && cur.progress.evoPaths ? JSON.parse(JSON.stringify(cur.progress.evoPaths)) : {};   // v0.16\n"
    "  villageMode = false; lastAutoT = 0; lastWriteT = -1e9;")
# orb screen: evolution path picker + resonance line
rep("const st = statLine(sid); if (st) card.appendChild(st); }",
    "const st = statLine(sid); if (st) card.appendChild(st); const ev = evoLine(sid); if (ev) card.appendChild(ev); }")
rep("    card.appendChild(head(tr('自動技能'), 'prim', tr('全部自動出招，每招有自己嘅輔助珠'), false, on + '/' + have.length));",
    "    card.appendChild(head(tr('自動技能'), 'prim', tr('全部自動出招，每招有自己嘅輔助珠'), false, on + '/' + have.length));\n"
    "    { const R = C.resonance(g); card.appendChild(el('div', 'oreso' + (R ? ' on' : ''), R ? (R.kind === 'tri' ? tr('元素共鳴：三相（元素反應傷害 +40%）') : tr('元素共鳴：') + D.ELEMENTS[R.el].name + ' ×' + R.n + tr('（嗰種元素嘅自動技能傷害 +') + Math.round((R.dmg - 1) * 100) + '%）') : tr('元素共鳴：2 招同元素 +10%、3 招同元素 +25%、3 種唔同元素＝三相（反應 +40%）'))); }\n"
    "    if (!villageMode && g.evo && g.evo.fusion) { const F = C.FUSIONS[g.evo.fusion.key]; card.appendChild(el('div', 'oreso on fus', tr('✦ 融合奧義：') + F.name + tr('（每 ') + C.FUSION_CD + tr(' 秒自動爆發）'))); }")
UI = r"""
// ---------------- v0.16 evolution paths (orb screen) ----------------
function evoPickUi(sid) { const P = cur && cur.progress && cur.progress.evoPaths; const v = P && P[sid]; return Array.isArray(v) ? [v[0] ? 1 : 0, v[1] ? 1 : 0] : [0, 0]; }
function setEvoPick(sid, k, c) { commitVillage((s) => { s.progress = s.progress || {}; const P = s.progress.evoPaths = s.progress.evoPaths || {}; const v = Array.isArray(P[sid]) ? P[sid].slice(0, 2) : [0, 0]; v[k] = c; P[sid] = v; }); }
function evoLine(sid) {
  if (!sid || !g) return null; const sk = D.SKILLS[sid]; if (!sk || sk.kind === 'buff') return null;
  const G = C.EVO_MUT[C.evoGroup(sk)], pick = villageMode ? evoPickUi(sid) : (g.evoPaths && Array.isArray(g.evoPaths[sid]) ? g.evoPaths[sid] : [0, 0]), E0 = g.evo, st = (E0 && E0.stage[sid]) || 0, pts = (E0 && E0.pts[sid]) || 0;
  const box = el('div', 'oevo'); box.appendChild(el('span', 'oevt', tr('進化')));
  for (let k = 0; k < 2; k++) {
    box.appendChild(el('span', 'oevs', k ? 'II' : 'I'));
    for (let c = 0; c < 2; c++) { const m = G[k][c], on = (pick[k] ? 1 : 0) === c; const b = el('button', 'oevc' + (on ? ' on' : '') + (on && st > k ? ' got' : ''), m.name); b.title = m.desc; b.id = 'oEvo_' + sid.replace(/\./g, '_') + '_' + k + c;
      b.addEventListener('click', () => { if (!villageMode) { orbMsg = m.name + tr('：') + m.desc + tr('（進化路線要喺村莊改，下一局生效）'); renderOrbs(); return; } setEvoPick(sid, k, c); orbMsg = m.name + tr('：') + m.desc; renderOrbs(); }); box.appendChild(b); }
  }
  if (!villageMode) box.appendChild(el('span', 'oevp', st >= 2 ? tr('已進化 II') : Math.floor(pts) + ' / ' + C.EVO_NEED[st]));
  return box;
}
"""
rep("function orbLock(text) {", UI + "function orbLock(text) {")
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    ".oevo{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin:0 0 6px 26px;font-size:max(11px,calc(var(--u)*4.2))}.oevt{color:#9dff7a;font-weight:800}.oevs{color:#8a93a6;margin-left:4px}\n"
    ".oevc{min-height:26px;padding:0 8px;background:#141022;border:1px solid #3a3058;color:#c9d3e3;border-radius:3px;font-size:inherit}.oevc.on{border-color:#9dff7a;color:#e8ffe0}.oevc.got{background:#1f3a1a}.oevp{color:#9dff7a;margin-left:6px}\n"
    ".oreso{font-size:max(11px,calc(var(--u)*4.2));color:#8a93a6;margin:2px 0 6px}.oreso.on{color:#ffd23f}.oreso.fus{color:#ff9ce6}\n"
    "#gemrow .evb{display:inline-block;width:calc(var(--u)*12);height:calc(var(--u)*1.6);background:#2a2440;margin-left:calc(var(--u)*1.5);vertical-align:middle;position:relative}#gemrow .evb i{position:absolute;left:0;top:0;bottom:0;background:#9dff7a}\n"
    "#gemrow .evs{color:#9dff7a;font-weight:800;margin-left:calc(var(--u)*1)}#gemrow span.fus{border-color:#ffd23f;color:#ffe9a8}#gemrow span.fus .evb i{background:#ffd23f}")
# HUD: evolution bars on the auto skills + the fusion
rep("const s0 = add(sk.name + (sp.length ? ' +' + sp.length : ''), 'mod', D.ELEMENTS[elementOf(id, sp)].color); s0.prepend(gemIconEl(id));",
    "const s0 = add(sk.name + (sp.length ? ' +' + sp.length : ''), 'mod', D.ELEMENTS[elementOf(id, sp)].color); s0.prepend(gemIconEl(id)); "
    "if (C.autoSkillIds(g).indexOf(id) >= 0) { const st = (g.evo && g.evo.stage[id]) || 0; if (st) s0.appendChild(el('b', 'evs', st > 1 ? 'II' : 'I')); if (st < 2) { const bar = el('i', 'evb'), f = el('i'); f.id = 'evb_' + id.replace(/\\./g, '_'); bar.appendChild(f); s0.appendChild(bar); } }")
rep("    const free = p.gems.bag.filter((x) => !C.findSocket(g, x.uid)).length; if (free) add(tr('背包 ') + free + tr(' 粒'), 'empty');",
    "    if (g.evo && g.evo.fusion) { const F = C.FUSIONS[g.evo.fusion.key]; const sf = add('✦ ' + F.name, 'fus'); const bar = el('i', 'evb'), f = el('i'); f.id = 'evfus'; bar.appendChild(f); sf.appendChild(bar); }   // v0.16\n"
    "    const free = p.gems.bag.filter((x) => !C.findSocket(g, x.uid)).length; if (free) add(tr('背包 ') + free + tr(' 粒'), 'empty');")
rep("function updateHud() {\n  if (!g) return; const p = g.player;",
    "function updateHud() {\n  if (!g) return; const p = g.player;\n"
    "  { const E0 = g.evo, A = C.autoSkillIds(g); const key = A.map((id) => id + ':' + ((E0 && E0.stage[id]) || 0)).join(',') + '|' + (E0 && E0.fusion ? E0.fusion.key : '');   // v0.16 evolution HUD\n"
    "    if (hudCache.evoK !== key) { hudCache.evoK = key; hudCache.build = null; }\n"
    "    for (const id of A) { const f = document.getElementById('evb_' + id.replace(/\\./g, '_')); if (!f) continue; const st = (E0 && E0.stage[id]) || 0, lo = st ? C.EVO_NEED[0] : 0, hi = C.EVO_NEED[Math.min(1, st)], v = (E0 && E0.pts[id]) || 0; f.style.width = Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100)) + '%'; }\n"
    "    const ff = document.getElementById('evfus'); if (ff && E0 && E0.fusion) ff.style.width = Math.max(0, Math.min(100, 100 - E0.fusT / C.FUSION_CD * 100)) + '%'; }")
# codex: record + achievements + list
rep("function checkAch(s, gg) {\n",
    "function checkAch(s, gg) {\n"
    "  if (gg && gg.evo && gg.evo.fusion) { s.progress = s.progress || {}; const FZ = s.progress.fusions = s.progress.fusions || {}; if (!FZ[gg.evo.fusion.key]) FZ[gg.evo.fusion.key] = new Date().toISOString(); }   // v0.16 fusion codex\n")
rep("  { id: 'legend', name: tr('寶藏獵人'),",
    "  { id: 'evolve', name: tr('進化'), desc: tr('一局入面令一招技能進化到第 II 階'), gold: 150, run: (g) => !!(g.evo && Object.values(g.evo.stage).some((v) => v >= 2)) },   // v0.16\n"
    "  { id: 'fusion1', name: tr('融合'), desc: tr('第一次觸發融合奧義'), gold: 300, test: (s) => Object.keys(s.progress.fusions || {}).length >= 1 },\n"
    "  { id: 'fusion5', name: tr('融合研究者'), desc: tr('圖鑑發現 5 種融合奧義'), gold: 800, prog: (s) => [Object.keys(s.progress.fusions || {}).length, 5] },\n"
    "  { id: 'fusion15', name: tr('萬象歸一'), desc: tr('圖鑑發現全部 15 種融合奧義'), gold: 3000, prog: (s) => [Object.keys(s.progress.fusions || {}).length, 15] },\n"
    "  { id: 'legend', name: tr('寶藏獵人'),")
rep("  $('achCount').textContent = n + ' / ' + ACH.length;",
    "  $('achCount').textContent = n + ' / ' + ACH.length;\n"
    "  { const fz = s.progress.fusions || {}, keys = Object.keys(C.FUSIONS), nf = keys.filter((k) => fz[k]).length;   // v0.16 fusion codex\n"
    "    L.appendChild(el('h3', 'achsub', tr('融合圖鑑 ') + nf + ' / ' + keys.length));\n"
    "    L.appendChild(el('small', 'achnote', tr('兩招自動技能都進化到第 II 階就會融合；結果由兩招嘅元素決定。')));\n"
    "    for (const k of keys) { const F = C.FUSIONS[k], ok = !!fz[k]; const d = el('div', 'a' + (ok ? ' done' : '')); d.appendChild(el('span', 'ic', ok ? '✦' : '？'));\n"
    "      const t = el('div'); t.appendChild(el('b', null, ok ? F.name : '？？？')); t.appendChild(el('small', null, (ok ? F.els.map((x) => D.ELEMENTS[x].name).join(' ＋ ') + (F.els.length === 1 ? tr(' ＋ ') + D.ELEMENTS[F.els[0]].name : '') + ' · ' + F.desc : tr('未發現'))));\n"
    "      d.appendChild(t); L.appendChild(d); } }")
rep(".stgrid .cell:hover{border-color:#ffd23f}", ".stgrid .cell:hover{border-color:#ffd23f}\n#achList .achsub{grid-column:1/-1;color:#ffd23f;margin:10px 0 0}#achList .achnote{grid-column:1/-1;color:#8a93a6;display:block;margin-bottom:4px}")

EN.update({
    ' 進化 ': ' evolves ', '融合！': 'Fusion! ', '融合：': 'Fusion: ', '進化': 'Evolve', '已進化 II': 'Evolved II', '（進化路線要喺村莊改，下一局生效）': ' (change evolution paths in the village; applies next run)',
    '元素共鳴：三相（元素反應傷害 +40%）': 'Resonance: Trinity (reaction damage +40%)', '元素共鳴：': 'Resonance: ', '（嗰種元素嘅自動技能傷害 +': ' (auto skills of that element +',
    '元素共鳴：2 招同元素 +10%、3 招同元素 +25%、3 種唔同元素＝三相（反應 +40%）': 'Resonance: 2 skills of one element +10%, 3 of one element +25%, 3 different elements = Trinity (reactions +40%)',
    '✦ 融合奧義：': '✦ Fusion: ', '（每 ': ' (bursts every ', ' 秒自動爆發）': ' s)',
    '一局入面令一招技能進化到第 II 階': 'Evolve a skill to stage II in one run', '融合': 'Fusion', '第一次觸發融合奧義': 'Trigger your first fusion',
    '融合研究者': 'Fusion Scholar', '圖鑑發現 5 種融合奧義': 'Discover 5 fusions', '萬象歸一': 'All Is One', '圖鑑發現全部 15 種融合奧義': 'Discover all 15 fusions',
    '融合圖鑑 ': 'Fusion codex ', '兩招自動技能都進化到第 II 階就會融合；結果由兩招嘅元素決定。': 'Two auto skills at stage II fuse; the result depends on their elements.',
    '未發現': 'Not discovered', ' ＋ ': ' + ',
})
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok evolution', len(h))
h = open(dst, encoding='utf-8').read()
rep("    // v0.16: only into a row whose skill it actually helps (empty rows are left alone)\n",
    "    if (SUPPORTS[inst.id] && SUPPORTS[inst.id].convert) return false;   // v0.16: conversions change the element (and the fusion) — the player places them\n"
    "    // v0.16: only into a row whose skill it actually helps (empty rows are left alone)\n")
rep("const EVO_NEED = [40, 120];", "const EVO_NEED = [30, 90];")
EN['獲得'] = 'Got '
open(dst, 'w', encoding='utf-8').write(h); json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok tweaks')
