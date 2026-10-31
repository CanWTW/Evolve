#!/usr/bin/env python3
"""EVOLVE v0.17.0 -> v0.17.1: save repair + recovery of saves 0.17.0 rejected, audio unlock on mobile / after interruptions,
resonance + fusion use the converted element, orb filters by category, gear level requirements + catch-up XP.
Usage: patch_p171.py in.html out.html"""
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


rep("<title>PROJECT: EVOLVE — 原型 0.17.0</title>", "<title>PROJECT: EVOLVE — 原型 0.17.1</title>")
rep("瀏覽器測試版 0.17.0 — 持續更新中", "瀏覽器測試版 0.17.1 — 持續更新中", 3)
rep("Browser beta 0.17.0", "Browser beta 0.17.1", 2)
rep("const VERSION = '0.17.0';", "const VERSION = '0.17.1';")
EN['瀏覽器測試版 0.17.1 — 持續更新中'] = 'Browser beta 0.17.1 — updated often'

# ---------------- 1. saves: clamp after conversion; repair out-of-range affixes instead of rejecting the file ----------------
rep("      a.value = d.int ? Math.round(v) : Math.round(v * 100) / 100; n++; } };",
    "      const [lo, hi] = C.affixValidRange(d, t); v = Math.max(lo, Math.min(hi, v));   // v0.17.1: old values were rounded up, ×new/old could pass the new top\n"
    "      a.value = d.int ? Math.round(v) : Math.floor(v * 100 + 1e-9) / 100; if (a.value < lo) a.value = lo; n++; } };")
rep("  function prepare(info, at) {\n    if (!info.ok || info.newer) return info;\n    let d; try { d = migrateSave(info.data, target, migrations); } catch (e) { return { ok: false, error: 'migration: ' + e.message }; }",
    "  function prepare(info, at) {\n    if (!info.ok || info.newer) return info;\n    let d; try { d = migrateSave(info.data, target, migrations); } catch (e) { return { ok: false, error: 'migration: ' + e.message }; }\n"
    "    try { if (validateSave(d).length) repairAffixRanges(d, at || now()); } catch (e) { /* validation below decides */ }   // v0.17.1: a value just outside its range is clamped, never a lost save")
rep("function migrate4to5(s) {",
    "function repairAffixRanges(s, at) {   // v0.17.1: clamp every known affix into the range its item level allows (logged)\n"
    "  const AB = C.DATA.AFFIX_BY_ID, ch = s && s.character; let n = 0; if (!isObj(ch)) return 0;\n"
    "  const fix = (it) => { if (!isObj(it) || !Array.isArray(it.affixes)) return; for (const a of it.affixes) { const d = isObj(a) && AB[a.id]; if (!d || typeof a.value !== 'number' || !isFinite(a.value)) continue;\n"
    "    const [lo, hi] = C.affixValidRange(d, it.ilvl); let v = Math.max(lo, Math.min(hi, a.value)); v = d.int ? Math.round(v) : Math.round(v * 100) / 100; if (v > hi) v = Math.floor(hi * 100) / 100; if (v < lo) v = lo;\n"
    "    if (d.int && !Number.isInteger(v)) v = Math.round(v); if (v !== a.value) { a.value = v; n++; } } };\n"
    "  (isObj(ch.inventory) && Array.isArray(ch.inventory.items) ? ch.inventory.items : []).forEach(fix); if (isObj(ch.equipment)) Object.values(ch.equipment).forEach(fix);\n"
    "  if (isObj(s.stash) && Array.isArray(s.stash.items)) s.stash.items.forEach(fix); if (isObj(s.progress) && isObj(s.progress.collection)) Object.values(s.progress.collection).forEach(fix);\n"
    "  if (n) s.migrationLog = (Array.isArray(s.migrationLog) ? s.migrationLog : []).concat([{ at: at || null, kind: 'affix-clamped', count: n, gold: 0 }]); return n;\n"
    "}\n"
    "function migrate4to5(s) {")
# recovery of a .corrupt copy that loads now
rep("  function isReadOnly(slot) { checkSlot(slot);",
    "  function peekCorrupt(slot) {   // v0.17.1: a rejected file that this version can load → summary, else null\n"
    "    checkSlot(slot); const raw = get(keys(slot).corrupt); if (raw == null) return null; const p = prepare(inspect(raw), now()); if (!p.ok || p.newer) return null;\n"
    "    const ch = p.data.character; return { name: ch.name, level: ch.level, savedAt: p.data.savedAt, items: (ch.inventory.items || []).length + ((p.data.stash && p.data.stash.items) || []).length };\n"
    "  }\n"
    "  function restoreCorrupt(slot, toSlot) {\n"
    "    checkSlot(slot); checkSlot(toSlot); const k = keys(slot), raw = get(k.corrupt); if (raw == null) return { ok: false, reason: 'none' };\n"
    "    const p = prepare(inspect(raw), now()); if (!p.ok) return { ok: false, reason: 'invalid', error: p.error }; const d = p.data; d.slot = toSlot;\n"
    "    d.migrationLog = (d.migrationLog || []).concat([{ at: now(), kind: 'restored-from-corrupt', from: slot }]);\n"
    "    const w = writeRaw(toSlot, d, false); if (w.ok) del(k.corrupt); return w;\n"
    "  }\n"
    "  function isReadOnly(slot) { checkSlot(slot);")
rep("  return { SLOT_COUNT, schemaVersion: target, keys, indexKey: INDEX_KEY, inspect, peek, save, load, listSlots, deleteSlot, createCharacter, exportCode, decodeCode, importCode, isReadOnly };",
    "  return { SLOT_COUNT, schemaVersion: target, keys, indexKey: INDEX_KEY, inspect, peek, save, load, listSlots, deleteSlot, createCharacter, exportCode, decodeCode, importCode, isReadOnly, peekCorrupt, restoreCorrupt };")
rep("  const L = $('slotList'); L.textContent = '';\n  for (let i = 0; i < 3; i++) {",
    "  const L = $('slotList'); L.textContent = '';\n"
    "  for (let i = 0; i < 3; i++) { const rc = saves.peekCorrupt(i); if (!rc) continue;   // v0.17.1 recover a character an update could not load\n"
    "    const empty = [0, 1, 2].find((j) => { const q = saves.peek(j); return !q || q.corrupt; }); const to = empty != null ? empty : i;\n"
    "    const box = el('div', 'slotc rec'); box.appendChild(el('div', 'sk', tr('可以恢復嘅舊角色')));\n"
    "    box.appendChild(el('div', 'sn', (rc.name || tr('旅人')) + ' Lv ' + (rc.level || 1))); box.appendChild(el('div', 'sm', tr('上次儲存 ') + fmtSavedAt(rc.savedAt) + tr(' · 裝備 ') + rc.items + tr(' 件')));\n"
    "    const b = el('button', 'primary', empty != null ? tr('恢復到存檔位 ') + (to + 1) : (slotRecArmed === i ? tr('⚠ 再撳一次：覆蓋存檔位 ') + (to + 1) : tr('恢復（會覆蓋存檔位 ') + (to + 1) + tr('）'))); b.id = 'slotRec' + i;\n"
    "    b.addEventListener('click', () => { if (empty == null && slotRecArmed !== i) { slotRecArmed = i; renderSlots(); return; } slotRecArmed = -1; const r = saves.restoreCorrupt(i, to);\n"
    "      if (r.ok) { setSlot(to); loadCurrent(); updateSaveUi(); slotMsg(tr('已經恢復：') + (rc.name || '') + ' Lv ' + rc.level); } else slotMsg(tr('恢復失敗：') + (r.error || r.reason)); renderSlots(); });\n"
    "    box.appendChild(b); L.appendChild(box); }\n"
    "  for (let i = 0; i < 3; i++) {")
rep("function openSlots() {", "let slotRecArmed = -1;\nfunction recoverableSlots() { const out = []; for (let i = 0; i < 3; i++) { try { if (saves.peekCorrupt(i)) out.push(i); } catch (e) { /* ignore */ } } return out; }\nfunction openSlots() {")
# title hint
rep("  const ts = document.getElementById('titleSave');",
    "  { const w = document.getElementById('titleWarn'); if (w && !saveFail) { const rs = recoverableSlots(); if (rs.length) { w.textContent = tr('發現可以恢復嘅舊角色：去「角色 Characters」畫面撳「恢復」。'); w.classList.remove('hidden'); } } }   // v0.17.1\n"
    "  const ts = document.getElementById('titleSave');")
rep(".stgrid .cell:hover{border-color:#ffd23f}", ".stgrid .cell:hover{border-color:#ffd23f}\n.slotc.rec{border-color:#9dff7a!important;background:#132a14}   /* v0.17.1 */")

# ---------------- 2. audio: resume on the gestures mobile browsers accept, after interruptions, when the tab returns ----------------
rep("  function unlock() { if (!ensure()) return; if (ac.state === 'suspended') ac.resume(); if (musicKey && !seqTimer) music(musicKey); }",
    "  let primed = false;\n"
    "  function unlock() {   // v0.17.1: resume from 'suspended' AND 'interrupted' (iOS after a call / lock / app switch); prime iOS with a silent buffer\n"
    "    if (!ensure()) return; if (ac.state !== 'running') { try { const pr = ac.resume(); if (pr && pr.then) pr.then(() => { if (musicKey && !seqTimer) music(musicKey); }).catch(() => {}); } catch (e) { /* ignore */ } }\n"
    "    if (!primed) { try { const b = ac.createBuffer(1, 1, 22050), s = ac.createBufferSource(); s.buffer = b; s.connect(ac.destination); s.start(0); primed = true; } catch (e) { /* ignore */ } }\n"
    "    if (musicKey && !seqTimer && ac.state === 'running') music(musicKey);\n"
    "  }")
rep("document.addEventListener('pointerdown', () => SFX.unlock(), true);",
    "for (const ev of ['pointerdown', 'pointerup', 'touchend', 'click', 'mousedown']) document.addEventListener(ev, () => SFX.unlock(), true);   // v0.17.1: mobile only accepts touchend / click\n"
    "document.addEventListener('visibilitychange', () => { if (!document.hidden) SFX.unlock(); });")

# ---------------- 3. resonance / fusion use the element after conversion supports ----------------
rep("function skillEl(g, id) { return (g.evo && g.evo.el[id]) || SKILLS[id].element; }",
    "function skillEl(g, id) {   // v0.17.1: from the skill's own row (conversion supports included), not the last cast\n"
    "  const b = g.player.build; for (const i of AUTO_ROWS) { const M = b.mains[i]; if (M && M.skill != null && gemId(g, M.skill) === id) { try { return skillMods(g, id, instSupIds(g, M), gemLevel(g, M.skill)).element || SKILLS[id].element; } catch (e) { break; } } }\n"
    "  return (g.evo && g.evo.el[id]) || SKILLS[id].element;\n}")

# ---------------- 4. orb filters by category ----------------
rep("function orbFiltOk(x, f) { return f === 'all' || (f === 'free' ? !C.findSocket(g, x.uid) : C.gemType(x.id) === f); }",
    "const ORB_CAT = { melee: (sk) => sk.attack && sk.weapons && !sk.weapons.some((w) => ['bow', 'darts', 'pistol'].indexOf(w) >= 0) && sk.kind !== 'leap' && sk.kind !== 'dash', ranged: (sk) => sk.attack && sk.weapons && sk.weapons.some((w) => ['bow', 'darts', 'pistol'].indexOf(w) >= 0),\n"
    "  spell: (sk) => !sk.attack && sk.kind !== 'buff' && sk.kind !== 'summon' && sk.kind !== 'blink', minion: (sk) => sk.kind === 'summon', buff: (sk) => sk.kind === 'buff', move: (sk) => C.isMoveSkill(sk.id) };   // v0.17.1\n"
    "function orbFiltOk(x, f) { if (ORB_CAT[f]) { const sk = D.SKILLS[x.id]; return !!sk && ORB_CAT[f](sk); } if (f === 'useful') { const t = C.gemType(x.id); if (t !== 'support') return false; return C.AUTO_ROWS.some((i) => { const M = g.player.build.mains[i], sid = M && C.gemId(g, M.skill); return sid && C.supportOk(x.id, sid, []); }); }\n"
    "  return f === 'all' || (f === 'free' ? !C.findSocket(g, x.uid) : C.gemType(x.id) === f); }")
rep("  for (const [f, label] of [['all', tr('全部')], ['active', tr('主動')], ['support', tr('輔助')], ['trigger', tr('觸發')], ['passive', tr('被動')], ['free', tr('未鑲')]]) {",
    "  for (const [f, label] of [['all', tr('全部')], ['active', tr('主動')], ['melee', tr('近戰')], ['ranged', tr('遠程')], ['spell', tr('法術')], ['minion', tr('召喚')], ['buff', tr('持續')], ['move', tr('位移')], ['support', tr('輔助')], ['useful', tr('有用輔助')], ['trigger', tr('觸發')], ['passive', tr('被動')], ['free', tr('未鑲')]]) {")
rep("    const n = cnt(f); const fb = el('button', orbFilter === f ? 'on' : null, label + ' ' + n);",
    "    const n = cnt(f); if (!n && f !== 'all' && orbFilter !== f && ORB_CAT[f] !== undefined) continue;   // v0.17.1: empty categories hidden\n    const fb = el('button', orbFilter === f ? 'on' : null, label + ' ' + n);")

# ---------------- 5. gear requirements follow zone progress; catch-up XP ----------------
rep("  2: { flat: 1.8, pct: 1.35, reqLevel: 12, attr: [4, 9] },\n  3: { flat: 2.8, pct: 1.75, reqLevel: 28, attr: [7, 14] },\n  4: { flat: 4, pct: 2.2, reqLevel: 40, attr: [10, 19] },\n  5: { flat: 5.4, pct: 2.7, reqLevel: 40, attr: [13, 24] },    // 遠古 Ancient\n  6: { flat: 7, pct: 3.2, reqLevel: 40, attr: [17, 30] },      // 太古 Primal",
    "  2: { flat: 1.8, pct: 1.35, reqLevel: 8, attr: [4, 9] },     // v0.17.1 requirements 12/28/40 → 8/18/30 (pushing zones outpaced levels)\n  3: { flat: 2.8, pct: 1.75, reqLevel: 18, attr: [7, 14] },\n  4: { flat: 4, pct: 2.2, reqLevel: 30, attr: [10, 19] },\n  5: { flat: 5.4, pct: 2.7, reqLevel: 30, attr: [13, 24] },    // 遠古 Ancient\n  6: { flat: 7, pct: 3.2, reqLevel: 30, attr: [17, 30] },      // 太古 Primal")
# owned items take the new requirement (computed from the item level)
rep("  const it = { uid: newUid(g, 'i'), slot: type, base, rarity, ilvl, reqLevel: ZONE_TIERS[ilvl].reqLevel,", "  const it = { uid: newUid(g, 'i'), slot: type, base, rarity, ilvl, reqLevel: ZONE_TIERS[ilvl].reqLevel,")
rep("  if ((item.reqLevel || 1) > p.level) return { ok: false, reason: tr('需要等級 ') + item.reqLevel + tr('（而家 Lv') + p.level + tr('）') };",
    "  const rq = itemReq(item); if (rq > p.level) return { ok: false, reason: tr('需要等級 ') + rq + tr('（而家 Lv') + p.level + tr('）') };   // v0.17.1")
rep("function gradeName(it) {", "function itemReq(it) { return it ? Math.min(it.reqLevel || 1, ZONE_TIERS[tierOf(it.ilvl)].reqLevel) : 1; }   // v0.17.1: older items keep at most the new requirement\nfunction gradeName(it) {")
rep("  if (it.reqLevel > 1) L.push({ text: tr('需要等級 ') + it.reqLevel +", "  if (itemReq(it) > 1) L.push({ text: tr('需要等級 ') + itemReq(it) +")
rep("    if ((it.reqLevel || 1) > p.level) { b.appendChild(el('i', 'req', 'Lv' + it.reqLevel)); b.classList.add('locked'); }",
    "    if (C.itemReq(it) > p.level) { b.appendChild(el('i', 'req', 'Lv' + C.itemReq(it))); b.classList.add('locked'); }")
rep("affixRange, affixValidRange, affixStackProblem, weaponAt,", "affixRange, affixValidRange, affixStackProblem, itemReq, weaponAt,")
rep("  p.xp += v * p.stats.xpMul * ((g.zone && g.zone.xpMul) || 1)",
    "  p.xp += v * p.stats.xpMul * catchUpXp(g) * ((g.zone && g.zone.xpMul) || 1)")
rep("function addXp(g, v) {",
    "function catchUpXp(g) { const rec = g.zone && g.zone.recLevel ? g.zone.recLevel : 1, d = rec - g.player.level; return d > 0 ? 1 + Math.min(1.5, 0.12 * d) : 1; }   // v0.17.1: under the zone's level → up to +150% XP\n"
    "function addXp(g, v) {")

EN.update({
    '可以恢復嘅舊角色': 'Recoverable character', '上次儲存 ': 'Last saved ', ' · 裝備 ': ' · items ', ' 件': '', '恢復到存檔位 ': 'Restore to slot ', '⚠ 再撳一次：覆蓋存檔位 ': '⚠ Tap again: overwrite slot ',
    '恢復（會覆蓋存檔位 ': 'Restore (overwrites slot ', '已經恢復：': 'Restored: ', '恢復失敗：': 'Restore failed: ',
    '發現可以恢復嘅舊角色：去「角色 Characters」畫面撳「恢復」。': 'A character can be recovered: open Characters and tap Restore.',
    '近戰': 'Melee', '遠程': 'Ranged', '法術': 'Spells', '召喚': 'Minions', '持續': 'Persistent', '位移': 'Movement', '有用輔助': 'Useful supports',
})
EN.pop(' 件', None)
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();", "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.17.1\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")
open(dst, 'w', encoding='utf-8').write(h)
print('ok 0.17.1', len(h))
