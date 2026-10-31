#!/usr/bin/env python3
"""EVOLVE v0.16.0 part UI: orb screen cards for 3 auto slots, link source picker, dead-support marks, live skill stats.
Usage: patch_p160b.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = json.load(open(src + '.en.json')) if __import__('os').path.exists(src + '.en.json') else {}


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)


a = h.index("  const supTab = (i) => (i === 0 ? U.sup : i === 1 ? U.moveSup : U.buffSup);")
b = h.index("  if (locked.length) B.appendChild(el('div', 'olocks',")
NEW = r"""  // v0.16: 自動技能 ×3 · 觸發連結 · 位移 · 持續 ×3 · 被動
  const supTab = (i) => { const r = C.slotRole(i); return r === 'primary' ? (i === 0 ? U.sup : U.subSup) : r === 'move' ? U.moveSup : U.buffSup; };
  const runDmg = g.stats && g.stats.dmgBySource ? g.stats.dmgBySource : {}, runTot = Object.values(runDmg).reduce((s, v) => s + v, 0);
  const mainRow = (i) => { const M = b.mains[i], r = el('div', 'orow'); r.appendChild(orbSock({ area: 'main', i, slot: 'skill' }, M.skill, 'active'));
    const T = supTab(i), mx = T[T.length - 1][1]; if (M.sup.length || unlockAt(T, 1)) r.appendChild(el('span', 'oplus', '+'));
    for (let j = 0; j < M.sup.length; j++) r.appendChild(orbSock({ area: 'main', i, slot: 'sup', j }, M.sup[j], 'support'));
    if (M.sup.length < mx) { const t = lockTile(T, M.sup.length + 1); if (t) r.appendChild(t); } return r; };
  const statLine = (sid) => {   // v0.16: is it doing anything? (this run)
    if (!sid) return null; const sk = D.SKILLS[sid]; const cst = (g.stats.casts && g.stats.casts[sid]) || 0, dm = runDmg[sid] || 0;
    const t = villageMode ? tr('出發後會顯示本局傷害') : sk.kind === 'buff' ? '' : tr('本局：傷害 ') + (runTot > 0 ? Math.round(dm / runTot * 100) : 0) + '%' + tr(' · 施放 ') + cst + (cst === 0 && g.t > 5 ? tr('（未出過招：') + (sk.attack && !C.attackWeapon(g, sk) ? tr('武器唔啱') : sk.kind === 'melee' ? tr('要貼近敵人') : tr('附近冇敵人')) + tr('）') : '');
    return t ? el('div', 'ostat' + (cst === 0 && !villageMode && g.t > 5 && sk.kind !== 'buff' ? ' bad' : ''), t) : null; };
  const head = (tag, cls, name, none, cnt) => { const hd = el('div', 'ohd'); hd.append(el('span', 'otag' + (cls ? ' ' + cls : ''), tag), el('span', 'oname' + (none ? ' none' : ''), name), el('span', 'ocnt', cnt)); return hd; };
  { const card = el('div', 'ocard prim'); card.id = 'oCardPrim'; const A = C.AUTO_ROWS;
    const have = A.filter((i) => b.mains[i]), on = have.filter((i) => b.mains[i].skill != null).length;
    card.appendChild(head(tr('自動技能'), 'prim', tr('全部自動出招，每招有自己嘅輔助珠'), false, on + '/' + have.length));
    A.forEach((i, k) => {
      if (b.mains[i]) { const sid = C.gemId(g, b.mains[i].skill); const r = mainRow(i); r.insertBefore(el('span', 'onum', String(k + 1)), r.firstChild); r.id = 'oAuto_' + k; card.appendChild(r); const st = statLine(sid); if (st) card.appendChild(st); }
      else { const lv = unlockAt(U.mains, i + 1); if (lv && A.slice(0, k).every((q) => b.mains[q])) { const r = el('div', 'orow'); r.append(el('span', 'onum', String(k + 1)), orbLock('Lv' + lv)); card.appendChild(r); } }
    });
    B.appendChild(card); }
  { const card = el('div', 'ocard'); card.id = 'oCardLinks'; const done = b.links.filter((L) => L.trig != null && L.to != null).length;
    const maxL = U.links[U.links.length - 1][1];
    card.appendChild(head(tr('觸發連結'), 'link', b.links.length ? tr('撳最左邊嘅來源揀邊招自動技能觸發') : tr('Lv3 解鎖'), !b.links.length, done + '/' + b.links.length));
    b.links.forEach((L, i) => {
      const lr = el('div', 'orow link'); const tid = C.gemId(g, L.trig), T = tid ? D.TRIGGERS[tid] : null;
      const fixed = T && (T.anySource || T.fromMove), src = el(fixed ? 'div' : 'button', 'osrc' + (fixed ? ' fixed' : '')); src.id = 'oSrc_' + i;
      if (T && T.anySource) { src.textContent = tr('你'); src.title = tr('由你自己觸發（') + T.verb + tr('）'); }
      else if (L.from) { src.appendChild(gemIconEl(L.from)); src.title = tr('來源：') + D.SKILLS[L.from].name + (T && T.fromMove ? tr('（位移槽）') : tr('（撳一下換第二招自動技能）')); }
      else { src.textContent = '—'; src.title = T && T.fromMove ? tr('位移槽要放位移技能') : tr('要揀一招自動技能做來源'); }
      if (!fixed) src.addEventListener('click', () => { C.cycleLinkSourceAuto(g, i); hudCache.build = null; if (villageMode) commitVillage(); renderOrbs(); });
      lr.append(src, el('span', 'oarr', '→'), orbSock({ area: 'link', i, slot: 'trig' }, L.trig, 'trigger'), el('span', 'oarr', '→'), orbSock({ area: 'link', i, slot: 'to' }, L.to, 'active'));
      if (L.sup.length || unlockAt(U.linkSup, 1)) lr.appendChild(el('span', 'oplus', '+'));
      for (let j = 0; j < L.sup.length; j++) lr.appendChild(orbSock({ area: 'link', i, slot: 'sup', j }, L.sup[j], 'support'));
      if (L.sup.length < maxLS) { const t = lockTile(U.linkSup, L.sup.length + 1); if (t) lr.appendChild(t); }
      card.appendChild(lr);
      if (tid && L.to != null && !villageMode && g.t > 5) card.appendChild(el('div', 'ostat' + ((L.n || 0) ? '' : ' bad'), tr('本局觸發 ') + (L.n || 0) + tr(' 次')));
    });
    if (b.links.length < maxL) card.appendChild(el('div', 'olinknote', tr('↳ 觸發連結 ') + (b.links.length + 1) + ' 🔒 Lv' + unlockAt(U.links, b.links.length + 1) + tr(' 解鎖（由你揀嘅自動技能觸發；受傷／閃避／格擋由你觸發；位移施放由位移技能觸發）')));
    B.appendChild(card); }
  if (b.mains[1]) { const M = b.mains[1], sid = C.gemId(g, M.skill), card = el('div', 'ocard'); card.id = 'oCardMove';
    card.appendChild(head(tr('位移'), 'move', sid ? D.SKILLS[sid].name + tr('（手動：位移掣／E／右鍵）') : tr('放位移技能（跳躍重擊、衝刺打擊、火焰衝刺、閃電傳送、冰霜閃現）'), !sid, tr('輔助 ') + M.sup.filter((u) => u != null).length + '/' + M.sup.length));
    card.appendChild(mainRow(1)); B.appendChild(card); }
  { const card = el('div', 'ocard'); card.id = 'oCardBuff'; const BR = [2, 4, 6], have = BR.filter((i) => b.mains[i]), on = have.filter((i) => b.mains[i].skill != null).length;
    card.appendChild(head(tr('持續'), 'buff', tr('光環／先驅／護盾／灌注（一直生效）'), false, on + '/' + have.length));
    for (const i of have) card.appendChild(mainRow(i));
    const nx = BR.find((i) => !b.mains[i]); if (nx != null) { const lv = unlockAt(U.mains, nx + 1); if (lv) { const r = el('div', 'orow'); r.appendChild(orbLock('Lv' + lv)); card.appendChild(r); } }
    B.appendChild(card); }
"""
h = h[:a] + NEW + h[b:]
EN.update({
    '自動技能': 'Auto skills', '全部自動出招，每招有自己嘅輔助珠': 'All cast automatically; each has its own supports',
    '出發後會顯示本局傷害': 'Run stats show up once you set out', '本局：傷害 ': 'This run: damage ', ' · 施放 ': ' · casts ', '（未出過招：': ' (never cast: ',
    '武器唔啱': 'wrong weapon', '要貼近敵人': 'needs to be next to enemies', '附近冇敵人': 'no enemies nearby', '）': ')',
    '觸發連結': 'Trigger links', '撳最左邊嘅來源揀邊招自動技能觸發': 'Tap the source on the left to pick which auto skill feeds it', 'Lv3 解鎖': 'Unlocks at Lv3',
    '（撳一下換第二招自動技能）': ' (tap to switch auto skill)', '要揀一招自動技能做來源': 'Needs an auto skill as its source', '本局觸發 ': 'Triggered ', ' 次': ' times this run',
    ' 解鎖（由你揀嘅自動技能觸發；受傷／閃避／格擋由你觸發；位移施放由位移技能觸發）': ' unlock (fed by the auto skill you pick; Damaged/Dodge/Block by you; Landing by the movement skill)',
    '（手動：位移掣／E／右鍵）': ' (manual: move button / E / right-click)', '放位移技能（跳躍重擊、衝刺打擊、火焰衝刺、閃電傳送、冰霜閃現）': 'Put a movement skill here (Leap Slam, Dash Strike, Flame Dash, Lightning Warp, Frostblink)',
    ' 對 ': ' does nothing for ', ' 冇效': '', '持續槽只可以放持續技能用嘅輔助珠': 'Persistent slots only take supports for persistent skills', ' 只可以配持續技能': ' only works with persistent skills',
    '冇效：呢粒輔助珠對呢招技能冇作用': 'No effect: this support does nothing for this skill',
})
# dead support marking + full-rule highlight
rep("  else if (sx && C.socketAccepts(where, C.gemType(sx.id), sx.id)) b.classList.add('ok');",
    "  else if (sx && C.socketOk(g, where, sx.id)) b.classList.add('ok');\n"
    "  if (x && C.gemType(x.id) === 'support' && where.area !== 'passive' && C.supportDead(g, where, uid)) { b.classList.add('dead'); b.appendChild(el('em', 'odead', '✕')); b.title = tr('冇效：呢粒輔助珠對呢招技能冇作用'); }   // v0.16")
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    ".osock.dead{opacity:.55;border-style:dashed!important}.osock .odead{position:absolute;right:1px;top:-2px;color:#ff6b6b;font-style:normal;font-weight:800;font-size:12px}   /* v0.16 */\n"
    ".ostat{font-size:max(11px,calc(var(--u)*4.2));color:#9fb0c8;margin:-2px 0 4px 26px}.ostat.bad{color:#ff8f8f}.onum{display:inline-flex;align-items:center;justify-content:center;min-width:16px;color:#ffd23f;font-weight:800;margin-right:2px}\n"
    "button.osrc{cursor:pointer}button.osrc:hover{border-color:#ffd23f}")

open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok UI', len(h))
