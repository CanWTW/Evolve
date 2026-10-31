#!/usr/bin/env python3
"""EVOLVE v0.15.2 -> v0.16.0 part A/B/C: bug fixes, socket rules, 3 auto slots, link source picker, new skills.
Usage: patch_p160a.py in.html out.html"""
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


def tr_rep(old_zh, new_zh, new_en, count=None):
    """replace a translated string everywhere it appears (as tr('...') or HTML text) and register its English"""
    global h
    n = h.count(old_zh)
    if n == 0 or (count is not None and n != count):
        raise SystemExit('tr_rep %r: %d' % (old_zh, n))
    h = h.replace(old_zh, new_zh)
    EN[new_zh] = new_en


# ======================= A. bug fixes =======================
# A1 Scorched Earth on every hit type (zones, meteor, chain, orbit, aura, mines, dash, minions...): hook in hitEnemy, 0.6 s per skill cooldown
rep("  if (!o.isDot) emit(g, 'Hit', { target: e.id, x: e.x, y: e.y, damage: total, element: H.element }, ctx);",
    "  if (!o.isDot) emit(g, 'Hit', { target: e.id, x: e.x, y: e.y, damage: total, element: H.element }, ctx);\n"
    "  if (!o.isDot && H.scorched && total > 0) maybeScorch(g, e.x, e.y, H, ctx);   // v0.16: every hit type (was projectiles / melee / leap only)")
# contagion spread marker (v0.16)
rep("function hitEnemy(g, e, H, ctx, o) {\n  if (e.dead || e.invuln) return 0;\n  o = o || {};",
    "function hitEnemy(g, e, H, ctx, o) {\n  if (e.dead || e.invuln) return 0;\n  o = o || {};\n"
    "  if (H.spread && !o.isDot) e._spr = { t: g.t + 4, H, ctx };   // v0.16 contagion: spreads when this enemy dies")
rep("function killEnemy(g, e, ctx, src) {\n  if (ctx && !src && ctx.skill) src = ctx.skill;\n  e.dead = true; e.hp = 0;",
    "function killEnemy(g, e, ctx, src) {\n  if (ctx && !src && ctx.skill) src = ctx.skill;\n  e.dead = true; e.hp = 0;\n"
    "  if (e._spr && e._spr.t > g.t && (e._spr.H.gen || 0) < e._spr.H.spread.gen) {   // v0.16 contagion\n"
    "    const S = e._spr, sp = S.H.spread, HS = Object.assign({}, S.H, { dmg: S.H.dmg * sp.mul, gen: (S.H.gen || 0) + 1 }); e._spr = null;\n"
    "    addFx(g, { type: 'nova', x: e.x, y: e.y, r: sp.r, dur: 0.35, color: '#9dff6a' });\n"
    "    forEnemiesIn(g, e.x, e.y, sp.r, (o) => { if (o !== e && !o.dead) hitEnemy(g, o, HS, S.ctx); });\n"
    "  }")
# A2 conversion onto the same element does nothing → not allowed
rep("  if (d.onlyTag && sk.tags.indexOf(d.onlyTag) < 0) return false;   // v0.15 反擊強化",
    "  if (d.onlyTag && sk.tags.indexOf(d.onlyTag) < 0) return false;   // v0.15 反擊強化\n"
    "  if (d.convert && d.convert === sk.element) return false;   // v0.16: converting fire to fire does nothing")
# A3 Ailment+ / Duration+ do nothing on pure physical skills (physical never applies ailments) unless a conversion is in the row
rep("ailChanceAdd: 0.3, ailPowerInc: 0.5, desc:", "needsElement: true, ailChanceAdd: 0.3, ailPowerInc: 0.5, desc:")
rep("    durationInc: 0.5, desc: tr('技能持續時間 +50%", "    needsElement: true, durOk: true, durationInc: 0.5, desc: tr('技能持續時間 +50%")
# A4 set pieces have no cost by design
rep("chk(u.cost && u.cost.length > 0, u.id + ' must have a cost (bible §5/§6)');", "chk(u.set || (u.cost && u.cost.length > 0), u.id + ' must have a cost (bible §5/§6)');")
# A5 link trigger counter was counted twice for projectile targets (multi-cast now has its own counter)
rep("    inst.n = (inst.n || 0) + 1;\n    let n = (sk.count || 1) + M.extraProj", "    inst.mc = (inst.mc || 0) + 1;\n    let n = (sk.count || 1) + M.extraProj")
rep("if (M.multi && inst.n % M.multi.everyN === 0)", "if (M.multi && inst.mc % M.multi.everyN === 0)")

# ======================= A6 socket rules =======================
rep("function roleAccepts(i, id) {",
    """function supportOk(supId, skillId, rowIds) {   // v0.16: support does something for this skill (in this row)
  if (!supportApplies(supId, skillId)) return false;
  const d = SUPPORTS[supId], sk = SKILLS[skillId];
  if (d.needsElement && sk.element === 'physical' && !(d.durOk && sk.tags.indexOf('duration') >= 0) && !(rowIds || []).some((id) => SUPPORTS[id] && SUPPORTS[id].convert)) return false;
  return true;
}
function rowOf(g, where) { const b = g.player.build; return where.area === 'main' ? b.mains[where.i] : where.area === 'link' ? b.links[where.i] : null; }
function rowSkillId(g, where) { const r = rowOf(g, where); if (!r) return null; return gemId(g, where.area === 'main' ? r.skill : r.to); }
function rowSupIds(g, row) { return row ? row.sup.map((u) => gemId(g, u)).filter(Boolean) : []; }
// why a support can't go into a row (null = fine). Empty row: the support must fit the row's role.
function supportBlock(g, where, supId, ignoreUid) {
  const row = rowOf(g, where); if (!row) return null; const sid = rowSkillId(g, where), d = SUPPORTS[supId]; if (!d) return null;
  const others = row.sup.filter((u) => u != null && u !== ignoreUid).map((u) => gemId(g, u)).filter(Boolean).concat([supId]);
  if (sid) return supportOk(supId, sid, others) ? null : d.name + tr(' 對 ') + SKILLS[sid].name + tr(' 冇效');
  const buffOnly = d.appliesTo.indexOf('buff') >= 0, role = where.area === 'main' ? slotRole(where.i) : 'link';
  if (role === 'buff' && !buffOnly) return tr('持續槽只可以放持續技能用嘅輔助珠');
  if (role !== 'buff' && buffOnly) return d.name + tr(' 只可以配持續技能');
  return null;
}
function socketOk(g, where, id) {   // full check used by the UI highlight
  const t = gemType(id); if (!socketAccepts(where, t, id)) return false;
  if (getSocket(g, where) === undefined) return false;
  if (t === 'support') return !supportBlock(g, where, id);
  return true;
}
function supportDead(g, where, uid) { const id = gemId(g, uid), sid = rowSkillId(g, where); return !!(id && sid && !supportOk(id, sid, rowSupIds(g, rowOf(g, where)))); }
function roleAccepts(i, id) {""")
rep("  if (where.area === 'link') return where.slot === 'to' ? type === 'active' : where.slot === 'trig'",
    "  if (where.area === 'link') return where.slot === 'to' ? type === 'active' && (id == null || (SKILLS[id] && SKILLS[id].kind !== 'buff')) : where.slot === 'trig'")
rep("  if (getSocket(g, where) === undefined) { g.lastSocketError = tr('呢個槽未解鎖'); return false; }",
    "  if (getSocket(g, where) === undefined) { g.lastSocketError = tr('呢個槽未解鎖'); return false; }\n"
    "  if (gemType(inst.id) === 'support') { const why = supportBlock(g, where, inst.id, uid); if (why) { g.lastSocketError = why; return false; } }   // v0.16")
rep("""    for (let pass = 0; pass < 2; pass++) {
      for (let i = 0; i < b.mains.length; i++) { const sk = gemId(g, b.mains[i].skill); if (pass === 0 ? !(sk && supportApplies(inst.id, sk)) : !!sk) continue; for (let j = 0; j < b.mains[i].sup.length; j++) if (tryAt({ area: 'main', i, slot: 'sup', j })) return true; }
      for (let i = 0; i < b.links.length; i++) { const sk = gemId(g, b.links[i].to); if (pass === 0 ? !(sk && supportApplies(inst.id, sk)) : !!sk) continue; for (let j = 0; j < b.links[i].sup.length; j++) if (tryAt({ area: 'link', i, slot: 'sup', j })) return true; }
    }""",
    """    // v0.16: only into a row whose skill it actually helps (empty rows are left alone)
    for (let i = 0; i < b.mains.length; i++) { const sk = gemId(g, b.mains[i].skill); if (!sk || !supportOk(inst.id, sk, rowSupIds(g, b.mains[i]).concat([inst.id]))) continue; for (let j = 0; j < b.mains[i].sup.length; j++) if (tryAt({ area: 'main', i, slot: 'sup', j })) return true; }
    for (let i = 0; i < b.links.length; i++) { const sk = gemId(g, b.links[i].to); if (!sk || !supportOk(inst.id, sk, rowSupIds(g, b.links[i]).concat([inst.id]))) continue; for (let j = 0; j < b.links[i].sup.length; j++) if (tryAt({ area: 'link', i, slot: 'sup', j })) return true; }""")
rep("  } else if (t === 'trigger') {\n    for (let i = 0; i < b.links.length; i++) if (tryAt({ area: 'link', i, slot: 'trig' })) return true;",
    "  } else if (t === 'trigger') {\n    for (let i = 0; i < b.links.length; i++) if (tryAt({ area: 'link', i, slot: 'trig' })) return true;")
# actives auto-socket: buffs never into link targets
rep("    for (let i = 0; i < b.links.length; i++) if (tryAt({ area: 'link', i, slot: 'to' })) return true;",
    "    if (SKILLS[inst.id] && SKILLS[inst.id].kind !== 'buff') for (let i = 0; i < b.links.length; i++) if (tryAt({ area: 'link', i, slot: 'to' })) return true;")

# ======================= B. skill bar: 3 auto slots =======================
rep("const SLOT_UNLOCKS = { mains: [[1, 3], [8, 4], [18, 5]], sup: [[1, 2], [6, 3], [20, 4], [40, 5]], moveSup: [[1, 1], [15, 2]], buffSup: [[1, 1]],",
    "const SLOT_UNLOCKS = { mains: [[1, 3], [6, 4], [8, 5], [14, 6], [18, 7]], sup: [[1, 2], [6, 3], [20, 4], [40, 5]], subSup: [[1, 2], [25, 3], [45, 4]], moveSup: [[1, 1], [15, 2]], buffSup: [[1, 1]],")
rep("  return { mains, sup: at(SLOT_UNLOCKS.sup), moveSup:", "  return { mains, sup: at(SLOT_UNLOCKS.sup), subSup: at(SLOT_UNLOCKS.subSup), moveSup:")
rep("function rowSup(S, i) { return i === 0 ? S.sup : i === 1 ? S.moveSup : S.buffSup; }",
    "function rowSup(S, i) { const r = slotRole(i); return r === 'primary' ? (i === 0 ? S.sup : S.subSup) : r === 'move' ? S.moveSup : S.buffSup; }   // v0.16 auto 1 / auto 2-3 / movement / persistent")
rep("function isMoveSkill(id) { const sk = SKILLS[id]; return !!sk && (sk.kind === 'leap' || sk.kind === 'dash'); }",
    "function isMoveSkill(id) { const sk = SKILLS[id]; return !!sk && (sk.kind === 'leap' || sk.kind === 'dash' || sk.kind === 'blink'); }")
rep("function slotRole(i) { return i === 0 ? 'primary' : i === 1 ? 'move' : 'buff'; }",
    "const AUTO_ROWS = [0, 3, 5];   // v0.16 build.mains: 0 auto1 · 1 movement · 2 buff1 · 3 auto2 (Lv6) · 4 buff2 (Lv8) · 5 auto3 (Lv14) · 6 buff3 (Lv18)\n"
    "function slotRole(i) { return AUTO_ROWS.indexOf(i) >= 0 ? 'primary' : i === 1 ? 'move' : 'buff'; }\n"
    "function autoSkillIds(g) { const b = g.player.build, out = []; for (const i of AUTO_ROWS) { const M = b.mains[i]; const id = M ? gemId(g, M.skill) : null; if (id && SKILLS[id] && SKILLS[id].kind !== 'buff') out.push(id); } return out; }")
tr_rep("tr('★主力槽唔可以放持續技能（持續技能放落面嘅持續槽）')", "tr('自動技能槽唔可以放持續技能（持續技能放落面嘅持續槽）')",
       "Auto skill slots can't hold persistent skills (put them in the persistent slots below)")
EN['自動技能槽唔可以放持續技能（持續技能放落面嘅持續槽）'] = EN.pop("tr('自動技能槽唔可以放持續技能（持續技能放落面嘅持續槽）')")
tr_rep("位移槽只可以放位移技能（跳躍重擊、衝刺打擊）", "位移槽只可以放位移技能（跳躍重擊、衝刺打擊、火焰衝刺、閃電傳送、冰霜閃現）",
       "The movement slot only takes movement skills (Leap Slam, Dash Strike, Flame Dash, Lightning Warp, Frostblink)")
rep("build: { mains: [newMain(2), newMain(1), newMain(1)], links: [], mainSup: 2, passives: [], layout: 2 }",
    "build: { mains: [newMain(2), newMain(1), newMain(1)], links: [], mainSup: 2, passives: [], layout: 3 }")
rep("if (id && b.layout === 2 && !roleAccepts(i, id))", "if (id && b.layout >= 2 && !roleAccepts(i, id))")
rep("passives: [null], layout: 2 },", "passives: [null], layout: 3 },")
rep("passives: (ch.build.passives || []).slice(), layout: 2 };", "passives: (ch.build.passives || []).slice(), layout: 3 };")
rep("  ch.build.layout = 2;\n", "  ch.build.layout = 3;\n")
# no more ★primary ×1.3 (three skills share the work now)
rep("  { const M0 = g.player.build && g.player.build.mains[0]; if (M0 && M0.skill != null && gemId(g, M0.skill) === sk.id && sk.kind !== 'buff') more *= 1.3; }   // v0.14 主力技能",
    "  // v0.16: the ★primary ×1.3 is gone — three auto skills share the work")
# battle rage / infusions: hits of any auto skill
rep("    const M0 = g.player.build.mains[0], pid = M0 && M0.skill != null ? gemId(g, M0.skill) : null;\n    if (pid && H.src === pid) { const p = g.player, R = s.raw;",
    "    if (autoSkillIds(g).indexOf(H.src) >= 0) { const p = g.player, R = s.raw;   // v0.16: any auto skill")
for zh, en in [('主力技能命中時額外造成 25% 冰冷傷害（可以冰緩、觸發元素反應）', 'Auto skill hits deal an extra 25% as cold damage (can chill and trigger reactions)'),
               ('主力技能命中時額外造成 25% 火焰傷害（可以施加燃燒、觸發元素反應）', 'Auto skill hits deal an extra 25% as fire damage (can ignite and trigger reactions)'),
               ('主力技能命中時額外造成 25% 閃電傷害（可以感電、觸發元素反應）', 'Auto skill hits deal an extra 25% as lightning damage (can shock and trigger reactions)'),
               ('主力技能命中疊戰意：每層 +2% 傷害，最多 20 層；2 秒冇命中會逐層流失', 'Auto skill hits build Rage: +2% damage per stack, up to 20; stacks fade after 2 s without a hit')]:
    tr_rep(zh, zh.replace('主力技能', '自動技能'), en)
tr_rep("tr('主力輔助槽 ')", "tr('自動技能 1 輔助槽 ')", 'Auto skill 1 support socket ')
EN['自動技能 1 輔助槽 '] = EN.pop("tr('自動技能 1 輔助槽 ')")
tr_rep("（★主力槽要有可以施放嘅技能先會觸發）", "（要有自動技能做來源先會觸發）", " (needs an auto skill as its source)")
# links: source = any auto skill the player picks (default auto 1); movement links / anySource unchanged
rep("function normalizeBuild(g) { const b = g.player.build; b.links.forEach((L) => { L.from = linkSourceId(g, TRIGGERS[gemId(g, L.trig)]); }); }",
    "function normalizeBuild(g) {   // v0.16: a link keeps the auto skill the player picked while it is still socketed; otherwise auto 1\n"
    "  const b = g.player.build, A = autoSkillIds(g);\n"
    "  b.links.forEach((L) => { const tg = TRIGGERS[gemId(g, L.trig)]; if (tg && (tg.anySource || tg.fromMove)) { L.from = linkSourceId(g, tg); return; } if (!(L.from && A.indexOf(L.from) >= 0)) L.from = A[0] || null; });\n}")
rep("function cycleLinkSource(g, li) { normalizeBuild(g); const L = g.player.build.links[li]; return L ? L.from : null; }   // v0.14: fixed to the main above",
    "function cycleLinkSource(g, li) {   // v0.16: next auto skill\n"
    "  normalizeBuild(g); const L = g.player.build.links[li]; if (!L) return null; const tg = TRIGGERS[gemId(g, L.trig)]; if (tg && (tg.anySource || tg.fromMove)) return L.from;\n"
    "  const A = autoSkillIds(g); if (!A.length) return null; L.from = A[(A.indexOf(L.from) + 1) % A.length]; return L.from;\n}")
# casting: only the movement slot waits for the player; auto rows cast anything castable
rep("    if (i > 0 && !g.autoMove && (sk.kind === 'leap' || sk.kind === 'dash')) { M.cd = 0; continue; }",
    "    if (i === 1 && !g.autoMove && isMoveSkill(id)) { M.cd = 0; continue; }   // v0.16: auto rows (0/3/5) cast movement skills too")
rep("    if (ok && i === 1 && (sk.kind === 'leap' || sk.kind === 'dash')) markLanding(g, id);", "    if (ok && i === 1 && isMoveSkill(id)) markLanding(g, id);")
rep("  const ms = g.player.build.mains; for (let i = ms.length > 1 ? 1 : 0; i < ms.length; i++) { const M = ms[i]; if (M.skill == null) continue; const id = gemId(g, M.skill); const sk = SKILLS[id]; if (sk && (sk.kind === 'leap' || sk.kind === 'dash')) return { M, id, sk }; }",
    "  const ms = g.player.build.mains; for (const i of [1]) { const M = ms[i]; if (!M || M.skill == null) continue; const id = gemId(g, M.skill); const sk = SKILLS[id]; if (sk && isMoveSkill(id)) return { M, id, sk }; }   // v0.16: the movement slot only")
# save fit: layout 2 → 3 (persistent rows move from 3/4 to 4/6; links stay on rows 0-3) and role check by slotRole
rep("    const isMv = (m) => { const k = kindOf(m); return k === 'leap' || k === 'dash'; };", "    const isMv = (m) => { const k = kindOf(m); return k === 'leap' || k === 'dash' || k === 'blink'; };")
rep("  if (b.layout !== 2) {   // v0.15 one-time reshuffle", "  if (b.layout !== 2 && b.layout !== 3) {   // v0.15 one-time reshuffle")
rep("  { const SK = C.DATA.SKILLS; b.mains.forEach((m, i) => { const id = idOf(m.skill); if (!id || !SK[id]) return; const k = SK[id].kind, mv = k === 'leap' || k === 'dash';\n"
    "      const ok = i === 0 ? k !== 'buff' : i === 1 ? mv : k === 'buff';",
    "  if (b.layout === 2) {   // v0.16 one-time: persistent rows 3/4 → 4/6 (new auto rows 3/5 start empty); links stay where they are\n"
    "    const old = b.mains.map((m) => ({ skill: m.skill, sup: (m.sup || []).slice() })), lk = b.mains.map((m) => m.link), map = [0, 1, 2, null, 3, null, 4];\n"
    "    const n = old.length <= 3 ? old.length : old.length === 4 ? 5 : 7;\n"
    "    b.mains = map.slice(0, n).map((oi, i) => ({ skill: oi != null && old[oi] ? old[oi].skill : null, sup: oi != null && old[oi] ? old[oi].sup : [], link: lk[i] === undefined ? null : lk[i] }));\n"
    "    b.layout = 3; log.push({ at, kind: 'layout-v16', gold: 0 });\n  }\n"
    "  { const SK = C.DATA.SKILLS; b.mains.forEach((m, i) => { const id = idOf(m.skill); if (!id || !SK[id]) return; const k = SK[id].kind, mv = k === 'leap' || k === 'dash' || k === 'blink';\n"
    "      const r = C.slotRole(i), ok = r === 'primary' ? k !== 'buff' : r === 'move' ? mv : k === 'buff';")
rep("    b.layout = 2; log.push({ at, kind: 'layout-v15', gold: 0 });", "    b.layout = 3; log.push({ at, kind: 'layout-v15', gold: 0 });")
# exports
rep("rowSup, isMoveSkill, roleAccepts, slotRole,", "rowSup, isMoveSkill, roleAccepts, slotRole, supportOk, supportBlock, socketOk, supportDead, autoSkillIds, AUTO_ROWS, cycleLinkSourceAuto: cycleLinkSource,")

# ======================= C. new skills =======================
NEW_SKILLS = r"""
// v0.16 new skills: spell movement (flame dash / lightning warp / frostblink), lightning melee, poison spread spell, poison minions
Object.assign(SKILLS, {
  'skill.flame_dash': { id: 'skill.flame_dash', version: 1, type: 'active', name: tr('火焰衝刺'), en: 'Flame Dash', icon: tr('焰'), attrs: SPELL_A, speedType: 'cast', kind: 'blink', element: 'fire',
    baseDamage: 9, cooldown: 1.5, range: 140, radius: 28, speed: 1100, trail: { r: 16, dur: 2.5, mul: 0.4 }, arrive: 1, ailChance: 0.4, tags: ['fire', 'movement', 'spell', 'aoe', 'duration'],
    desc: tr('化身火焰衝刺 140，沿路留低燃燒地面（每塊 40% 傷害，2.5 秒），落點爆炸（範圍 28）；40% 燃燒。衝刺時無敵。') },
  'skill.lightning_warp': { id: 'skill.lightning_warp', version: 1, type: 'active', name: tr('閃電傳送'), en: 'Lightning Warp', icon: tr('傳'), attrs: SPELL_A, speedType: 'cast', kind: 'blink', element: 'lightning',
    baseDamage: 15, cooldown: 2.1, range: 175, radius: 46, warp: true, arrive: 1, ailChance: 0.5, tags: ['lightning', 'movement', 'spell', 'aoe'],
    desc: tr('瞬間傳送 175，落點落雷（範圍 46）；50% 感電。最遠嘅位移技能。') },
  'skill.frostblink': { id: 'skill.frostblink', version: 1, type: 'active', name: tr('冰霜閃現'), en: 'Frostblink', icon: tr('閃'), attrs: SPELL_A, speedType: 'cast', kind: 'blink', element: 'cold',
    baseDamage: 10, cooldown: 1.7, range: 120, radius: 54, warp: true, depart: 1, arrive: 0.6, ailChance: 1, tags: ['cold', 'movement', 'spell', 'aoe'],
    desc: tr('閃現 120：原地留低冰霜爆發（範圍 54），落點再爆一次（60%）；必定冰緩。適合甩開包圍。') },
  'skill.lightning_strike': { id: 'skill.lightning_strike', version: 1, type: 'active', name: tr('雷霆打擊'), en: 'Lightning Strike', icon: tr('霆'), attrs: MELEE_A, speedType: 'attack', kind: 'melee', element: 'lightning',
    attack: true, weapons: MELEE_W, dmgEff: 1.0, speedMod: 1.05, baseDamage: 9, cooldown: 1, radius: 40, arcDeg: 80, castRange: 46, ailChance: 0.3,
    proj: { n: 4, mul: 0.5, speed: 300, life: 0.55, pierce: 0, spread: 0.3 }, tags: ['melee', 'lightning', 'attack', 'projectile'],
    desc: tr('閃電斬擊（傷害 100%），同時向前射出 4 道雷光（每道 50%）；30% 感電。') },
  'skill.contagion': { id: 'skill.contagion', version: 1, type: 'active', name: tr('瘟疫傳播'), en: 'Contagion', icon: tr('瘟'), attrs: SPELL_A, speedType: 'cast', kind: 'delayed', element: 'poison',
    baseDamage: 10, cooldown: 1.3, range: 220, radius: 40, delay: 0.25, spread: { r: 70, mul: 0.6, gen: 3 }, ailChance: 1, tags: ['poison', 'aoe', 'spell'],
    desc: tr('向最近嘅敵人釋放瘟疫（範圍 40），必定中毒。4 秒內被感染嘅敵人死亡時，瘟疫擴散到 70 範圍（60% 傷害，最多傳 3 代）。') },
  'skill.summon_spiders': { id: 'skill.summon_spiders', version: 1, type: 'active', name: tr('召喚毒蛛'), en: 'Summon Spiders', icon: tr('蛛'), attrs: SPELL_A, speedType: 'cast', kind: 'summon', element: 'poison',
    baseDamage: 4.5, cooldown: 1.4, perCast: 2, maxAlive: 8, duration: 12, mSpeed: 120, mHit: 0.6, mRange: 0, mR: 3, look: 'spider', ailChance: 0.6, tags: ['minion', 'poison', 'duration', 'spell'],
    desc: tr('每次召喚 2 隻毒蛛（最多 8 隻，維持 12 秒），快速撲向敵人咬（每 0.6 秒一下）；60% 中毒。') },
});
"""
rep("\nconst SUPPORTS = {", NEW_SKILLS + "const SUPPORTS = {")
for zh, en in [('火焰衝刺', 'Flame Dash'), ('閃電傳送', 'Lightning Warp'), ('冰霜閃現', 'Frostblink'), ('雷霆打擊', 'Lightning Strike'), ('瘟疫傳播', 'Contagion'), ('召喚毒蛛', 'Summon Spiders'),
               ('焰', 'Fl'), ('傳', 'Wp'), ('閃', 'Bk'), ('霆', 'LS'), ('瘟', 'Ct'), ('蛛', 'Sp'),
               ('化身火焰衝刺 140，沿路留低燃燒地面（每塊 40% 傷害，2.5 秒），落點爆炸（範圍 28）；40% 燃燒。衝刺時無敵。', 'Dash 140 as fire, leaving burning ground along the way (40% damage each, 2.5 s) and exploding where you land (radius 28); 40% ignite. Invulnerable while dashing.'),
               ('瞬間傳送 175，落點落雷（範圍 46）；50% 感電。最遠嘅位移技能。', 'Teleport 175; lightning strikes where you land (radius 46); 50% shock. The longest movement skill.'),
               ('閃現 120：原地留低冰霜爆發（範圍 54），落點再爆一次（60%）；必定冰緩。適合甩開包圍。', 'Blink 120: a frost burst where you were (radius 54) and another where you land (60%); always chills. Good for escaping.'),
               ('閃電斬擊（傷害 100%），同時向前射出 4 道雷光（每道 50%）；30% 感電。', 'A lightning slash (100% damage) that also fires 4 bolts forward (50% each); 30% shock.'),
               ('向最近嘅敵人釋放瘟疫（範圍 40），必定中毒。4 秒內被感染嘅敵人死亡時，瘟疫擴散到 70 範圍（60% 傷害，最多傳 3 代）。', 'Plague the nearest enemy (radius 40), always poisoning. An infected enemy that dies within 4 s spreads it within 70 (60% damage, up to 3 generations).'),
               ('每次召喚 2 隻毒蛛（最多 8 隻，維持 12 秒），快速撲向敵人咬（每 0.6 秒一下）；60% 中毒。', 'Summon 2 spiders per cast (up to 8, 12 s) that rush enemies and bite every 0.6 s; 60% poison.')]:
    EN.setdefault(zh, en)
# spread on the hit packet
rep("    durMul: M.dur, chillStacks: M.chillStacks, areaMul: M.area, scorched: M.scorched };",
    "    durMul: M.dur, chillStacks: M.chillStacks, areaMul: M.area, scorched: M.scorched };\n  if (sk.spread) H.spread = sk.spread;   // v0.16 contagion")
# blink cast
rep("  else if (sk.kind === 'chain') {   // v0.8.1: instant chain lightning",
    r"""  else if (sk.kind === 'blink') {   // v0.16 spell movement: flame dash (travels, burning trail) / lightning warp / frostblink (teleport)
    if (origin.fromPlayer && !trig && p.motion) return false;
    const tgt = trig ? null : origin.dir ? aimTarget(g, ox, oy, sk.range, origin.dir) : nearestEnemy(g, ox, oy, sk.range, null); if (!tgt && !trig && !origin.dir) return false;
    const sx = origin.fromPlayer ? p.x : ox, sy = origin.fromPlayer ? p.y : oy;
    const a = tgt ? Math.atan2(tgt.y - sy, tgt.x - sx) : origin.dir ? Math.atan2(origin.dir[1], origin.dir[0]) : Math.atan2(p.faceY, p.faceX);
    let len = trig || !origin.fromPlayer ? 0 : tgt ? Math.min(sk.range, Math.hypot(tgt.x - sx, tgt.y - sy)) : sk.range;
    let ex = clamp(sx + Math.cos(a) * len, ARENA.wall + 6, ARENA.W - ARENA.wall - 6), ey = clamp(sy + Math.sin(a) * len, ARENA.wall + 6, ARENA.H - ARENA.wall - 6);
    for (let k = 0; k < 12 && len > 0 && inWall(g, ex, ey); k++) { len *= 0.8; ex = clamp(sx + Math.cos(a) * len, ARENA.wall + 6, ARENA.W - ARENA.wall - 6); ey = clamp(sy + Math.sin(a) * len, ARENA.wall + 6, ARENA.H - ARENA.wall - 6); }
    const R = sk.radius * M.area;
    const boom = (x, y, mul) => { addFx(g, { type: 'nova', x, y, r: R, dur: 0.3, color: elc, skill: true }); if (sk.element === 'lightning') addFx(g, { type: 'lightning', pts: [[x + 2, y - 46], [x - 3, y - 20], [x, y]], dur: 0.18, color: elc, big: true });
      const HB = mul === 1 ? H : Object.assign({}, H, { dmg: H.dmg * mul }); forEnemiesIn(g, x, y, R, (e) => hitEnemy(g, e, HB, ctx)); };
    if (sk.depart) boom(sx, sy, sk.depart);
    const arrive = () => {
      if (sk.arrive) boom(ex, ey, sk.arrive);
      if (sk.trail && len > 0) { const n = Math.max(1, Math.round(len / 30)); for (let i = 0; i <= n; i++) { const t = i / n; spawnZone(g, { kind: 'burning', skill: skillId, x: sx + (ex - sx) * t, y: sy + (ey - sy) * t, r: sk.trail.r * M.area, dur: sk.trail.dur * M.dur, tick: 0.5, H: Object.assign({}, H, { dmg: H.dmg * sk.trail.mul }), ctx }); } }
    };
    if (len > 0 && origin.fromPlayer) { if (sk.warp) { addFx(g, { type: 'nova', x: sx, y: sy, r: 12, dur: 0.2, color: elc }); p.x = ex; p.y = ey; p.iframes = Math.max(p.iframes, 0.25); arrive(); } else startMotion(g, 'dash', ex, ey, Math.max(0.08, len / (sk.speed || 900)), arrive); }
    else arrive();
    ok = true;
  }
  else if (sk.kind === 'chain') {   // v0.8.1: instant chain lightning""")
# spider look
rep("  } else {\n    ctx.fillStyle = '#0a2a4a'; ctx.fillRect(x - 6, y - 4, 13, 7);",
    "  } else if (m.look === 'spider') {   // v0.16\n"
    "    const st = Math.floor(now * 14 + m.id) % 2; ctx.fillStyle = '#1c2a12'; for (let k = -1; k <= 1; k += 2) { ctx.fillRect(x + k * 3, y - 2 + st, k * 3, 1); ctx.fillRect(x + k * 3, y + 1 - st, k * 3, 1); }\n"
    "    ctx.fillStyle = '#2f4a1a'; ctx.fillRect(x - 3, y - 3, 6, 5); ctx.fillStyle = '#7dff6a'; ctx.fillRect(x - 2, y - 2, 4, 3); ctx.fillStyle = '#e8ff9a'; ctx.fillRect(x + 2 * m.face - (m.face < 0 ? 1 : 0), y - 3, 1, 1);\n"
    "  } else {\n    ctx.fillStyle = '#0a2a4a'; ctx.fillRect(x - 6, y - 4, 13, 7);")
# glyphs + shop
rep("  'skill.summon_skeletons': 'skel', 'skill.flame_spirits': 'spirit', 'skill.frost_wolf': 'wolf',",
    "  'skill.flame_dash': 'dash', 'skill.lightning_warp': 'bolt', 'skill.frostblink': 'flake', 'skill.lightning_strike': 'fblades', 'skill.contagion': 'spiral', 'skill.summon_spiders': 'skel',   // v0.16\n"
    "  'skill.summon_skeletons': 'skel', 'skill.flame_spirits': 'spirit', 'skill.frost_wolf': 'wolf',")
rep("  ['skill.summon_skeletons', 150], ['skill.flame_spirits', 150], ['skill.frost_wolf', 150],",
    "  ['skill.flame_dash', 160], ['skill.lightning_warp', 160], ['skill.frostblink', 160], ['skill.lightning_strike', 150], ['skill.contagion', 150], ['skill.summon_spiders', 150],   // v0.16\n"
    "  ['skill.summon_skeletons', 150], ['skill.flame_spirits', 150], ['skill.frost_wolf', 150],")

open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok A/B/C', len(h))

# --- appended fixes (audit round 2) ---
h = open(dst, encoding='utf-8').read()
def rep2(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:90]))
    h = h.replace(old, new)
# scorched also from ground-skill ticks (pools, fields, rain, auras)
rep2("  if (!o.isDot && H.scorched && total > 0) maybeScorch(", "  if ((!o.isDot || o.zoneTick) && H.scorched && total > 0) maybeScorch(")
rep2("hitEnemy(g, e, z.H, tctx, { isDot: true }); }", "hitEnemy(g, e, z.H, tctx, { isDot: true, zoneTick: true }); }")
# melee skills that throw projectiles (frost blades, lightning strike): multi-cast and fork work on their projectiles too
rep2("      const HP = Object.assign({}, H, { dmg: H.dmg * sk.proj.mul }); const n = sk.proj.n + M.extraProj;",
     "      inst.mc = (inst.mc || 0) + 1; const HP = Object.assign({}, H, { dmg: H.dmg * sk.proj.mul }); const n = sk.proj.n + M.extraProj + (M.multi && inst.mc % M.multi.everyN === 0 ? M.multi.extraProjectiles : 0);   // v0.16 multi-cast")
rep2("speed: sk.proj.speed * s.projSpeedMul, life: sk.proj.life, r: 2, H: HP, bounces: M.bounces, bounceRange: 80, pierce: sk.proj.pierce + M.pierce, ctx, vis: skillId });",
     "speed: sk.proj.speed * s.projSpeedMul, life: sk.proj.life, r: 2, H: HP, bounces: M.bounces, bounceRange: 80, pierce: sk.proj.pierce + M.pierce, fork: M.fork, forkMul: M.forkMul, ctx, vis: skillId });")
open(dst, 'w', encoding='utf-8').write(h)
print('ok audit-2 fixes')
