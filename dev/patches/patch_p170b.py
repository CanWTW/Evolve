#!/usr/bin/env python3
"""EVOLVE v0.17.0 part B: bigger stash (1000 gear / 4000 orbs, orb cells unlimited), orb fusion inside the stash, Codex
(orbs, legendaries, sets) with a PoE-style collection (one item per legendary). Usage: patch_p170b.py in.html out.html"""
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


# ---------------- stash size ----------------
rep("const INV_CAP = 80, STASH_CAP = 500,   /* v0.8.4: stash 120 → 200; v0.15.2: 200 → 500 */",
    "const INV_CAP = 80, STASH_CAP = 1000,   /* v0.8.4: stash 120 → 200; v0.15.2: 200 → 500; v0.17: 1000 (cloud saves stay under 600k) */")
rep("const STG_SELL = 20, STASH_GEM_HARD = 2000;", "const STG_SELL = 20, STASH_GEM_HARD = 4000;   // v0.17: orbs in the stash have no cell limit, only a count")
rep("function stGemRoom(list, x) { if (list.length >= STASH_GEM_HARD) return false; if (C.gemCells(list) < C.DATA.STASH_CAP) return true; const L = Math.max(1, x.level | 0); return list.some((q) => q.id === x.id && Math.max(1, q.level | 0) === L); }",
    "function stGemRoom(list) { return list.length < STASH_GEM_HARD; }")
rep("  $('stStCap').textContent = tr('倉庫 ') + (items ? st.length + '/' + C.DATA.STASH_CAP : C.gemCells(st) + '/' + C.DATA.STASH_CAP + tr(' 格'));",
    "  $('stStCap').textContent = tr('倉庫 ') + (items ? st.length + '/' + C.DATA.STASH_CAP : st.length + '/' + STASH_GEM_HARD + tr(' 粒'));")
rep("    if (kind === 'gem' && toStash) { const x = from[i]; if (!stGemRoom(to, x)) { msg = tr('倉庫已滿（') + C.DATA.STASH_CAP + tr(' 格）'); return; } }",
    "    if (kind === 'gem' && toStash) { if (!stGemRoom(to)) { msg = tr('倉庫已滿（') + STASH_GEM_HARD + tr(' 粒）'); return; } }")

# ---------------- stash fusion + deposit-all ----------------
rep("function renderStTools(s, items) {",
    r"""// v0.17 orb fusion inside the stash (gold from the character); deposit every unsocketed orb
function stashFusePlan(s) { const by = {}; for (const x of s.stash.gems) { const L = Math.max(1, x.level | 0); if (L >= C.GEM_MAX_LEVEL) continue; const k = x.id + '|' + L; (by[k] = by[k] || []).push(x); } return by; }
function stashFuse(s) {   // repeat until nothing more fuses (Lv1 → Lv2 results may fuse again); returns { n, gold, short }
  let n = 0, spent = 0, short = false;
  for (let guard = 0; guard < 50; guard++) {
    let did = false; const by = stashFusePlan(s);
    for (const k of Object.keys(by).sort((a, b) => +a.split('|')[1] - +b.split('|')[1])) {
      const list = by[k], L = Math.max(1, list[0].level | 0), cost = C.FUSE_COST[L];
      while (list.length >= C.FUSE_COUNT) {
        if ((s.character.gold || 0) < cost) { short = true; break; }
        const mats = list.splice(0, C.FUSE_COUNT), drop = new Set(mats.map((x) => x.uid));
        s.stash.gems = s.stash.gems.filter((x) => !drop.has(x.uid)); s.character.gold -= cost; spent += cost;
        if (!Number.isInteger(s.nextUid) || s.nextUid < 1) s.nextUid = 1;
        s.stash.gems.push({ uid: 'g_' + (s.nextUid++), id: list[0] ? list[0].id : mats[0].id, level: L + 1 }); n++; did = true;
      }
    }
    if (!did) break;
  }
  return { n, gold: spent, short };
}
function stFuseNow(quiet) {
  let r = { n: 0 }; commitVillage((s) => { if (!s.stash) s.stash = { capacity: C.DATA.STASH_CAP, items: [], gems: [] }; s.stash.gems = s.stash.gems || []; r = stashFuse(s); });
  if (r.n) { SFX.play('fuse', 120); $('stMsg').textContent = tr('倉庫融合咗 ') + r.n + tr(' 次（−') + r.gold + tr(' 金）'); } else if (!quiet) $('stMsg').textContent = r.short ? tr('金幣唔夠融合') : tr('倉庫冇 3 粒同款同等級嘅技能珠');
  stSel = null; renderStash(); renderTownHud(); return r.n;
}
function stDepositOrbs() {
  let n = 0; commitVillage((s) => { if (!s.stash) s.stash = { capacity: C.DATA.STASH_CAP, items: [], gems: [] }; s.stash.gems = s.stash.gems || [];
    const keep = []; for (const x of s.character.gems.list) { if (C.findSocket(g, x.uid) || s.stash.gems.length >= STASH_GEM_HARD) keep.push(x); else { s.stash.gems.push(x); n++; } } s.character.gems.list = keep; });
  $('stMsg').textContent = tr('放咗 ') + n + tr(' 粒入倉庫'); if (opts.autoFuse) stFuseNow(true); else renderStash(); renderTownHud();
}
function renderStTools(s, items) {""")
rep("  const so = el('button', 'small', tr('整理倉庫')); so.id = 'stSort'; so.addEventListener('click', () => { stArm = null; stSort(items); }); T.appendChild(so);",
    "  if (!items) { const fu = el('button', 'small primary', tr('倉庫融合')); fu.id = 'stFuse'; fu.title = tr('倉庫入面 3 粒同款同等級＋金幣 → 升一級（會重複直到冇得再融合）'); fu.addEventListener('click', () => { stArm = null; stFuseNow(false); }); T.appendChild(fu);\n"
    "    const dp = el('button', 'small', tr('全部放入倉庫')); dp.id = 'stDeposit'; dp.title = tr('未鑲嘅技能珠全部放入倉庫'); dp.addEventListener('click', () => { stArm = null; stDepositOrbs(); }); T.appendChild(dp); }\n"
    "  const so = el('button', 'small', tr('整理倉庫')); so.id = 'stSort'; so.addEventListener('click', () => { stArm = null; stSort(items); }); T.appendChild(so);")
# moving orbs into the stash auto-fuses when the option is on
rep("  $('stMsg').textContent = msg; renderStash(); renderTownHud();\n}",
    "  $('stMsg').textContent = msg; if (kind === 'gem' && toStash && opts.autoFuse) stFuseNow(true); else renderStash(); renderTownHud();\n}")
rep('<div class="snote">撳一格睇詳情，再撳一次（或者撳「搬」）就喺背包同倉庫之間搬。鑲緊嘅技能珠同著緊嘅裝備唔會搬。倉庫跟住角色，唔會因為死亡而冇。</div>',
    '<div class="snote">撳一格睇詳情，再撳一次（或者撳「搬」）就喺背包同倉庫之間搬。倉庫可以放 1000 件裝備同 4000 粒技能珠，技能珠可以直接喺倉庫融合（開咗「自動融合」就會自動做）。鑲緊嘅技能珠同著緊嘅裝備唔會搬。</div>')

# ---------------- codex ----------------
rep('      <button id="tmAch">成就 Achievements</button>', '      <button id="tmCodex">圖鑑 Codex</button>\n      <button id="tmAch">成就 Achievements</button>')
rep('  <section id="ach" class="screen hidden">',
    '''  <!-- v0.17 codex: every orb / legendary / set piece you have found; one legendary of each can be kept in the collection -->
  <section id="codex" class="screen hidden">
    <div class="shead"><h2>圖鑑 Codex <small id="cxCount"></small></h2><div class="stabs"><button id="cxTabO" class="small tab on">技能珠 Orbs</button><button id="cxTabU" class="small tab">傳奇 Legendaries</button><button id="cxTabS" class="small tab">套裝 Sets</button></div></div>
    <div id="cxNote" class="snote"></div>
    <div class="cxcols"><div id="cxBody" class="cxbody"></div><div id="cxDet" class="stdet cxdet"></div></div>
    <div id="cxMsg" class="vmsg" aria-live="polite"></div>
    <div class="btns row"><button id="cxClose">返回 Back<span class="kbonly">（Esc）</span></button></div>
  </section>
  <section id="ach" class="screen hidden">''')
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    "#codex{justify-content:flex-start}.cxcols{display:flex;gap:10px;width:100%;max-width:calc(var(--u)*560);flex:1;min-height:0}\n"
    ".cxbody{flex:1 1 0;min-width:0;overflow-y:auto;max-height:60vh;padding-right:4px}.cxdet{flex:0 0 clamp(220px,38%,380px);margin:0;overflow-y:auto;max-height:60vh}\n"
    ".cxgrp{color:#7dfcff;font-weight:800;margin:8px 0 4px;font-size:max(12px,calc(var(--u)*5))}.cxgrid{display:grid;grid-template-columns:repeat(auto-fill,44px);gap:5px}\n"
    ".cxgrid .cell{position:relative;width:44px;height:44px;background:#141022;border:1px solid #3a3058;display:flex;align-items:center;justify-content:center;padding:0;cursor:pointer}\n"
    ".cxgrid .cell img{width:32px;height:32px;image-rendering:pixelated}.cxgrid .cell.unk{color:#4a4560;font-weight:800;font-size:18px}.cxgrid .cell.sel{outline:2px solid #fff;outline-offset:1px}\n"
    ".cxgrid .cell .lv{position:absolute;right:2px;bottom:0;font-size:10px;color:#ffd23f}.cxgrid .cell .cx{position:absolute;left:2px;top:0;font-size:10px;color:#9dff7a;font-weight:800}\n"
    ".cxrow{display:flex;align-items:center;gap:8px;padding:5px 6px;border:1px solid #2d2742;background:#100d1c;margin-bottom:4px;cursor:pointer}.cxrow.sel{border-color:#fff}.cxrow.unk{opacity:.55}\n"
    ".cxrow img{width:32px;height:32px;image-rendering:pixelated}.cxrow .t{flex:1;min-width:0}.cxrow .t b{display:block}.cxrow .t small{color:#8a93a6}.cxrow .st{font-size:11px;font-weight:800}.cxrow .st.c{color:#9dff7a}.cxrow .st.f{color:#ffd23f}\n"
    "@media (max-height:520px){#codex{padding:6px 10px}#codex>.snote{display:none}.cxbody,.cxdet{max-height:none}.cxcols{max-width:none}}")
CODEX = r"""
// ---------------- v0.17 codex + collection ----------------
let cxTab = 'orbs', cxSel = null;
const CX_TYPES = [['active', tr('主動技能')], ['support', tr('輔助珠')], ['trigger', tr('觸發珠')], ['passive', tr('被動珠')]];
function codexRecord(s) {   // seen orbs (max level) and legendaries from everything the character owns
  s.progress = s.progress || {}; const P = s.progress; const O = P.codexOrbs = P.codexOrbs || {}; const U = new Set(P.uniques || []);
  const seeO = (x) => { if (x && x.id && C.gemDefById(x.id)) O[x.id] = Math.max(O[x.id] || 0, Math.max(1, x.level | 0)); };
  (s.character.gems.list || []).forEach(seeO); ((s.stash && s.stash.gems) || []).forEach(seeO);
  const seeI = (it) => { if (it && it.unique) U.add(it.unique); };
  Object.values(s.character.equipment || {}).forEach(seeI); (s.character.inventory.items || []).forEach(seeI); ((s.stash && s.stash.items) || []).forEach(seeI); Object.values(P.collection || {}).forEach(seeI);
  P.uniques = [...U];
}
function itemScore(it) {   // best copy = highest item level, then best affix rolls
  let sc = (it.ilvl || 1) * 1000; const AB = D.AFFIX_BY_ID;
  for (const a of it.affixes || []) { const d = AB[a.id]; if (!d) continue; const [lo, hi] = C.affixRange(d, it.ilvl); sc += hi > lo ? Math.max(0, Math.min(1, (a.value - lo) / (hi - lo))) * 100 : 100; }
  return sc;
}
function cxOwned(s, uq) { const out = []; (s.character.inventory.items || []).forEach((it) => { if (it.unique === uq) out.push(['bag', it]); }); ((s.stash && s.stash.items) || []).forEach((it) => { if (it.unique === uq) out.push(['stash', it]); }); return out; }
function cxCollectBest(uq) {
  let msg = ''; commitVillage((s) => { codexRecord(s); const P = s.progress, col = P.collection = P.collection || {}; const own = cxOwned(s, uq).sort((a, b) => itemScore(b[1]) - itemScore(a[1]));
    if (!own.length) { msg = tr('背包同倉庫都冇呢件傳奇'); return; } const [where, best] = own[0]; const cur0 = col[uq];
    if (cur0 && itemScore(cur0) >= itemScore(best)) { msg = tr('收藏緊嗰件已經係最好'); return; }
    const L = where === 'bag' ? s.character.inventory.items : s.stash.items; L.splice(L.indexOf(best), 1); col[uq] = best;
    if (cur0) { s.stash = s.stash || { capacity: C.DATA.STASH_CAP, items: [], gems: [] }; s.stash.items = s.stash.items || []; s.stash.items.push(cur0); msg = tr('換咗更好嘅一件，舊嗰件放返倉庫'); } else msg = tr('已收藏'); });
  $('cxMsg').textContent = msg; SFX.play('equip', 80); renderCodex(); renderTownHud();
}
function cxTakeOut(uq) {
  let msg = ''; commitVillage((s) => { const col = s.progress && s.progress.collection; if (!col || !col[uq]) return; s.stash = s.stash || { capacity: C.DATA.STASH_CAP, items: [], gems: [] }; s.stash.items = s.stash.items || [];
    if (s.stash.items.length >= C.DATA.STASH_CAP) { msg = tr('倉庫已滿'); return; } s.stash.items.push(col[uq]); delete col[uq]; msg = tr('已經放咗入倉庫'); });
  $('cxMsg').textContent = msg; renderCodex();
}
function openCodex() { if (villageMode) commitVillage((s) => codexRecord(s)); cxSel = null; $('cxMsg').textContent = ''; renderCodex(); show('codex'); }
function closeCodex() { renderTownHud(); show(villageMode ? 'town' : 'pause'); }
function renderCodex() {
  const s = cur ? JSON.parse(JSON.stringify(cur)) : null; if (!s) return; codexRecord(s); const P = s.progress, O = P.codexOrbs, seenU = new Set(P.uniques || []), col = P.collection || {};
  for (const [id, t] of [['cxTabO', 'orbs'], ['cxTabU', 'uniq'], ['cxTabS', 'sets']]) $(id).classList.toggle('on', cxTab === t);
  const B = $('cxBody'), Dt = $('cxDet'); B.textContent = ''; Dt.textContent = '';
  const allO = [].concat(...Object.values(C.GEM_IDS)), UQ = Object.values(D.UNIQUES), nU = UQ.filter((u) => !u.set), nS = UQ.filter((u) => u.set);
  $('cxCount').textContent = tr('技能珠 ') + allO.filter((id) => O[id]).length + '/' + allO.length + tr(' · 傳奇 ') + nU.filter((u) => seenU.has(u.id)).length + '/' + nU.length + tr(' · 套裝 ') + nS.filter((u) => seenU.has(u.id)).length + '/' + nS.length + tr(' · 收藏 ') + Object.keys(col).length;
  if (cxTab === 'orbs') {
    $('cxNote').textContent = tr('見過嘅技能珠會記錄落嚟（顯示見過最高等級）。技能珠本身放喺倉庫，可以喺倉庫融合。');
    for (const [t, nm] of CX_TYPES) { const ids = C.GEM_IDS[t] || []; B.appendChild(el('div', 'cxgrp', nm + ' ' + ids.filter((id) => O[id]).length + '/' + ids.length)); const G = el('div', 'cxgrid');
      for (const id of ids) { const known = !!O[id], c = el('button', 'cell' + (known ? '' : ' unk') + (cxSel === id ? ' sel' : '')); c.id = 'cxO_' + id.replace(/\./g, '_');
        if (known) { c.appendChild(gemIconEl(id)); c.appendChild(el('span', 'lv', 'Lv' + O[id])); c.style.borderColor = C.GEM_COLORS[t]; c.title = C.gemDefById(id).name; } else c.textContent = '？';
        c.addEventListener('click', () => { cxSel = id; renderCodex(); }); G.appendChild(c); }
      B.appendChild(G); }
    if (cxSel && C.gemDefById(cxSel)) { const d = C.gemDefById(cxSel), t = C.gemType(cxSel), known = !!O[cxSel]; const nm = el('b', null, known ? d.name + ' ' + (d.en || '') : '？？？'); nm.style.color = C.GEM_COLORS[t]; Dt.appendChild(nm);
      Dt.appendChild(el('div', 'ln', C.GEM_TYPES[t] + (known ? tr(' · 見過最高 Lv') + O[cxSel] : tr(' · 未發現'))));
      if (known && d.desc) Dt.appendChild(el('div', 'ln', d.desc)); else if (!known) Dt.appendChild(el('div', 'ln muted', tr('打怪、精英同 Boss 會掉落；部分喺商店有得買。'))); }
    else Dt.appendChild(el('div', 'muted', tr('撳一粒睇詳情。')));
    return;
  }
  const list = cxTab === 'uniq' ? nU : nS;
  $('cxNote').textContent = tr('每款傳奇可以收藏一件（好似 PoE 嘅收藏）。撳「收藏最好嗰件」會由背包同倉庫揀物品等級同詞綴最好嗰件放入去，舊嗰件會放返倉庫。收藏品唔佔背包同倉庫。');
  let lastSet = null;
  for (const u of list) {
    if (cxTab === 'sets' && u.set !== lastSet) { lastSet = u.set; const S = D.SETS[u.set]; B.appendChild(el('div', 'cxgrp', S ? S.name + ' · ' + S.b2Text + ' ／ ' + S.b4Text : u.set)); }
    const known = seenU.has(u.id), have = col[u.id], r = el('div', 'cxrow' + (known ? '' : ' unk') + (cxSel === u.id ? ' sel' : '')); r.id = 'cxU_' + u.id.replace(/\./g, '_');
    const it = have ? C.Save.toRuntimeItem(have) : { base: u.base, rarity: 'legendary', unique: u.id, ilvl: 1, slot: u.slot, affixes: [] };
    r.appendChild(known ? itemIconEl(it) : el('span', 'muted', '？'));
    const t = el('div', 't'); t.append(el('b', null, known ? (have ? it.name : u.name) : '？？？'), el('small', null, (D.SLOT_NAMES[u.slot] || u.slot) + (known ? ' · ' + C.uniqueText(u, have ? Math.min(6, have.ilvl || 1) : 1) : ''))); r.appendChild(t);
    r.appendChild(el('span', 'st' + (have ? ' c' : known ? ' f' : ''), have ? tr('已收藏') : known ? tr('已發現') : tr('未發現')));
    r.addEventListener('click', () => { cxSel = u.id; renderCodex(); }); B.appendChild(r);
  }
  const u = cxSel && D.UNIQUES[cxSel]; if (!u || (cxTab === 'sets') !== !!u.set) { Dt.appendChild(el('div', 'muted', tr('撳一件睇詳情。'))); return; }
  const known = seenU.has(u.id), have = col[u.id], own = cxOwned(s, u.id);
  if (!known) { Dt.appendChild(el('b', null, '？？？')); Dt.appendChild(el('div', 'ln muted', (D.SLOT_NAMES[u.slot] || u.slot) + tr(' · 未發現'))); return; }
  const shown = have ? C.Save.toRuntimeItem(have) : null; const nm = el('b', null, shown ? shown.name : u.name + ' ' + (u.en || '')); nm.style.color = D.RARITY.legendary.color; Dt.appendChild(nm);
  if (shown) for (const l of C.describeItem(shown)) Dt.appendChild(el('div', 'ln ' + l.kind, l.text)); else { Dt.appendChild(el('div', 'ln unique', u.text)); if (u.costText) Dt.appendChild(el('div', 'ln cost', u.costText)); }
  Dt.appendChild(el('div', 'ln', tr('背包／倉庫有 ') + own.length + tr(' 件') + (own.length ? tr('（最好：物品等級 ') + Math.max(...own.map((o) => o[1].ilvl || 1)) + tr('）') : '')));
  const row = el('div', 'gbtns'); if (villageMode) {
    if (own.length) { const b = el('button', 'small primary', have ? tr('換最好嗰件') : tr('收藏最好嗰件')); b.id = 'cxCollect'; b.addEventListener('click', () => cxCollectBest(u.id)); row.appendChild(b); }
    if (have) { const b = el('button', 'small', tr('取出（放入倉庫）')); b.id = 'cxTake'; b.addEventListener('click', () => cxTakeOut(u.id)); row.appendChild(b); }
  } else row.appendChild(el('div', 'muted', tr('喺村莊先可以收藏或者取出。')));
  Dt.appendChild(row);
}
on('tmCodex', () => openCodex()); on('cxClose', closeCodex);
on('cxTabO', () => { cxTab = 'orbs'; cxSel = null; renderCodex(); }); on('cxTabU', () => { cxTab = 'uniq'; cxSel = null; renderCodex(); }); on('cxTabS', () => { cxTab = 'sets'; cxSel = null; renderCodex(); });
"""
rep("function renderAch() {", CODEX + "function renderAch() {")
rep("  if (screen === 'ach') { if (e.code === 'Escape') { renderTownHud(); show(achBack); } return; }",
    "  if (screen === 'ach') { if (e.code === 'Escape') { renderTownHud(); show(achBack); } return; }\n  if (screen === 'codex') { if (e.code === 'Escape') closeCodex(); return; }   // v0.17")
# record the codex whenever achievements are checked (run end + village)
rep("function checkAch(s, gg) {\n", "function checkAch(s, gg) {\n  try { codexRecord(s); } catch (e) { /* codex is best effort */ }   // v0.17\n")
# achievements counting collected / codex
rep("  { id: 'legend', name: tr('寶藏獵人'),",
    "  { id: 'codex50', name: tr('技能珠學者'), desc: tr('圖鑑記錄 50 種技能珠'), gold: 500, prog: (s) => [Object.keys(s.progress.codexOrbs || {}).length, 50] },   // v0.17\n"
    "  { id: 'museum5', name: tr('收藏家之館'), desc: tr('圖鑑收藏 5 件傳奇'), gold: 400, prog: (s) => [Object.keys(s.progress.collection || {}).length, 5] },\n"
    "  { id: 'legend', name: tr('寶藏獵人'),")
# expose for tests
rep("  openStash, stashSave, stRun, ST_OPS,", "  openStash, stashSave, stRun, ST_OPS, stFuseNow, stDepositOrbs, openCodex, renderCodex, cxCollectBest, cxTakeOut, itemScore, get cxTab() { return cxTab; }, set cxTab(v) { cxTab = v; }, set cxSel(v) { cxSel = v; },")

EN.update({
    ' 粒': ' orbs', '倉庫已滿（': 'Stash full (', '）': ')', '倉庫融合咗 ': 'Stash fused ', ' 次（−': ' times (−', ' 金）': ' gold)', '金幣唔夠融合': 'Not enough gold to fuse', '倉庫冇 3 粒同款同等級嘅技能珠': 'No 3 identical orbs of the same level in the stash',
    '放咗 ': 'Moved ', ' 粒入倉庫': ' orbs to the stash', '倉庫融合': 'Fuse in stash', '倉庫入面 3 粒同款同等級＋金幣 → 升一級（會重複直到冇得再融合）': '3 identical orbs of one level + gold → next level, repeated until nothing fuses',
    '全部放入倉庫': 'Deposit all', '未鑲嘅技能珠全部放入倉庫': 'Move every unsocketed orb to the stash',
    '撳一格睇詳情，再撳一次（或者撳「搬」）就喺背包同倉庫之間搬。倉庫可以放 1000 件裝備同 4000 粒技能珠，技能珠可以直接喺倉庫融合（開咗「自動融合」就會自動做）。鑲緊嘅技能珠同著緊嘅裝備唔會搬。': 'Tap a cell for details, tap again (or Move) to move it between bag and stash. The stash holds 1000 items and 4000 orbs, and orbs fuse right in the stash (automatically with Auto-fuse on). Socketed orbs and worn gear are not moved.',
    '圖鑑 Codex': 'Codex', '技能珠 Orbs': 'Orbs', '傳奇 Legendaries': 'Legendaries', '套裝 Sets': 'Sets', '主動技能': 'Active skills', '輔助珠': 'Supports', '觸發珠': 'Triggers', '被動珠': 'Passives',
    '背包同倉庫都冇呢件傳奇': "You don't own this legendary", '收藏緊嗰件已經係最好': 'The collected one is already the best', '換咗更好嘅一件，舊嗰件放返倉庫': 'Swapped in a better one; the old one went to the stash', '已收藏': 'Collected',
    '倉庫已滿': 'Stash full', '已經放咗入倉庫': 'Moved to the stash', '技能珠 ': 'Orbs ', ' · 傳奇 ': ' · Legendaries ', ' · 套裝 ': ' · Sets ', ' · 收藏 ': ' · Collected ',
    '見過嘅技能珠會記錄落嚟（顯示見過最高等級）。技能珠本身放喺倉庫，可以喺倉庫融合。': 'Every orb you have owned is recorded (with the highest level seen). Keep the orbs themselves in the stash, where they can fuse.',
    ' · 見過最高 Lv': ' · highest seen Lv', ' · 未發現': ' · not found yet', '打怪、精英同 Boss 會掉落；部分喺商店有得買。': 'Drops from monsters, elites and bosses; some are sold in the shop.', '撳一粒睇詳情。': 'Tap an orb for details.',
    '每款傳奇可以收藏一件（好似 PoE 嘅收藏）。撳「收藏最好嗰件」會由背包同倉庫揀物品等級同詞綴最好嗰件放入去，舊嗰件會放返倉庫。收藏品唔佔背包同倉庫。': 'Keep one of each legendary in the collection (like PoE). "Collect the best" picks the copy with the highest item level and best rolls from your bag and stash; the previous one goes back to the stash. Collected items take no bag or stash space.',
    '已發現': 'Found', '未發現': 'Not found', '撳一件睇詳情。': 'Tap an item for details.', '背包／倉庫有 ': 'In bag / stash: ', ' 件': '', '（最好：物品等級 ': ' (best: item level ', '換最好嗰件': 'Swap in the best', '收藏最好嗰件': 'Collect the best',
    '取出（放入倉庫）': 'Take out (to stash)', '喺村莊先可以收藏或者取出。': 'Collect or take out in the village.', '技能珠學者': 'Orb Scholar', '圖鑑記錄 50 種技能珠': 'Record 50 orbs in the codex', '收藏家之館': 'Museum', '圖鑑收藏 5 件傳奇': 'Collect 5 legendaries in the codex',
})
# ' 件' is used elsewhere with other English already; don't override it
EN.pop(' 件', None); EN.pop('）', None); EN.pop(' 粒', None); EN.pop(' 金）', None)
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok B codex/stash', len(h))
