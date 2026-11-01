#!/usr/bin/env python3
"""EVOLVE v0.18.0 part A: harder baseline + difficulty levels (普通 / 困難 / 地獄), character profile: server-unique names,
6-character public IDs, rename, friends (request / accept / remove) with online status. Supabase tables: characters, friends.
Usage: patch_p180a.py in.html out.html"""
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


# ---------------- difficulty ----------------
for old, new in [("tier: 1, recLevel: 1, hpMul: 1, dmgMul: 1,", "tier: 1, recLevel: 1, hpMul: 1.15, dmgMul: 1.15,"),
                 ("recLevel: 12, hpMul: 3.75, dmgMul: 1.6,", "recLevel: 12, hpMul: 4.9, dmgMul: 2,"),
                 ("recLevel: 26, hpMul: 10.1, dmgMul: 2.5,", "recLevel: 26, hpMul: 13.1, dmgMul: 3.1,"),
                 ("recLevel: 40, hpMul: 21.1, dmgMul: 3.5,", "recLevel: 40, hpMul: 27.4, dmgMul: 4.4,")]:
    rep(old, new)
rep("function tierZone(opts) {   // v0.10: a tier run",
    "const DIFFS = [   // v0.18 difficulty levels for main-zone runs (rift tiers, daily / weekly and boss rush keep their own scaling)\n"
    "  { id: 0, name: tr('普通'), en: 'Normal', hp: 1, dmg: 1, reward: 0, col: '#cfd8e8' },\n"
    "  { id: 1, name: tr('困難'), en: 'Hard', hp: 2.4, dmg: 1.7, reward: 0.6, col: '#ffb36b' },\n"
    "  { id: 2, name: tr('地獄'), en: 'Hell', hp: 5.5, dmg: 2.6, reward: 1.4, col: '#ff4a6e' },\n"
    "];\n"
    "function tierZone(opts) {   // v0.10: a tier run")
rep("  if (!T) return Z;\n  const B = ZONES['zone.void_sanctum'];",
    "  if (!T) { const Dd = DIFFS[opts.diff | 0]; return Dd && Dd.id ? Object.assign({}, Z, { hpMul: Z.hpMul * Dd.hp, dmgMul: Z.dmgMul * Dd.dmg, diff: Dd.id }) : Z; }   // v0.18\n  const B = ZONES['zone.void_sanctum'];")
rep("modReward: riftReward(opts.mods) + (Number.isInteger(opts.tier) && opts.tier >= 1 ? 0.04 * Math.min(opts.tier, 999) : 0),",
    "modReward: riftReward(opts.mods) + (Number.isInteger(opts.tier) && opts.tier >= 1 ? 0.04 * Math.min(opts.tier, 999) : 0) + (!opts.tier && !opts.rush && DIFFS[opts.diff | 0] ? DIFFS[opts.diff | 0].reward : 0), diff: !opts.tier && !opts.rush ? (opts.diff | 0) : 0,")
rep("ZONES, DEFAULT_ZONE,", "ZONES, DEFAULT_ZONE, DIFFS,")
# record boss kills per difficulty
rep("    const nz = g.zone && g.zone.next; const un = Array.isArray(s.progress.zonesUnlocked)",
    "    if (g.diff) { const DB = s.progress.diffBoss = s.progress.diffBoss || {}; DB[g.diff] = DB[g.diff] || {}; DB[g.diff][bid] = (DB[g.diff][bid] || 0) + 1; }   // v0.18\n"
    "    const nz = g.zone && g.zone.next; const un = Array.isArray(s.progress.zonesUnlocked)")
# the run passes the difficulty
rep("    try { g = C.Save.gameFromSave(cur, { seed, bossTime: bt ? +bt : undefined, zone: runZone, mods: runMods, tier: runTier || undefined, rush: runRush || undefined,",
    "    try { g = C.Save.gameFromSave(cur, { seed, bossTime: bt ? +bt : undefined, zone: runZone, mods: runMods, tier: runTier || undefined, rush: runRush || undefined, diff: !runChal && !runTier && !runRush ? diffNow() : 0,")
rep("let runZone = 'zone.rift_outskirts', runMods = [], runChal = null;",
    "function diffUnlocked(d) { const P = cur && cur.progress; if (!d) return true; if (d === 1) return !!(P && P.bossKills && P.bossKills['boss.void_sovereign'] > 0); return !!(P && P.diffBoss && P.diffBoss[1] && P.diffBoss[1]['boss.void_sovereign'] > 0); }   // v0.18\n"
    "let runDiff = (() => { try { return Math.max(0, Math.min(2, +localStorage.getItem('evolve.diff') || 0)); } catch (e) { return 0; } })();\n"
    "function diffNow() { let d = runDiff; while (d > 0 && !diffUnlocked(d)) d--; return d; }\n"
    "let runZone = 'zone.rift_outskirts', runMods = [], runChal = null;")
rep("  const L = $('zoneList'); L.textContent = '';\n  for (const z of Object.values(C.ZONES)) {",
    "  const L = $('zoneList'); L.textContent = '';\n"
    "  { const row = el('div', 'diffrow'); const d0 = diffNow(); row.appendChild(el('span', 'dl', tr('難度')));   // v0.18\n"
    "    for (const Dd of C.DIFFS) { const ok = diffUnlocked(Dd.id), b = el('button', 'small dbtn' + (d0 === Dd.id ? ' on' : '')); b.id = 'diff' + Dd.id; b.disabled = !ok; b.style.color = Dd.col;\n"
    "      b.append(el('b', null, Dd.name), el('small', null, ok ? (Dd.id ? tr('生命 ×') + Dd.hp + tr('、傷害 ×') + Dd.dmg + tr(' · 獎勵 +') + Math.round(Dd.reward * 100) + '%' : tr('標準')) : (Dd.id === 1 ? tr('🔒 打低虛空之主（Z4）') : tr('🔒 困難打低虛空之主'))));\n"
    "      b.addEventListener('click', () => { runDiff = Dd.id; try { localStorage.setItem('evolve.diff', String(Dd.id)); } catch (e) { /* ignore */ } renderZones(); }); row.appendChild(b); }\n"
    "    L.appendChild(row); }\n"
    "  for (const z of Object.values(C.ZONES)) {")
rep("(g._chal && !g.rush ? (g._chal.kind === 'daily' ? tr('每日裂隙 · ') : tr('每週裂隙 · ')) : '') + 'Z' + g.zone.n",
    "(g._chal && !g.rush ? (g._chal.kind === 'daily' ? tr('每日裂隙 · ') : tr('每週裂隙 · ')) : '') + (g.diff ? C.DIFFS[g.diff].name + ' · ' : '') + 'Z' + g.zone.n")
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    ".diffrow{grid-column:1/-1;display:flex;gap:6px;align-items:stretch;flex-wrap:wrap;margin-bottom:4px}.diffrow .dl{align-self:center;color:#8a93a6;font-weight:800;margin-right:4px}   /* v0.18 */\n"
    ".diffrow .dbtn{display:flex;flex-direction:column;align-items:flex-start;min-height:44px;padding:4px 10px;text-align:left}.diffrow .dbtn small{color:#9fb3c8;font-size:11px;font-weight:400}.diffrow .dbtn.on{border-color:currentColor;background:#2a2208}\n"
    "#profile{justify-content:flex-start}.pfgrid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:12px;width:100%;max-width:calc(var(--u)*520);flex:1;min-height:0}\n"
    ".pfbox{background:#100d1c;border:1px solid #2d2742;padding:8px 10px;overflow-y:auto;min-height:0}.pfbox h3{margin:0 0 6px;color:#7dfcff;font-size:max(13px,calc(var(--u)*5.5))}\n"
    ".pfid{font-size:max(18px,calc(var(--u)*8));font-weight:800;color:#ffd23f;letter-spacing:.1em}.pfrow{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:6px 0}.pfrow input{flex:1;min-width:120px;min-height:36px}\n"
    ".fr{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px dashed #2d2742}.fr .dot{width:9px;height:9px;border-radius:50%;background:#4a4560;flex:0 0 auto}.fr .dot.on{background:#7dff9b;box-shadow:0 0 6px #7dff9b}\n"
    ".fr .t{flex:1;min-width:0}.fr .t b{display:block}.fr .t small{color:#8a93a6}.pfmsg{min-height:1.2em;color:#ffd23f}.pfwarn{color:#ff8f8f}\n"
    "@media (max-height:520px){.pfgrid{grid-template-columns:1fr 1fr;max-width:none}#profile .snote{display:none}}")

# ---------------- profile / friends ----------------
rep('      <button id="tmCodex">圖鑑 Codex</button>', '      <button id="tmProfile">角色資料／好友 Profile</button>\n      <button id="tmCodex">圖鑑 Codex</button>')
rep('  <section id="ach" class="screen hidden">',
    '''  <!-- v0.18 profile: unique name, public ID, friends -->
  <section id="profile" class="screen hidden">
    <h2>角色資料 Profile</h2>
    <div class="snote">角色名全伺服器獨一無二。將你嘅角色 ID 俾朋友，佢哋就可以加你做好友（之後會用嚟組隊）。</div>
    <div class="pfgrid">
      <div class="pfbox"><h3>我嘅角色</h3><div id="pfMe"></div></div>
      <div class="pfbox"><h3>好友 Friends</h3><div class="pfrow"><input id="pfAddId" maxlength="7" placeholder="輸入好友 ID，例如 A7K2Q9" autocomplete="off"><button id="pfAdd" class="small primary">加好友</button></div><div id="pfFriends"></div></div>
    </div>
    <div id="pfMsg" class="pfmsg" aria-live="polite"></div>
    <div class="btns row"><button id="pfClose">返回 Back<span class="kbonly">（Esc）</span></button></div>
  </section>
  <section id="ach" class="screen hidden">''')
PROFILE = r"""
// ---------------- v0.18 character profile: unique names, public IDs, friends ----------------
const PID_CH = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function newPublicId() { let s = ''; const a = new Uint32Array(6); try { crypto.getRandomValues(a); } catch (e) { for (let i = 0; i < 6; i++) a[i] = Math.floor(Math.random() * 1e9); } for (let i = 0; i < 6; i++) s += PID_CH[a[i] % PID_CH.length]; return s; }
let pfState = { reg: '', note: '', friends: [], busy: false };   // reg: '' | 'ok' | 'taken' | 'other' | 'offline'
const nameOk = (n) => typeof n === 'string' && n.trim() === n && n.length >= 2 && n.length <= 12 && !/[<>\n\r\t]/.test(n);
function myPid() { return cur && cur.character && cur.character.publicId; }
function setCharField(k, v) { if (g && g.character && g.character.data) g.character.data[k] = v; if (villageMode && g) commitVillage((s) => { s.character[k] = v; }); else if (cur) { const s = JSON.parse(JSON.stringify(cur)); s.character[k] = v; writeSave(s, 'profile'); } }
async function sbJson(r) { try { return await r.json(); } catch (e) { return null; } }
function conflictKind(j) { const m = j && ((j.message || '') + ' ' + (j.details || '')); return /name_key/.test(m) ? 'name' : /pkey/.test(m) ? 'id' : /user_id_slot/.test(m) ? 'slot' : 'other'; }
async function registerChar(nameOverride) {   // makes sure this character has a row (unique name + public ID); returns 'ok' | 'taken' | 'other' | 'offline'
  if (!cur) return 'offline'; if (!(await sbAuth())) return 'offline';
  let pid = myPid(); if (!pid) { pid = newPublicId(); setCharField('publicId', pid); }
  const name = nameOverride || cur.character.name, lvl = cur.character.level || 1;
  try {
    const mine = await sbJson(await sbFetch('/rest/v1/characters?char_id=eq.' + pid + '&select=char_id,user_id,name', { auth: true }));
    if (Array.isArray(mine) && mine.length) { if (mine[0].user_id !== sbSess.uid) return 'other'; if (mine[0].name === name) return 'ok';
      const r = await sbFetch('/rest/v1/characters?char_id=eq.' + pid, { method: 'PATCH', auth: true, body: { name, level: lvl, last_seen: new Date().toISOString() }, headers: { Prefer: 'return=minimal' } });
      if (r.ok) return 'ok'; const j = await sbJson(r); return r.status === 409 && conflictKind(j) === 'name' ? 'taken' : 'offline'; }
    await sbFetch('/rest/v1/characters?user_id=eq.' + sbSess.uid + '&slot=eq.' + SLOT + '&char_id=neq.' + pid, { method: 'DELETE', auth: true, headers: { Prefer: 'return=minimal' } });   // an older character in this slot
    for (let k = 0; k < 3; k++) {
      const r = await sbFetch('/rest/v1/characters', { method: 'POST', auth: true, body: { char_id: pid, user_id: sbSess.uid, slot: SLOT, name, level: lvl, build: g ? buildTag(g) : '' }, headers: { Prefer: 'return=minimal' } });
      if (r.ok) return 'ok'; const j = await sbJson(r); if (r.status !== 409) return 'offline'; const ck = conflictKind(j);
      if (ck === 'name') return 'taken'; if (ck === 'id') { pid = newPublicId(); setCharField('publicId', pid); continue; } return 'other';
    }
  } catch (e) { return 'offline'; }
  return 'offline';
}
async function renameChar(n) {
  if (!nameOk(n)) return tr('名要 2–12 個字，前後唔可以有空格');
  const was = cur.character.name; const r = await registerChar(n);
  if (r === 'ok') { setCharField('name', n); pfState.reg = 'ok'; return ''; }
  if (r === 'taken') return tr('「') + n + tr('」已經有人用咗，試下第個名');
  if (r === 'other') return tr('呢個角色喺另一個帳戶登記咗：登入同一個帳戶先可以改名');
  return tr('連唔到伺服器，遲啲再試') + (was ? '' : '');
}
async function heartbeat() {   // every 60 s while a registered character is loaded
  try { const pid = myPid(); if (!pid || pfState.reg !== 'ok' || !sbSess || document.hidden) return; await sbAuth();
    await sbFetch('/rest/v1/characters?char_id=eq.' + pid, { method: 'PATCH', auth: true, body: { last_seen: new Date().toISOString(), level: (g && g.player ? g.player.level : cur.character.level) || 1, build: g ? buildTag(g) : '' }, headers: { Prefer: 'return=minimal' } }); } catch (e) { /* ignore */ }
}
setInterval(heartbeat, 60000);
async function loadFriends() {
  const pid = myPid(); if (!pid || !(await sbAuth())) return [];
  const rows = await sbJson(await sbFetch('/rest/v1/friends?or=(owner_char.eq.' + pid + ',friend_char.eq.' + pid + ')&select=owner_char,friend_char,status', { auth: true }));
  if (!Array.isArray(rows)) return []; const ids = [...new Set(rows.map((r) => (r.owner_char === pid ? r.friend_char : r.owner_char)))]; if (!ids.length) return [];
  const chars = await sbJson(await sbFetch('/rest/v1/characters?char_id=in.(' + ids.join(',') + ')&select=char_id,name,level,build,last_seen', { auth: true })); const by = {}; (chars || []).forEach((c) => { by[c.char_id] = c; });
  return rows.map((r) => { const other = r.owner_char === pid ? r.friend_char : r.owner_char; return { id: other, c: by[other] || null, status: r.status, incoming: r.friend_char === pid, row: r }; });
}
function pfMsg(t, bad) { const m = $('pfMsg'); m.textContent = t || ''; m.classList.toggle('pfwarn', !!bad); }
async function openProfile() { pfMsg(''); show('profile'); renderProfile(); pfMsg(tr('連線中…')); pfState.reg = await registerChar(); pfState.friends = pfState.reg === 'ok' ? await loadFriends() : []; pfMsg(''); renderProfile(); }
function closeProfile() { renderTownHud(); show(villageMode ? 'town' : 'title'); }
function renderProfile() {
  if (!cur) return; const M = $('pfMe'); M.textContent = ''; const pid = myPid();
  M.append(el('div', 'muted', tr('角色 ID')), el('div', 'pfid', pid ? '#' + pid : '—'));
  const st = pfState.reg; M.appendChild(el('div', st === 'ok' ? 'muted' : 'pfwarn', st === 'ok' ? tr('已登記 · 名稱全伺服器獨一無二') : st === 'taken' ? tr('⚠ 呢個名已經有人用：請改名先可以登記同加好友') : st === 'other' ? tr('⚠ 呢個角色登記喺另一個帳戶') : st === 'offline' ? tr('離線：連到伺服器先可以登記') : ''));
  if (pid) { const cp = el('button', 'small', tr('複製 ID')); cp.addEventListener('click', () => { try { navigator.clipboard.writeText(pid); pfMsg(tr('已複製：') + pid); } catch (e) { pfMsg(pid); } }); M.appendChild(cp); }
  const row = el('div', 'pfrow'); const inp = document.createElement('input'); inp.id = 'pfName'; inp.maxLength = 12; inp.value = cur.character.name || ''; inp.placeholder = tr('角色名稱（2–12 字）');
  const b = el('button', 'small primary', tr('改名')); b.id = 'pfRename';
  b.addEventListener('click', async () => { const n = (inp.value || '').trim(); if (n === cur.character.name && pfState.reg === 'ok') { pfMsg(tr('名冇變')); return; } b.disabled = true; pfMsg(tr('檢查緊…')); const err = await renameChar(n); b.disabled = false;
    if (err) pfMsg(err, true); else { pfMsg(tr('改好咗：') + n); pfState.friends = await loadFriends(); renderProfile(); updateSaveUi(); } });
  row.append(inp, b); M.appendChild(row);
  M.appendChild(el('div', 'muted', 'Lv ' + (cur.character.level || 1) + ' · ' + tr('存檔位 ') + (SLOT + 1)));
  const F = $('pfFriends'); F.textContent = ''; const list = pfState.friends || [];
  const on = (c) => c && c.last_seen && Date.now() - Date.parse(c.last_seen) < 180000;
  const sect = (title, arr, mk) => { if (!arr.length) return; F.appendChild(el('div', 'cxgrp', title + ' ' + arr.length)); arr.forEach((f) => F.appendChild(mk(f))); };
  const line = (f, btns) => { const r = el('div', 'fr'); r.appendChild(el('span', 'dot' + (on(f.c) ? ' on' : ''))); const t = el('div', 't');
    t.append(el('b', null, (f.c ? f.c.name : tr('（已刪除角色）')) + ' #' + f.id), el('small', null, f.c ? 'Lv ' + f.c.level + (f.c.build ? ' · ' + f.c.build : '') + ' · ' + (on(f.c) ? tr('在線') : tr('最後上線 ') + fmtSavedAt(f.c.last_seen)) : '')); r.appendChild(t);
    for (const [txt, cls, fn] of btns) { const bb = el('button', 'small ' + (cls || ''), txt); bb.addEventListener('click', fn); r.appendChild(bb); } return r; };
  const del = (f) => async () => { await sbFetch('/rest/v1/friends?owner_char=eq.' + f.row.owner_char + '&friend_char=eq.' + f.row.friend_char, { method: 'DELETE', auth: true, headers: { Prefer: 'return=minimal' } }); pfState.friends = await loadFriends(); renderProfile(); };
  const acc = (f) => async () => { await sbFetch('/rest/v1/friends?owner_char=eq.' + f.row.owner_char + '&friend_char=eq.' + f.row.friend_char, { method: 'PATCH', auth: true, body: { status: 'accepted' }, headers: { Prefer: 'return=minimal' } }); pfState.friends = await loadFriends(); renderProfile(); pfMsg(tr('已經加咗好友')); };
  const friends = list.filter((f) => f.status === 'accepted').sort((a, b) => (on(b.c) ? 1 : 0) - (on(a.c) ? 1 : 0));
  sect(tr('好友請求'), list.filter((f) => f.status === 'pending' && f.incoming), (f) => line(f, [[tr('接受'), 'primary', acc(f)], [tr('拒絕'), 'danger', del(f)]]));
  sect(tr('好友'), friends, (f) => line(f, [[tr('刪除'), 'danger', del(f)]]));
  sect(tr('等緊對方接受'), list.filter((f) => f.status === 'pending' && !f.incoming), (f) => line(f, [[tr('取消'), '', del(f)]]));
  if (!list.length) F.appendChild(el('div', 'muted', pfState.reg === 'ok' ? tr('未有好友：輸入朋友嘅角色 ID 加佢。') : tr('登記咗角色先可以加好友。')));
}
async function addFriend() {
  const id = String($('pfAddId').value || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); const pid = myPid();
  if (pfState.reg !== 'ok' || !pid) { pfMsg(tr('角色未登記：先改一個未有人用嘅名'), true); return; }
  if (!/^[A-Z2-9]{6}$/.test(id)) { pfMsg(tr('ID 係 6 個字母／數字'), true); return; } if (id === pid) { pfMsg(tr('唔可以加自己'), true); return; }
  const c = await sbJson(await sbFetch('/rest/v1/characters?char_id=eq.' + id + '&select=char_id,name', { auth: true })); if (!Array.isArray(c) || !c.length) { pfMsg(tr('搵唔到呢個 ID'), true); return; }
  if ((pfState.friends || []).some((f) => f.id === id)) { const f = pfState.friends.find((q) => q.id === id); if (f.status === 'pending' && f.incoming) { await sbFetch('/rest/v1/friends?owner_char=eq.' + id + '&friend_char=eq.' + pid, { method: 'PATCH', auth: true, body: { status: 'accepted' }, headers: { Prefer: 'return=minimal' } }); pfMsg(tr('已經加咗好友')); } else pfMsg(tr('已經喺你嘅好友名單')); pfState.friends = await loadFriends(); renderProfile(); return; }
  const r = await sbFetch('/rest/v1/friends', { method: 'POST', auth: true, body: { owner_char: pid, friend_char: id }, headers: { Prefer: 'return=minimal' } });
  pfMsg(r.ok ? tr('已經送出好友請求俾 ') + c[0].name : tr('送唔到請求（') + r.status + tr('）'), !r.ok); $('pfAddId').value = ''; pfState.friends = await loadFriends(); renderProfile();
}
on('tmProfile', () => openProfile()); on('pfClose', closeProfile); on('pfAdd', addFriend);
// register in the background when a character enters the village; a taken name asks for a rename
async function bgRegister() { try { const r = await registerChar(); pfState.reg = r; if (r === 'taken' && villageMode) townSay(tr('你個角色名已經有其他玩家用咗：去選單「角色資料／好友」改名。')); } catch (e) { /* ignore */ } }
"""
rep("function renderAch() {", PROFILE + "function renderAch() {")
rep("  setTimeout(achVillage, 400);   // v0.8.8", "  setTimeout(achVillage, 400);   // v0.8.8\n  setTimeout(bgRegister, 1500);   // v0.18")
rep("  if (screen === 'codex') { if (e.code === 'Escape') closeCodex(); return; }   // v0.17",
    "  if (screen === 'codex') { if (e.code === 'Escape') closeCodex(); return; }   // v0.17\n  if (screen === 'profile') { if (e.code === 'Escape') closeProfile(); return; }   // v0.18")
rep("  openStash, stashSave, stRun, ST_OPS,", "  openStash, stashSave, stRun, ST_OPS, openProfile, registerChar, renameChar, newPublicId, get pfState() { return pfState; }, diffUnlocked, diffNow, set runDiff(v) { runDiff = v; },")

EN.update({
    '普通': 'Normal', '困難': 'Hard', '地獄': 'Hell', '難度': 'Difficulty', '生命 ×': 'Life ×', '、傷害 ×': ', damage ×', ' · 獎勵 +': ' · rewards +', '標準': 'Standard',
    '🔒 打低虛空之主（Z4）': '🔒 Beat the Void Sovereign (Z4)', '🔒 困難打低虛空之主': '🔒 Beat the Void Sovereign on Hard',
    '角色資料／好友 Profile': 'Profile & friends', '角色資料 Profile': 'Profile', '我嘅角色': 'My character', '好友 Friends': 'Friends', '加好友': 'Add friend', '輸入好友 ID，例如 A7K2Q9': "Friend's ID, e.g. A7K2Q9",
    '角色名全伺服器獨一無二。將你嘅角色 ID 俾朋友，佢哋就可以加你做好友（之後會用嚟組隊）。': 'Character names are unique across the server. Give friends your character ID so they can add you (parties come later).',
    '名要 2–12 個字，前後唔可以有空格': 'Names are 2–12 characters, no leading or trailing spaces', '「': '"', '」已經有人用咗，試下第個名': '" is taken, try another name',
    '呢個角色喺另一個帳戶登記咗：登入同一個帳戶先可以改名': 'This character is registered to another account: log in with that account to rename it', '連唔到伺服器，遲啲再試': "Can't reach the server, try again later",
    '連線中…': 'Connecting…', '角色 ID': 'Character ID', '已登記 · 名稱全伺服器獨一無二': 'Registered · name is unique on the server', '⚠ 呢個名已經有人用：請改名先可以登記同加好友': '⚠ This name is taken: rename to register and add friends',
    '⚠ 呢個角色登記喺另一個帳戶': '⚠ This character is registered to another account', '離線：連到伺服器先可以登記': 'Offline: registration needs the server', '複製 ID': 'Copy ID', '已複製：': 'Copied: ',
    '角色名稱（2–12 字）': 'Character name (2–12)', '改名': 'Rename', '名冇變': 'Same name', '檢查緊…': 'Checking…', '改好咗：': 'Renamed: ', '存檔位 ': 'Slot ', '（已刪除角色）': '(deleted character)',
    '在線': 'Online', '最後上線 ': 'Last seen ', '已經加咗好友': 'Friend added', '好友請求': 'Friend requests', '接受': 'Accept', '拒絕': 'Decline', '好友': 'Friends', '刪除': 'Remove', '等緊對方接受': 'Waiting for them',
    '取消': 'Cancel', '未有好友：輸入朋友嘅角色 ID 加佢。': "No friends yet: enter a friend's character ID.", '登記咗角色先可以加好友。': 'Register your character to add friends.',
    '角色未登記：先改一個未有人用嘅名': 'Not registered: pick a name nobody uses yet', 'ID 係 6 個字母／數字': 'IDs are 6 letters / digits', '唔可以加自己': "You can't add yourself", '搵唔到呢個 ID': 'No character with that ID',
    '已經喺你嘅好友名單': 'Already on your list', '已經送出好友請求俾 ': 'Friend request sent to ', '送唔到請求（': 'Could not send the request (',
    '你個角色名已經有其他玩家用咗：去選單「角色資料／好友」改名。': 'Another player already uses your character name: rename it in Menu → Profile & friends.',
})
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok A', len(h))
