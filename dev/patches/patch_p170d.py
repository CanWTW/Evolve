#!/usr/bin/env python3
"""EVOLVE v0.17.0 part D: stable column widths on the gear / orb screens, outdated help and description texts.
Usage: patch_p170d.py in.html out.html"""
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


def tx(zh_old, zh_new, en_new, count=None):
    """replace a user-facing string everywhere and give the new one an English line"""
    global h
    n = h.count(zh_old)
    if n == 0 or (count is not None and n != count):
        raise SystemExit('tx %r: %d' % (zh_old[:60], n))
    h = h.replace(zh_old, zh_new); EN[zh_new] = en_new


# ---------------- layout: fixed shares instead of content-sized columns ----------------
rep("#oBarCol{flex:0 0 auto}", "#oBarCol{flex:1 1 52%;min-width:0;max-width:640px}   /* v0.17: was content-sized → the bar could squeeze the bag */")
rep("#orbs #oBagCol{flex:1 1 auto;min-width:0}", "#orbs #oBagCol{flex:1 1 26%;min-width:172px}")
rep("#orbs:not(.narrow) #oDetail{flex:0 0 clamp(240px,30%,420px)}", "#orbs:not(.narrow) #oDetail{flex:0 0 clamp(220px,26%,380px)}")
rep(".orow{display:flex;align-items:center;gap:4px;flex:0 0 auto}", ".orow{display:flex;align-items:center;gap:4px;flex:0 0 auto;flex-wrap:wrap;min-width:0}")
rep(".stgrid .cell:hover{border-color:#ffd23f}",
    ".stgrid .cell:hover{border-color:#ffd23f}\n"
    ".oevo{flex-wrap:wrap}.obar .ocard{min-width:0}#gear:not(.narrow) #gEquipCol{flex:0 0 172px}#gear #gInvCol{min-width:180px}   /* v0.17 */\n"
    "#orbs.narrow #oBarCol{flex:1 1 auto;max-width:none}#orbs.narrow #oBagCol{flex:0 0 auto;min-width:0}")
# re-measure the narrow class whenever these screens open (rotating a phone used to keep the old layout)
rep("function orbLayout() { const O = $('orbs'); if (O.classList.contains('hidden')) return; O.classList.toggle('narrow', O.clientWidth < ORB_NARROW); }",
    "function orbLayout() { const O = $('orbs'); if (O.classList.contains('hidden')) return; O.classList.toggle('narrow', O.clientWidth < ORB_NARROW); }\n"
    "if (window.ResizeObserver) { try { new ResizeObserver(() => { if (screen === 'orbs') orbLayout(); if (screen === 'gear') gearLayout(); }).observe(document.body); } catch (e) { /* ignore */ } }   // v0.17")

# ---------------- texts ----------------
tx("右上 ❚❚ 暫停 · ☰ 技能連結與裝備 · 升級得能力點：❚❚ →「能力值」分配", "右上 ◆ 技能珠 · ⚔ 裝備 · ❚❚ 暫停（能力值、天賦、設定）· 右下「閃避」同「位移」",
   "Top right ◆ skill orbs · ⚔ equipment · ❚❚ pause (attributes, talents, options) · bottom right Dodge and Move")
tx("組合技能珠：例如「電弧火花 →暴擊施放→ 冰霜新星」，再配元素反應（碎冰、毒爆、電漿弧…）。", "3 招自動技能各自出招、會喺戰鬥中進化，兩招進化到 II 會融合成融合奧義；再用觸發珠連結（例如「電弧火花 →暴擊施放→ 冰霜新星」）同元素反應。",
   "3 auto skills cast on their own, evolve during a run, and two at stage II fuse into a Fusion; link more with trigger orbs (e.g. Arc Spark → Cast on Crit → Frost Nova) and elemental reactions.")
tx("技能珠：主動技能 120–150 金、輔助珠 90–110 金。買咗會自動鑲嵌（有空位嘅話）。觸發珠同被動珠只可以喺戰鬥掉落。", "技能珠：主動技能 120–160 金、持續技能 200–260 金、輔助珠 90–180 金。買咗會自動鑲入有用嘅空位。部分觸發珠有得賣，其餘同被動珠要喺戰鬥掉落。",
   "Orbs: actives 120–160 gold, persistent skills 200–260, supports 90–180. Bought orbs go into a free socket where they work. Some triggers are sold; the rest and all passives drop in battle.")
tx("⚠ 存檔只儲存喺呢個瀏覽器。itch.io 每次更新遊戲都可能換網址，令舊存檔讀唔到。請用「匯出」備份（複製或者下載 .txt），更新後喺呢度「匯入」。",
   "存檔儲存喺呢個瀏覽器；遊戲網址（canwtw.github.io/Evolve）固定，更新唔會冇存檔。登入帳戶可以自動雲端備份，亦可以用「匯出」另外備份（複製或者下載 .txt）。",
   "Saves live in this browser; the game's address (canwtw.github.io/Evolve) is fixed, so updates keep your saves. Log in for automatic cloud backup, or use Export for an extra copy (copy or download .txt).")
tx("升級會得能力點：INT 加法術、DEX 加暴擊同攻速、VIT 加生命。按 C 分配，或者搵雲姐。", "升級會得能力點：INT 加法術、STR 加近戰、DEX 加遠程同施法速度、AGI 加攻速同閃避、VIT 加生命、LUK 加暴擊率。按 C 分配，或者搵雲姐。",
   "Level-ups give attribute points: INT for spells, STR for melee, DEX for ranged and cast speed, AGI for attack speed and evasion, VIT for life, LUK for crit chance. Press C or talk to Yun.")
tx("技能珠可以連結：「A →觸發→ B」。按 K 打開技能珠畫面試吓。", "按 K 打開技能珠畫面：3 個自動技能槽、位移槽、持續槽，仲可以揀每招技能嘅進化路線；觸發珠可以連結「A →觸發→ B」。",
   "Press K for the orb screen: 3 auto skill slots, a movement slot, persistent slots, and an evolution path for each skill; trigger orbs link “A → trigger → B”.")
tx("歡迎光臨！我呢度有起始技能珠，主動技能 120 金、輔助珠 90 金。", "歡迎光臨！我呢度有技能珠賣，主動技能由 120 金起、輔助珠由 90 金起。", "Welcome! I sell skill orbs: actives from 120 gold, supports from 90.")
tx("位移槽嘅技能（跳躍重擊、衝刺打擊）落地時，喺落點施放連結技能。", "位移槽嘅技能（跳躍重擊、衝刺打擊、火焰衝刺、閃電傳送、冰霜閃現）到達落點時，喺落點施放連結技能。",
   "When the movement-slot skill (Leap Slam, Dash Strike, Flame Dash, Lightning Warp, Frostblink) arrives, casts the linked skill there.")
tx("主技能施放速度 +30%；傷害 ×0.85。（只影響主技能嘅施放頻率，唔影響觸發）", "呢招技能施放速度 +30%；傷害 ×0.85。（只影響自動施放嘅頻率，唔影響觸發）", "This skill casts 30% faster; damage ×0.85 (only how often it auto-casts, not triggers).")
tx("傷害 +40%；主技能施放速度 −25%。", "傷害 +40%；呢招技能施放速度 −25%。", "+40% damage; this skill casts 25% slower.")
tx("以施放點為中心嘅冰霜爆發（範圍 62），必定冰緩。做主技能時要有敵人喺 90 範圍內先會放；被觸發時喺觸發位置爆發。", "以你為中心嘅冰霜爆發（範圍 62），必定冰緩。自動施放時要有敵人喺 110 範圍內；被觸發時喺觸發位置爆發。",
   "A frost burst around you (radius 62) that always chills. Auto-casts when an enemy is within 110; when triggered it bursts at the trigger point.")
tx("撳背包嘅珠睇詳情，可以放嘅槽會亮綠色；3 粒同款同等級＋金幣可以融合升一級（最高 Lv", "撳背包嘅珠睇詳情，佢有用嘅槽會亮綠色（冇效嘅輔助珠會標 ✕）；3 粒同款同等級＋金幣可以融合升一級，倉庫入面都可以融合（最高 Lv",
   "Tap an orb for details; sockets where it works light up green (useless supports are marked ✕). 3 identical orbs of one level + gold fuse into the next level, also inside the stash (max Lv")
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok D layout/texts', len(h))
