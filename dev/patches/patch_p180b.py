#!/usr/bin/env python3
"""EVOLVE v0.18.0 part B: trigger chains. A link's source can be an auto skill or a skill another link casts, so
"A → trigger → B → trigger → C" chains can be built from the orb screen (the engine already limited them by trigger depth).
Usage: patch_p180b.py in.html out.html"""
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


rep("function normalizeBuild(g) {   // v0.16: a link keeps the auto skill the player picked while it is still socketed; otherwise auto 1\n"
    "  const b = g.player.build, A = autoSkillIds(g);\n"
    "  b.links.forEach((L) => { const tg = TRIGGERS[gemId(g, L.trig)]; if (tg && (tg.anySource || tg.fromMove)) { L.from = linkSourceId(g, tg); return; } if (!(L.from && A.indexOf(L.from) >= 0)) L.from = A[0] || null; });\n}",
    "function linkSources(g, li) {   // v0.18: auto skills, then skills that OTHER links cast (chains: A → B → C); a link never feeds itself\n"
    "  const b = g.player.build, out = autoSkillIds(g).slice();\n"
    "  b.links.forEach((L, j) => { if (j === li) return; const t = gemId(g, L.to), tg = TRIGGERS[gemId(g, L.trig)]; if (tg && t && SKILLS[t] && SKILLS[t].kind !== 'buff' && out.indexOf(t) < 0) out.push(t); });\n"
    "  const own = b.links[li] ? gemId(g, b.links[li].to) : null; return out.filter((s) => s !== own || autoSkillIds(g).indexOf(s) >= 0);\n}\n"
    "function normalizeBuild(g) {   // v0.16: a link keeps the source the player picked while it is still available; otherwise auto 1\n"
    "  const b = g.player.build;\n"
    "  b.links.forEach((L, li) => { const tg = TRIGGERS[gemId(g, L.trig)]; if (tg && (tg.anySource || tg.fromMove)) { L.from = linkSourceId(g, tg); return; } const A = linkSources(g, li); if (!(L.from && A.indexOf(L.from) >= 0)) L.from = A[0] || null; });\n}")
rep("  const A = autoSkillIds(g); if (!A.length) return null; L.from = A[(A.indexOf(L.from) + 1) % A.length]; return L.from;",
    "  const A = linkSources(g, li); if (!A.length) return null; L.from = A[(A.indexOf(L.from) + 1) % A.length]; return L.from;")
rep("cycleLinkSourceAuto: cycleLinkSource, linkSourceId,", "cycleLinkSourceAuto: cycleLinkSource, linkSourceId, linkSources,")
# UI: say where the source comes from and that it can be a chained skill
rep("      else if (L.from) { src.appendChild(gemIconEl(L.from)); src.title = tr('來源：') + D.SKILLS[L.from].name + (T && T.fromMove ? tr('（位移槽）') : tr('（撳一下換第二招自動技能）')); }",
    "      else if (L.from) { src.appendChild(gemIconEl(L.from)); const chained = C.autoSkillIds(g).indexOf(L.from) < 0 && !(T && T.fromMove); if (chained) { src.classList.add('chain'); src.appendChild(el('span', 'oschain', '⛓')); }\n"
    "        src.title = tr('來源：') + D.SKILLS[L.from].name + (T && T.fromMove ? tr('（位移槽）') : chained ? tr('（連鎖：另一條連結施放嘅技能）· 撳一下換來源') : tr('（撳一下換來源：自動技能或者其他連結施放嘅技能）')); }")
rep("b.links.length ? tr('撳最左邊嘅來源揀邊招自動技能觸發') : tr('Lv3 解鎖')",
    "b.links.length ? tr('撳左邊來源揀觸發者（可揀其他連結施放嘅技能做連鎖）') : tr('Lv3 解鎖')")
rep("    else s = tr('當') + (T.anySource ? tr('你') : D.SKILLS[L.from].name) + T.verb",
    "    else s = (!T.anySource && !T.fromMove && C.autoSkillIds(g).indexOf(L.from) < 0 ? tr('⛓ 連鎖：') : '') + (tr('當') === '當' ? '當' + (T.anySource ? tr('你') : D.SKILLS[L.from].name) + T.verb : (T.anySource ? 'You' : D.SKILLS[L.from].name) + ' · ' + T.name)")   # v0.18: English read "Pawn…Accuracy"
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n.osrc{position:relative}.osrc.chain{border-color:#ff9ce6}.oschain{position:absolute;right:-4px;bottom:-4px;font-size:11px;line-height:1;background:#1a1426;border-radius:6px;padding:1px}   /* v0.18 chains */")
EN.update({
    '（連鎖：另一條連結施放嘅技能）· 撳一下換來源': '(chain: a skill another link casts) · tap to change the source',
    '（撳一下換來源：自動技能或者其他連結施放嘅技能）': '(tap to change the source: an auto skill or a skill another link casts)',
    '撳左邊來源揀觸發者（可揀其他連結施放嘅技能做連鎖）': 'Tap the source to pick the trigger (another link\'s skill makes a chain)',
    '⛓ 連鎖：': '⛓ Chain: ',
})
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok B chains', len(h))
