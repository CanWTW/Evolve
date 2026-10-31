#!/usr/bin/env python3
"""EVOLVE v0.15.1 -> v0.15.2: stash / bag space.
- stash 200 -> 500 gear; stash orbs stack (500 cells, 2000 orbs)
- loot filter option 3: common + magic + rare
- stash tools: bulk sell by rarity (bag + stash), sell duplicate legendaries, sell spare orbs, sort, sell selected
- gear bag: 賣晒稀有 (two-tap)
Usage: patch_p152.py in.html out.html
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:90]))
    h = h.replace(old, new)


# ---- version ----
rep("<title>PROJECT: EVOLVE — 原型 0.15.1</title>", "<title>PROJECT: EVOLVE — 原型 0.15.2</title>")
rep("瀏覽器原型 0.15.1（M0 + M1）", "瀏覽器原型 0.15.2（M0 + M1）", 2)
rep("const VERSION = '0.15.1';", "const VERSION = '0.15.2';")

# ---- capacities ----
rep("const INV_CAP = 80, STASH_CAP = 200,   /* v0.8.4: stash 120 → 200 */",
    "const INV_CAP = 80, STASH_CAP = 500,   /* v0.8.4: stash 120 → 200; v0.15.2: 200 → 500 */")

# ---- loot filter option 3 ----
rep('<option value="2">普通＋魔法 Common + Magic</option></select>',
    '<option value="2">普通＋魔法 Common + Magic</option><option value="3">普通＋魔法＋稀有（只留傳奇） Common + Magic + Rare (keep legendaries)</option></select>')

# ---- gear bag: sell all rares ----
rep('<button id="gSellM" class="small">賣晒魔法</button></div>',
    '<button id="gSellM" class="small">賣晒魔法</button><button id="gSellR" class="small">賣晒稀有</button></div>')
rep("on('gSellM', () => { if (!g) return; const r = C.sellItemsByRarity(g, ['magic']); bulkDone(tr('賣咗 ') + r.n + tr(' 件魔法裝備（+') + r.gold + tr(' 金）')); });",
    "on('gSellM', () => { if (!g) return; const r = C.sellItemsByRarity(g, ['magic']); bulkDone(tr('賣咗 ') + r.n + tr(' 件魔法裝備（+') + r.gold + tr(' 金）')); });\n"
    "let gSellRArm = 0;   // v0.15.2 two-tap: rares are worth keeping more often\n"
    "on('gSellR', () => { if (!g) return; const b = $('gSellR'); if (Date.now() - gSellRArm > 3000) { const n = g.player.inventory.filter((it) => !it.unique && it.rarity === 'rare').length; if (!n) { bulkDone(tr('背包冇稀有裝備')); return; } gSellRArm = Date.now(); b.textContent = tr('確定？') + n + tr(' 件'); setTimeout(() => { b.textContent = tr('賣晒稀有'); }, 3000); return; } gSellRArm = 0; b.textContent = tr('賣晒稀有'); const r = C.sellItemsByRarity(g, ['rare']); bulkDone(tr('賣咗 ') + r.n + tr(' 件稀有裝備（+') + r.gold + tr(' 金）')); });")

# ---- stash screen: tools row ----
rep('<div class="snote">撳一格睇詳情，再撳一次（或者撳「搬」）就喺背包同倉庫之間搬。鑲緊嘅技能珠同著緊嘅裝備唔會搬。倉庫跟住角色，唔會因為死亡而冇。</div>',
    '<div class="snote">撳一格睇詳情，再撳一次（或者撳「搬」）就喺背包同倉庫之間搬。鑲緊嘅技能珠同著緊嘅裝備唔會搬。倉庫跟住角色，唔會因為死亡而冇。</div>\n'
    '    <div id="stTools" class="sttools"></div>')
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    ".sttools{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin:2px 0 6px}.sttools .small.arm{background:#5a1f1f;border-color:#ff8f8f;color:#fff}   /* v0.15.2 */\n"
    "@media (max-height:520px){   /* v0.15.2 phones: bag | stash | details side by side, the help line hidden (the details panel used to cover both grids) */\n"
    "#stash{display:grid;grid-template-columns:minmax(0,1fr) minmax(170px,30%);grid-template-rows:auto auto minmax(0,1fr) auto auto;gap:4px 8px;align-items:stretch;justify-items:stretch;padding:6px 10px calc(6px + env(safe-area-inset-bottom))}\n"
    "#stash>.shead,#stash>#stTools,#stash>#stMsg,#stash>.btns{grid-column:1/-1}#stash>.snote{display:none}#stash>.shead{display:flex;align-items:center;justify-content:center;gap:10px}#stash>.shead h2{margin:0}\n"
    "#stash>#stTools{margin:0}#stash .sttools .small{min-height:32px;padding:0 8px}#stash>.stcols{grid-column:1;grid-row:3;max-width:none;gap:8px}#stash .stgrid{max-height:none;flex:1}\n"
    "#stash>#stDet{grid-column:2;grid-row:3;margin:0;max-width:none;overflow-y:auto;min-height:0}#stash>#stMsg{min-height:0;margin:0}#stash>.btns{margin:0;justify-content:center}}")

# stash orbs: cells + hard cap instead of list length
rep("const from = toStash ? A : B, to = toStash ? B : A, cap = toStash ? C.DATA.STASH_CAP : (kind === 'item' ? C.DATA.INV_CAP : C.GEM_HARD);\n"
    "    const i = from.findIndex((x) => x && x.uid === uid); if (i < 0) return;\n"
    "    if (to.length >= cap) { msg = (toStash ? tr('倉庫') : tr('背包')) + tr('已滿（') + cap + tr('）'); return; }",
    "const from = toStash ? A : B, to = toStash ? B : A, cap = toStash ? C.DATA.STASH_CAP : (kind === 'item' ? C.DATA.INV_CAP : C.GEM_HARD);\n"
    "    const i = from.findIndex((x) => x && x.uid === uid); if (i < 0) return;\n"
    "    if (kind === 'gem' && toStash) { const x = from[i]; if (!stGemRoom(to, x)) { msg = tr('倉庫已滿（') + C.DATA.STASH_CAP + tr(' 格）'); return; } }   // v0.15.2 orbs stack in the stash\n"
    "    else if (to.length >= cap) { msg = (toStash ? tr('倉庫') : tr('背包')) + tr('已滿（') + cap + tr('）'); return; }")

rep("  $('stStCap').textContent = tr('倉庫 ') + st.length + '/' + C.DATA.STASH_CAP;",
    "  $('stStCap').textContent = tr('倉庫 ') + (items ? st.length + '/' + C.DATA.STASH_CAP : C.gemCells(st) + '/' + C.DATA.STASH_CAP + tr(' 格'));\n"
    "  renderStTools(s, items);")

# single sell in the detail panel
rep("""stashMove(k.kind, k.uid, k.toStash); }); row.appendChild(mv);
  if (!items && stSel.n > 1)""",
    """stashMove(k.kind, k.uid, k.toStash); }); row.appendChild(mv);
  { const v = items ? C.Save.itemSellValue(x) : STG_SELL * Math.max(1, x.level | 0); const sb = el('button', 'small danger', tr('賣 +') + v + tr(' 金')); sb.id = 'stSell'; sb.addEventListener('click', () => { const k = stSel; stSel = null; stSellOne(k.kind, k.uid, !k.toStash); }); row.appendChild(sb); }   // v0.15.2
  if (!items && stSel.n > 1)""")

# tools implementation (after the stash renderer)
rep("on('stClose', closeStash);",
    r"""on('stClose', closeStash);
// ---------------- v0.15.2 stash tools: bulk sell (bag + stash, never worn gear / socketed orbs), duplicate legendaries, spare orbs, sort ----------------
const STG_SELL = 20, STASH_GEM_HARD = 2000;   // orb sell price per level (same as 賣出多餘); max orbs in the stash
function stGemRoom(list, x) { if (list.length >= STASH_GEM_HARD) return false; if (C.gemCells(list) < C.DATA.STASH_CAP) return true; const L = Math.max(1, x.level | 0); return list.some((q) => q.id === x.id && Math.max(1, q.level | 0) === L); }
const RAR_I = { common: 0, magic: 1, rare: 2, legendary: 3 };
function stItemLists(s) { return [s.character.inventory.items, s.stash.items]; }
function stGemLists(s) { return [s.character.gems.list, s.stash.gems]; }
// each op: (s) → Set of things to sell (items or orbs) and how to price them; run once on a preview save, once inside commitVillage
const ST_OPS = {
  common: { kind: 'item', pick: (s) => stItemLists(s).flat().filter((it) => !it.unique && it.rarity === 'common') },
  magic: { kind: 'item', pick: (s) => stItemLists(s).flat().filter((it) => !it.unique && it.rarity === 'magic') },
  rare: { kind: 'item', pick: (s) => stItemLists(s).flat().filter((it) => !it.unique && it.rarity === 'rare') },
  dupes: { kind: 'item', pick: (s) => {   // legendaries / set pieces: keep the best unworn copy of each (highest item level), sell the rest
    const best = {}, all = stItemLists(s).flat().filter((it) => it.unique);
    for (const it of all) { const b = best[it.unique]; if (!b || (it.ilvl || 0) > (b.ilvl || 0)) best[it.unique] = it; }
    return all.filter((it) => best[it.unique] !== it); } },
  orbs: { kind: 'gem', pick: (s) => {   // keep socketed orbs and the highest level unsocketed copy of each orb
    const all = stGemLists(s).flat().filter((x) => !C.findSocket(g, x.uid)), best = {};
    for (const x of all) { const b = best[x.id]; if (!b || (x.level || 1) > (b.level || 1)) best[x.id] = x; }
    return all.filter((x) => best[x.id] !== x); } },
};
const ST_LABEL = { common: '賣晒普通', magic: '賣晒魔法', rare: '賣晒稀有', dupes: '賣重複傳奇', orbs: '賣出多餘' };
let stArm = null, stArmT = 0;
function stPrice(kind, x) { return kind === 'item' ? C.Save.itemSellValue(x) : STG_SELL * Math.max(1, x.level | 0); }
function stRun(op) {
  const O = ST_OPS[op]; let n = 0, gold = 0;
  commitVillage((s) => {
    if (!s.stash) s.stash = { capacity: C.DATA.STASH_CAP, items: [], gems: [] }; s.stash.items = s.stash.items || []; s.stash.gems = s.stash.gems || [];
    const sell = new Set(O.pick(s).map((x) => x.uid)); if (!sell.size) return;
    const strip = (L) => L.filter((x) => { if (!sell.has(x.uid)) return true; n++; gold += stPrice(O.kind, x); return false; });
    if (O.kind === 'item') { s.character.inventory.items = strip(s.character.inventory.items); s.stash.items = strip(s.stash.items); }
    else { s.character.gems.list = strip(s.character.gems.list); s.stash.gems = strip(s.stash.gems); }
    s.character.gold = (s.character.gold || 0) + gold;
  });
  if (n) SFX.play('buy', 80);
  return { n, gold };
}
function stSellOne(kind, uid, inStash) {
  let v = 0;
  commitVillage((s) => {
    const L = kind === 'item' ? (inStash ? s.stash.items : s.character.inventory.items) : (inStash ? s.stash.gems : s.character.gems.list);
    const i = L.findIndex((x) => x && x.uid === uid); if (i < 0) return;
    if (kind === 'gem' && C.findSocket(g, uid)) return;
    v = stPrice(kind, L[i]); L.splice(i, 1); s.character.gold = (s.character.gold || 0) + v;
  });
  $('stMsg').textContent = v ? tr('賣咗（+') + v + tr(' 金）') : ''; if (v) SFX.play('buy', 80); renderStash(); renderTownHud();
}
function stSort(items) {
  commitVillage((s) => {
    if (!s.stash) return;
    if (items) { const rt = new Map(s.stash.items.map((x) => [x.uid, C.Save.toRuntimeItem(x)])); s.stash.items.sort((a, b) => { const A = rt.get(a.uid), B = rt.get(b.uid); return (RAR_I[B.rarity] || 0) - (RAR_I[A.rarity] || 0) || String(A.slot).localeCompare(String(B.slot)) || (B.ilvl || 0) - (A.ilvl || 0) || String(A.name).localeCompare(String(B.name)); }); }
    else s.stash.gems.sort((a, b) => String(C.gemType(a.id)).localeCompare(String(C.gemType(b.id))) || String(a.id).localeCompare(String(b.id)) || (b.level || 1) - (a.level || 1));
  });
  $('stMsg').textContent = tr('整理好咗'); stSel = null; renderStash();
}
function renderStTools(s, items) {
  const T = $('stTools'); if (!T) return; T.textContent = '';
  if (stArm && Date.now() - stArmT > 4000) stArm = null;
  for (const op of items ? ['common', 'magic', 'rare', 'dupes'] : ['orbs']) {
    const armed = stArm === op, pick = armed ? ST_OPS[op].pick(s) : null;
    const b = el('button', 'small' + (armed ? ' arm' : ''), armed ? tr('確定？') + pick.length + tr(' 件 +') + pick.reduce((a, x) => a + stPrice(ST_OPS[op].kind, x), 0) + tr(' 金') : tr(ST_LABEL[op]));
    b.id = 'stOp_' + op; b.title = tr('背包＋倉庫一齊計；著緊嘅裝備同鑲緊嘅技能珠唔會賣');
    b.addEventListener('click', () => {
      if (stArm !== op) { const k = ST_OPS[op].pick(stashSave()).length; if (!k) { $('stMsg').textContent = tr('冇嘢可以賣'); stArm = null; renderStash(); return; } stArm = op; stArmT = Date.now(); renderStash(); return; }
      stArm = null; stSel = null; const r = stRun(op); $('stMsg').textContent = tr('賣咗 ') + r.n + tr(' 件（+') + r.gold + tr(' 金）'); renderStash(); renderTownHud();
    });
    T.appendChild(b);
  }
  const so = el('button', 'small', tr('整理倉庫')); so.id = 'stSort'; so.addEventListener('click', () => { stArm = null; stSort(items); }); T.appendChild(so);
}""")

# tab switches clear the armed button
rep("on('stTabI', () => { stTab = 'items'; stSel = null; renderStash(); }); on('stTabG', () => { stTab = 'gems'; stSel = null; renderStash(); });",
    "on('stTabI', () => { stTab = 'items'; stSel = null; stArm = null; renderStash(); }); on('stTabG', () => { stTab = 'gems'; stSel = null; stArm = null; renderStash(); });")
rep("function openStash() { stTab = 'items'; $('stMsg').textContent = ''; renderStash(); show('stash'); }",
    "function openStash() { stTab = 'items'; stArm = null; $('stMsg').textContent = ''; renderStash(); show('stash'); }")

# expose for tests
rep("  get town() { return town; }, NPCS,", "  openStash, stashSave, stRun, ST_OPS,   // v0.15.2 (smoke_p152)\n  get town() { return town; }, NPCS,")

# patch notes fallback
rep("const PATCH_NOTES = [\n", "const PATCH_NOTES = [\n  ['0.15.2', tr('倉庫 200 → 500 格、技能珠喺倉庫疊埋；倉庫一鍵賣（普通／魔法／稀有／重複傳奇／多餘技能珠）同整理；自動賣出可以賣埋稀有。')],\n")

# English strings
EN = {
    '賣晒稀有': 'Sell rares',
    '背包冇稀有裝備': 'No rare gear in the bag',
    '確定？': 'Sure? ',
    ' 件稀有裝備（+': ' rare items (+',
    '賣重複傳奇': 'Sell duplicate legendaries',
    '整理倉庫': 'Sort stash',
    '整理好咗': 'Sorted',
    '冇嘢可以賣': 'Nothing to sell',
    ' 件 +': ' items +',
    ' 件（+': ' items (+',
    '賣咗（+': 'Sold (+',
    '倉庫已滿（': 'Stash full (',
    ' 格）': ' cells)',
    '背包＋倉庫一齊計；著緊嘅裝備同鑲緊嘅技能珠唔會賣': 'Counts bag + stash; worn gear and socketed orbs are never sold',
    '普通＋魔法＋稀有（只留傳奇） Common + Magic + Rare (keep legendaries)': 'Common + Magic + Rare (keep legendaries)',
    '倉庫 200 → 500 格、技能珠喺倉庫疊埋；倉庫一鍵賣（普通／魔法／稀有／重複傳奇／多餘技能珠）同整理；自動賣出可以賣埋稀有。':
        'Stash 200 → 500 slots and orbs stack in the stash; stash bulk sell (common / magic / rare / duplicate legendaries / spare orbs) and sort; auto-sell can include rares.',
}
import json
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();",
    "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.15.2\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")

open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
