#!/usr/bin/env python3
"""EVOLVE v0.17.0 part A: gear redesign (item level really matters), full stat comparison, save schema 4 → 5 (proportional affix conversion).
Usage: patch_p170a.py in.html out.html"""
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


# ---------------- affix tiers: steeper ----------------
rep("""const ZONE_TIERS = {
  1: { flat: 1, pct: 1, reqLevel: 1, attr: [1, 4] },
  2: { flat: 1.6, pct: 1.3, reqLevel: 12, attr: [3, 7] },
  3: { flat: 2.4, pct: 1.6, reqLevel: 28, attr: [5, 10] },
  4: { flat: 3.3, pct: 1.9, reqLevel: 40, attr: [7, 13] },   // v0.8.5
  5: { flat: 4.3, pct: 2.3, reqLevel: 40, attr: [9, 16] },    // v0.10 遠古 Ancient (rift tiers)
  6: { flat: 5.6, pct: 2.8, reqLevel: 40, attr: [12, 20] },   // v0.10 太古 Primal (rift tier 10+)
};""",
"""const ZONE_TIERS = {   // v0.17: steeper so item level really matters (old values: flat 1/1.6/2.4/3.3/4.3/5.6, pct 1/1.3/1.6/1.9/2.3/2.8, attr 1–4 … 12–20)
  1: { flat: 1, pct: 1, reqLevel: 1, attr: [1, 4] },
  2: { flat: 1.8, pct: 1.35, reqLevel: 12, attr: [4, 9] },
  3: { flat: 2.8, pct: 1.75, reqLevel: 28, attr: [7, 14] },
  4: { flat: 4, pct: 2.2, reqLevel: 40, attr: [10, 19] },
  5: { flat: 5.4, pct: 2.7, reqLevel: 40, attr: [13, 24] },    // 遠古 Ancient
  6: { flat: 7, pct: 3.2, reqLevel: 40, attr: [17, 30] },      // 太古 Primal
};
const ZONE_TIERS_V4 = { 1: { flat: 1, pct: 1, attr: [1, 4] }, 2: { flat: 1.6, pct: 1.3, attr: [3, 7] }, 3: { flat: 2.4, pct: 1.6, attr: [5, 10] }, 4: { flat: 3.3, pct: 1.9, attr: [7, 13] }, 5: { flat: 4.3, pct: 2.3, attr: [9, 16] }, 6: { flat: 5.6, pct: 2.8, attr: [12, 20] } };   // save schema 4 → 5 conversion
// v0.17 base scaling by item level: weapon damage / spell power and implicits grow with the tier; legendary lines grow a little
const GEAR_SCALE = { base: { 1: 1, 2: 1.5, 3: 2.1, 4: 2.8, 5: 3.6, 6: 4.5 }, impPct: { 1: 1, 2: 1.2, 3: 1.4, 4: 1.6, 5: 1.8, 6: 2 }, uq: { 1: 1, 2: 1, 3: 1.1, 4: 1.2, 5: 1.35, 6: 1.6 } };
const FLAT_STATS = { damageFlat: 1, maxHpFlat: 1, regen: 1, STR: 1, AGI: 1, VIT: 1, INT: 1, DEX: 1, LUK: 1, bounces: 1, forkJumps: 1, extraProj: 1, triggerDepth: 1 };
const COUNT_STATS = { bounces: 1, forkJumps: 1, extraProj: 1, triggerDepth: 1 };   // never scaled""")

# tierOf is defined after ZONE_TIERS; helper functions after it
rep("const r2 = (v) => Math.round(v * 100) / 100;",
    "const r2 = (v) => Math.round(v * 100) / 100;\n"
    "function scaleImplicit(m, t) {   // v0.17\n"
    "  if (m.flag || !(m.value > 0) || COUNT_STATS[m.stat] || t <= 1) return m; const k = FLAT_STATS[m.stat] ? GEAR_SCALE.base[t] : GEAR_SCALE.impPct[t];\n"
    "  const v = m.value * k; return { stat: m.stat, value: FLAT_STATS[m.stat] && Number.isInteger(m.value) ? Math.round(v) : Math.round(v * 1000) / 1000 };\n"
    "}\n"
    "function scaleUnique(m, t) { if (m.flag || !(m.value > 0) || COUNT_STATS[m.stat] || GEAR_SCALE.uq[t] === 1) return m; const v = m.value * GEAR_SCALE.uq[t]; return { stat: m.stat, value: Number.isInteger(m.value) ? Math.round(v) : Math.round(v * 1000) / 1000 }; }\n"
    "const SPELL_BASE = { wand: 6, staff: 7 };   // v0.17 spell weapons: + spell base damage that grows with the item level (0 at tier 1)\n"
    "const WEAP_CACHE = {};\n"
    "function weaponAt(it) {   // the weapon stats of THIS item (base × item-level scaling)\n"
    "  const b = it && baseOf(it), w = b && b.weapon; if (!w) return null; const t = tierOf(it.ilvl); if (t <= 1) return w;\n"
    "  const k = b.id + '|' + t; if (WEAP_CACHE[k]) return WEAP_CACHE[k]; const S = GEAR_SCALE.base[t];\n"
    "  const o = Object.assign({}, w); if (w.min) { o.min = Math.round(w.min * S); o.max = Math.round(w.max * S); } if (w.spell) o.spellPower = Math.round(SPELL_BASE[w.cls] * (S - 1) * 10) / 10; return (WEAP_CACHE[k] = o);\n"
    "}")

# itemMods: implicits + unique lines scale with the tier
rep("  if (base) for (const m of base.implicit) out.push(m);",
    "  const T = tierOf(it.ilvl);\n  if (base) for (const m of base.implicit) out.push(scaleImplicit(m, T));   // v0.17")
rep("  if (it.unique) { const u = UNIQUES[it.unique]; for (const m of u.mods) out.push(m); for (const m of u.cost) out.push(m); }\n  return out;",
    "  if (it.unique) { const u = UNIQUES[it.unique]; for (const m of u.mods) out.push(scaleUnique(m, T)); for (const m of u.cost) out.push(m); }   // v0.17: legendary lines grow with the grade, costs stay\n  return out;")
# attack weapon uses the item's scaled stats
rep("function attackWeapon(g, sk) { const it = g.player.equip.weapon; const b = it && baseOf(it); const w = b && b.weapon;",
    "function attackWeapon(g, sk) { const it = g.player.equip.weapon; const w = weaponAt(it);")
# spells: + spell power from a spell weapon
rep("  else base = sk.baseDamage + s.damageFlat;\n  const R = s.raw || {}, F = s.flags || {};",
    "  else base = sk.baseDamage + s.damageFlat + (s.spellPower || 0);   // v0.17 wand / staff spell power\n  const R = s.raw || {}, F = s.flags || {};")
rep("    meleeWeapon: !!(eq.weapon && baseOf(eq.weapon) && baseOf(eq.weapon).weapon && baseOf(eq.weapon).weapon.melee),",
    "    meleeWeapon: !!(eq.weapon && baseOf(eq.weapon) && baseOf(eq.weapon).weapon && baseOf(eq.weapon).weapon.melee),\n"
    "    spellPower: (() => { const w = eq.weapon ? weaponAt(eq.weapon) : null; return w && w.spellPower ? w.spellPower : 0; })(),   // v0.17")
# describeItem: show the scaled weapon / implicit / legendary numbers
rep("  if (bd && bd.weapon) L.push({ text: bd.weapon.min ? WEAPON_NAMES[bd.weapon.cls]",
    "  const W0 = bd && bd.weapon ? weaponAt(it) : null, T0 = tierOf(it.ilvl);\n"
    "  if (W0 && W0.spellPower) L.push({ text: tr('法術基礎傷害 +') + W0.spellPower + tr('（物品等級越高越多）'), kind: 'implicit' });\n"
    "  if (bd && bd.weapon) L.push({ text: bd.weapon.min ? WEAPON_NAMES[bd.weapon.cls]")
h_desc_start = h.index("  if (bd && bd.weapon) L.push({ text: bd.weapon.min ? WEAPON_NAMES[bd.weapon.cls]")
h_desc_end = h.index("\n", h_desc_start)
line = h[h_desc_start:h_desc_end]
line2 = line.replace("bd.weapon.min + '–' + bd.weapon.max", "W0.min + '–' + W0.max")
if line2 == line:
    raise SystemExit('weapon line not patched')
h = h[:h_desc_start] + line2 + h[h_desc_end:]
rep("  if (it.reqLevel > 1) L.push({", "  if (!it.unique) L.push({ text: tr('物品等級 ') + T_(it) + ' · ' + [tr('鐵'), tr('青銅'), tr('霜銀'), tr('虛空'), tr('遠古'), tr('太古')][T_(it) - 1] + tr('（基礎數值 ×') + GEAR_SCALE.base[T_(it)] + tr('）'), kind: 'grade' });   // v0.17\n  if (it.reqLevel > 1) L.push({")
rep("function describeItem(it) {", "const T_ = (it) => tierOf(it.ilvl);\nfunction describeItem(it) {")
rep("  if (bd) for (const m of bd.implicit) L.push({ text: tr('基礎：') + statText(m), kind: 'implicit' });",
    "  if (bd) for (const m of bd.implicit) L.push({ text: tr('基礎：') + statText(scaleImplicit(m, T0)), kind: 'implicit' });")
# unique text: show scaled numbers by replacing them in the text when the grade multiplier is > 1
rep("  if (it.unique) { const u = UNIQUES[it.unique]; L.push({ text: u.text, kind: 'unique' });",
    "  if (it.unique) { const u = UNIQUES[it.unique]; L.push({ text: uniqueText(u, T0), kind: 'unique' });")
rep("function statText(m) {",
    "function uniqueText(u, t) {   // v0.17: the numbers in a legendary's text follow its grade (×1 / 1.1 / 1.2 / 1.35 / 1.6)\n"
    "  const k = GEAR_SCALE.uq[t] || 1; if (k === 1) return u.text;\n"
    "  return u.text.replace(/([+＋]?)(\\d+(?:\\.\\d+)?)(\\s*%)/g, (s, sg, n, pc) => sg + Math.round(+n * k * 10) / 10 + pc).replace(/([+＋])(\\d+)(?!\\d|\\.|\\s*%)/g, (s, sg, n) => sg + Math.round(+n * k)) + tr('（品級 ×') + k + tr('）');\n"
    "}\n"
    "function statText(m) {")
# sell value: a little more for higher items (unchanged table) — nothing to do
# exports
rep("ITEM_SELL, ILVL_SELL_MUL },", "ITEM_SELL, ILVL_SELL_MUL, ZONE_TIERS_V4, GEAR_SCALE },", 1)
rep("affixRange, affixValidRange, affixStackProblem,", "affixRange, affixValidRange, affixStackProblem, weaponAt, scaleImplicit, uniqueText,")

# ---------------- save schema 5: proportional affix conversion ----------------
rep("const SAVE_SCHEMA = 4;", "const SAVE_SCHEMA = 5;   // v0.17: 4 → 5 converts affix values to the new item-level tiers (MIGRATIONS[4])")
rep("const MIGRATIONS = { 1: migrate1to2, 2: migrate2to3, 3: migrate3to4 };",
    "function migrate4to5(s) {   // v0.17: every affix keeps its place inside its range — old tier range → new tier range (flat / pct: ×new/old; attributes: same fraction)\n"
    "  if (!isObj(s)) return s; const at = s.savedAt || null, ch = s.character, OLD = C.DATA.ZONE_TIERS_V4, NEW = C.DATA.ZONE_TIERS, AB = C.DATA.AFFIX_BY_ID; let n = 0;\n"
    "  const conv = (it) => { if (!isObj(it) || !Array.isArray(it.affixes)) return; const t = Math.min(6, Math.max(1, Number.isInteger(it.ilvl) ? it.ilvl : 1));\n"
    "    for (const a of it.affixes) { const d = isObj(a) && AB[a.id]; if (!d || typeof a.value !== 'number') continue; let v = a.value;\n"
    "      if (d.scale === 'flat') v = v * NEW[t].flat / OLD[t].flat; else if (d.scale === 'pct') v = v * NEW[t].pct / OLD[t].pct;\n"
    "      else if (d.scale === 'attr') { const o = OLD[t].attr, q = NEW[t].attr, f = o[1] > o[0] ? Math.max(0, Math.min(1, (v - o[0]) / (o[1] - o[0]))) : 1; v = q[0] + (q[1] - q[0]) * f; } else continue;\n"
    "      a.value = d.int ? Math.round(v) : Math.round(v * 100) / 100; n++; } };\n"
    "  if (isObj(ch)) { (isObj(ch.inventory) && Array.isArray(ch.inventory.items) ? ch.inventory.items : []).forEach(conv); if (isObj(ch.equipment)) Object.values(ch.equipment).forEach(conv); }\n"
    "  if (isObj(s.stash) && Array.isArray(s.stash.items)) s.stash.items.forEach(conv);\n"
    "  if (isObj(s.progress) && isObj(s.progress.collection)) Object.values(s.progress.collection).forEach(conv);\n"
    "  s.migrationLog = (Array.isArray(s.migrationLog) ? s.migrationLog : []).concat([{ at, kind: 'gear-v17', affixes: n, gold: 0 }]);\n"
    "  return s;\n}\n"
    "const MIGRATIONS = { 1: migrate1to2, 2: migrate2to3, 3: migrate3to4, 4: migrate4to5 };")

# ---------------- full comparison (UI) ----------------
a = h.index("const STAT_ROWS = [")
b = h.index("\n", a)
NEWROWS = r"""const pctF = (v) => Math.round(v * 1000) / 10 + '%', mulF = (v) => '×' + v.toFixed(2), intF = (v) => String(Math.round(v)), d1F = (v) => (Math.round(v * 10) / 10).toString();
// v0.17: every stat the gear can touch (row = [getter, label, +1 higher is better / −1 lower is better, format, group])
const STAT_ROWS = [
  [(s) => s.damageMul, tr('傷害倍率'), 1, mulF], [(s) => s.damageFlat, tr('技能基礎傷害 +'), 1, d1F], [(s) => s.spellPower || 0, tr('法術基礎傷害 +'), 1, d1F],
  [(s) => s.raw.spellInc || 0, tr('法術傷害 +'), 1, pctF], [(s) => s.raw.attackInc || 0, tr('攻擊傷害 +'), 1, pctF], [(s) => s.raw.meleeInc || 0, tr('近戰傷害 +'), 1, pctF], [(s) => s.raw.rangedInc || 0, tr('遠程傷害 +'), 1, pctF], [(s) => s.raw.minionInc || 0, tr('召喚物傷害 +'), 1, pctF],
  [(s) => s.elemMul.fire, tr('火焰傷害'), 1, mulF], [(s) => s.elemMul.cold, tr('冰冷傷害'), 1, mulF], [(s) => s.elemMul.lightning, tr('閃電傷害'), 1, mulF], [(s) => s.elemMul.poison, tr('毒素傷害'), 1, mulF], [(s) => s.reactionMul, tr('元素反應傷害'), 1, mulF],
  [(s) => s.speedMul.attack, tr('攻擊速度'), 1, mulF], [(s) => s.speedMul.cast, tr('施法速度'), 1, mulF], [(s) => s.critChance, tr('暴擊率'), 1, pctF], [(s) => s.critMul, tr('暴擊傷害'), 1, mulF], [(s) => s.accuracy, tr('命中 +'), 1, pctF],
  [(s) => s.areaMul, tr('範圍'), 1, pctF], [(s) => s.durationMul, tr('持續時間'), 1, pctF], [(s) => s.ailChanceAdd, tr('異常機率 +'), 1, pctF], [(s) => s.ailPowMul, tr('異常傷害'), 1, mulF], [(s) => s.projSpeedMul, tr('投射物速度'), 1, pctF], [(s) => s.chainRangeMul, tr('彈跳距離'), 1, pctF],
  [(s) => s.bounces, tr('彈跳 +'), 1, intF], [(s) => s.forkBonus, tr('分叉 +'), 1, intF], [(s) => s.extraProj, tr('額外投射物'), 1, intF], [(s) => s.triggerDepthBonus, tr('觸發深度 +'), 1, intF], [(s) => s.trigCdMul, tr('觸發冷卻'), -1, pctF],
  [(s) => s.maxHp, tr('最大生命'), 1, intF], [(s) => s.dmgReduction, tr('減傷'), 1, pctF], [(s) => s.evasion, tr('閃避'), 1, pctF], [(s) => s.raw.blockChance || 0, tr('格擋'), 1, pctF], [(s) => s.regen, tr('每秒回復'), 1, d1F], [(s) => s.raw.lifeLeech || 0, tr('生命偷取'), 1, pctF], [(s) => s.dodgeCdMul, tr('閃避冷卻'), -1, pctF],
  [(s) => s.moveSpeed, tr('移速'), 1, intF], [(s) => s.pickupRadius, tr('拾取範圍'), 1, intF], [(s) => s.dropMul, tr('掉寶率'), 1, mulF], [(s) => s.rarityMul, tr('稀有度'), 1, mulF], [(s) => s.goldMul, tr('金幣'), 1, mulF], [(s) => s.xpMul, tr('經驗'), 1, mulF],
  [(s) => s.attr.STR, tr('力量'), 1, intF], [(s) => s.attr.AGI, tr('敏捷'), 1, intF], [(s) => s.attr.VIT, tr('體力'), 1, intF], [(s) => s.attr.INT, tr('智力'), 1, intF], [(s) => s.attr.DEX, tr('靈巧'), 1, intF], [(s) => s.attr.LUK, tr('幸運'), 1, intF],
];
const STAT_LIST_ALWAYS = 11;   // the first rows (and every non-default one) show in the stats list"""
h = h[:a] + NEWROWS + h[b:]
rep("const fmtStat = (row, v) => (row[3] ? row[3](v) : (Math.round(v * 10) / 10).toString());",
    "const fmtStat = (row, v) => (row[3] ? row[3](v) : (Math.round(v * 10) / 10).toString());\n"
    "function autoHitLines(eq, ns) {   // v0.17: each auto skill's damage per hit with the current gear vs. the compared gear\n"
    "  const out = [], p = g.player; for (const id of C.autoSkillIds(g)) { const sk = C.skillAt ? C.skillAt(id, 1) : D.SKILLS[id];\n"
    "    const fa = { player: p, t: g.t }, fb = { player: Object.assign({}, p, { equip: eq, stats: ns }), t: g.t }; const a = C.skillDamage(fa, sk), b = C.skillDamage(fb, sk);\n"
    "    if (Math.abs(a - b) > 0.05) out.push([sk.name + tr(' 每下'), a, b]); } return out;\n}")
rep("    for (const r of STAT_ROWS) { const a = p.stats[r[0]], b = ns[r[0]]; if (Math.abs(a - b) > 1e-6) { const better = (b - a) * r[2] > 0; parts.push(el('span', better ? 'up' : 'dn', (better ? '▲' : '▼') + r[1] + ' ' + fmtStat(r, a) + '→' + fmtStat(r, b) + '  ')); } }",
    "    for (const [nm, a, b] of autoHitLines(eq, ns)) { const better = b > a; parts.push(el('span', (better ? 'up' : 'dn') + ' big', (better ? '▲' : '▼') + nm + ' ' + a.toFixed(1) + '→' + b.toFixed(1) + '  ')); }   // v0.17\n"
    "    for (const r of STAT_ROWS) { const a = r[0](p.stats), b = r[0](ns); if (Math.abs(a - b) > 1e-6) { const better = (b - a) * r[2] > 0; parts.push(el('span', better ? 'up' : 'dn', (better ? '▲' : '▼') + r[1] + ' ' + fmtStat(r, a) + '→' + fmtStat(r, b) + '  ')); } }")
rep("  const sl = el('div', 'statlist'); for (const r of STAT_ROWS) sl.append(el('span', null, r[1]), el('b', null, fmtStat(r, p.stats[r[0]])));",
    "  const base = C.computeStats(Object.assign({}, p, { talents: [], boons: [] }), {});   // v0.17: rows that differ from 'nothing equipped' (or the first ones) are listed\n"
    "  const sl = el('div', 'statlist'); STAT_ROWS.forEach((r, i) => { const v = r[0](p.stats); if (i < STAT_LIST_ALWAYS || Math.abs(v - r[0](base)) > 1e-6) sl.append(el('span', null, r[1]), el('b', null, fmtStat(r, v))); });")
rep(".stgrid .cell:hover{border-color:#ffd23f}", ".stgrid .cell:hover{border-color:#ffd23f}\n.diff .big{font-weight:800}   /* v0.17 */")

EN.update({'物品等級 ': 'Item level ', '（基礎數值 ×': ' (base values ×', '鐵': 'Iron', '青銅': 'Bronze', '霜銀': 'Frost-silver', '虛空': 'Void', '太古': 'Primal', '遠古': 'Ancient', '法術基礎傷害 +': 'Spell base damage +', '（物品等級越高越多）': ' (grows with item level)', '（品級 ×': ' (grade ×', '法術傷害 +': 'Spell damage +', '攻擊傷害 +': 'Attack damage +',
           '近戰傷害 +': 'Melee damage +', '遠程傷害 +': 'Ranged damage +', '召喚物傷害 +': 'Minion damage +', '火焰傷害': 'Fire damage', '冰冷傷害': 'Cold damage', '閃電傷害': 'Lightning damage', '毒素傷害': 'Poison damage',
           '元素反應傷害': 'Reaction damage', '攻擊速度': 'Attack speed', '施法速度': 'Cast speed', '暴擊傷害': 'Crit damage', '異常傷害': 'Ailment damage', '投射物速度': 'Projectile speed', '彈跳距離': 'Chain range',
           '觸發冷卻': 'Trigger cooldown', '格擋': 'Block', '每秒回復': 'Regen / s', '生命偷取': 'Life leech', '閃避冷卻': 'Dodge cooldown', '拾取範圍': 'Pickup radius', '金幣': 'Gold', '經驗': 'XP',
           '力量': 'STR', '敏捷': 'AGI', '體力': 'VIT', '智力': 'INT', '靈巧': 'DEX', '幸運': 'LUK'})
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok A gear', len(h))
# balance: gear now grows faster with the zone → zones 2–4 tougher (Z2/Z3/Z4 sims: player DPS +10–35%, EHP +11–29%)
h = open(dst, encoding='utf-8').read()
for old, new in [("recLevel: 12, hpMul: 3.25, dmgMul: 1.45,", "recLevel: 12, hpMul: 3.75, dmgMul: 1.6,"), ("recLevel: 26, hpMul: 8.45, dmgMul: 2.1,", "recLevel: 26, hpMul: 10.1, dmgMul: 2.5,"), ("recLevel: 40, hpMul: 16.9, dmgMul: 2.8,", "recLevel: 40, hpMul: 21.1, dmgMul: 3.5,"),
                 ("const SPELL_BASE = { wand: 6, staff: 7 };", "const SPELL_BASE = { wand: 8, staff: 9 };")]:
    assert h.count(old) == 1, old; h = h.replace(old, new)
open(dst, 'w', encoding='utf-8').write(h); print('ok zone balance v0.17')
